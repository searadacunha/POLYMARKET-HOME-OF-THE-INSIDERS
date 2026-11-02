"""Contre-vérification du taux de base, sans le code de l'audit et sans réseau. Relit controls/ et le cache HTTP, écrit evidence/contre_verification_20261102/taux_de_base.json."""
import hashlib, json, sys
from collections import Counter
from math import comb
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/contre_verification_20261102/taux_de_base.json'


def fisher(a, n1, c, n2):
    """P(X >= a), unilatéral, marges fixes."""
    K = a + c
    return sum(comb(n1, k) * comb(n2, K - k) for k in range(a, min(K, n1) + 1)) / comb(n1 + n2, K)


assert abs(fisher(3, 11, 1, 50) - .0164) < 1e-3 and fisher(1, 1, 0, 1) == .5  # valeurs de contrôle : 0,016 publié, cas à la main
det = [json.loads(l) for l in open(ROOT / 'controls/funding_baseline_detail.jsonl')]
base = {r['wallet']: r for r in map(json.loads, open(ROOT / 'controls/funding_baseline.jsonl'))}
e6 = json.load(open(ROOT / 'collective/derived/B_E6.json'))
meta = json.load(open(ROOT / 'controls/funding_baseline_meta.json'))
planned = {g: len(w) for g, w in e6['groups'].items() if g != 'named'}
planned['fraiches_recensement'] = meta['sampled']
named = [r for r in det if r['group'] == 'named']
comp = [r for r in det if r['group'] != 'named']
per = e6['per_wallet']
ku = lambda r: any('KuCoin' in str(h.get('label')) for h in r.get('hops', []))
so = lambda r: r.get('origin_chain') == 792703809
c8 = lambda r: str(r.get('immediate_source')).lower().startswith('0xc8a6871d')
rel = lambda r: bool(r.get('relay_user'))
TRAITS = dict(kucoin=ku, solana=so, c8a6=c8)
# 5 wallets figurent dans deux groupes : on compte des wallets distincts, pas des lignes
distincts = {w for g, v in e6['groups'].items() if g != 'named' for w in v}
res = dict(prevus_par_groupe=planned, lignes_prevues=sum(planned.values()), prevus_total=len(distincts) + meta['sampled'], lus=dict(Counter(r['group'] for r in comp)), n_lus=len(comp))
res['manquants'] = dict(fraiches_recensement=planned['fraiches_recensement'] - res['lus']['fraiches_recensement'], autres_groupes=len(distincts - {r['wallet'] for r in comp}))
assert sum(res['manquants'].values()) == res['prevus_total'] - res['n_lus']
res['etat_premiere_lecture'] = dict(Counter(r.get('state') for r in base.values()))


def cached_history(w):
    """Relit les pages de baseline.history depuis le cache de tools/net.py, sans réseau."""
    return None


# Coupure réelle : le dépôt retenu est-il bien le dernier avant le premier achat, ou la lecture s'est-elle arrêtée avant ?
cut = [r['wallet'] for r in comp if per.get(r['wallet'], {}).get('complete') is False]
no_origin = [r['wallet'] for r in comp if not r.get('origin_chain')]
no_wrap = [r['wallet'] for r in comp if not r.get('immediate_source')]
usable = [r for r in comp if r.get('origin_chain') and r['wallet'] not in cut]
readable = [r for r in comp if r.get('origin_chain')]
res['coupes'] = len(cut)
res['coupes_par_groupe'] = dict(Counter(next(r['group'] for r in comp if r['wallet'] == w) for w in cut))
res['sans_origine'] = len(no_origin)
res['sans_wrap'] = len(no_wrap)
res['coupes_et_sans_origine'] = len(set(cut) & set(no_origin))
res['utilisables'] = len(usable)
res['utilisables_par_groupe'] = dict(Counter(r['group'] for r in usable))
res['inutilisables_sur_prevus'] = res['prevus_total'] - len(usable)
res['decomposition_inutilisables'] = dict(jamais_lus=sum(res['manquants'].values()), lus_sans_origine=len(no_origin), lus_avec_origine_mais_coupes=len(set(cut) - set(no_origin)))
assert sum(res['decomposition_inutilisables'].values()) == res['inutilisables_sur_prevus']
res['nommes_coupes'] = [r['wallet'] for r in named if per.get(r['wallet'], {}).get('complete') is False]
fresh = [r for r in readable if r['group'] == 'fraiches_recensement']
res['traits'] = {}
for t, fn in TRAITS.items():
    a = sum(map(fn, named))
    row = dict(nommes=f'{a}/{len(named)}')
    for label, pop in (('publie', comp), ('origine_lue', readable), ('utilisables', usable), ('frais', [r for r in usable if r['group'] == 'fraiches_recensement'])):
        c = sum(map(fn, pop))
        row[label] = dict(k=c, n=len(pop), p=round(fisher(a, len(named), c, len(pop)), 4))
    res['traits'][t] = row
res['kucoin_conditionnel_solana'] = dict(nommes=f"{sum(map(ku, [r for r in named if so(r)]))}/{sum(map(so, named))}", comparateurs=f"{sum(map(ku, [r for r in comp if so(r)]))}/{sum(map(so, comp))}")
# Bonferroni sur les 3 traits lus sur une population défendable, et borne haute exacte 95 % de 0/n
n_frais = len([r for r in usable if r['group'] == 'fraiches_recensement'])
res['borne_haute_95_frais_0_sur_n'] = round(1 - .05 ** (1 / n_frais), 3) if n_frais else None
res['sensibilite_kucoin_frais'] = {str(k): round(fisher(3, 11, k, n_frais + res['manquants']['fraiches_recensement']), 4) for k in range(0, 9)}
# E6 : financement sous une heure
g = e6['groups']
rows = []
for name in ('non_surlignes', 'meme_token', 'token_oppose'):
    rows += [(name, w) for w in g[name]]
uniq = {w for _, w in rows}
under = lambda w: per[w]['gap_s'] is not None and per[w]['gap_s'] <= 3600
nam_u = sum(under(w) for w in g['named'])
res['E6'] = dict(nommes=f"{nam_u}/{len(g['named'])}", lignes=len(rows), wallets_uniques=len(uniq), lignes_coupees=sum(per[w]['complete'] is False for _, w in rows), wallets_coupes=sum(per[w]['complete'] is False for w in uniq), publie=dict(k=sum(under(w) for _, w in rows), n=len(rows)), lignes_completes=dict(k=sum(under(w) for _, w in rows if per[w]['complete']), n=sum(per[w]['complete'] is True for _, w in rows)), uniques=dict(k=sum(under(w) for w in uniq), n=len(uniq)), uniques_complets=dict(k=sum(under(w) for w in uniq if per[w]['complete']), n=sum(per[w]['complete'] is True for w in uniq)), nommes_coupes=sum(per[w]['complete'] is False for w in g['named']))
for k in ('publie', 'lignes_completes', 'uniques', 'uniques_complets'):
    res['E6'][k]['p'] = round(fisher(nam_u, len(g['named']), res['E6'][k]['k'], res['E6'][k]['n']), 4)
OUT.write_text(json.dumps(res, indent=1, ensure_ascii=False))
print(json.dumps(res, indent=1, ensure_ascii=False))
