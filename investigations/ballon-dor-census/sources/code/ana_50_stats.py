"""Tests T1 to T4 of PROTOCOL.md section 5. `build` writes the analysis table from the census, `run` computes, `controls` passes synthetic tables through the same tests.
Random numbers: numpy default_rng, seed 20261102. Memory: one compact array per field, the tape is read once."""
import csv
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import net

MEN = {'48361', '811116', '811117', '1105185', '1189431', '1105364', '1105369', '1105379', '1218178', '1218179', '1225367', '1225368', '1226675', '1226676'}
T_UPSIDE = 1792768669  # 2026-10-23 15:17:49 UTC
T_CEREMONIE = 1793044800
FRESH_DAYS = 30
SEED = 20261102
N_PERM = 20000
SCENARIO_Q = {  # question fragment -> outcome that happened. Checked against final_prices in build().
    "Will Harry Kane win the 2026 Ballon d'Or?": 'Yes', "Will Kylian Mbappé finish 2nd in the 2026 Ballon d'Or?": 'Yes', "Will Lamine Yamal finish 3rd in the 2026 Ballon d'Or?": 'Yes',
    "Will Rodri finish 4th in the 2026 Ballon d'Or?": 'Yes', "Will Lionel Messi finish 5th in the 2026 Ballon d'Or?": 'Yes',
    "Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher?": 'Mbappé', "Ballon d'Or 2026: Rodri or Lionel Messi to finish higher?": 'Rodri',
}


def load_markets():
    token = {}
    scenario = set()
    missing = dict(SCENARIO_Q)
    with open(net.ROOT / 'derived/markets.csv') as f:
        for m in csv.DictReader(f):
            if m['event_id'] not in MEN or not m['tokens']:
                continue
            toks, outs, prices = m['tokens'].split('|'), m['outcomes'].split('|'), m['final_prices'].split('|')
            for t, o, p in zip(toks, outs, prices):
                token[t] = dict(q=m['question'], outcome=o, final=float(p) if p else None, closed=m['closed'], cond=m['condition_id'], eid=m['event_id'])
                if SCENARIO_Q.get(m['question']) == o:
                    scenario.add(t)
                    missing.pop(m['question'], None)
                    if float(p) != 1.0:
                        raise SystemExit(f'scenario token not resolved to 1: {m["question"]} {o} {p}')
    if missing:
        raise SystemExit(f'scenario markets not found: {list(missing)}')
    return token, scenario


def build():
    token, scenario = load_markets()
    pop = json.load(open(net.ROOT / 'derived/population.json'))['population']
    stats = json.load(open(net.ROOT / 'derived/population_stats.json'))
    missing_stats = [w for w in pop if w not in stats]
    if missing_stats:
        raise SystemExit(f'{len(missing_stats)} wallets without stats: finish col_45_joindates.py')
    first = {}
    wallets = defaultdict(lambda: dict(notional=0.0, payoff=0.0, scen=0.0, n=0))
    rows = []
    unresolved = dropped = 0
    with gzip.open(net.ROOT / 'derived/census_trades.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r['eid'] not in MEN or r['side'] != 'BUY' or r['w'] not in pop or r['ts'] >= T_UPSIDE:
                continue
            t = token.get(r['token'])
            if t is None or t['final'] is None or t['final'] not in (0.0, 1.0):
                unresolved += 1
                continue
            first[r['w']] = min(first.get(r['w'], r['ts']), r['ts'])
            n = r['size'] * r['price']
            w = wallets[r['w']]
            w['notional'] += n
            w['payoff'] += r['size'] * t['final']
            w['n'] += 1
            if r['token'] in scenario:
                w['scen'] += n
            rows.append((r['w'], r['token'], r['ts'], r['price'], n, r['token'] in scenario))
    # freshness from the first buy in the family over the whole tape, not only before T_UPSIDE
    table = {}
    for a, w in wallets.items():
        jd = stats[a].get('join_date')
        status = 'unknown' if not jd else ('fresh' if first[a] - jd <= FRESH_DAYS * 86400 else 'old')
        table[a] = dict(w, join_date=jd, first=first[a], status=status)
    (net.ROOT / 'derived/stats_table.json').write_text(json.dumps(dict(wallets=table, unresolved_rows=unresolved)))
    with gzip.open(net.ROOT / 'derived/stats_rows.jsonl.gz', 'wt') as out:
        for row in rows:
            out.write(json.dumps(row, separators=(',', ':')) + '\n')
    c = defaultdict(int)
    for v in table.values():
        c[v['status']] += 1
    print('wallets before T_UPSIDE', len(table), dict(c), 'rows', len(rows), 'unresolved rows left out', unresolved)


def roi(sub):
    n = sum(w['notional'] for w in sub)
    return sum(w['payoff'] for w in sub) / n - 1 if n else float('nan')


def t1(wallets, rng, n_perm=N_PERM):
    """Dollar-weighted hold-to-resolution ROI, fresh against old. Exit decisions do not enter: each dollar bought is valued at its resolution."""
    fresh = [w for w in wallets if w['status'] == 'fresh']
    old = [w for w in wallets if w['status'] == 'old']
    obs = roi(fresh) - roi(old)
    nf, pf = np.array([w['notional'] for w in fresh]), np.array([w['payoff'] for w in fresh])
    no, po = np.array([w['notional'] for w in old]), np.array([w['payoff'] for w in old])
    boots = np.empty(n_perm)
    for i in range(n_perm):
        a = rng.integers(0, len(fresh), len(fresh))
        b = rng.integers(0, len(old), len(old))
        boots[i] = pf[a].sum() / nf[a].sum() - po[b].sum() / no[b].sum()
    allv = np.concatenate([nf, no]), np.concatenate([pf, po])
    perm = np.empty(n_perm)
    k = len(fresh)
    for i in range(n_perm):
        idx = rng.permutation(len(allv[0]))
        a, b = idx[:k], idx[k:]
        perm[i] = allv[1][a].sum() / allv[0][a].sum() - allv[1][b].sum() / allv[0][b].sum()
    p = (np.sum(np.abs(perm) >= abs(obs)) + 1) / (n_perm + 1)
    return dict(test='T1', n_fresh=len(fresh), n_old=len(old), roi_fresh=roi(fresh), roi_old=roi(old), effect=obs, ci95=[float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))], p=float(p), n_perm=n_perm)


def wallet_status(wallets):
    return {a: w['status'] for a, w in wallets.items()}


def t2(rows, status, rng, n_perm=N_PERM):
    """In each scenario market: the dollar-weighted percentile of the entry price among all buys before T_UPSIDE that same day. Lower = cheaper than others the same day."""
    groups = defaultdict(lambda: [0.0, 0.0])
    by_stratum = defaultdict(list)
    for w, tok, ts, price, n, scen in rows:
        if scen and status.get(w) in ('fresh', 'old'):
            by_stratum[(tok, ts // 86400)].append((w, price, n))
    units = []
    for st, buys in by_stratum.items():
        if len({b[0] for b in buys}) < 2:
            continue
        prices = np.array([b[1] for b in buys])
        weights = np.array([b[2] for b in buys])
        order = np.argsort(prices)
        cum = np.cumsum(weights[order]) / weights.sum()
        pct = np.empty(len(buys))
        pct[order] = cum
        agg = defaultdict(lambda: [0.0, 0.0])
        for (w, _, n), q in zip(buys, pct):
            agg[w][0] += n * q
            agg[w][1] += n
        for w, (a, b) in agg.items():
            units.append((st, w, a, b))
    strata = defaultdict(list)
    for i, u in enumerate(units):
        strata[u[0]].append(i)
    a = np.array([u[2] for u in units])
    b = np.array([u[3] for u in units])
    fresh = np.array([status[u[1]] == 'fresh' for u in units])

    def stat(mask):
        return a[mask].sum() / b[mask].sum() - a[~mask].sum() / b[~mask].sum()

    obs = stat(fresh)
    idx = [np.array(v) for v in strata.values() if fresh[v].any() and (~fresh[v]).any()]
    perm = np.empty(n_perm)
    for i in range(n_perm):
        m = fresh.copy()
        for g in idx:
            m[g] = rng.permutation(m[g])
        perm[i] = stat(m)
    p = (np.sum(np.abs(perm) >= abs(obs)) + 1) / (n_perm + 1)
    return dict(test='T2', units=len(units), strata_informative=len(idx), mean_pct_fresh=float(a[fresh].sum() / b[fresh].sum()), mean_pct_old=float(a[~fresh].sum() / b[~fresh].sum()), effect=float(obs), p=float(p), n_perm=n_perm)


def t3(wallets, rng, n_perm=N_PERM):
    """Share of wallets with at least 80 % of their family buys on the winning scenario, fresh against old, permuting inside deciles of amount."""
    use = [w for w in wallets if w['status'] in ('fresh', 'old')]
    amount = np.array([w['notional'] for w in use])
    conc = np.array([w['scen'] / w['notional'] >= .8 for w in use])
    fresh = np.array([w['status'] == 'fresh' for w in use])
    edges = np.quantile(amount, np.linspace(0, 1, 11)[1:-1])
    dec = np.searchsorted(edges, amount)
    obs = conc[fresh].mean() - conc[~fresh].mean()
    groups = [np.where(dec == d)[0] for d in range(10)]
    perm = np.empty(n_perm)
    for i in range(n_perm):
        m = fresh.copy()
        for g in groups:
            m[g] = rng.permutation(m[g])
        perm[i] = conc[m].mean() - conc[~m].mean()
    p = (np.sum(np.abs(perm) >= abs(obs)) + 1) / (n_perm + 1)
    return dict(test='T3', n_fresh=int(fresh.sum()), n_old=int((~fresh).sum()), share_fresh=float(conc[fresh].mean()), share_old=float(conc[~fresh].mean()), hits_fresh=int(conc[fresh].sum()), hits_old=int(conc[~fresh].sum()), effect=float(obs), p=float(p), n_perm=n_perm)


def t4(rows, status, token_is_scenario=None, rng=None, n_perm=N_PERM):
    """Fresh share of buy dollars on the winning scenario against their share on other outcomes, same day and same 10-cent price bin."""
    units = defaultdict(float)
    for w, tok, ts, price, n, scen in rows:
        if status.get(w) in ('fresh', 'old') and .01 <= price <= .99:
            units[(ts // 86400, min(int(price * 10), 9), bool(scen), w)] += n
    keys = list(units)
    n = np.array([units[k] for k in keys])
    fresh = np.array([status[k[3]] == 'fresh' for k in keys])
    scen = np.array([k[2] for k in keys])
    st_ids = {}
    st = np.array([st_ids.setdefault(k[:2], len(st_ids)) for k in keys])
    ok = []
    for s in range(len(st_ids)):
        g = np.where(st == s)[0]
        if scen[g].any() and (~scen[g]).any():
            ok.append(g)

    def stat(f):
        total, weight = 0.0, 0.0
        for g in ok:
            a, b = g[scen[g]], g[~scen[g]]
            na, nb = n[a].sum(), n[b].sum()
            d = n[a][f[a]].sum() / na - n[b][f[b]].sum() / nb
            wgt = min(na, nb)
            total += wgt * d
            weight += wgt
        return total / weight

    obs = stat(fresh)
    perm = np.empty(n_perm)
    for i in range(n_perm):
        m = fresh.copy()
        for g in ok:
            m[g] = rng.permutation(m[g])
        perm[i] = stat(m)
    p = (np.sum(np.abs(perm) >= abs(obs)) + 1) / (n_perm + 1)
    return dict(test='T4', strata=len(ok), units=len(keys), effect=float(obs), p=float(p), n_perm=n_perm)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, top = [0.0] * len(ps), 0.0
    for r, i in enumerate(order):
        top = max(top, (len(ps) - r) * ps[i])
        adj[i] = min(1.0, top)
    return adj


def all_tests(wallets, rows, rng, n_perm):
    status = wallet_status(wallets)
    lst = list(wallets.values())
    out = [t1(lst, rng, n_perm), t2(rows, status, rng, n_perm), t3(lst, rng, n_perm), t4(rows, status, rng=rng, n_perm=n_perm)]
    for o, a in zip(out, holm([x['p'] for x in out])):
        o['p_holm'] = a
    return out


def synthetic(strength, seed, n_wallets=800, fresh_share=.15):
    """A table with the shape of the real one. `strength`: extra probability that a fresh wallet's dollar lands on the eventual winners at a cheap price."""
    rng = np.random.default_rng(seed)
    wallets, rows = {}, []
    tokens = [f'tok{i}' for i in range(40)]
    scen_tokens = set(tokens[:7])
    for k in range(n_wallets):
        a = f'w{k}'
        fresh = rng.random() < fresh_share
        wal = dict(notional=0.0, payoff=0.0, scen=0.0, n=0, status='fresh' if fresh else 'old')
        for _ in range(int(rng.integers(3, 12))):
            informed = fresh and rng.random() < strength
            tok = tokens[int(rng.integers(0, 7))] if informed or rng.random() < .35 else tokens[int(rng.integers(7, 40))]
            is_s = tok in scen_tokens
            base = rng.uniform(.3, .75) if is_s else rng.uniform(.02, .5)
            price = float(np.clip(base - (.1 if informed else 0) + rng.normal(0, .03), .02, .97))
            size = float(rng.lognormal(6, 1))
            n = size * price
            win = is_s
            wal['notional'] += n
            wal['payoff'] += size * (1.0 if win else 0.0)
            wal['scen'] += n if is_s else 0
            wal['n'] += 1
            rows.append((a, tok, 1792000000 + int(rng.integers(0, 15)) * 86400, price, n, is_s))
        wallets[a] = wal
    return wallets, rows


def controls():
    out = []
    for name, strength in (('nul', 0.0), ('moyen', .25), ('fort', .6)):
        for seed in (1, 2, 3):
            w, r = synthetic(strength, seed)
            res = all_tests(w, r, np.random.default_rng(seed + 100), 1000)
            line = dict(scenario=name, seed=seed, **{x['test']: round(x['p_holm'], 4) for x in res}, effects={x['test']: round(x['effect'], 4) for x in res})
            out.append(line)
            print(line, flush=True)
    (net.ROOT / 'derived/stats_controls.json').write_text(json.dumps(out, indent=1))


def run():
    d = json.load(open(net.ROOT / 'derived/stats_table.json'))
    wallets = d['wallets']
    rows = []
    with gzip.open(net.ROOT / 'derived/stats_rows.jsonl.gz', 'rt') as f:
        for line in f:
            rows.append(json.loads(line))
    res = all_tests(wallets, rows, np.random.default_rng(SEED), N_PERM)
    (net.ROOT / 'derived/stats_results.json').write_text(json.dumps(dict(tests=res, unresolved_rows=d['unresolved_rows']), indent=1))
    for x in res:
        print(x)


if __name__ == '__main__':
    {'build': build, 'run': run, 'controls': controls}[sys.argv[1]]()
