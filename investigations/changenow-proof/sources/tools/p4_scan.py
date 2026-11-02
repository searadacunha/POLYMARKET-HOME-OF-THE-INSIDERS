"""Local only. Every cached public answer of the two prior studies, streamed one file at a time: any row touching an address some source calls ChangeNOW. Writes state/scan_rows.jsonl. Files are matched on bytes first, so a file with no hit is never parsed."""
import csv, gzip, hashlib, json, re, resource, sys, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
CACHES = {'flow-trace': Path.home() / 'Projects/PolySentinel-flow-trace/state', 'investigation': Path.home() / 'Projects/PolySentinel-investigation/state'}
RSS_CAP = 700 * 1024 * 1024  # macOS ru_maxrss is in bytes; stop before pressing on swap
uni = {}
for r in csv.DictReader(open(ROOT / 'state/universe_raw.csv')):
    uni.setdefault(r['address'].lower() if r['address'].startswith('0x') else r['address'], set()).add(r['name'])
hexes = {a[2:] for a in uni if a.startswith('0x')}
others = {a for a in uni if not a.startswith('0x')}
print('universe', len(uni), 'evm', len(hexes), 'other', len(others))
rx40 = re.compile(rb'(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])')
rxpad = re.compile(rb'0{24}([0-9a-f]{40})')


def url_map(state):
    out = {}
    with open(state / 'requests.jsonl') as f:
        for line in f:
            try:
                u = json.loads(line).get('url')
            except ValueError:
                continue
            if u:
                out[hashlib.sha256(u.encode()).hexdigest()] = u
    return out


def chain_of(url):
    if not url:
        return None
    q = urllib.parse.parse_qs(urllib.parse.urlsplit(url).query)
    if 'chainid' in q:
        return int(q['chainid'][0])
    host = urllib.parse.urlsplit(url).hostname or ''
    return {'eth.blockscout.com': 1, 'explorer.optimism.io': 10, 'base.blockscout.com': 8453, 'polygon.blockscout.com': 137}.get(host, host)


def rows_of(value, url, hits):
    """Yield normalised rows from Etherscan lists, Blockscout items, RPC logs and receipts. Anything else yields a raw marker, so nothing is silently dropped."""
    def norm(a):
        return (a or '').lower() if isinstance(a, str) else ((a or {}).get('hash') or '').lower()
    stack = [value]
    found = False
    while stack:
        x = stack.pop()
        if isinstance(x, list):
            stack.extend(x)
        elif isinstance(x, dict):
            f, t = norm(x.get('from')), norm(x.get('to'))
            if f[2:] in hits or t[2:] in hits:
                found = True
                tok = x.get('token') if isinstance(x.get('token'), dict) else {}
                total = x.get('total') if isinstance(x.get('total'), dict) else {}
                yield dict(src=f, dst=t, tx=x.get('hash') or x.get('transaction_hash') or x.get('transactionHash') or x.get('tx_hash'), block=x.get('blockNumber') or x.get('block_number') or x.get('block'), ts=x.get('timeStamp') or x.get('timestamp'), raw=x.get('value') if x.get('value') is not None else total.get('value'), token=x.get('tokenSymbol') or tok.get('symbol'), decimals=x.get('tokenDecimal') or tok.get('decimals') or total.get('decimals'), contract=x.get('contractAddress') or tok.get('address') or tok.get('address_hash'), shape='row')
            topics = x.get('topics')
            if isinstance(topics, list) and any(isinstance(z, str) and z[-40:] in hits for z in topics):
                found = True
                yield dict(src='0x' + topics[1][-40:] if len(topics) > 1 else None, dst='0x' + topics[2][-40:] if len(topics) > 2 else None, tx=x.get('transactionHash'), block=x.get('blockNumber'), ts=x.get('blockTimestamp'), raw=x.get('data'), token=None, decimals=None, contract=x.get('address'), shape='log', topic0=topics[0] if topics else None)
            stack.extend(v for v in x.values() if isinstance(v, (list, dict)))
    if not found:
        yield dict(src=None, dst=None, tx=None, shape='text_only')


out = (ROOT / 'state/scan_rows.jsonl').open('w')
stats = dict(files=0, hit_files=0, rows=0, unreadable=0)
for name, state in CACHES.items():
    urls = url_map(state)
    for path in (state / 'http_cache').rglob('*.json.gz'):
        stats['files'] += 1
        if stats['files'] % 2000 == 0:
            rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            print(stats, 'rss_mb', rss // 1048576, flush=True)
            if rss > RSS_CAP:
                raise SystemExit('rss cap reached, stop: nothing lost, rerun in smaller parts')
        try:
            raw = gzip.open(path, 'rb').read()
        except OSError:
            stats['unreadable'] += 1
            continue
        low = raw.lower()
        hits = {h.decode() for h in rx40.findall(low)} & hexes
        hits |= {h.decode() for h in rxpad.findall(low)} & hexes
        text_other = {o for o in others if o.encode() in raw}
        if not hits and not text_other:
            continue
        stats['hit_files'] += 1
        url = urls.get(path.name.split('.')[0])
        try:
            value = json.loads(raw)
        except ValueError:
            stats['unreadable'] += 1
            continue
        for row in rows_of(value, url, hits):
            row.update(cache=name, file=path.name[:16], url=(url or '')[:220], chain=chain_of(url), hits=sorted('0x' + h for h in hits) + sorted(text_other))
            out.write(json.dumps(row) + '\n')
            stats['rows'] += 1
        del value
print('final', stats)
