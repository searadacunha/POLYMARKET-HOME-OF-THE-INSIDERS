#!/usr/bin/env python3
"""Offline intake/crosswalk validation. NOT an on-chain transaction verifier.

Run: python3 research_notes/c5-c7-recovery-overlaps-2026-11-07/verify.py
"""
import csv
import re
from collections import Counter
from decimal import Decimal
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EVM = re.compile(r"^0x[0-9a-f]{40}$")


def records(path):
    with path.open("r", newline="", encoding="utf-8") as fp:
        return list(csv.DictReader(fp))


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def contains_exact(path, needle):
    with path.open("r", encoding="utf-8") as fp:
        return any(needle in line for line in fp)


def main():
    proxies = records(HERE / "data" / "candidates.csv")
    alerts = records(HERE / "data" / "alert_crosswalk.csv")

    require(len(proxies) == 13, "Expected 13 C5/C7 accounts")
    require(Counter(r["case"] for r in proxies) == {"C5": 7, "C7": 6},
            "Wrong case populations")
    require(len({(r["case"], r["handle"]) for r in proxies}) == 13,
            "Duplicate case/handle")
    resolved = [r for r in proxies if r["polygon_proxy"]]
    unresolved = [r for r in proxies if not r["polygon_proxy"]]
    require(len(resolved) == 11 and len(unresolved) == 2,
            "Expected 11 mapped and 2 unresolved accounts")
    require(all(EVM.fullmatch(r["polygon_proxy"]) for r in resolved),
            "Invalid or truncated address")
    require(len({r["polygon_proxy"] for r in resolved}) == len(resolved),
            "Duplicate proxy")
    require({r["handle"] for r in unresolved} == {"6741", "aenews0"},
            "Unexpected unresolved handle set")
    require(all(r["financial_status"] == "NOT_REPLAYED" for r in resolved),
            "Documentary mappings cannot be labelled chain-confirmed")
    require(all(r["financial_status"] == "UNRESOLVED" for r in unresolved),
            "Missing addresses must remain unresolved")

    # Verify exactly what the pre-existing P9 CSV records, not blockchain truth.
    timeline_path = (
        ROOT / "investigations" / "maduro-iran" / "sources"
        / "phase10" / "maduro_iran_timeline.csv"
    )
    with timeline_path.open("r", newline="", encoding="utf-8") as fp:
        timeline = list(csv.reader(fp))
    c5 = {r["polygon_proxy"] for r in resolved if r["case"] == "C5"}
    require(len(alerts) == 3, "Expected three historical P9 overlaps")
    require(len({(r["polygon_proxy"], r["at_utc"]) for r in alerts}) == 3,
            "Duplicate alert row")
    for alert in alerts:
        addr = alert["polygon_proxy"]
        require(addr in c5, "Alert references a proxy outside the C5 registry")
        prefix = addr[:10]
        value = f'{int(alert["stake_usd"]):,} $ p={Decimal(alert["entry_price"]):.3f}'
        matching = [
            row for row in timeline
            if len(row) > 5
            and row[1] == alert["at_utc"]
            and row[2] == "alerte détecteur " + alert["signal"]
            and row[3] == "p9_detector.py rejoué"
            and row[4] == "MESURÉ"
            and prefix + " outcome0 (YES)" in row[5]
            and value in row[5]
        ]
        require(len(matching) == 1,
                f"P9 historical journal mismatch: {prefix} {alert['at_utc']}")

    # Full-address, independent occurrence in an older local registry.
    watch = ROOT / "investigations" / "maduro-iran" / "sources" / "phase13" / "wallet_watchlist.csv"
    require(
        contains_exact(watch, "0xde7be6d489bce070a959e0cb813128ae659b5f4b"),
        "PolyBeats extra proxy not found in existing phase-13 watchlist",
    )
    journal = ROOT / "investigations" / "polysentinel" / "sources" / "evidence" / "signal_engine_v1" / "journal.jsonl"
    require(
        contains_exact(journal, "0x88c4919de76e526d55a32c1f8afb439dd1f1129a"),
        "PolyBeats extra proxy not found in existing PolySentinel journal",
    )

    print("OK: 13 accounts (7 C5; 6 C7), 11 syntactically valid mapped proxies, 2 unresolved.")
    print("OK: 3 exact P9 timeline observations at eight-hex prefixes, 2 older full-address presences.")
    print("These checks do NOT validate chain transfers, attribution, PnL or external archive hashes.")


if __name__ == "__main__":
    main()
