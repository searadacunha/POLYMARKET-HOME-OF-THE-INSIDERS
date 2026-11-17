"""Exercise publication failures in small real Git repositories, without network."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from check_publication import (
    PublicationError,
    expected_manifest,
    verify,
    verify_policy_unchanged,
)


class PublicationChecks(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Publication tests")
        self.git("config", "user.email", "tests@example.invalid")
        self.write("README.md", "old overview\n")
        self.before = self.save()
        self.write("README.md", "accepted overview\n")
        self.write("research_notes/accepted/proof.json", '{"raw_amount":2969568353}\n')
        self.anchor = self.save()
        self.policy = {"branches": {"main": {"commit": self.anchor,
                       "protected_paths": ["README.md", "research_notes/accepted/"]}}}

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.repo), *args], check=True,
                              capture_output=True, text=True).stdout.strip()

    def write(self, path, text):
        dest = self.repo / path
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)

    def save(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "fixture update")
        return self.git("rev-parse", "HEAD")

    def test_new_research_can_be_published_without_writing_existing_files(self):
        self.write("investigations/new-case/README.md", "new research\n")
        candidate = self.save()
        before = self.git("status", "--porcelain")
        result = verify(self.repo, self.policy, "main", base_ref=self.anchor)
        self.assertEqual(result["candidate"], candidate)
        self.assertEqual(result["protected_files"], 2)
        self.assertEqual(self.git("status", "--porcelain"), before)
        self.assertEqual(self.git("rev-parse", "HEAD"), candidate)

    def test_restored_old_readme_fails_despite_preserved_ancestry(self):
        self.write("README.md", "old overview\n")
        self.save()
        with self.assertRaisesRegex(PublicationError, "README.md"):
            verify(self.repo, self.policy, "main")

    def test_deleted_readme_fails(self):
        (self.repo / "README.md").unlink()
        self.save()
        with self.assertRaisesRegex(PublicationError, "README.md"):
            verify(self.repo, self.policy, "main")

    def test_changed_archived_response_fails(self):
        self.write("research_notes/accepted/proof.json", '{"raw_amount":1}\n')
        self.save()
        with self.assertRaisesRegex(PublicationError, "proof.json"):
            verify(self.repo, self.policy, "main")

    def test_added_file_inside_protected_directory_fails(self):
        self.write("research_notes/accepted/new-receipt.json", '{"raw_amount":1}\n')
        self.save()
        with self.assertRaisesRegex(PublicationError, "new-receipt.json"):
            verify(self.repo, self.policy, "main")

    def test_added_nested_file_inside_protected_directory_fails(self):
        self.write("research_notes/accepted/derived/new-proof.json", '{"raw_amount":1}\n')
        self.save()
        with self.assertRaisesRegex(PublicationError, "derived/new-proof.json"):
            verify(self.repo, self.policy, "main")

    def test_missing_baseline_is_an_error(self):
        policy = copy.deepcopy(self.policy)
        policy["branches"]["main"]["commit"] = "f" * 40
        with self.assertRaises(PublicationError):
            verify(self.repo, policy, "main")

    def test_simulated_merge_does_not_mask_an_outdated_pr_head(self):
        self.git("checkout", "-qb", "stale-session", self.before)
        self.write("new-result.json", "{}\n")
        stale_head = self.save()
        self.git("checkout", "-qb", "simulated-merge", self.anchor)
        self.git("merge", "--no-ff", "-qm", "simulated PR merge", stale_head)
        with self.assertRaisesRegex(PublicationError, "omits required commit"):
            verify(self.repo, self.policy, "main", head=stale_head)

    def test_fresh_destination_must_be_included_when_requested(self):
        self.write("another-session.json", "{}\n")
        destination = self.save()
        with self.assertRaisesRegex(PublicationError, "omits required commit"):
            verify(self.repo, self.policy, "main", candidate=self.anchor,
                   base_ref=destination)

    def test_policy_change_cannot_self_approve_a_new_anchor(self):
        path = "scripts/publication_baseline.json"
        self.write(path, "trusted\\n")
        destination = self.save()
        self.write(path, "self-approved\\n")
        changed_head = self.save()
        with self.assertRaisesRegex(PublicationError, "publication policy changed"):
            verify_policy_unchanged(self.repo, self.repo / path, destination,
                                    changed_head, changed_head)

    def test_unchanged_policy_is_accepted_from_destination(self):
        path = "scripts/publication_baseline.json"
        self.write(path, "trusted\\n")
        destination = self.save()
        self.write("investigations/new/test.txt", "new evidence\\n")
        head = self.save()
        verify_policy_unchanged(self.repo, self.repo / path, destination, head, head)

    def test_policy_missing_on_destination_fails_closed(self):
        path = "scripts/publication_baseline.json"
        with self.assertRaisesRegex(PublicationError, "destination lacks publication policy"):
            verify_policy_unchanged(self.repo, self.repo / path, self.anchor,
                                    self.anchor, self.anchor)

    def test_uncommitted_policy_cannot_authorize_a_changed_readme(self):
        path = "scripts/publication_baseline.json"
        self.write(path, json.dumps(self.policy))
        destination = self.save()
        self.write("README.md", "unreviewed replacement\n")
        candidate = self.save()
        local_policy = copy.deepcopy(self.policy)
        local_policy["branches"]["main"]["commit"] = candidate
        self.write(path, json.dumps(local_policy))
        script = Path(__file__).with_name("check_publication.py")
        missing = subprocess.run(
            [sys.executable, str(script), "--repo", str(self.repo),
             "--policy", str(self.repo / path), "--target", "main",
             "--candidate", candidate], capture_output=True, text=True)
        self.assertEqual(missing.returncode, 1)
        self.assertIn("cannot be skipped", missing.stderr)
        present = subprocess.run(
            [sys.executable, str(script), "--repo", str(self.repo),
             "--policy", str(self.repo / path), "--target", "main",
             "--candidate", candidate, "--base-ref", destination],
            capture_output=True, text=True)
        self.assertEqual(present.returncode, 1)
        self.assertIn("protected files", present.stderr)
        self.assertIn("README.md", present.stderr)

    def test_committed_policy_is_read_even_if_worktree_copy_is_missing(self):
        path = "scripts/publication_baseline.json"
        self.write(path, json.dumps(self.policy))
        destination = self.save()
        (self.repo / path).unlink()
        result = subprocess.run(
            [sys.executable, str(Path(__file__).with_name("check_publication.py")),
             "--repo", str(self.repo), "--policy", str(self.repo / path),
             "--target", "main", "--base-ref", destination], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.repo / path).exists())

    def _migrate(self, new_anchor, authorization=None, reason=None, assets=None, readme=None):
        path = "scripts/publication_baseline.json"
        manifest_path = "scripts/publication_migration.json"
        policy = copy.deepcopy(self.policy)
        policy["branches"]["main"]["commit"] = new_anchor
        text = authorization or (
            f"Benjamin authorized this test move from {self.anchor} to {new_anchor}."
        )
        because = reason or (
            f"Recorded test migration from {self.anchor} to {new_anchor}."
        )
        manifest = expected_manifest(
            self.repo, self.anchor, new_anchor,
            self.policy["branches"]["main"]["protected_paths"], text, because,
        )
        if assets is not None:
            manifest["assets"] = assets
        if readme is not None:
            manifest["readme"] = readme
        self.write(path, json.dumps(policy))
        self.write(manifest_path, json.dumps(manifest))
        return self.save()

    def _run_check(self, candidate, base):
        script = Path(__file__).with_name("check_publication.py")
        return subprocess.run(
            [sys.executable, str(script), "--repo", str(self.repo),
             "--policy", str(self.repo / "scripts/publication_baseline.json"),
             "--target", "main", "--candidate", candidate, "--head", candidate,
             "--base-ref", base],
            capture_output=True, text=True,
        )

    def _base_at_new_anchor(self, mutate):
        """The destination already contains the new tree and still names the old anchor."""
        self.write("scripts/publication_baseline.json", json.dumps(self.policy))
        self.save()
        mutate()
        return self.save()

    def test_declared_readme_migration_preserves_other_protected_files(self):
        def mutate():
            self.write("README.md", "accepted overview\n\n![hero](assets/hero.txt)\n")
            self.write("assets/hero.txt", "hero-bytes\n")
        destination = self._base_at_new_anchor(mutate)
        candidate = self._migrate(destination)
        result = self._run_check(candidate, destination)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.write("research_notes/accepted/proof.json", '{"raw_amount":1}\n')
        later = self.save()
        refused = self._run_check(later, candidate)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("proof.json", refused.stderr)

    def test_migration_refuses_a_changed_protected_archive(self):
        def mutate():
            self.write("README.md", "accepted overview\n\nwith a picture\n")
            self.write("research_notes/accepted/proof.json", '{"raw_amount":1}\n')
        destination = self._base_at_new_anchor(mutate)
        candidate = self._migrate(destination)
        result = self._run_check(candidate, destination)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("protected files other than README.md", result.stderr)

    def test_migration_refuses_an_added_protected_file(self):
        def mutate():
            self.write("README.md", "accepted overview\n\nwith a picture\n")
            self.write("research_notes/accepted/extra.json", "{}\n")
        destination = self._base_at_new_anchor(mutate)
        candidate = self._migrate(destination)
        result = self._run_check(candidate, destination)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("protected files other than README.md", result.stderr)

    def test_migration_refuses_an_undeclared_readme_diff(self):
        def mutate():
            self.write("README.md", "accepted overview\n\nwith a picture\n")
        destination = self._base_at_new_anchor(mutate)
        candidate = self._migrate(destination, readme={
            "old_sha256": "0" * 64, "new_sha256": "1" * 64, "diff_sha256": "2" * 64,
        })
        result = self._run_check(candidate, destination)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("manifest readme", result.stderr)

    def test_migration_refuses_a_protected_path_list_change(self):
        def mutate():
            self.write("README.md", "accepted overview\n\nwith a picture\n")
        destination = self._base_at_new_anchor(mutate)
        policy = copy.deepcopy(self.policy)
        policy["branches"]["main"]["commit"] = destination
        policy["branches"]["main"]["protected_paths"] = ["README.md"]
        self.write("scripts/publication_baseline.json", json.dumps(policy))
        manifest = expected_manifest(
            self.repo, self.anchor, destination, ["README.md"],
            f"Benjamin authorized this test move from {self.anchor} to {destination}.",
            f"Recorded test migration from {self.anchor} to {destination}.",
        )
        self.write("scripts/publication_migration.json", json.dumps(manifest))
        candidate = self.save()
        result = self._run_check(candidate, destination)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("protected paths may only be added", result.stderr)

    def test_migration_refuses_an_unrelated_file_in_the_same_commit(self):
        def mutate():
            self.write("README.md", "accepted overview\n\nwith a picture\n")
        destination = self._base_at_new_anchor(mutate)
        self.write("notes/side.txt", "not part of the migration\n")
        text = f"Benjamin authorized this test move from {self.anchor} to {destination}."
        because = f"Recorded test migration from {self.anchor} to {destination}."
        policy = copy.deepcopy(self.policy)
        policy["branches"]["main"]["commit"] = destination
        manifest = expected_manifest(
            self.repo, self.anchor, destination,
            self.policy["branches"]["main"]["protected_paths"], text, because,
        )
        self.write("scripts/publication_baseline.json", json.dumps(policy))
        self.write("scripts/publication_migration.json", json.dumps(manifest))
        candidate = self.save()
        result = self._run_check(candidate, destination)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("other than the publication policy", result.stderr)

    def test_missing_zero_and_unknown_previous_commit_fail(self):
        self.write("scripts/publication_baseline.json", json.dumps(self.policy))
        candidate = self.save()
        script = Path(__file__).with_name("check_publication.py")
        cases = (
            ([], "missing or zero"),
            (["--before", ""], "missing or zero"),
            (["--before", "0" * 40], "missing or zero"),
            (["--before", "ab" * 20], "not in this clone"),
        )
        for extra, needle in cases:
            with self.subTest(extra=extra):
                result = subprocess.run(
                    [sys.executable, str(script), "--repo", str(self.repo),
                     "--policy", str(self.repo / "scripts/publication_baseline.json"),
                     "--target", "main", "--candidate", candidate, *extra],
                    capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn(needle, result.stderr)
                self.assertIn("cannot be skipped", result.stderr)

    def test_direct_anchor_change_without_migration_fails_for_push_and_pull_request(self):
        self.write("scripts/publication_baseline.json", json.dumps(self.policy))
        destination = self.save()
        self.write("investigations/note.txt", "unrelated\n")
        moved = self.save()
        policy = copy.deepcopy(self.policy)
        policy["branches"]["main"]["commit"] = moved
        self.write("scripts/publication_baseline.json", json.dumps(policy))
        candidate = self.save()
        for flag in ("--before", "--base-ref"):
            with self.subTest(flag=flag):
                result = subprocess.run(
                    [sys.executable, str(Path(__file__).with_name("check_publication.py")),
                     "--repo", str(self.repo),
                     "--policy", str(self.repo / "scripts/publication_baseline.json"),
                     "--target", "main", "--candidate", candidate, "--head", candidate,
                     flag, destination],
                    capture_output=True, text=True)
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("publication policy changed", result.stderr)

    def test_inconsistent_content_lock_manifest_fails(self):
        image = "assets/hero.bin"
        body = "hero-bytes\n"

        def mutate():
            self.write("README.md", "accepted overview\n\nwith a picture\n")
            self.write(image, body)
        destination = self._base_at_new_anchor(mutate)
        lock = {"path": image, "sha256": hashlib.sha256(body.encode()).hexdigest(),
                "size": len(body.encode())}
        paths = list(self.policy["branches"]["main"]["protected_paths"]) + [image]
        text = f"Benjamin authorized this test move from {self.anchor} to {destination}."
        because = f"Recorded test migration from {self.anchor} to {destination}."
        manifest = expected_manifest(
            self.repo, self.anchor, destination, paths, text, because, [], [lock])
        manifest["content_locks"][0]["new_sha256"] = "0" * 64
        policy = copy.deepcopy(self.policy)
        policy["branches"]["main"]["commit"] = destination
        policy["branches"]["main"]["protected_paths"] = paths
        policy["branches"]["main"]["content_locks"] = [lock]
        self.write("scripts/publication_baseline.json", json.dumps(policy))
        self.write("scripts/publication_migration.json", json.dumps(manifest))
        candidate = self.save()
        result = self._run_check(candidate, destination)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("manifest content_locks", result.stderr)

    def test_image_change_delete_and_replacement_fail_without_migration(self):
        image = "assets/hero.bin"
        body = "hero-bytes\n"

        def mutate():
            self.write("README.md", "accepted overview\n\nwith a picture\n")
            self.write(image, body)
        destination = self._base_at_new_anchor(mutate)
        lock = {"path": image, "sha256": hashlib.sha256(body.encode()).hexdigest(),
                "size": len(body.encode())}
        paths = list(self.policy["branches"]["main"]["protected_paths"]) + [image]
        text = f"Benjamin authorized this test move from {self.anchor} to {destination}."
        because = f"Recorded test migration from {self.anchor} to {destination}."
        manifest = expected_manifest(
            self.repo, self.anchor, destination, paths, text, because, [], [lock])
        policy = copy.deepcopy(self.policy)
        policy["branches"]["main"]["commit"] = destination
        policy["branches"]["main"]["protected_paths"] = paths
        policy["branches"]["main"]["content_locks"] = [lock]
        self.write("scripts/publication_baseline.json", json.dumps(policy))
        self.write("scripts/publication_migration.json", json.dumps(manifest))
        migrated = self.save()
        accepted = self._run_check(migrated, destination)
        self.assertEqual(accepted.returncode, 0, accepted.stderr)

        def refused(action, needle):
            action()
            candidate = self.save()
            result = self._run_check(candidate, migrated)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertIn(needle, result.stderr)
            self.git("reset", "--hard", migrated)

        refused(lambda: self.write(image, "changed-bytes\n"), "protected content mismatch")
        refused(lambda: (self.repo / image).unlink(), "protected content missing")
        refused(lambda: self.write(image, "replaced-bytes\n"), "protected content mismatch")

        replacement = "replaced-bytes\n"
        self.write(image, replacement)
        new_anchor = self.save()
        new_lock = {"path": image, "sha256": hashlib.sha256(replacement.encode()).hexdigest(),
                    "size": len(replacement.encode())}
        moved = copy.deepcopy(policy)
        moved["branches"]["main"]["commit"] = new_anchor
        moved["branches"]["main"]["content_locks"] = [new_lock]
        grant = f"Benjamin authorized this test move from {destination} to {new_anchor}."
        cause = f"Recorded test migration from {destination} to {new_anchor}."
        declared = expected_manifest(
            self.repo, destination, new_anchor, paths, grant, cause, [lock], [new_lock])
        self.write("scripts/publication_baseline.json", json.dumps(moved))
        self.write("scripts/publication_migration.json", json.dumps(declared))
        candidate = self.save()
        result = self._run_check(candidate, new_anchor)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_unknown_target_and_missing_protected_path_fail(self):
        with self.assertRaises(PublicationError):
            verify(self.repo, self.policy, "different-target")
        policy = copy.deepcopy(self.policy)
        policy["branches"]["main"]["protected_paths"].append("missing.md")
        with self.assertRaisesRegex(PublicationError, "missing from baseline"):
            verify(self.repo, policy, "main")


if __name__ == "__main__":
    unittest.main()
