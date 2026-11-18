"""Reproducible *optimistic* settlement sensitivity for the frozen LONELY_THIN study.

No order book, no fill simulation, no claim of live tradability. Pure Python stdlib.
Published analytic table is read, not modified.
"""
from __future__ import annotations

import argparse
import json
import random
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TABLE = (
    REPO_ROOT
    / "research_notes/early-detection-2026-11-13/study/derived/analytic_table.jsonl"
)
COSTS = (0.0, 0.005, 0.01, 0.02, 0.03, 0.05)
SEED = 20261116


def load_frozen_rows(path: Path, *, expected_count: int | None = 45) -> list[dict]:
    """Only the validation records from the original *pre-existing* frozen rule."""
    rows = []
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("eval_set") != "VALIDATION" or r.get("lonely_thin") is not True:
                continue
            price = r.get("p_alert")
            if type(price) not in (int, float) or not 0 < price < 1:
                raise ValueError(f"invalid alert price at line {line_number}")
            if type(r.get("win")) is not int or r["win"] not in (0, 1):
                raise ValueError(f"invalid settlement at line {line_number}")
            if not isinstance(r.get("event_slug"), str) or not r["event_slug"]:
                raise ValueError(f"missing event grouping at line {line_number}")
            rows.append(r)
    if not rows:
        raise ValueError("No valid frozen validation rows: fail closed")
    if expected_count is not None and len(rows) != expected_count:
        raise ValueError(f"Frozen cohort changed: expected {expected_count}, got {len(rows)}")
    return rows


def _quantile(values: list[float], q: float) -> float:
    return sorted(values)[int(q * (len(values) - 1))]


def cluster_ci(rows: list[dict], *, trials: int = 10000, seed: int = SEED) -> tuple[float, float]:
    """Resample *events*, not transactions, to preserve event dependence."""
    if trials < 2:
        raise ValueError("At least two bootstrap trials required")
    grouped = defaultdict(list)
    for r in rows:
        grouped[r["event_slug"]].append(r)
    groups = [grouped[k] for k in sorted(grouped)]
    rng = random.Random(seed)
    outcomes = []
    for _ in range(trials):
        sample = [rng.choice(groups) for _ in groups]
        n = sum(len(group) for group in sample)
        pnl = sum(r["win"] - r["p_alert"] for group in sample for r in group)
        outcomes.append(pnl / n)
    return _quantile(outcomes, .025), _quantile(outcomes, .975)


def analyse(rows: list[dict], *, trials: int = 10000) -> dict:
    n = len(rows)
    if not n:
        raise ValueError("Empty cohort")
    capital = sum(r["p_alert"] for r in rows)
    profit = sum(r["win"] - r["p_alert"] for r in rows)
    gross = profit / n
    ci = cluster_ci(rows, trials=trials)
    sensitivity = []
    for cost in COSTS:
        # 'cost' is an *all-in per-share price disadvantage*, not a venue fee model.
        sensitivity.append({
            "adverse_entry_markup_per_share": cost,
            "mean_optimistic_net_per_share": gross - cost,
            "one_share_each_optimistic_roi": (profit - n * cost) / (capital + n * cost),
        })
    return {
        "dataset": "research_notes/early-detection-2026-11-13/study/derived/analytic_table.jsonl",
        "selection": 'eval_set == "VALIDATION" and lonely_thin == true',
        "rows": n,
        "events": len(set(r["event_slug"] for r in rows)),
        "wins": sum(r["win"] for r in rows),
        "mean_observed_trade_price": capital / n,
        "optimistic_settlement_pnl_per_share": gross,
        "optimistic_roi_one_share_per_alert": profit / capital,
        "gross_cluster_bootstrap_95ci_per_share": list(ci),
        "bootstrap_trials": trials,
        "sensitivity": sensitivity,
        "verdict": "NO_EDGE_VALIDATED",
        "limitations": [
            "Reuses an existing validation cohort; this is post-hoc sensitivity, not a new holdout.",
            "Recorded last-trade price is not an executable ask and can precede detection.",
            "No order-book depth, queue, slippage, platform fees, position sizing, or latency.",
            "Assumes one share for every alert, full fill, and settlement; ignores opportunity cost.",
            "No PnL estimate herein should be described as achievable trading returns.",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--table", type=Path, default=DEFAULT_TABLE)
    p.add_argument("--bootstrap", type=int, default=10000)
    p.add_argument("--output", type=Path, help="optional JSON path; never overwrites source evidence")
    args = p.parse_args()
    result = analyse(load_frozen_rows(args.table), trials=args.bootstrap)
    data = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        if args.output.resolve() == args.table.resolve():
            raise ValueError("Cannot overwrite input evidence")
        args.output.write_text(data, encoding="utf-8")
    else:
        print(data, end="")


if __name__ == "__main__":
    main()
