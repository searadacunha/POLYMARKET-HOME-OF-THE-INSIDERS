"""Complete address histories from Etherscan v2 and normalised value edges. Only etherscan reads and pure functions."""
import sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import es
import net

PAGE = 1000
NATIVE = {1: 'ETH', 137: 'POL', 42161: 'ETH', 10: 'ETH', 8453: 'ETH', 56: 'BNB'}


def row_key(action, r):
    """Unique identity of an explorer row: a tx can hold many token transfers and many internal calls."""
    if action == 'txlist':
        return r['hash']
    if action == 'txlistinternal':
        return (r['hash'], r.get('traceId', ''), r['from'], r['to'], r['value'])
    return (r['hash'], r.get('logIndex', ''), r['contractAddress'], r['from'], r['to'], r.get('value', r.get('tokenID', '')))


def walk_pages(fetch, action, start, end):
    """Walk an ascending explorer list past its page cap: restart at the last block read, drop the overlap. A block fuller than one page raises instead of losing rows."""
    seen, out, cursor = set(), [], start
    while True:
        batch = fetch(cursor, end)
        for r in batch:
            k = row_key(action, r)
            if k not in seen:
                seen.add(k)
                out.append(r)
        if len(batch) < PAGE:
            return out
        last = int(batch[-1]['blockNumber'])
        if last == cursor:
            raise RuntimeError(f'block {last} holds a full page of {action}, rows would be lost')
        cursor = last


def history(address, chain=137, action='txlist', start=0, end=99999999, cap=None):
    """All rows of one list for an address between two blocks. cap stops early, and the caller gets truncated=True."""
    fetched = []

    def fetch(a, b):
        rows = es.rows(action, address, chain=chain, start=a, end=b, offset=PAGE, sort='asc')
        fetched.append(len(rows))
        if cap and sum(fetched) >= cap:
            raise _Cap(rows)
        return rows
    try:
        return walk_pages(fetch, action, start, end), False
    except _Cap:
        return _partial(address, chain, action, start, end, cap), True


class _Cap(Exception):
    pass


def _partial(address, chain, action, start, end, cap):
    seen, out, cursor = set(), [], start
    while len(out) < cap:
        batch = es.rows(action, address, chain=chain, start=cursor, end=end, offset=PAGE, sort='asc')
        for r in batch:
            k = row_key(action, r)
            if k not in seen:
                seen.add(k)
                out.append(r)
        if len(batch) < PAGE:
            break
        cursor = int(batch[-1]['blockNumber'])
    return out


def block_at(ts, chain=137, closest='before'):
    d = net.get(es.URL, dict(chainid=chain, module='block', action='getblocknobytime', timestamp=int(ts), closest=closest), pause=1.0, secret=dict(apikey=net._key_from_env()))
    if d.get('status') != '1':
        raise RuntimeError(f'block_at {chain} {ts}: {d}')
    return int(d['result'])


def utc(ts):
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime('%Y-%m-%d %H:%M:%S')


def ts_of(s):
    return int(datetime.strptime(s, '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc).timestamp())


def fee(r):
    """Transaction fee in wei, empty for internal rows, which the explorer gives without gas price."""
    return str(int(r['gasUsed']) * int(r['gasPrice'])) if r.get('gasPrice') and r.get('gasUsed') else ''


def native_edges(rows, chain, kind='native'):
    """Successful value-bearing native moves. Raw wei stays a string."""
    out = []
    for r in rows:
        if r.get('isError', '0') != '0' or int(r['value']) == 0 or not r.get('to'):
            continue
        out.append(dict(chain=chain, kind=kind, tx=r['hash'], block=int(r['blockNumber']), ts=int(r['timeStamp']), src=r['from'].lower(), dst=r['to'].lower(), token='', symbol=NATIVE[chain], decimals=18, raw=r['value'], log=r.get('traceId', ''), fee_wei=fee(r)))
    return out


def token_edges(rows, chain):
    out = []
    for r in rows:
        if int(r['value']) == 0:
            continue
        out.append(dict(chain=chain, kind='erc20', tx=r['hash'], block=int(r['blockNumber']), ts=int(r['timeStamp']), src=r['from'].lower(), dst=r['to'].lower(), token=r['contractAddress'].lower(), symbol=r['tokenSymbol'], decimals=int(r['tokenDecimal']), raw=r['value'], log=r.get('logIndex', ''), fee_wei=fee(r)))
    return out


def all_edges(address, chain=137, start=0, end=99999999, cap=None):
    """Native, internal and token edges of one address, plus whether any list was cut."""
    edges, truncated = [], False
    for action, conv in (('txlist', lambda rows: native_edges(rows, chain)), ('txlistinternal', lambda rows: native_edges(rows, chain, 'internal')), ('tokentx', lambda rows: token_edges(rows, chain))):
        rows, cut = history(address, chain, action, start, end, cap)
        truncated |= cut
        edges += conv(rows)
    return edges, truncated


def amount(e):
    return int(e['raw']) / 10 ** e['decimals']
