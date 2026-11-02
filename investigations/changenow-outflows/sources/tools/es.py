"""Etherscan v2 reads through net.get. A refusal raises, it never becomes an empty list."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import net
URL = 'https://api.etherscan.io/v2/api'


def rows(action, address, chain=1, start=0, end=999999999, page=1, offset=1000, sort='asc', contract=None, pause=.4, store=True):
    p = dict(chainid=chain, module='account', action=action, address=address, page=page, offset=offset, sort=sort, startblock=start, endblock=end)
    if contract:
        p['contractaddress'] = contract
    d = net.get(URL, p, pause=pause, secret=dict(apikey=net._key_from_env()), store=store)
    msg = str(d.get('message', ''))
    if d.get('status') == '1':
        return d['result']
    if msg.startswith('No ') or 'No transactions' in msg:
        return []
    raise RuntimeError(f'etherscan {chain} {action} {address}: {msg} {str(d.get("result"))[:120]}')
