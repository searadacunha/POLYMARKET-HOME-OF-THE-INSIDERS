#!/usr/bin/env python3
"""Offline publication regressions using temporary Git repositories only.

GitHub responses are synthetic; Git commits, concurrent pushes, worktrees and
generator/check exit codes are exercised for real. No live repository is used.
"""
import gzip
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "backup"))
import phi_backup as core  # noqa: E402
import phi_repo as service  # noqa: E402


class ParallelPublication(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.remote = self.root / "remote.git"
        self.clone = self.root / "central"
        self.other = self.root / "session"
        self.state = self.root / "state"
        self.state.mkdir()
        self.real_run = subprocess.run
        self.env = dict(os.environ, GIT_AUTHOR_NAME="Publication tests",
                        GIT_AUTHOR_EMAIL="tests@example.invalid", GIT_COMMITTER_NAME="Publication tests",
                        GIT_COMMITTER_EMAIL="tests@example.invalid", GIT_CONFIG_NOSYSTEM="1",
                        GIT_CONFIG_GLOBAL=os.devnull)
        self.run_git(self.root, "init", "-q", "--bare", "--initial-branch=main", str(self.remote))
        self.run_git(self.root, "clone", "-q", str(self.remote), str(self.clone))
        self.write("README.md", "Accepted README.\n")
        self.write("investigations/case/data.txt", "initial evidence\n")
        self.write("investigations/case/STATUS.md", "updated_utc: initial\n")
        self.write("MASTER_REPORT.md", "old report\n")
        self.write("INVENTORY.md", "inventory\n")
        self.write("BACKUP_STATUS.md", "old status\n")
        self.write("datasets/manifests/local_only.json", "{}\n")
        self.write("datasets/backup/packs.json", "[]\n")
        self.write("datasets/backup/pending.json", "[]\n")
        self.write("scripts/build_master_report.py", """from pathlib import Path
import sys
r = Path(__file__).resolve().parent.parent
value = (r / 'investigations/case/data.txt').read_text()
if '--check' in sys.argv:
    raise SystemExit(0 if (r / 'MASTER_REPORT.md').read_text() == value else 1)
(r / 'MASTER_REPORT.md').write_text(value)
""")
        for name in ("check_publication.py", "test_phi.py", "test_integrity_regressions.py",
                     "test_publication.py", "test_parallel_publication.py", "validate_evidence.py"):
            self.write("scripts/" + name, "raise SystemExit(0)\n")
        self.write("research_notes/relay-followup-2026-11-04/verify.py", "raise SystemExit(0)\n")
        self.run_git(self.clone, "add", ".")
        self.run_git(self.clone, "commit", "-qm", "Initial fixture")
        self.run_git(self.clone, "push", "-q", "origin", "main")
        self.base = self.run_git(self.clone, "rev-parse", "HEAD").stdout.strip()
        self.run_git(self.root, "clone", "-q", str(self.remote), str(self.other))
        self.db = sqlite3.connect(":memory:", isolation_level=None)
        self.addCleanup(self.db.close)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(core.SCHEMA)
        self.cfg = {"repo": "test/fixture", "gh_bin": "synthetic-gh", "publish_every_s": 0}
        (self.state / "BACKUP_STATUS.md").write_text("fresh status\n")
        (self.state / "index.jsonl.gz").write_bytes(gzip.compress(b'{"synthetic": true}\n', mtime=0))
        self.logs = []
        for p in (patch.object(core, "STATE", self.state),
                  patch.object(core, "log", side_effect=lambda event, **kw: self.logs.append((event, kw))),
                  patch.dict(os.environ, self.env)):
            p.start()
            self.addCleanup(p.stop)

    def run_git(self, repo, *args, check=True):
        result = self.real_run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=self.env)
        if check and result.returncode:
            raise AssertionError(f"git {args}: {result.stderr}")
        return result

    def write(self, path, content, repo=None):
        dest = (repo or self.clone) / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(content)

    def remote_text(self, path):
        return self.run_git(self.remote, "show", "main:" + path).stdout

    def remote_head(self):
        return self.run_git(self.remote, "rev-parse", "main").stdout.strip()

    def advance_remote(self, value):
        self.run_git(self.other, "pull", "-q", "--ff-only")
        self.write("investigations/case/data.txt", value, self.other)
        self.run_git(self.other, "add", "--", "investigations/case/data.txt")
        self.run_git(self.other, "commit", "-qm", "Concurrent research")
        self.run_git(self.other, "push", "-q", "origin", "main")

    def is_publication_push(self, args):
        return args[0] == "git" and "push" in args and "origin" in args

    def test_push_race_regenerates_from_latest_main_and_keeps_caller_clean(self):
        pushes = []

        def racing_run(args, **kw):
            if self.is_publication_push(args):
                pushes.append(args)
                if len(pushes) == 1:
                    self.advance_remote("new session evidence\n")
            return self.real_run(args, **kw)

        with patch.object(service.subprocess, "run", side_effect=racing_run):
            service.publish_generated(self.cfg, self.db, self.clone, [])
        self.assertEqual(len(pushes), 2)
        self.assertEqual(self.remote_text("investigations/case/data.txt"), "new session evidence\n")
        self.assertEqual(self.remote_text("MASTER_REPORT.md"), "new session evidence\n")
        self.assertEqual(self.remote_text("README.md"), "Accepted README.\n")
        self.assertEqual(self.run_git(self.clone, "rev-parse", "HEAD").stdout.strip(), self.base)
        self.assertEqual(self.run_git(self.clone, "status", "--porcelain").stdout, "")
        self.assertTrue(service.clean_main(self.clone))

    def test_staged_and_untracked_session_work_is_neither_published_nor_changed(self):
        self.write("README.md", "Unrelated staged work.\n")
        self.run_git(self.clone, "add", "README.md")
        self.write("datasets/session-notes.txt", "Untracked research.\n")
        before = self.run_git(self.clone, "status", "--porcelain").stdout
        index_before = self.run_git(self.clone, "write-tree").stdout
        service.publish_generated(self.cfg, self.db, self.clone, [])
        self.assertEqual(self.remote_text("README.md"), "Accepted README.\n")
        self.assertNotEqual(self.run_git(self.remote, "cat-file", "-e", "main:datasets/session-notes.txt", check=False).returncode, 0)
        self.assertEqual(self.run_git(self.clone, "status", "--porcelain").stdout, before)
        self.assertEqual(self.run_git(self.clone, "write-tree").stdout, index_before)
        self.assertEqual((self.clone / "datasets/session-notes.txt").read_text(), "Untracked research.\n")

    def set_remote_script(self, path, text):
        self.write(path, text, self.other)
        self.run_git(self.other, "add", "--", path)
        self.run_git(self.other, "commit", "-qm", "Fixture failure")
        self.run_git(self.other, "push", "-q", "origin", "main")
        self.run_git(self.clone, "pull", "-q", "--ff-only")
        return self.remote_head()

    def test_generator_failure_cannot_publish_partial_output_or_advance_state(self):
        head = self.set_remote_script("scripts/build_master_report.py", "from pathlib import Path\nPath('MASTER_REPORT.md').write_text('partial output')\nraise SystemExit(7)\n")
        service.publish_generated(self.cfg, self.db, self.clone, [])
        self.assertEqual(self.remote_head(), head)
        self.assertIsNone(core.kv_get(self.db, "generated_at"))
        self.assertIsNone(core.kv_get(self.db, "index_committed_week"))
        self.assertEqual(self.run_git(self.clone, "status", "--porcelain").stdout, "")

    def test_failed_evidence_check_cannot_publish_or_advance_state(self):
        head = self.set_remote_script("scripts/validate_evidence.py", "raise SystemExit(9)\n")
        service.publish_generated(self.cfg, self.db, self.clone, [])
        self.assertEqual(self.remote_head(), head)
        self.assertIsNone(core.kv_get(self.db, "generated_at"))
        self.assertIsNone(core.kv_get(self.db, "index_committed_week"))

    def test_rejected_push_does_not_leave_a_local_commit_or_claim_success(self):
        pushes = []

        def rejected_run(args, **kw):
            if self.is_publication_push(args):
                pushes.append(args)
                return subprocess.CompletedProcess(args, 1, stdout="", stderr="synthetic push refusal")
            return self.real_run(args, **kw)

        with patch.object(service.subprocess, "run", side_effect=rejected_run):
            service.publish_generated(self.cfg, self.db, self.clone, [])
        self.assertEqual(self.remote_head(), self.base)
        self.assertEqual(self.run_git(self.clone, "rev-parse", "HEAD").stdout.strip(), self.base)
        self.assertIsNone(core.kv_get(self.db, "generated_at"))
        self.assertIsNone(core.kv_get(self.db, "index_committed_week"))
        self.assertEqual(len(pushes), 1)

    def test_repeated_remote_changes_have_bounded_retries(self):
        pushes = []

        def racing_run(args, **kw):
            if self.is_publication_push(args):
                pushes.append(args)
                self.advance_remote(f"parallel evidence {len(pushes)}\n")
            return self.real_run(args, **kw)

        with patch.object(service.subprocess, "run", side_effect=racing_run):
            service.publish_generated(self.cfg, self.db, self.clone, [])
        self.assertEqual(len(pushes), 3)
        self.assertEqual(self.remote_text("investigations/case/data.txt"), "parallel evidence 3\n")
        self.assertEqual(self.run_git(self.clone, "rev-parse", "HEAD").stdout.strip(), self.base)
        self.assertIsNone(core.kv_get(self.db, "generated_at"))

    def make_pr(self, branch="investigation/case", draft=False):
        self.run_git(self.other, "switch", "-qc", branch)
        self.write("investigations/case/new.txt", "New source\n", self.other)
        self.run_git(self.other, "add", "--", "investigations/case/new.txt")
        self.run_git(self.other, "commit", "-qm", "New research source")
        self.run_git(self.other, "push", "-q", "origin", branch)
        head = self.run_git(self.other, "rev-parse", "HEAD").stdout.strip()
        self.run_git(self.other, "switch", "-q", "main")
        return {"number": 1, "headRefName": branch, "baseRefName": "main", "headRefOid": head,
                "title": "Research source", "isDraft": draft}

    def gh_responses(self, pr, runs, merged, view=None):
        def gh(_cfg, *args):
            if args[:2] == ("pr", "list"):
                return json.dumps([pr])
            if args[:2] == ("pr", "view"):
                return json.dumps(view or pr)
            if args[:2] == ("run", "list"):
                return json.dumps(runs)
            if args[:2] == ("pr", "merge"):
                merged.append(args)
                self.run_git(self.remote, "update-ref", "refs/heads/main", pr["headRefOid"])
                return ""
            raise AssertionError(args)
        return gh

    def successful_run(self, pr, **overrides):
        return {"databaseId": 100, "headSha": pr["headRefOid"], "headBranch": pr["headRefName"],
                "status": "completed", "conclusion": "success", **overrides}

    def test_draft_investigation_is_held_and_blocks_duplicate_snapshot(self):
        pr = self.make_pr(draft=True)
        merged = []
        with patch.object(service, "gh", side_effect=self.gh_responses(pr, [self.successful_run(pr)], merged)), patch.object(service, "python", return_value=(True, "")):
            open_ids = service.merge_prs(self.cfg, self.db, self.clone)
        self.assertEqual(open_ids, {"case"})
        self.assertEqual(merged, [])
        self.assertEqual(self.remote_head(), self.base)
        self.assertTrue(any("draft" in value.lower() for value in core.kv_get(self.db, "holds", {}).values()))

    def test_pending_ci_is_rechecked_for_the_same_head_on_the_next_pass(self):
        pr = self.make_pr()
        merged = []
        runs = [self.successful_run(pr, status="queued", conclusion="")]
        with patch.object(service, "gh", side_effect=self.gh_responses(pr, runs, merged)), patch.object(service, "python", return_value=(True, "")):
            service.merge_prs(self.cfg, self.db, self.clone)
            self.assertEqual(merged, [])
            runs[:] = [self.successful_run(pr)]
            service.merge_prs(self.cfg, self.db, self.clone)
        self.assertEqual(len(merged), 1)
        self.assertIn("--match-head-commit", merged[0])
        self.assertEqual(self.remote_head(), pr["headRefOid"])

    def test_missing_failed_stale_or_skipped_ci_cannot_merge(self):
        pr = self.make_pr()
        cases = [[], [self.successful_run(pr, headSha="f" * 40)],
                 [self.successful_run(pr, conclusion="failure")],
                 [self.successful_run(pr, conclusion="skipped")],
                 [self.successful_run(pr), self.successful_run(pr, databaseId=101, status="queued", conclusion="")],
                 [self.successful_run(pr, updatedAt="2026-11-04T12:00:00Z"),
                  self.successful_run(pr, databaseId=99, updatedAt="2026-11-04T12:01:00Z", status="queued", conclusion="")]]
        for runs in cases:
            with self.subTest(runs=runs):
                merged = []
                with patch.object(service, "gh", side_effect=self.gh_responses(pr, runs, merged)), patch.object(service, "python", return_value=(True, "")):
                    service.merge_prs(self.cfg, self.db, self.clone)
                self.assertEqual(merged, [])

    def test_head_changed_after_listing_is_not_merged(self):
        pr = self.make_pr()
        merged = []
        with patch.object(service, "gh", side_effect=self.gh_responses(pr, [self.successful_run(pr)], merged, view={**pr, "headRefOid": "e" * 40})), patch.object(service, "python", return_value=(True, "")):
            service.merge_prs(self.cfg, self.db, self.clone)
        self.assertEqual(merged, [])

    def test_base_changed_during_checks_is_not_merged(self):
        pr = self.make_pr()
        merged = []
        advanced = []

        def check(_work, *args):
            if args[0] == "scripts/validate_evidence.py" and not advanced:
                self.advance_remote("another session arrived during checks\n")
                advanced.append(True)
            return True, ""

        with patch.object(service, "gh", side_effect=self.gh_responses(pr, [self.successful_run(pr)], merged)), patch.object(service, "python", side_effect=check):
            service.merge_prs(self.cfg, self.db, self.clone)
        self.assertEqual(merged, [])
        self.assertTrue(any("main changed" in v for v in core.kv_get(self.db, "holds", {}).values()))

    def test_unexpected_generator_output_is_refused(self):
        head = self.set_remote_script("scripts/build_master_report.py", "from pathlib import Path\nPath('README.md').write_text('Unexpected rewrite')\nraise SystemExit(0)\n")
        service.publish_generated(self.cfg, self.db, self.clone, [])
        self.assertEqual(self.remote_head(), head)
        self.assertEqual(self.remote_text("README.md"), "Accepted README.\n")
        self.assertIsNone(core.kv_get(self.db, "generated_at"))

    def configure_snapshot(self):
        origin = self.root / "source-case"
        origin.mkdir()
        (origin / "data.txt").write_text("snapshot evidence\n")
        self.cfg["snapshot_settle_s"] = 0
        self.cfg["investigations"] = {"case": {"origin": str(origin), "root": "case-root", "auto": True, "min_hours": 0}}
        self.db.execute("INSERT INTO files(root,rel,last_hashed) VALUES(?,?,?)", ("case-root", "data.txt", time.time() - 60))
        self.set_remote_script("scripts/import_snapshot.py", """import json
import sys
from pathlib import Path
origin = Path(sys.argv[sys.argv.index('--origin') + 1])
dest = Path('investigations/case')
(dest / 'data.txt').write_text((origin / 'data.txt').read_text())
(dest / 'data_manifest.json').write_text(json.dumps({'snapshot_utc': '2026-11-04T12:00:00Z'}))
""")

    def queue_snapshot(self):
        calls = []

        def gh(_cfg, *args):
            calls.append(args)
            if args[:2] == ("pr", "create"):
                return "https://github.invalid/test/fixture/pull/1"
            raise AssertionError(args)

        ids = set()
        with patch.object(service, "gh", side_effect=gh):
            service.auto_snapshots(self.cfg, self.db, self.clone, ids)
        self.assertEqual(len(calls), 1, self.logs)
        self.assertEqual(calls[0][:2], ("pr", "create"))
        self.assertEqual(ids, {"case"})
        branch = calls[0][calls[0].index("--head") + 1]
        head = self.run_git(self.remote, "rev-parse", "refs/heads/" + branch).stdout.strip()
        return {"number": 1, "headRefName": branch, "baseRefName": "main", "headRefOid": head,
                "title": "Snapshot", "isDraft": False}

    def test_snapshot_is_queued_for_ci_then_retried_without_a_duplicate(self):
        self.configure_snapshot()
        base = self.remote_head()
        self.write("README.md", "Unrelated staged session change\n")
        self.run_git(self.clone, "add", "README.md")
        self.write("investigations/case/unsaved-note.txt", "Untracked session note\n")
        before = self.run_git(self.clone, "status", "--porcelain").stdout
        index_before = self.run_git(self.clone, "write-tree").stdout
        pr = self.queue_snapshot()
        self.assertEqual(self.remote_head(), base)
        self.assertEqual(self.run_git(self.remote, "show", pr["headRefOid"] + ":MASTER_REPORT.md").stdout, "snapshot evidence\n")
        merged = []
        runs = [self.successful_run(pr, status="in_progress", conclusion="")]
        with patch.object(service, "gh", side_effect=self.gh_responses(pr, runs, merged)):
            ids = service.merge_prs(self.cfg, self.db, self.clone)
            core.kv_set(self.db, "import:case", 0)
            service.auto_snapshots(self.cfg, self.db, self.clone, ids)
            self.assertEqual(merged, [])
            self.assertEqual(ids, {"case"})
            runs[:] = [self.successful_run(pr)]
            service.merge_prs(self.cfg, self.db, self.clone)
        self.assertEqual(len(merged), 1)
        self.assertEqual(self.remote_head(), pr["headRefOid"])
        self.assertEqual(self.remote_text("README.md"), "Accepted README.\n")
        self.assertEqual(self.run_git(self.clone, "status", "--porcelain").stdout, before)
        self.assertEqual(self.run_git(self.clone, "write-tree").stdout, index_before)

    def test_pending_snapshot_integrates_new_main_and_regenerates_conflicting_reports(self):
        self.configure_snapshot()
        pr = self.queue_snapshot()
        self.run_git(self.other, "pull", "-q", "--ff-only")
        self.write("investigations/other/new.txt", "Concurrent accepted source\n", self.other)
        self.write("MASTER_REPORT.md", "Concurrent generated report\n", self.other)
        self.run_git(self.other, "add", ".")
        self.run_git(self.other, "commit", "-qm", "Another session published")
        self.run_git(self.other, "push", "-q", "origin", "main")
        main_head = self.remote_head()
        old_head = pr["headRefOid"]
        merged = []
        with patch.object(service, "gh", side_effect=self.gh_responses(pr, [self.successful_run(pr)], merged)):
            ids = service.merge_prs(self.cfg, self.db, self.clone)
        self.assertEqual(ids, {"case"})
        self.assertEqual(merged, [])
        self.assertEqual(self.remote_head(), main_head)
        new_head = self.run_git(self.remote, "rev-parse", "refs/heads/" + pr["headRefName"]).stdout.strip()
        self.assertNotEqual(new_head, old_head)
        for parent in (main_head, old_head):
            self.assertEqual(self.run_git(self.remote, "merge-base", "--is-ancestor", parent, new_head, check=False).returncode, 0)
        self.assertEqual(self.run_git(self.remote, "show", new_head + ":MASTER_REPORT.md").stdout, "snapshot evidence\n")
        self.assertEqual(self.run_git(self.remote, "show", new_head + ":investigations/other/new.txt").stdout, "Concurrent accepted source\n")
        pr["headRefOid"] = new_head
        with patch.object(service, "gh", side_effect=self.gh_responses(pr, [self.successful_run(pr)], merged)):
            service.merge_prs(self.cfg, self.db, self.clone)
        self.assertEqual(len(merged), 1)
        self.assertEqual(self.remote_head(), new_head)

    def test_snapshot_source_conflict_is_held_without_overwriting_either_branch(self):
        self.configure_snapshot()
        pr = self.queue_snapshot()
        self.advance_remote("Conflicting source from another session\n")
        base = self.remote_head()
        merged = []
        with patch.object(service, "gh", side_effect=self.gh_responses(pr, [self.successful_run(pr)], merged)):
            ids = service.merge_prs(self.cfg, self.db, self.clone)
        self.assertEqual(ids, {"case"})
        self.assertEqual(merged, [])
        self.assertEqual(self.remote_head(), base)
        self.assertEqual(self.run_git(self.remote, "rev-parse", pr["headRefName"]).stdout.strip(), pr["headRefOid"])
        self.assertTrue(any("source changes" in v for v in core.kv_get(self.db, "holds", {}).values()))

    def test_failed_snapshot_generation_is_retryable_and_preserves_local_work(self):
        self.configure_snapshot()
        base = self.set_remote_script("scripts/build_master_report.py", "raise SystemExit(6)\n")
        self.write("investigations/case/local-note.txt", "Untracked session note\n")
        before = self.run_git(self.clone, "status", "--porcelain").stdout
        with patch.object(service, "gh", side_effect=AssertionError("No publication is allowed")):
            service.auto_snapshots(self.cfg, self.db, self.clone, set())
        self.assertEqual(self.remote_head(), base)
        self.assertIsNone(core.kv_get(self.db, "import:case"))
        self.assertIn("snapshot case", core.kv_get(self.db, "holds", {}))
        self.assertEqual(self.run_git(self.clone, "status", "--porcelain").stdout, before)
        self.assertEqual((self.clone / "investigations/case/local-note.txt").read_text(), "Untracked session note\n")


if __name__ == "__main__":
    unittest.main()
