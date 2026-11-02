"""Blind, conditional transaction replay; never evidence of historical collection.

Run only after root freezes method, code and sanitized inputs. Source observed_at
is retained in the caller's rows. An explicitly hypothetical availability clock is
adapted to the vendored kernel's observed_at parameter in memory only.
"""
from bisect import bisect_right
from collections import Counter, defaultdict
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path

START = 1790176669
CUTOFF = 1792768669
CADENCE = 60
DELAYS = (0, 60, 300, 900)
ORACLE_TICKS = tuple(START + (i * 43199 // 63) * CADENCE for i in range(64))
MAX_OUTPUT = 20_000_000
HERE = Path(__file__).resolve().parent
ALLOWED = {'id', 'wallet', 'side', 'timestamp', 'observed_at', 'token_id',
           'transaction_hash', 'order_hash', 'size', 'price', 'market_id',
           'event_id', 'condition_id'}


def kernel():
    spec = importlib.util.spec_from_file_location('frozen_replay_signals', HERE / 'vendor/signals.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prepare(trades, *, start=START, cutoff=CUTOFF):
    """Fail closed on unapproved columns/economics; count every dropped row."""
    counts = Counter(input_rows=0, duplicate_rows=0, before_window=0, at_or_after_cutoff=0)
    seen, groups, kept = {}, {}, []
    for original in trades:
        counts['input_rows'] += 1
        if not isinstance(original, dict) or set(original) - ALLOWED:
            raise ValueError('Unapproved input columns; labels and metadata must be removed upstream')
        row = dict(original)
        for field in ('id', 'wallet', 'token_id', 'market_id', 'event_id', 'condition_id'):
            if not isinstance(row.get(field), str) or not row[field]:
                raise ValueError('Missing/non-string identity field: ' + field)
        for field in ('market_id', 'event_id', 'condition_id', 'transaction_hash', 'order_hash'):
            if row.get(field) is not None and not isinstance(row[field], str):
                raise ValueError('Non-string optional identity field: ' + field)
        row['wallet'] = row['wallet'].lower()
        if not isinstance(row.get('observed_at'), (int, float)) or isinstance(row['observed_at'], bool):
            raise ValueError('Source observed_at must be a finite number')
        for field in ('timestamp', 'observed_at', 'size', 'price'):
            if isinstance(row.get(field), bool):
                raise ValueError('Boolean economics/time field: ' + field)
            try:
                row[field] = float(row[field])
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError('Invalid numeric field: ' + field) from exc
            if not math.isfinite(row[field]):
                raise ValueError('Non-finite field: ' + field)
        if row['size'] <= 0 or not 0 <= row['price'] <= 1 or row.get('side') not in ('BUY', 'SELL'):
            raise ValueError('Invalid trade economics')
        signature = {k: v for k, v in row.items() if k != 'observed_at'}
        if row['id'] in seen:
            if seen[row['id']] != signature:
                raise ValueError('Conflicting duplicate trade: ' + row['id'])
            counts['duplicate_rows'] += 1
            continue
        seen[row['id']] = signature
        if row['timestamp'] < start:
            counts['before_window'] += 1
        elif row['timestamp'] >= cutoff:
            counts['at_or_after_cutoff'] += 1
        else:
            group = (row['wallet'], row['token_id'], row['side'],
                     row.get('order_hash') or row.get('transaction_hash') or row['id'])
            mapping = (row.get('event_id'), row.get('market_id'), row.get('condition_id'))
            if group in groups and groups[group] != mapping:
                raise ValueError('Conflicting mappings within a fill group')
            groups[group] = mapping
            kept.append(row)
    kept.sort(key=lambda r: (r['timestamp'], r['id']))
    counts['eligible_unique_rows'] = len(kept)
    assert counts['input_rows'] == sum(counts[k] for k in ('duplicate_rows', 'before_window', 'at_or_after_cutoff', 'eligible_unique_rows'))
    return kept, dict(counts)


def event_key(row):
    return row.get('event_id') or 'unmapped:' + str(row.get('condition_id') or row['token_id'])


def decision_ticks(rows, delay, window, *, start=START, cutoff=CUTOFF, dense=False):
    """Skipping unchanged ticks preserves scores, ranks and first detections."""
    last = start + math.floor((cutoff - start - 1) / CADENCE) * CADENCE
    if dense:
        return list(range(start, last + 1, CADENCE))
    ticks = {start, last}
    for row in rows:
        arrival = start + math.ceil((row['timestamp'] + delay - start) / CADENCE) * CADENCE
        # Native recent test is >=; expiry therefore occurs strictly after t+window.
        expiry = start + (math.floor((row['timestamp'] + window - start) / CADENCE) + 1) * CADENCE
        if start <= arrival <= last:
            ticks.add(arrival)
        if start <= expiry <= last:
            ticks.add(expiry)
    return sorted(ticks)


def ranks(scores):
    frequencies = Counter(scores.values())
    by_score, ahead = {}, 0
    for score, frequency in sorted(frequencies.items(), reverse=True):
        by_score[score] = ahead + 1
        ahead += frequency
    return {key: by_score[score] for key, score in scores.items()}


def empty_record(**identity):
    return dict(**identity, present_in_corpus=True, evaluated_ever=False,
                context_present_ever=False, context_present_last_regular=False, context_present_final=False,
                recent_buy_evaluated_ever=False, first_available_at=None,
                first_signal_at=None, rank_at_first_signal=None,
                first_conditional_priority_at=None, rank_at_first_conditional_priority=None,
                best_score=None, best_rank=None, best_rank_denominator=None,
                best_score_at=None, best_score_reasons=[], first_signals={},
                final_diagnostic_score=None, final_diagnostic_rank=None,
                last_regular_score=None, last_regular_rank=None, last_regular_conditional_priority=None,
                final_diagnostic_conditional_priority=None, exact_detector_status='unknown',
                actual_historical_priority=None, actual_historical_alert=None)


def accumulate(record, score, rank, denominator, cases, at, priority_threshold, recent_buy):
    record['evaluated_ever'] = True
    record['recent_buy_evaluated_ever'] |= recent_buy
    signals = [s for case in cases for s in case['signals']]
    if record['best_score'] is None or score > record['best_score']:
        record.update(best_score=score, best_score_at=at,
                      best_score_reasons=sorted({s['rule'] for case in cases if case['score'] == score
                                                for s in case['signals']}))
    if record['best_rank'] is None or rank < record['best_rank']:
        record.update(best_rank=rank, best_rank_denominator=denominator)
    if signals and record['first_signal_at'] is None:
        record.update(first_signal_at=at, rank_at_first_signal=dict(rank=rank, denominator=denominator))
    if signals and score >= priority_threshold and record['first_conditional_priority_at'] is None:
        record.update(first_conditional_priority_at=at,
                      rank_at_first_conditional_priority=dict(rank=rank, denominator=denominator))
    for signal in signals:
        record['first_signals'].setdefault(signal['rule'], dict(
            at=at, family=signal['family'], value=signal['value'], n=signal['n'],
            weight=signal['weight'], quality=signal['quality']))


def replay_delay(rows, config, delay, *, start=START, cutoff=CUTOFF, dense=False, progress=None, fast=True):
    module = kernel()
    if fast:
        from replay_fast import WalletCache
        cache = WalletCache(module)
    window = float(config.get('signal_window_seconds', 86400))
    limit = int(config.get('analysis_trade_limit', 50000))
    if limit <= 0:
        raise ValueError('Nonpositive analysis_trade_limit')
    threshold = config.get('candidate_score', 2)
    by_wallet = {r['wallet']: empty_record(wallet=r['wallet']) for r in rows}
    by_pair = {(r['wallet'], event_key(r)): empty_record(wallet=r['wallet'], event_id=event_key(r)) for r in rows}
    timestamps = [r['timestamp'] for r in rows]
    wallet_history, history_cursor = {}, 0
    ticks = decision_ticks(rows, delay, window, start=start, cutoff=cutoff, dense=dense)
    oracle_ticks = set(ORACLE_TICKS) if fast and start == START and cutoff == CUTOFF else set()
    ticks = sorted(set(ticks) | oracle_ticks)
    oracle_checks = 0
    total_examined = 0
    executed_examined = 0
    max_selected = 0
    units_ever_examined = set()
    final_diagnostics = None
    for tick_index, at in enumerate(ticks + [cutoff - 1], 1):
        final = at == cutoff - 1
        available_end = bisect_right(timestamps, at - delay)
        while history_cursor < available_end:
            source = rows[history_cursor]
            wallet = source['wallet']
            history = wallet_history.setdefault(wallet, dict(first_timestamp=source['timestamp'], observations=0))
            history['observations'] += 1
            availability = source['timestamp'] + delay
            for record in (by_wallet[wallet], by_pair[wallet, event_key(source)]):
                if record['first_available_at'] is None:
                    record['first_available_at'] = availability
            history_cursor += 1
        # Same order and limit as engine.payloads; source dictionaries stay untouched.
        selected = sorted(rows[:available_end], key=lambda r: (-r['timestamp'], r['id']))[:limit]
        adapted = [dict(r, observed_at=r['timestamp'] + delay) for r in selected]
        diagnostics = {}
        if fast:
            cases = cache.evaluate(adapted, now=at, config=config, wallet_history=wallet_history, diagnostics=diagnostics)
            if at in oracle_ticks:
                oracle_diagnostics = {}
                oracle_cases = module.evaluate(adapted, [], [], now=at, config=config,
                                               wallet_history=wallet_history, diagnostics=oracle_diagnostics)
                if cases != oracle_cases or diagnostics != oracle_diagnostics:
                    raise AssertionError(f'Cached/full kernel mismatch at delay={delay}, time={at}')
                oracle_checks += 1
        else:
            cases = module.evaluate(adapted, [], [], now=at, config=config,
                                    wallet_history=wallet_history, diagnostics=diagnostics)
        if progress is not None:
            progress(dict(delay_seconds=delay, evaluation=tick_index,
                          total_evaluations=len(ticks) + 1, decision_at=at, selected_rows=len(selected)))
        pair_cases = {(c['wallet'], c['event_id']): c for c in cases}
        selected_pairs = {(r['wallet'], event_key(r)) for r in selected}
        selected_wallets = {r['wallet'] for r in selected}
        recent_pairs = {(r['wallet'], event_key(r)) for r in selected
                        if r['side'] == 'BUY' and r['timestamp'] >= at - window}
        recent_wallets = {w for w, _ in recent_pairs}
        pair_scores = {key: pair_cases[key]['score'] if key in pair_cases else 0 for key in recent_pairs}
        wallet_scores = {wallet: 0 for wallet in recent_wallets}
        for (wallet, _), score in pair_scores.items():
            wallet_scores[wallet] = max(wallet_scores[wallet], score)
        pair_ranks, wallet_ranks = ranks(pair_scores), ranks(wallet_scores)
        wallet_cases = defaultdict(list)
        for case in cases:
            wallet_cases[case['wallet']].append(case)
        max_selected = max(max_selected, len(selected))
        for records, keys in ((by_wallet, selected_wallets), (by_pair, selected_pairs)):
            for key in keys:
                if final:
                    records[key]['context_present_final'] = True
                else:
                    records[key]['context_present_ever'] = True
                    if at == ticks[-1]:
                        records[key]['context_present_last_regular'] = True
        if final:
            final_diagnostics = diagnostics
            for records, scores, ranking in ((by_wallet, wallet_scores, wallet_ranks), (by_pair, pair_scores, pair_ranks)):
                for key, score in scores.items():
                    records[key].update(final_diagnostic_score=score, final_diagnostic_rank=ranking[key],
                                        final_diagnostic_conditional_priority=score >= threshold)
            continue
        represented_ticks = ((ticks[tick_index] - at) // CADENCE) if tick_index < len(ticks) else 1
        total_examined += diagnostics['examined_recent_buy_pairs'] * represented_ticks
        executed_examined += diagnostics['examined_recent_buy_pairs']
        units_ever_examined.update(recent_pairs)
        if at == ticks[-1]:
            for records, scores, ranking in ((by_wallet, wallet_scores, wallet_ranks), (by_pair, pair_scores, pair_ranks)):
                for key, score in scores.items():
                    records[key].update(last_regular_score=score, last_regular_rank=ranking[key],
                                        last_regular_conditional_priority=score >= threshold)
        for key, score in pair_scores.items():
            accumulate(by_pair[key], score, pair_ranks[key], len(pair_scores),
                       [pair_cases[key]] if key in pair_cases else [], at, threshold, key in recent_pairs)
        for wallet, score in wallet_scores.items():
            accumulate(by_wallet[wallet], score, wallet_ranks[wallet], len(wallet_scores),
                       wallet_cases[wallet], at, threshold, wallet in recent_wallets)
    for records in (by_wallet, by_pair):
        peak_scores = {k: r['best_score'] for k, r in records.items() if r['evaluated_ever']}
        peak_ranks = ranks(peak_scores)
        for key, record in records.items():
            record['peak_score_rank'] = peak_ranks.get(key)
            record['peak_score_rank_denominator'] = len(peak_scores)
    ordering = lambda r: (-(r['best_score'] if r['best_score'] is not None else -1), r['wallet'], r.get('event_id', ''))
    return dict(delay_seconds=delay, regular_decision_ticks=len(ticks),
                conceptual_regular_decision_ticks=len(range(start, ticks[-1] + 1, CADENCE)),
                last_regular_tick=ticks[-1], final_diagnostic_at=cutoff - 1,
                max_selected_trade_rows=max_selected,
                n_wallets_present=len(by_wallet),
                n_wallets_available_by_final=sum(r['first_available_at'] is not None for r in by_wallet.values()),
                n_wallets_evaluated=sum(r['evaluated_ever'] for r in by_wallet.values()),
                n_wallets_context_present=sum(r['context_present_ever'] for r in by_wallet.values()),
                n_wallets_recent_buy_evaluated=sum(r['recent_buy_evaluated_ever'] for r in by_wallet.values()),
                n_wallets_behavior_signal=sum(r['first_signal_at'] is not None for r in by_wallet.values()),
                n_wallets_conditional_priority=sum(r['first_conditional_priority_at'] is not None for r in by_wallet.values()),
                examined_wallet_event_tick_units=total_examined,
                executed_wallet_event_tick_units=executed_examined,
                conceptual_comparisons_two_metadata_scenarios=2 * total_examined,
                conservative_comparison_bound=2 * len(range(start, ticks[-1] + 1, CADENCE)) * len(units_ever_examined),
                implementation='wallet-cache' if fast else 'full-vendored-oracle',
                kernel_calls=cache.kernel_calls if fast else len(ticks) + 1,
                full_kernel_oracle_checks=oracle_checks,
                full_kernel_oracle_times=sorted(oracle_ticks),
                kernel_input_rows=cache.kernel_input_rows if fast else None,
                final_diagnostic_comparisons_two_scenarios=2 * final_diagnostics['examined_recent_buy_pairs'],
                final_diagnostics=final_diagnostics,
                wallets=sorted(by_wallet.values(), key=ordering),
                wallet_events=sorted(by_pair.values(), key=ordering))


def run_replay(trades, *, stratum, config=None, start=START, cutoff=CUTOFF, delays=DELAYS, dense=False, progress=None, fast=True):
    if not isinstance(stratum, str) or not stratum.strip():
        raise ValueError('Explicit collection stratum required')
    if config is None:
        config = json.loads((HERE / 'vendor/config.json').read_text())
    rows, counts = prepare(trades, start=start, cutoff=cutoff)
    scenarios = [replay_delay(rows, config, delay, start=start, cutoff=cutoff, dense=dense, progress=progress, fast=fast) for delay in delays]
    return dict(method='conditional-transaction-replay-v1', stratum=stratum,
                start_inclusive=start, cutoff_exclusive=cutoff,
                source_counts=counts, cadence_seconds=CADENCE,
                threshold_config_sha256=hashlib.sha256((HERE / 'vendor/config.json').read_bytes()).hexdigest(),
                effective_detection_parameters=dict(
                    large_nominal=config.get('large_nominal', 1000),
                    minimum_baseline=config.get('minimum_baseline', 20),
                    candidate_score=config.get('candidate_score', 2),
                    signal_window_seconds=config.get('signal_window_seconds', 86400),
                    analysis_trade_limit=config.get('analysis_trade_limit', 50000)),
                kernel_sha256=hashlib.sha256((HERE / 'vendor/signals.py').read_bytes()).hexdigest(),
                adapter_sha256=hashlib.sha256((HERE / 'replay_core.py').read_bytes()).hexdigest(),
                wallet_cache_sha256=hashlib.sha256((HERE / 'replay_fast.py').read_bytes()).hexdigest(),
                actual_historical_observability='unknown', exact_detector_status='unknown',
                metadata_scenarios=['transaction_behavior_without_historical_metadata',
                                    'conditional_open_no_known_public_result'],
                assumptions=[
                    'Availability timestamp+delay is hypothetical; original observed_at is never changed.',
                    'Provided event/market mapping is conditional; historical availability is unproved.',
                    'Conditional priority assumes markets open and no known public result; it is not a guaranteed bound.',
                    'Liquidity, category, cohort and established event independence are unavailable.',
                    'Wallet history is left-censored at window start and by collection stratum.',
                    'One point per native signal family; no calibration and no probability of inside information.',
                    'Regular first signals exclude the final off-cadence diagnostic.',
                    'Ranks use competition ties; best rank can change with the population denominator.',
                    '50,000-row selection reproduces the kernel caller, not historical collection or notifications.',
                ],
                n_comparisons=sum(s['conceptual_comparisons_two_metadata_scenarios'] +
                                  s['final_diagnostic_comparisons_two_scenarios'] for s in scenarios),
                conservative_comparison_bound=sum(s['conservative_comparison_bound'] +
                                                  s['final_diagnostic_comparisons_two_scenarios'] for s in scenarios),
                p_value=None, corrected_p_value=None, scenarios=scenarios)


def read_rows(path):
    opener = gzip.open if str(path).endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8') as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                raise ValueError(f'Blank JSONL row {line_number}')
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f'Invalid JSONL row {line_number}') from exc


def write_result(result, destination):
    payload = gzip.compress(json.dumps(result, ensure_ascii=False, sort_keys=True,
                                       separators=(',', ':'), allow_nan=False).encode(), mtime=0)
    if len(payload) > MAX_OUTPUT:
        raise ValueError('Compressed output would exceed the 20 MB study allowance')
    with Path(destination).open('xb') as stream:
        stream.write(payload)
    return len(payload)


def main():
    raise SystemExit('Use ana_replay.py: the official entry point verifies the frozen input manifest before replay.')


if __name__ == '__main__':
    main()
