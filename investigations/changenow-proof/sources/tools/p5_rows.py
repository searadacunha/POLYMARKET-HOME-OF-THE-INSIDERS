"""Local only. All cached history rows of the study addresses, normalised and deduplicated, plus what was read and what was not. Streams one file at a time."""
import csv, gzip, hashlib, json, re, urllib.parse
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
STATES = (Path.home() / 'Projects/PolySentinel-flow-trace/state', Path.home() / 'Projects/PolySentinel-investigation/state')
study = {r['address'] for r in csv.DictReader(open(ROOT / 'state/study_addresses.csv'))}
EXTRA = {'0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23', '0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d', '0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5', '0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b'}  # full forms copied from flow-trace and investigation reports


def parse(url):
    u = urllib.parse.urlsplit(url)
    q = urllib.parse.parse_qs(u.query)
    if 'etherscan' in (u.hostname or '') and q.get('module') == ['account'] and 'address' in q and q.get('action', [''])[0] in ('txlist', 'txlistinternal', 'tokentx'):
        return q['address'][0].lower(), int(q.get('chainid', ['0'])[0]), q['action'][0], int(q.get('page', ['1'])[0]), q.get('sort', ['asc'])[0]
    m = re.match(r'/api/v2/addresses/(0x[0-9a-fA-F]{40})/(transactions|token-transfers|internal-transactions)', u.path)
    if m:
        chain = {'eth.blockscout.com': 1, 'explorer.optimism.io': 10, 'base.blockscout.com': 8453}.get(u.hostname, 0)
        return m.group(1).lower(), chain, m.group(2), 0, 'blockscout'
    return None


seen, cov, n = set(), defaultdict(lambda: dict(rows=0, full_pages=0)), Counter()
out = gzip.open(ROOT / 'state/study_rows.jsonl.gz', 'wt')
for state in STATES:
    with open(state / 'requests.jsonl') as f:
        urls = {json.loads(l).get('url') for l in f if '"url"' in l}
    for url in filter(None, urls):
        p = parse(url)
        if not p or (p[0] not in study and p[0] not in EXTRA):
            continue
        key = hashlib.sha256(url.encode()).hexdigest()
        path = state / 'http_cache' / key[:2] / (key + '.json.gz')
        if not path.exists():
            n['missing_file'] += 1
            continue
        with gzip.open(path, 'rt') as g:
            v = json.load(g)
        items = v.get('result') if isinstance(v, dict) and 'result' in v else (v.get('items') if isinstance(v, dict) else None)
        if not isinstance(items, list):
            n['not_a_list'] += 1
            continue
        c = cov[(p[0], p[1], p[2], state.parent.name)]
        c['rows'] += len(items)
        c['full_pages'] += len(items) >= 1000
        for x in items:
            f_, t_ = x.get('from'), x.get('to')
            f_ = (f_ if isinstance(f_, str) else (f_ or {}).get('hash') or '').lower()
            t_ = (t_ if isinstance(t_, str) else (t_ or {}).get('hash') or '').lower()
            tok = x.get('token') if isinstance(x.get('token'), dict) else {}
            total = x.get('total') if isinstance(x.get('total'), dict) else {}
            r = dict(chain=p[1], kind={'txlist': 'native', 'transactions': 'native', 'txlistinternal': 'internal', 'internal-transactions': 'internal', 'tokentx': 'erc20', 'token-transfers': 'erc20'}[p[2]], tx=x.get('hash') or x.get('transaction_hash'), block=x.get('blockNumber') or x.get('block_number') or x.get('block'), ts=x.get('timeStamp') or x.get('timestamp'), src=f_, dst=t_, raw=str(x.get('value') if x.get('value') is not None else total.get('value')), token=x.get('tokenSymbol') or tok.get('symbol'), decimals=x.get('tokenDecimal') or tok.get('decimals') or total.get('decimals'), contract=(x.get('contractAddress') or tok.get('address') or tok.get('address_hash') or '').lower() or None, err=x.get('isError'), log=x.get('logIndex') or x.get('log_index'), trace=x.get('traceId'))
            k = (r['chain'], r['kind'], r['tx'], r['src'], r['dst'], r['raw'], r['contract'], r['log'], r['trace'])
            if k in seen:
                n['dup'] += 1
                continue
            seen.add(k)
            out.write(json.dumps(r) + '\n')
            n['rows'] += 1
out.close()
with (ROOT / 'state/history_coverage.csv').open('w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['address', 'chain_id', 'action', 'cache', 'rows', 'full_pages_1000'])
    for k, c in sorted(cov.items(), key=str):
        w.writerow([*k, c['rows'], c['full_pages']])
print(n, 'study', len(study), 'addresses with history', len({k[0] for k in cov}))
print(Counter(k[1] for k in cov))
print('no history at all:', sorted(a for a in study if a not in {k[0] for k in cov} )[:60])
print('capped:', [(k[0][:10], k[1], k[2], c['rows']) for k, c in cov.items() if c['full_pages']][:40])
