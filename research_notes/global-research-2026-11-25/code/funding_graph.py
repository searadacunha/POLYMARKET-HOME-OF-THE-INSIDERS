"""Shared counterparties of the five Inca accounts in the archived flow file.

The file is the 6 November 2026 cross-check, not a new chain crawl. A blank
counterparty is ignored. Confidence is about the shared endpoint, not about
one person owning the wallets.
"""

import csv
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FLOWS = REPO / "research_notes/inca-crosscheck-2026-11-06/data/flows.csv"
INCA = (
    "0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a",
    "0xd5de5cad9ef22b16317fe30a4234c72ece3eac1a",
    "0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2",
    "0xcb18ea2923d957bd9cf049cce60a87638722f867",
    "0xa3a6fa49a39a4bf84cf510b7c8a2ab8be8508c44",
)
# Named in that report as services or as a customer-specific exchange deposit.
LABELS = {
    "0x93b7e169b93ece646d08cedbb8fa505796a5b96b": "bybit_deposit",
    "0xf0fc40a635a907ac93924f2d8c36b3e87afef52e": "service_f0fc",
    "0x1929347e025d4f5f8d6b2bd2261e2f4efcacd215": "service_1929",
    "0xf70da97812cb96acdf810712aa562db8dfa3dbef": "service_f70d",
}


def shared(path: Path = FLOWS) -> dict:
    buckets = defaultdict(lambda: defaultdict(lambda: {"n": 0, "usdc": Decimal("0"), "types": set()}))
    with path.open() as handle:
        for row in csv.DictReader(handle):
            wallet = row["wallet"].lower()
            if wallet not in INCA:
                continue
            counterparty = row["counterparty"].strip().lower()
            if not counterparty:
                continue
            cell = buckets[counterparty][wallet]
            cell["n"] += 1
            cell["usdc"] += Decimal(row["usdc"])
            cell["types"].add(row["type"])
    out = []
    for counterparty, wallets in sorted(buckets.items()):
        if len(wallets) < 2:
            continue
        out.append({
            "counterparty": counterparty,
            "label": LABELS.get(counterparty, "unlabelled"),
            "wallets": len(wallets),
            "usdc": format(sum((cell["usdc"] for cell in wallets.values()), Decimal("0")), "f"),
            "types": sorted({kind for cell in wallets.values() for kind in cell["types"]}),
        })
    return {"rows_considered_rule": "non-blank counterparty, five Inca wallets", "shared": out}
