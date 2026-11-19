#!/usr/bin/env python3
"""Read-only audit of archived Polymarket order-book status events.

This measures status-record quality, not actual executed trade results.
"""
import argparse
import json
import math
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[2] / "edge_research" / "data" / "book_status.jsonl"
EXPECTED = {
    "status_records": 1327,
    "distinct_assets": 40,
    "desynchronized_records": 1327,
    "synchronized_true": 0,
    "best_bid_true": 1326,
    "best_ask_true": 1326,
    "both_best_quotes_true": 1325,
    "depth_true": 368,
    "both_quotes_and_depth_true": 368,
    "hash_true": 0,
    "hash_false": 247,
    "hash_null": 1080,
    "strictly_verified_book_state": 0,
}


def load_rows(path):
    rows = []
    required = {"asset_id", "t", "status", "synchronized", "best_bid",
                "best_ask", "depth", "hash_match"}
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Malformed JSON line {line_no}") from exc
        if not isinstance(row, dict) or not required.issubset(row):
            raise ValueError(f"Invalid schema at line {line_no}")
        if not isinstance(row["asset_id"], str) or not row["asset_id"]:
            raise ValueError(f"Missing asset at line {line_no}")
        if not isinstance(row["status"], str):
            raise ValueError(f"Invalid status at line {line_no}")
        if isinstance(row["t"], bool) or not isinstance(row["t"], (int, float)) or not math.isfinite(row["t"]):
            raise ValueError(f"Invalid timestamp at line {line_no}")
        if any(type(row[k]) is not bool for k in ("synchronized", "best_bid", "best_ask", "depth")):
            raise ValueError(f"Invalid Boolean flag at line {line_no}")
        if row["hash_match"] is not None and type(row["hash_match"]) is not bool:
            raise ValueError(f"Invalid hash flag at line {line_no}")
        rows.append(row)
    if not rows:
        raise ValueError("Empty status-record archive")
    return rows


def summarize(rows):
    def count(test):
        return sum(bool(test(r)) for r in rows)

    def both(r):
        return r["best_bid"] and r["best_ask"]

    def full(r):
        return (r["synchronized"] and r["status"] != "desynchronized"
                and both(r) and r["depth"] and r["hash_match"] is True)
    time_bounds = [r["t"] for r in rows]
    def ts(value):
        return datetime.fromtimestamp(value, tz=timezone.utc).isoformat()
    return {
        "status_records": len(rows),
        "distinct_assets": len({r["asset_id"] for r in rows}),
        "desynchronized_records": count(lambda r: r["status"] == "desynchronized"),
        "synchronized_true": count(lambda r: r["synchronized"]),
        "best_bid_true": count(lambda r: r["best_bid"]),
        "best_ask_true": count(lambda r: r["best_ask"]),
        "both_best_quotes_true": count(both),
        "depth_true": count(lambda r: r["depth"]),
        "both_quotes_and_depth_true": count(lambda r: both(r) and r["depth"]),
        "hash_true": count(lambda r: r["hash_match"] is True),
        "hash_false": count(lambda r: r["hash_match"] is False),
        "hash_null": count(lambda r: r["hash_match"] is None),
        "strictly_verified_book_state": count(full),
        "earliest_utc": ts(min(time_bounds)),
        "latest_utc": ts(max(time_bounds)),
    }


def self_test():
    good = {"asset_id": "A", "t": 1.0, "status": "synchronized",
            "synchronized": True, "best_bid": True, "best_ask": True,
            "depth": True, "hash_match": True}
    bad = dict(good, asset_id="B", status="desynchronized", synchronized=False)
    out = summarize([good, bad])
    assert out["strictly_verified_book_state"] == 1
    assert out["desynchronized_records"] == 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="verify pinned status-record counts")
    ap.add_argument("--self-test", action="store_true", help="run synthetic logic test")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        print("Synthetic tests passed")
        return
    result = summarize(load_rows(SOURCE))
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.check:
        for k, expected in EXPECTED.items():
            if result[k] != expected:
                raise SystemExit(f"Snapshot mismatch: {k}: {result[k]} != {expected}")


if __name__ == "__main__":
    main()
