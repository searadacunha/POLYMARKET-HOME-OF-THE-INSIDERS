"""The market report against fake sources: price moves in one window, holder concentration, who bought before the move."""
import unittest

from phi_forensics import market, sources

CONDITION = "0x" + "14" * 32
T0 = 1_790_000_000
W1, W2, W3, W4, W5 = ("0x" + c * 40 for c in "12345")
RECORD = {"question": "Will it happen?", "slug": "will-it-happen", "conditionId": CONDITION, "outcomes": '["Yes", "No"]',
          "outcomePrices": '["1", "0"]', "clobTokenIds": '["111", "222"]', "closed": True, "closedTime": "2026-11-01 12:00:00+00",
          "endDate": "2026-11-01T00:00:00Z", "startDate": "2026-10-01T00:00:00Z", "negRisk": False, "volume": "1234.5",
          "umaResolutionStatus": "resolved"}
# 0.25 -> 0.70 within 2 hours is the largest rise; 0.20 -> 0.95 is larger but takes more than 6 hours.
HISTORY = [{"t": T0, "p": 0.30}, {"t": T0 + 3600, "p": 0.25}, {"t": T0 + 7200, "p": 0.40}, {"t": T0 + 10800, "p": 0.70},
           {"t": T0 + 30000, "p": 0.20}, {"t": T0 + 60000, "p": 0.95}]
HOLDERS = [{"token_id": "111", "holders": [{"proxy_wallet": W1, "amount": a, "name": "x", "outcome_index": 0} for a in (50, 30, 10, 5, 3, 2)]},
           {"token_id": "222", "holders": [{"proxy_wallet": W2, "amount": 1, "name": "y", "outcome_index": 1}] * 100}]


def fill(wallet, side, index, size, price, sec):
    return {"proxy_wallet": wallet, "side": side, "token_id": ("111", "222")[index], "condition_id": CONDITION, "size": size, "price": price,
            "timestamp": T0 + sec, "outcome": ("Yes", "No")[index], "outcome_index": index, "transaction_hash": "0x" + f"{sec:064x}", "name": "n"}


TRADES = [fill(W1, "BUY", 0, 100, 0.30, 100), fill(W1, "BUY", 0, 50, 0.24, 3000), fill(W1, "SELL", 0, 30, 0.7, 11000),
          fill(W2, "BUY", 0, 10, 0.25, 3600),
          fill(W3, "BUY", 0, 200, 0.3, 500), fill(W3, "SELL", 0, 200, 0.28, 2000),
          fill(W4, "BUY", 1, 40, 0.7, 1000),
          fill(W5, "BUY", 0, 20, 0.3333, 3500)]


class Fake:
    def __init__(self, record=RECORD, history=HISTORY, holders=HOLDERS, trades=TRADES, complete=True):
        self.record, self.history, self._holders, self.rows, self.complete, self.asked = record, history, holders, trades, complete, []

    def market(self, condition):
        self.asked.append(("market", condition))
        return self.record

    def price_history(self, token_id, start=None, end=None, fidelity=60):
        self.asked.append(("price_history", token_id, fidelity))
        return self.history

    def holders(self, condition):
        self.asked.append(("holders", condition))
        return self._holders

    def trades(self, wallet=None, condition=None, start=None, end=None, max_rows=200_000):
        self.asked.append(("trades", condition, max_rows))
        return {"rows": self.rows, "complete": self.complete, "pages": 3}


def wallets(report):
    return [(w["proxy_wallet"], w["outcome_index"], w["net_cash_paid"], w["average_buy_price"], w["lead_seconds"])
            for w in report["positioned_before_move"]["wallets"]]


class Report(unittest.TestCase):
    def test_state_and_reads(self):
        fake = Fake()
        got = market.market_report(fake, CONDITION, max_trade_rows=500)
        self.assertEqual(fake.asked, [("market", CONDITION), ("price_history", "111", 10), ("holders", CONDITION), ("trades", CONDITION, 500)])
        self.assertEqual({k: got["market"][k] for k in ("question", "outcomes", "token_ids", "closed", "resolved", "payouts", "neg_risk")},
                         {"question": "Will it happen?", "outcomes": ["Yes", "No"], "token_ids": ["111", "222"], "closed": True,
                          "resolved": True, "payouts": ["1", "0"], "neg_risk": False})

    def test_an_unresolved_market_has_no_payouts(self):
        got = market.market_report(Fake(record={**RECORD, "umaResolutionStatus": "proposed", "outcomePrices": '["0.6", "0.4"]'}), CONDITION)
        self.assertEqual((got["market"]["resolved"], got["market"]["payouts"]), (False, None))

    def test_largest_rise_and_fall_within_six_hours(self):
        path = market.market_report(Fake(), CONDITION)["price_path"]
        self.assertEqual((path["points"], path["first"]["ts"], path["last"]["ts"], path["min"], path["max"]), (6, T0, T0 + 60000, 0.20, 0.95))
        rise, fall = path["largest_rise"], path["largest_fall"]
        self.assertEqual((rise["start"]["ts"], rise["start"]["price"], rise["end"]["ts"], rise["end"]["price"], rise["change"]),
                         (T0 + 3600, 0.25, T0 + 10800, 0.70, 0.45))
        self.assertEqual((fall["start"]["ts"], fall["end"]["ts"], fall["change"]), (T0 + 10800, T0 + 30000, -0.5))

    def test_holder_concentration_is_among_the_listed_holders(self):
        yes, no = market.market_report(Fake(), CONDITION)["holders"]
        self.assertEqual(yes, {"token_id": "111", "outcome": "Yes", "holders_listed": 6, "listed_total": "100.000000", "may_be_truncated": False,
                               "top_1_share": 0.5, "top_5_share": 0.98, "top_10_share": 1.0})
        self.assertEqual((no["outcome"], no["holders_listed"], no["may_be_truncated"], no["top_1_share"], no["top_5_share"], no["top_10_share"]),
                         ("No", 100, True, 0.01, 0.05, 0.1))
        self.assertNotIn("name", str(yes))

    def test_cash_per_wallet_and_outcome(self):
        trades = market.market_report(Fake(), CONDITION)["trades"]
        self.assertEqual((trades["rows"], trades["pages"], trades["complete"], trades["wallets"]), (8, 3, True, 5))
        self.assertEqual([(t["proxy_wallet"], t["outcome_index"], t["cash_bought"], t["cash_sold"]) for t in trades["by_wallet_outcome"]],
                         [(W3, 0, "60.000000", "56.000000"), (W1, 0, "42.000000", "21.000000"), (W4, 1, "28.000000", "0.000000"),
                          (W5, 0, "6.666000", "0.000000"), (W2, 0, "2.500000", "0.000000")])
        w1 = trades["by_wallet_outcome"][1]
        self.assertEqual((w1["first_buy_ts"], w1["average_buy_price"], w1["shares_bought"]), (T0 + 100, "0.280000", "150.000000"))
        self.assertNotIn("name", w1)

    def test_positioned_before_the_largest_rise(self):
        got = market.market_report(Fake(), CONDITION)
        moved = got["positioned_before_move"]
        self.assertEqual((moved["reference_ts"], moved["reference_source"], moved["outcome"]),
                         (T0 + 3600, "start of the largest 6-hour rise of the first outcome", "Yes"))
        # W2 bought at the reference second, not before it; W3 bought and sold back; W4 bought the other side.
        self.assertEqual(wallets(got), [(W1, 0, "42.000000", "0.280000", 3500), (W5, 0, "6.666000", "0.333300", 100)])
        self.assertIn("non-public", moved["statement"])

    def test_a_supplied_event_time_is_the_reference(self):
        got = market.market_report(Fake(), CONDITION, event_ts=T0 + 7200)
        self.assertEqual(got["positioned_before_move"]["reference_source"], "event_ts supplied by the caller")
        self.assertEqual(wallets(got), [(W1, 0, "42.000000", "0.280000", 7100), (W5, 0, "6.666000", "0.333300", 3700),
                                        (W2, 0, "2.500000", "0.250000", 3600)])

    def test_when_the_first_outcome_falls_after_the_event_the_second_one_rose(self):
        got = market.market_report(Fake(), CONDITION, event_ts=T0 + 10800)
        self.assertEqual((got["positioned_before_move"]["outcome"], wallets(got)), ("No", [(W4, 1, "28.000000", "0.700000", 9800)]))

    def test_no_move_gives_no_list_and_says_why(self):
        flat = market.market_report(Fake(history=[{"t": T0, "p": 0.5}, {"t": T0 + 600, "p": 0.5}]), CONDITION)
        moved = flat["positioned_before_move"]
        self.assertEqual((flat["price_path"]["largest_rise"], moved["wallets"], moved["reference_ts"], moved["reason"]),
                         (None, None, None, "no reference time"))
        late = market.market_report(Fake(), CONDITION, event_ts=T0 - 10)["positioned_before_move"]
        self.assertEqual((late["wallets"], late["reason"]), (None, "the price path does not show a move after the reference time"))

    def test_limits_name_the_cap(self):
        limits = market.market_report(Fake(complete=False), CONDITION, max_trade_rows=8)["limits"]
        self.assertEqual(limits[0], "trades: capped at max_trade_rows=8; 8 rows in 3 pages, complete=False, "
                                    "so wallets, cash and positions are of the rows read only")
        self.assertTrue(any("fees are not included" in l for l in limits) and any("same public news" in l for l in limits))
        self.assertTrue(any("at most 100 holders" in l for l in limits))

    def test_refusals(self):
        for kwargs in ({"max_trade_rows": 0}, {"max_trade_rows": True}, {"event_ts": "2026-11-01"}, {"event_ts": 1.5}):
            with self.assertRaises(ValueError):
                market.market_report(Fake(), CONDITION, **kwargs)
        for fake in (Fake(record=None), Fake(record={**RECORD, "clobTokenIds": "not json"}),
                     Fake(record={**RECORD, "outcomes": '["A", "B", "C"]', "clobTokenIds": '["1", "2", "3"]'}),
                     Fake(history=[{"t": T0}]), Fake(trades=[{**TRADES[0], "side": None}])):
            with self.assertRaises(sources.SourceError):
                market.market_report(fake, CONDITION)


if __name__ == "__main__":
    unittest.main()
