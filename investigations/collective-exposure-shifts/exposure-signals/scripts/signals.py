#!/usr/bin/env python3
"""Collective exposure signals (mission 4/7). Deterministic. Reads fills through the point-in-time ledger of
mission 3 (position-ledger/scripts/ledger.py); never reads an outcome. This module must not open any label file.

Phase A, one market at a time (market_pass): for every 900 s grid time t, the window (t-W, t]. A wallet contributes
to side s when its directional exposure X = q(YES) - q(NO) moved toward s by >= min_change_shares over the window
AND the ledger classifies the move as a real change (classes C_*, NONE, UNKNOWN excluded). Everything uses only
fills with ts <= t (ledger snapshots, last executed price at or before t).

Phase B, all markets in time order (enrich_and_fire): features that need other markets (wallet habits, first-seen
age, group repetition, lead/follow, funding edges) use only data strictly before the candidate's window or time.
"""
import bisect
import hashlib
import json
import math
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
LEDGER_DIR = os.path.normpath(os.path.join(HERE, "..", "..", "position-ledger", "scripts"))
sys.path.insert(0, LEDGER_DIR)
import ledger as L  # noqa: E402

YES, NO = L.YES, L.NO
SIDES = ("YES", "NO")
FAMILIES = ("F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8")


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_params(path):
    with open(path) as f:
        P = json.load(f)
    P["infra"] = {a.lower() for a in P["infra"]}
    return P


def day_shift(seed, D):
    """Null model: shift each wallet's fills in one market by a whole number of days, circularly inside
    [first, first + D) with D a multiple of 86400. Keeps each wallet's sizes, sides, hour-of-day and its own
    spacing (except at the wrap); breaks the alignment between wallets."""
    days = D // 86400

    def f(wallet, cid, first, ts):
        h = int(hashlib.sha256(f"{seed}|{wallet}|{cid}".encode()).hexdigest()[:12], 16)
        off = (1 + h % (days - 1)) * 86400
        return first + (ts - first + off) % D
    return f


def dx_of(e):
    """Change of X = q(YES) - q(NO) caused by one fill."""
    s = 1.0 if e["kind"] == "BUY" else -1.0
    return s * e["qty"] if e["oi"] == YES else -s * e["qty"]


def market_pass(mk, rows, P, null_seed=None):
    """mk: sample row (condition_id, event_id, event_slug, closed_ts, yes_token, no_token, neg_risk).
    rows: tape rows (rowid, condition_id, ts, wallet, side, outcome, outcome_index, size, price, tx, token_id).
    Returns {"cid", "candidates", "pv", "grid", "wallet_hours", "wallet_first", "stats"}."""
    cid = mk["condition_id"].lower()
    W, G = P["window_s"], P["grid_s"]
    infra = P["infra"]
    stats = {"rows": len(rows), "skipped": None}
    if not rows:
        stats["skipped"] = "NO_FILLS"
        return {"cid": cid, "candidates": [], "pv": [], "grid": [], "wallet_hours": {}, "wallet_first": {},
                "stats": stats}
    first = min(r[2] for r in rows)
    if null_seed is not None:
        D = ((max(r[2] for r in rows) - first) // 86400 + 1) * 86400
        if D < 3 * 86400:
            stats["skipped"] = "NULL_LIFE_UNDER_3_DAYS"
            return {"cid": cid, "candidates": [], "pv": [], "grid": [], "wallet_hours": {}, "wallet_first": {},
                    "stats": stats}
        sh = day_shift(null_seed, D)
        rows = [(r[0], r[1], sh(r[3].lower(), cid, first, r[2])) + tuple(r[3:]) for r in rows]
    events = [L.make_event(ts, w, c, side, oi=int(oi), qty=size, price=price, tx=tx, seq=rowid,
                           src=f"tape#rowid={rowid}")
              for rowid, c, ts, w, side, oc, oi, size, price, tx, tok in rows]
    tok_of_row = {r[0]: r[10] for r in rows}
    info = {cid: {"history_complete": True, "neg_risk": mk.get("neg_risk"), "coverage": L.TAPE_COVERAGE,
                  "fees_enabled": None}}
    # a shifted tape no longer pairs both legs of a transaction in time: the tx check is meaningless there
    lg = L.Ledger(events, info, check_tx=null_seed is None)
    fam = L.family_binary(cid)
    evs = lg.events
    ets = [e["ts"] for e in evs]
    stats.update(events=len(evs), quarantined=len(lg.quarantine),
                 tx_unbalanced=sum(1 for v in lg.tx_verdicts.values() if v == "UNBALANCED"))

    pts, pps = ([], []), ([], [])
    for e in evs:
        if e["kind"] in L.TRADE_KINDS:
            pts[e["oi"]].append(e["ts"])
            pps[e["oi"]].append(e["price"])

    def price(oi, t):
        i = bisect.bisect_right(pts[oi], t) - 1
        return pps[oi][i] if i >= 0 else None

    def x_at(w, t):
        return lg.snapshot(w, cid, t)["observable"]["x_yes_equiv"]     # public API only: the engine evolves

    wallet_hours = defaultdict(set)
    wallet_first = {}
    for e in evs:
        wallet_hours[e["wallet"]].add(e["ts"] // 3600)
        if e["wallet"] not in wallet_first:
            wallet_first[e["wallet"]] = e["ts"]

    closed = mk.get("closed_ts") or (ets[-1] + W)
    g0 = -(-(ets[0] + P["warmup_s"]) // G)
    g1 = min(ets[-1] + W, closed) // G
    lo_b, hi_b = P["price_band"]
    tokens = (str(mk.get("yes_token") or ""), str(mk.get("no_token") or ""))
    # F8 running sums per side over prior grid points: n, sum dp*f, sum dp^2, sum f, sum f^2, sum dp
    f8 = [[0, 0.0, 0.0, 0.0, 0.0, 0.0] for _ in SIDES]
    pv_prior = []            # sorted nonzero window volumes of prior grid points
    pv_first = [None, None]
    candidates, grid = [], []
    excl = set(P["excluded_classes"])
    for g in range(g0, g1 + 1):
        t = g * G
        i0, i1 = bisect.bisect_right(ets, t - W), bisect.bisect_right(ets, t)
        win = evs[i0:i1]
        p_now = (price(YES, t), price(NO, t))
        p_prev = (price(YES, t - W), price(NO, t - W))
        grid.append((t, p_now[0], p_now[1]))
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
                    continue
                si = YES if d > 0 else NO
                v1 = r["evidence"]["v1"]
                contrib[si].append({"wallet": w, "net_change_shares": abs(d), "class": r["class"],
                                    "x_status": v1["status"], "reasons": v1["reasons"],
                                    "first_fill_ts": by_w[w][0]["ts"], "window_fills": len(by_w[w]),
                                    "market_first_ts": wallet_first[w],
                                    "txs": sorted({e["tx"] for e in by_w[w] if e["tx"]})})
        for si in (YES, NO):
            ps, pp = p_now[si], p_prev[si]
            flow = sum(c["net_change_shares"] for c in contrib[si])
            dp = (ps - pp) if ps is not None and pp is not None else None
            # F8 z from PRIOR grid points only, then update
            n, sdf, sdd, sf, sff, sd = f8[si]
            z = None
            if dp is not None and n >= P["F8"]["min_prior"] and sdd > 0:
                k = sdf / sdd
                mean_r = (sf - k * sd) / n
                var_r = (sff - 2 * k * sdf + k * k * sdd) / n - mean_r ** 2
                if var_r > 1e-12:
                    z = (flow - k * dp - mean_r) / math.sqrt(var_r)
            # PV baseline (price/volume only, no wallet information)
            if (pv_first[si] is None and ps is not None and dp is not None and lo_b <= ps <= hi_b
                    and len(pv_prior) >= P["PV"]["min_prior"] and dp >= P["PV"]["min_dp"]
                    and vol >= P["PV"]["vol_mult"] * pv_prior[len(pv_prior) // 2]):
                pv_first[si] = {"condition_id": cid, "event_id": str(mk.get("event_id")), "side": SIDES[si],
                                "token_id": tokens[si], "t": t, "available_ts": t + P["latency_s"],
                                "price_side": ps, "dp": dp, "window_volume": vol,
                                "median_prior_volume": pv_prior[len(pv_prior) // 2]}
            if len(contrib[si]) >= 2 and ps is not None and lo_b <= ps <= hi_b and t <= closed:
                cs = contrib[si]
                for c in cs:
                    c["net_change_usd"] = c["net_change_shares"] * ps
                cp = counterparties(win, cs, infra, {c["wallet"] for c in contrib[0] + contrib[1]})
                usd = [c["net_change_usd"] for c in cs]
                tot = sum(usd)
                candidates.append({
                    "condition_id": cid, "event_id": str(mk.get("event_id")), "event_slug": mk.get("event_slug"),
                    "side": SIDES[si], "token_id": tokens[si], "t": t, "window": [t - W, t],
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
        if vol > 0:
            bisect.insort(pv_prior, vol)
    stats["grid_points"] = len(grid)
    stats["candidates"] = len(candidates)
    return {"cid": cid, "candidates": candidates, "pv": [x for x in pv_first if x], "grid": grid,
            "wallet_hours": {w: sorted(h) for w, h in wallet_hours.items()}, "wallet_first": wallet_first,
            "stats": stats, "tokens_seen": sorted({str(v) for v in tok_of_row.values() if v})}


def counterparties(win, cs, infra, all_contrib):
    """Counterparties of the side's contributors inside the window: wallets whose X moved the opposite way in the
    same transaction. Infra contracts excluded. Returns concentration and the share traded among contributors."""
    tx_dx = defaultdict(lambda: defaultdict(float))
    for e in win:
        if e["tx"] and e["kind"] in L.TRADE_KINDS:
            tx_dx[e["tx"]][e["wallet"]] += dx_of(e)
    names = {c["wallet"] for c in cs}
    qty = defaultdict(float)
    for tx, m in tx_dx.items():
        for c in names & set(m):
            dc = m[c]
            if abs(dc) < L.EPS:
                continue
            for w2, d2 in m.items():
                if w2 != c and w2 not in infra and d2 * dc < 0:
                    qty[w2] += min(abs(dc), abs(d2))
    tot = sum(qty.values())
    if not tot:
        return {"n_counterparties": 0, "top_counterparty": None, "top_share": None, "internal_share": None}
    top = max(sorted(qty), key=lambda w: qty[w])
    return {"n_counterparties": len(qty), "top_counterparty": top, "top_share": qty[top] / tot,
            "internal_share": sum(v for w, v in qty.items() if w in all_contrib) / tot}


# ---------------------------------------------------------------------------------------------------------------
# Phase B
# ---------------------------------------------------------------------------------------------------------------

def build_index(results):
    """wallet -> (sorted active hours over all markets, first fill ts, sorted first-fill ts per market)."""
    hours, first, mfirst = defaultdict(set), {}, defaultdict(list)
    for r in results:
        for w, hs in r["wallet_hours"].items():
            hours[w].update(hs)
        for w, ts in r["wallet_first"].items():
            first[w] = min(first.get(w, ts), ts)
            mfirst[w].append(ts)
    return {w: (sorted(hours[w]), first[w], sorted(mfirst[w])) for w in hours}


def load_edges(path):
    """Funding edges: JSONL {from, to, ts, tx, source, kind}. Only kind == 'direct_transfer' with a tx hash is kept;
    anything labelled exchange / bridge / hot_wallet / technical is dropped at load. None if no file."""
    if not path:
        return None
    out = defaultdict(list)
    with open(path) as f:
        for line in f:
            e = json.loads(line)
            if e.get("kind") != "direct_transfer" or not e.get("tx"):
                continue
            a, b = e["from"].lower(), e["to"].lower()
            out[frozenset((a, b))].append(int(e["ts"]))
    return {k: sorted(v) for k, v in out.items()}


def enrich_and_fire(candidates, index, P, edges=None, infra=frozenset()):
    """Adds F3-F7 features (strictly prior information) and fires. Returns alerts sorted by (t, cid, side)."""
    W = P["window_s"]
    cands = sorted(candidates, key=lambda c: (c["t"], c["condition_id"], c["side"]))
    pair_ev = defaultdict(set)       # frozenset(w1,w2) -> event_ids where both contributed to one side
    lead_ev = defaultdict(set)       # (leader, follower) -> event_ids
    alerts, first_fire = [], set()
    i = 0
    while i < len(cands):
        j = i
        while j < len(cands) and cands[j]["t"] == cands[i]["t"]:
            j += 1
        batch = cands[i:j]
        for c in batch:
            t, ev = c["t"], c["event_id"]
            h0 = (t - W) // 3600
            ws = [x["wallet"] for x in c["contributors"]]
            sur, ages, prior_m = [], [], []
            for x in c["contributors"]:
                hs, fts, mf = index.get(x["wallet"], ([], t, []))
                a = bisect.bisect_left(hs, h0)
                span = max(0, h0 - hs[0]) if hs else 0
                r = (a + 1) / (span + 2)
                x["habit_active_hours_before"] = a
                x["habit_hours_observed"] = span
                x["sync_surprise"] = -math.log(r)
                x["first_seen_ts"] = fts
                x["age_days"] = (t - fts) / 86400
                # other markets entered before the window opens
                x["prior_markets"] = bisect.bisect_left(mf, t - W) - (1 if x["market_first_ts"] < t - W else 0)
                sur.append(x["sync_surprise"])
                ages.append(x["age_days"])
                prior_m.append(x["prior_markets"])
            c["F3"] = {"mean_surprise": sum(sur) / len(sur), "min_surprise": min(sur)}
            c["F4"] = {"median_age_days": sorted(ages)[len(ages) // 2],
                       "young_share": sum(1 for a in ages if a < P["F4"]["young_days"]) / len(ages),
                       "median_prior_markets": sorted(prior_m)[len(prior_m) // 2]}
            pairs = [frozenset((a, b)) for k, a in enumerate(ws) for b in ws[k + 1:]]
            rep = [len(pair_ev[p] - {ev}) for p in pairs]
            c["F5"] = {"repeat_pairs": sum(1 for v in rep if v > 0), "max_other_events": max(rep) if rep else 0,
                       "pairs": len(pairs)}
            lw = P["F7"]["lead_window_s"]
            fts = {x["wallet"]: x["first_fill_ts"] for x in c["contributors"]}
            leads = [(a, b) for a in ws for b in ws if a != b and 0 < fts[b] - fts[a] <= lw]
            c["_leads"] = leads
            c["F7"] = dict(c.pop("F7a"), lead_pairs=len(leads),
                           lead_repeats=sum(1 for lp in leads if lead_ev[lp] - {ev}))
            if edges is None:
                c["F6"] = {"status": "NOT_COLLECTED", "linked_pairs": None}
            else:
                lp = 0
                for p in pairs:
                    if p & infra:
                        continue
                    ts_list = edges.get(p, [])
                    if ts_list and ts_list[0] < t - W:      # payment strictly before the window opens
                        lp += 1
                c["F6"] = {"status": "COLLECTED", "linked_pairs": lp}
            fire(c, P)
            for f in c["families_fired"]:
                key = (c["condition_id"], c["side"], f)
                if key not in first_fire:
                    first_fire.add(key)
                    c["primary_for"].append(f)
            if c["families_fired"]:
                alerts.append(c)
        # only after the whole batch at t: candidates at the same t never see each other
        for c in batch:
            ws = [x["wallet"] for x in c["contributors"]]
            for k, a in enumerate(ws):
                for b in ws[k + 1:]:
                    pair_ev[frozenset((a, b))].add(c["event_id"])
            for lp in c.pop("_leads"):
                lead_ev[lp].add(c["event_id"])
        i = j
    return alerts


def fire(c, P):
    n = c["F1"]["n_wallets"]
    fired, why = [], []
    if n >= P["F1"]["min_wallets"]:
        fired.append("F1"); why.append(f"F1: {n} wallets >= {P['F1']['min_wallets']}")
    f2 = c["F2"]
    if n >= P["F2"]["min_wallets"] and f2["total_usd"] >= P["F2"]["min_usd"] and \
            f2["top_share"] <= P["F2"]["max_top_share"]:
        fired.append("F2"); why.append(f"F2: {f2['total_usd']:.0f} USD, top share {f2['top_share']:.2f}")
    if n >= P["F3"]["min_wallets"] and c["F3"]["mean_surprise"] >= P["F3"]["min_mean_surprise"]:
        fired.append("F3"); why.append(f"F3: mean habit surprise {c['F3']['mean_surprise']:.2f}")
    if n >= P["F4"]["min_wallets"] and c["F4"]["young_share"] >= P["F4"]["min_young_share"]:
        fired.append("F4"); why.append(f"F4: young share {c['F4']['young_share']:.2f}")
    if n >= P["F5"]["min_wallets"] and c["F5"]["repeat_pairs"] >= P["F5"]["min_repeat_pairs"]:
        fired.append("F5"); why.append(f"F5: {c['F5']['repeat_pairs']} pairs seen together in other events")
    if n >= P["F6"]["min_wallets"] and (c["F6"]["linked_pairs"] or 0) >= P["F6"]["min_linked_pairs"]:
        fired.append("F6"); why.append(f"F6: {c['F6']['linked_pairs']} funded pairs before the window")
    f7 = c["F7"]
    if n >= P["F7"]["min_wallets"] and f7["lead_repeats"] >= P["F7"]["min_lead_repeats"] and \
            (f7["internal_share"] is None or f7["internal_share"] < P["F7"]["max_internal_share"]):
        fired.append("F7"); why.append(f"F7: {f7['lead_repeats']} repeated lead/follow pairs")
    z = c["F8"]["z"]
    if n >= P["F8"]["min_wallets"] and z is not None and z >= P["F8"]["min_z"]:
        fired.append("F8"); why.append(f"F8: flow z {z:.2f} after the price-move fit")
    c["families_fired"], c["reasons"], c["score"] = fired, why, len(fired)
    c["primary_for"] = []
    c["alert_id"] = hashlib.sha256(f"{c['condition_id']}|{c['side']}|{c['t']}".encode()).hexdigest()[:20]
