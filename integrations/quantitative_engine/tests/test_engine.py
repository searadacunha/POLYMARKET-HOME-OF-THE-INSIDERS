"""Offline tests. No network and no third-party package."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alerts import promote
from contracts import poly_data_v2_claim
from executions import economic_executions, inspect_poly_data_csv_row
from microstructure import score_events
from replay import replay_all
from validation import evaluate, fisher_greater


def _log(index, maker, taker, maker_asset, taker_asset, maker_amount, taker_amount, tx="0x" + "ab" * 32):
    return {
        "protocol_variant": "CTF_EXCHANGE_V2",
        "timestamp_utc": "2026-05-01T00:00:00Z",
        "contract": "0xe111180000d2663c0091e4f400237545b87b996b",
        "chain_id": 137,
        "transaction_hash": tx,
        "log_index": index,
        "maker": maker,
        "taker": taker,
        "maker_asset": maker_asset,
        "taker_asset": taker_asset,
        "maker_amount": maker_amount,
        "taker_amount": taker_amount,
    }


class ExecutionTests(unittest.TestCase):
    def test_mirrored_fill_is_one_execution(self):
        maker = "0x" + "11" * 20
        taker = "0x" + "22" * 20
        logs = [
            _log(1, maker, taker, "0", "999", 5_000_000, 10_000_000),
            _log(2, taker, maker, "999", "0", 10_000_000, 5_000_000),
        ]
        found = economic_executions(logs)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["views"], 2)
        self.assertEqual(found[0]["notional_usdc_raw"], 5_000_000)
        self.assertEqual(found[0]["log_indexes"], [1, 2])

    def test_pre_migration_v2_claim_is_refused(self):
        self.assertEqual(
            poly_data_v2_claim("2026-02-01T00:00:00Z", "0xe111180000d2663c0091e4f400237545b87b996b"),
            "BEFORE_V1_CUTOVER_NOT_COVERED",
        )
        row = _log(1, "0x" + "11" * 20, "0x" + "22" * 20, "0", "9", 1, 1)
        row["timestamp_utc"] = "2026-01-15T00:00:00Z"
        with self.assertRaises(ValueError):
            economic_executions([row])

    def test_neg_risk_is_not_called_poly_data_coverage(self):
        self.assertEqual(
            poly_data_v2_claim("2026-06-01T00:00:00Z", "0xe2222d279d744050d28e00520010520000310f59"),
            "NEG_RISK_NOT_IN_POLY_DATA",
        )

    def test_csv_row_without_log_index_is_not_an_execution(self):
        inspected = inspect_poly_data_csv_row({"timestamp_utc": "2026-06-01T00:00:00Z"})
        self.assertIsNone(inspected["economic_execution"])
        self.assertFalse(inspected["wallet_identified"])

    def test_exchange_taker_is_not_a_wallet(self):
        maker = "0x" + "11" * 20
        exchange = "0xe111180000d2663c0091e4f400237545b87b996b"
        found = economic_executions([
            _log(4, maker, exchange, "0", "999", 1, 2),
        ])
        self.assertIsNone(found[0]["taker"]["wallet"])
        self.assertEqual(found[0]["taker"]["role"], "EXCHANGE_CONTRACT")
        self.assertTrue(found[0]["unpaired"])


class BookTests(unittest.TestCase):
    def test_future_book_does_not_change_the_signal(self):
        events = [
            {"kind": "BOOK", "asset": "A", "market": "M", "ts": 0, "ordinal": 1,
             "bids": [(4000, 100_000_000)], "asks": [(6000, 100_000_000)]},
            {"kind": "PRINT", "asset": "A", "market": "M", "ts": 1_000, "ordinal": 2,
             "side": "BUY", "price": 6000, "size": 80_000_000, "tx": "TX1", "split": "validation",
             "hour": "h", "category": "c"},
            {"kind": "BOOK", "asset": "A", "market": "M", "ts": 5_000, "ordinal": 3,
             "bids": [(1000, 1)], "asks": [(9000, 1)]},
            {"kind": "QUOTE", "asset": "A", "market": "M", "ts": 61_000, "ordinal": 4,
             "best_bid": 7000, "best_ask": 8000},
        ]
        scored = score_events(events)
        self.assertEqual(len(scored), 1)
        self.assertEqual(scored[0]["spread_1e4"], 2000)
        self.assertEqual(scored[0]["depth_1e6"], 100_000_000)
        self.assertIsNone(scored[0]["wallet"])
        self.assertFalse(scored[0]["chain_receipt_checked"])
        self.assertTrue(scored[0]["moved"])

    def test_quote_inside_the_embargo_is_not_the_outcome(self):
        events = [
            {"kind": "BOOK", "asset": "A", "market": "M", "ts": 0, "ordinal": 1,
             "bids": [(4000, 10)], "asks": [(4200, 10)]},
            {"kind": "PRINT", "asset": "A", "market": "M", "ts": 1_000, "ordinal": 2,
             "side": "BUY", "price": 4200, "size": 10, "tx": "TX2", "split": "validation"},
            {"kind": "QUOTE", "asset": "A", "market": "M", "ts": 50_000, "ordinal": 3,
             "best_bid": 9000, "best_ask": 9100},
        ]
        scored = score_events(events)
        self.assertIsNone(scored[0]["moved"])
        self.assertIsNone(scored[0]["outcome_mid_1e4"])

    def test_same_transaction_print_is_not_counted_twice(self):
        book = {"kind": "BOOK", "asset": "A", "market": "M", "ts": 0, "ordinal": 1,
                "bids": [(4000, 10)], "asks": [(5000, 10)]}
        first = {"kind": "PRINT", "asset": "A", "market": "M", "ts": 10, "ordinal": 2,
                 "side": "BUY", "price": 5000, "size": 1, "tx": "SAME", "split": "discovery"}
        second = dict(first, ordinal=3)
        self.assertEqual(len(score_events([book, first, second])), 1)


class ValidationTests(unittest.TestCase):
    def _row(self, moved, consumption, spread, gap, split="validation", size=50_000_000):
        return {
            "split": split,
            "eligible_size": size >= 50_000_000,
            "moved": moved,
            "consumption": consumption,
            "spread_1e4": spread,
            "burst_gap_ms": gap,
            "side": "BUY",
            "asset": "A",
            "tx": None,
            "ts": 0,
            "wallet": None,
            "object_kind": "VENUE_PRINT",
            "market": "M",
        }

    def test_planted_difference_passes_and_null_does_not(self):
        planted = [self._row(True, "0.8", 500, None) for _ in range(12)]
        planted += [self._row(False, "0.1", 100, None) for _ in range(12)]
        result = evaluate(planted)
        self.assertEqual(result["tests"]["H1_DEPTH_CONSUMPTION"]["decision"], "PASSES_VALIDATION")
        self.assertIsNone(result["insider_probability"])
        null = [self._row(i < 6, "0.8", 500, None) for i in range(12)]
        null += [self._row(i < 6, "0.1", 100, None) for i in range(12)]
        self.assertEqual(evaluate(null)["tests"]["H1_DEPTH_CONSUMPTION"]["decision"], "REJECTED")

    def test_small_arms_stay_underpowered(self):
        rows = [self._row(True, "0.9", 500, None), self._row(False, "0.1", 100, None)]
        self.assertEqual(evaluate(rows)["tests"]["H1_DEPTH_CONSUMPTION"]["decision"], "UNDERPOWERED")

    def test_fisher_rejects_a_non_extreme_table(self):
        self.assertGreater(fisher_greater(5, 5, 5, 5), 0.05 / 3)

    def test_failed_pattern_does_not_emit_an_alert(self):
        rows = [self._row(True, "0.9", 500, 1000) for _ in range(4)]
        evaluation = evaluate(rows)
        report = promote(rows, evaluation, "ARCHIVE_HOURLY")
        self.assertEqual(report["emitted"], [])
        self.assertFalse(report["live_claim"])
        self.assertGreater(report["withheld"], 0)

    def test_historical_windows_are_not_claimed_as_v2(self):
        found = {item["case_id"]: item for item in replay_all(())}
        self.assertEqual(found["maduro"]["poly_data_v2"], "NO_POLY_DATA_V2_COVERAGE")
        self.assertEqual(found["maduro"]["conclusion_change"], "NO_NEW_DATA_ON_THIS_CASE")
        self.assertFalse(found["maduro"]["new_wallet_link"])
        self.assertFalse(any(item["downloaded_for_this_case"] for item in found["iran"]["pendulum"]))
        self.assertEqual(found["ballon_dor_2026"]["conclusion_change"], "NO_NEW_DATA_ON_THIS_CASE")
        self.assertEqual(found["kpmg_documentary"]["poly_data_v2"], "WINDOW_CROSSES_CUTOVER_NOT_CLAIMED")
        iran_v1 = next(item for item in found["iran"]["pendulum"] if item["era"] == "pmxt_v1")
        self.assertTrue(iran_v1["calendar_overlap"])
        self.assertFalse(iran_v1["downloaded_for_this_case"])
        self.assertFalse(iran_v1["can_identify_wallet"])


if __name__ == "__main__":
    unittest.main()
