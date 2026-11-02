"""Offline. Every cached public answer of the earlier studies, one file at a time: any row between an address of the 11 dossiers and an address some source calls ChangeNOW, or a behavioural candidate. Whole history, not only the 90 days. Writes state/dossier_hits.csv."""
import csv, gzip, hashlib, json, re, resource, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import sources as S
ROOT = Path(__file__).resolve().parent.parent
HOME = Path.home() / 'Projects'
CACHES = {d: HOME / d / 'state' for d in ('PolySentinel-flow-trace', 'PolySentinel-investigation', 'PolySentinel-ChangeNOW-proof')}
dos = {r['address']: r for r in csv.DictReader(open(ROOT / 'state/dossier_addresses.csv'))}
cn = {r['address']: r['label'] for r in csv.DictReader(open(ROOT / 'data/attribution_sources.csv')) if r['address'].startswith('0x')}
for _, a in S.CANDIDAT:
    cn.setdefault(a, 'candidat comportemental')
dh, ch = {a[2:] for a in dos}, {a[2:] for a in cn}
rx = re.compile(rb'(?<![0-9a-f])[0-9a-f]{40}(?![0-9a-f])')


def norm(a):
    return (a or '').lower() if isinstance(a, str) else ((a or {}).get('hash') or '').lower()


def walk(v):
    stack = [v]
    while stack:
        x = stack.pop()
        if isinstance(x, list):
            stack.extend(x)
        elif isinstance(x, dict):
            f, t = norm(x.get('from')), norm(x.get('to'))
            if (f in dos and t in cn) or (f in cn and t in dos):
                yield f, t, x
            tp = x.get('topics')
            if isinstance(tp, list) and len(tp) >= 3 and all(isinstance(z, str) for z in tp[:3]):
                f, t = '0x' + tp[1][-40:].lower(), '0x' + tp[2][-40:].lower()
                if (f in dos and t in cn) or (f in cn and t in dos):
                    yield f, t, x
            stack.extend(y for y in x.values() if isinstance(y, (list, dict)))


seen = {}
n = hit = 0
for name, st in CACHES.items():
    urls = {}
    for line in open(st / 'requests.jsonl'):
        try:
            u = json.loads(line).get('url')
        except ValueError:
            continue
        if u:
            urls[hashlib.sha256(u.encode()).hexdigest()] = u
    for p in (st / 'http_cache').rglob('*.json.gz'):
        n += 1
        if n % 5000 == 0:
            print(n, 'hit', hit, 'rss', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 2**20, flush=True)
        raw = gzip.open(p, 'rb').read()
        ids = {h.decode() for h in rx.findall(raw.lower())}
        ids |= {m.decode() for m in re.findall(rb'0{24}([0-9a-f]{40})', raw.lower())}
        if not (ids & dh and ids & ch):
            continue
        hit += 1
        url = urls.get(p.name.split('.')[0], '')
        for f, t, x in walk(json.loads(raw)):
            tx = x.get('hash') or x.get('transaction_hash') or x.get('transactionHash') or x.get('tx_hash')
            if isinstance(tx, dict):
                tx = tx.get('hash')
            tok = x.get('token') if isinstance(x.get('token'), dict) else {}
            val = x.get('value') if x.get('value') is not None else (x.get('total') or {}).get('value') if isinstance(x.get('total'), dict) else x.get('data')
            key = (tx, f, t, str(val), x.get('contractAddress') or tok.get('address') or x.get('address'))
            q = dict(url=url[:200], cache=name)
            chain = re.search(r'chainid=(\d+)', url)
            seen.setdefault(key, dict(tx=tx, src=f, dst=t, raw=val, contract=key[4], symbol=x.get('tokenSymbol') or tok.get('symbol') or ('natif' if key[4] is None else ''), decimals=x.get('tokenDecimal') or tok.get('decimals') or '', ts=x.get('timeStamp') or x.get('timestamp') or x.get('blockTimestamp') or '', block=x.get('blockNumber') or x.get('block_number') or '', chain=chain.group(1) if chain else ('1' if 'eth.blockscout' in url else ''), direction='entree_dossier' if t in dos else 'sortie_dossier', dossier_address=t if t in dos else f, cases=dos[t if t in dos else f]['cases'], roles=dos[t if t in dos else f]['roles'], cn_address=f if t in dos else t, cn_label=cn[f if t in dos else t], cache=name))
out = sorted(seen.values(), key=lambda r: (str(r['cases']), str(r['ts'])))
with (ROOT / 'state/dossier_hits.csv').open('w', newline='') as fo:
    w = csv.DictWriter(fo, fieldnames=list(out[0]) if out else ['tx'])
    w.writeheader()
    w.writerows(out)
print('files', n, 'hit_files', hit, 'rows', len(out))
