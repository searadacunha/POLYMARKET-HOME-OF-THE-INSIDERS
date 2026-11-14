"""Audit of the frozen study after its results: power, simultaneous intervals, corrections, dependence, timing, fees,
and the prices a follower could really get after an alert. EXPLORATORY: written after the results were read; it
computes no new p-value and changes no verdict.

    python3 -I scripts/audit_after_results.py offline [--check]   published tables only -> data/audit_after_results.json
    python3 -I scripts/audit_after_results.py local <study folder> raw fills of the study -> data/audit_accessible_prices.json

offline, per class of VALIDATION x INFO (one alert per event, data/study_export/alerts.jsonl):
  power      minimum excess detectable with 80 % power, one-sided, at the corrected threshold and at 0.05, from the
             null variance mean p(1 - p) of the alerted prices; events needed to detect +5 points and C2's estimate
  intervals  95 % intervals made simultaneous over the comparisons of the registry (Bonferroni, normal approximation)
  dependence cluster-robust standard error with alerts grouped by UTC day of the real close, and by day of the
             scheduled end; design effect = (clustered / independent standard error) squared
  timing     alert events and excess by hours between the alert and the real close
  fees       excess after the taker fee of the current schedule, fee = rate x p x (1 - p) per share
  registry   Holm and Benjamini-Hochberg over the p-values of the registry, m = every comparison on real data
local, from the study's fills of 1,000 USD or more (not published, addresses), per class of VALIDATION x INFO:
  the first purchase of the same side by another wallet at least L seconds after the alert (L = 6, the median lateness
  of the live engine, then 60, 300 and 3,600), within 24 hours; the share of alerts with none and how those ended;
  the excess at that price and after the fee of the market's category (docs.polymarket.com/trading/fees.md, read on
  14 November 2026: geopolitics 0, politics and tech 0.04, culture, economy and other 0.05, crypto 0.07)."""
import collections, hashlib, json, math, os, random, sqlite3, statistics, sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = lambda *p: os.path.join(HERE, "data", *p)
N = statistics.NormalDist()
FEE_RATE = {"geopolitics": 0.0, "politics": 0.04, "tech_business": 0.04, "culture": 0.05, "economy": 0.05, "other": 0.05, "crypto": 0.07}
LAGS = (6, 60, 300, 3600)
DAY = 86400
VALIDATION_WEEKS = 214 / 7      # scheduled ends from 1 April to 31 October 2026 (the plan's VALIDATION), 214 days


def rows(path):
    with open(path) as f:
        return [json.loads(l) for l in f if l.strip()]


def mean(x):
    return sum(x) / len(x) if x else None


def r6(x):
    return None if x is None else round(x, 6)


def cluster_se(d, keys):
    """Cluster-robust standard error of the mean of d, clusters given by keys."""
    m, s = mean(d), collections.defaultdict(float)
    for x, k in zip(d, keys):
        s[k] += x - m
    return math.sqrt(sum(v * v for v in s.values())) / len(d), len(s)


def holm_bh(ps, m):
    """Smallest Holm-adjusted p and smallest BH q over m comparisons; the p-values not given count as 1."""
    ps = sorted(ps)
    holm = max(min(1.0, (m - i) * p) for i, p in enumerate(ps[:1])) if ps else None
    bh = min(min(1.0, p * m / (i + 1)) for i, p in enumerate(ps)) if ps else None
    holm_rej = 0
    for i, p in enumerate(ps):
        if p * (m - i) <= 0.05:
            holm_rej += 1
        else:
            break
    bh_rej = max([i + 1 for i, p in enumerate(ps) if p <= 0.05 * (i + 1) / m] or [0])
    return {"m": m, "p_values_given": len(ps), "smallest_p": ps[0] if ps else None, "smallest_holm_adjusted": holm,
            "smallest_bh_q": bh, "rejected_at_0.05_holm": holm_rej, "rejected_at_0.05_bh": bh_rej}


def offline():
    al = rows(OUT("study_export", "alerts.jsonl"))
    reg = [r for r in rows(os.path.join(HERE, "study", "registre", "tests.jsonl")) if r.get("donnees") == "reelles"]
    m = sum(int(r.get("n_comparaisons") or 1) for r in reg)
    a_corr = 0.05 / m
    z_sim = N.inv_cdf(1 - a_corr / 2)
    z80 = N.inv_cdf(0.8)
    out = {"comparisons_on_real_data": m, "alpha_corrected": a_corr, "z_simultaneous": z_sim, "classes": {}}
    by = collections.defaultdict(list)
    for a in al:
        by[(a["population"], a["class"])].append(a)
    c2 = by.get(("validation_info", "C2_DORMANT_REACTIVATION"))
    c2_excess = mean([a["win"] - a["price"] for a in c2]) if c2 else None
    for (pop, cls), xs in sorted(by.items()):
        if pop != "validation_info":
            continue
        n = len(xs)
        d = [a["win"] - a["price"] for a in xs]
        v0 = mean([a["price"] * (1 - a["price"]) for a in xs])
        se = statistics.pstdev(d) / math.sqrt(n) if n > 1 else None
        ex = mean(d)
        se_close, k_close = cluster_se(d, [math.floor((a["t"] + a["hours_before_real_close"] * 3600) / DAY) for a in xs]) if n > 1 else (None, 0)
        se_end, k_end = cluster_se(d, [math.floor((a["t"] + a["hours_to_end"] * 3600) / DAY) for a in xs]) if n > 1 else (None, 0)
        need = lambda delta, alpha: math.ceil((N.inv_cdf(1 - alpha) + z80) ** 2 * v0 / delta ** 2)
        buckets = collections.OrderedDict((("after_real_close", lambda h: h < 0), ("0_to_1h", lambda h: 0 <= h < 1), ("1_to_6h", lambda h: 1 <= h < 6),
                                           ("6_to_24h", lambda h: 6 <= h < 24), ("1_to_7_days", lambda h: 24 <= h < 168), ("7_days_or_more", lambda h: h >= 168)))
        timing = {}
        for name, f in buckets.items():
            sub = [a["win"] - a["price"] for a in xs if f(a["hours_before_real_close"])]
            timing[name] = {"events": len(sub), "excess": r6(mean(sub))}
        rate = n / VALIDATION_WEEKS                   # alert events per week of scheduled ends, the rate at which a future holdout fills
        out["classes"][cls] = {
            "alert_events": n, "excess": r6(ex), "se_independent": r6(se),
            "prospective": {"alert_events_per_week_of_scheduled_ends": r6(rate),
                            "weeks_for_5_points_at_0.05": round(need(0.05, 0.05) / rate, 1) if rate else None,
                            "weeks_for_5_points_at_0.0125": round(need(0.05, 0.0125) / rate, 1) if rate else None,
                            "mde_80_at_0.05_after_52_weeks": r6((N.inv_cdf(0.95) + z80) * math.sqrt(v0 / (rate * 52))) if rate else None,
                            "mde_80_at_0.0125_after_52_weeks": r6((N.inv_cdf(1 - 0.0125) + z80) * math.sqrt(v0 / (rate * 52))) if rate else None,
                            "power_for_own_estimate_after_52_weeks_at_0.05": r6(1 - N.cdf(N.inv_cdf(0.95) - ex / math.sqrt(v0 / (rate * 52)))) if rate and ex > 0 else None,
                            "power_for_own_estimate_after_104_weeks_at_0.05": r6(1 - N.cdf(N.inv_cdf(0.95) - ex / math.sqrt(v0 / (rate * 104)))) if rate and ex > 0 else None},
            "power": {"null_variance": r6(v0),
                      "mde_80_corrected": r6((N.inv_cdf(1 - a_corr) + z80) * math.sqrt(v0 / n)),
                      "mde_80_at_0.05": r6((N.inv_cdf(0.95) + z80) * math.sqrt(v0 / n)),
                      "power_for_5_points_corrected": r6(1 - N.cdf(N.inv_cdf(1 - a_corr) - 0.05 / math.sqrt(v0 / n))),
                      "events_for_5_points_at_0.05": need(0.05, 0.05), "events_for_5_points_at_0.0125": need(0.05, 0.0125),
                      "events_for_c2_estimate_at_0.05": need(c2_excess, 0.05) if c2_excess and c2_excess > 0 else None},
            "simultaneous_interval": [r6(ex - z_sim * se), r6(ex + z_sim * se)] if se else [None, None],
            "dependence": {"se_by_real_close_day": r6(se_close), "days_real_close": k_close,
                           "design_effect_real_close_day": r6((se_close / se) ** 2) if se else None,
                           "se_by_scheduled_end_day": r6(se_end), "days_scheduled_end": k_end,
                           "design_effect_scheduled_end_day": r6((se_end / se) ** 2) if se else None,
                           "interval_95_by_real_close_day": [r6(ex - 1.959964 * se_close), r6(ex + 1.959964 * se_close)] if se_close else [None, None]},
            "timing": timing,
            "fees_upper_bound": {f"excess_after_rate_{r}": r6(ex - r * v0) for r in (0.04, 0.05, 0.07)}}
    ps = [r["p"] for r in reg if r.get("p") is not None and int(r.get("n_comparaisons") or 1) == 1]
    out["registry"] = holm_bh(ps, m)
    return out


def local(study):
    sys.path.insert(0, os.path.join(study, "code"))
    import stats, tests_lib as T                         # the frozen code, read only
    table = rows(os.path.join(study, "derived", "analytic_table.jsonl"))
    T.fit_m3(table)
    by_id = {r["id"]: r for r in table}
    part = [r for r in table if r["set"] == "VALIDATION" and r["grp"] == "INFO"]
    alerts = {cls: stats.first_per_event(T.split(part, cls)[0]) for cls in T.TESTED + T.BASELINES}
    con = sqlite3.connect("file:" + os.path.join(study, "data", "fills_all.sqlite") + "?mode=ro", uri=True)
    cid = dict(con.execute("select condition_id, id from conds"))
    wid = {}
    need = {cid[by_id[a["key"]]["condition_id"]] for xs in alerts.values() for a in xs if by_id[a["key"]]["condition_id"] in cid}
    for a in {by_id[a["key"]]["address"] for xs in alerts.values() for a in xs}:
        r = con.execute("select id from wallets where address=?", (a,)).fetchone()
        wid[a] = r[0] if r else None
    fills = collections.defaultdict(list)
    for ts, w, c, oi, side, size, price in con.execute("select ts, wallet, cond, outcome_index, side, size, price from fills"):
        if c in need:
            fills[c].append((ts, w, oi, side, price))
    for v in fills.values():
        v.sort()
    import bisect
    out = {"read": "fills_all.sqlite of the study, fills of 1,000 USD or more", "lags_s": LAGS, "fee_rates": FEE_RATE, "classes": {},
           "cross_check_plan_follow_price": {"compared": 0, "equal": 0}}
    rnd = random.Random(20261114)
    for cls, xs in alerts.items():
        res = {"alert_events": len(xs), "lags": {}}
        per = []
        for a in xs:
            r = by_id[a["key"]]
            c = cid.get(r["condition_id"]); fs = fills.get(c, [])
            ts_list = [f[0] for f in fs]
            item = {"win": a["win"], "p": a["price"], "rate": FEE_RATE.get(r["category"], 0.05), "q": {}}
            for L in LAGS:
                i = bisect.bisect_left(ts_list, a["t"] + L)
                q = None
                for ts, w, oi, side, price in fs[i:]:
                    if ts > a["t"] + DAY:
                        break
                    if w != wid.get(r["address"]) and oi == r["oi"] and side == 1:
                        q = (price, ts - a["t"]); break
                item["q"][L] = q
            if cls != "C7_HEAVY_NEWCOMER" and a.get("follow_price") is not None:     # the plan's follower: any fill of another wallet, 300 s after the entry
                i = bisect.bisect_left(ts_list, a["t"] + 300)
                for ts, w, oi, side, price in fs[i:]:
                    if ts > a["t"] + DAY:
                        break
                    if w != wid.get(r["address"]):
                        implied = price if oi == r["oi"] else 1 - price
                        out["cross_check_plan_follow_price"]["compared"] += 1
                        out["cross_check_plan_follow_price"]["equal"] += abs(implied - a["follow_price"]) < 1e-6
                        break
            per.append(item)
        res["excess_at_entry_price"] = r6(mean([x["win"] - x["p"] for x in per]))
        res["excess_at_entry_price_after_fee"] = r6(mean([x["win"] - x["p"] - x["rate"] * x["p"] * (1 - x["p"]) for x in per]))
        res["share_fee_free"] = r6(mean([x["rate"] == 0 for x in per]))
        for L in LAGS:
            got = [x for x in per if x["q"][L]]
            miss = [x for x in per if not x["q"][L]]
            d = [x["win"] - x["q"][L][0] - x["rate"] * x["q"][L][0] * (1 - x["q"][L][0]) for x in got]
            boot = sorted(mean([rnd.choice(d) for _ in d]) for _ in range(2000)) if len(d) >= 10 else None
            res["lags"][str(L)] = {"with_a_follower_purchase": len(got), "without": len(miss),
                                   "without_won_share": r6(mean([x["win"] for x in miss])), "without_excess_at_entry": r6(mean([x["win"] - x["p"] for x in miss])),
                                   "same_alerts_excess_at_entry_price": r6(mean([x["win"] - x["p"] for x in got])),
                                   "excess_at_follower_price": r6(mean([x["win"] - x["q"][L][0] for x in got])),
                                   "excess_at_follower_price_after_fee": r6(mean(d)),
                                   "interval_95_after_fee": [r6(boot[49]), r6(boot[1949])] if boot else [None, None],
                                   "mean_price_move": r6(mean([x["q"][L][0] - x["p"] for x in got])),
                                   "median_delay_s": statistics.median([x["q"][L][1] for x in got]) if got else None}
        out["classes"][cls] = res
    h = hashlib.sha256()
    with open(os.path.join(study, "data", "fills_all.sqlite"), "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    out["inputs_sha256"] = {"data/fills_all.sqlite": h.hexdigest(), "derived/analytic_table.jsonl": hashlib.sha256(open(os.path.join(study, "derived", "analytic_table.jsonl"), "rb").read()).hexdigest()}
    return out


def render():
    """The tables of STATISTICAL_AUDIT.md, from the two audit files and the frozen verdict."""
    a = json.load(open(OUT("audit_after_results.json")))
    b = json.load(open(OUT("audit_accessible_prices.json")))
    v = json.load(open(os.path.join(HERE, "study", "derived", "verdict.json")))["classes"]
    pt = lambda x: "" if x is None else f"{100 * x:+.1f}"
    iv = lambda xs: "" if None in xs else f"{pt(xs[0])} to {pt(xs[1])}"
    order = [c for c in v if c in a["classes"]] + [c for c in a["classes"] if c not in v]
    t = {}
    rows_ = ["| Class | Alert events | Excess, points | 95 % interval (published) | Simultaneous interval, 63 comparisons | Detectable at the corrected threshold | Detectable at 0.05 | Power for +5 points, corrected |",
             "|---|---:|---:|---|---|---:|---:|---:|"]
    for c in order:
        x = a["classes"][c]; p = x["power"]
        rows_.append(f"| {c} | {x['alert_events']} | {pt(x['excess'])} | {iv(v[c]['excess_ci']) if c in v else ''} | {iv(x['simultaneous_interval'])} | "
                     f"{100 * p['mde_80_corrected']:.1f} | {100 * p['mde_80_at_0.05']:.1f} | {p['power_for_5_points_corrected']:.2f} |")
    t["power"] = rows_
    rows_ = ["| Class | Design effect, day of real close | Design effect, day of scheduled end | 95 % interval, days of real close resampled | Alert events 0-24 h before the real close | after it |",
             "|---|---:|---:|---|---:|---:|"]
    for c in order:
        d = a["classes"][c]["dependence"]; tm = a["classes"][c]["timing"]
        near = tm["0_to_1h"]["events"] + tm["1_to_6h"]["events"] + tm["6_to_24h"]["events"]
        rows_.append(f"| {c} | {d['design_effect_real_close_day']:.2f} | {d['design_effect_scheduled_end_day']:.2f} | {iv(d['interval_95_by_real_close_day'])} | {near} | {tm['after_real_close']['events']} |")
    t["dependence"] = rows_
    rows_ = ["| Class | Excess at the alerted price | after the taker fee | Fee-free share | With a later purchase (6 s) | Without | Without: excess at the alerted price | With: excess at the alerted price | With: at the follower's price, after fee | 95 % interval | Price move, points |",
             "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|"]
    for c in order:
        x = b["classes"].get(c)
        if not x or not x["alert_events"]:
            continue
        l6 = x["lags"]["6"]
        rows_.append(f"| {c} | {pt(x['excess_at_entry_price'])} | {pt(x['excess_at_entry_price_after_fee'])} | {x['share_fee_free']:.2f} | {l6['with_a_follower_purchase']} | {l6['without']} | "
                     f"{pt(l6['without_excess_at_entry'])} | {pt(l6['same_alerts_excess_at_entry_price'])} | {pt(l6['excess_at_follower_price_after_fee'])} | {iv(l6['interval_95_after_fee'])} | {pt(l6['mean_price_move'])} |")
    t["prices"] = rows_
    rows_ = ["| Class | Lag | With a later purchase | At the follower's price, after fee | Median wait, hours |", "|---|---:|---:|---:|---:|"]
    for c in ("C1_FRESH_FUNDED_BET", "C2_DORMANT_REACTIVATION", "R1_S_FRESH_REPLICATION"):
        for L in ("6", "60", "300", "3600"):
            l = b["classes"][c]["lags"][L]
            rows_.append(f"| {c} | {L} s | {l['with_a_follower_purchase']} | {pt(l['excess_at_follower_price_after_fee'])} | {l['median_delay_s'] / 3600:.1f} |")
    t["lags"] = rows_
    rows_ = ["| Class | Alert events a week of scheduled ends | Weeks to detect +5 points at 0.05 | at 0.0125 | Detectable after 52 weeks at 0.05 | at 0.0125 |",
             "|---|---:|---:|---:|---:|---:|"]
    for c in order:
        p = a["classes"][c]["prospective"]
        rows_.append(f"| {c} | {p['alert_events_per_week_of_scheduled_ends']:.2f} | {p['weeks_for_5_points_at_0.05']:.0f} | {p['weeks_for_5_points_at_0.0125']:.0f} | "
                     f"{100 * p['mde_80_at_0.05_after_52_weeks']:.1f} | {100 * p['mde_80_at_0.0125_after_52_weeks']:.1f} |")
    t["prospective"] = rows_
    return {k: "\n".join(x) for k, x in t.items()}


def write_tables(page, check):
    import re
    text = open(page).read()
    new = text
    for k, body in render().items():
        new = re.sub(rf"(<!-- audit:{k} -->\n).*?(\n<!-- /audit:{k} -->)", lambda m: m.group(1) + body + m.group(2), new, flags=re.S)
    if check:
        if new != text:
            sys.exit(f"{page}: tables differ from the audit files")
        print("tables reproduced")
    else:
        open(page, "w").write(new); print("tables written")


def same(a, b, tol=2e-6):
    """Equal structures; numbers within tol (the file rounds to 6 decimals, and libm differs in the last digit across platforms)."""
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k], tol) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        return abs(a - b) <= tol * max(1.0, abs(a), abs(b))
    return a == b


def _selftest():
    assert same({"x": [1.0, 0.1234561]}, {"x": [1.0, 0.1234569]}) and not same({"x": 1}, {"x": 1.01}) and not same({"x": 1}, {"y": 1})
    se, k = cluster_se([1, -1, 1, -1], ["a", "a", "b", "b"])
    assert k == 2 and se == 0.0                     # opposite deviations inside each cluster cancel
    hb = holm_bh([0.001, 0.02, 0.5], 3)             # Holm: 0.003 and 0.04 pass, 0.5 stops; BH: 0.001 <= 0.0167, 0.02 <= 0.0333
    assert hb["rejected_at_0.05_holm"] == 2 and hb["rejected_at_0.05_bh"] == 2 and abs(hb["smallest_holm_adjusted"] - 0.003) < 1e-12


if __name__ == "__main__":
    _selftest()
    if sys.argv[1:2] == ["offline"]:
        res = offline()
        path = OUT("audit_after_results.json")
        if "--check" in sys.argv:
            saved = json.load(open(path))
            if not same(saved, json.loads(json.dumps(res))):
                sys.exit("audit_after_results.json differs from a fresh computation")
            print("audit_after_results.json reproduced")
        else:
            json.dump(res, open(path, "w"), indent=1); print("written", path)
    elif sys.argv[1:2] == ["render"]:
        write_tables(os.path.join(HERE, "STATISTICAL_AUDIT.md"), "--check" in sys.argv)
    elif sys.argv[1:2] == ["local"]:
        json.dump(local(sys.argv[2]), open(OUT("audit_accessible_prices.json"), "w"), indent=1); print("written")
    else:
        sys.exit(__doc__)
