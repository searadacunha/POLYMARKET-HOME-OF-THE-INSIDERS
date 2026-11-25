"""Offline tests for the 25 November 2026 note. No network."""

import json
import unittest
from pathlib import Path

NOTE = Path(__file__).resolve().parents[1]
REPO = NOTE.parents[1]
import sys
sys.path.insert(0, str(NOTE))

from code.activity_ledger import market_cash
from code.ctf_position import NEG_RISK_WRAPPED, USDC_E, position_id
from code.f2020_cohort import recount
from code.frozen_replay import replay
from code.keccak256 import keccak256
from code.population_rank import rank_table
from code.ranking_formula import published_score
from code.same_cell import summarize
from code.scoregrid import load, rank, score_repo
from code.settlement import settle
from code.w47_check import check

FRIDAY = "0x7f39808829da93cfd189807f13f6d86a0e604835e6f9482d8094fac46b3abaac"
FRIDAY_CASH = {
    "0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a": "36790.37",
    "0xd5de5cad9ef22b16317fe30a4234c72ece3eac1a": "85120.76",
    "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2": "128735.29",
    "0xcb18ea2923d957bd9cf049cce60a87638722f867": "34996.81",
    "0xa3a6fa49a39a4bf84cf510b7c8a2ab8be8508c44": "52329.44",
}


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
        self.assertEqual(after["raw"], 88)
        self.assertEqual(before["coverage"], 1)
        changed = [
            name for name in card["weights"]
            if card["repos"]["phi-before"]["items"][name] != card["repos"]["phi-after"]["items"][name]
        ]
        self.assertEqual(sorted(changed), ["C4", "R3", "S4"])

    def test_rank_does_not_include_partial_reads(self):
        card = load(NOTE / "data" / "scorecard.json")
        result = rank(card)
        ranked = [row["id"] for row in result["ranked"]]
        self.assertEqual(ranked, ["phi-after", "phi-before", "pselamy/polymarket-insider-tracker"])
        unread = {row["id"] for row in result["unranked"]}
        self.assertIn("orcalayer/polymarket-insider-score-backtest", unread)


class Cohort(unittest.TestCase):
    def test_f2020_matches_published_counts_and_hash(self):
        out = recount()
        self.assertEqual(out["mismatch"], [])
        self.assertTrue(out["sha_match"])
        self.assertEqual(out["fresh"]["payees"], 3408)
        self.assertEqual(out["fresh"]["distinct_trading_addresses"], 153)


class Population(unittest.TestCase):
    def test_ignition_wallets_survive_no_bh_rejection(self):
        out = rank_table(REPO / "research_notes/early-detection-2026-11-13/study/derived/analytic_table.jsonl")
        self.assertEqual(out["rows"], 587)
        self.assertEqual(out["wallets"], 468)
        self.assertEqual(out["rejected_bh_0.05"], 0)


class SameCell(unittest.TestCase):
    def test_day_interval_includes_zero_and_tapes_are_complete(self):
        payload = json.loads((NOTE / "data" / "same_cell.json").read_text())
        summary = summarize(payload)
        self.assertEqual(summary["n_complete"], 45)
        self.assertEqual(summary["n_with_day_peers"], 44)
        low, high = summary["ci95_delta_day"]
        self.assertLess(low, 0)
        self.assertGreater(high, 0)
        causal_low, causal_high = summary["ci95_delta_causal"]
        self.assertLess(causal_high, 0)
        self.assertGreater(summary["mean_delta_causal"], -1)


class IncaLedger(unittest.TestCase):
    def test_friday_market_cash_matches_the_november_cross_check(self):
        payload = json.loads((NOTE / "data" / "inca_activity.json").read_text())
        self.assertEqual(len(payload["wallets"]), 5)
        for wallet in payload["wallets"]:
            self.assertTrue(wallet["complete"])
            kinds = {}
            for row in wallet["rows"]:
                kinds[row.get("type")] = kinds.get(row.get("type"), 0) + 1
            self.assertEqual(kinds.get("SPLIT", 0), 0)
            self.assertEqual(kinds.get("MERGE", 0), 0)
            cash = market_cash(wallet["rows"], FRIDAY)["cash"]
            self.assertEqual(f"{float(cash):.2f}", FRIDAY_CASH[wallet["address"]])


class RankingAudit(unittest.TestCase):
    def test_published_top_score_and_service_funded_high_tier(self):
        score = published_score(0.6480762421361304, 1, 0.9, 1, 0, 0.3520270833333333, 0.005, 319393)
        self.assertAlmostEqual(score, 0.7528383714612586, places=12)
        audit = json.loads((NOTE / "data" / "vsbtc_score_audit.json").read_text())
        self.assertEqual(audit["rows"], 7784)
        self.assertEqual(audit["score_mismatches_gt_1e-6"], 0)
        self.assertEqual(audit["high_tier_service_funder"], 65)
        self.assertEqual(audit["high_tier"], 75)
        label = json.loads((NOTE / "data" / "deportfolio_label_addresses.json").read_text())
        self.assertEqual(label["n"], 100)
        self.assertEqual(label["inca_five_overlap"], ["0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2"])


if __name__ == "__main__":
    unittest.main()
