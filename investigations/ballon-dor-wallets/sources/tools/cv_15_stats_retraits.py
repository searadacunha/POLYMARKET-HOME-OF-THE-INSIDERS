"""Test exploratoire, écrit après avoir vu les données. Vitesse de retrait de 0x86544e4dfde et walletwallet8424 après le lot Kane, face aux autres comptes du lot, avec strates pour les différences mesurables.
Sans réseau : relit fenetre_lot_kane.jsonl, fenetre_vendeurs_kane.jsonl, trades_kane.json. Aucun fichier gelé touché, aucune écriture dans le registre de l'étude."""
import glob
import gzip
import itertools
import json
import os
from math import comb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'evidence/contre_verification_20261102'
DAY = 86400
T_LOT = 1793066300
A, W = '0x3ed2c452f141c291adecb97ddfc72b1650acff3d', '0x1a1ef4c65583d5c71011d7fe51e9f544e2b1cc40'
K_W, B_W = '0x84212ee459d1edaf35983bbec342b0806282d8ec', '0x873848cd27784900e193611845fc3fd2c4716d03'
CLOSE = ('REDEEM', 'MERGE')


def fisher(a, n1, c, n2):
    K = a + c
    if n2 == 0:
        return None
    return sum(comb(n1, k) * comb(n2, K - k) for k in range(a, min(K, n1) + 1)) / comb(n1 + n2, K)


def upper95(k, n):
    """Borne haute exacte unilatérale à 95 % du taux binomial."""
    if n == 0:
        return None
    lo, hi = k / n, 1.
    for _ in range(60):
        m = (lo + hi) / 2
        tail = sum(comb(n, i) * m ** i * (1 - m) ** (n - i) for i in range(k + 1))
        lo, hi = (m, hi) if tail > .05 else (lo, m)
    return round(hi, 4)


assert abs(fisher(2, 2, 1, 178) - 3 / comb(180, 2)) < 1e-12
assert abs(upper95(0, 12) - (1 - .05 ** (1 / 12))) < 1e-3


def is_close(r):
    return r['k'] in CLOSE or (r['k'] == 'TRADE' and r.get('s') == 'SELL')


def metrics(row, t_ref):
    """Tout est mesuré depuis t_ref, propre à chaque compte."""
    rows = sorted(row['rows'], key=lambda r: r['t'])
    wd = [r for r in rows if r['k'] == 'WITHDRAWAL' and r['t'] >= t_ref]
    first = wd[0] if wd else None
    until = first['t'] if first else t_ref + DAY
    return dict(user=row['user'], delay=first['t'] - t_ref if first else None, wd_usd=float(first['u'] or 0) if first else 0., wd_24h=sum(float(r['u'] or 0) for r in wd),
                close_after=sum(1 for r in rows if t_ref < r['t'] < until and is_close(r)),
                buy_1h=sum(1 for r in rows if t_ref < r['t'] <= t_ref + 3600 and r['k'] == 'TRADE' and r.get('s') == 'BUY'),
                any_1h=sum(1 for r in rows if t_ref < r['t'] <= t_ref + 3600 and r['k'] == 'TRADE'),
                last_close_gap=first['t'] - max((r['t'] for r in rows if r['t'] < first['t'] and is_close(r)), default=first['t']) if first else None,
                wd_prior_24h=sum(1 for r in rows if r['t'] < t_ref and r['k'] == 'WITHDRAWAL'))


raw = [json.loads(l) for l in open(OUT / 'fenetre_lot_kane.jsonl')]
errors = [r for r in raw if 'error' in r]
incomplete = [r for r in raw if not r.get('complete', False) and 'error' not in r]
data = {}
for r in raw:
    # lecture coupée au plafond de pages : le compte sort du dénominateur, il n'est jamais compté comme « n'a pas retiré »
    if 'error' in r or not r.get('complete'):
        continue
    m = metrics(r, r['redeem_ts'])
    m.update(amount=r['amount'], first_event=r['first_event'], age_days=round((T_LOT - r['first_event']) / DAY, 1) if r['first_event'] else None)
    data[r['user']] = m
named = [data[A], data[W]]
# 0xa8e64a3c est financé par la clé de brace227 (cv_20) : il n'est pas un comparateur indépendant
LIE = '0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5'
comp = [m for u, m in data.items() if u not in (A, W, LIE)]
res = dict(lie_exclu=LIE, lie_delai_s=data[LIE]['delay'], lus=len(raw), erreurs=len(errors), incomplets=len(incomplete), exclus=[(r['user'], round(r['amount']), len(r['rows'])) for r in incomplete], nommes={'0x86544e4dfde': data[A], 'walletwallet8424': data[W]}, n_comparateurs=len(comp))
for k, m in zip(('0x86544e4dfde', 'walletwallet8424'), named):
    assert m['delay'] and m['delay'] < 300, (k, m)

STRATES = {
    'tous': lambda m: True,
    'taille_10k_100k': lambda m: 10000 <= m['amount'] <= 100000,
    'taille_20k_50k': lambda m: 20000 <= m['amount'] <= 50000,
    'compte_30j_ou_moins': lambda m: m['age_days'] is not None and m['age_days'] <= 30,
    'compte_60j_ou_moins': lambda m: m['age_days'] is not None and m['age_days'] <= 60,
    'sans_achat_1h_apres': lambda m: m['buy_1h'] == 0,
    'sans_trade_1h_apres': lambda m: m['any_1h'] == 0,
    'retrait_sous_24h': lambda m: m['delay'] is not None,
    'kane_derniere_cloture': lambda m: m['close_after'] == 0,
    'retrait_24h_et_derniere_cloture': lambda m: m['delay'] is not None and m['close_after'] == 0,
    'retrait_50pct_sous_24h': lambda m: m['wd_24h'] >= .5 * m['amount'],
    'retrait_50pct_et_sans_trade_1h': lambda m: m['wd_24h'] >= .5 * m['amount'] and m['any_1h'] == 0,
    'recent_60j_et_retrait_24h': lambda m: m['age_days'] is not None and m['age_days'] <= 60 and m['delay'] is not None,
}
res['nommes_dans_strates'] = {s: [bool(f(n)) for n in named] for s, f in STRATES.items()}
res['strates'] = {}
for name, f in STRATES.items():
    pop = [m for m in comp if f(m)]
    row = dict(n=len(pop))
    for lim in (300, 600):
        k = sum(1 for m in pop if m['delay'] is not None and m['delay'] < lim)
        p = fisher(2, 2, k, len(pop))
        row[f'moins_{lim}s'] = dict(k=k, p=round(p, 6) if p is not None else None, p_x55=round(min(1, p * 55), 4) if p is not None else None, borne_haute_95=upper95(k, len(pop)))
    res['strates'][name] = row
# Les nommés sont-ils dans toutes les strates ? Une strate qui les exclut ne sert pas de comparaison.
res['strates_valides'] = [s for s, v in res['nommes_dans_strates'].items() if all(v)]
ancien = {x['user']: x for x in json.load(open(OUT / 'retraits_apres_lot_kane.json'))['rows']}
ecarts = [u for u, m in data.items() if u in ancien and 'first_after_s' in ancien[u] and (ancien[u]['first_after_s'] is not None and ancien[u]['first_after_s'] < 86000) != (m['delay'] is not None and m['delay'] < 86000)]
res['coherence_cv11'] = dict(comptes=len(data), ecarts_sur_retrait_sous_24h=len(ecarts), detail=[(u[:10], ancien[u]['first_after_s'], data[u]['delay']) for u in ecarts][:10])
proches = sorted(m['delay'] for m in comp if m['delay'] is not None and m['close_after'] == 0)
res['delais_profil_proche_s'] = dict(n=len(proches), minimum=proches[0], mediane=proches[len(proches) // 2], premiers=proches[:6])

# La proximité entre les deux, une fois admis que les deux sont rapides
gap = abs(data[A]['delay'] - data[W]['delay'])
res['ecart_entre_les_deux_s'] = gap
fast = [m['delay'] for m in comp if m['delay'] is not None and m['delay'] < 3600]
res['paires_comparateurs'] = dict(retrait_24h=sum(1 for m in comp if m['delay'] is not None), paires=comb(sum(1 for m in comp if m['delay'] is not None), 2), paires_ecart_inferieur=sum(1 for a, b in itertools.combinations([m['delay'] for m in comp if m['delay'] is not None], 2) if abs(a - b) <= gap), paires_toutes_deux_sous_300s=comb(sum(1 for m in comp if m['delay'] is not None and m['delay'] < 300), 2))
res['p_ecart_si_deux_delais_uniformes_0_300s'] = round(1 - (1 - gap / 300) ** 2, 3)

# Trait de groupe : délai entre la dernière clôture et le retrait principal
cases = {Path(f).stem: json.load(open(f)) for f in glob.glob(str(ROOT / 'cases/*.json'))}
act = {os.path.basename(f).split('.')[0]: [json.loads(l) for l in gzip.open(f, 'rt')] for f in glob.glob(str(ROOT / 'evidence/activity/*.jsonl.gz'))}
delai = {}
for s, c in cases.items():
    w = max(c['withdrawals'], key=lambda x: x['usd'])
    last = max((r['timestamp'] for r in act[s] if r['timestamp'] < w['at'] and (r['type'] in CLOSE or (r['type'] == 'TRADE' and r.get('side') == 'SELL'))), default=None)
    delai[s] = w['at'] - last if last else None
res['nommes_delai_cloture_retrait_s'] = delai
gaps = [m['last_close_gap'] for m in comp if m['last_close_gap'] is not None]
gaps_clean = [m['last_close_gap'] for m in comp if m['last_close_gap'] is not None and m['wd_24h'] >= .5 * m['amount']]
res['trait_de_groupe'] = {}
for lim in (300, 600):
    a = sum(1 for v in delai.values() if v is not None and v < lim)
    res['trait_de_groupe'][f'moins_{lim}s'] = dict(nommes=f'{a}/11', tous_retraits_24h=dict(k=sum(1 for g in gaps if g < lim), n=len(gaps), p=round(fisher(a, 11, sum(1 for g in gaps if g < lim), len(gaps)), 5)), retrait_50pct=dict(k=sum(1 for g in gaps_clean if g < lim), n=len(gaps_clean), p=round(fisher(a, 11, sum(1 for g in gaps_clean if g < lim), len(gaps_clean)), 5)))
    p_named = a / 11
    res['trait_de_groupe'][f'moins_{lim}s']['proba_les_deux_si_taux_nommes'] = round(p_named ** 2, 3)
res['liste_comparateurs_sous_600s'] = sorted(((m['user'][:12], round(m['amount']), m['delay'], m['age_days'], m['close_after'], m['any_1h'], round(m['wd_usd'])) for m in comp if m['delay'] is not None and m['delay'] < 600), key=lambda x: x[2])

# Vendeurs à 0,99 ou plus : même mesure pour kraben006 et brace227
vend_path = OUT / 'fenetre_vendeurs_kane.jsonl'
vend = [json.loads(l) for l in open(vend_path)] if vend_path.exists() else []
ven = {}
for r in vend:
    if 'error' in r:
        continue
    m = metrics(r, r['sale_ts'])
    m.update(usd=r['usd'], sale_ts=r['sale_ts'])
    ven[r['user']] = m
nv = {k: ven.get(w) for k, w in (('kraben006', K_W), ('brace227', B_W))}
cv = [m for u, m in ven.items() if u not in (K_W, B_W)]
res['vendeurs'] = dict(lus=len(vend), erreurs=sum('error' in r for r in vend), nommes=nv, n=len(cv))
for lim in (300, 600):
    k = sum(1 for m in cv if m['delay'] is not None and m['delay'] < lim)
    p = fisher(2, 2, k, len(cv))
    res['vendeurs'][f'moins_{lim}s'] = dict(k=k, p=round(p, 5) if p is not None else None, borne_haute_95=upper95(k, len(cv)))
cvw = [m for m in cv if m['delay'] is not None]
for lim in (300, 600):
    k = sum(1 for m in cvw if m['delay'] < lim)
    res['vendeurs'][f'retrait_24h_moins_{lim}s'] = dict(k=k, n=len(cvw), p=round(fisher(2, 2, k, len(cvw)), 5) if cvw else None)
res['vendeurs']['ecart_retraits_s'] = 166
tr = json.load(open(OUT / 'trades_kane.json'))
hi = sorted((r for r in tr['annonce'] if str(r['o']).lower() == 'yes' and r['p'] >= .99), key=lambda r: r['t'])
res['premiere_transaction_099'] = hi[0]['t'] if hi else None
yes = sorted((r for r in tr['annonce'] if str(r['o']).lower() == 'yes'), key=lambda r: r['t'])
res['prix_kane_par_10min'] = {}
for r in yes:
    res['prix_kane_par_10min'][r['t'] // 600 * 600] = round(r['p'], 3)

# 24 oct. : les achats de brace227 et kraben006 étaient-ils isolés ?
buys = {}
for s, w in (('brace227', B_W), ('kraben006', K_W)):
    buys[s] = sorted(r['timestamp'] for r in act[s] if r['type'] == 'TRADE' and r.get('side') == 'BUY' and 'Harry Kane win' in (r.get('title') or '') and float(r.get('usdc_size') or 0) >= 100 and 1792850400 <= r['timestamp'] < 1792861200)
others = {}
for r in tr['24_oct']:
    if r['s'] == 'BUY' and str(r['o']).lower() == 'yes' and r['z'] * r['p'] >= 100:
        others.setdefault(r['w'], []).append(r['t'])
rank = {}
for s, times in buys.items():
    scores = sorted(((sum(1 for x in times if any(abs(x - y) <= 300 for y in v)), w) for w, v in others.items() if w not in (B_W, K_W)), reverse=True)
    other = 'kraben006' if s == 'brace227' else 'brace227'
    own = sum(1 for x in times if any(abs(x - y) <= 300 for y in buys[other]))
    rank[s] = dict(achats_100_ou_plus=len(times), rapproches_avec_lautre=own, autres_acheteurs_taker=sum(1 for w in others if w not in (B_W, K_W)), comptes_autant_ou_plus=sum(1 for n, _ in scores if n >= own), top=[n for n, _ in scores[:8]])
res['24_oct'] = rank
res['24_oct_nommes_dans_taker'] = {s: len(others.get(w, [])) for s, w in (('brace227', B_W), ('kraben006', K_W))}

(OUT / 'stats_retraits_kane.json').write_text(json.dumps(res, indent=1, ensure_ascii=False))
tests = [dict(test=f'retrait_{lim}s_{s}', k=v[f'moins_{lim}s']['k'], n=v['n'], p=v[f'moins_{lim}s']['p']) for s, v in res['strates'].items() for lim in (300, 600)]
with (OUT / 'tests_exploratoires.jsonl').open('w') as f:
    for t in tests:
        f.write(json.dumps(t) + '\n')
print(json.dumps({k: v for k, v in res.items() if k not in ('prix_kane_par_10min',)}, indent=0, ensure_ascii=False))
print('tests écrits', len(tests))
