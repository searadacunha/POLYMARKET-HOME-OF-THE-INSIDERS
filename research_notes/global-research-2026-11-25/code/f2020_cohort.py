"""Recount the archived f2020 cohort from the committed source files.

This does not import weekly_funding. The expected counts are the ones already
published in investigations/weekly-funding-intelligence/results/weekly_funding.json.
"""

import csv
import hashlib
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "investigations/changenow-polymarket/sources"
WEEKLY = REPO / "investigations/weekly-funding-intelligence/results/weekly_funding.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def recount() -> dict:
    recipients = json.loads((SOURCE / "f2020_recipients.json").read_text())
    with (SOURCE / "state/pm_traders.csv").open() as handle:
        traders = list(csv.DictReader(handle))
    with (SOURCE / "state/pm_pnl2.csv").open() as handle:
        pnl = list(csv.DictReader(handle))
    published = json.loads(WEEKLY.read_text())["historical_f2020_cohort"]
    fresh = {
        "payees": len(recipients),
        "bettor_records": len(traders),
        "distinct_trading_addresses": len({row["account"].lower() for row in traders}),
        "eoa_records": sum(row["account_type"] == "EOA" for row in traders),
        "deposit_wallet_records": sum(row["account_type"] == "DW" for row in traders),
        "incomplete_pnl_records": sum(row["incomplete"].lower() == "true" for row in pnl),
    }
    mismatch = [key for key, value in fresh.items() if value != published[key]]
    digest = sha256(SOURCE / "f2020_recipients.json")
    pinned = json.loads(WEEKLY.read_text())["inputs_sha256"][
        "investigations/changenow-polymarket/sources/f2020_recipients.json"
    ]
    return {
        "fresh": fresh,
        "published": {key: published[key] for key in fresh},
        "mismatch": mismatch,
        "recipients_sha256": digest,
        "pinned_sha256": pinned,
        "sha_match": digest == pinned,
    }
