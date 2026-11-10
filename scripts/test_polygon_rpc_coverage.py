"""Offline regressions for claims derived from the Polygon RPC export.

Copy only the six relevant evidence files into temporary directories.
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

    def test_duplicate_direct_receipt_cannot_replace_an_expected_event(self):
        def damage(x):
            rows = x["rows"]
            for i, row in enumerate(rows):
                for j in range(i):
                    if rows[j]["proxy"].lower() == row["proxy"].lower():
                        rows[i] = dict(rows[j])
                        return
            self.fail("fixture needs one proxy with two receipts")
        self.change("g38_direct_receipts_2026-11-08.json", damage)
        with self.assertRaisesRegex(AssertionError, "duplicate direct receipt"):
            scan.audit(self.path)

    def test_duplicate_relay_order_cannot_replace_an_expected_order(self):
        def damage(x):
            indexes = [i for i, order in enumerate(x["orders"]) if order["chain"] == 137]
            x["orders"][indexes[1]] = dict(x["orders"][indexes[0]])
        self.change("g38_rpc_replay_2026-11-08.json", damage)
        with self.assertRaisesRegex(AssertionError, "duplicate Relay order"):
            scan.audit(self.path)

    def test_unregistered_order_id_is_rejected_despite_matching_receipt(self):
        def damage(x):
            next(order for order in x["orders"] if order["chain"] == 137)["id"] = "0x" + "0" * 64
        self.change("g38_rpc_replay_2026-11-08.json", damage)
        with self.assertRaisesRegex(AssertionError, "absent from original archive"):
            scan.audit(self.path)

    def test_block_match_boolean_cannot_hide_different_block_numbers(self):
        self.change("g38_direct_receipts_2026-11-08.json", lambda x: x["rows"][0].update(rpc_block=1))
        with self.assertRaisesRegex(AssertionError, "block mismatch"):
            scan.audit(self.path)

    def test_summary_does_not_certify_raw_rpc_input_or_base_receipts(self):
        result = scan.audit(self.path)
        self.assertFalse(result["order_id_binding_verified"])
        self.assertFalse(result["base_receipts_verified"])
        self.assertIn("raw RPC responses not replayed", result["rpc_proof_scope"])

    def test_a_clean_split_counter_does_not_prove_range_coverage(self):
        for name in FILES[:4]:
            self.change(name, lambda x: x.update(failed_splits=0))
        self.assertEqual(scan.audit(self.path)["coverage_status"], "NOT_ESTABLISHED")

    def test_fractional_atomic_value_is_rejected_instead_of_truncated(self):
        self.change("polygon_logs_USDC_to.json", lambda x: x["logs"][0].update(value=99800270.5))
        with self.assertRaisesRegex(AssertionError, "integer quantity"):
            scan.audit(self.path)

    def test_quantities_reject_bool_float_fraction_and_negative(self):
        for value in (True, False, 1.0, 1.5, "1.5", "1e3", "-1", -1, " 1", None):
            with self.subTest(value=value):
                with self.assertRaisesRegex(AssertionError, "integer quantity"):
                    scan.as_int(value)
        self.assertEqual(scan.as_int(0), 0)
        self.assertEqual(scan.as_int("00017"), 17)
        self.assertEqual(scan.as_int("0x11"), 17)
        self.assertEqual(scan.as_int("0XFF"), 255)

    def test_hex_log_indices_and_amounts_have_the_same_event_identity(self):
        def quantities(x):
            for row in x["logs"]:
                for field in ("block", "logIndex", "value"):
                    row[field] = hex(int(row[field]))
        for name in FILES[:4]:
            self.change(name, quantities)
        self.change("g38_direct_receipts_2026-11-08.json", lambda x: [
            row.update(logIndex=hex(row["logIndex"])) for row in x["rows"]])
        self.change("g38_rpc_replay_2026-11-08.json", lambda x: [
            row["match_log"].update(logIndex=hex(row["match_log"]["logIndex"]))
            for row in x["orders"] if row["chain"] == 137])
        self.assertEqual(scan.audit(self.path)["direct_receipts_matched"], 38)
        self.assertEqual(scan.audit(self.path)["polygon_relay_receipts_matched"], 12)

    def test_fractional_event_indices_and_boolean_receipt_counts_are_rejected(self):
        mutations = (
            ("polygon_logs_USDC_to.json", lambda x: x["logs"][0].update(logIndex=1.5)),
            ("g38_direct_receipts_2026-11-08.json", lambda x: x["rows"][0].update(logIndex=True)),
            ("g38_direct_receipts_2026-11-08.json", lambda x: x["rows"][0].update(status=True)),
            ("g38_direct_receipts_2026-11-08.json", lambda x: x["rows"][0].update(match_count=True)),
            ("g38_rpc_replay_2026-11-08.json", lambda x: next(
                row for row in x["orders"] if row["chain"] == 137).update(match_log_count=True)),
        )
        for filename, mutator in mutations:
            with self.subTest(filename=filename):
                self.change(filename, mutator)
                with self.assertRaisesRegex(AssertionError, "integer quantity"):
                    scan.audit(self.path)
                shutil.copyfile(scan.EVIDENCE / filename, self.path / filename)

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
