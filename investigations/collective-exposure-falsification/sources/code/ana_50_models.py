#!/usr/bin/env python3
"""Mission 5 analysis: models M0-M4, confirmatory tests T1-T7, matched controls, calibration, sensitivity, verdict.

Stages (each reads only the labels it is allowed to read):
  train     TRAIN labels only: lambda by event-grouped CV, TRAIN fit (models_train.json).
  valid     after the freeze, once: TRAIN fit scored on VALID (T1-T7), then refit on TRAIN+VALID (VALID units of
            events that also hold TEST markets are purged from the refit).
  test      after valid, once: frozen TRAIN+VALID models scored on TEST (T1-T7, Holm, BH, calibration, sensitivity).
  nullgate  after test: T1 on day-shift null panels of TEST with the frozen models, same market subset.
  controls  synthetic injection panels (TRAIN only): mock split by event hash, the same tests and p rule.
  verdict   applies the plan's verdict rules to results_valid/test, nullgate and controls (no new computation).
Labels are joined here (and, for TRAIN only, in ctl_40_inject.py).

usage: ana_50_models.py STAGE --panel P.jsonl.gz --labels labels.jsonl.gz --out DIR [options]
"""
import argparse
import datetime as dt
import gzip
import hashlib
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ETUDE = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from registre import enregistrer  # noqa: E402  copied into code/ before the freeze

W = 3600
LAMBDAS = (0.1, 1.0, 10.0, 100.0)
B_EVENT = 20000
B_TWOWAY = 20000
B_SENS = 5000
SESOI_LL = 0.002
SESOI_EXCESS = 0.03
MIN_UNITS, MIN_EVENTS = 100, 50
MIN_F6_UNITS, MIN_F6_COVERAGE = 30, 0.70
HYPERACTIVE_EVENTS = 50
ALPHA = 0.05
N_FAMILY = 7
MODELS = ("M0", "M1", "M2", "M3", "M4")
TESTS = {  # name: (small model, large model, unit type)
    "T1": ("M1", "M3", "COL"), "T2": ("M2", "M3", "COL"), "T3": ("M0", "M3", "ALL"),
    "T4": (None, None, "COL"), "T5": ("M3", "M4", "COL"), "T6": ("M1", "M2", "IND"), "T7": ("M0", "M1", "PV")}
M3_GROUPS = {"F3": [3], "F4": [4], "F5": [5], "F7": [6], "F8": [7], "size": [0, 1, 2, 8, 9, 10, 11, 12]}


# ------------------------------------------------------------------------------------------------ data
def load_jsonl_gz(p):
    with gzip.open(p, "rt") as f:
        return [json.loads(l) for l in f]


def load_labels(path, cids):
    """winner per requested condition id only; a winner other than YES/NO is refused, never coded as a loss."""
    out = {}
    with gzip.open(path, "rt") as f:
        for l in f:
            r = json.loads(l)
            c = r["condition_id"].lower()
            if c in cids:
                if r["winner"] not in ("YES", "NO"):
                    raise SystemExit(f"unexpected winner {r['winner']!r} for {c}: refused")
                out[c] = r["winner"]
    return out


def lg1p(x):
    return math.log1p(max(0.0, x or 0.0))


def logit(p):
    p = min(0.99, max(0.01, p))
    return math.log(p / (1 - p))


def funding_feats(u, fund):
    """[F6a direct pair, F6b common non-hub funder, share of contributors without complete history,
    F6 unknown (no link found while some history is incomplete or a candidate edge is unresolved)]."""
    ws = u["col_s"]["wallets"]
    if not ws or fund is None:
        return [0.0, 0.0, 0.0, 0.0]
    st = fund["status"]
    unk = sum(1 for w in ws if st.get(w) not in ("complete", "early")) / len(ws)
    cut = u["t"] - W
    a = b = unresolved = 0
    for i, w1 in enumerate(ws):
        for w2 in ws[i + 1:]:
            k = "|".join(sorted((w1, w2)))
            if any(ts < cut for ts in fund["direct"].get(k, [])):
                a = 1
            if k in fund["unresolved"]:
                unresolved = 1
            f1 = {f for f, ts in fund["funders"].get(w1, {}).items() if ts < cut}
            f2 = {f for f, ts in fund["funders"].get(w2, {}).items() if ts < cut}
            if f1 & f2:
                b = 1
    f6u = float(not (a or b) and (unk > 0 or unresolved))
    return [float(a), float(b), unk, f6u]


def features(u, model, fund=None):
    # price with side-specific calibration: YES and NO sides of a market do not win at the same base rate
    yes = 1.0 if u["side"] == "YES" else 0.0
    x = [logit(u["p"]), yes, yes * logit(u["p"])]
    if model == "M0":
        return x
    pb = u["pub"]
    he = pb["h_to_end"]
    x += [lg1p(pb["vol"]), math.log(pb["vol_ratio"]) if pb["vol_ratio"] else 0.0,
          float(pb["vol_ratio"] is None), pb["dp"], lg1p(pb["n_wallets"]), lg1p(pb["n_fills"]),
          pb["last_share"], math.log1p(max(0.0, pb["age_h"])), lg1p(max(0.0, he)) if he is not None else 0.0,
          float(he is None), float(pb["pv"])]
    if model == "M1":
        return x
    d = u["ind"]
    x += [lg1p(d["max1_s"]), lg1p(d["max1_o"]), float(d["ind_s"]), float(d["ind_o"])]
    if model == "M2":
        return x
    s, o = u["col_s"], u["col_o"]
    x += [lg1p(s["n"]), lg1p(s["usd"]), s["top"], s["f3"], s["f4"], float(s["f5"]), float(s["f7"]), s["f8"],
          float(s["score"]), float(s["col"]), lg1p(o["n"]), lg1p(o["usd"]), o["top"]]
    if model == "M3":
        return x
    return x + funding_feats(u, fund)


N_M2 = len(features({"side": "YES", "p": 0.5, "pub": {"h_to_end": None, "vol": 0, "vol_ratio": None, "dp": 0,
                                                      "n_wallets": 0, "n_fills": 0, "last_share": 0, "age_h": 0,
                                                      "pv": 0},
                     "ind": {"max1_s": 0, "max1_o": 0, "ind_s": 0, "ind_o": 0}}, "M2"))


def design(units, model, fund=None, drop=None):
    X = np.array([features(u, model, fund) for u in units], dtype=float)
    if drop:
        X = np.delete(X, [N_M2 + j for j in drop], axis=1)
    return X


# ------------------------------------------------------------------------------------------------ model
class Logit:
    """L2-penalised logistic regression on features standardised with the fitting set's moments (intercept not
    penalised), IRLS with a convergence check."""

    def fit(self, X, y, lam, mu=None, sd=None):
        if len(np.unique(y)) != 2:
            raise SystemExit("fit refused: the outcome has a single class")
        self.mu = X.mean(0) if mu is None else mu
        self.sd = X.std(0) if sd is None else sd
        self.sd = np.where(self.sd > 1e-12, self.sd, 1.0)
        Z = np.column_stack([np.ones(len(X)), (X - self.mu) / self.sd])
        beta = np.zeros(Z.shape[1])
        pen = np.full(Z.shape[1], lam)
        pen[0] = 0.0
        self.converged = False
        for _ in range(200):
            eta = np.clip(Z @ beta, -30, 30)
            p = 1 / (1 + np.exp(-eta))
            w = np.maximum(p * (1 - p), 1e-9)
            g = Z.T @ (y - p) - pen * beta
            H = (Z * w[:, None]).T @ Z + np.diag(pen) + 1e-9 * np.eye(Z.shape[1])
            step = np.linalg.solve(H, g)
            beta = beta + step
            if np.max(np.abs(step)) < 1e-8:
                self.converged = True
                break
        self.beta, self.lam = beta, lam
        return self

    def logit(self, X):
        Z = np.column_stack([np.ones(len(X)), (X - self.mu) / self.sd])
        return np.clip(Z @ self.beta, -30, 30)

    def predict(self, X):
        return 1 / (1 + np.exp(-self.logit(X)))

    def to_json(self):
        return {"beta": self.beta.tolist(), "mu": self.mu.tolist(), "sd": self.sd.tolist(), "lam": self.lam,
                "converged": self.converged}

    @staticmethod
    def from_json(d):
        m = Logit()
        m.beta, m.mu, m.sd, m.lam = (np.array(d["beta"]), np.array(d["mu"]), np.array(d["sd"]), d["lam"])
        m.converged = d.get("converged")
        return m


def logloss(y, p):
    p = np.clip(p, 1e-12, 1 - 1e-12)
    return -(y * np.log(p) + (1 - y) * np.log(1 - p))


def fold_of(ev, k=5):
    return int(hashlib.sha256(f"fold|{ev}".encode()).hexdigest()[:8], 16) % k


def choose_lambda(X, y, ev):
    folds = np.array([fold_of(e) for e in ev])
    scores = {}
    for lam in LAMBDAS:
        ll = np.full(len(y), np.nan)
        for k in range(5):
            tr, te = folds != k, folds == k
            if te.sum() == 0 or len(np.unique(y[tr])) < 2:
                raise SystemExit(f"CV fold {k} unusable: refused (never scored as a zero loss)")
            ll[te] = logloss(y[te], Logit().fit(X[tr], y[tr], lam).predict(X[te]))
        scores[lam] = float(np.mean(ll))
    best = min(LAMBDAS, key=lambda l: (scores[l], -l))  # tie -> stronger penalty
    return best, scores


def fit_models(units, y, fund, lams=None, drop3=None):
    ev = [u["event_id"] for u in units]
    out, cv = {}, {}
    for m in MODELS:
        if m == "M4" and fund is None:
            continue
        X = design(units, m, fund, drop=drop3 if m == "M3" else None)
        if lams and m in lams:
            lam = lams[m]
        else:
            lam, cv[m] = choose_lambda(X, y, ev)
        out[m] = Logit().fit(X, y, lam)
    return out, cv


# ------------------------------------------------------------------------------------------------ inference
def rng_for(tag):
    return np.random.default_rng(int(hashlib.sha256(tag.encode()).hexdigest()[:8], 16))


def _summary(theta, stats, B):
    cen = stats - theta
    p = (1 + np.sum(cen >= theta)) / (B + 1)
    return {"stat": float(theta), "p": float(p), "upper95_one_sided": float(theta - np.quantile(cen, 0.05)),
            "lower95_one_sided": float(theta - np.quantile(cen, 0.95)),
            "ci95": [float(np.quantile(stats, 0.025)), float(np.quantile(stats, 0.975))], "B": B}


def event_boot(d, ev, tag, B=B_EVENT):
    """Mean of per-unit values d, events resampled with replacement. H0: theta <= 0."""
    ev = np.asarray(ev)
    uniq, inv = np.unique(ev, return_inverse=True)
    E = len(uniq)
    s = np.bincount(inv, weights=d, minlength=E)
    n = np.bincount(inv, minlength=E).astype(float)
    rng = rng_for(tag)
    stats = np.empty(B)
    for b0 in range(0, B, 1000):
        bb = min(1000, B - b0)
        cnt = rng.multinomial(E, np.full(E, 1.0 / E), size=bb).astype(float)
        stats[b0:b0 + bb] = (cnt @ s) / np.maximum(cnt @ n, 1e-12)
    r = _summary(float(d.mean()), stats, B)
    r.update(n_units=int(len(d)), n_events=int(E))
    return r


def _wallet_index(wallets):
    wl = sorted({w for ws in wallets for w in ws})
    widx = {w: i for i, w in enumerate(wl)}
    flat = np.array([widx[w] for ws in wallets for w in ws], dtype=int)
    owner = np.repeat(np.arange(len(wallets)), [len(ws) for ws in wallets])
    lens = np.array([len(ws) for ws in wallets], dtype=float)
    return wl, flat, owner, lens


def twoway_boot(d, ev, wallets, tag, B=B_TWOWAY):
    """Pigeonhole bootstrap: Poisson(1) weights on events and on contributor wallets; unit weight = event weight
    x mean weight of its wallets (1 if none)."""
    ev = np.asarray(ev)
    uniq, inv = np.unique(ev, return_inverse=True)
    wl, flat, owner, lens = _wallet_index(wallets)
    has = lens > 0
    rng = rng_for(tag + "|2w")
    stats = np.empty(B)
    n = len(d)
    for b in range(B):
        we = rng.poisson(1.0, len(uniq)).astype(float)[inv]
        if len(wl):
            ww = rng.poisson(1.0, len(wl)).astype(float)
            sums = np.bincount(owner, weights=ww[flat], minlength=n)
            mw = np.where(has, sums / np.maximum(lens, 1), 1.0)
        else:
            mw = 1.0
        w = we * mw
        stats[b] = (w * d).sum() / max(w.sum(), 1e-12)
    r = _summary(float(d.mean()), stats, B)
    r["n_wallets"] = len(wl)
    return r


def wallet_clusters(units_sel, all_units):
    """One cluster per unit: its wallet that holds the most units of the split (ties by address), so that units
    sharing a recurrent wallet move together; a unit without any wallet is its own event-level cluster."""
    count = {}
    for u in all_units:
        for w in unit_wallets(u):
            count[w] = count.get(w, 0) + 1
    out = []
    for u in units_sel:
        ws = unit_wallets(u)
        out.append("w:" + max(ws, key=lambda w: (count[w], w)) if ws else "e:" + u["event_id"])
    return out


def holm(ps):
    order = sorted(ps, key=lambda k: ps[k])
    m, out, run = len(order), {}, 0.0
    for i, k in enumerate(order):
        run = max(run, min(1.0, (m - i) * ps[k]))
        out[k] = run
    return out


def bh(ps):
    order = sorted(ps, key=lambda k: ps[k])
    m, out, prev = len(order), {}, 1.0
    for i in range(m - 1, -1, -1):
        k = order[i]
        prev = min(prev, ps[k] * m / (i + 1))
        out[k] = prev
    return out


def calibration(y, p):
    q = np.clip(p, 1e-6, 1 - 1e-6)
    lp = np.log(q / (1 - q))
    m = Logit().fit(lp[:, None], y, 0.0, mu=np.zeros(1), sd=np.ones(1))
    order = np.argsort(p, kind="stable")
    bins = np.array_split(order, 10)
    ece = sum(len(b) / len(p) * abs(y[b].mean() - p[b].mean()) for b in bins if len(b))
    rel = [{"p_mean": float(p[b].mean()), "win_rate": float(y[b].mean()), "n": int(len(b))} for b in bins if len(b)]
    return {"intercept": float(m.beta[0]), "slope": float(m.beta[1]), "ece": float(ece),
            "brier": float(np.mean((p - y) ** 2)), "logloss": float(logloss(y, p).mean()), "reliability": rel}


# ------------------------------------------------------------------------------------------------ matched controls
MATCH_COVS = ("logit_p", "h_end", "cumvol", "vol", "nw", "age", "adp", "adp4", "day")


def match_cov(u):
    pb = u["pub"]
    return [logit(u["p"]), lg1p(max(0.0, pb["h_to_end"] or 0.0)), lg1p(pb["cumvol"]), lg1p(pb["vol"]),
            lg1p(pb["n_wallets"]), math.log1p(max(0.0, pb["age_h"])), abs(pb["dp"]), abs(pb["dp4h"]),
            u["t"] / 86400.0]


def matched_excess(units, y, tag, B=B_EVENT, k=5, caliper=1.0):
    """Exact on side, category and endDate known/unknown; nearest 5 non-COL units of other events (with
    replacement), caliper 1.0. p and upper bound = the larger of (a) COL-event bootstrap and (b) a two-way
    bootstrap with Poisson weights on ALL events involved (the COL unit's and its controls'), and (c) a bootstrap of
    wallet clusters (wallet_clusters)."""
    col = [i for i, u in enumerate(units) if "COL" in u["types"]]
    ctl = [i for i, u in enumerate(units) if "COL" not in u["types"] and u["col_s"]["n"] == 0]
    if not col or not ctl:
        return {"status": "IMPOSSIBLE", "reason": "no COL or no control unit"}
    C = np.array([match_cov(u) for u in units])
    sd = C.std(0)
    sd = np.where(sd > 1e-12, sd, 1.0)
    Zs = C / sd
    p = np.array([u["p"] for u in units])
    res = y - p
    key = lambda u: (u["side"], u["category"], u["pub"]["h_to_end"] is None)
    by_key = {}
    for j in ctl:
        by_key.setdefault(key(units[j]), []).append(j)
    diffs, used, dropped, pairs = [], [], 0, []
    for i in col:
        u = units[i]
        ok = np.array([j for j in by_key.get(key(u), []) if units[j]["event_id"] != u["event_id"]], dtype=int)
        if not len(ok):
            dropped += 1
            continue
        dist = np.abs(Zs[ok] - Zs[i]).mean(1)
        sel = ok[np.argsort(dist, kind="stable")[:k]]
        sel = sel[np.abs(Zs[sel] - Zs[i]).mean(1) <= caliper]
        if not len(sel):
            dropped += 1
            continue
        diffs.append(res[i] - res[sel].mean())
        used.append(i)
        pairs.append(sel)
    if len(used) < MIN_UNITS:
        return {"status": "IMPOSSIBLE", "reason": f"{len(used)} matched COL units < {MIN_UNITS}",
                "n_matched": len(used)}
    diffs = np.array(diffs)
    evs = [units[i]["event_id"] for i in used]
    r = event_boot(diffs, evs, tag, B)
    # (b) two-way over all events and wallets
    all_ev = sorted({units[i]["event_id"] for i in used} | {units[j]["event_id"] for s in pairs for j in s})
    eidx = {e: n for n, e in enumerate(all_ev)}
    col_e = np.array([eidx[units[i]["event_id"]] for i in used])
    c_flat = np.array([eidx[units[j]["event_id"]] for s in pairs for j in s])
    c_owner = np.repeat(np.arange(len(used)), [len(s) for s in pairs])
    c_len = np.array([len(s) for s in pairs], dtype=float)
    rng = rng_for(tag + "|T4-2w")
    stats = np.empty(B)
    for b in range(B):
        we = rng.poisson(1.0, len(all_ev)).astype(float)
        wc = np.bincount(c_owner, weights=we[c_flat], minlength=len(used)) / c_len
        w = we[col_e] * wc   # every event involved (the COL unit's and its controls'), no wallet factor
        stats[b] = (w * diffs).sum() / max(w.sum(), 1e-12)
    r2 = _summary(float(diffs.mean()), stats, B)
    allc = np.concatenate(pairs)
    ctl_arr = np.array(ctl)
    smd = {}
    for c, name in enumerate(MATCH_COVS):
        a, b0, b1 = C[used, c], C[ctl_arr, c], C[allc, c]
        pooled = math.sqrt((a.var() + b0.var()) / 2) or 1.0
        smd[name] = {"before": float((a.mean() - b0.mean()) / pooled), "after": float((a.mean() - b1.mean()) / pooled)}
    rw = event_boot(diffs, wallet_clusters([units[i] for i in used], units), tag + "|T4-wallet", B)
    r.update(p_event=r["p"], all_events=r2, wallet_cluster=rw, p=max(r["p"], r2["p"], rw["p"]),
             upper95_one_sided=max(r["upper95_one_sided"], r2["upper95_one_sided"], rw["upper95_one_sided"]),
             n_col_units=len(col), n_matched=len(used), n_unmatched=dropped, balance_smd=smd,
             reused_controls=int(len(allc) - len(set(allc.tolist()))),
             col_excess=float(res[used].mean()), control_excess=float(np.mean([res[s].mean() for s in pairs])))
    return r


# ------------------------------------------------------------------------------------------------ evaluation
def unit_wallets(u):
    ws = list(u["col_s"]["wallets"])
    if u["ind"].get("single_s"):
        ws.append(u["ind"]["single_s"])
    return sorted(set(ws))


def select(units, kind):
    if kind == "ALL":
        return list(range(len(units)))
    return [i for i, u in enumerate(units) if kind in u["types"]]


def hyperactive_wallets(units):
    ev = {}
    for u in units:
        for w in unit_wallets(u):
            ev.setdefault(w, set()).add(u["event_id"])
    return {w for w, s in ev.items() if len(s) >= HYPERACTIVE_EVENTS}


def run_tests(units, y, models, fund, tag, only=None):
    preds = {m: models[m].predict(design(units, m, fund)) for m in models}
    ll = {m: logloss(y, preds[m]) for m in preds}
    hyper = hyperactive_wallets(units)
    out = {}
    for name, (small, large, kind) in TESTS.items():
        if only and name not in only:
            continue
        idx = select(units, kind)
        ev = [units[i]["event_id"] for i in idx]
        n_ev = len(set(ev))
        size_ok = len(idx) >= MIN_UNITS and n_ev >= MIN_EVENTS
        info = {"units": kind, "n_units": len(idx), "n_events": n_ev,
                "n_wallets": len({w for i in idx for w in unit_wallets(units[i])}),
                "share_units_with_hyperactive_wallet": (sum(1 for i in idx if set(unit_wallets(units[i])) & hyper)
                                                        / len(idx)) if idx else None}
        if name == "T5":
            f6 = [funding_feats(units[i], fund) for i in idx] if fund else []
            n_f6 = sum(1 for f in f6 if f[0] or f[1])
            wl = {w for i in idx for w in units[i]["col_s"]["wallets"]}
            cov = (sum(1 for w in wl if fund["status"].get(w) in ("complete", "early")) / len(wl)) if (fund and wl) else 0.0
            info.update(n_units_f6=n_f6, funding_coverage_wallets=float(cov))
            size_ok = size_ok and fund is not None and n_f6 >= MIN_F6_UNITS and cov >= MIN_F6_COVERAGE
        if not size_ok:
            out[name] = {**info, "status": "IMPOSSIBLE", "p": None}
            continue
        if name == "T4":
            r = matched_excess(units, y, f"{tag}|{name}")
            if r.get("status") == "IMPOSSIBLE":
                out[name] = {**info, **r, "p": None}
            else:
                out[name] = {**info, **r, "sesoi": SESOI_EXCESS}
            continue
        d = ll[small][idx] - ll[large][idx]
        r = event_boot(d, ev, f"{tag}|{name}")
        rw = event_boot(d, wallet_clusters([units[i] for i in idx], units), f"{tag}|{name}|wallet")
        r2 = twoway_boot(d, ev, [unit_wallets(units[i]) for i in idx], f"{tag}|{name}")
        # decision: the larger of the event-cluster and wallet-cluster p; pigeonhole two-way reported only
        r.update(p_event=r["p"], wallet_cluster=rw, twoway_pigeonhole=r2, p=max(r["p"], rw["p"]),
                 upper95_one_sided=max(r["upper95_one_sided"], rw["upper95_one_sided"]))
        out[name] = {**info, **r, "small": small, "large": large, "sesoi": SESOI_LL}
    # Holm over the whole declared family; an impossible test enters with p = 1 (it cannot reject)
    ps = {k: (v["p"] if v.get("p") is not None else 1.0) for k, v in out.items()}
    if only is None:
        assert len(ps) == N_FAMILY
    hp, bp = holm(ps), bh(ps)
    for k in out:
        imp = out[k].get("status") == "IMPOSSIBLE"
        out[k]["p_holm"], out[k]["q_bh"] = hp[k], bp[k]
        out[k]["rejected_holm"] = bool(hp[k] <= ALPHA and not imp)
        out[k]["survives_bh"] = bool(bp[k] <= ALPHA and not imp)
    cal = {}
    for m in preds:
        cal[m] = {"all": calibration(y, preds[m])}
        ci = select(units, "COL")
        if len(ci) >= 20:
            cal[m]["COL"] = calibration(y[ci], preds[m][ci])
    cal["M0raw"] = {"all": calibration(y, np.array([u["p"] for u in units]))}
    return out, cal, preds


# ------------------------------------------------------------------------------------------------ helpers
def eligible(units, split):
    return [u for u in units if u["split"] == split]


def labels_vec(units, lab):
    miss = [u["cid"] for u in units if u["cid"] not in lab]
    if miss:
        raise SystemExit(f"{len(miss)} units without a label, e.g. {miss[:3]}: refused (never scored as a miss)")
    return np.array([1.0 if lab[u["cid"]] == u["side"] else 0.0 for u in units])


def reg(test, declare, t, sortie, donnees="reelles", ncomp=1, note=None, params=None):
    imp = t.get("status") == "IMPOSSIBLE"
    enregistrer(ETUDE, test=test, declare=declare, n=int(t.get("n_units") or 0), agent="mission5-ana50",
                n_effectif=t.get("n_events"), stat=None if imp or t.get("stat") is None else float(t["stat"]),
                p=None if imp or t.get("p") is None else float(t["p"]),
                n_tirages=None if imp else t.get("B"), n_comparaisons=ncomp, donnees=donnees, sortie=sortie,
                params=params or {}, note=("IMPOSSIBLE: " + str(t.get("reason", "minimum size or data not met")))
                if imp else note)


def load_funding(path):
    if not path:
        return None
    d = json.load(open(path))
    return {"status": d["status"], "direct": d["direct"], "funders": d["funders"],
            "unresolved": set(d.get("unresolved", []))}


def merge_funding(fund, extra_path):
    e = json.load(open(extra_path))
    out = {"status": dict(fund["status"]), "direct": dict(fund["direct"]), "funders": dict(fund["funders"]),
           "unresolved": set(fund["unresolved"])}
    out["status"].update(e["status"])
    out["direct"].update(e["direct"])
    out["funders"].update(e["funders"])
    return out


def write(path, obj):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1, sort_keys=True, default=float)


def test_events(holdout_path):
    return {str(json.loads(l)["event_id"]) for l in open(holdout_path) if json.loads(l)["split"] == "TEST"}


# ------------------------------------------------------------------------------------------------ stages
def stage_train(a, units, fund):
    tr = eligible(units, "TRAIN")
    lab = load_labels(a.labels, {u["cid"] for u in tr})
    y = labels_vec(tr, lab)
    models, cv = fit_models(tr, y, fund)
    out = {"n_units": len(tr), "n_events": len({u["event_id"] for u in tr}), "cv_logloss": cv,
           "lambda": {m: models[m].lam for m in models}, "models": {m: models[m].to_json() for m in models},
           "unit_types": {k: sum(1 for u in tr if k in u["types"]) for k in ("R", "PV", "IND", "COL")}}
    write(os.path.join(a.out, "models_train.json"), out)
    return {k: out[k] for k in ("n_units", "n_events", "lambda", "unit_types")}


def stage_valid(a, units, fund):
    path = os.path.join(a.out, "results_valid.json")
    if os.path.exists(path):
        raise SystemExit("VALID was already evaluated: refused (VALID is read once)")
    tr, va = eligible(units, "TRAIN"), eligible(units, "VALID")
    mt = json.load(open(os.path.join(a.out, "models_train.json")))
    models = {m: Logit.from_json(d) for m, d in mt["models"].items()}
    lab = load_labels(a.labels, {u["cid"] for u in tr + va})
    yv = labels_vec(va, lab)
    tests, cal, _ = run_tests(va, yv, models, fund, "VALID")
    write(path, {"tests": tests, "calibration": cal, "n_units": len(va),
                 "unit_types": {k: sum(1 for u in va if k in u["types"]) for k in ("R", "PV", "IND", "COL")}})
    for k, t in tests.items():
        reg(f"VALID_{k}", True, t, path)
    # refit on TRAIN + VALID, same lambda and specification; VALID units of events holding TEST markets purged
    tev = test_events(a.holdout)
    va_keep = [u for u in va if u["event_id"] not in tev]
    both = tr + va_keep
    yb = labels_vec(both, lab)
    refit, _ = fit_models(both, yb, fund, lams=mt["lambda"])
    write(os.path.join(a.out, "models_trainvalid.json"),
          {"models": {m: refit[m].to_json() for m in refit}, "lambda": mt["lambda"], "n_units": len(both),
           "valid_units_purged_shared_event_with_test": len(va) - len(va_keep)})
    return {k: {kk: v.get(kk) for kk in ("n_units", "stat", "p", "status")} for k, v in tests.items()}


def refit_variant(units_tv, y_tv, lam_m1, lam_m3, drop3=None):
    return {"M1": Logit().fit(design(units_tv, "M1"), y_tv, lam_m1),
            "M3": Logit().fit(design(units_tv, "M3", drop=drop3), y_tv, lam_m3)}


def stage_test(a, units, fund):
    path = os.path.join(a.out, "results_test.json")
    if os.path.exists(path):
        raise SystemExit("TEST was already evaluated: refused (TEST is read once)")
    if not os.path.exists(os.path.join(a.out, "results_valid.json")):
        raise SystemExit("VALID must be evaluated before TEST")
    te = eligible(units, "TEST")
    mtv = json.load(open(os.path.join(a.out, "models_trainvalid.json")))
    models = {m: Logit.from_json(d) for m, d in mtv["models"].items()}
    lab = load_labels(a.labels, {u["cid"] for u in te})
    y = labels_vec(te, lab)
    tests, cal, preds = run_tests(te, y, models, fund, "TEST")
    write(path, {"tests": tests, "calibration": cal, "n_units": len(te),
                 "unit_types": {k: sum(1 for u in te if k in u["types"]) for k in ("R", "PV", "IND", "COL")}})
    for k, t in tests.items():
        reg(f"TEST_{k}", True, t, path)

    # sensitivity of T1 (reported, never used to choose): one registry line per variant
    sens = {}
    col = select(te, "COL")
    d_main = logloss(y, preds["M1"]) - logloss(y, preds["M3"])

    def sub(name, idx, d=d_main):
        if len(idx) < 20:
            sens[name] = {"n_units": len(idx), "status": "TOO_FEW"}
            return
        sens[name] = event_boot(d[idx], [te[i]["event_id"] for i in idx], f"TEST|sens|{name}", B_SENS)

    fam = lambda i: te[i]["col_s"]["families"]
    sub("F1_only", [i for i in col if "F1" in fam(i)])
    sub("F2_only", [i for i in col if "F2" in fam(i)])
    sub("score_ge_2", [i for i in col if te[i]["col_s"]["score"] >= 2])
    sub("score_ge_3", [i for i in col if te[i]["col_s"]["score"] >= 3])
    sub("price_0.10_0.80", [i for i in col if 0.10 <= te[i]["p"] <= 0.80])
    sub("ge_24h_before_end", [i for i in col if (te[i]["pub"]["h_to_end"] or 0) >= 24])
    closed = {}
    with gzip.open(a.universe, "rt") as f:
        for l in f:
            m = json.loads(l)
            closed[m["condition_id"].lower()] = m["closed_ts"]
    end = {}
    for l in open(a.meta):
        r = json.loads(l)
        if r.get("status") == "ok" and r.get("endDate"):
            try:
                end[r["condition_id"].lower()] = int(dt.datetime.fromisoformat(
                    r["endDate"].replace("Z", "+00:00")).timestamp())
            except ValueError:
                pass
    sub("closed_on_schedule", [i for i in col if te[i]["cid"] in end
                               and abs(closed.get(te[i]["cid"], 0) - end[te[i]["cid"]]) <= 86400])
    hyper = hyperactive_wallets(te)
    sub("without_hyperactive_wallets", [i for i in col if not (set(unit_wallets(te[i])) & hyper)])
    # refit variants on TRAIN + VALID (same purge): lambda fixed at each grid value, leave one M3 group out
    tr, va = eligible(units, "TRAIN"), eligible(units, "VALID")
    tev = test_events(a.holdout)
    tv = tr + [u for u in va if u["event_id"] not in tev]
    lab_tv = load_labels(a.labels, {u["cid"] for u in tv})
    y_tv = labels_vec(tv, lab_tv)
    for lam in LAMBDAS:
        mv = refit_variant(tv, y_tv, lam, lam)
        d = (logloss(y[col], mv["M1"].predict(design([te[i] for i in col], "M1")))
             - logloss(y[col], mv["M3"].predict(design([te[i] for i in col], "M3"))))
        sens[f"lambda_{lam}"] = event_boot(d, [te[i]["event_id"] for i in col], f"TEST|sens|lam{lam}", B_SENS)
    for g, cols in M3_GROUPS.items():
        mv = refit_variant(tv, y_tv, mtv["lambda"]["M1"], mtv["lambda"]["M3"], drop3=cols)
        d = (logloss(y[col], models["M1"].predict(design([te[i] for i in col], "M1")))
             - logloss(y[col], mv["M3"].predict(design([te[i] for i in col], "M3", drop=cols))))
        sens[f"leave_out_{g}"] = event_boot(d, [te[i]["event_id"] for i in col], f"TEST|sens|lofo{g}", B_SENS)
    sens["event_only_vs_twoway_T1"] = {"p_event": tests["T1"].get("p_event"),
                                       "p_twoway": (tests["T1"].get("twoway") or {}).get("p")}
    spath = os.path.join(a.out, "sensitivity_test.json")
    write(spath, sens)
    for name, v in sens.items():
        if "stat" in v:
            reg(f"TEST_sens_{name}", False, v, spath, ncomp=1,
                note="sensitivity of T1, reported, never used to choose")
    return {k: {kk: v.get(kk) for kk in ("n_units", "stat", "p", "p_holm", "upper95_one_sided", "status")}
            for k, v in tests.items()}


def stage_nullgate(a, units, fund):
    path = os.path.join(a.out, "nullgate.json")
    if os.path.exists(path):
        raise SystemExit("null gate already computed: refused")
    mtv = json.load(open(os.path.join(a.out, "models_trainvalid.json")))
    models = {m: Logit.from_json(d) for m, d in mtv["models"].items() if m in ("M1", "M3")}
    te = eligible(units, "TEST")
    lab = load_labels(a.labels, {u["cid"] for u in te})

    def t1(us):
        idx = select(us, "COL")
        if not idx:
            return None
        yy = labels_vec([us[i] for i in idx], lab)
        X1 = design([us[i] for i in idx], "M1")
        X3 = design([us[i] for i in idx], "M3")
        return float((logloss(yy, models["M1"].predict(X1)) - logloss(yy, models["M3"].predict(X3))).mean())

    stats, obs_sub = [], []
    for pth in a.null_panel:
        st = json.load(open(os.path.join(os.path.dirname(pth), "stats.json")))
        skipped = {c for v in st.get("skipped_cids", {}).values() for c in v}
        nu = eligible(load_jsonl_gz(pth), "TEST")
        stats.append(t1(nu))
        obs_sub.append(t1([u for u in te if u["cid"] not in skipped]))
    obs = obs_sub[0] if obs_sub else None
    assert all(o == obs for o in obs_sub), "skipped markets differ between seeds"
    # a seed without any COL unit counts as a null at least as large as the observed (conservative)
    hits = sum(1 for s in stats if s is None or (obs is not None and s >= obs))
    p = (1 + hits) / (len(stats) + 1)
    out = {"observed_T1_same_markets": obs, "null_T1": stats, "K": len(stats), "p": p,
           "seeds_without_col": sum(1 for s in stats if s is None)}
    write(path, out)
    enregistrer(ETUDE, test="TEST_nullgate_T1", declare=True, n=len(stats), agent="mission5-ana50",
                stat=obs, p=p, n_tirages=len(stats), n_hits=hits, sortie=path)
    return out


def permute_labels(units, lab):
    """Negative control 2: each market gets one stratum (category, month of its first unit); labels are a
    deterministic permutation of the market labels inside each stratum (a bijection)."""
    first = {}
    for u in units:
        c = u["cid"]
        if c not in first or u["t"] < first[c][1]:
            first[c] = ((u["category"], u["t"] // (30 * 86400)), u["t"])
    groups = {}
    for c, (k, _) in first.items():
        groups.setdefault(k, []).append(c)
    perm = {}
    for k, cids in sorted(groups.items()):
        cids = sorted(cids)
        rot = sorted(cids, key=lambda c: hashlib.sha256(f"perm|{c}".encode()).hexdigest())
        for c, c2 in zip(cids, rot):
            perm[c] = lab[c2]
    return perm


def detection_rate(manifest_path, alerts_path):
    """Share of injected markets with an alert, on the injected side, containing >= 2 injected wallets and
    firing within 2 h after t0."""
    man = json.load(open(manifest_path))
    inj = man["injected_wallets"]
    hit = set()
    with gzip.open(alerts_path, "rt") as f:
        for l in f:
            al = json.loads(l)
            m = inj.get(al["cid"])
            if not m or al["side"] != m["side"] or not (m["t0"] <= al["t"] <= m["t0"] + 7200):
                continue
            if len(set(al["wallets"]) & set(m["wallets"])) >= 2:
                hit.add(al["cid"])
    return {"injected": len(inj), "detected": len(hit), "rate": len(hit) / len(inj) if inj else None}


def stage_controls(a, units, fund):
    """Mock split of TRAIN events; fit on mock-train, T1 and T4 (and T5 with funding) on mock-test, same p rule."""
    tr = eligible(units, "TRAIN")
    lab = load_labels(a.labels, {u["cid"] for u in tr})
    if a.permute_labels:
        lab = permute_labels(tr, lab)
    if a.funding_extra:
        fund = merge_funding(fund, a.funding_extra)
    mock = lambda u: "MTRAIN" if int(hashlib.sha256(f"mock|{u['event_id']}".encode()).hexdigest()[:8], 16) % 10 < 7 \
        else "MTEST"
    mt = [u for u in tr if mock(u) == "MTRAIN"]
    ms = [u for u in tr if mock(u) == "MTEST"]
    ym, ys = labels_vec(mt, lab), labels_vec(ms, lab)
    models, cv = fit_models(mt, ym, fund)
    only = ("T1", "T4", "T5") if fund is not None else ("T1", "T4")
    tests, _, _ = run_tests(ms, ys, models, fund, f"CTL|{a.tag}", only=only)
    det = detection_rate(a.inject_manifest, os.path.join(os.path.dirname(a.panel), "alerts.jsonl.gz")) \
        if a.inject_manifest else None
    path = os.path.join(a.out, f"controls_{a.tag}.json")
    write(path, {"tag": a.tag, "tests": tests, "lambda": {m: models[m].lam for m in models},
                 "n_mock_train": len(mt), "n_mock_test": len(ms), "detection": det,
                 "col_units_mock_test": len(select(ms, "COL"))})
    for k in tests:
        reg(f"CTL_{a.tag}_{k}", False, tests[k], path, donnees="synthetiques")
    return {k: {kk: tests[k].get(kk) for kk in ("n_units", "stat", "p", "status")} for k in tests} | {"det": det}


def verdict_from(valid, test, nullgate, controls):
    """Plan section 'Verdict, wording fixed now', applied mechanically. `controls` is the summary written by
    ctl_45_summary.py: {'passed': bool, 'null_T1_mean': float}."""
    t1 = test["T1"]
    out = {}
    bias = min(0.0, controls.get("null_T1_mean") or 0.0)   # negative = M3 overfits under no information
    if t1.get("status") == "IMPOSSIBLE":
        h1 = "IMPOSSIBLE"
    elif t1["rejected_holm"]:
        ok = (valid["T1"].get("stat") or 0) > 0 and nullgate["p"] <= 0.05 and controls["passed"]
        h1 = "SUPPORTED" if ok else "INCONSISTENT"
        out["supported_conditions"] = {"valid_T1_positive": (valid["T1"].get("stat") or 0) > 0,
                                       "nullgate_p_le_0.05": nullgate["p"] <= 0.05,
                                       "controls_passed": controls["passed"]}
    else:
        t4 = test["T4"]
        up1 = t1["upper95_one_sided"] - bias
        t4_ok = t4.get("status") != "IMPOSSIBLE" and t4["upper95_one_sided"] < SESOI_EXCESS
        h1 = "NEGATIVE_PRECISE" if (up1 < SESOI_LL and t4_ok) else "UNDERPOWERED"
        out["negative_precise_inputs"] = {"T1_upper95": t1["upper95_one_sided"], "null_bias": bias,
                                          "T1_upper95_bias_corrected": up1,
                                          "T4_upper95": t4.get("upper95_one_sided"), "T4_status": t4.get("status")}
    out["H1"] = h1
    for k in ("T2", "T5", "T6", "T7"):
        t = test[k]
        if t.get("status") == "IMPOSSIBLE":
            out[k] = "IMPOSSIBLE"
        elif t["rejected_holm"]:
            out[k] = "REJECTS_H0_AFTER_HOLM"
        else:
            out[k] = "NEGATIVE_PRECISE" if t["upper95_one_sided"] < SESOI_LL else "UNDERPOWERED"
    return out


def stage_verdict(a, units, fund):
    path = os.path.join(a.out, "verdict.json")
    if os.path.exists(path):
        raise SystemExit("verdict already written: refused")
    v = json.load(open(os.path.join(a.out, "results_valid.json")))["tests"]
    t = json.load(open(os.path.join(a.out, "results_test.json")))["tests"]
    ng = json.load(open(os.path.join(a.out, "nullgate.json")))
    ctl = json.load(open(a.controls_summary))
    out = verdict_from(v, t, ng, ctl)
    write(path, out)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("stage", choices=("train", "valid", "test", "nullgate", "controls", "verdict"))
    ap.add_argument("--panel", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--universe")
    ap.add_argument("--meta")
    ap.add_argument("--holdout")
    ap.add_argument("--funding")
    ap.add_argument("--funding-extra")
    ap.add_argument("--out", required=True)
    ap.add_argument("--null-panel", action="append", default=[])
    ap.add_argument("--tag", default="")
    ap.add_argument("--permute-labels", action="store_true")
    ap.add_argument("--inject-manifest")
    ap.add_argument("--controls-summary")
    a = ap.parse_args()
    units = load_jsonl_gz(a.panel) if a.stage != "verdict" else []
    fund = load_funding(a.funding)
    r = {"train": stage_train, "valid": stage_valid, "test": stage_test, "nullgate": stage_nullgate,
         "controls": stage_controls, "verdict": stage_verdict}[a.stage](a, units, fund)
    print(json.dumps(r, default=float)[:4000])


if __name__ == "__main__":
    main()
