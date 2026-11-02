"""The whole chain on synthetic collector data, with real processes killed and real sockets closed.

The reference is an uninterrupted run. Every interrupted run must reach the same digest: same hypotheses, same statuses, same alerts, byte for byte.
"""
import hashlib
import json
import os
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('SIGNAL_ENGINE_STATE', tempfile.mkdtemp(prefix='engine_state_'))

from harness import demo, memory, planner, recover  # noqa: E402
from harness.runner import load_config, passage  # noqa: E402
from harness.store import Harness  # noqa: E402

SMALL = dict(wallets=700, events=40, batch_rows=200)


def harness_run(root, seconds=120, **env):
    done = subprocess.run([sys.executable, '-m', 'harness', 'run', '--root', str(root), '--seconds', str(seconds)], cwd=ROOT, env=dict(os.environ, **env), capture_output=True, text=True, timeout=seconds + 120)
    if done.returncode != 0:
        raise AssertionError(done.stderr[-2000:])
    return json.loads(done.stdout.strip().splitlines()[-1])


def settle(root, limit=60, **env):
    """Repeats passages, as launchd would, until nothing is left."""
    results = []
    for _ in range(limit):
        results.append(harness_run(root, **env))
        if results[-1]['state'] == 'drained':
            return results
        time.sleep(.3)
    raise AssertionError(f'Never drained: {results[-3:]}')


def configure(root, **sections):
    path = Path(root) / 'config.json'
    config = json.loads(path.read_text())
    for name, values in sections.items():
        config[name] = dict(config.get(name, {}), **values)
    path.write_text(json.dumps(config))


def wait_for_tasks(database, done, timeout=120):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        time.sleep(.2)
        try:
            cx = sqlite3.connect(database, timeout=5)
            try:
                if cx.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0] >= done:
                    return
            finally:
                cx.close()
        except sqlite3.OperationalError:
            pass  # not created yet
    raise AssertionError(f'{done} tasks not done after {timeout} s')


def verdicts(root):
    h = Harness(root)
    try:
        return {json.loads(r['spec'])['event_key']: r['status'] for r in h.cx.execute('SELECT spec, status FROM hypotheses')}
    finally:
        h.close()


class EndToEnd(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.top = Path(tempfile.mkdtemp(prefix='e2e_'))
        cls.reference = cls.top / 'reference'
        demo.build(cls.reference, **SMALL)
        collector = cls.reference / 'demo_collector/data/polysentinel.sqlite3'
        cls.collector_sha = hashlib.sha256(collector.read_bytes()).hexdigest()
        started = time.monotonic()
        cls.results = settle(cls.reference)
        cls.seconds = time.monotonic() - started
        h = Harness(cls.reference)
        cls.digest = h.digest()
        cls.status = h.status()
        h.close()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.top, ignore_errors=True)

    def fresh(self, name):
        root = self.top / name
        demo.build(root, **SMALL)
        return root

    def digest_of(self, root):
        h = Harness(root)
        try:
            return h.digest()
        finally:
            h.close()

    # The chain decides each planted case as expected, for the expected reason.

    def test_each_planted_case_gets_its_expected_verdict(self):
        found = verdicts(self.reference)
        for name, expected in demo.EXPECTED.items():
            self.assertEqual(found['case_' + name], expected, name)

    def test_rejections_name_their_real_cause(self):
        h = Harness(self.reference)
        reason = {json.loads(r['spec'])['event_key']: r['reason'] for r in h.cx.execute('SELECT spec, reason FROM hypotheses')}
        h.close()
        self.assertIn('public_before_entry', reason['case_public_decoy'])
        self.assertIn('two_sided_or_sold_back', reason['case_two_sided_decoy'])
        self.assertIn('contradicted by their receipts', reason['case_tampered_receipts'])
        self.assertIn('no receipt yet', reason['case_no_receipts'])

    def test_an_alert_carries_transactions_a_reader_can_check_and_no_accusation(self):
        h = Harness(self.reference)
        rows = h.cx.execute('SELECT * FROM alerts').fetchall()
        h.close()
        planted = [json.loads(r['body']) for r in rows if r['event_key'] == 'case_true_case']
        self.assertEqual(len(planted), 1)
        alert = planted[0]
        self.assertEqual(len(alert['transactions']), 3)
        for t in alert['transactions']:
            self.assertRegex(t['tx'], r'^0x[0-9a-f]{64}$')
            self.assertIn(t['tx'], t['url'])
        self.assertIn('Identity of any wallet owner.', alert['not_established'])
        self.assertIn('Common ownership of these wallets.', alert['not_established'])
        self.assertNotIn('insider', json.dumps(alert).lower().replace('never', ''))
        self.assertIn('public_before_entry', alert['not_testable'])
        self.assertTrue(list((self.reference / 'alerts').glob('*.json')))

    def test_the_collector_database_is_not_changed_by_a_byte(self):
        collector = self.reference / 'demo_collector/data/polysentinel.sqlite3'
        self.assertEqual(hashlib.sha256(collector.read_bytes()).hexdigest(), self.collector_sha)

    def test_the_source_connection_cannot_write(self):
        from harness.sources import CollectorSource
        source = CollectorSource(load_config(self.reference)['source'])
        with self.assertRaises(sqlite3.OperationalError):
            source.cx.execute('DELETE FROM trade_index')
        source.close()

    def test_a_deterministic_run_spends_no_token(self):
        self.assertFalse({k for k in self.status['usage'] if k.startswith('llm')})

    # Scenario: repeated execution without duplication

    def test_running_again_changes_nothing(self):
        h = Harness(self.reference)
        tasks = h.cx.execute('SELECT COUNT(*) FROM tasks').fetchone()[0]
        trades = h.cx.execute('SELECT COUNT(*) FROM trades').fetchone()[0]
        self.assertEqual(planner.plan(h, load_config(self.reference)), [])
        h.close()
        results = [harness_run(self.reference) for _ in range(3)]
        self.assertTrue(all(r['done'] == 0 and r['state'] == 'drained' for r in results), results)
        h = Harness(self.reference)
        self.assertEqual(h.cx.execute('SELECT COUNT(*) FROM tasks').fetchone()[0], tasks)
        self.assertEqual(h.cx.execute('SELECT COUNT(*) FROM trades').fetchone()[0], trades)
        self.assertEqual(h.digest(), self.digest)
        h.close()

    def test_a_second_run_from_nothing_reaches_the_same_conclusions(self):
        root = self.fresh('replay')
        settle(root)
        self.assertEqual(self.digest_of(root), self.digest)

    # Scenarios: deliberate interruption, resume from the last checkpoint

    def interrupted(self, name, kind, moment):
        """Kills the worker once, at that point, then lets passages run as launchd would."""
        root = self.fresh(name)
        marker = root / 'kill.marker'
        marker.touch()
        settle(root, HARNESS_KILL_ONCE=f'{marker}:{kind}:{moment}')
        self.assertFalse(marker.exists(), 'the kill never fired')
        h = Harness(root)
        retried = h.cx.execute("SELECT COUNT(*) FROM tasks WHERE attempts>1").fetchone()[0]
        quarantined = h.cx.execute("SELECT COUNT(*) FROM tasks WHERE status='quarantined'").fetchone()[0]
        h.close()
        self.assertGreaterEqual(retried, 1, 'the killed task should have run again')
        self.assertEqual(quarantined, 0)
        self.assertEqual(self.digest_of(root), self.digest)

    def test_kill_inside_a_discovery_transaction(self):
        """Trades, evaluation and cursor roll back together, so no pair is lost."""
        self.interrupted('kill_discover_inside', 'discover', 'inside')

    def test_kill_after_a_discovery_checkpoint(self):
        self.interrupted('kill_discover_after', 'discover', 'after')

    def test_kill_before_the_verification_is_finished(self):
        self.interrupted('kill_verify', 'case_verify', 'after')

    def test_kill_inside_the_conclusion(self):
        """Status, memory and alert land together or not at all."""
        self.interrupted('kill_conclude', 'case_conclude', 'inside')

    def test_supervisor_killed_outright_in_the_middle(self):
        """No signal handler runs. The kernel frees the lock, and the next passage reclaims the task and keeps going."""
        root = self.fresh('kill_supervisor')
        process = subprocess.Popen([sys.executable, '-m', 'harness', 'run', '--root', str(root), '--seconds', '200'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        wait_for_tasks(root / 'harness.sqlite3', 3)
        process.send_signal(signal.SIGKILL)
        process.wait()
        results = settle(root)
        self.assertEqual(self.digest_of(root), self.digest)
        self.assertEqual(results[-1]['state'], 'drained')

    def test_sigterm_stops_cleanly_without_spending_an_attempt(self):
        root = self.fresh('sigterm')
        process = subprocess.Popen([sys.executable, '-m', 'harness', 'run', '--root', str(root), '--seconds', '200'], cwd=ROOT, stdout=subprocess.PIPE, text=True)
        wait_for_tasks(root / 'harness.sqlite3', 2)
        process.send_signal(signal.SIGTERM)
        out, _ = process.communicate(timeout=60)
        self.assertEqual(json.loads(out.strip().splitlines()[-1])['state'], 'stopped')
        settle(root)
        h = Harness(root)
        self.assertEqual(h.cx.execute("SELECT COUNT(*) FROM tasks WHERE status='quarantined'").fetchone()[0], 0)
        h.close()
        self.assertEqual(self.digest_of(root), self.digest)

    # Scenario: look-ahead

    def test_later_rows_do_not_move_an_earlier_decision(self):
        """Same data cut at a date: every decision made before the cut must be identical with or without what came after."""
        from harness.demo import case_start
        cut = case_start(3)
        root = self.fresh('truncated')
        cx = sqlite3.connect(root / 'demo_collector/data/polysentinel.sqlite3')
        cx.execute("DELETE FROM object_refs WHERE kind='trade' AND observed_at>?", (cut,))
        cx.execute('DELETE FROM trade_index WHERE observed_at>?', (cut,))
        cx.commit()
        cx.close()
        settle(root)

        def before(path):
            h = Harness(path)
            out = {}
            for r in h.cx.execute("SELECT h.fingerprint, h.status, t.params FROM hypotheses h JOIN tasks t ON t.dedupe_key='case:'||h.id||':case_dossier'"):
                if json.loads(r['params'])['as_of'] <= cut - 86400 * 2:  # the last batch before the cut is shorter, so its boundaries differ
                    out[r['fingerprint']] = r['status']
            h.close()
            return out
        early, full = before(root), before(self.reference)
        self.assertGreater(len(early), 0)
        self.assertEqual(early, full)

    # Scenario: concurrent execution

    def test_only_one_of_several_passages_runs_and_each_task_runs_once(self):
        root = self.fresh('concurrent')
        processes = [subprocess.Popen([sys.executable, '-m', 'harness', 'run', '--root', str(root), '--seconds', '200'], cwd=ROOT, stdout=subprocess.PIPE, text=True) for _ in range(4)]
        states = [json.loads(p.communicate(timeout=300)[0].strip().splitlines()[-1])['state'] for p in processes]
        self.assertEqual(states.count('already_running'), 3, states)
        settle(root)
        h = Harness(root)
        duplicated = h.cx.execute("SELECT COUNT(*) FROM tasks WHERE attempts<>1").fetchone()[0]
        h.close()
        self.assertEqual(duplicated, 0)
        self.assertEqual(self.digest_of(root), self.digest)


class HttpEndToEnd(unittest.TestCase):
    """Receipts through a real socket, with the server failing on purpose."""

    def setUp(self):
        self.top = Path(tempfile.mkdtemp(prefix='e2e_http_'))
        self.root = self.top / 'run'
        demo.build(self.root, **SMALL)
        self.receipts = json.loads((self.root / 'demo_receipts.json').read_text())
        self.requests = {}
        self.mode = ['ok']
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                tx = self.path.strip('/')
                outer.requests[tx] = outer.requests.get(tx, 0) + 1
                if outer.mode[0] == 'down':
                    self.send_response(503)
                    self.end_headers()
                elif outer.mode[0] == 'garbage':
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b'<html>maintenance</html>')
                elif tx in outer.receipts:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(json.dumps(outer.receipts[tx]).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

            def log_message(self, *_):
                pass
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        port = self.server.server_address[1]
        configure(self.root, chain=dict(type='http', url=f'http://127.0.0.1:{port}/{{tx}}', hosts=['127.0.0.1']), recovery=dict(outage_delay_s=6, read_attempts=2, circuit_cooldown_s=.2))

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        shutil.rmtree(self.top, ignore_errors=True)

    def test_killed_during_receipts_no_receipt_is_read_twice(self):
        """Fifteen planted receipts: each committed one survives the kill, so the resumed task only reads the rest."""
        marker = self.root / 'kill.marker'
        marker.touch()
        settle(self.root, HARNESS_KILL_ONCE=f'{marker}:case_receipts:after')
        self.assertFalse(marker.exists())
        counted = {tx: n for tx, n in self.requests.items() if tx in self.receipts}
        self.assertEqual(len(counted), len(self.receipts))
        self.assertEqual(max(counted.values()), 1, 'a committed receipt was read twice')
        self.assertEqual(verdicts(self.root)['case_true_case'], 'validated')

    def test_an_outage_waits_spends_no_attempt_and_recovers(self):
        self.mode[0] = 'down'
        for _ in range(8):
            result = harness_run(self.root)
            if result['paused'] or result['state'] in ('waiting',):
                break
        h = Harness(self.root)
        waiting = h.cx.execute("SELECT kind, attempts, status, last_error FROM tasks WHERE kind='case_receipts' AND last_error IS NOT NULL").fetchall()
        self.assertTrue(waiting, 'the outage should have reached the receipts')
        self.assertTrue(all(r['attempts'] == 0 and r['status'] == 'pending' for r in waiting), [dict(r) for r in waiting])
        self.assertIn('Source unavailable', waiting[0]['last_error'])
        self.assertFalse(h.cx.execute("SELECT 1 FROM hypotheses WHERE status='validated'").fetchone())
        h.close()
        self.mode[0] = 'ok'
        settle(self.root)
        found = verdicts(self.root)
        self.assertEqual(found['case_true_case'], 'validated')
        self.assertEqual(found['case_no_receipts'], 'needs_data')

    def test_a_source_answering_nonsense_ends_in_quarantine_and_nothing_is_validated(self):
        self.mode[0] = 'garbage'
        settle(self.root)
        h = Harness(self.root)
        stopped = h.cx.execute("SELECT kind, last_error FROM tasks WHERE status='quarantined'").fetchall()
        self.assertIn('case_receipts', {r['kind'] for r in stopped})
        self.assertIn('case_conclude', {r['kind'] for r in stopped}, 'dependents must not wait forever')
        self.assertTrue(any('Unparsable JSON' in (r['last_error'] or '') for r in stopped))
        self.assertFalse(h.cx.execute("SELECT 1 FROM hypotheses WHERE status='validated'").fetchone())
        self.assertFalse(h.cx.execute('SELECT 1 FROM alerts').fetchone())
        for row in h.cx.execute('SELECT sha FROM artifacts').fetchall():
            self.assertNotIn('maintenance', json.dumps(h.get_artifact(row['sha'])))
        h.close()


class Limits(unittest.TestCase):
    def setUp(self):
        self.top = Path(tempfile.mkdtemp(prefix='limits_'))
        self.root = self.top / 'run'
        demo.build(self.root, wallets=60, events=25, batch_rows=500)

    def tearDown(self):
        shutil.rmtree(self.top, ignore_errors=True)

    def files(self):
        return sorted(str(p) for p in self.root.rglob('*') if p.is_file() and not p.name.startswith('harness.'))

    def test_over_the_storage_budget_it_pauses_deletes_nothing_and_resumes(self):
        configure(self.root, resources=dict(root_quota_bytes=1000))
        before = self.files()
        result = harness_run(self.root)
        self.assertEqual((result['state'], result['done']), ('paused', 0))
        self.assertIn('storage', result['reason'])
        self.assertEqual(self.files(), before)
        configure(self.root, resources=dict(root_quota_bytes=2_000_000_000))
        self.assertEqual(settle(self.root)[-1]['state'], 'drained')

    def test_a_database_it_cannot_read_is_reported_not_taken_for_an_empty_queue(self):
        configure(self.root, source=dict(database=str(self.root / 'absent.sqlite3')))
        result = harness_run(self.root)
        self.assertEqual(result['state'], 'paused')
        self.assertIn('unreadable', result['reason'])
        h = Harness(self.root)
        self.assertIn('unreadable', h.status()['last_passage']['reason'])
        h.close()

    def test_rows_long_behind_live_only_warm_up_and_are_counted(self):
        configure(self.root, pipeline=dict(max_lag_s=-10 ** 10))
        settle(self.root)
        h = Harness(self.root)
        self.assertFalse(h.cx.execute('SELECT 1 FROM hypotheses').fetchone())
        self.assertGreater(h.status()['rows_too_late_for_cases'], 0)
        h.close()

    def test_a_long_transaction_blocking_the_lease_renewal_does_not_stop_the_passage(self):
        from unittest import mock
        import harness.runner as runner
        h = Harness(self.root)
        recover.enqueue(h, 'load', 'run_tests', dict(module=str(self.top / 'empty')), 99)
        (self.top / 'empty').mkdir()
        task = recover.claim(h, 'o')
        config = load_config(self.root)
        config['resources'] = dict(config['resources'], lease_s=.3)
        os.environ['SIGNAL_ENGINE_STATE'] = str(self.root / 'engine_state')
        with mock.patch.object(runner, 'renew', side_effect=sqlite3.OperationalError('database is locked')):
            self.assertEqual(runner.supervise(h, task, config, dict(requested=False)), 'done')
        h.close()

    def test_under_the_disk_floor_it_pauses(self):
        configure(self.root, resources=dict(disk_floor_bytes=10 ** 16))
        result = harness_run(self.root)
        self.assertEqual((result['state'], result['done']), ('paused', 0))
        self.assertIn('disk', result['reason'])

    def test_collector_in_reduced_mode_stops_the_passage(self):
        beat = self.root / 'heartbeat.json'
        beat.write_text(json.dumps(dict(at=time.time(), resource_mode='reduced')))
        configure(self.root, source=dict(heartbeat=str(beat)))
        result = harness_run(self.root)
        self.assertEqual((result['state'], result['done']), ('paused', 0))
        self.assertIn('reduced', result['reason'])

    def add_task(self, code, **kwargs):
        folder = self.top / 'suite'
        folder.mkdir(exist_ok=True)
        (folder / 'test_load.py').write_text(code)
        h = Harness(self.root)
        recover.enqueue(h, 'load', 'run_tests', dict(module=str(folder)), 99, **kwargs)
        h.close()

    def test_memory_over_the_ceiling_kills_the_task_and_not_the_passage(self):
        """The memory is in a child of the worker, under the sandbox: both have defeated a naive measure before."""
        self.add_task("import time,unittest\nclass T(unittest.TestCase):\n    def test(self):\n        b=bytearray(150*1024*1024)\n        for i in range(0,len(b),4096):b[i]=1\n        time.sleep(30)\n", max_attempts=1)
        configure(self.root, resources=dict(worker_memory_mb=90))
        started = time.monotonic()
        result = harness_run(self.root, seconds=20)
        self.assertLess(time.monotonic() - started, 60)
        h = Harness(self.root)
        row = h.cx.execute("SELECT status, last_error FROM tasks WHERE dedupe_key='load'").fetchone()
        h.close()
        self.assertEqual(row['status'], 'quarantined')
        self.assertIn('ceiling', row['last_error'])
        self.assertEqual(result['quarantined'], 1)

    def test_a_hung_task_is_stopped_at_its_timeout(self):
        self.add_task("import time,unittest\nclass T(unittest.TestCase):\n    def test(self):\n        time.sleep(300)\n", max_attempts=1)
        configure(self.root, resources=dict(task_timeout_s=2))
        started = time.monotonic()
        harness_run(self.root, seconds=6)
        self.assertLess(time.monotonic() - started, 60)
        h = Harness(self.root)
        row = h.cx.execute("SELECT status, last_error FROM tasks WHERE dedupe_key='load'").fetchone()
        h.close()
        self.assertEqual(row['status'], 'quarantined')
        self.assertIn('over 2 s', row['last_error'])

    def test_a_test_suite_as_a_task_records_its_verdict(self):
        self.add_task("import unittest\nclass T(unittest.TestCase):\n    def test(self):\n        self.fail('deliberate')\n")
        harness_run(self.root, seconds=20)
        h = Harness(self.root)
        row = h.cx.execute("SELECT result FROM tasks WHERE dedupe_key='load'").fetchone()
        self.assertEqual(json.loads(row['result'])['returncode'], 1)
        self.assertTrue(h.cx.execute("SELECT 1 FROM facts WHERE kind='method_bad'").fetchone())
        h.close()


class ModelInTheLoop(unittest.TestCase):
    """The proposer's path through the real queue and verifier, with a stand-in for the CLI."""

    def test_a_proposal_is_tested_a_repeat_is_dropped_and_tokens_are_counted(self):
        from test_harness import FakeClaude
        top = Path(tempfile.mkdtemp(prefix='model_'))
        try:
            root = top / 'run'
            demo.build(root, **SMALL)
            answer = dict(hypotheses=[dict(statement='Large entries gain.', feature='large_entry', threshold=1000), dict(statement='Bigger entries win more.', feature='large_entry', threshold=1000)])
            fake = FakeClaude(top, answer)
            configure(root, llm=dict(enabled=True, executable=str(fake.path), cooldown_s=86400), budgets=dict(llm_calls_per_day=1))
            settle(root)
            self.assertEqual(fake.count(), 1)
            h = Harness(root)
            rows = h.cx.execute("SELECT * FROM hypotheses WHERE kind='population'").fetchall()
            self.assertEqual(len(rows), 1, 'a reworded repeat must not become a second test')
            self.assertNotEqual(rows[0]['status'], 'validated')
            self.assertEqual(rows[0]['proposer'], 'llm:claude-haiku-5-5')
            self.assertEqual(h.used('llm_calls'), 1)
            self.assertGreater(h.used('llm_tokens'), 0)
            self.assertTrue(h.cx.execute('SELECT 1 FROM verifications WHERE hypothesis=?', (rows[0]['id'],)).fetchone())
            h.close()
        finally:
            shutil.rmtree(top, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
