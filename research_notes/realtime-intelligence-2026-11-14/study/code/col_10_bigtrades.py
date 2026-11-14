"""col_10: every order fill of FILTER_USD or more, on every market, walked back from the present along the cursor of the
public data API (newest first, 1,000 rows a page). One row per order fill, seen from the owner of the order.

  python3 -I code/col_10_bigtrades.py all      # maker and taker rows (taker_only=false)
  python3 -I code/col_10_bigtrades.py taker    # taker rows only: used to mark which rows were the aggressor

Resumable: the rows of a page, the page record and the next cursor commit in one transaction. Any unexpected answer
raises; nothing is ever replaced by an empty result. Profile text fields of the rows are never stored.
Counts kept in the `pages` table and printed: pages, rows, anomalies (rows under the filter, bad price)."""
import json, os, sqlite3, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILTER_USD = 1000
T_STOP = 1735689600            # 2025-01-01 00:00:00 UTC: the walk stops at the first page that ends before it
BASE = "https://data-api.polymarket.com/v2/trades?limit=1000&filter_type=CASH&filter_amount=%d&taker_only=%s"
NEEDED = ("proxy_wallet", "side", "token_id", "condition_id", "size", "price", "timestamp", "transaction_hash", "outcome_index")

SCHEMA = """
create table if not exists wallets(id integer primary key, address text unique);
create table if not exists markets(id integer primary key, condition_id text unique, slug text, event_slug text);
create table if not exists tokens(id integer primary key, token_id text unique, market integer, outcome text, outcome_index integer);
create table if not exists fills(ts integer, wallet integer, token integer, side integer, size real, price real, tx blob, page integer);
create table if not exists pages(n integer primary key, cursor_in text, cursor_out text, rows integer, newest integer, oldest integer,
  under_filter integer, sha256 text, fetched real);
create table if not exists state(key text primary key, value text);
"""


def _id(con, cache, table, col, value, extra=()):
    k = (table, value)
    if k not in cache:
        r = con.execute(f"select id from {table} where {col}=?", (value,)).fetchone()
        if r is None:
            marks = ",".join("?" * (1 + len(extra)))
            r = (con.execute(f"insert into {table} values(null,{marks})", (value, *extra)).lastrowid,)
        cache[k] = r[0]
    return cache[k]


def main(feed):
    taker = {"all": "false", "taker": "true"}[feed]
    con = sqlite3.connect(os.path.join(ETUDE, "data", f"bigtrades_{feed}.sqlite"), timeout=60)
    con.execute("pragma journal_mode=wal"); con.execute("pragma synchronous=normal"); con.executescript(SCHEMA)
    st = dict(con.execute("select key, value from state"))
    if st.get("done"):
        print("already complete:", st["done"]); return 0
    cursor, n, last_ts = st.get("cursor"), int(st.get("pages", 0)), (int(st["last_ts"]) if st.get("last_ts") else None)
    pace, cache, t_start = net.Pace(0.55), {}, time.time()
    while True:
        url = BASE % (FILTER_USD, taker) + (f"&cursor={cursor}" if cursor else "")
        j, sha = net.get(url, pace=pace)
        data, pg = j.get("data"), (j.get("pagination") or {})
        if not isinstance(data, list):
            raise net.SourceError(f"unexpected schema at page {n}: {str(j)[:200]}")
        if not data:
            done = f"empty page at {n}; has_more={pg.get('has_more')}"
            with con:
                con.execute("insert or replace into state values('done',?)", (done,))
            print(done); break
        rows, under = [], 0
        for r in data:
            miss = [k for k in NEEDED if r.get(k) in (None, "")]
            if miss:
                raise net.SourceError(f"row without {miss} at page {n}: {str(r)[:300]}")
            ts, size, price = int(r["timestamp"]), float(r["size"]), float(r["price"])
            if last_ts is not None and ts > last_ts:
                raise net.SourceError(f"feed not newest-first at page {n}: {ts} after {last_ts}")
            last_ts = ts
            if r["side"] not in ("BUY", "SELL") or not (0 < price <= 1.0) or size <= 0:
                raise net.SourceError(f"bad side, price or size at page {n}: {str(r)[:300]}")
            under += size * price < FILTER_USD * 0.999
            m = _id(con, cache, "markets", "condition_id", r["condition_id"], (r.get("slug"), r.get("event_slug")))
            tok = _id(con, cache, "tokens", "token_id", str(r["token_id"]), (m, r.get("outcome"), int(r["outcome_index"])))
            w = _id(con, cache, "wallets", "address", r["proxy_wallet"].lower())
            rows.append((ts, w, tok, 1 if r["side"] == "BUY" else 0, size, price, bytes.fromhex(r["transaction_hash"][2:]), n))
        nxt = pg.get("next_cursor")
        end = (not pg.get("has_more")) or (not nxt) or rows[-1][0] < T_STOP
        with con:                                     # rows, page record and cursor commit together
            con.executemany("insert into fills values(?,?,?,?,?,?,?,?)", rows)
            con.execute("insert into pages values(?,?,?,?,?,?,?,?,?)", (n, cursor, nxt, len(rows), rows[0][0], rows[-1][0], under, sha, time.time()))
            n += 1
            for k, v in (("cursor", nxt), ("pages", n), ("last_ts", last_ts)):
                con.execute("insert or replace into state values(?,?)", (k, None if v is None else str(v)))
            if end:
                con.execute("insert or replace into state values('done',?)",
                            (f"stopped after page {n - 1}: has_more={pg.get('has_more')} oldest={rows[-1][0]}",))
        if n % 50 == 0 or end:
            print(time.strftime("%H:%M:%S"), feed, "pages", n, "oldest", time.strftime("%Y-%m-%d %H:%M", time.gmtime(rows[-1][0])),
                  "rate", round(n / max(1, time.time() - t_start) * 60, 1), "pages/min", dict(net.COUNTS), flush=True)
        if end:
            break
        cursor = nxt
    print("final", dict(con.execute("select key, value from state")), dict(net.COUNTS))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
