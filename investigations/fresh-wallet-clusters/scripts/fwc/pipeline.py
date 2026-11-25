#!/usr/bin/env python3
"""Resumable collection and the pre-registered tests.

Nothing in this file is allowed to treat a shared service as a common owner.
A failed read is stored as an error and is never replaced with an empty tape.
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import json
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPO = ROOT.parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(REPO / "monitoring"))

from phi_engine.chainfund import INFRA, payer_of_deposit, transfers  # noqa: E402
from phi_engine.contracts import family  # noqa: E402
from fwc.logic import (  # noqa: E402
    central_answer, classify_address, commitment, evidence_class, family_permutation,
    forward_destination, freshness, h1_stat, has_tight_group, load_spec, month_key,
    quintiles, sample_indices, shuffle_labels, tight_subset, verdict_h1,
)

DATA = ROOT / "data"
DB = DATA / "cache.sqlite"
SPEC = load_spec()
SPEC_SHA = hashlib.sha256((ROOT / "preregistration.json").read_bytes()).hexdigest()
UA = {"User-Agent": "Mozilla/5.0 (compatible; research-client/1.0)", "Accept": "application/json",
      "Accept-Encoding": "gzip"}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOKENS = SPEC["funding"]["tokens"]
RPCS = ["https://gateway.tenderly.co/public/polygon", "https://polygon.drpc.org"]
WINDOWS = SPEC["groups"]["windows_seconds"]
PRIMARY_W = SPEC["groups"]["primary_window_seconds"]
BEHAVIOR_W = SPEC["groups"]["behavioral_window_seconds"]
MIN_USD = SPEC["commitment"]["min_commit_usd"]
CASH_FILTER = SPEC["commitment"]["cash_filter_usd"]
PC = SPEC["population"]["positive_control"]["condition_id"]
NOBEL_KEY = SPEC["population"]["positive_control"]["key"]
NOBEL_WALLETS = set(SPEC["population"]["positive_control"]["wallets"])

_pace_lock = threading.Lock()
_next_http = [0.0]


def _pace(interval=0.12):
    with _pace_lock:
        delay = _next_http[0] - time.time()
        _next_http[0] = max(time.time(), _next_http[0]) + interval
    if delay > 0:
        time.sleep(delay)


def http_json(url: str, tries: int = 6):
    last = "none"
    for attempt in range(tries):
        _pace()
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip":
                    raw = gzip.decompress(raw)
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
            if exc.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f"{url[:140]} :: {last}") from exc
            time.sleep(min(60, 2 * (attempt + 1)))
        except Exception as exc:  # noqa: BLE001 — transport failures are retried, then raised
            last = repr(exc)
            time.sleep(min(30, 2 * (attempt + 1)))
    raise RuntimeError(f"{url[:140]} :: {last}")


def rpc(method: str, params, log_range: bool = False):
    urls = [RPCS[0]] if log_range else RPCS
    last = "none"
    for url in urls:
        for attempt in range(4):
            try:
                body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
                req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", **UA})
                with urllib.request.urlopen(req, timeout=40) as resp:
                    raw = resp.read()
                    if resp.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                        raw = gzip.decompress(raw)
                    payload = json.loads(raw)
                if payload.get("error"):
                    last = str(payload["error"])[:200]
                    if "100 blocks" in last or "free plan" in last:
                        break
                    time.sleep(0.4 * (attempt + 1))
                    continue
                return payload.get("result")
            except Exception as exc:  # noqa: BLE001
                last = repr(exc)[:200]
                time.sleep(0.5 * (attempt + 1))
    raise RuntimeError(f"rpc {method} failed: {last}")


def connect() -> sqlite3.Connection:
    DATA.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=120)
    con.execute("pragma journal_mode=wal")
    con.execute("pragma synchronous=normal")
    con.executescript("""
    create table if not exists meta(k text primary key, v text);
    create table if not exists markets(
      condition_id text primary key, event_slug text, event_title text, question text,
      event_volume real, volume real, end_date text, end_ts integer, closed integer,
      yes_token text, no_token text, yes_price real, no_price real, tags text,
      family text, stratum text, in_sample integer default 0, forced_control integer default 0,
      in_denominator integer default 0);
    create table if not exists fetches(
      condition_id text primary key, status text, pages integer, n_rows integer, note text, fetched real);
    create table if not exists fills(
      condition_id text, ts integer, wallet text, outcome text, side text,
      price real, size real, tx text);
    create table if not exists activity(
      wallet text, ts integer, typ text, condition_id text, side text, usdc real, price real, tx text);
    create table if not exists activity_status(
      wallet text primary key, status text, n_rows integer, has_more integer, note text);
    create table if not exists exposures(
      wallet text, condition_id text, outcome text, gross_buy real, sell_proceeds real,
      committed real, threshold_ts integer, threshold_price real, vwap real,
      n_buys integer, n_sells integer, eligible integer,
      primary key(wallet, condition_id, outcome));
    create table if not exists fresh(
      wallet text, condition_id text, labels text, qualifying integer, history text,
      f0 integer, first_activity integer, prior_trade integer, gap_censored integer,
      primary key(wallet, condition_id));
    create table if not exists edges(
      wallet text, hop integer, sender text, prelim_class text, token text,
      amount_usd real, tx text, block integer, block_ts integer, kind text);
    create table if not exists trace_status(wallet text primary key, status text, note text);
    create table if not exists blocks(n integer primary key, ts integer);
    create table if not exists addr_state(address text, block integer, code integer, nonce integer,
      primary key(address, block));
    """)
    row = con.execute("select v from meta where k='spec_sha'").fetchone()
    if row and row[0] != SPEC_SHA:
        raise SystemExit("preregistration.json changed after collection started; refusing to mix criteria")
    con.execute("insert into meta(k,v) values('spec_sha', ?) on conflict(k) do nothing", (SPEC_SHA,))
    con.commit()
    return con


def iso_ts(value: str | None) -> int | None:
    if not value or not isinstance(value, str):
        return None
    text = value.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.year < 2024 or dt.year > 2028:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


def stratum_of(end_ts: int | None, closed: bool) -> str:
    if not closed:
        return "OPEN"
    if end_ts is None:
        return "OUT_OF_WINDOW"
    splits = SPEC["population"]["splits"]
    for name, (start, end) in splits.items():
        if iso_ts(start) <= end_ts < iso_ts(end):
            return name
    return "OUT_OF_WINDOW"


def parse_list(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return []
    return value or []


def catalogue(con: sqlite3.Connection):
    """Keyset pagination. Offset listing 422s above a few thousand rows, which drops 2026."""
    if con.execute("select v from meta where k='catalogue_complete'").fetchone():
        print("catalogue complete", flush=True)
        return
    from urllib.parse import quote
    phases = [
        ("closed", "https://gamma-api.polymarket.com/events/keyset?closed=true&volume_min=50000"
         "&end_date_min=2025-01-01T00:00:00Z&end_date_max=2026-11-26T00:00:00Z"
         "&order=endDate&ascending=true&limit=50"),
        ("open", "https://gamma-api.polymarket.com/events/keyset?closed=false&volume_min=50000&limit=50"),
    ]
    phase_row = con.execute("select v from meta where k='catalogue_phase'").fetchone()
    cursor_row = con.execute("select v from meta where k='catalogue_cursor'").fetchone()
    phase_name = phase_row[0] if phase_row else "closed"
    cursor = cursor_row[0] if cursor_row and cursor_row[0] not in (None, "") else None
    seen_events = set()
    started = False
    for label, template in phases:
        if not started:
            if label != phase_name:
                continue
            started = True
        else:
            cursor = None
        pages = 0
        while pages < 8000:
            url = template if not cursor else template + "&after_cursor=" + quote(cursor, safe="")
            payload = http_json(url)
            rows = payload.get("events") if isinstance(payload, dict) else None
            if not isinstance(rows, list):
                raise RuntimeError("keyset schema")
            pages += 1
            fresh_ids = 0
            batch = []
            for event in rows:
                eid = str(event.get("id"))
                if eid in seen_events:
                    continue
                seen_events.add(eid)
                fresh_ids += 1
                tags = [t.get("slug") for t in (event.get("tags") or []) if isinstance(t, dict) and t.get("slug")]
                fam = family(tags)
                event_volume = float(event.get("volume") or 0)
                event_closed = bool(event.get("closed"))
                for market in event.get("markets") or []:
                    outcomes = [str(x).lower() for x in parse_list(market.get("outcomes"))]
                    tokens = [str(x) for x in parse_list(market.get("clobTokenIds"))]
                    if not market.get("conditionId") or outcomes != ["yes", "no"] or len(tokens) != 2:
                        continue
                    volume = float(market.get("volumeNum") or market.get("volume") or 0)
                    if volume < SPEC["population"]["market_volume_min_usd"] and fam != "EXCLUDED":
                        continue
                    end = market.get("endDate") or event.get("endDate")
                    end_ts = iso_ts(end)
                    prices = parse_list(market.get("outcomePrices"))
                    yes_p = no_p = None
                    if len(prices) == 2:
                        try:
                            yes_p, no_p = float(prices[0]), float(prices[1])
                        except (TypeError, ValueError):
                            yes_p = no_p = None
                    closed = bool(market.get("closed")) and event_closed
                    batch.append((
                        str(market.get("conditionId") or "").lower(), event.get("slug"),
                        (event.get("title") or "")[:180], (market.get("question") or "")[:240],
                        event_volume, volume, end, end_ts, 1 if closed else 0,
                        tokens[0], tokens[1], yes_p, no_p, ",".join(tags), fam,
                        stratum_of(end_ts, closed),
                    ))
            if batch:
                con.executemany("""insert into markets(condition_id, event_slug, event_title, question,
                    event_volume, volume, end_date, end_ts, closed, yes_token, no_token, yes_price, no_price,
                    tags, family, stratum) values(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    on conflict(condition_id) do nothing""", batch)
                con.commit()
            nxt = payload.get("next_cursor") or ""
            con.execute("insert into meta(k,v) values('catalogue_phase', ?) on conflict(k) do update set v=excluded.v", (label,))
            con.execute("insert into meta(k,v) values('catalogue_cursor', ?) on conflict(k) do update set v=excluded.v", (nxt,))
            con.commit()
            print(f"catalogue {label} page {pages} events {len(rows)} new {fresh_ids}", flush=True)
            if not nxt or not rows:
                break
            if fresh_ids == 0 and pages > 1:
                # a repeated page would otherwise spin; the cursor is supposed to move
                raise RuntimeError(f"keyset did not advance during {label}")
            cursor = nxt
        else:
            raise RuntimeError(f"catalogue page cap hit during {label}")
    con.execute("insert into meta(k,v) values('catalogue_complete', '1') on conflict(k) do update set v='1'")
    con.commit()
    counts = dict(con.execute("select family||':'||stratum, count(*) from markets group by 1"))
    print("catalogue counts", counts, flush=True)


def choose_sample(con: sqlite3.Connection):
    if con.execute("select count(*) from markets where in_sample=1").fetchone()[0]:
        print("sample already chosen", flush=True)
        return
    targets = SPEC["population"]["targets"]
    for fam, strata in (("INFO", targets["INFO"]), ("PUBLIC_PROCESS", targets["PUBLIC_PROCESS"])):
        for stratum, target in strata.items():
            rows = [r[0] for r in con.execute(
                """select condition_id from markets where family=? and stratum=? and volume>=?
                   order by end_date, condition_id""",
                (fam, stratum, SPEC["population"]["market_volume_min_usd"]))]
            for index in sample_indices(len(rows), target):
                con.execute("update markets set in_sample=1, in_denominator=1 where condition_id=?", (rows[index],))
            print(f"sample {fam} {stratum}: frame {len(rows)} target {target}", flush=True)
    open_rows = [r[0] for r in con.execute(
        """select condition_id from markets where family='INFO' and stratum='OPEN' and volume>=?
           order by end_date, condition_id""", (SPEC["population"]["market_volume_min_usd"],))]
    for index in sample_indices(len(open_rows), targets["OPEN_INFO"]):
        con.execute("update markets set in_sample=1, in_denominator=0 where condition_id=?", (open_rows[index],))
    print(f"sample OPEN_INFO frame {len(open_rows)}", flush=True)
    row = con.execute("select in_sample from markets where condition_id=?", (PC,)).fetchone()
    if row is None:
        print("positive control market is not in the catalogue", flush=True)
    elif row[0] == 1:
        con.execute("update markets set forced_control=0 where condition_id=?", (PC,))
    else:
        con.execute("update markets set in_sample=1, forced_control=1, in_denominator=0 where condition_id=?", (PC,))
        print("positive control forced in, outside the confirmatory denominator", flush=True)
    con.commit()
    print("sample size", con.execute("select count(*) from markets where in_sample=1").fetchone()[0], flush=True)


def fetch_trades(condition: str, yes: str, no: str, max_pages: int):
    rows = []
    cursor = None
    pages = 0
    under = 0
    last = None
    while pages < max_pages:
        url = ("https://data-api.polymarket.com/v2/trades?limit=1000&filter_type=CASH"
               f"&filter_amount={CASH_FILTER}&taker_only=false&condition={condition}")
        if cursor:
            from urllib.parse import quote
            url += "&cursor=" + quote(cursor, safe="")
        payload = http_json(url)
        data = payload.get("data")
        page = payload.get("pagination") or {}
        if not isinstance(data, list):
            raise RuntimeError("trade schema")
        pages += 1
        for raw in data:
            token = str(raw.get("token_id"))
            if str(raw.get("condition_id", "")).lower() != condition or token not in (yes, no):
                raise RuntimeError("trade from another market")
            outcome = "YES" if token == yes else "NO"
            if str(raw.get("outcome", "")).lower() not in ("yes", "no"):
                raise RuntimeError("missing outcome")
            if (str(raw.get("outcome")).lower() == "yes") != (outcome == "YES"):
                raise RuntimeError("token and outcome disagree")
            side = raw.get("side")
            price, size = float(raw["price"]), float(raw["size"])
            ts = int(raw["timestamp"])
            if side not in ("BUY", "SELL") or not (0 < price <= 1) or size <= 0:
                raise RuntimeError("bad trade fields")
            if last is not None and ts > last:
                raise RuntimeError("tape is not newest-first")
            last = ts
            if size * price < CASH_FILTER * 0.999:
                under += 1
            rows.append((condition, ts, raw["proxy_wallet"].lower(), outcome, side, price, size,
                         raw["transaction_hash"].lower()))
        cursor = page.get("next_cursor")
        if not page.get("has_more") or not cursor or not data:
            return rows, pages, under, "ok"
    return None, pages, under, "too_deep"


def trades(con: sqlite3.Connection):
    todo = []
    for condition, yes, no, forced in con.execute(
            """select m.condition_id, m.yes_token, m.no_token, m.forced_control
               from markets m left join fetches f on f.condition_id=m.condition_id
               where m.in_sample=1 and (f.status is null or f.status='error')"""):
        cap = SPEC["commitment"]["positive_control_max_pages"] if condition == PC or forced else SPEC["commitment"]["max_pages"]
        todo.append((condition, yes, no, cap))
    print(f"trades to fetch {len(todo)}", flush=True)

    def work(item):
        condition, yes, no, cap = item
        try:
            return item, fetch_trades(condition, yes, no, cap), None
        except Exception as exc:  # noqa: BLE001
            return item, None, str(exc)[:240]

    done = 0
    with ThreadPoolExecutor(4) as pool:
        futures = [pool.submit(work, item) for item in todo]
        for fut in as_completed(futures):
            (condition, _yes, _no, _cap), result, err = fut.result()
            with con:
                con.execute("delete from fills where condition_id=?", (condition,))
                if err:
                    con.execute("insert into fetches values(?,?,?,?,?,?) on conflict(condition_id) do update set "
                                "status=excluded.status, pages=excluded.pages, n_rows=excluded.n_rows, note=excluded.note, fetched=excluded.fetched",
                                (condition, "error", 0, 0, err, time.time()))
                else:
                    rows, pages, under, status = result
                    if status != "ok":
                        con.execute("insert into fetches values(?,?,?,?,?,?) on conflict(condition_id) do update set "
                                    "status=excluded.status, pages=excluded.pages, n_rows=excluded.n_rows, note=excluded.note, fetched=excluded.fetched",
                                    (condition, "too_deep", pages, 0, "page cap", time.time()))
                    else:
                        # exact duplicate rows are dropped; distinct fills that share a transaction are kept
                        unique = list({(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7]) for r in rows})
                        con.executemany("insert into fills values(?,?,?,?,?,?,?,?)", unique)
                        note = f"under_filter={under};dropped_dupes={len(rows)-len(unique)}"
                        con.execute("insert into fetches values(?,?,?,?,?,?) on conflict(condition_id) do update set "
                                    "status=excluded.status, pages=excluded.pages, n_rows=excluded.n_rows, note=excluded.note, fetched=excluded.fetched",
                                    (condition, "ok", pages, len(unique), note, time.time()))
            done += 1
            if done % 25 == 0 or done == len(todo):
                print(f"trades {done}/{len(todo)}", flush=True)


def exposures(con: sqlite3.Connection):
    con.execute("create index if not exists fills_cond on fills(condition_id)")
    con.execute("create index if not exists fills_wallet on fills(wallet)")
    con.execute("delete from exposures")
    markets = [r[0] for r in con.execute(
        "select m.condition_id from markets m join fetches f on f.condition_id=m.condition_id where f.status='ok' and m.in_sample=1")]
    n = 0
    for condition in markets:
        grouped = defaultdict(list)
        for wallet, outcome, ts, side, price, size in con.execute(
                "select wallet, outcome, ts, side, price, size from fills where condition_id=?", (condition,)):
            grouped[(wallet, outcome)].append((ts, side, price, size))
        batch = []
        for (wallet, outcome), fills in grouped.items():
            got = commitment(fills, MIN_USD)
            batch.append((wallet, condition, outcome, got["gross_buy_usd"], got["sell_proceeds_usd"],
                          got["capital_committed_usd"], got["threshold_ts"], got["threshold_price"],
                          got["vwap_to_threshold"], got["n_buys"], got["n_sells"], 1 if got["eligible"] else 0))
        con.executemany("insert into exposures values(?,?,?,?,?,?,?,?,?,?,?,?)", batch)
        n += 1
        if n % 50 == 0:
            con.commit()
            print(f"exposures {n}/{len(markets)}", flush=True)
    con.commit()
    print("eligible rows", con.execute("select count(*) from exposures where eligible=1").fetchone()[0], flush=True)


def activity_queue(con: sqlite3.Connection) -> list[str]:
    priority = {name: i for i, name in enumerate(SPEC["freshness"]["activity_priority"])}
    best = {}
    for wallet, stratum, condition in con.execute(
            """select e.wallet, m.stratum, e.condition_id from exposures e
               join markets m on m.condition_id=e.condition_id
               where e.eligible=1 and m.in_sample=1"""):
        rank = priority.get(stratum, 9)
        if condition == PC:
            rank = -1
        if wallet not in best or rank < best[wallet]:
            best[wallet] = rank
    ordered = sorted(best, key=lambda w: (best[w], w))
    cap = SPEC["freshness"]["activity_cap"]
    return ordered[:cap]


def fetch_activity(wallet: str):
    url = ("https://data-api.polymarket.com/v2/activity?user=" + wallet
           + "&start=1&sort_by=TIMESTAMP&sort_direction=ASC&exclude_deposits_withdrawals=false&limit=1000")
    payload = http_json(url)
    data = payload.get("data")
    page = payload.get("pagination") or {}
    if not isinstance(data, list):
        raise RuntimeError("activity schema")
    rows = []
    last = 0
    for raw in data:
        if str(raw.get("proxy_wallet", "")).lower() != wallet:
            raise RuntimeError("activity row for another wallet")
        ts = int(raw["timestamp"])
        if ts < last:
            raise RuntimeError("activity not oldest-first")
        last = ts
        # profile text is discarded on purpose
        usdc = raw.get("usdc_size")
        if usdc in (None, ""):
            usdc = raw.get("size") or 0
        rows.append((wallet, ts, str(raw.get("type") or "OTHER"), str(raw.get("condition_id") or "").lower(),
                     str(raw.get("side") or ""), float(usdc or 0), float(raw.get("price") or 0),
                     str(raw.get("transaction_hash") or "").lower()))
    return rows, 1 if page.get("has_more") else 0


def activity(con: sqlite3.Connection):
    have = {r[0] for r in con.execute("select wallet from activity_status where status='ok'")}
    queue = [w for w in activity_queue(con) if w not in have]
    print(f"activity to fetch {len(queue)} (cap {SPEC['freshness']['activity_cap']})", flush=True)

    def work(wallet):
        try:
            return wallet, fetch_activity(wallet), None
        except Exception as exc:  # noqa: BLE001
            return wallet, None, str(exc)[:240]

    done = 0
    with ThreadPoolExecutor(4) as pool:
        for fut in as_completed([pool.submit(work, w) for w in queue]):
            wallet, result, err = fut.result()
            with con:
                con.execute("delete from activity where wallet=?", (wallet,))
                if err:
                    con.execute("insert into activity_status values(?,?,?,?,?) on conflict(wallet) do update set "
                                "status=excluded.status, n_rows=excluded.n_rows, has_more=excluded.has_more, note=excluded.note",
                                (wallet, "error", 0, 0, err))
                else:
                    rows, has_more = result
                    con.executemany("insert into activity values(?,?,?,?,?,?,?,?)", rows)
                    con.execute("insert into activity_status values(?,?,?,?,?) on conflict(wallet) do update set "
                                "status=excluded.status, n_rows=excluded.n_rows, has_more=excluded.has_more, note=excluded.note",
                                (wallet, "ok", len(rows), has_more, None))
            done += 1
            if done % 100 == 0 or done == len(queue):
                print(f"activity {done}/{len(queue)}", flush=True)


def features(con: sqlite3.Connection):
    con.execute("create index if not exists activity_wallet on activity(wallet, ts)")
    con.commit()
    con.execute("delete from fresh")
    elig = list(con.execute(
        """select e.wallet, e.condition_id, min(e.threshold_ts) from exposures e
           join markets m on m.condition_id=e.condition_id
           where e.eligible=1 and m.in_sample=1
           group by e.wallet, e.condition_id"""))
    by_wallet = defaultdict(list)
    for wallet, condition, threshold in elig:
        by_wallet[wallet].append((condition, threshold))
    batch = []
    for wallet, jobs in by_wallet.items():
        status = con.execute("select status, has_more from activity_status where wallet=?", (wallet,)).fetchone()
        rows = list(con.execute(
            "select ts, typ, condition_id from activity where wallet=? order by ts", (wallet,))) if status and status[0] == "ok" else []
        other_fills = defaultdict(list)
        for cond, ts in con.execute(
                """select f.condition_id, f.ts from fills f
                   join fetches t on t.condition_id=f.condition_id and t.status='ok'
                   where f.wallet=?""", (wallet,)):
            other_fills[cond].append(ts)
        for condition, threshold in jobs:
            if not status or status[0] != "ok" or threshold is None:
                batch.append((wallet, condition, "", 0, "unresolved", 0, None, None, 0))
                continue
            trade_ts = [ts for ts, typ, cond in rows if typ == "TRADE" and cond == condition]
            fill_ts = other_fills.get(condition, [])
            first_trade = min(trade_ts) if trade_ts else (min(fill_ts) if fill_ts else None)
            if first_trade is None:
                batch.append((wallet, condition, "", 0, "unresolved", 0, None, None, 0))
                continue
            has_more = bool(status[1])
            last_row = rows[-1][0] if rows else None
            gap_censored = bool(has_more and (not trade_ts) and last_row is not None and last_row < first_trade)
            # a fill on another fully read market is a prior trade even if the activity page missed it
            activity_rows = [(ts, typ, cond) for ts, typ, cond in rows]
            for cond, times in other_fills.items():
                if cond != condition and times and min(times) < first_trade:
                    activity_rows.append((min(times), "TRADE", cond))
            activity_rows.sort()
            got = freshness(activity_rows, condition, first_trade, int(threshold), True, "unchecked", None, False, gap_censored)
            batch.append((wallet, condition, ",".join(got["labels"]), 1 if got["qualifying"] else 0,
                          got["history"], 1 if got["F0"] else 0, got.get("first_activity_ts"),
                          1 if got.get("prior_trade") else 0, 1 if gap_censored else 0))
    con.executemany("insert into fresh values(?,?,?,?,?,?,?,?,?)", batch)
    con.commit()
    print("qualifying fresh rows", con.execute("select count(*) from fresh where qualifying=1").fetchone()[0], flush=True)


def block_ts(con, n: int) -> int:
    row = con.execute("select ts from blocks where n=?", (n,)).fetchone()
    if row:
        return row[0]
    result = rpc("eth_getBlockByNumber", [hex(n), False])
    ts = int(result["timestamp"], 16)
    con.execute("insert or replace into blocks values(?,?)", (n, ts))
    con.commit()
    return ts


def ensure_head(con):
    if con.execute("select v from meta where k='head_block'").fetchone():
        return
    head = int(rpc("eth_blockNumber", []), 16)
    head_time = block_ts(con, head)
    con.execute("insert or replace into meta values('head_block', ?)", (str(head),))
    con.execute("insert or replace into meta values('head_ts', ?)", (str(head_time),))
    con.commit()


def block_for_time(con, ts: int) -> int:
    """Linear estimate from the chain head, then a short search. Polygon blocks are about 2 seconds."""
    ensure_head(con)
    head = int(con.execute("select v from meta where k='head_block'").fetchone()[0])
    head_time = int(con.execute("select v from meta where k='head_ts'").fetchone()[0])
    guess = max(1, min(head, head - int(max(0, head_time - ts) / 2)))
    lo, hi = max(1, guess - 20000), min(head, guess + 20000)
    # Expand until the timestamp is inside, at most a few header reads.
    for _ in range(8):
        if block_ts(con, lo) <= ts <= block_ts(con, hi):
            break
        if block_ts(con, lo) > ts:
            lo = max(1, lo - (hi - lo))
        if block_ts(con, hi) < ts:
            hi = min(head, hi + (hi - lo + 1))
    while lo < hi:
        mid = (lo + hi) // 2
        if block_ts(con, mid) < ts:
            lo = mid + 1
        else:
            hi = mid
    return lo


def address_state(con, address: str, block: int) -> tuple[bool, int | None]:
    row = con.execute("select code, nonce from addr_state where address=? and block=?", (address, block)).fetchone()
    if row:
        return bool(row[0]), row[1]
    code = rpc("eth_getCode", [address, hex(block)])
    nonce_hex = rpc("eth_getTransactionCount", [address, hex(block)])
    present = 1 if code and code != "0x" else 0
    nonce = int(nonce_hex, 16) if nonce_hex is not None else None
    con.execute("insert or replace into addr_state values(?,?,?,?)", (address, block, present, nonce))
    con.commit()
    return bool(present), nonce


def logs_to(address: str, start: int, end: int) -> list[dict]:
    pad = "0x" + "0" * 24 + address[2:]
    found = []
    for token in TOKENS:
        result = rpc("eth_getLogs", [{
            "fromBlock": hex(start), "toBlock": hex(end), "address": token,
            "topics": [TRANSFER, None, pad],
        }], log_range=True)
        found.extend(result or [])
    return found


def trace_wallet(con, wallet: str, threshold_ts: int):
    end = block_for_time(con, threshold_ts)
    start = max(1, end - SPEC["funding"]["lookback_blocks"])
    trade_txs = {r[0] for r in con.execute("select tx from fills where wallet=?", (wallet,))}
    best_amount: dict[str, float] = {}

    def consider(sender: str, block: int, amount_raw: int, tx: str, token: str, hop: int):
        sender = sender.lower()
        if sender == wallet or hop > SPEC["funding"]["max_hops"]:
            return
        amount = amount_raw / 1_000_000
        if amount < SPEC["funding"]["dust_usd"] or amount > 5_000_000:
            return
        bts = block_ts(con, block)
        if bts > threshold_ts:
            return
        if sender in best_amount and amount <= best_amount[sender]:
            return
        first_time = sender not in best_amount
        best_amount[sender] = amount
        code, nonce = address_state(con, sender, block)
        kind = classify_address(code, nonce, sender in INFRA, None)
        if first_time:
            con.execute("insert into edges values(?,?,?,?,?,?,?,?,?,?)",
                        (wallet, hop, sender, kind, token, amount, tx, block, bts, "inflow"))
        else:
            con.execute("""update edges set amount_usd=?, tx=?, block=?, block_ts=?, hop=?, prelim_class=?
                           where wallet=? and sender=? and kind='inflow'""",
                        (amount, tx, block, bts, hop, kind, wallet, sender))
            return
        if kind == "passthrough_eoa" and hop < SPEC["funding"]["max_hops"]:
            for lg in logs_to(sender, max(1, block - SPEC["funding"]["lookback_blocks"]), block):
                src = "0x" + lg["topics"][1][-40:]
                consider(src, int(lg["blockNumber"], 16), int(lg["data"], 16), lg["transactionHash"].lower(),
                         lg["address"].lower(), hop + 1)
        if kind == "contract" and hop < SPEC["funding"]["max_hops"]:
            receipt = rpc("eth_getTransactionReceipt", [tx])
            if not receipt:
                return
            walked = payer_of_deposit(receipt.get("logs") or [], wallet if hop == 1 else sender)
            if walked and walked.get("payer"):
                consider(walked["payer"], int(receipt["blockNumber"], 16), walked["value"],
                         tx, walked.get("token") or token, hop + 1)

    for lg in logs_to(wallet, start, end):
        tx = lg["transactionHash"].lower()
        if tx in trade_txs:
            continue
        src = "0x" + lg["topics"][1][-40:]
        consider(src, int(lg["blockNumber"], 16), int(lg["data"], 16), tx, lg["address"].lower(), 1)
    # exits: withdrawal receipts only, so a bridge solver is not walked into a false person
    for tx, in con.execute(
            """select tx from activity where wallet=? and typ='WITHDRAWAL' and ts>=? and tx!=''""",
            (wallet, threshold_ts)):
        receipt = rpc("eth_getTransactionReceipt", [tx])
        if not receipt:
            continue
        moves = transfers(receipt.get("logs") or [])
        dest = forward_destination(moves, wallet, INFRA)
        if not dest or not dest.get("destination"):
            con.execute("insert into edges values(?,?,?,?,?,?,?,?,?,?)",
                        (wallet, 1, None, "service_infra" if dest and dest.get("stopped") == "infra" else "unresolved",
                         None, (dest or {}).get("value", 0) / 1_000_000 if dest else 0, tx,
                         int(receipt["blockNumber"], 16), None, "cashout"))
            continue
        block = int(receipt["blockNumber"], 16)
        code, nonce = address_state(con, dest["destination"], block)
        kind = classify_address(code, nonce, dest["destination"] in INFRA, None)
        con.execute("insert into edges values(?,?,?,?,?,?,?,?,?,?)",
                    (wallet, 1 + len(dest["path"]), dest["destination"], kind, dest["token"],
                     dest["value"] / 1_000_000, tx, block, block_ts(con, block), "cashout"))


def funding_queue(con: sqlite3.Connection) -> list[str]:
    """Positive control, then members of the tightest fresh groups, then a seeded matched set."""
    fresh_rows = list(con.execute(
        """select e.wallet, e.condition_id, e.outcome, e.threshold_ts, m.stratum, m.family
           from exposures e
           join fresh f on f.wallet=e.wallet and f.condition_id=e.condition_id
           join markets m on m.condition_id=e.condition_id
           join fetches t on t.condition_id=e.condition_id and t.status='ok'
           where e.eligible=1 and f.qualifying=1 and m.in_sample=1"""))
    by_market = defaultdict(list)
    for row in fresh_rows:
        by_market[(row[1], row[2])].append({"wallet": row[0], "threshold_ts": row[3], "stratum": row[4]})
    ranked = []
    for (condition, outcome), members in by_market.items():
        for window in WINDOWS:
            subset = tight_subset(members, window)
            if not subset:
                continue
            for member in subset:
                ranked.append((window, member["wallet"], condition))
    ranked.sort()
    queue = []
    seen = set()
    for wallet in NOBEL_WALLETS:
        if wallet not in seen:
            queue.append(wallet)
            seen.add(wallet)
    for _window, wallet, _condition in ranked:
        if wallet not in seen:
            queue.append(wallet)
            seen.add(wallet)
    # matched wallets: eligible, qualifying, not already queued, stable order
    extras = sorted({row[0] for row in fresh_rows if row[0] not in seen})
    # one matched wallet per queued group wallet, capped, using the frozen seed order
    import random
    rng = random.Random(SPEC["tests"]["seed"])
    rng.shuffle(extras)
    target_extra = min(len(extras), max(0, len(queue)))
    for wallet in extras[:target_extra]:
        queue.append(wallet)
        seen.add(wallet)
    return queue[:SPEC["funding"]["trace_cap"]]


def funding(con: sqlite3.Connection):
    queue = funding_queue(con)
    have = {r[0] for r in con.execute("select wallet from trace_status where status='ok'")}
    todo = [w for w in queue if w not in have]
    print(f"funding queue {len(queue)} remaining {len(todo)}", flush=True)
    for i, wallet in enumerate(todo, 1):
        threshold = con.execute(
            """select min(threshold_ts) from exposures where wallet=? and eligible=1""", (wallet,)).fetchone()[0]
        try:
            if threshold is None:
                raise RuntimeError("no threshold")
            con.execute("delete from edges where wallet=?", (wallet,))
            trace_wallet(con, wallet, int(threshold))
            con.execute("insert into trace_status values(?,?,?) on conflict(wallet) do update set status=excluded.status, note=excluded.note",
                        (wallet, "ok", None))
            con.commit()
        except Exception as exc:  # noqa: BLE001
            con.execute("insert into trace_status values(?,?,?) on conflict(wallet) do update set status=excluded.status, note=excluded.note",
                        (wallet, "error", str(exc)[:240]))
            con.commit()
        if i % 10 == 0 or i == len(todo):
            print(f"funding {i}/{len(todo)}", flush=True)


def apply_fanout(con) -> dict[tuple, str]:
    counts = defaultdict(set)
    for wallet, sender, kind in con.execute("select wallet, sender, prelim_class from edges where kind='inflow' and sender is not null"):
        if kind in ("plain_eoa", "passthrough_eoa"):
            counts[sender].add(wallet)
    relabel = {}
    for sender, wallets in counts.items():
        if len(wallets) > SPEC["funding"]["fanout_max"]:
            relabel[sender] = "high_fanout_service"
    return relabel


def primary_labels(con, relabel: dict[str, str], kind: str) -> dict[str, str | None]:
    """Largest plain-EOA counterparty at or above the link floor. kind is inflow or cashout."""
    best: dict[str, tuple] = {}
    floor = SPEC["funding"]["min_link_usd"]
    for wallet, sender, prelim, amount, block_ts in con.execute(
            "select wallet, sender, prelim_class, amount_usd, block_ts from edges where kind=? and sender is not null", (kind,)):
        klass = relabel.get(sender, prelim)
        if klass != "plain_eoa" or amount < floor:
            continue
        current = best.get(wallet)
        if current is None or amount > current[0]:
            best[wallet] = (amount, sender)
    return {wallet: sender for wallet, (amount, sender) in best.items()}


def qualifying_rows(con, stratum: str | None, family_name: str | None, denominator_only: bool):
    sql = """select e.wallet, e.condition_id, e.outcome, e.threshold_ts, m.family, m.stratum, m.volume, m.in_denominator
             from exposures e
             join fresh f on f.wallet=e.wallet and f.condition_id=e.condition_id and f.qualifying=1
             join markets m on m.condition_id=e.condition_id
             join fetches t on t.condition_id=e.condition_id and t.status='ok'
             where e.eligible=1 and m.in_sample=1"""
    out = []
    for row in con.execute(sql):
        if stratum and row[5] != stratum:
            continue
        if family_name and row[4] != family_name:
            continue
        if denominator_only and not row[7]:
            continue
        out.append({"wallet": row[0], "market": row[1], "outcome": row[2], "threshold_ts": row[3],
                    "family": row[4], "stratum": row[5], "volume": row[6]})
    return out


def run_h1(con, rows, labels, permutations: int):
    wallets = sorted({r["wallet"] for r in rows})
    assignments = []
    for wallet in wallets:
        ts = min(r["threshold_ts"] for r in rows if r["wallet"] == wallet)
        label = labels.get(wallet)
        assignments.append({"id": wallet, "month": month_key(ts), "label": label})

    def stat(assigned):
        return h1_stat(rows, {a["id"]: a["label"] for a in assigned})

    return shuffle_labels(assignments, permutations, SPEC["tests"]["seed"], stat)


def analyze(con: sqlite3.Connection):
    relabel = apply_fanout(con)
    funders = primary_labels(con, relabel, "inflow")
    destinations = primary_labels(con, relabel, "cashout")
    perms = SPEC["tests"]["permutations"]
    alpha = SPEC["tests"]["corrected_alpha"]
    test_info = qualifying_rows(con, "TEST", "INFO", True)
    test_ctrl = qualifying_rows(con, "TEST", "PUBLIC_PROCESS", True)
    h1 = run_h1(con, test_info, funders, perms) if test_info else {"observed": 0, "p": None, "null_mean": None, "permutations": perms}
    h1_ctrl = run_h1(con, test_ctrl, funders, perms) if test_ctrl else {"observed": 0, "p": None, "null_mean": None, "permutations": perms}
    h3 = run_h1(con, test_info, destinations, perms) if test_info else {"observed": 0, "p": None, "null_mean": None, "permutations": perms}

    # H2: market-level 24h fresh pair, INFO vs control, inside the test denominator
    identities = []
    market_rows = list(con.execute(
        """select m.condition_id, m.family, m.volume from markets m
           join fetches f on f.condition_id=m.condition_id and f.status='ok'
           where m.in_sample=1 and m.in_denominator=1 and m.stratum='TEST'
             and m.family in ('INFO','PUBLIC_PROCESS')"""))
    by_mo = defaultdict(list)
    for row in test_info + test_ctrl:
        by_mo[(row["market"], row["outcome"])].append(row["threshold_ts"])
    for condition, fam, volume in market_rows:
        hit = 0
        for outcome in ("YES", "NO"):
            if has_tight_group(by_mo.get((condition, outcome), []), BEHAVIOR_W):
                hit = 1
        identities.append((condition, fam, volume, hit))
    import math
    log_vols = [math.log10(v) if v and v > 0 else 0.0 for _c, _f, v, _h in identities]
    qs = quintiles(log_vols)
    h2_markets = [{"family": fam, "quintile": q, "hit": hit} for (_c, fam, _v, hit), q in zip(identities, qs)]
    h2 = family_permutation(h2_markets, perms, SPEC["tests"]["seed"]) if h2_markets else {"observed": None, "p": None, "null_mean": None}

    n_test_info = sum(1 for _c, fam, _v, _h in identities if fam == "INFO")
    groups_7d = 0
    groups_traced = 0
    for (condition, outcome), times_wallets in _group_members(test_info).items():
        if not has_tight_group([t for t, _w in times_wallets], PRIMARY_W):
            continue
        groups_7d += 1
        wallets = [w for _t, w in times_wallets]
        traced = all(con.execute("select status from trace_status where wallet=?", (w,)).fetchone() == ("ok",) for w in wallets)
        # only members of a tight subset need to be traced
        subset = tight_subset([{"wallet": w, "threshold_ts": t} for t, w in times_wallets], PRIMARY_W) or []
        traced = all(con.execute("select status from trace_status where wallet=?", (m["wallet"],)).fetchone() == ("ok",)
                     for m in subset)
        if traced:
            groups_traced += 1
    h1_verdict = verdict_h1(h1.get("p"), h1_ctrl.get("p"), h1.get("observed") or 0, n_test_info, groups_7d, groups_traced, alpha)
    answer = central_answer(h1_verdict, h2.get("p"), h3.get("p"), alpha)

    validation = {}
    for name, labels in (("H1", funders), ("H3", destinations)):
        rows = qualifying_rows(con, "VALIDATION", "INFO", True)
        validation[name] = run_h1(con, rows, labels, perms) if rows else {"observed": 0, "p": None, "null_mean": None}

    pipeline_check = pipeline_check_result(con, funders)
    stats = {
        "spec_sha256": SPEC_SHA,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "answer": answer,
        "h1_verdict": h1_verdict,
        "alpha": alpha,
        "H1": h1,
        "H1_control": h1_ctrl,
        "H2": h2,
        "H3": h3,
        "validation_info": validation,
        "test_info_markets": n_test_info,
        "test_groups_7d": groups_7d,
        "test_groups_traced": groups_traced,
        "pipeline_check": pipeline_check,
        "frame": {f"{a}:{b}": c for a, b, c in con.execute("select family, stratum, count(*) from markets group by 1,2")},
        "sample": {f"{a}:{b}": c for a, b, c in con.execute(
            "select family, stratum, count(*) from markets where in_sample=1 group by 1,2")},
        "fetches": dict(con.execute("select status, count(*) from fetches group by 1")),
        "eligible": con.execute("select count(*) from exposures where eligible=1").fetchone()[0],
        "qualifying": con.execute("select count(*) from fresh where qualifying=1").fetchone()[0],
        "traced_ok": con.execute("select count(*) from trace_status where status='ok'").fetchone()[0],
        "traced_error": con.execute("select count(*) from trace_status where status='error'").fetchone()[0],
        "activity_cap_hit": activity_queue_was_capped(con),
    }
    write_tables(con, relabel, funders, destinations, stats, identities)
    stats["csv_rows"] = {name: sum(1 for _ in open(DATA / name)) - 1 for name in (
        "eligible_wallets.csv", "funding_edges.csv", "wallet_clusters.csv", "market_exposures.csv",
        "cashout_edges.csv", "cluster_statistics.csv", "matched_controls.csv", "data_coverage.csv")}
    (DATA / "stats.json").write_text(json.dumps(stats, indent=2, sort_keys=True) + "\n")
    write_figure(stats)
    write_dossiers(con, relabel, funders, destinations, pipeline_check)
    write_prose(stats)
    print("answer", answer, "H1", h1_verdict, "pipeline", pipeline_check.get("passed"), flush=True)


def _group_members(rows):
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["market"], row["outcome"])].append((row["threshold_ts"], row["wallet"]))
    return grouped


def activity_queue_was_capped(con) -> bool:
    n = con.execute(
        """select count(distinct e.wallet) from exposures e
           join markets m on m.condition_id=e.condition_id
           where e.eligible=1 and m.in_sample=1""").fetchone()[0]
    return n > SPEC["freshness"]["activity_cap"]


def pipeline_check_result(con, funders: dict[str, str]) -> dict:
    yes = {}
    for wallet, committed in con.execute(
            "select wallet, committed from exposures where condition_id=? and outcome='YES' and eligible=1", (PC,)):
        yes[wallet] = committed
    present = [w for w in NOBEL_WALLETS if w in yes]
    linked = [w for w in present if funders.get(w) == NOBEL_KEY]
    fetch = con.execute("select status, note from fetches where condition_id=?", (PC,)).fetchone()
    return {
        "market_status": None if fetch is None else fetch[0],
        "market_note": None if fetch is None else fetch[1],
        "known_wallets_eligible_yes": len(present),
        "known_wallets_with_key": len(linked),
        "passed": len(present) >= 4 and len(linked) >= 2,
        "eligible_known": present,
        "linked_known": linked,
    }


def write_tables(con, relabel, funders, destinations, stats, identities):
    def dump(name, header, rows):
        path = DATA / name
        with path.open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)

    eligible = []
    for row in con.execute(
            """select e.wallet, e.condition_id, e.outcome, e.committed, e.gross_buy, e.sell_proceeds,
                      e.threshold_ts, e.threshold_price, e.vwap, f.labels, f.qualifying, f.history, m.family, m.stratum
               from exposures e join markets m on m.condition_id=e.condition_id
               left join fresh f on f.wallet=e.wallet and f.condition_id=e.condition_id
               where e.eligible=1 and m.in_sample=1
               order by e.threshold_ts"""):
        eligible.append(row)
    dump("eligible_wallets.csv",
         ["wallet", "condition_id", "outcome", "capital_committed_usd", "gross_buy_usd", "sell_proceeds_usd",
          "threshold_ts", "threshold_price", "vwap_to_threshold", "freshness", "qualifying", "history", "family", "stratum"],
         eligible)

    exposures = list(con.execute(
        """select wallet, condition_id, outcome, gross_buy, sell_proceeds, committed, threshold_ts, n_buys, n_sells, eligible
           from exposures order by condition_id, outcome, wallet"""))
    dump("market_exposures.csv",
         ["wallet", "condition_id", "outcome", "gross_buy_usd", "sell_proceeds_usd", "capital_committed_usd",
          "threshold_ts", "n_buys", "n_sells", "eligible"], exposures)

    fund_rows = []
    for row in con.execute("select wallet, hop, sender, prelim_class, token, amount_usd, tx, block, block_ts from edges where kind='inflow'"):
        sender = row[2]
        fund_rows.append((*row[:3], relabel.get(sender, row[3]), *row[4:]))
    dump("funding_edges.csv",
         ["wallet", "hop", "sender", "sender_class", "token", "amount_usd", "tx", "block", "block_ts"], fund_rows)
    cash_rows = []
    for row in con.execute("select wallet, hop, sender, prelim_class, token, amount_usd, tx, block, block_ts from edges where kind='cashout'"):
        sender = row[2]
        cash_rows.append((*row[:3], relabel.get(sender, row[3]) if sender else row[3], *row[4:]))
    dump("cashout_edges.csv",
         ["wallet", "hop", "destination", "destination_class", "token", "amount_usd", "tx", "block", "block_ts"], cash_rows)

    clusters = cluster_rows(con, relabel, funders, destinations)
    dump("wallet_clusters.csv",
         ["cluster_id", "condition_id", "outcome", "window_seconds", "wallet", "threshold_ts", "committed_usd",
          "freshness", "primary_funder", "primary_destination", "evidence_class", "family", "stratum", "in_denominator"],
         clusters)

    coverage = list(con.execute(
        """select m.condition_id, m.family, m.stratum, m.end_date, m.volume, m.in_sample, m.in_denominator, m.forced_control,
                  coalesce(f.status,'not_fetched'), coalesce(f.pages,0), coalesce(f.n_rows,0), coalesce(f.note,''),
                  (select count(*) from exposures e where e.condition_id=m.condition_id and e.eligible=1),
                  (select count(*) from fresh fr where fr.condition_id=m.condition_id and fr.qualifying=1)
           from markets m left join fetches f on f.condition_id=m.condition_id
           where m.family != 'EXCLUDED'
           order by m.stratum, m.end_date, m.condition_id"""))
    dump("data_coverage.csv",
         ["condition_id", "family", "stratum", "end_date", "volume_usd", "in_sample", "in_denominator", "forced_control",
          "fetch_status", "pages", "n_fills", "note", "n_eligible", "n_qualifying_fresh"], coverage)

    matched = []
    # rebuild quintile membership from identities, which is TEST only
    import math
    log_vols = [math.log10(v) if v and v > 0 else 0 for _c, _f, v, _h in identities]
    qs = quintiles(log_vols)
    buckets = defaultdict(lambda: defaultdict(lambda: [0, 0]))
    for (_c, fam, _v, hit), q in zip(identities, qs):
        buckets[q][fam][0] += 1
        buckets[q][fam][1] += hit
    for q, fams in sorted(buckets.items()):
        for fam, (n, hits) in sorted(fams.items()):
            matched.append((q, fam, n, hits, hits / n if n else 0))
    dump("matched_controls.csv",
         ["volume_quintile", "family", "n_markets", "n_with_24h_fresh_pair", "rate"], matched)

    stat_rows = [
        ["answer", "", stats["answer"], ""],
        ["h1_verdict", "TEST:INFO", stats["h1_verdict"], ""],
        ["H1_observed", "TEST:INFO", stats["H1"].get("observed"), stats["H1"].get("p")],
        ["H1_null_mean", "TEST:INFO", stats["H1"].get("null_mean"), ""],
        ["H1_control_observed", "TEST:PUBLIC_PROCESS", stats["H1_control"].get("observed"), stats["H1_control"].get("p")],
        ["H2_difference", "TEST", stats["H2"].get("observed"), stats["H2"].get("p")],
        ["H2_null_mean", "TEST", stats["H2"].get("null_mean"), ""],
        ["H3_observed", "TEST:INFO", stats["H3"].get("observed"), stats["H3"].get("p")],
        ["H3_null_mean", "TEST:INFO", stats["H3"].get("null_mean"), ""],
        ["validation_H1", "VALIDATION:INFO", stats["validation_info"]["H1"].get("observed"), stats["validation_info"]["H1"].get("p")],
        ["validation_H3", "VALIDATION:INFO", stats["validation_info"]["H3"].get("observed"), stats["validation_info"]["H3"].get("p")],
        ["pipeline_check_passed", "DISCOVERY", int(stats["pipeline_check"]["passed"]), ""],
        ["test_info_markets", "TEST:INFO", stats["test_info_markets"], ""],
        ["test_groups_7d", "TEST:INFO", stats["test_groups_7d"], ""],
        ["corrected_alpha", "", stats["alpha"], ""],
    ]
    dump("cluster_statistics.csv", ["metric", "stratum", "value", "p"], stat_rows)


def cluster_rows(con, relabel, funders, destinations):
    rows = qualifying_rows(con, None, None, False)
    grouped = defaultdict(list)
    meta = {}
    for row in rows:
        grouped[(row["market"], row["outcome"])].append(row)
        meta[row["market"]] = row
    out = []
    for (condition, outcome), members in grouped.items():
        market = con.execute("select family, stratum, in_denominator, question from markets where condition_id=?", (condition,)).fetchone()
        for window in WINDOWS:
            subset = tight_subset(members, window)
            if not subset:
                continue
            evidence = class_for(con, subset, funders, destinations, relabel)
            cluster_id = hashlib.sha256(f"{condition}|{outcome}|{window}|{','.join(sorted(m['wallet'] for m in subset))}".encode()).hexdigest()[:16]
            for member in subset:
                fresh = con.execute("select labels from fresh where wallet=? and condition_id=?", (member["wallet"], condition)).fetchone()
                committed = con.execute(
                    "select committed from exposures where wallet=? and condition_id=? and outcome=?",
                    (member["wallet"], condition, outcome)).fetchone()
                out.append((cluster_id, condition, outcome, window, member["wallet"], member["threshold_ts"],
                            None if committed is None else committed[0], "" if fresh is None else fresh[0],
                            funders.get(member["wallet"]) or "", destinations.get(member["wallet"]) or "",
                            evidence, market[0], market[1], market[2]))
    return out


def class_for(con, subset, funders, destinations, relabel) -> str:
    wallets = [m["wallet"] for m in subset]
    traced = []
    for wallet in wallets:
        status = con.execute("select status from trace_status where wallet=?", (wallet,)).fetchone()
        traced.append(status[0] if status else "missing")
    complete = all(s == "ok" for s in traced)
    funder_counts = defaultdict(int)
    dest_counts = defaultdict(int)
    for wallet in wallets:
        if funders.get(wallet):
            funder_counts[funders[wallet]] += 1
        if destinations.get(wallet):
            dest_counts[destinations[wallet]] += 1
    has_funder = any(v >= 2 for v in funder_counts.values())
    has_dest = any(v >= 2 for v in dest_counts.values())
    times = sorted(m["threshold_ts"] for m in subset)
    within_hour = times[-1] - times[0] <= 3600
    amounts = []
    for wallet in wallets:
        # committed is recovered by the caller only as threshold; use exposures
        pass
    amount_vals = []
    for member in subset:
        row = con.execute(
            """select committed from exposures e where e.wallet=? and e.threshold_ts=?""",
            (member["wallet"], member["threshold_ts"])).fetchone()
        if row and row[0]:
            amount_vals.append(row[0])
    similar = False
    if len(amount_vals) >= 2 and min(amount_vals) > 0:
        similar = max(amount_vals) / min(amount_vals) <= 1.10
    service_only = False
    if complete and not has_funder and not has_dest:
        senders = []
        for wallet in wallets:
            for sender, prelim in con.execute(
                    "select sender, prelim_class from edges where wallet=? and kind='inflow'", (wallet,)):
                senders.append(relabel.get(sender, prelim))
        service_only = bool(senders) and all(s in ("contract", "service_infra", "busy_eoa", "high_fanout_service") for s in senders)
    contradicted = False
    if has_funder:
        # a shared id that the fan-out pass relabelled is not a private link; class_for only
        # sees primary labels, which are already plain. Nothing extra to contradict here.
        contradicted = False
    return evidence_class(has_funder, has_dest, similar, False, within_hour, service_only, complete, contradicted)


def write_figure(stats):
    fig = ROOT / "figures"
    fig.mkdir(parents=True, exist_ok=True)
    bars = [
        ("H1 clusters", stats["H1"].get("observed") or 0),
        ("H1 null mean", stats["H1"].get("null_mean") or 0),
        ("H3 clusters", stats["H3"].get("observed") or 0),
        ("H3 null mean", stats["H3"].get("null_mean") or 0),
    ]
    width = 480
    height = 220
    max_v = max([v for _n, v in bars] + [1])
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<text x="16" y="24" font-family="sans-serif" font-size="14">Test stratum: observed clusters and null means</text>']
    for i, (name, value) in enumerate(bars):
        bh = 120 * (value / max_v)
        x = 40 + i * 110
        y = 170 - bh
        parts.append(f'<rect x="{x}" y="{y:.1f}" width="70" height="{bh:.1f}" fill="#234"/>')
        parts.append(f'<text x="{x}" y="190" font-family="sans-serif" font-size="11">{name}</text>')
        parts.append(f'<text x="{x}" y="{y - 4:.1f}" font-family="sans-serif" font-size="11">{value:.2f}</text>')
    parts.append("</svg>")
    (fig / "test_stratum_rates.svg").write_text("\n".join(parts) + "\n")


def write_dossiers(con, relabel, funders, destinations, pipeline_check):
    folder = ROOT / "evidence" / "dossiers"
    folder.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Pipeline check: Nobel Peace Prize 2025",
        "",
        "This dossier checks that the collector can recover a link already published in this repository.",
        "It is not a new confirmatory result and it is not a finding about any person.",
        "",
        f"- Market `{PC}`",
        f"- Tape status: {pipeline_check.get('market_status')} ({pipeline_check.get('market_note')})",
        f"- Known wallets eligible on YES: {pipeline_check.get('known_wallets_eligible_yes')}",
        f"- Of those, primary funder is the published key: {pipeline_check.get('known_wallets_with_key')}",
        f"- Check passed: {pipeline_check.get('passed')}",
        "",
        "Published key `0xe206961002feebd9edb152eed9b630a351874043`.",
        "A passed check means the public transfers were read again. It does not identify a person and it does not show inside information.",
        "",
    ]
    (folder / "positive-control-nobel.md").write_text("\n".join(lines))
    by_id = defaultdict(list)
    for row in cluster_rows(con, relabel, funders, destinations):
        if row[3] == PRIMARY_W:
            by_id[row[0]].append(row)
    ranked = sorted(by_id.values(), key=lambda members: (
        0 if members[0][10] in ("VERIFIED FINANCIAL LINK", "CORROBORATED COORDINATION") else
        1 if members[0][10] == "REFUTED" else
        2 if members[0][10] == "SHARED SERVICE ONLY" else
        3 if members[0][10] == "UNRESOLVED" else 4,
        members[0][12] != "TEST"))
    index = ["# Dossier index", "", "A financial link is a transfer that was read. It is not a common owner and it is not an offence.", ""]
    for members in ranked[:40]:
        head = members[0]
        cluster_id, condition, outcome = head[0], head[1], head[2]
        question = con.execute("select question, event_slug, end_date from markets where condition_id=?", (condition,)).fetchone()
        body = [
            f"# Cluster {cluster_id}",
            "",
            f"- Evidence class: **{head[10]}**",
            f"- Market: {question[0]}",
            f"- Event slug: {question[1]}",
            f"- Condition: `{condition}`",
            f"- Outcome: {outcome}",
            f"- Family / stratum: {head[11]} / {head[12]}",
            f"- In confirmatory denominator: {bool(head[13])}",
            f"- Scheduled end: {question[2]}",
            "",
            "| Wallet | Threshold (UTC) | Committed USD | Freshness | Primary funder | Primary destination |",
            "|---|---|---:|---|---|---|",
        ]
        for member in members:
            when = datetime.fromtimestamp(member[5], timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            committed = "" if member[6] is None else f"{member[6]:.2f}"
            body.append(f"| `{member[4]}` | {when} | {committed} | {member[7]} | `{member[8]}` | `{member[9]}` |")
        body += [
            "",
            "Public information time: not collected. This run does not date announcements.",
            "Approximate profit and loss is not used in any test.",
            "Alternative explanations: independent traders, a shared service that this trace could not see past, or a proxy whose operator is older than the address.",
            "Attribution limit: the trace stops at contracts, busy keys, bridges and any hop the window did not contain.",
            "",
        ]
        (folder / f"{cluster_id}.md").write_text("\n".join(body))
        index.append(f"- [{cluster_id}]({cluster_id}.md) — {head[10]} — {head[12]} {head[11]} — {question[1]}")
    if len(by_id) > 40:
        index.append("")
        index.append(f"{len(by_id) - 40} further 7-day clusters are in wallet_clusters.csv and are not given a separate dossier.")
    (folder / "INDEX.md").write_text("\n".join(index) + "\n")


def write_prose(stats):
    pc = stats["pipeline_check"]
    h1, h2, h3 = stats["H1"], stats["H2"], stats["H3"]
    answer = stats["answer"]
    if answer == "NO":
        lead = ("On the pre-registered test stratum, this run does not show fresh-wallet groups whose private funding "
                "or private withdrawals exceed what the month-shuffle expects, and the 24-hour co-timing gap versus "
                "control markets does not clear the corrected threshold.")
    elif answer == "INCONCLUSIVE_COVERAGE":
        lead = ("The confirmatory test does not meet its coverage floor, so this run does not answer the rate question. "
                "Any link that was read is in the dossiers and is not a rate.")
    else:
        lead = ("At least one pre-registered test is under the corrected threshold. The dossiers list those clusters. "
                "A link is not a person and it is not evidence of inside information.")
    readme = f"""# Fresh wallet clusters

{lead}

The central question, the population, the $1,000 rule and the three tests are frozen in [preregistration.json](preregistration.json) (SHA-256 `{stats['spec_sha256']}`).

| Item | Value |
|---|---|
| Central answer | `{answer}` |
| H1 verdict | `{stats['h1_verdict']}` |
| H1 observed clusters (test, information markets) | {h1.get('observed')} (null mean {h1.get('null_mean')}, p {h1.get('p')}) |
| H2 co-timing difference | {h2.get('observed')} (p {h2.get('p')}) |
| H3 cash-out clusters | {h3.get('observed')} (null mean {h3.get('null_mean')}, p {h3.get('p')}) |
| Corrected alpha | {stats['alpha']} |
| Pipeline check (published Nobel group) | passed={pc.get('passed')} |

Read [FINDINGS.md](FINDINGS.md) for the counts and [NEGATIVE_RESULTS.md](NEGATIVE_RESULTS.md) for what did not hold. [METHODOLOGY.md](METHODOLOGY.md) records the prior work this study does not repeat. [REPRODUCE.md](REPRODUCE.md) is the run book.

Nothing here identifies a person or alleges an offence.
"""
    (ROOT / "README.md").write_text(readme)
    findings = f"""# Findings

Generated {stats['generated_utc']} from `data/stats.json`. The prose states what the tables already contain.

## Answer

{lead}

Corrected threshold for the three tests: {stats['alpha']} (0.05 / 3).

| Test | Stratum | Observed | Null mean | p | Role |
|---|---|---:|---:|---:|---|
| H1 private funder | TEST × INFO | {h1.get('observed')} | {h1.get('null_mean')} | {h1.get('p')} | confirmatory |
| H1 specificity | TEST × PUBLIC_PROCESS | {stats['H1_control'].get('observed')} | {stats['H1_control'].get('null_mean')} | {stats['H1_control'].get('p')} | qualifier |
| H2 24-hour co-timing | TEST, INFO minus control | {h2.get('observed')} | {h2.get('null_mean')} | {h2.get('p')} | confirmatory |
| H3 private cash-out | TEST × INFO | {h3.get('observed')} | {h3.get('null_mean')} | {h3.get('p')} | confirmatory |
| H1 replication | VALIDATION × INFO | {stats['validation_info']['H1'].get('observed')} | {stats['validation_info']['H1'].get('null_mean')} | {stats['validation_info']['H1'].get('p')} | replication, not a replacement |
| H3 replication | VALIDATION × INFO | {stats['validation_info']['H3'].get('observed')} | {stats['validation_info']['H3'].get('null_mean')} | {stats['validation_info']['H3'].get('p')} | replication |

H1 verdict: **{stats['h1_verdict']}**. Test information markets with a complete tape: {stats['test_info_markets']}. Seven-day fresh groups in that set: {stats['test_groups_7d']}, of which fully traced: {stats['test_groups_traced']}.

## What a positive cluster would mean

`VERIFIED FINANCIAL LINK` means two qualifying wallets on one outcome, inside seven days, with the same plain EOA as the largest inbound transfer of at least $100 before each threshold. `CORROBORATED COORDINATION` adds a second observation (amounts within 10 percent, both a funder and a cash-out, or threshold times inside one hour). Neither class names an owner. Neither class is a statement about information.

## Pipeline check

The published Nobel 2025 key and eight wallets are a check that this code can read a known link. Eligible known wallets on YES: {pc.get('known_wallets_eligible_yes')}. Linked to the published key by the primary-funder rule: {pc.get('known_wallets_with_key')}. Passed: {pc.get('passed')}. Tape: {pc.get('market_status')}.

## Coverage

Catalogue frame (family:stratum): `{json.dumps(stats['frame'], sort_keys=True)}`.

Sample: `{json.dumps(stats['sample'], sort_keys=True)}`.

Trade fetches: `{json.dumps(stats['fetches'], sort_keys=True)}`.

Eligible wallet-outcome rows: {stats['eligible']}. Qualifying fresh rows: {stats['qualifying']}. Funding traces ok/error: {stats['traced_ok']} / {stats['traced_error']}. Activity cap hit: {stats['activity_cap_hit']}.

Markets that reached the page cap are `too_deep` and are out of every rate. Rows under the $100 cash filter that the API still returned are kept and counted in the fetch note. Buys smaller than that filter are not in the tape.

## Dossiers

See [evidence/dossiers/INDEX.md](evidence/dossiers/INDEX.md). Wallet-level rows for every window are in `data/wallet_clusters.csv`.
"""
    (ROOT / "FINDINGS.md").write_text(findings)
    negative = f"""# Negative results

These are results of this run, not a claim about markets the tape did not cover.

- H1 verdict on the test stratum: **{stats['h1_verdict']}**. Observed private-funder clusters: {h1.get('observed')}. One-sided shuffle p: {h1.get('p')}.
- H2 co-timing difference (information minus control): {h2.get('observed')}, p {h2.get('p')}. A positive difference would mean fresh wallets cross $1,000 on the same outcome inside 24 hours more often on information markets than on the matched public-process markets. It would still not be a common owner.
- H3 private cash-out clusters: {h3.get('observed')}, p {h3.get('p')}.
- The validation replication is reported in FINDINGS.md and was not used to change a threshold.
- Shared services are counted in `funding_edges.csv` with a service class. They are not hits.
- Wallets whose activity read failed are `unresolved` and are not treated as fresh. That choice can only hide a group; it cannot create one.
- No announcement clock was built. A purchase before a resolution is not, by itself, a purchase before the public knew.
- The pipeline check being true or false is about this collector. It does not reopen the published Nobel accounting and it does not extend that case to other markets.

If the answer cell in `data/cluster_statistics.csv` is `NO` or `INCONCLUSIVE_COVERAGE`, that is the result of the confirmatory tests. It is not a statement that no coordinated trading exists outside the sample.
"""
    (ROOT / "NEGATIVE_RESULTS.md").write_text(negative)


def main(argv: list[str]):
    command = argv[1] if len(argv) > 1 else "all"
    con = connect()
    steps = {
        "catalogue": [catalogue],
        "sample": [catalogue, choose_sample],
        "trades": [catalogue, choose_sample, trades],
        "activity": [catalogue, choose_sample, trades, exposures, activity, features],
        "funding": [catalogue, choose_sample, trades, exposures, activity, features, funding],
        "analyze": [analyze],
        "all": [catalogue, choose_sample, trades, exposures, activity, features, funding, analyze],
    }
    if command not in steps:
        raise SystemExit("use catalogue, sample, trades, activity, funding, analyze or all")
    for step in steps[command]:
        print("==", step.__name__, flush=True)
        step(con)
    con.close()


if __name__ == "__main__":
    main(sys.argv)
