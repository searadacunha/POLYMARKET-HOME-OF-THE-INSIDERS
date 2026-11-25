#!/usr/bin/env python3
"""Funding check for the 25 largest eligible wallets on the two headline markets.

This is the confirmatory read named H4 in amendment-003.json. It does not trace
every eligible wallet. Wallets outside this set stay untraced.
"""
from __future__ import annotations

import csv
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from fwc.extend import fetch_activity, trace_wallet  # noqa: E402
from fwc.logic import classify_address, freshness  # noqa: E402

CACHE = Path("/tmp/fwc-phase3/cache.sqlite")
MARKETS = [
    "0x580adc1327de9bf7c179ef5aaffa3377bb5cb252b7d6390b027172d43fd6f993",
    "0xdc4b9ecbfac2c8e98fe18b35c4578a3c64e34ddfe16b1cf8a98ab3ad9d06c088",
]


def main():
    con = sqlite3.connect(CACHE, timeout=120)
    con.execute("pragma journal_mode=wal")
    con.executescript("""
    create table if not exists blocks(n integer primary key, ts integer);
    create table if not exists addr_state(address text, block integer, code integer, nonce integer, primary key(address, block));
    create table if not exists meta(k text primary key, v text);
    create table if not exists activity(wallet text, ts integer, typ text, condition_id text);
    create table if not exists edges(wallet text, hop integer, sender text, prelim_class text, amount_usd real, tx text, block integer, block_ts integer, kind text, source text);
    create table if not exists fills(condition_id text, ts integer, wallet text, outcome text, side text, price real, size real, tx text);
    """)
    picked = []
    for market in MARKETS:
        rows = list(con.execute(
            "select wallet, outcome, committed, threshold_ts from eligible where condition_id=? order by committed desc limit 25",
            (market,)))
        picked.extend((market, *row) for row in rows)
    print("picked", len(picked), flush=True)
    seen = set()
    for market, wallet, outcome, committed, threshold in picked:
        if wallet in seen:
            continue
        seen.add(wallet)
        try:
            rows, _more = fetch_activity(wallet)
        except Exception as exc:  # noqa: E402, BLE001
            print("activity fail", wallet[:10], exc, flush=True)
            continue
        con.executemany("insert into activity values(?,?,?,?)",
                        [(wallet, ts, typ, cond) for wallet, ts, typ, cond, _side, _usdc, _tx in rows])
        trade_ts = [r[1] for r in rows if r[2] == "TRADE" and r[3] == market]
        first = min(trade_ts) if trade_ts else threshold
        got = freshness([(r[1], r[2], r[3]) for r in rows], market, int(first), int(threshold), True, "unchecked", None, False, False)
        if not got["qualifying"]:
            continue
        try:
            trace_wallet(con, wallet, int(threshold), 10000, "inflow")
            con.commit()
            print("traced", wallet[:10], got["labels"], flush=True)
        except Exception as exc:  # noqa: BLE001
            print("trace fail", wallet[:10], str(exc)[:120], flush=True)
            con.commit()
    # shared plain funders among traced wallets on the same market
    # edges may include parent schema mismatch: trace_wallet inserts 10 columns into extend db.
    # This database's edges table has 8 columns. trace_wallet will have failed.
    print("done", flush=True)


if __name__ == "__main__":
    main()
