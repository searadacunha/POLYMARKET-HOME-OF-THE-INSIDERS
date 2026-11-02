"""Detectors D1, D2, D3 of PROTOCOL.md section 6: chronological replay with no look-ahead. Each alert is dated at the trade that crosses the threshold, using only the tape up to that second and join_date.
`family`: the 31 Ballon d'Or events taken together, or one event id for a control family. Thresholds are constants: they do not move after reading.
Input is a gz JSONL tape. One wallet state per active wallet in memory, no global trade list kept."""
import csv
import gzip
import json
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net

AGE_DAYS = 30
D1_USD = 5000.0
D1_WINDOW = 72 * 3600
D1_SHARE = .80
D2_N = 3
D2_WINDOW = 7 * 86400
D3_MARKETS = 3
D3_USD = 1000.0
D3_LOW, D3_HIGH = .20, .85
T_UPSIDE = 1792768669


def join_date(w, cache):
    if w not in cache:
        d = net.get('https://data-api.polymarket.com/v2/user-stats', dict(user=w))
        cache[w] = (d.get('data') or {}).get('join_date')
    return cache[w]


def wallet_buys(w, end):
    """Every buy of the wallet on any market up to `end`, to compute at each t the share of its seen buys in the family. Rows after t are filtered at use."""
    out = []
    for r in net.v2_all('/v2/activity', dict(user=w, limit=1000, start=1, end=end, type='TRADE', side='BUY', sort_direction='ASC')):
        out.append((r['timestamp'], r['size'] * r['price']))
    return out


def replay(path, family_name, conds_in_family=None):
    """Returns alerts. A tape row: ts, w, side, token, cond, size, price, ..."""
    rows = []
    with gzip.open(path, 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r['side'] != 'BUY':
                continue
            rows.append((r['ts'], r['w'], r['token'], r['cond'], r['size'] * r['price'], r['price'], r.get('outcome')))
    rows.sort(key=lambda x: x[0])
    if not rows:
        return dict(family=family_name, alerts=[], rows=0)
    end = rows[-1][0]
    # coarse pre-filter, to fetch join dates only for wallets that could fire: no time information leaks out of it, a wallet below these sums never fires
    total = defaultdict(float)
    for r in rows:
        total[r[1]] += r[4]
    candidates = {w for w, v in total.items() if v >= min(D1_USD, 3 * D3_USD)}
    jd_path = net.ROOT / 'state/join_cache.json'
    jd = json.loads(jd_path.read_text()) if jd_path.exists() else {}
    for w in sorted(candidates):
        join_date(w, jd)
    jd_path.write_text(json.dumps(jd))
    fills = defaultdict(deque)
    d3fills = defaultdict(deque)
    d1_at, d3_at = {}, {}
    d2_seen = defaultdict(dict)
    d2_at = {}
    buys_cache = {}
    last_price = {}
    alerts = []
    no_join = 0
    for ts, w, token, cond, usd, price, outcome in rows:
        last_price[token] = price
        if w not in candidates:
            continue
        j = jd.get(w)
        if not j:
            no_join += 1
            continue
        if ts - j > AGE_DAYS * 86400:
            continue
        q = fills[w]
        q.append((ts, usd))
        while q and q[0][0] < ts - D1_WINDOW:
            q.popleft()
        if w not in d1_at and sum(x[1] for x in q) >= D1_USD:
            buys = buys_cache.get(w)
            if buys is None:
                buys = wallet_buys(w, end)
                buys_cache[w] = buys
            seen = sum(v for t, v in buys if t <= ts)
            family_usd = total_family(rows_by_wallet(rows, w), ts)
            if seen > 0 and family_usd / seen >= D1_SHARE:
                d1_at[w] = ts
                alerts.append(dict(det='D1', wallet=w, ts=ts, token=token, cond=cond, price=price, outcome=outcome, usd_72h=round(sum(x[1] for x in q), 2), age_days=round((ts - j) / 86400, 2), share=round(family_usd / seen, 3)))
        if w in d1_at:
            rec = d2_seen[token]
            rec[w] = ts
            recent = {a for a, t in rec.items() if t >= ts - D2_WINDOW}
            if len(recent) >= D2_N and token not in d2_at:
                d2_at[token] = ts
                alerts.append(dict(det='D2', token=token, cond=cond, ts=ts, price=price, outcome=outcome, wallets=sorted(recent)))
        if D3_LOW <= price <= D3_HIGH:
            q3 = d3fills[w]
            q3.append((ts, cond, usd))
            while q3 and q3[0][0] < ts - D1_WINDOW:
                q3.popleft()
            if w not in d3_at:
                by = defaultdict(float)
                for _, c, v in q3:
                    by[c] += v
                big = [c for c, v in by.items() if v >= D3_USD]
                if len(big) >= D3_MARKETS:
                    d3_at[w] = ts
                    alerts.append(dict(det='D3', wallet=w, ts=ts, token=token, cond=cond, price=price, outcome=outcome, markets=len(big), age_days=round((ts - j) / 86400, 2)))
    return dict(family=family_name, rows=len(rows), first_ts=rows[0][0], last_ts=end, wallets=len(total), candidates=len(candidates), without_join=no_join, alerts=alerts)


_by_wallet = {}


def rows_by_wallet(rows, w):
    key = (id(rows), w)
    if key not in _by_wallet:
        _by_wallet[key] = [(r[0], r[4]) for r in rows if r[1] == w]
    return _by_wallet[key]


def total_family(rw, ts):
    return sum(v for t, v in rw if t <= ts)


def score(res, finals):
    """Copy value: what a reader of the alert would earn by buying the alerted token at the alert price, held to resolution. Fees left out and written."""
    out = defaultdict(lambda: dict(n=0, wallets=set(), tokens=set(), hold=[], before_upside=0))
    for a in res['alerts']:
        o = out[a['det']]
        o['n'] += 1
        if a.get('wallet'):
            o['wallets'].add(a['wallet'])
        o['tokens'].add(a['token'])
        f = finals.get(a['token'])
        if f is not None and a['price'] > 0:
            o['hold'].append(f / a['price'] - 1)
        if a['ts'] < T_UPSIDE:
            o['before_upside'] += 1
    summary = {}
    for k, o in out.items():
        weeks = max(1 / 7, (res['last_ts'] - res['first_ts']) / (7 * 86400))
        h = sorted(o['hold'])
        summary[k] = dict(alerts=o['n'], wallets=len(o['wallets']), tokens=len(o['tokens']), per_week=round(o['n'] / weeks, 2), mean_copy_roi=round(sum(h) / len(h), 4) if h else None, median_copy_roi=round(h[len(h) // 2], 4) if h else None, n_scored=len(h), before_t_upside=o['before_upside'])
    return summary


def main():
    finals = {}
    if len(sys.argv) > 1 and sys.argv[1] == 'ballon':
        with open(net.ROOT / 'derived/markets.csv') as f:
            for m in csv.DictReader(f):
                for t, p in zip(m['tokens'].split('|'), m['final_prices'].split('|')):
                    if p:
                        finals[t] = float(p)
        res = replay(net.ROOT / 'derived/census_trades.jsonl.gz', 'ballon_dor_2026')
        res['summary'] = score(res, finals)
        (net.ROOT / 'derived/detectors_ballon.json').write_text(json.dumps(res))
        print(res['summary'], {k: res[k] for k in ('rows', 'wallets', 'candidates', 'without_join')})
    elif len(sys.argv) > 1 and sys.argv[1] == 'oos':
        out = {}
        spec = json.load(open(net.ROOT / 'study/oos_events.json'))
        for e in spec['sealed'] + spec['sport']:
            path = net.ROOT / f"derived/oos/{e['event_id']}.jsonl.gz"
            if not path.exists():
                print('missing tape', e['event_id'])
                continue
            with open(net.ROOT / f"derived/oos/{e['event_id']}.finals.json") as f:
                finals = json.load(f)
            res = replay(path, e['event_id'])
            res['kind'] = e['kind']
            res['title'] = e['title']
            res['summary'] = score(res, finals) if res['alerts'] else {}
            out[e['event_id']] = res
            print(e['kind'], e['title'][:40], res['rows'], res.get('wallets'), res['summary'], flush=True)
        (net.ROOT / 'derived/detectors_oos.json').write_text(json.dumps(out))


if __name__ == '__main__':
    main()
