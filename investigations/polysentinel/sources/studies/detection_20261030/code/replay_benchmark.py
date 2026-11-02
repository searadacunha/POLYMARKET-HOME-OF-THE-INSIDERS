"""Synthetic timing at neutral corpus dimensions; no historical corpus is read."""
import json
import statistics
import time

from replay_core import START, CUTOFF, HERE, kernel
from replay_fast import WalletCache
from replay_selfcheck import trade


def benchmark():
    config = json.loads((HERE / 'vendor/config.json').read_text())
    module = kernel()
    n = 15148
    rows = []
    for i in range(n):
        wallet = 'wallet-0' if i < 1285 else 'wallet-' + str(1 + (i - 1285) % 1300)
        row = trade(i, START + int(i * (CUTOFF - START - 60) / n), wallet=wallet,
                    nominal=1200 if i % 7 == 0 else 10)
        row['observed_at'] = row['timestamp']
        rows.append(row)
    measurements = []
    for fraction in (.1, .5, 1):
        selected = rows[:int(n * fraction)]
        timings = []
        for _ in range(3):
            before = time.perf_counter()
            cases = module.evaluate(selected, [], [], now=selected[-1]['timestamp'], config=config)
            timings.append(time.perf_counter() - before)
        measurements.append(dict(rows=len(selected), calls=3, median_seconds=statistics.median(timings),
                                 min_seconds=min(timings), max_seconds=max(timings), synthetic_cases=len(cases)))
    cache = WalletCache(module)
    timings = []
    for end in range(n - 100, n + 1):
        selected = sorted(rows[:end], key=lambda r: (-r['timestamp'], r['id']))
        before = time.perf_counter()
        cache.evaluate(selected, now=selected[0]['timestamp'], config=config, wallet_history={}, diagnostics={})
        elapsed = time.perf_counter() - before
        if end != n - 100:
            timings.append(elapsed)
    cached = dict(measured_calls=len(timings), warmup_calls=1,
                  median_seconds=statistics.median(timings), max_seconds=max(timings),
                  mean_seconds=statistics.mean(timings),
                  illustration_seconds_34440_calls=34440 * statistics.mean(timings))
    return dict(dataset='synthetic-only', n_rows=n, n_wallets=1301, max_rows_per_wallet=1285,
                measurements=measurements,
                cached_measurements=cached,
                illustration_seconds_34440_calls_at_full_size=34440 * measurements[-1]['median_seconds'],
                limitation='Synthetic uniform event times and nominal mix; not a bound on real runtime. Full replay also ranks and accumulates records.')


if __name__ == '__main__':
    print(json.dumps(benchmark(), indent=2, sort_keys=True))
