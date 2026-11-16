#!/usr/bin/env python3
"""Declared tests T1..T8, event-clustered bootstrap, Bonferroni + Benjamini-Hochberg, verdict.

No numpy/scipy: exact binomial is computed with math.comb; bootstrap with the stdlib random module
(seed fixed at 20261116 and written in the output).
"""
import argparse, json, math, random
from collections import defaultdict

SEED = 20261116
DRAWS = 10000
ALPHA = 0.05
N_COMPARISONS = 10  # 8 declared tests + 3 sweep cells = T1..T7 (7) + T8 (3) ; fixed in the plan


def binom_one_sided(k, n, p):
    """P(X >= k) for X ~ Bin(n, p)."""
    if n == 0:
        return 1.0
    if p <= 0:
        return 0.0 if k > 0 else 1.0
    if p >= 1:
        return 1.0 if k >= n else 0.0
    tail = 0.0
    for i in range(k, n + 1):
        tail += math.comb(n, i) * (p ** i) * ((1 - p) ** (n - i))
    return min(1.0, tail)


def rate(xs):
    return sum(xs) / len(xs) if xs else float("nan")


def cluster_bootstrap(rows, stat, draws=DRAWS, seed=SEED):
    """Resample whole events with replacement. `stat` must be a mean of one field."""
    by_event = defaultdict(list)
    for r in rows:
        by_event[r.get("event_id") or r.get("condition_id")].append(stat([r]))
    cells = [(sum(v), len(v)) for v in by_event.values()]
    rng = random.Random(seed)
    out = []
    n_cells = len(cells)
    for _ in range(draws):
        tot = 0.0
        cnt = 0
        for _ in range(n_cells):
            s_, n_ = cells[rng.randrange(n_cells)]
            tot += s_
            cnt += n_
        if cnt:
            out.append(tot / cnt)
    out.sort()
    if not out:
        return {"lo": None, "hi": None, "n_draws": 0}
    return {"lo": out[int(0.025 * len(out))], "hi": out[int(0.975 * len(out)) - 1], "n_draws": len(out)}


def two_group(rows_a, rows_b, metric="excess", seed=SEED):
    """Difference of means with event-clustered bootstrap; one-sided p = share of draws <= 0."""
    combined = [dict(r, _g="a") for r in rows_a] + [dict(r, _g="b") for r in rows_b]
    by_event = defaultdict(lambda: {"a": [0.0, 0], "b": [0.0, 0]})
    for r in combined:
        cell = by_event[r.get("event_id") or r.get("condition_id")][r["_g"]]
        cell[0] += r[metric]
        cell[1] += 1
    cells = list(by_event.values())
    rng = random.Random(seed)
    obs = rate([r[metric] for r in rows_a]) - rate([r[metric] for r in rows_b])
    le = 0
    draws = []
    n_cells = len(cells)
    for _ in range(DRAWS):
        sa = na = sb = nb = 0.0
        for _ in range(n_cells):
            c = cells[rng.randrange(n_cells)]
            sa += c["a"][0]; na += c["a"][1]
            sb += c["b"][0]; nb += c["b"][1]
        if not na or not nb:
            continue
        v = sa / na - sb / nb
        draws.append(v)
        if v <= 0:
            le += 1
    draws.sort()
    ci = {"lo": draws[int(0.025 * len(draws))], "hi": draws[int(0.975 * len(draws)) - 1], "n_draws": len(draws)} if draws else {"lo": None, "hi": None, "n_draws": 0}
    p = (le + 1) / (len(draws) + 1) if obs > 0 else 1.0
    return obs, ci, p


def bh(pvals):
    """Benjamini-Hochberg adjusted p-values."""
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals)
    adj = [0.0] * m
    prev = 1.0
    for rank, i in enumerate(reversed(idx), 1):
        val = min(prev, pvals[i] * m / (m - rank + 1))
        adj[i] = val
        prev = val
    return adj


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True)
    ap.add_argument("--placebo", required=True)
    ap.add_argument("--sweep", nargs="*", default=[])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rows = [json.loads(l) for l in open(a.scored)]
    rows = [r for r in rows if r.get("primary")]
    placebo = [json.loads(l) for l in open(a.placebo)]
    by = defaultdict(list)
    for r in rows:
        by[r["variant"]].append(r)
    s4, s4b, s2, s3 = by["S4"], by["S4b_include_two_sided"], by["S2_buy_consensus"], by["S3_individual"]

    tests = {}

    def add(name, desc, p, extra):
        tests[name] = dict(description=desc, p_value=p, **extra)

    # T1 S4 calibration
    n, k, mp = len(s4), sum(r["win"] for r in s4), rate([r["price"] for r in s4])
    p1 = binom_one_sided(k, n, mp)
    add("T1", "S4 alerts: win rate vs price at the alert", p1,
        {"n": n, "wins": k, "rate": rate([r["win"] for r in s4]), "mean_price": mp,
         "excess": rate([r["win"] for r in s4]) - mp,
         "excess_ci": cluster_bootstrap(s4, lambda s: rate([r["win"] for r in s]))})

    # T2 S4 vs matched placebo
    d2, ci2, p2 = two_group(s4, placebo)
    add("T2", "S4 minus matched S1 placebo (same price band, random time)", p2,
        {"n_s4": n, "n_placebo": len(placebo), "diff": d2, "diff_ci": ci2,
         "placebo_rate": rate([r["win"] for r in placebo]), "placebo_mean_price": rate([r["price"] for r in placebo]),
         "raw_rate_diff": rate([r["win"] for r in s4]) - rate([r["win"] for r in placebo])})

    # T3 S4 vs naive buy consensus
    d3, ci3, p3 = two_group(s4, s2)
    add("T3", "S4 minus S2 naive buy consensus", p3,
        {"n_s4": n, "n_s2": len(s2), "diff": d3, "diff_ci": ci3, "s2_rate": rate([r["win"] for r in s2]), "raw_rate_diff": rate([r["win"] for r in s4]) - rate([r["win"] for r in s2]),
         "s2_excess": rate([r["excess"] for r in s2])})

    # T4 S4 vs individual shift
    d4, ci4, p4 = two_group(s4, s3)
    add("T4", "S4 minus S3 individual shift", p4,
        {"n_s4": n, "n_s3": len(s3), "diff": d4, "diff_ci": ci4, "s3_rate": rate([r["win"] for r in s3]), "raw_rate_diff": rate([r["win"] for r in s4]) - rate([r["win"] for r in s3]),
         "s3_excess": rate([r["excess"] for r in s3])})

    # T5 net executable result at 1 % slippage
    pay = [r["payoff_0.01"] for r in s4]
    ci5 = cluster_bootstrap(s4, lambda s: rate([r["payoff_0.01"] for r in s]))
    mean_pay = rate(pay)
    # one-sided, event-clustered: share of resampled event means at or below zero
    by_event = defaultdict(list)
    for r in s4:
        by_event[r.get("event_id") or r["condition_id"]].append(r["payoff_0.01"])
    keys = list(by_event)
    rng = random.Random(SEED)
    le = 0
    for _ in range(DRAWS):
        draw = []
        for _ in range(len(keys)):
            draw.extend(by_event[keys[rng.randrange(len(keys))]])
        if rate(draw) <= 0:
            le += 1
    p5 = (le + 1) / (DRAWS + 1)
    add("T5", "S4 gross payoff per share at 1 % slippage > 0", p5,
        {"n": len(pay), "mean_payoff_1pct": mean_pay, "ci": ci5,
         "mean_payoff_0": rate([r["payoff_0.0"] for r in s4])})

    # T6 two-sided inclusion matters?
    d6, ci6, p6 = two_group(s4b, s4)
    add("T6", "S4b (two-sided included) minus S4", p6,
        {"n_s4b": len(s4b), "diff": d6, "diff_ci": ci6, "s4b_rate": rate([r["win"] for r in s4b]), "s4b_excess": rate([r["excess"] for r in s4b])})

    # T7 out-of-sample: TEST only
    s4t = [r for r in s4 if r.get("split") == "TEST"]
    n7 = len(s4t)
    k7 = sum(r["win"] for r in s4t)
    mp7 = rate([r["price"] for r in s4t])
    p7 = binom_one_sided(k7, n7, mp7)
    add("T7", "TEST split only: S4 win rate vs price", p7,
        {"n": n7, "wins": k7, "rate": rate([r["win"] for r in s4t]) if s4t else None, "mean_price": mp7,
         "excess": (rate([r["win"] for r in s4t]) - mp7) if s4t else None,
         "excess_ci": cluster_bootstrap(s4t, lambda s: rate([r["win"] for r in s])) if s4t else None})

    # T8 declared sweep cells
    sweep = []
    for i, path in enumerate(a.sweep, 1):
        sw = [json.loads(l) for l in open(path)]
        sw = [r for r in sw if r.get("variant") == "S4" and r.get("primary") and r.get("win") is not None]
        nn = len(sw)
        kk = sum(r["win"] for r in sw)
        mm = rate([r["price"] for r in sw]) if sw else float("nan")
        sweep.append({"cell": i, "n": nn, "wins": kk, "mean_price": mm,
                      "excess": (kk / nn - mm) if nn else None,
                      "p_value": binom_one_sided(kk, nn, mm) if nn else 1.0})
    p8 = min([s["p_value"] for s in sweep], default=1.0)
    add("T8", "declared threshold sweep (3 cells, min p reported)", p8, {"cells": sweep})

    # corrections
    order = ["T1", "T2", "T3", "T4", "T5", "T6", "T7"]
    pv = [tests[t]["p_value"] for t in order] + [s["p_value"] for s in sweep]
    adj = bh(pv)
    for i, t in enumerate(order):
        tests[t]["p_bh"] = adj[i]
        tests[t]["bonferroni_alpha"] = ALPHA / N_COMPARISONS
        tests[t]["significant_bonferroni"] = adj and tests[t]["p_value"] < ALPHA / N_COMPARISONS
        tests[t]["significant_bh"] = adj[i] < ALPHA
    for j, s in enumerate(sweep):
        s["p_bh"] = adj[len(order) + j]

    # per-split descriptive
    per_split = {}
    for name in ("TRAIN", "VALID", "TEST"):
        sub = [r for r in s4 if r.get("split") == name]
        per_split[name] = {"n": len(sub), "wins": sum(r["win"] for r in sub),
                           "mean_price": rate([r["price"] for r in sub]) if sub else None,
                           "rate": rate([r["win"] for r in sub]) if sub else None}

    n_test = per_split["TEST"]["n"]
    t7 = tests["T7"]
    pay_test = [r["payoff_0.01"] for r in s4t]
    if t7["significant_bonferroni"] and pay_test and rate(pay_test) > 0 and n_test >= 30:
        verdict = "EXPLOITABLE"
    elif n_test >= 30:
        verdict = "NOT_SUPPORTED"
    else:
        verdict = "INCONCLUSIVE"

    out = {"seed": SEED, "draws": DRAWS, "n_comparisons": N_COMPARISONS,
           "counts": {"S4": len(s4), "S4b": len(s4b), "S2": len(s2), "S3": len(s3),
                      "placebo": len(placebo), "scored_rows": len(rows)},
           "events": {"S4": len({r.get("event_id") for r in s4})},
           "per_split": per_split, "tests": tests, "verdict": verdict,
           "verdict_rule": "EXPLOITABLE needs T7 significant after Bonferroni, positive mean payoff at 1% slippage in TEST, and >=30 TEST alerts; NOT_SUPPORTED when >=30 TEST alerts and T7 fails; else INCONCLUSIVE."}
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps({"verdict": verdict, "counts": out["counts"], "per_split": per_split,
                      "p": {k: round(v["p_value"], 5) for k, v in tests.items()}}, indent=1))


if __name__ == "__main__":
    main()
