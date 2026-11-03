"""Pure functions of the study. Same code for real and synthetic tables. See ../analysis_plan.md."""
import random
from bisect import bisect_right
from collections import defaultdict, deque

WINDOWS = (5, 30, 90, 300, 900, 3600)
MIN_WALLETS = 3
COOLDOWN_S = 21600
PRICE_MIN, PRICE_MAX = 0.01, 0.35
MIN_USD = 100.0
FRESH_S = 7 * 86400
SHOCK_S, SHOCK_MOVE = 900, 0.05
BANDS = ((0.01, 0.10), (0.10, 0.20), (0.20, 0.35000001))
SEED = 20261102
CROWD_S = 86400
CROWD_TOPS = (2, 5, 10, 30)
TOTAL_TOPS = (5, 15, 50, 150)


def band_of(price):
    for i, (low, high) in enumerate(BANDS):
        if low <= price < high:
            return i
    return None


def entrants(rows, first_seen, counts=None):
    """rows: one market, any order, as dicts wallet, side, token, size, price, ts, seq. Returns entrant buys in time order, and the price history per token. `counts` receives why a wallet's first row was not an entrant."""
    ordered = sorted(rows, key=lambda r: (r['ts'], r['seq']))
    seen, out, history = set(), [], defaultdict(list)
    for r in ordered:
        known = r['wallet'] in seen
        seen.add(r['wallet'])
        usd = r['size'] * r['price']
        if not known:
            if r['side'] != 'BUY':
                reason = 'first_row_is_sell'
            elif not PRICE_MIN <= r['price'] <= PRICE_MAX:
                reason = 'first_row_price_out_of_range'
            elif usd < MIN_USD:
                reason = 'first_row_under_100'
            else:
                reason = None
            if reason is None:
                first = first_seen.get(r['wallet'], r['ts'])
                out.append(dict(wallet=r['wallet'], token=r['token'], ts=r['ts'], price=r['price'], usd=usd, fresh=int(r['ts'] - first <= FRESH_S)))
            elif counts is not None:
                counts[reason] += 1
        history[r['token']].append((r['ts'], r['price']))
    return out, history


def shock_before(history, start):
    """Move of the last traded price over the 900 s before `start`, read only from rows before it. None when there is no row before that span: unknown, not absent."""
    last, base = None, None
    for ts, price in history:
        if ts >= start:
            break
        last = price
        if ts <= start - SHOCK_S:
            base = price
    if last is None or base is None:
        return None
    return abs(last - base) >= SHOCK_MOVE


def bursts(entries, window, history=None):
    """Trigger events for one token, in time order. A row belongs to the burst if it is one of the wallets counted at a trigger."""
    live, last_trigger, events, members = deque(), None, [], set()
    for i, e in enumerate(sorted(entries, key=lambda x: x['ts'])):
        while live and live[0][0]['ts'] <= e['ts'] - window:
            live.popleft()
        live.append((e, i))
        wallets = {x['wallet'] for x, _ in live}
        if len(wallets) >= MIN_WALLETS:
            if last_trigger is None or e['ts'] - last_trigger >= COOLDOWN_S:
                last_trigger = e['ts']
                rows = [x for x, _ in live]
                usd = sum(x['usd'] for x in rows)
                mean = usd / len(rows)
                spread = (sum((x['usd'] - mean) ** 2 for x in rows) / len(rows)) ** .5
                start = rows[0]['ts']
                events.append(dict(token=e['token'], window=window, ts=e['ts'], start=start, wallets=len(wallets), usd=usd, vwap=usd / sum(x['usd'] / x['price'] for x in rows), cv=spread / mean if mean else 0, fresh_share=sum(x['fresh'] for x in rows) / len(rows), shock=shock_before(history, start) if history is not None else None))
            members.update(j for _, j in live)
    return events, members


def crowd_bucket(count):
    for i, top in enumerate(CROWD_TOPS):
        if count <= top:
            return i
    return len(CROWD_TOPS)


def total_bucket(count):
    for i, top in enumerate(TOTAL_TOPS):
        if count <= top:
            return i
    return len(TOTAL_TOPS)


def add_crowd(burst_rows, entrant_rows):
    """Two matching keys on every row. `crowd`: entrants of the token in the 24 hours up to the row, earlier rows only. `total`: entrants of the token over its whole life, which looks ahead and so serves matching only, never a detector."""
    times = defaultdict(list)
    for r in entrant_rows:
        times[r['token']].append(r['ts'])
    for values in times.values():
        values.sort()
    for r in list(burst_rows) + list(entrant_rows):
        values = times.get(r['token'], [])
        r['crowd'] = bisect_right(values, r['ts']) - bisect_right(values, r['ts'] - CROWD_S)
        r['total'] = len(values)


def cell_of(r):
    return crowd_bucket(r['crowd']), total_bucket(r['total'])


def excess_table(burst_rows, base_rows):
    """Sums per event and per cell (price band, crowd bucket, total bucket): [burst excess, burst count, entrant excess, entrant count]."""
    groups = defaultdict(dict)
    for rows, price_key, first in ((burst_rows, 'vwap', 0), (base_rows, 'price', 2)):
        for r in rows:
            band = band_of(r[price_key])
            if band is None:
                continue
            cell = groups[r['group']].setdefault((band,) + cell_of(r), [0.0, 0, 0.0, 0])
            cell[first] += r['win'] - r[price_key]
            cell[first + 1] += 1
    return groups


def difference(cells):
    """Mean excess of bursts minus mean excess of entrants in the same cell, weighted by bursts. A burst with no comparable entrant is left out. None if nothing is comparable."""
    totals = {}
    for group in cells:
        for key, cell in group.items():
            total = totals.get(key)
            if total is None:
                totals[key] = list(cell)
            else:
                for i in range(4):
                    total[i] += cell[i]
    value, weight = 0.0, 0
    for s_b, c_b, s_e, c_e in totals.values():
        if c_b and c_e:
            value += c_b * (s_b / c_b - s_e / c_e)
            weight += c_b
    return value / weight if weight else None


def matched_share(cells):
    totals = {}
    for group in cells:
        for key, cell in group.items():
            total = totals.setdefault(key, [0, 0])
            total[0] += cell[1]
            total[1] += cell[3]
    all_bursts = sum(t[0] for t in totals.values())
    return sum(t[0] for t in totals.values() if t[1]) / all_bursts if all_bursts else None


def bootstrap(groups, draws=4000, seed=SEED, alpha=0.05 / 6):
    """Cluster bootstrap on events. Two-sided p from the share of resamples on the far side of zero. None when too little to compare."""
    cells = list(groups.values())
    observed = difference(cells)
    if observed is None or len(cells) < 2:
        return dict(diff=observed, p=None, low=None, high=None, draws=0, clusters=len(cells), matched_share=matched_share(cells))
    rng = random.Random(seed)
    values = []
    for _ in range(draws):
        value = difference(rng.choices(cells, k=len(cells)))
        if value is not None:
            values.append(value)
    values.sort()
    below = sum(v <= 0 for v in values)
    above = sum(v >= 0 for v in values)
    p = min(1.0, 2 * (min(below, above) + 1) / (len(values) + 1))
    index = lambda q: values[min(len(values) - 1, int(q * len(values)))]
    return dict(diff=observed, p=p, low=index(alpha / 2), high=index(1 - alpha / 2), draws=len(values), clusters=len(cells), matched_share=matched_share(cells))


def verdict(all_splits, valid, test, placebo, h2, threshold=0.05 / 6):
    """The plan's rule for one window, nothing else."""
    if all_splits['p'] is None or all_splits['diff'] is None or all_splits['p'] >= threshold or all_splits['diff'] <= 0:
        return 'NOT_SUPPORTED'
    if valid['diff'] is None or test['diff'] is None or valid['diff'] <= 0 or test['diff'] <= 0:
        return 'NOT_SUPPORTED'
    if placebo['p'] is not None and placebo['diff'] is not None and placebo['diff'] > 0 and placebo['p'] < threshold:
        return 'NOT_SUPPORTED'
    if h2['p'] >= threshold:
        return 'NOT_SUPPORTED'
    return 'PREDICTIVE_TIMING_PATTERN'


def benjamini_hochberg(pairs, q=0.05):
    ordered = sorted(pairs, key=lambda x: x[1])
    keep = 0
    for i, (_, p) in enumerate(ordered, 1):
        if p <= q * i / len(ordered):
            keep = i
    return {name for name, _ in ordered[:keep]}


def by_token(entrants):
    out = defaultdict(list)
    for r in entrants:
        out[r['token']].append(r)
    return out


def jittered_triggers(tokens, window, rng):
    """Triggers after each row moves within plus or minus 10 windows, so local intensity stays. One row is one wallet in one market, so wallets stay distinct."""
    triggers = 0
    for token, rows in tokens.items():
        if len(rows) < MIN_WALLETS:
            continue
        span = 10 * window
        moved = sorted((dict(wallet=i, token=token, ts=r['ts'] + rng.uniform(-span, span), price=r['price'], usd=r['usd'], fresh=r['fresh']) for i, r in enumerate(rows)), key=lambda x: x['ts'])
        triggers += len(bursts(moved, window)[0])
    return triggers


def compare(burst_rows, entrant_rows, window, keep_burst=lambda r: True, keep_base=lambda r: True, draws=4000, seed=SEED):
    chosen = [r for r in burst_rows if r['window'] == window and keep_burst(r)]
    base = [r for r in entrant_rows if window not in r['burst_windows'] and keep_base(r)]
    result = bootstrap(excess_table(chosen, base), draws=draws, seed=seed)
    result.update(n_bursts=len(chosen), n_base=len(base), events_bursts=len({r['group'] for r in chosen}), events_base=len({r['group'] for r in base}))
    return result


def label_placebo(burst_rows, entrant_rows, window, draws=4000, seed=SEED):
    """Each burst takes the outcome of a random entrant of its cell and split: no information can remain."""
    rng = random.Random(seed + window)
    pools = defaultdict(list)
    for r in entrant_rows:
        pools[(band_of(r['price']),) + cell_of(r) + (r['split'],)].append(r['win'])
    moved = []
    for r in burst_rows:
        if r['window'] == window and band_of(r['vwap']) is not None:
            pool = pools.get((band_of(r['vwap']),) + cell_of(r) + (r['split'],))
            if pool:
                moved.append(dict(r, win=rng.choice(pool)))
    return bootstrap(excess_table(moved, [r for r in entrant_rows if window not in r['burst_windows']]), draws=draws, seed=seed + window)


def h2_test(entrant_rows, window, draws=499, seed=SEED):
    """Are triggers more frequent than local intensity allows?"""
    tokens = by_token(entrant_rows)
    observed = 0
    for token, rows in tokens.items():
        ordered = sorted((dict(wallet=i, token=token, ts=r['ts'], price=r['price'], usd=r['usd'], fresh=r['fresh']) for i, r in enumerate(rows)), key=lambda x: x['ts'])
        observed += len(bursts(ordered, window)[0])
    counts = [jittered_triggers(tokens, window, random.Random(seed + 7000 * window + d)) for d in range(draws)]
    return dict(observed=observed, null_median=sorted(counts)[draws // 2], null_max=max(counts), p=(1 + sum(c >= observed for c in counts)) / (draws + 1), draws=draws)
