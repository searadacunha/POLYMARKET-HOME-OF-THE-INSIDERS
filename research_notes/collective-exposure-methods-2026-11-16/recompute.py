#!/usr/bin/env python3
"""Recompute descriptive Iran archive counts only; no chain replay or statistical inference."""
import argparse
import csv
import json
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
JSON_SOURCE = REPO / "research_notes/independent-forensic-audit-2026-11-08/evidence/feb28_noyes_descriptive.json"
CSV_SOURCE = REPO / "research_notes/x-history-2026-11-06/verification/data/g38_accounts.csv"
RESULT = HERE / "results/feb28_descriptive_recheck.json"


def fraction(numerator, denominator):
    if not 0 <= numerator <= denominator or denominator == 0:
        raise ValueError("invalid rate numerator or denominator")
    return format(Decimal(numerator) / Decimal(denominator), ".6f")


def build(source=JSON_SOURCE, roster=CSV_SOURCE):
    record = json.loads(Path(source).read_text(encoding="utf-8"))
    d, counts = record["definition"], record["counts"]
    if d["market"] != "US strikes Iran by February 28, 2026?":
        raise ValueError("wrong market or source")
    if d["no_before_yes"] != "earliest BUY of outcome No strictly before earliest BUY of outcome Yes, this market and this band only":
        raise ValueError("source definition changed; cannot compare")
    if d["p_value"] is not None:
        raise ValueError("archive no longer reports descriptive-only result")
    cohort, other = counts["cohort"], counts["other"]
    if sum(cohort.get(key, 0) for key in ("no_buy_before_yes_buy", "yes_buy_only", "no_buy_only", "yes_buy_before_no_buy", "no_buy")) != cohort["n"]:
        raise ValueError("cohort partition does not sum to n")
    if sum(other.get(key, 0) for key in ("no_buy_before_yes_buy", "yes_buy_only", "no_buy_only", "yes_buy_before_no_buy", "no_buy")) != other["n"]:
        raise ValueError("other partition does not sum to n")
    if counts["window_profiles"] != cohort["n"] + other["n"]:
        raise ValueError("wrong total comparable profiles")
    if int(d["rows"]) != 42000 or int(d["pages"]) != 84:
        raise ValueError("archived sample window changed: review required")
    with Path(roster).open(newline="", encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 38 or len({r["proxy"].lower() for r in rows}) != 38:
        raise ValueError("original 38-wallet roster changed")
    selected = [r for r in rows if r["created"][:10] in {"2026-02-22", "2026-02-23", "2026-02-24", "2026-02-25"}]
    if len(selected) != cohort["n"]:
        raise ValueError("different cohort definition")
    noyes = sum(r["no_before_yes"] == "True" for r in selected)
    if noyes != len(selected):
        raise ValueError("cross-market NO-before-YES roster changed")
    c, o = cohort["no_buy_before_yes_buy"], other["no_buy_before_yes_buy"]
    if not c or not o or c >= cohort["n"] or o >= other["n"]:
        raise ValueError("observed frequencies unsuitable for odds-ratio display")
    clock = counts["first_yes_in_27_feb_2049_2335_utc"]
    if not (0 <= clock["cohort_in_clock"] <= clock["cohort_yes_buyers"] <= cohort["n"]):
        raise ValueError("invalid cohort clock-window counts")
    if not (0 <= clock["other_in_clock"] <= clock["other_yes_buyers"] <= other["n"]):
        raise ValueError("invalid comparison clock-window counts")
    return {
        "archive_status": "RECALCULATED_ARCHIVE_SUMMARY_ONLY",
        "source_json": str(Path(source).resolve().relative_to(REPO.resolve())) if Path(source).resolve().is_relative_to(REPO.resolve()) else str(source),
        "source_csv": str(Path(roster).resolve().relative_to(REPO.resolve())) if Path(roster).resolve().is_relative_to(REPO.resolve()) else str(roster),
        "source_window_rows": d["rows"],
        "same_market": d["market"],
        "cohort": {"n": cohort["n"], "no_before_yes_count": c, "no_before_yes_fraction": fraction(c, cohort["n"])},
        "comparison": {"n": other["n"], "no_before_yes_count": o, "no_before_yes_fraction": fraction(o, other["n"])},
        "descriptive_ratios": {
            "frequency_ratio": format((Decimal(c) / cohort["n"]) / (Decimal(o) / other["n"]), ".6f"),
            "odds_ratio": format((Decimal(c) * (other["n"]-o)) / (Decimal(o) * (cohort["n"]-c)), ".6f"),
        },
        "cross_market_cohort": {"n": len(selected), "archive_no_before_yes_flags": noyes,
                                "scope": "across Iran deadline markets, not same market"},
        "first_yes_clock_window": {
            "cohort_first_yes_buyers": clock["cohort_yes_buyers"],
            "cohort_in_window": clock["cohort_in_clock"],
            "comparison_first_yes_buyers": clock["other_yes_buyers"],
            "comparison_in_window": clock["other_in_clock"],
            "start_utc": "2026-02-27T20:49:00Z",
            "end_utc": "2026-02-27T23:35:00Z",
        },
        "inferential_status": "NOT_VALIDATED",
        "warning": "Case-selected cohort; temporally incomplete market sample; buy ordering does not reconstruct exposures or prove reversal; independent trade-level replay and population-wide test absent. No p-value or predictive alpha.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Compare recomputed JSON with committed reference")
    args = parser.parse_args()
    actual = build()
    if args.check:
        reference = json.loads(RESULT.read_text(encoding="utf-8"))
        if actual != reference:
            raise SystemExit("FAILED: archived descriptive result does not match reference")
        print("PASS: descriptive archival values match reference (no inferential test)")
    else:
        print(json.dumps(actual, indent=2, sort_keys=True, ensure_ascii=False))


if __name__ == "__main__":
    main()
