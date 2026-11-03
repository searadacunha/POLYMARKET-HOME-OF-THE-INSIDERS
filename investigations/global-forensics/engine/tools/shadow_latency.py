"""Where the shadow replay's delays come from. Read-only on the signal engine's state: short keyset reads, so the collector is never blocked. Writes one JSON.

Usage: shadow_latency.py <alerts.jsonl> <out.json> [db]. Lag = observed_at - ts for each collected row. Batch = rows sharing one observation second. Nothing here reads an outcome.
"""
import json
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

DB = Path.home() / '.local/state/polysentinel-signal-engine/state.sqlite3'
BANDS = ((60, '<1 min'), (300, '1-5 min'), (900, '5-15 min'), (3600, '15-60 min'), (21600, '1-6 h'), (86400, '6-24 h'), (float('inf'), '>24 h'))
GAP = 600


def band(x):
    return next(name for limit, name in BANDS if x < limit)


def pct(values, q):
    values = sorted(values)
    return values[min(len(values) - 1, int(q * len(values)))] if values else None


def rows(path, step=50_000):
    """Keyset pages, each its own short read. `shortcut: sleeps 50 ms between pages, tighten only if the collector ever waits.`"""
    last = 0
    while True:
        cx = sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=30)
        page = cx.execute('SELECT rowid, ts, observed_at, nominal, is_buy, price FROM trades WHERE rowid>? ORDER BY rowid LIMIT ?', (last, step)).fetchall()
        cx.close()
        if not page:
            return
        last = page[-1][0]
        yield from page
        time.sleep(.05)


def main(alerts_path, out, db=DB):
    lag_bands, batch_sizes, observed = Counter(), Counter(), []
    lag_by_filter, negative, total = {True: [], False: []}, 0, 0
    for _, ts, seen, usd, is_buy, price in rows(db):
        total += 1
        lag = seen - ts
        negative += lag < 0
        lag_bands[band(max(lag, 0))] += 1
        batch_sizes[int(seen)] += 1
        observed.append(seen)
        lag_by_filter[bool(is_buy and price <= .35 and usd >= 100)].append(lag)
    observed.sort()
    gaps = [(a, b) for a, b in zip(observed, observed[1:]) if b - a > GAP]
    gap_ends = [b for _, b in gaps]
    batch = Counter(band_size for band_size in ('1-10' if n <= 10 else '11-100' if n <= 100 else '101-1000' if n <= 1000 else '>1000' for n in batch_sizes.values()))
    alerts = [json.loads(line) for line in Path(alerts_path).read_text().splitlines()]
    decomposed, spread_over, order_inverted = Counter(), 0, 0
    detail = []
    for a in alerts:
        trigger = a['observed_at']
        latest = max(t['ts'] for t in a['trades'])
        earliest = min(t['ts'] for t in a['trades'])
        window = a['components']['synchronised_entrants']['window_s']
        over = latest - earliest > window
        spread_over += over
        observed_at = [t['observed_at'] for t in a['trades']]
        same_second = len({int(x) for x in observed_at}) == 1
        after_gap = next((b for b in gap_ends if 0 <= trigger - b <= 3600), None)
        latency = a['detection_latency_s']
        cause = 'after_collection_gap' if after_gap is not None and latency > GAP else 'collector_lag_no_gap' if latency > GAP else 'normal_poll'
        decomposed[cause] += 1
        detail.append(dict(latency=latency, window=window, spread=latest - earliest, same_second=same_second, cause=cause))
    by_cause = {c: dict(n=n, median_s=pct([d['latency'] for d in detail if d['cause'] == c], .5), p90_s=pct([d['latency'] for d in detail if d['cause'] == c], .9)) for c, n in decomposed.items()}
    result = dict(
        rows=total, span_days=round((observed[-1] - observed[0]) / 86400, 2), rows_observed_before_trade=negative,
        lag_bands=[dict(band=name, rows=lag_bands[name], share=round(lag_bands[name] / total, 4)) for _, name in BANDS],
        lag_median_s=pct(lag_by_filter[True] + lag_by_filter[False], .5), lag_p90_s=pct(lag_by_filter[True] + lag_by_filter[False], .9),
        candidate_rows=dict(n=len(lag_by_filter[True]), lag_median_s=pct(lag_by_filter[True], .5), lag_p90_s=pct(lag_by_filter[True], .9)),
        observation_seconds_by_batch_size=batch, gaps=dict(n=len(gaps), largest_s=max((b - a for a, b in gaps), default=0), total_hours=round(sum(b - a for a, b in gaps) / 3600, 1)),
        alerts=dict(n=len(alerts), by_cause=by_cause, all_members_seen_in_one_second=sum(d['same_second'] for d in detail), spread_wider_than_stated_window=spread_over),
        reading='Delay comes from when the collector saw a row, not from the detector, which fires on the row that completes a set. Alerts with all members seen in one second were completed by one batch.')
    Path(out).write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))


if __name__ == '__main__':
    main(*sys.argv[1:])
