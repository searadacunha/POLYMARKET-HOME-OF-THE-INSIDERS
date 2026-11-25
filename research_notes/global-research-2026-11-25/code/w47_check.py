"""Checks for the closed ISO week 2026-W47 snapshot. Does not reinterpret other weeks."""

import csv
import json
from pathlib import Path


def load(root: Path):
    report = json.loads((root / "results" / "weekly_funding.json").read_text())
    with (root / "results" / "weekly_funding.csv").open() as handle:
        rows = list(csv.DictReader(handle))
    with (root / "results" / "wallet_funding.csv").open() as handle:
        wallets = list(csv.DictReader(handle))
    meta = json.loads((root / "capture.json").read_text())
    return report, rows, wallets, meta


def check(root: Path):
    report, rows, wallets, meta = load(root)
    errors = []
    if meta.get("week") != "2026-W47" or report.get("last_week") != "2026-W47":
        errors.append("week is not 2026-W47")
    if meta.get("repository_commit") != "9c279334a5dd77ef5fc30c9c2333c9f43aac5a5a":
        errors.append("capture was not taken from the recorded main commit")
    by = {(r["service"], r["evidence"]): r for r in rows}
    for service in ("ChangeNOW", "Tornado Cash"):
        for level in ("CONFIRMED_DIRECT", "SUPPORTED_INDIRECT"):
            row = by[(service, level)]
            if row["funding_usd"] != "0.00" or row["funded_distinct"] != "0":
                errors.append(f"verified funding is not zero for {service} {level}")
    possible = by[("ChangeNOW", "POSSIBLE")]
    if possible["exact_pm_receipt_usd"] != "8.93" or possible["exact_pm_recipients"] != "1":
        errors.append("possible exact Polymarket receipt is not the recorded 8.93 to one address")
    tornado_unknown = by[("Tornado Cash", "UNKNOWN")]
    if tornado_unknown["funding_usd"] != "0.00":
        errors.append("unassigned Tornado intake was counted as funding")
    if float(tornado_unknown["gross_source_usd"]) < 1000:
        errors.append("Tornado gross intake missing")
    exact = [w for w in wallets if w["relationship"] == "exact_trading_address"]
    if len(exact) != 1 or exact[0]["wallet"] != "0x74a7ff3574d91545a947bce48ef7b1c9452c56cb":
        errors.append("exact trading address changed")
    if exact and exact[0]["source_confidence"] != "POSSIBLE":
        errors.append("commingled route was upgraded above POSSIBLE")
    stats = report["statistics"]
    if not isinstance(stats, list) or len(stats) != 10:
        errors.append("expected ten frozen endpoints")
    for cell in stats:
        if cell.get("status") != "NOT_TESTABLE" or cell.get("p") is not None:
            errors.append("unexpected tested endpoint " + str(cell.get("endpoint")))
    return {
        "ok": not errors,
        "errors": errors,
        "verified_funded_wallets": 0,
        "possible_exact_receipt_usd": "8.93",
        "possible_exact_wallet": "0x74a7ff3574d91545a947bce48ef7b1c9452c56cb",
        "tornado_unknown_gross_usd": tornado_unknown["gross_source_usd"],
        "tornado_funding_usd": "0.00",
        "active_sample": possible["covered_active_pm"],
        "statistics": "NOT_TESTABLE",
        "prior_report_sha256": "fed5e9193ffa7d9401f4d42d02fdefef6fc7b3c1752bdc8ed66339f3763a3c73",
    }
