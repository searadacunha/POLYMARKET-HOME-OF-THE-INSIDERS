#!/usr/bin/env python3
"""Fetch Gamma metadata (rules text, deadlines, contract version, fees, neg-risk flags) for a list of markets.

Read-only public API. Resumable: condition ids already present in the output are skipped. Every row keeps the
fetch time and the sha256 of the raw market JSON, so a later reader can tell what was known and when.
A market Gamma does not return is written as {"condition_id": ..., "status": "missing"}, never dropped.

usage: fetch_meta.py --markets sample_markets.jsonl [--markets more.jsonl] [--extra 0xcid ...] --out meta.jsonl
"""
import argparse, hashlib, json, os, sys, time, urllib.request

GAMMA = "https://gamma-api.polymarket.com/markets"
KEEP = ("conditionId", "question", "description", "resolutionSource", "endDate", "closedTime", "createdAt",
        "startDate", "negRisk", "negRiskMarketID", "negRiskOther", "version", "feesEnabled", "feeType",
        "outcomes", "clobTokenIds", "groupItemTitle", "slug")   # no outcome field (outcomePrices, resolution status)
EVENT_KEEP = ("id", "slug", "negRisk", "enableNegRisk", "negRiskAugmented")


def get(url):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-client"}),
                                        timeout=60) as r:
                return json.loads(r.read())
        except Exception as e:  # retried, then raised: never turned into an empty result
            if attempt == 4:
                raise
            time.sleep(2 * (attempt + 1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--markets", action="append", default=[])
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cids = []
    for path in a.markets:
        for line in open(path):
            cids.append(json.loads(line)["condition_id"])
    cids += a.extra
    cids = list(dict.fromkeys(c.lower() for c in cids))
    done = set()
    if os.path.exists(a.out):
        for line in open(a.out):
            done.add(json.loads(line)["condition_id"])
    todo = [c for c in cids if c not in done]
    print(f"markets {len(cids)}, todo {len(todo)}", flush=True)
    with open(a.out, "a") as out:
        for i in range(0, len(todo), 40):
            chunk = todo[i:i + 40]
            got = {}
            for closed in ("true", "false"):
                q = "&".join(f"condition_ids={c}" for c in chunk if c not in got)
                if not q:
                    break
                for m in get(f"{GAMMA}?{q}&closed={closed}&limit=100"):
                    got[m["conditionId"].lower()] = m
            now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            for c in chunk:
                m = got.get(c)
                if m is None:
                    row = {"condition_id": c, "status": "missing", "fetched_at": now}
                else:
                    raw = json.dumps(m, sort_keys=True).encode()
                    row = {"condition_id": c, "status": "ok", "fetched_at": now,
                           "raw_sha256": hashlib.sha256(raw).hexdigest(),
                           **{k: m.get(k) for k in KEEP},
                           "event": {k: (m.get("events") or [{}])[0].get(k) for k in EVENT_KEEP}}
                out.write(json.dumps(row) + "\n")
            out.flush()
            print(i + len(chunk), flush=True)
            time.sleep(0.3)


if __name__ == "__main__":
    main()
