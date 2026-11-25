#!/usr/bin/env python3
"""Stream the global cash trade feed into aggregates. Resumable. Cache in /tmp."""
from __future__ import annotations

import csv
import gzip
import json
import sqlite3
import time
import urllib.request
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
CACHE = Path("/tmp/fwc-census/agg.sqlite")
URL = "https://data-api.polymarket.com/v2/trades?limit=1000&filter_type=CASH&filter_amount=100&taker_only=false"
UA = {"User-Agent": "research-client/1.0", "Accept": "application/json", "Accept-Encoding": "gzip"}


def connect():
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(CACHE, timeout=120)
    con.execute("pragma journal_mode=wal")
    con.execute("pragma synchronous=normal")
    con.executescript("""
    create table if not exists agg(
      wallet text, condition_id text, outcome text,
      buy real, sell real, n integer, min_ts integer, max_ts integer,
      primary key(wallet, condition_id, outcome));
    create table if not exists meta(k text primary key, v text);
    """)
    return con


def load_ids():
    info, control = set(), set()
    with (DATA / "data_coverage.csv").open() as handle:
        for row in csv.DictReader(handle):
            if row["family"] == "INFO":
                info.add(row["condition_id"])
            elif row["family"] == "PUBLIC_PROCESS":
                control.add(row["condition_id"])
    return info, control


def get(url):
    last = "none"
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=40) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return json.loads(raw)
        except Exception as exc:  # noqa: BLE001
            last = str(exc)[:160]
            time.sleep(min(30, 1.5 * (attempt + 1)))
    raise RuntimeError(last)


def main():
    info, control = load_ids()
    wanted = info | control
    con = connect()
    cursor = (con.execute("select v from meta where k='cursor'").fetchone() or [None])[0]
    pages = int((con.execute("select v from meta where k='pages'").fetchone() or [0])[0])
    rows_n = int((con.execute("select v from meta where k='rows'").fetchone() or [0])[0])
    kept = int((con.execute("select v from meta where k='kept'").fetchone() or [0])[0])
    oldest = None
    print("resume pages", pages, "rows", rows_n, flush=True)
    batch = {}
    t0 = time.time()
    while True:
        url = URL if not cursor else URL + "&cursor=" + quote(cursor, safe="")
        payload = get(url)
        data = payload.get("data") or []
        page = payload.get("pagination") or {}
        if not data:
            break
        for raw in data:
            cond = str(raw.get("condition_id") or "").lower()
            if cond not in wanted:
                continue
            outcome = str(raw.get("outcome") or "").upper()
            side = raw.get("side")
            if outcome not in ("YES", "NO") or side not in ("BUY", "SELL"):
                continue
            try:
                price, size = float(raw["price"]), float(raw["size"])
                ts = int(raw["timestamp"])
            except (TypeError, ValueError):
                continue
            if not (0 < price <= 1) or size <= 0:
                continue
            notion = price * size
            key = (raw["proxy_wallet"].lower(), cond, outcome)
            rec = batch.get(key)
            if rec is None:
                rec = [0.0, 0.0, 0, ts, ts]
                batch[key] = rec
            if side == "BUY":
                rec[0] += notion
            else:
                rec[1] += notion
            rec[2] += 1
            if ts < rec[3]:
                rec[3] = ts
            if ts > rec[4]:
                rec[4] = ts
            kept += 1
            oldest = ts if oldest is None else min(oldest, ts)
        rows_n += len(data)
        pages += 1
        cursor = page.get("next_cursor")
        if pages % 50 == 0:
            flush(con, batch)
            batch = {}
            con.execute("insert into meta values('cursor',?) on conflict(k) do update set v=excluded.v", (cursor or "",))
            con.execute("insert into meta values('pages',?) on conflict(k) do update set v=excluded.v", (str(pages),))
            con.execute("insert into meta values('rows',?) on conflict(k) do update set v=excluded.v", (str(rows_n),))
            con.execute("insert into meta values('kept',?) on conflict(k) do update set v=excluded.v", (str(kept),))
            con.execute("insert into meta values('oldest',?) on conflict(k) do update set v=excluded.v", (str(oldest or ""),))
            con.commit()
            rate = rows_n / max(1, time.time() - t0)
            print(f"pages {pages} rows {rows_n} kept {kept} oldest {oldest} rate {rate:.0f}/s", flush=True)
        if not page.get("has_more") or not cursor:
            break
    flush(con, batch)
    con.commit()
    print("finished", pages, rows_n, flush=True)


def flush(con, batch):
    if not batch:
        return
    con.executemany(
        """insert into agg values(?,?,?,?,?,?,?,?)
           on conflict(wallet, condition_id, outcome) do update set
           buy=buy+excluded.buy, sell=sell+excluded.sell, n=n+excluded.n,
           min_ts=min(min_ts, excluded.min_ts), max_ts=max(max_ts, excluded.max_ts)""",
        [(w, c, o, b, s, n, a, z) for (w, c, o), (b, s, n, a, z) in batch.items()],
    )


if __name__ == "__main__":
    main()
