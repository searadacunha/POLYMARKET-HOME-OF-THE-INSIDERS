"""Regression tests for cohort, outcome-rule and cutoff boundaries."""

import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location("kpmg_descriptive_verify", Path(__file__).with_name("verify.py"))
VERIFY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFY)


def row(**overrides):
    result = {
        "condition_id": "condition-a", "accounts": "alice|bob",
        "account_sides": "No|Yes", "main_side": "Yes", "winner": "Yes",
        "main_side_won": "True", "every_account_side_won": "False",
        "cutoff": "SEC_ITEM_2.02", "sec_item202_acceptance_utc": "2026-01-13T11:30:39+00:00",
        "ticker": "EXAMPLE", "slug": "example-earnings", "p_main_side_cost_weighted": "0.81",
    }
    result.update(overrides)
    return result


class DescriptiveBoundaryTests(unittest.TestCase):
    def test_opposed_account_sides_are_not_one_bernoulli_win_event(self):
        result = VERIFY.describe([row()], {"alice", "bob"})
        self.assertEqual(result["aggregate_main_side_wins"], 1)
        self.assertEqual(result["unanimous_account_main_side_wins"], 0)
        opposed = result["opposed_account_main_sides"][0]
        self.assertFalse(opposed["all_account_main_sides_can_win"])
        self.assertEqual(opposed["archived_main_side_reference_price"], "0.81")

    def test_claimed_unanimous_win_with_opposed_sides_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "account-main-side outcome"):
            VERIFY.describe([row(every_account_side_won="True")], {"alice", "bob"})

    def test_duplicate_market_cannot_inflate_sample_size(self):
        with self.assertRaisesRegex(ValueError, "duplicate condition"):
            VERIFY.describe([row(), row()], {"alice", "bob"})

    def test_expanded_account_cannot_leak_into_core_cohort(self):
        with self.assertRaisesRegex(ValueError, "outside its cohort"):
            VERIFY.describe([row(accounts="alice|expanded-account")], {"alice", "bob"})

    def test_market_close_fallback_is_counted_separately(self):
        result = VERIFY.describe([
            row(cutoff="MARKET_CLOSE", sec_item202_acceptance_utc="")
        ], {"alice", "bob"})
        self.assertEqual(result["cutoffs"], {"MARKET_CLOSE": 1})
        self.assertEqual(len(result["market_close_fallbacks"]), 1)

    def test_missing_sec_timestamp_cannot_be_reported_as_sec_cutoff(self):
        with self.assertRaisesRegex(ValueError, "SEC cutoff"):
            VERIFY.describe([row(sec_item202_acceptance_utc="")], {"alice", "bob"})

    def test_nan_price_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "reference price"):
            VERIFY.describe([row(p_main_side_cost_weighted="NaN")], {"alice", "bob"})

    def test_real_cohorts_and_rule_counts_remain_separate(self):
        cohorts = VERIFY.build_summary()["cohorts"]
        self.assertEqual(cohorts["core19"]["accounts_in_scope"], 19)
        self.assertEqual(cohorts["all22"]["accounts_in_scope"], 22)
        self.assertEqual(cohorts["core19"]["unanimous_account_main_side_wins"], 18)
        self.assertEqual(cohorts["all22"]["unanimous_account_main_side_wins"], 17)
        self.assertEqual(len(cohorts["core19"]["opposed_account_main_sides"]), 2)
        self.assertEqual(len(cohorts["all22"]["opposed_account_main_sides"]), 3)


if __name__ == "__main__":
    unittest.main()
