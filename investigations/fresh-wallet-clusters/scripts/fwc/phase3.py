#!/usr/bin/env python3
"""Amendment 003 coverage recovery. Cache stays in /tmp/fwc-phase3."""
from __future__ import annotations

import csv
import sqlite3
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from fwc.extend import fetch_one  # noqa: E402
from fwc.logic import commitment  # noqa: E402

CACHE = Path("/tmp/fwc-phase3/cache.sqlite")
CAP = 80
HEADLINE = [
    ("0x580adc1327de9bf7c179ef5aaffa3377bb5cb252b7d6390b027172d43fd6f993", "INFO", "Maduro out by January 31, 2026"),
    ("0xdc4b9ecbfac2c8e98fe18b35c4578a3c64e34ddfe16b1cf8a98ab3ad9d06c088", "INFO", "US or Israel strike Iran by February 28, 2026"),
    ("0x12dc2b61723b2a54fc1947a307389b5f32038e7a29a0e936ad1fe410b969d06a", "PUBLIC_PROCESS", "Harry Kane Ballon d'Or 2026"),
]
DEEP = [
    ("0x656039df275062de2a439710a4aa0671328511c447630d3f05e4f35d6f1cc049", "INFO"),
    ("0xb7faecd2db357e4634fe87ef9bb48b4e1305cd618276d730b73190662fe6bafd", "INFO"),
    ("0x7e84002d49c772d2083afaec7fbe129481f7ef8d269973dfa9b14c7fe9ee0b03", "PUBLIC_PROCESS"),
    ("0xbba16a21398862877d2ba91d7221be625b4514066580c91c6acbc32b03fe7997", "PUBLIC_PROCESS"),
    ("0x4ea6acab2dcda8bb2fdf50d332ea58c4178660dd77aeb3eda8746f475fbdece0", "PUBLIC_PROCESS"),
    ("0x4ec6fcb43fe1a32163c7da09d54a99ab9bf6abdc6fd49939d7ad67d696a3248b", "INFO"),
    ("0x80ebf0a88a44bf737d4047b3accd7108285c69b84257e5c684bdc4c715c81139", "INFO"),
    ("0xc32a544f65e3a8ffec6499e40290f10fa68a3f4a4819dfd366b6cb1fd7c4be1d", "INFO"),
    ("0x836b850fc838195374862551a36f1c8691d96ff01e58b0a071f0fc1a0e357fb1", "INFO"),
    ("0x34918035a590555ba1fb1d6a019d766ab6e557d63e7f3140b63b4550eee7f417", "INFO"),
    ("0x741bb46008b72234857c5118c8365ab3c2f69dbf28b30b59de04f173b8a778de", "INFO"),
    ("0xc8c5760c26490b0cd0bedcf1c61aa86c5e09c8b2886b84ff4ea2db81d5f29388", "INFO"),
    ("0xcceae66d81c60f90c9679ab531b865bd7e9f95cc54f7b0634a24095519b10d65", "INFO"),
    ("0x797d586ad45522306490b0cc9b2f21bdf957f3843476fae99f3bcc2cec83b74b", "INFO"),
    ("0x3a26ca6425e2d98f14935670bc22cdb0744defc6f6d83c65f8c413a921c5c70c", "PUBLIC_PROCESS"),
    ("0xb5c0abeecb5502e6e8d83155c27819174d8317af3c425c3afc5a8c45257a3793", "INFO"),
]


def connect():
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(CACHE, timeout=120)
    con.execute("pragma journal_mode=wal")
    con.executescript("""
    create table if not exists fetches(condition_id text primary key, family text, label text, status text, pages integer, n_rows integer, under100 integer);
    create table if not exists fills(condition_id text, ts integer, wallet text, outcome text, side text, price real, size real, tx text);
    create table if not exists eligible(condition_id text, wallet text, outcome text, committed real, threshold_ts integer, primary key(condition_id, wallet, outcome));
    """)
    return con


def load(con):
    rows = [(c, fam, "recovered_too_deep") for c, fam in DEEP] + [(c, fam, name) for c, fam, name in HEADLINE]
    for cond, fam, label in rows:
        con.execute("insert or ignore into fetches(condition_id, family, label, status, pages, n_rows, under100) values(?,?,?,'pending',0,0,0)",
                    (cond, fam, label))
    con.commit()


def fetch(con):
    todo = [(r[0],) for r in con.execute("select condition_id from fetches where status='pending' or status='error'")]
    print("to fetch", len(todo), flush=True)

    def work(cond):
        try:
            return cond, fetch_one(cond, CAP), None
        except Exception as exc:  # noqa: BLE001
            return cond, None, str(exc)[:180]

    done = 0
    with ThreadPoolExecutor(3) as pool:
        for fut in as_completed([pool.submit(work, c) for c, in todo]):
            cond, result, err = fut.result()
            with con:
                con.execute("delete from fills where condition_id=?", (cond,))
                if err:
                    con.execute("update fetches set status='error', pages=0, n_rows=0, under100=0 where condition_id=?", (cond,))
                    print("error", cond[:12], err, flush=True)
                else:
                    rows, pages, under, status = result
                    if status != "ok":
                        con.execute("update fetches set status='too_deep', pages=?, n_rows=0, under100=? where condition_id=?",
                                    (pages, under, cond))
                    else:
                        unique = list({row for row in rows})
                        con.executemany("insert into fills values(?,?,?,?,?,?,?,?)", unique)
                        con.execute("update fetches set status='ok', pages=?, n_rows=?, under100=? where condition_id=?",
                                    (pages, len(unique), under, cond))
            done += 1
            print(f"fetch {done}/{len(todo)}", cond[:12], flush=True)


def exposures(con):
    con.execute("delete from eligible")
    for (cond,) in con.execute("select condition_id from fetches where status='ok'"):
        grouped = defaultdict(list)
        for wallet, outcome, ts, side, price, size in con.execute(
                "select wallet, outcome, ts, side, price, size from fills where condition_id=?", (cond,)):
            grouped[(wallet, outcome)].append((ts, side, price, size))
        batch = []
        for (wallet, outcome), fills in grouped.items():
            got = commitment(fills, 1000)
            if got["eligible"]:
                batch.append((cond, wallet, outcome, got["capital_committed_usd"], got["threshold_ts"]))
        con.executemany("insert into eligible values(?,?,?,?,?)", batch)
        print(cond[:12], "eligible", len(batch), flush=True)
    con.commit()


def report(con):
    out = ROOT / "data" / "phase3_coverage.csv"
    with out.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["condition_id", "family", "label", "status", "pages", "n_rows", "under100", "n_eligible"])
        for row in con.execute("""select f.condition_id, f.family, f.label, f.status, f.pages, f.n_rows, f.under100,
               (select count(*) from eligible e where e.condition_id=f.condition_id) from fetches f"""):
            writer.writerow(row)
    groups = ROOT / "data" / "phase3_eligible.csv"
    with groups.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["condition_id", "wallet", "outcome", "committed_usd", "threshold_ts"])
        for row in con.execute("select condition_id, wallet, outcome, committed, threshold_ts from eligible order by condition_id, outcome, threshold_ts"):
            writer.writerow(row)
    print("wrote", out.name, groups.name, flush=True)


def main():
    con = connect()
    load(con)
    fetch(con)
    exposures(con)
    report(con)


if __name__ == "__main__":
    main()
