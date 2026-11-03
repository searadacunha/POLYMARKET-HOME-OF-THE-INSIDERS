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


def tape_row(wallet, ts, side='BUY', price=.1, usd=500., token='T'):
    return dict(wallet=wallet, side=side, token=token, size=usd / price, price=price, ts=ts)


def table(rows):
    keys = ('token', 'fact', 'wallet', 'ts', 'price', 'usd', 'prior_volume', 'mom', 'tte_s', 'guard_ok', 'strict_ok', 'part', 'win')
    columns = {k: np.array([r.get(k, default) for r in rows]) for k, default in zip(keys, (0, 0, 0, lib.HOLDOUT_FROM, .1, 500., 1e6, 2, 5e6, True, True, 0, 0.))}
    return lib.sort_table(columns)


class Parser(unittest.TestCase):
    def test_entrant_needs_first_row_buy_price_and_size(self):
        out = lib.entrants_of_market([tape_row('a', 100, side='SELL'), tape_row('a', 200), tape_row('b', 100, usd=50), tape_row('b', 300), tape_row('c', 100, price=.6), tape_row('d', 400)], 10 ** 6, 10 ** 6)
        self.assertEqual([e['wallet'] for e in out], ['d'])

    def test_same_second_rows_do_not_feed_each_other(self):
        out = lib.entrants_of_market([tape_row('a', 100, usd=30000), tape_row('b', 100, usd=30000), tape_row('c', 200)], 10 ** 6, 10 ** 6)
        volume = {e['wallet']: e['prior_volume'] for e in out}
        self.assertEqual((volume['a'], volume['b']), (0.0, 0.0))
        self.assertAlmostEqual(volume['c'], 60000.0)

    def test_guard_removes_rows_near_a_touch_and_after_close(self):
        rows = [tape_row('a', 100), tape_row('b', 1950), tape_row('z', 2000, price=.95, usd=500), tape_row('c', 2500)]
        out = {e['wallet']: e['guard_ok'] for e in lib.entrants_of_market(rows, 10 ** 6, 2400)}
        self.assertEqual(out, dict(a=True, b=False, c=False))

    def test_momentum_reads_only_earlier_rows(self):
        rows = [tape_row('a', 1000, price=.10), tape_row('b', 5000, price=.20), tape_row('c', 5100, price=.30)]
        out = {e['wallet']: e['mom'] for e in lib.entrants_of_market(rows, 10 ** 6, 10 ** 6)}
        self.assertEqual(out['a'], lib.MOM_UNKNOWN)
        self.assertEqual(out['b'], lib.MOM_FLAT)
        self.assertEqual(out['c'], lib.MOM_STRONG)


    def test_a_row_before_a_jump_is_guarded_and_the_same_row_long_before_is_not(self):
        rows = [tape_row('a', 1000), tape_row('b', 5000), tape_row('z', 5500, price=.30, usd=500, side='SELL')]
        out = {e['wallet']: e['guard_ok'] for e in lib.entrants_of_market(rows, 10 ** 6, 10 ** 6)}
        self.assertEqual(out, dict(a=True, b=False))

    def test_a_sweep_in_one_second_ends_on_its_dearest_row(self):
        rows = [tape_row('c', 100, price=.30), tape_row('a', 100, price=.10), tape_row('b', 100, price=.20)]
        self.assertEqual([e['wallet'] for e in lib.entrants_of_market(rows, 10 ** 6, 10 ** 6)], ['a', 'b', 'c'])


    def test_the_strict_guard_sees_a_slow_rise_the_first_guard_does_not(self):
        rows = [tape_row('a', 1000), tape_row('z', 20000, price=.16, side='SELL')]
        out = lib.entrants_of_market(rows, 10 ** 6, 10 ** 6)[0]
        self.assertEqual((out['guard_ok'], out['strict_ok']), (True, False))

    def test_future_max_reads_later_seconds_only(self):
        self.assertEqual(lib.future_max([1, 1, 2, 9], [.5, .9, .3, .4], 5), [.3, .3, None, None])


class Roles(unittest.TestCase):
    def test_trigger_is_decided_at_the_row_and_a_control_stays_a_control(self):
        t = table([dict(wallet=i, ts=lib.HOLDOUT_FROM + 1000 + i) for i in range(3)])
        role, count = lib.roles(t, 300)
        self.assertEqual(list(role), [0, 0, 1])
        self.assertEqual(list(count), [1, 2, 3])

    def test_a_set_inside_the_cooldown_is_dropped_and_a_lone_row_stays_a_control(self):
        t = table([dict(wallet=i, ts=lib.HOLDOUT_FROM + 1000 + i) for i in range(4)] + [dict(wallet=9, ts=lib.HOLDOUT_FROM + 9000)])
        role, _ = lib.roles(t, 300)
        self.assertEqual(list(role), [0, 0, 1, -1, 0])

    def test_tokens_do_not_mix(self):
        t = table([dict(wallet=1, ts=lib.HOLDOUT_FROM + 1000, token=1), dict(wallet=2, ts=lib.HOLDOUT_FROM + 1001, token=1), dict(wallet=3, ts=lib.HOLDOUT_FROM + 1002, token=2)])
        self.assertEqual(list(lib.roles(t, 300)[0]), [0, 0, 0])

    def test_crowd_excludes_the_window_itself(self):
        t = table([dict(wallet=i, ts=lib.HOLDOUT_FROM + 1000 + i) for i in range(5)] + [dict(wallet=9, ts=lib.HOLDOUT_FROM + 1000 + 400)])
        self.assertEqual(int(lib.crowd(t, 300)[-1]), 5)

    def test_h2_statistic_rises_with_the_window(self):
        ts = np.array([0., 100., 250., 700., 1100.])
        token = np.zeros(5, dtype=np.int64)
        counts = [lib.member_count(token, ts, w) for w in (30, 300, 900, 3600)]
        self.assertEqual(counts, sorted(counts))

    def test_rows_before_the_first_study_ends_are_not_scored(self):
        t = table([dict(wallet=1, ts=lib.HOLDOUT_FROM - 1), dict(wallet=2, ts=lib.HOLDOUT_FROM)])
        self.assertEqual(list(lib.eligible(t)), [False, True])

    def test_near_set_arm_leaves_tokens_with_a_set(self):
        t = table([dict(wallet=i, ts=lib.HOLDOUT_FROM + 1000 + i, token=1) for i in range(3)] + [dict(wallet=7, ts=lib.HOLDOUT_FROM + 1000, token=2), dict(wallet=8, ts=lib.HOLDOUT_FROM + 1001, token=2), dict(wallet=9, ts=lib.HOLDOUT_FROM + 9000, token=2)])
        role, count = lib.roles(t, 300)
        arm = lib.near_set_arm(t, role, count)
        self.assertEqual(list(arm), [-1, -1, -1, 0, 1, 0])


class Scoring(unittest.TestCase):
    def test_controls_of_the_same_fact_never_score_a_trigger(self):
        """Trigger and same-fact controls all win at 0.10: excess +0.9 on both. Other-fact controls lose. A same-fact control would hide this."""
        fact = np.array([0, 0, 0, 1, 1, 1])
        cell = np.zeros(6, dtype=np.int64)
        arm = np.array([1, 0, 0, 0, 0, 0], dtype=np.int8)
        excess = np.array([.9, .9, .9, -.1, -.1, -.1])
        self.assertAlmostEqual(lib.h1(fact, cell, arm, excess, 0)['diff'], 1.0)

    def test_a_trigger_with_no_control_elsewhere_is_unmatched(self):
        r = lib.h1(np.array([0, 0]), np.zeros(2, dtype=np.int64), np.array([1, 0], dtype=np.int8), np.array([.5, .5]), 0)
        self.assertEqual(r['matched'], 0) if r['diff'] is None else self.fail('a same-fact control was used')

    def test_bootstrap_interval_contains_the_estimate_on_noise(self):
        rng = np.random.default_rng(1)
        n = 3000
        fact = rng.integers(0, 200, n)
        arm = (rng.random(n) < .1).astype(np.int8)
        excess = (rng.random(n) < .2) - .2
        r = lib.h1(fact, np.zeros(n, dtype=np.int64), arm, excess, 400)
        self.assertLess(r['ci'][0], r['diff'])
        self.assertGreater(r['ci'][1], r['diff'])
        self.assertGreater(r['p'], .001)


class Wallets(unittest.TestCase):
    def test_sets_of_the_same_wallets_are_removed_by_the_wallet_test(self):
        rows = [dict(wallet=w, ts=lib.HOLDOUT_FROM + 1000 + w, token=tok) for tok in range(4) for w in (1, 2, 3)] + [dict(wallet=10 + tok * 3 + w, ts=lib.HOLDOUT_FROM + 1000 + w, token=10 + tok) for tok in range(3) for w in range(3)]
        t = table(rows)
        role, count = lib.roles(t, 300)
        arm = lib.without_top_wallets(t, role.copy(), count, top=3)
        self.assertEqual(int((role == 1).sum()), 7)
        self.assertEqual(int((arm == 1).sum()), 3)


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
    base = dict(h1=dict(diff=.1, p=.01, ci=[.02, .2], matched_share=1., facts_triggers=300, kish_facts=200.), by_week=dict(diff=.1, p=.01, ci=[.02, .2]), strict=dict(diff=.08, p=.02), raw=dict(mean=.1, ci=[.02, .2]), without_top_wallets=.05, h2=dict(p=.01), nce=dict(diff=0., ci=[-.02, .02], matched=500), by_part={0: .1, 1: .1}, influence=.05)

    def test_all_conditions_give_the_association(self):
        self.assertEqual(lib.verdict(self.base)[0], 'TIMING_ASSOCIATION')

    def test_each_failure_blocks_it(self):
        for change in (dict(h2=dict(p=.2)), dict(nce=dict(diff=.08, ci=[-.01, .2], matched=500)), dict(nce=dict(diff=.01, ci=[.001, .02], matched=500)), dict(nce=dict(diff=0., ci=[-.1, .1], matched=10)), dict(by_week=dict(diff=.1, p=.2, ci=[-.1, .3])), dict(strict=dict(diff=.01, p=.4)), dict(without_top_wallets=None), dict(by_part={0: .1, 1: -.1}), dict(influence=-.01)):
            self.assertEqual(lib.verdict(dict(self.base, **change))[0], 'POSITIVE_NOT_INTERPRETABLE', change)

    def quiet(self, **change):
        return dict(self.base, h1=dict(dict(diff=.01, p=.5, ci=[-.03, .05], matched_share=1., facts_triggers=300, kish_facts=200.), **change), by_week=dict(diff=.01, p=.5, ci=[-.03, .06]), raw=dict(mean=.01, ci=[-.03, .05]))

    def test_a_bound_needs_all_three_upper_ends_under_it(self):
        self.assertEqual(lib.verdict(self.quiet())[0], 'BOUNDED_NULL')
        self.assertEqual(lib.verdict(self.quiet(ci=[-.03, .12]))[0], 'INCONCLUSIVE')
        self.assertEqual(lib.verdict(dict(self.quiet(), raw=dict(mean=.2, ci=[.1, .3])))[0], 'INCONCLUSIVE')
        self.assertEqual(lib.verdict(dict(self.quiet(), by_week=dict(diff=.01, p=.5, ci=[-.03, .11])))[0], 'INCONCLUSIVE')

    def test_no_bound_on_a_significantly_negative_result_or_few_effective_facts(self):
        self.assertEqual(lib.verdict(self.quiet(diff=-.05, p=.01, ci=[-.09, -.01]))[0], 'INCONCLUSIVE')
        self.assertEqual(lib.verdict(self.quiet(kish_facts=20.))[0], 'INCONCLUSIVE')

    def test_too_few_matched_or_too_few_facts_say_so(self):
        self.assertEqual(lib.verdict(dict(self.base, h1=dict(self.base['h1'], matched_share=.5)))[0], 'INCONCLUSIVE')
        self.assertEqual(lib.verdict(dict(self.base, h1=dict(self.base['h1'], facts_triggers=50, p=.5)))[0], 'INCONCLUSIVE')


if __name__ == '__main__':
    unittest.main(verbosity=1)
