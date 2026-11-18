#!/usr/bin/env python3
"""History-only markets for mission 5, outcome-blind. Written 2026-11-17 before any of these tapes was fetched.

Markets of band [50, 350), volume < 1 M USD, closed in VALID or TEST, that col_10 dropped because their event was
already read by the 16-Nov study. They are never evaluated and their labels are never joined. Their fills only
feed the wallet-history pool (habits, first-seen age, repeated pairs, lead/follow), so that the pool has the same
band density in 2026 as in 2025 (where TRAIN covers the whole band).

usage: col_12_history_population.py UNIVERSE.jsonl.gz SEEN_SAMPLE.jsonl OUT.jsonl
"""
import gzip
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from col_10_population import LO, HI, hband, is_iran, split_of  # noqa: E402


def main():
    uni, seen_path, out_path = sys.argv[1:4]
    seen = [json.loads(l) for l in open(seen_path)]
    seen_cids = {m["condition_id"].lower() for m in seen}
    seen_events = {str(m["event_id"]) for m in seen}
    out = []
    for l in gzip.open(uni, "rt"):
        m = json.loads(l)
        cid = m["condition_id"].lower()
        if is_iran(m) or float(m.get("volume") or 0) >= 1e6 or not (LO <= hband(cid) < HI):
            continue
        if split_of(m["closed_ts"]) not in ("VALID", "TEST") or cid in seen_cids:
            continue
        if str(m["event_id"]) in seen_events:
            out.append({**m, "hash_band": hband(cid), "split": "HISTORY_ONLY"})
    out.sort(key=lambda m: m["condition_id"])
    with open(out_path, "w") as f:
        for m in out:
            f.write(json.dumps(m, sort_keys=True) + "\n")
    print(json.dumps({"kept": len(out), "out_sha256": hashlib.sha256(open(out_path, "rb").read()).hexdigest()}))


if __name__ == "__main__":
    main()
