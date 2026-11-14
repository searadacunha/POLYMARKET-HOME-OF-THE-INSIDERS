"""Statistics of the study. Standard library only, deterministic given a seed.

T1  one alert per event: do the alerted sides win more often than their prices say?  Exact tail of a sum of independent
    Bernoulli(p_i) (Poisson-binomial), one-sided.
T2  do they win more than ordinary large entries at the same price and horizon?  Difference of mean excess (win - price)
    between alerts and control entries inside strata, events resampled whole (bootstrap), one-sided.
An excess is always win minus the price actually paid at the alert, in probability points.
"""
import math, random

PRICE_EDGES = (0.10, 0.25, 0.50, 0.75)          # price bands: <=0.10, <=0.25, <=0.50, <=0.75, <=0.90
HORIZON_EDGES = (24.0, 168.0, 720.0)            # hours to the scheduled end: <1 day, <7 days, <30 days, longer


def stratum(price, hours_to_end):
    return sum(price > e for e in PRICE_EDGES), sum(hours_to_end >= e for e in HORIZON_EDGES)


def pb_sf(ps, k):
    """P(W >= k) for W a sum of independent Bernoulli(ps). Exact by dynamic programming."""
    n = len(ps)
    if k <= 0:
        return 1.0
    if k > n:
        return 0.0
    dist = [1.0] + [0.0] * n
    for i, p in enumerate(ps):
        q = 1.0 - p
        for j in range(i + 1, 0, -1):
            dist[j] = dist[j] * q + dist[j - 1] * p
        dist[0] *= q
    return min(1.0, sum(dist[k:]))


def wilson(k, n, z=1.959964):
    if n == 0:
        return (None, None)
    p = k / n; d = 1 + z * z / n
    c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def first_per_event(alerts):
    """alerts: iterable of dicts with event, t, price, win. Keeps the earliest alert of each event (ties: lowest key)."""
    best = {}
    for a in alerts:
        b = best.get(a["event"])
        if b is None or (a["t"], a.get("key", 0)) < (b["t"], b.get("key", 0)):
            best[a["event"]] = a
    return sorted(best.values(), key=lambda a: (a["t"], a.get("key", 0)))


def t1(alerts):
    """Exact test on one alert per event. Returns n, wins, expected wins, excess (mean of win - price), p."""
    one = first_per_event(alerts)
    n = len(one); w = sum(a["win"] for a in one); e = sum(a["price"] for a in one)
    return {"n": n, "events": n, "wins": w, "expected": round(e, 4), "win_rate": w / n if n else None,
            "mean_price": e / n if n else None, "excess": (w - e) / n if n else None, "p": pb_sf([a["price"] for a in one], w) if n else None}


def _cells(alerts, controls):
    """Per event: its alert (stratum, excess) if any, and its control sums per stratum. Controls of an alerted event are
    the entries that are not alerts of the class (the caller filters them)."""
    ev = {}
    for a in first_per_event(alerts):
        ev.setdefault(a["event"], [None, {}])[0] = (stratum(a["price"], a["hours_to_end"]), a["win"] - a["price"])
    for c in controls:
        d = ev.setdefault(c["event"], [None, {}])[1]
        s = stratum(c["price"], c["hours_to_end"])
        x = d.get(s)
        if x is None:
            d[s] = [1, c["win"] - c["price"]]
        else:
            x[0] += 1; x[1] += c["win"] - c["price"]
    return ev


def _diff(sample):
    """sample: list of [alert or None, {stratum: [n, sum]}]. Controls enter as one mean per event and stratum, so that an
    event with thousands of entries weighs like any other. Returns the stratum-weighted difference, or None."""
    fa, cm = {}, {}
    for alert, ctrl in sample:
        if alert is not None:
            x = fa.setdefault(alert[0], [0, 0.0]); x[0] += 1; x[1] += alert[1]
        for s, (n, tot) in ctrl.items():
            x = cm.setdefault(s, [0, 0.0]); x[0] += 1; x[1] += tot / n
    num = den = 0.0
    for s, (n, tot) in fa.items():
        if s in cm:                                   # strata without any control are left out (counted by the caller)
            num += n * (tot / n - cm[s][1] / cm[s][0]); den += n
    return num / den if den else None


def t2(alerts, controls, draws=20000, seed=20261114):
    """Difference of mean excess, alerts minus controls, inside price x horizon strata, with events resampled whole.
    p is the share of resamples in which the difference is zero or less (one-sided); hits is that count."""
    ev = _cells(alerts, controls)
    cells = list(ev.values())
    obs = _diff(cells)
    if obs is None:
        return {"diff": None, "p": None, "draws": 0, "hits": None, "ci": (None, None), "events": len(cells)}
    rng = random.Random(seed); n = len(cells); res = []; hits = 0
    for _ in range(draws):
        d = _diff(rng.choices(cells, k=n))
        if d is None:
            continue
        res.append(d); hits += d <= 0
    res.sort()
    lo, hi = res[int(0.025 * (len(res) - 1))], res[int(0.975 * (len(res) - 1))]
    n_alert = sum(1 for a, _ in cells if a is not None)
    matched = sum(1 for a, _ in cells if a is not None and any(a[0] in c for _, c in cells))
    return {"diff": obs, "p": (hits + 1) / (len(res) + 1), "draws": len(res), "hits": hits, "ci": (lo, hi), "events": n,
            "alert_events": n_alert, "alerts_in_strata_with_controls": matched}


def boot_excess(alerts, draws=5000, seed=20261114):
    """95 % interval of the mean excess of one alert per event, events resampled."""
    one = first_per_event(alerts)
    if not one:
        return (None, None)
    x = [a["win"] - a["price"] for a in one]; rng = random.Random(seed); n = len(x)
    m = sorted(sum(rng.choices(x, k=n)) / n for _ in range(draws))
    return (m[int(0.025 * (draws - 1))], m[int(0.975 * (draws - 1))])


def _selftest():
    assert abs(pb_sf([0.5] * 4, 2) - 11 / 16) < 1e-12 and pb_sf([0.2, 0.7], 0) == 1.0 and pb_sf([0.2, 0.7], 3) == 0.0
    assert abs(pb_sf([0.2, 0.7], 2) - 0.14) < 1e-12 and abs(pb_sf([0.2, 0.7], 1) - (1 - 0.8 * 0.3)) < 1e-12
    assert stratum(0.05, 5) == (0, 0) and stratum(0.10, 24) == (0, 1) and stratum(0.9, 10000) == (4, 3) and stratum(0.3, 200) == (2, 2)
    rng = random.Random(1)
    def table(delta, n_events=600, n_ctrl=5):
        alerts, controls = [], []
        for e in range(n_events):
            p = rng.choice((0.08, 0.2, 0.4, 0.6, 0.8)); h = rng.choice((5.0, 60.0, 300.0, 2000.0))
            if e % 2 == 0:
                alerts.append({"event": e, "t": e, "price": p, "hours_to_end": h, "win": int(rng.random() < p + delta)})
            y = int(rng.random() < p)                 # the controls of one event share one outcome
            controls += [{"event": e + (0 if e % 2 else 10 ** 6), "price": p, "hours_to_end": h, "win": y} for _ in range(n_ctrl)]
        return alerts, controls
    a, c = table(0.0); r1, r2 = t1(a), t2(a, c, draws=2000)
    assert r1["n"] == 300 and 0.01 < r1["p"] < 0.999 and abs(r2["diff"]) < 0.08, (r1, r2)
    a, c = table(0.15); r1, r2 = t1(a), t2(a, c, draws=2000)
    assert r1["p"] < 1e-4 and r2["diff"] > 0.07 and r2["p"] < 0.01, (r1, r2)
    two = first_per_event([{"event": 1, "t": 5, "price": .2, "win": 1}, {"event": 1, "t": 3, "price": .4, "win": 1}])
    assert len(two) == 1 and two[0]["t"] == 3
    print("stats selftest ok")


if __name__ == "__main__":
    _selftest()
