"""Etherscan v2 reads through net.get. A refusal raises, it never becomes an empty list.
Measured 02/11: the same query flips between 'No transactions found' and the real rows from one call to the next (polygon, address with 196 rows, 4 empties in 8 calls). An empty answer is therefore retried under varied parameters and only kept after EMPTY_TRIES agree."""
import hashlib
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net
URL = 'https://api.etherscan.io/v2/api'
EMPTY_TRIES = {'txlist': 6, 'tokentx': 4, 'txlistinternal': 3}  # txlist also has a node check, the nonce


def in_range(rows_, start, end):
    return [r for r in rows_ if start <= int(r['blockNumber']) <= end]


def rows(action, address, chain=1, start=0, end=99999999, page=1, offset=1000, sort='asc', contract=None, pause=1.0, store=True):
    address = address.lower()
    p = dict(chainid=chain, module='account', action=action, address=address, page=page, offset=offset, sort=sort, startblock=start, endblock=end)
    if contract:
        p['contractaddress'] = contract
    marker = hashlib.sha256(('confirmed_empty:' + str(sorted(p.items()))).encode()).hexdigest()
    hit, _ = net._load(marker)
    if hit:
        return []
    variants = [p, {k: v for k, v in p.items() if k != 'endblock'}, dict(p, endblock=end + 1), {k: v for k, v in p.items() if k != 'sort'}, dict(p, endblock=end + 2), dict(p, endblock=end + 3)]
    for i, v in enumerate(variants[:EMPTY_TRIES.get(action, 4)]):
        if i:
            time.sleep(pause)
        d = net.get(URL, v, pause=pause, secret=dict(apikey=net._key_from_env()), store=store)
        msg = str(d.get('message', ''))
        if d.get('status') == '1':
            kept = in_range(d['result'], start, end)  # a variant may widen the range: its extra rows are real but outside the request
            if i and kept:
                net.note(kind='false_empty', action=action, chain=chain, address=address, tries=i, rows=len(kept))
            return kept
        if not (msg.startswith('No ') or 'No transactions' in msg):
            raise RuntimeError(f'etherscan {chain} {action} {address}: {msg} {str(d.get("result"))[:120]}')
    net._store(marker, dict(confirmed_empty=True, tries=EMPTY_TRIES.get(action, 4)))
    return []
