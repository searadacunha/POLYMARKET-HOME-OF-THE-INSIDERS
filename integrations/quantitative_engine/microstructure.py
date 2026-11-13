"""Causal book state and print features.

A book row is what was displayed. A print is a venue execution report. A
transaction hash on a print is an identifier supplied by the venue, not a
receipt this module has checked. None of these objects identifies a wallet.
"""

from __future__ import annotations

import bisect
from decimal import Decimal

# Locked before the 2026-10-11 science/economy/earnings hours were scored.
SIZE_1E6 = 50_000_000
NOTIONAL_PRODUCT = 200_000_000_000
MOVE_1E4 = 200
OUTCOME_LO_MS = 60_000
OUTCOME_HI_MS = 180_000


def _touch(levels_bid, levels_ask):
    bids = [(price, size) for price, size in levels_bid if size > 0]
    asks = [(price, size) for price, size in levels_ask if size > 0]
    if not bids or not asks:
        return None
    bid, bid_size = max(bids)
    ask, ask_size = min(asks)
    if bid >= ask:
        return None
    return bid, bid_size, ask, ask_size


def score_events(events: list[dict]) -> list[dict]:
    """Score venue prints using only book state strictly before each print.

    Outcome quotes are stored separately and are not readable from the signal
    fields. ``moved`` is an evaluation label, not a feature.
    """
    books = {}
    quotes = {}
    prints = []
    for event in events:
        kind = event["kind"]
        asset = event["asset"]
        if kind == "BOOK":
            touch = _touch(event.get("bids") or (), event.get("asks") or ())
            if touch is None:
                continue
            bid, bid_size, ask, ask_size = touch
            stamp = (event["ts"], event["ordinal"])
            books.setdefault(asset, []).append((*stamp, bid, bid_size, ask, ask_size))
            quotes.setdefault(asset, []).append((*stamp, bid, ask))
        elif kind == "QUOTE":
            bid, ask = event.get("best_bid"), event.get("best_ask")
            if type(bid) is not int or type(ask) is not int or bid >= ask:
                continue
            quotes.setdefault(asset, []).append((event["ts"], event["ordinal"], bid, ask))
        elif kind == "PRINT":
            prints.append(event)
        else:
            raise ValueError(f"unknown event kind {kind}")

    for asset in books:
        books[asset].sort()
    for asset in quotes:
        quotes[asset].sort()
    prints.sort(key=lambda event: (event["ts"], event["ordinal"], event.get("tx") or ""))

    seen = set()
    unique = []
    for event in prints:
        tx = event.get("tx")
        key = (tx, event["asset"])
        if tx and key in seen:
            continue
        if tx:
            seen.add(key)
        unique.append(event)

    previous = {}
    scored = []
    for event in unique:
        asset = event["asset"]
        book = books.get(asset) or ()
        position = bisect.bisect_left(book, (event["ts"], event["ordinal"]))
        snapshot = book[position - 1] if position else None
        spread = depth = mid = None
        if snapshot is not None:
            _ts, _ordinal, bid, bid_size, ask, ask_size = snapshot
            spread = ask - bid
            mid = (bid + ask) // 2
            if event.get("side") == "BUY":
                depth = ask_size
            elif event.get("side") == "SELL":
                depth = bid_size
        quote = quotes.get(asset) or ()
        start = bisect.bisect_left(quote, (event["ts"] + OUTCOME_LO_MS, -10**18))
        outcome = None
        if start < len(quote) and quote[start][0] <= event["ts"] + OUTCOME_HI_MS:
            outcome = (quote[start][2] + quote[start][3]) // 2
        moved = None
        if mid is not None and outcome is not None and event.get("side") in ("BUY", "SELL"):
            delta = outcome - mid
            if event["side"] == "SELL":
                delta = -delta
            moved = delta >= MOVE_1E4
        gap = None if asset not in previous else event["ts"] - previous[asset]
        previous[asset] = event["ts"]
        price, size = event.get("price"), event.get("size")
        product = None if type(price) is not int or type(size) is not int else price * size
        eligible = type(size) is int and (
            size >= SIZE_1E6 or (product is not None and product >= NOTIONAL_PRODUCT)
        )
        consumption = None
        if type(depth) is int and depth > 0 and type(size) is int:
            consumption = str(Decimal(size) / Decimal(depth))
        scored.append({
            "object_kind": "VENUE_PRINT",
            "hour": event.get("hour"),
            "split": event.get("split"),
            "category": event.get("category"),
            "market": event.get("market"),
            "asset": asset,
            "tx": event.get("tx"),
            "ts": event["ts"],
            "side": event.get("side"),
            "price_1e4": price,
            "size_1e6": size,
            "eligible_size": eligible,
            "spread_1e4": spread,
            "depth_1e6": depth,
            "mid_1e4": mid,
            "consumption": consumption,
            "outcome_mid_1e4": outcome,
            "moved": moved,
            "burst_gap_ms": gap,
            "witness": event.get("witness"),
            "wallet": None,
            "chain_receipt_checked": False,
        })
    return scored
