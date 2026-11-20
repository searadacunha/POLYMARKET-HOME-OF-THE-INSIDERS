#!/usr/bin/env python3
"""Build data/ from a local Relay archive (no network). Not needed to verify the note: verify.py reads data/.

usage: python3 -I build.py ARCHIVE_DIR [--snapshot]
The archive (queue.tsv, manifest.jsonl, raw/) is produced by a polite collector of the public Relay requests API.
Its raw pages stay local; data/archive_manifest.jsonl records the SHA-256 of every page that was read.
--snapshot rebuilds from the pages listed in the committed data/archive_manifest.jsonl instead of the archive's own
manifest, so that the published snapshot can be rebuilt while the collector keeps adding pages.
"""
import csv
import json
import shutil
import sys
from collections import Counter
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
        via_after = ""
        if e["via"]:  # orders of the address in the middle dated at or after the first payment into it
            via_after = sum(1 for o in e["orders_via"] if by_order[o]["in_time"] and times and by_order[o]["in_time"] >= min(times))
        yield {"from": e["from"], "to": e["to"], "via": e["via"] or "", "via_pays": e["via_pays"] or "",
               "n_orders": len(e["orders"]), "n_orders_via": len(e["orders_via"]), "n_orders_via_after": via_after,
               "usd_in": f"{sum(float(r['usd_in']) for r in own):.2f}",  # a missing USD value raises, it is never read as 0
               "first_utc": utc(min(times)) if times else "", "last_utc": utc(max(times)) if times else "",
               "label_from": labels[e["from"]], "label_to": labels[e["to"]]}


def gainers(txs):
    """Addresses whose balance rises in the state changes that the API recorded for these transactions."""
    out = set()
    for tx in txs or []:
        for change in tx.get("stateChanges") or []:
            try:
                if int(change["change"].get("balanceDiff", "0")) > 0:
                    out.add(rg.norm(change["address"]))
            except (KeyError, TypeError, ValueError):
                continue
    return out


def conflict_rows(orders, complete):
    for order_id in rg.field_conflicts(orders):
        order = orders[order_id]
        data = order.get("data") or {}
        row = rg.order_row(order_id, order)
        top = rg.norm(order["recipient"])
        gain_in, gain_out = gainers(data.get("inTxs")), gainers(data.get("outTxs"))
        yield {"order": order_id, "status": row["status"], "sender": row["sender"], "metadata_recipient": row["recipient"],
               "order_recipient": top, "in_chain": row["in_chain"], "out_chain": row["out_chain"],
               "order_recipient_gains": "deposit" if top in gain_in else "fill" if top in gain_out else "",
               "metadata_recipient_gains": "fill" if row["recipient"] in gain_out else "",
               "joins_two_complete_if_order_recipient": int(row["sender"] in complete and top in complete and top != row["sender"])}


def write(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main(archive, snapshot=False):
    archive, data = Path(archive), NOTE / "data"
    manifest = data / "archive_manifest.jsonl" if snapshot else archive / "manifest.jsonl"
    stats = {}
    labels, complete, orders = rg.load(archive, manifest=manifest, stats=stats)
    rows = rg.transfers(orders)
    write(data / "accounts.csv", [{"address": a, "complete": int(a in complete), "label": labels[a]} for a in sorted(labels, key=str)],
          ["address", "complete", "label"])
    write(data / "transfers.csv", rows, list(rows[0]))
    pairs = list(pair_rows(rows, complete, labels))
    write(data / "pairs.csv", pairs, list(pairs[0]))
    conflicts = list(conflict_rows(orders, complete))
    write(data / "field_conflicts.csv", conflicts, list(conflicts[0]))
    kept = [line for line in manifest.read_text(encoding="utf-8").splitlines()
            if (m := json.loads(line))["kind"] == "user" and m.get("status") == 200 and rg.norm(m["value"]) in complete]
    if not snapshot:
        (data / "archive_manifest.jsonl").write_text("\n".join(kept) + "\n", encoding="utf-8")
    for line in kept:
        m = json.loads(line)
        if rg.norm(m["value"]) in EVIDENCE_PAGES:
            shutil.copyfile(archive / m["file"], NOTE / "evidence" / "relay" / Path(m["file"]).name)
    pages = [json.loads(line) for line in kept]
    listed = Counter()
    for p in pages:
        listed[rg.norm(p["value"])] += p["n_requests"]
    census = {
        "snapshot_first_fetch_utc": min(p["fetched_utc"] for p in pages), "snapshot_last_fetch_utc": max(p["fetched_utc"] for p in pages),
        "addresses_asked": len(labels), "histories_complete": len(complete), **stats,
        "pages_body_bytes": sum(p["bytes"] for p in pages), "pages_gzip_bytes": sum((archive / p["file"]).stat().st_size for p in pages),
        "page_entries_sum": sum(p["n_requests"] for p in pages), "orders_unique": len(orders),
        "transfers": len(rows), "orders_without_two_distinct_parties": len(orders) - len(rows),
        "transfers_by_status": dict(sorted(Counter(r["status"] for r in rows).items())),
        "complete_histories_without_orders": sum(1 for a in complete if listed[a] == 0),
        "successful_transfers_without_fill_hash": sum(1 for r in rows if r["status"] == "success" and not r["out_tx"]),
        "orders_naming_two_recipients": len(conflicts),
        "of_which_order_recipient_gains_in_deposit": sum(c["order_recipient_gains"] == "deposit" for c in conflicts),
        "of_which_order_recipient_gains_in_fill": sum(c["order_recipient_gains"] == "fill" for c in conflicts),
        "of_which_neither_gains_in_recorded_changes": sum(not c["order_recipient_gains"] and not c["metadata_recipient_gains"] for c in conflicts),
        "of_which_would_join_two_complete_histories": sum(c["joins_two_complete_if_order_recipient"] for c in conflicts),
    }
    # why the other histories were not complete at the snapshot: read from the archive's own manifest up to that time
    seen = {}
    for line in (archive / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
        m = json.loads(line)
        if m["kind"] == "user" and m["fetched_utc"] <= census["snapshot_last_fetch_utc"]:
            seen.setdefault(rg.norm(m["value"]), []).append(m.get("status"))
    census["incomplete_by_reason"] = dict(sorted(Counter(
        "not asked yet" if a not in seen else "partly read" if set(seen[a]) == {200} else "an error or 429 answer among its reads"
        for a in labels if a not in complete).items()))
    (data / "census.json").write_text(json.dumps(census, indent=1) + "\n", encoding="utf-8")
    print(json.dumps(census, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], snapshot="--snapshot" in sys.argv[2:])
