"""Behaviour of the shadow engine. Chain tests use real receipts; synthetic rows prove mechanics, not detection power."""
import ast
import copy
import json
import random
import re
import shutil
import sqlite3
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signal_engine import dossiers, service  # noqa: E402
from signal_engine.comparators import Comparators, strata  # noqa: E402
from signal_engine.evidence_scoring import ANOMALOUS, CORROBORATED_BEHAVIOR, INSUFFICIENT_EVIDENCE, classify  # noqa: E402
from signal_engine import case_checks, status_page  # noqa: E402
from signal_engine.funding_graph import ZERO_ADDRESS, behavioural_links, build_funding_links, corroborating_funding, economic_role, possible_coordination, unique_edges  # noqa: E402
from signal_engine.phenomena import NOT_EVALUATED, OBSERVED, assess_phenomena  # noqa: E402
from signal_engine.market_information_risk import HIGH, LOW, UNKNOWN, assess_market, information_timeline  # noqa: E402
from signal_engine.position_anomalies import independent_events, reconstruct_from_fills  # noqa: E402
from signal_engine.post_event_investigation import compare_with_other_side, investigate_resolved_case, price_after_entry, settle_position, wallet_record_on_resolved  # noqa: E402
from signal_engine.prospective_detection import apply_review_budget, fingerprint, load_config, run_cycle  # noqa: E402
from signal_engine.store import SignalStore  # noqa: E402
from signal_engine.wallet_behavior import BASELINE_INSUFFICIENT, wallet_profile  # noqa: E402

T0 = 1_800_000_000
CONFIG = load_config()
FIXTURE = json.loads((ROOT / 'tests/fixtures/chain_receipts_sample.json').read_text())


def row(n, wallet, event, condition, ts, nominal, price=.3, buy=True, token=None, observed=None):
    return dict(key=f'k{n}', wallet=wallet, ts=ts, observed_at=ts + 60 if observed is None else observed, event_key=event, market_id='m' + condition, condition_id=condition, token_id=token or 'tok' + condition,
                is_buy=buy, size=nominal / price, price=price, tx=f'0x{n:064x}', outcome='Yes')


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix='signal_')
        self.store = SignalStore(self.dir + '/state.sqlite3')
        self.n = 0

    def tearDown(self):
        self.store.close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def next(self, *args, **kwargs):
        self.n += 1
        return row(self.n, *args, **kwargs)

    def background(self, wallets=400, title='Will the committee approve the budget?', end=T0 + 40 * 86400, seed=1):
        rng = random.Random(seed)
        for i in range(wallets):
            event, condition = f'e{i % 40}', f'c{i % 40}'
            self.store.add_market(condition, title=title, event_key=event, market_id='m' + condition, end_at=end, cataloged=True)
            rows = [self.next(f'w{i}', event, condition, T0 - rng.randrange(0, 3 * 86400), rng.uniform(100, 1500), rng.choice((.15, .3, .6, .9))) for _ in range(rng.randrange(2, 6))]
            run_cycle(self.store, self.store.add_trades(rows), T0, CONFIG, emit=False)

    def buy_case(self, wallets=('n1', 'n2', 'n3'), nominal=60000, title='Will the company announce the acquisition?', end=T0 + 40 * 86400, closed=None):
        self.store.add_market('cx', title=title, event_key='ex', market_id='mcx', end_at=end, closed_at=closed, cataloged=True)
        rows = [self.next(w, 'ex', 'cx', T0 + 50 + i, nominal) for i, w in enumerate(wallets)]
        return run_cycle(self.store, self.store.add_trades(rows), T0 + 200, CONFIG)


class MarketInformationRisk(unittest.TestCase):
    def test_structures_of_the_requested_categories(self):
        cases = [("Will OpenAI launch a browser by March 31?", 'corporate_leadership', HIGH), ("Will X appoint a new CEO before July?", 'corporate_leadership', HIGH), ("Fed decision in December?", 'committee', None),
                 ("Airdrop by June 30?", 'corporate_leadership', HIGH), ("Will the documentary identify the founder?", 'small_group', HIGH), ("Who will win the Best Picture award?", 'small_group', HIGH),
                 ("Q3 earnings above estimates?", 'corporate_leadership', HIGH), ("Will the Supreme Court rule for the plaintiff?", 'judicial', None), ("Military action against Country A by Friday?", 'government_or_military', HIGH),
                 ("Bitcoin above 100,000 on June 1?", 'continuous_price', LOW), ("Will the hurricane make landfall?", 'natural_phenomenon', LOW)]
        for title, structure, level in cases:
            risk = assess_market(title)
            self.assertEqual(risk.decision_structure, structure, title)
            if level:
                self.assertEqual(risk.level, level, title)

    def test_sport_and_elections_are_scored_not_excluded(self):
        self.assertEqual(assess_market("Team A vs. Team B").decision_structure, 'competitive_outcome')
        self.assertEqual(assess_market("Team A vs. Team B: first goal scorer?").decision_structure, 'competitive_micro_event')
        self.assertEqual(assess_market("Who wins the general election?").decision_structure, 'broad_public')
        # A candidate's own choice inside an election is one person's decision.
        self.assertEqual(assess_market("Will the candidate drop out of the general election?").decision_structure, 'single_actor')

    def test_cases_found_while_reading_a_real_queue(self):
        self.assertEqual(assess_market("Spread: Team A (-3.5)").decision_structure, 'competitive_outcome')
        self.assertEqual(assess_market("Will Party A control the Senate after the 2030 midterm elections?").decision_structure, 'broad_public')
        self.assertEqual(assess_market("Country A leadership change by December 31?").decision_structure, 'government_or_military')

    def test_resolution_text_alone_cannot_reach_high(self):
        risk = assess_market("Who will take it in 2030?", rules="Resolves to the official release announced by the company.")
        self.assertEqual((risk.decision_structure, risk.level, risk.confidence), ('corporate_leadership', 'MEDIUM', 'low'))

    def test_unknown_is_not_low(self):
        risk = assess_market("Blue or green?")
        self.assertEqual(risk.level, UNKNOWN)
        self.assertIsNone(risk.ordinal_score)

    def test_rules_and_tags_are_weaker_than_the_title(self):
        by_rules = assess_market("Who will take it in 2030?", rules="The winner is decided by a jury of journalists.")
        self.assertEqual((by_rules.decision_structure, by_rules.confidence), ('small_group', 'low'))
        by_tag = assess_market("Who will take it in 2030?", tags=['awards'])
        self.assertEqual((by_tag.decision_structure, by_tag.confidence), ('small_group', 'medium'))
        self.assertEqual(assess_market("Who will take it in 2030?").level, UNKNOWN)

    def test_never_presented_as_probability(self):
        self.assertIn('not a probability', assess_market("Fed decision in December?").as_dict()['meaning'])

    def test_timeline_invents_no_date(self):
        timeline = information_timeline()
        self.assertIsNone(timeline['known_to_restricted_group']['at'])
        self.assertEqual(timeline['first_credible_public_information']['status'], 'unknown')
        self.assertEqual(timeline['market_resolution']['status'], 'not_resolved')
        self.assertEqual(information_timeline(dict(public_at=T0, source='s'))['first_credible_public_information']['at'], T0)


class ComparatorsBehaviour(Base):
    def test_too_few_values_give_no_tail(self):
        c = Comparators(self.store, 200, .01)
        out = c.tail(strata('small_group', .3, None, T0, 100, None), 'max_market_spend', 1e9)
        self.assertEqual(out['status'], 'COMPARATOR_INSUFFICIENT')
        self.assertIsNone(out['tail'])

    def test_falls_back_and_says_so(self):
        c = Comparators(self.store, 200, .01)
        keys = strata('small_group', .3, None, T0, 100, None)
        for i in range(250):
            c.remember(['discrete|*'], 'max_market_spend', f'u{i}', T0, float(i))
        c.begin_cycle()
        out = c.tail(keys, 'max_market_spend', 1e9)
        self.assertEqual((out['stratum'], out['fallback_level']), ('discrete|*', 2))
        self.assertAlmostEqual(out['tail'], 1 / 251)

    def test_only_anomalous_pairs_are_kept(self):
        self.background()
        ordinary = self.store.cx.execute('SELECT COUNT(*) FROM pairs').fetchone()[0]
        self.assertLess(ordinary, 400 * .05)  # a few tails are extreme by construction, most pairs are not stored
        self.buy_case()
        self.assertEqual(self.store.cx.execute('SELECT COUNT(*) FROM pairs').fetchone()[0], ordinary + 3)

    def test_a_batch_does_not_dilute_itself(self):
        self.background()
        outputs, _ = self.buy_case(('a', 'b', 'c', 'd', 'e'))
        self.assertEqual(len(outputs), 1)
        self.assertEqual(len(outputs[0]['pairs']), 5)


class WalletBehaviour(Base):
    def test_baseline_insufficient_is_stated(self):
        self.store.add_market('cx', title='t', event_key='ex', market_id='mcx')
        self.store.add_trades([self.next('w', 'ex', 'cx', T0, 5000)])
        p = wallet_profile(self.store, 'w', 'ex', T0 + 200, CONFIG)
        self.assertEqual(p['baseline_status'], BASELINE_INSUFFICIENT)
        self.assertIsNone(p['size_ratio'])
        self.assertIsNone(p['verified_first_chain_activity'])
        self.assertTrue(p['first_trade_on_this_event'])

    def test_a_row_not_yet_observed_does_not_exist(self):
        self.store.add_market('cx', title='t', event_key='ex', market_id='mcx')
        self.store.add_trades([self.next('w', 'ex', 'cx', T0, 5000, observed=T0 + 9000)])
        self.assertIsNone(wallet_profile(self.store, 'w', 'ex', T0 + 200, CONFIG))


class ChainReconstruction(unittest.TestCase):
    """Real decoded receipts, both exchange generations of market, against Data API rows for the same transaction."""

    def test_fixture_covers_negative_risk_and_standard(self):
        kinds = {s['kind'] for s in FIXTURE}
        self.assertEqual(kinds, {'neg_risk', 'standard'})
        self.assertGreaterEqual(len(FIXTURE), 20)

    def test_positions_match_the_reported_trades(self):
        checked = 0
        for sample in FIXTURE:
            wallets = {t['wallet'] for t in sample['trades']}
            for wallet in wallets:
                expected = {}
                for t in sample['trades']:
                    if t['wallet'] == wallet:
                        expected[t['token_id']] = expected.get(t['token_id'], 0) + (t['size'] if t['side'] == 'BUY' else -t['size'])
                got = reconstruct_from_fills(sample['fills'], wallet)['tokens']
                for token, shares in expected.items():
                    self.assertIn(token, got, sample['transaction_hash'])
                    self.assertAlmostEqual(got[token]['net_shares'], shares, delta=max(1e-4, abs(shares) * 1e-5), msg=sample['transaction_hash'])
                    checked += 1
        self.assertGreater(checked, 20)

    def test_taker_field_never_gives_a_position(self):
        sample = next(s for s in FIXTURE if len(s['fills']) >= 2)
        fill = sample['fills'][0]
        outsider = fill['taker']
        owned = [f for f in sample['fills'] if f['maker'].lower() == outsider.lower()]
        got = reconstruct_from_fills(sample['fills'], outsider)
        self.assertEqual(sum(t['fills'] for t in got['tokens'].values()), len({(f['transaction_hash'], f['log_index']) for f in owned}))

    def test_duplicates_and_removed_logs_count_once_or_not_at_all(self):
        sample = FIXTURE[0]
        wallet = sample['trades'][0]['wallet']
        once = reconstruct_from_fills(sample['fills'], wallet)['tokens']
        twice = reconstruct_from_fills(sample['fills'] * 2, wallet)
        self.assertEqual(twice['tokens'], once)
        self.assertGreater(twice['skipped']['duplicate'], 0)
        removed = [dict(f, removed=True) for f in sample['fills']]
        self.assertEqual(reconstruct_from_fills(removed, wallet)['tokens'], {})

    def test_correlated_events_count_as_one_bet(self):
        self.assertEqual(independent_events(['e1', 'e2', 'e3'], {'e1': 'g', 'e2': 'g'}), 2)


class ProspectiveEngine(Base):
    def test_ordinary_background_stays_silent(self):
        self.background()
        self.assertEqual(self.store.cx.execute('SELECT COUNT(*) FROM cases').fetchone()[0], 0)

    def test_no_comparator_means_no_finding_and_it_is_counted(self):
        outputs, summary = self.buy_case(('solo',))
        self.assertEqual(outputs, [])
        self.assertEqual(summary['no_comparator'], 1)

    def test_converging_wallets_are_corroborated_and_reviewed(self):
        self.background()
        outputs, _ = self.buy_case()
        self.assertEqual(outputs[0]['category'], CORROBORATED_BEHAVIOR)
        self.assertTrue(outputs[0]['wants_review'])
        self.assertEqual(outputs[0]['risk']['level'], HIGH)

    def test_one_large_wallet_is_anomalous_without_corroboration(self):
        self.background()
        outputs, _ = self.buy_case(('solo',))
        self.assertEqual(outputs[0]['category'], ANOMALOUS)

    def test_continuous_market_is_scored_but_never_reviewed(self):
        self.background(title='Bitcoin Up or Down')
        outputs, _ = self.buy_case(title='Bitcoin Up or Down')
        self.assertTrue(outputs)
        self.assertTrue(all(o['continuous_market'] and not o['wants_review'] for o in outputs))

    def test_sport_is_not_excluded(self):
        self.background(title='Team A vs. Team B')
        outputs, _ = self.buy_case(title='Team C vs. Team D')
        self.assertEqual(outputs[0]['category'], CORROBORATED_BEHAVIOR)
        self.assertEqual(outputs[0]['risk']['level'], LOW)
        self.assertFalse(outputs[0]['wants_review'])  # scored and queued, but aligned bettors on a match do not notify

    def test_a_single_person_decision_inside_a_sport_notifies(self):
        self.background(title='Team A vs. Team B')
        outputs, _ = self.buy_case(title='Team C vs. Team D: first goal scorer?')
        self.assertTrue(outputs[0]['wants_review'])

    def test_rare_combination_fires_where_size_alone_would_not(self):
        """The positive control that failed on real background: rarity is joint, not per dimension."""
        self.store.add_market('cw', title='Will the bill pass?', event_key='ew', market_id='mcw', end_at=T0 + 40 * 86400, cataloged=True)
        rng = random.Random(3)
        # Established wallets with large bets: spend is common, new and concentrated wallets are not.
        for i in range(300):
            rows = [self.next(f'old{i}', f'e{i % 30}', f'c{i % 30}', T0 - 5 * 86400 - j * 3600, 300) for j in range(10)]
            rows.append(self.next(f'old{i}', f'e{i % 30}', f'c{i % 30}', T0 - 100, rng.uniform(40000, 500000)))
            rows.append(self.next(f'old{i}', 'other', 'cy', T0 - 90, rng.uniform(40000, 500000)))
            for condition in {r['condition_id'] for r in rows}:
                self.store.add_market(condition, title='Will the bill pass?', event_key=next(r['event_key'] for r in rows if r['condition_id'] == condition), market_id='m' + condition, end_at=T0 + 40 * 86400, cataloged=True)
            run_cycle(self.store, self.store.add_trades(rows), T0, CONFIG, emit=False)
        outputs, _ = run_cycle(self.store, self.store.add_trades([self.next('fresh', 'ew', 'cw', T0 + 50, 45000)]), T0 + 200, CONFIG)
        record = json.loads(self.store.cx.execute("SELECT record FROM pairs WHERE wallet='fresh'").fetchone()[0])
        self.assertIn('new_and_concentrated', record['wallet_findings'])
        self.assertLess(record['wallet_findings']['new_and_concentrated']['comparator']['tail'], CONFIG['comparator_tail'])
        self.assertIsNotNone(outputs)

    def test_three_candidates_on_one_outcome_are_corroborated_even_below_each_strict_threshold(self):
        self.store.add_market('cw', title='Will the company announce the merger?', event_key='ew', market_id='mcw', end_at=T0 + 40 * 86400, cataloged=True)
        rng = random.Random(4)
        for i in range(300):
            event, condition = f'e{i % 30}', f'c{i % 30}'
            self.store.add_market(condition, title='Will the company announce the merger?', event_key=event, market_id='m' + condition, end_at=T0 + 40 * 86400, cataloged=True)
            rows = [self.next(f'w{i}', event, condition, T0 - 100, rng.uniform(500, 100000))]
            run_cycle(self.store, self.store.add_trades(rows), T0, CONFIG, emit=False)
        rows = [self.next(w, 'ew', 'cw', T0 + 50 + i, 95000, token='tokw') for i, w in enumerate(('x1', 'x2', 'x3'))]
        outputs, _ = run_cycle(self.store, self.store.add_trades(rows), T0 + 200, CONFIG)
        self.assertEqual(outputs[0]['category'], CORROBORATED_BEHAVIOR)
        self.assertTrue(outputs[0]['wants_review'])

    def test_closed_or_due_market_is_not_reviewed(self):
        self.background()
        outputs, _ = self.buy_case(end=T0 - 10)
        self.assertTrue(all(not o['wants_review'] for o in outputs))

    def test_reobservation_is_not_a_new_case(self):
        self.background()
        self.buy_case()
        rows = [self.next('n1', 'ex', 'cx', T0 + 300, 61000)]
        outputs, summary = run_cycle(self.store, self.store.add_trades(rows), T0 + 400, CONFIG)
        self.assertEqual(outputs, [])
        self.assertEqual(summary['reobserved'], 1)
        case = self.store.cx.execute("SELECT version, reobservations FROM cases WHERE event_key='ex'").fetchone()
        self.assertEqual((case[0], case[1]), (1, 1))

    def test_future_rows_change_nothing(self):
        """Metamorphic: the decision at T is the same with or without rows observed after T."""
        results = []
        for future in (False, True):
            store = SignalStore(f'{self.dir}/m{future}.sqlite3')
            self.store, keep = store, self.store
            self.n = 0
            self.background()
            if future:
                # Numbered apart so that the real rows keep their identities. Includes an old row observed late.
                self.store.add_trades([row(90001, 'n1', 'ex', 'cx', T0 + 90000, 900000), row(90002, 'n1', 'other', 'cy', T0 + 90000, 900000), row(90003, 'zz', 'ex', 'cx', T0 + 100, 5000, observed=T0 + 95000),
                                       row(90004, 'n2', 'other', 'cy', T0 - 500000, 700, observed=T0 + 96000)])
            outputs, _ = self.buy_case()
            results.append(fingerprint([{k: o[k] for k in ('event_key', 'category', 'pairs', 'collective', 'risk')} for o in outputs]))
            store.close()
            self.store = keep
        self.assertEqual(results[0], results[1])

    def test_same_inputs_give_the_same_decision(self):
        results = []
        for i in range(2):
            store = SignalStore(f'{self.dir}/r{i}.sqlite3')
            self.store, keep = store, self.store
            self.n = 0
            self.background()
            outputs, _ = self.buy_case()
            results.append(fingerprint([{k: o[k] for k in ('event_key', 'category', 'pairs', 'collective', 'risk', 'rank')} for o in outputs]))
            store.close()
            self.store = keep
        self.assertEqual(results[0], results[1])

    def test_removing_one_row_can_lower_a_case_without_breaking_it(self):
        self.background()
        outputs, _ = self.buy_case(('a', 'b'))
        self.assertIn(outputs[0]['category'], (ANOMALOUS, CORROBORATED_BEHAVIOR))
        self.assertEqual(len(outputs[0]['pairs']), 2)

    def test_daily_ceiling_holds_cases_without_hiding_them(self):
        outputs = [dict(wants_review=True, already_review=False, rank=[3, 3, i]) for i in range(6)]
        apply_review_budget(outputs, 1, CONFIG)
        self.assertEqual(sum(o['wants_review'] for o in outputs), CONFIG['review_budget_per_day'] - 1)
        self.assertEqual(sum(o.get('budget_held', False) for o in outputs), 6 - (CONFIG['review_budget_per_day'] - 1))


class Boundaries(unittest.TestCase):
    PROSPECTIVE = ('prospective_detection', 'wallet_behavior', 'position_anomalies', 'collective_behavior', 'comparators', 'evidence_scoring', 'market_information_risk', 'store')

    def test_detection_cannot_import_post_event_analysis(self):
        for name in self.PROSPECTIVE:
            tree = ast.parse((ROOT / f'signal_engine/{name}.py').read_text())
            imported = {n.module or '' for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
            self.assertFalse([m for m in imported if 'post_event' in m], name)

    def test_detection_reads_no_outcome_field(self):
        forbidden = re.compile(r"\b(?:won|winner_flag|realized|pnl|profit|resolved_to|outcome_price|payout)\b")
        for name in self.PROSPECTIVE:
            text = (ROOT / f'signal_engine/{name}.py').read_text()
            code = '\n'.join(line for line in text.splitlines() if not line.lstrip().startswith('#'))
            tree = ast.parse(code)
            strings = {n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str) and len(n.value) < 40}
            names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)} | {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
            self.assertFalse([s for s in strings | names if forbidden.fullmatch(s)], name)

    def test_no_case_is_hardcoded(self):
        pattern = re.compile(r"0x[0-9a-fA-F]{40}\b|ballon|mbapp|yamal|dembele|thin-disclaimer|arbitrum|openai|dior|satoshi|lord miles", re.I)
        for path in sorted((ROOT / 'signal_engine').glob('*')):
            if path.suffix in ('.py', '.json'):
                self.assertFalse(pattern.findall(path.read_text()), path.name)

    def test_config_stays_out_of_the_production_bundle(self):
        self.assertFalse((ROOT / 'polysentinel/signal_engine.py').exists())
        self.assertFalse((ROOT / 'config/signal_engine.json').exists())


class PostEventEngine(unittest.TestCase):
    def test_amounts_stay_apart(self):
        trades = [dict(ts=1, size=100, price=.2, is_buy=True), dict(ts=2, size=40, price=.5, is_buy=False)]
        activity = [dict(type='REDEEM', usdc_size=60), dict(type='WITHDRAWAL', usdc_size=500)]
        s = settle_position(trades, activity, resolution_price=1, history_complete=True)
        self.assertEqual(s['status'], 'calculable')
        self.assertAlmostEqual(s['realized_trading_profit'], 40 * (.5 - .2))
        self.assertAlmostEqual(s['settlement_value_minus_cost'], 60 * (1 - .2))
        self.assertEqual((s['redeemed_amount'], s['withdrawn_amount']), (60, 500))

    def test_no_profit_without_a_known_start(self):
        trades = [dict(ts=1, size=100, price=.2, is_buy=True)]
        self.assertEqual(settle_position(trades, [], 1, history_complete=False)['status'], 'not_calculable')
        self.assertIsNone(settle_position(trades, [], 1, history_complete=False)['settlement_value_minus_cost'])
        sold_more = [dict(ts=1, size=10, price=.2, is_buy=True), dict(ts=2, size=50, price=.5, is_buy=False)]
        self.assertIn('opening inventory', settle_position(sold_more, [], 1, history_complete=True)['reason'])
        self.assertIn('cost basis', settle_position(trades, [dict(type='SPLIT', size=1)], 1, history_complete=True)['reason'])

    def test_unrealized_is_not_realized(self):
        s = settle_position([dict(ts=1, size=100, price=.2, is_buy=True)], [], None, last_price=.5, history_complete=True)
        self.assertAlmostEqual(s['unrealized_value_minus_cost'], 30)
        self.assertEqual(s['realized_trading_profit'], 0)
        self.assertIsNone(s['settlement_value_minus_cost'])

    def test_price_change_is_unknown_without_points(self):
        out = price_after_entry([(T0 + 100, .5)], T0, .3)
        self.assertAlmostEqual(out['1d'], .2)
        self.assertIsNone(price_after_entry([], T0, .3)['7d'])

    def test_hit_rate_has_a_denominator(self):
        record = wallet_record_on_resolved([dict(won=True), dict(won=False), dict(won=None)])
        self.assertEqual((record['resolved_positions'], record['won'], record['hit_rate']), (2, 1, .5))
        self.assertIn('selection_warning', compare_with_other_side([dict(won=True, entry_price=.2, nominal=10), dict(won=False, entry_price=.4, nominal=5)]))

    def test_the_sealed_case_is_not_touched(self):
        sealed = dict(event_key='e', fingerprint='abc', category='ANOMALOUS')
        before = json.dumps(sealed, sort_keys=True)
        report = investigate_resolved_case(sealed, {'w': [dict(ts=T0, size=100, price=.2, is_buy=True, token_id='t')]}, {}, {'t': [(T0 + 3600, .9)]}, {'t': 1})
        self.assertEqual(json.dumps(sealed, sort_keys=True), before)
        self.assertEqual(report['case_fingerprint'], 'abc')
        self.assertAlmostEqual(report['wallets']['w']['t']['price_change']['1d'], .7)


class FundingLinks(unittest.TestCase):
    log = 0

    def edge(self, source, target, **kw):
        FundingLinks.log += 1
        kw.setdefault('log_index', FundingLinks.log)
        return dict(dict(source=source, target=target, transaction_hash='0x' + format(FundingLinks.log, 'x').rjust(64, 'a'), block_number=5, proof_level='lien directement observable', symbol='USDC', amount=100.0, infrastructure=False, counterparty_label=None), **kw)

    def test_one_log_read_twice_is_one_edge_and_several_logs_stay_several(self):
        a = self.edge('0xf', '0xa', transaction_hash='0x1', log_index=7)
        edges, conflicts = unique_edges([a, dict(a), self.edge('0xf', '0xb', transaction_hash='0x1', log_index=8)])
        self.assertEqual((len(edges), conflicts), (2, []))

    def test_two_readings_that_disagree_are_dropped_and_reported(self):
        a = self.edge('0xf', '0xa', transaction_hash='0x1', log_index=7)
        links = build_funding_links([a, dict(a, amount=999.0), self.edge('0xf', '0xb')], ['0xa', '0xb'])
        self.assertEqual([l['kind'] for l in links], ['conflicting_records'])
        self.assertEqual(corroborating_funding(links), [])

    def test_a_mint_is_not_a_funder(self):
        links = build_funding_links([self.edge(ZERO_ADDRESS, '0xa'), self.edge(ZERO_ADDRESS, '0xb')], ['0xa', '0xb'])
        self.assertEqual((links[0]['kind'], links[0]['roles'], links[0]['assessment']), ('shared_infrastructure', ['mint'], 'SHARED_INFRASTRUCTURE'))
        self.assertEqual(corroborating_funding(links), [])

    def test_money_forwarded_in_the_same_transaction_funded_nothing(self):
        # Shape of a real conversion in the collector's receipts: in from a router, straight out again.
        def conversion(wallet, i):
            tx = f'0x{i}'
            return [self.edge('0xrouter', wallet, transaction_hash=tx, log_index=1, token='0xusdc'), self.edge(wallet, '0xbridge', transaction_hash=tx, log_index=2, token='0xusdc')]
        edges = conversion('0xa', 1) + conversion('0xb', 2)
        self.assertEqual(economic_role(edges[0], edges[:2]), 'pass_through')
        links = build_funding_links(edges, ['0xa', '0xb'])
        self.assertEqual([l['kind'] for l in links], ['shared_infrastructure'])
        self.assertEqual(corroborating_funding(links), [])

    def test_a_link_carries_its_whole_proof(self):
        links = build_funding_links([self.edge('0xf', '0xa', timestamp=T0, token='0xusdc', amount_raw='100'), self.edge('0xf', '0xb', timestamp=T0)], ['0xa', '0xb'])
        proof = links[0]['provenance'][0]
        for field in ('chain_id', 'source', 'target', 'transaction_hash', 'log_index', 'block_number', 'timestamp', 'token', 'amount', 'role', 'completeness'):
            self.assertIn(field, proof)
        self.assertEqual((proof['chain_id'], links[0]['assessment'], links[0]['ownership']), (137, 'COMMON_FUNDING_ROUTE', 'OWNERSHIP_NOT_ESTABLISHED'))

    def test_route_and_behaviour_together_are_possible_coordination_never_an_owner(self):
        route = build_funding_links([self.edge('0xf', '0xa'), self.edge('0xf', '0xb')], ['0xa', '0xb'])
        behaviour = behavioural_links(dict(convergence={'t': ['0xa', '0xb', '0xc']}, identical_amounts=[], repeated_across_events=[]))
        found = possible_coordination(route + behaviour)
        self.assertEqual((found[0]['assessment'], found[0]['wallets'], found[0]['common_owner_established']), ('POSSIBLE_COORDINATION', ['0xa', '0xb'], False))
        self.assertEqual(possible_coordination(behaviour), [])

    def test_shared_exchange_never_corroborates(self):
        links = build_funding_links([self.edge('0xex', '0xa', infrastructure=True, counterparty_label='Exchange'), self.edge('0xex', '0xb', infrastructure=True, counterparty_label='Exchange')], ['0xa', '0xb'])
        self.assertEqual(links[0]['kind'], 'shared_infrastructure')
        self.assertEqual(links[0]['confidence'], 'none')
        self.assertEqual(corroborating_funding(links), [])

    def test_shared_funder_is_low_and_never_merges_owners(self):
        links = build_funding_links([self.edge('0xf', '0xa', timestamp=T0), self.edge('0xf', '0xb', timestamp=T0 + 60)], ['0xa', '0xb'])
        self.assertEqual((links[0]['kind'], links[0]['confidence'], links[0]['common_owner_established'], links[0]['close_in_time']), ('shared_funder', 'low', False, True))
        self.assertTrue(links[0]['provenance'][0]['url'].startswith('https://polygonscan.com/tx/'))

    def test_unconfirmed_transfer_is_no_link(self):
        edge = dict(self.edge('0xa', '0xb'), proof_level='données insuffisantes')
        self.assertEqual(build_funding_links([edge], ['0xa', '0xb']), [])

    def test_behaviour_alone_does_not_corroborate(self):
        links = behavioural_links(dict(convergence={'t': ['a', 'b', 'c']}, identical_amounts=[dict(token_id='t', amount=1000, wallets=['a', 'b', 'c'])], repeated_across_events=[dict(wallets=['a', 'b'], events=['e1', 'e2'])]))
        self.assertEqual(len(links), 3)
        self.assertEqual(corroborating_funding(links), [])
        self.assertTrue(all(l['common_owner_established'] is False and l['alternative'] for l in links))

    def test_money_upgrades_an_anomaly_but_infrastructure_does_not(self):
        pair = dict(wallet_findings=dict(a=dict(comparator=dict(tail=.005))), position_findings=dict(b=dict(comparator=dict(tail=.005))), unavailable=[])
        quiet = dict(convergence={}, identical_amounts=[], repeated_across_events=[])
        risk = dict(level='HIGH', evidence=[])
        self.assertEqual(classify([pair], quiet, risk, None, CONFIG), ANOMALOUS)
        self.assertEqual(classify([pair], quiet, risk, [dict(kind='shared_infrastructure')], CONFIG), ANOMALOUS)
        self.assertEqual(classify([pair], quiet, risk, [dict(kind='shared_funder')], CONFIG), CORROBORATED_BEHAVIOR)
        self.assertEqual(classify([dict(wallet_findings={}, position_findings={}, unavailable=['BASELINE_INSUFFICIENT'])], quiet, risk, None, CONFIG), INSUFFICIENT_EVIDENCE)


class CaseFiles(Base):
    def test_every_section_and_a_limited_conclusion(self):
        self.background()
        outputs, _ = self.buy_case()
        rows = [dict(r) for r in self.store.cx.execute("SELECT * FROM trades WHERE event_key='ex'")]
        case = dossiers.build(outputs[0], rows, CONFIG)
        for key, _title in dossiers.SECTIONS:
            self.assertIn(key, case)
        self.assertEqual(case['conclusion']['category'], CORROBORATED_BEHAVIOR)
        self.assertTrue(case['conclusion']['not_a_probability'])
        text = json.dumps(case['conclusion']).lower()
        self.assertNotRegex(text, r'\d+ ?%')
        self.assertIn('private information', text)
        self.assertIn('polygonscan.com/tx/', case['chronology'][0]['url'])
        self.assertEqual(case['funding_and_transactions']['funding_status'], 'not checked yet')
        self.assertIn('unknown', case['public_information']['timeline']['known_to_restricted_group']['status'])

    def test_enrichment_is_a_new_version_and_sets_facts(self):
        self.background()
        outputs, _ = self.buy_case()
        rows = [dict(r) for r in self.store.cx.execute("SELECT * FROM trades WHERE event_key='ex'")]
        first = dossiers.build(outputs[0], rows, CONFIG)
        second = dossiers.build(dict(outputs[0], version='1-enriched'), rows, CONFIG, enrichment=dict(links=[], reconciled=[dict(status='matched', tx='0x1')], public_availability='unknown'))
        self.assertEqual(first['funding_and_transactions']['funding_status'], 'not checked yet')
        self.assertEqual(second['funding_and_transactions']['funding_status'], 'checked')
        self.assertIn('trades_confirmed_on_chain', second['evidence_axes']['evidence_completeness']['present'])
        self.assertNotEqual(fingerprint(first), fingerprint(second))


class ServiceBehaviour(Base):
    def collector(self, rows=()):
        cx = sqlite3.connect(':memory:')
        cx.executescript('''CREATE TABLE trade_index(key TEXT, wallet TEXT, trade_time REAL, observed_at REAL, condition_id TEXT);
                            CREATE TABLE object_refs(kind TEXT, key TEXT, content_id TEXT, observed_at REAL); CREATE TABLE contents(id TEXT, body BLOB);''')
        for r in rows:
            cx.execute('INSERT INTO trade_index VALUES(?,?,?,?,?)', (r['key'], r['wallet'], r['ts'], r['observed_at'], r['condition_id']))
            cx.execute("INSERT INTO object_refs VALUES('trade',?,?,?)", (r['key'], r['key'], r['observed_at']))
            cx.execute('INSERT INTO contents VALUES(?,?)', (r['key'], zlib.compress(json.dumps(dict(wallet=r['wallet'], timestamp=r['ts'], event_id='', event_slug='slug-x', market_id='', condition_id=r['condition_id'], token_id=r['token_id'], side='BUY', size=r['size'], price=r['price'], transaction_hash=r['tx'], raw=dict(title='T', pseudonym='alias'))).encode())))
        return cx

    def test_a_cut_batch_comes_back_whole_and_aliases_are_dropped(self):
        rows = [row(1, '0xab', 'e', '0xc', T0, 10, observed=T0 + 1)] + [row(i, '0xab', 'e', '0xc', T0, 10, observed=T0 + 5) for i in range(2, 5)]
        cx = self.collector(rows)
        first = service.read_new_trades(cx, 0, 2)
        self.assertEqual([t['key'] for t in first], ['k1'])
        self.assertEqual(first[0]['event_key'], 'unmapped:slug-x')
        self.assertNotIn('pseudonym', first[0])
        with self.assertRaises(RuntimeError):
            service.read_new_trades(cx, T0 + 1, 3)
        self.assertEqual(len(service.read_new_trades(cx, T0 + 1, 4)), 3)

    def test_collector_is_opened_read_only(self):
        base = Path(self.dir) / 'b.sqlite3'
        sqlite3.connect(base).execute('CREATE TABLE t(x)').connection.commit()
        kept, service.DATABASE = service.DATABASE, base
        try:
            cx = service.open_collector()
            with self.assertRaises(sqlite3.OperationalError):
                cx.execute('INSERT INTO t VALUES(1)')
            cx.close()
        finally:
            service.DATABASE = kept

    def test_chain_detects_tampering_and_config_drift_is_refused(self):
        journal = Path(self.dir) / 'j.jsonl'
        for i in range(3):
            service.append_link(journal, 'case', dict(i=i), T0 + i)
        self.assertEqual(service.verify_chain(journal)['links'], 3)
        lines = journal.read_text().splitlines()
        lines[1] = lines[1].replace('"i":1', '"i":9')
        journal.write_text('\n'.join(lines) + '\n')
        with self.assertRaises(RuntimeError):
            service.verify_chain(journal)
        other = Path(self.dir) / 'k.jsonl'
        service.append_link(other, 'genesis', dict(fingerprints={'config.json': 'other'}), T0)
        with self.assertRaises(RuntimeError):
            service.require_sealed_version(other)

    def test_case_is_sealed_then_enriched_separately(self):
        self.background()
        self.store.add_market('cx', title='Will the company announce the acquisition?', event_key='ex', market_id='mcx', end_at=T0 + 40 * 86400, cataloged=True)
        journal, reports_dir = Path(self.dir) / 'j.jsonl', Path(self.dir) / 'reports'
        reports_dir.mkdir()
        cx = self.collector()
        kept, service.notify = service.notify, lambda o: dict(exit_code=0, human_reception_verified=False)
        try:
            trades = [dict(self.next(w, 'ex', 'cx', T0 + 50 + i, 60000), title='Will the company announce the acquisition?') for i, w in enumerate(('n1', 'n2', 'n3'))]
            service.process(self.store, cx, trades, T0 + 200, CONFIG, journal=journal, report_dir=reports_dir)
            self.assertIsNone(service.run_due_enrichment(self.store, cx, T0 + 201, CONFIG, journal, reports_dir, lambda o, c: dict(links=[])))
            stem = service.run_due_enrichment(self.store, cx, T0 + 200 + CONFIG['enrichment_delay_s'], CONFIG, journal, reports_dir, lambda o, c: dict(links=[], reconciled=[dict(status='matched', tx='0x1')], public_availability='unknown'))
        finally:
            service.notify = kept
        kinds = [json.loads(line)['kind'] for line in journal.read_text().splitlines()]
        self.assertEqual(kinds, ['case', 'notification', 'enrichment'])
        self.assertIn('enriched', stem)
        self.assertTrue((reports_dir / (stem + '.html')).exists())
        self.assertEqual(self.store.get('sealed'), 1)
        self.assertEqual(self.store.get('enrichment_queue'), [])

    def test_warm_up_opens_nothing_and_its_end_survives_a_restart(self):
        rows = [row(i, f'0xw{i}', 'e', '0xc', T0 + i, 5000, observed=T0 + i + 1) for i in range(1, 6)]
        cx = self.collector(rows)
        path = self.dir + '/warm.sqlite3'
        store = SignalStore(path)
        summary = dict(pairs=0, rows=0)
        service.warm_up(store, cx, CONFIG, summary, float('inf'), float('inf'))
        store.close()
        reopened = SignalStore(path)
        self.assertIsNotNone(reopened.get('warmup_finished'))
        self.assertEqual(reopened.cx.execute('SELECT COUNT(*) FROM cases').fetchone()[0], 0)
        self.assertEqual(summary['rows'], 5)
        self.assertEqual(reopened.get('cursor'), T0 + 6)
        reopened.close()

    def test_post_event_waits_for_the_end_and_keeps_its_own_journal(self):
        self.background()
        self.buy_case()
        cx = self.collector()
        journal = Path(self.dir) / 'post.jsonl'
        calls = []

        def fetch(case, wallets, conditions, tokens, first_buy):
            calls.append(case['event_key'])
            return dict(resolution={'tokcx': 1.0}, activity={w: [] for w in wallets}, trades={w: [dict(ts=T0, size=100, price=.3, is_buy=True, token_id='tokcx')] for w in wallets}, complete={w: True for w in wallets}, prices={'tokcx': [(T0 + 3600, .8)]})

        self.assertEqual(service.run_post_event(self.store, cx, T0 + 300, CONFIG, journal, fetch), 0)
        self.assertEqual(calls, [])
        before = fingerprint(dict(self.store.cx.execute("SELECT fingerprint, category, version FROM cases WHERE event_key='ex'").fetchone()))
        self.store.cx.execute("UPDATE markets SET closed_at=? WHERE event_key='ex'", (T0 + 1000,))
        self.assertEqual(service.run_post_event(self.store, cx, T0 + 2000, CONFIG, journal, fetch), 1)
        self.assertEqual(calls, ['ex'])
        self.assertEqual(before, fingerprint(dict(self.store.cx.execute("SELECT fingerprint, category, version FROM cases WHERE event_key='ex'").fetchone())))
        link = json.loads(journal.read_text().splitlines()[0])
        self.assertEqual(link['kind'], 'post_event')
        self.assertEqual(service.run_post_event(self.store, cx, T0 + 100000, CONFIG, journal, fetch), 0)


class CollectorFirst(unittest.TestCase):
    def test_refuses_unless_the_collector_is_normal_and_recent(self):
        with tempfile.TemporaryDirectory() as tmp:
            beat = Path(tmp) / 'heartbeat.json'
            self.assertIn('unreadable', service.collector_refusal(T0, beat))
            beat.write_text(json.dumps(dict(at=T0, resource_mode='reduced')))
            self.assertIn('reduced', service.collector_refusal(T0, beat))
            beat.write_text(json.dumps(dict(at=T0, resource_mode='normal')))
            self.assertIsNone(service.collector_refusal(T0 + 10, beat))
            self.assertIn('old', service.collector_refusal(T0 + service.HEARTBEAT_MAX_AGE + 1, beat))


if __name__ == '__main__':
    unittest.main()


class Checks(Base):
    def real_format_rows(self):
        condition = '0x' + 'c' * 64
        self.background()
        self.store.add_market(condition, title='Will the company announce the acquisition?', event_key='ex', market_id='mcx', end_at=T0 + 40 * 86400, cataloged=True)
        trades = [dict(self.next('0x' + c * 40, 'ex', condition, T0 + 50 + i, 60000), tx='0x' + c * 64) for i, c in enumerate('abd')]
        outputs, _ = run_cycle(self.store, self.store.add_trades(trades), T0 + 200, CONFIG)
        return outputs, [dict(r) for r in self.store.cx.execute("SELECT * FROM trades WHERE event_key='ex'")]

    def case(self):
        outputs, rows = self.real_format_rows()
        return dossiers.build(outputs[0], rows, CONFIG), rows

    def test_a_clean_file_has_no_failure_and_is_not_called_complete(self):
        case, _ = self.case()
        self.assertEqual(case['verification']['overall'], case_checks.INCOMPLETE)
        self.assertEqual(case['verification']['checks']['public_information_dated']['status'], case_checks.NOT_VERIFIABLE)
        self.assertNotIn(case_checks.FAIL, {c['status'] for c in case['verification']['checks'].values()})

    def tampered(self, built, change):
        case = copy.deepcopy(built[0])
        change(case)
        return case_checks.check_case(case, built[1], CONFIG)

    def test_each_tampering_fails_its_own_check(self):
        def amount(case):
            case['chronology'][0]['nominal'] += 5
        def transaction(case):
            case['chronology'][0]['tx'] = '0x' + 'f' * 64
        def decided_early(case):
            case['decided_at'] = case['chronology'][0]['first_observed'] - 1
        def identifier(case):
            case['wallets'][0]['address'] = 'not-an-address'
        def owner(case):
            case['funding_and_transactions']['links'].append(dict(kind='shared_funder', provenance=[], wallets=[], common_owner_established=True))
        def missing(case):
            case['missing_data'] = []
        def public(case):
            case['public_information']['timeline']['first_credible_public_information'].update(status='documented', at=None, source=None)
        built = self.case()
        for change, name in ((amount, 'amounts_match'), (transaction, 'transactions_exist'), (decided_early, 'timestamps_coherent'), (identifier, 'identifiers_valid'), (owner, 'wallet_links_verifiable'), (missing, 'missing_data_declared'), (public, 'public_information_dated')):
            result = self.tampered(built, change)
            self.assertEqual(result['checks'][name]['status'], case_checks.FAIL, name)
            self.assertEqual(result['overall'], case_checks.FAIL, name)

    def test_a_small_comparator_fails_even_with_a_low_tail(self):
        case, rows = self.case()
        case['signals'][0]['wallet_findings'] = dict(size_break=dict(comparator=dict(tail=.001, n=3)))
        self.assertEqual(case_checks.check_case(case, rows, CONFIG)['checks']['comparators_have_denominators']['status'], case_checks.FAIL)

    def test_enriched_file_with_a_matched_receipt_passes_that_check(self):
        outputs, rows = self.real_format_rows()
        case = dossiers.build(outputs[0], rows, CONFIG, enrichment=dict(links=[], reconciled=[dict(status='matched', tx=rows[0]['tx'])]))
        self.assertEqual(case['verification']['checks']['transactions_exist']['status'], case_checks.PASS)
        self.assertEqual(case['verification']['checks']['wallet_links_verifiable']['status'], case_checks.PASS)


class FundFlowsInFiles(Checks):
    def test_an_untraced_file_says_so_and_stays_incomplete(self):
        case, _ = self.case()
        self.assertEqual(case['fund_flows']['status'], 'NOT_TRACED')
        self.assertEqual(case['verification']['checks']['fund_flows_carry_proof']['status'], case_checks.INCOMPLETE)

    def test_fund_flows_change_no_category(self):
        outputs, rows = self.real_format_rows()
        traced = dict(status='TRACED', shadow_mode=True, wallets=[dict(wallet='0xa', ownership='OWNERSHIP_NOT_ESTABLISHED', incoming=[dict(state='ONCHAIN_CONFIRMED', tx='0x' + 'a' * 64, log_index=1)], outgoing=[], upstream=[])])
        with_flows = dossiers.build(outputs[0], rows, CONFIG, enrichment=dict(links=[], reconciled=[], fund_flows=traced))
        without = dossiers.build(outputs[0], rows, CONFIG, enrichment=dict(links=[], reconciled=[]))
        self.assertEqual((with_flows['category'], with_flows['conclusion']), (without['category'], without['conclusion']))
        self.assertEqual(with_flows['verification']['checks']['fund_flows_carry_proof']['status'], case_checks.PASS)

    def test_a_relation_without_its_log_fails_the_check(self):
        case, rows = self.case()
        case['fund_flows'] = dict(status='TRACED', wallets=[dict(wallet='0xa', ownership='OWNERSHIP_NOT_ESTABLISHED', incoming=[dict(state='ONCHAIN_CONFIRMED', tx='0x' + 'a' * 64, log_index=None)], outgoing=[], upstream=[])])
        self.assertEqual(case_checks.check_case(case, rows, CONFIG)['checks']['fund_flows_carry_proof']['status'], case_checks.FAIL)


class Phenomena(unittest.TestCase):
    timeline = dict(first_credible_public_information=dict(status='unknown'))
    quiet = dict(convergence={}, identical_amounts=[], repeated_across_events=[])

    def pair(self, wallet=None, position=None):
        return dict(wallet='0xa', wallet_findings=wallet or {}, position_findings={}, position=position or {})

    def test_spoofing_and_wash_stay_unevaluated_whatever_the_volume(self):
        result = assess_phenomena([self.pair(dict(size_break={}))], self.quiet, dict(level='HIGH'), True, self.timeline)
        self.assertEqual(result['market_manipulation']['status'], NOT_EVALUATED)
        self.assertTrue(result['market_manipulation']['data_needed'])
        self.assertEqual(result['size_or_frequency_anomaly']['status'], OBSERVED)

    def test_absent_liquidity_is_not_a_no(self):
        result = assess_phenomena([self.pair()], self.quiet, dict(level='LOW'), True, self.timeline)
        self.assertEqual(result['liquidity_anomaly']['status'], NOT_EVALUATED)

    def test_information_advantage_needs_structure_and_behaviour_and_says_what_it_is_not(self):
        high = assess_phenomena([self.pair(dict(size_break={}))], self.quiet, dict(level='HIGH'), True, self.timeline)['possible_information_advantage']
        self.assertEqual(high['status'], OBSERVED)
        self.assertIn('leak', high['not_established'])
        self.assertEqual(assess_phenomena([self.pair(dict(size_break={}))], self.quiet, dict(level='LOW'), True, self.timeline)['possible_information_advantage']['status'], 'NOT_OBSERVED')

    def test_public_reaction_is_kept_apart_and_unknown_when_uncovered(self):
        self.assertEqual(assess_phenomena([self.pair()], self.quiet, dict(level='LOW'), True, self.timeline)['reaction_to_public_information']['status'], NOT_EVALUATED)
        drift = assess_phenomena([self.pair(position=dict(drift_before_entry=.2))], self.quiet, dict(level='LOW'), True, self.timeline)
        self.assertEqual(drift['reaction_to_public_information']['status'], OBSERVED)


class InformationProfile(unittest.TestCase):
    def test_profile_describes_access_and_changes_no_level(self):
        award = assess_market('Who will win the Oscar for best picture?').as_dict()
        self.assertEqual((award['private_decision_before_publication'], award['level']), ('yes', HIGH))
        self.assertEqual(assess_market('Something nobody classified').as_dict()['people_who_could_know'], 'unknown')

    def test_balance_of_power_is_a_public_vote(self):
        self.assertEqual(assess_market('2026 Balance of Power: R Senate, R House').as_dict()['decision_structure'], 'broad_public')


class StatusPage(unittest.TestCase):
    NOW = T0 + 1000

    def tree(self, heartbeat=None, seal=False, finished=(), compared=False, shadow=None, journal=()):
        root = Path(tempfile.mkdtemp(prefix='status_'))
        self.addCleanup(shutil.rmtree, root, True)
        for folder in ('metrics', 'evidence/signal_engine_v1', 'reports', 'data', status_page.REPLAY + '/derived'):
            (root / folder).mkdir(parents=True)
        if heartbeat:
            (root / 'metrics/heartbeat.json').write_text(json.dumps(heartbeat))
        if shadow:
            (root / 'evidence/signal_engine_v1/status.json').write_text(json.dumps(shadow))
        if journal:
            (root / 'evidence/signal_engine_v1/journal.jsonl').write_text('\n'.join(json.dumps(j) for j in journal) + '\n')
        for name in finished:
            (root / status_page.REPLAY / f'derived/R1_{name}.json.gz').write_bytes(b'')
        if seal:
            (root / status_page.REPLAY / 'derived/pre_label_seal.json').write_text('{}')
        if compared:
            (root / status_page.REPLAY / 'derived/R3_labels.json.gz').write_bytes(b'')
        return root

    def page(self, root, running=False):
        state = status_page.collect(root, self.NOW, running)
        return state, status_page.html(state)

    def test_nothing_known_is_said_in_words(self):
        state, text = self.page(self.tree())
        for word in ('COLLECTION_UNKNOWN', 'REGISTRY_UNKNOWN', 'SHADOW_NOT_RUN', 'SIMULATION_PAUSED', 'NO_VERIFIED_RESULT', 'NO_VERIFIED_CASE', 'NOT_SEALED', 'NO_REVIEW'):
            self.assertIn(word, text)

    def test_a_running_replay_with_partial_files_is_not_a_result(self):
        state, text = self.page(self.tree(finished=('S_A',)), running=True)
        self.assertEqual((state['simulation']['state'], state['simulation']['result']), ('SIMULATION_RUNNING', 'NO_VERIFIED_RESULT'))
        self.assertIn('ce n’est pas une absence de détection', text)
        self.assertIn('terminés : S_A', text)

    def test_replay_states_in_their_order(self):
        finished = status_page.SCENARIOS
        self.assertEqual(self.page(self.tree(finished=finished))[0]['simulation']['state'], 'SIMULATION_FINISHED_NOT_SEALED')
        self.assertEqual(self.page(self.tree(finished=finished, seal=True))[0]['simulation']['state'], 'SIMULATION_SEALED')
        state = self.page(self.tree(finished=finished, seal=True, compared=True))[0]['simulation']
        self.assertEqual((state['state'], state['result']), ('SIMULATION_COMPARED', 'CONDITIONAL_REPLAY_COMPARED'))

    def test_collection_modes_and_a_silent_collector(self):
        self.assertEqual(self.page(self.tree(heartbeat=dict(at=self.NOW - 5, resource_mode='reduced')))[0]['collection']['state'], 'COLLECTION_REDUCED')
        self.assertEqual(self.page(self.tree(heartbeat=dict(at=self.NOW - 5, resource_mode='paused')))[0]['collection']['state'], 'COLLECTION_PAUSED')
        self.assertEqual(self.page(self.tree(heartbeat=dict(at=self.NOW - 500, resource_mode='normal')))[0]['collection']['state'], 'COLLECTION_STALE')

    def test_shadow_refusal_and_error_are_not_active(self):
        base = dict(at=self.NOW - 5, engine='e')
        self.assertEqual(self.page(self.tree(shadow=dict(base, last_run=dict(refused='full'))))[0]['shadow']['state'], 'SHADOW_REFUSED')
        self.assertEqual(self.page(self.tree(shadow=dict(base, error='boom')))[0]['shadow']['state'], 'SHADOW_ERROR')
        self.assertEqual(self.page(self.tree(shadow=dict(base, last_run={})))[0]['shadow']['state'], 'SHADOW_ACTIVE')

    def test_only_a_pass_counts_as_verified_and_no_address_appears(self):
        journal = [dict(kind='case', content=dict(verification='INCOMPLETE', wallets=['0x' + 'a' * 40])), dict(kind='case', content=dict(verification='FAIL'))]
        state, text = self.page(self.tree(journal=journal))
        self.assertEqual(state['case_files']['state'], 'NO_VERIFIED_CASE')
        self.assertIn('FAIL : 1', text)
        self.assertNotRegex(text, r'0x[0-9a-f]{40}')
        state, _ = self.page(self.tree(journal=[dict(kind='case', content=dict(verification='PASS'))]))
        self.assertEqual(state['case_files']['state'], 'VERIFIED_CASES_PRESENT')
