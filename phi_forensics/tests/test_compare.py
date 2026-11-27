"""Overlap of trading wallets on small hand-built activity, the co-timing null, and the loader of the legacy null model."""
import sys
import unittest
from unittest import mock

from phi_forensics import _legacy, compare

A, B, C = ("0x" + c * 40 for c in "abc")
M1, M2, M3 = ("0x" + c * 64 for c in "123")


def row(kind, side, market, index, size, cash, ts, tx):
    return {"type": kind, "side": side, "condition_id": market, "token_id": f"{index}{market[-4:]}", "outcome": ("Yes", "No")[index],
            "outcome_index": index, "size": size, "usdc_size": cash, "timestamp": ts, "transaction_hash": "0x" + f"{tx:064x}", "title": "t"}


ACTIVITY = {
    A: [row("TRADE", "BUY", M1, 0, 100, 40, 1000, 1), row("TRADE", "BUY", M1, 0, 1, 1.01, 2000, 4), row("TRADE", "BUY", M2, 1, 10, 5, 5000, 2),
        row("REDEEM", "", M1, 0, 101, 101, 9000, 9)],
    B: [row("TRADE", "BUY", M1, 0, 50, 20, 1030, 3), row("TRADE", "BUY", M2, 1, 20, 8, 5500, 2), row("TRADE", "SELL", M2, 1, 20, 9, 6000, 5),
        row("TRADE", "BUY", M3, 0, 5, 2, 7000, 6)],
    C: [row("TRADE", "BUY", M3, 1, 5, 2, 7010, 7)],
}


class Fake:
    def __init__(self, activity=ACTIVITY, incomplete=()):
        self.activity_rows, self.incomplete, self.asked = activity, incomplete, []

    def activity(self, wallet, start=None, end=None, kind=None, max_rows=200_000):
        self.asked.append((wallet, max_rows))
        return {"rows": self.activity_rows[wallet], "complete": wallet not in self.incomplete, "pages": 1}


def counts(pair):
    return (pair["a"], pair["b"], pair["markets_both_count"], pair["jaccard"], len(pair["same_side_net_buys"]), pair["bought_within_60s"],
            pair["bought_within_600s"], pair["shared_transactions"]["count"])


class Compare(unittest.TestCase):
    def test_pair_overlap_counts(self):
        fake = Fake()
        got = compare.compare_traders(fake, [A.upper().replace("0X", "0x"), B, C], max_rows=700)
        self.assertEqual(fake.asked, [(A, 700), (B, 700), (C, 700)])
        self.assertEqual([counts(p) for p in got["pairs"]],
                         [(A, B, 2, 0.666667, 1, 1, 2, 1), (A, C, 0, 0.0, 0, 0, 0, 0), (B, C, 1, 0.333333, 0, 0, 0, 0)])
        ab = got["pairs"][0]
        self.assertEqual(ab["markets_both"], [M1, M2])
        self.assertEqual(ab["same_side_net_buys"], [{"condition_id": M1, "outcome_index": 0}])  # B sold its M2 shares back
        self.assertEqual(ab["shared_transactions"]["transactions"], ["0x" + f"{2:064x}"])
        self.assertEqual(ab["shared_transactions"]["grade"], "NOT_A_LINK")
        self.assertEqual([(s["wallet"], s["rows"], s["trade_rows"], s["markets"]) for s in got["wallets"]],
                         [(A, 4, 3, 2), (B, 4, 4, 3), (C, 1, 1, 1)])

    def test_co_timing_null(self):
        null = compare.compare_traders(Fake(), [A, B, C])["co_timing_null"]
        # Only A and B bought one outcome within 60 seconds; A's buy that cost more than its size has no price in (0, 1].
        self.assertEqual((null["available"], null["window_s"], null["buys_used"], null["buys_excluded_cash_not_in_0_to_size"]), (True, 60, 6, 1))
        self.assertEqual((null["observed_pairs"], null["simulations"], null["status"]), (1, 199, "EXPLORATORY_NOT_VALIDATED"))
        self.assertEqual((null["null_ge_observed"], null["p_value"], null["seed"]), (40, 0.205, 20261102))

    def test_statement_and_limits(self):
        got = compare.compare_traders(Fake(incomplete=(B,)), [A, B], max_rows=4)
        self.assertIn("at most PROBABLE_COORDINATION", got["statement"])
        self.assertIn("everybody rushes into after public news proves nothing", got["statement"])
        self.assertEqual(got["limits"][0], f"activity capped at max_rows=4 and NOT complete for {B}: counts are of the rows read only")

    def test_without_the_checkout_the_overlap_stays_and_the_null_is_unavailable(self):
        with mock.patch.object(_legacy, "repository_root", lambda: None):
            got = compare.compare_traders(Fake(), [A, B])
        self.assertEqual(counts(got["pairs"][0]), (A, B, 2, 0.666667, 1, 1, 2, 1))
        self.assertEqual(got["co_timing_null"]["available"], False)

    def test_refusals(self):
        fake = Fake()
        for wallets in ([A], [A] + ["0x" + f"{i:040x}" for i in range(10)], [A, A.upper().replace("0X", "0x")], [A, "0x123"], A + B):
            with self.assertRaises(ValueError):
                compare.compare_traders(fake, wallets)
        with self.assertRaises(ValueError):
            compare.compare_traders(fake, [A, B], max_rows=0)
        self.assertEqual(fake.asked, [])


class Loader(unittest.TestCase):
    def test_the_loader_leaves_sys_path_and_sys_modules_as_it_found_them(self):
        path, sentinel = list(sys.path), object()
        sys.modules["ledger"] = sentinel
        try:
            temporal = _legacy.temporal()
            self.assertIs(sys.modules["ledger"], sentinel)
        finally:
            del sys.modules["ledger"]
        self.assertEqual(temporal.WINDOWS, (5, 30, 60, 300, 900, 3600))
        self.assertTrue(callable(temporal.circular_shift_null))
        _legacy.temporal()
        self.assertEqual(sys.path, path)
        self.assertNotIn("ledger", sys.modules)
        self.assertNotIn("temporal", sys.modules)

    def test_no_checkout_gives_none(self):
        with mock.patch.object(_legacy, "repository_root", lambda: None):
            self.assertIsNone(_legacy.temporal())


if __name__ == "__main__":
    unittest.main()
