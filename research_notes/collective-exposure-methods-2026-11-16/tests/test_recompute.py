"""Read-only tests for descriptive interpretation and archive hygiene."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("recompute", HERE / "recompute.py")
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class CountsTests(unittest.TestCase):
    def test_reference_result_matches_archives(self):
        self.assertEqual(mod.build(), json.loads(mod.RESULT.read_text(encoding="utf-8")))

    def test_no_fake_p_value(self):
        result = mod.build()
        self.assertEqual(result["inferential_status"], "NOT_VALIDATED")
        self.assertEqual(result["cross_market_cohort"]["n"], 36)
        self.assertEqual(result["cohort"]["no_before_yes_count"], 20)
        self.assertEqual(result["comparison"]["no_before_yes_count"], 16)
        self.assertEqual(result["descriptive_ratios"]["frequency_ratio"], "25.451389")

    def test_invalid_partition_rejected(self):
        d = json.loads(mod.JSON_SOURCE.read_text())
        d["counts"]["cohort"]["yes_buy_only"] += 1
        with tempfile.TemporaryDirectory() as temp:
            altered = Path(temp) / "source.json"
            altered.write_text(json.dumps(d))
            with self.assertRaises(ValueError):
                mod.build(source=altered)

    def test_unproven_source_redefinition_rejected(self):
        d = json.loads(mod.JSON_SOURCE.read_text())
        d["definition"]["no_before_yes"] = "a reconstructed full inventory reversal"
        with tempfile.TemporaryDirectory() as temp:
            altered = Path(temp) / "source.json"
            altered.write_text(json.dumps(d))
            with self.assertRaises(ValueError):
                mod.build(source=altered)

    def test_sampled_clock_window_is_not_all_36_wallets(self):
        r = mod.build()
        self.assertEqual(r["first_yes_clock_window"]["cohort_in_window"], 6)
        self.assertEqual(r["first_yes_clock_window"]["cohort_first_yes_buyers"], 35)


if __name__ == "__main__":
    unittest.main()
