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
    print(f"ok prints={len(rows)} passing=0")


if __name__ == "__main__":
    main()
