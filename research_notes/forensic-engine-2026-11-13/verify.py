#!/usr/bin/env python3
"""Recompute the committed sample and refuse a drifted or invented result."""

from __future__ import annotations

import json
import sys
from pathlib import Path

NOTE = Path(__file__).resolve().parent
ENGINE = NOTE.parents[1] / "integrations" / "quantitative_engine"
sys.path.insert(0, str(ENGINE))

from replay import replay_all
from validation import evaluate


def main() -> None:
    rows = [
        json.loads(line)
        for line in (NOTE / "data" / "scored_prints.jsonl").read_text(encoding="utf-8").splitlines()
        if line
    ]
    saved = json.loads((NOTE / "data" / "results.json").read_text(encoding="utf-8"))
    fresh = json.loads(json.dumps(evaluate(rows)))
    if fresh != saved["evaluation"]:
        raise SystemExit("evaluation does not match scored_prints.jsonl")
    if saved["prints"] != len(rows):
        raise SystemExit("print count does not match the jsonl")
    if fresh["patterns_passing_validation"] != []:
        raise SystemExit("a pattern passed after recomputation; update the report before publishing")
    if saved["alerts"]["emitted"] != 0 or saved["alerts"]["live_claim"] is not False:
        raise SystemExit("alert record is not the withheld archive replay")
    if json.loads(json.dumps(replay_all(()))) != saved["historical_cases"]:
        raise SystemExit("historical coverage record drifted")
    if any(row["wallet"] is not None or row["chain_receipt_checked"] for row in rows):
        raise SystemExit("a print was given a wallet or a chain receipt it does not have")
    inca = json.loads((NOTE / "data" / "inca_prejump.json").read_text(encoding="utf-8"))
    analysis = inca["analysis"]
    if analysis["prospective_detector"] is not False or analysis["insider_probability"] is not None:
        raise SystemExit("the selected-cohort tape was promoted to a detector")
    if analysis["decision"] != "NOT_DISCRIMINANT":
        raise SystemExit("the tape decision changed")
    if analysis["other_large_wallets"] != 12 or analysis["prejump_wallets"] != 328:
        raise SystemExit("the tape population counts changed")
    full = json.loads((NOTE / "data" / "inca_full.json").read_text(encoding="utf-8"))
    if full["israel_tape"]["decision"] != "NO_ALERT":
        raise SystemExit("the frozen monitor decision changed")
    if full["trade_hashes_found_in_polygon_receipts"] != 0:
        raise SystemExit("receipt overlap changed")
    if full["receipts"]["log_families"].get("ERC20_TRANSFER") != full["receipts"]["receipt_files"]:
        raise SystemExit("a receipt contained an OrderFilled log that this pass did not record")
    draw = json.loads((NOTE / "data" / "sampling_draw.json").read_text(encoding="utf-8"))
    if draw["seed"] != 20261113 or draw["frozen_ignitions_on_api_grid"] != 0:
        raise SystemExit("the public-sample ignition count changed")
    if draw["drawn"] < 300:
        raise SystemExit("the draw fell below 300 markets")
    print(f"ok prints={len(rows)} passing=0 inca={analysis['decision']} monitor={full['israel_tape']['decision']} draw={draw['drawn']}")


if __name__ == "__main__":
    main()
