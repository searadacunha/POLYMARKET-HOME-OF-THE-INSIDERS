"""Whole history of one address by block cursor, with the range actually covered.

Earlier readers stopped at 6 pages and kept both ends; a block cursor reaches the end or says where it stopped.
A capped read is INCOMPLETE with its exact covered range, never a short history. Token rows have no log index
here: they stay LISTED until a receipt confirms them.
"""
from datetime import datetime

from .events import ARCHIVED, FRESH, LISTED, NATIVE, TOKENS
from .keccak import selector
from .net import Refused

ETHERSCAN = 'https://api.etherscan.io/v2/api'
ETHERSCAN_CHAINS = (1, 137, 42161)
BLOCKSCOUT = {10: 'https://explorer.optimism.io'}
PAGE = 1000
MAX_ROWS = 30000
COMPLETE, INCOMPLETE = 'COMPLETE', 'INCOMPLETE'


def _class(meta):
    return ARCHIVED if meta.get('origin') == 'archived' else FRESH


def _etherscan_page(net, chain, action, address, start):
    params = dict(chainid=chain, module='account', action=action, address=address, page=1, offset=PAGE, sort='asc', startblock=start, endblock=999999999)
    body, meta = net.get(ETHERSCAN, params, pause=.25, secret=dict(apikey=net.etherscan_key()))
    message = str(body.get('message', ''))
    if body.get('status') == '1' or any(m in message for m in ('No transactions', 'No records', 'No internal', 'No token')):
        return body.get('result') or [], meta
    raise Refused(f'etherscan {chain} {action} {address}: {message} {str(body.get("result"))[:120]}')


def _cursor(net, chain, action, address, max_rows):
    """Asc pages from a moving start block. The last block is read again in the next page, since a page can cut it in two."""
    rows, seen, start, classes = [], set(), 0, set()
    while True:
        batch, meta = _etherscan_page(net, chain, action, address, start)
        classes.add(_class(meta))
        new = 0
        for r in batch:
            key = (r.get('hash'), r.get('from'), r.get('to'), r.get('value'), r.get('contractAddress'), r.get('traceId'), r.get('tokenID'), r.get('nonce') if action == 'txlist' else None)
            if key not in seen:
                seen.add(key)
                rows.append(r)
                new += 1
        if len(batch) < PAGE:
            return rows, dict(status=COMPLETE, from_block=0, to_block=None, classes=sorted(classes))
        last = int(batch[-1]['blockNumber'])
        if new == 0 or last == start:  # a single block holds a full page: this reader cannot go further
            return rows, dict(status=INCOMPLETE, from_block=0, to_block=last, reason='a full page within one block', classes=sorted(classes))
        if len(rows) >= max_rows:
            return rows, dict(status=INCOMPLETE, from_block=0, to_block=last, reason=f'row budget of {max_rows} reached', classes=sorted(classes))
        start = last


def _native(chain, r, kind, cls):
    return dict(chain_id=chain, block_number=int(r['blockNumber']), block_hash=r.get('blockHash'), transaction_hash=r.get('hash') or r.get('transactionHash'), log_index=None, kind=kind, contract=None, token=NATIVE[chain], decimals=18, raw_amount=str(r['value']), timestamp=int(r['timeStamp']), **{'from': r['from'].lower(), 'to': (r.get('to') or r.get('contractAddress') or '').lower()}, success=r.get('isError', '0') == '0', method=(r.get('functionName') or '').split('(')[0] or r.get('methodId') or None, trace_id=r.get('traceId'), source=f'etherscan-v2:{chain}:{kind}', decoding='explorer listing', level=LISTED, data_class=cls)


def _token(chain, r, cls):
    contract = r['contractAddress'].lower()
    known = TOKENS.get(chain, {}).get(contract)
    return dict(chain_id=chain, block_number=int(r['blockNumber']), block_hash=r.get('blockHash'), transaction_hash=r['hash'], log_index=int(r['logIndex']) if str(r.get('logIndex', '')).isdigit() else None, kind='erc20', contract=contract, token=known[0] if known else r.get('tokenSymbol'), token_known=bool(known), decimals=known[1] if known else int(r.get('tokenDecimal') or 0), raw_amount=str(r['value']), timestamp=int(r['timeStamp']), **{'from': r['from'].lower(), 'to': r['to'].lower()}, success=True, method=None, source=f'etherscan-v2:{chain}:tokentx', decoding='explorer listing', level=LISTED, data_class=cls)


def _sequence(events):
    """Two identical listed rows in one transaction are two moves: number them, so they never merge."""
    counts = {}
    for e in events:
        if e.get('log_index') is None:
            key = (e['transaction_hash'], e['kind'], e['from'], e['to'], e.get('contract'), e['raw_amount'])
            e['seq'] = counts.get(key, 0)
            counts[key] = e['seq'] + 1
    return events


def _blockscout(net, chain, address, max_rows):
    base = BLOCKSCOUT[chain]
    out, status = [], COMPLETE
    for path, kind, extra in ((f'/api/v2/addresses/{address}/transactions', 'native', {}), (f'/api/v2/addresses/{address}/internal-transactions', 'internal', {}), (f'/api/v2/addresses/{address}/token-transfers', 'erc20', dict(type='ERC-20'))):
        query, read = dict(extra), 0
        while True:
            body, meta = net.get(base + path, query or None, pause=.4)
            if '_http_error' in body:
                if body['_http_error'] == 404:
                    break
                raise Refused(f'blockscout {chain} {path}: {body}')
            for x in body.get('items') or []:
                at = int(datetime.fromisoformat(x['timestamp'].replace('Z', '+00:00')).timestamp())
                common = dict(chain_id=chain, block_number=int(x.get('block') or x.get('block_number') or 0), block_hash=x.get('block_hash'), transaction_hash=x.get('hash') or x.get('transaction_hash'), timestamp=at, level=LISTED, data_class=_class(meta), source=f'blockscout:{chain}:{kind}', decoding='explorer listing', **{'from': ((x.get('from') or {}).get('hash') or '').lower(), 'to': ((x.get('to') or {}).get('hash') or '').lower()})
                if kind == 'erc20':
                    contract = ((x.get('token') or {}).get('address_hash') or (x.get('token') or {}).get('address') or '').lower()
                    known = TOKENS.get(chain, {}).get(contract)
                    out.append(dict(common, log_index=x.get('log_index'), kind='erc20', contract=contract, token=known[0] if known else (x.get('token') or {}).get('symbol'), token_known=bool(known), decimals=known[1] if known else int((x.get('token') or {}).get('decimals') or 0), raw_amount=str((x.get('total') or {}).get('value') or 0), success=True, method=None))
                else:
                    out.append(dict(common, log_index=None, kind=kind, contract=None, token=NATIVE[chain], decimals=18, raw_amount=str(x.get('value') or 0), success=(x.get('status') or x.get('success')) in ('ok', True), method=x.get('method')))
                read += 1
            params = body.get('next_page_params')
            if not params:
                break
            if read >= max_rows:
                status = INCOMPLETE
                break
            query = dict(extra, **params)
    return out, dict(status=status, from_block=0, to_block=None, reason=None if status == COMPLETE else f'row budget of {max_rows} reached', classes=[FRESH])


def history(net, address, chain, max_rows=MAX_ROWS):
    """(events, coverage). Zero-value natives from others are dropped, failed transactions stay flagged and never count as a flow."""
    address = address.lower()
    if chain in ETHERSCAN_CHAINS:
        events, parts = [], {}
        txs, parts['txlist'] = _cursor(net, chain, 'txlist', address, max_rows)
        internal, parts['txlistinternal'] = _cursor(net, chain, 'txlistinternal', address, max_rows)
        tokens, parts['tokentx'] = _cursor(net, chain, 'tokentx', address, max_rows)
        cls = lambda p: ARCHIVED if parts[p]['classes'] == [ARCHIVED] else FRESH
        events = [_native(chain, r, 'native', cls('txlist')) for r in txs] + [_native(chain, r, 'internal', cls('txlistinternal')) for r in internal] + [_token(chain, r, cls('tokentx')) for r in tokens]
        statuses = {p['status'] for p in parts.values()}
        coverage = dict(chain_id=chain, address=address, source='etherscan-v2', status=INCOMPLETE if INCOMPLETE in statuses else COMPLETE, parts=parts, rows=len(events), sent=sum(1 for r in txs if r['from'].lower() == address))
    elif chain in BLOCKSCOUT:
        events, part = _blockscout(net, chain, address, max_rows)
        coverage = dict(chain_id=chain, address=address, source='blockscout', status=part['status'], parts=dict(all=part), rows=len(events), sent=sum(1 for e in events if e['kind'] == 'native' and e['from'] == address))
    else:
        raise ValueError(f'no explorer for chain {chain}: use sqd windows')
    kept = [e for e in events if e['kind'] != 'native' or int(e['raw_amount']) > 0 or e['from'] == address]
    return _sequence(sorted(kept, key=lambda e: (e['timestamp'], e['transaction_hash'], e['kind']))), coverage


def position_txs(net, address):
    """Every transaction that moved a conditional token for this address: fills, splits, merges and redeems, at one call per page instead of one receipt per transaction."""
    rows, coverage = _cursor(net, 137, 'token1155tx', address, MAX_ROWS)
    return {r['hash'] for r in rows}, coverage


def presence(net, address, chain):
    """Nonce, code and balances now, from a public node. Nonce 0 with nothing held means no spend, and no listed token or native ever kept here."""
    address = address.lower()
    code, _ = net.rpc('eth_getCode', [address, 'latest'], chain, cache=False)
    nonce, _ = net.rpc('eth_getTransactionCount', [address, 'latest'], chain, cache=False)
    native, _ = net.rpc('eth_getBalance', [address, 'latest'], chain, cache=False)
    held = {}
    for contract, (name, decimals) in TOKENS.get(chain, {}).items():
        value, _ = net.rpc('eth_call', [dict(to=contract, data=selector('balanceOf(address)') + address[2:].rjust(64, '0')), 'latest'], chain, cache=False)
        if value in (None, '0x'):  # no contract at this address on this chain: nothing to hold, and not a zero balance read
            continue
        if int(value, 16):
            held[name] = int(value, 16) / 10 ** decimals
    return dict(chain_id=chain, address=address, code=len(code) > 2 and not code.startswith('0xef0100'), delegated=code.startswith('0xef0100'), nonce=int(nonce, 16), native=int(native, 16) / 1e18, tokens=held)
