#!/usr/bin/env python3
"""Trade-tape collector for Polymarket data-api v2.

Rules taken from the repository (METHODOLOGY.md, research_notes/early-detection-2026-11-13/study):
  * the stream is newest-first; every page is asserted monotone non-increasing on timestamp;
  * pages follow `pagination.next_cursor` until `has_more` is false, or a page cap is reached
    (a capped market is recorded as `too_deep`, never as an empty tape);
  * profile text fields (name, pseudonym, bio, images) are never stored;
  * errors are recorded as errors, never as an empty result;
  * every market's outcome is resumable, one row per market in a status table.
"""
import json, sqlite3, time, sys
from concurrent.futures import ThreadPoolExecutor

import requests

BASE = "https://data-api.polymarket.com/v2/trades"
KEEP = ("proxy_wallet", "side", "outcome", "outcome_index", "size", "price", "timestamp",
        "transaction_hash", "token_id", "condition_id")


def fetch_trades(condition_id, max_pages=300, limit=1000, pause=0.15, timeout=60, session=None,
                 stop_before_ts=None, on_page=None):
    """Return (status, pages, oldest_ts, rows). Rows keep excuted fills only, profile fields stripped."""
    s = session or requests.Session()
    cursor = None
    rows = []
    pages = 0
    last = None
    while True:
        if pages >= max_pages:
            return "too_deep", pages, last, rows
        url = f"{BASE}?condition={condition_id}&limit={limit}&taker_only=false"
        if cursor:
            url += f"&cursor={cursor}"
        for attempt in range(4):
            try:
                r = s.get(url, timeout=timeout)
            except Exception:
                if attempt == 3:
                    return "error", pages, last, rows
                time.sleep(1.5 * (attempt + 1))
                continue
            if r.status_code == 200:
                break
            if r.status_code == 429:
                time.sleep(2.0 * (attempt + 1))
                continue
            if attempt == 3:
                return f"http_{r.status_code}", pages, last, rows
            time.sleep(1.0 * (attempt + 1))
        j = r.json()
        data = j.get("data")
        if not isinstance(data, list):
            return "bad_schema", pages, last, rows
        pages += 1
        for rec in data:
            ts = int(rec["timestamp"])
            if last is not None and ts > last:
                raise RuntimeError(f"tape not newest-first for {condition_id} at page {pages}")
            last = ts
            row = {k: rec.get(k) for k in KEEP}
            row["proxy_wallet"] = (row["proxy_wallet"] or "").lower()
            row["size"] = float(row["size"])
            row["price"] = float(row["price"])
            rows.append(row)
        if on_page:
            on_page(pages, last, len(rows))
        pg = j.get("pagination") or {}
        cursor = pg.get("next_cursor")
        if not pg.get("has_more") or not cursor:
            return "ok", pages, last, rows
        if stop_before_ts is not None and last is not None and last < stop_before_ts:
            return "ok_partial_window", pages, last, rows
        time.sleep(pause)


def main():
    """CLI: python3 phi_tapes.py <out.sqlite> <condition_id> [condition_id ...]"""
    db = sys.argv[1]
    con = sqlite3.connect(db)
    con.executescript("""
      create table if not exists trades(condition_id text, ts integer, wallet text, side text,
        outcome text, outcome_index integer, size real, price real, tx text, token_id text);
      create index if not exists trades_c on trades(condition_id, ts);
      create table if not exists status(condition_id text primary key, status text, pages integer,
        oldest_ts integer, n_rows integer, fetched_at text);
    """)
    todo = [c for c in sys.argv[2:] if not con.execute(
        "select 1 from status where condition_id=?", (c,)).fetchone()]
    print(f"markets: {len(sys.argv) - 2}, todo: {len(todo)}", flush=True)

    def one(cid):
        with requests.Session() as s:
            return cid, fetch_trades(cid, session=s)

    with ThreadPoolExecutor(8) as ex:
        for cid, (status, pages, oldest, rows) in ex.map(one, todo):
            con.executemany(
                "insert into trades values(?,?,?,?,?,?,?,?,?,?)",
                [(cid, r["timestamp"], r["proxy_wallet"], r["side"], r["outcome"], r["outcome_index"],
                  r["size"], r["price"], r["transaction_hash"], r["token_id"]) for r in rows])
            con.execute("insert or replace into status values(?,?,?,?,?,?)",
                        (cid, status, pages, oldest, len(rows), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
            con.commit()
            print(cid[:12], status, pages, len(rows), flush=True)


if __name__ == "__main__":
    main()
