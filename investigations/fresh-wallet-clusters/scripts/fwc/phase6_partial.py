#!/usr/bin/env python3
"""Re-read the 161 markets still partial at 15 pages, up to 40 pages, 100 USD floor.

Cache: /tmp/fwc-phase6/partial.sqlite. Raw pages are not stored.
"""
from __future__ import annotations

import gzip
import json
import sqlite3
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import quote

OLD = Path("/tmp/fwc-phase5/partial.sqlite")
CACHE = Path("/tmp/fwc-phase6/partial.sqlite")
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


def one(cond):
    url = ("https://data-api.polymarket.com/v2/trades?limit=1000&filter_type=CASH&filter_amount=100"
           f"&taker_only=false&condition={cond}")
    cursor = None
    rows = []
    pages = 0
    while pages < 40:
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
            rows.append((raw["proxy_wallet"].lower(), outcome, side, price * size))
        cursor = page.get("next_cursor")
        if not page.get("has_more") or not cursor or not data:
            return rows, pages, "complete"
    return rows, pages, "partial"


def main():
    old = sqlite3.connect(f"file:{OLD}?mode=ro", uri=True)
    todo = [r[0] for r in old.execute("select condition_id from markets where status='partial'")]
    print("still partial", len(todo), flush=True)
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(CACHE, timeout=180)
    con.execute("pragma journal_mode=wal")
    con.execute("create table if not exists markets(condition_id text primary key, status text, pages integer, n_rows integer)")
    con.execute("""create table if not exists agg(
      wallet text, condition_id text, outcome text, buy real, sell real,
      primary key(wallet, condition_id, outcome))""")
    pending = [c for c in todo if con.execute("select 1 from markets where condition_id=?", (c,)).fetchone() is None]
    print("pending", len(pending), flush=True)
    done = 0

    def work(cond):
        try:
            return cond, one(cond), None
        except Exception as exc:  # noqa: BLE001
            return cond, None, str(exc)[:140]

    with ThreadPoolExecutor(4) as pool:
        for fut in as_completed([pool.submit(work, c) for c in pending]):
            cond, result, err = fut.result()
            with con:
                if err:
                    con.execute("insert into markets values(?,?,?,?)", (cond, "error", 0, 0))
                else:
                    rows, pages, status = result
                    bucket = {}
                    for wallet, outcome, side, notion in rows:
                        rec = bucket.setdefault((wallet, outcome), [0.0, 0.0])
                        if side == "BUY":
                            rec[0] += notion
                        else:
                            rec[1] += notion
                    if bucket:
                        con.executemany(
                            "insert into agg values(?,?,?,?,?)",
                            [(w, cond, o, b, s) for (w, o), (b, s) in bucket.items()],
                        )
                    con.execute("insert into markets values(?,?,?,?)", (cond, status, pages, len(rows)))
            done += 1
            if done % 20 == 0 or done == len(pending):
                print(f"phase6 {done}/{len(pending)}", flush=True)
    print(con.execute("select status, count(*) from markets group by status").fetchall(), flush=True)


if __name__ == "__main__":
    main()
