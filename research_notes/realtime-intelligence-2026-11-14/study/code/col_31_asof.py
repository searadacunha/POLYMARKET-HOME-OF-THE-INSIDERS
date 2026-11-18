"""col_31: for the tier-1 entries that lie beyond the first 1,000 rows of their wallet (col_30), the wallet's 500 rows
before the entry (data API `v2/activity`, `end` = entry time - 1, newest first), and, when the entry must be watched
(dormant or thin, and fresh), its rows of the 24 hours from the entry. `end` is asserted on every answer.
Resumable; a failed read is stored as an error row and retried, never as an empty history."""
import json, os, sqlite3, sys, threading, time, zlib
from concurrent.futures import ThreadPoolExecutor, as_completed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import asof, net
from col_30_activity import slim, pace

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://data-api.polymarket.com/v2/activity?user=%s&sort_by=TIMESTAMP&exclude_deposits_withdrawals=false&limit=500"
WORKERS = 8


def entry_key(wallet, t, cond, oi):
    return f"{wallet}|{t}|{cond}|{oi}"


def fetch(wallet, t, cond, oi, cash):
    j, _ = net.get(URL % wallet + f"&sort_direction=DESC&end={t - 1}", pace=pace)
    data = j.get("data")
    if not isinstance(data, list):
        raise net.SourceError(f"unexpected activity schema for {wallet}")
    if any(int(r["timestamp"]) >= t for r in data):
        raise net.SourceError(f"`end` not honoured for {wallet} at {t}")
    before = slim(list(reversed(data)), wallet)
    capped = bool((j.get("pagination") or {}).get("has_more"))
    f = asof.flags_at_entry(dict(asof.view(before, t, cond), _t=t), cash)
    after = None
    if f["fresh"] and (f["dormant"] or f["thin"]):
        j2, _ = net.get(URL % wallet + f"&sort_direction=ASC&start={t}&end={t + asof.WATCH_S}", pace=pace)
        d2 = j2.get("data")
        if not isinstance(d2, list):
            raise net.SourceError(f"unexpected activity schema for {wallet}")
        if any(not (t <= int(r["timestamp"]) <= t + asof.WATCH_S) for r in d2):
            raise net.SourceError(f"`start` or `end` not honoured for {wallet} at {t}")
        after = [slim(d2, wallet), bool((j2.get("pagination") or {}).get("has_more"))]
    return before, capped, after


def main():
    ent = sqlite3.connect("file:" + os.path.join(ETUDE, "derived", "entries.sqlite") + "?mode=ro", uri=True)
    act = sqlite3.connect(os.path.join(ETUDE, "data", "activity.sqlite"), timeout=60)
    # keyed by the entry itself (wallet, time, market, side): entry numbers change whenever the entries are rebuilt
    act.execute("create table if not exists asof(key text primary key, status text, capped integer, body blob, after blob, after_more integer, note text, fetched real)")
    page = {r[0]: r[1] for r in act.execute("select wallet, last_ts from activity where status='ok' and has_more=1")}
    done = {r[0] for r in act.execute("select key from asof where status='ok'")}
    todo = [r for r in ent.execute("select id, address, t, condition_id, oi, cash from entries where tier1=1")
            if r[1] in page and r[2] > page[r[1]] and entry_key(r[1], r[2], r[3], r[4]) not in done]
    print(f"entries beyond the first page: to read {len(todo)}, already read {len(done)}", flush=True)
    n_ok = n_err = n_after = 0; t0 = time.time()

    def work(r):
        try:
            return r, fetch(r[1], r[2], r[3], r[4], r[5]), None
        except net.SourceError as e:
            return r, None, str(e)[:300]

    z = lambda rows: zlib.compress(json.dumps(rows, separators=(",", ":")).encode(), 6)
    with ThreadPoolExecutor(WORKERS) as ex:
        for i, fut in enumerate(as_completed([ex.submit(work, r) for r in todo]), 1):
            r, res, err = fut.result()
            with act:
                if err is not None:
                    n_err += 1; act.execute("insert or replace into asof values(?,?,?,?,?,?,?,?)", (entry_key(r[1], r[2], r[3], r[4]), "error", None, None, None, None, err, time.time()))
                else:
                    before, capped, after = res; n_ok += 1; n_after += after is not None
                    act.execute("insert or replace into asof values(?,?,?,?,?,?,?,?)",
                                (entry_key(r[1], r[2], r[3], r[4]), "ok", int(capped), z(before), z(after[0]) if after else None,
                                 int(after[1]) if after else None, None, time.time()))
            if i % 2000 == 0 or i == len(todo):
                print(time.strftime("%H:%M:%S"), f"{i}/{len(todo)} ok {n_ok} error {n_err} watched {n_after}", "rate", round(i / max(1, time.time() - t0), 1),
                      "entries/s", dict(net.COUNTS), flush=True)
    print("final", dict(act.execute("select status, count(*) from asof group by status")), dict(net.COUNTS))
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main())
