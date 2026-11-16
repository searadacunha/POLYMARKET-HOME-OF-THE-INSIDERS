"""Offline tests for C7 archive reconciliation and V2 maker-taker edge hygiene."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


c7 = module("reconcile_c7", "scripts/reconcile_c7.py")
graph = module("counterparty_graph", "scripts/counterparty_graph.py")
A, B = "0x" + "a" * 40, "0x" + "b" * 40
TX1, TX2 = "0x" + "1" * 64, "0x" + "2" * 64
EX = sorted(graph.EXCHANGES)[0]


def fill(tx=TX1, log=1, ts=100, wallet=A, counterparty=B, side="SELL", cash="10.50"):
    return {"exchange": EX, "wallet": wallet, "counterparty": counterparty,
            "tx": tx, "log_index": log, "ts": ts, "token_id": "123",
            "side": side, "cash": cash}


class ArchiveTests(unittest.TestCase):
    def test_c7_matches_committed_output(self):
        derived = c7.reconcile()
        stored = json.loads((ROOT / "results/c7_reconciled.json").read_text())
        self.assertEqual(stored, derived)
        self.assertEqual(derived["usd"], "30514.17")
        self.assertEqual(derived["shares"], "53355.91")

    def test_duplicate_archive_hash_is_rejected(self):
        text = c7.SOURCE.read_text()
        lines = text.splitlines()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "rows.csv"
            p.write_text("\n".join(lines + [lines[1]]) + "\n")
            with self.assertRaises(ValueError):
                c7.reconcile(p)


class GraphTests(unittest.TestCase):
    def test_synthetic_and_repeat_dedup(self):
        a = fill()
        synthetic = fill(log=2, wallet=B, counterparty=EX, side="BUY")
        report = graph.summarize([a, a.copy(), synthetic, fill(tx=TX2, log=3, ts=110)])
        self.assertEqual(report["ignored_synthetic_legs"], 1)
        self.assertEqual(report["unique_maker_legs"], 2)
        self.assertEqual(report["edges"][0]["distinct_transactions"], 2)
        self.assertEqual(report["edges"][0]["cash_on_maker_legs"], "21.00")
        self.assertEqual(report["edges"][0]["match_type"], "UNRESOLVED")

    def test_cutoff_prevents_future_edge(self):
        report = graph.summarize([fill(ts=100), fill(tx=TX2, log=2, ts=101)], cutoff=100)
        self.assertEqual(report["edges"][0]["fill_legs"], 1)

    def test_conflicting_duplicate_is_error(self):
        with self.assertRaises(ValueError):
            graph.summarize([fill(), fill(cash="11.00")])

    def test_contract_version_must_be_verified(self):
        with self.assertRaises(ValueError):
            graph.summarize([fill() | {"exchange": "0x" + "c" * 40}])

    def test_self_match_kept_separate(self):
        report = graph.summarize([fill(counterparty=A)])
        self.assertTrue(report["edges"][0]["self_match"])
        self.assertEqual(report["edges"][0]["maker_sell_legs"], 1)

    def test_bad_amount_fails_closed(self):
        with self.assertRaises(ValueError):
            graph.summarize([fill(cash="-1")])


if __name__ == "__main__":
    unittest.main()
