#!/usr/bin/env python3
"""Observed TRAIN firings vs the day-shift null (activity, sizes, sides and hour-of-day of every wallet kept;
alignment between wallets broken). Question answered: are collective alignments more frequent than the wallets'
own habits produce? No outcome is used.

Observed counts are restricted to the markets the null can shift (life >= 3 days), the same set as every seed.
Limit: F5 / F7 also use candidates of other markets; in the null the short markets contribute none.

usage: compare_nulls.py --observed out/observed --nulls out/null --tapes ... --out F.json
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_signals as R  # noqa: E402
import signals as S  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--observed", required=True)
    ap.add_argument("--nulls", required=True)
    ap.add_argument("--tapes", action="append", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cids = [json.loads(l)["condition_id"] for l in open(f"{a.observed}/market_stats.jsonl")]
    cons = [R.open_ro(t) for t in a.tapes]
    eligible = set()
    for c in cids:
        for con in cons:
            lo, hi = con.execute("select min(ts), max(ts) from trades where condition_id=?", (c,)).fetchone()
            if lo is not None:
                if ((hi - lo) // 86400 + 1) * 86400 >= 3 * 86400:
                    eligible.add(c.lower())
                break
    obs_m = json.load(open(f"{a.observed}/manifest.json"))
    alerts = [json.loads(l) for l in open(f"{a.observed}/alerts.jsonl")]
    alerts = [x for x in alerts if x["condition_id"].lower() in eligible]
    obs = {f: sum(1 for x in alerts if f in x["primary_for"]) for f in S.FAMILIES}
    obs_fire = {f: sum(1 for x in alerts if f in x["families_fired"]) for f in S.FAMILIES}
    seeds = []
    for p in sorted(glob.glob(f"{a.nulls}/seed_*/manifest.json")):
        m = json.load(open(p))
        if m["sha256"]["ledger.py"] != obs_m["sha256"]["ledger.py"] or m["sha256"]["params"] != obs_m["sha256"]["params"]:
            raise SystemExit(f"refused: {p} ran on another ledger or params than the observed run")
        seeds.append(m)
    K = len(seeds)
    out = {"_status": "TRAIN only, no outcome used. One-sided empirical p = (1 + #null >= observed) / (K + 1).",
           "seeds": K, "eligible_markets": len(eligible), "train_markets": len(cids), "families": {}}
    for f in S.FAMILIES:
        nu = [s["summary"]["primary_units_by_family"][f] for s in seeds]
        nf = [s["summary"]["firings_by_family"][f] for s in seeds]
        out["families"][f] = {
            "observed_units": obs[f], "null_units_mean": sum(nu) / K if K else None,
            "null_units_min_max": [min(nu), max(nu)] if K else None,
            "p_units": (1 + sum(1 for v in nu if v >= obs[f])) / (K + 1) if K else None,
            "observed_firings": obs_fire[f], "null_firings_mean": sum(nf) / K if K else None,
            "p_firings": (1 + sum(1 for v in nf if v >= obs_fire[f])) / (K + 1) if K else None}
    if "F6" in out["families"]:
        out["families"]["F6"]["note"] = "funding edges not collected: 0 by construction"
    json.dump(out, open(a.out, "w"), indent=1, sort_keys=True)
    for f, r in out["families"].items():
        print(f, r["observed_units"], round(r["null_units_mean"] or 0, 1), r["null_units_min_max"], r["p_units"],
              "| firings", r["observed_firings"], round(r["null_firings_mean"] or 0, 1), r["p_firings"])


if __name__ == "__main__":
    main()
