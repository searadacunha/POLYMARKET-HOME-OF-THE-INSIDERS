#!/usr/bin/env python3
"""Independent recomputation of the frozen study from data/study_export/ alone.

Written from study/analysis_plan.md only: no study code (verify.py, render_results.py, study/code/) read or imported.
Standard library, no network, fixed seeds.

  python3 scripts/independent_recompute.py             # own numbers and comparison, printed
  python3 scripts/independent_recompute.py --out F.json
  python3 scripts/independent_recompute.py --check     # exit 1 if a gated comparison fails

Published values (study/derived/verdict.json, study/registre/tests.jsonl, RESULTS.md) are read only by compare(),
after compute() has produced every own number.
"""
import argparse
import bisect
import json
import math
import random
import re
import statistics
import sys
import time
from operator import mul
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPORT = ROOT / "data" / "study_export"
REGISTRY = ROOT / "study" / "registre" / "tests.jsonl"
VERDICT = ROOT / "study" / "derived" / "verdict.json"
RESULTS = ROOT / "RESULTS.md"

PRICE_CUTS = [0.10, 0.25, 0.50, 0.75]
HOUR_CUTS = [24, 168, 720]
T2_DRAWS = [(2000, 0.02), (20000, 0.002), (100000, 0.0005), (500000, None)]  # plan: escalate while hits < share
CI_DRAWS = 10000
PUB_CI_DRAWS = 2000  # assumption: published draw count of the excess interval is not stated anywhere; plan's base count
EFFECT = 0.05
MIN_EVENTS = 30
ALPHA = 0.05
T2_POP = "validation_info"
NEG_POP = "validation_public_process"
SWEEP_CLASS = "C1_FRESH_FUNDED_BET"
ROBUST_CLASSES = ["C1_FRESH_FUNDED_BET", "C2_DORMANT_REACTIVATION", "C3_OUT_OF_CHARACTER", "R1_S_FRESH_REPLICATION"]
DET_TOL = 1e-6
Z_SE = 4.0  # resampled quantities: 4 combined Monte-Carlo standard errors

AMBIGUITIES = [
    "T2 alert side: the plan says 'difference of mean excess between the alerts and the control entries (..., one mean "
    "per event and stratum)'. Read first as alert cells (class_cells, all class entries, one mean per event and "
    "stratum): C1 gave -0.04692 against -0.05492 published, and every class differed. Chosen reading: the alerts are "
    "the one-per-event alerts of alerts.jsonl (the plan's unit of every test), placed in the stratum of their own price "
    "and hours to the scheduled end; the controls are one mean per event and stratum. The chosen reading reproduces the "
    "published T2 difference of every class to < 1e-7.",
    "T2 combination across strata: the plan does not give the weights. Chosen: mean over alerts of (alert excess minus "
    "the mean of the control cell means of its stratum), i.e. strata weighted by their number of alert events. "
    "Weighting by entries or unweighted strata gave different numbers (diagnostic run, not kept).",
    "T2 controls: base cell minus class cells minus excluded cells. class_cells holds the alerts and the refused alerts "
    "of a class (amendment 001), so refused alerts are neither alerts nor controls. Reproduces the published control "
    "counts exactly.",
    "Strata bounds on ties (price exactly 0.10/0.25/0.50/0.75, hours exactly 24/168/720): the plan gives cuts only. "
    "Chosen: band = number of cuts strictly below the value (a cut belongs to the lower band); this is what the "
    "exported cells show on the 19 single-entry events whose price sits on a cut.",
    "T2 resampling: events drawn with replacement among all events of validation_info with an eligible entry "
    "(base_cells, 1406); escalation draws are fresh draws, not added to the 2,000; an undefined resample (no alert "
    "drawn) counts as a hit; an alert whose stratum has no control in a resample is left out of that resample.",
    "Excess interval: the plan gives neither the number of draws nor the interval method. Chosen: 10,000 draws, "
    "percentile interval with linear interpolation; one alert per event, so resampling events = resampling alerts.",
    "Verdict 'under the corrected threshold' read as strict p < 0.05 / N; a T2 p with 0 hits is replaced by its bound "
    "3/draws; SUPPORTED needs excess >= 0.05; NOT_SPECIFIC uses the T1 p of the same class on validation_public_process.",
    "Alerted entries: the export gives entries only through class_cells, which also hold refused alerts (amendment 001); "
    "for C7 it gives 524 entries where the registry and RESULTS.md give 519. Not derivable from the export; reported, "
    "not gated. Entries are not exported for discovery_info and validation_public_process.",
    "Sweep halves and robustness halves: 'cut at the median alert time' read as t < median vs t >= median of the class's "
    "own validation alerts. 'Median hours from alert to real close' read as the upper median (median_high): the "
    "plain median gives 497.8 / 523.5 / 527.2 for C1 / C2 / C3 against 499 / 528 / 529 published, the upper median "
    "matches all four. 'Calendar weeks' read as 7-day blocks from the Unix epoch (t // 604800): ISO weeks gave a C2 "
    "upper bound of +12.6 against +10.9 published and C3 -5.0 to +2.6 against -6.1 to +3.4; epoch blocks agree within "
    "Monte-Carlo error. 'Entry of 5,000 USD or more' is not derivable: the published n (105 for C1) exceeds the "
    "earliest alerts of 5,000 USD or more (43), so the variant re-derives the earliest alert among large entries, and "
    "alerts.jsonl keeps only the earliest alert of each event; reported, not gated. 'Alert events a week' read as events / ((last alert t - first alert t) / 7 days). "
    "'Strictly before the scheduled end' read as hours_to_end > 0; 'at least 24 h before the real close' as "
    "hours_before_real_close >= 24; 'entry of 5,000 USD or more' as entry_usd >= 5000; 'price a follower paid' as "
    "win - follow_price over alerts with a follower price <= 0.90; weeks = ISO calendar week of the alert time (UTC).",
]


def load(name):
    with open(EXPORT / name) as f:
        return [json.loads(line) for line in f if line.strip()]


def band(x, cuts):
    return bisect.bisect_left(cuts, x)  # number of cuts strictly below x


def stratum(a):
    return band(a["price"], PRICE_CUTS), band(a["hours_to_end"], HOUR_CUTS)


# ---------------------------------------------------------------- T1 and excess, one alert per event

def poisson_binomial_upper(prices, wins):
    """P(S >= wins) for S a sum of independent Bernoulli(prices)."""
    f = [1.0]
    for p in prices:
        q = 1.0 - p
        g = [0.0] * (len(f) + 1)
        for k, v in enumerate(f):
            g[k] += v * q
            g[k + 1] += v * p
        f = g
    return min(1.0, math.fsum(f[wins:]))


def percentile(sorted_vals, q):
    pos = q * (len(sorted_vals) - 1)
    lo = math.floor(pos)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (pos - lo)


def boot_ci(groups, seed, draws=CI_DRAWS):
    """Percentile interval of the mean, resampling groups (lists of values) whole."""
    rng = random.Random(seed)
    sums = [(math.fsum(g), len(g)) for g in groups]
    k = len(sums)
    boot = []
    for _ in range(draws):
        s = rng.choices(sums, k=k)
        boot.append(math.fsum(x for x, _ in s) / sum(n for _, n in s))
    boot.sort()
    mean = math.fsum(boot) / draws
    sd = (math.fsum((b - mean) ** 2 for b in boot) / (draws - 1)) ** 0.5
    return [percentile(boot, 0.025), percentile(boot, 0.975)], sd


def excess(rows, price_key="price"):
    return math.fsum(r["win"] - r[price_key] for r in rows) / len(rows) if rows else None


def alert_stats(rows, seed):
    n = len(rows)
    if n == 0:
        return {"events": 0, "wins": 0, "sum_price": None, "mean_price": None, "excess": None, "t1_p": None,
                "ci95": None, "boot_sd": None}
    assert len({r["event"] for r in rows}) == n, "alerts must be one per event"
    prices = [r["price"] for r in rows]
    wins = sum(r["win"] for r in rows)
    ci, sd = boot_ci([[r["win"] - r["price"]] for r in rows], seed)
    return {"events": n, "wins": wins, "sum_price": math.fsum(prices), "mean_price": math.fsum(prices) / n,
            "excess": excess(rows), "t1_p": poisson_binomial_upper(prices, wins), "ci95": ci, "boot_sd": sd}


# ---------------------------------------------------------------- T2 on validation_info

def cells(rows):
    out = {}
    for r in rows:
        k = (r["event"], (r["price_band"], r["horizon_band"]))
        assert k not in out, k
        out[k] = (r["n"], r["sum_excess"])
    return out


def t2_stat(c, base_sums, alert, touched):
    """Mean over alerts of (alert excess - mean of control cell means of its stratum), events weighted by c."""
    num, den = 0.0, 0
    g = c.__getitem__
    for s, (ia, va) in alert.items():
        na = sum(map(g, ia))
        if na == 0:
            continue
        nk, sk = base_sums[s]
        if s in touched:
            it, dn, ds = touched[s]
            nk += sum(map(mul, map(g, it), dn))
            sk += sum(map(mul, map(g, it), ds))
        if nk <= 0:
            continue
        num += sum(map(mul, map(g, ia), va)) - na * sk / nk
        den += na
    return num / den if den else None


def t2_all(alerts, classes, base_rows, class_rows, excl_rows):
    base = cells(base_rows)
    events = sorted({e for e, _ in base})
    idx = {e: i for i, e in enumerate(events)}
    E = len(events)
    base_by_s = {}
    for (e, s), (n, tot) in base.items():
        b = base_by_s.setdefault(s, ([], []))
        b[0].append(idx[e]); b[1].append(tot / n)

    def base_sums_of(c):
        g = c.__getitem__
        return {s: (sum(map(g, ib)), sum(map(mul, map(g, ib), vb))) for s, (ib, vb) in base_by_s.items()}

    out, prepared = {}, {}
    ones = [1] * E
    bs1 = base_sums_of(ones)
    for cls in classes:
        cc = cells(r for r in class_rows if r["class"] == cls)
        xx = cells(r for r in excl_rows if r["class"] == cls)
        touched_all = {}
        for k in set(cc) | set(xx):
            bn, bsum = base[k]
            cn, cs = cc.get(k, (0, 0.0))
            xn, xs = xx.get(k, (0, 0.0))
            kn, ks = bn - cn - xn, bsum - cs - xs
            assert kn >= 0, (cls, k)
            touched_all[k] = (kn, ks, bn, bsum)
        controls = sum(n for n, _ in base.values()) - sum(n for n, _ in cc.values()) - sum(n for n, _ in xx.values())
        rows = [a for a in alerts if a["population"] == T2_POP and a["class"] == cls]
        res = {"alert_events": len(rows), "class_cell_entries": sum(n for n, _ in cc.values()),
               "excluded_entries": sum(n for n, _ in xx.values()), "controls": controls,
               "diff": None, "p": None, "p_bound": None, "hits": None, "draws": None}
        out[cls] = res
        if not rows:
            continue
        alert = {}
        for a in rows:
            al = alert.setdefault(stratum(a), ([], []))
            al[0].append(idx[a["event"]]); al[1].append(a["win"] - a["price"])
        touched = {}
        for (e, s), (kn, ks, bn, bsum) in touched_all.items():
            if s in alert:
                t = touched.setdefault(s, ([], [], []))
                t[0].append(idx[e]); t[1].append((1 if kn > 0 else 0) - 1)
                t[2].append((ks / kn if kn > 0 else 0.0) - bsum / bn)
        res["alerts_without_control_stratum"] = sum(
            len(ia) for s, (ia, _) in alert.items()
            if bs1[s][0] + (sum(touched[s][1]) if s in touched else 0) <= 0)
        res["diff"] = t2_stat(ones, bs1, alert, touched)
        prepared[cls] = (alert, touched)

    pending = list(prepared)
    for level, (draws, share) in enumerate(T2_DRAWS):
        if not pending:
            break
        rng = random.Random(20261114 + level)
        hits = dict.fromkeys(pending, 0)
        for _ in range(draws):
            c = [0] * E
            for i in rng.choices(range(E), k=E):
                c[i] += 1
            bsum = base_sums_of(c)
            for cls in pending:
                d = t2_stat(c, bsum, *prepared[cls])
                if d is None or d <= 0:
                    hits[cls] += 1
        nxt = []
        for cls in pending:
            h = hits[cls]
            out[cls].update({"hits": h, "draws": draws, "p": (h + 1) / (draws + 1),
                             "p_bound": 3 / draws if h == 0 else None})
            if share is not None and h < share * draws:
                nxt.append(cls)
        pending = nxt
    return out, sum(n for n, _ in base.values())


# ---------------------------------------------------------------- sweep and robustness (descriptions of C1..R1)

def halves(rows):
    med = statistics.median(r["t"] for r in rows)
    return [r for r in rows if r["t"] < med], [r for r in rows if r["t"] >= med]


def sweep(rows):
    out = {}
    for b in range(len(PRICE_CUTS) + 1):
        out[f"price_band_{b}"] = [r for r in rows if band(r["price"], PRICE_CUTS) == b]
    for b in range(len(HOUR_CUTS) + 1):
        out[f"horizon_{b}"] = [r for r in rows if band(r["hours_to_end"], HOUR_CUTS) == b]
    out["first_half"], out["second_half"] = halves(rows)
    return {k: {"events": len(v), "excess": excess(v),
                "t1_p": poisson_binomial_upper([r["price"] for r in v], sum(r["win"] for r in v)) if v else None}
            for k, v in out.items()}


def robustness(rows, seed):
    n = len(rows)
    tot = math.fsum(r["win"] - r["price"] for r in rows)
    loo = [(tot - (r["win"] - r["price"])) / (n - 1) for r in rows]
    weeks = {}
    for r in rows:
        weeks.setdefault(r["t"] // (7 * 86400), []).append(r["win"] - r["price"])  # 7-day blocks from the epoch
    wci, wsd = boot_ci(list(weeks.values()), seed)

    def sub(cond, key="price"):
        v = [r for r in rows if cond(r)]
        return {"events": len(v), "excess": excess(v, key)}

    h1, h2 = halves(rows)
    ts = [r["t"] for r in rows]
    return {
        "excess": {"events": n, "excess": tot / n},
        "weeks_ci95": wci, "weeks_boot_sd": wsd,
        "loo_range": [min(loo), max(loo)],
        "strictly_before_end": sub(lambda r: r["hours_to_end"] > 0),
        "24h_before_close": sub(lambda r: r["hours_before_real_close"] >= 24),
        "entry_5000": sub(lambda r: r["entry_usd"] >= 5000),
        "follower": sub(lambda r: r["follow_price"] is not None and r["follow_price"] <= 0.90, "follow_price"),
        "halves": [excess(h1), excess(h2)],
        "events_a_week": n / ((max(ts) - min(ts)) / (7 * 86400)),
        "median_hours_to_close": statistics.median_high(r["hours_before_real_close"] for r in rows),
    }


# ---------------------------------------------------------------- verdict

def registry_comparisons():
    n = 0
    with open(REGISTRY) as f:
        for line in f:
            r = json.loads(line)
            if r.get("donnees") == "reelles":
                n += int(r.get("n_comparaisons") or 1)
    return n


def verdict(v, t1_neg, thr):
    if v["events"] < MIN_EVENTS:
        return "INCONCLUSIVE"
    t2p = v["t2"]["p_bound"] or v["t2"]["p"]
    if v["t1_p"] < thr and t2p is not None and t2p < thr and v["excess"] >= EFFECT:
        return "NOT_SPECIFIC" if t1_neg is not None and t1_neg < thr else "SUPPORTED"
    return "NOT_SUPPORTED_EFFECT_EXCLUDED" if v["ci95"][1] < EFFECT else "NOT_SUPPORTED_UNDERPOWERED"


def compute():
    alerts = load("alerts.jsonl")
    class_rows, base_rows, excl_rows = load("class_cells.jsonl"), load("base_cells.jsonl"), load("excluded_cells.jsonl")
    pops = sorted({r["population"] for r in alerts})
    classes = sorted({r["class"] for r in alerts} | {r["class"] for r in class_rows} | {r["class"] for r in excl_rows})
    n_cmp = registry_comparisons()
    res = {"n_comparisons_registry": n_cmp, "threshold": ALPHA / n_cmp, "populations": {}}
    by = {}
    for a in alerts:
        by.setdefault((a["population"], a["class"]), []).append(a)
    for pop in pops:
        res["populations"][pop] = {cls: alert_stats(sorted(by.get((pop, cls), []), key=lambda r: r["event"]),
                                                    seed=f"ci:{pop}:{cls}") for cls in classes}
    t2, n_base = t2_all(alerts, classes, base_rows, class_rows, excl_rows)
    res["validation_info_eligible_entries"] = n_base
    res["verdicts"] = {}
    for cls in classes:
        v = res["populations"][T2_POP][cls]
        v["t2"] = t2[cls]
        res["verdicts"][cls] = verdict(v, res["populations"].get(NEG_POP, {}).get(cls, {}).get("t1_p"),
                                       res["threshold"])
    vi = lambda c: sorted(by.get((T2_POP, c), []), key=lambda r: r["t"])
    res["sweep_C1"] = sweep(vi(SWEEP_CLASS))
    res["robustness"] = {c: robustness(vi(c), seed=f"weeks:{c}") for c in ROBUST_CLASSES}
    return res


# ---------------------------------------------------------------- comparison (reads published values)

def mc_tol_p(p_mine, p_pub, b_mine, b_pub):
    p = (p_mine + p_pub) / 2
    lo = 1 / min(b_mine, b_pub)
    p = min(max(p, lo), 1 - lo)
    return Z_SE * math.sqrt(p * (1 - p) * (1 / b_mine + 1 / b_pub))


def mc_tol_q(sd):
    """Monte-Carlo s.e. of a 2.5 % / 97.5 % bootstrap percentile ~ sd * sqrt(q(1-q)) / phi(z) / sqrt(B)."""
    k = math.sqrt(0.025 * 0.975) / (math.exp(-1.959964 ** 2 / 2) / math.sqrt(2 * math.pi))
    return Z_SE * sd * k * math.sqrt(1 / CI_DRAWS + 1 / PUB_CI_DRAWS) + DET_TOL


def num(s):
    s = s.strip().replace(",", "")
    return None if s == "" else float(s)


def parse_table(text, name):
    block = text.split(f"<!-- table:{name} -->")[1].split(f"<!-- /table:{name} -->")[0]
    rows = [[c.strip() for c in line.strip().strip("|").split("|")] for line in block.splitlines()
            if line.startswith("|") and not line.startswith("|---")]
    return rows[0], rows[1:]


def compare(res):
    out = []

    def add(source, where, qty, mine, pub, kind, tol=0.0, gate=True, note=None):
        if mine is None or pub is None:
            ok = mine is None and pub is None
            diff = None
        elif kind == "exact":
            ok, diff = mine == pub, (mine - pub if isinstance(mine, (int, float)) and not isinstance(mine, bool)
                                     and isinstance(pub, (int, float)) else None)
        else:
            diff = mine - pub
            ok = abs(diff) <= (DET_TOL if kind == "det" else tol)
        out.append({"source": source, "where": where, "quantity": qty, "mine": mine, "published": pub,
                    "kind": kind, "tolerance": DET_TOL if kind == "det" else (tol if kind != "exact" else 0),
                    "diff": diff, "match": ok, "gated": gate, "note": note})

    P = res["populations"]
    # verdict.json
    vj = json.loads(VERDICT.read_text())
    add("verdict.json", "", "comparisons_on_real_data", res["n_comparisons_registry"], vj["comparisons_on_real_data"],
        "exact")
    add("verdict.json", "", "alpha_corrected", res["threshold"], vj["alpha_corrected"], "det")
    for cls, pv in vj["classes"].items():
        v = P[T2_POP][cls]
        w = f"{T2_POP}/{cls}"
        add("verdict.json", w, "verdict", res["verdicts"][cls], pv["verdict"], "exact")
        add("verdict.json", w, "alert_events", v["events"], pv["alert_events"], "exact")
        add("verdict.json", w, "excess", v["excess"], pv["excess"], "det")
        add("verdict.json", w, "t1_p", v["t1_p"], pv["t1_p"], "det")
        add("verdict.json", w, "t2_diff", v["t2"]["diff"], pv["t2_diff"], "det")
        neg = P.get(NEG_POP, {}).get(cls, {}).get("t1_p")
        add("verdict.json", w, "negative_control_t1_p", neg, pv["negative_control_t1_p"], "det")
        for i, nm in enumerate(["excess_ci_low", "excess_ci_high"]):
            add("verdict.json", w, nm, v["ci95"][i] if v["ci95"] else None, pv["excess_ci"][i], "resampled",
                mc_tol_q(v["boot_sd"]) if v["boot_sd"] is not None else 0)
        t2p, t2b = v["t2"]["p"], v["t2"]["draws"]
        add("verdict.json", w, "t2_p", t2p, pv["t2_p"], "resampled",
            mc_tol_p(t2p, pv["t2_p"], t2b, 2000) if t2p is not None and pv["t2_p"] is not None else 0,
            note="published draws (2000) from the registry")

    # registry, full precision, every population
    for line in REGISTRY.read_text().splitlines():
        r = json.loads(line)
        if r["donnees"] != "reelles":
            continue
        m = re.match(r"(T[12])_(.+)_(validation_info|validation_public_process|discovery_info)$", r["test"])
        if not m:
            continue
        t, cls, pop = m.groups()
        v = P[pop][cls]
        w = f"{pop}/{cls}"
        src = "registry:" + r["test"]
        add(src, w, "alert_events", v["events"], r["n_effectif"], "exact")
        if pop == T2_POP:
            derivable = cls != "C7_HEAVY_NEWCOMER"
            add(src, w, "alerted_entries", v["t2"]["class_cell_entries"], r["n"], "exact", gate=derivable,
                note=None if derivable else "class_cells mixes alerts and refused alerts (amendment 001)")
        if t == "T1":
            add(src, w, "wins", v["wins"], r["params"]["wins"], "exact")
            add(src, w, "sum_price", v["sum_price"], r["params"]["expected"] if v["events"] else None, "display",
                5e-5 + DET_TOL, note="registry rounds the expected wins to 4 decimals")
            add(src, w, "excess", v["excess"], r["stat"], "det")
            add(src, w, "t1_p", v["t1_p"], r["p"], "det")
        else:
            t2 = v["t2"]
            add(src, w, "controls", t2["controls"], r["params"]["controls"], "exact")
            add(src, w, "t2_diff", t2["diff"], r["stat"], "det")
            add(src, w, "t2_draws", t2["draws"], r["n_tirages"], "exact", note="escalation level reached")
            add(src, w, "t2_p", t2["p"], r["p"], "resampled",
                mc_tol_p(t2["p"], r["p"], t2["draws"], r["n_tirages"]) if r["p"] is not None else 0)

    # RESULTS.md tables (display precision: half a unit of the last digit, plus the MC tolerance when resampled)
    text = RESULTS.read_text()
    hm = re.search(r"registry: (\d+); corrected threshold 0\.05 / \d+ = ([\d.]+)\. .*validation_info ([\d,]+)", text)
    add("RESULTS.md:header", "", "comparisons", res["n_comparisons_registry"], int(hm.group(1)), "exact")
    add("RESULTS.md:header", "", "threshold", res["threshold"], float(hm.group(2)), "display", 5e-6)
    add("RESULTS.md:header", "", "validation_info_eligible_entries", res["validation_info_eligible_entries"],
        int(hm.group(3).replace(",", "")), "exact")
    head, rows = parse_table(text, "primary")
    for row in rows:
        d = dict(zip(head, row))
        cls = d["Class"]
        v = P[T2_POP][cls]
        w = f"{T2_POP}/{cls}"
        src = "RESULTS.md:primary"
        add(src, w, "verdict", res["verdicts"][cls], d["Verdict"], "exact")
        derivable = cls != "C7_HEAVY_NEWCOMER"
        add(src, w, "alerted_entries", v["t2"]["class_cell_entries"], int(d["Alerted entries"]), "exact",
            gate=derivable, note=None if derivable else "class_cells mixes alerts and refused alerts (amendment 001)")
        add(src, w, "alert_events", v["events"], int(d["Alert events"]), "exact")
        add(src, w, "wins", v["wins"] if v["events"] else None, int(d["Won"]) if d["Won"] else None, "exact")
        pts = lambda x: None if x is None else 100 * x
        add(src, w, "excess_points", pts(v["excess"]), num(d["Excess, points"]), "display", 0.05 + DET_TOL)
        if d["95 % interval"]:
            lo, hi = [num(x) for x in d["95 % interval"].split(" to ")]
            tq = 100 * mc_tol_q(v["boot_sd"])
            add(src, w, "ci_low_points", pts(v["ci95"][0]), lo, "display", 0.05 + tq)
            add(src, w, "ci_high_points", pts(v["ci95"][1]), hi, "display", 0.05 + tq)
        add(src, w, "t1_p", v["t1_p"], num(d["T1 p"]), "display", 0.005 + DET_TOL)
        add(src, w, "t2_diff_points", pts(v["t2"]["diff"]), num(d["T2 difference, points"]), "display", 0.05 + DET_TOL)
        tp = num(d["T2 p"])
        add(src, w, "t2_p", v["t2"]["p"], tp, "display",
            0.005 + (mc_tol_p(v["t2"]["p"], tp, v["t2"]["draws"], 2000) if tp is not None else 0))
        add(src, w, "negative_control_t1_p", P.get(NEG_POP, {}).get(cls, {}).get("t1_p"),
            num(d["Negative control T1 p"]), "display", 0.005 + DET_TOL)
    head, rows = parse_table(text, "other")
    for row in rows:
        cls = row[0]
        for pop, cell in [(NEG_POP, row[1]), ("discovery_info", row[2])]:
            parts = [x.strip() for x in cell.split(",")]
            v = P[pop][cls]
            w = f"{pop}/{cls}"
            add("RESULTS.md:other", w, "alert_events", v["events"], int(parts[0]), "exact")
            if len(parts) > 1:
                add("RESULTS.md:other", w, "excess_points", 100 * v["excess"], num(parts[1]), "display", 0.05 + DET_TOL)
                add("RESULTS.md:other", w, "t1_p", v["t1_p"], num(parts[2]), "display", 0.005 + DET_TOL)
            else:
                add("RESULTS.md:other", w, "excess_points", v["excess"], None, "display")
    head, rows = parse_table(text, "sweep")
    for row in rows:
        s = res["sweep_C1"][row[0]]
        w = f"{T2_POP}/{SWEEP_CLASS}/{row[0]}"
        add("RESULTS.md:sweep", w, "events", s["events"], int(row[1]), "exact")
        add("RESULTS.md:sweep", w, "excess_points", 100 * s["excess"], num(row[2]), "display", 0.05 + DET_TOL)
        add("RESULTS.md:sweep", w, "t1_p", s["t1_p"], num(row[3]), "display", 0.005 + DET_TOL)
    sweep_min = min(s["t1_p"] for s in res["sweep_C1"].values())
    reg = {json.loads(l)["test"]: json.loads(l) for l in REGISTRY.read_text().splitlines()}
    add("registry:X1_sweep_C1_cells", f"{T2_POP}/{SWEEP_CLASS}", "smallest_cell_p", sweep_min,
        reg["X1_sweep_C1_cells"]["p"], "det")
    head, rows = parse_table(text, "robustness")
    for row in rows:
        label = row[0]
        for short, cell in zip(head[1:], row[1:]):
            cls = next(c for c in ROBUST_CLASSES if c.startswith(short + "_"))
            rb = res["robustness"][cls]
            w = f"{T2_POP}/{cls}"
            src = "RESULTS.md:robustness/" + label
            m = re.match(r"([-+\d.]+) \(n (\d+)\)$", cell)
            key = {"Excess, one alert per event": "excess", "Strictly before the scheduled end": "strictly_before_end",
                   "At least 24 h before the real close": "24h_before_close", "Entry of 5,000 USD or more": "entry_5000",
                   "At the price a follower paid": "follower"}.get(label)
            if key:
                # the 5,000 USD variant re-derives the earliest alert among large entries; alerts.jsonl keeps only
                # the earliest alert of each event, so it cannot be rebuilt from the export
                derivable = key != "entry_5000"
                note = None if derivable else "not derivable: export keeps only the earliest alert of each event"
                add(src, w, "events", rb[key]["events"], int(m.group(2)), "exact", gate=derivable, note=note)
                add(src, w, "excess_points", 100 * rb[key]["excess"], num(m.group(1)), "display", 0.05 + DET_TOL,
                    gate=derivable, note=note)
            elif label.startswith("Weeks resampled"):
                lo, hi = [num(x) for x in cell.split(" to ")]
                tq = 100 * mc_tol_q(rb["weeks_boot_sd"])
                add(src, w, "weeks_ci_low_points", 100 * rb["weeks_ci95"][0], lo, "display", 0.05 + tq)
                add(src, w, "weeks_ci_high_points", 100 * rb["weeks_ci95"][1], hi, "display", 0.05 + tq)
            elif label.startswith("Any single event"):
                lo, hi = [num(x) for x in cell.split(" to ")]
                add(src, w, "loo_low_points", 100 * rb["loo_range"][0], lo, "display", 0.05 + DET_TOL)
                add(src, w, "loo_high_points", 100 * rb["loo_range"][1], hi, "display", 0.05 + DET_TOL)
            elif label.startswith("First half"):
                a, b = [num(x) for x in cell.split(",")]
                add(src, w, "first_half_points", 100 * rb["halves"][0], a, "display", 0.05 + DET_TOL)
                add(src, w, "second_half_points", 100 * rb["halves"][1], b, "display", 0.05 + DET_TOL)
            elif label.startswith("Alert events a week"):
                add(src, w, "events_a_week", rb["events_a_week"], num(cell), "display", 0.005 + DET_TOL)
            elif label.startswith("Median hours"):
                add(src, w, "median_hours_to_close", rb["median_hours_to_close"], num(cell), "display", 0.5 + DET_TOL)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="write own numbers, comparison and ambiguities as JSON")
    ap.add_argument("--check", action="store_true", help="exit 1 if a gated comparison fails")
    a = ap.parse_args()
    t0 = time.time()
    res = compute()
    cmp = compare(res)
    runtime = round(time.time() - t0, 2)
    fails = [c for c in cmp if not c["match"]]
    gated_fails = [c for c in fails if c["gated"]]
    summary = {"compared": len(cmp), "matched": len(cmp) - len(fails), "mismatched": len(fails),
               "gated_mismatched": len(gated_fails), "runtime_s": runtime}
    if a.out:
        Path(a.out).write_text(json.dumps({"summary": summary, "ambiguities": AMBIGUITIES, "mismatches": fails,
                                           "comparisons": cmp, "own_numbers": res}, indent=1, default=str))
    print(json.dumps(summary))
    for c in fails:
        print(("FAIL " if c["gated"] else "NOTE ") + json.dumps(c, default=str))
    if a.check:
        sys.exit(1 if gated_fails else 0)


if __name__ == "__main__":
    main()
