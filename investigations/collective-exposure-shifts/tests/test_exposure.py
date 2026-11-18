#!/usr/bin/env python3
"""Unit tests and the positive control required before the freeze.

Run: python3 -m unittest discover -s investigations/collective-exposure-shifts/tests -v
"""
import importlib.util, os, random, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "scripts"))
spec = importlib.util.spec_from_file_location("build_alerts", os.path.join(HERE, "..", "scripts", "build_alerts.py"))
ba = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ba)


def synth(n_fills=2000, planted=False, seed=1, n_wallets=40):
    """Synthetic tape: random wallets trade both outcomes around 0.50; optional planted collective shift."""
    rng = random.Random(seed)
    t0 = 1_700_000_000
    rows = []
    for i in range(n_fills):
        ts = t0 + i * 60
        w = "0x%040x" % rng.randrange(n_wallets)
        side = "BUY" if rng.random() < 0.6 else "SELL"
        oc = "Yes" if rng.random() < 0.5 else "No"
        price = 0.5 + rng.uniform(-0.05, 0.05)
        rows.append((ts, w, side, oc, rng.uniform(5, 40), round(price, 3)))
    if planted:
        # three wallets each buy 1,500 USD of YES inside ten minutes, mid-life
        base = t0 + n_fills * 30
        for j in range(3):
            for k in range(3):
                rows.append((base + 120 * k + j, "0xp%038x" % j, "BUY", "Yes", 1000.0, 0.52))
    rows.sort(key=lambda r: (r[0], r[1]))
    return rows


class TestAccounting(unittest.TestCase):
    def test_coexistence_is_not_inversion(self):
        rows = [(1000, "0xa", "BUY", "No", 100, 0.40),
                (2000, "0xa", "BUY", "Yes", 50, 0.60)]
        books, _ = ba.build_books(rows)
        b = books["0xa"]
        self.assertAlmostEqual(b.at(b.x, 2000), 50 - 100)  # YES-equivalents, both legs held

    def test_yes_share_equivalents(self):
        rows = [(1000, "0xa", "BUY", "Yes", 10, 0.5),
                (2000, "0xa", "SELL", "No", 4, 0.5),
                (3000, "0xa", "SELL", "Yes", 3, 0.5)]
        books, _ = ba.build_books(rows)
        b = books["0xa"]
        self.assertAlmostEqual(b.at(b.x, 3000), (10 - 3) + 4)

    def test_two_sided_high_turnover_flagged(self):
        rows = [(1000, "0xa", "BUY", "Yes", 100, 0.5),
                (1100, "0xa", "SELL", "Yes", 90, 0.5),
                (1200, "0xa", "SELL", "No", 5, 0.5)]
        books, _ = ba.build_books(rows)
        g, buy, sell, both = books["0xa"].window(0, 1200)
        self.assertTrue(both)
        net = abs(books["0xa"].at(books["0xa"].x, 1200)) * 0.5
        self.assertGreaterEqual(g, 5 * max(net, 1e-9))

    def test_price_is_last_executed_fill(self):
        rows = [(1000, "0xa", "BUY", "Yes", 10, 0.31),
                (2000, "0xb", "SELL", "Yes", 10, 0.47)]
        _, prices = ba.build_books(rows)
        self.assertEqual(ba.price_at(prices, "Yes", 2500), 0.47)
        self.assertEqual(ba.price_at(prices, "Yes", 1500), 0.31)
        self.assertIsNone(ba.price_at(prices, "No", 2500))


class TestPositiveControl(unittest.TestCase):
    """The detector must find a planted collective shift and stay quiet without one."""

    def test_planted_shift_detected(self):
        meta = {"event_id": "e", "split": "TRAIN", "closed_ts": 0, "volume": 1}
        alerts, _ = ba.evaluate_market("0xc", synth(planted=True), meta)
        self.assertTrue(any(a["variant"] == "S4" for a in alerts),
                        "planted collective shift not detected")

    def test_null_tapes_quiet(self):
        meta = {"event_id": "e", "split": "TRAIN", "closed_ts": 0, "volume": 1}
        fired = 0
        for seed in range(60):
            alerts, _ = ba.evaluate_market("0xc", synth(planted=False, seed=seed), meta)
            fired += any(a["variant"] == "S4" for a in alerts)
        self.assertLessEqual(fired / 60, 0.05, f"S4 fired on {fired}/60 null tapes")

    def test_planted_rate(self):
        meta = {"event_id": "e", "split": "TRAIN", "closed_ts": 0, "volume": 1}
        fired = 0
        for seed in range(200):
            alerts, _ = ba.evaluate_market("0xc", synth(planted=True, seed=1000 + seed), meta)
            fired += any(a["variant"] == "S4" for a in alerts)
        self.assertGreaterEqual(fired / 200, 0.90, f"planted shift found in only {fired}/200 tapes")


class TestDedupe(unittest.TestCase):
    def test_largest_kept_in_block(self):
        cands = [{"side": "Yes", "t": 1000, "total_usd": 5000.0},
                 {"side": "Yes", "t": 2000, "total_usd": 9000.0},
                 {"side": "Yes", "t": 100000, "total_usd": 100.0}]
        kept = ba.dedupe(cands)
        self.assertEqual(len(kept), 2)
        self.assertEqual(kept[0]["total_usd"], 9000.0)


if __name__ == "__main__":
    unittest.main()
