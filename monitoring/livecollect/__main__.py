"""Prospective collector for a machine that stays on.

    python3 -m pip install -r monitoring/livecollect/requirements.txt
    python3 -m monitoring.livecollect collect --markets markets.json --out /var/phi
    python3 -m monitoring.livecollect status --out /var/phi

Market messages come from the public CLOB websocket. Wallet attribution comes
from the public trades API, a separate source. A few transaction hashes are
read back from a public Polygon endpoint. Nothing here is a permanent monitor:
this process stops when the machine or the supervisor stops.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import time
import urllib.error
import urllib.request
from collections import OrderedDict
from pathlib import Path

WS_URL = "wss://ws-subscriptions-clob.polymarket.com/ws/market"
TRADE_URL = "https://data-api.polymarket.com/v2/trades?condition={condition}&limit=200"
POLYGON = "https://polygon-bor-rpc.publicnode.com"
TOPICS = {
    "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee": "v2_order_filled",
    "0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6": "v1_order_filled",
    "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef": "erc20_transfer",
}
SEEN_LIMIT = 20000
CHAIN_CAP = 5


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

    def tail(self, count: int = 2000) -> list:
        return list(self._keys)[-count:]


def _append(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def _state(out: Path) -> dict:
    path = out / "state.json"
    if not path.exists():
        return {"seen": [], "started": _now(), "restarts": 0}
    return json.loads(path.read_text(encoding="utf-8"))


def _save(out: Path, state: dict) -> None:
    temporary = out / "state.json.tmp"
    temporary.write_text(json.dumps(state), encoding="utf-8")
    temporary.replace(out / "state.json")


def _trades(condition: str) -> list[dict]:
    request = urllib.request.Request(
        TRADE_URL.format(condition=condition),
        headers={"User-Agent": "research-client/1.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("data") or []


def _families(tx_hash: str) -> list[str]:
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "eth_getTransactionReceipt", "params": [tx_hash]}).encode()
    request = urllib.request.Request(
        POLYGON, data=body, headers={"Content-Type": "application/json", "User-Agent": "research-client/1.0"},
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    found = []
    for log in (payload.get("result") or {}).get("logs") or []:
        topics = [str(topic).lower() for topic in (log.get("topics") or [])]
        if topics and topics[0] in TOPICS and TOPICS[topics[0]] not in found:
            found.append(TOPICS[topics[0]])
    return found


def collect(markets: Path, out: Path, seconds: float) -> None:
    import asyncio
    import websockets

    out.mkdir(parents=True, exist_ok=True)
    specs = json.loads(markets.read_text(encoding="utf-8"))
    tokens = [item["yes_token"] for item in specs if item.get("yes_token")]
    state = _state(out)
    state["restarts"] = int(state.get("restarts", 0)) + 1
    market_seen = Seen(state.get("seen_market") or [])
    trade_seen = Seen(state.get("seen_trades") or [], limit=50000)
    _save(out, state)
    deadline = _now() + seconds
    last_message = _now()
    chain_budget = CHAIN_CAP

    def _checkpoint() -> None:
        state["seen_market"] = market_seen.tail(5000)
        state["seen_trades"] = trade_seen.tail(50000)
        state["last_seen"] = _now()
        _save(out, state)

    async def _run() -> None:
        nonlocal last_message
        async with websockets.connect(WS_URL, open_timeout=20) as socket:
            await socket.send(json.dumps({"assets_ids": tokens, "type": "market"}))

            async def _pulse() -> None:
                while _now() < deadline:
                    _append(out / "heartbeats.jsonl", {"t": _now()})
                    _checkpoint()
                    await asyncio.sleep(10)

            pulse = asyncio.create_task(_pulse())
            try:
                while _now() < deadline:
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
            finally:
                pulse.cancel()
                try:
                    await pulse
                except asyncio.CancelledError:
                    pass

    try:
        asyncio.run(_run())
    except Exception as exc:
        _append(out / "errors.jsonl", {"t": _now(), "error": type(exc).__name__, "detail": str(exc)[:200]})
    for item in specs:
        condition = item.get("condition_id")
        if not condition:
            continue
        try:
            for trade in _trades(condition):
                tx_hash = str(trade.get("transaction_hash") or "")
                key = tx_hash + str(trade.get("proxy_wallet") or "") + str(trade.get("side") or "")
                if not trade_seen.add(key):
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
                })
                if chain_budget > 0 and tx_hash.startswith("0x"):
                    chain_budget -= 1
                    try:
                        _append(out / "chain.jsonl", {"t": _now(), "tx": tx_hash, "families": _families(tx_hash)})
                    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
                        _append(out / "errors.jsonl", {"t": _now(), "error": type(exc).__name__, "where": "polygon"})
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            _append(out / "errors.jsonl", {"t": _now(), "error": type(exc).__name__, "condition": condition})
    _checkpoint()


def _count(out: Path, name: str) -> int:
    path = out / name
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


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
    report = {
        "started": started,
        "uptime_s": None if started is None else round(_now() - float(started), 1),
        "restarts": state.get("restarts", 0),
        "market_rows": _count(out, "market.jsonl"),
        "trade_rows": _count(out, "trades.jsonl"),
        "chain_rows": _count(out, "chain.jsonl"),
        "gaps": _count(out, "gaps.jsonl"),
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
    args = parser.parse_args()
    if args.command == "status":
        print(json.dumps(status(args.out), indent=2))
        return
    if args.markets is None:
        raise SystemExit("collect requires --markets")
    collect(args.markets, args.out, args.seconds)


if __name__ == "__main__":
    main()
