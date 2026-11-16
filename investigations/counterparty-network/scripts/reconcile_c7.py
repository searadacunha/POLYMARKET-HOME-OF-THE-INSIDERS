#!/usr/bin/env python3
"""Independently recompute archived C7 pair-trade arithmetic; never claim RPC verification."""
import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
SOURCE = REPO / "research_notes/early-detection-2026-11-13/data/c7_intra_group_trades.csv"
CENTS = Decimal("0.01")
FIELDS = {"utc", "tx", "seller", "buyers", "shares", "usd", "price"}


def fixed(value):
    return str(value.quantize(CENTS))


def reconcile(path=SOURCE):
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        if not reader.fieldnames or not FIELDS.issubset(reader.fieldnames):
            raise ValueError("Missing required archive columns")
        rows = list(reader)
    if not rows:
        raise ValueError("Empty trade archive")
    transactions = set()
    buyers = defaultdict(lambda: {"trades": 0, "shares": Decimal(0), "usd": Decimal(0)})
    shares_total = Decimal(0)
    usd_total = Decimal(0)
    sellers = set()
    for row in rows:
        tx = row["tx"].lower()
        if len(tx) != 66 or not tx.startswith("0x") or any(c not in "0123456789abcdef" for c in tx[2:]):
            raise ValueError("Invalid transaction hash")
        if tx in transactions:
            raise ValueError("Duplicate transaction hash")
        transactions.add(tx)
        seller, buyer = row["seller"].strip(), row["buyers"].strip()
        if not seller or not buyer or seller == buyer or "," in buyer:
            raise ValueError("Invalid or ambiguous archived parties")
        sellers.add(seller)
        qty, cash, price = (Decimal(row[k]) for k in ("shares", "usd", "price"))
        if min(qty, cash, price) <= 0 or abs(qty * price - cash) > Decimal("0.02"):
            raise ValueError("Archived shares and cash do not reconcile to execution price")
        buyers[buyer]["trades"] += 1
        buyers[buyer]["shares"] += qty
        buyers[buyer]["usd"] += cash
        shares_total += qty
        usd_total += cash
    if len(sellers) != 1:
        raise ValueError("Archive contains more than one seller")
    return {
        "status": "ARCHIVE_RECALCULATION_ONLY",
        "source": str(SOURCE.relative_to(REPO)),
        "trade_count": len(rows),
        "seller": next(iter(sellers)),
        "buyer_count": len(buyers),
        "shares": fixed(shares_total),
        "usd": fixed(usd_total),
        "by_buyer": [
            {"buyer": name, "trades": buyers[name]["trades"],
             "shares": fixed(buyers[name]["shares"]), "usd": fixed(buyers[name]["usd"])}
            for name in sorted(buyers)
        ],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(reconcile(args.input), indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(report, encoding="utf-8")
    else:
        print(report, end="")


if __name__ == "__main__":
    main()
