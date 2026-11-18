"""col_30: public activity history of the wallets listed in derived/tier1_wallets.txt (data API `v2/activity`, oldest first,
first 1,000 rows: trades, deposits, withdrawals, redemptions, conversions). For most wallets that is the whole history;
`has_more` says when it is not, and later entries of such a wallet are read as of their own time by col_31.

Slim rows only: time, type, market, side, cash, price, outcome index, and the transaction of deposits and withdrawals.
Profile text fields are never stored. Resumable; a failed wallet gets an `error` row (retried at the next launch),
never an empty history."""
import json, os, sqlite3, sys, threading, time, zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = ("https://data-api.polymarket.com/v2/activity?user=%s&start=1&sort_by=TIMESTAMP&sort_direction=ASC"
       "&exclude_deposits_withdrawals=false&limit=1000")
WORKERS, INTERVAL = 8, 0.10     # about 10 requests a second (documented ceiling of the route: 20 a second)
CODE = {"TRADE": "T", "DEPOSIT": "D", "WITHDRAWAL": "W", "REDEEM": "R", "CONVERSION": "C", "SPLIT": "S", "MERGE": "M"}
_lock, _next = threading.Lock(), [0.0]


def pace():
    with _lock:
        d = _next[0] - time.time()
        _next[0] = max(time.time(), _next[0]) + INTERVAL
    if d > 0:
        time.sleep(d)


def slim(rows, wallet):
    """[ts, type, condition_id, side, usdc, price, outcome_index, tx] per row; raises on a row of another wallet or unsorted rows."""
    out, last = [], 0
    for r in rows:
        ts = int(r["timestamp"])
        if ts < last:
            raise net.SourceError(f"activity not oldest-first for {wallet}")
        last = ts
        if str(r.get("proxy_wallet", "")).lower() != wallet:
            raise net.SourceError(f"row of another wallet in the activity of {wallet}")
        typ = CODE.get(r.get("type"), "X")
        out.append([ts, typ, r.get("condition_id") if typ == "T" else None, r.get("side") if typ == "T" else None,
                    float(r.get("usdc_size") or 0), float(r.get("price") or 0) if typ == "T" else None,
                    int(r["outcome_index"]) if typ == "T" and r.get("outcome_index") not in (None, "") else None,
                    r.get("transaction_hash") if typ in ("D", "W") else None])
    return out


def fetch(wallet):
    j, sha = net.get(URL % wallet, pace=pace)
    data, pg = j.get("data"), (j.get("pagination") or {})
    if not isinstance(data, list):
        raise net.SourceError(f"unexpected activity schema for {wallet}: {str(j)[:160]}")
    return slim(data, wallet), bool(pg.get("has_more")), sha


def main():
    con = sqlite3.connect(os.path.join(ETUDE, "data", "activity.sqlite"), timeout=60)
    con.execute("pragma journal_mode=wal"); con.execute("pragma synchronous=normal")
    con.execute("create table if not exists activity(wallet text primary key, status text, n_rows integer, has_more integer, first_ts integer, "
                "last_ts integer, body blob, sha256 text, note text, fetched real)")
    wanted = [l.strip() for l in open(os.path.join(ETUDE, "derived", "tier1_wallets.txt")) if l.strip()]
    done = {r[0] for r in con.execute("select wallet from activity where status='ok'")}
    todo = [w for w in wanted if w not in done]
    print(f"wallets listed {len(wanted)}, already read {len(done & set(wanted))}, to read {len(todo)}", flush=True)
    n_ok = n_err = n_more = n_empty = 0; t0 = time.time()

    def work(w):
        try:
            return w, fetch(w), None
        except net.SourceError as e:
            return w, None, str(e)[:300]

    with ThreadPoolExecutor(WORKERS) as ex:
        for i, fut in enumerate(as_completed([ex.submit(work, w) for w in todo]), 1):
            w, res, err = fut.result()
            with con:
                if err is not None:
                    n_err += 1
                    con.execute("insert or replace into activity values(?,?,?,?,?,?,?,?,?,?)", (w, "error", None, None, None, None, None, None, err, time.time()))
                else:
                    rows, more, sha = res; n_ok += 1; n_more += more; n_empty += not rows
                    con.execute("insert or replace into activity values(?,?,?,?,?,?,?,?,?,?)",
                                (w, "ok", len(rows), int(more), rows[0][0] if rows else None, rows[-1][0] if rows else None,
                                 zlib.compress(json.dumps(rows, separators=(",", ":")).encode(), 6), sha, None, time.time()))
            if i % 2000 == 0 or i == len(todo):
                print(time.strftime("%H:%M:%S"), f"{i}/{len(todo)} ok {n_ok} error {n_err} with more than 1000 rows {n_more} empty {n_empty}",
                      "rate", round(i / max(1, time.time() - t0), 1), "wallets/s", dict(net.COUNTS), flush=True)
    print("final", dict(con.execute("select status, count(*) from activity group by status")), dict(net.COUNTS))
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
