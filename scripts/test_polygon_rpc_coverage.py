"""Offline regressions for claims derived from the Polygon RPC export.

Copy only the seven relevant evidence files into temporary directories.
No network calls, changes to frozen evidence or credentials are involved.
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_polygon_rpc_coverage as scan  # noqa: E402

FILES = [
    f"polygon_logs_{symbol}_{direction}.json"
    for symbol in scan.CONTRACTS for direction in ("from", "to")
] + ["g38_direct_receipts_2026-11-08.json", "g38_rpc_replay_2026-11-08.json"]


class PolygonCoverageRegressions(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.path = Path(tmp.name)
        for name in FILES:
            shutil.copyfile(scan.EVIDENCE / name, self.path / name)

    def change(self, name, mutator):
        target = self.path / name
        data = json.loads(target.read_text())
        mutator(data)
        target.write_text(json.dumps(data))

    def test_reconciliation_matches_only_recorded_logs(self):
        result = scan.audit(self.path)
        self.assertEqual(result["recorded_incoming_logs"], 53)
        self.assertEqual(result["recorded_outgoing_logs"], 30)
        self.assertEqual(result["recorded_incoming_atomic"], 1984038168550)
        self.assertEqual(result["recorded_outgoing_atomic"], 1984038168550)
        self.assertEqual(result["direct_receipts_matched"], 38)
        self.assertEqual(result["polygon_relay_receipts_matched"], 12)
        self.assertEqual(result["coverage_status"], "NOT_ESTABLISHED")

    def test_a_clean_split_counter_does_not_prove_range_coverage(self):
        for name in FILES[:4]:
            self.change(name, lambda x: x.update(failed_splits=0))
        self.assertEqual(scan.audit(self.path)["coverage_status"], "NOT_ESTABLISHED")

    def test_changed_amount_fails(self):
        def damage(x):
            x["logs"][0]["value"] = str(int(x["logs"][0]["value"]) + 1)
        self.change("polygon_logs_USDC_to.json", damage)
        with self.assertRaisesRegex(AssertionError, "totals no longer reconcile"):
            scan.audit(self.path)

    def test_missing_direct_receipt_fails(self):
        def damage(x):
            x["rows"][0]["hash"] = "0x" + "0" * 64
        self.change("g38_direct_receipts_2026-11-08.json", damage)
        with self.assertRaisesRegex(AssertionError, "direct receipt missing"):
            scan.audit(self.path)

    def test_bad_window_range_fails(self):
        self.change("polygon_logs_USDC_from.json", lambda x: x.update(start=0))
        with self.assertRaisesRegex(AssertionError, "block range changed"):
            scan.audit(self.path)

    def test_duplicate_event_fails_even_if_value_is_zero(self):
        def damage(x):
            entry = dict(x["logs"][0])
            entry["value"] = "0"
            x["logs"].append(entry)
            x["n"] += 1
        self.change("polygon_logs_USDC_to.json", damage)
        with self.assertRaisesRegex(AssertionError, "duplicate transaction log"):
            scan.audit(self.path)


if __name__ == "__main__":
    unittest.main()
