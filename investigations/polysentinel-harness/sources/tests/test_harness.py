"""Harness parts, one by one. Sockets, processes and files are real; data is synthetic except the on-chain fills, so these prove mechanics, not detection power."""
import ast
import hashlib
import json
import os
import random
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('SIGNAL_ENGINE_STATE', tempfile.mkdtemp(prefix='engine_state_'))

from harness import agent, memory, promotion, recover, tiering, verify  # noqa: E402
from harness.paths import IsolationError, PRODUCTION, assert_isolated  # noqa: E402
from harness.pipeline import Context, case_priority  # noqa: E402
from harness.runner import load_config  # noqa: E402
from harness.sources import Receipts, get_json, receipt_problem  # noqa: E402
from harness.store import Harness  # noqa: E402
from signal_engine.fund_flow.links import changenow_tier  # noqa: E402
from signal_engine.prospective_detection import load_config as engine_config  # noqa: E402

T0 = 1_800_000_000
TX = '0x' + 'a' * 64


class Base(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix='harness_')
        self.h = Harness(self.dir)
        self.config = load_config(self.dir)

    def tearDown(self):
        self.h.close()
        shutil.rmtree(self.dir, ignore_errors=True)


class Isolation(unittest.TestCase):
    def test_production_paths_and_their_parents_are_refused(self):
        for path in PRODUCTION:
            with self.assertRaises(IsolationError):
                assert_isolated(path)
            with self.assertRaises(IsolationError):
                assert_isolated(path / 'sub')
            with self.assertRaises(IsolationError):
                assert_isolated(path.parent if path.parent != Path.home() else Path.home())

    def test_a_sibling_folder_is_allowed(self):
        self.assertEqual(assert_isolated(Path.home() / 'Projects/PolySentinel-harness').name, 'PolySentinel-harness')

    def test_engine_state_left_at_its_default_is_refused(self):
        """Without the override the engine would write its ledgers into production's folder."""
        code = "import sqlite3;from harness.sources import CollectorSource;CollectorSource(dict(database='/nonexistent'))"
        env = {k: v for k, v in os.environ.items() if k != 'SIGNAL_ENGINE_STATE'}
        done = subprocess.run([sys.executable, '-c', code], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn('IsolationError', done.stderr)


class QueueMechanics(Base):
    def test_same_key_makes_one_task(self):
        first, created = recover.enqueue(self.h, 'k', 'x')
        second, again = recover.enqueue(self.h, 'k', 'x')
        self.assertEqual((first, created, again), (second, True, False))

    def test_dependency_waits_and_priority_orders(self):
        a, _ = recover.enqueue(self.h, 'a', 'x', priority=1)
        recover.enqueue(self.h, 'b', 'x', priority=9, needs=[a])
        recover.enqueue(self.h, 'c', 'x', priority=5)
        self.assertEqual(recover.claim(self.h, 'o')['dedupe_key'], 'c')
        self.assertEqual(recover.claim(self.h, 'o')['dedupe_key'], 'a')
        self.assertIsNone(recover.claim(self.h, 'o'))

    def test_case_priority_prefers_risk_and_a_near_deadline(self):
        base = dict(risk=dict(level='HIGH'), category='ANOMALOUS', market_open=True, end_at=T0 + 86400)
        self.assertGreater(case_priority(base, T0), case_priority(dict(base, risk=dict(level='LOW')), T0))
        self.assertGreater(case_priority(base, T0), case_priority(dict(base, end_at=T0 + 60 * 86400), T0))
        self.assertGreater(case_priority(base, T0), case_priority(dict(base, market_open=False), T0))

    def test_a_worker_that_lost_its_lease_cannot_write(self):
        recover.enqueue(self.h, 'k', 'x')
        old = recover.claim(self.h, 'old')
        recover.reclaim_dead(self.h, 'new')
        new = recover.claim(self.h, 'new')
        self.assertEqual(new['attempts'], 2)
        with self.assertRaises(recover.LeaseLost):
            recover.commit(self.h, old['id'], 'old', old['attempts'], dict(stale=True), lambda cx: cx.execute("INSERT INTO kv VALUES('stale','1')"))
        with self.assertRaises(recover.LeaseLost):
            recover.finish(self.h, old['id'], 'old', old['attempts'])
        self.assertIsNone(self.h.signal.get('stale'))

    def test_output_and_checkpoint_roll_back_together(self):
        recover.enqueue(self.h, 'k', 'x')
        task = recover.claim(self.h, 'o')

        def boom(cx):
            cx.execute("INSERT INTO kv VALUES('half','1')")
            raise RuntimeError('crash in the middle')
        with self.assertRaises(RuntimeError):
            recover.commit(self.h, task['id'], 'o', task['attempts'], dict(step=1), boom)
        self.assertIsNone(self.h.signal.get('half'))
        self.assertIsNone(self.h.cx.execute('SELECT checkpoint FROM tasks').fetchone()[0])

    def test_retries_end_in_quarantine_and_dependents_follow(self):
        a, _ = recover.enqueue(self.h, 'a', 'x', max_attempts=2)
        b, _ = recover.enqueue(self.h, 'b', 'x', needs=[a])
        c, _ = recover.enqueue(self.h, 'c', 'x', needs=[b])
        outcomes = []
        for _ in range(2):
            task = recover.claim(self.h, 'o', now=9e12)
            outcomes.append(recover.fail(self.h, task, recover.Transient('boom'), self.config))
        self.assertEqual(outcomes, ['retry', 'quarantined'])
        self.assertEqual({r[0] for r in self.h.cx.execute('SELECT status FROM tasks')}, {'quarantined'})
        self.assertIsNone(recover.claim(self.h, 'o', now=9e12))

    def test_permanent_error_is_not_retried(self):
        recover.enqueue(self.h, 'a', 'x')
        self.assertEqual(recover.fail(self.h, recover.claim(self.h, 'o'), recover.Permanent('never'), self.config), 'quarantined')

    def test_pause_spends_no_attempt(self):
        recover.enqueue(self.h, 'a', 'x', max_attempts=1)
        task = recover.claim(self.h, 'o')
        self.assertEqual(recover.fail(self.h, task, recover.Pause('budget', delay=0), self.config), 'paused')
        self.assertEqual(self.h.cx.execute('SELECT attempts, status FROM tasks').fetchone()[:2], (0, 'pending'))

    def test_a_crash_loop_ends_in_quarantine(self):
        recover.enqueue(self.h, 'poison', 'x', max_attempts=3)
        for n in range(3):
            self.assertIsNotNone(recover.claim(self.h, f'dead{n}'))
            outcome = recover.reclaim_dead(self.h, 'next')
        self.assertEqual(outcome, dict(requeued=0, quarantined=1))

    def test_same_failure_across_tasks_opens_a_circuit_for_that_kind_only(self):
        config = dict(self.config, recovery=dict(self.config['recovery'], circuit_failures=3))
        for n in range(3):
            recover.enqueue(self.h, f'a{n}', 'flaky')
        recover.enqueue(self.h, 'other', 'fine', priority=-1)
        for n in range(3):
            # Addresses differ, the failure is the same: the signature must see through them.
            recover.fail(self.h, recover.claim(self.h, 'o'), recover.Transient(f'HTTP 503 for 0x{n:040x} after {n} tries'), config)
        self.assertEqual(recover.open_circuits(self.h), ['flaky'])
        self.assertEqual(recover.claim(self.h, 'o', now=9e9 if False else None)['kind'], 'fine')

    def test_backoff_grows_stays_capped_and_repeats_exactly(self):
        delays = [recover.backoff(1, a, 2, 30) for a in range(1, 10)]
        self.assertLess(delays[0], delays[3])
        self.assertLessEqual(max(delays), 30)
        self.assertEqual(delays, [recover.backoff(1, a, 2, 30) for a in range(1, 10)])

    def test_retry_call_uses_retry_after_and_gives_up(self):
        seen, sleeps = [], []

        def flaky():
            seen.append(1)
            if len(seen) < 3:
                raise recover.Transient('down', retry_after=7)
            return 'ok'
        self.assertEqual(recover.retry_call(flaky, sleep=sleeps.append), 'ok')
        self.assertEqual(sleeps, [7, 7])

        def always():
            raise recover.Transient('down')
        with self.assertRaises(recover.Transient):
            recover.retry_call(always, attempts=2, sleep=lambda _: None)

    def test_concurrent_claims_never_share_a_task(self):
        for n in range(40):
            recover.enqueue(self.h, f't{n}', 'x')
        claimed, errors = [], []

        def worker(name):
            h = Harness(self.dir)
            try:
                while (task := recover.claim(h, name)) is not None:
                    claimed.append(task['id'])
            except Exception as exc:
                errors.append(exc)
            finally:
                h.close()
        threads = [threading.Thread(target=worker, args=(f'w{n}',)) for n in range(6)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        self.assertEqual(errors, [])
        self.assertEqual(sorted(claimed), sorted(set(claimed)))
        self.assertEqual(len(claimed), 40)

    def test_instance_lock_excludes_a_second_holder_and_dies_with_the_process(self):
        path = Path(self.dir) / 'lock'
        with recover.InstanceLock(path) as first, recover.InstanceLock(path) as second:
            self.assertTrue(first.acquired)
            self.assertFalse(second.acquired)
        code = f"import os;from harness.recover import InstanceLock;l=InstanceLock({str(path)!r});l.__enter__();print(l.acquired,flush=True);os.kill(os.getpid(),9)"
        subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True)
        with recover.InstanceLock(path) as after:
            self.assertTrue(after.acquired)


class Memory(Base):
    def test_contradiction_contests_both_and_chooses_neither(self):
        self.assertEqual(memory.remember(self.h, 'result', 'wallet', 'first_seen', 'Tuesday', status='verified'), 'verified')
        self.assertEqual(memory.remember(self.h, 'result', 'wallet', 'first_seen', 'Friday', status='verified'), 'contested')
        found = memory.recall(self.h, 'first_seen wallet')
        self.assertEqual({(f['value'], f['status']) for f in found}, {('Tuesday', 'contested'), ('Friday', 'contested')})
        self.assertEqual(len(self.h.status()['contested']), 2)

    def test_contested_comes_first_in_the_briefing(self):
        memory.remember(self.h, 'result', 'funding', 'route', 'via A', status='verified')
        memory.remember(self.h, 'result', 'other', 'funding', 'plain fact', status='verified')
        memory.remember(self.h, 'result', 'funding', 'route', 'via B')
        lines = memory.context_pack(self.h, 'funding route')['text'].split('\n')[3:]
        self.assertIn('contested', lines[0])
        self.assertIn('contested', lines[1])

    def test_a_file_that_changed_makes_its_memory_stale(self):
        """A memory is a recollection: when the file says otherwise, the file wins."""
        source = Path(self.dir) / 'results.md'
        source.write_text('rate 12 percent')
        memory.remember(self.h, 'result', 'study', 'rate', '12 percent', status='verified', source_path=source)
        self.assertEqual(memory.recall(self.h, 'study rate')[0]['status'], 'verified')
        source.write_text('rate 9 percent')
        self.assertEqual(memory.recall(self.h, 'study rate')[0]['status'], 'stale')
        self.assertEqual(self.h.cx.execute('SELECT status FROM facts').fetchone()[0], 'stale')

    def test_a_vanished_source_makes_its_memory_stale(self):
        source = Path(self.dir) / 'gone.md'
        source.write_text('x')
        memory.remember(self.h, 'result', 'study', 'gone', 'x', status='verified', source_path=source)
        source.unlink()
        self.assertEqual(memory.recall(self.h, 'study gone')[0]['status'], 'stale')

    def test_same_fact_twice_counts_it_once(self):
        memory.remember(self.h, 'method_ok', 'm', 'k', 'v')
        memory.remember(self.h, 'method_ok', 'm', 'k', 'v')
        self.assertEqual(self.h.cx.execute('SELECT COUNT(*), MAX(seen) FROM facts').fetchone()[:2], (1, 2))

    def test_rejected_idea_cannot_return_reworded_only_with_new_evidence(self):
        spec = dict(feature='new_wallet', threshold=3600)
        first, _, duplicate = memory.propose(self.h, 'population', 'New wallets win', spec, 'llm')
        self.assertFalse(duplicate)
        self.h.cx.execute("UPDATE hypotheses SET status='rejected', reason='no effect' WHERE id=?", (first,))
        again, status, duplicate = memory.propose(self.h, 'population', 'Fresh addresses outperform, surely', spec, 'llm')
        self.assertEqual((again, status, duplicate), (first, 'rejected', True))
        _, status, duplicate = memory.propose(self.h, 'population', 'New wallets win', dict(spec, new_evidence='sha-of-new-data'), 'llm')
        self.assertEqual((status, duplicate), ('proposed', False))

    def test_memory_survives_reopening(self):
        memory.remember(self.h, 'decision', 'quota', 'limit', '6 GB', status='verified')
        self.h.close()
        self.h = Harness(self.dir)
        self.assertEqual(memory.recall(self.h, 'quota')[0]['value'], '6 GB')

    def test_briefing_respects_its_budget_and_says_what_it_left_out(self):
        for n in range(400):
            memory.remember(self.h, 'result', 'noise', f'k{n}', f'value number {n} ' + 'x' * 200, status='verified')
        pack = memory.context_pack(self.h, 'noise value', budget_chars=2000)
        self.assertLessEqual(len(pack['text']), 2000)
        self.assertGreater(pack['omitted'], 0)

    def test_briefing_retrieves_rather_than_dumps(self):
        memory.remember(self.h, 'result', 'relay', 'bridge', 'wanted fact about bridges', status='verified')
        for n in range(50):
            memory.remember(self.h, 'result', 'noise', f'k{n}', 'unrelated', status='verified')
        text = memory.context_pack(self.h, 'bridge')['text']
        self.assertIn('wanted fact', text)
        self.assertNotIn('unrelated', text)


class Trust(Base):
    """An agent's word changes nothing: the database itself refuses."""

    def hypothesis(self, proposer='llm'):
        return memory.propose(self.h, 'case', 's', dict(n=1), proposer)[0]

    def verification(self, hypothesis, verdict='PASS', verifier='harness.verify:abc'):
        self.h.cx.execute('INSERT INTO verifications(hypothesis, verifier, verdict, report_sha, input_sha, code_sha, at) VALUES(?,?,?,?,?,?,0)', (hypothesis, verifier, verdict, 'r', 'i', 'c'))

    def validate(self, hypothesis):
        self.h.cx.execute("UPDATE hypotheses SET status='validated' WHERE id=?", (hypothesis,))

    def test_no_validation_without_verification(self):
        hypothesis = self.hypothesis()
        with self.assertRaises(sqlite3.IntegrityError):
            self.validate(hypothesis)

    def test_not_born_validated(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.h.cx.execute("INSERT INTO hypotheses(fingerprint, kind, statement, spec, proposer, status) VALUES('f','case','s','{}','llm','validated')")

    def test_the_proposer_cannot_verify_itself(self):
        hypothesis = self.hypothesis('llm')
        self.verification(hypothesis, verifier='llm')
        with self.assertRaises(sqlite3.IntegrityError):
            self.validate(hypothesis)

    def test_the_latest_verification_decides(self):
        hypothesis = self.hypothesis()
        self.verification(hypothesis, 'PASS')
        self.verification(hypothesis, 'FAIL')
        with self.assertRaises(sqlite3.IntegrityError):
            self.validate(hypothesis)
        self.verification(hypothesis, 'PASS')
        self.validate(hypothesis)

    def test_verifications_are_append_only(self):
        hypothesis = self.hypothesis()
        self.verification(hypothesis, 'FAIL')
        with self.assertRaises(sqlite3.IntegrityError):
            self.h.cx.execute("UPDATE verifications SET verdict='PASS'")
        with self.assertRaises(sqlite3.IntegrityError):
            self.h.cx.execute('DELETE FROM verifications')

    def test_the_verifier_imports_nothing_from_who_it_checks(self):
        tree = ast.parse((ROOT / 'harness/verify.py').read_text())
        names = {n.module or '' for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)} | {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        self.assertFalse({m for m in names if m.startswith('harness') or m.startswith('polysentinel')}, names)
        self.assertEqual({m for m in names if m.startswith('signal_engine')}, {'signal_engine.experimental.splits'})

    def test_altered_artifact_is_refused(self):
        digest = self.h.put_artifact(dict(a=1))
        self.h.cx.execute('UPDATE artifacts SET body=? WHERE sha=?', (__import__('zlib').compress(b'{"a":2}'), digest))
        with self.assertRaises(ValueError):
            self.h.get_artifact(digest)


def row(n, wallet, event='ev', nominal=1000.0, price=.5, buy=True, ts=T0, token='tok', condition='c1', tx=None, observed=None):
    return dict(wallet=wallet, ts=ts + n, observed_at=(ts + n + 60) if observed is None else observed, event_key=event, market_id='m', condition_id=condition, token_id=token, is_buy=buy, size=nominal / price, price=price, nominal=nominal, tx=tx or '0x' + hashlib.sha256(f'{wallet}{n}{event}'.encode()).hexdigest(), outcome='Yes')


def wallet_address(n):
    return '0x' + hashlib.sha256(f'w{n}'.encode()).hexdigest()[:40]


LIMITS = json.loads((ROOT / 'harness/default_config.json').read_text())['verify']


def case_bundle(**over):
    rng = random.Random(1)
    wallets = [wallet_address(n) for n in range(3)]
    rows = [row(n, w, nominal=60000.0, price=.3) for n, w in enumerate(wallets)]
    controls = [dict(wallet=wallet_address(100 + n), event_key=f'e{n % 40}', spend=(s := rng.uniform(100, 2000)), shares=s / .3, total=s * rng.uniform(1, 4)) for n in range(1000)]
    receipts = {r['tx']: dict(transaction_hash=r['tx'], status=1, fills=[dict(transaction_hash=r['tx'], token_id=r['token_id'], maker=r['wallet'], taker='0x' + 'b' * 40, side='BUY', nominal_raw=str(int(r['nominal'] * 1e6)), removed=False)]) for r in rows}
    bundle = dict(kind='case', as_of=T0 + 1000, event_key='ev', statement='Unusual purchases. Compatible with several explanations.', claim=dict(level='CORROBORATED_BEHAVIOR', wallets=wallets, metrics={w: 60000.0 for w in wallets}, relations=[]),
                  event_rows=rows, wallet_history={w: [] for w in wallets}, wallet_totals={w: 60000.0 for w in wallets}, controls=controls, controls_truncated=False, milestone=None, receipts=receipts, screened=100, dossier_overall='INCOMPLETE', gaps=[], history_truncated=[], config=LIMITS)
    bundle.update(over)
    return bundle


class CaseVerification(unittest.TestCase):
    def verdict(self, bundle):
        report = verify.run(bundle)
        return report['overall'], report['checks']

    def test_a_clean_case_passes_every_check(self):
        overall, checks = self.verdict(case_bundle())
        self.assertEqual(overall, 'PASS', checks)

    def test_inflated_claim_fails_whatever_the_proposer_says(self):
        bundle = case_bundle()
        bundle['claim']['metrics'][bundle['claim']['wallets'][0]] = 500000.0
        overall, checks = self.verdict(bundle)
        self.assertEqual((overall, checks['claim_matches']['status']), ('FAIL', 'FAIL'))

    def test_a_future_row_fails_the_look_ahead_check(self):
        bundle = case_bundle()
        bundle['event_rows'].append(row(9000, bundle['claim']['wallets'][0]))
        overall, checks = self.verdict(bundle)
        self.assertEqual((overall, checks['no_future']['status']), ('FAIL', 'FAIL'))

    def test_a_milestone_published_after_the_decision_is_not_used(self):
        late = dict(public_at=T0 - 100, public_observed_at=T0 + 99999)
        overall, checks = self.verdict(case_bundle(milestone=late))
        self.assertEqual(overall, 'PASS', checks)

    def test_rows_with_impossible_values_fail(self):
        for damage in (dict(tx='nope'), dict(wallet='nope'), dict(observed_at=T0 - 99), dict(nominal=1.0), dict(price=1.5, nominal=1.5 * 200000.0)):
            bundle = case_bundle()
            bundle['event_rows'][0] = dict(bundle['event_rows'][0], **damage)
            self.assertEqual(self.verdict(bundle)[0], 'FAIL', damage)

    def test_missing_receipt_stays_open_and_a_wrong_one_fails(self):
        bundle = case_bundle()
        bundle['receipts'].pop(next(iter(bundle['receipts'])))
        self.assertEqual(self.verdict(bundle)[1]['chain']['status'], 'INCOMPLETE')
        self.assertEqual(self.verdict(bundle)[0], 'INCOMPLETE')
        bundle = case_bundle()
        for receipt in bundle['receipts'].values():
            receipt['fills'][0]['nominal_raw'] = '1000000'
        self.assertEqual(self.verdict(bundle)[1]['chain']['status'], 'FAIL')
        bundle = case_bundle()
        next(iter(bundle['receipts'].values()))['status'] = 0
        self.assertEqual(self.verdict(bundle)[1]['chain']['status'], 'FAIL')

    def test_real_onchain_fills_match_and_a_changed_amount_does_not(self):
        """Public receipts from the existing fixture, decoded by the collector's code."""
        fixtures = json.loads((ROOT / 'tests/fixtures/chain_receipts_sample.json').read_text())
        tested = 0
        for item in fixtures:
            tx = item['transaction_hash'].lower()
            for trade in item.get('trades', []):
                if str(trade.get('side', '')).upper() != 'BUY':
                    continue
                # The amount comes from the trade feed, independently of the fills, and takers are included: counting the counterparty's log would double them.
                one = dict(tx=tx, wallet=trade['wallet'].lower(), token_id=str(trade['token_id']), nominal=float(trade['size']) * float(trade['price']), is_buy=True)
                bundle = dict(event_rows=[one], receipts={tx: dict(transaction_hash=tx, status=1, fills=item['fills'])})
                self.assertEqual(verify.chain(bundle, {one['wallet']})['status'], 'PASS', tx)
                bundle['event_rows'] = [dict(one, nominal=one['nominal'] * 2)]
                self.assertEqual(verify.chain(bundle, {one['wallet']})['status'], 'FAIL', tx)
                tested += 1
        self.assertEqual(tested, 28)

    def test_not_rare_enough_fails_too_few_controls_stays_open(self):
        rng = random.Random(2)
        crowded = [dict(wallet=wallet_address(100 + n), event_key=f'e{n % 40}', spend=70000.0, shares=70000 / .3, total=70000.0) for n in range(1000)]
        overall, checks = self.verdict(case_bundle(controls=crowded))
        self.assertEqual((overall, checks['controls']['status'], checks['placebo_events']['status']), ('FAIL', 'FAIL', 'FAIL'))
        overall, checks = self.verdict(case_bundle(controls=case_bundle()['controls'][:50]))
        self.assertEqual((checks['controls']['status'], overall), ('INCOMPLETE', 'INCOMPLETE'))
        self.assertEqual(self.verdict(case_bundle(controls_truncated=True))[1]['controls']['status'], 'INCOMPLETE')
        self.assertEqual(self.verdict(case_bundle(screened=100000))[1]['controls']['status'], 'INCOMPLETE')

    def test_screening_more_pairs_raises_the_bar(self):
        bundle = case_bundle()
        hits = [dict(wallet=wallet_address(2000 + n), event_key='e1', spend=80000.0, shares=80000 / .3, total=80000.0) for n in range(4)]
        self.assertEqual(self.verdict(dict(bundle, controls=bundle['controls'] + hits, screened=10))[1]['controls']['status'], 'PASS')
        self.assertEqual(self.verdict(dict(bundle, controls=bundle['controls'] + hits, screened=200))[1]['controls']['status'], 'FAIL')

    def alternative(self, bundle, name):
        overall, checks = self.verdict(bundle)
        self.assertEqual(overall, 'FAIL', checks)
        self.assertIn(name, checks['alternatives']['reasons'])

    def test_public_news_before_entry_explains_it(self):
        self.alternative(case_bundle(milestone=dict(public_at=T0 - 100, public_observed_at=T0 - 90, kind='public_information')), 'public_before_entry')

    def test_each_wallet_is_judged_against_its_own_entry(self):
        """A bought before the news, the others after: only the others are explained by it."""
        bundle = case_bundle(milestone=dict(public_at=T0 + 1, public_observed_at=T0 + 1, kind='public_information'))
        per_wallet = self.verdict(bundle)[1]['alternatives']['per_wallet']
        self.assertEqual([per_wallet[w]['public_before_entry'] for w in bundle['claim']['wallets']], ['NOT_SUPPORTED', 'SUPPORTED', 'SUPPORTED'])

    def test_a_resolution_after_entry_says_nothing_about_when_the_news_came_out(self):
        bundle = case_bundle(milestone=dict(public_at=T0 + 500, public_observed_at=T0 + 600, kind='official_resolution'))
        overall, checks = self.verdict(bundle)
        self.assertEqual(overall, 'PASS', checks)
        self.assertIn('public_before_entry', checks['alternatives']['not_testable'])
        self.assertTrue(all(a['public_before_entry'] == 'NOT_TESTABLE' for a in checks['alternatives']['per_wallet'].values()))

    def test_a_dated_public_source_after_entry_excludes_earlier_news_from_that_source_only(self):
        bundle = case_bundle(milestone=dict(public_at=T0 + 500, public_observed_at=T0 + 600, kind='public_information'))
        self.assertEqual(self.verdict(bundle)[1]['alternatives']['not_testable'], [])

    def test_a_collection_gap_at_the_entry_leaves_it_open(self):
        overall, checks = self.verdict(case_bundle(gaps=[dict(start=T0 - 600, end=T0 - 300, reason='sleep')]))
        self.assertEqual((checks['coverage']['status'], overall), ('INCOMPLETE', 'INCOMPLETE'))

    def test_a_gap_elsewhere_changes_nothing_but_is_counted(self):
        overall, checks = self.verdict(case_bundle(gaps=[dict(start=T0 - 90000, end=T0 - 80000, reason='sleep')]))
        self.assertEqual(overall, 'PASS', checks)
        self.assertIn('1 elsewhere', checks['coverage']['detail'])

    def test_a_cut_history_makes_the_habit_untestable_not_absent(self):
        bundle = case_bundle()
        bundle['history_truncated'] = list(bundle['claim']['wallets'])
        self.assertIn('habitual_size', self.verdict(bundle)[1]['alternatives']['not_testable'])

    def test_a_contradiction_in_the_engines_file_blocks_the_case(self):
        overall, checks = self.verdict(case_bundle(dossier_overall='FAIL'))
        self.assertEqual((overall, checks['dossier']['status']), ('FAIL', 'FAIL'))
        self.assertEqual(self.verdict(case_bundle(dossier_overall=None))[1]['dossier']['status'], 'INCOMPLETE')

    def test_absence_of_a_public_source_is_not_evidence(self):
        self.assertIn('public_before_entry', self.verdict(case_bundle())[1]['alternatives']['not_testable'])

    def test_buying_both_sides_explains_it(self):
        bundle = case_bundle()
        bundle['event_rows'] += [row(50 + n, w, nominal=60000.0, price=.7, token='tok2') for n, w in enumerate(bundle['claim']['wallets'])]
        bundle['claim']['metrics'] = {w: 120000.0 for w in bundle['claim']['wallets']}
        self.alternative(bundle, 'two_sided_or_sold_back')

    def test_selling_back_explains_it(self):
        bundle = case_bundle()
        bundle['event_rows'] += [row(60 + n, w, nominal=40000.0, price=.3, buy=False) for n, w in enumerate(bundle['claim']['wallets'])]
        self.alternative(bundle, 'two_sided_or_sold_back')

    def test_a_basket_across_outcomes_explains_it(self):
        bundle = case_bundle()
        bundle['event_rows'] += [row(70 + n * 10 + k, w, nominal=100.0, price=.3, condition=f'c{k + 2}', token=f't{k}') for n, w in enumerate(bundle['claim']['wallets']) for k in range(2)]
        bundle['claim']['metrics'] = {w: 60200.0 for w in bundle['claim']['wallets']}
        self.alternative(bundle, 'basket_or_hedge')

    def test_a_habit_of_this_size_explains_it(self):
        bundle = case_bundle()
        bundle['wallet_history'] = {w: [row(-5000 - k, w, event=f'old{k}', nominal=50000.0) for k in range(10)] for w in bundle['claim']['wallets']}
        self.alternative(bundle, 'habitual_size')

    def test_following_a_visible_move_explains_it(self):
        bundle = case_bundle()
        for n in range(6):
            bundle['event_rows'].append(row(-600 + n, wallet_address(500 + n), nominal=100.0, price=.1))
        self.alternative(bundle, 'reaction_to_visible_move')

    def test_one_explained_wallet_leaves_the_others_standing(self):
        bundle = case_bundle()
        for n in (3, 4):  # five wallets, each with several fills, so losing one row or wallet leaves a finding standing
            wallet = wallet_address(n)
            bundle['claim']['wallets'].append(wallet)
            bundle['claim']['metrics'][wallet] = 60000.0
            bundle['wallet_totals'][wallet] = 60000.0
            bundle['wallet_history'][wallet] = []
            added = row(n, wallet, nominal=60000.0, price=.3)
            bundle['event_rows'].append(added)
            bundle['receipts'][added['tx']] = dict(transaction_hash=added['tx'], status=1, fills=[dict(transaction_hash=added['tx'], token_id=added['token_id'], maker=wallet, side='BUY', nominal_raw=str(int(60000 * 1e6)))])
        explained = bundle['claim']['wallets'][0]
        bundle['wallet_history'][explained] = [row(-5000 - k, explained, event=f'old{k}', nominal=50000.0) for k in range(10)]
        overall, checks = self.verdict(bundle)
        self.assertEqual(overall, 'PASS', checks)
        self.assertEqual(len(checks['alternatives']['surviving']), 4)

    def test_a_finding_from_one_fill_or_one_wallet_is_not_robust(self):
        wallets = [wallet_address(n) for n in range(3)]
        rows = [row(n, w, nominal=60000.0 if n == 0 else 3000.0, price=.3) for n, w in enumerate(wallets)]
        rng = random.Random(4)
        controls = [dict(wallet=wallet_address(100 + n), event_key=f'e{n % 40}', spend=(s := rng.uniform(1000, 5000)), shares=s / .3, total=s) for n in range(1000)]
        receipts = {r['tx']: dict(transaction_hash=r['tx'], status=1, fills=[dict(transaction_hash=r['tx'], token_id=r['token_id'], maker=r['wallet'], side='BUY', nominal_raw=str(int(r['nominal'] * 1e6)))]) for r in rows}
        bundle = case_bundle(event_rows=rows, controls=controls, receipts=receipts)
        bundle['claim'] = dict(bundle['claim'], wallets=wallets, metrics={r['wallet']: r['nominal'] for r in rows})
        self.assertEqual(self.verdict(bundle)[1]['robustness']['status'], 'FAIL')

    def test_the_report_is_identical_across_processes_and_hash_seeds(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bundle.json'
            path.write_text(json.dumps(case_bundle()))
            outs = {subprocess.run([sys.executable, '-m', 'harness.verify', str(path)], cwd=ROOT, env=dict(os.environ, PYTHONHASHSEED=s), capture_output=True, text=True, check=True).stdout for s in '123'}
        self.assertEqual(len(outs), 1)


class ProofLevels(unittest.TestCase):
    """Similarity, a probable route and common control stay apart. A swap service links nothing without its own record."""

    def status(self, *relations):
        return verify.relations(dict(relations=list(relations)))['status']

    def test_behaviour_cannot_claim_funding(self):
        self.assertEqual(self.status(dict(kind='similar_timing', claimed='BEHAVIORAL_SIMILARITY')), 'PASS')
        self.assertEqual(self.status(dict(kind='similar_timing', claimed='COMMON_FUNDING_ROUTE')), 'FAIL')
        self.assertEqual(self.status(dict(kind='similar_amount', claimed='COMMON_FUNDING_ROUTE')), 'FAIL')

    def test_funding_needs_a_transaction_and_a_log(self):
        self.assertEqual(self.status(dict(kind='shared_funder', claimed='COMMON_FUNDING_ROUTE')), 'FAIL')
        self.assertEqual(self.status(dict(kind='shared_funder', claimed='COMMON_FUNDING_ROUTE', transaction_hash=TX)), 'FAIL')
        self.assertEqual(self.status(dict(kind='shared_funder', claimed='COMMON_FUNDING_ROUTE', transaction_hash=TX, log_index=3)), 'PASS')

    def test_shared_infrastructure_stays_what_it_is(self):
        self.assertEqual(self.status(dict(kind='shared_infrastructure', claimed='SHARED_INFRASTRUCTURE')), 'PASS')
        self.assertEqual(self.status(dict(kind='shared_infrastructure', claimed='COMMON_FUNDING_ROUTE', transaction_hash=TX, log_index=1)), 'FAIL')

    def test_common_control_cannot_be_claimed_from_public_data(self):
        self.assertEqual(self.status(dict(kind='direct_transfer_between_wallets', claimed='COMMON_CONTROL', transaction_hash=TX, log_index=1)), 'FAIL')

    def test_changenow_candidate_is_not_a_match(self):
        """Time and amount alike, the classic trap: the deposit and the withdrawal stay unlinked."""
        for tier in (changenow_tier(candidate=True), changenow_tier(labelled=True), changenow_tier()):
            self.assertEqual(self.status(dict(claimed='SWAP_MATCH', tier=tier['tier'], record_verified=False)), 'FAIL')

    def test_changenow_with_a_verified_record_is_a_match_and_nothing_more(self):
        tier = changenow_tier(record=dict(id='x'), record_verified=True)
        self.assertEqual(self.status(dict(claimed='SWAP_MATCH', tier=tier['tier'], record_verified=True)), 'PASS')
        self.assertEqual(self.status(dict(claimed='COMMON_CONTROL', tier=tier['tier'], record_verified=True)), 'FAIL')

    def test_a_statement_cannot_name_an_insider_or_a_proof(self):
        for text in ('This wallet is an insider.', 'Ces wallets sont des initiés', 'Same owner behind both.', 'This proves it.', 'Le même propriétaire'):
            self.assertEqual(verify.language(text)['status'], 'FAIL', text)
        self.assertEqual(verify.language('Unusual purchases, compatible with several explanations.')['status'], 'PASS')


def population(seed, effect=0.0, events=80, wallets=40):
    """Everyone on an event shares its outcome: wallets are not independent, which is what the test has to survive."""
    rng = random.Random(seed)
    rows = []
    for e in range(events):
        outcome = rng.gauss(0, .5)
        ts = T0 + e * 6 * 3600
        for w in range(wallets):
            x = rng.random() < .3
            rows.append(dict(wallet=f'0x{seed:08x}{e:08x}{w:024x}', event_key=f'e{e}', ts=ts + w, observed_at=ts + w + 60, x=x, y=outcome + rng.gauss(0, 1) + (effect if x else 0)))
    return rows


def population_bundle(rows, n_tests=1):
    times = sorted(r['ts'] for r in rows)
    return dict(kind='population', as_of=max(r['observed_at'] for r in rows), rows=rows, statement='Feature predicts returns. Compatible with several explanations.', split_ts=times[len(times) // 2], embargo_s=3600, n_tests=n_tests, config=LIMITS)


class SeductiveHypothesis(unittest.TestCase):
    def mine(self, seed, candidates=200):
        """A proposer that tries many features on the development side and reports the best: p looks wonderful, and means nothing."""
        from signal_engine.experimental.splits import temporal_group_split
        rows = population(seed, events=60, wallets=30)
        bundle = population_bundle(rows, candidates)
        dev = temporal_group_split(rows, bundle['split_ts'], bundle['embargo_s'], salt='harness')['dev']
        rng = random.Random(seed + 1000)
        features = [{r['wallet']: rng.random() < .3 for r in rows} for _ in range(candidates)]
        best = max(features, key=lambda f: sum(verify.event_effects([dict(r, x=f[r['wallet']]) for r in dev])))
        p = verify.sign_flip_p(verify.event_effects([dict(r, x=best[r['wallet']]) for r in dev]), 999, random.Random(1))
        return dict(bundle, rows=[dict(r, x=best[r['wallet']]) for r in rows]), p

    def test_the_best_of_200_noise_features_looks_good_and_is_rejected(self):
        seductive = accepted = 0
        for seed in range(6):
            bundle, dev_p = self.mine(seed)
            seductive += dev_p <= .05
            accepted += verify.run(bundle)['overall'] == 'PASS'
        self.assertGreaterEqual(seductive, 3, 'the mined feature should look good on development data')
        self.assertEqual(accepted, 0)

    def test_without_counting_past_tests_a_noise_feature_is_rarely_accepted(self):
        accepted = sum(verify.run(population_bundle(population(seed)))['overall'] == 'PASS' for seed in range(20))
        self.assertLessEqual(accepted, 3)

    def test_a_real_effect_passes_so_the_verifier_is_not_just_saying_no(self):
        accepted = sum(verify.run(population_bundle(population(seed, effect=.8), n_tests=5))['overall'] == 'PASS' for seed in range(5))
        self.assertEqual(accepted, 5)

    def test_a_sample_cut_at_its_cap_cannot_judge(self):
        self.assertEqual(verify.run(dict(population_bundle(population(1, effect=.8)), rows_truncated=True))['overall'], 'INCOMPLETE')

    def test_too_little_data_is_open_not_rejected(self):
        report = verify.run(population_bundle(population(1, events=10, wallets=20)))
        self.assertEqual(report['overall'], 'INCOMPLETE')

    def test_wallets_on_both_sides_of_the_split_are_impossible(self):
        rows = population(3)
        bundle = population_bundle(rows)
        bundle['rows'] = [dict(r, observed_at=r['ts'] - 1) if i == 0 else r for i, r in enumerate(rows)]
        self.assertEqual(verify.run(bundle)['overall'], 'FAIL')


class RuleGate(Base):
    @staticmethod
    def by_threshold(params, data):
        return {u: data['scores'][u] >= params['threshold'] for u in data['labels']}

    @staticmethod
    def dataset(prefix, positives, negatives, pos_score, neg_score):
        labels = {f'{prefix}p{n}': True for n in range(positives)} | {f'{prefix}n{n}': False for n in range(negatives)}
        rng = random.Random(prefix)
        return dict(labels=labels, scores={u: (pos_score if labels[u] else neg_score)(rng) for u in labels})

    def active(self):
        row = self.h.cx.execute("SELECT params FROM rules WHERE name='r' AND status='active'").fetchone()
        return json.loads(row[0]) if row else None

    def test_a_rule_that_loses_recall_is_blocked(self):
        data = lambda p: self.dataset(p, 40, 40, lambda r: r.uniform(5, 10), lambda r: r.uniform(0, 4))
        report = promotion.gate(self.h, 'r', dict(threshold=8), self.by_threshold, data('d'), data('h'), baseline=dict(threshold=4.5))
        self.assertFalse(report['passed'])
        self.assertIn('recall falls', ' '.join(report['reasons']))
        self.assertIsNone(self.active())

    def test_a_rule_that_adds_false_positives_is_blocked(self):
        data = lambda p: self.dataset(p, 40, 40, lambda r: r.uniform(5, 10), lambda r: r.uniform(0, 4))
        report = promotion.gate(self.h, 'r', dict(threshold=1), self.by_threshold, data('d'), data('h'), baseline=dict(threshold=4.5))
        self.assertFalse(report['passed'])
        self.assertIn('false positive rate rises', ' '.join(report['reasons']))

    def test_a_rule_tuned_to_its_development_data_fails_on_the_holdout(self):
        """Better on the data it was tuned on, worse on data it never saw: the regression the gate exists for."""
        development = self.dataset('d', 40, 40, lambda r: r.uniform(6, 7), lambda r: r.uniform(0, 5.5))
        holdout = self.dataset('h', 40, 40, lambda r: r.uniform(5, 6.5), lambda r: r.uniform(0, 4))
        report = promotion.gate(self.h, 'r', dict(threshold=5.75), self.by_threshold, development, holdout, baseline=dict(threshold=4.5))
        self.assertGreater(report['development']['candidate']['recall'] - report['development']['candidate']['false_positive_rate'], report['development']['current']['recall'] - report['development']['current']['false_positive_rate'])
        self.assertFalse(report['passed'])

    def test_an_equal_rule_is_not_a_gain(self):
        data = lambda p: self.dataset(p, 40, 40, lambda r: r.uniform(5, 10), lambda r: r.uniform(0, 4))
        report = promotion.gate(self.h, 'r', dict(threshold=4.6), self.by_threshold, data('d'), data('h'), baseline=dict(threshold=4.5))
        self.assertFalse(report['passed'])
        self.assertIn('gain not shown', ' '.join(report['reasons']))

    def test_a_real_gain_is_activated_and_the_next_rule_must_beat_it(self):
        data = lambda p: self.dataset(p, 40, 40, lambda r: r.uniform(5, 10), lambda r: r.uniform(0, 4))
        report = promotion.gate(self.h, 'r', dict(threshold=4.5), self.by_threshold, data('d'), data('h'), baseline=dict(threshold=8))
        self.assertTrue(report['passed'], report['reasons'])
        self.assertEqual(self.active(), dict(threshold=4.5))
        again = promotion.gate(self.h, 'r', dict(threshold=8), self.by_threshold, data('d'), data('h'))
        self.assertFalse(again['passed'])
        self.assertEqual(self.active(), dict(threshold=4.5))

    def test_a_used_holdout_is_counted_and_then_refused(self):
        data = lambda p: self.dataset(p, 10, 10, lambda r: 9, lambda r: 1)
        for _ in range(3):
            promotion.gate(self.h, 'r', dict(threshold=5), self.by_threshold, data('d'), data('h'), baseline=dict(threshold=5))
        with self.assertRaises(promotion.HoldoutRefused):
            promotion.gate(self.h, 'r', dict(threshold=5), self.by_threshold, data('d'), data('h'), baseline=dict(threshold=5))

    def test_holdout_sharing_units_with_development_is_refused(self):
        data = self.dataset('d', 10, 10, lambda r: 9, lambda r: 1)
        with self.assertRaises(promotion.HoldoutRefused):
            promotion.gate(self.h, 'r', dict(threshold=5), self.by_threshold, data, data)

    def test_the_database_refuses_activation_without_the_gate(self):
        rule = self.h.cx.execute("INSERT INTO rules(name, params, status) VALUES('r','{}','candidate')").lastrowid
        with self.assertRaises(sqlite3.IntegrityError):
            self.h.cx.execute("UPDATE rules SET status='active' WHERE id=?", (rule,))

    def test_the_real_engine_through_the_gate(self):
        """Replays synthetic rows through run_cycle with each configuration. A parameter that hides the planted case is refused."""
        rng = random.Random(1)
        base = engine_config()
        def make(prefix):
            markets = [dict(condition_id=f'{prefix}c{i}', title='Will the committee approve the budget?', event_key=f'{prefix}e{i}', market_id=f'{prefix}m{i}', end_at=T0 + 40 * 86400, cataloged=True) for i in range(30)]
            markets.append(dict(condition_id=f'{prefix}cx', title='Will the company announce the acquisition?', event_key=f'{prefix}ex', market_id=f'{prefix}mx', end_at=T0 + 40 * 86400, cataloged=True))
            rows, n = [], 0
            def add(wallet, event, condition, ts, nominal, price):
                nonlocal n
                n += 1
                rows.append(dict(key=f'{prefix}k{n}', wallet=wallet, ts=ts, observed_at=ts + 60, event_key=event, market_id='m', condition_id=condition, token_id='t' + condition, is_buy=True, size=nominal / price, price=price, tx=f'0x{n:064x}', outcome='Yes'))
            for w in range(300):
                i = w % 30
                for _ in range(rng.randrange(2, 5)):
                    add(f'{prefix}w{w}', f'{prefix}e{i}', f'{prefix}c{i}', T0 - rng.randrange(0, 3 * 86400), rng.uniform(100, 1500), rng.choice((.15, .3, .6, .9)))
            rows.sort(key=lambda r: r['observed_at'])
            planted = []
            for k in range(3):
                add(f'{prefix}new{k}', f'{prefix}ex', f'{prefix}cx', T0 + 50 + k, 60000, .3)
                planted.append(f'{prefix}new{k}|{prefix}ex')
            batches = [rows[:-3], rows[-3:]]
            labels = {u: True for u in planted} | {f'{prefix}w{w}|{prefix}e{w % 30}': False for w in range(300)}
            return dict(markets=markets, batches=batches, labels=labels)
        evaluate = lambda params, data: promotion.replay_engine(params, data, base)
        development, holdout = make('d'), make('h')
        self.assertTrue(all(evaluate({}, holdout).get(u) for u, positive in holdout['labels'].items() if positive), 'the engine should flag the planted case')
        report = promotion.gate(self.h, 'engine', dict(minimum_spend=1e9), evaluate, development, holdout)
        self.assertFalse(report['passed'])
        self.assertEqual(report['holdout']['candidate']['recall'], 0)


class FakeClaude:
    def __init__(self, folder, answer, tokens=500, code=0):
        self.calls = Path(folder) / 'calls.txt'
        self.path = Path(folder) / 'fake_claude.py'
        payload = dict(type='result', is_error=code != 0, result='', structured_output=answer, usage=dict(input_tokens=tokens, output_tokens=10), total_cost_usd=.001)
        self.path.write_text(f'#!{sys.executable}\nimport json,os,sys\nopen({str(self.calls)!r},"a").write(json.dumps(dict(argv=sys.argv[1:],depth=os.environ.get("POLYSENTINEL_HARNESS_LLM")))+"\\n")\nprint({json.dumps(json.dumps(payload))})\nsys.exit({code})\n')
        self.path.chmod(0o755)

    def count(self):
        return len(self.calls.read_text().splitlines()) if self.calls.exists() else 0

    def last(self):
        return json.loads(self.calls.read_text().splitlines()[-1])


class Model(Base):
    GOOD = dict(hypotheses=[dict(statement='Large entries gain.', feature='large_entry', threshold=5000)])

    def context(self, fake, **llm):
        self.config['llm'] = dict(self.config['llm'], enabled=True, executable=str(fake.path), **llm)
        recover.enqueue(self.h, f'p{fake.count()}{random.random()}', 'propose_hypotheses')
        return Context(self.h, recover.claim(self.h, 'o'), self.config)

    def test_a_call_has_no_tools_no_session_and_a_cost_ceiling(self):
        fake = FakeClaude(self.dir, self.GOOD)
        answer = agent.ask_for_hypotheses(self.context(fake), 'notes')
        self.assertEqual(answer['hypotheses'][0]['feature'], 'large_entry')
        argv = fake.last()['argv']
        self.assertEqual(argv[argv.index('--tools') + 1], '')
        for flag in ('--strict-mcp-config', '--no-session-persistence', '--max-budget-usd', '--json-schema'):
            self.assertIn(flag, argv)
        self.assertEqual(argv[argv.index('--setting-sources') + 1], '')
        self.assertEqual(fake.last()['depth'], '1')
        self.assertEqual(self.h.used('llm_calls'), 1)
        self.assertEqual(self.h.used('llm_tokens'), 510)

    def test_disabled_by_default_and_the_cli_is_not_touched(self):
        fake = FakeClaude(self.dir, self.GOOD)
        recover.enqueue(self.h, 'p', 'propose_hypotheses')
        context = Context(self.h, recover.claim(self.h, 'o'), self.config)
        self.assertFalse(self.config['llm']['enabled'])
        with self.assertRaises(recover.Permanent):
            agent.ask_for_hypotheses(context, 'notes')
        self.assertEqual(fake.count(), 0)

    def test_a_model_call_cannot_start_another(self):
        fake = FakeClaude(self.dir, self.GOOD)
        os.environ[agent.DEPTH] = '1'
        try:
            with self.assertRaises(recover.Permanent):
                agent.ask_for_hypotheses(self.context(fake), 'notes')
        finally:
            del os.environ[agent.DEPTH]
        self.assertEqual(fake.count(), 0)

    def test_excess_tokens_stop_the_next_call_before_it_is_made(self):
        fake = FakeClaude(self.dir, self.GOOD, tokens=38000)
        self.config['budgets'] = dict(self.config['budgets'], llm_calls_per_day=100)
        agent.ask_for_hypotheses(self.context(fake), 'notes')
        self.assertEqual(fake.count(), 1)
        with self.assertRaises(recover.Pause) as caught:
            agent.ask_for_hypotheses(self.context(fake), 'x' * 9000)
        self.assertIn('Token budget', str(caught.exception))
        self.assertEqual(fake.count(), 1)

    def test_the_call_count_and_cost_budgets_also_stop_it(self):
        fake = FakeClaude(self.dir, self.GOOD)
        self.config['budgets'] = dict(self.config['budgets'], llm_calls_per_day=1)
        agent.ask_for_hypotheses(self.context(fake), 'notes')
        with self.assertRaises(recover.Pause):
            agent.ask_for_hypotheses(self.context(fake), 'notes')
        self.assertEqual(fake.count(), 1)
        self.config['budgets'] = dict(self.config['budgets'], llm_calls_per_day=9, llm_usd_per_day=.05)
        with self.assertRaises(recover.Pause):
            agent.ask_for_hypotheses(self.context(fake), 'notes')
        self.assertEqual(fake.count(), 1)

    def test_answers_outside_the_schema_are_refused(self):
        for bad in (dict(hypotheses=[dict(statement='x', feature='os.system', threshold=1)]), dict(hypotheses=[dict(statement='x', feature='new_wallet', threshold=-1)]), dict(hypotheses='drop table'), dict(nothing=1), dict(hypotheses=[dict(statement='x', feature='new_wallet', threshold=1)] * 4)):
            fake = FakeClaude(self.dir, bad)
            self.config['budgets'] = dict(self.config['budgets'], llm_calls_per_day=100)
            with self.assertRaises(recover.Permanent, msg=bad):
                agent.ask_for_hypotheses(self.context(fake), 'notes')

    def test_a_failed_call_is_retried_and_its_cost_is_still_counted(self):
        fake = FakeClaude(self.dir, self.GOOD, code=1)
        with self.assertRaises(recover.Transient):
            agent.ask_for_hypotheses(self.context(fake), 'notes')
        self.assertEqual(self.h.used('llm_tokens'), 510)


class Http(unittest.TestCase):
    """A real server on a real socket."""

    def setUp(self):
        self.script = []
        self.seen = []
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                outer.seen.append(self.path)
                status, headers, body = outer.script.pop(0) if outer.script else (200, {}, b'{}')
                self.send_response(status)
                for k, v in headers.items():
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_):
                pass
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def get(self):
        return get_json(f'http://127.0.0.1:{self.port}/r', allowed_hosts={'127.0.0.1'}, validate=receipt_problem(TX), timeout=5)

    def test_server_errors_and_rate_limits_are_transient(self):
        self.script = [(503, {}, b'')]
        with self.assertRaises(recover.Transient):
            self.get()
        self.script = [(429, {'Retry-After': '9'}, b'')]
        with self.assertRaises(recover.Transient) as caught:
            self.get()
        self.assertEqual(caught.exception.retry_after, 9)

    def test_a_closed_port_is_transient(self):
        self.server.shutdown()
        self.server.server_close()
        with self.assertRaises(recover.Transient):
            self.get()
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), BaseHTTPRequestHandler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def test_refusal_is_permanent_and_a_foreign_host_never_gets_a_request(self):
        self.script = [(403, {}, b'')]
        with self.assertRaises(recover.Permanent):
            self.get()
        before = len(self.seen)
        with self.assertRaises(recover.Permanent):
            get_json(f'http://127.0.0.1:{self.port}/r', allowed_hosts={'example.com'}, validate=receipt_problem(TX))
        self.assertEqual(len(self.seen), before)

    def test_invalid_bodies_are_refused_never_returned(self):
        for body in (b'not json', b'[1,2]', json.dumps(dict(transaction_hash='0x' + 'b' * 64, fills=[])).encode(), json.dumps(dict(transaction_hash=TX)).encode(), json.dumps(dict(transaction_hash=TX, fills=[dict(nominal_raw='abc')])).encode()):
            self.script = [(200, {}, body)]
            with self.assertRaises(recover.InvalidResponse, msg=body):
                self.get()

    def test_retry_recovers_after_an_outage(self):
        good = json.dumps(dict(transaction_hash=TX, fills=[dict(nominal_raw='5')])).encode()
        self.script = [(503, {}, b''), (502, {}, b''), (200, {}, good)]
        self.assertEqual(recover.retry_call(self.get, sleep=lambda _: None)['fills'][0]['nominal_raw'], '5')
        self.assertEqual(len(self.seen), 3)

    def test_an_unknown_transaction_is_absent_not_an_error(self):
        self.script = [(404, {}, b'')]
        source = Receipts(dict(type='http', url=f'http://127.0.0.1:{self.port}/{{tx}}', hosts=['127.0.0.1']))
        self.assertIsNone(source.get(TX))


class Resources(Base):
    def test_memory_is_measured_for_the_whole_group_inside_the_sandbox_too(self):
        from harness.runner import footprint_mb, group_memory_mb
        code = "import subprocess,sys,time;b=bytearray(60*1024*1024);[b.__setitem__(i,1) for i in range(0,len(b),4096)];c=subprocess.Popen([sys.executable,'-c','b=bytearray(60*1024*1024);[b.__setitem__(i,1) for i in range(0,len(b),4096)];import time;time.sleep(20)']);print('up',flush=True);time.sleep(20)"
        process = subprocess.Popen([sys.executable, '-c', code], stdout=subprocess.PIPE, text=True, start_new_session=True)
        try:
            process.stdout.readline()
            deadline = __import__('time').monotonic() + 20
            while __import__('time').monotonic() < deadline and group_memory_mb(process.pid) < 100:
                __import__('time').sleep(.2)
            self.assertGreater(group_memory_mb(process.pid), 100, 'parent and child together hold over 100 MB')
            self.assertIsNotNone(footprint_mb(os.getpid()))
        finally:
            os.killpg(process.pid, 9)
            process.wait()

    def limits(self, **resources):
        return dict(self.config, source=dict(heartbeat=None), resources=dict(self.config['resources'], max_load=1000, **resources))

    def test_each_limit_stops_the_passage(self):
        self.assertIsNone(recover.resource_block(self.dir, self.limits(disk_floor_bytes=0)))
        self.assertIn('disk', recover.resource_block(self.dir, self.limits(disk_floor_bytes=10 ** 16)))
        self.assertIn('storage', recover.resource_block(self.dir, self.limits(disk_floor_bytes=0, root_quota_bytes=1)))
        self.assertIn('load', recover.resource_block(self.dir, dict(self.limits(disk_floor_bytes=0), resources=dict(self.config['resources'], disk_floor_bytes=0, max_load=-1))))

    def test_the_collector_comes_first(self):
        import time
        beat = Path(self.dir) / 'heartbeat.json'
        config = dict(self.limits(disk_floor_bytes=0), source=dict(heartbeat=str(beat)))
        beat.write_text(json.dumps(dict(at=time.time(), resource_mode='normal')))
        self.assertIsNone(recover.resource_block(self.dir, config))
        beat.write_text(json.dumps(dict(at=time.time(), resource_mode='reduced')))
        self.assertIn('reduced', recover.resource_block(self.dir, config))
        beat.write_text(json.dumps(dict(at=time.time() - 9999, resource_mode='normal')))
        self.assertIn('old', recover.resource_block(self.dir, config))
        beat.unlink()
        self.assertIn('unreadable', recover.resource_block(self.dir, config))

    def test_daily_budget_counts_and_refuses(self):
        with self.h.tx():
            self.h.spend('api_requests', 8, 10)
        from harness.store import BudgetExceeded
        with self.assertRaises(BudgetExceeded):
            with self.h.tx():
                self.h.spend('api_requests', 3, 10)
        self.assertEqual(self.h.used('api_requests'), 8)


class Tiering(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp(prefix='tier_'))
        self.source, self.volume = self.dir / 'data', self.dir / 'Volumes/SSD'
        self.source.mkdir()
        self.volume.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def file(self, name, size=1000, age_days=30):
        path = self.source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(os.urandom(size))
        import time
        os.utime(path, (time.time() - age_days * 86400,) * 2)
        return path

    def mark(self):
        (self.volume / tiering.MARKER).touch()

    def copy(self, **kwargs):
        return tiering.copy(self.source, self.volume, kwargs.pop('max_bytes', 10 ** 9), 7, margin=0, **kwargs)

    def test_a_drive_not_connected_is_a_clear_state(self):
        with self.assertRaises(tiering.VolumeUnavailable):
            tiering.copy(self.source, self.dir / 'Volumes/ABSENT', 10 ** 6, 7)
        done = subprocess.run([sys.executable, '-m', 'harness.tiering', 'copy', '--source', str(self.source), '--volume', str(self.dir / 'Volumes/ABSENT')], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(done.returncode, 3)
        self.assertEqual(json.loads(done.stdout)['state'], 'volume_unavailable')

    def test_an_unmarked_drive_is_never_written(self):
        self.file('a.gz')
        with self.assertRaises(tiering.VolumeUnavailable):
            self.copy()
        self.assertEqual(list(self.volume.iterdir()), [])

    def test_copies_verify_and_keep_the_source(self):
        self.mark()
        path = self.file('old/a.gz')
        self.assertEqual(self.copy()['copied'], ['old/a.gz'])
        self.assertEqual(tiering.file_sha(path), tiering.file_sha(self.volume / 'old/a.gz'))
        self.assertTrue(path.exists())
        self.assertEqual(tiering.check(self.volume), dict(files=1, bad=[]))

    def test_recent_and_live_files_stay(self):
        self.mark()
        self.file('fresh.gz', age_days=0)
        self.file('polysentinel.sqlite3')
        self.file('polysentinel.sqlite3-wal')
        self.assertEqual(self.copy()['copied'], [])

    def test_progress_is_gradual_and_repeating_copies_nothing_twice(self):
        self.mark()
        for n in range(5):
            self.file(f'f{n}.gz', 1000)
        self.assertEqual(len(self.copy(max_bytes=2500)['copied']), 2)
        self.assertEqual(len(self.copy(max_bytes=2500)['copied']), 2)
        self.assertEqual(len(self.copy()['copied']), 1)
        self.assertEqual(self.copy()['copied'], [])
        self.assertEqual(tiering.check(self.volume)['files'], 5)

    def test_interrupted_copy_leaves_no_entry_and_finishes_next_time(self):
        self.mark()
        self.file('a.gz')
        def die(partial):
            raise KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            self.copy(fault=die)
        self.assertEqual(tiering.check(self.volume)['files'], 0)
        self.assertFalse((self.volume / 'a.gz').exists())
        self.assertEqual(self.copy()['copied'], ['a.gz'])

    def test_a_corrupt_copy_never_counts_and_the_source_stays(self):
        self.mark()
        path = self.file('a.gz')
        def corrupt(partial):
            partial.write_bytes(b'garbage')
        out = self.copy(fault=corrupt, remove_source=True)
        self.assertEqual((out['copied'], out['failed'], out['removed']), ([], ['a.gz'], []))
        self.assertTrue(path.exists())

    def test_too_little_room_is_refused_before_writing(self):
        self.mark()
        self.file('a.gz')
        with self.assertRaises(tiering.VolumeUnavailable):
            tiering.copy(self.source, self.volume, 10 ** 9, 7, margin=10 ** 16)

    def test_a_file_too_large_for_the_batch_does_not_block_the_others(self):
        self.mark()
        self.file('a_big.gz', 5000)
        self.file('b_small.gz', 100)
        out = self.copy(max_bytes=1000)
        self.assertEqual((out['copied'], out['too_large']), (['b_small.gz'], ['a_big.gz']))

    def test_deleting_from_production_is_refused_outright(self):
        self.mark()
        with self.assertRaises(IsolationError):
            tiering.copy(Path.home() / 'Projects/PolySentinel/evidence', self.volume, 10 ** 9, 7, remove_source=True, margin=0)

    def test_rot_on_the_drive_is_reported(self):
        self.mark()
        self.file('a.gz')
        self.copy()
        (self.volume / 'a.gz').write_bytes(b'rot')
        self.assertEqual(tiering.check(self.volume)['bad'], ['a.gz'])

    def test_removing_the_source_only_when_asked(self):
        self.mark()
        path = self.file('a.gz')
        out = self.copy(remove_source=True)
        self.assertEqual(out['removed'], ['a.gz'])
        self.assertFalse(path.exists())
        self.assertTrue((self.volume / 'a.gz').exists())


class StopBullshiting(Base):
    def test_long_output_shrinks_and_the_original_comes_back(self):
        text = '\n'.join(f'2026-11-01 INFO step {n} finished in {n * 3} ms with status ok' for n in range(3000))
        out = memory.compress_output(text, self.dir)
        if out['tool'] != 'stop-bullshiting':
            self.skipTest('Stop-Bullshiting is not installed')
        self.assertLess(out['visible_chars'], len(text) / 5)
        self.assertTrue((Path(self.dir) / 'sbs').exists(), 'receipts must stay under this root')
        receipt = __import__('re').search(r'sbs show (\w+)', out['view']).group(1)
        executable = next(c for c in memory.SBS_CANDIDATES if c and Path(c).exists())
        back = subprocess.run([executable, 'show', receipt], capture_output=True, text=True, env=dict(os.environ, SBS_HOME=str(Path(self.dir) / 'sbs')))
        self.assertEqual(back.stdout.rstrip('\n'), text.rstrip('\n'))

    def test_without_it_the_original_goes_to_a_file(self):
        original = memory.SBS_CANDIDATES
        memory.SBS_CANDIDATES = ('', '/nonexistent/sbs')
        try:
            text = 'y' * 9000
            out = memory.compress_output(text, self.dir)
        finally:
            memory.SBS_CANDIDATES = original
        self.assertEqual(out['tool'], 'fallback')
        self.assertEqual(Path(out['original']).read_text(), text)
        self.assertLess(out['visible_chars'], 3500)


if __name__ == '__main__':
    unittest.main()
