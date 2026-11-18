#!/usr/bin/env python3
"""Fresh hold-out population for mission 5 (falsification), outcome-blind.

Written 2026-11-17 before any hold-out tape was fetched, before any label was read for these markets.

Rule (all inputs are known before resolution or are the frozen 13-Nov population rules):
  * population  = research_notes/early-detection-2026-11-13/study/derived/universe_markets.jsonl.gz (origin/main 0d79ba6)
  * volume < 1,000,000 USD (same cap as the 16-Nov study, so the hold-out matches the TRAIN sample)
  * h = int(sha256(condition_id)[:8], 16) % 1000, keep 50 <= h < 350  (h < 50 was read by the 16-Nov study)
  * split by closed_ts with the frozen bounds: keep VALID and TEST only (TRAIN comes from the h < 50 sample)
  * drop every market of an event that holds any market of the already-read sample (sample_expanded.jsonl),
    so no hold-out event shares an outcome with a market already looked at
  * drop the Iran event family (event_slug starting with 'us-strikes-iran') and the 28-Feb condition, always

usage: col_10_population.py UNIVERSE.jsonl.gz SEEN_SAMPLE.jsonl OUT.jsonl
"""
import datetime as dt
import gzip
import hashlib
import json
import sys

IRAN_CID = "0x3488f31e6449f9803f99a8b5dd232c7ad883637f1c86e6953305a2ef19c77f20"
U = dt.timezone.utc
BOUNDS = (("TRAIN", dt.datetime(2025, 1, 1, tzinfo=U), dt.datetime(2025, 12, 31, 23, 59, 59, tzinfo=U)),
          ("VALID", dt.datetime(2026, 1, 1, tzinfo=U), dt.datetime(2026, 6, 30, 23, 59, 59, tzinfo=U)),
          ("TEST", dt.datetime(2026, 7, 1, tzinfo=U), dt.datetime(2026, 10, 31, 23, 59, 59, tzinfo=U)))
LO, HI = 50, 350


def hband(cid):
    return int(hashlib.sha256(cid.encode()).hexdigest()[:8], 16) % 1000


def split_of(ts):
    t = dt.datetime.fromtimestamp(ts, U)
    for name, lo, hi in BOUNDS:
        if lo <= t <= hi:
            return name
    return "EXCLUDED_PERIOD"


def is_iran(m):
    return m["condition_id"].lower() == IRAN_CID or (m.get("event_slug") or "").startswith("us-strikes-iran")


def select(universe, seen):
    seen_cids = {m["condition_id"].lower() for m in seen}
    seen_events = {str(m["event_id"]) for m in seen}
    out, drop = [], {}

    def d(k):
        drop[k] = drop.get(k, 0) + 1

    for m in universe:
        cid = m["condition_id"].lower()
        if is_iran(m):
            d("iran"); continue
        if float(m.get("volume") or 0) >= 1e6:
            d("volume_ge_1M"); continue
        h = hband(cid)
        if not (LO <= h < HI):
            d("hash_outside_band"); continue
        s = split_of(m["closed_ts"])
        if s not in ("VALID", "TEST"):
            d(f"period_{s}"); continue
        if cid in seen_cids:
            d("market_already_read"); continue
        if str(m["event_id"]) in seen_events:
            d("event_already_read"); continue
        out.append({**m, "hash_band": h, "split": s})
    out.sort(key=lambda m: m["condition_id"])
    return out, drop


def _selfcheck():
    seen = [{"condition_id": "0xaa", "event_id": "1"}]
    base = {"volume": 10, "closed_ts": dt.datetime(2026, 8, 1, tzinfo=U).timestamp(), "event_slug": "x"}
    cands = [{**base, "condition_id": f"0x{i:04x}", "event_id": str(i % 3)} for i in range(400)]
    out, _ = select(cands, seen)
    assert out and all(LO <= m["hash_band"] < HI and m["event_id"] != "1" and m["split"] == "TEST" for m in out)
    assert not select([{**base, "condition_id": IRAN_CID, "event_id": "9"}], [])[0]
    assert not select([{**base, "condition_id": "0xbeef", "event_id": "9", "event_slug": "us-strikes-iran-by"}], [])[0]


def main():
    _selfcheck()
    uni_path, seen_path, out_path = sys.argv[1:4]
    universe = [json.loads(l) for l in gzip.open(uni_path, "rt")]
    seen = [json.loads(l) for l in open(seen_path)]
    out, drop = select(universe, seen)
    with open(out_path, "w") as f:
        for m in out:
            f.write(json.dumps(m, sort_keys=True) + "\n")
    counts = {}
    for m in out:
        counts[m["split"]] = counts.get(m["split"], 0) + 1
    ev = {s: len({m["event_id"] for m in out if m["split"] == s}) for s in counts}
    print(json.dumps({"universe": len(universe), "seen_sample": len(seen), "kept": len(out), "by_split": counts,
                      "events_by_split": ev, "dropped": drop,
                      "out_sha256": hashlib.sha256(open(out_path, "rb").read()).hexdigest()}, sort_keys=True))


if __name__ == "__main__":
    main()
