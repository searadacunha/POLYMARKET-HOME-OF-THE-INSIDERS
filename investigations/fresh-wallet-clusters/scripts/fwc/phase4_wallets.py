#!/usr/bin/env python3
"""First-deposit provenance for the 29 headline wallets, and one more hop on the two distributors.

Reads public activity listings and Polygon receipts. Does not use a paid indexer.
"""
from __future__ import annotations

import csv
import gzip
import json
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data"
UA = {"User-Agent": "research-client/1.0", "Accept": "application/json", "Accept-Encoding": "gzip",
      "Content-Type": "application/json"}
PREFIXES = ["0xce71bed9", "0xc8ab97a9", "0x5157a81d", "0x858d551d", "0x2a019dc0", "0xab197165",
            "0x090a0d3f", "0xc6dd7225", "0xc07b56fa", "0x62764005", "0x20054442", "0x43440ab0",
            "0xbaa2bcb5", "0x2615e0c5", "0xfcf2378f", "0xbacd00c9", "0x52b74441", "0x71ed0bc9",
            "0x12d6cccf", "0xb03b826a", "0x53e55bc7", "0x9ef58274", "0xb5ebce29", "0xecaa8806",
            "0xe1055b4b", "0x95074f70", "0xc2f20907", "0x9d84ce03", "0x4773906b"]
DISTRIBUTORS = ["0x8ecd0938300411e8d84b5778b331decee8989705", "0xd8aefc93708f89daa1417faab1a2d26c3cb4e7c9"]
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
STABLES = {"0x3c499c542cef5e3811e1192ce70d8cc03d5c3359", "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
           "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"}


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "research-client/1.0", "Accept": "application/json",
                                               "Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=40) as resp:
        raw = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)
        return json.loads(raw)


def rpc(method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    last = "none"
    for url in ("https://polygon.drpc.org", "https://gateway.tenderly.co/public/polygon"):
        try:
            req = urllib.request.Request(url, data=body, headers=UA)
            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read()
                if raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                payload = json.loads(raw)
            if payload.get("error"):
                last = str(payload["error"])[:120]
                continue
            return payload.get("result")
        except Exception as exc:  # noqa: BLE001
            last = str(exc)[:120]
    raise RuntimeError(last)


def activity(wallet, pages=4):
    rows = []
    cursor = None
    for _ in range(pages):
        url = ("https://data-api.polymarket.com/v2/activity?user=" + wallet
               + "&start=1&sort_by=TIMESTAMP&sort_direction=ASC&exclude_deposits_withdrawals=false&limit=1000")
        if cursor:
            url += "&cursor=" + cursor
        payload = get(url)
        data = payload.get("data") or []
        rows.extend(data)
        cursor = (payload.get("pagination") or {}).get("next_cursor")
        if not cursor or not data:
            break
        time.sleep(0.15)
    return rows


def payer_of(tx, wallet):
    receipt = rpc("eth_getTransactionReceipt", [tx])
    if not receipt:
        return None
    best = None
    for log in receipt.get("logs") or []:
        topics = log.get("topics") or []
        if len(topics) < 3 or topics[0] != TRANSFER:
            continue
        if log.get("address", "").lower() not in STABLES:
            continue
        dst = "0x" + topics[2][-40:]
        if dst != wallet:
            continue
        value = int(log.get("data") or "0x0", 16) / 1e6
        src = "0x" + topics[1][-40:]
        if best is None or value > best[0]:
            best = (value, src, log.get("address", "").lower(), int(receipt["blockNumber"], 16))
    if not best:
        return {"tx": tx, "block": int(receipt["blockNumber"], 16), "payer": None, "usd": 0, "kind": "no_stable_credit"}
    value, src, token, block = best
    code = rpc("eth_getCode", [src, hex(block)])
    nonce = int(rpc("eth_getTransactionCount", [src, hex(block)]) or "0x0", 16)
    kind = "contract" if code and code != "0x" else "eoa"
    return {"tx": tx, "block": block, "payer": src, "usd": round(value, 2), "token": token, "kind": kind, "nonce_at_block": nonce}


def full_addresses():
    import sqlite3
    con = sqlite3.connect("/tmp/fwc-phase3/cache.sqlite")
    found = {}
    for (wallet,) in con.execute("select distinct wallet from activity"):
        for prefix in PREFIXES:
            if wallet.startswith(prefix):
                found[prefix] = wallet
    missing = [p for p in PREFIXES if p not in found]
    return list(found.values()), missing


def main():
    wallets, missing = full_addresses()
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    payers = []
    for wallet in wallets:
        try:
            acts = activity(wallet, 3)
        except Exception as exc:  # noqa: BLE001
            rows.append({"wallet": wallet, "note": str(exc)[:160]})
            continue
        if not acts:
            rows.append({"wallet": wallet, "note": "no activity"})
            continue
        first = min(int(a["timestamp"]) for a in acts)
        deposits = [a for a in acts if a.get("type") == "DEPOSIT" and a.get("transaction_hash")]
        trades = [a for a in acts if a.get("type") == "TRADE"]
        redeems = [a for a in acts if a.get("type") == "REDEEM"]
        buys = sum(float(a.get("usdc_size") or 0) for a in trades if a.get("side") == "BUY")
        sells = sum(float(a.get("usdc_size") or 0) for a in trades if a.get("side") == "SELL")
        redeemed = sum(float(a.get("usdc_size") or 0) for a in redeems)
        first_dep = min(deposits, key=lambda a: int(a["timestamp"])) if deposits else None
        info = {"wallet": wallet, "first_ts": first, "n_rows": len(acts), "n_deposits": len(deposits),
                "n_trades": len(trades), "buy_usdc": round(buys, 2), "sell_usdc": round(sells, 2),
                "redeem_usdc": round(redeemed, 2), "net_cash_flow": round(sells + redeemed - buys, 2)}
        if first_dep:
            try:
                paid = payer_of(first_dep["transaction_hash"], wallet)
                info.update({"deposit_tx": first_dep["transaction_hash"], **{f"payer_{k}": v for k, v in (paid or {}).items()}})
                if paid and paid.get("payer"):
                    payers.append((paid["payer"], wallet, paid.get("usd")))
            except Exception as exc:  # noqa: BLE001
                info["payer_note"] = str(exc)[:140]
        rows.append(info)
        print(wallet[:10], "rows", len(acts), "deps", len(deposits), flush=True)
        time.sleep(0.1)
    with (OUT / "phase4_wallets.csv").open("w", newline="") as handle:
        fields = sorted({k for row in rows for k in row})
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    # shared first payers
    from collections import defaultdict
    groups = defaultdict(list)
    for payer, wallet, usd in payers:
        groups[payer].append((wallet, usd))
    with (OUT / "phase4_first_payers.csv").open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["payer", "n_wallets", "wallets", "amounts"])
        for payer, members in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            writer.writerow([payer, len(members), " ".join(m[0] for m in members), " ".join(str(m[1]) for m in members)])
    (OUT / "phase4_wallet_missing.txt").write_text("\n".join(missing) + "\n")
    print("wallets", len(rows), "missing", missing, "payers", len(groups), flush=True)


if __name__ == "__main__":
    main()
