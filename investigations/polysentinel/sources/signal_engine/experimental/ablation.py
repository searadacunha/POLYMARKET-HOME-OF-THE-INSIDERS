"""What each evidence family changes in the queue, on the engine's own recent pairs. Load and overlap, no accuracy.

Removing a family and re-reading the categories says what the family moves; it cannot say whether the
result is right, because no label exists. CUSUM is tried as one more finding on a wallet.
Usage: python -m signal_engine.experimental.ablation [--out FILE] [--window-days N]
"""
import argparse
import json
import os
import sqlite3
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

from ..collective_behavior import collective_signals
from ..comparators import STRUCTURE_FAMILY
from ..evidence_scoring import ANOMALOUS, CATEGORY_ORDER, classify, needs_review_now
from ..funding_graph import corroborating_funding
from ..prospective_detection import is_open, load_config
from ..wallet_behavior import fill_groups
from . import sequential as seq

STATE = Path(os.environ.get('SIGNAL_ENGINE_STATE', Path.home() / '.local/state/polysentinel-signal-engine')) / 'state.sqlite3'
QUIET = dict(convergence={}, identical_amounts=[], repeated_across_events=[], convergence_spread_s={})
CHOSEN = dict(seq.DEFAULTS, k=1.0, h=5.0, own_minimum=8)  # the setting bench.py chose on development wallets for its reference seed


def with_cusum(pair):
    return dict(pair, wallet_findings=dict(pair['wallet_findings'], sequential_break=dict(limit='Experimental')))


def run(window_days=3):
    cx = sqlite3.connect(f'file:{STATE}?mode=ro', uri=True, timeout=10)
    cx.row_factory = sqlite3.Row
    store = SimpleNamespace(cx=cx)
    config = load_config()
    now = cx.execute('SELECT MAX(evaluated_at) FROM pairs').fetchone()[0]
    rows_by_wallet = defaultdict(list)
    for r in cx.execute('SELECT * FROM trades'):
        rows_by_wallet[r['wallet']].append(dict(r))
    alarms = {w: seq.scan_wallet(fill_groups(rows), CHOSEN) for w, rows in rows_by_wallet.items()}
    alarmed = {w for w, a in alarms.items() if any(x['ts'] >= now - window_days * 86400 for x in a)}
    variants = {name: Counter() for name in ('engine', 'without_collective', 'without_funding', 'without_market_risk', 'with_cusum_findings')}
    moved = Counter()
    flagged_wallets, events = set(), 0
    starts = [r[0] for r in cx.execute("SELECT DISTINCT event_key FROM pairs WHERE anomalies!='{}' AND evaluated_at>=?", (now - window_days * 86400,))]
    for event_key in starts:
        pairs = [json.loads(r['record']) for r in cx.execute("SELECT record FROM pairs WHERE event_key=? AND anomalies!='{}' AND evaluated_at>=?", (event_key, now - window_days * 86400))]
        measured = {p['wallet'] for p in pairs if p['wallet_findings'] or p['position_findings']}
        flagged_wallets |= measured
        reference = max(pairs, key=lambda p: p['measures']['max_market_spend'])
        market = reference['market']
        collective = collective_signals(store, event_key, now, config)
        funding = json.loads(cx.execute('SELECT value FROM kv WHERE key=?', ('funding:' + event_key,)).fetchone()[0]) if cx.execute('SELECT 1 FROM kv WHERE key=?', ('funding:' + event_key,)).fetchone() else None
        continuous = STRUCTURE_FAMILY.get(market['risk']['decision_structure']) == 'continuous'
        open_now = is_open(market, now)
        base = classify(pairs, collective, market['risk'], funding, config)
        cases = dict(engine=(pairs, collective, market['risk'], funding), without_collective=(pairs, QUIET, market['risk'], funding), without_funding=(pairs, collective, market['risk'], None),
                     without_market_risk=(pairs, collective, dict(market['risk'], level='MEDIUM'), funding), with_cusum_findings=([with_cusum(p) if p['wallet'] in alarmed else p for p in pairs], collective, market['risk'], funding))
        events += 1
        for name, (p, c, risk, f) in cases.items():
            category = classify(p, c, risk, f, config)
            variants[name][category] += 1
            if CATEGORY_ORDER.get(category, 0) >= CATEGORY_ORDER[ANOMALOUS]:
                variants[name]['cases'] += 1
            if needs_review_now(category, risk, continuous, open_now):
                variants[name]['review'] += 1
            if category != base:
                moved[name] += 1
    cx.close()
    active = {w for w, rows in rows_by_wallet.items() if any(r['ts'] >= now - window_days * 86400 for r in rows)}
    return dict(window_days=window_days, events_with_pairs=events, per_variant={k: dict(v) for k, v in variants.items()}, events_whose_category_moved=dict(moved),
                wallets_active=len(active), wallets_flagged_by_engine=len(flagged_wallets), wallets_with_cusum_alarm=len(alarmed), overlap=len(alarmed & flagged_wallets),
                cusum_only=len(alarmed - flagged_wallets), engine_only=len(flagged_wallets - alarmed), meaning='Counts of queue load on one short window of live rows; no accuracy can be read from them.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out')
    p.add_argument('--window-days', type=int, default=3)
    a = p.parse_args()
    text = json.dumps(run(a.window_days), indent=1, sort_keys=True)
    if a.out:
        Path(a.out).write_text(text)
    print(text)


if __name__ == '__main__':
    main()
