"""Mechanics of the experimental modules, on synthetic rows. Detection power is measured by the bench, not here."""
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signal_engine.experimental import sequential as seq  # noqa: E402
from signal_engine.experimental import bench, funding_bench, splits  # noqa: E402
from signal_engine.funding_graph import ZERO_ADDRESS  # noqa: E402

T0 = 1_800_000_000


def population(n=2000, seed=1):
    rng = random.Random(seed)
    return seq.Reference([rng.lognormvariate(7, 1.5) for _ in range(n)])


def buys(sizes, start=T0, gap=3600):
    return [dict(ts=start + i * gap, nominal=x, is_buy=True) for i, x in enumerate(sizes)]


class RankCusum(unittest.TestCase):
    def test_one_huge_trade_cannot_alarm_alone(self):
        rng = random.Random(2)
        rows = buys([rng.lognormvariate(7, 1) for _ in range(40)] + [1e12])
        self.assertEqual(seq.scan_wallet(rows, streams=('size',)), [])

    def test_sustained_rise_alarms_once(self):
        rng = random.Random(3)
        rows = buys([rng.lognormvariate(6, .5) for _ in range(40)] + [rng.lognormvariate(11, .5) for _ in range(15)])
        alarms = seq.scan_wallet(rows, streams=('size',))
        self.assertEqual(len(alarms), 1)
        self.assertGreater(alarms[0]['ts'], rows[39]['ts'])

    def test_short_history_is_unscored_not_quiet(self):
        stream = seq.StreamCusum()
        self.assertIsNone(stream.update(T0, 5.0))
        self.assertEqual(stream.unscored, 1)
        self.assertEqual(seq.scan_wallet(buys([1e9] * 6)), [])

    def test_old_pressure_decays(self):
        stream = seq.StreamCusum()
        for i in range(40):
            stream.update(T0 + i, float(i))
        high = stream.s
        self.assertGreater(high, 0)
        stream.update(T0 + 30 * 86400, 20.0)
        self.assertLess(stream.s, high)

    def test_a_collection_gap_is_not_inactivity(self):
        rows = buys([100, 100], gap=7 * 86400)
        rate = [o for o in seq.wallet_observations(rows, gaps=[(T0 + 100, T0 + 200)]) if o[0] == 'rate']
        self.assertEqual(rate, [])
        self.assertEqual(len([o for o in seq.wallet_observations(rows) if o[0] == 'rate']), 1)

    def test_future_values_cannot_change_past_alarms(self):
        rng = random.Random(4)
        rows = buys([rng.lognormvariate(6, .5) for _ in range(40)] + [rng.lognormvariate(11, .5) for _ in range(15)])
        full = seq.scan_wallet(rows)
        cut = rows[-1]['ts'] - 1
        self.assertEqual(seq.scan_wallet(rows[:-1]), [a for a in full if a['ts'] <= cut])

    def test_ties_take_their_mid_rank(self):
        self.assertAlmostEqual(seq.Reference([1.0] * 100).score(1.0), 0.0, places=6)

    def test_baselines(self):
        pop = population()
        self.assertEqual(len(seq.quantile_rule(buys([1e12]), pop)), 1)
        self.assertEqual(seq.quantile_rule(buys([1e12]), seq.Reference()), [])
        steady = [100.0 + i for i in range(10)]
        self.assertEqual(seq.robust_rule(buys(steady)), [])
        self.assertEqual(len(seq.robust_rule(buys(steady + [10000.0]))), 1)

    def test_silent_hours_count_within_the_span(self):
        rows = [dict(ts=T0 // 3600 * 3600, is_buy=True, event_key='e', wallet=f'w{i}') for i in range(3)] + [dict(ts=T0 // 3600 * 3600 + 7200, is_buy=True, event_key='e', wallet='w0')]
        self.assertEqual([h[2] for h in seq.event_hours(rows, minimum_rows=1)], [3, 0, 1])


class Partitions(unittest.TestCase):
    def rows(self):
        rng = random.Random(5)
        return [dict(wallet=f'w{rng.randrange(40)}', event_key=f'e{rng.randrange(8)}', ts=T0 + rng.randrange(20 * 86400), observed_at=T0 + 20 * 86400) for _ in range(2000)]

    def test_linked_wallets_stay_on_one_side(self):
        groups = splits.Groups()
        for i in range(39):
            if i % 2:
                groups.link(f'w{i}', f'w{i + 1}', 'direct transfer, tx 0xabc')
        split_ts = T0 + 10 * 86400
        result = splits.temporal_group_split(self.rows(), split_ts, 86400, groups)
        splits.assert_no_leak(result, split_ts, 86400, groups)
        self.assertGreater(len(result['dev']), 0)
        self.assertGreater(len(result['test']), 0)
        self.assertGreater(result['dropped_embargo'], 0)

    def test_the_audit_catches_a_contaminated_partition(self):
        row = self.rows()[0]
        dirty = dict(dev=[dict(row, ts=T0)], test=[dict(row, ts=T0 + 10 ** 7)], burn_in=[])
        with self.assertRaisesRegex(AssertionError, 'both sides'):
            splits.assert_no_leak(dirty, T0 + 100, 10)

    def test_a_row_in_the_embargo_is_caught(self):
        row = self.rows()[0]
        with self.assertRaisesRegex(AssertionError, 'embargo'):
            splits.assert_no_leak(dict(dev=[], test=[dict(row, ts=T0 + 101)], burn_in=[]), T0 + 100, 10)

    def test_the_studied_case_cannot_tune_its_own_rules(self):
        rows = self.rows()
        result = splits.temporal_group_split(rows, T0 + 10 * 86400, 0, excluded_events={'e1'}, excluded_wallets={'w3'})
        kept = result['dev'] + result['test'] + result['burn_in']
        self.assertFalse(any(r['event_key'] == 'e1' or r['wallet'] == 'w3' for r in kept))
        with self.assertRaisesRegex(AssertionError, 'Excluded'):
            splits.assert_no_leak(dict(dev=[dict(rows[0], event_key='e1', ts=T0)], test=[], burn_in=[]), T0 + 1, 0, excluded_events={'e1'})

    def test_metadata_read_later_is_not_contemporary(self):
        self.assertEqual(splits.available_at_decision(T0 + 1, T0), 'ACTUALIZED_AFTER_DECISION')
        self.assertEqual(splits.available_at_decision(T0, T0), 'CONTEMPORARY')
        self.assertEqual(splits.available_at_decision(None, T0), 'UNDATED')


class Bench(unittest.TestCase):
    def rows(self):
        rng = random.Random(6)
        start = bench.SPLIT_TS - 3 * 86400
        return sorted((dict(wallet=f'w{w}', ts=start + rng.randrange(6 * 86400), observed_at=start + 7 * 86400, event_key=f'e{w % 5}', condition_id=f'c{w % 5}', token_id=f't{w % 5}', is_buy=rng.random() < .8, size=x / .5, price=.5, nominal=x, tx=f'0x{w}{i}', outcome='Yes')
                       for w in range(60) for i, x in enumerate(rng.lognormvariate(6, 1) for _ in range(40))), key=lambda r: r['ts'])

    def test_shuffle_keeps_amounts_and_total_span(self):
        groups = [dict(ts=T0 + i * i, nominal=float(i), is_buy=i % 2 == 0) for i in range(30)]
        out = bench.shuffled(groups, random.Random(7))
        self.assertEqual(sorted(g['nominal'] for g in out), sorted(g['nominal'] for g in groups))
        self.assertEqual((out[0]['ts'], out[-1]['ts']), (groups[0]['ts'], groups[-1]['ts']))
        self.assertNotEqual([g['nominal'] for g in out], [g['nominal'] for g in groups])

    def test_sustained_injection_leaves_rows_before_the_change_alone(self):
        groups = [dict(ts=T0 + i, nominal=100.0, is_buy=True) for i in range(40)]
        out, change, end = bench.inject('sustained', 5, groups, random.Random(8), 100.0)
        self.assertTrue(all(g['nominal'] == 100.0 for g in out if g['ts'] < change))
        self.assertTrue(all(g['nominal'] == 500.0 for g in out if change <= g['ts'] <= end))

    def test_a_run_is_reproducible_and_never_reports_without_a_threshold(self):
        rows = self.rows()
        first, second = bench.run(rows, seed=9, wallets_per_scenario=5), bench.run(rows, seed=9, wallets_per_scenario=5)
        self.assertEqual(first, second)
        self.assertEqual(first['split']['dev_wallets'] + first['split']['test_wallets'] <= 60, True)
        if not first['chosen']:
            self.assertEqual(first['verdict'], 'NO_THRESHOLD_MET_THE_CHANCE_TARGET')
            self.assertNotIn('trigger_rates_test', first)

    def test_wilson_says_nothing_without_a_denominator(self):
        self.assertIsNone(bench.wilson(0, 0)['rate'])
        self.assertGreater(bench.wilson(0, 50)['high'], 0)


class FundingBench(unittest.TestCase):
    def test_a_hub_limit_removes_a_sender_and_groups_join_only_through_pairs(self):
        edges = [dict(source=ZERO_ADDRESS, target=f'0x{i}') for i in range(6)] + [dict(source='0xf', target='0x1'), dict(source='0xf', target='0x2')]
        wallets = {f'0x{i}' for i in range(6)}
        self.assertEqual(len(funding_bench.funder_pairs(edges, wallets, None)[0]), 15)
        self.assertEqual(funding_bench.funder_pairs(edges, wallets, 5)[0], {('0x1', '0x2')})
        self.assertEqual(funding_bench.components({('a', 'b'), ('b', 'c'), ('x', 'y')}), [3, 2])


if __name__ == '__main__':
    unittest.main()
