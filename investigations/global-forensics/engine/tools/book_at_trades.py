"""The book each large entrant met: best prices, spread, depth, cost of the size, and the mid before and after. All from archived captures with time at or before the trade for the state at entry. The mid after is description, never used to select anyone.

Usage: book_at_trades.py <market id> <results dir>. Entrants come from results/discovery/<market>.json, both tokens.
"""
import bisect
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path('/Volumes/PHI-Data/global-forensics')


def load(market):
    series, snaps = defaultdict(list), defaultdict(list)
    with gzip.open(ROOT / 'orderbooks' / market / 'book_rows.jsonl.gz', 'rt') as f:
        for line in f:
            r = json.loads(line)
            d = r['data']
            token = str(d.get('token_id'))
            t = float(d.get('timestamp') or r['received'])
            if d.get('best_bid') is not None and d.get('best_ask') is not None:
                series[token].append((t, float(d['best_bid']), float(d['best_ask'])))
            if r['kind'] == 'book_snapshot':
                snaps[token].append((t, [(float(p), float(s)) for p, s in d.get('asks') or []], [(float(p), float(s)) for p, s in d.get('bids') or []]))
    for s in (series, snaps):
        for token in s:
            s[token].sort(key=lambda x: x[0])
    return series, snaps


def state(series, t):
    i = bisect.bisect_right(series, (t, 9e9, 9e9)) - 1
    return series[i] if i >= 0 else None


def main(market, results):
    d = json.loads((Path(results) / 'discovery' / f'{market}.json').read_text())
    series, snaps = load(market)
    span = (min((s[0][0] for s in series.values()), default=None), max((s[-1][0] for s in series.values()), default=None))
    rows, outside = [], 0
    for e in d['chosen']:
        token, t = e['token'], e['ts']
        s = series.get(token) or []
        if not s or t < s[0][0] or t > s[-1][0]:
            outside += 1
            continue
        before = state(s, t - 1)
        keys = [x[0] for x in snaps.get(token, [])]
        j = bisect.bisect_right(keys, t - 1) - 1
        snap = snaps[token][j] if j >= 0 else None
        out = dict(wallet=e['wallet'], outcome=e.get('outcome'), token=token, ts=t, usd=e['usd'], paid=float(e['price']), seconds_before_event=e['seconds_before_event'], tx=e['tx'])
        if before:
            bid, ask = before[1], before[2]
            out.update(best_bid=bid, best_ask=ask, spread=round(ask - bid, 4), quote_age_s=round(t - before[0], 2), paid_minus_ask=round(float(e['price']) - ask, 4))
        if snap:
            asks = sorted(snap[1])
            shares = e['usd'] / max(float(e['price']), .001)
            filled, cost = 0.0, 0.0
            for p, size in asks:
                take = min(size, shares - filled)
                filled += take
                cost += take * p
                if filled >= shares:
                    break
            out.update(snapshot_age_s=round(t - snap[0], 2), ask_depth_usd_within_2c=round(sum(p * x for p, x in asks if p <= asks[0][0] + .02), 2) if asks else None, theoretical_vwap_for_size=round(cost / filled, 5) if filled else None, snapshot_could_fill=filled >= shares)
        for tag, dt in (('mid_minus_300s', -300), ('mid_minus_60s', -60), ('mid_plus_60s', 60), ('mid_plus_300s', 300)):
            x = state(s, t + dt)
            if x:
                out[tag] = round((x[1] + x[2]) / 2, 4)
        rows.append(out)
    target = Path(results) / 'orderbooks'
    target.mkdir(parents=True, exist_ok=True)
    (target / f'{market}.json').write_text(json.dumps(dict(market=market, captured_span=span, tokens=len(series), entries_in_span=len(rows), entries_outside_span=outside, rows=sorted(rows, key=lambda r: r['ts']), reading='A third party capture. Prices at or before the trade describe what it met. Later mids are description. Nothing here says who knew what.'), indent=0))
    print(market, 'entries in span', len(rows), 'outside', outside, 'tokens', len(series))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
