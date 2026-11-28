"""The statistics module against results already published in this repository by independent code.

The frozen early-detection study computed its primary test with its own implementation. Reading its analytic
table and finding the same numbers shows two implementations agree on real data. Nothing is written.
"""
import json
import unittest
from pathlib import Path

from phi_forensics import stats

STUDY = Path(__file__).resolve().parents[2] / "research_notes" / "early-detection-2026-11-13" / "study" / "derived"


@unittest.skipUnless((STUDY / "analytic_table.jsonl").exists(), "frozen study table not present")
class FrozenEarlyDetectionStudy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        table = [json.loads(line) for line in (STUDY / "analytic_table.jsonl").read_text(encoding="utf-8").splitlines()]
        cls.rows = [r for r in table if r["eval_set"] == "VALIDATION" and r["lonely_thin"]]
        cls.frozen = json.loads((STUDY / "verdict.json").read_text(encoding="utf-8"))["primary_T1"]

    def test_the_population_is_the_frozen_one(self):
        self.assertEqual((len(self.rows), sum(r["win"] for r in self.rows)), (self.frozen["n"], self.frozen["wins"]))
        self.assertEqual(len({r["event_slug"] for r in self.rows}), self.frozen["n_events"])

    def test_poisson_binomial_tail_equals_the_frozen_p_value(self):
        p = stats.poisson_binomial_tail(self.frozen["wins"], [r["p_alert"] for r in self.rows])
        self.assertAlmostEqual(p, self.frozen["p"], places=12)
        self.assertAlmostEqual(p, 0.3345912628416912, places=12)

    def test_cluster_bootstrap_agrees_with_the_frozen_interval(self):
        excess = lambda sample: sum(r["win"] - r["p_alert"] for r in sample) / len(sample)
        ci = stats.cluster_bootstrap_ci(sorted(self.rows, key=lambda r: r["event_slug"]), lambda r: r["event_slug"], excess,
                                        draws=5_000, seed=11)
        self.assertAlmostEqual(ci["estimate"], self.frozen["excess"], places=12)
        self.assertEqual(ci["n_clusters"], self.frozen["n_events"])
        low, high = self.frozen["ci95_excess_cluster"]
        self.assertAlmostEqual(ci["low"], low, delta=0.01)
        self.assertAlmostEqual(ci["high"], high, delta=0.01)

    def test_the_sample_could_not_exclude_a_moderate_excess(self):
        # What the frozen null result leaves open: with 45 alerts priced near 0.25, the smallest excess detected
        # four times out of five is far above the 3.5 points observed.
        effect = stats.minimum_detectable_effect(self.frozen["mean_p"], 10_000, self.frozen["n"])
        self.assertGreater(effect, 0.15)
        self.assertLess(effect, 0.25)


if __name__ == "__main__":
    unittest.main()
