"""Descriptive robustness and co-buy overlap; not an insider classifier."""
import csv
import itertools
import json
import sys
import unittest
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path


def pnl(rows):
    rows = list(rows)
    addresses = [r['account'].lower() for r in rows]
    if len(set(addresses)) != len(addresses):
        raise ValueError('duplicate account')
    active = [r for r in rows if int(r['fills']) > 0]
    complete = [Decimal(r['trading_pnl_known']) for r in active
                if r['trading_pnl_status'] == 'COMPLETE']
    if any(not x.is_finite() for x in complete):
        raise ValueError('nonfinite PnL')
    losses = sorted(x for x in complete if x < 0)
    total = sum(complete, Decimal(0))
    return {'addresses': len(rows), 'active': len(active),
            'complete_active': len(complete), 'partial_active': len(active)-len(complete),
            'winners': sum(x > 0 for x in complete), 'losers': len(losses),
            'flat': complete.count(Decimal(0)), 'complete_pnl': str(total),
            'remove_worst': {str(k): str(total-sum(losses[:k]))
                             for k in (1, 5, 10) if len(losses) >= k}}


def overlap(rows, cutoff):
    # This archived case has labels, not condition IDs; never join other datasets by title.
    keys = defaultdict(set)
    for r in rows:
        if int(r['t']) >= cutoff or r['type'] != 'TRADE' or r['side'] != 'BUY':
            continue
        if not r['handle'] or not r['market'] or not r['outcome']:
            raise ValueError('missing identifier')
        keys[r['handle']].add((r['market'], r['outcome']))
    pairs = [keys[a] & keys[b] for a, b in itertools.combinations(sorted(keys), 2)]
    return {'active_buyers': len(keys), 'pairs': len(pairs),
            'pairs_shared_one_or_more': sum(len(x) >= 1 for x in pairs),
            'pairs_shared_two_or_more': sum(len(x) >= 2 for x in pairs)}


def read(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))


class Tests(unittest.TestCase):
    def test_pnl(self):
        rows = [{'account': a, 'fills': f, 'trading_pnl_status': s, 'trading_pnl_known': p}
                for a, f, s, p in [('a', '2', 'COMPLETE', '-4'), ('b', '1', 'COMPLETE', '1'),
                                   ('c', '1', 'PARTIAL', '50'), ('d', '0', 'COMPLETE', '0')]]
        out = pnl(rows)
        self.assertEqual((out['complete_pnl'], out['remove_worst']['1']), ('-3', '1'))
        self.assertEqual((out['complete_active'], out['partial_active']), (2, 1))
        with self.assertRaises(ValueError):
            pnl(rows + rows[:1])

    def test_cutoff_and_direction(self):
        def row(a, t, m, o='Yes', side='BUY'):
            return dict(handle=a, t=str(t), type='TRADE', side=side, market=m, outcome=o)
        rows = [row('a', 1, 'X'), row('a', 2, 'X'), row('b', 2, 'X'),
                row('a', 3, 'Y'), row('b', 4, 'Y'), row('b', 2, 'Y', side='SELL'),
                row('c', 1, 'X', 'No')]
        self.assertEqual(overlap(rows, 4), dict(active_buyers=3, pairs=3,
                         pairs_shared_one_or_more=1, pairs_shared_two_or_more=0))
        self.assertEqual(overlap(rows, 5)['pairs_shared_two_or_more'], 1)


def main(root):
    wallets = read(root / 'investigations/data-completion-20261123/results/wallet_summary.csv')
    activity = read(root / 'research_notes/nobel-strict-replay-2026-11-20/data/accounts_activity.csv')
    out = {'f2020': pnl(wallets), 'nobel': {s: overlap(activity, int(datetime.fromisoformat(s).timestamp()))
           for s in ('2025-10-09T23:00:15+00:00', '2025-10-10T09:00:00+00:00')}}
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == '__main__':
    if sys.argv[1:] == ['--test']:
        unittest.main(argv=[sys.argv[0]])
    else:
        main(Path(__file__).resolve().parents[2])
