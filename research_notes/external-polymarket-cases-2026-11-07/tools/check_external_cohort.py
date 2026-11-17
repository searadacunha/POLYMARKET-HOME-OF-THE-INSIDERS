#!/usr/bin/env python3
"""Offline scope and exact-wallet overlap check.

This does NOT verify Polymarket trades, custody, Binance/Kraken labels, or the
source of the public analysis. It checks two published *lists* are distinguishable
by exact Polygon proxy address and that the third-party registry is well formed.
No network access or external APIs. No files are written.
"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parents[1]
G38 = REPO / "research_notes/x-history-2026-11-06/verification/data/g38_accounts.csv"
EXTERNAL = HERE / "EXTERNAL_WALLETS.csv"
SOURCE_URL = "https://www.bitquery.io/investigations/polymarket-cftc-iran-pardon-bets"
ADDRESS = re.compile(r"^0x[0-9a-f]{40}$")


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def exact_addresses(rows: list[dict[str, str]], column: str) -> set[str]:
    addresses = [r[column].strip().lower() for r in rows]
    if any(not ADDRESS.fullmatch(a) for a in addresses):
        raise ValueError(f"Malformed or missing {column} in compared population")
    if len(addresses) != len(set(addresses)):
        raise ValueError(f"Duplicate {column} in compared population")
    return set(addresses)


def test_helper() -> None:
    assert exact_addresses([{"addr": "0x" + "a" * 40}], "addr") == {"0x" + "a" * 40}
    try:
        exact_addresses([{"addr": "0x123"}], "addr")
    except ValueError:
        pass
    else:
        raise AssertionError("Malformed address was not rejected")
    try:
        exact_addresses([{"addr": "0x" + "a" * 40}] * 2, "addr")
    except ValueError:
        pass
    else:
        raise AssertionError("Duplicate address was not rejected")


def main() -> None:
    test_helper()
    cases = load_rows(HERE / "CASES.csv")
    ids = [r["case_id"] for r in cases]
    if len(cases) != 13 or len(set(ids)) != 13:
        raise SystemExit("Expected 13 uniquely labelled historical case entries")
    if {f"C{i}" for i in range(1, 9)} - set(ids):
        raise SystemExit("The eight principal leads must all have registered entries")
    if any(not r["evidence_class"] or not r["source_status"] or not r["next_test"] for r in cases):
        raise SystemExit("Every case must specify evidence class, status and next test")
    if any(not r["source_url"].startswith("https://") for r in cases if r["case_id"].startswith("C")):
        raise SystemExit("Every principal case needs an external documentary citation")
    baseline = load_rows(G38)
    ext = load_rows(EXTERNAL)
    if len(baseline) != 38:
        raise SystemExit(f"Expected 38 original proxies, got {len(baseline)}")
    main_addresses = exact_addresses(baseline, "proxy")
    cohort = [r for r in ext if r["cohort"] == "iran_bitquery_9"]
    if len(cohort) != 9:
        raise SystemExit(f"Expected 9 external Iran accounts, got {len(cohort)}")
    cohort_addresses = exact_addresses(cohort, "polygon_address")
    labels = [r["public_label"] for r in cohort]
    if len(set(labels)) != 9:
        raise SystemExit("External account labels are duplicated")
    if any(r["ledger_source"] != SOURCE_URL or r["role"] != "trading_proxy" for r in cohort):
        raise SystemExit("An external account lacks the expected source/role")
    result_total = sum(int(r["reconstructed_result_usd"]) for r in cohort)
    if result_total != 2_476_951:
        raise SystemExit(f"Published nine-account result sum drift: {result_total}")
    overlap = main_addresses & cohort_addresses
    if any(r["main_38_exact_proxy_overlap"] != ("yes" if r["polygon_address"].lower() in overlap else "no") for r in cohort):
        raise SystemExit("Registry overlap label disagrees with the actual exact addresses")
    if overlap:
        raise SystemExit(f"New shared exact addresses require case reconciliation: {sorted(overlap)}")

    pardon = [r for r in ext if r["cohort"] == "biden_pardon_2"]
    if len(pardon) != 3 or sorted(r["role"] for r in pardon) != [
        "deposit_destination", "trading_proxy", "trading_proxy"
    ]:
        raise SystemExit("Pardon two proxies and one distinct destination are required")
    _ = exact_addresses(pardon, "polygon_address")
    print(json.dumps({
        "main_iran_proxies": len(main_addresses),
        "bitquery_iran_proxies": len(cohort_addresses),
        "exact_proxy_overlap": len(overlap),
        "recomputed_sum_of_PUBLISHED_individual_results_usd": result_total,
        "biden_trading_proxies": 2,
        "biden_deposit_destinations": 1,
        "scope": "Published registries only. NOT fresh RPC verification or proof of no indirect relationships.",
    }, indent=2))


if __name__ == "__main__":
    main()
