"""Detectors D1, D2, D3, amendment 1. Age from the on-chain deployment, required to precede the trade. Same family rule on both sides: replay per event, last 45 days before the last trade. The whole Ballon family is replayed apart, as a view of the affair.
Copy value: next trade of the token at least 60 s after the alert, held to resolution, until the result is known. Fees left out. No ground truth: an alert is never called true or false."""
import csv
import gzip
import json
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import net
import seed

ROOT = net.ROOT
AGE = 30 * 86400
D1_USD, D1_WINDOW, D1_SHARE = 5000.0, 72 * 3600, .80
D2_N, D2_WINDOW = 3, 7 * 86400
D3_MARKETS, D3_USD, D3_LOW, D3_HIGH = 3, 1000.0, .20, .85
LATENCY = 60
T_UPSIDE = 1792768669
T_CEREMONIE = 1793044800
WINDOW = 45 * 86400
PUBLIC = {a.lower(): n for n, a in list(seed.UPSIDE_PRINTED.items()) + list(seed.UPSIDE_LATER.items())}
PUBLIC.update({a['profile'].lower(): (PUBLIC.get(a['profile'].lower()) or f'irboz_{n}') for n, a in seed.IRBOZ.items()})


def wallet_buys(w, end):
    """Every buy of the wallet on any market until `end`. Filtered at use to what was visible at t."""
    return [(r['timestamp'], r['size'] * r['price']) for r in net.v2_all('/v2/activity', dict(user=w, limit=1000, start=1, end=end, type='TRADE', side='BUY', sort_direction='ASC'))]


def replay(rows, deploy, tag):
    """rows: sorted (ts, wallet, token, cond, usd, price, outcome), buys only."""
    if not rows:
        return dict(tag=tag, alerts=[], rows=0, wallets=0, first_ts=None, last_ts=None)
    end = rows[-1][0]
    per_w = defaultdict(list)
    for r in rows:
        per_w[r[1]].append((r[0], r[4]))
    fills, d3f = defaultdict(deque), defaultdict(deque)
    d1_at, d3_at, d2_at = {}, {}, {}
    d2_seen = defaultdict(dict)
    buys_cache = {}
    alerts = []
    no_deploy = set()
    for ts, w, token, cond, usd, price, outcome in rows:
        d = deploy.get(w)
        if d is None:
            no_deploy.add(w)
            continue
        if d > ts or ts - d > AGE:
            continue
        q = fills[w]
        q.append((ts, usd))
        while q and q[0][0] < ts - D1_WINDOW:
            q.popleft()
        if w not in d1_at and sum(x[1] for x in q) >= D1_USD:
            if w not in buys_cache:
                try:
                    buys_cache[w] = wallet_buys(w, end)
                except net.FetchError:
                    buys_cache[w] = None
            buys = buys_cache[w]
            if buys is not None:
                seen = sum(v for t, v in buys if t <= ts)
                fam = sum(v for t, v in per_w[w] if t <= ts)
                if seen > 0 and fam / seen >= D1_SHARE:
                    d1_at[w] = ts
                    alerts.append(dict(det='D1', wallet=w, ts=ts, token=token, cond=cond, price=price, outcome=outcome, usd_72h=round(sum(x[1] for x in q), 2), age_days=round((ts - d) / 86400, 2), share=round(fam / seen, 3)))
        if w in d1_at:
            rec = d2_seen[token]
            rec[w] = ts
            recent = {a for a, t in rec.items() if t >= ts - D2_WINDOW}
            if len(recent) >= D2_N and token not in d2_at:
                d2_at[token] = ts
                alerts.append(dict(det='D2', token=token, cond=cond, ts=ts, price=price, outcome=outcome, wallets=sorted(recent)))
        if D3_LOW <= price <= D3_HIGH:
            q3 = d3f[w]
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
                    alerts.append(dict(det='D3', wallet=w, ts=ts, token=token, cond=cond, price=price, outcome=outcome, markets=len(big), age_days=round((ts - d) / 86400, 2)))
    return dict(tag=tag, alerts=alerts, rows=len(rows), wallets=len(per_w), first_ts=rows[0][0], last_ts=end, wallets_without_deploy=len(no_deploy), markets=len({r[3] for r in rows}))


def copy_values(alerts, rows, finals, t_stop):
    """Next trade of the alerted token at least LATENCY seconds later. Alerts at or after t_stop are not scored."""
    by_tok = defaultdict(list)
    for r in rows:
        by_tok[r[2]].append((r[0], r[5]))
    out = []
    for a in alerts:
        if a['ts'] >= t_stop:
            a['scored'] = False
            continue
        nxt = next(((t, p) for t, p in by_tok[a['token']] if t >= a['ts'] + LATENCY), None)
        f = finals.get(a['token'])
        if not nxt or f is None or nxt[0] >= t_stop or nxt[1] <= 0:
            a['scored'] = False
            continue
        a['scored'] = True
        a['copy_price'] = nxt[1]
        a['copy_roi'] = f / nxt[1] - 1
        out.append(a['copy_roi'])
    return out


def summarize(res, values):
    c = defaultdict(int)
    for a in res['alerts']:
        c[a['det']] += 1
    weeks = (res['last_ts'] - res['first_ts']) / (7 * 86400) if res.get('first_ts') else 0
    v = sorted(values)
    return dict(tag=res['tag'], kind=res.get('kind'), title=res.get('title'), wallets=res['wallets'], markets=res.get('markets'), weeks=round(weeks, 2), D1=c['D1'], D2=c['D2'], D3=c['D3'], d1_per_1000_wallets=round(c['D1'] / res['wallets'] * 1000, 2) if res['wallets'] else None, n_scored=len(v), mean_copy=round(sum(v) / len(v), 3) if v else None, median_copy=round(v[len(v) // 2], 3) if v else None, wallets_without_deploy=res.get('wallets_without_deploy'))


def read_rows(path, eid=None, events=None):
    rows = []
    with gzip.open(path, 'rt') as f:
        for line in f:
            r = json.loads(line)
            if r['side'] != 'BUY':
                continue
            if events is not None and r.get('eid') not in events:
                continue
            rows.append((r['ts'], r['w'], r['token'], r['cond'], r['size'] * r['price'], r['price'], r.get('outcome'), r.get('eid')))
    rows.sort(key=lambda x: x[0])
    return rows


def main():
    deploy_raw = json.load(open(ROOT / 'derived/wallet_deploy.json'))
    deploy = {w: v['ts'] for w, v in deploy_raw.items() if v}
    with open(ROOT / 'derived/markets.csv') as f:
        markets = list(csv.DictReader(f))
    men = {m['event_id'] for m in markets if 'ballon' in (m['event_slug'] or '').lower() and 'women' not in (m['event_slug'] or '').lower() and '2027' not in (m['event_slug'] or '')}
    all_ev = {m['event_id'] for m in markets if '2027' not in (m['event_slug'] or '')}
    finals = {}
    title = {}
    for m in markets:
        title[m['event_id']] = m['event_title']
        for t, p in zip(m['tokens'].split('|'), m['final_prices'].split('|')):
            if p:
                finals[t] = float(p)
    fam_rows = read_rows(ROOT / 'derived/census_trades.jsonl.gz', events=all_ev)
    print('family buys', len(fam_rows), flush=True)
    strip = lambda rs: [r[:7] for r in rs]
    # view of the affair: whole family
    res = replay(strip(fam_rows), deploy, 'famille_ballon_31_evenements')
    vals = copy_values(res['alerts'], strip(fam_rows), finals, T_CEREMONIE)
    fam = dict(res=res, summary=summarize(res, vals))
    al = res['alerts']
    pub = {}
    for a in al:
        w = a.get('wallet')
        if a['det'] == 'D1' and w in PUBLIC:
            pub[PUBLIC[w]] = a['ts']
    d1 = [a for a in al if a['det'] == 'D1']
    d2 = [a for a in al if a['det'] == 'D2']
    d3 = [a for a in al if a['det'] == 'D3']
    view = dict(d1_total=len(d1), d1_before_upside=sum(a['ts'] < T_UPSIDE for a in d1), d1_before_ceremony=sum(a['ts'] < T_CEREMONIE for a in d1), d1_public_before=sorted(k for k, t in pub.items() if t < T_UPSIDE), d1_public_after=sorted(k for k, t in pub.items() if t >= T_UPSIDE), public_not_flagged=sorted(set(PUBLIC.values()) - set(pub)), d1_first=time.strftime('%Y-%m-%d %H:%M', time.gmtime(min(a['ts'] for a in d1))) if d1 else None,
                d2_total=len(d2), d2_before_upside=sum(a['ts'] < T_UPSIDE for a in d2), d2_before_upside_won=sum(a['ts'] < T_UPSIDE and finals.get(a['token']) == 1.0 for a in d2), d2_before_upside_lost=sum(a['ts'] < T_UPSIDE and finals.get(a['token']) == 0.0 for a in d2), d2_first=time.strftime('%Y-%m-%d %H:%M', time.gmtime(min(a['ts'] for a in d2))) if d2 else None,
                d3_total=len(d3), d3_before_upside=sum(a['ts'] < T_UPSIDE for a in d3))
    print(view, flush=True)
    print(fam['summary'], flush=True)
    # per event, same rule both sides, last 45 days
    table = []
    by_event = defaultdict(list)
    for r in fam_rows:
        by_event[r[7]].append(r[:7])
    for eid, rows in sorted(by_event.items(), key=lambda x: -len(x[1])):
        rows = [r for r in rows if r[0] >= rows[-1][0] - WINDOW]
        if eid not in men:
            continue
        r = replay(rows, deploy, eid)
        r['title'] = title.get(eid)
        r['kind'] = 'ballon_par_evenement'
        v = copy_values(r['alerts'], rows, finals, T_CEREMONIE)
        table.append(summarize(r, v))
    spec = json.load(open(ROOT / 'study/oos_events.json'))
    for e in spec['sealed'] + spec['sport']:
        path = ROOT / f"derived/oos/{e['event_id']}.jsonl.gz"
        if not path.exists():
            continue
        fin = json.load(open(ROOT / f"derived/oos/{e['event_id']}.finals.json"))
        rows = []
        with gzip.open(path, 'rt') as f:
            for line in f:
                x = json.loads(line)
                if x['side'] == 'BUY':
                    rows.append((x['ts'], x['w'], x['token'], x['cond'], x['size'] * x['price'], x['price'], x.get('outcome')))
        rows.sort(key=lambda z: z[0])
        rows = [q for q in rows if q[0] >= rows[-1][0] - WINDOW]
        r = replay(rows, deploy, e['event_id'])
        r['title'] = e['title']
        r['kind'] = 'scelle_hors_echantillon' if e['kind'] == 'sealed' else 'temoin_sportif'
        t_stop = rows[-1][0] - 2 * 3600
        v = copy_values(r['alerts'], rows, fin, t_stop)
        table.append(summarize(r, v))
    for row in table:
        print({k: row[k] for k in ('kind', 'title', 'wallets', 'markets', 'D1', 'D2', 'D3', 'd1_per_1000_wallets', 'n_scored', 'mean_copy')}, flush=True)
    (ROOT / 'derived/detectors_v2.json').write_text(json.dumps(dict(view=view, family=fam, per_event=table, note='Detectors written after reading the affair: every Ballon figure is in-sample. Sealed events are not controls; 3 sport events are, and they are few. D3 cannot fire on an event with fewer than 3 markets.'), indent=0))


if __name__ == '__main__':
    main()
