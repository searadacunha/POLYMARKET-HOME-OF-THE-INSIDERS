#!/usr/bin/env python3
"""Prospective paper trading of the frozen S4 rule. NO ORDER IS EVER SENT: no key, no auth endpoint.

Each cycle (run it every 15 min, e.g. from cron or a loop):
  1. tops up a local tape per tracked market from data-api v2/trades (frozen collector, newest first);
  2. runs the frozen detector (build_alerts.evaluate_market) with no suppression, and logs the FIRST S4
     candidate of each (market, side) whose grid time is the newest bucket (causal trigger);
  3. on an alert, snapshots the public CLOB book of the alerted token and simulates a taker buy that
     walks the displayed asks for each declared size (prereg/GRID.json); the snapshot is stored whole;
  4. snapshots one price-only control per cycle: a seeded tracked (market, side) priced in [0.05, 0.90].

Journal: <state>/journal.jsonl, append-only, each line carries the sha256 of the previous line.
A simulated fill is NOT an execution: the book can change between the snapshot and a real order,
and displayed size is not guaranteed capacity.

  python3 paper_trade.py --study <frozen study dir> --state <dir on the external disk> --build-markets
  python3 paper_trade.py --study <frozen study dir> --state <dir> --once
"""
import argparse, hashlib, json, os, random, sqlite3, sys, time, urllib.parse

import requests

SIZES = (10.0, 100.0, 1000.0)
COSTS = {"optimistic": (0.0, 0.0), "politics": (0.04, 0.001), "stress": (0.07, 0.002)}
GAMMA = "https://gamma-api.polymarket.com/events"
BOOK = "https://clob.polymarket.com/book"
EXCLUDED_TAGS = {"games", "esports", "crypto-prices", "hit-price", "up-or-down", "multi-strikes", "weather",
                 "tweets-markets", "mention-markets"}           # population rule of 13/11
GRID = 900


def in_sample(cid):
    return int(hashlib.sha256(cid.encode()).hexdigest()[:8], 16) % 1000 < 50   # amendment 002 rule


def build_markets(path):
    """Open markets under the frozen population filters and hash rule (volume floors as of today)."""
    out, offset = [], 0
    while True:
        r = requests.get(GAMMA, params=dict(closed="false", active="true", volume_min=50000, limit=500, offset=offset), timeout=60)
        r.raise_for_status()
        evs = r.json()
        if not evs:
            break
        for e in evs:
            tags = {t.get("slug") for t in e.get("tags") or []}
            if tags & EXCLUDED_TAGS or float(e.get("volume") or 0) < 50_000:
                continue
            for m in e.get("markets") or []:
                cid = m.get("conditionId")
                vol = float(m.get("volumeNum") or m.get("volume") or 0)
                outs = json.loads(m.get("outcomes") or "[]")
                toks = json.loads(m.get("clobTokenIds") or "[]")
                if (not cid or outs != ["Yes", "No"] or len(toks) != 2 or m.get("closed")
                        or not (10_000 <= vol < 1_000_000) or not in_sample(cid)):
                    continue
                out.append(dict(condition_id=cid, event_id=str(e.get("id")), event_slug=e.get("slug"),
                                yes_token=toks[0], no_token=toks[1], volume=vol, end_date=m.get("endDate")))
        offset += len(evs)
    json.dump(out, open(path, "w"), indent=1)
    print(f"{len(out)} markets -> {path}")


def journal(state, rec):
    p = os.path.join(state, "journal.jsonl")
    prev = "0" * 64
    if os.path.exists(p) and os.path.getsize(p):
        with open(p, "rb") as fh:
            fh.seek(max(0, os.path.getsize(p) - 65536))
            prev = hashlib.sha256(fh.read().splitlines()[-1]).hexdigest()
    rec = dict(rec, prev_sha256=prev, logged_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    with open(p, "a") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


def walk_asks(book, usd, fee_rate, slip):
    """Simulated taker buy on the displayed asks. Returns None when the book shows no ask."""
    asks = sorted((float(a["price"]), float(a["size"])) for a in book.get("asks") or [])
    if not asks:
        return None
    shares = cost = fees = 0.0
    for p, q in asks:
        need = usd - cost
        if need <= 1e-9:
            break
        take = min(q, need / p)
        shares += take
        cost += take * p
        fees += take * (fee_rate * p * (1 - p) + slip)
    return dict(best_ask=asks[0][0], shares=round(shares, 6), cost=round(cost, 6), fees_slip=round(fees, 6),
                vwap=round(cost / shares, 6) if shares else None, full=cost >= usd - 1e-6,
                displayed_ask_usd=round(sum(p * q for p, q in asks), 2))


def snapshot(token):
    t0 = time.time()
    r = requests.get(BOOK, params={"token_id": token}, timeout=30)
    if r.status_code != 200:
        return None, dict(error=f"http_{r.status_code}", requested=t0)
    raw = r.text
    return json.loads(raw), dict(requested=t0, received=time.time(), sha256=hashlib.sha256(raw.encode()).hexdigest())


def simulate(book):
    return {f"{int(u)}_{cn}": walk_asks(book, u, *COSTS[cn]) for u in SIZES for cn in COSTS}


def cycle(a, ba, ct):
    markets = json.load(open(os.path.join(a.state, "markets.json")))
    con = sqlite3.connect(os.path.join(a.state, "tapes.sqlite"))
    con.executescript("""create table if not exists trades(condition_id text, ts integer, wallet text, side text,
        outcome text, outcome_index integer, size real, price real, tx text, token_id text,
        unique(condition_id, tx, wallet, side, outcome, size, price, ts));
      create index if not exists trades_c on trades(condition_id, ts);
      create table if not exists fired(condition_id text, side text, t integer, primary key(condition_id, side));""")
    now = time.time()
    newest = int(now // GRID) * GRID
    priced = []
    for m in markets:
        cid = m["condition_id"]
        last = con.execute("select max(ts) from trades where condition_id=?", (cid,)).fetchone()[0]
        status, pages, _, rows = ct.fetch_trades(cid, stop_before_ts=last)
        if status not in ("ok", "ok_partial_window"):
            journal(a.state, dict(kind="collect_error", condition_id=cid, status=status, pages=pages))
            continue                        # a failed top-up is logged, never read as an empty market
        con.executemany("insert or ignore into trades values(?,?,?,?,?,?,?,?,?,?)",
                        [(cid, r["timestamp"], r["proxy_wallet"], r["side"], r["outcome"], r["outcome_index"],
                          r["size"], r["price"], r["transaction_hash"], r["token_id"]) for r in rows])
        con.commit()
        tape = ba.load_market(con, cid)
        frozen = ba.dedupe
        ba.dedupe = lambda c: sorted(c, key=lambda x: x["t"])
        cands, _ = ba.evaluate_market(cid, tape, dict(event_id=m["event_id"], event_slug=m["event_slug"]))
        ba.dedupe = frozen
        _, prices = ba.build_books(tape) if tape else (None, None)
        for side, tok in (("Yes", m["yes_token"]), ("No", m["no_token"])):
            if prices:
                p = ba.price_at(prices, side, now)
                if p is not None and 0.05 <= p <= 0.90:
                    priced.append((m, side, tok, p))
            s4 = [c for c in cands if c["variant"] == "S4" and c["side"] == side]
            if not s4 or con.execute("select 1 from fired where condition_id=? and side=?", (cid, side)).fetchone():
                continue
            c = s4[0]
            if c["t"] < newest:             # first candidate is already in the past: not a live trigger
                con.execute("insert into fired values(?,?,?)", (cid, side, c["t"]))
                con.commit()
                journal(a.state, dict(kind="stale_first_candidate", condition_id=cid, side=side, t=c["t"]))
                continue
            book, meta = snapshot(tok)
            con.execute("insert into fired values(?,?,?)", (cid, side, c["t"]))
            con.commit()
            journal(a.state, dict(kind="alert", status="SIMULATED_NOT_EXECUTED", condition_id=cid,
                                  event_id=m["event_id"], token_id=tok, side=side, grid_t=c["t"],
                                  detected_at=now, alert_price=c["price"], n_wallets=c["n_wallets"],
                                  total_usd=c["total_usd"], wallets=c["wallets"], shift_usd=c["shift_usd"],
                                  book_meta=meta, book=book, fills=simulate(book) if book else None))
    if priced:                                  # one price-only control per cycle, seeded by the cycle time
        m, side, tok, p = random.Random(newest).choice(sorted(priced, key=lambda x: (x[0]["condition_id"], x[1])))
        book, meta = snapshot(tok)
        journal(a.state, dict(kind="price_only_control", status="SIMULATED_NOT_EXECUTED",
                              condition_id=m["condition_id"], event_id=m["event_id"], token_id=tok, side=side,
                              last_price=p, detected_at=now, book_meta=meta, book=book,
                              fills=simulate(book) if book else None))
    journal(a.state, dict(kind="cycle", markets=len(markets), newest_grid=newest, seconds=round(time.time() - now, 1)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--study", required=True)
    ap.add_argument("--state", required=True)
    ap.add_argument("--build-markets", action="store_true")
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="smoke test: first N markets only")
    a = ap.parse_args()
    os.makedirs(a.state, exist_ok=True)
    if a.build_markets:
        build_markets(os.path.join(a.state, "markets.json"))
        if a.limit:
            p = os.path.join(a.state, "markets.json")
            json.dump(json.load(open(p))[:a.limit], open(p, "w"), indent=1)
    sys.path.insert(0, os.path.join(a.study, "scripts"))
    import build_alerts as ba, collect_tapes as ct     # frozen code, unmodified
    if a.once:
        cycle(a, ba, ct)


if __name__ == "__main__":
    main()
