#!/usr/bin/env python3
"""EXPLORATORY, post hoc sensitivity of the frozen phase 8 S_FRESH signal to pUSD collateral.

Reads the frozen phase 8 tables in place (never writes there) and data/pusd_first_transfer.jsonl, then prints one
JSON document on stdout:
  - the frozen wallet age and S_FRESH flags, recomputed and compared with the published ones;
  - the same rule with first_any = min(first USDC.e/USDC transfer, first pUSD transfer) (one alternative definition);
  - flips by split, the pUSD timeline, the stratified estimate of p8_analysis.py, a market-clustered bootstrap
    (seed and draws below) and Kish effective sample sizes.
Standard library only. Deterministic. Nothing here changes the frozen phase 8 verdict.
"""
import collections
import csv
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
P8 = ROOT / "investigations/maduro-iran/sources/phase8"
EVENTS, WALLETS, BACKTEST = P8 / "event_study.csv", P8 / "wallet_features.csv", P8 / "backtest_results.csv"
PUSD = HERE / "data/pusd_first_transfer.jsonl"
SPLITS = ("TRAIN", "VALID", "TEST")
SEED, DRAWS = 20261120, 4000
MINT = "0x" + "0" * 40


def num(x):
    return None if x in ("", None) else float(x)


def boolean(x):
    if x not in ("True", "False", ""):
        raise ValueError(f"bad boolean {x!r}")
    return x == "True"


def load_events():
    rows = []
    with open(EVENTS, newline="") as fh:
        for r in csv.DictReader(fh):
            rows.append({"eid": r["eid"], "split": r["split"], "cid": r["cid"], "wallet": r["wallet"],
                         "ts": int(r["ts"]), "price": num(r["price"]), "prior": num(r["prior_trades_univ"]),
                         "momo": num(r["momo_60"]), "y": num(r["ret_res"]), "base": boolean(r["in_baseline"]),
                         "fund": boolean(r["in_fund_sample"]), "age_pub": num(r["wallet_age_h"]),
                         "fresh_pub": boolean(r["S_FRESH"])})
    return rows


def load_first_usdc():
    with open(WALLETS, newline="") as fh:
        return {r["wallet"]: (None if r["first_any"] == "" else int(float(r["first_any"]))) for r in csv.DictReader(fh)}


def load_pusd(path=PUSD):
    out = {}
    with open(path) as fh:
        for line in fh:
            d = json.loads(line)
            if "error" in d or d["wallet"] in out:
                raise ValueError("lookup error or duplicate wallet in the pUSD file")
            out[d["wallet"]] = d
    return out


def age(T, first):
    return (T - first) / 3600 if first is not None and first < T else None


def flag_events(rows, first_usdc, pusd):
    """Adds age0/F0 (frozen rule) and age1/F1 (pUSD counted) to every row. Thresholds unchanged: 48 h, <= 2 trades."""
    for r in rows:
        r["age0"] = r["age1"] = None
        r["pusd_before"] = False
        if r["fund"] and r["wallet"] in first_usdc:
            f0, pt = first_usdc[r["wallet"]], pusd[r["wallet"]]["pusd_first_ts"]
            f1 = min([x for x in (f0, pt) if x is not None], default=None)
            r["age0"], r["age1"], r["pusd_before"] = age(r["ts"], f0), age(r["ts"], f1), pt is not None and pt < r["ts"]
        r["F0"] = r["age0"] is not None and r["age0"] <= 48 and r["prior"] <= 2
        r["F1"] = r["age1"] is not None and r["age1"] <= 48 and r["prior"] <= 2
    return rows


def quantile(sorted_vals, q):
    """Linear interpolation, the numpy default."""
    h = (len(sorted_vals) - 1) * q
    lo = math.floor(h)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (h - lo) * (sorted_vals[hi] - sorted_vals[lo])


def add_strata(rows):
    """Price bucket x TRAIN momentum tercile, as p8_analysis.py lines 46 to 50."""
    tr = sorted(r["momo"] for r in rows if r["split"] == "TRAIN" and r["base"] and r["momo"] is not None)
    q1, q2 = quantile(tr, 1 / 3), quantile(tr, 2 / 3)
    for r in rows:
        p = r["price"]
        pb = None if p is None else ("0-0.2" if p <= 0.2 else "0.2-0.5" if p <= 0.5 else "0.5-0.8" if p <= 0.8
                                     else "0.8-1" if p <= 1.0001 else None)
        m = r["momo"]
        mt = "NA" if m is None else ("bas" if m <= q1 else "moyen" if m <= q2 else "haut")
        r["stratum"] = None if pb is None else pb + "|" + mt
    return q1, q2


def cluster_table(d, flag, key):
    """Per cluster: {stratum: [signal sum, signal count, baseline sum, baseline count]} over the signal strata."""
    strata = sorted({r["stratum"] for r in d if r[flag] and r["stratum"] is not None})
    idx = {s: i for i, s in enumerate(strata)}
    tab = collections.OrderedDict()
    for r in d:
        if r["stratum"] not in idx:
            continue
        cell = tab.setdefault(r[key], {}).setdefault(idx[r["stratum"]], [0.0, 0, 0.0, 0])
        if r[flag]:
            cell[0] += r["y"]; cell[1] += 1
        else:
            cell[2] += r["y"]; cell[3] += 1
    return len(strata), [list(v.items()) for v in tab.values()]


def estimate(n_strata, clusters, mult=None):
    """Stratified signal minus baseline, weighted by signal count; baseline strata need >= 10 (weighted) events."""
    acc = [[0.0, 0, 0.0, 0] for _ in range(n_strata)]
    for c, cells in enumerate(clusters):
        w = 1 if mult is None else mult[c]
        if not w:
            continue
        for s, (ss, sc, bs, bc) in cells:
            a = acc[s]; a[0] += w * ss; a[1] += w * sc; a[2] += w * bs; a[3] += w * bc
    tot = ws = 0.0
    for ss, sc, bs, bc in acc:
        if sc <= 0 or bc < 10:
            continue
        tot += sc * (ss / sc - bs / bc); ws += sc
    return (tot / ws if ws else None), ws


def kish(values):
    c = collections.Counter(values)
    return len(values) ** 2 / sum(v * v for v in c.values())


def infer(rows, split, flag, rng):
    d = [r for r in rows if r["split"] == split and r["fund"] and r["y"] is not None]
    sig = [r for r in d if r[flag]]
    n_strata, by_market = cluster_table(d, flag, "cid")
    est, used = estimate(n_strata, by_market)
    m = len(by_market)
    draws = []
    for _ in range(DRAWS):  # markets resampled once, signal and baseline jointly (the auditor's scheme)
        mult = [0] * m
        for i in rng.choices(range(m), k=m):
            mult[i] += 1
        v = estimate(n_strata, by_market, mult)[0]
        if v is not None:
            draws.append(v)
    draws.sort()
    mean = sum(draws) / len(draws)
    se = math.sqrt(sum((v - mean) ** 2 for v in draws) / len(draws))
    return {"effect_pts": round(est * 100, 2), "n_sig": len(sig), "n_sig_in_used_strata": int(used),
            "n_baseline": len(d) - len(sig), "sig_markets": len({r["cid"] for r in sig}),
            "sig_wallets": len({r["wallet"] for r in sig}),
            "kish_neff_market": round(kish([r["cid"] for r in sig]), 1),
            "kish_neff_wallet": round(kish([r["wallet"] for r in sig]), 1),
            "ci95_market": [round(quantile(draws, 0.025) * 100, 2), round(quantile(draws, 0.975) * 100, 2)],
            "se_market_pts": round(se * 100, 2), "mde80_pts": round(2.8 * se * 100, 1),
            "draws_kept": len(draws)}


def utc(t):
    return datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def published_rows():
    out = {}
    with open(BACKTEST, newline="") as fh:
        for r in csv.DictReader(fh):
            if r["signal"] == "S_FRESH" and r["horizon"] == "res" and r["cost_pp"] == "1.0":
                out[r["split"]] = {"effect_pts": round(float(r["diff_strat"]) * 100, 2), "n_sig": int(r["n_sig"]),
                                   "ci95": [round(float(r["ci_lo"]) * 100, 2), round(float(r["ci_hi"]) * 100, 2)]}
    return out


def compute(pusd=None, bootstrap=True):
    rows, first_usdc = load_events(), load_first_usdc()
    pusd = load_pusd() if pusd is None else pusd
    if set(pusd) != set(first_usdc):
        raise ValueError("the pUSD file must cover exactly the wallets of wallet_features.csv")
    flag_events(rows, first_usdc, pusd)
    fund = [r for r in rows if r["fund"]]
    out = {"frozen_reproduction": {
        "flag_mismatch": sum(r["F0"] != r["fresh_pub"] for r in rows),
        "age_mismatch": sum((r["age0"] is None) != (r["age_pub"] is None) or
                            (r["age0"] is not None and abs(r["age0"] - r["age_pub"]) > 1e-6) for r in fund),
        "events": len(rows), "fund_sample_events": len(fund)}}
    counts = {}
    for sp in SPLITS:
        g = [r for r in fund if r["split"] == sp]
        cand = [r for r in g if r["prior"] <= 2]
        counts[sp] = {"fund_sample_events": len(g), "candidates_prior_le2": len(cand),
                      "age_unknown_frozen_candidates": sum(r["age0"] is None for r in cand),
                      "age_unknown_pusd_candidates": sum(r["age1"] is None for r in cand),
                      "fresh_published": sum(r["fresh_pub"] for r in g), "fresh_frozen": sum(r["F0"] for r in g),
                      "fresh_pusd": sum(r["F1"] for r in g),
                      "fresh_frozen_with_outcome": sum(r["F0"] and r["y"] is not None for r in g),
                      "fresh_pusd_with_outcome": sum(r["F1"] and r["y"] is not None for r in g),
                      "flips_not_fresh_to_fresh": sum(r["F1"] and not r["F0"] for r in g),
                      "flips_fresh_to_not_fresh": sum(r["F0"] and not r["F1"] for r in g),
                      "events_pusd_before_T": sum(r["pusd_before"] for r in g),
                      "wallets_pusd_before_T": len({r["wallet"] for r in g if r["pusd_before"]})}
    out["counts"] = counts
    fl = [r for r in rows if r["F0"] != r["F1"]]
    out["flips"] = {"n": len(fl), "wallets": len({r["wallet"] for r in fl}), "markets": len({r["cid"] for r in fl}),
                    "age_unknown_under_frozen_rule": sum(r["age0"] is None for r in fl),
                    "first_pusd_is_mint": sum(pusd[r["wallet"]].get("from") == MINT for r in fl),
                    "usdc_never": sum(first_usdc[r["wallet"]] is None for r in fl),
                    "usdc_first_after_T": sum(first_usdc[r["wallet"]] is not None and first_usdc[r["wallet"]] >= r["ts"]
                                              for r in fl),
                    "trades_utc": [utc(min(r["ts"] for r in fl)), utc(max(r["ts"] for r in fl))] if fl else None}
    ft = [r for r in fl if r["split"] == "TEST" and r["y"] is not None]
    out["flipped_test_with_outcome"] = {"n": len(ft), "markets": len({r["cid"] for r in ft}),
                                        "wallets": len({r["wallet"] for r in ft}),
                                        "mean_gross_ret_res_pts": round(100 * sum(r["y"] for r in ft) / len(ft), 2)
                                        if ft else None}
    pts = sorted(d["pusd_first_ts"] for d in pusd.values() if d["pusd_first_ts"] is not None)
    months = collections.OrderedDict()
    for r in sorted((r for r in fund if r["prior"] <= 2), key=lambda r: r["ts"]):
        mo = utc(r["ts"])[:7]
        if mo >= "2026-04":
            m = months.setdefault(mo, {"candidates": 0, "age_unknown_frozen": 0, "fresh_frozen": 0, "fresh_pusd": 0})
            m["candidates"] += 1; m["age_unknown_frozen"] += r["age0"] is None
            m["fresh_frozen"] += r["F0"]; m["fresh_pusd"] += r["F1"]
    out["pusd_timeline"] = {"wallets": len(pusd), "wallets_with_a_pusd_transfer": len(pts),
                            "earliest_first_pusd_utc": utc(pts[0]) if pts else None, "candidates_by_trade_month": months}
    q1, q2 = add_strata(rows)
    out["momentum_tercile_bounds"] = [q1, q2]
    if bootstrap:
        rng = random.Random(SEED)
        out["estimates"] = {sp: {"frozen": infer(rows, sp, "F0", rng), "pusd": infer(rows, sp, "F1", rng)}
                            for sp in ("TRAIN", "VALID", "TEST")}
        out["bootstrap"] = {"seed": SEED, "draws": DRAWS, "generator": "Python random.Random (Mersenne Twister)",
                            "order": "TRAIN, VALID, TEST; frozen then pUSD", "scheme": "markets resampled with "
                            "replacement once per draw; signal and baseline events of a drawn market enter together",
                            "python": sys.version.split()[0]}
    out["published"] = published_rows()
    return out


if __name__ == "__main__":
    json.dump(compute(), sys.stdout, indent=1)
    print()
