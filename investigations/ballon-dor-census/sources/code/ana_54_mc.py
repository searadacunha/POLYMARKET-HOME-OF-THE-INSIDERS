"""Descriptive Monte Carlo of PROTOCOL.md section 5: one ranking per draw, so correlated bets on one classification count as one realization.
Plackett-Luce from winner-market prices at the wallet's dollar-weighted buy date, 50 000 draws. A low p here says the wallet did better than that crude model expected at that date. It is NOT a probability of insider trading: the model ignores all rank-market information, and the wallets were selected after the result."""
import csv
import glob
import gzip
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import net

ROOT = net.ROOT
DRAWS = 50000
SEED = 20261102


def main():
    with open(ROOT / 'derived/markets.csv') as f:
        markets = list(csv.DictReader(f))
    tok = {}
    winner = {}
    for m in markets:
        if not m['tokens']:
            continue
        for t, o in zip(m['tokens'].split('|'), m['outcomes'].split('|')):
            tok[t] = dict(q=m['question'], o=o)
            if m['event_id'] == '48361' and o == 'Yes':
                winner[t] = m['group_item'] or m['question']
    series = defaultdict(list)
    with gzip.open(ROOT / 'derived/census_trades.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r['token'] in winner:
                series[winner[r['token']]].append((r['ts'], r['price'], r['size']))
    for s in series.values():
        s.sort()
    players = sorted(series)
    index = {p.lower(): i for i, p in enumerate(players)}

    def strengths(ts):
        out = np.full(len(players), .0005)
        for i, p in enumerate(players):
            rows = [x for x in series[p] if ts - 6 * 3600 <= x[0] <= ts] or [x for x in series[p] if x[0] <= ts][-3:]
            if rows:
                n = sum(x[2] for x in rows)
                out[i] = max(.0005, sum(x[1] * x[2] for x in rows) / n)
        return out / out.sum()

    def find(name):
        name = name.strip().lower()
        for p, i in index.items():
            if name in p or p in name:
                return i
        return None

    def payoff_fn(q, o):
        """Payoff per share from the simulated rank array (rank[i] = 0 for the winner). None: not modelled, valued at its buy price."""
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

    order = ['Harry Kane', 'Kylian Mbappé', 'Lamine Yamal', 'Rodri', 'Lionel Messi']
    rng = np.random.default_rng(SEED)
    out = {}
    for f in sorted(glob.glob(str(ROOT / 'derived/accounts/*.json'))):
        a = json.load(open(f))
        buys = [r for r in a['activity'] if r['type'] == 'TRADE' and r['side'] == 'BUY' and r['token_id'] in tok]
        if not buys:
            continue
        notional = sum(r['size'] * r['price'] for r in buys)
        t_mean = int(sum(r['timestamp'] * r['size'] * r['price'] for r in buys) / notional)
        s = strengths(t_mean)
        g = np.log(s) + rng.gumbel(size=(DRAWS, len(players)))
        rk = np.argsort(np.argsort(-g, axis=1), axis=1)
        pnl = np.zeros(DRAWS)
        modelled = 0.0
        real = 0.0
        finals = {}
        for r in buys:
            fn = payoff_fn(tok[r['token_id']]['q'], tok[r['token_id']]['o'])
            n = r['size'] * r['price']
            if fn is None:
                continue
            modelled += n
            pnl += r['size'] * fn(rk).astype(float) - n
        with open(ROOT / 'derived/markets.csv') as ff:
            pass
        # realized on the modelled set, true ranking
        truth = np.zeros((1, len(players)), dtype=int) + 99
        for pos, name in enumerate(order):
            truth[0, find(name)] = pos
        observed = 0.0
        for r in buys:
            fn = payoff_fn(tok[r['token_id']]['q'], tok[r['token_id']]['o'])
            if fn is not None:
                observed += r['size'] * float(fn(truth)[0]) - r['size'] * r['price']
        pl = 1.0
        rem = 1.0
        for name in order:
            v = s[find(name)]
            pl *= v / rem
            rem -= v
        out[a['address']] = dict(labels=a['labels'], t_mean=t_mean, notional=round(notional, 2), modelled=round(modelled, 2), observed_hold_pnl=round(observed, 2), p_model=float((np.sum(pnl >= observed) + 1) / (DRAWS + 1)), mean_sim_pnl=round(float(pnl.mean()), 2), pl_exact_top5=round(float(pl), 6))
        print(a['address'][:10], a['labels'][-1][:22], 'date', __import__('time').strftime('%m-%d', __import__('time').gmtime(t_mean)), 'modelled', round(modelled), 'obs', round(observed), 'p_model', round(out[a['address']]['p_model'], 5), 'PLtop5', out[a['address']]['pl_exact_top5'], flush=True)
    (ROOT / 'derived/mc_results.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
