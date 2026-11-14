"""Trade pagination and the Polygon receipt queue.

`/v2/trades` is newest-first. A poll walks the cursor until it reaches the
stored high-water mark for that market. A page cap that stops short is a gap,
not an empty tape. The documented ceiling on this route is 300 requests / 10 s
(https://docs.polymarket.com/api-reference/rate-limits, read 2026-11-13).
This client stays near 4 requests/s and honors Retry-After on 429 and 503.
"""

from __future__ import annotations

import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request

TRADE_URL = "https://data-api.polymarket.com/v2/trades?condition={condition}"
POLYGON = "https://polygon-bor-rpc.publicnode.com"
TRADE_INTERVAL = 0.25
POLYGON_INTERVAL = 0.5
POLL_SECONDS = 90
PAGE_CAP = 4
TOPICS = {
    "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee": "v2_order_filled",
    "0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6": "v1_order_filled",
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "erc20_transfer",
}


class Pace:
    """Minimum spacing between calls, plus a one-shot delay after a 429."""

    def __init__(self, interval: float):
        self.interval = interval
        self._next = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            delay = self._next - time.time()
            if delay > 0:
                time.sleep(delay)
            self._next = time.time() + self.interval

    def delay(self, seconds: float) -> None:
        with self._lock:
            self._next = max(self._next, time.time() + seconds)


def fetch_json(url: str, pace: Pace, data: bytes | None = None, opener=None, attempts: int = 4):
    opener = opener or urllib.request.urlopen
    headers = {"User-Agent": "research-client/1.0", "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    last = None
    for attempt in range(attempts):
        pace.wait()
        request = urllib.request.Request(url, data=data, headers=headers)
        try:
            with opener(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            last = exc
            if exc.code in (429, 503) and attempt + 1 < attempts:
                raw = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    delay = float(raw) if raw else float(2 ** attempt)
                except (TypeError, ValueError):
                    delay = float(2 ** attempt)
                pace.delay(min(max(delay, 1.0), 30.0))
                continue
            raise
    if last:
        raise last
    raise RuntimeError(url)


def parse_trade_page(payload: dict) -> dict:
    pagination = payload.get("pagination") or {}
    return {
        "data": payload.get("data") or [],
        "has_more": bool(pagination.get("has_more")),
        "next_cursor": pagination.get("next_cursor"),
    }


def trade_fetcher(condition: str, pace: Pace, opener=None):
    quoted = urllib.parse.quote(condition, safe="")

    def fetch(cursor):
        url = TRADE_URL.format(condition=quoted) + "&limit=1000"
        if cursor:
            url += "&cursor=" + urllib.parse.quote(str(cursor), safe="")
        return parse_trade_page(fetch_json(url, pace, opener=opener))

    return fetch


def trade_key(row: dict) -> str:
    tx_hash = row.get("transaction_hash", row.get("tx"))
    wallet = row.get("proxy_wallet", row.get("wallet"))
    return str(tx_hash or "") + str(wallet or "") + str(row.get("side") or "")


def _blank_mark(mark: dict | None) -> dict:
    mark = mark or {}
    return {
        "t": mark.get("t"),
        "tx": mark.get("tx"),
        "cursor": mark.get("cursor"),
        "tip_t": mark.get("tip_t"),
        "tip_tx": mark.get("tip_tx"),
    }


def walk_trades(fetch_page, mark: dict | None, seen, floor: float | None, page_cap: int = PAGE_CAP) -> dict:
    """Walk newest-first pages until the high-water mark, or until `page_cap`.

    `seen` is a predicate. Rows it accepts are not returned again. The mark's
    timestamp and tx advance only when the walk reaches the previous mark (or
    the collector floor, when no mark exists). A cap before that leaves `cursor`
    set and `complete` false.
    """
    mark = _blank_mark(mark)
    pages = 0
    rows = []
    newest = None
    reached = False
    local = set()

    def handle(row: dict, stop_tip: bool) -> str:
        nonlocal newest, reached
        raw_time = row.get("timestamp", row.get("t"))
        if raw_time is None:
            return "skip"
        stamp = int(raw_time)
        tx_hash = str(row.get("transaction_hash") or row.get("tx") or "")
        if newest is None:
            newest = {"t": stamp, "tx": tx_hash}
        if mark["t"] is not None and (stamp < mark["t"] or (stamp == mark["t"] and tx_hash == mark["tx"])):
            reached = True
            return "stop"
        if mark["t"] is None and floor is not None and stamp < floor:
            reached = True
            return "stop"
        if stop_tip and mark["tip_t"] is not None and (
            stamp < mark["tip_t"] or (stamp == mark["tip_t"] and tx_hash == mark["tip_tx"])
        ):
            return "tip"
        key = trade_key(row)
        if key not in local and not seen(key):
            local.add(key)
            rows.append(row)
        return "ok"

    def pull(cursor, stop_tip: bool):
        nonlocal pages, reached
        while pages < page_cap:
            payload = fetch_page(cursor)
            pages += 1
            data = payload.get("data") or []
            if not data:
                reached = True
                return None
            for row in data:
                action = handle(row, stop_tip)
                if action in ("stop", "tip"):
                    return None
            if not payload.get("has_more"):
                reached = True
                return None
            cursor = payload.get("next_cursor")
            if not cursor:
                reached = True
                return None
        return cursor

    saved = mark.get("cursor")
    if saved:
        pull(None, True)
        if not reached and pages < page_cap:
            mark["cursor"] = pull(saved, False)
        if reached:
            mark["cursor"] = None
    else:
        mark["cursor"] = pull(None, False)
        if reached:
            mark["cursor"] = None
    if newest:
        mark["tip_t"] = newest["t"]
        mark["tip_tx"] = newest["tx"]
    if reached and newest:
        mark["t"] = newest["t"]
        mark["tx"] = newest["tx"]
        mark["cursor"] = None
    return {"rows": rows, "complete": reached, "pages": pages, "mark": mark}


def coverage_row(condition: str, result: dict, now: float, error: str | None = None) -> dict:
    row = {
        "t": now,
        "condition": condition,
        "complete": bool(result.get("complete")) and error is None,
        "pages": result.get("pages", 0),
        "new_trades": len(result.get("rows") or []),
    }
    if error:
        row["error"] = error
    return row


def gap_row(condition: str, result: dict, now: float, floor: float | None) -> dict | None:
    """A page cap before the high-water mark. Absence of rows is not this gap."""
    if result.get("complete"):
        return None
    anchor = result["mark"].get("t")
    if anchor is None:
        anchor = floor
    gap_s = None if anchor is None else max(0, int(now - float(anchor)))
    return {
        "t": now,
        "gap_s": gap_s,
        "kind": "trade_page_cap",
        "condition": condition,
        "pages": result.get("pages", 0),
    }


class ReceiptQueue:
    """Tx hashes still needing a receipt. Done hashes and duplicates are refused."""

    def __init__(self, pending=(), done=()):
        self.done = set(done)
        self.pending = []
        self._pending = set()
        for tx_hash in pending:
            self.add(tx_hash)

    def add(self, tx_hash: str) -> bool:
        if not tx_hash or tx_hash in self.done or tx_hash in self._pending:
            return False
        self.pending.append(tx_hash)
        self._pending.add(tx_hash)
        return True

    def pop(self) -> str | None:
        while self.pending:
            tx_hash = self.pending.pop(0)
            self._pending.discard(tx_hash)
            if tx_hash in self.done:
                continue
            return tx_hash
        return None

    def ack(self, tx_hash: str) -> None:
        self.done.add(tx_hash)
        self._pending.discard(tx_hash)

    def requeue(self, tx_hash: str) -> None:
        self.add(tx_hash)


def receipt_families(tx_hash: str, pace: Pace, opener=None) -> list[str]:
    return load_receipt(tx_hash, pace, opener=opener)["families"]


CLOB_BOOKS = "https://clob.polymarket.com/books"
GAMMA_MARKET = "https://gamma-api.polymarket.com/markets?condition_ids={condition}"
# /books is documented at 500 requests / 10 s. One batch stays far under that.
BOOK_BATCH = 20


def fetch_no_tokens(specs: list[dict], pace: Pace, opener=None) -> list[dict]:
    """Return yes and no token ids. The markets file only stores the yes token."""
    pairs = []
    for spec in specs:
        yes = spec.get("yes_token")
        no = spec.get("no_token")
        condition = spec.get("condition_id")
        if no:
            pairs.append({"condition_id": condition, "yes_token": yes, "no_token": no})
            continue
        if not condition:
            continue
        url = GAMMA_MARKET.format(condition=urllib.parse.quote(condition, safe=""))
        payload = fetch_json(url, pace, opener=opener)
        row = payload[0] if isinstance(payload, list) and payload else {}
        outcomes = row.get("outcomes") or []
        tokens = row.get("clobTokenIds") or []
        if isinstance(outcomes, str):
            outcomes = json.loads(outcomes)
        if isinstance(tokens, str):
            tokens = json.loads(tokens)
        found = {str(name): str(token) for name, token in zip(outcomes, tokens)}
        pairs.append({
            "condition_id": condition,
            "yes_token": found.get("Yes") or yes,
            "no_token": found.get("No"),
        })
    return pairs


def fetch_official_books(token_ids: list[str], pace: Pace, opener=None) -> list[dict]:
    """Official CLOB snapshots. Each returned object is a book message."""
    books = []
    for start in range(0, len(token_ids), BOOK_BATCH):
        chunk = token_ids[start:start + BOOK_BATCH]
        body = json.dumps([{"token_id": token} for token in chunk]).encode()
        payload = fetch_json(CLOB_BOOKS, pace, data=body, opener=opener)
        if isinstance(payload, dict):
            payload = [payload]
        for item in payload or []:
            if isinstance(item, dict):
                item["event_type"] = item.get("event_type") or "book"
                books.append(item)
    return books


def load_receipt(tx_hash: str, pace: Pace, opener=None) -> dict:
    from .decode import decode_logs
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionReceipt", "params": [tx_hash],
    }).encode()
    payload = fetch_json(POLYGON, pace, data=body, opener=opener)
    logs = (payload.get("result") or {}).get("logs") or []
    return decode_logs(logs)
