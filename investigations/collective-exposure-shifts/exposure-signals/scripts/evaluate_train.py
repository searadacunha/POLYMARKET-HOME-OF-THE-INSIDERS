#!/usr/bin/env python3
"""Preliminary TRAIN-only comparison of the detector families with price alone and price/volume alone.

Exploratory. Not evidence of predictability: thresholds are untuned but many families and variants are compared on
the same TRAIN data, no correction is applied, and nothing here is a test. Labels must be pre-filtered to TRAIN
condition ids (the script refuses any other id).

usage: evaluate_train.py --run out/observed --labels-train labels_train.jsonl --params params.json --out F.json
                         --markets M.jsonl [--markets ...]
"""
import argparse
import gzip
import hashlib
import json
import random
from collections import defaultdict

SEED, DRAWS = 20261117, 2000


def boot(units, key, seed=SEED):
    """Event-clustered bootstrap of mean(key) over units; returns mean, 2.5 %, 97.5 %, n units, n events."""
    by_ev = defaultdict(list)
    for u in units:
        by_ev[u["event_id"]].append(u[key])
    evs = sorted(by_ev)
    if not evs:
        return {"n": 0, "events": 0}
    vals = [sum(sum(by_ev[e]) for e in evs) / sum(len(by_ev[e]) for e in evs)]
    rnd = random.Random(seed)
    draws = []
    for _ in range(DRAWS):
        pick = [evs[rnd.randrange(len(evs))] for _ in evs]
        s = sum(sum(by_ev[e]) for e in pick)
        n = sum(len(by_ev[e]) for e in pick)
        draws.append(s / n)
    draws.sort()
    return {"mean": vals[0], "lo95": draws[int(0.025 * DRAWS)], "hi95": draws[int(0.975 * DRAWS)],
            "n": len(units), "events": len(evs)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True)
    ap.add_argument("--labels-train", required=True)
    ap.add_argument("--params", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--markets", action="append", required=True)
    a = ap.parse_args()
    event_of = {}
    for path in a.markets:
        for line in open(path):
            m = json.loads(line)
            event_of.setdefault(m["condition_id"].lower(), str(m["event_id"]))
    P = json.load(open(a.params))
    train = {json.loads(l)["condition_id"] for l in open(f"{a.run}/market_stats.jsonl")}
    win_of = {}
    for line in open(a.labels_train):
        r = json.loads(line)
        c = r["condition_id"].lower()
        if c not in train:
            raise SystemExit(f"refused: label for non-TRAIN market {c}")
        win_of[c] = r["winner"]
    grid = {}
    with gzip.open(f"{a.run}/grid_prices.jsonl.gz", "rt") as f:
        for line in f:
            r = json.loads(line)
            grid[r["condition_id"]] = r["grid"]
    lo_b, hi_b = P["price_band"]

    def next_price(cid, side, t):
        for tt, py, pn in grid.get(cid, ()):
            if tt > t:
                return py if side == "YES" else pn
        return None

    def unit(cid, ev, side, t, p, uid):
        w = win_of.get(cid)
        if w is None:
            return None
        win = 1.0 if w == side else 0.0
        pn = next_price(cid, side, t)
        u = {"event_id": ev, "cid": cid, "side": side, "t": t, "p": p, "win": win, "excess": win - p,
             "net_1pct": win - p - 0.01, "uid": uid}
        u["excess_next"] = (win - pn) if pn is not None else None
        # within-market placebo: same market and side, >= 6 h away, price within tolerance, deterministic pick
        cand = [(hashlib.sha256(f"{uid}|{tt}".encode()).hexdigest(), py if side == "YES" else pn_)
                for tt, py, pn_ in grid.get(cid, ())
                if abs(tt - t) >= P["placebo"]["min_gap_s"]
                and (py if side == "YES" else pn_) is not None
                and lo_b <= (py if side == "YES" else pn_) <= hi_b
                and abs((py if side == "YES" else pn_) - p) <= P["placebo"]["price_tol"]]
        cand.sort()
        pl = [x[1] for x in cand[:P["placebo"]["per_alert"]]]
        u["placebo_excess"] = (win - sum(pl) / len(pl)) if pl else None
        u["minus_placebo"] = (u["excess"] - u["placebo_excess"]) if pl else None
        return u

    alerts = [json.loads(l) for l in open(f"{a.run}/alerts.jsonl")]
    groups = defaultdict(list)
    first_any, first_s2, first_s3 = {}, {}, {}
    for al in sorted(alerts, key=lambda x: x["t"]):
        k = (al["condition_id"], al["side"])
        args = (al["condition_id"], al["event_id"], al["side"], al["t"], al["price_side"], al["alert_id"])
        for f in al["primary_for"]:
            groups[f].append(args)
        if k not in first_any:
            first_any[k] = args
        if al["score"] >= 2 and k not in first_s2:
            first_s2[k] = args
        if al["score"] >= 3 and k not in first_s3:
            first_s3[k] = args
    groups["ANY_first"] = list(first_any.values())
    groups["SCORE>=2_first"] = list(first_s2.values())
    groups["SCORE>=3_first"] = list(first_s3.values())
    groups["PV_price_volume_only"] = [(x["condition_id"], x["event_id"], x["side"], x["t"], x["price_side"],
                                       "pv|" + x["condition_id"] + x["side"])
                                      for x in map(json.loads, open(f"{a.run}/pv_baseline.jsonl"))]
    # price alone: every market side at a deterministic random grid time in the band (calibration of the price)
    pa = []
    for cid, g in sorted(grid.items()):
        for side in ("YES", "NO"):
            pts = [(hashlib.sha256(f"price|{cid}|{side}|{tt}".encode()).hexdigest(), tt, py if side == "YES" else pn)
                   for tt, py, pn in g if (py if side == "YES" else pn) is not None
                   and lo_b <= (py if side == "YES" else pn) <= hi_b]
            if pts:
                _, tt, p = min(pts)
                pa.append((cid, event_of[cid], side, tt, p, f"price|{cid}|{side}"))
    groups["PRICE_alone_random_time"] = pa

    out = {"_status": "EXPLORATORY TRAIN ONLY. Not evidence of predictability. No correction for the "
                      f"{len(groups)} groups compared. VALID and TEST not read.",
           "labels_train_markets": len(win_of), "train_markets": len(train), "groups": {}}
    for name, items in sorted(groups.items()):
        us = [u for u in (unit(*x) for x in items) if u]
        res = {"units": len(us), "mean_price": (sum(u["p"] for u in us) / len(us)) if us else None,
               "win_rate": (sum(u["win"] for u in us) / len(us)) if us else None,
               "excess_vs_price_at_t": boot(us, "excess"),
               "excess_vs_next_grid_price": boot([u for u in us if u["excess_next"] is not None], "excess_next"),
               "net_after_1pct_slippage": boot(us, "net_1pct")}
        if not name.startswith(("PRICE", "PV")):
            res["minus_within_market_placebo"] = boot([u for u in us if u["minus_placebo"] is not None],
                                                      "minus_placebo")
        out["groups"][name] = res
    json.dump(out, open(a.out, "w"), indent=1, sort_keys=True)
    for name, r in sorted(out["groups"].items()):
        e = r["excess_vs_price_at_t"]
        print(f"{name:26s} n={r['units']:4d} ev={e.get('events', 0):4d} "
              f"excess={e.get('mean', float('nan')):+.3f} [{e.get('lo95', float('nan')):+.3f},"
              f"{e.get('hi95', float('nan')):+.3f}]")


if __name__ == "__main__":
    main()
