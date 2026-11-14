"""Statistics of the study. Pure functions, standard library only.

excess of a group = mean(win) - mean(p_alert): how much more often the ignited side won than the tape price at the time
of the alert implied. T1 tests it against 0 for a class (exact Poisson-binomial tail, one-sided). T2 compares the class
with the other ignitions by a permutation of the class label inside p_alert strata (one-sided, Monte Carlo)."""
import random
from collections import defaultdict

STRATA = (0.3, 0.6)


def stratum(p):
    return 0 if p <= STRATA[0] else (1 if p <= STRATA[1] else 2)


def summary(rows):
    n = len(rows)
    if n == 0:
        return {"n": 0, "wins": 0, "win_rate": None, "mean_p": None, "excess": None, "n_events": 0, "n_initiators": 0}
    w = sum(r["win"] for r in rows); mp = sum(r["p_alert"] for r in rows) / n
    return {"n": n, "wins": w, "win_rate": w / n, "mean_p": mp, "excess": w / n - mp,
            "n_events": len({r["event_slug"] for r in rows}), "n_initiators": len({r["initiator"] for r in rows})}


def t1_exact(rows):
    """P(W* >= W) when each row wins independently with probability p_alert. Exact by convolution.
    Rows of one event are negatively dependent at most (one winner per neg-risk event), which makes this tail conservative."""
    s = summary(rows)
    if s["n"] == 0:
        return dict(s, p=None)
    dist = [1.0]
    for r in rows:
        p = min(1.0, max(0.0, r["p_alert"])); nxt = [0.0] * (len(dist) + 1)
        for k, v in enumerate(dist):
            nxt[k] += v * (1 - p); nxt[k + 1] += v * p
        dist = nxt
    return dict(s, p=min(1.0, sum(dist[s["wins"]:])))


def t2_permutation(rows, flag, n_perm, seed):
    """One-sided permutation p-value of excess(flagged) - excess(others), labels permuted inside p_alert strata."""
    by, k = defaultdict(list), defaultdict(int)
    s1 = 0.0; n1 = 0
    for r in rows:
        st = stratum(r["p_alert"]); x = r["win"] - r["p_alert"]; by[st].append(x)
        if r[flag]:
            k[st] += 1; s1 += x; n1 += 1
    n0 = len(rows) - n1
    if n1 == 0 or n0 == 0:
        return {"n_flag": n1, "n_other": n0, "diff": None, "p": None, "n_perm": 0, "hits": None}
    tot = sum(sum(v) for v in by.values())
    rnd = random.Random(seed); hits = 0
    for _ in range(n_perm):
        if sum(sum(rnd.sample(by[st], k[st])) for st in k) >= s1 - 1e-12:
            hits += 1
    return {"n_flag": n1, "n_other": n0, "diff": s1 / n1 - (tot - s1) / n0, "p": (hits + 1) / (n_perm + 1), "n_perm": n_perm, "hits": hits}


def cluster_ci(rows, n_boot, seed, level=0.95):
    """Percentile bootstrap of the excess, resampling whole events (clusters)."""
    ev = defaultdict(list)
    for r in rows:
        ev[r["event_slug"]].append(r)
    keys = sorted(ev)
    if len(keys) < 2:
        return None
    rnd = random.Random(seed); out = []
    for _ in range(n_boot):
        w = p = n = 0
        for _k in keys:
            for r in ev[keys[rnd.randrange(len(keys))]]:
                w += r["win"]; p += r["p_alert"]; n += 1
        out.append((w - p) / n)
    out.sort()
    a = (1 - level) / 2
    return [out[int(a * n_boot)], out[min(n_boot - 1, int((1 - a) * n_boot))]]


MIN_N, MIN_EVENTS, MIN_EXCESS = 10, 8, 0.15


def verdict(t1, t2, alpha_corr):
    """Wording fixed by the plan."""
    if t1["n"] < MIN_N or t1["n_events"] < MIN_EVENTS:
        return "INCONCLUSIVE"
    if t1["p"] < alpha_corr and t2["p"] is not None and t2["p"] < alpha_corr and t1["excess"] >= MIN_EXCESS:
        return "SUPPORTED"
    return "NOT_SUPPORTED"


def _selftest():
    rows = [{"win": 1, "p_alert": 0.5, "event_slug": f"e{i}", "initiator": f"w{i}", "f": True} for i in range(3)]
    assert abs(t1_exact(rows)["p"] - 0.125) < 1e-12                       # 3 wins out of 3 at p = 0.5
    assert abs(t1_exact(rows[:1] + [dict(rows[0], win=0)])["p"] - 0.75) < 1e-12
    rnd = random.Random(1)
    null = [{"win": int(rnd.random() < 0.4), "p_alert": 0.4, "event_slug": f"e{i}", "initiator": "w", "f": i < 40} for i in range(400)]
    assert t2_permutation(null, "f", 2000, 7)["p"] > 0.01
    strong = [dict(r, win=1) if r["f"] else r for r in null]
    assert t2_permutation(strong, "f", 2000, 7)["p"] < 0.002 and t1_exact([r for r in strong if r["f"]])["p"] < 1e-10
    lo, hi = cluster_ci([r for r in strong if r["f"]], 500, 3)
    assert lo > 0.5 and hi <= 0.6000001
    assert verdict(dict(summary(rows), p=0.0), {"p": 0.0}, 0.01) == "INCONCLUSIVE"
    print("stats selftest ok")


if __name__ == "__main__":
    _selftest()
