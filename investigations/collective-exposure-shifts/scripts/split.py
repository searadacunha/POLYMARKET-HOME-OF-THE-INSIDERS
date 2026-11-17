#!/usr/bin/env python3
"""Chronological split, outcome-free: condition_id -> TRAIN | VALID | TEST by market close time.

TRAIN  closed 2025-01-01 .. 2025-12-31 UTC
VALID  closed 2026-01-01 .. 2026-06-30 UTC
TEST   closed 2026-07-01 .. 2026-10-31 UTC
Markets outside those windows (possible if the catalogue was read later) are marked EXCLUDED_PERIOD.
"""
import datetime as dt, hashlib, json, sys

BOUNDS = [("TRAIN", dt.datetime(2025, 1, 1, tzinfo=dt.timezone.utc), dt.datetime(2025, 12, 31, 23, 59, 59, tzinfo=dt.timezone.utc)),
          ("VALID", dt.datetime(2026, 1, 1, tzinfo=dt.timezone.utc), dt.datetime(2026, 6, 30, 23, 59, 59, tzinfo=dt.timezone.utc)),
          ("TEST", dt.datetime(2026, 7, 1, tzinfo=dt.timezone.utc), dt.datetime(2026, 10, 31, 23, 59, 59, tzinfo=dt.timezone.utc))]


def split_of(closed_ts):
    t = dt.datetime.fromtimestamp(closed_ts, dt.timezone.utc)
    for name, lo, hi in BOUNDS:
        if lo <= t <= hi:
            return name
    return "EXCLUDED_PERIOD"


def main():
    universe, out = sys.argv[1], sys.argv[2]
    markets = [json.loads(l) for l in open(universe)]
    splits = {m["condition_id"]: split_of(m["closed_ts"]) for m in markets}
    json.dump(splits, open(out, "w"), indent=0, sort_keys=True)
    counts = {}
    for v in splits.values():
        counts[v] = counts.get(v, 0) + 1
    print(json.dumps({"counts": counts, "sha256": hashlib.sha256(json.dumps(splits, sort_keys=True).encode()).hexdigest()}))


if __name__ == "__main__":
    main()
