"""How far a flow can be followed, and on what evidence. The states are the module's whole vocabulary.

Similar amounts and close times never prove anything: they make a candidate, shown beside how often the
same rule matches on controls. A service's internal books are not public, and Monero's privacy is not
something this code tries to defeat: there, the trail stops and says so.
"""
import hashlib
import random
from collections import Counter

from .client import ENDPOINTS, ChainError
from .flows import RELAY_DEPOSITORY, TRANSFER, label_of, transfers

ONCHAIN_CONFIRMED = 'ONCHAIN_CONFIRMED'
PROTOCOL_LINK_CONFIRMED = 'PROTOCOL_LINK_CONFIRMED'
SERVICE_INTERACTION = 'SERVICE_INTERACTION'
CROSSCHAIN_CANDIDATE = 'CROSSCHAIN_CANDIDATE'
OFFCHAIN_RECORD_REQUIRED = 'OFFCHAIN_RECORD_REQUIRED'
XMR_VISIBILITY_BOUNDARY = 'XMR_VISIBILITY_BOUNDARY'
INSUFFICIENT_EVIDENCE = 'INSUFFICIENT_EVIDENCE'
OWNERSHIP = 'OWNERSHIP_NOT_ESTABLISHED'
CANDIDATE_WINDOW_S = 6 * 3600
BRIDGE_MIN_RATIO, BRIDGE_MAX_RATIO = .90, 1.001
SPEND_SECRETS = frozenset({'spend_key', 'spendkey', 'private_spend_key', 'seed', 'mnemonic', 'mnemonic_seed', 'wallet_password', 'password'})
MONERO_RPC_HOSTS = ('http://127.0.0.1', 'http://localhost')
RELAY_ORIGIN_CHAINS = (1, 42161, 8453, 10, 137)
RELAY_SOLVER = '0xf70da97812cb96acdf810712aa562db8dfa3dbef'


def relation(state, source, target, *, chain_id=137, tx=None, log_index=None, token=None, raw=None, raw_meaning='received_by_target', received_raw=None, payout_tx=None, order_id=None, source_is_service=False, at=None, basis, alternatives=(), via=()):
    return dict(state=state, source=source, target=target, chain_id=chain_id, tx=tx, log_index=log_index, token=token, raw=str(raw) if raw is not None else None, raw_meaning=raw_meaning, received_raw=str(received_raw) if received_raw is not None else None, payout_tx=payout_tx, order_id=order_id,
                source_is_service=source_is_service, funder_shown=not source_is_service,
                at=at, basis=basis, alternatives=list(alternatives), via=list(via), ownership=OWNERSHIP,
                url=f'https://polygonscan.com/tx/{tx}' if tx and chain_id == 137 else None)


def candidate_matches(target, pool, window_s=CANDIDATE_WINDOW_S, min_ratio=BRIDGE_MIN_RATIO, max_ratio=BRIDGE_MAX_RATIO):
    """Later amounts close to this one. The ratio allows bridge fees. A candidate, never a link."""
    return [p for p in pool if p.get('owner') != target.get('owner') and 0 <= p['at'] - target['at'] <= window_s and target['amount'] > 0 and min_ratio <= p['amount'] / target['amount'] <= max_ratio]


def chance_rate(targets, pool, shifts_s=(3 * 86400, 5 * 86400, 7 * 86400, 11 * 86400), seed=20261101, **rule):
    """The rule on real times, then with the pool moved by days: what matches then is accident by construction."""
    rng = random.Random(seed)
    real = sum(bool(candidate_matches(t, pool, **rule)) for t in targets)
    shifted = hits = 0
    for t in targets:
        moved = dict(t, at=t['at'] + rng.choice(shifts_s) * rng.choice((-1, 1)))
        shifted += 1
        hits += bool(candidate_matches(moved, pool, **rule))
    return dict(targets=len(targets), pool=len(pool), real_with_candidate=real, control_targets=shifted, control_with_candidate=hits, control_rate=hits / shifted if shifted else None,
                reading='A control rate near the real rate means the rule finds accidents as easily as links.')


def origin_transfer(client, record, bridge_address):
    """The bridge's record names a transaction; the origin chain's receipt must show the same token, amount and recipient."""
    chain = int(record['fromChainId']) if str(record.get('fromChainId', '')).isdigit() else None
    if chain not in ENDPOINTS:
        return None, f"Chain {record.get('fromChainId')} is not read here"
    try:
        receipt = client.receipt(record['txHash'], chain)
    except ChainError as exc:
        return None, f'Origin receipt unavailable: {str(exc)[:100]}'
    if not receipt:
        return None, 'Named transaction not found on the origin chain'
    token = record['fromTokenAddress'].lower()
    wanted = int(record['fromAmountBaseUnit'])
    for t in transfers(receipt, chain):
        if t['token'] == token and t['target'] == bridge_address.lower() and t['raw'] == wanted:
            return t, None
    return None, 'Receipt shows no transfer of that token and amount to this bridge address'


def bridge_upstream(client, source_address, amount_raw, at, decimals=6):
    """Upstream of a deposit's sender, through Polymarket's public bridge record. An address used by many stays a candidate."""
    status, body = client.get_json(f'https://bridge.polymarket.com/status/{source_address}', dict(limit=50))
    if status != 200 or not isinstance(body, dict):
        return dict(state=INSUFFICIENT_EVIDENCE, basis=f'No public bridge record for this address (HTTP {status}).', relations=[])
    records = body.get('transactions', [])
    nearby = []
    for r in records:
        if r.get('status') != 'COMPLETED' or str(r.get('fromChainId')) == '137':
            continue
        created = r.get('createdTimeMs', 0) / 1000
        size = int(r.get('fromAmountBaseUnit') or 0) / 10 ** (18 if str(r.get('fromChainId')) == '56' else decimals)
        if 0 <= at - created <= CANDIDATE_WINDOW_S and size and BRIDGE_MIN_RATIO <= (amount_raw / 10 ** decimals) / size <= BRIDGE_MAX_RATIO:
            nearby.append(r)
    exact = [r for r in records if str(r.get('fromChainId')) == '137' and str(r.get('fromAmountBaseUnit')) == str(amount_raw) and abs(at - r.get('createdTimeMs', 0) / 1000) <= CANDIDATE_WINDOW_S]
    out = dict(records_on_this_address=len(records), records_capped=len(records) >= 50, candidates=len(nearby), exact_same_chain_record=bool(exact), relations=[])
    if not nearby:
        out.update(state=INSUFFICIENT_EVIDENCE, basis='No cross-chain record of a comparable amount shortly before this deposit.')
        return out
    for r in nearby[:3]:
        moved, why = origin_transfer(client, r, source_address)
        if moved:
            out['relations'].append(relation(PROTOCOL_LINK_CONFIRMED, moved['source'], source_address, chain_id=moved['chain_id'], tx=moved['tx'], log_index=moved['log_index'], token=moved['token'], raw=moved['raw'], at=r['createdTimeMs'] / 1000,
                                             basis='Named by the official bridge record for this address, and shown by the origin chain receipt.', alternatives=['The sender may itself be a service paying for someone else.']))
        else:
            out.setdefault('unverified', []).append(why)
    out.update(state=CROSSCHAIN_CANDIDATE, basis=f"{len(nearby)} cross-chain record(s) of this address fit by amount and time, with no identifier shared with the deposit. The origin sender stays unknown unless a named hash is found on its chain.", ambiguous=len(nearby) > 1,
               origin_chains=sorted({str(r['fromChainId']) for r in nearby}), origin_amounts=[r['fromAmountBaseUnit'] for r in nearby][:3])
    return out


def relay_order_status(client, order):
    """Relay's public status route, read by order id. Its full request route needs an API key, which this code does not use."""
    status, body = client.get_json('https://api.relay.link/intents/status/v3', dict(requestId=order['order_id']))
    if status != 200 or not isinstance(body, dict) or body.get('status') in (None, 'unknown'):
        return dict(state=OFFCHAIN_RECORD_REQUIRED, order_id=order['order_id'], basis='The escrow deposit and its order id are on-chain; the public status route does not know this id, so the destination is not public.', status=(body or {}).get('status') if isinstance(body, dict) else status)
    hashes = body.get('txHashes') or []
    out = dict(state=OFFCHAIN_RECORD_REQUIRED, order_id=order['order_id'], status=body.get('status'), destination_chain=body.get('destinationChainId') or body.get('chainId'), out_tx=hashes, relations=[])
    chain = out['destination_chain']
    if body.get('status') == 'success' and hashes and chain in ENDPOINTS:
        receipt = client.receipt(hashes[0], chain)
        moved = transfers(receipt, chain) if receipt else []
        if moved:
            out.update(state=PROTOCOL_LINK_CONFIRMED, basis='Same order id on the protocol status route, and a final receipt on the destination chain.', destination_transfers=[dict(token=t['token'], source=t['source'], target=t['target'], raw=str(t['raw']), log_index=t['log_index']) for t in moved][:12])
    return out


def block_near(client, chain, moment, rate_s=2.0, tolerance_s=300):
    """A block within minutes of a time, by secant steps on block timestamps, since block rates drift over months."""
    high = client.head(chain)
    guess, time_at = high, client.block_time(high, chain)
    for _ in range(5):
        if abs(time_at - moment) <= tolerance_s:
            break
        step = int((time_at - moment) / rate_s)
        other = max(1, min(high, guess - step))
        other_time = client.block_time(other, chain)
        if other != guess and other_time != time_at:
            rate_s = abs((time_at - other_time) / (guess - other)) or rate_s
        guess, time_at = other, other_time
    return guess, rate_s


def relay_origin_from_payout(client, payout_tx, at, wallet, received_raw, chains=RELAY_ORIGIN_CHAINS):
    """Relay's payout carries the order id at the end of its calldata, and the escrow logs the same id on the origin chain.

    Both sides are public chain data, so this needs no service's record. Anyone can append a copied id to a
    transfer of their own, so the payout counts only if Relay's documented solver itself paid this wallet.
    """
    payout = client.receipt(payout_tx)
    if not payout or not any(t['source'] == RELAY_SOLVER and t['target'] == wallet.lower() for t in transfers(payout)):
        return None
    transaction = client.rpc('eth_getTransactionByHash', [payout_tx])
    order = (transaction or {}).get('input', '')[-64:].lower()
    if len(order) != 64 or int(order, 16) < 2 ** 128:
        return None
    for chain in chains:
        try:
            block, rate = block_near(client, chain, at)
            logs = client.rpc('eth_getLogs', [dict(fromBlock=hex(max(1, block - int(1800 / rate))), toBlock=hex(block + int(300 / rate)), address=RELAY_DEPOSITORY)], chain)
        except ChainError:
            continue
        hit = next((l for l in logs if order in l['data'][2:].lower()), None)
        if not hit:
            continue
        receipt = client.receipt(hit['transactionHash'], chain)
        # A bundle can carry several people's deposits: take the transfer this escrow log accounts for, not the first one.
        amount = int(hit['data'][2:][128:192], 16)
        position = int(hit['logIndex'], 16)
        paying = [t for t in transfers(receipt, chain) if t['target'] == RELAY_DEPOSITORY and t['raw'] == amount and t['log_index'] < position] if receipt else []
        if not paying:
            continue
        moved = max(paying, key=lambda t: t['log_index'])
        return dict(state=PROTOCOL_LINK_CONFIRMED, order_id='0x' + order, origin_chain=chain, origin_tx=hit['transactionHash'], origin_submitter=(receipt.get('from') or '').lower(), origin_sender=moved['source'], payout_tx=payout_tx,
                    basis='The same order id is in the escrow log on the origin chain and in the calldata of a payout the documented solver made to this wallet.',
                    relations=[relation(PROTOCOL_LINK_CONFIRMED, moved['source'], wallet.lower(), chain_id=chain, tx=hit['transactionHash'], log_index=moved['log_index'], token=moved['token'], raw=moved['raw'], raw_meaning='left_source_on_origin_chain', received_raw=received_raw, payout_tx=payout_tx, order_id='0x' + order, at=at,
                                        basis='Same order id in the escrow log and in the calldata of a payout made by the documented solver, read from public chain data.', alternatives=['The sender may be a smart wallet or a service acting for someone else.'], via=['Relay'])])
    return None


def relay_fill_origin(client, tx, wallet):
    """A fill paid by Relay on Polygon. Its public record, while that route lives, names an origin transaction and a sender.

    The origin transaction's own sender is often a bundler, so the record's sender counts only if the origin
    receipt shows it moving tokens, and the fill counts for this wallet only if the record names it as recipient.
    """
    status, body = client.get_json('https://api.relay.link/requests/v2', dict(hash=tx))
    requests = (body or {}).get('requests') if isinstance(body, dict) else None
    if status != 200 or not requests:
        return dict(state=OFFCHAIN_RECORD_REQUIRED, basis=f'Relay paid this deposit; its public route gives no origin for it (HTTP {status}). The origin is in Relay\u2019s records.', relations=[])
    record = requests[0]
    data = record.get('data') or {}
    meta = data.get('metadata') or {}
    recipient = str(record.get('recipient') or meta.get('recipient') or '').lower()
    sender = str(record.get('user') or meta.get('sender') or '').lower()
    out = dict(state=OFFCHAIN_RECORD_REQUIRED, order_id=record.get('id'), status=record.get('status'), recipient_matches=recipient == wallet.lower(), relations=[], basis='Record found; its origin transaction could not be checked.')
    if recipient != wallet.lower():
        out.update(state=INSUFFICIENT_EVIDENCE, basis='The record for this fill names another recipient.')
        return out
    for t in data.get('inTxs') or []:
        chain, origin_tx = t.get('chainId'), t.get('hash')
        if chain not in ENDPOINTS or not origin_tx:
            out['basis'] = f'Origin on chain {chain}, which is not read here.'
            continue
        receipt = client.receipt(origin_tx, chain)
        if not receipt:
            out['basis'] = 'The named origin transaction was not found on its chain.'
            continue
        out.update(origin_chain=chain, origin_tx=origin_tx, origin_submitter=receipt.get('from', '').lower())
        moved = next((m for m in transfers(receipt, chain) if m['source'] == sender), None)
        if moved:
            out.update(state=PROTOCOL_LINK_CONFIRMED, origin_sender=sender, basis='Same request id on the protocol record; the origin receipt shows this sender moving tokens; the record names this wallet as recipient.')
            out['relations'].append(relation(PROTOCOL_LINK_CONFIRMED, sender, wallet.lower(), chain_id=chain, tx=origin_tx, log_index=moved['log_index'], token=moved['token'], raw=moved['raw'], raw_meaning='left_source_on_origin_chain', basis='Protocol record and origin receipt agree on the sender; the record names this recipient.', alternatives=['The sender may be a smart wallet or a service acting for someone else.'], via=['Relay']))
        else:
            out.update(state=CROSSCHAIN_CANDIDATE, basis='The record names a sender the origin receipt does not show moving tokens; only the recipient and the transaction agree.')
    return out


def changenow_tier(*, labelled=False, candidate=False, record=None, record_verified=False):
    """Four levels kept apart. No ChangeNOW address list is published, so the first needs a sourced label."""
    if record is not None and record_verified:
        return dict(tier=3, state=PROTOCOL_LINK_CONFIRMED, basis='Exchange id supplied by someone entitled to it, both hashes verified on their chains.')
    if candidate:
        return dict(tier=2, state=CROSSCHAIN_CANDIDATE, basis='Plausible by time and amount only. This is not evidence of a common owner.')
    if labelled:
        return dict(tier=1, state=SERVICE_INTERACTION, basis='Transaction to an address a cited source attributes to this service.')
    return dict(tier=4, state=OFFCHAIN_RECORD_REQUIRED, basis='Cannot be shown without the service’s internal record.')


def verify_exchange_record(client, record):
    """A swap record the user may access. Each hash must exist with the stated amount and address, or the link stays open."""
    source = record.get('record_source')
    checks = {}
    for side, key, chain_key, address_key, amount_key in (('payin', 'payinHash', 'fromChainId', 'payinAddress', 'amountSendRaw'), ('payout', 'payoutHash', 'toChainId', 'payoutAddress', 'amountReceiveRaw')):
        chain = record.get(chain_key)
        if not record.get(key) or chain not in ENDPOINTS:
            checks[side] = 'NOT_CHECKABLE'
            continue
        receipt = client.receipt(record[key], chain)
        moved = transfers(receipt, chain) if receipt else []
        checks[side] = 'VERIFIED' if any(t['target'] == record.get(address_key, '').lower() and str(t['raw']) == str(record.get(amount_key)) for t in moved) else 'NOT_FOUND'
    if str(record.get('toCurrency', '')).lower() == 'xmr':
        return dict(monero_boundary(), id=record.get('id'), checks=checks)
    verified = checks.get('payin') == 'VERIFIED' and checks.get('payout') == 'VERIFIED' and source == 'exchange_api_authorized'
    return dict(changenow_tier(record=record, record_verified=verified, candidate=not verified and checks.get('payin') == 'VERIFIED'), id=record.get('id'), checks=checks, record_source=source)


def monero_boundary():
    return dict(state=XMR_VISIBILITY_BOUNDARY, basis='Monero hides sender, receiver and amount by design. The trail stops at the swap; nothing here tries to read past it.', tracing_continues=False)


def later_transparent_exit(observation):
    """A later exit on a transparent chain is its own observation until something links them."""
    return dict(observation, state=INSUFFICIENT_EVIDENCE, linked_to_monero_entry=False, basis='Observed independently. No proof connects it to any Monero entry.')


def verify_monero_proof(proof, wallet_rpc=None, post=None):
    """Checks a voluntary proof through the user's own local wallet RPC. Refuses spend secrets, keeps no key."""
    leaked = SPEND_SECRETS & {str(k).lower() for k in proof}
    if leaked:
        raise ValueError('Spend secrets are refused and were not read: ' + ', '.join(sorted(leaked)))
    kind = proof.get('kind')
    method = dict(tx_key='check_tx_key', tx_proof='check_tx_proof', reserve_proof='check_reserve_proof').get(kind)
    if not method:
        return dict(monero_boundary(), proof_verified=False, reason='Unknown proof kind')
    if not wallet_rpc:
        return dict(monero_boundary(), state=OFFCHAIN_RECORD_REQUIRED, proof_verified=False, reason='No local Monero wallet RPC given; the proof was not checked.')
    if not wallet_rpc.startswith(MONERO_RPC_HOSTS):
        raise ValueError('A proof goes to a local wallet RPC only')
    params = {k: v for k, v in proof.items() if k != 'kind'}
    result = post(wallet_rpc, dict(jsonrpc='2.0', id='0', method=method, params=params))
    answer = result.get('result') or {}
    good = bool(answer.get('good', answer.get('received', 0)))
    return dict(monero_boundary(), proof_verified=good, proof_kind=kind, tx_hash=proof.get('txid'), address=proof.get('address'), received=answer.get('received'), confirmations=answer.get('confirmations'), material_sha256=hashlib.sha256(str(sorted(params.items())).encode()).hexdigest(),
                reading='Shows this address received this output. It links to no EVM flow unless something else does.')
