#!/usr/bin/env python3
"""Offline checks for this note. Exits non-zero on the first failed claim."""

import json
import sys
from pathlib import Path

NOTE = Path(__file__).resolve().parent
sys.path.insert(0, str(NOTE))
REPO = NOTE.parents[1]

from code.frozen_replay import replay
from code.scoregrid import load, rank
from code.w47_check import check


def main():
    week = check(NOTE / "w47")
    if not week["ok"]:
        raise SystemExit("W47: " + "; ".join(week["errors"]))
    frozen = replay(
        REPO / "research_notes/early-detection-2026-11-13/study/derived/analytic_table.jsonl",
        REPO / "research_notes/early-detection-2026-11-13/study/derived/verdict.json",
    )
    if frozen["mismatch"] or frozen["same_cell"]["status"] != "NOT_TESTABLE":
        raise SystemExit("frozen replay failed")
    if "NO_EDGE_VALIDATED" not in (REPO / "EDGE_VERDICT.md").read_text():
        raise SystemExit("EDGE_VERDICT lost its standing phrase")
    card = load(NOTE / "data" / "scorecard.json")
    if sum(card["weights"].values()) != 100:
        raise SystemExit("weights")
    result = rank(card)
    catalog = json.loads((NOTE / "data" / "catalog.json").read_text())
    if len(catalog["repositories"]) != 56:
        raise SystemExit("catalog count")
    if len(catalog["opened_this_session"]) != 12:
        raise SystemExit("inspection count")
    print(json.dumps({
        "w47_verified_funded_wallets": week["verified_funded_wallets"],
        "w47_possible_exact_usd": week["possible_exact_receipt_usd"],
        "t1_mismatch": frozen["mismatch"],
        "t1_p": frozen["recomputed"]["p"],
        "ranked": [row["id"] + ":" + str(row["raw"]) for row in result["ranked"]],
        "catalogued": len(catalog["repositories"]),
        "opened_this_session": len(catalog["opened_this_session"]),
    }, indent=1))


if __name__ == "__main__":
    main()
