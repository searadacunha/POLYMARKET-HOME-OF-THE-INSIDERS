"""Small tests of verify.py: each check passes on the committed data and fails on a planted defect. Offline."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify  # noqa: E402

DATA, META = verify.load()


class Checks(unittest.TestCase):
    def test_render_is_stable_and_counts_match(self):
        report = verify.render(DATA, META)
        self.assertEqual(report, verify.render(copy.deepcopy(DATA), META))
        self.assertEqual(verify.check_result_counts(DATA, report), [])

    def test_changed_position_breaks_quoted_counts(self):
        report = verify.render(DATA, META)
        d = copy.deepcopy(DATA)
        d["capabilities"][0]["position"] = "ahead"
        self.assertTrue(verify.check_result_counts(d, report))

    def test_unknown_competitor_path_is_reported(self):
        d = copy.deepcopy(DATA)
        d["repos"][0]["strengths"][0]["theirs"] = ["no/such/file.py"]
        self.assertTrue(any("no/such/file.py" in b for b in verify.check_their_paths(d, META)))
        self.assertEqual(verify.check_their_paths(DATA, META), [])

    def test_missing_our_path_and_short_commit_are_reported(self):
        d = copy.deepcopy(DATA)
        d["blockers"][0]["ours"] = ["no/such/path.md"]
        self.assertEqual(verify.check_our_paths(d), ["no/such/path.md"])
        m = copy.deepcopy(META)
        m["repos"][DATA["repos"][0]["name"]]["head"]["sha"] = "afe554b154"
        self.assertEqual(verify.check_commits(DATA, m), [DATA["repos"][0]["name"]])

    def test_statement_without_our_evidence_is_reported(self):
        d = copy.deepcopy(DATA)
        d["repos"][1]["defects"][0]["ours"] = []
        self.assertEqual(len(verify.check_both_sides(d)), 1)

    def test_recount_detects_a_wrong_expected_value(self):
        d = copy.deepcopy(DATA)
        d["our_counts"][2]["expected"] = 46
        self.assertEqual(len(verify.check_our_counts(d)), 1)
        self.assertEqual(verify.check_our_counts(DATA), [])


if __name__ == "__main__":
    unittest.main()
