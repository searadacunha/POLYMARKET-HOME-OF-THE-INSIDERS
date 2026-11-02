"""Contre-vérification : une histoire coupée à 12 pages fausse-t-elle vraiment le dépôt retenu ? Rejoue les 12 pages depuis le cache, sans réseau ni écriture dans le cache."""
import gzip, hashlib, json, urllib.parse
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
CACHES = [ROOT / 'state/http_cache', ROOT / 'collective/state/http_cache']
URL = 'https://data-api.polymarket.com/v2/activity'


def cached(full):
    key = hashlib.sha256(full.encode()).hexdigest()
    for c in CACHES:
        p = c / key[:2] / (key + '.json.gz')
        if p.exists():
            with gzip.open(p, 'rt') as f:
                return json.load(f)
    return None


def pages(wallet):
    rows, cursor, status = [], None, 'COMPLETE'
    for i in range(12):
        params = dict(user=wallet, limit=500, sort_by='TIMESTAMP', sort_direction='ASC', exclude_deposits_withdrawals='false')
        if cursor:
            params['cursor'] = cursor
        body = cached(URL + '?' + urllib.parse.urlencode(params))
        if body is None:
            return rows, f'CACHE_MISS_PAGE_{i}', i
        rows += body.get('data', [])
        cursor = (body.get('pagination') or {}).get('next_cursor')
        if not cursor:
            return rows, 'COMPLETE', i + 1
    return rows, 'CUT_12_PAGES', 12


det = [json.loads(l) for l in open(ROOT / 'controls/funding_baseline_detail.jsonl')]
e6 = json.load(open(ROOT / 'collective/derived/B_E6.json'))['per_wallet']
out = []
for r in det:
    w = r['wallet']
    rows, status, n = pages(w)
    fb = e6.get(w, {}).get('first_family_buy')
    last_ts = rows[-1]['timestamp'] if rows else None
    deps = sorted(x['timestamp'] for x in rows if x['type'] == 'DEPOSIT')
    before = [t for t in deps if fb and t <= fb]
    out.append(dict(group=r['group'], wallet=w, status=status, pages=n, rows=len(rows), last_ts=last_ts, first_family_buy=fb, reaches_first_buy=bool(fb and last_ts and last_ts >= fb), deposit_at=r['at'], picked_is_last_before=bool(before and before[-1] == r['at']), gap_days=round((fb - r['at']) / 86400, 1) if fb else None, usd=r['usd'], e6_complete=e6.get(w, {}).get('complete'), origin=r.get('origin_chain')))
Path(ROOT / 'evidence/contre_verification_20261102/coupure_par_comparateur.json').write_text(json.dumps(out, indent=0))
from collections import Counter
print(Counter((x['group'] == 'named', x['status']) for x in out))
cut = [x for x in out if x['group'] != 'named' and x['e6_complete'] is False]
print('flag E6 coupé', len(cut), 'statut replay', Counter(x['status'] for x in cut))
print('coupés qui atteignent quand même le premier achat', sum(x['reaches_first_buy'] for x in cut), 'dépôt retenu = dernier avant achat dans ce qui est lu', sum(x['picked_is_last_before'] for x in cut))
for x in sorted(cut, key=lambda x: -(x['gap_days'] or 0)):
    print(x['group'][:10], x['wallet'][:10], x['status'], 'rows', x['rows'], 'gap_j', x['gap_days'], 'usd', round(x['usd'], 2), 'atteint_1er_achat', x['reaches_first_buy'], 'origin', x['origin'])
comp = [x for x in out if x['group'] != 'named' and x['first_family_buy']]
nc = [x for x in comp if x['e6_complete'] is True]
print('complets', len(nc), 'gap>30j', sum((x['gap_days'] or 0) > 30 for x in nc), [(x['wallet'][:8], x['gap_days'], x['origin']) for x in nc if (x['gap_days'] or 0) > 30])
valid = [x for x in out if x['group'] != 'named' and x['origin'] and (x['e6_complete'] is not False or x['reaches_first_buy'])]
print('origine lue et lecture avant premier achat valide (coupés atteignant le premier achat réintégrés)', len(valid), Counter(x['group'] for x in valid))
