"""Synthetic controls only. No corpus, labels, network, production DB or registry."""
from copy import deepcopy
import gzip
import hashlib
import json
from pathlib import Path
import random
import tempfile
import time

from replay_core import (CUTOFF, DELAYS, HERE, START, decision_ticks, kernel,
                         prepare, replay_delay, run_replay, write_result)


def trade(i, at, wallet='wallet-a', nominal=10, **changes):
    row = dict(id=str(i), wallet=wallet, side='BUY', timestamp=at,
               observed_at=CUTOFF + 86400, token_id='token-a', transaction_hash='tx-' + str(i),
               size=nominal * 2, price=.5, market_id='market-a', event_id='event-a', condition_id='condition-a')
    row.update(changes)
    return row


def fails(action):
    try:
        action()
    except ValueError:
        return
    raise AssertionError('Expected explicit ValueError')


def controls():
    started = time.perf_counter()
    config = json.loads((HERE / 'vendor/config.json').read_text())
    module = kernel()
    checks = []
    cutoff = START + 3600
    cases = {
        'null': [trade(0, START)],
        'medium': [trade(0, START, nominal=1200)],
        'strong': [trade(i, START + i * 30, wallet='wallet-' + str(i), nominal=1200) for i in range(3)],
    }
    outcomes = {}
    for name, rows in cases.items():
        source_copy = deepcopy(rows)
        result = run_replay(rows, stratum='synthetic-' + name, config=config, cutoff=cutoff)
        assert rows == source_copy
        expected_signals = 0 if name == 'null' else len(rows)
        expected_priority = len(rows) if name == 'strong' else 0
        for scenario in result['scenarios']:
            assert scenario['n_wallets_behavior_signal'] == expected_signals
            assert scenario['n_wallets_conditional_priority'] == expected_priority
            assert all(r['actual_historical_alert'] is None for r in scenario['wallets'])
        outcomes[name] = dict(wallets=len(rows), behavior=expected_signals, conditional_priority=expected_priority)
    checks.append('null-medium-strong-all-four-delays-and-source-observed-at-preserved')

    baseline = [trade(i, START + i * 60) for i in range(20)]
    baseline.append(trade(21, START + 1200, nominal=2000))
    result = run_replay(baseline, stratum='synthetic-baseline', config=config, cutoff=cutoff, delays=(0,))
    wallet = result['scenarios'][0]['wallets'][0]
    assert wallet['best_score'] == 2
    assert wallet['first_conditional_priority_at'] == START + 1200
    assert 'wallet_size_shift' in wallet['first_signals']
    checks.append('native-minimum-baseline-and-family-deduplication')

    recurrence = [trade(i, START + i * 60, nominal=1200, event_id='event-' + str(i),
                        market_id='market-' + str(i), token_id='token-' + str(i)) for i in range(3)]
    result = run_replay(recurrence, stratum='synthetic-recurrence', config=config, cutoff=cutoff, delays=(0,))
    assert result['scenarios'][0]['n_wallets_conditional_priority'] == 0
    recurrence_rules = [r['first_signals'].get('repeated_large_entries') for r in result['scenarios'][0]['wallet_events']]
    assert any(r is not None and r['weight'] == 0 for r in recurrence_rules)
    checks.append('unknown-event-independence-never-scores-recurrence')

    shared = [trade(i, START + i * 30, wallet='wallet-' + str(i), nominal=1200,
                    transaction_hash='same-tx') for i in range(3)]
    result = run_replay(shared, stratum='synthetic-shared-tx', config=config, cutoff=cutoff, delays=(0,))
    assert result['scenarios'][0]['n_wallets_conditional_priority'] == 0
    checks.append('shared-transaction-is-not-distinct-wallet-synchrony')

    for rows in (cases['null'], cases['medium'], cases['strong'], baseline, recurrence):
        adapted = [dict(row, observed_at=row['timestamp']) for row in rows]
        plain = module.evaluate(adapted, [], [], now=cutoff - 1, config=config)
        events = [dict(id=event, active=True, observed_at=START) for event in {r['event_id'] for r in rows}]
        favorable = module.evaluate(adapted, [], events, now=cutoff - 1, config=config)
        assert [(c['id'], c['score'], c['signals']) for c in plain] == [(c['id'], c['score'], c['signals']) for c in favorable]
        assert [bool(c['signals']) and c['score'] >= config['candidate_score'] for c in plain] == [c['priority'] for c in favorable]
    checks.append('derived-favorable-priority-equals-native-active-stub-scenario')

    # A shorter synthetic window exercises many expiries; production config is untouched.
    synthetic_config = dict(config, signal_window_seconds=600)
    for seed in range(8):
        rng = random.Random(seed)
        rows = [trade(i, START + rng.randrange(3300), wallet='wallet-' + str(rng.randrange(5)),
                      nominal=rng.choice([10, 300, 1200, 3000]), event_id='event-' + str(rng.randrange(3)),
                      side=rng.choice(['BUY', 'BUY', 'SELL'])) for i in range(24)]
        rows, _ = prepare(rows, cutoff=cutoff)
        for delay in DELAYS:
            sparse = replay_delay(rows, synthetic_config, delay, cutoff=cutoff)
            dense = replay_delay(rows, synthetic_config, delay, cutoff=cutoff, dense=True)
            assert sparse['wallets'] == dense['wallets'], (seed, delay, 'wallet')
            assert sparse['wallet_events'] == dense['wallet_events'], (seed, delay, 'pair')
            assert sparse['final_diagnostics'] == dense['final_diagnostics']
    checks.append('sparse-versus-all-60-second-ticks-eight-seeds-four-delays')

    late = [trade(0, cutoff - 2, nominal=1200), trade(1, cutoff, wallet='excluded', nominal=1200)]
    result = run_replay(late, stratum='synthetic-boundary', config=config, cutoff=cutoff, delays=(0, 60))
    zero, sixty = result['scenarios']
    assert result['source_counts']['at_or_after_cutoff'] == 1
    assert zero['wallets'][0]['first_signal_at'] is None
    assert zero['wallets'][0]['final_diagnostic_score'] == 1
    assert sixty['n_wallets_available_by_final'] == 0
    checks.append('strict-cutoff-and-final-diagnostic-never-backdates-regular-signal')

    expiry = decision_ticks([trade(0, START)], 0, 86400)
    assert START + 86460 in expiry and START + 86400 not in expiry
    checks.append('native-24-hour-window-inclusive-boundary')

    row = trade(0, START)
    clean, counts = prepare([row, row])
    assert len(clean) == 1 and counts['duplicate_rows'] == 1
    fails(lambda: prepare([row, dict(row, size=999)]))
    fails(lambda: prepare([dict(row, label=True)]))
    fails(lambda: prepare([dict(row, outcome='Yes')]))
    fails(lambda: prepare([dict(row, price=float('nan'))]))
    fails(lambda: prepare([dict(row, size=True)]))
    fails(lambda: prepare([row, dict(row, id='1', event_id='other-event')]))
    checks.append('strict-allowlist-economics-duplicate-and-group-mapping-validation')

    ties = [trade('b', START), trade('a', START, wallet='other-wallet')]
    tiny = dict(config, analysis_trade_limit=1)
    result = run_replay(ties, stratum='synthetic-cap-tie', config=tiny, cutoff=cutoff, delays=(0,))
    wallets = {r['wallet']: r for r in result['scenarios'][0]['wallets']}
    assert wallets['other-wallet']['evaluated_ever']
    assert not wallets['wallet-a']['evaluated_ever']
    assert result['scenarios'][0]['n_wallets_present'] == 2
    checks.append('native-descending-time-ascending-id-limit-and-no-signal-wallet-denominator')

    shuffled = list(reversed(baseline))
    assert run_replay(shuffled, stratum='synthetic-order', config=config, cutoff=cutoff) == run_replay(
        baseline, stratum='synthetic-order', config=config, cutoff=cutoff)
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory) / 'control.json.gz'
        size = write_result(result, output)
        assert json.loads(gzip.decompress(output.read_bytes())) == result
        assert size == output.stat().st_size
        try:
            write_result(result, output)
        except FileExistsError:
            pass
        else:
            raise AssertionError('Existing result overwritten')
    checks.append('permutation-determinism-compressed-output-roundtrip-and-no-overwrite')
    return dict(status='PASS', dataset='synthetic-only', controls=checks,
                n_controls=len(checks), outcomes=outcomes, elapsed_seconds=round(time.perf_counter() - started, 3),
                synthetic_power_note='Deterministic control detection, not empirical power or false-positive calibration.',
                hashes={str(p.relative_to(HERE)): hashlib.sha256(p.read_bytes()).hexdigest()
                        for p in (HERE / 'replay_core.py', HERE / 'replay_fast.py', HERE / 'replay_selfcheck.py',
                                  HERE / 'vendor/signals.py', HERE / 'vendor/config.json')})


if __name__ == '__main__':
    print(json.dumps(controls(), ensure_ascii=False, sort_keys=True, indent=2))
