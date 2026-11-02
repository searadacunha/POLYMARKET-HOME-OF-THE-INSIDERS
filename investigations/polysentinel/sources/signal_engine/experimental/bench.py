"""Reproducible comparison of change detectors on real rows, with no insider labels anywhere.

Measures trigger rates, chance rates under shuffled order, detection and delay on injected patterns, and
what each stream contributes. Injections prove mechanics on that pattern, not sensitivity to real insiders.
Real wallets change for ordinary reasons, so a trigger on real rows is a load, not a false positive.
The engine's state is purged after 14 days, so --snapshot freezes the rows to a file and --rows reads them back.
Usage: python -m signal_engine.experimental.bench [--seed N] [--out FILE] [--wallets N] [--rows FILE] [--snapshot FILE]
"""
import argparse
import gzip
import hashlib
import json
import os
import random
import resource
import sqlite3
import statistics
import time
from collections import defaultdict
from pathlib import Path

from ..wallet_behavior import fill_groups
from . import sequential as seq
from .splits import Groups, assert_no_leak, temporal_group_split

STATE = Path(os.environ.get('SIGNAL_ENGINE_STATE', Path.home() / '.local/state/polysentinel-signal-engine')) / 'state.sqlite3'
T_FIN_REPLAY = 1792768669  # the replay's period and its case stay out of development and test
SPLIT_TS = 20755 * 86400 + 43200
EMBARGO_S = 86400
GRID_H = (4.0, 5.0, 6.0, 8.0, 10.0, 12.0)
GRID_K = (0.25, 0.5, 1.0)
GRID_OWN = (8, 20)
CHANCE_TARGET = 1.0  # at most this many alarms per 1000 scored wallet-days under shuffled order
STREAMS = dict(all=('size', 'rate', 'net'), size=('size',), rate=('rate',), net=('net',), size_rate=('size', 'rate'))
SCENARIOS = dict(sustained_x2=('sustained', 2), sustained_x5=('sustained', 5), sustained_x20=('sustained', 20), burst_x5=('burst', 5), burst_x20=('burst', 20),
                 single_x20=('single', 20), single_x100=('single', 100), new_wallet_x5=('new', 5), new_wallet_x20=('new', 20), new_wallet_x100=('new', 100))


def load_rows(path=STATE, start=T_FIN_REPLAY):
    cx = sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=10)
    cx.row_factory = sqlite3.Row
    rows = [dict(r) for r in cx.execute('SELECT wallet, ts, observed_at, event_key, condition_id, token_id, is_buy, size, price, nominal, tx FROM trades WHERE ts>=? ORDER BY ts', (start,))]
    cx.close()
    return rows


def write_snapshot(rows, path):
    with gzip.GzipFile(path, 'wb', mtime=0) as f:
        f.write('\n'.join(json.dumps(r, sort_keys=True, separators=(',', ':')) for r in rows).encode())


def read_snapshot(path):
    with gzip.open(path, 'rt') as f:
        return [json.loads(line) for line in f]


def by_wallet(rows):
    out = defaultdict(list)
    for r in rows:
        out[r['wallet']].append(r)
    return {w: fill_groups(v) for w, v in out.items()}


def active_days(groups, own_minimum=0):
    """Days with an observation past the minimum history: only those can alarm, so only those are a denominator."""
    return len({g['ts'] // 86400 for g in groups[own_minimum:]})


def references(groups_by_wallet):
    values = defaultdict(list)
    for groups in groups_by_wallet.values():
        for stream, _, x in seq.wallet_observations(groups):
            values[stream].append(x)
    return {s: seq.Reference(v) for s, v in values.items()}


def shuffled(groups, rng):
    """Same amounts, sides and gaps in random order, from the same start: only chance can remain."""
    if len(groups) < 2:
        return groups
    payload = [(g['nominal'], g['is_buy']) for g in groups]
    gaps = [b['ts'] - a['ts'] for a, b in zip(groups, groups[1:])]
    rng.shuffle(payload)
    rng.shuffle(gaps)
    out, ts = [], groups[0]['ts']
    for (nominal, is_buy), gap in zip(payload, [0] + gaps):
        ts += gap
        out.append(dict(ts=ts, nominal=nominal, is_buy=is_buy))
    return out


def rate_per_1000(alarms_by_wallet, days_by_wallet, rng, draws=500):
    """Wallet-level bootstrap: one wallet's alarms are not independent of each other."""
    wallets = sorted(days_by_wallet)
    total_days = sum(days_by_wallet.values())
    point = 1000 * sum(alarms_by_wallet.get(w, 0) for w in wallets) / total_days if total_days else None
    samples = []
    for _ in range(draws):
        picks = rng.choices(wallets, k=len(wallets))
        days = sum(days_by_wallet[w] for w in picks)
        samples.append(1000 * sum(alarms_by_wallet.get(w, 0) for w in picks) / days if days else 0.0)
    samples.sort()
    return dict(rate=point, low=samples[int(.025 * draws)], high=samples[int(.975 * draws)], wallet_days=total_days, wallets=len(wallets))


def wilson(hits, n, z=1.96):
    if not n:
        return dict(hits=0, n=0, rate=None, low=None, high=None)
    p = hits / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** .5) / (1 + z * z / n)
    return dict(hits=hits, n=n, rate=p, low=max(0.0, centre - half), high=min(1.0, centre + half))


def inject(kind, factor, groups, rng, population_median):
    """Returns (rows with the pattern, change time, end time). Real rows stay as they were before the change."""
    if kind == 'new':
        start = rng.randrange(SPLIT_TS, SPLIT_TS + 2 * 86400)
        fresh = [dict(ts=start + i * 1200, nominal=factor * population_median, is_buy=True) for i in range(3)]
        return fresh, start, start + 2400
    buys = [i for i, g in enumerate(groups) if g['is_buy']]
    median = statistics.median(groups[i]['nominal'] for i in buys)
    if kind == 'sustained':
        at = rng.randrange(len(buys) // 3, len(buys) - 5)
        changed = set(buys[at:at + 10])
        out = [dict(g, nominal=g['nominal'] * factor) if i in changed else g for i, g in enumerate(groups)]
        return out, groups[buys[at]]['ts'], groups[buys[min(at + 9, len(buys) - 1)]]['ts']
    start = groups[rng.randrange(len(groups) // 3, len(groups))]['ts']
    extra = [dict(ts=start + i * 600 + 1, nominal=factor * median, is_buy=True) for i in range(1 if kind == 'single' else 5)]
    return sorted(groups + extra, key=lambda g: g['ts']), start + 1, extra[-1]['ts']


def choose_threshold(dev_groups, seed):
    """On development wallets only, against shuffled order, before the test side is read."""
    rng = random.Random(seed)
    table = []
    for own in GRID_OWN:
        days = sum(active_days(g, own) for g in dev_groups.values())
        for k in GRID_K:
            for h in GRID_H:
                params = dict(seq.DEFAULTS, k=k, h=h, own_minimum=own)
                alarms = sum(len(seq.scan_wallet(shuffled(g, rng), params)) for g in dev_groups.values())
                table.append(dict(own_minimum=own, k=k, h=h, alarms=alarms, scored_wallet_days=days, per_1000=1000 * alarms / days))
    # At the target, lowest h is fastest, then the shorter history covers more wallets, then the larger k forgets noise sooner.
    passing = [t for t in table if t['per_1000'] <= CHANCE_TARGET]
    return (min(passing, key=lambda t: (t['h'], t['own_minimum'], -t['k'])) if passing else None), table


def evaluate_scenarios(test_groups, burn_groups, pops, params, seed, wallets_per_scenario):
    rng = random.Random(seed + 1)
    population_median = pops['size'].sorted[len(pops['size']) // 2]
    eligible = sorted(w for w, g in test_groups.items() if sum(x['is_buy'] for x in burn_groups.get(w, [])) + sum(x['is_buy'] for x in g) >= 30 and sum(x['is_buy'] for x in g) >= 12)
    out = {}
    for name, (kind, factor) in SCENARIOS.items():
        picks = rng.sample(eligible, min(wallets_per_scenario, len(eligible))) if kind != 'new' else [f'fresh{i}' for i in range(wallets_per_scenario)]
        hits = defaultdict(int)
        delays = defaultdict(list)
        for wallet in picks:
            history = burn_groups.get(wallet, [])
            rows, change, end = inject(kind, factor, test_groups.get(wallet, []), rng, population_median)
            full = history + rows
            methods = {f'cusum_{label}': seq.scan_wallet(full, params, streams=streams) for label, streams in STREAMS.items()}
            methods['quantile'] = seq.quantile_rule(full, pops['size'])
            methods['robust'] = seq.robust_rule(full)
            for method, alarms in methods.items():
                caught = [a['ts'] for a in alarms if change <= a['ts'] <= end]
                if caught:
                    hits[method] += 1
                    delays[method].append(caught[0] - change)
        out[name] = {m: dict(wilson(hits[m], len(picks)), median_delay_s=statistics.median(delays[m]) if delays[m] else None) for m in [f'cusum_{l}' for l in STREAMS] + ['quantile', 'robust']}
    return out, len(eligible)


def event_stream(test_rows, params, seed):
    """Distinct buyers per hour on one event against its own past, and an injected convergence."""
    by_event = defaultdict(list)
    for event, ts, n in seq.event_hours(test_rows):
        by_event[event].append((ts, n))
    rng = random.Random(seed + 2)
    alarms = 0
    hours = sum(len(v) for v in by_event.values())
    for values in by_event.values():
        stream = seq.StreamCusum(params)
        alarms += sum(1 for ts, n in values if stream.update(ts, n))
    picks = rng.sample(sorted(by_event), min(200, len(by_event)))
    injected = {}
    for extra in (3, 5, 10, 20):
        hits = 0
        for event in picks:
            values = by_event[event]
            at = rng.randrange(len(values) // 2, len(values)) if len(values) > 1 else 0
            stream = seq.StreamCusum(params)
            # Three consecutive hours: a one-hour jump adds at most one bounded score.
            hits += any(stream.update(ts, n + extra if at <= i < at + 3 else n) and at <= i for i, (ts, n) in enumerate(values))
        injected[f'plus_{extra}_wallets_per_hour_3h'] = wilson(hits, len(picks))
    return dict(events=len(by_event), event_hours=hours, alarms=alarms, alarms_per_1000_event_hours=1000 * alarms / hours if hours else None, injected=injected)


def run(rows, seed=20261101, wallets_per_scenario=200, groups=None):
    split = temporal_group_split(rows, SPLIT_TS, EMBARGO_S, groups)
    assert_no_leak(split, SPLIT_TS, EMBARGO_S, groups)
    dev, burn, test = by_wallet(split['dev']), by_wallet(split['burn_in']), by_wallet(split['test'])
    pops = references(dev)
    chosen, grid = choose_threshold(dev, seed)
    params = dict(seq.DEFAULTS, k=chosen['k'], h=chosen['h'], own_minimum=chosen['own_minimum']) if chosen else None
    result = dict(seed=seed, split=dict(split_ts=SPLIT_TS, embargo_s=EMBARGO_S, dev_rows=len(split['dev']), burn_in_rows=len(split['burn_in']), test_rows=len(split['test']), dropped_embargo=split['dropped_embargo'],
                                        test_rows_on_events_unseen_in_dev=split['test_rows_on_unseen_events'], dev_wallets=len(dev), test_wallets=len(test)),
                  chance_target_per_1000=CHANCE_TARGET, threshold_grid=grid, chosen=chosen)
    if not params:
        result['verdict'] = 'NO_THRESHOLD_MET_THE_CHANCE_TARGET'
        return result
    rng = random.Random(seed + 3)
    days = {w: active_days(burn.get(w, []) + g, params['own_minimum']) for w, g in test.items()}
    days = {w: d for w, d in days.items() if d}
    methods = {f'cusum_{label}': (lambda g, s=streams: seq.scan_wallet(g, params, streams=s)) for label, streams in STREAMS.items()}
    methods.update(quantile=lambda g: seq.quantile_rule(g, pops['size']), robust=seq.robust_rule)
    triggers = {}
    for name, method in methods.items():
        real, chance = {}, {}
        for wallet in days:
            groups, history = test[wallet], burn.get(wallet, [])
            real[wallet] = sum(a['ts'] >= SPLIT_TS + EMBARGO_S for a in method(history + groups))
            chance[wallet] = sum(a['ts'] >= SPLIT_TS + EMBARGO_S for a in method(history + shuffled(groups, rng)))
        triggers[name] = dict(real=rate_per_1000(real, days, rng), shuffled=rate_per_1000(chance, days, rng))
    result['trigger_rates_test'] = triggers
    result['scenarios'], result['wallets_eligible_for_injection'] = evaluate_scenarios(test, burn, pops, params, seed, wallets_per_scenario)
    result['event_stream'] = event_stream(split['test'], params, seed)
    return result


def documented_links():
    """Wallets joined by a confirmed transfer stay on one side. Too many links only cost data; none is an owner."""
    from .funding_bench import confirmed_transfer_pairs
    groups = Groups()
    for a, b, tx in confirmed_transfer_pairs():
        groups.link(a, b, tx)
    return groups


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed', type=int, default=20261101)
    p.add_argument('--wallets', type=int, default=200)
    p.add_argument('--out', default=None)
    p.add_argument('--rows', default=None)
    p.add_argument('--snapshot', default=None)
    a = p.parse_args()
    started = time.time()
    rows = read_snapshot(a.rows) if a.rows else load_rows()
    if a.snapshot:
        write_snapshot(rows, a.snapshot)
        print(json.dumps(dict(rows=len(rows), sha256=hashlib.sha256(Path(a.snapshot).read_bytes()).hexdigest())))
        return 0
    result = run(rows, a.seed, a.wallets, documented_links())
    if a.rows:
        result['rows_sha256'] = hashlib.sha256(Path(a.rows).read_bytes()).hexdigest()
    package = Path(__file__).parent
    result.update(rows=len(rows), source=str(STATE.name), code={f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(package.glob('*.py'))},
                  seconds=time.time() - started, max_rss_mb=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1048576)
    text = json.dumps(result, indent=1, sort_keys=True, default=str)
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(text)
    print(json.dumps({k: result[k] for k in ('chosen', 'split', 'rows', 'seconds', 'max_rss_mb')}, indent=0))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
