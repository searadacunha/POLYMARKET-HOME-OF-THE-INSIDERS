#!/usr/bin/env python3
"""Mission 5: run the mission 4 detector on one global pool and build the evaluation panel. Never reads a label.

Phase A (per market, parallel): `market_pass_m5` is a line-for-line copy of mission 4 `signals.market_pass`
(sha256 914f59c8...) with additions only:
  * per-grid public-market features (fills, distinct wallets, volume share of the last 900 s, cumulative volume,
    4 h price move) and individual-shift features (largest single contributor, IND flag), stored only at grid
    points that can become units (candidates, first PV and IND per side and period, hash-drawn R points);
  * the Iran cohort wallets are added to the infra set, so they never contribute nor count as counterparties.
  tests/test_feat.py checks that the candidates equal those of signals.market_pass on real tapes.
Phase B (global, time order): mission 4 `enrich_and_fire`, imported unchanged, on all candidates of the pool, with
a compact wallet index (same content as signals.build_index, stored as int arrays to fit in memory).
Panel: units R, PV, IND, COL as defined in analysis_plan.md, eligible only when the unit time lies in its market's
split window. Output: out/<tag>/panel.jsonl.gz, alerts.jsonl.gz, stats.json. No outcome field is read.

usage: feat_30_detect.py --tapes A.sqlite [...] --markets ROLE=PATH [...] --meta meta.jsonl --params params.json
                         --iran iran_cohort_wallets.json --out DIR [--workers 4] [--null-seed K --null-split TEST]
                         [--phase-a-cache DIR] [--inject inject.json] [--only-markets cids.txt]
"""
import argparse
import array
import bisect
import datetime as dt
import gzip
import hashlib
import json
import math
import multiprocessing as mp
import os
import pickle
import sqlite3
import sys
import time
import urllib.parse
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
STUDY = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(STUDY, "frozen_deps", "exposure-signals", "scripts"))
import signals as S  # noqa: E402  mission 4, unchanged

L = S.L
YES, NO = L.YES, L.NO
UTC = dt.timezone.utc


def _ep(*a):
    return int(dt.datetime(*a, tzinfo=UTC).timestamp())


WINDOWS = {"TRAIN": (_ep(2025, 1, 1), _ep(2025, 12, 31, 23, 59, 59)),
           "VALID": (_ep(2026, 1, 1), _ep(2026, 6, 30, 23, 59, 59)),
           "TEST": (_ep(2026, 7, 1), _ep(2026, 10, 31, 23, 59, 59))}
EVAL_SPLITS = ("TRAIN", "VALID", "TEST")
COL_FAMILIES = ("F1", "F2", "F3", "F4", "F5", "F7", "F8")
IND_MIN_USD = 3000.0
R_DEN = 384          # one R draw per 384 grid times (4 days of 900 s) on average
H4 = 4 * 3600


def period_of(t):
    for k, (lo, hi) in WINDOWS.items():
        if lo <= t <= hi:
            return k
    return None


def hnum(*parts):
    return int(hashlib.sha256("|".join(str(p) for p in parts).encode()).hexdigest()[:12], 16)


def sha256_file(p):
    return S.sha256_file(p)


# ------------------------------------------------------------------------------------------------ phase A
def market_pass_m5(mk, rows, P, null_seed=None):
    """Copy of signals.market_pass (mission 4). Lines marked `# m5` are additions; nothing else differs."""
    cid = mk["condition_id"].lower()
    W, G = P["window_s"], P["grid_s"]
    infra = P["infra"]
    stats = {"rows": len(rows), "skipped": None}
    empty = {"cid": cid, "candidates": [], "pv": [], "wallet_hours": {}, "wallet_first": {}, "stats": stats,
             "extras": {}}  # m5
    if not rows:
        stats["skipped"] = "NO_FILLS"
        return empty
    first = min(r[2] for r in rows)
    if null_seed is not None:
        D = ((max(r[2] for r in rows) - first) // 86400 + 1) * 86400
        if D < 3 * 86400:
            stats["skipped"] = "NULL_LIFE_UNDER_3_DAYS"
            return empty
        sh = S.day_shift(null_seed, D)
        rows = [(r[0], r[1], sh(r[3].lower(), cid, first, r[2])) + tuple(r[3:]) for r in rows]
    events = [L.make_event(ts, w, c, side, oi=int(oi), qty=size, price=price, tx=tx, seq=rowid,
                           src=f"tape#rowid={rowid}")
              for rowid, c, ts, w, side, oc, oi, size, price, tx, tok in rows]
    info = {cid: {"history_complete": True, "neg_risk": mk.get("neg_risk"), "coverage": L.TAPE_COVERAGE,
                  "fees_enabled": None}}
    lg = L.Ledger(events, info, check_tx=null_seed is None)
    fam = L.family_binary(cid)
    evs = lg.events
    ets = [e["ts"] for e in evs]
    stats.update(events=len(evs), quarantined=len(lg.quarantine),
                 tx_unbalanced=sum(1 for v in lg.tx_verdicts.values() if v == "UNBALANCED"))
    if not evs:  # m5: every row quarantined
        stats["skipped"] = "NO_EVENTS"
        return empty

    pts, pps = ([], []), ([], [])
    for e in evs:
        if e["kind"] in L.TRADE_KINDS:
            pts[e["oi"]].append(e["ts"])
            pps[e["oi"]].append(e["price"])

    def price(oi, t):
        i = bisect.bisect_right(pts[oi], t) - 1
        return pps[oi][i] if i >= 0 else None

    def x_at(w, t):
        return lg.snapshot(w, cid, t)["observable"]["x_yes_equiv"]

    wallet_hours = defaultdict(set)
    wallet_first = {}
    for e in evs:
        wallet_hours[e["wallet"]].add(e["ts"] // 3600)
        if e["wallet"] not in wallet_first:
            wallet_first[e["wallet"]] = e["ts"]

    # m5: cumulative traded notional, for liquidity up to t
    cum = []
    run = 0.0
    for e in evs:
        if e["kind"] in L.TRADE_KINDS:
            run += e["qty"] * e["price"]
        cum.append(run)

    closed = mk.get("closed_ts") or (ets[-1] + W)
    g0 = -(-(ets[0] + P["warmup_s"]) // G)
    g1 = min(ets[-1] + W, closed) // G
    lo_b, hi_b = P["price_band"]
    tokens = (str(mk.get("yes_token") or ""), str(mk.get("no_token") or ""))
    f8 = [[0, 0.0, 0.0, 0.0, 0.0, 0.0] for _ in S.SIDES]
    pv_prior = []
    pv_first = [None, None]
    candidates = []
    excl = set(P["excluded_classes"])

    # m5: R points, one Bernoulli(1/R_DEN) draw per grid time by hash of (cid, t): the chance that an open
    # grid time becomes a unit does not depend on the market's (future) length of life. Side drawn by hash.
    r_points = {}
    for g in range(g0, g1 + 1):
        if period_of(g * G) and hnum(cid, g * G, "R") % R_DEN == 0:
            r_points[g * G] = hnum(cid, g * G, "side") % 2
    first_flag = {}   # m5: (kind, side, period) -> t of first PV / IND
    excluded_moves = defaultdict(int)  # m5: moves >= min_change dropped by ledger class (UNKNOWN, C_*, NONE)
    extras = {}       # m5: t -> per-grid features (only at possible unit times)

    for g in range(g0, g1 + 1):
        t = g * G
        i0, i1 = bisect.bisect_right(ets, t - W), bisect.bisect_right(ets, t)
        win = evs[i0:i1]
        p_now = (price(YES, t), price(NO, t))
        p_prev = (price(YES, t - W), price(NO, t - W))
        vol = sum(e["qty"] * e["price"] for e in win if e["kind"] in L.TRADE_KINDS)
        contrib = ([], [])
        if win:
            by_w = defaultdict(list)
            for e in win:
                by_w[e["wallet"]].append(e)
            for w in sorted(by_w):
                if w in infra:
                    continue
                d = x_at(w, t) - x_at(w, t - W)
                if abs(d) < P["min_change_shares"]:
                    continue
                r = L.classify(lg, w, fam, t - W, t)
                if r["class"] in excl:
                    excluded_moves[r["class"]] += 1   # m5: counted, reported in stats
                    continue
                si = YES if d > 0 else NO
                v1 = r["evidence"]["v1"]
                contrib[si].append({"wallet": w, "net_change_shares": abs(d), "class": r["class"],
                                    "x_status": v1["status"], "reasons": v1["reasons"],
                                    "first_fill_ts": by_w[w][0]["ts"], "window_fills": len(by_w[w]),
                                    "market_first_ts": wallet_first[w],
                                    "txs": sorted({e["tx"] for e in by_w[w] if e["tx"]})})
        med_prior = pv_prior[len(pv_prior) // 2] if pv_prior else None   # m5: before this window is added
        per = period_of(t)                                                # m5
        pv_now, ind_now, has_cand = [False, False], [False, False], [False, False]  # m5
        for si in (YES, NO):
            ps, pp = p_now[si], p_prev[si]
            flow = sum(c["net_change_shares"] for c in contrib[si])
            dp = (ps - pp) if ps is not None and pp is not None else None
            n, sdf, sdd, sf, sff, sd = f8[si]
            z = None
            if dp is not None and n >= P["F8"]["min_prior"] and sdd > 0:
                k = sdf / sdd
                mean_r = (sf - k * sd) / n
                var_r = (sff - 2 * k * sdf + k * k * sdd) / n - mean_r ** 2
                if var_r > 1e-12:
                    z = (flow - k * dp - mean_r) / math.sqrt(var_r)
            pv_cond = (ps is not None and dp is not None and lo_b <= ps <= hi_b
                       and len(pv_prior) >= P["PV"]["min_prior"] and dp >= P["PV"]["min_dp"]
                       and vol >= P["PV"]["vol_mult"] * pv_prior[len(pv_prior) // 2])
            if pv_first[si] is None and pv_cond:
                pv_first[si] = {"condition_id": cid, "event_id": str(mk.get("event_id")), "side": S.SIDES[si],
                                "token_id": tokens[si], "t": t, "available_ts": t + P["latency_s"],
                                "price_side": ps, "dp": dp, "window_volume": vol,
                                "median_prior_volume": pv_prior[len(pv_prior) // 2]}
            pv_now[si] = bool(pv_cond) and t <= closed                                        # m5
            ind_now[si] = (len(contrib[si]) == 1 and ps is not None and lo_b <= ps <= hi_b and t <= closed
                           and contrib[si][0]["net_change_shares"] * ps >= IND_MIN_USD)       # m5
            if len(contrib[si]) >= 2 and ps is not None and lo_b <= ps <= hi_b and t <= closed:
                has_cand[si] = True                                                          # m5
                cs = contrib[si]
                for c in cs:
                    c["net_change_usd"] = c["net_change_shares"] * ps
                cp = S.counterparties(win, cs, infra, {c["wallet"] for c in contrib[0] + contrib[1]})
                usd = [c["net_change_usd"] for c in cs]
                tot = sum(usd)
                candidates.append({
                    "condition_id": cid, "event_id": str(mk.get("event_id")), "event_slug": mk.get("event_slug"),
                    "side": S.SIDES[si], "token_id": tokens[si], "t": t, "window": [t - W, t],
                    "available_ts": t + P["latency_s"], "price_side": ps, "price_side_prev": pp,
                    "contributors": cs,
                    "F1": {"n_wallets": len(cs)},
                    "F2": {"total_usd": tot, "top_share": max(usd) / tot if tot else None,
                           "hhi": sum((u / tot) ** 2 for u in usd) if tot else None},
                    "F7a": cp,
                    "F8": {"flow_shares": flow, "dp": dp, "z": z, "prior_points": n},
                })
            if dp is not None:
                f8[si] = [n + 1, sdf + dp * flow, sdd + dp * dp, sf + flow, sff + flow * flow, sd + dp]
        # m5: decide whether this grid time can become a unit, then store its features
        keep = has_cand[0] or has_cand[1] or t in r_points
        if per:
            for si in (YES, NO):
                for kind, flag in (("PV", pv_now[si]), ("IND", ind_now[si])):
                    key = (kind, si, per)
                    if flag and key not in first_flag:
                        first_flag[key] = t
                        keep = True
        if keep:
            trades = [e for e in win if e["kind"] in L.TRADE_KINDS]
            last = sum(e["qty"] * e["price"] for e in trades if e["ts"] > t - G)
            p4 = (price(YES, t - H4), price(NO, t - H4))

            def mx(si):
                return max((c["net_change_shares"] * p_now[si] for c in contrib[si]), default=0.0) \
                    if p_now[si] is not None else 0.0
            extras[t] = {
                "t": t, "period": per,
                "p": list(p_now), "p_prev": list(p_prev),
                "dp4h": [(p_now[s] - p4[s]) if p_now[s] is not None and p4[s] is not None else None
                         for s in (YES, NO)],
                "vol": vol, "vol_ratio": (vol / med_prior) if med_prior else None,
                "n_fills": len(trades), "n_wallets": len({e["wallet"] for e in trades}),
                "last_share": (last / vol) if vol > 0 else 0.0,
                "cumvol": cum[i1 - 1] if i1 > 0 else 0.0,
                "age_h": (t - ets[0]) / 3600.0,
                "max1_usd": [mx(YES), mx(NO)],
                "ncontrib": [len(contrib[YES]), len(contrib[NO])],
                "pv": pv_now, "ind": ind_now,
                "r_side": r_points.get(t),
                "single": [contrib[s][0]["wallet"] if len(contrib[s]) == 1 else None for s in (YES, NO)],
            }
        if vol > 0:
            bisect.insort(pv_prior, vol)
    stats["grid_points"] = g1 - g0 + 1
    stats["candidates"] = len(candidates)
    stats["excluded_moves"] = dict(excluded_moves)
    return {"cid": cid, "candidates": candidates, "pv": [x for x in pv_first if x],
            "wallet_hours": {w: sorted(h) for w, h in wallet_hours.items()}, "wallet_first": wallet_first,
            "stats": stats, "extras": extras,
            "first_flag": {f"{k[0]}|{k[1]}|{k[2]}": v for k, v in first_flag.items()}}


# ------------------------------------------------------------------------------------------------ workers
_CTX = {}


def open_ro(path):
    return sqlite3.connect(f"file:{urllib.parse.quote(os.path.abspath(path))}?mode=ro&immutable=1", uri=True)


def _init(tapes, P, seed, null_cids, inject):
    _CTX["cons"] = {p: open_ro(p) for p in tapes}
    _CTX["P"], _CTX["seed"], _CTX["null_cids"], _CTX["inject"] = P, seed, null_cids, inject


def _work(job):
    mk, tape = job
    cid = mk["condition_id"]
    rows = _CTX["cons"][tape].execute(
        "select rowid, condition_id, ts, wallet, side, outcome, outcome_index, size, price, tx, token_id "
        "from trades where condition_id=? order by ts, rowid", (cid,)).fetchall()
    extra = (_CTX["inject"] or {}).get(cid.lower())
    if extra:  # synthetic rows of the positive controls (TRAIN only, never on real runs)
        rows = sorted(rows + [tuple(r) for r in extra], key=lambda r: (r[2], r[0]))
    seed = _CTX["seed"] if cid.lower() in _CTX["null_cids"] else None
    r = market_pass_m5(mk, rows, _CTX["P"], null_seed=seed)
    r["stats"]["tape"] = os.path.basename(tape)
    return r


# ------------------------------------------------------------------------------------------------ phase B
def build_index_compact(results_iter):
    """Same content as signals.build_index, stored in int arrays (memory)."""
    hours, first, mfirst = defaultdict(lambda: array.array("q")), {}, defaultdict(lambda: array.array("q"))
    for wh, wf in results_iter:
        for w, hs in wh.items():
            hours[w].extend(hs)
        for w, ts in wf.items():
            first[w] = min(first.get(w, ts), ts)
            mfirst[w].append(ts)
    out = {}
    for w in list(hours):
        hs = array.array("q", sorted(set(hours.pop(w))))
        out[w] = (hs, first[w], array.array("q", sorted(mfirst.pop(w))))
    return out


# ------------------------------------------------------------------------------------------------ panel
def category(tags):
    t = {x.lower() for x in (tags or [])}
    order = (("politics", {"politics", "elections", "us-politics", "global-elections", "trump", "congress"}),
             ("sports", {"sports", "soccer", "nba", "nfl", "mlb", "nhl", "tennis", "golf", "ufc", "boxing",
                         "f1", "cricket", "mma", "football", "basketball", "baseball", "hockey"}),
             ("crypto", {"crypto", "bitcoin", "ethereum", "solana", "airdrops", "stablecoins"}),
             ("culture", {"pop-culture", "culture", "movies", "music", "awards", "celebrities", "entertainment",
                          "tv", "oscars", "grammys"}),
             ("economy", {"economy", "business", "finance", "fed", "stocks", "inflation", "earnings",
                          "economics", "tech-stocks", "ipos", "commodities"}),
             ("world", {"world", "geopolitics", "middle-east", "ukraine", "russia", "china", "israel",
                        "iran", "war", "world-affairs", "foreign-policy"}),
             ("science", {"science", "tech", "ai", "space", "openai", "technology", "climate", "health"}))
    for name, keys in order:
        if t & keys:
            return name
    return "other"


def side_feats(c):
    """Collective features of one candidate (after enrich), 0 when absent."""
    if not c:
        return {"n": 0, "usd": 0.0, "top": 0.0, "f3": 0.0, "f4": 0.0, "f5": 0, "f7": 0, "f8": 0.0, "score": 0,
                "col": 0, "families": [], "wallets": []}
    z = c["F8"]["z"]
    fams = [f for f in c.get("families_fired", []) if f in COL_FAMILIES]
    return {"n": c["F1"]["n_wallets"], "usd": c["F2"]["total_usd"], "top": c["F2"]["top_share"] or 0.0,
            "f3": c["F3"]["mean_surprise"], "f4": c["F4"]["young_share"], "f5": int(c["F5"]["repeat_pairs"] > 0),
            "f7": int(c["F7"]["lead_repeats"] > 0), "f8": max(-5.0, min(5.0, z)) if z is not None else 0.0,
            "score": len(fams), "col": int(bool(fams)), "families": fams,
            "wallets": [x["wallet"] for x in c["contributors"]]}


def build_panel(markets, extras_by_cid, first_flags, cands_by_key, meta):
    """Units R, PV, IND, COL. Returns (units, counts)."""
    units, cnt = {}, defaultdict(int)
    col_first = {}
    for (cid, side, t), c in cands_by_key.items():
        fams = [f for f in c.get("families_fired", []) if f in COL_FAMILIES]
        mk = markets.get(cid)
        if not fams or not mk or mk["role"] not in EVAL_SPLITS or period_of(t) != mk["role"]:
            continue
        k = (cid, side)
        if k not in col_first or t < col_first[k]:
            col_first[k] = t
    for cid, mk in markets.items():
        split = mk["role"]
        if split not in EVAL_SPLITS:
            continue
        ex = extras_by_cid.get(cid) or {}
        ff = first_flags.get(cid) or {}
        want = defaultdict(set)   # (side, t) -> types
        for t, row in ex.items():
            if row["r_side"] is not None and row["period"] == split:
                want[(row["r_side"], t)].add("R")
        for key, t in ff.items():
            kind, si, per = key.split("|")
            if per == split:
                want[(int(si), t)].add(kind)
        for si in (YES, NO):
            if (cid, S.SIDES[si]) in col_first:
                want[(si, col_first[(cid, S.SIDES[si])])].add("COL")
        for (si, t), types in want.items():
            row = ex.get(t)
            if row is None:
                cnt["dropped_no_extras_row"] += 1
                continue
            ps = row["p"][si]
            if ps is None or not (0.05 <= ps <= 0.90):
                cnt["dropped_price_out_of_band_or_unknown"] += 1
                continue
            o = 1 - si
            cs = side_feats(cands_by_key.get((cid, S.SIDES[si], t)))
            co = side_feats(cands_by_key.get((cid, S.SIDES[o], t)))
            m = meta.get(cid) or {}
            end = m.get("end_ts")
            u = {"cid": cid, "event_id": str(mk["event_id"]), "split": split, "side": S.SIDES[si], "t": t,
                 "types": sorted(types), "p": ps, "category": category(mk.get("tags")),
                 "neg_risk": bool(mk.get("neg_risk")),
                 "pub": {"vol": row["vol"], "vol_ratio": row["vol_ratio"],
                         "dp": (ps - row["p_prev"][si]) if row["p_prev"][si] is not None else 0.0,
                         "dp4h": row["dp4h"][si] if row["dp4h"][si] is not None else 0.0,
                         "n_wallets": row["n_wallets"], "n_fills": row["n_fills"],
                         "last_share": row["last_share"], "age_h": row["age_h"], "cumvol": row["cumvol"],
                         "h_to_end": ((end - t) / 3600.0) if end else None, "pv": int(row["pv"][si])},
                 "ind": {"max1_s": row["max1_usd"][si], "max1_o": row["max1_usd"][o],
                         "ind_s": int(row["ind"][si]), "ind_o": int(row["ind"][o]),
                         "single_s": row["single"][si]},
                 "col_s": cs, "col_o": co}
            units[(cid, si, t)] = u
            for ty in types:
                cnt[f"units_{split}_{ty}"] += 1
    return sorted(units.values(), key=lambda u: (u["cid"], u["t"], u["side"])), dict(cnt)


# ------------------------------------------------------------------------------------------------ main
def load_markets(specs):
    """specs: ROLE=PATH; ROLE 'AUTO' assigns TRAIN/VALID/TEST by close time for TRAIN only and HISTORY otherwise
    (used for the h < 50 sample: its VALID/TEST markets were read in November and are history only)."""
    out = {}
    for spec in specs:
        role, path = spec.split("=", 1)
        for line in open(path):
            m = json.loads(line)
            cid = m["condition_id"].lower()
            if role == "AUTO":
                r = "TRAIN" if period_of(m["closed_ts"]) == "TRAIN" else "HISTORY"
            elif role == "SPLIT":
                r = m["split"]
            else:
                r = role
            if cid in out and out[cid]["role"] != r:
                raise SystemExit(f"market {cid} has two roles: {out[cid]['role']} and {r}")
            out[cid] = {**m, "condition_id": cid, "role": r}
    return out


def load_meta(path):
    meta = {}
    if not path:
        return meta
    for line in open(path):
        r = json.loads(line)
        end = None
        if r.get("status") == "ok" and r.get("endDate"):
            try:
                end = int(dt.datetime.fromisoformat(r["endDate"].replace("Z", "+00:00")).timestamp())
            except ValueError:
                end = None
        meta[r["condition_id"].lower()] = {"end_ts": end}
    return meta


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tapes", action="append", required=True)
    ap.add_argument("--markets", action="append", required=True)
    ap.add_argument("--meta")
    ap.add_argument("--params", required=True)
    ap.add_argument("--iran", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--null-seed", type=int)
    ap.add_argument("--null-split", default="TEST")
    ap.add_argument("--phase-a-cache")
    ap.add_argument("--inject")
    ap.add_argument("--only-markets")
    ap.add_argument("--only-roles", help="comma list, e.g. TRAIN (controls: TRAIN-only pool)")
    ap.add_argument("--allow-missing", action="store_true", help="warm-up only: tolerate markets without tape")
    a = ap.parse_args()
    t0 = time.time()
    os.makedirs(a.out, exist_ok=True)
    P = S.load_params(a.params)
    iran = {w.lower() for w in json.load(open(a.iran))["wallets"]}
    assert len(iran) == 36, len(iran)
    P["infra"] = set(P["infra"]) | iran
    markets = load_markets(a.markets)
    meta = load_meta(a.meta)
    if a.only_markets:
        keep = {l.strip().lower() for l in open(a.only_markets) if l.strip()}
        markets = {k: v for k, v in markets.items() if k in keep}
    if a.only_roles:
        roles = set(a.only_roles.split(","))
        markets = {k: v for k, v in markets.items() if v["role"] in roles}
    inject = json.load(open(a.inject)) if a.inject else None
    if inject:
        bad = [c for c in inject if markets.get(c, {}).get("role") != "TRAIN"]
        assert not bad, f"injection outside TRAIN refused: {bad[:3]}"
    null_cids = set()
    if a.null_seed is not None:
        null_cids = {c for c, m in markets.items() if m["role"] == a.null_split}

    # jobs: every market of the pool with a complete tape
    jobs, cov = [], defaultdict(int)
    seen = set()
    for tp in a.tapes:
        con = open_ro(tp)
        for cid, status in con.execute("select condition_id, status from status"):
            c = cid.lower()
            if c not in markets or c in seen:
                continue
            seen.add(c)
            cov[f"{markets[c]['role']}_{status}"] += 1
            if status == "ok":
                jobs.append(({**markets[c], "condition_id": cid}, tp))
        con.close()
    missing = [c for c in markets if c not in seen]
    for c in missing:
        cov[f"{markets[c]['role']}_no_tape"] += 1
    if missing and not a.allow_missing:
        raise SystemExit(f"{len(missing)} markets have no final tape status (collection unfinished?): refused")
    jobs.sort(key=lambda j: j[0]["condition_id"])

    # phase A, with an optional cache of unchanged markets (null runs re-run only the shifted split).
    # The cache holds only pickles written by this script on this machine (trusted, never downloaded).
    # It is keyed by the code, parameters, ledger, detector and Iran list, so any change invalidates it.
    cache = a.phase_a_cache
    if cache:
        key = hashlib.sha256("|".join([sha256_file(__file__), sha256_file(a.params), sha256_file(L.__file__),
                                       sha256_file(S.__file__), sha256_file(a.iran)]).encode()).hexdigest()[:16]
        cache = os.path.join(cache, key)
    results = []
    todo = []
    for j in jobs:
        c = j[0]["condition_id"].lower()
        f = os.path.join(cache, c + ".pkl") if cache else None
        reuse = cache and os.path.exists(f) and c not in null_cids and not (inject and c in inject)
        if reuse:
            with open(f, "rb") as fh:
                results.append(pickle.load(fh))
        else:
            todo.append(j)
    print(json.dumps({"markets": len(markets), "jobs": len(jobs), "phase_a_todo": len(todo),
                      "coverage": dict(cov)}), flush=True)
    with mp.get_context("spawn").Pool(a.workers, initializer=_init,
                                      initargs=(a.tapes, P, a.null_seed, null_cids, inject)) as pool:
        for k, r in enumerate(pool.imap_unordered(_work, todo, chunksize=4)):
            if cache and a.null_seed is None and not inject:
                os.makedirs(cache, exist_ok=True)
                with open(os.path.join(cache, r["cid"] + ".pkl"), "wb") as fh:
                    pickle.dump(r, fh, protocol=pickle.HIGHEST_PROTOCOL)
            results.append(r)
            if (k + 1) % 200 == 0:
                print(f"phase A {k + 1}/{len(todo)} {time.time() - t0:.0f}s", flush=True)

    # phase B
    index = build_index_compact((r["wallet_hours"], r["wallet_first"]) for r in results)
    cands = [c for r in results for c in r["candidates"]]
    alerts = S.enrich_and_fire(cands, index, P, edges=None, infra=P["infra"])
    cands_by_key = {(c["condition_id"].lower(), c["side"], c["t"]): c for c in cands}
    extras_by_cid = {r["cid"]: r["extras"] for r in results}
    first_flags = {r["cid"]: r.get("first_flag", {}) for r in results}
    units, ucnt = build_panel(markets, extras_by_cid, first_flags, cands_by_key, meta)

    with gzip.open(os.path.join(a.out, "panel.jsonl.gz"), "wt") as f:
        for u in units:
            f.write(json.dumps(u, sort_keys=True) + "\n")
    with gzip.open(os.path.join(a.out, "alerts.jsonl.gz"), "wt") as f:
        for c in alerts:
            m = markets.get(c["condition_id"].lower(), {})
            f.write(json.dumps({"alert_id": c["alert_id"], "cid": c["condition_id"].lower(),
                                "event_id": c["event_id"], "side": c["side"], "t": c["t"],
                                "role": m.get("role"), "families": c["families_fired"], "score": c["score"],
                                "wallets": [x["wallet"] for x in c["contributors"]],
                                "net_usd": [round(x["net_change_usd"], 2) for x in c["contributors"]],
                                "price_side": c["price_side"], "reasons": c["reasons"]}, sort_keys=True) + "\n")
    skipped, skipped_cids, excl = defaultdict(int), defaultdict(list), defaultdict(int)
    for r in results:
        if r["stats"]["skipped"]:
            skipped[r["stats"]["skipped"]] += 1
            skipped_cids[r["stats"]["skipped"]].append(r["cid"])
        for k, v in r["stats"].get("excluded_moves", {}).items():
            excl[k] += v
    end_known = sum(1 for u in units if u["pub"]["h_to_end"] is not None)
    stats = {"coverage": dict(cov), "phase_a_markets": len(results), "skipped": dict(skipped),
             "skipped_cids": {k: sorted(v) for k, v in skipped_cids.items()},
             "moves_excluded_by_ledger_class": dict(excl),
             "units_with_enddate_known": end_known,
             "candidates": len(cands), "alerts": len(alerts), "units": ucnt, "n_units": len(units),
             "null_seed": a.null_seed, "null_split": a.null_split if a.null_seed is not None else None,
             "injected_markets": len(inject or {}),
             "quarantined_rows": sum(r["stats"].get("quarantined", 0) for r in results),
             "tx_unbalanced": sum(r["stats"].get("tx_unbalanced", 0) for r in results),
             "inputs": {"signals.py": sha256_file(S.__file__), "ledger.py": sha256_file(L.__file__),
                        "params": sha256_file(a.params), "this": sha256_file(__file__),
                        "markets": {s: sha256_file(s.split("=", 1)[1]) for s in a.markets}},
             "seconds": round(time.time() - t0)}
    json.dump(stats, open(os.path.join(a.out, "stats.json"), "w"), indent=1, sort_keys=True)
    print(json.dumps({k: stats[k] for k in ("candidates", "alerts", "n_units", "units", "seconds")}), flush=True)


if __name__ == "__main__":
    main()
