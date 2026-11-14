"""Three scores computed from the entry-time features. Standard library only, deterministic given a seed.

M1 rarity     explainable: for each of a few directed features, how rare the value is in the discovery population
              (minus log10 of the empirical tail share), summed. No outcome is used.
M2 isolation  an isolation forest (Liu, Ting, Zhou 2008) fitted on the discovery population. No outcome is used.
M3 edge       a logistic model of the outcome with the entry price as offset, fitted on DISCOVERY outcomes only:
              predicted probability minus price. It is the only score that reads outcomes, and only those of discovery.
Thresholds are quantiles of the discovery scores; nothing is tuned on validation.
"""
import bisect, math, random

FEATURES = ("log_cash", "price", "log_hours_to_end", "log_prior_trades", "log_prior_other_markets", "log_age_h", "log_dep_24h",
            "conc_at_entry", "size_surprise", "move_1h", "log_mk_fills_24h", "side_share", "co_entrants_6h", "log_dormant_days")
# directed features of the rarity score: (name, +1 when large is unusual, -1 when small is unusual)
RARITY = (("log_cash", 1), ("log_prior_trades", -1), ("log_age_h", -1), ("conc_at_entry", 1), ("size_surprise", 1), ("side_share", 1),
          ("log_mk_fills_24h", -1), ("log_dormant_days", 1))


def vector(e):
    """Feature dict of one entry (keys of FEATURES) from the entry row and its wallet view. Missing history counts as none."""
    lg = lambda x: math.log10(1.0 + max(0.0, x or 0.0))
    med = e.get("prior_trade_median")
    dormant = (e["t"] - e["last_other_trade_ts"]) / 86400.0 if e.get("last_other_trade_ts") else 0.0
    return {"log_cash": math.log10(e["cash"]), "price": e["price"], "log_hours_to_end": lg(e["hours_to_end"]),
            "log_prior_trades": lg(e.get("prior_trades")), "log_prior_other_markets": lg(e.get("prior_other_markets")),
            "log_age_h": lg(e.get("age_h")), "log_dep_24h": lg(e.get("dep_24h")),
            "conc_at_entry": min(5.0, e["cash"] / (e["dep_7d"] + 1.0)) if e.get("dep_7d") else 0.0,
            "size_surprise": math.log10(e["cash"] / max(med, 1.0)) if med and (e.get("prior_trades") or 0) >= 5 else 0.0,
            "move_1h": (e["price"] - e["price_1h"]) if e.get("price_1h") is not None else 0.0,
            "log_mk_fills_24h": lg(e.get("mk_fills_24h")), "side_share": e["cash"] / (e["cash"] + (e.get("side_buy_cash_24h") or 0.0)),
            "co_entrants_6h": float(e.get("co_entrants_6h") or 0), "log_dormant_days": lg(dormant)}


# ---------------------------------------------------------------- M1
def rarity_fit(rows):
    return {name: sorted(r[name] for r in rows) for name, _ in RARITY}


def rarity_score(model, r):
    s, parts = 0.0, {}
    for name, sign in RARITY:
        xs = model[name]; n = len(xs)
        k = (n - bisect.bisect_left(xs, r[name])) if sign > 0 else bisect.bisect_right(xs, r[name])   # how many are at least as extreme
        parts[name] = -math.log10((k + 1) / (n + 1)); s += parts[name]
    return s, parts


# ---------------------------------------------------------------- M2
def _c(n):
    return 0.0 if n <= 1 else 2.0 * (math.log(n - 1) + 0.5772156649) - 2.0 * (n - 1) / n


def iforest_fit(rows, trees=100, sample=256, seed=20261114):
    rng = random.Random(seed); X = [[r[f] for f in FEATURES] for r in rows]; limit = math.ceil(math.log2(sample))

    def grow(idx, depth):
        if depth >= limit or len(idx) <= 1:
            return (len(idx),)
        for _ in range(8):                               # a feature with spread, if any
            f = rng.randrange(len(FEATURES)); vals = [X[i][f] for i in idx]; lo, hi = min(vals), max(vals)
            if hi > lo:
                break
        else:
            return (len(idx),)
        cut = rng.uniform(lo, hi)
        return (f, cut, grow([i for i in idx if X[i][f] < cut], depth + 1), grow([i for i in idx if X[i][f] >= cut], depth + 1))
    forest = [grow(rng.sample(range(len(X)), min(sample, len(X))), 0) for _ in range(trees)]
    return {"forest": forest, "c": _c(min(sample, len(X)))}


def iforest_score(model, r):
    x = [r[f] for f in FEATURES]; total = 0.0
    for node in model["forest"]:
        depth = 0
        while len(node) == 4:
            node = node[2] if x[node[0]] < node[1] else node[3]; depth += 1
        total += depth + _c(node[0])
    return 2.0 ** (-(total / len(model["forest"])) / model["c"])       # close to 1: isolated early, unusual


# ---------------------------------------------------------------- M3
def _solve(A, b):
    n = len(b); M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for i in range(n):
        p = max(range(i, n), key=lambda k: abs(M[k][i])); M[i], M[p] = M[p], M[i]
        if abs(M[i][i]) < 1e-12:
            raise ValueError("singular system")
        for k in range(i + 1, n):
            f = M[k][i] / M[i][i]
            for j in range(i, n + 1):
                M[k][j] -= f * M[i][j]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (M[i][n] - sum(M[i][j] * x[j] for j in range(i + 1, n))) / M[i][i]
    return x


def edge_fit(rows, wins, ridge=1.0, iters=12):
    """Newton steps on a logistic model with offset logit(price): the model can only learn departures from the price."""
    k = len(FEATURES); n = len(rows)
    mu = [sum(r[f] for r in rows) / n for f in FEATURES]
    sd = [math.sqrt(sum((r[f] - m) ** 2 for r in rows) / n) or 1.0 for f, m in zip(FEATURES, mu)]
    Z = [[1.0] + [(r[f] - m) / s for f, m, s in zip(FEATURES, mu, sd)] for r in rows]
    off = [math.log(min(max(r["price"], 0.005), 0.995) / (1 - min(max(r["price"], 0.005), 0.995))) for r in rows]
    beta = [0.0] * (k + 1)
    for _ in range(iters):
        g = [-(ridge * b if j else 0.0) for j, b in enumerate(beta)]
        H = [[(ridge if (i == j and i) else 0.0) for j in range(k + 1)] for i in range(k + 1)]
        for z, o, y in zip(Z, off, wins):
            p = 1.0 / (1.0 + math.exp(-(o + sum(b * v for b, v in zip(beta, z))))); w = p * (1 - p); d = y - p
            for i in range(k + 1):
                g[i] += d * z[i]; zi = w * z[i]
                for j in range(i, k + 1):
                    H[i][j] += zi * z[j]
        for i in range(k + 1):
            for j in range(i):
                H[i][j] = H[j][i]
        step = _solve(H, g); beta = [b + s for b, s in zip(beta, step)]
        if max(abs(s) for s in step) < 1e-6:
            break
    return {"mu": mu, "sd": sd, "beta": beta}


def edge_score(model, r):
    p0 = min(max(r["price"], 0.005), 0.995)
    z = [1.0] + [(r[f] - m) / s for f, m, s in zip(FEATURES, model["mu"], model["sd"])]
    lin = math.log(p0 / (1 - p0)) + sum(b * v for b, v in zip(model["beta"], z))
    return 1.0 / (1.0 + math.exp(-lin)) - r["price"]


def quantile(values, q):
    v = sorted(values)
    return v[min(len(v) - 1, int(q * len(v)))]


def _selftest():
    rng = random.Random(3)
    def row(odd=False):
        e = {"cash": 10 ** rng.uniform(3, 3.6), "price": rng.uniform(0.05, 0.9), "hours_to_end": rng.uniform(1, 2000), "t": 10 ** 9,
             "prior_trades": rng.randint(30, 400), "prior_other_markets": rng.randint(5, 80), "age_h": rng.uniform(500, 9000), "dep_24h": 0.0,
             "dep_7d": 0.0, "prior_trade_median": rng.uniform(50, 500), "price_1h": None, "mk_fills_24h": rng.randint(5, 300),
             "side_buy_cash_24h": rng.uniform(5000, 90000), "co_entrants_6h": rng.randint(0, 6), "last_other_trade_ts": 10 ** 9 - 3600}
        if odd:
            e.update(cash=60000.0, prior_trades=0, prior_other_markets=0, age_h=0.1, dep_24h=61000.0, dep_7d=61000.0, prior_trade_median=None,
                     mk_fills_24h=0, side_buy_cash_24h=0.0, last_other_trade_ts=None)
        return vector(e)
    base = [row() for _ in range(1500)]; odd = row(True)
    m1 = rarity_fit(base); s_odd, parts = rarity_score(m1, odd); s_base = sorted(rarity_score(m1, r)[0] for r in base)
    assert s_odd > s_base[-1] and parts["log_cash"] > 3, (s_odd, s_base[-1])
    m2 = iforest_fit(base, trees=60); i_odd = iforest_score(m2, odd); i_base = sorted(iforest_score(m2, r) for r in base)
    assert i_odd > i_base[int(0.99 * len(i_base))], (i_odd, i_base[-5:])
    wins = [int(rng.random() < min(0.99, r["price"] + (0.25 if r["co_entrants_6h"] >= 5 else 0.0))) for r in base]   # planted relation
    m3 = edge_fit(base, wins)
    hi = [edge_score(m3, r) for r in base if r["co_entrants_6h"] >= 5]; lo = [edge_score(m3, r) for r in base if r["co_entrants_6h"] <= 1]
    assert sum(hi) / len(hi) > sum(lo) / len(lo) + 0.05, (sum(hi) / len(hi), sum(lo) / len(lo))
    flat = edge_fit(base, [int(rng.random() < r["price"]) for r in base])
    assert abs(sum(edge_score(flat, r) for r in base) / len(base)) < 0.03                                          # no relation: no edge
    assert _solve([[2.0, 1.0], [1.0, 3.0]], [3.0, 5.0]) == [0.8, 1.4]
    print("models selftest ok")


if __name__ == "__main__":
    _selftest()
