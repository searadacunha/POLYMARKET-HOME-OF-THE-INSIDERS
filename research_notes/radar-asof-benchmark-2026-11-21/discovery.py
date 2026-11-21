"""Look for previously unlisted outer endpoints in Arbitrum pass-throughs of archived Relay orders."""
import argparse
from bisect import bisect_right
from collections import defaultdict
import csv
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))

from case_replay import DATA, HERE, ROOT, screening


def read_rows(path):
    with path.open() as f:
        return list(csv.DictReader(f))


def scan():
    accounts = {r["address"].lower() for r in read_rows(DATA / "accounts.csv")}
    old = {(p["upstream_order"], p["downstream_order"]) for p in json.loads((HERE / "cases.json").read_text())["relay"]["candidates_24h"]}
    transfers = read_rows(DATA / "transfers.csv")
    successful = [r for r in transfers if r["status"] == "success"]
    arrivals, departures = [], defaultdict(list)
    for r in successful:
        if r["out_chain"] == "42161" and r["symbol_out"] == "USDC" and r["out_time"] and Decimal(r["amount_out"]) >= 100:
            arrivals.append(r)
        if r["in_chain"] == "42161" and r["symbol_in"] == "USDC" and r["in_time"] and Decimal(r["amount_in"]) >= 100:
            departures[r["sender"].lower(), Decimal(r["amount_in"])].append(r)
    grouped = {}
    for key, group in departures.items():
        ordered = sorted(group, key=lambda r: int(r["in_time"]))
        grouped[key] = [int(r["in_time"]) for r in ordered], ordered
    candidates, before_registry = [], 0
    for a in arrivals:
        via = a["recipient"].lower()
        times, rows = grouped.get((via, Decimal(a["amount_out"])), ([], []))
        t = int(a["out_time"])
        for b in rows[bisect_right(times, t):bisect_right(times, t + 60)]:
            sender, end = a["sender"].lower(), b["recipient"].lower()
            if len({sender, via, end}) != 3 or a["order"] == b["order"]:
                continue
            before_registry += 1
            if (sender in accounts and end in accounts) or (a["order"], b["order"]) in old:
                continue
            _, p = screening(a, b)
            candidates.append({**p, "sender": sender, "via": via, "recipient": end,
                               "sender_in_registry": sender in accounts, "recipient_in_registry": end in accounts})
    candidates.sort(key=lambda p: (p["arrival_utc"],p["upstream_order"],p["downstream_order"]))
    files = [DATA / "accounts.csv", DATA / "transfers.csv", HERE / "DISCOVERY_PROTOCOL.md", HERE / "cases.json"]
    return {"inputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
            "registry_addresses": len(accounts), "transfer_rows": len(transfers), "successful_orders":len(successful),
            "eligible_arrivals":len(arrivals), "eligible_departures":sum(map(len,departures.values())),
            "matched_before_registry_screen":before_registry, "matches":candidates}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    opts = parser.parse_args()
    result = json.dumps(scan(), sort_keys=True, indent=2) + "\n"
    if opts.check:
        if result != (HERE / "discovery.json").read_text():
            raise SystemExit("discovery scan differs")
        print("open-ended route scan reproduced")
    else:
        print(result, end="")
