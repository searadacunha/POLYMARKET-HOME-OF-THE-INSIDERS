#!/usr/bin/env python3
"""Read-only archival recalculation. No RPC, no account attribution, no alpha claims."""
import argparse
import csv
import json
import statistics
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = ROOT / 'research_notes' / 'financial-links-replay-2026-11-07' / 'data'


def rows(path, required):
    with Path(path).open(newline='', encoding='utf-8-sig') as fh:
        reader = csv.DictReader(fh)
        missing = set(required) - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'missing columns: {sorted(missing)}')
        result = list(reader)
    if not result:
        raise ValueError('empty archive')
    if any(not all(row.get(k, '').strip() for k in required) for row in result):
        raise ValueError('empty mandatory field')
    return result


def safe_number(value):
    result = Decimal(value)
    if not result.is_finite():
        raise ValueError('non-finite number')
    return result


def railgun(path):
    data = rows(path, ('proxy', 'market', 'side', 'won', 'price', 'usdc',
                       'payout_if_redeemed', 'trade_tx', 'funding_lineage'))
    if len({r['proxy'].lower() for r in data}) != len(data):
        raise ValueError('duplicate trading wallet; wallet-level denominator invalid')
    if len({r['trade_tx'].lower() for r in data}) != len(data):
        raise ValueError('duplicate trade transaction; audit individual fills')
    wins = Counter()
    group = defaultdict(lambda: {'trades': 0, 'wins': 0, 'usd': Decimal(0),
                                 'price_sum': Decimal(0)})
    spend = payout = sum_prices = Decimal(0)
    for r in data:
        if r['won'] not in ('True', 'False'):
            raise ValueError('unrecognised outcome label')
        if r['side'] != 'BUY':
            raise ValueError('unsupported transaction side')
        price = safe_number(r['price'])
        amount = safe_number(r['usdc'])
        due = safe_number(r['payout_if_redeemed'])
        if not 0 < price < 1 or amount <= 0 or due < 0:
            raise ValueError('invalid entry price or accounting amount')
        did_win = r['won'] == 'True'
        if did_win != (due > 0):
            raise ValueError('payout label inconsistent with observed winner')
        wins[r['won']] += 1
        spend += amount
        payout += due
        sum_prices += price
        item = group[r['market']]
        item['trades'] += 1
        item['wins'] += int(did_win)
        item['usd'] += amount
        item['price_sum'] += price
    n = len(data)
    def fmt(v): return format(v.quantize(Decimal('0.000001')), 'f')
    return {
        'rows': n,
        'unique_wallets': n,
        'wins': wins['True'],
        'losses': wins['False'],
        'win_fraction': fmt(Decimal(wins['True']) / n),
        'price_sum': fmt(sum_prices),
        'mean_entry_price': fmt(sum_prices / n),
        'arithmetic_win_minus_mean_entry_price': fmt(Decimal(wins['True']) / n - sum_prices / n),
        'spent_usdc': fmt(spend),
        'potential_payout_if_redeemed_usdc': fmt(payout),
        'markets': {k: {'trades': v['trades'], 'wins': v['wins'],
                       'spent_usdc': fmt(v['usd']), 'sum_entry_prices': fmt(v['price_sum'])}
                    for k, v in sorted(group.items())},
        'warning': 'Selected, correlated, retrospective cohort. No p-value, no independent-event count, no realised-PnL claim.'
    }


def kpmg(path):
    data = rows(path, ('sender', 'recipient', 'status', 'L1_polygon_tx',
                       'L2_polygon_tx', 'seconds_L1_to_L2',
                       'intermediary_credit_usdc_atomic', 'intermediary_debit_usdc_atomic'))
    if len({(r['L1_polygon_tx'], r['L2_polygon_tx']) for r in data}) != len(data):
        raise ValueError('duplicate transaction pair')
    delays = []
    for r in data:
        if r['status'] != 'CONFIRMED':
            raise ValueError('mixed evidence tier; cannot count all as confirmed')
        d = int(r['seconds_L1_to_L2'])
        if d < 0:
            raise ValueError('non-causal handoff')
        if safe_number(r['intermediary_credit_usdc_atomic']) != safe_number(r['intermediary_debit_usdc_atomic']):
            raise ValueError('intermediary value does not reconcile')
        delays.append(d)
    return {'rows': len(data), 'confirmed_handoffs_in_archive': len(data),
            'delay_seconds_min': min(delays), 'delay_seconds_max': max(delays),
            'delay_seconds_median': statistics.median(delays),
            'unique_sender_labels': len({r['sender'] for r in data}),
            'unique_recipient_labels': len({r['recipient'] for r in data}),
            'warning': 'Archive-value verification only; not fresh receipt or controller verification.'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--railgun', type=Path, default=ARCHIVE / 'railgun_tree_accounts.csv')
    ap.add_argument('--kpmg', type=Path, default=ARCHIVE / 'kpmg_handoffs_verified.csv')
    ap.add_argument('--check-archive', action='store_true')
    args = ap.parse_args()
    output = {'railgun': railgun(args.railgun), 'kpmg': kpmg(args.kpmg)}
    if args.check_archive:
        assert (output['railgun']['rows'], output['railgun']['wins'],
                output['railgun']['losses'], output['railgun']['spent_usdc']) == (
                    71, 5, 66, '21965.645223'), 'archival Railgun figures changed'
        assert (output['kpmg']['rows'], output['kpmg']['delay_seconds_min'],
                output['kpmg']['delay_seconds_max']) == (14, 18, 50), 'archival KPMG figures changed'
    print(json.dumps(output, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
