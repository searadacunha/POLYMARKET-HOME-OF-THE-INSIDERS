"""Regression tests for the f2020 bet reconstruction. Offline, standard library only.

usage: python3 -I research_notes/f2020-bet-reconstruction-2026-11-22/tests/test_reconstruct.py
"""
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import reconstruct as R  # noqa: E402
from decode import fill, wallet_view  # noqa: E402
from focus import FOCUS, MISSION_WALLET4  # noqa: E402

D = Decimal


def row(ts, typ, side=None, size=0, price=0, usdc=0, token="", cid="0xc1", tx="0x1"):
    return {"timestamp": ts, "type": typ, "side": side or "", "size": size, "price": price, "usdc_size": usdc,
            "token_id": token, "condition_id": cid, "transaction_hash": tx, "title": "t", "slug": "btc-updown-5m-1"}


MARKET = {"0xc1": {"conditionId": "0xc1", "question": "q", "slug": "btc-updown-5m-1", "outcomes": '["Up", "Down"]',
                   "clobTokenIds": '["11", "22"]', "outcomePrices": '["0", "1"]', "closed": True,
                   "umaResolutionStatus": "resolved", "events": [{"slug": "e1"}], "eventStartTime": None, "endDate": None}}


class Decoding(unittest.TestCase):
    def test_w1_bet_receipt(self):
        raw = R.load(R.RAW / "chain/focus_W1.json.gz")
        v = wallet_view(raw["receipts"][FOCUS[0]["bet_tx"]], FOCUS[0]["wallet"])
        self.assertEqual(len(v["fills"]), 1)
        f = v["fills"][0]
        self.assertEqual((f["side"], f["role"], f["shares"], f["cash"], f["fee"]),
                         ("BUY", "taker", D("6.461537"), D("4.199999"), D("0.10289")))

    def test_order_filled_rejects_other_events(self):
        with self.assertRaises(ValueError):
            fill({"topics": ["0x" + "0" * 64] * 4, "data": "0x" + "0" * 320, "transactionHash": "0x", "logIndex": "0x0"})


class Accounting(unittest.TestCase):
    def test_buy_sell_rebuy_redeem(self):
        rows = [row(1, "TRADE", "BUY", 10, D("0.6"), D("6.1"), "22"), row(2, "TRADE", "SELL", 10, D("0.7"), D("6.9"), "22"),
                row(3, "TRADE", "BUY", 5, D("0.5"), D("2.55"), "22"), row(4, "REDEEM", None, 5, 0, D("5"), "22")]
        p = R.positions(rows, MARKET, {})[0]
        self.assertEqual(p["net_pnl"], D("3.25"))
        self.assertEqual(p["fees"], D("0.1") + D("0.1") + D("0.05"))
        self.assertTrue(p["sold_before_resolution"])
        self.assertEqual((p["first_buy_outcome"], p["first_buy_won"]), ("Down", True))

    def test_redeem_clears_fee_in_shares_residue(self):
        # Before 2026-04-28 the API size was gross of a fee taken in shares: the redeem burns what is really held.
        rows = [row(1, "TRADE", "BUY", 41, D("0.07"), D("2.87"), "22"), row(2, "REDEEM", None, D("38.25"), 0, D("38.25"), "22")]
        p = R.positions(rows, MARKET, {})[0]
        self.assertEqual((p["left_shares"], p["unredeemed_value"], p["net_pnl"]), (0, 0, D("35.38")))

    def test_unredeemed_winner_and_chain_balance(self):
        rows = [row(1, "TRADE", "BUY", 4, D("0.5"), D("2"), "22")]
        self.assertEqual(R.positions(rows, MARKET, {})[0]["unredeemed_value"], D(4))
        self.assertEqual(R.positions(rows, MARKET, {}, chain_bal={"22": D(0)})[0]["unredeemed_value"], 0)

    def test_open_market(self):
        m = {"0xc1": {**MARKET["0xc1"], "closed": False, "outcomePrices": '["0.4", "0.6"]'}}
        p = R.positions([row(1, "TRADE", "BUY", 4, D("0.5"), D("2"), "11")], m, {})[0]
        self.assertEqual(p["status"], "OPEN")

    def test_window_filter(self):
        rows = [row(5, "TRADE", "BUY", 1, D("0.5"), D("0.5"), "11")]
        self.assertEqual(len(R.positions(rows, MARKET, {}, since=6)), 0)
        self.assertEqual(len(R.positions(rows, MARKET, {}, until=5)), 0)


class Statistics(unittest.TestCase):
    def test_calibration_null(self):
        pos = [{"first_buy_price": D("0.5"), "first_buy_won": w} for w in (True, False) * 50]
        c = R.calibration(pos)
        self.assertEqual((c["n"], c["wins"], c["z"]), (100, 50, 0.0))

    def test_calibration_edge(self):
        pos = [{"first_buy_price": D("0.5"), "first_buy_won": True}] * 30 + [{"first_buy_price": D("0.5"), "first_buy_won": False}] * 10
        self.assertAlmostEqual(R.calibration(pos)["z"], 10 / (40 * 0.25) ** 0.5, places=3)

    def test_weather_event_counts_once(self):
        base = {"family": "Weather: highest temperature", "event_slug": "busan", "cash_out": D(1)}
        pos = [{**base, "condition_id": "b", "first_buy": 2}, {**base, "condition_id": "a", "first_buy": 1}]
        self.assertEqual([p["condition_id"] for p in R.event_dedupe(pos)], ["a"])

    def test_fee_payment_detection(self):
        ext = [{"direction": "out", "counterparty": "0xfee", "counterparty_has_code": False, "amount": D("0.02"), "block": i}
               for i in range(20)]
        ext.append({"direction": "out", "counterparty": "0xfee", "counterparty_has_code": False, "amount": D("9.99"), "block": 99})
        got = R.fee_payments(ext)
        self.assertEqual((got[0]["small_payments"], got[0]["small_total"], got[0]["larger_transfers"]), (20, D("0.40"), 1))
        self.assertEqual(R.fee_payments(ext[:19]), [])


class MissionInputs(unittest.TestCase):
    def test_wallet4_as_given_is_a_splice(self):
        w4 = FOCUS[3]["wallet"]
        other = "0xe129d1e0d47d08339255582373b9bbafb9cc9361"
        self.assertEqual(len(MISSION_WALLET4) - 2, 39)
        self.assertTrue(MISSION_WALLET4.startswith(w4[:31]) and MISSION_WALLET4.endswith(other[-10:]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
