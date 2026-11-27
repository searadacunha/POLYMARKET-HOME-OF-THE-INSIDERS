"""The behaviour profile on a hand-computed wallet, its track record against the exact tail, and the change detector
on a planted break, on noise and on too few rows."""
import random
import unittest

from phi_forensics import behaviour, stats

C1, C2, C3 = "0x" + "c1" * 32, "0x" + "c2" * 32, "0x" + "c3" * 32
T0 = 1_700_006_400 + 9 * 3600  # 2023-11-15T09:00:00Z
DAY = 86_400


def row(ts, kind, size=0.0, cash=0.0, side="", price=None, index=None, condition=C1, event="e1"):
    return {"timestamp": ts, "type": kind, "side": side, "condition_id": condition, "token_id": f"{condition[-4:]}{index}", "size": size,
            "usdc_size": cash, "price": price, "outcome_index": index, "outcome": {0: "Yes", 1: "No"}.get(index), "title": "Will X happen?",
            "slug": "will-x", "event_slug": event}


def buy(ts, size, cash, price, index=0, **kw):
    return row(ts, "TRADE", size, cash, "BUY", price, index, **kw)


WALLET = [buy(T0, 100, 6.25, 0.0625),
          buy(T0 + 3600, 10, 2.5, 0.25, index=1),
          buy(T0 + DAY, 20, 18.75, 0.9375, condition=C2, event="e2"),
          row(T0 + DAY + 7200, "TRADE", 20, 19.5, "SELL", 0.975, 0, condition=C2, event="e2"),
          row(T0 + 3 * DAY, "REDEEM", 100, 100, condition=C1),
          {"timestamp": T0 + 3 * DAY + 60, "type": "REWARD", "usdc_size": 1, "condition_id": ""}]


def resolved(*payouts, source="RESOLUTION_PAYOUT"):
    return {"prices": dict(enumerate(payouts)), "source": source}


class Profile(unittest.TestCase):
    def test_a_hand_computed_wallet(self):
        p = behaviour.profile(list(reversed(WALLET)))  # order of the input does not matter
        self.assertEqual((p["rows"], p["row_types"]), (6, {"REDEEM": 1, "REWARD": 1, "TRADE": 4}))
        self.assertEqual((p["first_utc"], p["last_utc"], p["active_days_utc"]), ("2023-11-15T09:00:00Z", "2023-11-18T09:01:00Z", 3))
        self.assertEqual((p["markets"], p["events"], p["buys"], p["sells"]), (2, 2, 3, 1))
        self.assertEqual((p["cash_bought"], p["cash_sold"]), ("27.500000", "19.500000"))
        self.assertEqual(p["buy_cash"], {"min": "2.500000", "q1": "4.375000", "median": "6.250000", "q3": "12.500000", "max": "18.750000"})
        self.assertEqual(p["largest_market"], {"condition_id": C2, "share_of_cash_bought": 15 / 22})
        self.assertEqual(p["buy_price"], {"min": 0.0625, "q1": 0.15625, "median": 0.25, "q3": 0.59375, "max": 0.9375})
        self.assertEqual((p["cash_share_bought_under_0_10"], p["cash_share_bought_over_0_90"]), (5 / 22, 15 / 22))
        self.assertEqual(p["trade_hours_utc"], [0] * 9 + [2, 1, 1] + [0] * 12)
        self.assertEqual((p["median_holding_hours"], p["markets_with_holding_time"]), (37.0, 2))  # 72 h and 2 h
        self.assertEqual((p["markets_exited"], p["markets_sold_before_redemption"], p["share_sold_before_redemption"]), (2, 1, 0.5))
        self.assertNotIn("track_record", p)

    def test_a_wallet_without_buys_has_no_distribution_rather_than_zeros(self):
        p = behaviour.profile([WALLET[4]])
        self.assertEqual((p["buys"], p["buy_cash"], p["buy_price"], p["largest_market"], p["cash_share_bought_under_0_10"]),
                         (0, None, None, None, None))
        self.assertEqual((p["median_holding_hours"], p["share_sold_before_redemption"]), (None, None))

    def test_refusals(self):
        with self.assertRaises(ValueError):
            behaviour.profile([])
        with self.assertRaises(ValueError):
            behaviour.profile([{"type": "TRADE", "timestamp": "1700000000"}])


class TrackRecord(unittest.TestCase):
    def test_main_outcome_average_price_and_exact_tail(self):
        record = behaviour.profile(WALLET, {C1: resolved(1, 0), C2: resolved(0, 1)})["track_record"]
        self.assertEqual([(b["condition_id"], b["outcome_index"], b["average_price"], b["won"], b["cash_bought"]) for b in record["bets"]],
                         [(C1, 0, 0.0625, True, "6.250000"), (C2, 0, 0.9375, False, "18.750000")])
        self.assertEqual((record["resolved_markets"], record["wins"], record["expected_wins"]), (2, 1, 1.0))
        self.assertEqual(record["p_at_least_these_wins"], stats.poisson_binomial_tail(1, [0.0625, 0.9375]))
        self.assertAlmostEqual(record["p_at_least_these_wins"], 1 - 0.9375 * 0.0625)
        self.assertIn("not independent", record["warning"])
        self.assertIn("cannot be tested on the wins that selected it", record["warning"])

    def test_three_wins_at_a_quarter(self):
        rows = [buy(T0 + i, 40, 10, 0.25, condition=c, event=c) for i, c in enumerate((C1, C2, C3))]
        record = behaviour.profile(rows, {c: resolved(1, 0) for c in (C1, C2, C3)})["track_record"]
        self.assertEqual((record["wins"], record["expected_wins"]), (3, 0.75))
        self.assertEqual(record["p_at_least_these_wins"], stats.poisson_binomial_tail(3, [0.25] * 3))
        self.assertAlmostEqual(record["p_at_least_these_wins"], 1 / 64)

    def test_marks_and_split_payouts_are_skipped_and_counted(self):
        prices = {C1: resolved(0.5, 0.5), C2: resolved(0.6, 0.4, source="MARK 2026-11-27T08:00:00Z")}
        record = behaviour.profile(WALLET, prices)["track_record"]
        self.assertEqual((record["bets"], record["wins"], record["p_at_least_these_wins"]), ([], 0, 1.0))
        self.assertEqual(record["skipped_markets"], {"not_resolved": 1, "payout_not_0_or_1": 1})

    def test_a_resolution_without_the_payout_of_the_main_outcome_is_refused(self):
        with self.assertRaises(ValueError):
            behaviour.profile(WALLET, {C1: {"prices": {1: 0}, "source": "RESOLUTION_PAYOUT"}})


def stream(cash, gaps, prices):
    times = [T0]
    for gap in gaps:
        times.append(times[-1] + gap)
    return [buy(t, c / p, c, p) for t, c, p in zip(times, cash, prices)]


def noise(rng, n=80):
    return stream([round(rng.uniform(1, 100), 2) for _ in range(n)], [rng.randrange(60, 7200) for _ in range(n - 1)],
                  [round(rng.uniform(0.05, 0.95), 2) for _ in range(n)])


class Changes(unittest.TestCase):
    def test_a_planted_change_is_found_at_its_index(self):
        rng = random.Random(3)
        small = [10 + 0.25 * i for i in range(40)]
        large = [10 * v for v in small]
        rng.shuffle(small)
        rng.shuffle(large)
        rows = stream(small + large, [600] * 79, [0.5] * 80) + [row(T0 + DAY, "REDEEM", 1, 1)]
        found = behaviour.changes(rows)
        cash = found["series"]["cash_per_trade"]
        self.assertEqual((found["buys"], cash["values"], cash["change_index"], cash["change_utc_ts"]), (80, 80, 40, T0 + 40 * 600))
        self.assertEqual((cash["median_before"], cash["median_after"], cash["statistic"]), ("14.875000", "148.750000", 800.0))
        self.assertEqual((cash["hits"], cash["p"], cash["p_holm"], cash["decision"]), (0, 1 / 2001, 3 * (1 / 2001), "CHANGE_DETECTED"))
        for flat in ("hours_between_trades", "price"):  # constant series: every shuffle ties, nothing to locate
            self.assertEqual({k: found["series"][flat][k] for k in ("change_index", "p", "p_holm", "decision")},
                             {"change_index": None, "p": 1.0, "p_holm": 1.0, "decision": "NO_CHANGE_DETECTED"})
        self.assertIn("not evidence", found["reading"])

    def test_noise_from_one_distribution_is_not_a_change(self):
        found = behaviour.changes(noise(random.Random(7)))
        self.assertEqual({k: s["decision"] for k, s in found["series"].items()},
                         dict.fromkeys(("cash_per_trade", "hours_between_trades", "price"), "NO_CHANGE_DETECTED"))

    def test_the_hours_series_reports_the_trade_after_the_change(self):
        rows = stream([5] * 40, [60] * 20 + [36_000] * 19, [0.5] * 40)
        hours = behaviour.changes(rows)["series"]["hours_between_trades"]
        self.assertEqual((hours["values"], hours["change_index"], hours["median_before"], hours["median_after"]), (39, 21, 60 / 3600, 10.0))

    def test_too_few_rows_are_insufficient_data_not_quiet(self):
        rows = noise(random.Random(7))[:29]
        found = behaviour.changes(rows)
        self.assertEqual(found["series"], {"cash_per_trade": {"values": 29, "decision": "INSUFFICIENT_DATA"},
                                           "hours_between_trades": {"values": 28, "decision": "INSUFFICIENT_DATA"},
                                           "price": {"values": 29, "decision": "INSUFFICIENT_DATA"}})
        self.assertIn("p", behaviour.changes(rows, min_rows=29)["series"]["price"])

    def test_deterministic_under_the_seed(self):
        rows = noise(random.Random(7))
        self.assertEqual(behaviour.changes(rows, seed=5), behaviour.changes(rows, seed=5))
        self.assertNotEqual([s["p"] for s in behaviour.changes(rows, seed=5)["series"].values()],
                            [s["p"] for s in behaviour.changes(rows, seed=6)["series"].values()])

    def test_refusals(self):
        with self.assertRaises(ValueError):
            behaviour.changes([])
        with self.assertRaises(ValueError):
            behaviour.changes(noise(random.Random(7)), min_rows=2)


if __name__ == "__main__":
    unittest.main()
