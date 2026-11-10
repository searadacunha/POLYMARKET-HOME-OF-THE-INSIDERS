#!/usr/bin/env python3
"""Offline reconciliation of archived Polygon RPC observations.

This checks what the four JSON exports *contain*. It deliberately cannot
certify full historical coverage: no successful per-range scan manifest was
archived, and failed_splits is not a list of recovered or missing block ranges.
"""
from __future__ import annotations

import csv
import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "research_notes/independent-forensic-audit-2026-11-08/evidence"
RECIPIENT = "0xc5bb1be0407db7312911ec765d399d02461e411a"
CONTRACTS = {
    "USDC": "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359",
    "USDCE": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
}
START = 81100000
END = 96974221
ARCHIVED_ATOMIC = 1984038168550
ARCHIVE = ROOT / "research_notes/x-history-2026-11-06/verification"
POLYGON_RELAY_WALLETS = (
    "0x858d551d073e9c647c17079ad9021de830201047",
    "0x5e0b017aef88af84fb3897fecce7413c6754981a",
    "0x8a480b60cb78213fdf34842160dc956a831a2558",
)


def demand(condition, msg):
    if not condition:
        raise AssertionError(msg)


def as_int(value):
    """Parse an exact unsigned quantity without bool coercion or truncation."""
    if type(value) is int:
        result = value
    elif isinstance(value, str) and re.fullmatch(r"[0-9]+|0[xX][0-9a-fA-F]+", value):
        result = int(value, 16 if value.lower().startswith("0x") else 10)
    else:
        raise AssertionError("expected unsigned integer quantity (integer, decimal text or hex text)")
    demand(result >= 0, "negative integer quantity")
    return result


def archived_expectations(archive=ARCHIVE):
    """Expected identities from the pre-existing explorer and Relay snapshots."""
    archive = Path(archive)
    with (archive / "data/g38_accounts.csv").open(encoding="utf-8", newline="") as fh:
        proxies = {row["proxy"].lower() for row in csv.DictReader(fh)}
    direct = Counter()
    folder = archive / "evidence/etherscan" / RECIPIENT
    for path in folder.glob("137_tokentx_p*.json"):
        if path.name.endswith(".meta.json"):
            continue
        for row in json.loads(path.read_text())["result"]:
            if (row["to"].lower() == RECIPIENT and row["from"].lower() in proxies
                    and row["contractAddress"].lower() in CONTRACTS.values()):
                direct[(row["hash"].lower(), row["from"].lower(), row["contractAddress"].lower(),
                        as_int(row["value"]), as_int(row["blockNumber"]))] += 1
    orders = {}
    for wallet in POLYGON_RELAY_WALLETS:
        for path in (archive / "evidence/relay" / wallet).glob("p*.json"):
            if path.name.endswith(".meta.json"):
                continue
            for order in json.loads(path.read_text())["requests"]:
                output = (order.get("data", {}).get("metadata") or {}).get("currencyOut") or {}
                currency = output.get("currency") or {}
                if order.get("recipient", "").lower() != RECIPIENT or currency.get("chainId") != 137:
                    continue
                identity = order["id"].lower()
                demand(identity not in orders, "duplicate order in original Relay archive")
                fills = order["data"].get("outTxs") or []
                orders[identity] = (wallet, currency["address"].lower(), as_int(output["amount"]),
                                    (fills[0].get("hash") or "").lower() if fills else "")
    demand(sum(direct.values()) == 38 and len(orders) == 12, "original archive membership changed")
    return direct, orders


def audit(root=EVIDENCE):
    root = Path(root)
    expected_direct, expected_orders = archived_expectations()
    all_logs = {}
    splits = {}
    window_counts = {}
    for symbol in CONTRACTS:
        for direction in ("from", "to"):
            filename = f"polygon_logs_{symbol}_{direction}.json"
            data = json.loads((root / filename).read_text(encoding="utf-8"))
            demand((data.get("name"), data.get("direction")) == (symbol, direction),
                   f"{filename}: pair misidentified")
            demand((as_int(data.get("start")), as_int(data.get("end"))) == (START, END),
                   f"{filename}: block range changed")
            demand(isinstance(data.get("logs"), list), f"{filename}: no logs list")
            demand(as_int(data.get("n")) == len(data["logs"]), f"{filename}: row count mismatch")
            request_count = as_int(data.get("windows"))
            split_count = as_int(data.get("failed_splits"))
            demand(request_count > 0, f"{filename}: window counter missing")
            windows = data.get("successful_ranges")
            # A count of requests, even if every request succeeded, is not a
            # coverage proof. Recovered retry ranges must be individually saved.
            if windows is not None:
                demand(isinstance(windows, list), f"{filename}: invalid ranges")
            found = {}
            for log in data["logs"]:
                block = as_int(log["block"])
                demand(START <= block <= END, f"{filename}: log outside period")
                value = as_int(log["value"])
                demand(log["hash"].startswith("0x") and len(log["hash"]) == 66,
                       f"{filename}: invalid transaction hash")
                log_index = as_int(log["logIndex"])
                addr = log["from" if direction == "from" else "to"].lower()
                demand(addr == RECIPIENT, f"{filename}: unexpected recipient side")
                key = (log["hash"].lower(), log_index)
                demand(key not in found, f"{filename}: duplicate transaction log")
                found[key] = {**log, "value": value, "block": block, "logIndex": log_index}
            all_logs[(symbol, direction)] = found
            splits[filename] = split_count
            window_counts[filename] = request_count

    all_keys = [key for logs in all_logs.values() for key in logs]
    demand(len(set(all_keys)) == len(all_keys), "same log appears in multiple exports")
    incoming = {(key): (symbol, log) for (symbol, direction), rows in all_logs.items()
                if direction == "to" for key, log in rows.items()}
    out = {(key): (symbol, log) for (symbol, direction), rows in all_logs.items()
           if direction == "from" for key, log in rows.items()}
    in_sum = sum(x["value"] for _, x in incoming.values())
    out_sum = sum(x["value"] for _, x in out.values())
    demand(in_sum == out_sum == ARCHIVED_ATOMIC,
           "recorded Polygon token totals no longer reconcile")

    direct = json.loads((root / "g38_direct_receipts_2026-11-08.json").read_text())["rows"]
    demand(len(direct) == 38 and len({r["proxy"].lower() for r in direct}) == 32,
           "38 direct receipts / 32 proxies changed")
    direct_keys = set()
    actual_direct = Counter()
    for r in direct:
        key = (r["hash"].lower(), as_int(r["logIndex"]))
        demand(key not in direct_keys, "duplicate direct receipt event")
        direct_keys.add(key)
        demand(key in incoming, "direct receipt missing from archive logs")
        token, log = incoming[key]
        demand(CONTRACTS[token] == r["contract"].lower(), "direct receipt token mismatch")
        demand(log["from"].lower() == r["proxy"].lower(), "direct receipt sender mismatch")
        demand(log["value"] == as_int(r["value"]), "direct receipt value mismatch")
        demand(as_int(r["archive_block"]) == as_int(r["rpc_block"]) == as_int(log["block"]),
               "direct receipt block mismatch")
        actual_direct[(r["hash"].lower(), r["proxy"].lower(), r["contract"].lower(),
                       as_int(r["value"]), as_int(r["archive_block"]))] += 1
        demand(as_int(r["status"]) == 1 and r["block_match"] is True and as_int(r["match_count"]) == 1,
               "direct RPC summary no longer reports a match")
    demand(actual_direct == expected_direct, "direct receipts differ from original archive membership")

    rpc = json.loads((root / "g38_rpc_replay_2026-11-08.json").read_text())
    relay = [o for o in rpc["orders"] if as_int(o["chain"]) == 137]
    demand(len(relay) == 12, "Polygon Relay order count changed")
    relay_keys, relay_ids = set(), set()
    for order in relay:
        identity = order["id"].lower()
        demand(identity not in relay_ids, "duplicate Relay order id")
        relay_ids.add(identity)
        demand(identity in expected_orders, "Relay order absent from original archive")
        wallet, contract, amount, fill_hash = expected_orders[identity]
        demand((order["user"].lower(), order["token"].lower(), as_int(order["amount"])) ==
               (wallet, contract, amount), "Relay order differs from original archive")
        if fill_hash:
            demand(order["archived_hash"].lower() == fill_hash, "Relay provider fill hash changed")
        key = (order["archived_hash"].lower(), as_int(order["match_log"]["logIndex"]))
        demand(key not in relay_keys and key not in direct_keys, "duplicate Relay receipt event")
        relay_keys.add(key)
        demand(key in incoming, "Relay fill receipt missing in Polygon logs")
        token, log = incoming[key]
        demand(token == "USDC" and log["value"] == as_int(order["amount"]),
               "Relay amount or token mismatch")
        demand(log["to"].lower() == RECIPIENT and
               log["from"].lower() == order["match_log"]["from"].lower(),
               "Relay recipient or sender mismatch")
        demand(as_int(order["archived_block"]) == as_int(order["block"]) == as_int(log["block"]),
               "Relay receipt block mismatch")
        demand(order["match_log"]["contract"].lower() == contract and
               as_int(order["match_log"]["value"]) == amount and
               order["match_log"]["to"].lower() == RECIPIENT, "Relay summary log mismatch")
        demand(as_int(order["status"]) == 1 and as_int(order["match_log_count"]) == 1,
               "Relay summary does not report a receipt match")
    demand(relay_ids == set(expected_orders), "Relay orders differ from original archive membership")

    return {
        "recorded_incoming_logs": len(incoming),
        "recorded_outgoing_logs": len(out),
        "recorded_incoming_atomic": in_sum,
        "recorded_outgoing_atomic": out_sum,
        "direct_receipts_matched": len(direct),
        "polygon_relay_receipts_matched": len(relay),
        "failed_split_attempts_by_export": splits,
        "request_windows_by_export": window_counts,
        "rpc_proof_scope": "reconciliation of archived summaries and logs; raw RPC responses not replayed",
        "order_id_binding_verified": False,
        "base_receipts_verified": False,
        "coverage_status": "NOT_ESTABLISHED",
        "coverage_reason": (
            "The original exports have request counts and failed_splits but no "
            "auditable per-range success manifest. A split counter does not by "
            "itself prove either a gap or successful recovery. These totals "
            "reconcile observed records only, not all chain activity."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, sort_keys=True))
