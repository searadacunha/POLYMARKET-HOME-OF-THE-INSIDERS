"""Known values, invariants and a cross-check against the engine's own Fisher test."""
import importlib.util
import math
import random
import unittest
from pathlib import Path

from phi_forensics import stats

ROOT = Path(__file__).resolve().parents[2]


class Exact(unittest.TestCase):
    def test_wilson_known_values(self):
        low, high = stats.wilson(5, 10)
        self.assertAlmostEqual(low, 0.2366, places=4)
        self.assertAlmostEqual(high, 0.7634, places=4)
        self.assertEqual(stats.wilson(0, 10)[0], 0.0)
        self.assertAlmostEqual(stats.wilson(0, 10)[1], 0.2775, places=4)
        self.assertAlmostEqual(stats.wilson(10, 10)[1], 1.0)
        self.assertAlmostEqual(stats.wilson(10, 10)[0], 0.7225, places=4)
        self.assertEqual(stats.wilson(0, 0), (None, None))

    def test_poisson_binomial_matches_hand_values_and_the_binomial(self):
        self.assertEqual(stats.poisson_binomial_pmf([0.5, 0.5]), [0.25, 0.5, 0.25])
        self.assertAlmostEqual(stats.poisson_binomial_tail(1, [0.5, 0.5]), 0.75)
        self.assertAlmostEqual(stats.poisson_binomial_tail(2, [0.1, 0.2]), 0.02)
        self.assertEqual(stats.poisson_binomial_tail(0, [0.3, 0.9]), 1.0)
        self.assertEqual(stats.poisson_binomial_tail(-3, [0.3]), 1.0)
        self.assertEqual(stats.poisson_binomial_tail(3, [0.3, 0.9]), 0)
        self.assertEqual(stats.poisson_binomial_tail(0, []), 1.0)
        self.assertAlmostEqual(stats.binomial_tail(8, 10, 0.5), 56 / 1024)
        self.assertAlmostEqual(sum(stats.poisson_binomial_pmf([0.03, 0.4, 0.77, 0.5, 0.91])), 1.0)

    def test_a_cheap_winner_is_rarer_than_a_favourite_winner(self):
        self.assertLess(stats.poisson_binomial_tail(5, [0.05] * 5), 1e-6)
        self.assertGreater(stats.poisson_binomial_tail(5, [0.95] * 5), 0.77)

    def test_probabilities_out_of_range_are_refused(self):
        for bad in (-0.1, 1.1, float("nan")):
            with self.assertRaises(ValueError):
                stats.poisson_binomial_pmf([0.5, bad])

    def test_fisher_tea_tasting(self):
        self.assertAlmostEqual(stats.fisher_exact(3, 1, 1, 3), 17 / 70)
        self.assertAlmostEqual(stats.fisher_exact(3, 1, 1, 3, "less"), 69 / 70)
        self.assertAlmostEqual(stats.fisher_exact(3, 1, 1, 3, "two-sided"), 34 / 70)
        self.assertAlmostEqual(stats.fisher_exact(4, 0, 0, 4), 1 / 70)
        self.assertEqual(stats.fisher_exact(0, 0, 0, 0), 1.0)
        with self.assertRaises(ValueError):
            stats.fisher_exact(-1, 1, 1, 1)
        with self.assertRaises(ValueError):
            stats.fisher_exact(1, 1, 1, 1, "sideways")

    def test_fisher_agrees_with_the_quantitative_engine(self):
        path = ROOT / "integrations" / "quantitative_engine" / "validation.py"
        if not path.exists():
            self.skipTest("quantitative engine not present")
        spec = importlib.util.spec_from_file_location("qe_validation", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rng = random.Random(7)
        for _ in range(200):
            a, b, c, d = (rng.randrange(0, 30) for _ in range(4))
            theirs = module.fisher_greater(a, b, c, d)
            if theirs is not None:
                self.assertAlmostEqual(stats.fisher_exact(a, b, c, d), theirs, places=9, msg=(a, b, c, d))


class Resampling(unittest.TestCase):
    def test_permutation_detects_a_planted_difference_and_reports_a_bound(self):
        result = stats.permutation_test([10.0] * 20, [0.0] * 20, draws=2_000, seed=1)
        self.assertEqual((result["hits"], result["p"]), (0, 1 / 2_001))
        self.assertEqual(result["observed"], 10.0)

    def test_permutation_stays_silent_on_a_null(self):
        rng = random.Random(3)
        a, b = [rng.gauss(0, 1) for _ in range(60)], [rng.gauss(0, 1) for _ in range(60)]
        self.assertGreater(stats.permutation_test(a, b, draws=2_000, seed=1, alternative="two-sided")["p"], 0.05)

    def test_permutation_is_reproducible_and_one_sided_tests_mirror(self):
        a, b = [1.0, 2.0, 3.5, 4.0, 9.0], [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]
        first = stats.permutation_test(a, b, draws=500, seed=42)
        self.assertEqual(first, stats.permutation_test(a, b, draws=500, seed=42))
        self.assertLess(first["p"], stats.permutation_test(a, b, draws=500, seed=42, alternative="less")["p"])
        with self.assertRaises(ValueError):
            stats.permutation_test([], [1.0])

    def test_null_p_values_are_roughly_uniform(self):
        rng, below = random.Random(11), 0
        for trial in range(200):
            a, b = [rng.random() for _ in range(15)], [rng.random() for _ in range(15)]
            below += stats.permutation_test(a, b, draws=199, seed=trial)["p"] <= 0.05
        self.assertLessEqual(below, 20)  # 5% expected (10 of 200); 20 would be a broken null

    def test_bootstrap_interval(self):
        constant = stats.bootstrap_ci([2.0] * 30, draws=200)
        self.assertEqual((constant["low"], constant["high"], constant["estimate"]), (2.0, 2.0, 2.0))
        rng = random.Random(5)
        sample = [rng.gauss(10, 2) for _ in range(200)]
        ci = stats.bootstrap_ci(sample, draws=2_000, seed=9)
        self.assertLess(ci["low"], ci["estimate"])
        self.assertLess(ci["estimate"], ci["high"])
        self.assertLess(ci["high"] - ci["low"], 1.0)
        self.assertLess(abs(ci["estimate"] - 10), 0.5)
        self.assertEqual(ci, stats.bootstrap_ci(sample, draws=2_000, seed=9))
        with self.assertRaises(ValueError):
            stats.bootstrap_ci([])

    def test_cluster_bootstrap_is_wider_than_a_row_bootstrap_on_clustered_rows(self):
        rows = [(cluster, float(cluster % 2)) for cluster in range(10) for _ in range(40)]
        mean = lambda sample: sum(value for _, value in sample) / len(sample)
        by_cluster = stats.cluster_bootstrap_ci(rows, lambda row: row[0], mean, draws=1_000, seed=2)
        by_row = stats.bootstrap_ci(rows, mean, draws=1_000, seed=2)
        self.assertEqual((by_cluster["n_clusters"], by_cluster["n_rows"]), (10, 400))
        self.assertGreater(by_cluster["high"] - by_cluster["low"], 3 * (by_row["high"] - by_row["low"]))


class Multiplicity(unittest.TestCase):
    P = [0.01, 0.04, 0.03, 0.005]

    def test_known_adjustments(self):
        for got, want in ((stats.bonferroni(self.P), [0.04, 0.16, 0.12, 0.02]), (stats.holm(self.P), [0.03, 0.06, 0.06, 0.02]),
                          (stats.benjamini_hochberg(self.P), [0.02, 0.04, 0.04, 0.02])):
            for g, w in zip(got, want):
                self.assertAlmostEqual(g, w)

    def test_adjusted_values_never_fall_below_raw_ones_and_keep_the_order(self):
        rng = random.Random(1)
        for _ in range(50):
            p = [rng.random() ** 3 for _ in range(rng.randrange(1, 30))]
            for adjust in (stats.bonferroni, stats.holm, stats.benjamini_hochberg):
                adjusted = adjust(p)
                self.assertTrue(all(raw <= adj <= 1.0 for raw, adj in zip(p, adjusted)))
                ranked = sorted(range(len(p)), key=lambda i: p[i])
                self.assertEqual([adjusted[i] for i in ranked], sorted(adjusted[i] for i in ranked))
            self.assertTrue(all(h <= b + 1e-12 for h, b in zip(stats.holm(p), stats.bonferroni(p))))
            self.assertTrue(all(f <= h + 1e-12 for f, h in zip(stats.benjamini_hochberg(p), stats.holm(p))))

    def test_empty_family(self):
        self.assertEqual((stats.bonferroni([]), stats.holm([]), stats.benjamini_hochberg([])), ([], [], []))


class Design(unittest.TestCase):
    def test_power_equals_alpha_without_an_effect_and_grows_with_the_sample(self):
        self.assertAlmostEqual(stats.power_two_proportions(0.3, 0.3, 100, 100), 0.05, places=3)
        self.assertLess(stats.power_two_proportions(0.3, 0.4, 50, 50), stats.power_two_proportions(0.3, 0.4, 500, 500))
        self.assertGreater(stats.power_two_proportions(0.3, 0.4, 5_000, 5_000), 0.999)

    def test_minimum_detectable_effect_reaches_the_requested_power(self):
        effect = stats.minimum_detectable_effect(0.25, 400, 45)
        self.assertAlmostEqual(stats.power_two_proportions(0.25, 0.25 + effect, 400, 45), 0.80, places=3)
        self.assertGreater(effect, 0.15)  # 45 alerts cannot exclude an excess of fifteen points
        self.assertIsNone(stats.minimum_detectable_effect(0.9, 3, 3))

    def test_walk_forward_never_trains_on_the_future(self):
        times = [float(t) for t in range(100)]
        random.Random(4).shuffle(times)
        seen = []
        for train, test in stats.walk_forward_splits(times, folds=4, embargo=5.0):
            self.assertLess(max(times[i] for i in train), min(times[i] for i in test) - 5.0 + 1e-9)
            self.assertFalse(set(train) & set(test))
            seen += test
        self.assertEqual(len(seen), len(set(seen)))
        self.assertEqual(sorted(times[i] for i in seen), [float(t) for t in range(20, 100)])

    def test_walk_forward_refuses_too_few_rows_and_drops_tied_times_from_training(self):
        with self.assertRaises(ValueError):
            list(stats.walk_forward_splits([1.0, 2.0], folds=4))
        for train, test in stats.walk_forward_splits([1.0] * 10, folds=4):
            self.fail("rows at the same instant as the test block must not train")


class Scores(unittest.TestCase):
    def test_precision_recall_with_empty_denominators(self):
        empty = stats.precision_recall(0, 0, 0)
        self.assertEqual((empty["precision"], empty["recall"], empty["precision_ci"]), (None, None, (None, None)))
        scored = stats.precision_recall(8, 2, 8)
        self.assertEqual((scored["precision"], scored["recall"], scored["flagged"], scored["positives"]), (0.8, 0.5, 10, 16))

    def test_pair_confusion_known_example(self):
        result = stats.pair_confusion({"a": 1, "b": 1, "c": 2, "d": 2}, {"a": "x", "b": "x", "c": "x", "d": "y"})
        self.assertEqual((result["pairs"], result["true_pairs"], result["predicted_pairs"], result["agreeing_pairs"]), (6, 2, 3, 1))
        self.assertAlmostEqual(result["precision"], 1 / 3)
        self.assertAlmostEqual(result["recall"], 1 / 2)
        self.assertAlmostEqual(result["adjusted_rand_index"], 0.0)

    def test_pair_confusion_extremes(self):
        truth = {"a": 1, "b": 1, "c": 2, "d": 2, "e": 3}
        self.assertEqual(stats.pair_confusion(truth, {k: f"g{v}" for k, v in truth.items()})["adjusted_rand_index"], 1.0)
        ignored = stats.pair_confusion(truth, {})
        self.assertEqual((ignored["predicted_pairs"], ignored["recall"], ignored["precision"]), (0, 0.0, None))
        merged = stats.pair_confusion(truth, {k: "one" for k in truth})
        self.assertEqual(merged["recall"], 1.0)
        self.assertAlmostEqual(merged["precision"], 2 / 10)
        self.assertEqual(merged["adjusted_rand_index"], 0.0)
        self.assertTrue(math.isfinite(stats.pair_confusion({"a": 1}, {"a": 1})["adjusted_rand_index"]))


if __name__ == "__main__":
    unittest.main()
