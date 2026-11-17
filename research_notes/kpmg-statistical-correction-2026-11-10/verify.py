#!/usr/bin/env python3
"""Replay KPMG cohort definitions and descriptive outcomes without a significance claim.

The November 7 CSV and statistical outputs remain frozen. This verifier checks
their internal row definitions and describes the two populations separately;
it neither retrieves new trades nor recalibrates an insider-trading detector.
"""

import argparse
from collections import Counter
import csv
from datetime import datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SOURCE = ROOT / "research_notes/financial-links-replay-2026-11-07"
SCOPE_ROLES = {
    "core19": {"ORIGINAL_19"},
    "all22": {"ORIGINAL_19", "EXPANDED_3"},
}
SOURCE_FILES = (
    "data/kpmg_accounts.csv",
    "data/kpmg_earnings_markets.csv",
    "data/kpmg_market_stats.json",
    "tools/kpmg_markets.py",
)


def flag(value):
    if value not in ("True", "False"):
        raise ValueError(f"Invalid archived boolean: {value!r}")
    return value == "True"


def describe(rows, names):
    """Validate and summarize one already selected cohort's KPMG market rows."""
    seen = set()
    cutoffs = Counter()
    mixed, fallback = [], []
    main_wins = unanimous_wins = 0
    for row in rows:
        condition = row["condition_id"]
        if not condition or condition in seen:
            raise ValueError("Missing or duplicate condition within a cohort")
        seen.add(condition)
        if not set(row["accounts"].split("|")).issubset(names):
            raise ValueError("Market row contains an account outside its cohort")
        sides = row["account_sides"].split("|")
        if not all(sides) or len(set(sides)) != len(sides):
            raise ValueError("Missing or duplicate account main side")
        if not row["main_side"] or not row["winner"]:
            raise ValueError("Missing market main side or winner")
        main_won = row["main_side"] == row["winner"]
        unanimous = set(sides) == {row["winner"]}
        if flag(row["main_side_won"]) != main_won:
            raise ValueError("Archived main-side outcome contradicts its winner")
        if flag(row["every_account_side_won"]) != unanimous:
            raise ValueError("Archived account-main-side outcome contradicts its winner")
        main_wins += main_won
        unanimous_wins += unanimous
        cutoff = row["cutoff"]
        stamp = row["sec_item202_acceptance_utc"]
        if cutoff == "SEC_ITEM_2.02":
            if not stamp or datetime.fromisoformat(stamp).utcoffset() is None:
                raise ValueError("SEC cutoff has no timezone-aware acceptance timestamp")
        elif cutoff == "MARKET_CLOSE":
            if stamp:
                raise ValueError("Market-close fallback unexpectedly carries an SEC cutoff")
            fallback.append({"ticker": row["ticker"], "slug": row["slug"]})
        else:
            raise ValueError(f"Unrecognized cutoff: {cutoff!r}")
        cutoffs[cutoff] += 1
        p = Decimal(row["p_main_side_cost_weighted"])
        if not p.is_finite() or not Decimal(0) <= p <= Decimal(1):
            raise ValueError("Invalid archived main-side reference price")
        if len(sides) > 1:
            mixed.append({
                "ticker": row["ticker"],
                "slug": row["slug"],
                "account_main_sides": sorted(sides),
                "archived_main_side_reference_price": str(p),
                "all_account_main_sides_can_win": False,
            })
    return {
        "accounts_in_scope": len(names),
        "markets": len(rows),
        "aggregate_main_side_wins": main_wins,
        "unanimous_account_main_side_wins": unanimous_wins,
        "cutoffs": dict(sorted(cutoffs.items())),
        "market_close_fallbacks": sorted(fallback, key=lambda x: x["slug"]),
        "opposed_account_main_sides": sorted(mixed, key=lambda x: x["slug"]),
    }


def build_summary(source=SOURCE):
    with (source / "data/kpmg_accounts.csv").open(newline="") as handle:
        accounts = list(csv.DictReader(handle))
    with (source / "data/kpmg_earnings_markets.csv").open(newline="") as handle:
        markets = list(csv.DictReader(handle))
    legacy = json.loads((source / "data/kpmg_market_stats.json").read_text())
    if len({r["public_label"] for r in accounts}) != len(accounts):
        raise ValueError("Duplicate public label in cohort register")
    if len({r["polygon_proxy"].lower() for r in accounts}) != len(accounts):
        raise ValueError("Duplicate proxy in cohort register")
    if any(r["cohort_role"] not in SCOPE_ROLES["all22"] for r in accounts):
        raise ValueError("Unrecognized cohort role")
    if any(r["scope"] not in SCOPE_ROLES for r in markets):
        raise ValueError("Unrecognized market cohort scope")
    cohorts = {}
    for scope, roles in SCOPE_ROLES.items():
        names = {r["public_label"] for r in accounts if r["cohort_role"] in roles}
        selected = [r for r in markets if r["scope"] == scope
                    and r["auditor"] == "KPMG" and flag(r["held_at_cutoff"])
                    and r["winner"]]
        description = describe(selected, names)
        for legacy_rule, result_key in (
            ("main_side_won", "aggregate_main_side_wins"),
            ("every_account_side_won", "unanimous_account_main_side_wins"),
        ):
            recorded = legacy[f"{scope}|KPMG|{legacy_rule}"]
            if (recorded["markets"] != description["markets"]
                    or recorded["wins"] != description[result_key]):
                raise ValueError("Legacy statistical table disagrees with descriptive counts")
        cohorts[scope] = description
    return {
        "snapshot": "2026-11-10",
        "method": "Descriptive replay; no inferential p-value calculated",
        "sources_sha256": {
            name: hashlib.sha256((source / name).read_bytes()).hexdigest()
            for name in SOURCE_FILES
        },
        "cohorts": cohorts,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true",
                        help="Write the dated descriptive snapshot explicitly")
    args = parser.parse_args()
    result = build_summary()
    target = HERE / "summary.json"
    if args.write:
        target.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
        print("Wrote the dated KPMG descriptive snapshot.")
        return
    if result != json.loads(target.read_text()):
        raise SystemExit("FAIL: descriptive snapshot or frozen source hashes changed")
    for scope, cohort in result["cohorts"].items():
        print(f"PASS {scope}: {cohort['accounts_in_scope']} accounts, "
              f"{cohort['aggregate_main_side_wins']}/{cohort['markets']} aggregate-main-side wins, "
              f"{cohort['unanimous_account_main_side_wins']}/{cohort['markets']} "
              f"unanimous-account-main-side wins; {cohort['cutoffs'].get('SEC_ITEM_2.02', 0)} "
              f"SEC cutoffs and {cohort['cutoffs'].get('MARKET_CLOSE', 0)} market-close fallbacks")
    print("PASS: frozen source hashes and descriptive snapshot agree; no significance claim.")


if __name__ == "__main__":
    main()
