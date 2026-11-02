"""Contre-vérification sans réseau : taux de base complet (5 traits, bornes), rangs E6 par dossier sur historiques complets, couverture E4 par dossier, achats rapprochés avant et après l'article. Écrit complements.json."""
import glob, gzip, itertools, json, os, time
from collections import defaultdict
from math import comb
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/contre_verification_20261102'
ART = 1792768669
D2 = 1791917460
U = lambda t: time.strftime('%m-%d %H:%M', time.gmtime(t))


def fisher(a, n1, c, n2):
    K = a + c
    return sum(comb(n1, k) * comb(n2, K - k) for k in range(a, min(K, n1) + 1)) / comb(n1 + n2, K)


det = [json.loads(l) for l in open(ROOT / 'controls/funding_baseline_detail.jsonl')]
e6 = json.load(open(ROOT / 'collective/derived/B_E6.json'))
per = e6['per_wallet']
named = [r for r in det if r['group'] == 'named']
comp = [r for r in det if r['group'] != 'named']
cut = {w for w, p in per.items() if p['complete'] is False}
usable = [r for r in comp if r.get('origin_chain') and r['wallet'] not in cut]
valid = [r for r in comp if r['wallet'] not in cut]
TR = dict(kucoin=lambda r: any('KuCoin' in str(h.get('label')) for h in r.get('hops', [])), solana=lambda r: r.get('origin_chain') == 792703809, c8a6=lambda r: str(r.get('immediate_source')).lower().startswith('0xc8a6871d'), relay=lambda r: bool(r.get('origin_chain')), pont7702=lambda r: r.get('immediate_kind') == 'EIP7702_DELEGATED_EOA')
res = dict(taux={})
for t, fn in TR.items():
    a = sum(map(fn, named))
    row = dict(nommes=a)
    for lab, pop in (('publie', comp), ('utilisables', usable), ('lecture_valide', valid)):
        c = sum(map(fn, pop))
        row[lab] = dict(k=c, n=len(pop), p=round(fisher(a, 11, c, len(pop)), 4))
    # bornes sur les 78 wallets distincts : les 48 non utilisables n'ont aucun, ou tous, le trait
    k = sum(map(fn, usable))
    row['borne_si_aucun_des_48'] = dict(k=k, n=78, p=round(fisher(a, 11, k, 78), 4))
    row['borne_si_tous_les_48'] = dict(k=k + 48, n=78, p=round(fisher(a, 11, k + 48, 78), 4))
    res['taux'][t] = row
res['controle_publie'] = {t: res['taux'][t]['publie']['k'] for t in TR}
res['utilisables_n'], res['lecture_valide_n'] = len(usable), len(valid)
res['coupes_liste'] = [dict(group=r['group'], wallet=r['wallet'], usd=round(r['usd'], 2), depot_lu=time.strftime('%Y-%m-%d', time.gmtime(r['at'])), premier_achat=time.strftime('%Y-%m-%d', time.gmtime(per[r['wallet']]['first_family_buy'])), ecart_j=round((per[r['wallet']]['first_family_buy'] - r['at']) / 86400, 1), origine=r.get('origin_chain'), lignes=per[r['wallet']]['rows']) for r in comp if r['wallet'] in cut]
hits = defaultdict(list)
for r in comp:
    for h in r.get('hops', []):
        hits[h['source']].append((r['group'], r['wallet'] in cut))
res['temoins_services'] = {a: {'n': len(v), 'coupes': sum(c for _, c in v)} for a, v in hits.items() if a and (a.startswith('0xc8a6871d') or a.startswith('BmFdpr') or a.startswith('0xee7ae85f'))}
# E6 par dossier
g = e6['groups']
uniq = sorted({w for k in ('non_surlignes', 'meme_token', 'token_oppose') for w in g[k]})
comp_ok = [w for w in uniq if per[w]['complete'] and per[w]['gap_s'] is not None]
lines = sorted({(k, w) for k in ('non_surlignes', 'meme_token', 'token_oppose') for w in g[k]})
res['E6_par_dossier'] = {}
slug = {json.load(open(f))['address'].lower(): Path(f).stem for f in glob.glob(str(ROOT / 'cases/*.json'))}
for w in g['named']:
    gap = per[w]['gap_s']
    res['E6_par_dossier'][slug[w]] = dict(gap_min=round(gap / 60, 1), complets=sum(per[x]['gap_s'] <= gap for x in comp_ok), n_complets=len(comp_ok), uniques_gap=sum(1 for x in uniq if per[x]['gap_s'] is not None and per[x]['gap_s'] <= gap), n_uniques_gap=sum(1 for x in uniq if per[x]['gap_s'] is not None))
res['E6_sans_depot_avant_achat'] = sum(1 for x in uniq if per[x]['gap_s'] is None)
sous_1h = lambda w: per[w]['gap_s'] is not None and per[w]['gap_s'] <= 3600
k_n = sum(sous_1h(w) for w in g['named'])
k_c = sum(sous_1h(w) for w in comp_ok)
complets = [w for w in uniq if per[w]['complete']]
res['E6_comparaison'] = dict(nommes=k_n, sur_20=dict(k=k_c, n=len(comp_ok), p=round(fisher(k_n, 11, k_c, len(comp_ok)), 4)), sur_21=dict(k=sum(sous_1h(w) for w in complets), n=len(complets), p=round(fisher(k_n, 11, sum(sous_1h(w) for w in complets), len(complets)), 4)), sans_ecart=[w for w in complets if per[w]['gap_s'] is None])
# Achats rapprochés, même définition que l'audit (100 $, dédoublonnage 60 s, 5 min)
act = {os.path.basename(f).split('.')[0]: [json.loads(l) for l in gzip.open(f, 'rt')] for f in glob.glob(str(ROOT / 'evidence/activity/*.jsonl.gz'))}
buys = defaultdict(lambda: defaultdict(list))
for s, a in act.items():
    for r in a:
        if r['type'] == 'TRADE' and r.get('side') == 'BUY' and float(r.get('usdc_size') or 0) >= 100:
            buys[s][(r['title'], r['outcome'])].append(r['timestamp'])


def dedupe(ts):
    out = []
    for t in sorted(ts):
        if not out or t - out[-1] > 60:
            out.append(t)
    return out


near = {}
for a, b in itertools.combinations(sorted(buys), 2):
    row = dict(avant_D2=0, D2_a_article=0, apres_article=0, detail=[])
    for tok in set(buys[a]) & set(buys[b]):
        ys = dedupe(buys[b][tok])
        for x in dedupe(buys[a][tok]):
            if any(abs(x - y) <= 300 for y in ys):
                row['avant_D2' if x < D2 else 'D2_a_article' if x < ART else 'apres_article'] += 1
                row['detail'].append((U(x), tok[0][:34]))
    if row['detail']:
        near[f'{a}|{b}'] = row
res['achats_rapproches'] = near
(OUT / 'complements.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
print(json.dumps(res['taux'], ensure_ascii=False))
print(res['controle_publie'], res['utilisables_n'], res['lecture_valide_n'])
print(json.dumps(res['E6_par_dossier'], ensure_ascii=False))
print('E6 sans dépôt', res['E6_sans_depot_avant_achat'], res['temoins_services'])
for k, v in sorted(near.items(), key=lambda kv: -len(kv[1]['detail'])):
    print(k, v['avant_D2'], v['D2_a_article'], v['apres_article'])
print(near.get('brace227|kraben006', {}).get('detail'))
