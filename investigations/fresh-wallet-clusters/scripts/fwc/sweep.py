#!/usr/bin/env python3
"""Per-market $100 tapes for every catalogue information market, up to 3 pages.

A market whose cursor is exhausted is complete at this floor. A market that still
has pages is partial and is not treated as a full history. Cache: /tmp/fwc-sweep.
"""
from __future__ import annotations

import csv
import gzip
import json
import sqlite3
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path("/tmp/fwc-sweep/agg.sqlite")
UA = {"User-Agent": "research-client/1.0", "Accept": "application/json", "Accept-Encoding": "gzip"}
_lock = threading.Lock()
_next = [0.0]


def pace():
    with _lock:
        delay = _next[0] - time.time()
        _next[0] = max(time.time(), _next[0]) + 0.04
    if delay > 0:
        time.sleep(delay)


def get(url):
    last = "none"
    for attempt in range(5):
        pace()
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            last = str(exc)[:140]
            time.sleep(min(20, 1.2 * (attempt + 1)))
    raise RuntimeError(last)


def connect():
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(CACHE, timeout=180)
    con.execute("pragma journal_mode=wal")
    con.execute("pragma synchronous=normal")
    con.executescript("""
    create table if not exists markets(condition_id text primary key, status text, pages integer, n_rows integer);
    create table if not exists agg(
      wallet text, condition_id text, outcome text, buy real, sell real, n integer,
      min_ts integer, max_ts integer, primary key(wallet, condition_id, outcome));
    """)
    return con


def load(con):
    if con.execute("select count(*) from markets").fetchone()[0]:
        return
    rows = []
    with (ROOT / "data" / "data_coverage.csv").open() as handle:
        for row in csv.DictReader(handle):
            if row["family"] == "INFO":
                rows.append((row["condition_id"], "pending", 0, 0))
    con.executemany("insert into markets values(?,?,?,?)", rows)
    con.commit()
    print("markets", len(rows), flush=True)


def one(cond):
    url = ("https://data-api.polymarket.com/v2/trades?limit=1000&filter_type=CASH&filter_amount=100"
           f"&taker_only=false&condition={cond}")
    cursor = None
    rows = []
    pages = 0
    while pages < 3:
        u = url if not cursor else url + "&cursor=" + quote(cursor, safe="")
        payload = get(u)
        data = payload.get("data") or []
        page = payload.get("pagination") or {}
        pages += 1
        for raw in data:
            if str(raw.get("condition_id") or "").lower() != cond:
                continue
            outcome = str(raw.get("outcome") or "").upper()
            side = raw.get("side")
            if outcome not in ("YES", "NO") or side not in ("BUY", "SELL"):
                continue
            price, size = float(raw["price"]), float(raw["size"])
            if not (0 < price <= 1) or size <= 0:
                continue
            rows.append((raw["proxy_wallet"].lower(), cond, outcome, side, price * size, int(raw["timestamp"])))
        cursor = page.get("next_cursor")
        if not page.get("has_more") or not cursor or not data:
            return rows, pages, "complete"
    return rows, pages, "partial"


def main():
    con = connect()
    load(con)
    todo = [r[0] for r in con.execute("select condition_id from markets where status='pending'")]
    print("todo", len(todo), flush=True)
    done = 0

    def work(cond):
        try:
            return cond, one(cond), None
        except Exception as exc:  # noqa: BLE001
            return cond, None, str(exc)[:140]

    with ThreadPoolExecutor(6) as pool:
        for fut in as_completed([pool.submit(work, c) for c in todo]):
            cond, result, err = fut.result()
            with con:
                if err:
                    con.execute("update markets set status='error', pages=0, n_rows=0 where condition_id=?", (cond,))
                else:
                    rows, pages, status = result
                    bucket = {}
                    for wallet, c, outcome, side, notion, ts in rows:
                        rec = bucket.get((wallet, outcome))
                        if rec is None:
                            rec = [0.0, 0.0, 0, ts, ts]
                            bucket[(wallet, outcome)] = rec
                        if side == "BUY":
                            rec[0] += notion
                        else:
                            rec[1] += notion
                        rec[2] += 1
                        rec[3] = min(rec[3], ts)
                        rec[4] = max(rec[4], ts)
                    if bucket:
                        con.executemany(
                            """insert into agg values(?,?,?,?,?,?,?,?)
                               on conflict(wallet, condition_id, outcome) do update set
                               buy=buy+excluded.buy, sell=sell+excluded.sell, n=n+excluded.n,
                               min_ts=min(min_ts, excluded.min_ts), max_ts=max(max_ts, excluded.max_ts)""",
                            [(w, cond, o, b, s, n, a, z) for (w, o), (b, s, n, a, z) in bucket.items()],
                        )
                    con.execute("update markets set status=?, pages=?, n_rows=? where condition_id=?",
                                (status, pages, len(rows), cond))
            done += 1
            if done % 200 == 0 or done == len(todo):
                print(f"sweep {done}/{len(todo)}", flush=True)
    print("sweep finished", flush=True)


if __name__ == "__main__":
    main()
