"""Exploratory, every line counted in study/test_register.jsonl. T1 and T4 again without public wallets, without inconsistent join dates, without wallets over 50 markets, and for buys before the first price jump and before the rank markets opened. Who moved the 9 October price."""
import gzip
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import ana_50_stats as S
import net
import seed

NAMED = {a.lower() for a in list(seed.UPSIDE_PRINTED.values()) + list(seed.UPSIDE_LATER.values())} | {a['profile'].lower() for a in seed.IRBOZ.values()}
T_JUMP = 1791475200   # 2026-10-08 16:00 UTC, before the rise of the Mbappé market
T_RANK = 1792420054   # 2026-10-19 14:47:34 UTC, opening of the 2nd place event
REG = net.ROOT / 'study/test_register.jsonl'


def main():
    d = json.load(open(net.ROOT / 'derived/stats_table.json'))['wallets']
    stats = json.load(open(net.ROOT / 'derived/population_stats.json'))
    rows = []
    with gzip.open(net.ROOT / 'derived/stats_rows.jsonl.gz', 'rt') as f:
        for line in f:
            rows.append(json.loads(line))
    neg = {w for w, v in d.items() if v['join_date'] and v['first'] < v['join_date']}
    many = {w for w in d if (stats.get(w, {}).get('markets') or 0) >= 50}
    variants = {
        'sans_comptes_publics': (lambda w, r: w not in NAMED),
        'sans_date_incoherente': (lambda w, r: w not in neg),
        'sans_50_marches_ou_plus': (lambda w, r: w not in many),
        'achats_avant_jump_08_10': (lambda w, r: r[2] < T_JUMP),
        'achats_avant_marches_de_place_19_10': (lambda w, r: r[2] < T_RANK),
    }
    token, scen = S.load_markets()
    out = {}
    for name, keep in variants.items():
        sub_rows = [r for r in rows if keep(r[0], r)]
        wallets = defaultdict(lambda: dict(notional=0.0, payoff=0.0, scen=0.0, n=0))
        for w, tok, ts, price, n, sc in sub_rows:
            x = wallets[w]
            x['notional'] += n
            x['payoff'] += (n / price) * token[tok]['final']
            x['scen'] += n if sc else 0
            x['n'] += 1
            x['status'] = d[w]['status']
        status = {w: v['status'] for w, v in wallets.items()}
        rng = np.random.default_rng(S.SEED)
        lst = list(wallets.values())
        a = S.t1(lst, rng, 5000)
        b = S.t4(sub_rows, status, rng=rng, n_perm=2000)
        out[name] = dict(T1=a, T4=b)
        print(name, 'n_fresh', a['n_fresh'], 'n_old', a['n_old'], 'roi', round(a['roi_fresh'], 3), round(a['roi_old'], 3), 'CI', [round(x, 3) for x in a['ci95']], 'p', round(a['p'], 4), '| T4', round(b['effect'], 3), 'p', round(b['p'], 4), flush=True)
        with open(REG, 'a') as f:
            for x in (a, b):
                f.write(json.dumps(dict(at=int(time.time()), script='ana_55_sensitivity.py', status='exploratoire', variant=name, test=x['test'], p=x['p'], effect=x['effect'], n_perm=x['n_perm'])) + '\n')
    # who bought while the Mbappé market moved, 8 to 10 October
    mbappe = next(t for t, v in token.items() if v['q'].startswith("Ballon d'Or 2026: Kylian") and v['outcome'] == 'Mbappé')
    w_buy = defaultdict(float)
    first_last = {}
    with gzip.open(net.ROOT / 'derived/census_trades.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r['token'] == mbappe and r['side'] == 'BUY' and 1791460800 <= r['ts'] <= 1791633600:
                w_buy[r['w']] += r['size'] * r['price']
    total = sum(w_buy.values())
    top = sorted(w_buy.items(), key=lambda x: -x[1])[:12]
    print('buy $ on Mbappé 08/10 12:00 to 10/10 12:00', round(total), 'wallets', len(w_buy))
    for w, v in top:
        jd = stats.get(w, {}).get('join_date')
        print(' ', w[:12], round(v), 'share', round(v / total, 3), 'join', time.strftime('%Y-%m-%d', time.gmtime(jd)) if jd else None, 'named' if w in NAMED else '')
    out['jump_buyers'] = dict(total=total, top=[dict(wallet=w, usd=v, join=stats.get(w, {}).get('join_date'), named=w in NAMED) for w, v in top])
    (net.ROOT / 'derived/stats_sensitivity.json').write_text(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
