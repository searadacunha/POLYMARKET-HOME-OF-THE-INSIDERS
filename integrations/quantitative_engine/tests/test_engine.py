"""Offline tests. No network and no third-party package."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from alerts import promote
from inca_tape import prejump
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


class BehaviorTests(unittest.TestCase):
    def test_volume_needs_three_quiet_hours(self):
        from behavior import alerts_at
        rows = [{"t": 10_000, "w": "0x" + "11" * 20, "side": "BUY", "outcome": "Yes", "size": 10000, "price": 0.2, "tx": "a"}]
        self.assertFalse(alerts_at(rows, 10_000)["volume"])
        quiet = [{"t": 10_000 - 4 * 3600, "w": "0x" + "22" * 20, "side": "BUY", "outcome": "Yes", "size": 1, "price": 0.2, "tx": "b"}]
        self.assertTrue(alerts_at(quiet + rows, 10_000)["volume"])

    def test_two_sided_wallet_is_not_a_fresh_position(self):
        from behavior import alerts_at
        wallet = "0x" + "33" * 20
        rows = [
            {"t": 100, "w": wallet, "side": "BUY", "outcome": "Yes", "size": 5000, "price": 0.4, "tx": "a"},
            {"t": 200, "w": wallet, "side": "SELL", "outcome": "Yes", "size": 5000, "price": 0.4, "tx": "b"},
        ]
        flags = alerts_at(rows, 200)
        self.assertFalse(flags["new_wallet"])
        self.assertFalse(flags["concentration"])
        self.assertFalse(flags["sync"])

    def test_three_buyers_in_the_same_minute_sync(self):
        from behavior import alerts_at
        rows = []
        for index in range(3):
            rows.append({
                "t": 500, "w": "0x" + f"{index + 1:02x}" * 20, "side": "BUY",
                "outcome": "Yes", "size": 1000, "price": 0.3, "tx": str(index),
            })
        self.assertTrue(alerts_at(rows, 500)["sync"])


class TradeScoreTests(unittest.TestCase):
    def test_incomplete_tape_is_excluded_and_a_market_counts_once(self):
        import json
        import tempfile
        from pathlib import Path
        from score_trades import score_dir
        origin = 1_700_000_000
        series = [[origin + index * 1800, 0.20 if index < 16 else 0.45] for index in range(20)]
        wallet = "0x" + "44" * 20
        buy = {"t": origin + 1800, "w": wallet, "side": "BUY", "outcome": "Yes", "size": 5000, "price": 0.2, "tx": "a"}
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            trades = root / "trades"
            trades.mkdir()
            (root / "series.jsonl").write_text(json.dumps({"condition_id": "0xabc", "series": series}) + "\n", encoding="utf-8")
            (trades / "0xabc.json").write_text(json.dumps({
                "condition_id": "0xabc", "split": "discovery", "complete": True, "rows": [buy],
            }), encoding="utf-8")
            (trades / "0xdef.json").write_text(json.dumps({
                "condition_id": "0xdef", "split": "discovery", "complete": False,
                "rows": [dict(buy, size=100000, tx="nope")],
            }), encoding="utf-8")
            report = score_dir(trades, root / "series.jsonl")
        self.assertEqual(report["coverage"]["discovery"]["incomplete"], 1)
        self.assertEqual(report["coverage"]["discovery"]["complete"], 1)
        level = report["market_level"]["discovery"]["new_wallet"]["24h"]
        self.assertEqual(level["markets_alerting"], 1)
        self.assertGreater(report["splits"]["discovery"]["new_wallet"]["24h"]["alerts"], 1)


class CollectorTests(unittest.TestCase):
    def test_dedup_and_status_do_not_claim_a_permanent_monitor(self):
        import json
        import tempfile
        from pathlib import Path
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo))
        from monitoring.livecollect.__main__ import Seen, status
        seen = Seen(limit=2)
        self.assertTrue(seen.add("a"))
        self.assertFalse(seen.add("a"))
        self.assertTrue(seen.add("b"))
        self.assertTrue(seen.add("c"))
        self.assertNotIn("a", seen.tail())
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / "state.json").write_text(json.dumps({"seen": [], "started": 1000, "restarts": 2}), encoding="utf-8")
            (out / "heartbeats.jsonl").write_text('{"t": 1000}\n{"t": 1010}\n{"t": 1040}\n', encoding="utf-8")
            report = status(out)
        self.assertFalse(report["permanent"])
        self.assertEqual(report["restarts"], 2)
        self.assertEqual(report["observed_online_s"], 10.0)
        self.assertEqual(report["observed_wall_s"], 40.0)
        self.assertEqual(report["max_gap_s"], 30.0)
        self.assertEqual(report["polls_complete"], 0)
        self.assertEqual(report["new_trades_after_start"], 0)


def _trade(stamp, tx_hash, wallet="0x" + "ab" * 20):
    return {
        "timestamp": stamp,
        "transaction_hash": tx_hash,
        "proxy_wallet": wallet,
        "side": "BUY",
        "size": 1,
        "price": 0.4,
        "outcome": "Yes",
    }


class TradePollTests(unittest.TestCase):
    def _walk(self, pages, mark, seen, floor=0, page_cap=4):
        from monitoring.livecollect.trades import trade_key, walk_trades
        seen_keys = {trade_key(row) for row in seen}

        def fetch(cursor):
            return pages[cursor]

        result = walk_trades(fetch, mark, lambda key: key in seen_keys, floor, page_cap)
        return result

    def test_pagination_stops_at_the_high_water_mark(self):
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo))
        pages = {
            None: {"data": [_trade(300, "a"), _trade(200, "b")], "has_more": True, "next_cursor": "p2"},
            "p2": {"data": [_trade(150, "c"), _trade(140, "seen"), _trade(120, "missed"), _trade(100, "old")], "has_more": True, "next_cursor": "p3"},
        }
        result = self._walk(pages, {"t": 100, "tx": "old"}, [_trade(140, "seen")])
        self.assertEqual([row["transaction_hash"] for row in result["rows"]], ["a", "b", "c", "missed"])
        self.assertTrue(result["complete"])
        self.assertEqual(result["mark"]["t"], 300)
        self.assertEqual(result["mark"]["tx"], "a")
        self.assertIsNone(result["mark"]["cursor"])
        self.assertEqual(result["pages"], 2)

    def test_restart_resumes_the_high_water_mark(self):
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo))
        import json
        from monitoring.livecollect.trades import gap_row
        first = self._walk(
            {None: {"data": [_trade(300, "a"), _trade(100, "old")], "has_more": False, "next_cursor": None}},
            {"t": 100, "tx": "old"},
            [],
        )
        stored = json.loads(json.dumps(first["mark"]))
        second = self._walk(
            {None: {"data": [_trade(300, "a"), _trade(50, "older")], "has_more": True, "next_cursor": "more"}},
            stored,
            [_trade(300, "a")],
        )
        self.assertEqual(second["rows"], [])
        self.assertTrue(second["complete"])
        self.assertEqual(second["mark"]["t"], 300)
        self.assertEqual(second["pages"], 1)
        self.assertIsNone(gap_row("m", second, 400, 0))

    def test_page_cap_is_a_gap_and_the_next_poll_continues(self):
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo))
        from monitoring.livecollect.trades import gap_row
        pages = {
            None: {"data": [_trade(50, "n1")], "has_more": True, "next_cursor": "c1"},
            "c1": {"data": [_trade(40, "n2")], "has_more": True, "next_cursor": "c2"},
            "c2": {"data": [_trade(30, "n3"), _trade(1, "old")], "has_more": False, "next_cursor": None},
        }
        first = self._walk(pages, {"t": 1, "tx": "old"}, [], page_cap=2)
        self.assertFalse(first["complete"])
        self.assertEqual(first["mark"]["t"], 1)
        self.assertEqual(first["mark"]["cursor"], "c2")
        self.assertEqual([row["transaction_hash"] for row in first["rows"]], ["n1", "n2"])
        gap = gap_row("market", first, 100, 0)
        self.assertEqual(gap["kind"], "trade_page_cap")
        self.assertEqual(gap["pages"], 2)
        continued = {
            None: {"data": [_trade(60, "n0"), _trade(50, "n1")], "has_more": True, "next_cursor": "head"},
            "c2": pages["c2"],
        }
        seen = [_trade(50, "n1"), _trade(40, "n2")]
        second = self._walk(continued, first["mark"], seen, page_cap=4)
        self.assertEqual([row["transaction_hash"] for row in second["rows"]], ["n0", "n3"])
        self.assertTrue(second["complete"])
        self.assertEqual(second["mark"]["t"], 60)
        self.assertIsNone(second["mark"]["cursor"])

    def test_receipt_queue_dedups_and_survives_a_restart(self):
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo))
        from monitoring.livecollect.trades import ReceiptQueue
        queue = ReceiptQueue()
        self.assertTrue(queue.add("0xabc"))
        self.assertFalse(queue.add("0xabc"))
        self.assertEqual(queue.pop(), "0xabc")
        queue.ack("0xabc")
        self.assertFalse(queue.add("0xabc"))
        restored = ReceiptQueue(["0xdef", "0xdef"], {"0xabc"})
        self.assertFalse(restored.add("0xabc"))
        self.assertFalse(restored.add("0xdef"))
        self.assertEqual(restored.pop(), "0xdef")
        self.assertIsNone(restored.pop())


class MarketDecodeTests(unittest.TestCase):
    def test_real_price_change_fills_each_level_and_rebuilds_the_book(self):
        import json
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo))
        from monitoring.livecollect.decode import apply_levels, best_price, book_from_row, decode_market
        fixture = json.loads((repo / "monitoring/livecollect/fixtures/market_messages.json").read_text(encoding="utf-8"))
        books, problems = decode_market(fixture["book"])
        self.assertEqual(problems, [])
        self.assertTrue(books[0]["bids"] and books[0]["asks"])
        state = book_from_row(books[0])
        asset = books[0]["asset_id"]
        applied = 0
        saw_reduced_ask = False
        for message in fixture["price_changes"]:
            rows, problems = decode_market(message)
            self.assertEqual(problems, [])
            self.assertGreaterEqual(len(rows), 1)
            for row in rows:
                self.assertTrue(row["asset_id"] and row["price"] and row["size"] and row["side"])
                self.assertEqual(row["market"], message["market"])
                self.assertEqual(row["timestamp"], message["timestamp"])
                if row["asset_id"] != asset:
                    continue
                state = apply_levels(state, row)
                applied += 1
                self.assertEqual(best_price(state["bids"], True), row["best_bid"])
                self.assertEqual(best_price(state["asks"], False), row["best_ask"])
                if row["price"] == "0.6" and row["size"] == "10151.81":
                    saw_reduced_ask = state["asks"].get("0.6") == "10151.81"
        self.assertTrue(saw_reduced_ask)
        self.assertGreaterEqual(applied, 3)
        self.assertNotIn("0.134", state["asks"])
        self.assertEqual(state["asks"].get("0.6"), "16401.81")

    def test_flat_price_change_still_decodes_and_empty_message_is_logged(self):
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo))
        from monitoring.livecollect.decode import decode_market
        flat = {"event_type": "price_change", "market": "0xabc", "asset_id": "9", "price": "0.2", "size": "3", "side": "BUY", "timestamp": "10"}
        rows, problems = decode_market(flat)
        self.assertEqual(problems, [])
        self.assertEqual(rows[0]["price"], "0.2")
        empty = {"event_type": "price_change", "market": "0xabc", "price_changes": [], "timestamp": "10"}
        rows, problems = decode_market(empty)
        self.assertEqual(rows, [])
        self.assertEqual(problems[0]["reason"], "empty_price_changes")

    def test_order_filled_pair_is_confirmed_and_a_stranger_is_not(self):
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo))
        from monitoring.livecollect.decode import attribute_trade, decode_logs
        wallet = "0x" + "11" * 20
        other = "0x" + "22" * 20
        exchange = "0xe2222d279d744050d28e00520010520000310f59"
        token = "54533043819946592547517511176940999955633860128497669742211153063842200957669"
        logs = [
            _fill(0, wallet, other, 0, token, 698880, 7280000, 0),
            _fill(1, wallet, exchange, 1, token, 7280000, 698880, 25270),
            _transfer(wallet, 698880),
        ]
        decoded = decode_logs(logs)
        self.assertEqual(decoded["fills"][0]["exchange"], exchange)
        self.assertTrue(decoded["fills"][0]["asset_ids_derived"])
        self.assertEqual(decoded["fills"][0]["token_id"], token)
        self.assertIn("v2_order_filled", decoded["families"])
        trade = {"wallet": wallet, "asset_id": token, "size": 7.28}
        found = attribute_trade(trade, decoded)
        self.assertEqual(found["status"], "confirmed")
        self.assertEqual(found["reason"], "paired_fills")
        stranger = attribute_trade({"wallet": "0x" + "33" * 20, "asset_id": token, "size": 7.28}, decoded)
        self.assertEqual(stranger["status"], "not_found")
        missing = attribute_trade({"wallet": wallet, "asset_id": token}, decoded)
        self.assertEqual(missing["status"], "ambiguous")
        self.assertEqual(missing["reason"], "trade_fields_missing")

    def test_recorded_last_trade_keeps_fee_and_size(self):
        import json
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo))
        from monitoring.livecollect.decode import decode_market
        message = json.loads((repo / "monitoring/livecollect/fixtures/last_trade_price.json").read_text(encoding="utf-8"))["message"]
        rows, problems = decode_market(message)
        self.assertEqual(problems, [])
        self.assertEqual(rows[0]["price"], message["price"])
        self.assertEqual(rows[0]["size"], message["size"])
        self.assertEqual(rows[0]["side"], message["side"])
        self.assertEqual(rows[0]["fee_rate_bps"], "0")
        self.assertEqual(rows[0]["asset_id"], message["asset_id"])
        self.assertEqual(rows[0]["timestamp"], message["timestamp"])

    def test_disk_alert_uses_the_documented_thresholds(self):
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo))
        from monitoring.livecollect.decode import disk_report
        self.assertFalse(disk_report(13_000_000_000, int(13_000_000_000 / 0.06))["disk_alert"])
        self.assertTrue(disk_report(4_000_000_000, 100_000_000_000)["disk_alert"])
        self.assertTrue(disk_report(6_000_000_000, int(6_000_000_000 / 0.03))["disk_alert"])


def _topic_addr(address: str) -> str:
    return "0x" + "0" * 24 + address[2:]


def _word(value: int) -> str:
    return format(value, "064x")


def _fill(index, maker, taker, side, token, maker_amount, taker_amount, fee):
    data = "0x" + "".join(_word(item) for item in (side, int(token), maker_amount, taker_amount, fee, 0, 0))
    return {
        "address": "0xe2222d279d744050d28e00520010520000310f59",
        "topics": [
            "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee",
            "0x" + "ab" * 32,
            _topic_addr(maker),
            _topic_addr(taker),
        ],
        "data": data,
        "logIndex": hex(index),
    }


def _transfer(wallet, amount):
    return {
        "address": "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb",
        "topics": [
            "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef",
            _topic_addr("0xe2222d279d744050d28e00520010520000310f59"),
            _topic_addr(wallet),
        ],
        "data": "0x" + _word(amount),
        "logIndex": "0x10",
    }


class CoverageTests(unittest.TestCase):
    def test_missing_series_is_not_a_quiet_market(self):
        from pass4 import coverage
        self.assertEqual(coverage(None, 3600), "missing")
        self.assertEqual(coverage([], 3600), "missing")
        short = [(0, 0.1), (1000, 0.1)]
        self.assertEqual(coverage(short, 48 * 3600), "unusable_window")


class PopulationTests(unittest.TestCase):
    def test_sample_is_seeded_and_stratified(self):
        from population import sample_frame
        frame = []
        for split in ("discovery", "validation"):
            for category in ("geopolitics", "sports"):
                for liquidity in ("ordinary", "high"):
                    for index in range(5):
                        frame.append({
                            "split": split, "category": category, "liquidity": liquidity,
                            "condition_id": f"{split}-{category}-{liquidity}-{index}",
                            "end": "2026-01-01T00:00:00Z",
                        })
        first = [row["condition_id"] for row in sample_frame(frame, per_cell=2, seed=20261113)]
        second = [row["condition_id"] for row in sample_frame(frame, per_cell=2, seed=20261113)]
        self.assertEqual(first, second)
        self.assertEqual(len(first), 16)
        self.assertNotEqual(first, [row["condition_id"] for row in sample_frame(frame, per_cell=2, seed=1)])


class MonitorTests(unittest.TestCase):
    def test_frozen_monitor_selftests(self):
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo))
        from monitoring.phi_monitor import ignition, tapefeat
        ignition._selftest()
        tapefeat._selftest()


class TapeTests(unittest.TestCase):
    def test_jump_ignores_the_cohort_and_future_buys(self):
        early = "0x" + "11" * 20
        other = "0x" + "22" * 20
        rows = [
            {"proxy_wallet": early, "outcome": "Yes", "side": "BUY", "price": 0.2, "size": 100, "timestamp": 10},
            {"proxy_wallet": other, "outcome": "Yes", "side": "BUY", "price": 0.2, "size": 10, "timestamp": 11},
            {"proxy_wallet": early, "outcome": "Yes", "side": "BUY", "price": 0.9, "size": 10, "timestamp": 50},
            {"proxy_wallet": other, "outcome": "Yes", "side": "BUY", "price": 0.95, "size": 1000, "timestamp": 60},
        ]
        found = prejump(rows, {early: "named"})
        self.assertEqual(found["jump_timestamp"], 50)
        self.assertEqual(found["prejump_wallets"], 2)
        self.assertEqual(found["cohort"][0]["prejump_notional"], 20.0)
        self.assertFalse(found["prospective_detector"])


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


class WebSocketFrameTests(unittest.TestCase):
    def test_every_message_in_batched_frame_is_decoded(self):
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo))
        from monitoring.livecollect.decode import decode_frame
        msg1 = {"event_type": "price_change", "market": "0xabc", "price_changes": [
            {"asset_id": "YES", "price": "0.40", "size": "100", "side": "BUY"},
            {"asset_id": "NO", "price": "0.60", "size": "50", "side": "SELL"}]}
        msg2 = {"event_type": "book", "market": "0xabc", "asset_id": "YES",
                "bids": [{"price": "0.40", "size": "100"}],
                "asks": [{"price": "0.42", "size": "200"}]}
        parsed = list(decode_frame([msg1, msg2, None]))
        self.assertEqual(len(parsed), 2)
        self.assertEqual([r["asset_id"] for r in parsed[0][1]], ["YES", "NO"])
        self.assertEqual(parsed[1][1][0]["bids"][0]["size"], "100")
        self.assertEqual(parsed[0][2], [])
        self.assertEqual(parsed[1][2], [])

    def test_single_and_empty_frame(self):
        repo = Path(__file__).resolve().parents[3]
        sys.path.insert(0, str(repo))
        from monitoring.livecollect.decode import decode_frame
        self.assertEqual(list(decode_frame([])), [])
        self.assertEqual(list(decode_frame([None])), [])
        msg = {"event_type": "last_trade_price", "asset_id": "YES", "price": "0.5"}
        self.assertEqual(len(list(decode_frame(msg))), 1)
