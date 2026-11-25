"""Offline tests for the 25 November 2026 note. No network."""

import json
import unittest
from pathlib import Path

NOTE = Path(__file__).resolve().parents[1]
REPO = NOTE.parents[1]
import sys
sys.path.insert(0, str(NOTE))

from code.ctf_position import NEG_RISK_WRAPPED, USDC_E, position_id
from code.frozen_replay import replay
from code.keccak256 import keccak256
from code.scoregrid import load, rank, score_repo
from code.settlement import settle
from code.w47_check import check


class Keccak(unittest.TestCase):
    def test_vectors(self):
        self.assertEqual(keccak256(b"").hex(), "c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470")
        self.assertEqual(keccak256(b"abc").hex(), "4e03657aea45a94fc7d47ba826c8d667c0d1e6e33a64a036ec44f58fa12d6c45")


class Positions(unittest.TestCase):
    def test_binary_usdc_e_matches_archived_gamma(self):
        market = json.loads((REPO / "research_notes/financial-links-replay-2026-11-07/evidence/gamma/rail_markets.json").read_text())[0]
        tokens = json.loads(market["clobTokenIds"])
        self.assertFalse(market["negRisk"])
        self.assertEqual(position_id(USDC_E, market["conditionId"], 1), int(tokens[0]))
        self.assertEqual(position_id(USDC_E, market["conditionId"], 2), int(tokens[1]))
        self.assertNotEqual(position_id(NEG_RISK_WRAPPED, market["conditionId"], 1), int(tokens[0]))

    def test_neg_risk_uses_wrapped_collateral(self):
        market = json.loads((REPO / "research_notes/financial-links-replay-2026-11-07/evidence/gamma/xfm_anth_market.json").read_text())[0]
        tokens = json.loads(market["clobTokenIds"])
        self.assertTrue(market["negRisk"])
        self.assertEqual(position_id(NEG_RISK_WRAPPED, market["conditionId"], 1), int(tokens[0]))
        self.assertEqual(position_id(NEG_RISK_WRAPPED, market["conditionId"], 2), int(tokens[1]))
        self.assertNotEqual(position_id(USDC_E, market["conditionId"], 1), int(tokens[0]))


class Frozen(unittest.TestCase):
    def test_t1_matches_published_verdict(self):
        out = replay(
            REPO / "research_notes/early-detection-2026-11-13/study/derived/analytic_table.jsonl",
            REPO / "research_notes/early-detection-2026-11-13/study/derived/verdict.json",
        )
        self.assertEqual(out["mismatch"], [])
        self.assertEqual(out["published_verdict"], "NOT_SUPPORTED")
        self.assertEqual(out["recomputed"]["n"], 45)
        self.assertEqual(out["recomputed"]["wins"], 13)
        self.assertEqual(out["discovery_lonely_thin"], {"n": 3, "wins": 3})
        self.assertEqual(out["same_cell"]["status"], "NOT_TESTABLE")
        self.assertEqual(out["same_cell"]["with_same_cell_peer"], 0)

    def test_edge_verdict_unchanged_phrase(self):
        text = (REPO / "EDGE_VERDICT.md").read_text()
        self.assertIn("NO_EDGE_VALIDATED", text)


class Settlement(unittest.TestCase):
    def test_redeem_pays_only_the_winning_slot(self):
        result = settle(
            [
                {"condition": "c", "slot": 0, "shares": 10, "cost": 4},
                {"condition": "c", "slot": 1, "shares": 10, "cost": 6},
            ],
            {"c": 0},
        )
        self.assertTrue(result["synthetic"])
        self.assertEqual(result["payout"], 10)
        self.assertEqual(result["realized"], 0)
        self.assertEqual(result["open_lots"], [])

    def test_unresolved_lot_stays_open(self):
        result = settle([{"condition": "c", "slot": 1, "shares": 2, "cost": 1}], {})
        self.assertEqual(result["realized"], 0)
        self.assertEqual(result["open_lots"][0]["shares"], 2)


class Week47(unittest.TestCase):
    def test_snapshot(self):
        out = check(NOTE / "w47")
        self.assertTrue(out["ok"], out["errors"])
        self.assertEqual(out["verified_funded_wallets"], 0)
        self.assertEqual(out["tornado_funding_usd"], "0.00")
        self.assertGreater(float(out["tornado_unknown_gross_usd"]), 1_000_000)


class Grid(unittest.TestCase):
    def test_weights_and_single_point_change(self):
        card = load(NOTE / "data" / "scorecard.json")
        self.assertEqual(sum(card["weights"].values()), 100)
        before = score_repo(card, "phi-before")
        after = score_repo(card, "phi-after")
        self.assertEqual(before["raw"], 80)
        self.assertEqual(after["raw"], 82)
        self.assertEqual(before["coverage"], 1)
        changed = [
            name for name in card["weights"]
            if card["repos"]["phi-before"]["items"][name] != card["repos"]["phi-after"]["items"][name]
        ]
        self.assertEqual(changed, ["C4"])

    def test_rank_does_not_include_partial_reads(self):
        card = load(NOTE / "data" / "scorecard.json")
        result = rank(card)
        ranked = [row["id"] for row in result["ranked"]]
        self.assertEqual(ranked, ["phi-after", "phi-before", "pselamy/polymarket-insider-tracker"])
        unread = {row["id"] for row in result["unranked"]}
        self.assertIn("orcalayer/polymarket-insider-score-backtest", unread)


if __name__ == "__main__":
    unittest.main()
