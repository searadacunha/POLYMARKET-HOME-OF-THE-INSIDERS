#!/usr/bin/env python3
"""Offline reconciliation of archived Polygon RPC observations.

This checks what the four JSON exports *contain*. It deliberately cannot
certify full historical coverage: no successful per-range scan manifest was
archived, and failed_splits is not a list of recovered or missing block ranges.
"""
from __future__ import annotations

import json
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


def demand(condition, msg):
    if not condition:
        raise AssertionError(msg)


def as_int(value):
    result = int(value)
    demand(result >= 0, "negative token amount")
    return result


def audit(root=EVIDENCE):
    root = Path(root)
    all_logs = {}
    splits = {}
    window_counts = {}
    for symbol in CONTRACTS:
        for direction in ("from", "to"):
            filename = f"polygon_logs_{symbol}_{direction}.json"
            data = json.loads((root / filename).read_text(encoding="utf-8"))
            demand((data.get("name"), data.get("direction")) == (symbol, direction),
                   f"{filename}: pair misidentified")
            demand((data.get("start"), data.get("end")) == (START, END),
                   f"{filename}: block range changed")
            demand(isinstance(data.get("logs"), list), f"{filename}: no logs list")
            demand(data.get("n") == len(data["logs"]), f"{filename}: row count mismatch")
            demand(isinstance(data.get("windows"), int) and data["windows"] > 0,
                   f"{filename}: window counter missing")
            demand(isinstance(data.get("failed_splits"), int) and data["failed_splits"] >= 0,
                   f"{filename}: invalid split counter")
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
                demand(as_int(log["logIndex"]) >= 0, f"{filename}: invalid log index")
                addr = log["from" if direction == "from" else "to"].lower()
                demand(addr == RECIPIENT, f"{filename}: unexpected recipient side")
                key = (log["hash"].lower(), int(log["logIndex"]))
                demand(key not in found, f"{filename}: duplicate transaction log")
                found[key] = {**log, "value": value}
            all_logs[(symbol, direction)] = found
            splits[filename] = data["failed_splits"]
            window_counts[filename] = data["windows"]

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
    for r in direct:
        key = (r["hash"].lower(), int(r["logIndex"]))
        demand(key in incoming, "direct receipt missing from archive logs")
        token, log = incoming[key]
        demand(CONTRACTS[token] == r["contract"].lower(), "direct receipt token mismatch")
        demand(log["from"].lower() == r["proxy"].lower(), "direct receipt sender mismatch")
        demand(log["value"] == as_int(r["value"]), "direct receipt value mismatch")
        demand(r["status"] == 1 and r["block_match"] and r["match_count"] == 1,
               "direct RPC match is no longer conclusive")

    rpc = json.loads((root / "g38_rpc_replay_2026-11-08.json").read_text())
    relay = [o for o in rpc["orders"] if o["chain"] == 137]
    demand(len(relay) == 12, "Polygon Relay order count changed")
    for order in relay:
        key = (order["archived_hash"].lower(), order["match_log"]["logIndex"])
        demand(key in incoming, "Relay fill receipt missing in Polygon logs")
        token, log = incoming[key]
        demand(token == "USDC" and log["value"] == as_int(order["amount"]),
               "Relay amount or token mismatch")
        demand(log["to"].lower() == RECIPIENT and
               log["from"].lower() == order["match_log"]["from"].lower(),
               "Relay recipient or sender mismatch")
        demand(order["status"] == 1 and order["match_log_count"] == 1,
               "Relay receipt unconfirmed")

    return {
        "recorded_incoming_logs": len(incoming),
        "recorded_outgoing_logs": len(out),
        "recorded_incoming_atomic": in_sum,
        "recorded_outgoing_atomic": out_sum,
        "direct_receipts_matched": len(direct),
        "polygon_relay_receipts_matched": len(relay),
        "failed_split_attempts_by_export": splits,
        "request_windows_by_export": window_counts,
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
