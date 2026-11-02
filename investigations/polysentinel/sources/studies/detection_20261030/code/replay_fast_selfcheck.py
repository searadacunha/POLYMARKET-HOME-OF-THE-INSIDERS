"""Adversarial synthetic equality checks against the full unchanged detector."""
from collections import defaultdict
from copy import deepcopy
import hashlib
import json
import random
import time

from replay_core import (START, CUTOFF, HERE, DELAYS, ORACLE_TICKS, kernel, prepare,
                         replay_delay)
from replay_fast import WalletCache
from replay_selfcheck import trade, fails


def compare_records(fast, full):
    for key in ('wallets', 'wallet_events', 'final_diagnostics', 'examined_wallet_event_tick_units',
                'conceptual_comparisons_two_metadata_scenarios', 'conservative_comparison_bound'):
        assert fast[key] == full[key], key


def controls():
    started = time.perf_counter()
    config = json.loads((HERE / 'vendor/config.json').read_text())
    checks = []
    replay_comparisons = 0
    exact_case_comparisons = 0
    for seed in range(24):
        rng = random.Random(seed)
        rows = []
        for i in range(60):
            wallet = 'wallet-' + str(rng.randrange(8))
            market = str(rng.randrange(3))
            rows.append(trade(i, START + rng.randrange(3600), wallet=wallet,
                              nominal=rng.choice([10, 249, 250, 300, 999, 1000, 1200]),
                              event_id='event-' + str(int(market) % 2), market_id='market-' + market,
                              token_id='token-' + market, side=rng.choice(['BUY', 'BUY', 'SELL']),
                              transaction_hash='shared-' + str(i // 3) if i % 7 == 0 else 'tx-' + str(i)))
        # Parent fills span ticks and can move the group's timestamp or cross 250.
        rows += [trade('fill-a-' + str(seed), START + 100, wallet='fills', nominal=150, order_hash='parent'),
                 trade('fill-b-' + str(seed), START + 170, wallet='fills', nominal=150, order_hash='parent'),
                 trade('fill-c-' + str(seed), START + 1000, wallet='fills', nominal=1000, order_hash='parent')]
        rows, _ = prepare(rows, cutoff=START + 4200)
        local_config = dict(config, signal_window_seconds=rng.choice([120, 600, 1800]),
                            analysis_trade_limit=rng.choice([10, 20, 50000]))
        for delay in DELAYS:
            fast = replay_delay(rows, local_config, delay, cutoff=START + 4200, fast=True)
            full = replay_delay(rows, local_config, delay, cutoff=START + 4200, fast=False)
            compare_records(fast, full)
            replay_comparisons += 1
        # Compare complete cases, including fingerprints and all reasons, at every tick.
        cache = WalletCache(kernel())
        for at in range(START, START + 4200, 60):
            available = [r for r in rows if r['timestamp'] <= at]
            selected = sorted(available, key=lambda r: (-r['timestamp'], r['id']))[:local_config['analysis_trade_limit']]
            adapted = [dict(r, observed_at=r['timestamp']) for r in selected]
            history = defaultdict(lambda: dict(first_timestamp=float('inf'), observations=0))
            for row in available:
                history[row['wallet']]['first_timestamp'] = min(history[row['wallet']]['first_timestamp'], row['timestamp'])
                history[row['wallet']]['observations'] += 1
            fast_diag, full_diag = {}, {}
            fast_cases = deepcopy(cache.evaluate(adapted, now=at, config=local_config, wallet_history=history, diagnostics=fast_diag))
            full_cases = cache.module.evaluate(adapted, [], [], now=at, config=local_config, wallet_history=history, diagnostics=full_diag)
            assert fast_cases == full_cases, (seed, at, 'cases')
            assert fast_diag == full_diag, (seed, at, 'diagnostics')
            exact_case_comparisons += 1
    checks.append('24-seeds-four-delays-caps-parent-fills-expiries-and-complete-case-equality')

    rows = [trade('sell', START, wallet='sell-only', side='SELL'),
            trade('expired', START, wallet='expired-buy'),
            trade('recent', START + 1800, wallet='recent-buy', nominal=1200)]
    rows, _ = prepare(rows, cutoff=START + 3600)
    local_config = dict(config, signal_window_seconds=600)
    sparse = replay_delay(rows, local_config, 0, cutoff=START + 3600)
    dense = replay_delay(rows, local_config, 0, cutoff=START + 3600, dense=True)
    compare_records(sparse, dense)
    wallets = {r['wallet']: r for r in sparse['wallets']}
    assert not wallets['sell-only']['evaluated_ever'] and wallets['sell-only']['context_present_ever']
    assert wallets['sell-only']['peak_score_rank'] is None
    assert wallets['expired-buy']['evaluated_ever'] and wallets['expired-buy']['last_regular_score'] is None
    assert sparse['conceptual_regular_decision_ticks'] == 60
    assert sparse['examined_wallet_event_tick_units'] == 22
    checks.append('rank-population-recent-buys-only-and-full-calendar-comparison-count')

    for missing in ('market_id', 'event_id', 'condition_id', 'observed_at'):
        fails(lambda missing=missing: prepare([{k: v for k, v in trade(1, START).items() if k != missing}]))
    fails(lambda: prepare([dict(trade(1, START), observed_at=float('inf'))]))
    fails(lambda: prepare([dict(trade(1, START), observed_at=str(CUTOFF))]))
    assert len(ORACLE_TICKS) == len(set(ORACLE_TICKS)) == 64
    assert ORACLE_TICKS[0] == START and ORACLE_TICKS[-1] == CUTOFF - 60
    checks.append('strict-mapping-source-time-and-prefixed-64-point-oracle-calendar')
    return dict(status='PASS', dataset='synthetic-only', n_control_groups=len(checks), controls=checks,
                full_replay_equivalence_comparisons=replay_comparisons,
                complete_case_and_diagnostics_comparisons=exact_case_comparisons,
                hashes={name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                        for name in ('replay_core.py', 'replay_fast.py', 'replay_fast_selfcheck.py')},
                elapsed_seconds=time.perf_counter() - started)


if __name__ == '__main__':
    print(json.dumps(controls(), indent=2, sort_keys=True))
