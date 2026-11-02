"""Frozen descriptive feasibility audit, not an estimate of detector accuracy."""
import gzip
import hashlib
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from registre import enregistrer
from vendor.signals import evaluate

STUDY = Path(__file__).resolve().parents[1]
LOWER_BOUNDARY = 1790452800  # 2026-09-26 20:00 UTC, identical for both comparisons.


def ledger(rows, cutoff):
    """Economic dates describe retrieved transactions; they do not certify old availability."""
    seen, wallets = {}, defaultdict(lambda: {'buys': Decimal(0), 'sells': Decimal(0),
                                            'rows': 0, 'transactions': set(), 'conditions': set(),
                                            'first': None, 'last': None})
    used = []
    for row in rows:
        if not LOWER_BOUNDARY <= row['timestamp'] < cutoff:
            continue
        key = row['id']
        signature = tuple(row.get(k) for k in ('wallet', 'side', 'size', 'price', 'timestamp',
                                              'token_id', 'condition_id', 'transaction_hash'))
        if key in seen:
            if seen[key] != signature:
                raise ValueError('Conflicting trade identity')
            continue
        seen[key] = signature
        size, price = Decimal(str(row['size'])), Decimal(str(row['price']))
        if (not size.is_finite() or not price.is_finite() or size <= 0 or not 0 <= price <= 1
                or row['side'] not in ('BUY', 'SELL')):
            raise ValueError('Invalid economic row')
        if row['observed_at'] < row['timestamp']:
            raise ValueError('Impossible acquisition time')
        w = wallets[row['wallet'].lower()]
        w['buys' if row['side'] == 'BUY' else 'sells'] += size * price
        w['rows'] += 1
        w['transactions'].add(row['transaction_hash'])
        w['conditions'].add(row['condition_id'])
        w['first'] = row['timestamp'] if w['first'] is None else min(w['first'], row['timestamp'])
        w['last'] = row['timestamp'] if w['last'] is None else max(w['last'], row['timestamp'])
        used.append(row)
    entries = []
    for wallet, w in sorted(wallets.items()):
        entries.append({'wallet': wallet, 'rows': w['rows'], 'first_timestamp': w['first'],
                        'last_timestamp': w['last'], 'gross_buy_claim': str(w['buys']),
                        'gross_sell_claim': str(w['sells']), 'observed_net_cash_claim': str(w['buys'] - w['sells']),
                        'transactions': sorted(w['transactions']), 'conditions': sorted(w['conditions']),
                        'actual_capital_at_risk': None, 'historical_inventory': None,
                        'funding_commonality': None, 'rank': None})
    return {'cutoff': cutoff, 'requested_window_start': LOWER_BOUNDARY, 'rows': len(used), 'wallets': len(entries),
            'min_timestamp': min((r['timestamp'] for r in used), default=None),
            'max_timestamp': max((r['timestamp'] for r in used), default=None),
            'wallet_ledger': entries,
            'meaning': 'Partial API taker-side cash flows, not verified complete exposure or PnL.'}


def strict_replay(inputs, cutoff, config):
    diagnostics = {}
    cases = evaluate(inputs['trades'], inputs['markets'], inputs['events'],
                     now=cutoff - 0.000001, config=config, diagnostics=diagnostics)
    return {'cases': cases, 'diagnostics': diagnostics,
            'priority_alerts': sum(c['priority'] for c in cases)}


def analyze(local, config, rows):
    required = {'trade', 'market', 'event', 'public_milestone', 'public_condition', 'alert'}
    if local['first_cycle']['id'] != 1:
        raise ValueError('First cycle must be present')
    if local['historical_inputs'] != {'trades': [], 'markets': [], 'events': []}:
        raise ValueError('This audit requires the documented empty historical input')
    if local['first_cycle']['start'] <= max(w['cutoff'] for w in local['windows'].values()):
        raise ValueError('This feasibility audit requires installation after both cutoffs')
    windows = {}
    for label, window in local['windows'].items():
        counts = window['counts']
        if set(counts) != required or any(counts.values()):
            raise ValueError('Empty input replay is not valid for nonempty local history')
        windows[label] = {'local_counts': counts,
                          'strict_replay': strict_replay(local['historical_inputs'], window['cutoff'], config),
                          'reconstructed_descriptive_ledger': ledger(rows, window['cutoff'])}
    result = {'verdict': 'NOT_DEPLOYED_THEN_AND_COUNTERFACTUAL_NOT_ESTIMABLE',
              'first_local_cycle': local['first_cycle'], 'windows': windows,
              'precision': None, 'recall': None, 'false_positives': None, 'first_alert_time': None,
              'ranking': None, 'effective_independent_events': 1,
              'limits': ['Bot was first installed after both cutoffs.',
                         'Retrieved historical trades were first acquired after both cutoffs.',
                         'Historical open status, liquidity and cross-market wallet history are not certified.',
                         'No ground-truth insider/non-insider labels; public allegations are not such labels.',
                         'Case selected retrospectively after a public report; detector rules are unchanged.']}
    return result


def main():
    local = json.loads((STUDY / 'data/local_availability.json').read_text())
    config = json.loads((STUDY / 'data/detector_config.json').read_text())
    validation = json.loads((STUDY / 'data/collection_validation.json').read_text())
    minimal = STUDY / 'data/trades_minimal.jsonl.gz'
    if (validation.get('status') != 'PASS' or validation.get('minimal_sha256') !=
            hashlib.sha256(minimal.read_bytes()).hexdigest()):
        raise ValueError('Minimal input lacks a successful matching collection validation')
    with gzip.open(minimal, 'rt') as stream:
        rows = [json.loads(line) for line in stream]
    result = analyze(local, config, rows)
    destination = STUDY / 'derived/audit.json'
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    enregistrer(str(STUDY), test='T1_two_cutoff_feasibility_and_descriptive_ledger', declare=True,
                n=len(rows), n_effectif=1, n_comparaisons=2, agent='Codex',
                params={'performance_metrics': 'not estimable', 'cutoffs': [w['cutoff'] for w in local['windows'].values()]},
                sortie='derived/audit.json')
    print(json.dumps({'verdict': result['verdict'], 'input_rows': len(rows),
                      'strict_priorities': {k:v['strict_replay']['priority_alerts'] for k,v in result['windows'].items()}}))


if __name__ == '__main__':
    main()
