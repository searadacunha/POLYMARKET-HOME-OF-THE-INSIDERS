"""Offline tests of the registry on SQLite. Run from integrations/phi_registry:  python3 -m unittest discover -s tests -v"""
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE))
import fixture as fx  # noqa: E402
import phi_registry as reg  # noqa: E402


def fresh(case, **kw):
    root = Path(tempfile.mkdtemp(prefix="phi-reg-"))
    case.addCleanup(shutil.rmtree, root, True)
    fx.make_tree(root / "tree", **kw)
    con = reg.connect(root / "r.sqlite3")
    case.addCleanup(con.close)
    return root, con


def git(root, *args):
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false", "-C", str(root), *args],
                          capture_output=True, text=True, check=True).stdout.strip()


class Build(unittest.TestCase):
    def test_tables_from_a_directory(self):
        root, con = fresh(self)
        out = reg.build(con, reg.DirSource(root / "tree"))
        c = out["counts"]
        self.assertEqual((c["investigations"], c["findings"], c["open_items"], c["evidence"]), (2, 3, 3, 3))
        self.assertEqual(dict(con.execute("SELECT level, count(*) FROM findings GROUP BY level").fetchall()),
                         {"CONFIRMED": 1, "REFUTED": 1, "HYPOTHESIS": 1})
        self.assertEqual({r[0] for r in con.execute("SELECT kind FROM open_items")}, {"missing", "contradiction"})
        self.assertEqual(dict(con.execute("SELECT path, sha256 FROM evidence WHERE investigation_id = 'alpha'").fetchall()),
                         {"sources/data/a.csv": "auto", "sources/report.md": fx.SHA, "sources/big.csv": "local_only"})

    def test_address_index(self):
        root, con = fresh(self)
        reg.build(con, reg.DirSource(root / "tree"))
        mentions = {(a, s): n for a, s, n in con.execute("SELECT address, scope, files FROM wallet_mentions")}
        self.assertEqual(mentions[(fx.A, "alpha")], 2, "a.csv and FINDINGS.md")
        self.assertIn((fx.A, "beta"), mentions)
        self.assertIn((fx.C, "rn:note-2026-11-02"), mentions)
        self.assertNotIn(fx.TX[:42], {a for a, _ in mentions}, "the first 40 hex characters of a 64-hex hash are not an address")
        paths = [r[0] for r in con.execute("SELECT first_ref FROM wallet_mentions")]
        self.assertFalse(any(p.endswith(".bin") for p in paths), "unknown extensions are not scanned")
        self.assertEqual([tuple(r) for r in con.execute(
            "SELECT finding_id FROM finding_addresses WHERE investigation_id = 'beta' AND address = ?", (fx.A,))], [("F-001",)])

    def test_check_address_and_words(self):
        root, con = fresh(self)
        reg.build(con, reg.DirSource(root / "tree"))
        got = reg.check(con, fx.A.upper().replace("0X", "0x"))
        self.assertEqual({s["scope"] for s in got["scopes"]}, {"alpha", "beta"})
        self.assertEqual({(f["investigation"], f["finding"], f["level"]) for f in got["findings"]},
                         {("alpha", "F-001", "CONFIRMED"), ("beta", "F-001", "HYPOTHESIS")})
        words = reg.check(con, "funding PURCHASE")
        self.assertEqual([(f["investigation"], f["level"]) for f in words["findings"]], [("alpha", "REFUTED")])
        self.assertEqual(reg.check(con, "nothing like this")["total"], 0)

    def test_reproducible_and_sensitive(self):
        root, con = fresh(self)
        reg.build(con, reg.DirSource(root / "tree"))
        first = reg.digest(con)
        reg.build(con, reg.DirSource(root / "tree"))
        self.assertEqual(first, reg.digest(con))
        fx.write(root / "tree", "investigations/alpha/FINDINGS.md", (root / "tree/investigations/alpha/FINDINGS.md").read_text() + "\n")
        reg.build(con, reg.DirSource(root / "tree"))
        self.assertEqual(first, reg.digest(con), "whitespace after the last bullet is not content")
        fx.write(root / "tree", "research_notes/note-2026-11-02/REPORT.md", f"The account {fx.B} appears.\n")
        reg.build(con, reg.DirSource(root / "tree"))
        self.assertNotEqual(first, reg.digest(con))

    def test_git_commit_equals_directory_and_ignores_the_dirty_tree(self):
        if not shutil.which("git"):
            self.skipTest("git not installed")
        root, con = fresh(self)
        tree = root / "tree"
        git(tree, "init", "-q")
        git(tree, "add", "-A")
        git(tree, "commit", "-q", "-m", "fixture")
        by_dir = reg.build(con, reg.DirSource(tree))
        d_dir = reg.digest(con)
        by_git = reg.build(con, reg.GitSource(tree, "HEAD"))
        self.assertEqual(d_dir, reg.digest(con))
        self.assertEqual(by_git["source"], "git:" + git(tree, "rev-parse", "HEAD"))
        self.assertEqual(by_dir["counts"], by_git["counts"])
        fx.write(tree, "investigations/alpha/FINDINGS.md", "# Findings\n")  # uncommitted edit
        reg.build(con, reg.GitSource(tree, "HEAD"))
        self.assertEqual(d_dir, reg.digest(con), "a commit is read from git objects, not from the working tree")

    def test_a_failed_build_changes_nothing(self):
        root, con = fresh(self)
        reg.build(con, reg.DirSource(root / "tree"))
        before = reg.digest(con)
        fx.make_tree(root / "tree", alpha_state="WRONG")
        with self.assertRaisesRegex(ValueError, "alpha/STATUS.md"):
            reg.build(con, reg.DirSource(root / "tree"))
        self.assertEqual(before, reg.digest(con))

    def test_a_failure_inside_the_transaction_rolls_back(self):
        root, con = fresh(self)
        reg.build(con, reg.DirSource(root / "tree"))
        before = reg.digest(con)
        text = (root / "tree/investigations/alpha/EVIDENCE.md").read_text()
        fx.write(root / "tree", "investigations/alpha/EVIDENCE.md", text + "| `sources/report.md` | auto | duplicated path |\n")
        with self.assertRaises(sqlite3.IntegrityError):
            reg.build(con, reg.DirSource(root / "tree"))
        self.assertEqual(before, reg.digest(con), "the old content is still there")

    def test_tasks_survive_a_rebuild(self):
        root, con = fresh(self)
        reg.add_task(con, "wallet", fx.A)
        reg.build(con, reg.DirSource(root / "tree"))
        self.assertEqual(reg.task_stats(con), {"queued": 1})


class Verify(unittest.TestCase):
    def committed(self):
        if not shutil.which("git"):
            self.skipTest("git not installed")
        root, con = fresh(self)
        tree = root / "tree"
        git(tree, "init", "-q")
        git(tree, "add", "-A")
        git(tree, "commit", "-q", "-m", "fixture")
        reg.build(con, reg.GitSource(tree, "HEAD"))
        return tree, con

    @staticmethod
    def failed(checks):
        return [c["check"] for c in checks if not c["ok"]]

    def test_a_clean_registry_passes_every_check(self):
        tree, con = self.committed()
        checks = reg.verify(con, tree, sample=100)
        self.assertEqual(self.failed(checks), [])
        self.assertEqual(len(checks), 5)
        self.assertIn("sampled address rows agree", checks[-1]["check"])

    def test_a_manual_edit_is_caught_by_the_digest_and_the_independent_sample(self):
        tree, con = self.committed()
        con.execute("UPDATE wallet_mentions SET files = files + 1 WHERE address = ? AND scope = 'alpha'", (fx.A,))
        failed = self.failed(reg.verify(con, tree, sample=100))
        self.assertTrue(any("stored digest" in c for c in failed), failed)
        self.assertTrue(any("independent git grep" in c for c in failed), failed)

    def test_a_forged_digest_is_caught_by_the_rebuild(self):
        tree, con = self.committed()
        con.execute("DELETE FROM wallet_mentions WHERE address = ? AND scope = 'alpha'", (fx.C,))
        con.execute("UPDATE registry_meta SET value = ? WHERE key = 'content_sha256'", (reg.digest(con),))
        failed = self.failed(reg.verify(con, tree, sample=100))
        self.assertEqual(failed, ["rebuilding that commit gives the stored digest"])

    def test_a_directory_build_has_no_provenance_to_verify(self):
        root, con = fresh(self)
        reg.build(con, reg.DirSource(root / "tree"))
        self.assertEqual(self.failed(reg.verify(con, root / "tree")), ["the registry was built from a git commit"])

    def test_an_investigation_id_lists_all_its_findings(self):
        root, con = fresh(self)
        reg.build(con, reg.DirSource(root / "tree"))
        got = reg.check(con, "alpha")
        self.assertEqual((got["kind"], got["state"], [(f["finding"], f["level"]) for f in got["findings"]]),
                         ("investigation", "DONE", [("F-001", "CONFIRMED"), ("F-002", "REFUTED")]))
        self.assertEqual([o["kind"] for o in got["open_items"]], ["contradiction", "missing", "missing"])


class TestLedger(unittest.TestCase):
    def test_three_formats_and_a_lookalike(self):
        root, con = fresh(self)
        out = reg.build(con, reg.DirSource(root / "tree"))
        rows = con.execute("SELECT study, test_id, status, n, effect, p_value, alpha_study, declared_comparisons FROM hypothesis_tests "
                           "ORDER BY study, test_id").fetchall()
        self.assertEqual([(r["study"], r["test_id"]) for r in rows],
                         [("alpha", "T1"), ("alpha", "T2"), ("alpha", "T3"), ("beta", "L1:T1"), ("beta", "L2:T4"), ("beta", "L3:T9"),
                          ("rn:study-2026-11-03", "T1"), ("rn:study-2026-11-03", "T2")])
        self.assertEqual((rows[0]["n"], rows[0]["effect"], rows[0]["alpha_study"], rows[0]["declared_comparisons"]), (50, 0.2, 0.0167, 3))
        self.assertEqual((rows[1]["n"], rows[1]["effect"]), (50, -0.01))
        self.assertEqual([r["status"] for r in rows if r["study"] == "beta"], ["exploratory", "confirmatory", "exploratory"])
        self.assertIsNone([r for r in rows if r["test_id"] == "L3:T9"][0]["effect"], "a list is not an effect size")
        self.assertEqual((rows[7]["n"], rows[7]["declared_comparisons"]), (45, 18))
        self.assertEqual(out["test_files_skipped"], "investigations/alpha/sources/state/tests.json,investigations/beta/sources/state/tests.json")

    def test_report_is_a_count_per_study_without_pooling(self):
        root, con = fresh(self)
        reg.build(con, reg.DirSource(root / "tree"))
        rep = reg.tests_report(con)
        self.assertEqual([(s["study"], s["registered"], s["declared"], s["exploratory"], s["nominal_p_below_alpha_unadjusted"])
                          for s in rep["studies"]],
                         [("alpha", 3, 3, 0, 1), ("beta", 3, None, 2, 1), ("rn:study-2026-11-03", 2, 18, 0, 1)])
        self.assertEqual(set(rep), {"studies", "alpha"}, "no pooled threshold, no expected-by-chance figure")


class Tasks(unittest.TestCase):
    def test_same_unit_is_one_task_and_prior_work_is_reported(self):
        root, con = fresh(self)
        reg.build(con, reg.DirSource(root / "tree"))
        first = reg.add_task(con, "Wallet", fx.A)
        second = reg.add_task(con, "wallet", "  " + fx.A.upper().replace("0X", "0x") + "\n")
        self.assertEqual((first["created"], second["created"], first["task"]), (True, False, second["task"]))
        self.assertEqual((first["prior_scopes"], first["prior_findings"]), (2, 2))
        self.assertEqual(reg.task_stats(con), {"queued": 1})
        self.assertEqual(reg.check(con, fx.A)["tasks"][0]["status"], "queued")

    def test_lease_fencing_and_attempts(self):
        _, con = fresh(self)
        t = reg.add_task(con, "hypothesis", "funding precedes purchase", max_attempts=2, now=100)["task"]
        one = reg.claim(con, "a1", ttl=10, now=100)
        self.assertEqual((one["task"], one["token"]), (t, 1))
        self.assertIsNone(reg.claim(con, "a2", ttl=10, now=105), "a live lease is not handed out")
        self.assertFalse(reg.complete(con, t, "a1", 99, now=105), "wrong token")
        self.assertFalse(reg.complete(con, t, "a2", 1, now=105), "wrong agent")
        self.assertTrue(reg.heartbeat(con, t, "a1", 1, ttl=10, now=108))
        self.assertIsNone(reg.claim(con, "a2", ttl=10, now=112), "the heartbeat extended the lease to 118")
        two = reg.claim(con, "a2", ttl=10, now=120)
        self.assertEqual((two["task"], two["token"]), (t, 2), "an expired lease is taken over")
        self.assertFalse(reg.complete(con, t, "a1", 1, result_ref="late", now=121), "the old holder is fenced out")
        self.assertTrue(reg.complete(con, t, "a2", 2, result_ref="F-007", now=122))
        self.assertFalse(reg.complete(con, t, "a2", 2, now=123), "completed once only")
        self.assertEqual(con.execute("SELECT status, result_ref FROM agent_tasks").fetchone()[:], ("done", "F-007"))
        events = [r[0] for r in con.execute("SELECT event FROM task_events ORDER BY at, rowid")]
        self.assertEqual(events, ["added", "claimed", "heartbeat", "claimed", "done"])

    def test_failure_requeues_then_closes(self):
        _, con = fresh(self)
        t = reg.add_task(con, "market", "m1", max_attempts=2, now=0)["task"]
        c1 = reg.claim(con, "a", ttl=5, now=1)
        self.assertEqual(reg.fail(con, t, "a", c1["token"], "rate limited", now=2), "queued")
        c2 = reg.claim(con, "b", ttl=5, now=3)
        self.assertEqual(c2["token"], 2)
        self.assertEqual(reg.fail(con, t, "b", 2, "again", now=4), "failed")
        self.assertIsNone(reg.claim(con, "c", now=5))
        self.assertEqual(reg.task_stats(con), {"failed": 1})

    def test_a_crashed_last_attempt_is_closed_not_retried_forever(self):
        _, con = fresh(self)
        reg.add_task(con, "market", "m2", max_attempts=1, now=0)
        reg.claim(con, "a", ttl=5, now=1)  # a crashes
        self.assertIsNone(reg.claim(con, "b", ttl=5, now=100))
        self.assertEqual(reg.task_stats(con), {"failed": 1})
        self.assertEqual(con.execute("SELECT last_error FROM agent_tasks").fetchone()[0], "lease expired after max attempts")

    def test_priority_then_age(self):
        _, con = fresh(self)
        reg.add_task(con, "w", "old", priority=3, now=1)
        reg.add_task(con, "w", "urgent", priority=1, now=2)
        reg.add_task(con, "w", "new", priority=3, now=3)
        self.assertEqual([reg.claim(con, "a", now=10)["subject"] for _ in range(3)], ["urgent", "old", "new"])

    def test_concurrent_agents_never_share_a_task_and_crashes_are_recovered(self):
        root, con = fresh(self)
        total = 60
        for i in range(total):
            reg.add_task(con, "wallet", f"subject {i}", max_attempts=20)
        db = str(root / "r.sqlite3")

        def worker(n):
            c = reg.connect(db)
            done = 0
            for step in range(10_000):
                got = reg.claim(c, f"agent-{n}", ttl=1)
                if got is None:
                    if c.execute("SELECT count(*) FROM agent_tasks WHERE status IN ('queued', 'running')").fetchone()[0] == 0:
                        break
                    time.sleep(0.05)
                    continue
                if (hash((n, step)) % 7) == 0:  # this agent "crashes": the lease is simply left to expire
                    continue
                done += reg.complete(c, got["task"], f"agent-{n}", got["token"], result_ref=f"by-{n}")
            c.close()
            return done

        with ThreadPoolExecutor(max_workers=6) as pool:
            completed = sum(pool.map(worker, range(6)))
        self.assertEqual(completed, total)
        self.assertEqual(reg.task_stats(con), {"done": total})
        per_task = dict(con.execute("SELECT task_id, count(*) FROM task_events WHERE event = 'done' GROUP BY task_id").fetchall())
        self.assertEqual((len(per_task), set(per_task.values())), (total, {1}), "every task completed exactly once")


class Export(unittest.TestCase):
    def test_exported_sql_rebuilds_the_same_content(self):
        root, con = fresh(self)
        reg.build(con, reg.DirSource(root / "tree"))
        con.execute("INSERT INTO findings VALUES ('alpha', 'F-099', 'UNRESOLVED', ?, 'it''s', 'line1\nline2', 'back\\slash', 'ünï ☃')",
                    ("quote ' and \\ and unicode é and NULL-like 'NULL'",))
        sql = reg.export_sql(con, reg.DERIVED)
        other = reg.connect(root / "other.sqlite3")
        self.addCleanup(other.close)
        other.executescript(sql)
        self.assertEqual(reg.digest(con), reg.digest(other))
        self.assertNotIn("INSERT INTO wallet_mentions", reg.export_sql(con), "the large index is opt-in")
        self.assertNotIn("agent_tasks", reg.export_sql(con), "operational state never leaves with the derived tables")
        with self.assertRaises(SystemExit):
            reg.export_sql(con, ("agent_tasks",))

    def test_backup_is_a_consistent_copy(self):
        root, con = fresh(self)
        reg.build(con, reg.DirSource(root / "tree"))
        reg.add_task(con, "wallet", fx.A)
        reg.backup(con, root / "copy.sqlite3")
        copy = reg.connect(root / "copy.sqlite3")
        self.addCleanup(copy.close)
        self.assertEqual((reg.digest(copy), reg.task_stats(copy)), (reg.digest(con), {"queued": 1}))


class CommandLine(unittest.TestCase):
    def run_cli(self, db, *args):
        done = subprocess.run([sys.executable, str(HERE.parent / "phi_registry.py"), "--db", str(db), *args], capture_output=True, text=True)
        self.assertEqual(done.returncode, 0, done.stderr)
        return done.stdout

    def test_build_check_task_cycle(self):
        root = Path(tempfile.mkdtemp(prefix="phi-cli-"))
        self.addCleanup(shutil.rmtree, root, True)
        fx.make_tree(root / "tree")
        db = root / "r.sqlite3"
        built = json.loads(self.run_cli(db, "build", "--dir", str(root / "tree")))
        self.assertEqual(built["counts"]["findings"], 3)
        self.assertEqual(self.run_cli(db, "digest").strip(), built["content_sha256"])
        got = json.loads(self.run_cli(db, "check", fx.A))
        self.assertEqual({s["scope"] for s in got["scopes"]}, {"alpha", "beta"})
        added = json.loads(self.run_cli(db, "task", "add", "wallet", fx.A))
        claimed = json.loads(self.run_cli(db, "task", "claim", "cli-agent"))
        self.assertEqual(claimed["task"], added["task"])
        self.assertIs(json.loads(self.run_cli(db, "task", "done", claimed["task"], "cli-agent", str(claimed["token"]), "F-001")), True)
        self.assertEqual(json.loads(self.run_cli(db, "task", "stats")), {"done": 1})
        self.assertIn("REFUTED", self.run_cli(db, "brief"))
        self.assertTrue(self.run_cli(db, "export-sql").startswith("-- phi_registry export"))


if __name__ == "__main__":
    unittest.main()
