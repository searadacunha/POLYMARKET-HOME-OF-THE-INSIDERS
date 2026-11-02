"""Exploratory. Upside: "each account buys 2 or 3 days, stops dead, a new one takes over". Windows of buying on the Mbappé market for the named accounts, against random draws of other wallets buying the same token with at least 500 $ (10 000 draws).
Statistic: share of pairs whose buying windows do not overlap. A high value is what a relay would produce, but also what a stream of newcomers would produce: this tests the claim's shape, not who is behind it."""
import csv
import gzip
import json
import random
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net
import seed

ROOT = net.ROOT
NAMED = {a.lower(): n for n, a in list(seed.UPSIDE_PRINTED.items()) + list(seed.UPSIDE_LATER.items())}
T_UPSIDE = 1792768669


def main():
    with open(ROOT / 'derived/markets.csv') as f:
        mb = [m for m in csv.DictReader(f) if m['event_id'] == '1105364'][0]
    tok = dict(zip(mb['outcomes'].split('|'), mb['tokens'].split('|')))['Mbappé']
    win = defaultdict(lambda: [None, None, 0.0])
    with gzip.open(ROOT / 'derived/census_trades.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r['token'] == tok and r['side'] == 'BUY' and r['ts'] < T_UPSIDE:
                x = win[r['w']]
                x[0] = r['ts'] if x[0] is None else min(x[0], r['ts'])
                x[1] = r['ts'] if x[1] is None else max(x[1], r['ts'])
                x[2] += r['size'] * r['price']
    stats = json.load(open(ROOT / 'derived/population_stats.json'))
    named = {w: v for w, v in win.items() if w in NAMED}
    rows = sorted(((NAMED[w], v) for w, v in named.items()), key=lambda x: x[1][0])
    for n, v in rows:
        print(n[:22].ljust(22), time.strftime('%d/%m %H:%M', time.gmtime(v[0])), '->', time.strftime('%d/%m %H:%M', time.gmtime(v[1])), round((v[1] - v[0]) / 86400, 2), 'j', round(v[2]))

    def share(items):
        pairs = dis = 0
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                pairs += 1
                a, b = items[i], items[j]
                if a[1] < b[0] or b[1] < a[0]:
                    dis += 1
        return dis / pairs if pairs else 0
    obs = share([v for v in named.values()])
    pool_all = [v for w, v in win.items() if w not in NAMED and v[2] >= 500]
    fresh_jd = {w for w, s in stats.items() if s.get('join_date') and win.get(w) and win[w][0] and win[w][0] - s['join_date'] <= 30 * 86400}
    pool_fresh = [win[w] for w in fresh_jd if w not in NAMED and win[w][2] >= 500]
    rng = random.Random(20261102)
    res = {}
    for name, pool in (('tous', pool_all), ('frais', pool_fresh)):
        k = len(named)
        if len(pool) < k:
            res[name] = dict(pool=len(pool), p=None)
            continue
        draws = [share(rng.sample(pool, k)) for _ in range(10000)]
        res[name] = dict(pool=len(pool), null_mean=round(sum(draws) / len(draws), 3), p=(sum(1 for d in draws if d >= obs) + 1) / 10001)
    print('named', len(named), 'observed share of non-overlapping pairs', round(obs, 3), res)
    out = dict(named=[dict(name=n, first=v[0], last=v[1], usd=v[2]) for n, v in rows], observed=obs, null=res)
    (ROOT / 'derived/relay_pattern.json').write_text(json.dumps(out, indent=1))
    with open(ROOT / 'study/test_register.jsonl', 'a') as f:
        for name, x in res.items():
            f.write(json.dumps(dict(at=int(time.time()), script='ana_56_relay_pattern.py', status='exploratoire', test=f'relais_{name}', p=x['p'], effect=obs, n_perm=10000)) + '\n')


if __name__ == '__main__':
    main()
