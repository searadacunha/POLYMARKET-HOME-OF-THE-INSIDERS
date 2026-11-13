"""Prospective collector for a machine that stays on.

    python3 -m pip install -r monitoring/livecollect/requirements.txt
    python3 -m monitoring.livecollect collect --markets markets.json --out /var/phi
    python3 -m monitoring.livecollect status --out /var/phi

Market messages come from the public CLOB websocket. Trades are polled on
their own loop, paging back to a per-market high-water mark. Every new
transaction hash is queued for a Polygon receipt. Nothing here is a permanent
monitor: this process stops when the machine or the supervisor stops.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import threading
import time
import urllib.error
from collections import OrderedDict
from pathlib import Path

from .trades import (
    PAGE_CAP,
    POLL_SECONDS,
    POLYGON_INTERVAL,
    TRADE_INTERVAL,
    Pace,
    ReceiptQueue,
    coverage_row,
    gap_row,
    receipt_families,
    trade_fetcher,
    trade_key,
    walk_trades,
)

WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
SEEN_LIMIT = 20000
RECEIPT_ATTEMPTS = 5


def _now() -> float:
    return time.time()


class Seen:
    """Insertion-ordered dedup keys. The oldest key is dropped past the limit."""

    def __init__(self, keys=(), limit: int = SEEN_LIMIT):
        self.limit = limit
        self._keys: OrderedDict = OrderedDict((key, None) for key in keys)

    def add(self, key: str) -> bool:
        if key in self._keys:
            self._keys.move_to_end(key)
            return False
        self._keys[key] = None
        while len(self._keys) > self.limit:
            self._keys.popitem(last=False)
        return True

    def __contains__(self, key: str) -> bool:
        return key in self._keys

    def tail(self, count: int = 2000) -> list:
        return list(self._keys)[-count:]


_write_lock = threading.Lock()


def _append(path: Path, row: dict) -> None:
    line = json.dumps(row, sort_keys=True) + "\n"
    with _write_lock:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(line)


def _state(out: Path) -> dict:
    path = out / "state.json"
    if not path.exists():
        return {"seen": [], "started": _now(), "restarts": 0}
    return json.loads(path.read_text(encoding="utf-8"))


def _save(out: Path, state: dict) -> None:
    temporary = out / "state.json.tmp"
    temporary.write_text(json.dumps(state), encoding="utf-8")
    temporary.replace(out / "state.json")


def _remember_trades(path: Path, seen: Seen) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        seen.add(str(row.get("tx") or "") + str(row.get("wallet") or "") + str(row.get("side") or ""))


def _remember_receipts(path: Path, queue: ReceiptQueue) -> None:
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        tx_hash = json.loads(line).get("tx")
        if tx_hash:
            queue.ack(str(tx_hash))


def collect(markets: Path, out: Path, seconds: float, poll_seconds: float = POLL_SECONDS) -> None:
    import asyncio
    import websockets

    out.mkdir(parents=True, exist_ok=True)
    specs = json.loads(markets.read_text(encoding="utf-8"))
    tokens = [item["yes_token"] for item in specs if item.get("yes_token")]
    conditions = [item["condition_id"] for item in specs if item.get("condition_id")]
    state = _state(out)
    state["restarts"] = int(state.get("restarts", 0)) + 1
    market_seen = Seen(state.get("seen_market") or [])
    trade_seen = Seen(state.get("seen_trades") or [], limit=200000)
    _remember_trades(out / "trades.jsonl", trade_seen)
    marks = dict(state.get("hwm") or {})
    queue = ReceiptQueue(state.get("receipt_queue") or [])
    _remember_receipts(out / "chain.jsonl", queue)
    failures = {str(key): int(value) for key, value in (state.get("receipt_failures") or {}).items()}
    lock = threading.Lock()
    trade_pace = Pace(TRADE_INTERVAL)
    polygon_pace = Pace(POLYGON_INTERVAL)
    floor = float(state.get("started") or _now())
    _save(out, state)
    deadline = _now() + seconds
    last_message = _now()

    def _checkpoint() -> None:
        with lock:
            state["seen_market"] = market_seen.tail(5000)
            state["seen_trades"] = trade_seen.tail(100000)
            state["hwm"] = marks
            state["receipt_queue"] = list(queue.pending)
            state["receipt_failures"] = failures
            state["last_seen"] = _now()
            _save(out, state)

    def _poll_cycle() -> None:
        complete = incomplete = fresh = 0
        for condition in conditions:
            now = _now()
            try:
                result = walk_trades(
                    trade_fetcher(condition, trade_pace),
                    marks.get(condition),
                    lambda key, seen=trade_seen: key in seen,
                    floor,
                    PAGE_CAP,
                )
                error = None
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                result = {"rows": [], "complete": False, "pages": 0, "mark": marks.get(condition) or {}}
                error = type(exc).__name__
                _append(out / "errors.jsonl", {"t": now, "error": error, "condition": condition})
            with lock:
                written = 0
                for trade in result["rows"]:
                    tx_hash = str(trade.get("transaction_hash") or "")
                    if not trade_seen.add(trade_key(trade)):
                        continue
                    trade_time = trade.get("timestamp")
                    lag = None
                    if isinstance(trade_time, (int, float)):
                        lag = round(_now() - float(trade_time), 1)
                    _append(out / "trades.jsonl", {
                        "received": _now(),
                        "t": trade_time,
                        "lag_s": lag,
                        "wallet": trade.get("proxy_wallet"),
                        "side": trade.get("side"),
                        "outcome": trade.get("outcome"),
                        "tx": tx_hash,
                        "condition": condition,
                    })
                    if tx_hash.startswith("0x"):
                        queue.add(tx_hash)
                    written += 1
                if error is None:
                    marks[condition] = result["mark"]
                _append(out / "coverage.jsonl", coverage_row(condition, result, now, error))
                gap = None if error else gap_row(condition, result, now, floor)
                if gap:
                    _append(out / "gaps.jsonl", gap)
                    incomplete += 1
                elif error:
                    incomplete += 1
                else:
                    complete += 1
                fresh += written
        _checkpoint()
        print(
            f"trades complete={complete} incomplete={incomplete} new={fresh} queue={len(queue.pending)}",
            flush=True,
        )

    def _drain_one() -> bool:
        with lock:
            tx_hash = queue.pop()
        if not tx_hash:
            return False
        try:
            families = receipt_families(tx_hash, polygon_pace)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            with lock:
                count = failures.get(tx_hash, 0) + 1
                failures[tx_hash] = count
                if count >= RECEIPT_ATTEMPTS:
                    queue.ack(tx_hash)
                    _append(out / "errors.jsonl", {"t": _now(), "error": type(exc).__name__, "where": "polygon", "tx": tx_hash, "dropped": True})
                else:
                    queue.requeue(tx_hash)
                    _append(out / "errors.jsonl", {"t": _now(), "error": type(exc).__name__, "where": "polygon", "tx": tx_hash})
            _checkpoint()
            return True
        with lock:
            _append(out / "chain.jsonl", {"t": _now(), "tx": tx_hash, "families": families})
            queue.ack(tx_hash)
            failures.pop(tx_hash, None)
        _checkpoint()
        return True

    async def _run() -> None:
        nonlocal last_message
        stop = asyncio.Event()

        async def _pulse() -> None:
            while not stop.is_set() and _now() < deadline:
                _append(out / "heartbeats.jsonl", {"t": _now()})
                _checkpoint()
                await asyncio.sleep(10)

        async def _trade_loop() -> None:
            while not stop.is_set() and _now() < deadline:
                await asyncio.to_thread(_poll_cycle)
                remaining = poll_seconds
                while remaining > 0 and not stop.is_set() and _now() < deadline:
                    step = min(1.0, remaining)
                    await asyncio.sleep(step)
                    remaining -= step

        async def _receipt_loop() -> None:
            while not stop.is_set() and _now() < deadline:
                worked = await asyncio.to_thread(_drain_one)
                if not worked:
                    await asyncio.sleep(1)

        async def _socket() -> None:
            nonlocal last_message
            async with websockets.connect(WS_URL, open_timeout=20) as socket:
                await socket.send(json.dumps({"assets_ids": tokens, "type": "market"}))
                while not stop.is_set() and _now() < deadline:
                    try:
                        raw = await asyncio.wait_for(socket.recv(), timeout=15)
                    except asyncio.TimeoutError:
                        gap = _now() - last_message
                        _append(out / "gaps.jsonl", {"t": _now(), "gap_s": round(gap, 1)})
                        continue
                    received = _now()
                    last_message = received
                    if isinstance(raw, bytes):
                        raw = raw.decode("utf-8", "replace")
                    if raw == "ping":
                        await socket.send("pong")
                        continue
                    try:
                        message = json.loads(raw)
                    except json.JSONDecodeError:
                        _append(out / "errors.jsonl", {"t": received, "error": "bad_json"})
                        continue
                    rows = message if isinstance(message, list) else [message]
                    for row in rows:
                        if not isinstance(row, dict):
                            continue
                        key = hashlib.sha256(json.dumps(row, sort_keys=True, default=str).encode()).hexdigest()
                        with lock:
                            if not market_seen.add(key):
                                continue
                            _append(out / "market.jsonl", {
                                "received": received,
                                "event_type": row.get("event_type"),
                                "asset_id": row.get("asset_id"),
                                "price": row.get("price"),
                                "best_bid": row.get("best_bid"),
                                "best_ask": row.get("best_ask"),
                            })

        pulse = asyncio.create_task(_pulse())
        trades = asyncio.create_task(_trade_loop())
        receipts = asyncio.create_task(_receipt_loop())
        try:
            await _socket()
        finally:
            stop.set()
            for task in (pulse, trades, receipts):
                task.cancel()
            await asyncio.gather(pulse, trades, receipts, return_exceptions=True)
            _checkpoint()

    try:
        asyncio.run(_run())
    except Exception as exc:
        _append(out / "errors.jsonl", {"t": _now(), "error": type(exc).__name__, "detail": str(exc)[:200]})
        _checkpoint()


def _rows(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except json.JSONDecodeError:
            continue


def _count(out: Path, name: str) -> int:
    return sum(1 for _ in _rows(out / name))


def _coverage(out: Path) -> dict:
    path = out / "heartbeats.jsonl"
    times = []
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                times.append(float(json.loads(line)["t"]))
    if len(times) < 2:
        return {"observed_online_s": 0.0, "observed_wall_s": 0.0, "max_gap_s": None, "uptime_ratio": None}
    online = 0.0
    widest = 0.0
    for earlier, later in zip(times, times[1:]):
        delta = later - earlier
        if 0 < delta <= 15:
            online += delta
        widest = max(widest, delta)
    wall = times[-1] - times[0]
    return {
        "observed_online_s": round(online, 1),
        "observed_wall_s": round(wall, 1),
        "max_gap_s": round(widest, 1),
        "uptime_ratio": round(online / wall, 3) if wall else None,
    }


def status(out: Path) -> dict:
    state = _state(out) if out.exists() else {}
    started = state.get("started")
    polls_complete = polls_incomplete = 0
    for row in _rows(out / "coverage.jsonl"):
        if row.get("complete"):
            polls_complete += 1
        else:
            polls_incomplete += 1
    fresh = 0
    if started is not None:
        for row in _rows(out / "trades.jsonl"):
            stamp = row.get("t")
            if isinstance(stamp, (int, float)) and float(stamp) >= float(started):
                fresh += 1
    report = {
        "started": started,
        "uptime_s": None if started is None else round(_now() - float(started), 1),
        "restarts": state.get("restarts", 0),
        "market_rows": _count(out, "market.jsonl"),
        "trade_rows": _count(out, "trades.jsonl"),
        "new_trades_after_start": fresh,
        "chain_rows": _count(out, "chain.jsonl"),
        "gaps": _count(out, "gaps.jsonl"),
        "polls_complete": polls_complete,
        "polls_incomplete": polls_incomplete,
        "receipt_queue": len(state.get("receipt_queue") or []),
        "errors": _count(out, "errors.jsonl"),
        "permanent": False,
    }
    report.update(_coverage(out))
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("collect", "status"))
    parser.add_argument("--markets", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=120)
    parser.add_argument("--trade-poll", type=float, default=POLL_SECONDS)
    args = parser.parse_args()
    if args.command == "status":
        print(json.dumps(status(args.out), indent=2))
        return
    if args.markets is None:
        raise SystemExit("collect requires --markets")
    collect(args.markets, args.out, args.seconds, args.trade_poll)


if __name__ == "__main__":
    main()
