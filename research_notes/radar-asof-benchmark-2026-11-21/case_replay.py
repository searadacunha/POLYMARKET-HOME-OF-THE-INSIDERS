"""Screen archived Relay routes by arrival and asset, and independently total the Ballon d'Or activity."""
import argparse
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
from decimal import Decimal
import gzip
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = ROOT / "research_notes/cross-investigation-relay-transfers-2026-11-20/data"
ACTIVITY = ROOT / "investigations/ballon-dor-wallets/sources/evidence/activity"
STAGES = ("all", "later", "same_chain", "same_symbol", "within_amount", "within_24h", "within_1h")


def stamp(t):
    return datetime.fromtimestamp(t, timezone.utc).isoformat()


def screening(inbound, outbound):
    stages = ["all"]
    if not inbound["out_time"] or not outbound["in_time"]:
        return stages, None
    lag = int(outbound["in_time"]) - int(inbound["out_time"])
    if lag <= 0:
        return stages, None
    stages.append("later")
    if not inbound["out_chain"] or inbound["out_chain"] != outbound["in_chain"]:
        return stages, None
    stages.append("same_chain")
    if not inbound["symbol_out"] or inbound["symbol_out"] != outbound["symbol_in"]:
        return stages, None
    stages.append("same_symbol")
    if not inbound["amount_out"] or not outbound["amount_in"] or not 0 < Decimal(outbound["amount_in"]) <= Decimal(inbound["amount_out"]):
        return stages, None
    stages.append("within_amount")
    if lag > 86400:
        return stages, None
    stages.append("within_24h")
    if lag <= 3600:
        stages.append("within_1h")
    return stages, {"upstream_order": inbound["order"], "downstream_order": outbound["order"],
                    "arrival_tx": inbound["out_tx"], "departure_tx": outbound["in_tx"], "chain": inbound["out_chain"],
                    "arrival_utc": stamp(int(inbound["out_time"])), "departure_utc": stamp(int(outbound["in_time"])),
                    "lag_s": lag, "symbol": inbound["symbol_out"],
                    "arrived": inbound["amount_out"], "departed": outbound["amount_in"]}


def relay():
    edges = defaultdict(list)
    with (DATA / "transfers.csv").open() as f:
        for r in csv.DictReader(f):
            if r["status"] == "success":
                edges[r["sender"], r["recipient"]].append(r)
    stages, triples, leads = Counter(), Counter(), []
    with (DATA / "pairs.csv").open() as f:
        for r in csv.DictReader(f):
            if not r["via"]:
                continue
            seen = set()
            for inbound in edges[r["from"], r["via"]]:
                for outbound in edges[r["via"], r["to"]]:
                    passes, lead = screening(inbound, outbound)
                    stages.update(passes)
                    seen.update(passes)
                    if lead:
                        leads.append({"sender": r["from"], "via": r["via"], "recipient": r["to"], **lead})
            triples.update(seen)
    return {"combinations": {s: stages[s] for s in STAGES}, "triples": {s: triples[s] for s in STAGES},
            "candidates_24h": sorted(leads, key=lambda v: (v["lag_s"], v["upstream_order"], v["downstream_order"]))}


def ballon():
    counts, hashes, sums = Counter(), defaultdict(set), defaultdict(Decimal)
    files = sorted(ACTIVITY.glob("*.jsonl.gz"))
    for path in files:
        with gzip.open(path, "rt") as f:
            for line in f:
                r = json.loads(line, parse_float=Decimal)
                kind = r["type"]
                if kind in ("DEPOSIT", "WITHDRAWAL"):
                    counts[kind] += 1
                    hashes[kind].add(r["transaction_hash"])
                    sums[kind] += Decimal(str(r["usdc_size"]))
    return {"accounts": len(files), "activity_rows": dict(counts),
            "distinct_transactions": {k: len(v) for k, v in hashes.items()}, "gross_usd": {k: str(v) for k, v in sums.items()}}


def eight_accounts():
    folder = ROOT / "investigations/maduro-iran"
    cohort = json.loads((folder / "results/accounting_audit_2026-11-04.json").read_text())["wallets"]
    raw = json.loads((folder / "sources/phase2/pnl_table.json").read_text(), parse_float=Decimal)
    rows = [r for r in raw if r["wallet"] in cohort]
    if len(rows) != len(set(cohort)) or {r["wallet"] for r in rows} != set(cohort):
        raise ValueError("ambiguous eight-account ledger")
    net = sum(r["SELL"] + r["REDEEM"] + r["MERGE"] + r["cur"] - r["BUY"] - r["SPLIT"] for r in rows)
    return {"accounts": len(rows), "components_usd": str(net), "rounded_once_usd": str(net.quantize(Decimal("0.01")))}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    files = [DATA / "pairs.csv", DATA / "transfers.csv", *sorted(ACTIVITY.glob("*.jsonl.gz")), HERE / "RELAY_PROTOCOL.md"]
    files.extend(ROOT / "investigations/maduro-iran" / p for p in ("results/accounting_audit_2026-11-04.json", "sources/phase2/pnl_table.json"))
    result = {"inputs": {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
              "relay": relay(), "ballon": ballon(), "eight_account_network": eight_accounts()}
    text = json.dumps(result, sort_keys=True, indent=2) + "\n"
    if args.check:
        if text != (HERE / "cases.json").read_text():
            raise SystemExit("case replay differs")
        print("archived Relay paths, Ballon activity and eight-account ledger reproduced")
    else:
        print(text, end="")


if __name__ == "__main__":
    main()
