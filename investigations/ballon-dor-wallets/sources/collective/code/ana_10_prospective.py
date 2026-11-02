"""Part A. E1, E1G, E2, E3, placebos. No name, no resolution, no account list is read here."""
import gzip
import json
import os
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import rows as R
import signals as K
from registre import enregistrer

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
E = Path(ETUDE)
UTC = lambda t: time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(t))
SEED = 20261101
AGES = {}
with gzip.open(E / 'data/ages.jsonl.gz', 'rt') as f:
    for line in f:
        a = json.loads(line)
        if 'first_ts' in a:
            AGES[a['wallet']] = a['first_ts']
ALL_FAM = list(R.family())
CTL = list(R.controls())
cat = R.catalog()
family_tokens = {r[2]: r[0] for r in ALL_FAM}
for tok, (event, _, _) in cat.items():
    if event in R.MEN:
        family_tokens.setdefault(tok, 'M')
    elif event in R.WOM:
        family_tokens.setdefault(tok, 'W')
CEN = list(R.census(family_tokens))
UNIV = {'M': [r for r in ALL_FAM if r[0] == 'M'], 'W': [r for r in ALL_FAM if r[0] == 'W'], 'X': CTL}
TOK = {u: K.by_token(v) for u, v in UNIV.items()}
TOK_CEN = K.by_token(CEN)
CEN_UNIV = {r[2]: r[0] for r in CEN}
CEN_NAME = {r[2]: r[1] for r in CEN}
DATES = dict(D1=R.D1, D2=R.D2, T_FIN=R.T_FIN, D2_moins_7j=R.D2 - 7 * R.DAY)


def show(token):
    if token in cat:
        return dict(token=token, event=cat[token][0], question=cat[token][1], outcome=cat[token][2])
    return dict(token=token, event=CEN_NAME.get(token))


def active_days(tokens, end):
    days = 0
    for rs in tokens.values():
        d = {t // R.DAY for t, _, _ in rs if t <= end}
        days += len(d)
    return days


# E1 and its sweep. One registry line per sweep.
RULES = [dict(min_n=n, min_u=u, age_days=a, hours=h) for n in (2, 3, 5) for u in (5000, 10000, 25000) for a in (14, 30) for h in (24, 72)]
e1 = {}
for u, tokens in TOK.items():
    # Sweep at T_FIN on the hourly grid; a first alert is dated, so earlier dates read from it.
    rows_out = []
    for rule in RULES:
        first, _ = K.alerts(tokens, AGES, R.T_FIN, R.T0, hours=rule['hours'], min_usd=1000, age_days=rule['age_days'], min_n=rule['min_n'], min_u=rule['min_u'])
        rows_out.append(dict(rule, tokens_alerted=len(first), first_alerts=sorted(((v['t'], k) for k, v in first.items()))[:400], details=None))
        if rule == dict(min_n=3, min_u=10000, age_days=14, hours=72):
            base = first
    e1[u] = dict(tokens=len(tokens), token_days=active_days(tokens, R.T_FIN), wallets_with_age=sum(1 for w in {x for rs in tokens.values() for _, x, _ in rs} if w in AGES), sweep=rows_out, a0={k: dict(v, utc=UTC(v['t']), **show(k)) for k, v in sorted(base.items(), key=lambda kv: kv[1]['t'])})
a0_dates = {}
for name, d in DATES.items():
    a0_dates[name] = {u: sum(1 for v in e1[u]['a0'].values() if v['t'] <= d) for u in e1}
(E / 'derived/A_E1.json').write_text(json.dumps(dict(e1=e1, a0_by_date=a0_dates), ensure_ascii=False))
enregistrer(ETUDE, 'E1_sweep', True, sum(len(v) for v in TOK.values()), 'claude', n_effectif=1, n_comparaisons=len(RULES) * len(TOK), sortie='derived/A_E1.json', params=dict(rules=len(RULES), universes=list(TOK)))

# E1G: same rule on the census, per wallet at 2,500 $ of census rows.
first_g, _ = K.alerts(TOK_CEN, AGES, R.T_FIN, R.T0, hours=72, min_usd=2500, age_days=14, min_n=3, min_u=10000)
unknown = 0
ranks = {}
for name, d in dict(D1=R.D1, D2=R.D2, T_FIN=R.T_FIN).items():
    table = []
    for token, rs in TOK_CEN.items():
        if rs[0][0] > d:
            continue
        n, u, members, unk = K.fresh_cohort(rs, d - d % R.H, AGES, 72, 2500, 14)
        unknown += unk
        if n:
            table.append((n, round(u, 2), token, CEN_UNIV.get(token, 'G'), members))
    table.sort(key=lambda x: (-x[0], -x[1], x[2]))
    ranks[name] = [dict(rank=i + 1, n=x[0], u=x[1], universe=x[3], members=x[4], **show(x[2])) for i, x in enumerate(table[:60])]
per_day = Counter((v['t'] // R.DAY, CEN_UNIV.get(k, 'G')) for k, v in first_g.items())
burden = defaultdict(dict)
for (day, u), n in sorted(per_day.items()):
    burden[u][time.strftime('%m-%d', time.gmtime(day * R.DAY))] = n
g_out = dict(first_alerts=[dict(utc=UTC(v['t']), t=v['t'], n=v['n'], u=v['u'], universe=CEN_UNIV.get(k, 'G'), members=v['members'], **show(k)) for k, v in sorted(first_g.items(), key=lambda kv: kv[1]['t'])], burden_new_tokens_per_day=burden, ranks=ranks, tokens=len(TOK_CEN), rows=len(CEN), wallets=len({r[3] for r in CEN}), wallets_with_age=sum(1 for w in {r[3] for r in CEN} if w in AGES), unknown_age_seen=unknown)
(E / 'derived/A_E1G.json').write_text(json.dumps(g_out, ensure_ascii=False))
enregistrer(ETUDE, 'E1G_census', True, len(TOK_CEN), 'claude', n_effectif=1, n_comparaisons=3, sortie='derived/A_E1G.json', params=dict(min_usd=2500))

# E2 bursts and E3 small then large, per universe.
e2 = {}
for u, tokens in TOK.items():
    for minutes in (5, 15, 60):
        all_b = []
        for token, rs in tokens.items():
            for b in K.bursts(rs, minutes):
                all_b.append(dict(b, token=token))
        spent = sum(x for rs in tokens.values() for _, _, x in rs)
        days = active_days(tokens, R.T_FIN)
        all_b.sort(key=lambda b: -b['usd'])
        e2[f'{u}_{minutes}'] = dict(bursts=len(all_b), token_days=days, buy_usd=round(spent, 2), per_token_day=round(len(all_b) / days, 4) if days else None, per_million_usd=round(len(all_b) / (spent / 1e6), 2) if spent else None, before_D2=sum(1 for b in all_b if b['start'] <= R.D2), top=[dict(b, utc=UTC(b['start']), **show(b['token'])) for b in all_b[:25]])
(E / 'derived/A_E2.json').write_text(json.dumps(e2, ensure_ascii=False))
enregistrer(ETUDE, 'E2_bursts', True, sum(v['bursts'] for v in e2.values()), 'claude', n_effectif=1, n_comparaisons=9, sortie='derived/A_E2.json')

e3 = {}
for u, rows in UNIV.items():
    per = defaultdict(list)
    for r in rows:
        if r[4] == 'BUY':
            per[(r[3], r[2])].append((r[8], r[9], r[5]))
    fills = groups = n_dec = big = hits = 0
    examples = []
    for (w, token), v in per.items():
        g, dec = K.decisions(v)
        fills += len(v)
        groups += g
        n_dec += len(dec)
        if sum(x for _, x in dec) >= 1000:
            big += 1
            h = K.small_then_large(dec)
            if h:
                hits += 1
                examples.append(dict(h, wallet=w, token=token, utc=UTC(h['at'])))
    examples.sort(key=lambda x: -x['usd'])
    e3[u] = dict(fills=fills, tx_groups=groups, decisions=n_dec, pairs_over_1000=big, small_then_large=hits, per_100=round(100 * hits / big, 1) if big else None, top=examples[:25])
(E / 'derived/A_E3.json').write_text(json.dumps(e3, ensure_ascii=False))
enregistrer(ETUDE, 'E3_small_then_large', True, sum(v['pairs_over_1000'] for v in e3.values()), 'claude', n_effectif=1, n_comparaisons=len(e3), sortie='derived/A_E3.json')

# Placebo of E1: shuffle first-event dates among qualified wallets of the universe. Does freshness gather on one token more than chance?
def placebo(u, end, draws=1000):
    tokens = TOK[u]
    sets = {}
    for token, rs in tokens.items():
        for t in K.hourly_ticks(max(R.T0, rs[0][0]), end):
            q = K.qualified(rs, t, 72, 1000)
            if len(q) >= 2:
                sets[tuple(sorted((w, first) for w, (first, _) in q.items()))] = token
    wallets = sorted({w for s in sets for w, _ in s})
    known = [w for w in wallets if w in AGES]
    def stat(age):
        best = 0
        for s in sets:
            n = sum(1 for w, first in s if w in age and first - age[w] <= 14 * R.DAY)
            if n > best:
                best = n
        return best
    real = stat(AGES)
    rng = random.Random(SEED)
    values = [AGES[w] for w in known]
    dist = Counter()
    for _ in range(draws):
        rng.shuffle(values)
        dist[stat(dict(zip(known, values)))] += 1
    hits = sum(c for v, c in dist.items() if v >= real)
    return dict(universe=u, end=UTC(end), sets=len(sets), wallets=len(wallets), known_age=len(known), real_max_n=real, draws=draws, null=dict(sorted(dist.items())), hits=hits, p=(hits + 1) / (draws + 1))


pl = {}
for u, end in (('M', R.D2), ('M', R.T_FIN), ('M', R.D2 - 7 * R.DAY), ('X', R.D2), ('X', R.T_FIN)):
    res = placebo(u, end)
    pl[f'{u}_{res["end"]}'] = res
    (E / 'derived/A_placebo.json').write_text(json.dumps(pl, ensure_ascii=False))
    enregistrer(ETUDE, f'placebo_E1_{u}_{end}', True, res['wallets'], 'claude', n_effectif=1, stat=res['real_max_n'], p=res['p'], n_tirages=res['draws'], n_hits=res['hits'], sortie='derived/A_placebo.json', params=dict(universe=u, end=end))
print(json.dumps(dict(a0_by_date=a0_dates, placebo={k: (v['real_max_n'], v['p'], v['null']) for k, v in pl.items()})))
