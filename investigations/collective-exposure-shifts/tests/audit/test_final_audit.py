#!/usr/bin/env python3
"""Checks of the audit code and of its recorded outputs. Runs offline from the investigation folder: python3 tests/audit/test_final_audit.py"""
import json, math, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
INV = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(INV, "results", "audit")
sys.path.insert(0, os.path.join(INV, "scripts", "audit"))
import final_audit as fa  # noqa: E402


class TestHelpers(unittest.TestCase):
    def test_binom_sf_exact(self):
        # P(X >= 2), X ~ Bin(3, 0.5) = 4/8
        self.assertAlmostEqual(fa.binom_sf(2, 3, 0.5), 0.5, places=12)
        self.assertAlmostEqual(fa.binom_sf(0, 10, 0.3), 1.0, places=12)
        self.assertAlmostEqual(fa.binom_sf(10, 10, 0.3), 0.3 ** 10, places=15)

    def test_cluster_ci_contains_mean(self):
        rows = [{"event_id": i // 2, "condition_id": str(i), "x": float(i % 3)} for i in range(60)]
        lo, hi = fa.cluster_ci(rows, "x", draws=2000)
        m = sum(r["x"] for r in rows) / len(rows)
        self.assertLessEqual(lo, m)
        self.assertGreaterEqual(hi, m)

    def test_split_bounds(self):
        self.assertEqual(fa.split_of(1767225599), "TRAIN")   # 2025-12-31T23:59:59Z
        self.assertEqual(fa.split_of(1767225600), "VALID")   # 2026-01-01T00:00:00Z
        self.assertEqual(fa.split_of(1782864000), "TEST")    # 2026-07-01T00:00:00Z


class TestRecordedAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.r = json.load(open(os.path.join(OUT, "final_audit.json")))
        cls.scored = [json.loads(l) for l in open(os.path.join(INV, "results", "replication_scored.jsonl"))]

    def test_published_numbers_reproduced(self):
        for run in ("primary", "replication"):
            self.assertTrue(self.r[run]["published_vs_audit"]["all_equal"], run)
            ls = self.r[run]["labels_splits"]
            self.assertEqual(ls["win_mismatch"] + ls["split_mismatch"] + ls["label_missing"], 0, run)
            ar = self.r[run]["alert_reconstruction"]
            self.assertEqual(ar["price_matches_tape"], ar["s4_primary"], run)
            self.assertEqual(ar["wallets_reproduced"], ar["wallets_listed"], run)
            self.assertEqual(ar["signal_complete_after_alert"], 0, run)

    def test_sample_rule(self):
        self.assertTrue(self.r["sample"]["primary"]["identical"])
        self.assertTrue(self.r["sample"]["replication"]["identical"])

    def test_tables_match_scored_file(self):
        t = json.load(open(os.path.join(OUT, "publication_tables.json")))
        idx = {(r["condition_id"], r["side"], r["t"]): r for r in self.scored
               if r["variant"] == "S4" and r.get("primary")}
        test_s4 = [r for r in idx.values() if r["split"] == "TEST"]
        self.assertEqual(len(t["false_positives"]), sum(1 for r in test_s4 if r["win"] == 0))
        for row in t["best_alerts"] + t["false_positives"]:
            s = idx[(row["condition_id"], row["side"], row["alert_ts"])]
            self.assertEqual(row["win"], s["win"])
            self.assertEqual(row["split"], "TEST")
            self.assertTrue(math.isclose(row["entry_price_last_fill"], s["price"]))
        sizes = [r["total_shift_usd"] for r in t["best_alerts"]]
        self.assertEqual(sizes, sorted(sizes, reverse=True))
        self.assertEqual(sizes[0], max(r["total_usd"] for r in test_s4))

    def test_sensitivity_recorded(self):
        s = self.r["sensitivity_replication"]
        for mode in ("causal_first", "distinct_rows"):
            self.assertEqual(s[mode]["verdict_rule"], "NOT_SUPPORTED")
            self.assertGreaterEqual(s[mode]["TEST"]["n"], 30)


if __name__ == "__main__":
    unittest.main(verbosity=2)
