"""Unit checks of the tape parser and roles of study_sync_v2, on synthetic rows. No network, no real data."""
import os
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(os.environ.get('STUDY_V2', '/Volumes/PHI-Data/global-forensics/study_sync_v2')) / 'code'))
try:
    import numpy as np
    import lib_v2 as lib
    from ana_00_freeze import facts_of, stem
except ImportError as exc:
    raise unittest.SkipTest(f'needs the venv with numpy and the study folder: {exc}')


def tape_row(wallet, ts, seq=0, side='BUY', price=.1, usd=500., token='T'):
    return dict(wallet=wallet, side=side, token=token, size=usd / price, price=price, ts=ts, seq=seq)


def table(rows):
    keys = ('token', 'fact', 'wallet', 'ts', 'price', 'usd', 'prior_volume', 'mom', 'tte_s', 'guard_ok', 'part', 'win')
    columns = {k: np.array([r.get(k, default) for r in rows]) for k, default in zip(keys, (0, 0, 0, 0, .1, 500., 1e6, 2, 5e6, True, 0, 0.))}
    return lib.sort_table(columns)


class Parser(unittest.TestCase):
    def test_entrant_needs_first_row_buy_price_and_size(self):
        out = lib.entrants_of_market([tape_row('a', 100, side='SELL'), tape_row('a', 200), tape_row('b', 100, usd=50), tape_row('b', 300), tape_row('c', 100, price=.6), tape_row('d', 400)], 10 ** 6, 10 ** 6)
        self.assertEqual([e['wallet'] for e in out], ['d'])

    def test_same_second_rows_do_not_feed_each_other(self):
        out = lib.entrants_of_market([tape_row('a', 100, 0, usd=30000), tape_row('b', 100, 1, usd=30000), tape_row('c', 200, 0)], 10 ** 6, 10 ** 6)
        volume = {e['wallet']: e['prior_volume'] for e in out}
        self.assertEqual((volume['a'], volume['b']), (0.0, 0.0))
        self.assertAlmostEqual(volume['c'], 60000.0)

    def test_guard_removes_rows_near_a_touch_and_after_close(self):
        rows = [tape_row('a', 1000), tape_row('b', 1950), tape_row('z', 2000, price=.95, usd=500), tape_row('c', 2500)]
        out = {e['wallet']: e['guard_ok'] for e in lib.entrants_of_market(rows, 10 ** 6, 2400)}
        self.assertEqual(out, dict(a=True, b=False, c=False))

    def test_momentum_reads_only_earlier_rows(self):
        rows = [tape_row('a', 1000, price=.10), tape_row('b', 5000, price=.20), tape_row('c', 5100, price=.30)]
        out = {e['wallet']: e['mom'] for e in lib.entrants_of_market(rows, 10 ** 6, 10 ** 6)}
        self.assertEqual(out['a'], lib.MOM_UNKNOWN)
        self.assertEqual(out['b'], lib.MOM_FLAT)
        self.assertEqual(out['c'], lib.MOM_STRONG)


class Roles(unittest.TestCase):
    def test_trigger_is_decided_at_the_row_and_a_control_stays_a_control(self):
        t = table([dict(wallet=i, ts=1000 + i) for i in range(3)])
        role, count = lib.roles(t, 300)
        self.assertEqual(list(role), [0, 0, 1])
        self.assertEqual(list(count), [1, 2, 3])

    def test_a_set_inside_the_cooldown_is_dropped_and_a_lone_row_stays_a_control(self):
        t = table([dict(wallet=i, ts=1000 + i) for i in range(4)] + [dict(wallet=9, ts=9000)])
        role, _ = lib.roles(t, 300)
        self.assertEqual(list(role), [0, 0, 1, -1, 0])

    def test_tokens_do_not_mix(self):
        t = table([dict(wallet=1, ts=1000, token=1), dict(wallet=2, ts=1001, token=1), dict(wallet=3, ts=1002, token=2)])
        self.assertEqual(list(lib.roles(t, 300)[0]), [0, 0, 0])

    def test_crowd_excludes_the_window_itself(self):
        t = table([dict(wallet=i, ts=1000 + i) for i in range(5)] + [dict(wallet=9, ts=1000 + 400)])
        self.assertEqual(int(lib.crowd(t, 300)[-1]), 5)

    def test_h2_statistic_rises_with_the_window(self):
        ts = np.array([0., 100., 250., 700., 1100.])
        token = np.zeros(5, dtype=np.int64)
        counts = [lib.member_count(token, ts, w) for w in (30, 300, 900, 3600)]
        self.assertEqual(counts, sorted(counts))

    def test_near_set_arm_leaves_tokens_with_a_set(self):
        t = table([dict(wallet=i, ts=1000 + i, token=1) for i in range(3)] + [dict(wallet=7, ts=1000, token=2), dict(wallet=8, ts=1001, token=2), dict(wallet=9, ts=9000, token=2)])
        role, count = lib.roles(t, 300)
        arm = lib.near_set_arm(t, role, count)
        self.assertEqual(list(arm), [-1, -1, -1, 0, 1, 0])


class Facts(unittest.TestCase):
    def test_a_ladder_of_dates_is_one_fact(self):
        self.assertEqual(stem('will-x-happen-by-march-31-2026'), stem('will-x-happen-by-june-30-2026'))
        markets = [dict(conditionId='a', slug='will-x-happen-by-march-31'), dict(conditionId='b', slug='will-x-happen-by-june-30'), dict(conditionId='c', slug='other-question')]
        facts = facts_of(markets)
        self.assertEqual(facts['a'], facts['b'])
        self.assertNotEqual(facts['a'], facts['c'])

    def test_shared_event_joins(self):
        facts = facts_of([dict(conditionId='a', slug='x-one', event_slugs=['e']), dict(conditionId='b', slug='y-two', event_slugs=['e'])])
        self.assertEqual(facts['a'], facts['b'])


class Verdict(unittest.TestCase):
    base = dict(h1=dict(diff=.1, p=.01, ci=[.02, .2], matched_share=1., facts_triggers=300), h2=dict(p=.01), nce=dict(diff=0., ci=[-.02, .02]), by_part={0: .1, 1: .1}, influence=.05)

    def test_all_conditions_give_the_association(self):
        self.assertEqual(lib.verdict(self.base)[0], 'TIMING_ASSOCIATION')

    def test_each_failure_blocks_it(self):
        for change in (dict(h2=dict(p=.2)), dict(nce=dict(diff=.08, ci=[-.01, .2])), dict(nce=dict(diff=.01, ci=[.001, .02])), dict(by_part={0: .1, 1: -.1}), dict(influence=-.01)):
            self.assertEqual(lib.verdict(dict(self.base, **change))[0], 'POSITIVE_NOT_INTERPRETABLE', change)

    def test_a_bound_needs_the_upper_end_under_it(self):
        off = dict(self.base, h1=dict(diff=.01, p=.5, ci=[-.03, .05], matched_share=1., facts_triggers=300))
        self.assertEqual(lib.verdict(off)[0], 'BOUNDED_NULL')
        off['h1'] = dict(off['h1'], ci=[-.03, .12])
        self.assertEqual(lib.verdict(off)[0], 'INCONCLUSIVE')

    def test_too_few_matched_or_too_few_facts_say_so(self):
        self.assertEqual(lib.verdict(dict(self.base, h1=dict(self.base['h1'], matched_share=.5)))[0], 'INCONCLUSIVE')
        self.assertEqual(lib.verdict(dict(self.base, h1=dict(self.base['h1'], facts_triggers=50, p=.5)))[0], 'INCONCLUSIVE')


if __name__ == '__main__':
    unittest.main(verbosity=1)
