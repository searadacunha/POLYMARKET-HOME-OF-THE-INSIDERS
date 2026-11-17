#!/usr/bin/env python3
"""Step 6: executable replay of the frozen S4 alerts, on the grid fixed in prereg/GRID.json.

Reads the frozen study read-only (detector code, scored alerts, statistics) and the trade tapes
read-only. Writes TRADE_REPLAY.csv, FALSE_POSITIVES.csv and EXECUTION_RESULTS.json in --out.
Historical order books are not archived: every execution here is HYPOTHETICAL (see fill_levels).
"""
import argparse, bisect, csv, hashlib, json, os, random, sqlite3, sys
from collections import defaultdict
from statistics import median

LAT = (60, 300, 900)
SIZES = (10.0, 100.0, 1000.0)
COSTS = {"optimistic": (0.0, 0.0), "politics": (0.04, 0.001), "stress": (0.07, 0.002)}
WINDOW = 900
K_CTRL = 5
SEED = 20261117
DRAWS = 2000
SPLIT_MONTHS = {"TRAIN": 12, "VALID": 6, "TEST": 4, "ALL": 22}   # plan's calendar splits
HEADLINE = ("causal", 300, 100.0, "politics", "TEST")


def tx_ask_levels(rows, side):
    """Ask levels for token `side` revealed by one transaction, or None if the taker is ambiguous.

    rows: [(ts, wallet, side, outcome, size, price)] of one tx. The taker is the unique row whose size
    equals the sum of the others (needs >= 3 rows). Maker SELL of `side` at p -> ask p; maker BUY of the
    complement at p' -> ask 1-p' (mint)."""
    if len(rows) < 3:
        return None
    tot = sum(r[4] for r in rows)
    takers = [i for i, r in enumerate(rows) if abs(2 * r[4] - tot) <= 1e-6 * max(1.0, r[4])]
    if len(takers) != 1:
        return None
    lv = []
    for i, (_, _, sd, oc, size, price) in enumerate(rows):
        if i == takers[0]:
            continue
        if oc == side and sd == "SELL":
            lv.append((price, size))
        elif oc != side and sd == "BUY":
            lv.append((round(1.0 - price, 10), size))
    return sorted(lv)


def fill(txs, side, start, usd):
    """Walk ask evidence from `start` for WINDOW seconds. txs: time-ordered [(ts, rows)].
    Returns dict(shares, cost, levels, ambiguous, first_ask, first_ask_ts, window_ask_usd)."""
    i = bisect.bisect_left([t for t, _ in txs], start)
    shares = cost = window_usd = 0.0
    used, amb, first, first_ts = [], 0, None, None
    for ts, rows in txs[i:]:
        if ts >= start + WINDOW:
            break
        lv = tx_ask_levels(rows, side)
        if lv is None:
            amb += 1
            continue
        for p, q in lv:
            if not (0.0 < p < 1.0):
                continue
            window_usd += p * q
            if first is None:
                first, first_ts = p, ts
            need = usd - cost
            if need <= 1e-9:
                continue
            take = min(q, need / p)
            shares += take
            cost += take * p
            used.append((ts, p, take))
    return dict(shares=shares, cost=cost, levels=used, ambiguous=amb, first_ask=first,
                first_ask_ts=first_ts, window_ask_usd=window_usd)


def pnl(f, win, cost_name):
    fee_rate, slip = COSTS[cost_name]
    fees = sum(q * fee_rate * p * (1 - p) for _, p, q in f["levels"])
    extra = f["shares"] * slip
    total_cost = f["cost"] + fees + extra
    return f["shares"] * win - total_cost, total_cost, fees + extra


def load_txs(con, cid):
    rows = con.execute("select ts, wallet, side, outcome, size, price, tx from trades "
                       "where condition_id=? order by ts, tx, wallet", (cid,)).fetchall()
    by = {}
    order = []
    for ts, w, sd, oc, size, price, tx in rows:
        if tx not in by:
            by[tx] = (ts, [])
            order.append(tx)
        by[tx][1].append((ts, w, sd, oc, size, price))
    txs = sorted((by[t] for t in order), key=lambda x: x[0])
    return [r[:6] for r in rows], txs


def side_price_series(rows, side):
    """Last executed price of `side` (complement converted), time-ordered."""
    ts, ps = [], []
    for t, _, _, oc, _, price in rows:
        ts.append(t)
        ps.append(price if oc == side else 1.0 - price)
    return ts, ps


def cluster_ci(units, seed):
    """units: [(event_id, pnl, cost)]; returns ratio pnl/cost and event-clustered 95% CI."""
    if not units:
        return None
    ev = defaultdict(lambda: [0.0, 0.0])
    for e, p, c in units:
        ev[e][0] += p
        ev[e][1] += c
    keys = sorted(ev)
    tp, tc = sum(ev[k][0] for k in keys), sum(ev[k][1] for k in keys)
    rng = random.Random(seed)
    stats = []
    for _ in range(DRAWS):
        p = c = 0.0
        for _ in keys:
            k = keys[rng.randrange(len(keys))]
            p += ev[k][0]
            c += ev[k][1]
        if c > 0:
            stats.append(p / c)
    stats.sort()
    return dict(per_usd=tp / tc if tc else None, lo=stats[int(0.025 * len(stats))] if stats else None,
                hi=stats[int(0.975 * len(stats)) - 1] if stats else None, events=len(keys))


def diff_ci(a, b, seed):
    """Event-clustered CI of (pnl/cost of a) - (pnl/cost of b); a, b: [(event, pnl, cost)]."""
    ev = defaultdict(lambda: [0.0, 0.0, 0.0, 0.0])
    for e, p, c in a:
        ev[e][0] += p; ev[e][1] += c
    for e, p, c in b:
        ev[e][2] += p; ev[e][3] += c
    keys = sorted(ev)
    def stat(ks):
        s = [sum(ev[k][j] for k in ks) for j in range(4)]
        return s[0] / s[1] - s[2] / s[3] if s[1] > 0 and s[3] > 0 else None
    point = stat(keys)
    rng = random.Random(seed)
    st = sorted(x for x in (stat([keys[rng.randrange(len(keys))] for _ in keys]) for _ in range(DRAWS))
                if x is not None)
    return dict(diff=point, lo=st[int(0.025 * len(st))] if st else None,
                hi=st[int(0.975 * len(st)) - 1] if st else None)


def max_drawdown(seq):
    peak = cum = dd = 0.0
    for x in seq:
        cum += x
        peak = max(peak, cum)
        dd = max(dd, peak - cum)
    return dd


def stats_gate(path):
    d = json.load(open(path))
    tests = d.get("tests", {})
    valid = [k for k, v in tests.items() if v.get("significant_bonferroni") and v.get("significant_bh")]
    return dict(file=path, sha256=hashlib.sha256(open(path, "rb").read()).hexdigest(),
                verdict=d.get("verdict"), supported_tests=valid, statistically_valid=bool(valid))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", required=True, help="frozen study dir (read only)")
    ap.add_argument("--tapes", required=True)
    ap.add_argument("--stats", required=True)
    ap.add_argument("--scored", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    sys.path.insert(0, os.path.join(a.study, "scripts"))
    import build_alerts as ba            # frozen detector, unmodified
    frozen_dedupe = ba.dedupe

    gate = stats_gate(a.stats)
    alerts = [json.loads(l) for l in open(a.scored)]
    alerts = [x for x in alerts if x["variant"] == "S4" and x.get("primary")]
    alerts.sort(key=lambda x: (x["t"], x["condition_id"], x["side"]))
    con = sqlite3.connect(f"file:{a.tapes}?mode=ro&immutable=1", uri=True)

    replay, ctrl_units, n_ctrl_alerts = [], defaultdict(list), 0
    cache = {}
    for idx, al in enumerate(alerts):
        cid, side = al["condition_id"], al["side"]
        if cid not in cache:
            rows, txs = load_txs(con, cid)
            meta = {k: al.get(k) for k in ("event_id", "event_slug", "closed_ts", "volume", "split")}
            ba.dedupe = lambda c: sorted(c, key=lambda x: x["t"])   # all candidates, no look-ahead
            cands, _ = ba.evaluate_market(cid, rows, meta)
            ba.dedupe = frozen_dedupe
            cache = {cid: (rows, txs, cands)}       # one market at a time keeps memory flat
        rows, txs, cands = cache[cid]
        s4 = sorted(c["t"] for c in cands if c["variant"] == "S4" and c["side"] == side)
        t_causal = s4[0] if s4 else None
        win = int(al["win"])
        base = dict(idx=idx, condition_id=cid, side=side, event_id=al["event_id"], split=al["split"],
                    alert_t=al["t"], causal_t=t_causal, alert_price=al["price"], win=win,
                    n_wallets=al["n_wallets"], total_usd=al["total_usd"],
                    frozen_t_reproduced=int(al["t"] in s4),
                    timing_non_causal=int(t_causal is not None and t_causal < al["t"]))
        for trig, t0 in (("causal", t_causal), ("frozen", al["t"])):
            for L in LAT:
                for usd in SIZES:
                    f = fill(txs, side, t0 + L, usd) if t0 is not None else None
                    for cn in COSTS:
                        r = dict(base, trigger=trig, trigger_t=t0, latency_s=L, size_usd=usd, costs=cn)
                        if f is None or f["shares"] <= 0:
                            r.update(status="NO_ASK_EVIDENCE" if f is not None else "NO_CAUSAL_CANDIDATE",
                                     shares=0, cost_usd=0, net_pnl_usd=0, fees_slip_usd=0)
                        else:
                            net, tc, fs = pnl(f, win, cn)
                            r.update(status="FULL" if f["cost"] >= usd - 1e-6 else "PARTIAL",
                                     shares=round(f["shares"], 6), cost_usd=round(tc, 6),
                                     net_pnl_usd=round(net, 6), fees_slip_usd=round(fs, 6),
                                     entry_vwap=round(f["cost"] / f["shares"], 6))
                        if f is not None:
                            r.update(first_ask=f["first_ask"], first_ask_delay_s=(
                                f["first_ask_ts"] - t0 if f["first_ask_ts"] else None),
                                window_ask_usd=round(f["window_ask_usd"], 2),
                                ambiguous_txs=f["ambiguous"])
                        r["execution"] = "HYPOTHETICAL_TAPE_EVIDENCE"
                        replay.append(r)
        # price-only control, same market and side, causal trigger only
        if t_causal is None:
            continue
        ts, ps = side_price_series(rows, side)
        first_ts = rows[0][0]
        grid = []
        g = (first_ts // 900 + 1) * 900
        end = (al["closed_ts"] or rows[-1][0])
        while g < end - max(LAT) - WINDOW:
            if g >= first_ts + 3600 and abs(g - t_causal) >= 6 * 3600:
                i = bisect.bisect_right(ts, g) - 1
                if i >= 0 and abs(ps[i] - al["price"]) <= 0.05:
                    grid.append(g)
            g += 900
        rng = random.Random(SEED + idx)
        picks = sorted(rng.sample(grid, min(K_CTRL, len(grid))))
        for g in picks:
            for L in LAT:
                for usd in SIZES:
                    f = fill(txs, side, g + L, usd)
                    for cn in COSTS:
                        if f["shares"] > 0:
                            net, tc, _ = pnl(f, win, cn)
                            ctrl_units[(L, usd, cn, al["split"])].append((al["event_id"], net, tc, idx))
        n_ctrl_alerts += bool(picks)

    os.makedirs(a.out, exist_ok=True)
    cols = sorted({k for r in replay for k in r})
    with open(os.path.join(a.out, "TRADE_REPLAY.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(replay)

    # false positives: alerts whose side lost, one row per alert, headline cell numbers
    hl = {(r["idx"]): r for r in replay if (r["trigger"], r["latency_s"], r["size_usd"], r["costs"]) ==
          HEADLINE[:4]}
    with open(os.path.join(a.out, "FALSE_POSITIVES.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["condition_id", "side", "event_id", "split", "alert_t", "causal_t", "alert_price",
                    "n_wallets", "total_usd", "headline_status", "headline_net_pnl_usd"])
        for al_idx, r in sorted(hl.items()):
            if r["win"] == 0:
                w.writerow([r["condition_id"], r["side"], r["event_id"], r["split"], r["alert_t"],
                            r["causal_t"], r["alert_price"], r["n_wallets"], r["total_usd"], r["status"],
                            r["net_pnl_usd"]])

    cells = []
    by = defaultdict(list)
    for r in replay:
        by[(r["trigger"], r["latency_s"], r["size_usd"], r["costs"], r["split"])].append(r)
        by[(r["trigger"], r["latency_s"], r["size_usd"], r["costs"], "ALL")].append(r)
    for key in sorted(by, key=str):
        rs = by[key]
        trig, L, usd, cn, split = key
        ex = [r for r in rs if r["shares"] > 0]
        units = [(r["event_id"], r["net_pnl_usd"], r["cost_usd"]) for r in ex]
        seq = [r["net_pnl_usd"] for r in sorted(ex, key=lambda r: r["trigger_t"])]
        cell = dict(trigger=trig, latency_s=L, size_usd=usd, costs=cn, split=split, n_alerts=len(rs),
                    n_full=sum(r["status"] == "FULL" for r in rs),
                    n_partial=sum(r["status"] == "PARTIAL" for r in rs),
                    n_no_evidence=sum(r["status"] in ("NO_ASK_EVIDENCE", "NO_CAUSAL_CANDIDATE") for r in rs),
                    cost_usd=round(sum(r["cost_usd"] for r in ex), 2),
                    net_pnl_usd=round(sum(r["net_pnl_usd"] for r in ex), 2),
                    max_drawdown_usd=round(max_drawdown(seq), 2),
                    alerts_per_month=round(len(rs) / SPLIT_MONTHS[split], 2),
                    median_window_ask_usd=(round(median(r["window_ask_usd"] for r in rs
                                                        if r.get("window_ask_usd") is not None), 2)
                                           if any(r.get("window_ask_usd") is not None for r in rs) else None),
                    median_entry_minus_alert_price=(round(median(r["entry_vwap"] - r["alert_price"]
                                                                 for r in ex), 5) if ex else None),
                    net_per_usd=cluster_ci(units, SEED))
        if trig == "causal":
            cu = ctrl_units.get((L, usd, cn, split)) if split != "ALL" else [
                u for s in ("TRAIN", "VALID", "TEST") for u in ctrl_units.get((L, usd, cn, s), [])]
            cu = cu or []
            cell["price_only_control"] = dict(n_trades=len(cu), net_per_usd=cluster_ci(
                [u[:3] for u in cu], SEED + 1))
            cell["s4_minus_control"] = diff_ci(units, [u[:3] for u in cu], SEED + 2) if units and cu else None
        cells.append(cell)

    head = next(c for c in cells if (c["trigger"], c["latency_s"], c["size_usd"], c["costs"], c["split"])
                == HEADLINE)
    if not gate["statistically_valid"]:
        verdict, why = "NO_DEMONSTRATED_EDGE", ("stop rule: no declared test of the input statistics passes "
                                               "Bonferroni and BH; the replay is descriptive only")
    else:
        verdict, why = "UNVERIFIABLE", "signal valid but no archived order book; prospective paper record needed"
    res = dict(grid_sha256=hashlib.sha256(open(os.path.join(os.path.dirname(a.out.rstrip("/")),
                                                            "prereg", "GRID.json"), "rb").read()).hexdigest(),
               stats_gate=gate, scored_sha256=hashlib.sha256(open(a.scored, "rb").read()).hexdigest(),
               n_alerts=len(alerts),
               n_frozen_t_reproduced=sum(r["frozen_t_reproduced"] for r in hl.values()), n_timing_non_causal=sum(1 for r in hl.values() if r["timing_non_causal"]),
               n_alerts_with_price_only_control=n_ctrl_alerts, n_no_causal_candidate=sum(1 for r in hl.values() if r["causal_t"] is None),
               historical_order_book="NOT_ARCHIVED", historical_execution="UNVERIFIABLE",
               simulations="HYPOTHETICAL_TAPE_EVIDENCE", headline_cell=head, verdict=verdict,
               verdict_reason=why, cells=cells)
    json.dump(res, open(os.path.join(a.out, "EXECUTION_RESULTS.json"), "w"), indent=1)
    print(json.dumps({k: res[k] for k in ("verdict", "n_alerts", "n_timing_non_causal",
                                          "n_no_causal_candidate")}, indent=1))


if __name__ == "__main__":
    main()
