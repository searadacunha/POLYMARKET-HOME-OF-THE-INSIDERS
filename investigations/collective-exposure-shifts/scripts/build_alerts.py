#!/usr/bin/env python3
"""Build exposure-shift signals from executed fills. Reads no outcome.

Inputs
  --tapes  SQLite produced by collect_tapes.py (trades + status)
  --universe JSON list of sampled markets (condition_id, events, volume, closed_ts)
  --split  JSON mapping condition_id -> TRAIN|VALID|TEST (written by split.py, outcome-free)

Output  results/alerts.jsonl : one row per evaluated candidate alert, with its signal family.

Position model (analysis_plan.md): q = net shares from fills; X = q(YES) - q(NO) (YES-share equivalents);
X_s = d_s * X with d_YES = +1, d_NO = -1; delta_s(w,t) = X_s(w,t) - X_s(w,t-W).
Splits, merges, redemptions and conversions are NOT fills and are not reconstructed (declared limit).
"""
import argparse, bisect, hashlib, json, os, sqlite3, sys, urllib.parse
from collections import defaultdict

W = 3600          # exposure-change window, seconds
GRID = 900        # candidate evaluation step, seconds
USD_MIN = 500.0   # per wallet
FRAC_MIN = 0.25   # change vs prior gross exposure
TOTAL_MIN = 3000.0
MIN_WALLETS = 3
MAX_SHARE = 0.60
P_LO, P_HI = 0.05, 0.90
WARMUP = 3600     # market needs one hour of history before any alert
BLOCK = 6 * 3600  # non-maximum suppression block per (market, side)


class WalletBook:
    """Cumulative YES-equivalent exposure and traded notional per wallet."""
    __slots__ = ("ts", "x", "qy", "qn", "gross", "buy", "sell")

    def __init__(self):
        self.ts, self.x, self.qy, self.qn, self.gross, self.buy, self.sell = [], [], [], [], [], [], []

    def at(self, arr, t):
        i = bisect.bisect_right(self.ts, t) - 1
        return arr[i] if i >= 0 else 0.0

    def window(self, t0, t1):
        """(gross, buy, sell, any_both) inside (t0, t1]."""
        lo = bisect.bisect_right(self.ts, t0)
        hi = bisect.bisect_right(self.ts, t1)
        if hi <= lo:
            return 0.0, 0.0, 0.0, False
        g = self.gross[hi - 1] - (self.gross[lo - 1] if lo else 0.0)
        b = self.buy[hi - 1] - (self.buy[lo - 1] if lo else 0.0)
        s = self.sell[hi - 1] - (self.sell[lo - 1] if lo else 0.0)
        return g, b, s, (b > 0 and s > 0)


def load_market(con, cid):
    rows = con.execute(
        "select ts, wallet, side, outcome, size, price from trades where condition_id=? "
        "order by ts, tx, wallet", (cid,)).fetchall()
    return rows


def build_books(rows):
    books = {}
    prices = {"Yes": ([], []), "No": ([], [])}
    for ts, w, side, oc, size, price in rows:
        b = books.get(w)
        if b is None:
            b = books[w] = WalletBook()
        d = size if side == "BUY" else -size
        dx = d if oc == "Yes" else -d          # YES-share equivalents
        notional = size * price
        b.ts.append(ts)
        b.x.append((b.x[-1] if b.x else 0.0) + dx)
        b.qy.append((b.qy[-1] if b.qy else 0.0) + (size if (oc == "Yes" and side == "BUY") else
                                                   -size if (oc == "Yes" and side == "SELL") else 0.0))
        b.qn.append((b.qn[-1] if b.qn else 0.0) + (size if (oc == "No" and side == "BUY") else
                                                   -size if (oc == "No" and side == "SELL") else 0.0))
        b.gross.append((b.gross[-1] if b.gross else 0.0) + notional)
        b.buy.append((b.buy[-1] if b.buy else 0.0) + (notional if side == "BUY" else 0.0))
        b.sell.append((b.sell[-1] if b.sell else 0.0) + (notional if side == "SELL" else 0.0))
        if oc in prices:
            pt, pp = prices[oc]
            if not pt or ts >= pt[-1]:
                pt.append(ts)
                pp.append(price)
    return books, prices


def price_at(prices, outcome, t):
    pt, pp = prices[outcome]
    i = bisect.bisect_right(pt, t) - 1
    return pp[i] if i >= 0 else None


def dedupe(cands):
    """Keep the largest total per (market, side) inside each BLOCK; input sorted by total desc."""
    kept = []
    for c in sorted(cands, key=lambda c: -c["total_usd"]):
        if all(not (k["side"] == c["side"] and abs(k["t"] - c["t"]) < BLOCK) for k in kept):
            kept.append(c)
    return kept


def evaluate_market(cid, rows, meta, params=None):
    p = dict(W=W, USD_MIN=USD_MIN, FRAC_MIN=FRAC_MIN, TOTAL_MIN=TOTAL_MIN, MIN_WALLETS=MIN_WALLETS,
             MAX_SHARE=MAX_SHARE, P_LO=P_LO, P_HI=P_HI)
    if params:
        p.update(params)
    if not rows:
        return [], {"condition_id": cid, "status": "no_fills"}
    books, prices = build_books(rows)
    first_ts, last_ts = rows[0][0], rows[-1][0]
    if last_ts - first_ts < p["W"] + WARMUP:
        return [], {"condition_id": cid, "status": "too_short"}

    buckets = sorted({ts // GRID for ts, *_ in rows})
    cand = {"Yes": [], "No": []}
    added = removed = 0        # two pointers over rows, which are time-ordered
    active = defaultdict(int)  # wallets holding at least one fill inside (t-W, t]
    n_rows = len(rows)
    for b in buckets:
        t = (b + 1) * GRID
        low = t - p["W"]
        while added < n_rows and rows[added][0] <= t:
            active[rows[added][1]] += 1
            added += 1
        while removed < added and rows[removed][0] <= low:
            w = rows[removed][1]
            active[w] -= 1
            if active[w] == 0:
                del active[w]
            removed += 1
        if t < first_ts + WARMUP + p["W"] or t > last_ts:
            continue
        py = price_at(prices, "Yes", t)
        pn = price_at(prices, "No", t)
        if py is None or pn is None:
            continue
        for side, d in (("Yes", 1.0), ("No", -1.0)):
            ps = py if side == "Yes" else pn
            if not (p["P_LO"] <= ps <= p["P_HI"]):
                continue
            qual = []
            buy_wallets, buy_usd = set(), 0.0
            for w in active:
                bk = books[w]
                b_win = bk.at(bk.buy, t) - bk.at(bk.buy, low)
                if b_win > 0:
                    buy_wallets.add(w)
                    buy_usd += b_win
                x_now = bk.at(bk.x, t)
                x_prev = bk.at(bk.x, low)
                if x_now == x_prev:
                    continue
                d_s = d * (x_now - x_prev)
                usd = d_s * ps
                if usd < p["USD_MIN"]:
                    continue
                g_prev = abs(bk.at(bk.qy, low)) * py + abs(bk.at(bk.qn, low)) * pn
                if g_prev >= p["USD_MIN"] and usd < p["FRAC_MIN"] * g_prev:
                    continue
                g_win = bk.at(bk.gross, t) - bk.at(bk.gross, low)
                s_win = bk.at(bk.sell, t) - bk.at(bk.sell, low)
                both = b_win > 0 and s_win > 0
                net_usd = abs(x_now - x_prev) * ps
                two_sided = both and g_win >= 5 * max(net_usd, 1e-9)
                qual.append({"wallet": w, "usd": usd, "two_sided": two_sided, "gross_prev": g_prev,
                             "delta_shares": d_s})
            if not qual:
                continue
            for include_two_sided in (False, True):
                q = [x for x in qual if include_two_sided or not x["two_sided"]]
                total = sum(x["usd"] for x in q)
                if len(q) < p["MIN_WALLETS"] or total < p["TOTAL_MIN"]:
                    continue
                largest = max(x["usd"] for x in q)
                if largest > p["MAX_SHARE"] * total:
                    continue
                cand[side].append({
                    "condition_id": cid, "side": side, "t": t, "price": ps,
                    "n_wallets": len(q), "total_usd": round(total, 2),
                    "largest_share": round(largest / total, 4),
                    "variant": "S4b_include_two_sided" if include_two_sided else "S4",
                    "wallets": [x["wallet"] for x in q],
                    "shift_usd": [round(x["usd"], 2) for x in q],
                    "share_treasury_prev": round(sum(x["gross_prev"] for x in q), 2),
                })
            if len(buy_wallets) >= p["MIN_WALLETS"] and buy_usd >= p["TOTAL_MIN"]:
                cand[side].append({"condition_id": cid, "side": side, "t": t, "price": ps,
                                   "n_wallets": len(buy_wallets), "total_usd": round(buy_usd, 2),
                                   "largest_share": None, "variant": "S2_buy_consensus",
                                   "wallets": sorted(buy_wallets), "shift_usd": [], "share_treasury_prev": None})
            if len(qual) == 1 and qual[0]["usd"] >= p["TOTAL_MIN"]:
                cand[side].append({"condition_id": cid, "side": side, "t": t, "price": ps,
                                   "n_wallets": 1, "total_usd": round(qual[0]["usd"], 2),
                                   "largest_share": 1.0, "variant": "S3_individual",
                                   "wallets": [qual[0]["wallet"]], "shift_usd": [round(qual[0]["usd"], 2)],
                                   "share_treasury_prev": round(qual[0]["gross_prev"], 2)})
    out = []
    for side in ("Yes", "No"):
        by_variant = defaultdict(list)
        for c in cand[side]:
            by_variant[c["variant"]].append(c)
        for v, cs in by_variant.items():
            kept = dedupe(cs)
            kept.sort(key=lambda c: c["t"])
            for i, c in enumerate(kept):
                c["primary"] = (i == 0)
            out.extend(kept)
    for c in out:
        c["event_id"] = meta.get("event_id")
        c["event_slug"] = meta.get("event_slug")
        c["closed_ts"] = meta.get("closed_ts")
        c["volume"] = meta.get("volume")
        c["market_first_ts"] = first_ts
        c["split"] = meta.get("split")
    return out, {"condition_id": cid, "status": "ok", "fills": len(rows), "wallets": len(books),
                 "first_ts": first_ts, "last_ts": last_ts}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tapes", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--splits", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--status", required=True)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--params", default=None, help="JSON overrides for the declared sweep cells")
    a = ap.parse_args()
    params = json.loads(a.params) if a.params else None

    meta = {}
    for line in open(a.universe):
        m = json.loads(line)
        meta[m["condition_id"]] = m
    splits = json.load(open(a.splits))
    con = sqlite3.connect(f"file:{urllib.parse.quote(os.path.abspath(a.tapes))}?mode=ro", uri=True)
    cids = [r[0] for r in con.execute("select condition_id from status where status='ok'")]
    if a.limit:
        cids = cids[:a.limit]
    alerts = []
    stat = []
    for i, cid in enumerate(cids, 1):
        m = dict(meta.get(cid) or {})
        m["split"] = splits.get(cid)
        rows = load_market(con, cid)
        al, st = evaluate_market(cid, rows, m, params)
        alerts.extend(al)
        stat.append(st)
        if i % 50 == 0:
            print(i, "/", len(cids), len(alerts), flush=True)
    with open(a.out, "w") as f:
        for al in alerts:
            f.write(json.dumps(al) + "\n")
    with open(a.status, "w") as f:
        json.dump({"markets_requested": len(cids), "markets_scored": len(stat),
                   "alerts": len(alerts), "per_market": stat}, f, indent=1)
    print("alerts", len(alerts), "markets", len(stat))


if __name__ == "__main__":
    main()
