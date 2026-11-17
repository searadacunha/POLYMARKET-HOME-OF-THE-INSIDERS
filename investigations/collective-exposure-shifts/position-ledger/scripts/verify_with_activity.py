#!/usr/bin/env python3
"""Re-read episodes of one partition with each wallet's public activity feed (SPLIT / MERGE are invisible in fills).

For every (wallet, market) of the selected episodes: fetch /v2/activity (cached under --cache), check that the
wallet's TRADE rows match its tape fills transaction by transaction, add its SPLIT and MERGE events (up to the
market's last fill), mark merges as visible for that wallet only, and classify the same windows again.
Reads no outcome label. Activity types that cannot be mapped (CONVERSION, REDEEM before the last fill) are counted
and make that pair UNRESOLVED, never ignored.

usage: verify_with_activity.py --run out/full --partition TRAIN --classes D_UNVERIFIED_NO_RETENTION A_TRUE_INVERSION
       --tapes T1 --tapes T2 --meta data/gamma_meta.jsonl --cache data/activity --out out/full/verify_TRAIN.json
"""
import argparse, collections, json, os, sqlite3, sys, time, urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger as L  # noqa: E402
from example_portfolio import fetch_activity  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--partition", required=True)
    ap.add_argument("--classes", nargs="+", required=True)
    ap.add_argument("--families", nargs="+", default=["binary"])
    ap.add_argument("--tapes", action="append", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    meta = {json.loads(l)["condition_id"]: json.loads(l) for l in open(a.meta)}
    eps = [json.loads(l) for l in open(os.path.join(a.run, "episodes.jsonl"))]
    eps = [e for e in eps if e["partition"] == a.partition and e["class"] in a.classes and e["family"] in a.families]
    pairs = collections.defaultdict(list)
    for e in eps:
        pairs[(e["wallet"], e["members"][0])].append(e)
    print(f"episodes {len(eps)}, wallet-market pairs {len(pairs)}", flush=True)
    cons = [sqlite3.connect(f"file:{urllib.parse.quote(os.path.abspath(p))}?mode=ro&immutable=1", uri=True)
            for p in a.tapes]

    def tape_of(cid):
        for con in cons:
            r = con.execute("select status from status where condition_id=?", (cid,)).fetchone()
            if r:
                rows = con.execute("select rowid, condition_id, ts, wallet, side, outcome, outcome_index, size, price, tx "
                                   "from trades where condition_id=? order by ts, rowid", (cid,)).fetchall()
                return r[0], rows
        raise KeyError(cid)

    trans = collections.Counter()
    per_pair = []
    activity_types = collections.Counter()
    loaded = {}
    for i, ((w, cid), elist) in enumerate(sorted(pairs.items())):
        cpath = os.path.join(a.cache, f"{w}_{cid}.json")
        if os.path.exists(cpath):
            act = json.load(open(cpath))
        else:
            act = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "rows": fetch_activity(w, cid)}
            json.dump(act, open(cpath, "w"))
            time.sleep(0.2)
        if cid not in loaded:
            loaded.clear()
            status, rows = tape_of(cid)
            loaded[cid] = (status, L.events_from_tape_rows(rows, "tape"))
        status, fills = loaded[cid]
        last_fill = max(e["ts"] for e in fills)
        activity_types.update(x["type"] for x in act["rows"])
        proto, unmapped = [], []
        for j, x in enumerate(act["rows"]):
            ts = int(x["timestamp"])
            if x["type"] in ("SPLIT", "MERGE") and ts <= last_fill:
                proto.append(L.make_event(ts, w, cid, x["type"], qty=x["size"], tx=x.get("transaction_hash"),
                                          seq=10 ** 9 + j, src=f"activity#{j}"))
            elif x["type"] in ("TRADE", "SPLIT", "MERGE"):
                continue
            elif x["type"] == "REDEEM":
                if ts <= last_fill:           # burns every token of the condition held (no outcome in the feed)
                    proto.append(L.make_event(ts, w, cid, "REDEEM", oi=None, qty=x.get("size") or 0.0,
                                              usdc=x.get("usdc_size"), tx=x.get("transaction_hash"),
                                              seq=10 ** 9 + j, src=f"activity#{j}"))
            else:
                unmapped.append(x["type"])
        # tape vs activity trades, per (tx, side, outcome)
        tape_w, act_w = collections.Counter(), collections.Counter()
        for e in fills:
            if e["wallet"] == w:
                tape_w[(e["tx"], e["kind"], e["oi"])] += e["qty"]
        for x in act["rows"]:
            if x["type"] == "TRADE":
                act_w[(x["transaction_hash"].lower(), x["side"], x["outcome_index"])] += float(x["size"])
        mism = sum(1 for k in set(tape_w) | set(act_w) if abs(tape_w[k] - act_w[k]) > 1e-3)
        g = meta.get(cid, {})
        base = {"history_complete": status == "ok", "neg_risk": g.get("negRisk"), "fees_enabled": g.get("feesEnabled"),
                "coverage": L.TAPE_COVERAGE}
        tape_lg = L.Ledger(fills, {cid: base})
        seen = {**base, "wallet_coverage": {w: {**L.TAPE_COVERAGE, "split_merge": True, "redeem": True}}}
        full_lg = L.Ledger(fills + proto, {cid: seen})
        fam = L.family_binary(cid)
        for e in elist:
            before = L.classify(tape_lg, w, fam, e["t0"], e["t1"])["class"]
            after = "UNRESOLVED_ACTIVITY" if unmapped or mism else L.classify(full_lg, w, fam, e["t0"], e["t1"])["class"]
            trans[(e["class"], before, after)] += 1
        per_pair.append({"wallet": w, "cid": cid, "episodes": len(elist), "splits": sum(p["kind"] == "SPLIT" for p in proto),
                         "merges": sum(p["kind"] == "MERGE" for p in proto), "unmapped": collections.Counter(unmapped),
                         "trade_mismatches": mism, "tape_trade_keys": len(tape_w), "activity_trade_keys": len(act_w),
                         "activity_rows": len(act["rows"]), "fetched_at": act.get("fetched_at")})
        if (i + 1) % 25 == 0:
            print(i + 1, flush=True)
    res = {"partition": a.partition, "classes": a.classes, "episodes": len(eps), "pairs": len(pairs),
           "transitions": [{"run_class": k[0], "tape_reclassified": k[1], "with_activity": k[2], "n": n}
                           for k, n in sorted(trans.items())],
           "pairs_with_trade_mismatch": sum(1 for p in per_pair if p["trade_mismatches"]),
           "pairs_with_merges": sum(1 for p in per_pair if p["merges"]),
           "pairs_with_splits": sum(1 for p in per_pair if p["splits"]),
           "activity_types": activity_types, "per_pair": per_pair}
    json.dump(res, open(a.out, "w"), indent=1, default=dict)
    print(json.dumps({k: v for k, v in res.items() if k != "per_pair"}, indent=1, default=dict))


if __name__ == "__main__":
    main()
