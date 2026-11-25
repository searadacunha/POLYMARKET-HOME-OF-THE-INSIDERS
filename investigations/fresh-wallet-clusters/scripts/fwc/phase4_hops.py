#!/usr/bin/env python3
"""One hop behind the two distributors and the large single-wallet payer.

Public Polygon logs only. Writes small CSVs. Does not store raw receipts.
"""
from __future__ import annotations

import csv
import gzip
import json
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data"
UA = {"User-Agent": "research-client/1.0", "Accept": "application/json", "Accept-Encoding": "gzip",
      "Content-Type": "application/json"}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
STABLES = ["0x3c499c542cef5e3811e1192ce70d8cc03d5c3359", "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"]
DISTRIBUTORS = ["0x8ecd0938300411e8d84b5778b331decee8989705", "0xd8aefc93708f89daa1417faab1a2d26c3cb4e7c9"]
KNOWN = [
    "0x5a54bf5dfe75a829ec40344b2e772510764b51d1f3069971ae95b991fed3e980",
    "0xb243bff418dd10afdbc382be8edc4add576a715936c39e50b284a9645fbab291",
    "0x81499b34ba3bc58a3d597b562dcfa11c01486d62f893b81d80efba2022bb4ba3",
    "0x8b86024b7a5baf24fd075a439801a4807ced09b7ed2fc6502392a28b18d7fe70",
]


def rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last = "none"
    for url in ("https://gateway.tenderly.co/public/polygon", "https://polygon.drpc.org"):
        try:
            req = urllib.request.Request(url, data=body, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as resp:
                raw = resp.read()
                if raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                payload = json.loads(raw)
            if payload.get("error"):
                last = str(payload["error"])[:160]
                continue
            return payload.get("result")
        except Exception as exc:  # noqa: BLE001
            last = str(exc)[:160]
    raise RuntimeError(last)


def pad(addr):
    return "0x" + addr.lower()[2:].rjust(64, "0")


def transfers(addr, start, end, direction):
    topic = pad(addr)
    topics = [TRANSFER, topic if direction == "out" else None, None if direction == "out" else topic]
    rows = []
    cursor = start
    while cursor <= end:
        hi = min(end, cursor + 9000)
        result = rpc("eth_getLogs", [{
            "fromBlock": hex(cursor),
            "toBlock": hex(hi),
            "address": STABLES,
            "topics": topics,
        }]) or []
        for log in result:
            topics_l = log.get("topics") or []
            if len(topics_l) < 3:
                continue
            value = int(log.get("data") or "0x0", 16) / 1e6
            if value < 500:
                continue
            rows.append({
                "address": addr,
                "direction": direction,
                "token": log.get("address", "").lower(),
                "counterparty": "0x" + topics_l[2 if direction == "out" else 1][-40:],
                "usd": round(value, 2),
                "tx": log.get("transactionHash"),
                "block": int(log["blockNumber"], 16),
            })
        cursor = hi + 1
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    state_rows = []
    for addr in DISTRIBUTORS:
        code = rpc("eth_getCode", [addr, "latest"])
        nonce = int(rpc("eth_getTransactionCount", [addr, "latest"]) or "0x0", 16)
        state_rows.append({"address": addr, "code_len": 0 if not code or code == "0x" else (len(code) - 2) // 2, "nonce": nonce})
        print(addr, state_rows[-1], flush=True)
    flows = []
    # The four known payments are at blocks 67113840-67114065. Read a day before and an hour after.
    for addr in DISTRIBUTORS:
        for direction in ("in", "out"):
            found = transfers(addr, 67070000, 67120000, direction)
            flows.extend(found)
            print(addr[:10], direction, len(found), flush=True)
    with (OUT / "phase4_distributor_flows.csv").open("w", newline="") as handle:
        fields = ["address", "direction", "token", "counterparty", "usd", "tx", "block"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(flows)
    tx_rows = []
    for tx in KNOWN:
        txn = rpc("eth_getTransactionByHash", [tx]) or {}
        tx_rows.append({"tx": tx, "from": (txn.get("from") or "").lower(), "to": (txn.get("to") or "").lower(),
                        "nonce": int(txn["nonce"], 16) if txn.get("nonce") else ""})
        print("tx", tx[:10], tx_rows[-1]["from"], tx_rows[-1]["to"], flush=True)
    with (OUT / "phase4_distributor_txfrom.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["tx", "from", "to", "nonce"])
        writer.writeheader()
        writer.writerows(tx_rows)
    with (OUT / "phase4_distributor_state.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["address", "code_len", "nonce"])
        writer.writeheader()
        writer.writerows(state_rows)
    print("flows", len(flows), flush=True)


if __name__ == "__main__":
    main()
