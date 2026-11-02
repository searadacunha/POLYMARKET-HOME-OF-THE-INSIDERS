"""Follows each deposit back and each withdrawal forward, hop by hop, from public chain data and Relay's public record.

Every relation carries a stable id and one category. A category is only as strong as what was read:
ONCHAIN_CONFIRMED (logs of one transaction), PROTOCOL_CONFIRMED (same order id on both chains, read from chain data),
SERVICE_INTERACTION (an address a cited source attributes to a service), STATISTICAL_CANDIDATE, UNKNOWN, XMR_VISIBILITY_BOUNDARY.

Usage: case_chain.py SLUG. Needs cases/SLUG.json from case_build.py. Re-running reads the cache.
"""
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import identities
import net
import sol

ROOT = Path(__file__).resolve().parent.parent
UTC = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))
SOLANA = 792703809
PUSD = net.TOKENS['pUSD']
USDCE = net.TOKENS['USDC.e']
RELAY_DEPOSITORY = '0x4cd00e387622c35bddb9b4c962c136462338bc31'
SERVICES = json.loads((ROOT / 'tools/services.json').read_text())['addresses']
net.RPC[56] = ('https://bsc-mainnet.gateway.tatum.io', 'https://56.rpc.thirdweb.com', 'https://bsc.blockrazor.xyz')
ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
STABLES_18 = {56}


def label(address):
    return SERVICES.get(address) or SERVICES.get(str(address).lower())


def b58_hex(text):
    n = 0
    for c in text:
        n = n * 58 + ALPHABET.index(c)
    return n.to_bytes((n.bit_length() + 7) // 8, 'big').hex()


class Case:
    def __init__(self, slug):
        self.slug, self.relations, self.stops = slug, [], []

    def rel(self, category, source, target, chain, tx, log_index=None, token=None, amount=None, at=None, basis='', alternatives=(), order_id=None, received=None, payout_tx=None, payout_chain=None):
        key = '|'.join(str(x) for x in (category, source, target, chain, tx, log_index))
        row = dict(id='R' + hashlib.sha256(key.encode()).hexdigest()[:14], case=self.slug, category=category, source=source, target=target, chain=chain, tx=tx, log_index=log_index, token=token, amount=amount, received=received, at=at, utc=UTC(at) if at else None, order_id=order_id, payout_tx=payout_tx, payout_chain=payout_chain, source_label=label(source), target_label=label(target), basis=basis, alternatives=list(alternatives), ownership='OWNERSHIP_NOT_ESTABLISHED')
        if not any(r['id'] == row['id'] for r in self.relations):
            self.relations.append(row)
        return row


def relay_record(tx):
    body = net.get('https://api.relay.link/requests/v2', dict(hash=tx), pause=12)  # the pause only applies when the answer is not cached
    requests = (body.get('requests') or []) if isinstance(body, dict) else []
    if not requests:
        return None
    q = requests[0]
    data, meta = q.get('data') or {}, (q.get('data') or {}).get('metadata') or {}
    cin, cout = meta.get('currencyIn') or {}, meta.get('currencyOut') or {}
    return dict(id=q.get('id'), status=q.get('status'), user=q.get('user'), recipient=q.get('recipient'), in_txs=[(t.get('chainId'), t.get('hash')) for t in data.get('inTxs') or []], out_txs=[(t.get('chainId'), t.get('hash')) for t in data.get('outTxs') or []],
                in_symbol=(cin.get('currency') or {}).get('symbol'), in_address=(cin.get('currency') or {}).get('address'), in_amount=cin.get('amountFormatted'), in_raw=cin.get('amount'), in_chain=(cin.get('currency') or {}).get('chainId'),
                out_symbol=(cout.get('currency') or {}).get('symbol'), out_amount=cout.get('amountFormatted'), out_chain=(cout.get('currency') or {}).get('chainId'))


def receipt_transfers(tx, chain=137):
    rc = net.rpc('eth_getTransactionReceipt', [tx], chain)
    out = []
    for l in rc['logs']:
        if l['topics'] and l['topics'][0] == net.TRANSFER and len(l['topics']) == 3 and l['data'] != '0x':
            out.append(dict(log_index=int(l['logIndex'], 16), token=l['address'].lower(), source='0x' + l['topics'][1][-40:], target='0x' + l['topics'][2][-40:], raw=int(l['data'], 16)))
    return rc, out


def block_at(chain, moment):
    low, high = 1, int(net.rpc('eth_blockNumber', [], chain), 16)
    for _ in range(45):
        if high - low <= 1:
            break
        mid = (low + high) // 2
        if net.block_time(mid, chain) < moment:
            low = mid
        else:
            high = mid
    return high


def inflow_on_polygon(address, amount, at, back=7200):
    """The transfer of exactly this amount into this address before this time, USDC.e or USDC."""
    high, low = block_at(137, at + 5), block_at(137, at - back)
    found = []
    for start in range(low, high + 1, net.CHUNK):
        for log in net.rpc('eth_getLogs', [dict(address=[USDCE, net.TOKENS['USDC']], fromBlock=hex(start), toBlock=hex(min(high, start + net.CHUNK - 1)), topics=[net.TRANSFER, None, net.pad(address)])], 137):
            if int(log['data'], 16) == amount:
                found.append(dict(tx=log['transactionHash'], log_index=int(log['logIndex'], 16), block=int(log['blockNumber'], 16), source='0x' + log['topics'][1][-40:], token=net.TOKEN_NAME[log['address'].lower()]))
    return found


def balance_funder(chain, token, holder, amount, spend_block):
    """Finds who paid an address by bisecting its token balance: a dozen calls instead of scanning thousands of blocks on throttled nodes."""
    def bal(block):
        time.sleep(1.2)
        return int(net.rpc('eth_call', [dict(to=token, data='0x70a08231' + holder[2:].rjust(64, '0')), hex(block)], chain), 16)
    high = spend_block - 1
    if bal(high) < amount:
        high = spend_block
    step, low = 2000, high - 2000
    while bal(low) >= amount and step < 2_000_000:
        step *= 2
        low = high - step
    while high - low > 1:
        mid = (low + high) // 2
        if bal(mid) >= amount:
            high = mid
        else:
            low = mid
    time.sleep(1.5)
    rows = []
    for log in net.rpc('eth_getLogs', [dict(address=token, fromBlock=hex(high), toBlock=hex(high), topics=[net.TRANSFER, None, net.pad(holder)])], chain):
        rows.append(dict(tx=log['transactionHash'], log_index=int(log['logIndex'], 16), block=high, at=net.block_time(high, chain), source='0x' + log['topics'][1][-40:], raw=int(log['data'], 16)))
    return rows


def address_kind(address, chain):
    code = net.rpc('eth_getCode', [address, 'latest'], chain)
    kind = 'EOA' if code in ('0x', None) else 'EIP7702_DELEGATED_EOA' if code.startswith('0xef0100') else 'CONTRACT'
    return dict(kind=kind, nonce=net.nonce(address, chain))


def follow_solana_origin(case, wallet_address, record, amount_note):
    """Who paid the address that deposited into Relay on Solana."""
    user, sig = record['user'], record['in_txs'][0][1]
    tx = sol.transaction(sig)
    sigs, complete = sol.signatures(user, limit=200, max_pages=2, must_contain=[sig])
    earlier = [s for s in sigs if s['blockTime'] <= tx['blockTime'] and s['signature'] != sig][:8]
    funders = []
    for s in earlier:
        t = sol.transaction(s['signature'])
        moves = sol.token_moves(t)
        if any(m['owner'] == user and m['delta'] > 0 for m in moves):
            payers = [m for m in moves if m['delta'] < 0 and m['owner'] != user]
            for m in payers[:2]:
                r = case.rel('SERVICE_INTERACTION' if label(m['owner']) else 'ONCHAIN_CONFIRMED', m['owner'], user, SOLANA, s['signature'], token=m['mint'], amount=-m['delta'], at=s['blockTime'],
                             basis=f"Token balances of one confirmed Solana transaction. {label(m['owner'])['name']} per {label(m['owner'])['source']}: a service paid, so the funder is not shown." if label(m['owner']) else 'Token balances of one confirmed Solana transaction.',
                             alternatives=['The sender may be a service holding funds for someone else.'] if not label(m['owner']) else ['An exchange withdrawal: only the exchange knows the account.'])
                funders.append(r)
    case.stops.append(dict(address=user, chain=SOLANA, history_signatures=len(sigs), history_complete=complete, funders=[f['source'] for f in funders], state='OFFCHAIN_RECORD_REQUIRED' if any(f['source_label'] for f in funders) else 'UNKNOWN'))
    return funders


def trace_deposit(case, wallet, deposit):
    tx, at = deposit['tx'], deposit['at']
    rc, moves = receipt_transfers(tx)
    want = round(float(deposit['usd']) * 1e6)
    mint = [m for m in moves if m['token'] == PUSD and m['target'] == wallet and m['source'] == '0x' + '0' * 40]
    paid = [m for m in moves if m['token'] == USDCE and m['target'] == PUSD and abs(m['raw'] - want) <= 1]
    if not paid:
        # Not a wrap: another route into the wallet, kept as seen.
        direct = [m for m in moves if m['target'] == wallet and abs(m['raw'] - want) <= 1 and m['source'] != '0x' + '0' * 40]
        for m in direct:
            case.rel('ONCHAIN_CONFIRMED', m['source'], wallet, 137, tx, m['log_index'], net.TOKEN_NAME.get(m['token'], m['token']), m['raw'] / 1e6, at, 'Transfer log of one confirmed transaction.', ['The sender may be a service paying for someone else.'])
        if not direct:
            case.stops.append(dict(tx=tx, state='UNKNOWN', basis='Deposit receipt shows no exact wrap and no exact transfer to the wallet.', moves=len(moves), mint=bool(mint)))
        return
    src = paid[0]['source']
    case.rel('ONCHAIN_CONFIRMED', src, wallet, 137, tx, paid[0]['log_index'], 'USDC.e→pUSD', want / 1e6, at, 'USDC.e paid into pUSD by this address, pUSD minted to the wallet, same amount, one confirmed transaction. The zero address only mints: it is not a funder.', ['This address may be a bridge deposit address or a service, not a person.'])
    kind = address_kind(src, 137)
    try:
        records = net.get('https://bridge.polymarket.com/status/' + src, dict(limit=50), retries=2)
        records = records.get('transactions', []) if isinstance(records, dict) else []
    except RuntimeError:  # the route answers 5xx for an address it does not know: that says nothing about the address
        records = []
    hop = dict(deposit_tx=tx, immediate_source=src, kind=kind, polymarket_bridge_records=len(records))
    # Polymarket's own bridge address or a direct payer: what paid it, on Polygon, in the two hours before?
    payers = inflow_on_polygon(src, want, at)
    if not payers:
        hop['payer'] = None
        case.stops.append(dict(address=src, tx=tx, state='UNKNOWN', basis='No exact USDC.e or USDC inflow to this address in the 2 hours before. The funds were there earlier or arrived in another amount.'))
        return hop
    payer = payers[-1]
    hop['payer'] = payer
    record = relay_record(payer['tx'])
    calldata = net.rpc('eth_getTransactionByHash', [payer['tx']], 137)['input'][-64:].lower()
    if not record or not record['in_txs']:
        t = net.block_time(payer['block'])
        case.rel('SERVICE_INTERACTION' if label(payer['source']) else 'ONCHAIN_CONFIRMED', payer['source'], src, 137, payer['tx'], payer['log_index'], payer['token'], want / 1e6, t, 'Transfer log of one confirmed transaction. Relay has no record of it.', ['The sender may be a service paying for someone else.'])
        hop['payer_kind'] = address_kind(payer['source'], 137)
        return hop
    in_chain, in_tx = record['in_txs'][0]
    hop['relay'] = record
    same_id = False
    origin_at = None
    if in_chain == SOLANA:
        t = sol.transaction(in_tx)
        origin_at = t['blockTime']
        datas = [i.get('data') for i in t['transaction']['message']['instructions'] if i.get('data')] + [i.get('data') for g in (t['meta'].get('innerInstructions') or []) for i in g['instructions'] if i.get('data')]
        same_id = any(calldata in b58_hex(d) for d in datas)
    elif in_chain in net.RPC:
        r, _ = receipt_transfers(in_tx, in_chain)
        origin_at = net.block_time(int(r['blockNumber'], 16), in_chain)
        same_id = any(l['address'].lower() == RELAY_DEPOSITORY and calldata in l['data'].lower() for l in r['logs'])
    amount_in = float(record['in_amount'] or 0)
    case.rel('PROTOCOL_CONFIRMED' if same_id else 'SERVICE_INTERACTION', record['user'], src, in_chain, in_tx, token=record['in_symbol'], amount=amount_in, received=want / 1e6, at=origin_at, order_id='0x' + calldata, payout_tx=payer['tx'], payout_chain=137,
             basis=('Same order id in the origin chain deposit and at the end of the Polygon payout calldata, read from chain data, paid by a solver Relay publishes.' if same_id else 'Relay\'s public record names this origin. The order id could not be matched in origin chain data.'), alternatives=['The sender may be a smart wallet or a service acting for someone else.'])
    if in_chain == SOLANA:
        hop['funders'] = [f['id'] for f in follow_solana_origin(case, wallet, record, want)]
    elif in_chain in net.RPC and record['in_address'] and record['user'].lower() == src:
        # The bridge address is the same on every EVM chain: read who paid it there.
        r, moved = receipt_transfers(in_tx, in_chain)
        spent = [m for m in moved if m['source'] == src]
        if spent:
            rows = balance_funder(in_chain, spent[0]['token'], src, spent[0]['raw'], int(r['blockNumber'], 16))
            for row in rows:
                k = address_kind(row['source'], in_chain)
                lab = label(row['source'])
                decimals = 18 if in_chain in STABLES_18 else 6
                case.rel('SERVICE_INTERACTION' if lab else 'ONCHAIN_CONFIRMED', row['source'], src, in_chain, row['tx'], row['log_index'], record['in_symbol'], row['raw'] / 10 ** decimals, row['at'], f"Transfer log on the origin chain, found by bisecting the bridge address balance. Sender nonce {k['nonce']}, kind {k['kind']}." + (f" {lab['name']} per {lab['source']}." if lab else ''), ['An exchange or custodian paying from a pooled address: its nonce would show it.'] if k['nonce'] > 100000 else ['The sender may be a service paying for someone else.'])
                hop.setdefault('origin_sender', []).append(dict(row, kind=k))
    elif in_chain in net.RPC:
        hop['origin_sender_kind'] = address_kind(record['user'], in_chain)
    return hop


def trace_exit(case, wallet, withdrawal):
    tx, at = withdrawal['tx'], withdrawal['at']
    rc, moves = receipt_transfers(tx)
    want = round(float(withdrawal['usd']) * 1e6)
    zero = '0x' + '0' * 40
    # A pUSD burn goes to the zero address: that is the unwrap, never a destination. What matters is where the wallet then sent the collateral.
    exact = [m for m in moves if abs(m['raw'] - want) <= 1 and m['token'] in (USDCE, net.TOKENS['USDC'], PUSD) and m['target'] not in (PUSD, zero, wallet) and m['source'] != zero]
    pick = [m for m in exact if m['source'] == wallet] or exact
    goes_to = pick[-1]['target'] if pick else None
    hop = dict(tx=tx, usd=withdrawal['usd'], at=at, first_destination=goes_to)
    if goes_to is None:
        case.stops.append(dict(tx=tx, state='UNKNOWN', basis='No exact outflow identified in the withdrawal receipt.', moves=len(moves)))
        return hop
    is_relay = goes_to == RELAY_DEPOSITORY or (label(goes_to) or {}).get('kind') == 'bridge'
    if not is_relay:
        k = address_kind(goes_to, 137)
        lab = label(goes_to)
        case.rel('SERVICE_INTERACTION' if lab else 'ONCHAIN_CONFIRMED', wallet, goes_to, 137, tx, pick[-1]['log_index'], net.TOKEN_NAME.get(pick[-1]['token']), want / 1e6, at, f"Transfer log of one confirmed transaction. Receiver nonce {k['nonce']}, kind {k['kind']}." + (f" {lab['name']} per {lab['source']}." if lab else ''), ['The receiver may be a service holding funds for someone else.'])
        hop['kind'] = k
        return hop
    record = relay_record(tx)
    escrow = None
    for l in rc['logs']:
        if l['address'].lower() == RELAY_DEPOSITORY and l['data'] != '0x':
            for i in range(0, len(l['data']) - 2, 64):
                word = l['data'][2:][i:i + 64]
                if len(word) == 64 and int(word, 16) >= 2 ** 200:
                    escrow = word
    hop['relay'] = record
    hop['escrow_id'] = escrow
    if not record or not record['out_txs']:
        case.rel('SERVICE_INTERACTION', wallet, goes_to, 137, tx, pick[-1]['log_index'], 'USDC.e', want / 1e6, at, 'Reached a Relay contract. No public record of the payout: the destination stays with Relay.', order_id=('0x' + escrow) if escrow else None)
        case.stops.append(dict(tx=tx, state='OFFCHAIN_RECORD_REQUIRED', basis='Escrow deposit on-chain, payout not found on the public route.'))
        return hop
    out_chain, out_tx = record['out_txs'][0]
    same_id = False
    payout_at = None
    if out_tx is None:
        # A swap settled inside the deposit transaction: the record names no separate payout, and a native payment leaves no log.
        out_tx, payout_at = tx, at
        hop['same_transaction_swap'] = True
        hop['recipient_native_balance_now'] = int(net.rpc('eth_getBalance', [record['recipient'], 'latest'], out_chain), 16) / 1e18
    elif out_chain == SOLANA:
        t = sol.transaction(out_tx)
        payout_at = t['blockTime']
        memos = [str(i.get('parsed')) for i in t['transaction']['message']['instructions'] if i.get('program') == 'spl-memo']
        same_id = bool(escrow) and any(escrow in m.lower() for m in memos)
    elif out_chain in net.RPC:
        r = net.rpc('eth_getTransactionByHash', [out_tx], out_chain)
        payout_at = net.block_time(int(r['blockNumber'], 16), out_chain)
        same_id = bool(escrow) and r['input'][-64:].lower() == escrow
    recipient = record['recipient']
    case.rel('PROTOCOL_CONFIRMED' if same_id else 'SERVICE_INTERACTION', wallet, recipient, out_chain, out_tx, token=record['out_symbol'], amount=float(record['out_amount'] or 0), received=want / 1e6, at=payout_at, order_id=('0x' + escrow) if escrow else record['id'], payout_tx=tx, payout_chain=137,
             basis='Same order id in the Polygon escrow log and in the payout on the destination chain, read from chain data, paid by a solver Relay publishes.' if same_id else ('Relay\'s public record names this recipient for a swap inside this transaction. The swap logs are on-chain; the native payment leaves no log, so the amount received rests on the record.' if hop.get('same_transaction_swap') else 'Relay\'s public record names this recipient. The order id could not be matched in destination chain data.'), alternatives=['The recipient may be a service, an exchange deposit address or another person.'])
    hop['recipient'] = recipient
    hop['out_chain'] = out_chain
    return hop


def follow_recipient(case, address, chain, must=()):
    """State today, and the first moves out. Stops at a labelled service: nothing beyond it is public."""
    out = dict(address=address, chain=chain, read_at=UTC(time.time()), label=label(address))
    if chain == SOLANA:
        sigs, complete = sol.signatures(address, limit=200, max_pages=2, must_contain=must)
        out.update(signatures=len(sigs), complete=complete, sol=sol.rpc('getBalance', [address])['value'] / 1e9)
        accounts = sol.rpc('getTokenAccountsByOwner', [address, dict(programId='TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA'), dict(encoding='jsonParsed')])['value']
        out['tokens'] = [dict(mint=a['account']['data']['parsed']['info']['mint'], amount=a['account']['data']['parsed']['info']['tokenAmount']['uiAmount'], delegate=a['account']['data']['parsed']['info'].get('delegate')) for a in accounts]
        moved = []
        for s in reversed(sigs[-30:]):
            t = sol.transaction(s['signature'])
            mine = [m for m in sol.token_moves(t) if m['owner'] == address and m['delta'] < 0]
            if mine:
                others = [m for m in sol.token_moves(t) if m['owner'] != address and m['delta'] > 0]
                moved.append(dict(sig=s['signature'], at=s['blockTime'], out=mine, to=others[:3]))
                for m in others[:3]:
                    case.rel('SERVICE_INTERACTION' if label(m['owner']) else 'ONCHAIN_CONFIRMED', address, m['owner'], SOLANA, s['signature'], token=m['mint'], amount=m['delta'], at=s['blockTime'], basis='Token balances of one confirmed Solana transaction.', alternatives=['A swap, a pool or a service may have taken the other side.'])
        out['moved_out'] = moved
    elif chain in net.RPC:
        out['kind'] = address_kind(address, chain)
    return out


def run(slug):
    path = ROOT / f'cases/{slug}.json'
    c = json.loads(path.read_text())
    wallet = c['address']
    case = Case(slug)
    for owner in (c.get('wallet') or {}).get('owners') or []:
        case.rel('ONCHAIN_CONFIRMED', owner, wallet, 137, None, basis='owner() read on the Deposit Wallet. A key, not a person.')
    c['funding_chain'] = [trace_deposit(case, wallet, d) for d in c['deposits']]
    c['exit_chain'] = [trace_exit(case, wallet, w) for w in c['withdrawals']]
    seen, c['recipients'] = set(), []
    for hop in c['exit_chain']:
        if hop and hop.get('recipient') and hop['recipient'] not in seen:
            seen.add(hop['recipient'])
            must = [h['relay']['out_txs'][0][1] for h in c['exit_chain'] if h.get('recipient') == hop['recipient'] and h.get('relay')] if hop.get('out_chain') == SOLANA else []
            c['recipients'].append(follow_recipient(case, hop['recipient'], hop['out_chain'], must))
    c['chain_relations'], c['chain_stops'] = case.relations, case.stops
    path.write_text(json.dumps(c, indent=1, ensure_ascii=False))
    with (ROOT / 'graphs/relations.jsonl').open('a') as f:
        for r in case.relations:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(slug, 'relations', len(case.relations), 'stops', len(case.stops), 'calls', net.Stats.calls, 'cached', net.Stats.cached)


if __name__ == '__main__':
    run(sys.argv[1])
