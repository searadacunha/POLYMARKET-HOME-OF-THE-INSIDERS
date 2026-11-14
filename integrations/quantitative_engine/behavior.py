"""Four wallet-behavior rules. Thresholds are fixed in this file, not fit on validation.

Only a cursor-exhausted tape is scored. A capped tape is reported as incomplete.
A price move is the target. It is not evidence of non-public information.
"""

from __future__ import annotations

MOVE = 0.15
HOUR = 3600
MIN_CASH = 1000.0
SYNC_CASH = 200.0
SYNC_WALLETS = 3
SYNC_WINDOW = 600
CONCENTRATION = 0.5


def _buys(rows, start, end, outcome=None):
    kept = []
    for row in rows:
        if row["side"] != "BUY" or not (start < row["t"] <= end):
            continue
        if outcome is not None and row["outcome"] != outcome:
            continue
        kept.append(row)
    return kept


def _sold(rows, wallet, start, end) -> bool:
    return any(row["w"] == wallet and row["side"] == "SELL" and start < row["t"] <= end for row in rows)


def alerts_at(rows, stamp: int) -> dict:
    """Rules at `stamp`, using trades at or before it."""
    hour = _buys(rows, stamp - HOUR, stamp)
    cash = sum(row["size"] * row["price"] for row in hour)
    prior = []
    for step in range(1, 7):
        bucket = _buys(rows, stamp - (step + 1) * HOUR, stamp - step * HOUR)
        prior.append(sum(row["size"] * row["price"] for row in bucket))
    prior.sort()
    median = prior[len(prior) // 2] if prior else 0.0
    covered = any(row["t"] <= stamp - 3 * HOUR for row in rows)
    volume = covered and cash >= MIN_CASH and cash >= 3 * median
    by_wallet = {}
    for row in hour:
        by_wallet[row["w"]] = by_wallet.get(row["w"], 0.0) + row["size"] * row["price"]
    top = max(by_wallet, key=by_wallet.get) if by_wallet else None
    share = (by_wallet[top] / cash) if top and cash else 0.0
    concentration = bool(top) and cash >= MIN_CASH and share >= CONCENTRATION and not _sold(rows, top, stamp - HOUR, stamp)
    first = {}
    for row in rows:
        if row["t"] <= stamp:
            first[row["w"]] = min(row["t"], first.get(row["w"], row["t"]))
    fresh = False
    for wallet, born in first.items():
        if stamp - HOUR * 24 < born <= stamp and not _sold(rows, wallet, born, stamp):
            bought = sum(row["size"] * row["price"] for row in rows if row["w"] == wallet and row["side"] == "BUY" and born <= row["t"] <= stamp)
            if bought >= MIN_CASH:
                fresh = True
                break
    recent = _buys(rows, stamp - SYNC_WINDOW, stamp)
    per_outcome = {}
    for row in recent:
        if _sold(rows, row["w"], stamp - SYNC_WINDOW, stamp):
            continue
        slot = per_outcome.setdefault(row["outcome"], {})
        slot[row["w"]] = slot.get(row["w"], 0.0) + row["size"] * row["price"]
    synced = any(sum(value >= SYNC_CASH for value in wallets.values()) >= SYNC_WALLETS for wallets in per_outcome.values())
    return {
        "volume": volume,
        "new_wallet": fresh,
        "sync": synced,
        "concentration": concentration,
    }
