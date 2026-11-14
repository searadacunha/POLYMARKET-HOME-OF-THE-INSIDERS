"""Decode public market messages and Polygon OrderFilled receipts.

The V2 topic and field order were checked on 2026-11-13 against a live
receipt and the exchange source: OrderFilled(bytes32,address,address,uint8,
uint256,uint256,uint256,uint256,bytes32,bytes32) on
0xe111180000d2663c0091e4f400237545b87b996b. The same topic was seen the same
day on the neg-risk exchange 0xe2222d279d744050d28e00520010520000310f59.
V2 does not log makerAssetId and takerAssetId as separate words. Those two
ids are derived from side and tokenId and marked as derived.
"""

from __future__ import annotations

DISK_FREE_BYTES = 5_000_000_000
DISK_USED_RATIO = 0.97
AMOUNT_SCALE = 1_000_000

V2_TOPIC = "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee"
V1_TOPIC = "0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6"
TRANSFER_TOPIC = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
FEE_TOPIC = "0x55bb3cade9d43b798a4fe5ffdd05024b2d7870df53920673bfc7e68047cd0ab1"
EXCHANGE_V2 = (
    "0xe111180000d2663c0091e4f400237545b87b996b",
    "0xe2222d279d744050d28e00520010520000310f59",
)
EXCHANGE_V1 = (
    "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e",
    "0xc5d563a36ae78145c45a50134d48a1215220f80a",
)


def disk_report(free: int, total: int) -> dict:
    used_ratio = (total - free) / total if total else None
    alert = free < DISK_FREE_BYTES or (used_ratio is not None and used_ratio >= DISK_USED_RATIO)
    return {
        "disk_free_bytes": free,
        "disk_used_ratio": None if used_ratio is None else round(used_ratio, 4),
        "disk_alert": alert,
        "disk_free_threshold_bytes": DISK_FREE_BYTES,
        "disk_used_threshold": DISK_USED_RATIO,
    }


def _text(value):
    if value is None:
        return None
    return value if isinstance(value, str) else str(value)


def _event(message: dict) -> str | None:
    return message.get("event_type") or message.get("type")


def _body(message: dict) -> dict:
    payload = message.get("payload")
    if isinstance(payload, dict) and _event(message) in ("price_change", "book", "last_trade_price"):
        return payload
    return message


def _market(message: dict, body: dict):
    return body.get("market") or body.get("conditionId") or message.get("market") or message.get("conditionId")


def _timestamp(message: dict, body: dict):
    return body.get("timestamp") or message.get("timestamp")


def _pick(item: dict, *names):
    for name in names:
        if item.get(name) is not None:
            return item.get(name)
    return None


def frame_account(message) -> dict:
    """Count every element of one websocket payload.

    A list is not one event. Each dict is decoded. A non-dict is rejected.
    A dict that produces no row is rejected too, so nothing disappears quietly.
    """
    if isinstance(message, list):
        elements = list(message)
    elif isinstance(message, dict):
        elements = [message]
    else:
        return {"received": 1, "stored": 0, "rejected": 1, "rows": [], "problems": [{"event_type": None, "reason": "not_object"}]}
    received = len(elements)
    stored = 0
    rejected = 0
    rows = []
    problems = []
    for element in elements:
        if not isinstance(element, dict):
            rejected += 1
            problems.append({"event_type": None, "reason": "not_object"})
            continue
        decoded, item_problems = decode_market(element)
        problems.extend(item_problems)
        if decoded:
            stored += 1
            rows.extend(decoded)
        else:
            rejected += 1
    return {"received": received, "stored": stored, "rejected": rejected, "rows": rows, "problems": problems}


def decode_market(message: dict) -> tuple[list[dict], list[dict]]:
    """Return filled rows and undecoded problems. A problem is not a market row."""
    if not isinstance(message, dict):
        return [], [{"event_type": None, "reason": "not_object"}]
    event = _event(message)
    body = _body(message)
    if event == "price_change":
        return _price_changes(message, body)
    if event == "book":
        return _book(message, body)
    if event == "last_trade_price":
        return _last_trade(message, body)
    return [], [{"event_type": event, "reason": "unsupported_event"}]


def _price_changes(message: dict, body: dict) -> tuple[list[dict], list[dict]]:
    nested = body.get("price_changes")
    if nested is None:
        nested = body.get("priceChanges")
    rows = []
    problems = []
    if isinstance(nested, list):
        if not nested and _pick(body, "asset_id", "assetId") is None:
            return [], [{"event_type": "price_change", "reason": "empty_price_changes"}]
        for item in nested:
            if not isinstance(item, dict):
                problems.append({"event_type": "price_change", "reason": "price_change_not_object"})
                continue
            row = _one_change(message, body, item)
            if row is None:
                problems.append({"event_type": "price_change", "reason": "price_change_missing_fields"})
            else:
                rows.append(row)
        if rows or problems:
            return rows, problems
    row = _one_change(message, body, body)
    if row is None:
        return [], [{"event_type": "price_change", "reason": "price_change_missing_fields"}]
    return [row], []


def _one_change(message: dict, body: dict, item: dict) -> dict | None:
    asset = _pick(item, "asset_id", "assetId")
    price = item.get("price")
    side = item.get("side")
    size = item.get("size")
    if asset is None or price is None or side is None or size is None:
        return None
    return {
        "event_type": "price_change",
        "market": _market(message, body),
        "asset_id": _text(asset),
        "price": _text(price),
        "size": _text(size),
        "side": side,
        "best_bid": _text(_pick(item, "best_bid", "bestBid")),
        "best_ask": _text(_pick(item, "best_ask", "bestAsk")),
        "hash": item.get("hash") or body.get("hash"),
        "timestamp": _timestamp(message, body),
    }


def _book(message: dict, body: dict) -> tuple[list[dict], list[dict]]:
    asset = _pick(body, "asset_id", "assetId")
    bids = body.get("bids")
    asks = body.get("asks")
    if asset is None or not isinstance(bids, list) or not isinstance(asks, list):
        return [], [{"event_type": "book", "reason": "book_missing_fields"}]
    levels_bid = _levels(bids)
    levels_ask = _levels(asks)
    if levels_bid is None or levels_ask is None:
        return [], [{"event_type": "book", "reason": "book_level_not_object"}]
    row = {
        "event_type": "book",
        "market": _market(message, body),
        "asset_id": _text(asset),
        "timestamp": _timestamp(message, body),
        "hash": body.get("hash"),
        "bids": levels_bid,
        "asks": levels_ask,
    }
    if body.get("tick_size") is not None:
        row["tick_size"] = _text(body.get("tick_size"))
    if body.get("last_trade_price") is not None:
        row["last_trade_price"] = _text(body.get("last_trade_price"))
    return [row], []


def _levels(raw: list) -> list[dict] | None:
    levels = []
    for level in raw:
        if not isinstance(level, dict) or level.get("price") is None or level.get("size") is None:
            return None
        levels.append({"price": _text(level["price"]), "size": _text(level["size"])})
    return levels


def _last_trade(message: dict, body: dict) -> tuple[list[dict], list[dict]]:
    asset = _pick(body, "asset_id", "assetId")
    price = body.get("price")
    if asset is None or price is None:
        return [], [{"event_type": "last_trade_price", "reason": "last_trade_missing_fields"}]
    row = {
        "event_type": "last_trade_price",
        "market": _market(message, body),
        "asset_id": _text(asset),
        "price": _text(price),
        "size": _text(body.get("size")),
        "side": body.get("side"),
        "timestamp": _timestamp(message, body),
    }
    fee = _pick(body, "fee_rate_bps", "feeRateBps")
    if fee is not None:
        row["fee_rate_bps"] = _text(fee)
    tx_hash = _pick(body, "transaction_hash", "transactionHash")
    if tx_hash is not None:
        row["transaction_hash"] = tx_hash
    return [row], []


def apply_levels(book: dict, change: dict) -> dict:
    """Return a new book after one price_change. BUY updates bids, SELL updates asks."""
    bids = dict(book.get("bids") or {})
    asks = dict(book.get("asks") or {})
    side = change.get("side")
    target = bids if side == "BUY" else asks if side == "SELL" else None
    if target is not None and change.get("price") is not None and change.get("size") is not None:
        price = str(change["price"])
        if float(change["size"]) == 0.0:
            target.pop(price, None)
        else:
            target[price] = str(change["size"])
    return {"bids": bids, "asks": asks}


def book_from_row(row: dict) -> dict:
    return {
        "bids": {str(level["price"]): str(level["size"]) for level in row.get("bids") or []},
        "asks": {str(level["price"]): str(level["size"]) for level in row.get("asks") or []},
    }


def best_price(levels: dict, high: bool):
    if not levels:
        return None
    return max(levels, key=lambda price: float(price)) if high else min(levels, key=lambda price: float(price))


def valid_snapshot(row: dict) -> bool:
    """A book is a reference only when the asset and both level lists are present."""
    return bool(
        isinstance(row, dict)
        and row.get("asset_id")
        and isinstance(row.get("bids"), list)
        and isinstance(row.get("asks"), list)
    )


def book_summary(row: dict) -> dict | None:
    if not valid_snapshot(row):
        return None
    bids = {str(level["price"]): str(level["size"]) for level in row["bids"]}
    asks = {str(level["price"]): str(level["size"]) for level in row["asks"]}
    bid = best_price(bids, True)
    ask = best_price(asks, False)
    return {
        "best_bid": bid,
        "best_bid_size": None if bid is None else bids[bid],
        "best_ask": ask,
        "best_ask_size": None if ask is None else asks[ask],
        "bid_levels": len(bids),
        "ask_levels": len(asks),
        "hash": row.get("hash") or None,
    }


def concordance(local: dict, official: dict, compare_hash: bool) -> dict:
    """Match the touch, the depth, and the hash only when both snapshots still have one."""
    hash_match = None
    if compare_hash and local.get("hash") and official.get("hash"):
        hash_match = local["hash"] == official["hash"]
    matched = (
        local.get("best_bid") == official.get("best_bid")
        and local.get("best_bid_size") == official.get("best_bid_size")
        and local.get("best_ask") == official.get("best_ask")
        and local.get("best_ask_size") == official.get("best_ask_size")
        and local.get("bid_levels") == official.get("bid_levels")
        and local.get("ask_levels") == official.get("ask_levels")
        and hash_match is not False
    )
    return {
        "synchronized": matched,
        "best_bid": local.get("best_bid") == official.get("best_bid"),
        "best_ask": local.get("best_ask") == official.get("best_ask"),
        "depth": local.get("bid_levels") == official.get("bid_levels") and local.get("ask_levels") == official.get("ask_levels"),
        "hash_match": hash_match,
    }


def _addr(topic: str) -> str:
    return "0x" + topic[-40:].lower()


def _words(data: str) -> list[int]:
    raw = data[2:] if data.startswith("0x") else data
    return [int(raw[index:index + 64], 16) for index in range(0, len(raw), 64)]


def decode_logs(logs: list[dict]) -> dict:
    fills = []
    transfers = []
    for log in logs:
        if log.get("removed"):
            continue
        topics = [str(topic).lower() for topic in (log.get("topics") or [])]
        if not topics:
            continue
        if topics[0] == V2_TOPIC and len(topics) == 4:
            fills.append(_fill_v2(log, topics))
        elif topics[0] == V1_TOPIC and len(topics) == 4:
            fills.append(_fill_v1(log, topics))
        elif topics[0] == TRANSFER_TOPIC and len(topics) >= 3:
            transfers.append({
                "token": str(log.get("address") or "").lower(),
                "from": _addr(topics[1]),
                "to": _addr(topics[2]),
                "amount": str(int(log.get("data") or "0x0", 16)),
                "log_index": _log_index(log),
            })
    families = []
    if transfers:
        families.append("erc20_transfer")
    if any(fill["version"] == "v2" for fill in fills):
        families.append("v2_order_filled")
    if any(fill["version"] == "v1" for fill in fills):
        families.append("v1_order_filled")
    return {"fills": fills, "transfers": transfers, "families": families}


def _log_index(log: dict):
    raw = log.get("logIndex")
    if raw is None:
        return None
    return int(raw, 16) if isinstance(raw, str) else int(raw)


def _fill_v2(log: dict, topics: list[str]) -> dict:
    words = _words(log.get("data") or "0x")
    side_raw = words[0] if words else None
    side = "BUY" if side_raw == 0 else "SELL" if side_raw == 1 else None
    token = str(words[1]) if len(words) > 1 else None
    maker_amount = str(words[2]) if len(words) > 2 else None
    taker_amount = str(words[3]) if len(words) > 3 else None
    fee = str(words[4]) if len(words) > 4 else None
    if side == "BUY":
        maker_asset, taker_asset = "0", token
    elif side == "SELL":
        maker_asset, taker_asset = token, "0"
    else:
        maker_asset = taker_asset = None
    return {
        "version": "v2",
        "exchange": str(log.get("address") or "").lower(),
        "log_index": _log_index(log),
        "order_hash": topics[1],
        "maker": _addr(topics[2]),
        "taker": _addr(topics[3]),
        "side": side,
        "token_id": token,
        "maker_amount_filled": maker_amount,
        "taker_amount_filled": taker_amount,
        "fee": fee,
        "builder": _word_hex(words, 5),
        "metadata": _word_hex(words, 6),
        "maker_asset_id": maker_asset,
        "taker_asset_id": taker_asset,
        "asset_ids_derived": True,
    }


def _fill_v1(log: dict, topics: list[str]) -> dict:
    words = _words(log.get("data") or "0x")
    maker_asset = str(words[0]) if words else None
    taker_asset = str(words[1]) if len(words) > 1 else None
    maker_amount = str(words[2]) if len(words) > 2 else None
    taker_amount = str(words[3]) if len(words) > 3 else None
    fee = str(words[4]) if len(words) > 4 else None
    if maker_asset == "0":
        side, token, shares = "BUY", taker_asset, taker_amount
    else:
        side, token, shares = "SELL", maker_asset, maker_amount
    return {
        "version": "v1",
        "exchange": str(log.get("address") or "").lower(),
        "log_index": _log_index(log),
        "order_hash": topics[1],
        "maker": _addr(topics[2]),
        "taker": _addr(topics[3]),
        "side": side,
        "token_id": token,
        "maker_amount_filled": maker_amount,
        "taker_amount_filled": taker_amount,
        "fee": fee,
        "maker_asset_id": maker_asset,
        "taker_asset_id": taker_asset,
        "asset_ids_derived": False,
        "share_amount": shares,
    }


def _word_hex(words: list[int], index: int):
    if len(words) <= index:
        return None
    return "0x" + format(words[index], "064x")


def _share_amount(fill: dict):
    if fill.get("version") == "v1":
        return fill.get("share_amount")
    if fill.get("side") == "SELL":
        return fill.get("maker_amount_filled")
    if fill.get("side") == "BUY":
        return fill.get("taker_amount_filled")
    return None


def _collateral_amount(fill: dict):
    if fill.get("side") == "SELL":
        return fill.get("taker_amount_filled")
    if fill.get("side") == "BUY":
        return fill.get("maker_amount_filled")
    return None


def attribute_trade(trade: dict, decoded: dict) -> dict:
    """Link one API trade to OrderFilled logs of the same transaction.

    Confirmed means one economic fill: the wallet is maker or taker, the
    token matches, and the share amount matches. Two logs with the same
    shares and the same collateral are the two sides of that fill, not two
    trades. Anything else stays ambiguous or not_found.
    """
    wallet = str(trade.get("wallet") or "").lower()
    asset = str(trade.get("asset_id") or "")
    size = trade.get("size")
    if not wallet or not asset or size is None:
        return {"status": "ambiguous", "reason": "trade_fields_missing", "log_indexes": []}
    try:
        want = int(round(float(size) * AMOUNT_SCALE))
    except (TypeError, ValueError):
        return {"status": "ambiguous", "reason": "trade_size_unreadable", "log_indexes": []}
    matches = []
    wallet_in_fill = False
    for fill in decoded.get("fills") or []:
        parties = {fill.get("maker"), fill.get("taker")}
        if wallet in parties:
            wallet_in_fill = True
        shares = _share_amount(fill)
        if wallet in parties and fill.get("token_id") == asset and shares is not None:
            got = int(shares)
            if abs(got - want) <= max(1000, int(abs(want) * 0.001)):
                matches.append(fill)
    wallet_in_transfer = any(
        wallet in {item.get("from"), item.get("to")} for item in decoded.get("transfers") or []
    )
    if not matches:
        if wallet_in_fill or wallet_in_transfer:
            return {"status": "ambiguous", "reason": "wallet_seen_amount_unmatched", "log_indexes": []}
        return {"status": "not_found", "reason": "wallet_absent", "log_indexes": []}
    collaterals = {_collateral_amount(fill) for fill in matches}
    indexes = [fill.get("log_index") for fill in matches]
    if len(collaterals) == 1:
        reason = "paired_fills" if len(matches) > 1 else "single_fill"
        return {"status": "confirmed", "reason": reason, "log_indexes": indexes}
    return {"status": "ambiguous", "reason": "several_prices", "log_indexes": indexes}


def decode_frame(payload):
    """Decode every independent object in one WebSocket frame, including batches."""
    frames = payload if isinstance(payload, list) else [payload]
    for frame in frames:
        if not isinstance(frame, dict):
            continue
        rows, problems = decode_market(frame)
        yield frame, rows, problems
