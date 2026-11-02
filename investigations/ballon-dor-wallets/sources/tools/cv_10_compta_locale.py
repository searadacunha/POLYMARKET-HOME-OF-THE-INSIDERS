"""Contre-vérification sans réseau : relations, retraits, dépôts, paires, sceau et gel, calendrier d'achat, D2. Écrit evidence/contre_verification_20261102/compta_locale.json."""
import glob, gzip, hashlib, itertools, json, os, time
from collections import Counter, defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
U = lambda t: time.strftime('%m-%d %H:%M:%S', time.gmtime(t))
cases = {Path(f).stem: json.load(open(f)) for f in sorted(glob.glob(str(ROOT / 'cases/*.json')))}
act = {os.path.basename(f).split('.')[0]: [json.loads(l) for l in gzip.open(f, 'rt')] for f in glob.glob(str(ROOT / 'evidence/activity/*.jsonl.gz'))}
res = {}
rel = [json.loads(l) for l in open(ROOT / 'graphs/relations.jsonl')]
res['relations'] = dict(n=len(rel), ids=len({r['id'] for r in rel}), cat=dict(Counter(r['category'] for r in rel)), by_case=dict(Counter(r['case'] for r in rel)), in_cases=sum(len(c['chain_relations']) for c in cases.values()))
res['retraits'] = dict(n=sum(len(c['withdrawals']) for c in cases.values()), usd=round(sum(w['usd'] for c in cases.values() for w in c['withdrawals']), 2))
res['depots'] = dict(n=sum(len(c['deposits']) for c in cases.values()), usd=round(sum(w['usd'] for c in cases.values() for w in c['deposits']), 2))
# Égalité activité (source) contre dossier
chk = {}
for s, c in cases.items():
    a = act[s]
    chk[s] = dict(lignes=len(a) == c['rows'], dep=round(sum(r['usdc_size'] for r in a if r['type'] == 'DEPOSIT'), 2) == round(sum(d['usd'] for d in c['deposits']), 2), ret=round(sum(r['usdc_size'] for r in a if r['type'] == 'WITHDRAWAL'), 2) == round(sum(d['usd'] for d in c['withdrawals']), 2), complete=c['history_complete'])
res['activite_contre_dossier'] = chk
closed = {}
for s, c in cases.items():
    d, w = sum(x['usd'] for x in c['deposits']), sum(x['usd'] for x in c['withdrawals'])
    closed[s] = dict(net=round(w - d, 2), account=c['account'].get('closed', c['account'].get('settled')), acc=c['account'])
res['net_11'] = round(sum(v['net'] for v in closed.values()), 2)
res['net'] = {s: v['net'] for s, v in closed.items()}
res['account_keys'] = list(next(iter(cases.values()))['account'].keys())
res['account_sample'] = {s: {k: v for k, v in c['account'].items() if not isinstance(v, (list, dict))} for s, c in cases.items()}
res['paires'] = comb = 11 * 10 // 2
links = json.load(open(ROOT / 'graphs/links_classified.json'))
res['links_keys'] = list(links.keys()) if isinstance(links, dict) else None
shared = links.get('shared') or links.get('rows') or links
pairs = set()
items = shared if isinstance(shared, list) else list(shared.values())
for x in items:
    if isinstance(x, dict) and x.get('cases'):
        for a, b in itertools.combinations(sorted(x['cases']), 2):
            pairs.add((a, b))
res['paires_naives'] = links['naive_pair_count']
# Gel
lock = json.load(open(ROOT / 'collective/PROTOCOL.lock'))
bad = [f for f, h in lock['fichiers'].items() if hashlib.sha256((ROOT / 'collective' / f).read_bytes()).hexdigest() != h]
res['gel'] = dict(fichiers=len(lock['fichiers']), differents=bad)
seal = json.load(open(ROOT / 'collective/derived/A_seal.json'))
res['sceau_cles'] = list(seal.keys())[:6]
s_files = seal['sha256']
res['sceau'] = dict(n=len(s_files), differents=[f for f, h in s_files.items() if hashlib.sha256((ROOT / 'collective' / f).read_bytes()).hexdigest() != h], t=seal['sealed_at'])
res['repro_e4v2'] = json.load(open(ROOT / 'collective/audit/REPRO_E4V2.json'))
res['e4_hash_fichiers'] = [hashlib.sha256((ROOT / f'collective/audit/e4v2_hash{i}.json').read_bytes()).hexdigest()[:16] for i in (1, 2, 3)]
res['e4_stored_sha'] = hashlib.sha256((ROOT / 'collective/derived/A_E4_v2.json').read_bytes()).hexdigest()
# Achats de Thin le 13 oct., et D2
thin = sorted((r for r in act['thin'] if r['type'] == 'TRADE' and r.get('side') == 'BUY' and 1791849600 <= r['timestamp'] < 1791936000), key=lambda r: r['timestamp'])
res['thin_13oct'] = [(U(r['timestamp']), round(r['usdc_size'], 2), r['title'][:30], r['outcome'], r['transaction_hash'][:12]) for r in thin]
# Achats Kane par jour
K = defaultdict(lambda: defaultdict(float))
for s, rows in act.items():
    for r in rows:
        if r['type'] == 'TRADE' and r.get('side') == 'BUY' and 'Harry Kane win' in (r.get('title') or '') and r.get('outcome') == 'Yes':
            K[time.strftime('%m-%d', time.gmtime(r['timestamp']))][s] += r['usdc_size']
res['kane_par_jour'] = {d: {s: round(v, 2) for s, v in sorted(x.items())} for d, x in sorted(K.items())}
# Délais retrait principal après dernière sortie de position
main = {}
for s, c in cases.items():
    w = max(c['withdrawals'], key=lambda x: x['usd'])
    prior = [r for r in act[s] if r['timestamp'] < w['at'] and (r['type'] == 'REDEEM' or (r['type'] == 'TRADE' and r.get('side') == 'SELL'))]
    last = max(prior, key=lambda r: r['timestamp']) if prior else None
    main[s] = dict(at=w['at'], utc=U(w['at']), usd=round(w['usd'], 2), delai_min=round((w['at'] - last['timestamp']) / 60, 1) if last else None, dernier=last and (last['type'], last['title'][:40]))
res['retrait_principal'] = main
res['sous_10_min'] = sum(1 for v in main.values() if v['delai_min'] is not None and v['delai_min'] < 10)
ordre = sorted(main.items(), key=lambda kv: kv[1]['at'])
res['ecarts_consecutifs_min'] = [(a[0], b[0], round((b[1]['at'] - a[1]['at']) / 60, 1)) for a, b in zip(ordre, ordre[1:])]
(ROOT / 'evidence/contre_verification_20261102/compta_locale.json').write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str))
print(json.dumps({k: v for k, v in res.items() if k not in ('account_sample',)}, indent=0, ensure_ascii=False, default=str)[:9000])
for s, v in res['account_sample'].items():
    print(s, v)
