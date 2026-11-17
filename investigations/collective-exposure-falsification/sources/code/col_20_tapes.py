#!/usr/bin/env python3
"""Fetch trade tapes with the frozen collector of the 16-Nov study (imported, unchanged).

Same endpoint, same page cap (300 x 1000), same stored fields, same schema as tapes*.sqlite. Never fetches labels.
Every market ends with one status row; errors are recorded as errors (never as an empty tape) and counted.
A tape that is not complete (status != ok) is not stored. Resumable: markets with a final status (ok, too_deep)
are skipped; any other status (error_*, http_*, bad_schema) is retried on the next pass.

usage: col_20_tapes.py MARKETS.jsonl OUT.sqlite [--workers 4]
"""
import json
import os
import sqlite3
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import requests

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.normpath(os.path.join(HERE, "..", "frozen_deps")))
import collect_tapes as C  # noqa: E402  byte copy of the frozen collector, sha256 ee7f6d75... (checked by run)

FROZEN_SHA = "ee7f6d75d4e5cede7b07091ab25dcd5981b8bc816d9f03e418c2c3956b8af1d1"


def main():
    import hashlib
    got = hashlib.sha256(open(C.__file__, "rb").read()).hexdigest()
    assert got == FROZEN_SHA, f"collector differs from the frozen one: {got}"
    mk_path, db = sys.argv[1], sys.argv[2]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 4
    cids = [json.loads(l)["condition_id"] for l in open(mk_path)]
    con = sqlite3.connect(db)
    con.executescript("""
      create table if not exists trades(condition_id text, ts integer, wallet text, side text,
        outcome text, outcome_index integer, size real, price real, tx text, token_id text);
      create index if not exists trades_c on trades(condition_id, ts);
      create table if not exists status(condition_id text primary key, status text, pages integer,
        oldest_ts integer, n_rows integer, fetched_at text);
    """)
    done = {r[0] for r in con.execute("select condition_id from status where status in ('ok', 'too_deep')")}
    todo = [c for c in cids if c not in done]
    print(json.dumps({"markets": len(cids), "already_final": len(done), "todo": len(todo)}), flush=True)

    def one(cid):
        with requests.Session() as s:
            try:
                return cid, C.fetch_trades(cid, session=s)
            except RuntimeError as e:  # non-monotone stream: recorded as an error, never stored as data
                return cid, (f"error_order:{str(e)[:80]}", 0, None, [])
            except Exception as e:  # e.g. HTTP 200 with a non-JSON body: recorded, retried next pass
                return cid, (f"error_{type(e).__name__}:{str(e)[:60]}", 0, None, [])

    n = 0
    with ThreadPoolExecutor(workers) as ex:
        for cid, (status, pages, oldest, rows) in ex.map(one, todo):
            keep = rows if status == "ok" else []
            con.execute("delete from trades where condition_id=?", (cid,))  # a retried market never doubles
            con.executemany(
                "insert into trades values(?,?,?,?,?,?,?,?,?,?)",
                [(cid, r["timestamp"], r["proxy_wallet"], r["side"], r["outcome"], r["outcome_index"],
                  r["size"], r["price"], r["transaction_hash"], r["token_id"]) for r in keep])
            con.execute("insert or replace into status values(?,?,?,?,?,?)",
                        (cid, status, pages, oldest, len(rows), time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())))
            con.commit()
            n += 1
            print(n, cid[:12], status, pages, len(rows), flush=True)
    summ = dict(con.execute("select status, count(*) from status group by status").fetchall())
    print(json.dumps({"final_status_counts": summ}), flush=True)


if __name__ == "__main__":
    main()
