"""Independent, small synthetic unit tests; do not need network or gigabytes."""
import json
import tempfile
import unittest
from pathlib import Path

from edge_research.cost_gate import analyse, cluster_ci, load_frozen_rows


def row(event, price, win, *, valid=True, selected=True):
    return {"event_slug": event, "p_alert": price, "win": win,
            "eval_set": "VALIDATION" if valid else "DISCOVERY", "lonely_thin": selected}


class TestCostGate(unittest.TestCase):
    def test_selection_is_frozen(self):
        entries = [row("a", .2, 1), row("b", .3, 0),
                   row("c", .8, 1, valid=False), row("d", .9, 1, selected=False)]
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "table.jsonl"
            path.write_text("\n".join(json.dumps(x) for x in entries), encoding="utf-8")
            self.assertEqual(len(load_frozen_rows(path, expected_count=2)), 2)
            with self.assertRaisesRegex(ValueError, "cohort changed"):
                load_frozen_rows(path)

    def test_no_data_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "table.jsonl"
            path.write_text(json.dumps(row("a", .2, 1, valid=False)), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "No valid"):
                load_frozen_rows(path, expected_count=None)

    def test_rejects_invalid_fields(self):
        for bad in (row("a", 1.1, 1), row("a", .2, 2), row("", .2, 1)):
            with self.subTest(bad=bad):
                with tempfile.TemporaryDirectory() as d:
                    path = Path(d) / "table.jsonl"
                    path.write_text(json.dumps(bad), encoding="utf-8")
                    with self.assertRaises(ValueError):
                        load_frozen_rows(path, expected_count=None)

    def test_cost_sensitivity(self):
        rows = [row("a", .2, 1), row("b", .6, 0)]
        result = analyse(rows, trials=200)
        self.assertEqual(result["verdict"], "NO_EDGE_VALIDATED")
        self.assertAlmostEqual(result["optimistic_settlement_pnl_per_share"], .1)
        self.assertAlmostEqual(result["optimistic_roi_one_share_per_alert"], .25)
        costs = result["sensitivity"]
        self.assertAlmostEqual(costs[0]["mean_optimistic_net_per_share"], .1)
        self.assertAlmostEqual(costs[2]["mean_optimistic_net_per_share"], .09)

    def test_bootstrap_reproducible(self):
        rows = [row("a", .2, 1), row("a", .3, 0), row("b", .4, 1)]
        self.assertEqual(cluster_ci(rows, trials=100, seed=17),
                         cluster_ci(rows, trials=100, seed=17))
        low, high = cluster_ci(rows, trials=100, seed=17)
        self.assertLessEqual(low, high)

    def test_bootstrap_rejects_too_few(self):
        with self.assertRaises(ValueError):
            cluster_ci([row("a", .2, 1)], trials=1)


if __name__ == "__main__":
    unittest.main()
