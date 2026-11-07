"""Backtests must not see the future."""
import unittest

from triagent import detector
from triagent.detector import DAY, AsOf, Case, LeakError, evaluate, features_asof, flags_for, placebo


def history(t, new=True):
    first = t - (2 * DAY if new else 400 * DAY)
    rows = [{"type": "DEPOSIT", "timestamp": t - 3600, "usdc_size": 10000}] + \
           [{"type": "TRADE", "timestamp": first + i, "condition_id": f"c{i}"} for i in range(1 if new else 30)]
    return rows


class DetectorTests(unittest.TestCase):
    def test_future_rows_do_not_change_features(self):
        t = 10**9
        past = history(t)
        future = [{"type": "TRADE", "timestamp": t + k, "condition_id": "z"} for k in range(50)] + \
                 [{"type": "DEPOSIT", "timestamp": t + 5, "usdc_size": 10**7}]
        self.assertEqual(features_asof(past, t, 9000), features_asof(past + future, t, 9000))
        with self.assertRaises(LeakError):
            AsOf(past, t).check(future)

    def test_threshold_is_chosen_on_train_only(self):
        split = 2000 * DAY
        cases = [Case(f"p{i}", 1000 * DAY + i * DAY, 1, 1000 * DAY + i * DAY + DAY, 9000) for i in range(10)] + \
                [Case(f"n{i}", 1000 * DAY + i * DAY, 0, 0, 9000) for i in range(30)] + \
                [Case(f"q{i}", 3000 * DAY + i * DAY, 1, 0, 9000) for i in range(10)]
        acts = {c.address: history(c.t, new=c.address[0] != "n") for c in cases}
        base = evaluate(cases, acts.get, split)
        flipped = [Case(c.address, c.t, 1 - c.label, c.event_ts, c.trade_usdc) if c.t >= split else c for c in cases]
        self.assertEqual(base["threshold_from_train"], evaluate(flipped, acts.get, split)["threshold_from_train"])
        self.assertEqual(base["train"]["recall"], 1.0)
        self.assertEqual(base["train"]["fp_per_1000"], 0.0)
        self.assertFalse(base["labels_sufficient"])  # 10 positives in test: report, do not claim validation

    def test_placebo_and_flag_semantics(self):
        cases = [Case(f"p{i}", 1000 * DAY, 1, 1001 * DAY, 9000) for i in range(5)]
        acts = {c.address: history(c.t) for c in cases}
        res = placebo(cases, acts.get, draws=50)
        self.assertTrue(0 < res["p_value"] <= 1)
        self.assertEqual(len(detector.FLAG_RULES), 9)
        f = features_asof(history(10**9, new=False), 10**9, 100)
        self.assertNotIn("NEW_WALLET", flags_for(f))
