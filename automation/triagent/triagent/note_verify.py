"""Offline re-check of this TriAgent campaign note, from its own files only. No network. Exit code 1 on any failure.

A  every file archived in evidence/ has the SHA-256 recorded in SOURCES.csv
B  every receipt-verified flow whose receipt is archived here shows an ERC-20 Transfer log from its source to its
   destination (the rule the supervisor applied before marking it verified)
C  every published claim cites only sources listed in SOURCES.csv, or a repository file (repo:<path>)
D  every timeline phase follows from the timestamps in meta.json (A before the first bet, B before the event, C after)
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
FAILS = []


def rows(name):
    with open(HERE / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def phase(ts, first_trade, event):
    if not first_trade or ts is None:
        return ""
    return "A" if ts < first_trade else ("B" if not event or ts < event else "C")


def main():
    sources = {r["sha256"]: r for r in rows("SOURCES.csv")}
    included = 0
    for sha, r in sources.items():
        if r["included"] == "yes":
            included += 1
            p = HERE / r["path"]
            if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != sha:
                FAILS.append(f"A: {r['path']} does not match {sha}")
    flows = 0
    for f in rows("FLOWS.csv"):
        src = sources.get(f["evidence_sha256"])
        if f["level"] != "receipt_verified" or not src or src["included"] != "yes":
            continue
        data = json.loads((HERE / src["path"]).read_text())
        receipt = data.get("result", data) if isinstance(data, dict) else {}
        logs = (receipt or {}).get("logs", [])
        if not any(len(lg.get("topics", [])) == 3 and lg["topics"][0] == TRANSFER and
                   "0x" + lg["topics"][1][26:].lower() == f["src"] and "0x" + lg["topics"][2][26:].lower() == f["dst"]
                   for lg in logs):
            FAILS.append(f"B: no Transfer {f['src']} -> {f['dst']} in {f['tx_hash']}")
        flows += 1
    claims = rows("CLAIMS.csv")
    for c in claims:
        for ev in c["evidence_ids"].split():
            if ev not in sources and not ev.startswith("repo:"):
                FAILS.append(f"C: claim {c['n']} cites unlisted evidence {ev}")
    meta = json.loads((HERE / "meta.json").read_text())
    timeline = rows("TIMELINE.csv")
    for t in timeline:
        ts = int(t["unix"]) if t["unix"] else None
        if t["phase"] != phase(ts, meta.get("first_trade_ts"), meta.get("event_ts")):
            FAILS.append(f"D: phase of '{t['event'][:60]}' is {t['phase']!r}")
    print(f"sources {len(sources)} ({included} archived here), receipt flows {flows}, claims {len(claims)}, "
          f"timeline {len(timeline)}: {len(FAILS)} failure(s)")
    for line in FAILS:
        print("FAIL", line)
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
