#!/usr/bin/env python3
"""Verify the Pulser–cashy–Car transaction index.

Offline: python3 -I verify.py
Re-derive from PR29's immutable 7,596-row source:
         python3 -I verify.py --source-github
Or:      python3 -I verify.py --source-file /path/to/data/flows.csv
"""
import argparse
import csv
import io
import json
import re
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parent
COMMIT = "c69ce98cea602ba01c434e4c68c2f5b8647a8463"
BASE = ("https://raw.githubusercontent.com/searadacunha/"
        "Polymarket-Home-of-the-Insiders/" + COMMIT
        + "/research_notes/inca-crosscheck-2026-11-06/data/")
PULSER = "0x6a8328b1ae11569f7b27600073558879885e4c59"
CASHY = "0x8f42ae0a01c0383c7ca8bd060b86a645ee74b88f"
CAR = "0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b"
OTHER_A = "0x5e9c76f30788f31f6c6867f5f44b1e95a7a7cd75"
OTHER_B = "0x8f7a4b414417911e7e9bd738399874792cdbdb40"
GROUP = {PULSER, CASHY, CAR}
AMOUNT_TOLERANCE = Decimal("0.000002")
FIELDS = ["from_wallet", "to_wallet", "usdc_amount", "timestamp_utc",
          "polygon_tx_hash", "source_commit"]


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def read_csv_text(s):
    return list(csv.DictReader(io.StringIO(s)))


def download(name):
    with urllib.request.urlopen(BASE + name, timeout=45) as resp:
        require(resp.status == 200, "HTTP response was not 200")
        return resp.read().decode("utf-8")


def iso(ts):
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def normalize(row):
    require(set(row) == set(FIELDS), "unexpected evidence columns")
    require(re.fullmatch(r"0x[a-f0-9]{40}", row["from_wallet"]) is not None,
            "invalid source wallet")
    require(re.fullmatch(r"0x[a-f0-9]{40}", row["to_wallet"]) is not None,
            "invalid destination wallet")
    require(re.fullmatch(r"0x[a-f0-9]{64}", row["polygon_tx_hash"]) is not None,
            "invalid transaction hash")
    require(row["from_wallet"] != row["to_wallet"], "self transfer")
    require(row["source_commit"] == COMMIT, "source SHA not pinned")
    require(Decimal(row["usdc_amount"]) > 0, "non-positive amount")
    datetime.strptime(row["timestamp_utc"], "%Y-%m-%dT%H:%M:%SZ")
    return (row["from_wallet"], row["to_wallet"], Decimal(row["usdc_amount"]),
            row["timestamp_utc"], row["polygon_tx_hash"])


def from_original_flow(text):
    """Reconstruct exact same-tx withdrawal/deposit matches; refuse ambiguity."""
    entries = defaultdict(list)
    rows = read_csv_text(text)
    require(len(rows) == 7596, f"source changed or truncated: {len(rows)} rows")
    for row in rows:
        require(row["type"] in ("DEPOSIT", "WITHDRAWAL"), "unexpected row type")
        entries[row["hash"]].append(row)

    matches = []
    for tx, bundle in entries.items():
        withdrawals = [r for r in bundle if r["type"] == "WITHDRAWAL"]
        deposits = [r for r in bundle if r["type"] == "DEPOSIT"]
        candidates = []
        for a in withdrawals:
            for b in deposits:
                if (a["wallet"] != b["wallet"]
                    and a["counterparty"] == b["wallet"]
                    and b["counterparty"] == a["wallet"]
                    and abs(int(a["ts"]) - int(b["ts"])) <= 1
                    and abs(Decimal(a["usdc"]) - Decimal(b["usdc"])) < AMOUNT_TOLERANCE):
                    candidates.append((a, b))
        require(len(candidates) <= 1,
                "multiple cross-wallet matches for tx " + tx)
        if candidates:
            a, b = candidates[0]
            matches.append((a["wallet"], b["wallet"], Decimal(a["usdc"]),
                            iso(a["ts"]), tx))
    return sorted(matches, key=lambda v: (v[3], v[4]))


def checks(rows):
    require(len(rows) == 27, f"expected 27, found {len(rows)}")
    matches = [normalize(x) for x in rows]
    require(len({v[4] for v in matches}) == 27, "duplicate transaction hash")
    require(len(set(matches)) == 27, "duplicate rows")
    counts = Counter((a, b) for a, b, amount, ts, tx in matches)
    expected = {
        (CASHY, PULSER): 11,
        (PULSER, CASHY): 14,
        (CASHY, CAR): 1,
        (OTHER_A, OTHER_B): 1,
    }
    require(counts == expected, "directional count mismatch: " + repr(counts))
    def volume(src, dst):
        return sum((amt for a,b,amt,ts,tx in matches
                    if a == src and b == dst), Decimal("0"))
    require(volume(CASHY,PULSER) == Decimal("10757.999999"),
            "cashy to Pulser amount mismatch")
    require(volume(PULSER,CASHY) == Decimal("2692.0"),
            "Pulser to cashy amount mismatch")
    require(volume(CASHY,CAR) == Decimal("250.0"),
            "cashy to Car amount mismatch")
    require(volume(OTHER_A,OTHER_B) == Decimal("1000.0"),
            "second pair amount mismatch")
    require(sum((v[2] for v in matches), Decimal("0")) ==
            Decimal("14699.999999"), "aggregate mismatch")
    require(len({v[0] for v in matches} | {v[1] for v in matches}) == 5,
            "unexpected distinct sender/recipient count")
    require(matches[0][3] == "2024-12-13T14:08:20Z", "first date mismatch")
    require(matches[-1][3] == "2026-02-23T15:56:18Z", "last date mismatch")
    print("PASS offline: 27 unique direct transfer hashes; "
          "25 cashy↔Pulser + 1 cashy→Car + 1 separate; 14,699.999999 USDC")
    return sorted(matches, key=lambda v: (v[3], v[4]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--source-github", action="store_true",
                    help="read immutable PR29 flows and population from public GitHub")
    ap.add_argument("--source-file", metavar="PATH",
                    help="read a local copy of PR29 data/flows.csv instead")
    ap.add_argument("--population-file", metavar="PATH",
                    help="local population.json, used with --source-file")
    args = ap.parse_args()
    require(not (args.source_github and args.source_file),
            "choose one source option")
    indexed = checks(read_csv_text((HERE / "DIRECT_TRANSFERS.csv").read_text()))

    if args.source_github or args.source_file:
        source = (download("flows.csv") if args.source_github else
                  Path(args.source_file).read_text())
        rebuilt = from_original_flow(source)
        require(indexed == rebuilt, "index does not match full source flow data")
        print("PASS full source replay: all 7,596 rows; no missing or extra "
              "direct inter-wallet transactions")
        pop_text = (download("population.json") if args.source_github else
                    Path(args.population_file).read_text() if args.population_file else None)
        if pop_text:
            pop = {x["wallet"]: x for x in json.loads(pop_text)["population"]}
            for w in {PULSER, CASHY, CAR, OTHER_A, OTHER_B}:
                require(pop.get(w, {}).get("role") == "control",
                        "transfer participant not a control: " + w)
            print("PASS population replay: all five wallets belong to the "
                  "fixed June 2025 control cohort")
        else:
            print("SKIP population check (specify --population-file)")
    else:
        print("NOTE: offline validates the exported index only; for full upstream "
              "replay, use --source-github or --source-file.")


if __name__ == "__main__":
    main()
