#!/usr/bin/env python3
"""Recalculate pre-Snoorrason matchup shares from the *published* Thin Markdown case.

This tests consistency of a repository-derived snapshot ONLY. It does not
authenticate the X post/capture, check external RPC receipts or identify
the person operating either an X account or a Polymarket wallet.
"""

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[3]
CASE = ROOT / "investigations/ballon-dor-wallets/sources/cases/thin.md"
CUTOFF = datetime(2026, 10, 14, 8, 23, 34, tzinfo=timezone.utc)
EXPECTED = {
    "Mbappé": Decimal("66799.56"),
    "Rodri": Decimal("3916.35"),
}


def parse_ledger(case_text: str):
    marker = "**Historique daté**"
    if marker not in case_text:
        raise ValueError("Thin history table not found")
    history = case_text.split(marker, 1)[1].split("\n## ", 1)[0]
    totals = {issue: Decimal("0") for issue in EXPECTED}
    count = 0
    for line in history.splitlines():
        if not line.startswith("| 10-") or "TRADE BUY" not in line:
            continue
        fields = [x.strip() for x in line.split("|")]
        # Markdown table: empty, date, type, market, outcome, $, shares, price, tx, empty.
        if len(fields) < 9:
            raise ValueError(f"Broken Thin row: {line[:100]}")
        m = re.fullmatch(r"10-(\d{2}) (\d{2}):(\d{2}):(\d{2})", fields[1])
        if m is None:
            raise ValueError(f"Unexpected transaction date: {fields[1]}")
        day, hour, minute, second = map(int, m.groups())
        when = datetime(2026, 10, day, hour, minute, second, tzinfo=timezone.utc)
        if when >= CUTOFF or fields[4] not in EXPECTED:
            continue
        amount = Decimal(fields[6].replace(" ", "").replace(",", "."))
        totals[fields[4]] += amount
        count += 1
    return totals, count


def main() -> None:
    totals, count = parse_ledger(CASE.read_text(encoding="utf-8"))
    if totals != EXPECTED:
        raise SystemExit(
            f"Thin case mismatch before {CUTOFF.isoformat()}: {totals} != {EXPECTED}"
        )
    if count != 49:
        raise SystemExit(f"Expected 49 matchup BUY lines, found {count}")
    for outcome in EXPECTED:
        print(f"{outcome}: {totals[outcome]} shares (published Thin ledger)")
    print(f"PASS: {count} parsed matching BUY rows before {CUTOFF.isoformat()}")
    print("Not fresh RPC evidence; not verification of X post or screenshot.")


if __name__ == "__main__":
    main()
