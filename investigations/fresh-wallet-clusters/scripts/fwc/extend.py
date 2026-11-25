#!/usr/bin/env python3
"""Amendment 002. Same sample, fills from 1 USD up, then the frozen fingerprints.

The cache lives outside the repository. A file over the scan limit must not be written
under investigations/. Raw pages are not published. Failed reads stay errors.
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
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT.parents[1] / "monitoring"))
from phi_engine.chainfund import INFRA, payer_of_deposit  # noqa: E402
from fwc.logic import (  # noqa: E402
    classify_address, commitment, family_permutation, freshness, h1_stat,
    has_tight_group, month_key, quintiles, shuffle_labels,
)

AMEND = json.loads((ROOT / "amendment-002.json").read_text())
DATA = ROOT / "data"
CACHE = Path("/tmp/fwc-extend/cache.sqlite")
FILTER = AMEND["tape"]["cash_filter_usd"]
MIN_USD = 1000.0
UA = {"User-Agent": "Mozilla/5.0 (compatible; research-client/1.0)", "Accept": "application/json",
      "Accept-Encoding": "gzip"}
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOKENS = ["0x3c499c542cef5e3811e1192ce70d8cc03d5c3359", "0x2791bca1f2de4661ed88a30c99a7a9449aa84174",
          "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"]
RPCS = ["https://gateway.tenderly.co/public/polygon", "https://polygon.drpc.org"]
PC = "0x14a3dfeba8b22a32feb0f10763db68bc4d2abeb5bff90e9ae20de53793b35a1d"
NOBEL = {"0xa430506774f9efaf39903ee7e0db1351f66891ca", "0x1973177faa69b94b4afab818e612a7c05b3c01a9",
         "0x03f8aae7ae1687ef7e2d55e4429e72e9a95d8541", "0xa9c57a20cb8433a269976bb35eb872bd11380bd9",
         "0x4bac00c61a02275d681f3857cdc5ae315f1f7075", "0x8507124d416dd181ea552e01a0dfed19ab0b1086",
         "0x2612496ab8f1d774f116f28b50769971936c92de", "0x234cc49e43dff8b3207bbd3a8a2579f339cb9867"}
_lock = threading.Lock()
_next = [0.0]


def pace(interval=0.1):
    with _lock:
        delay = _next[0] - time.time()
        _next[0] = max(time.time(), _next[0]) + interval
    if delay > 0:
        time.sleep(delay)


def http_json(url: str):
    last = "none"
    for attempt in range(6):
        pace()
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=45) as resp:
                raw = resp.read()
                if resp.headers.get("Content-Encoding") == "gzip" or raw[:2] == b"\x1f\x8b":
                    raw = gzip.decompress(raw)
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            last = f"HTTP {exc.code}"
            if exc.code not in (429, 500, 502, 503, 504):
                raise RuntimeError(f"{url[:140]} :: {last}") from exc
            time.sleep(min(40, 2 * (attempt + 1)))
        except Exception as exc:  # noqa: BLE001
            last = repr(exc)[:160]
            time.sleep(min(20, 1.5 * (attempt + 1)))
    raise RuntimeError(f"{url[:140]} :: {last}")


def rpc(method, params, log_range=False):
    last = "none"
    for url in ([RPCS[0]] if log_range else RPCS):
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
                    last = str(payload["error"])[:180]
                    if "100 blocks" in last:
                        break
                    time.sleep(0.4 * (attempt + 1))
                    continue
                return payload.get("result")
            except Exception as exc:  # noqa: BLE001
                last = repr(exc)[:180]
                time.sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"rpc {method} failed: {last}")


def connect() -> sqlite3.Connection:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(CACHE, timeout=120)
    con.execute("pragma journal_mode=wal")
    con.execute("pragma synchronous=normal")
    con.executescript("""
    create table if not exists markets(
      condition_id text primary key, family text, stratum text, volume real,
      in_denominator integer, forced integer, max_pages integer);
    create table if not exists fetches(
      condition_id text primary key, status text, pages integer, n_rows integer, under100 integer, note text);
    create table if not exists fills(
      condition_id text, ts integer, wallet text, outcome text, side text, price real, size real, tx text);
    create table if not exists exposures(
      wallet text, condition_id text, outcome text, committed real, gross_buy real, sell_proceeds real,
      threshold_ts integer, threshold_price real, eligible integer,
      primary key(wallet, condition_id, outcome));
    create table if not exists activity(wallet text, ts integer, typ text, condition_id text, side text, usdc real, tx text);
    create table if not exists activity_status(wallet text primary key, status text, has_more integer, note text);
    create table if not exists fresh(
      wallet text, condition_id text, labels text, qualifying integer, history text,
      primary key(wallet, condition_id));
    create table if not exists edges(
      wallet text, hop integer, sender text, prelim_class text, amount_usd real, tx text,
      block integer, block_ts integer, kind text, source text);
    create table if not exists trace_status(wallet text primary key, status text, note text);
    create table if not exists blocks(n integer primary key, ts integer);
    create table if not exists addr_state(address text, block integer, code integer, nonce integer, primary key(address, block));
    create table if not exists meta(k text primary key, v text);
    """)
    con.commit()
    return con


def load_sample(con: sqlite3.Connection):
    if con.execute("select count(*) from markets").fetchone()[0]:
        return
    rows = []
    with (DATA / "data_coverage.csv").open() as handle:
        for row in csv.DictReader(handle):
            if row["in_sample"] != "1":
                continue
            cap = AMEND["tape"]["positive_control_max_pages"] if row["condition_id"] == PC else AMEND["tape"]["max_pages"]
            rows.append((row["condition_id"], row["family"], row["stratum"], float(row["volume_usd"] or 0),
                         int(row["in_denominator"]), int(row["forced_control"]), cap))
    con.executemany("insert into markets values(?,?,?,?,?,?,?)", rows)
    con.commit()
    print("sample", len(rows), flush=True)


def fetch_one(condition: str, cap: int):
    rows, cursor, pages, under, last = [], None, 0, 0, None
    while pages < cap:
        url = ("https://data-api.polymarket.com/v2/trades?limit=1000&filter_type=CASH"
               f"&filter_amount={FILTER}&taker_only=false&condition={condition}")
        if cursor:
            url += "&cursor=" + quote(cursor, safe="")
        payload = http_json(url)
        data = payload.get("data")
        page = payload.get("pagination") or {}
        if not isinstance(data, list):
            raise RuntimeError("trade schema")
        pages += 1
        for raw in data:
            if str(raw.get("condition_id", "")).lower() != condition:
                raise RuntimeError("row from another market")
            outcome = str(raw.get("outcome", "")).upper()
            if outcome not in ("YES", "NO"):
                raise RuntimeError("outcome")
            side = raw.get("side")
            price, size = float(raw["price"]), float(raw["size"])
            ts = int(raw["timestamp"])
            if side not in ("BUY", "SELL") or not (0 < price <= 1) or size <= 0:
                raise RuntimeError("bad trade")
            if last is not None and ts > last:
                raise RuntimeError("tape order")
            last = ts
            notion = price * size
            if notion < 100:
                under += 1
            rows.append((condition, ts, raw["proxy_wallet"].lower(), outcome, side, price, size,
                         str(raw.get("transaction_hash") or "").lower()))
        cursor = page.get("next_cursor")
        if not page.get("has_more") or not cursor or not data:
            return rows, pages, under, "ok"
    return None, pages, under, "too_deep"


def fetch(con: sqlite3.Connection):
    load_sample(con)
    done = {r[0] for r in con.execute("select condition_id from fetches where status in ('ok','too_deep')")}
    todo = [(c, cap) for c, cap in con.execute("select condition_id, max_pages from markets") if c not in done]
    print("trades to fetch", len(todo), flush=True)

    def work(item):
        try:
            return item[0], fetch_one(*item), None
        except Exception as exc:  # noqa: BLE001
            return item[0], None, str(exc)[:200]

    finished = 0
    with ThreadPoolExecutor(4) as pool:
        for fut in as_completed([pool.submit(work, item) for item in todo]):
            condition, result, err = fut.result()
            with con:
                con.execute("delete from fills where condition_id=?", (condition,))
                if err:
                    con.execute("insert into fetches values(?,?,?,?,?,?) on conflict(condition_id) do update set status=excluded.status, note=excluded.note",
                                (condition, "error", 0, 0, 0, err))
                else:
                    rows, pages, under, status = result
                    if status != "ok":
                        con.execute("insert into fetches values(?,?,?,?,?,?) on conflict(condition_id) do update set status=excluded.status, pages=excluded.pages, note=excluded.note",
                                    (condition, "too_deep", pages, 0, under, "page cap"))
                    else:
                        unique = list({row for row in rows})
                        con.executemany("insert into fills values(?,?,?,?,?,?,?,?)", unique)
                        con.execute("insert into fetches values(?,?,?,?,?,?) on conflict(condition_id) do update set status=excluded.status, pages=excluded.pages, n_rows=excluded.n_rows, under100=excluded.under100, note=excluded.note",
                                    (condition, "ok", pages, len(unique), under, f"dupes={len(rows)-len(unique)}"))
            finished += 1
            if finished % 20 == 0 or finished == len(todo):
                print(f"trades {finished}/{len(todo)}", flush=True)


def build_exposures(con: sqlite3.Connection):
    con.execute("create index if not exists fills_c on fills(condition_id)")
    con.execute("delete from exposures")
    markets = [r[0] for r in con.execute("select condition_id from fetches where status='ok'")]
    for i, condition in enumerate(markets, 1):
        grouped = defaultdict(list)
        for wallet, outcome, ts, side, price, size in con.execute(
                "select wallet, outcome, ts, side, price, size from fills where condition_id=?", (condition,)):
            grouped[(wallet, outcome)].append((ts, side, price, size))
        batch = []
        for (wallet, outcome), fills in grouped.items():
            got = commitment(fills, MIN_USD)
            batch.append((wallet, condition, outcome, got["capital_committed_usd"], got["gross_buy_usd"],
                          got["sell_proceeds_usd"], got["threshold_ts"], got["threshold_price"], 1 if got["eligible"] else 0))
        con.executemany("insert into exposures values(?,?,?,?,?,?,?,?,?)", batch)
        if i % 40 == 0:
            con.commit()
            print(f"exposures {i}/{len(markets)}", flush=True)
    con.commit()
    print("eligible", con.execute("select count(*) from exposures where eligible=1").fetchone()[0], flush=True)


def old_eligible():
    out = {}
    with (DATA / "eligible_wallets.csv").open() as handle:
        for row in csv.DictReader(handle):
            out[(row["wallet"], row["condition_id"], row["outcome"])] = row
    return out


def old_edges(con: sqlite3.Connection):
    if con.execute("select count(*) from edges where source='parent'").fetchone()[0]:
        return
    with (DATA / "funding_edges.csv").open() as handle:
        for row in csv.DictReader(handle):
            con.execute("insert into edges values(?,?,?,?,?,?,?,?,?,?)",
                        (row["wallet"], int(row["hop"] or 1), row["sender"] or None, row["sender_class"],
                         float(row["amount_usd"] or 0), row["tx"], int(row["block"] or 0),
                         int(float(row["block_ts"] or 0)), "inflow", "parent"))
    with (DATA / "cashout_edges.csv").open() as handle:
        for row in csv.DictReader(handle):
            con.execute("insert into edges values(?,?,?,?,?,?,?,?,?,?)",
                        (row["wallet"], int(row["hop"] or 1), row["destination"] or None, row["destination_class"],
                         float(row["amount_usd"] or 0), row["tx"], int(row["block"] or 0),
                         int(float(row["block_ts"] or 0)), "cashout", "parent"))
    con.commit()


def needs_activity(con) -> list[str]:
    old = old_eligible()
    priority = {"TEST": 0, "VALIDATION": 1, "DISCOVERY": 2, "OPEN": 3}
    ranked = []
    for wallet, condition, outcome, threshold, committed in con.execute(
            """select e.wallet, e.condition_id, e.outcome, e.threshold_ts, e.committed
               from exposures e join fetches f on f.condition_id=e.condition_id and f.status='ok'
               where e.eligible=1"""):
        prev = old.get((wallet, condition, outcome))
        stratum = con.execute("select stratum from markets where condition_id=?", (condition,)).fetchone()
        rank = priority.get(stratum[0] if stratum else "", 9)
        if prev is None:
            ranked.append((rank, -committed, wallet))
        else:
            old_ts = int(float(prev["threshold_ts"] or 0))
            if threshold and old_ts - int(threshold) > 20000:
                ranked.append((rank, -committed, wallet))
    have = {r[0] for r in con.execute("select wallet from activity_status where status='ok'")}
    ordered, seen = [], set()
    for _rank, _c, wallet in sorted(ranked):
        if wallet not in seen and wallet not in have:
            ordered.append(wallet)
            seen.add(wallet)
    return ordered[:1500]


def fetch_activity(wallet: str):
    url = ("https://data-api.polymarket.com/v2/activity?user=" + wallet
           + "&start=1&sort_by=TIMESTAMP&sort_direction=ASC&exclude_deposits_withdrawals=false&limit=1000")
    payload = http_json(url)
    data, page = payload.get("data"), payload.get("pagination") or {}
    if not isinstance(data, list):
        raise RuntimeError("activity schema")
    rows, last = [], 0
    for raw in data:
        if str(raw.get("proxy_wallet", "")).lower() != wallet:
            raise RuntimeError("other wallet")
        ts = int(raw["timestamp"])
        if ts < last:
            raise RuntimeError("order")
        last = ts
        rows.append((wallet, ts, str(raw.get("type") or ""), str(raw.get("condition_id") or "").lower(),
                     str(raw.get("side") or ""), float(raw.get("usdc_size") or raw.get("size") or 0),
                     str(raw.get("transaction_hash") or "").lower()))
    return rows, 1 if page.get("has_more") else 0


def activity(con: sqlite3.Connection):
    queue = needs_activity(con)
    print("activity", len(queue), flush=True)

    def work(wallet):
        try:
            return wallet, fetch_activity(wallet), None
        except Exception as exc:  # noqa: BLE001
            return wallet, None, str(exc)[:180]

    done = 0
    with ThreadPoolExecutor(4) as pool:
        for fut in as_completed([pool.submit(work, w) for w in queue]):
            wallet, result, err = fut.result()
            with con:
                con.execute("delete from activity where wallet=?", (wallet,))
                if err:
                    con.execute("insert into activity_status values(?,?,?,?) on conflict(wallet) do update set status=excluded.status, note=excluded.note",
                                (wallet, "error", 0, err))
                else:
                    rows, more = result
                    con.executemany("insert into activity values(?,?,?,?,?,?,?)", rows)
                    con.execute("insert into activity_status values(?,?,?,?) on conflict(wallet) do update set status=excluded.status, has_more=excluded.has_more",
                                (wallet, "ok", more, None))
            done += 1
            if done % 100 == 0 or done == len(queue):
                print(f"activity {done}/{len(queue)}", flush=True)


def label_fresh(con: sqlite3.Connection):
    old = old_eligible()
    con.execute("delete from fresh")
    batch = []
    seen = set()
    for wallet, condition, threshold in con.execute(
            """select wallet, condition_id, min(threshold_ts) from exposures where eligible=1 group by 1,2"""):
        if (wallet, condition) in seen:
            continue
        seen.add((wallet, condition))
        prev = None
        for outcome in ("YES", "NO"):
            prev = old.get((wallet, condition, outcome)) or prev
        reuse = False
        if prev and prev.get("history") == "ok" and threshold:
            old_ts = int(float(prev["threshold_ts"] or 0))
            if old_ts - int(threshold) <= 20000:
                reuse = True
                batch.append((wallet, condition, prev.get("freshness") or "", int(prev.get("qualifying") or 0), "reused"))
        if reuse:
            continue
        status = con.execute("select status, has_more from activity_status where wallet=?", (wallet,)).fetchone()
        if not status or status[0] != "ok":
            batch.append((wallet, condition, "", 0, "unresolved"))
            continue
        rows = list(con.execute("select ts, typ, condition_id from activity where wallet=? order by ts", (wallet,)))
        trade_ts = [ts for ts, typ, cond in rows if typ == "TRADE" and cond == condition]
        first = min(trade_ts) if trade_ts else None
        if first is None:
            # the eligible buy is itself a trade; use the threshold as a lower bound only if no other trade exists
            fills_ts = [r[0] for r in con.execute(
                "select min(ts) from fills where wallet=? and condition_id=? and side='BUY'", (wallet, condition))]
            first = fills_ts[0]
        if first is None:
            batch.append((wallet, condition, "", 0, "unresolved"))
            continue
        gap = bool(status[1] and rows and not trade_ts and rows[-1][0] < first)
        got = freshness([(ts, typ, cond) for ts, typ, cond in rows], condition, int(first), int(threshold),
                        True, "unchecked", None, False, gap)
        batch.append((wallet, condition, ",".join(got["labels"]), 1 if got["qualifying"] else 0, got["history"]))
    con.executemany("insert into fresh values(?,?,?,?,?)", batch)
    con.commit()
    print("qualifying", con.execute("select count(*) from fresh where qualifying=1").fetchone()[0], flush=True)


def block_ts(con, n: int) -> int:
    row = con.execute("select ts from blocks where n=?", (n,)).fetchone()
    if row:
        return int(row[0])
    result = rpc("eth_getBlockByNumber", [hex(int(n)), False])
    ts = int(result["timestamp"], 16)
    con.execute("insert or replace into blocks values(?,?)", (int(n), ts))
    con.commit()
    return ts


def block_for_time(con, ts: int) -> int:
    head = con.execute("select v from meta where k='head'").fetchone()
    if not head:
        number = int(rpc("eth_blockNumber", []), 16)
        when = block_ts(con, number)
        con.execute("insert or replace into meta values('head',?)", (str(number),))
        con.execute("insert or replace into meta values('head_ts',?)", (str(when),))
        con.commit()
    head_n = int(con.execute("select v from meta where k='head'").fetchone()[0])
    head_t = int(con.execute("select v from meta where k='head_ts'").fetchone()[0])
    guess = max(1, min(head_n, head_n - int(max(0, head_t - ts) / 2)))
    lo, hi = max(1, guess - 20000), min(head_n, guess + 20000)
    for _ in range(6):
        if block_ts(con, lo) <= ts <= block_ts(con, hi):
            break
        span = max(1000, hi - lo)
        if block_ts(con, lo) > ts:
            lo = max(1, lo - span)
        if block_ts(con, hi) < ts:
            hi = min(head_n, hi + span)
    while lo < hi:
        mid = (lo + hi) // 2
        if block_ts(con, mid) < ts:
            lo = mid + 1
        else:
            hi = mid
    return lo


def address_state(con, address: str, block: int):
    row = con.execute("select code, nonce from addr_state where address=? and block=?", (address, block)).fetchone()
    if row:
        return bool(row[0]), row[1]
    code = rpc("eth_getCode", [address, hex(block)])
    nonce = int(rpc("eth_getTransactionCount", [address, hex(block)]) or "0x0", 16)
    present = 1 if code and code != "0x" else 0
    con.execute("insert or replace into addr_state values(?,?,?,?)", (address, block, present, nonce))
    con.commit()
    return bool(present), nonce


def logs_between(address: str, start: int, end: int, incoming: bool):
    pad = "0x" + "0" * 24 + address[2:]
    topic = [TRANSFER, None, pad] if incoming else [TRANSFER, pad, None]
    found = []
    cursor = start
    while cursor <= end:
        stop = min(end, cursor + 9999)
        for token in TOKENS:
            result = rpc("eth_getLogs", [{"fromBlock": hex(cursor), "toBlock": hex(stop), "address": token,
                                          "topics": topic}], log_range=True) or []
            found.extend(result)
        cursor = stop + 1
    return found


def trace_wallet(con, wallet: str, threshold_ts: int, lookback: int, kind: str):
    end = block_for_time(con, threshold_ts)
    start = max(1, end - lookback)
    best = {}

    def consider(sender, block, amount_raw, tx, hop):
        sender = sender.lower()
        if sender == wallet or hop > 3:
            return
        amount = amount_raw / 1_000_000
        if amount < 1 or amount > 5_000_000:
            return
        bts = block_ts(con, block)
        if bts > threshold_ts:
            return
        if best.get(sender, 0) >= amount:
            return
        first = sender not in best
        best[sender] = amount
        code, nonce = address_state(con, sender, block)
        klass = classify_address(code, nonce, sender in INFRA, None)
        con.execute("insert into edges values(?,?,?,?,?,?,?,?,?,?)",
                    (wallet, hop, sender, klass, amount, tx, block, bts, kind, "amendment"))
        if not first:
            return
        if klass == "passthrough_eoa" and hop < 3:
            for lg in logs_between(sender, max(1, block - 10000), block, True):
                consider("0x" + lg["topics"][1][-40:], int(lg["blockNumber"], 16), int(lg["data"], 16),
                         lg["transactionHash"].lower(), hop + 1)
        if klass == "contract" and hop < 3:
            receipt = rpc("eth_getTransactionReceipt", [tx])
            if receipt:
                walked = payer_of_deposit(receipt.get("logs") or [], wallet if hop == 1 else sender)
                if walked and walked.get("payer"):
                    consider(walked["payer"], int(receipt["blockNumber"], 16), walked["value"], tx, hop + 1)

    trade_txs = {r[0] for r in con.execute("select tx from fills where wallet=?", (wallet,))}
    for lg in logs_between(wallet, start, end, True):
        tx = lg["transactionHash"].lower()
        if tx in trade_txs:
            continue
        consider("0x" + lg["topics"][1][-40:], int(lg["blockNumber"], 16), int(lg["data"], 16), tx, 1)


def funding(con: sqlite3.Connection):
    old_edges(con)
    # wallets in a 7-day fresh group that lack a usable parent trace
    members = group_members(con, 7 * 86400)
    queue, seen = [], set()
    for wallet, condition, threshold in members:
        if wallet in seen:
            continue
        parent = con.execute(
            "select max(block_ts) from edges where wallet=? and source='parent' and kind='inflow'", (wallet,)).fetchone()[0]
        old_row = old_eligible().get((wallet, condition, "YES")) or old_eligible().get((wallet, condition, "NO"))
        stale = True
        if parent and old_row and threshold:
            old_ts = int(float(old_row["threshold_ts"] or 0))
            if old_ts - int(threshold) <= 20000:
                stale = False
        if stale:
            queue.append(wallet)
            seen.add(wallet)
    have = {r[0] for r in con.execute("select wallet from trace_status where status='ok'")}
    todo = [w for w in queue if w not in have][:400]
    print("new traces", len(todo), "of", len(queue), flush=True)
    for i, wallet in enumerate(todo, 1):
        threshold = con.execute("select min(threshold_ts) from exposures where wallet=? and eligible=1", (wallet,)).fetchone()[0]
        try:
            con.execute("delete from edges where wallet=? and source='amendment'", (wallet,))
            trace_wallet(con, wallet, int(threshold), 10000, "inflow")
            con.execute("insert into trace_status values(?,?,?) on conflict(wallet) do update set status='ok', note=null",
                        (wallet, "ok", None))
            con.commit()
        except Exception as exc:  # noqa: BLE001
            con.execute("insert into trace_status values(?,?,?) on conflict(wallet) do update set status='error', note=?",
                        (wallet, "error", str(exc)[:180]))
            con.commit()
        if i % 10 == 0 or i == len(todo):
            print(f"trace {i}/{len(todo)}", flush=True)


def group_members(con, window: int):
    rows = qualifying(con)
    grouped = defaultdict(list)
    for row in rows:
        grouped[(row["market"], row["outcome"])].append(row)
    out = []
    for members in grouped.values():
        ordered = sorted(members, key=lambda r: r["threshold_ts"])
        for i, start in enumerate(ordered):
            chunk = [start]
            for nxt in ordered[i + 1:]:
                if nxt["threshold_ts"] - start["threshold_ts"] <= window:
                    chunk.append(nxt)
                else:
                    break
            if len(chunk) >= 2 and len(chunk) == max(len(chunk), 2):
                # keep the largest chunk starting here only if it is a real group; caller dedupes wallets
                if len(chunk) >= 2:
                    for member in chunk:
                        out.append((member["wallet"], member["market"], member["threshold_ts"]))
    return out


def qualifying(con, stratum=None, family=None, denominator=False):
    sql = """select e.wallet, e.condition_id, e.outcome, e.threshold_ts, e.threshold_price, e.committed,
                    m.family, m.stratum, m.volume, m.in_denominator
             from exposures e
             join fresh f on f.wallet=e.wallet and f.condition_id=e.condition_id and f.qualifying=1
             join markets m on m.condition_id=e.condition_id
             join fetches t on t.condition_id=e.condition_id and t.status='ok'
             where e.eligible=1"""
    out = []
    for row in con.execute(sql):
        if stratum and row[7] != stratum:
            continue
        if family and row[6] != family:
            continue
        if denominator and not row[9]:
            continue
        out.append({"wallet": row[0], "market": row[1], "outcome": row[2], "threshold_ts": row[3],
                    "price": row[4], "committed": row[5], "family": row[6], "stratum": row[7], "volume": row[8]})
    return out


def fanout_relabel(con):
    counts = defaultdict(set)
    for wallet, sender, klass in con.execute(
            "select wallet, sender, prelim_class from edges where kind='inflow' and sender is not null"):
        if klass in ("plain_eoa", "passthrough_eoa"):
            counts[sender].add(wallet)
    return {sender: "high_fanout_service" for sender, wallets in counts.items() if len(wallets) > 10}


def primary(con, relabel, kind, floor, before_ts_by_wallet):
    best = {}
    for wallet, sender, klass, amount, bts in con.execute(
            "select wallet, sender, prelim_class, amount_usd, block_ts from edges where kind=? and sender is not null", (kind,)):
        klass = relabel.get(sender, klass)
        if klass != "plain_eoa" or amount < floor:
            continue
        limit = before_ts_by_wallet.get(wallet)
        if limit is not None and bts and bts > limit:
            continue
        current = best.get(wallet)
        if current is None or amount > current[0]:
            best[wallet] = (amount, sender)
    return {wallet: sender for wallet, (_a, sender) in best.items()}


def run_h1(rows, labels):
    wallets = sorted({r["wallet"] for r in rows})
    assignments = []
    for wallet in wallets:
        ts = min(r["threshold_ts"] for r in rows if r["wallet"] == wallet)
        assignments.append({"id": wallet, "month": month_key(ts), "label": labels.get(wallet)})

    def stat(assigned):
        return h1_stat(rows, {a["id"]: a["label"] for a in assigned})

    return shuffle_labels(assignments, AMEND["sensitivity_tests"]["permutations"], AMEND["sensitivity_tests"]["seed"], stat)


def analyze(con: sqlite3.Connection):
    build_exposures(con)
    activity(con)
    label_fresh(con)
    old_edges(con)
    funding(con)
    relabel = fanout_relabel(con)
    thresholds = {r[0]: r[1] for r in con.execute("select wallet, min(threshold_ts) from exposures where eligible=1 group by 1")}
    funders = primary(con, relabel, "inflow", 100, thresholds)
    destinations = primary(con, relabel, "cashout", 100, thresholds)
    test_info = qualifying(con, "TEST", "INFO", True)
    test_ctrl = qualifying(con, "TEST", "PUBLIC_PROCESS", True)
    h1 = run_h1(test_info, funders) if test_info else {"observed": 0, "p": None, "null_mean": None}
    h1c = run_h1(test_ctrl, funders) if test_ctrl else {"observed": 0, "p": None, "null_mean": None}
    h3 = run_h1(test_info, destinations) if test_info else {"observed": 0, "p": None, "null_mean": None}
    val = qualifying(con, "VALIDATION", "INFO", True)
    h1v = run_h1(val, funders) if val else {"observed": 0, "p": None, "null_mean": None}
    h3v = run_h1(val, destinations) if val else {"observed": 0, "p": None, "null_mean": None}
    h2 = co_timing(con, test_info + test_ctrl)
    parent = json.loads((DATA / "stats.json").read_text())
    old = old_eligible()
    new_rows = con.execute("select count(*) from exposures where eligible=1").fetchone()[0]
    new_keys = {(w, c, o) for w, c, o in con.execute("select wallet, condition_id, outcome from exposures where eligible=1")}
    added = len(new_keys - set(old))
    lost = len(set(old) - new_keys)
    fetches = dict(con.execute("select status, count(*) from fetches group by 1"))
    under = con.execute("select coalesce(sum(under100),0) from fetches where status='ok'").fetchone()[0]
    fp = fingerprints(con, funders, destinations, relabel)
    deep = deeper(con, fp)
    reentry = reenter(con, deep["keys"])
    stats = {
        "amendment": "002",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "parent_eligible_rows": parent["eligible"],
        "new_eligible_rows": new_rows,
        "eligible_added": added,
        "eligible_lost": lost,
        "under_100_fills": under,
        "fetches": fetches,
        "parent_H1": parent["H1"],
        "H1": h1, "H1_control": h1c, "H3": h3, "H2": h2,
        "validation_H1": h1v, "validation_H3": h3v,
        "parent_verdict": parent["h1_verdict"],
        "fingerprints": fp["summary"],
        "deeper": deep["summary"],
        "reentry_rows": len(reentry),
    }
    write_outputs(con, stats, fp, deep, reentry)
    print(json.dumps({k: stats[k] for k in ("new_eligible_rows", "eligible_added", "H1", "H2", "H3")}, default=str), flush=True)


def co_timing(con, rows):
    import math
    by = defaultdict(list)
    for row in rows:
        by[(row["market"], row["outcome"])].append(row["threshold_ts"])
    markets = list(con.execute(
        """select m.condition_id, m.family, m.volume from markets m
           join fetches f on f.condition_id=m.condition_id and f.status='ok'
           where m.in_denominator=1 and m.stratum='TEST' and m.family in ('INFO','PUBLIC_PROCESS')"""))
    identities = []
    for condition, fam, volume in markets:
        hit = int(any(has_tight_group(by.get((condition, outcome), []), 86400) for outcome in ("YES", "NO")))
        identities.append((fam, volume or 0, hit))
    logs = [math.log10(v) if v > 0 else 0 for _f, v, _h in identities]
    qs = quintiles(logs)
    packed = [{"family": fam, "quintile": q, "hit": hit} for (fam, _v, hit), q in zip(identities, qs)]
    return family_permutation(packed, 2000, 20261125) if packed else {"observed": None, "p": None, "null_mean": None}


def fingerprints(con, funders, destinations, relabel):
    """Frequency of the four frozen shapes. Nobel is reported apart and left out of the rates."""
    rows = [r for r in qualifying(con) if r["market"] != PC and r["stratum"] in ("TEST", "VALIDATION")]
    summary = []
    hits = []
    # FP1
    fp1 = 0
    grouped = defaultdict(list)
    for row in rows:
        if row["family"] == "INFO" and row["stratum"] == "TEST":
            grouped[(row["market"], row["outcome"])].append(row)
    for key, members in grouped.items():
        ordered = sorted(members, key=lambda r: r["threshold_ts"])
        found = False
        for i, start in enumerate(ordered):
            counts = defaultdict(list)
            for nxt in ordered[i:]:
                if nxt["threshold_ts"] - start["threshold_ts"] > 86400:
                    break
                funder = funders.get(nxt["wallet"])
                amount = largest_in_window(con, nxt["wallet"], funder, nxt["threshold_ts"])
                if funder and amount >= 1000:
                    counts[funder].append(nxt["wallet"])
            if any(len(v) >= 2 for v in counts.values()):
                found = True
                hits.append(("FP1_COFUNDED_FRESH", key[0], key[1], "VERIFIED FINANCIAL LINK"))
                break
        fp1 += int(found)
    ctrl_rows = [r for r in qualifying(con) if r["market"] != PC and r["stratum"] == "TEST" and r["family"] == "PUBLIC_PROCESS"]
    summary.append({"fingerprint": "FP1_COFUNDED_FRESH", "test_info": fp1, "note": "24h and a plain funder of at least 1000 USD"})
    # FP3
    markets = list(con.execute(
        """select condition_id, family, volume from markets where in_denominator=1 and stratum='TEST'
           and family in ('INFO','PUBLIC_PROCESS')"""))
    eligible = defaultdict(list)
    for wallet, condition, outcome, committed, ts, price in con.execute(
            """select e.wallet, e.condition_id, e.outcome, e.committed, e.threshold_ts, e.threshold_price
               from exposures e join fresh f on f.wallet=e.wallet and f.condition_id=e.condition_id
               where e.eligible=1 and f.labels like '%F1%'"""):
        eligible[(condition, outcome)].append((wallet, committed, ts, price))
    identities = []
    for condition, fam, volume in markets:
        hit = 0
        for outcome in ("YES", "NO"):
            people = eligible.get((condition, outcome), [])
            for wallet, committed, ts, price in people:
                if committed < 1000 or price is None or price > 0.20:
                    continue
                peers = [c for _w, c, t, _p in people if t is not None and 0 <= t - ts <= 900]
                if peers and committed >= 0.5 * sum(peers):
                    hit = 1
        identities.append((fam, volume or 0, hit))
    import math
    qs = quintiles([math.log10(v) if v > 0 else 0 for _f, v, _h in identities])
    packed = [{"family": f, "quintile": q, "hit": h} for (f, _v, h), q in zip(identities, qs)]
    fp3 = family_permutation(packed, 2000, 20261125)
    summary.append({"fingerprint": "FP3_THIN_LOW", "test": fp3})
    # FP4
    fp4 = 0
    for (market, outcome), members in grouped.items():
        ordered = sorted(members, key=lambda r: r["threshold_ts"])
        for i, start in enumerate(ordered):
            counts = defaultdict(int)
            for nxt in ordered[i:]:
                if nxt["threshold_ts"] - start["threshold_ts"] > 7 * 86400:
                    break
                dest = destinations.get(nxt["wallet"])
                if dest:
                    counts[dest] += 1
            if any(v >= 2 for v in counts.values()):
                fp4 += 1
                hits.append(("FP4_SHARED_PLAIN_CASHOUT", market, outcome, "VERIFIED FINANCIAL LINK"))
                break
    summary.append({"fingerprint": "FP4_SHARED_PLAIN_CASHOUT", "test_info": fp4})
    # FP2 handoff inside traced edges
    fp2 = handoffs(con, relabel)
    summary.append({"fingerprint": "FP2_HANDOFF", "pairs": len(fp2)})
    nobel = nobel_check(con, funders)
    return {"summary": summary, "hits": hits, "handoffs": fp2, "nobel": nobel, "fp3_identities": identities}


def largest_in_window(con, wallet, funder, threshold):
    if not funder or not threshold:
        return 0
    row = con.execute(
        """select max(amount_usd) from edges where wallet=? and sender=? and kind='inflow'
           and block_ts>0 and block_ts<=? and amount_usd>=1000""", (wallet, funder, threshold)).fetchone()
    # funding must also be within 24h. block time is checked against threshold; 24h is approximate via seconds
    row2 = con.execute(
        """select max(amount_usd) from edges where wallet=? and sender=? and kind='inflow'
           and block_ts>=? and block_ts<=?""",
        (wallet, funder, int(threshold) - 86400, int(threshold))).fetchone()
    return row2[0] or 0


def handoffs(con, relabel):
    """Same transaction, or 20 minutes and 5 percent, between two traced wallets. Services dropped."""
    outs = [(w, s, a, tx, bts) for w, s, a, tx, bts, k in con.execute(
        "select wallet, sender, amount_usd, tx, block_ts, prelim_class from edges where kind='cashout' and sender is not null and amount_usd>=100")]
    ins = [(w, s, a, tx, bts) for w, s, a, tx, bts in con.execute(
        "select wallet, sender, amount_usd, tx, block_ts from edges where kind='inflow' and sender is not null and amount_usd>=100")]
    # A handoff is an outflow whose destination is another traced wallet, or whose tx is that wallet's inflow.
    wallets = {w for w, *_ in ins} | {w for w, *_ in outs}
    found = []
    by_tx = defaultdict(list)
    for w, s, a, tx, bts in ins:
        by_tx[tx].append(("in", w, s, a, bts))
    for w, s, a, tx, bts in outs:
        klass = relabel.get(s, "plain_eoa")
        if klass != "plain_eoa":
            continue
        if s in wallets and s != w:
            found.append((w, s, a, tx, "destination_is_wallet"))
        for kind, other, _sender, amount, _bts in by_tx.get(tx, []):
            if other != w and abs(amount - a) / max(a, 1) <= 0.05:
                found.append((w, other, a, tx, "same_tx"))
    # dedupe
    return list({row[:4] for row in found})


def nobel_check(con, funders):
    yes = [w for w, in con.execute(
        "select wallet from exposures where condition_id=? and outcome='YES' and eligible=1", (PC,))]
    linked = [w for w in yes if w in NOBEL and funders.get(w) == "0xe206961002feebd9edb152eed9b630a351874043"]
    status = con.execute("select status from fetches where condition_id=?", (PC,)).fetchone()
    return {"tape": None if not status else status[0], "eligible_yes": len(yes),
            "known_eligible": len([w for w in yes if w in NOBEL]), "linked": len(linked)}


def deeper(con, fp):
    """Longer lookback for the Nobel wallets, fingerprint hits, and 20 service-only test wallets."""
    queue = list(NOBEL)
    for _name, market, _outcome, _klass in fp["hits"]:
        for (wallet,) in con.execute(
                "select wallet from exposures where condition_id=? and eligible=1", (market,)):
            queue.append(wallet)
    # service-only is not stored as a hit. Take traced test wallets whose only inflows are services, up to 20.
    serviceish = []
    for (wallet,) in con.execute(
            """select distinct e.wallet from exposures e
               join markets m on m.condition_id=e.condition_id and m.stratum='TEST' and m.family='INFO'
               where e.eligible=1"""):
        kinds = [r[0] for r in con.execute(
            "select prelim_class from edges where wallet=? and kind='inflow'", (wallet,))]
        if kinds and all(k in ("contract", "service_infra", "busy_eoa", "high_fanout_service") for k in kinds):
            serviceish.append(wallet)
    queue.extend(serviceish[:20])
    seen, done = set(), []
    for wallet in queue:
        if wallet in seen:
            continue
        seen.add(wallet)
        threshold = con.execute("select min(threshold_ts) from exposures where wallet=? and eligible=1", (wallet,)).fetchone()
        if not threshold or not threshold[0]:
            continue
        try:
            trace_wallet(con, wallet, int(threshold[0]), AMEND["deeper_flow"]["lookback_blocks"], "inflow_deep")
            con.commit()
            done.append(wallet)
        except Exception as exc:  # noqa: BLE001
            con.execute("insert into meta(k,v) values(?,?) on conflict(k) do update set v=excluded.v",
                        (f"deep_error_{wallet[:10]}", str(exc)[:140]))
            con.commit()
        if len(done) >= 40:
            break
        if len(done) % 5 == 0:
            print("deep", len(done), flush=True)
    plain = con.execute(
        """select sender, count(distinct wallet) from edges
           where kind='inflow_deep' and prelim_class='plain_eoa' and amount_usd>=100
           group by 1 having count(distinct wallet)>=2""").fetchall()
    return {"summary": {"wallets": len(done), "plain_keys_paying_two": [{"key": k, "wallets": n} for k, n in plain]},
            "keys": [k for k, _n in plain] + ["0xe206961002feebd9edb152eed9b630a351874043",
                                              "0x36626bd83accd8c1e0b9268a9db98a2233fc8c55"]}


def reenter(con, keys):
    rows = []
    for key in keys:
        if not key:
            continue
        try:
            head = int(con.execute("select v from meta where k='head'").fetchone()[0])
        except Exception:
            continue
        # one recent chunk and one older chunk, not a full 150k sweep of every key, recorded as a limit
        recipients = []
        # 150,000 blocks, in the 10,000-block slices the public endpoint accepts.
        start_floor = max(1, head - AMEND["deeper_flow"]["lookback_blocks"])
        cursor = start_floor
        while cursor <= head:
            stop = min(head, cursor + 9999)
            try:
                for lg in logs_between(key, cursor, stop, False):
                    dest = "0x" + lg["topics"][2][-40:]
                    amount = int(lg["data"], 16) / 1e6
                    if dest in INFRA or amount < 100:
                        continue
                    recipients.append((dest, amount, lg["transactionHash"].lower()))
            except Exception as exc:  # noqa: BLE001
                rows.append({"key": key, "recipient": "", "amount": 0, "markets": "", "note": f"log_error {exc}"[:160],
                             "evidence_class": "UNRESOLVED"})
            cursor = stop + 1
        seen = set()
        for dest, amount, tx in recipients:
            if dest in seen:
                continue
            seen.add(dest)
            if len(seen) > 15:
                break
            try:
                payload = http_json("https://data-api.polymarket.com/v2/activity?user=" + dest
                                    + "&limit=50&sort_by=TIMESTAMP&sort_direction=DESC")
                trades = [r for r in (payload.get("data") or []) if r.get("type") == "TRADE"]
            except Exception as exc:  # noqa: BLE001
                rows.append({"key": key, "recipient": dest, "amount": amount, "markets": "",
                             "note": str(exc)[:120], "evidence_class": "UNRESOLVED"})
                continue
            if not trades:
                rows.append({"key": key, "recipient": dest, "amount": round(amount, 2), "markets": "",
                             "note": "no polymarket trade in the newest 50 activity rows",
                             "evidence_class": "UNRESOLVED"})
                continue
            markets = sorted({str(r.get("title") or r.get("slug") or "")[:80] for r in trades})[:8]
            rows.append({"key": key, "recipient": dest, "amount": round(amount, 2),
                         "markets": " | ".join(markets), "note": f"{len(trades)} recent trades",
                         "evidence_class": "VERIFIED FINANCIAL LINK"})
    return rows


def write_outputs(con, stats, fp, deep, reentry):
    def dump(name, header, rows):
        with (DATA / name).open("w", newline="") as handle:
            writer = csv.writer(handle)
            writer.writerow(header)
            writer.writerows(rows)

    dump("amendment002_comparison.csv",
         ["metric", "parent_filter_100", "amendment_filter_1"],
         [["eligible_rows", stats["parent_eligible_rows"], stats["new_eligible_rows"]],
          ["eligible_added", "", stats["eligible_added"]],
          ["eligible_lost", "", stats["eligible_lost"]],
          ["under_100_fills_kept", "", stats["under_100_fills"]],
          ["H1_observed", stats["parent_H1"].get("observed"), stats["H1"].get("observed")],
          ["H1_p", stats["parent_H1"].get("p"), stats["H1"].get("p")],
          ["H1_validation_observed", 0, stats["validation_H1"].get("observed")],
          ["H3_observed", 0, stats["H3"].get("observed")],
          ["H2_difference", 0.1, stats["H2"].get("observed")],
          ["H2_p", 0.2518740629685157, stats["H2"].get("p")]])
    dump("fingerprints.csv", ["fingerprint", "detail"],
         [[row.get("fingerprint"), json.dumps({k: v for k, v in row.items() if k != "fingerprint"}, default=str)]
          for row in fp["summary"]] + [["nobel_check", json.dumps(fp["nobel"])]])
    dump("deep_flows.csv", ["key", "wallets"],
         [[item["key"], item["wallets"]] for item in deep["summary"].get("plain_keys_paying_two", [])])
    dump("reentry.csv", ["key", "recipient", "amount_usd", "markets", "note", "evidence_class"],
         [[r["key"], r["recipient"], r["amount"], r["markets"], r["note"], r["evidence_class"]] for r in reentry])
    (DATA / "amendment002_stats.json").write_text(json.dumps(stats, indent=2, default=str) + "\n")
    print("wrote amendment outputs", flush=True)


def main(argv):
    command = argv[1] if len(argv) > 1 else "all"
    con = connect()
    if command in ("fetch", "all"):
        fetch(con)
    if command in ("analyze", "all"):
        analyze(con)
    con.close()


if __name__ == "__main__":
    main(sys.argv)
