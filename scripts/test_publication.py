"""Exercise publication failures in small real Git repositories, without network."""
import copy
import subprocess
import tempfile
import unittest
from pathlib import Path

from check_publication import PublicationError, verify


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

    def test_unknown_target_and_missing_protected_path_fail(self):
        with self.assertRaises(PublicationError):
            verify(self.repo, self.policy, "different-target")
        policy = copy.deepcopy(self.policy)
        policy["branches"]["main"]["protected_paths"].append("missing.md")
        with self.assertRaisesRegex(PublicationError, "missing from baseline"):
            verify(self.repo, policy, "main")


if __name__ == "__main__":
    unittest.main()
