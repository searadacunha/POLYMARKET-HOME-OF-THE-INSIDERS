"""Offline tests for the pre-registered rules. No network."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from fwc.logic import (  # noqa: E402
    central_answer, classify_address, commitment, evidence_class, family_permutation,
    forward_destination, freshness, h1_stat, has_tight_group, load_spec,
    opposing_outcomes_do_not_sum, shuffle_labels, tight_subset, verdict_h1,
)


class Commitment(unittest.TestCase):
    def test_cumulative_buys_count(self):
        fills = [(1, "BUY", 0.40, 1000), (2, "BUY", 0.35, 1000), (3, "BUY", 0.25, 1000)]
        got = commitment(fills)
        self.assertAlmostEqual(got["gross_buy_usd"], 1000.0, places=6)
        self.assertTrue(got["eligible"])
        self.assertEqual(got["threshold_ts"], 3)

    def test_nine_hundred_is_short(self):
        self.assertFalse(commitment([(1, "BUY", 0.9, 1000)])["eligible"])

    def test_eleven_buys_under_one_hundred_reach_the_threshold(self):
        fills = [(i, "BUY", 1.0, 99) for i in range(11)]
        got = commitment(fills)
        self.assertAlmostEqual(got["capital_committed_usd"], 1089.0, places=6)
        self.assertTrue(got["eligible"])
        self.assertEqual(got["threshold_ts"], 10)

    def test_recycle_does_not_inflate(self):
        fills = [(1, "BUY", 1, 600), (2, "SELL", 1, 600), (3, "BUY", 1, 600)]
        got = commitment(fills)
        self.assertAlmostEqual(got["gross_buy_usd"], 1200.0, places=6)
        self.assertAlmostEqual(got["capital_committed_usd"], 600.0, places=6)
        self.assertFalse(got["eligible"])

    def test_opposing_outcomes_do_not_combine(self):
        self.assertTrue(opposing_outcomes_do_not_sum(600, 400))
        self.assertFalse(opposing_outcomes_do_not_sum(1000, 400))


class Freshness(unittest.TestCase):
    def test_f1_and_f2(self):
        activity = [(100, "DEPOSIT", ""), (130, "TRADE", "0xabc")]
        got = freshness(activity, "0xabc", 130, 130, True, "contract", None, False)
        self.assertIn("F1", got["labels"])
        self.assertIn("F2_24h", got["labels"])
        self.assertTrue(got["qualifying"])
        self.assertFalse(got["F0"])

    def test_prior_trade_is_not_f1(self):
        activity = [(1, "TRADE", "0xother"), (10**7, "TRADE", "0xabc")]
        got = freshness(activity, "0xabc", 10**7, 10**7, True, "eoa", 5, True)
        self.assertNotIn("F1", got["labels"])
        self.assertIn("F3_90", got["labels"])
        self.assertFalse(got["F0"])

    def test_failed_history_is_not_fresh(self):
        got = freshness([], "0xabc", 10, 10, False, "eoa", 0, False)
        self.assertFalse(got["qualifying"])
        self.assertEqual(got["history"], "unresolved")

    def test_censored_gap_does_not_invent_dormancy(self):
        activity = [(1, "TRADE", "0xother")]
        got = freshness(activity, "0xabc", 10**8, 10**8, True, "eoa", 4, True, gap_censored=True)
        self.assertFalse(any(x.startswith("F3") for x in got["labels"]))

    def test_f0_requires_an_eoa_with_nonce_zero(self):
        activity = [(50, "DEPOSIT", "")]
        eoa = freshness(activity, "0xabc", 60, 60, True, "eoa", 0, False)
        proxy = freshness(activity, "0xabc", 60, 60, True, "contract", 0, False)
        self.assertTrue(eoa["F0"])
        self.assertFalse(proxy["F0"])


class Groups(unittest.TestCase):
    def test_windows(self):
        self.assertTrue(has_tight_group([0, 300], 300))
        self.assertFalse(has_tight_group([0, 301], 300))
        self.assertFalse(has_tight_group([0], 86400))

    def test_subset_keeps_the_largest_fit(self):
        rows = [{"wallet": "a", "threshold_ts": 0}, {"wallet": "b", "threshold_ts": 10},
                {"wallet": "c", "threshold_ts": 10**7}]
        got = tight_subset(rows, 3600)
        self.assertEqual([r["wallet"] for r in got], ["a", "b"])


class Classes(unittest.TestCase):
    def test_service_is_not_a_private_link(self):
        self.assertEqual(classify_address(True, 1, False, 1), "contract")
        self.assertEqual(classify_address(False, 5000, False, 1), "busy_eoa")
        self.assertEqual(classify_address(False, 20, True, 1), "service_infra")
        self.assertEqual(classify_address(False, 20, False, 11), "high_fanout_service")
        self.assertEqual(classify_address(False, 20, False, 2), "plain_eoa")

    def test_evidence_ladder(self):
        self.assertEqual(evidence_class(True, False, False, False, False, False, True, False),
                         "VERIFIED FINANCIAL LINK")
        self.assertEqual(evidence_class(True, True, False, False, False, False, True, False),
                         "CORROBORATED COORDINATION")
        self.assertEqual(evidence_class(False, False, False, False, False, True, True, False),
                         "SHARED SERVICE ONLY")
        self.assertEqual(evidence_class(False, False, False, False, False, False, False, False),
                         "UNRESOLVED")
        self.assertEqual(evidence_class(True, False, False, False, False, False, True, True),
                         "REFUTED")

    def test_exit_stops_at_infrastructure(self):
        infra = {"0xbridge"}
        moves = [{"token": "usdc", "from": "0xw", "to": "0xbridge", "value": 100},
                 {"token": "usdc", "from": "0xbridge", "to": "0xperson", "value": 100}]
        got = forward_destination(moves, "0xw", infra)
        self.assertIsNone(got["destination"])
        self.assertEqual(got["stopped"], "infra")


class Statistics(unittest.TestCase):
    def test_planted_funder_is_rare_under_the_shuffle(self):
        members = []
        assignments = []
        members.append({"market": "m", "outcome": "YES", "wallet": "a", "threshold_ts": 1_000_000})
        members.append({"market": "m", "outcome": "YES", "wallet": "b", "threshold_ts": 1_000_100})
        assignments.append({"id": "a", "month": "2026-11", "label": "key"})
        assignments.append({"id": "b", "month": "2026-11", "label": "key"})
        for i in range(30):
            w = f"w{i}"
            members.append({"market": f"o{i}", "outcome": "YES", "wallet": w, "threshold_ts": 1_000_000})
            assignments.append({"id": w, "month": "2026-11", "label": f"solo{i}"})

        def stat(rows):
            return h1_stat(members, {r["id"]: r["label"] for r in rows})

        got = shuffle_labels(assignments, 400, 20261125, stat)
        self.assertEqual(got["observed"], 1)
        self.assertLess(got["p"], 0.05)

    def test_unique_funders_are_not_a_hit(self):
        members = [
            {"market": "m", "outcome": "YES", "wallet": "a", "threshold_ts": 10},
            {"market": "m", "outcome": "YES", "wallet": "b", "threshold_ts": 20},
        ]
        self.assertEqual(h1_stat(members, {"a": "k1", "b": "k2"}), 0)

    def test_family_permutation_detects_a_one_sided_gap(self):
        markets = [{"family": "INFO", "quintile": i % 5, "hit": 1} for i in range(20)]
        markets += [{"family": "PUBLIC_PROCESS", "quintile": i % 5, "hit": 0} for i in range(20)]
        got = family_permutation(markets, 300, 7)
        self.assertGreater(got["observed"], 0.5)
        self.assertLess(got["p"], 0.02)

    def test_verdict_and_central_answer(self):
        self.assertEqual(verdict_h1(0.5, 0.5, 0, 40, 0, 0, 0.0167), "NOT_OBSERVED")
        self.assertEqual(verdict_h1(0.001, 0.5, 2, 40, 4, 4, 0.0167), "PRIMARY_SUPPORTED")
        self.assertEqual(verdict_h1(0.001, 0.001, 2, 40, 4, 4, 0.0167), "NOT_SPECIFIC")
        self.assertEqual(verdict_h1(0.001, 0.5, 2, 10, 4, 4, 0.0167), "INCONCLUSIVE_COVERAGE")
        self.assertEqual(central_answer("NOT_OBSERVED", 0.4, 0.8, 0.0167), "NO")
        self.assertEqual(central_answer("PRIMARY_SUPPORTED", 0.4, 0.8, 0.0167), "YES:H1")

    def test_spec_loads_and_keeps_the_three_tests(self):
        spec = load_spec()
        self.assertEqual(spec["tests"]["bonferroni_tests"], 3)
        self.assertEqual(spec["commitment"]["min_commit_usd"], 1000)
        self.assertEqual(len(spec["groups"]["windows_seconds"]), 8)

    def test_sample_spans_the_stratum(self):
        from fwc.logic import sample_indices
        idx = sample_indices(1000, 80)
        self.assertEqual(len(idx), 80)
        self.assertEqual(idx[0], 0)
        self.assertEqual(idx[-1], 999)
        self.assertEqual(sample_indices(10, 80), list(range(10)))


if __name__ == "__main__":
    unittest.main()
