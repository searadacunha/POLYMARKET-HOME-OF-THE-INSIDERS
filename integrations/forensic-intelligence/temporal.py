"""Exploratory synchronized-entry tests. No win/outcome, PnL or future price is an input."""
from __future__ import annotations
import random
from collections import defaultdict
from itertools import combinations
from statistics import median
from ledger import utc_seconds, decimal_value

WINDOWS = (5, 30, 60, 300, 900, 3600)


def observed_trades(trades, as_of_utc):
    cutoff = utc_seconds(as_of_utc)
    out, seen = [], {}
    required = {'wallet', 'market_id', 'outcome_id', 'timestamp_utc', 'observed_at_utc', 'transaction_hash', 'nominal', 'price'}
    for row in trades:
        if required - row.keys():
            raise ValueError('Missing trade fields')
        at, seen_at = utc_seconds(row['timestamp_utc']), utc_seconds(row['observed_at_utc'])
        price, nominal = decimal_value(row['price']), decimal_value(row['nominal'])
        if not 0 < price <= 1 or nominal <= 0:
            raise ValueError('Invalid price or nominal')
        # The same wallet may fill multiple orders within one transaction.
        # A distinct log or explicit fill/order identifier is required to split them.
        trade_key = (row.get('chain_id'), row['transaction_hash'].lower(), row.get('log_index'),
                     row.get('fill_id', row.get('order_hash')), row['wallet'].lower(),
                     row['market_id'], row['outcome_id'])
        material = (at, seen_at, price, nominal, row.get('side'))
        if trade_key in seen:
            if seen[trade_key] != material:
                raise ValueError(f'Conflicting observed trade for same fill identity: {trade_key}')
            continue
        seen[trade_key] = material
        if seen_at <= cutoff and at <= cutoff:
            # Retain the recorded spelling while using one identity throughout
            # the observed statistic and the wallet-train randomization.
            out.append({**row, '_time': at, '_wallet': row['wallet'].lower()})
    return out


def synchronized_pairs(trades, as_of_utc, windows=WINDOWS):
    rows = observed_trades(trades, as_of_utc)
    buckets = defaultdict(list)
    for row in rows:
        buckets[row['market_id'], row['outcome_id']].append(row)
    output = {}
    for (market, outcome), bucket in buckets.items():
        bucket.sort(key=lambda x: x['_time'])
        for left, row in enumerate(bucket):
            for other in bucket[left + 1:]:
                dt = other['_time'] - row['_time']
                if dt > max(windows):
                    break
                if row['wallet'].lower() == other['wallet'].lower():
                    continue
                a, b = sorted([row['wallet'].lower(), other['wallet'].lower()])
                for w in windows:
                    if dt <= w:
                        k = (market, outcome, w, a, b)
                        output.setdefault(k, {'market_id': market, 'outcome_id': outcome, 'window_s': w,
                            'wallet_a': a, 'wallet_b': b, 'min_delta_s': dt, 'tx_pairs': []})
                        entry = output[k]
                        entry['min_delta_s'] = min(entry['min_delta_s'], dt)
                        entry['tx_pairs'].append([row['transaction_hash'], other['transaction_hash']])
    return [output[k] for k in sorted(output)]


def circular_shift_null(trades, as_of_utc, window_s=60, simulations=199, seed=20261102):
    """Shift complete wallet trains within each market/outcome without reshuffling trade-level
    bursts. Null is conditional on observed sample + chosen horizon; exploratory only.
    """
    if window_s not in WINDOWS or simulations < 1:
        raise ValueError('Invalid requested test')
    rows = observed_trades(trades, as_of_utc)
    groups = defaultdict(list)
    for row in rows:
        groups[(row['market_id'], row['outcome_id'])].append(row)
    def statistic(values):
        counts = 0
        for records in values.values():
            ordered = sorted(records, key=lambda r: r['_time'])
            counted = set()
            for i, a in enumerate(ordered):
                for b in ordered[i + 1:]:
                    if b['_time'] - a['_time'] > window_s:
                        break
                    if a['_wallet'] == b['_wallet']:
                        continue
                    counted.add(tuple(sorted((a['_wallet'], b['_wallet']))))
            counts += len(counted)
        return counts
    observed = statistic(groups)
    rng = random.Random(seed)
    null = []
    for _ in range(simulations):
        shifted = defaultdict(list)
        for key, bucket in groups.items():
            if len(bucket) < 2:
                shifted[key] = bucket
                continue
            start = min(r['_time'] for r in bucket)
            # Do not claim precision below the selected visible horizon.
            span = max(window_s * 20, max(r['_time'] for r in bucket) - start + window_s)
            offsets = {wallet: rng.uniform(0, span) for wallet in sorted({r['_wallet'] for r in bucket})}
            shifted[key] = [{**r, '_time': start + ((r['_time'] - start + offsets[r['_wallet']]) % span)} for r in bucket]
        null.append(statistic(shifted))
    return {'observed_pairs': observed, 'null_median': median(null),
            'null_ge_observed': sum(x >= observed for x in null),
            'p_value': (1 + sum(x >= observed for x in null)) / (simulations + 1),
            'simulations': simulations, 'seed': seed,
            'status': 'EXPLORATORY_NOT_VALIDATED',
            'null_assumptions': 'independent wallet-train circular shifts; selection and liquidity confounding remain'}
