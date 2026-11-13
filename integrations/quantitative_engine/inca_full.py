"""Offline pass over the local Inca archive. Ignores AppleDouble `._*` files.

Uses the frozen thresholds in monitoring/phi_monitor. Does not change them and
does not read a network. Raw files stay outside git.
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

V1_FILL = "0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6"
V2_FILL = "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
FEB28 = "US strikes Iran by February 28, 2026?"


def _utc(ts: int) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def _real_files(directory: Path):
    for path in directory.rglob("*"):
        if path.is_file() and not path.name.startswith("._"):
            yield path


def activity_rows(root: Path):
    base = root / "raw" / "polymarket"
    for wallet_dir in sorted(p for p in base.iterdir() if p.is_dir() and not p.name.startswith("._")):
        for path in sorted(wallet_dir.glob("v2activity_p*.json")):
            if path.name.endswith(".meta.json") or path.name.startswith("._"):
                continue
            payload = json.loads(path.read_text(encoding="utf-8"))
            for row in payload.get("data") or []:
                yield wallet_dir.name.lower(), row


def load_tape(root: Path, condition: str):
    directory = root / "raw" / "trades" / condition
    rows, seen = [], set()
    for path in sorted(directory.glob("p*.json")):
        if path.name.endswith(".meta.json") or path.name.startswith("._"):
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("data") or []:
            key = (
                row.get("transaction_hash"), row.get("proxy_wallet"), row.get("timestamp"),
                row.get("side"), row.get("outcome"), row.get("size"), row.get("price"),
            )
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
    return rows


def receipt_index(root: Path) -> set[str]:
    found = set()
    for path in (root / "raw" / "polygon").glob("*.eth_getTransactionReceipt.json"):
        if path.name.startswith("._"):
            continue
        found.add(path.name.split(".", 1)[0].lower())
    return found


def scan_receipts(root: Path) -> dict:
    """Count log families. A transfer is not an OrderFilled execution."""
    counts = Counter()
    files = 0
    for path in (root / "raw" / "polygon").glob("*.eth_getTransactionReceipt.json"):
        if path.name.startswith("._"):
            continue
        files += 1
        result = (json.loads(path.read_text(encoding="utf-8")).get("result") or {})
        kinds = set()
        for log in result.get("logs") or []:
            topic = ((log.get("topics") or [""])[0] or "").lower()
            if topic == V1_FILL:
                kinds.add("V1_ORDERFILLED")
            elif topic == V2_FILL:
                kinds.add("V2_ORDERFILLED")
            elif topic == TRANSFER:
                kinds.add("ERC20_TRANSFER")
        counts["+".join(sorted(kinds)) or "OTHER_OR_EMPTY"] += 1
    return {"receipt_files": files, "log_families": dict(counts)}


def run(root: Path) -> dict:
    import sys
    repo = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo))
    from monitoring.phi_monitor import ignition, tapefeat

    trades = list(activity_rows(root))
    trade_tx = set()
    by_month = Counter()
    feb = []
    for wallet, row in trades:
        if row.get("type") != "TRADE":
            continue
        tx = (row.get("transaction_hash") or "").lower()
        if tx:
            trade_tx.add(tx)
        stamp = int(row.get("timestamp") or 0)
        by_month[datetime.fromtimestamp(stamp, timezone.utc).strftime("%Y-%m")] += 1
        if row.get("title") == FEB28 and row.get("side") == "BUY":
            cash = row.get("usdc_size")
            if not isinstance(cash, (int, float)):
                cash = float(row.get("price") or 0) * float(row.get("size") or 0)
            feb.append({
                "wallet": wallet,
                "timestamp": stamp,
                "outcome": row.get("outcome"),
                "price": row.get("price"),
                "usdc": round(float(cash), 2),
                "tx": tx,
            })
    receipts = receipt_index(root)
    condition = "0x7f39808829da93cfd189807f13f6d86a0e604835e6f9482d8094fac46b3abaac"
    tape_rows = load_tape(root, condition)
    yes = sorted((r for r in tape_rows if r.get("outcome") == "Yes"), key=lambda r: r["timestamp"])
    grid = {}
    for row in yes:
        bucket = int(row["timestamp"]) - int(row["timestamp"]) % ignition.GRID
        grid[bucket] = float(row["price"])
    series = sorted(grid.items())
    yes_ig = ignition.first_ignition(series, "YES")
    no_ig = ignition.first_ignition(series, "NO")
    tape = [
        (int(r["timestamp"]), str(r["proxy_wallet"]).lower(), r["side"], r["outcome"], float(r["size"]), float(r["price"]))
        for r in tape_rows
    ]
    features, why = (None, "no_ignition")
    decision = "NO_IGNITION"
    if yes_ig is not None:
        features, why = tapefeat.alert_features(tape, "YES", yes_ig["base"], yes_ig["t0"], yes_ig["t1"])
        if features is None:
            decision = "NO_ALERT"
        else:
            lonely = features["share15"] >= tapefeat.LONELY_SHARE
            # The initiator is not in the 13-wallet activity set, so prior markets are unknown.
            classes = tapefeat.classify(features, None)
            decision = "NO_ALERT" if not lonely else "ALERT_BLOCKED_WITHOUT_HISTORY"
            features = {**features, "classes_without_history": classes, "history_in_archive": False}
    wallets = defaultdict(lambda: {"n": 0, "usdc": 0.0, "first": None, "last": None})
    for row in feb:
        slot = wallets[row["wallet"]]
        slot["n"] += 1
        slot["usdc"] = round(slot["usdc"] + row["usdc"], 2)
        slot["first"] = row["timestamp"] if slot["first"] is None else min(slot["first"], row["timestamp"])
        slot["last"] = row["timestamp"] if slot["last"] is None else max(slot["last"], row["timestamp"])
    feb_out = [
        {"wallet": wallet, "buys": slot["n"], "usdc": slot["usdc"],
         "first_utc": _utc(slot["first"]), "last_utc": _utc(slot["last"])}
        for wallet, slot in sorted(wallets.items(), key=lambda item: item[1]["first"])
    ]
    return {
        "appledouble_ignored": True,
        "activity_trade_rows": sum(by_month.values()),
        "unique_trade_transactions": len(trade_tx),
        "trades_by_month": dict(sorted(by_month.items())),
        "trade_hashes_found_in_polygon_receipts": len(trade_tx & receipts),
        "receipts": scan_receipts(root),
        "israel_tape": {
            "prints": len(tape_rows),
            "grid_points": len(series),
            "yes_ignition": None if yes_ig is None else {**yes_ig, "t1_utc": _utc(yes_ig["t1"]), "t0_utc": _utc(yes_ig["t0"])},
            "no_ignition": no_ig is not None,
            "features": None if not features else {**features, "t_first_utc": _utc(features["t_first"]), "t_alert_utc": _utc(features["t_alert"])},
            "feature_reason": why,
            "decision": decision,
            "rule": "Frozen phi_monitor thresholds. Lonely requires 50 percent of the first 15 minutes. No threshold was changed after this run.",
        },
        "february_2026_strike_buys": {
            "market": FEB28,
            "full_market_tape": False,
            "control_population": None,
            "false_positive_rate": None,
            "wallets": feb_out,
        },
        "coverage": {
            "poly_data_v2": "Does not cover June 2025 or February 2026. Its reader starts at the April 2026 V2 contract and one exchange.",
            "phi_monitor_chain": "Decodes only V2 OrderFilled. It cannot read the pre-migration fills in this archive.",
            "pendulum": "V1 hours begin 2026-02-21T18Z on the archive index. They carry no wallet and no transaction hash. Not re-downloaded here.",
            "near_real_time": "The monitor's tape and price reads are built for a polled data API. This run used a stored archive only. Pendulum publication is delayed. A stored hour is not a live alert.",
        },
    }
