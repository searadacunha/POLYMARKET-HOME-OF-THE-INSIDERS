"""Recoupe, sans réseau, les résultats finaux de flow-trace avec les lectures de l'enquête, avant de les citer. Lit son dossier sans y écrire. Corrige aussi le compte des comparateurs : 78 wallets distincts, pas 83 lignes."""
import glob, json
from collections import Counter
from math import comb
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
FT = Path.home() / 'Projects/PolySentinel-flow-trace'
OUT = ROOT / 'evidence/contre_verification_20261102/recoupe_flow_trace.json'


def fisher(a, n1, c, n2):
    K = a + c
    return sum(comb(n1, k) * comb(n2, K - k) for k in range(a, min(K, n1) + 1)) / comb(n1 + n2, K)


res = {}
c = json.load(open(FT / 'state/compare_rates.json'))
res['p_recalcules'] = []
for t in c['traits']:
    a, n = t['named']
    pa = fisher(a, n, t['all'][0], t['all'][1])
    pf = fisher(a, n, t['fresh'][0], t['fresh'][1])
    res['p_recalcules'].append(dict(trait=t['trait'], nommes=t['named'], tous=t['all'], frais=t['fresh'], p_tous=round(pa, 4), p_frais=round(pf, 4), egal=abs(pa - t['p_all']) < 1e-9 and abs(pf - t['p_fresh']) < 1e-9))
res['liens'] = dict(nommes=c['named_links']['direct'], temoins=c['comparator_links'], frais=c['fresh_links'])
# Comparaison des deux lecteurs sur les mêmes wallets
det = {r['wallet']: r for r in map(json.loads, open(ROOT / 'controls/funding_baseline_detail.jsonl')) if r['group'] != 'named'}
e6 = json.load(open(ROOT / 'collective/derived/B_E6.json'))
cut = {w for w, p in e6['per_wallet'].items() if p['complete'] is False}
ft = {}
for l in open(FT / 'state/comparators.jsonl'):
    r = json.loads(l)
    ft.setdefault(r.get('wallet'), r)
res['ft_champs'] = sorted(next(iter(ft.values())).keys())
print('champs flow-trace', res['ft_champs'])
keys = res['ft_champs']
orig = next((k for k in keys if 'origin' in k), None)
src = next((k for k in keys if 'immediate' in k or 'source' == k or 'wrap' in k), None)
acc = dict(communs=0, origine_egale=0, origine_comparee=0, source_egale=0, source_comparee=0, ecarts=[])
for w, m in det.items():
    f = ft.get(w)
    if not f or w in cut:
        continue
    acc['communs'] += 1
    if orig and m.get('origin_chain') and f.get(orig):
        acc['origine_comparee'] += 1
        same = str(m['origin_chain']) == str(f[orig])
        acc['origine_egale'] += same
        if not same:
            acc['ecarts'].append((w[:10], m['origin_chain'], f[orig]))
    if src and m.get('immediate_source') and f.get(src):
        acc['source_comparee'] += 1
        acc['source_egale'] += str(m['immediate_source']).lower() == str(f[src]).lower()
res['deux_lecteurs'] = acc
# Portefeuilles personnels
p = json.load(open(FT / 'state/personal_wallets.json'))
act = [x for x in p if x.get('activity_rows')]
res['wallets'] = dict(lignes=len(p), adresses=len({x['address'] for x in p}), formes=dict(Counter(x['shape'] for x in p)), actifs=[(x['wallet'], x['address'], x['shape'], x['activity_rows'], x['types'], x.get('first'), x.get('last')) for x in act], has_more=sum(bool(x.get('has_more')) for x in p))
# BSC
b = json.load(open(FT / 'state/bsc_0xc852b0938f5ad79b640d105ed11c14499454af26.json'))
blob = ' '.join(open(f).read().lower() for f in glob.glob(str(ROOT / 'cases/*.json')))
res['bsc'] = dict(lues=b['read'], complete=b['complete'], premiere=b['first'], derniere=b['last'], nonce=b['nonce_now'], anciennes=b['older_nonces_not_enumerated'], vers=[(t['utc'], t['nonce'], t['to'], t['value_bnb'], t.get('to_label'), t['to'].lower() in blob) for t in b['txs']])
# Étiquettes citées
t = json.load(open(FT / 'evidence/blockscout_tags.json'))
name = lambda a: [x['name'] for x in next(v for k, v in t.items() if k.startswith(a)) if x.get('type') == 'name'] if isinstance(next(v for k, v in t.items() if k.startswith(a)), list) else next(v for k, v in t.items() if k.startswith(a))
res['etiquettes'] = {a: str(name(a))[:90] for a in ('0xee7ae85f', '0xf7c8da79', '0x8894e0a0', '0xb43c1981', '0xeba88149', '0xdd3d72c5', '0x3f3ee0a9')}
txt = (FT / 'reports/FUNDING_FORENSICS_FINAL.md').read_text() + (FT / 'reports/COMMON_FUNDERS.md').read_text()
import re
res['c8a6'] = sorted({m.group(0)[:110] for m in re.finditer(r'[^\n|]*0xc8a6[^\n|]*', txt)})[:4]
res['vault'] = sorted({m.group(0)[:110] for m in re.finditer(r'[^\n|]*VaultDepositooor[^\n|]*', txt)})[:3]
# Compte corrigé
lus = set(det)
uniq = {w for k in ('non_surlignes', 'meme_token', 'token_oppose') for w in e6['groups'][k]}
meta = json.load(open(ROOT / 'controls/funding_baseline_meta.json'))
res['compte'] = dict(lignes_prevues=sum(len(e6['groups'][k]) for k in ('non_surlignes', 'meme_token', 'token_oppose')) + meta['sampled'], wallets_distincts=len(uniq) + meta['sampled'], lus=len(lus), jamais_lus=len(uniq) + meta['sampled'] - len(lus), e6_non_lus=len(uniq - lus))
us = [r for r in det.values() if r.get('origin_chain') and r['wallet'] not in cut]
res['compte']['utilisables'] = len(us)
res['compte']['inutilisables'] = res['compte']['wallets_distincts'] - len(us)
res['compte']['sans_origine'] = sum(1 for r in det.values() if not r.get('origin_chain'))
res['compte']['origine_coupes'] = sum(1 for r in det.values() if r.get('origin_chain') and r['wallet'] in cut)
assert res['compte']['jamais_lus'] + res['compte']['sans_origine'] + res['compte']['origine_coupes'] == res['compte']['inutilisables']
n = res['compte']['inutilisables']
res['bornes_avant_relecture'] = {k: dict(sans=round(fisher(a, 11, x, 78), 4), tous=round(fisher(a, 11, x + n, 78), 4)) for k, a, x in (('kucoin', 3, 1), ('solana', 3, 2), ('c8a6', 5, 5))}
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
print(json.dumps({k: v for k, v in res.items() if k != 'ft_champs'}, indent=0, ensure_ascii=False))
