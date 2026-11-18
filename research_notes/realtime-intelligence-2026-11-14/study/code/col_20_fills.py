"""col_20: every order fill of FILTER_USD or more of each market of the universe, from the public data API
(`v2/trades?condition=...&filter_type=CASH`, newest first, cursor pagination, full history of the market).

  python3 -I code/col_20_fills.py all      # maker and taker rows: one row per order fill, seen from the owner of the order
  python3 -I code/col_20_fills.py taker    # taker rows only (marks which rows were the aggressor)

One row per fill; identical rows are distinct fills and are kept. Resumable: a market is written with its status in one
transaction. A market whose pages fail after the retries gets an `error` status (counted, retried at the next launch):
an error is never stored as an empty tape. Profile text fields are never stored."""
import json, os, sqlite3, sys, threading, time
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILTER_USD = 1000
MAX_PAGES = 400                 # 400,000 fills of 1,000 USD or more in one market: beyond that the market is marked too_deep
WORKERS, INTERVAL = 8, 0.11     # about 9 requests a second in total (documented ceiling of the route: 30 a second)
BASE = "https://data-api.polymarket.com/v2/trades?limit=1000&filter_type=CASH&filter_amount=%d&taker_only=%s&condition=%s"
NEEDED = ("proxy_wallet", "side", "token_id", "condition_id", "size", "price", "timestamp", "transaction_hash")

SCHEMA = """
create table if not exists wallets(id integer primary key, address text unique);
create table if not exists fills(ts integer, wallet integer, cond integer, outcome_index integer, side integer, size real, price real, tx blob);
create table if not exists conds(id integer primary key, condition_id text unique, status text, pages integer, n_rows integer, note text, fetched real);
"""
_lock, _next = threading.Lock(), [0.0]


def pace():
    with _lock:
        d = _next[0] - time.time()
        _next[0] = max(time.time(), _next[0]) + INTERVAL
    if d > 0:
        time.sleep(d)


def fetch(cond, yes, no, taker):
    """All rows of one market. Returns (rows, pages, rows under the nominal filter) or raises SourceError."""
    rows, cursor, pages, last, under = [], None, 0, None, 0
    while True:
        if pages >= MAX_PAGES:
            return None, pages, under
        j, _ = net.get(BASE % (FILTER_USD, taker, cond) + (f"&cursor={cursor}" if cursor else ""), pace=pace)
        data, pg = j.get("data"), (j.get("pagination") or {})
        if not isinstance(data, list):
            raise net.SourceError(f"unexpected schema for {cond}: {str(j)[:160]}")
        pages += 1
        for r in data:
            miss = [k for k in NEEDED if r.get(k) in (None, "")]
            if miss:
                raise net.SourceError(f"row without {miss} in {cond}")
            ts, size, price, tok = int(r["timestamp"]), float(r["size"]), float(r["price"]), str(r["token_id"])
            if r["condition_id"] != cond or tok not in (yes, no):
                raise net.SourceError(f"row of another market in {cond}: {r['condition_id']} {tok[:12]}")
            if last is not None and ts > last:
                raise net.SourceError(f"tape not newest-first in {cond}")
            last = ts
            if r["side"] not in ("BUY", "SELL") or not (0 < price <= 1.0) or size <= 0:
                raise net.SourceError(f"bad side, price or size in {cond}: {r['side']} {price} {size}")
            # The source decides what is worth FILTER_USD. A few rows have size x price a little under it (16 markets of
            # 32,552 at the first pass, 927 to 998 USD): they are kept as served and counted, not rejected.
            under += size * price < FILTER_USD * 0.999
            rows.append((ts, r["proxy_wallet"].lower(), 0 if tok == yes else 1, 1 if r["side"] == "BUY" else 0, size, price,
                         bytes.fromhex(r["transaction_hash"][2:])))
        cursor = pg.get("next_cursor")
        if not pg.get("has_more") or not cursor or not data:
            return rows, pages, under


def main(feed):
    taker = {"all": "false", "taker": "true"}[feed]
    con = sqlite3.connect(os.path.join(ETUDE, "data", f"fills_{feed}.sqlite"), timeout=60)
    con.execute("pragma journal_mode=wal"); con.execute("pragma synchronous=normal"); con.executescript(SCHEMA)
    universe = [json.loads(l) for l in open(os.path.join(ETUDE, "derived", "universe_markets.jsonl"))]
    done = {r[0] for r in con.execute("select condition_id from conds where status in ('ok','too_deep')")}
    todo = [m for m in universe if m["condition_id"] not in done]
    print(f"{feed}: universe {len(universe)}, already done {len(done)}, to fetch {len(todo)}", flush=True)
    wid = dict(con.execute("select address, id from wallets"))
    n_ok = n_err = n_deep = n_rows = n_under = 0; t0 = time.time()

    def work(m):
        try:
            return m, fetch(m["condition_id"], str(m["yes_token"]), str(m["no_token"]), taker), None
        except net.SourceError as e:
            return m, (None, 0, 0), str(e)[:300]

    with ThreadPoolExecutor(WORKERS) as ex:
        futures = [ex.submit(work, m) for m in todo]
        for i, fut in enumerate(as_completed(futures), 1):
            m, (rows, pages, under), err = fut.result()
            with con:
                if err is not None:
                    status, note, n = "error", err, 0; n_err += 1
                elif rows is None:
                    status, note, n = "too_deep", f"more than {MAX_PAGES} pages", 0; n_deep += 1
                else:
                    status, note, n = "ok", (f"under_filter={under}" if under else None), len(rows); n_ok += 1; n_rows += n; n_under += under
                cur = con.execute("insert into conds(condition_id, status, pages, n_rows, note, fetched) values(?,?,?,?,?,?) "
                                  "on conflict(condition_id) do update set status=excluded.status, pages=excluded.pages, n_rows=excluded.n_rows, "
                                  "note=excluded.note, fetched=excluded.fetched", (m["condition_id"], status, pages, n, note, time.time()))
                cid = con.execute("select id from conds where condition_id=?", (m["condition_id"],)).fetchone()[0]
                if status == "ok":
                    con.execute("delete from fills where cond=?", (cid,))      # a market is always written whole
                    out = []
                    for ts, w, oi, side, size, price, tx in rows:
                        if w not in wid:
                            wid[w] = con.execute("insert into wallets(address) values(?)", (w,)).lastrowid
                        out.append((ts, wid[w], cid, oi, side, size, price, tx))
                    con.executemany("insert into fills values(?,?,?,?,?,?,?,?)", out)
            if i % 1000 == 0 or i == len(todo):
                print(time.strftime("%H:%M:%S"), feed, f"{i}/{len(todo)} ok {n_ok} error {n_err} too_deep {n_deep} rows {n_rows}",
                      "rate", round(i / max(1, time.time() - t0), 1), "markets/s", dict(net.COUNTS), flush=True)
    print("final", feed, dict(con.execute("select status, count(*) from conds group by status")), "rows", con.execute("select count(*) from fills").fetchone()[0],
          "wallets", len(wid), "markets with rows under the nominal filter", con.execute("select count(*) from conds where note like 'under_filter=%'").fetchone()[0],
          dict(net.COUNTS))
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
