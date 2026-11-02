"""Tests of PROTOCOL.md, amendment 1. `build` reads the tape once, `controls` passes synthetic tables through the same functions, `run` computes on real data, `worlds` replays the frozen positions on drawn rankings.
Permutations move the status of a wallet, within strata of amount x markets x entry week. One ranking was realized: nothing here tells information from a shared conviction."""
import csv
import gzip
import json
import re
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import net
import seed

ROOT = net.ROOT
T_UPSIDE = 1792768669
T_CEREMONIE = 1793044800
T_TAPE = 1785542400  # 2026-08-01 UTC, first day of the tape
T_JUMP = 1791475200
T_RANK = 1792420054
SEED = 20261102
N_PERM = 20000
REG = ROOT / 'study/test_register.jsonl'
SCEN = {"Will Harry Kane win the 2026 Ballon d'Or?": 'Yes', "Will Kylian Mbappé finish 2nd in the 2026 Ballon d'Or?": 'Yes', "Will Lamine Yamal finish 3rd in the 2026 Ballon d'Or?": 'Yes', "Will Rodri finish 4th in the 2026 Ballon d'Or?": 'Yes', "Will Lionel Messi finish 5th in the 2026 Ballon d'Or?": 'Yes', "Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher?": 'Mbappé', "Ballon d'Or 2026: Rodri or Lionel Messi to finish higher?": 'Rodri'}
PUBLIC = {a.lower() for a in list(seed.UPSIDE_PRINTED.values()) + list(seed.UPSIDE_LATER.values())} | {a['profile'].lower() for a in seed.IRBOZ.values()}


def family():
    tok, events = {}, set()
    scenario = set()
    with open(ROOT / 'derived/markets.csv') as f:
        for m in csv.DictReader(f):
            s = (m['event_slug'] or '').lower()
            if 'ballon' not in s or 'women' in s or '2027' in s or not m['tokens']:
                continue
            events.add(m['event_id'])
            for t, o, p in zip(m['tokens'].split('|'), m['outcomes'].split('|'), m['final_prices'].split('|')):
                tok[t] = dict(q=m['question'], o=o, final=float(p) if p else None, cond=m['condition_id'])
                if SCEN.get(m['question']) == o:
                    if float(p) != 1.0:
                        raise SystemExit(f"scenario token not at 1: {m['question']}")
                    scenario.add(t)
    if len(scenario) != len(SCEN):
        raise SystemExit(f'{len(scenario)} scenario tokens of {len(SCEN)}')
    return tok, events, scenario


def build():
    tok, events, scenario = family()
    deploy = json.load(open(ROOT / 'derived/wallet_deploy.json'))
    w = defaultdict(lambda: dict(notional=0.0, payoff=0.0, scen=0.0, n=0, conds=set(), first=None))
    rows = []
    unresolved = 0
    first_any = {}
    with gzip.open(ROOT / 'derived/census_trades.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r['eid'] not in events or r['side'] != 'BUY':
                continue
            first_any[r['w']] = min(first_any.get(r['w'], r['ts']), r['ts'])
            if r['ts'] >= T_UPSIDE:
                continue
            t = tok.get(r['token'])
            if t is None or t['final'] not in (0.0, 1.0):
                unresolved += 1
                continue
            n = r['size'] * r['price']
            x = w[r['w']]
            x['notional'] += n
            x['payoff'] += r['size'] * t['final']
            x['n'] += 1
            x['conds'].add(t['cond'])
            is_s = r['token'] in scenario
            if is_s:
                x['scen'] += n
            rows.append((r['w'], r['token'], r['ts'], r['price'], n, is_s))
    pop = {a: v for a, v in w.items() if v['notional'] >= 500}
    table = {}
    no_deploy = late = 0
    for a, v in pop.items():
        d = (deploy.get(a) or {}).get('ts') if a in deploy else None
        first = first_any[a]
        if not d:
            status = 'unknown'
            no_deploy += 1
        elif d > first:
            status = 'unknown'
            late += 1
        elif d >= T_TAPE and first - d <= 30 * 86400:
            status = 'fresh'
        else:
            status = 'old'
        table[a] = dict(notional=v['notional'], payoff=v['payoff'], scen=v['scen'], n=v['n'], markets=len(v['conds']), first=first, deploy=d, status=status)
    (ROOT / 'derived/stats_v2_table.json').write_text(json.dumps(dict(wallets=table, unresolved_rows=unresolved, buyers_before_upside=len(w), no_deploy=no_deploy, deploy_after_first=late, events=sorted(events)), indent=0))
    with gzip.open(ROOT / 'derived/stats_v2_rows.jsonl.gz', 'wt') as out:
        for r in rows:
            out.write(json.dumps(r, separators=(',', ':')) + '\n')
    c = defaultdict(int)
    for v in table.values():
        c[v['status']] += 1
    print('events', len(events), 'buyers before T_UPSIDE', len(w), 'population', len(table), dict(c), 'no deploy', no_deploy, 'deploy after first', late, 'rows', len(rows), 'unresolved', unresolved)
    jd = json.load(open(ROOT / 'derived/population_stats.json'))
    gaps = [abs(jd[a]['join_date'] - v['deploy']) for a, v in table.items() if a in jd and jd[a].get('join_date') and v['deploy']]
    if gaps:
        print('join_date against deploy, median gap s', int(np.median(gaps)), 'over 1 day', sum(g > 86400 for g in gaps), 'of', len(gaps))


class Table:
    """Arrays for the tests. Row lists are read once. Non-population buys stay in the tape arrays with wallet index -1."""

    def __init__(self, wallets, rows):
        self.names = [a for a, v in wallets.items() if v['status'] in ('fresh', 'old')]
        idx = {a: i for i, a in enumerate(self.names)}
        get = lambda k: np.array([wallets[a][k] for a in self.names], dtype=float)
        self.notional, self.payoff, self.scen = get('notional'), get('payoff'), get('scen')
        self.markets = get('markets')
        self.first = get('first')
        self.fresh = np.array([wallets[a]['status'] == 'fresh' for a in self.names])
        self.w = np.array([idx.get(r[0], -1) for r in rows], dtype=np.int32)
        self.ts = np.array([r[2] for r in rows], dtype=np.int64)
        self.price = np.array([r[3] for r in rows], dtype=float)
        self.usd = np.array([r[4] for r in rows], dtype=float)
        self.is_s = np.array([bool(r[5]) for r in rows])
        toks = {t: i for i, t in enumerate(sorted({r[1] for r in rows}))}
        self.tok = np.array([toks[r[1]] for r in rows], dtype=np.int32)
        self.groups = self._strata()
        self._t2_prepare()
        self._t4_prepare()

    def _strata(self):
        edges = np.quantile(self.notional, np.linspace(0, 1, 11)[1:-1])
        dec = np.searchsorted(edges, self.notional)
        mk = np.digitize(self.markets, [2, 4, 10])
        wk = ((self.first - T_TAPE) // (7 * 86400)).astype(int)
        keys = defaultdict(list)
        for i in range(len(self.names)):
            keys[(int(dec[i]) // 2, int(mk[i]), int(wk[i]))].append(i)
        self.strata_all = [np.array(v) for v in keys.values()]
        return [np.array(v) for v in keys.values() if self.fresh[v].any() and (~self.fresh[v]).any()]

    def shuffle(self, rng):
        m = self.fresh.copy()
        for g in self.groups:
            m[g] = rng.permutation(m[g])
        return m

    def _t2_prepare(self):
        mask = self.is_s
        day = self.ts // 86400
        pct = np.zeros(len(self.usd))
        keys = defaultdict(list)
        for i in np.where(mask)[0]:
            keys[(int(self.tok[i]), int(day[i]))].append(i)
        for ids in keys.values():
            ids = np.array(ids)
            o = ids[np.argsort(self.price[ids], kind='stable')]
            total = self.usd[o].sum()
            cum = np.cumsum(self.usd[o])
            pct[o] = (cum - self.usd[o] / 2) / total  # mid-rank: a line does not outrank itself
        n = len(self.names)
        keep = mask & (self.w >= 0)
        self.t2a = np.bincount(self.w[keep], weights=self.usd[keep] * pct[keep], minlength=n)
        self.t2b = np.bincount(self.w[keep], weights=self.usd[keep], minlength=n)

    def _t4_prepare(self):
        day = self.ts // 86400
        pb = np.minimum((self.price * 10).astype(int), 9)
        ok = (self.price >= .01) & (self.price <= .99)
        ids = {}
        st = np.zeros(len(self.usd), dtype=np.int32) - 1
        for i in np.where(ok)[0]:
            st[i] = ids.setdefault((int(day[i]), int(pb[i])), len(ids))
        self.t4_n = len(ids)
        self.t4_cell = st * 2 + self.is_s.astype(np.int32)
        self.t4_valid = ok
        self.t4_total = np.bincount(self.t4_cell[ok], weights=self.usd[ok], minlength=2 * self.t4_n)
        both = (self.t4_total[::2] > 0) & (self.t4_total[1::2] > 0)
        self.t4_w = np.minimum(self.t4_total[::2], self.t4_total[1::2]) * both
        self.t4_both = int(both.sum())
        keep = ok & (self.w >= 0)
        self.t4_idx = np.where(keep)[0]


def t1(T, m):
    a, b = T.notional[m].sum(), T.notional[~m].sum()
    return T.payoff[m].sum() / a - T.payoff[~m].sum() / b


def t2(T, m):
    return T.t2a[m].sum() / T.t2b[m].sum() - T.t2a[~m].sum() / T.t2b[~m].sum()


def t3(T, m):
    conc = T.scen / T.notional >= .8
    num = den = 0.0
    for g in T.strata_all:
        f = m[g]
        nf, no = f.sum(), (~f).sum()
        if nf and no:
            w = nf * no / (nf + no)
            num += w * (conc[g][f].mean() - conc[g][~f].mean())
            den += w
    return num / den if den else 0.0


def t4(T, m):
    i = T.t4_idx
    use = i[m[T.w[i]]]
    fresh = np.bincount(T.t4_cell[use], weights=T.usd[use], minlength=2 * T.t4_n)
    with np.errstate(divide='ignore', invalid='ignore'):
        share = np.where(T.t4_total > 0, fresh / T.t4_total, 0.0)
    d = share[1::2] - share[::2]
    return float((T.t4_w * d).sum() / T.t4_w.sum()) if T.t4_w.sum() else 0.0


TESTS = dict(T1=t1, T2=t2, T3=t3, T4=t4)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, top = [0.0] * len(ps), 0.0
    for r, i in enumerate(order):
        top = max(top, (len(ps) - r) * ps[i])
        adj[i] = min(1.0, top)
    return adj


def run_all(T, rng, n_perm, names=('T1', 'T2', 'T3', 'T4')):
    obs = {k: TESTS[k](T, T.fresh) for k in names}
    ge = {k: 0 for k in names}
    for _ in range(n_perm):
        m = T.shuffle(rng)
        for k in names:
            if abs(TESTS[k](T, m)) >= abs(obs[k]):
                ge[k] += 1
    out = []
    for k in names:
        out.append(dict(test=k, effect=float(obs[k]), p=(ge[k] + 1) / (n_perm + 1), at_floor=ge[k] == 0, n_perm=n_perm, n_fresh=int(T.fresh.sum()), n_old=int((~T.fresh).sum()), informative_strata=len(T.groups)))
    for o, a in zip(out, holm([x['p'] for x in out])):
        o['p_holm'] = a
    return out


def bootstrap_t1(T, rng, n=20000):
    f, o = np.where(T.fresh)[0], np.where(~T.fresh)[0]
    v = np.empty(n)
    for i in range(n):
        a, b = rng.choice(f, len(f)), rng.choice(o, len(o))
        v[i] = T.payoff[a].sum() / T.notional[a].sum() - T.payoff[b].sum() / T.notional[b].sum()
    return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]


def register(line):
    with open(REG, 'a') as f:
        f.write(json.dumps(dict(at=int(time.time()), script='ana_57_stats_v2.py', **line)) + '\n')


def load():
    d = json.load(open(ROOT / 'derived/stats_v2_table.json'))
    rows = []
    with gzip.open(ROOT / 'derived/stats_v2_rows.jsonl.gz', 'rt') as f:
        for line in f:
            rows.append(json.loads(line))
    return d, rows


def run():
    d, rows = load()
    wallets = d['wallets']
    T = Table(wallets, rows)
    rng = np.random.default_rng(SEED)
    res = run_all(T, rng, N_PERM)
    fresh, old = T.fresh, ~T.fresh
    summary = dict(roi_fresh=float(T.payoff[fresh].sum() / T.notional[fresh].sum() - 1), roi_old=float(T.payoff[old].sum() / T.notional[old].sum() - 1), ci95_t1=bootstrap_t1(T, rng), winners_fresh=int((T.payoff[fresh] > T.notional[fresh]).sum()), losers_fresh=int((T.payoff[fresh] < T.notional[fresh]).sum()), winners_old=int((T.payoff[old] > T.notional[old]).sum()), losers_old=int((T.payoff[old] < T.notional[old]).sum()), share_scen80_fresh=float((T.scen[fresh] / T.notional[fresh] >= .8).mean()), share_scen80_old=float((T.scen[old] / T.notional[old] >= .8).mean()), median_markets_fresh=float(np.median(T.markets[fresh])), median_markets_old=float(np.median(T.markets[old])), notional_fresh=float(T.notional[fresh].sum()), notional_old=float(T.notional[old].sum()))
    for x in res:
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in x.items()}, flush=True)
        register(dict(status='amende_v2', test=x['test'], p=x['p'], p_holm=x['p_holm'], effect=x['effect'], n_perm=x['n_perm']))
    print(summary)
    # exploratory sensitivities, declared in amendment 1
    names = T.names
    big_f = names[int(np.argmax(np.where(fresh, T.notional, -1)))]
    big_o = names[int(np.argmax(np.where(old, T.notional, -1)))]
    clusters = set()
    p = ROOT / 'CLUSTERS.json'
    if p.exists():
        for c in json.load(open(p)).get('clusters', []):
            clusters |= {w for w in c.get('wallets', [])}
    variants = dict(sans_comptes_publics=lambda r: r[0] not in PUBLIC, sans_plus_grosse_position=lambda r: r[0] not in (big_f, big_o), achats_avant_08_10=lambda r: r[2] < T_JUMP, achats_avant_19_10=lambda r: r[2] < T_RANK)
    if clusters:
        variants['sans_clusters_L1_L2'] = lambda r: r[0] not in clusters
    sens = {}
    for name, keep in variants.items():
        sub = [r for r in rows if keep(r)]
        w2 = {}
        token_final = {}
        tok, _, _ = family()
        agg = defaultdict(lambda: dict(notional=0.0, payoff=0.0, scen=0.0, n=0, conds=set()))
        for a, t, ts, price, n, sc in sub:
            x = agg[a]
            x['notional'] += n
            x['payoff'] += n / price * tok[t]['final']
            x['scen'] += n if sc else 0
            x['n'] += 1
            x['conds'].add(tok[t]['cond'])
        for a, v in agg.items():
            if a in wallets:
                w2[a] = dict(notional=v['notional'], payoff=v['payoff'], scen=v['scen'], n=v['n'], markets=len(v['conds']), first=wallets[a]['first'], deploy=wallets[a]['deploy'], status=wallets[a]['status'])
        TT = Table(w2, sub)
        r = run_all(TT, np.random.default_rng(SEED), 5000, names=('T1', 'T4'))
        f2, o2 = TT.fresh, ~TT.fresh
        sens[name] = dict(n_fresh=int(f2.sum()), n_old=int(o2.sum()), roi_fresh=float(TT.payoff[f2].sum() / TT.notional[f2].sum() - 1), roi_old=float(TT.payoff[o2].sum() / TT.notional[o2].sum() - 1), tests=r)
        print(name, {k: (round(v, 4) if isinstance(v, float) else v) for k, v in sens[name].items() if k != 'tests'}, [(x['test'], round(x['effect'], 4), round(x['p'], 4)) for x in r], flush=True)
        for x in r:
            register(dict(status='exploratoire', variant=name, test=x['test'], p=x['p'], effect=x['effect'], n_perm=x['n_perm']))
    (ROOT / 'derived/stats_v2_results.json').write_text(json.dumps(dict(tests=res, summary=summary, sensitivities=sens, unresolved_rows=d['unresolved_rows'], no_deploy=d['no_deploy'], deploy_after_first=d['deploy_after_first']), indent=1))


def synth(kind, seed, n_wallets=700, fresh_share=.2):
    """Shapes close to the real table. `lift`: extra hold ROI of fresh wallets, reached through a share of dollars moved to the winners. Habits: each wallet has a persistent tilt for winners and for cheap prices, independent of status except where said."""
    rng = np.random.default_rng(seed)
    wallets, rows = {}, []
    tokens = [f't{i}' for i in range(40)]
    lift = dict(signal_9=.03, signal_18=.06, signal_37=.13).get(kind, 0.0)
    for k in range(n_wallets):
        a = f'w{k}'
        fresh = rng.random() < fresh_share
        n_buys = int(rng.integers(1, 3)) if (kind == 'nul_frais_concentres' and fresh) else int(rng.integers(3, 14))
        tilt = rng.normal(0, 1.0 if kind == 'nul_habitudes' else 0.0)
        cheap = rng.normal(0, .08 if kind == 'nul_habitudes' else 0.0)
        week = int(rng.integers(0, 12))
        w = dict(notional=0.0, payoff=0.0, scen=0.0, n=0, conds=set(), first=T_TAPE + week * 7 * 86400, deploy=1, status='fresh' if fresh else 'old')
        for _ in range(n_buys):
            p_s = np.clip(.4 + .15 * tilt + (lift if fresh else 0.0), .02, .98)
            sc = rng.random() < p_s
            tok = tokens[int(rng.integers(0, 7))] if sc else tokens[int(rng.integers(7, 40))]
            base = rng.uniform(.45, .75) if sc else rng.uniform(.25, .7)
            price = float(np.clip(base + cheap + rng.normal(0, .03), .02, .97))
            size = float(rng.lognormal(6, 1.1))
            n = size * price
            won = sc or rng.random() < .22 * (1 if not sc else 0)
            w['notional'] += n
            w['payoff'] += size * (1.0 if won else 0.0)
            w['scen'] += n if sc else 0
            w['n'] += 1
            w['conds'].add(tok)
            rows.append((a, tok, w['first'] + int(rng.integers(0, 6)) * 86400, price, n, sc))
        w['markets'] = len(w.pop('conds'))
        wallets[a] = w
    return wallets, rows


def wilson_upper(k, n, z=1.96):
    p = k / n
    d = 1 + z * z / n
    return (p + z * z / (2 * n) + z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** .5)) / d


def controls():
    out = {}
    for kind in ('nul_iid', 'nul_habitudes', 'nul_frais_concentres', 'signal_9', 'signal_18', 'signal_37'):
        rej = defaultdict(int)
        rois = []
        seeds = 20
        for s in range(seeds):
            w, r = synth(kind, 5000 + s)
            T = Table(w, r)
            res = run_all(T, np.random.default_rng(s), 300)
            rois.append(float(T.payoff[T.fresh].sum() / T.notional[T.fresh].sum() - T.payoff[~T.fresh].sum() / T.notional[~T.fresh].sum()))
            alarm = False
            for x in res:
                if x['p_holm'] < .05:
                    rej[x['test']] += 1
                    alarm = True
            rej['any'] += alarm
        out[kind] = dict(seeds=seeds, rejections=dict(rej), any_upper95=round(wilson_upper(rej['any'], seeds), 3), mean_roi_gap=round(float(np.mean(rois)), 3))
        print(kind, out[kind], flush=True)
    (ROOT / 'derived/stats_v2_controls.json').write_text(json.dumps(out, indent=1))


def worlds():
    """T1w. Frozen positions, drawn rankings. One draw is one world. Descriptive."""
    tok, events, scenario = family()
    d, rows = load()
    status = {a: v['status'] for a, v in d['wallets'].items()}
    size = {'fresh': defaultdict(float), 'old': defaultdict(float)}
    cost = {'fresh': defaultdict(float), 'old': defaultdict(float)}
    for a, t, ts, price, n, sc in rows:
        s = status.get(a)
        if s in size:
            size[s][t] += n / price
            cost[s][t] += n
    # winner market prices
    with open(ROOT / 'derived/markets.csv') as f:
        winner = {}
        for m in csv.DictReader(f):
            if m['event_id'] == '48361' and m['tokens']:
                winner[m['tokens'].split('|')[0]] = m['group_item'] or m['question']
    series = defaultdict(list)
    with gzip.open(ROOT / 'derived/census_trades.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r['token'] in winner:
                series[winner[r['token']]].append((r['ts'], r['price'], r['size']))
    players = sorted(series)
    idx = {p.lower(): i for i, p in enumerate(players)}

    def find(name):
        name = name.strip().lower()
        for p, i in idx.items():
            if name in p or p in name:
                return i
        return None

    def strengths(ts):
        v = np.full(len(players), .0005)
        for i, p in enumerate(players):
            sr = [x for x in series[p] if ts - 6 * 3600 <= x[0] <= ts] or [x for x in series[p] if x[0] <= ts][-3:]
            if sr:
                q = sum(x[2] for x in sr)
                v[i] = max(.0005, sum(x[1] * x[2] for x in sr) / q)
        return v / v.sum()

    def fn(q, o):
        m = re.match(r"Will (.+?) win the 2026 Ballon d'Or\?", q)
        if m:
            i = find(m.group(1))
            return None if i is None else (lambda rk: (rk[:, i] == 0) if o == 'Yes' else (rk[:, i] != 0))
        m = re.match(r"Will (.+?) finish (\d)(?:st|nd|rd|th) in the 2026 Ballon d'Or\?", q)
        if m:
            i, k = find(m.group(1)), int(m.group(2)) - 1
            return None if i is None else (lambda rk: (rk[:, i] == k) if o == 'Yes' else (rk[:, i] != k))
        m = re.match(r"Will (.+?) finish in the top (\d+) of the 2026 Ballon d'Or", q)
        if m:
            i, k = find(m.group(1)), int(m.group(2))
            return None if i is None else (lambda rk: (rk[:, i] < k) if o == 'Yes' else (rk[:, i] >= k))
        m = re.match(r"Ballon d'Or 2026: (.+?) or (.+?) to finish higher\?", q)
        if m:
            a, b = find(m.group(1)), find(m.group(2))
            if a is None or b is None:
                return None
            first = o.split()[-1].lower() in m.group(1).lower()
            return (lambda rk: rk[:, a] < rk[:, b]) if first else (lambda rk: rk[:, b] < rk[:, a])
        return None

    DRAWS = 20000
    order = ['Harry Kane', 'Kylian Mbappé', 'Lamine Yamal', 'Rodri', 'Lionel Messi']
    fns = {t: fn(tok[t]['q'], tok[t]['o']) for t in set(size['fresh']) | set(size['old'])}
    modelled = {s: sum(cost[s][t] for t in cost[s] if fns.get(t)) for s in size}
    total = {s: sum(cost[s].values()) for s in size}
    realized = {s: sum(size[s][t] * tok[t]['final'] - cost[s][t] for t in cost[s] if fns.get(t)) / modelled[s] for s in size}
    out = dict(modelled_share={s: modelled[s] / total[s] for s in size}, realized_modelled_roi=realized, observed_gap=realized['fresh'] - realized['old'], models={})
    rng = np.random.default_rng(SEED)
    for name, ts, q in (('PL_09_10', 1791547200, 0.0), ('PL_22_10', 1792670400, 0.0), ('melange_q068_22_10', 1792670400, .68)):
        s = strengths(ts)
        g = np.log(s) + rng.gumbel(size=(DRAWS, len(players)))
        rk = np.argsort(np.argsort(-g, axis=1), axis=1)
        if q:
            real = np.zeros(len(players), dtype=int)
            rest = [i for i in range(len(players)) if i not in [find(n) for n in order]]
            for pos, n in enumerate(order):
                real[find(n)] = pos
            rest_sorted = sorted(rest, key=lambda i: -s[i])
            for pos, i in enumerate(rest_sorted):
                real[i] = 5 + pos
            pick = rng.random(DRAWS) < q
            rk[pick] = real
        roi = {}
        for st in size:
            v = np.zeros(DRAWS)
            for t, f in fns.items():
                if f and t in size[st]:
                    v += size[st][t] * f(rk).astype(float) - cost[st][t]
            roi[st] = v / modelled[st]
        gap = roi['fresh'] - roi['old']
        out['models'][name] = dict(mean_gap=float(gap.mean()), sd_gap=float(gap.std()), mean_roi_fresh=float(roi['fresh'].mean()), mean_roi_old=float(roi['old'].mean()), p05_gap=float(np.percentile(gap, 5)), p95_gap=float(np.percentile(gap, 95)), share_worlds_gap_ge_observed=float((gap >= out['observed_gap']).mean()), share_worlds_fresh_beat_old=float((gap > 0).mean()))
        print(name, {k: round(v, 4) for k, v in out['models'][name].items()}, flush=True)
    print('observed gap', round(out['observed_gap'], 4), 'realized', {k: round(v, 4) for k, v in realized.items()}, 'modelled share', {k: round(v, 3) for k, v in out['modelled_share'].items()})
    (ROOT / 'derived/stats_v2_worlds.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    dict(build=build, run=run, controls=controls, worlds=worlds)[sys.argv[1]]()
