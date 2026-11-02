"""Etherscan v2 reads on one address, through net.get (cache, ledger with SHA-256, guards). An explorer refusal raises, it never becomes an empty list."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net
URL = 'https://api.etherscan.io/v2/api'


def rows(action, address, chain=1, start=0, end=999999999, page=1, offset=1000, sort='asc', contract=None):
    p = dict(chainid=chain, module='account', action=action, address=address, page=page, offset=offset, sort=sort, startblock=start, endblock=end)
    if contract:
        p['contractaddress'] = contract
    d = net.get(URL, p, pause=.6, secret=dict(apikey=net._key_from_env()))
    msg = str(d.get('message', ''))
    if d.get('status') == '1':
        return d['result']
    if 'No transactions' in msg or 'No records' in msg or 'No internal' in msg or 'No token' in msg:
        return []
    raise RuntimeError(f'etherscan {chain} {action} {address}: {msg} {str(d.get("result"))[:120]}')


def window(action, address, chain=1, start=0, end=999999999, contract=None, max_pages=10):
    """All rows in a block window, page by page. Second value False when the 10-page explorer cap was reached."""
    out = []
    for page in range(1, max_pages + 1):
        batch = rows(action, address, chain, start, end, page, 1000, 'asc', contract)
        out += batch
        if len(batch) < 1000:
            return out, True
    return out, False
