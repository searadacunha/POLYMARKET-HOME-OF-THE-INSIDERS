#!/usr/bin/env python3
"""Build data/ from a local Relay archive (no network). Not needed to verify the note: verify.py reads data/.

usage: python3 -I build.py ARCHIVE_DIR
The archive (queue.tsv, manifest.jsonl, raw/) is produced by a polite collector of the public Relay requests API.
Its raw pages stay local; data/archive_manifest.jsonl records the SHA-256 of every page that was read.
"""
import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

NOTE = Path(__file__).resolve().parent
sys.path.insert(0, str(NOTE.parents[1] / "integrations" / "forensic-intelligence"))
import relay_graph as rg

EVIDENCE_PAGES = ("0x1fa1be3eab546e06e4290839bf4c1d7abfbf1fa9", "0xe25b9180f5687aa85bd94ee309bb72a464320f1b")


def utc(seconds):
    return datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if seconds else ""


def pair_rows(rows, accounts, labels):
    by_order = {r["order"]: r for r in rows}
    for e in rg.account_edges(rows, accounts):
        own = [by_order[o] for o in e["orders"]]
        times = [r["in_time"] for r in own if r["in_time"]]
        yield {"from": e["from"], "to": e["to"], "via": e["via"] or "", "via_pays": e["via_pays"] or "",
               "n_orders": len(e["orders"]), "n_orders_via": len(e["orders_via"]),
               "usd_in": f"{sum(float(r['usd_in'] or 0) for r in own):.2f}",
               "first_utc": utc(min(times)) if times else "", "last_utc": utc(max(times)) if times else "",
               "label_from": labels[e["from"]], "label_to": labels[e["to"]]}


def write(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main(archive):
    archive = Path(archive)
    labels, complete, orders = rg.load(archive)
    rows = rg.transfers(orders)
    data = NOTE / "data"
    write(data / "accounts.csv", [{"address": a, "complete": int(a in complete), "label": labels[a]} for a in sorted(labels, key=str)],
          ["address", "complete", "label"])
    write(data / "transfers.csv", rows, list(rows[0]))
    pairs = list(pair_rows(rows, complete, labels))
    write(data / "pairs.csv", pairs, list(pairs[0]))
    kept = [line for line in (archive / "manifest.jsonl").read_text(encoding="utf-8").splitlines()
            if (m := json.loads(line))["kind"] == "user" and m.get("status") == 200 and rg.norm(m["value"]) in complete]
    (data / "archive_manifest.jsonl").write_text("\n".join(kept) + "\n", encoding="utf-8")
    for line in kept:
        m = json.loads(line)
        if rg.norm(m["value"]) in EVIDENCE_PAGES:
            shutil.copyfile(archive / m["file"], NOTE / "evidence" / "relay" / Path(m["file"]).name)
    print(f"{len(labels)} addresses asked, {len(complete)} complete, {len(orders)} orders, {len(rows)} transfers, {len(pairs)} pairs")


if __name__ == "__main__":
    main(sys.argv[1])
