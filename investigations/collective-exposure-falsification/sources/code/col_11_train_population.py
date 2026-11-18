#!/usr/bin/env python3
"""TRAIN extension for mission 5, outcome-blind. Written 2026-11-17 before any of these tapes was fetched.

Why: wallet-history features (habits, first-seen age, repeated pairs, lead/follow) depend on how many markets the
history pool holds. The hold-out uses hash band [50, 350); TRAIN must use the same band density, otherwise the
coefficients fitted on TRAIN meet a shifted feature distribution out of sample.

Rule: same population, volume < 1 M USD, 50 <= h < 350, closed in TRAIN (2025), Iran family excluded, and every
market of an event that also holds a hold-out (VALID/TEST) market is purged, so no outcome is shared across splits.

usage: col_11_train_population.py UNIVERSE.jsonl.gz HOLDOUT.jsonl OUT.jsonl
"""
import gzip
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from col_10_population import LO, HI, hband, is_iran, split_of  # noqa: E402


def select(universe, holdout):
    hold_events = {str(m["event_id"]) for m in holdout}
    out, drop = [], {}
    for m in universe:
        k = None
        if is_iran(m):
            k = "iran"
        elif float(m.get("volume") or 0) >= 1e6:
            k = "volume_ge_1M"
        elif not (LO <= hband(m["condition_id"].lower()) < HI):
            k = "hash_outside_band"
        elif split_of(m["closed_ts"]) != "TRAIN":
            k = "not_TRAIN"
        elif str(m["event_id"]) in hold_events:
            k = "event_in_holdout_purged"
        if k:
            drop[k] = drop.get(k, 0) + 1
            continue
        out.append({**m, "hash_band": hband(m["condition_id"].lower()), "split": "TRAIN"})
    out.sort(key=lambda m: m["condition_id"])
    return out, drop


def main():
    uni, hold, out_path = sys.argv[1:4]
    universe = [json.loads(l) for l in gzip.open(uni, "rt")]
    holdout = [json.loads(l) for l in open(hold)]
    out, drop = select(universe, holdout)
    assert not ({m["event_id"] for m in out} & {m["event_id"] for m in holdout})
    with open(out_path, "w") as f:
        for m in out:
            f.write(json.dumps(m, sort_keys=True) + "\n")
    print(json.dumps({"kept": len(out), "events": len({m["event_id"] for m in out}), "dropped": drop,
                      "out_sha256": hashlib.sha256(open(out_path, "rb").read()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
