"""Offline validation of captured source records with negative controls."""
import copy
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re
import statistics
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import arbitrum
import benchmark
import sports


def read(name):
    return json.loads((HERE / name).read_text())


class Evidence(unittest.TestCase):
    def test_chain_and_intermediate_balance(self):
        pairs = read("cases.json")["relay"]["candidates_24h"]
        captures = read("arbitrum_receipts.json")["rows"]
        results = [arbitrum.verify(p, d) for p, d in zip(pairs, captures, strict=True)]
        self.assertTrue(all(r["balance_reconciled"] for r in results))
        self.assertEqual([r["chain_seconds"] for r in results], [10, 12, 12])
        self.assertEqual(sum(Decimal(p["arrived"]) for p in pairs), Decimal("8992.754726"))
        for field, new_value in (("balances", []), ("transfers", []), ("blocks", [])):
            changed = dict(captures[0])
            changed[field] = new_value
            self.assertFalse(arbitrum.verify(pairs[0], changed)["balance_reconciled"])
        changed = copy.deepcopy(captures[0])
        changed["transfers"][0]["result"][0]["data"] = "0x01"
        self.assertFalse(arbitrum.verify(pairs[0], changed)["balance_reconciled"])
        changed = copy.deepcopy(captures[0])
        changed["balances"][0]["result"] = "0x01"
        self.assertFalse(arbitrum.verify(pairs[0], changed)["balance_reconciled"])
        with self.assertRaises(ValueError):
            arbitrum.verify(dict(pairs[0], arrival_tx=pairs[1]["arrival_tx"]), captures[0])

    def test_calendar_denominators(self):
        for name, events, games, late, bucket in (("sports.json",948,95,93,0), ("sports_game_start.json",1054,98,97,1)):
            data = read(name)
            summary = sports.summarize(data)
            self.assertEqual((summary["catalogue_events"], summary["moneylines"], summary["listed_after_target"],
                              summary["end_minus_start_exactly_7d"], summary.get("bucket",0)),
                             (events, games, late, games, bucket))
            self.assertEqual(summary.get("bucket_wins",0), 0)
            for r in data["catalogue"] + [x["history_request"] for x in data["games"] if "history_request" in x]:
                self.assertEqual(r["status"], 200)
                self.assertRegex(r["sha256"], "^[a-f0-9]{64}$")

    def test_exploratory_search_denominator(self):
        data = read("discovery.json")
        self.assertEqual(data["successful_orders"], 14127)
        self.assertEqual(data["matched_before_registry_screen"], 3)
        self.assertEqual(data["matches"], [])

    def test_live_observations(self):
        points = read("pilot.json")["observations"]
        self.assertEqual(len(points), 3)
        self.assertEqual([r["as_of"] - r["points"][0]["timestamp"] for r in points], [56, 29, 4])
        self.assertTrue(all(r["status"] == 200 and r["request"] <= r["response"] for r in points))
        self.assertTrue(all(b["request"] - a["request"] >= 30 for a,b in zip(points,points[1:])))
        run = read("live_run.json")
        lines = run["log_lines"]
        self.assertEqual(hashlib.sha256(("\n".join(lines) + "\n").encode()).hexdigest(), run["log_sha256"])
        batches = [tuple(map(int,re.search(r"blocks (\d+)-(\d+) behind \d+ fills (\d+) kept (\d+) large buys (\d+).*?evaluated (\d+).*?alerts (\d+)", line).groups())) for line in lines]
        self.assertTrue(all(first[1]+1 == second[0] for first,second in zip(batches,batches[1:])))
        self.assertEqual((sum(b-a+1 for a,b,*_ in batches), *(sum(row[i] for row in batches) for i in range(2,7))), (64,5116,32,24,2,0))
        self.assertEqual(sum(run["database_counts"]["retained_by_exchange"].values()),32)
        self.assertEqual(run["database_counts"]["alerts"],0)
        self.assertEqual(len(run["retained_ingest_lags_seconds"]),32)
        self.assertAlmostEqual(statistics.median(run["retained_ingest_lags_seconds"]),30.5657405,places=5)
        self.assertEqual((datetime.fromisoformat(run["end_utc"].replace("Z","+00:00")) - datetime.fromisoformat(run["start_utc"].replace("Z","+00:00"))).total_seconds(),189)

    def test_split_purges_late_labels_and_whole_overlapping_events(self):
        t = benchmark.BOUNDARIES[0]
        def row(event, decision, close):
            return dict(event_id=event, t_alert=decision, closed_ts=close, eval_set="VALIDATION")
        partitions, count = benchmark.clean_split([row("A",t-5,t-1),row("A",t+1,t+4),
                                                  row("B",t-3,t),row("C",t+1,t+1),row("D",t-9,t-1)])
        self.assertEqual((count["overlapping_event_rows"],count["unresolved_at_split_rows"],count["at_or_after_close"]), (2,1,1))
        self.assertEqual([r["event_id"] for v in partitions.values() for r in v], ["D"])


if __name__ == "__main__":
    unittest.main()
