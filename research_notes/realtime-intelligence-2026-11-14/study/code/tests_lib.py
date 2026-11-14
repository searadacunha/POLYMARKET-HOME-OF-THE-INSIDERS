"""Shared by the real analysis (ana_50) and the positive controls (ctrl_10): how a class becomes alerts, and the tests.

A row is one eligible entry of the analytic table (a dict). A class is read from its columns:
  time column, price column -> the alert moment and the price paid then (C7);
  flag column               -> the alert is the entry itself (every other class).
An alert is admissible when its price is 0.90 or less and its moment is before the end of the day that follows the
scheduled end date of the market (the scheduled end is a date; the event happens during or after that day).
"""
import math, random
import models, stats

PRICE_MAX = 0.90
END_GRACE_S = 86400
T_SPLIT = 1775001599            # 2026-03-31 23:59:59 UTC, as in feat_10
# Entries that cannot be controls of a class because their status depends on what followed: an entry of C1 that did not
# turn heavy is not a control of C7 (pre-freeze audit: the 24 hours after the entry would sort the controls)
NOT_A_CONTROL = {"C7_HEAVY_NEWCOMER": "c1"}


def grace(end_ts):
    """An end at 00:00 UTC is a date and its day is included; any other end is a deadline (feat_20)."""
    return END_GRACE_S if end_ts % 86400 == 0 else 0
CLASSES = {                      # name -> (kind, columns)
    "C1_FRESH_FUNDED_BET": ("flag", "c1"),
    "C2_DORMANT_REACTIVATION": ("flag", "c2"),
    "C3_OUT_OF_CHARACTER": ("flag", "c3"),
    "C4_COFUNDED_GROUP": ("flag", "c4"),
    "C5_RECURRENT_FUNDER": ("flag", "c5"),
    "C6_QUIET_FRESH_LOW": ("flag", "c6"),
    "C7_HEAVY_NEWCOMER": ("moment", ("c7_t", "c7_p")),
    "R1_S_FRESH_REPLICATION": ("flag", "r1"),
    "M1_RARITY_TOP1": ("flag", "m1"),
    "M2_IFOREST_TOP1": ("flag", "m2"),
    "M3_EDGE_TOP5": ("flag", "m3"),
    "B1_BIG": ("flag", "b1"),
    "B2_AFTER_MOVE": ("flag", "b2"),
    "B3_THIN_NOT_FRESH": ("flag", "b3"),
}
TESTED = [c for c in CLASSES if c[0] in "CRM"]
BASELINES = [c for c in CLASSES if c[0] == "B"]


def alert_of(row, cls):
    """The alert of `cls` on this entry, or None; second value counts why an alert was refused."""
    kind, col = CLASSES[cls]
    if kind == "moment":
        t, p = row.get(col[0]), row.get(col[1])
        if t is None:
            return None, None
    else:
        if not row.get(col):
            return None, None
        t, p = row["t"], row["price"]
    if p is None or p > PRICE_MAX:
        return None, "price_above_0.90"
    if t >= row["end_ts"] + grace(row["end_ts"]):
        return None, "after_scheduled_end_day"
    return {"event": row["event_id"], "t": t, "price": p, "win": row["win"], "hours_to_end": (row["end_ts"] - t) / 3600.0, "key": row["id"],
            "wallet": row["address"], "cash": row["cash"], "closed_ts": row.get("closed_ts"), "follow_price": row.get("follow_price"),
            "follow_dt": row.get("follow_dt"), "entry_t": row["t"], "category": row.get("category")}, None


def split(rows, cls):
    """(alerts of the class, control entries, refusal counts). A control is an eligible entry that is not an alert of the
    class and whose class membership is known: outside the screen, or inside it with its wallet history read."""
    alerts, controls, refused = [], [], {}
    for r in rows:
        if cls in r.get("unknown", ()):
            refused["membership_unknown"] = refused.get("membership_unknown", 0) + 1; continue
        a, why = alert_of(r, cls)
        if a is not None:
            alerts.append(a)
        elif why is not None:
            refused[why] = refused.get(why, 0) + 1
        elif (not r["tier1"] or r["evaluated"]) and not (cls in NOT_A_CONTROL and r.get(NOT_A_CONTROL[cls])):
            controls.append({"event": r["event_id"], "price": r["price"], "hours_to_end": (r["end_ts"] - r["t"]) / 3600.0, "win": r["win"]})
    return alerts, controls, refused


def t2_adaptive(alerts, controls, seed=20261114, steps=(2000, 20000, 100000, 500000)):
    """Bootstrap of events, more draws only while the share of hits stays small (plan: 2 %, 0.2 %, then 0.05 %)."""
    res = None
    for n, limit in zip(steps, (0.02, 0.002, 0.0005, -1.0)):
        res = stats.t2(alerts, controls, draws=n, seed=seed)
        if res["p"] is None or res["hits"] / max(1, res["draws"]) >= limit:
            break
    return res


def class_tests(rows, cls, with_t2=True, seed=20261114, steps=(2000, 20000, 100000, 500000)):
    alerts, controls, refused = split(rows, cls)
    one = stats.first_per_event(alerts)
    r1 = stats.t1(alerts)
    out = {"class": cls, "entries_alerted": len(alerts), "alert_events": r1["n"], "wallets": len({a["wallet"] for a in one}), "refused": refused,
           "t1": r1, "excess_ci": stats.boot_excess(alerts, seed=seed) if r1["n"] else (None, None), "controls": len(controls)}
    if with_t2 and r1["n"]:
        out["t2"] = t2_adaptive(alerts, controls, seed=seed, steps=steps)
    return out


def verdict(res, alpha, nc_p=None):
    """Wording fixed by the plan."""
    n, t1, t2 = res["alert_events"], res["t1"], res.get("t2") or {}
    if n < 30:
        return "INCONCLUSIVE"
    ok = (t1["p"] is not None and t1["p"] < alpha and t2.get("p") is not None and t2["p"] < alpha and t1["excess"] >= 0.05)
    if ok:
        return "NOT_SPECIFIC" if (nc_p is not None and nc_p < alpha) else "SUPPORTED"
    hi = res["excess_ci"][1]
    return "NOT_SUPPORTED_EFFECT_EXCLUDED" if hi is not None and hi < 0.05 else "NOT_SUPPORTED_UNDERPOWERED"


def fit_m3(rows):
    """Edge model fitted on DISCOVERY x INFO entries whose wallet history was read; flag m3 = top 5 % of discovery scores.
    Writes the score and the flag into every evaluated row; returns the model summary."""
    # outcomes learnt only from discovery entries made by the split date, outside the documented cases; validation rows made
    # before that date are contemporary with the learnt outcomes, so M3 is unknown there (pre-freeze leakage audit)
    train = [r for r in rows if r["set"] == "DISCOVERY" and r["grp"] == "INFO" and r["evaluated"] and r["t"] <= T_SPLIT and not r.get("documented")]
    for r in rows:
        if r["set"] == "VALIDATION" and r["t"] <= T_SPLIT and "M3_EDGE_TOP5" not in r.setdefault("unknown", []):
            r["unknown"].append("M3_EDGE_TOP5")
    if len(train) < 500:
        for r in rows:
            r["m3_score"], r["m3"] = None, 0
        return {"trained_on": len(train), "note": "too few rows"}
    model = models.edge_fit([r["x"] for r in train], [r["win"] for r in train])
    for r in rows:
        r["m3_score"] = models.edge_score(model, r["x"]) if r["evaluated"] else None
    cut = models.quantile([r["m3_score"] for r in train], 0.95)
    for r in rows:
        r["m3"] = int(r["m3_score"] is not None and r["m3_score"] >= cut)
    return {"trained_on": len(train), "threshold": cut, "beta": dict(zip(("intercept",) + models.FEATURES, [round(b, 5) for b in model["beta"]]))}


def robustness(rows, cls, seed=20261114):
    """Descriptive variants fixed by the plan: estimates and intervals only, no p-value."""
    alerts, _, _ = split(rows, cls)
    one = stats.first_per_event(alerts)
    if not one:
        return {}
    ex = lambda a: a["win"] - a["price"]
    mean = lambda xs: sum(xs) / len(xs) if xs else None
    out = {"n": len(one), "excess": mean([ex(a) for a in one])}
    # calendar weeks resampled instead of events
    weeks = {}
    for a in one:
        weeks.setdefault(a["t"] // (7 * 86400), []).append(ex(a))
    rng = random.Random(seed); keys = list(weeks); m = []
    for _ in range(2000):
        xs = [x for k in rng.choices(keys, k=len(keys)) for x in weeks[k]]
        m.append(sum(xs) / len(xs))
    m.sort(); out["week_block_ci"] = (m[50], m[1949]); out["weeks"] = len(keys)
    tot = sum(ex(a) for a in one)
    loo = [(tot - ex(a)) / (len(one) - 1) for a in one] if len(one) > 1 else []
    out["leave_one_event_out"] = (min(loo), max(loo)) if loo else None
    strict = stats.first_per_event([a for a in alerts if a["hours_to_end"] > 0])     # the first rule, applied before the earliest alert is chosen
    out["before_scheduled_end_date"] = {"n": len(strict), "excess": mean([ex(a) for a in strict])}
    for name, hours in (("lead_6h", 6), ("lead_24h", 24)):
        sub = [a for a in one if a["closed_ts"] is not None and a["closed_ts"] - a["t"] >= hours * 3600]
        out[name] = {"n": len(sub), "excess": mean([ex(a) for a in sub])}
    fol = [a for a in one if a["follow_price"] is not None and a["follow_price"] <= PRICE_MAX]
    out["follower"] = {"n": len(fol), "excess_at_follow_price": mean([a["win"] - a["follow_price"] for a in fol]),
                       "median_wait_s": sorted(a["follow_dt"] for a in fol)[len(fol) // 2] if fol else None}
    for name, floor in (("cash_2000", 2000), ("cash_5000", 5000)):
        sub = stats.first_per_event([a for a in alerts if a["cash"] >= floor])
        out[name] = {"n": len(sub), "excess": mean([ex(a) for a in sub])}
    cats = {}
    for a in one:
        cats.setdefault(a.get("category") or "other", []).append(ex(a))
    out["by_category"] = {k: {"n": len(v), "excess": mean(v)} for k, v in sorted(cats.items())}
    ts = sorted(a["t"] for a in one); mid = ts[len(ts) // 2]
    out["halves"] = {"first": {"n": sum(1 for a in one if a["t"] < mid), "excess": mean([ex(a) for a in one if a["t"] < mid])},
                     "second": {"n": sum(1 for a in one if a["t"] >= mid), "excess": mean([ex(a) for a in one if a["t"] >= mid])}}
    out["alert_events_per_week"] = round(len(one) / max(1.0, (ts[-1] - ts[0]) / (7 * 86400.0)), 2)
    # how much of the cheap winning entries the class holds, against how much of all cheap entries (entries, not events)
    flagged = {a["key"] for a in alerts}
    cheap = [r for r in rows if r["price"] <= 0.30 and cls not in r.get("unknown", ())]; won = [r for r in cheap if r["win"]]
    out["cheap_entries"] = {"entries_at_0.30_or_less": len(cheap), "share_flagged": (sum(1 for r in cheap if r["id"] in flagged) / len(cheap)) if cheap else None,
                            "of_which_won": len(won), "share_of_winners_flagged": (sum(1 for r in won if r["id"] in flagged) / len(won)) if won else None}
    lead = sorted((a["closed_ts"] - a["t"]) / 3600.0 for a in one if a["closed_ts"] is not None)
    out["lead_to_close_h"] = {"median": lead[len(lead) // 2], "p10": lead[int(0.1 * (len(lead) - 1))], "p90": lead[int(0.9 * (len(lead) - 1))]} if lead else None
    return out


def sweep_c1(rows, cls="C1_FRESH_FUNDED_BET"):
    """The declared sweep of 11 cells for C1: five price bands, four horizons, two halves of the period."""
    alerts, _, _ = split(rows, cls)
    one = stats.first_per_event(alerts)
    cells = {}
    def add(name, sub):
        r = stats.t1(sub)
        cells[name] = {"n": r["n"], "wins": r["wins"], "excess": r["excess"], "p": r["p"]}
    for b in range(5):
        add(f"price_band_{b}", [a for a in one if stats.stratum(a["price"], a["hours_to_end"])[0] == b])
    for h in range(4):
        add(f"horizon_{h}", [a for a in one if stats.stratum(a["price"], a["hours_to_end"])[1] == h])
    ts = sorted(a["t"] for a in one)
    mid = ts[len(ts) // 2] if ts else 0
    add("first_half", [a for a in one if a["t"] < mid]); add("second_half", [a for a in one if a["t"] >= mid])
    return cells


def placebo(rows, cls="C1_FRESH_FUNDED_BET", n=200, seed=20261114):
    """Random classes of the size of the real one inside each stratum, drawn among the control entries: share of them
    whose exact test gives p < 0.05. One diagnostic number about the population, not 200 hypotheses."""
    alerts, _, _ = split(rows, cls)
    one = stats.first_per_event(alerts)
    need = {}
    for a in one:
        s = stats.stratum(a["price"], a["hours_to_end"]); need[s] = need.get(s, 0) + 1
    pool = {}
    for r in rows:
        if alert_of(r, cls)[0] is None and r["price"] <= PRICE_MAX and (not r["tier1"] or r["evaluated"]) and cls not in r.get("unknown", ()):
            pool.setdefault(stats.stratum(r["price"], (r["end_ts"] - r["t"]) / 3600.0), []).append(r)
    rng = random.Random(seed); low = 0; ps = []
    for _ in range(n):
        fake = []
        for s, k in need.items():
            fake += [{"event": r["event_id"], "t": r["t"], "price": r["price"], "win": r["win"], "key": r["id"]}
                     for r in rng.sample(pool.get(s, []), min(k, len(pool.get(s, []))))]
        p = stats.t1(fake)["p"]
        if p is not None:
            ps.append(p); low += p < 0.05
    return {"placebos": len(ps), "share_p_below_0.05": low / len(ps) if ps else None, "median_p": sorted(ps)[len(ps) // 2] if ps else None}
