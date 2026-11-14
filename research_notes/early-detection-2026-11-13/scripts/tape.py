"""Fetch a market trade tape from data-api v2 (descending, cursor pagination) into work/tapes.sqlite.
Profile fields (name, pseudonym, bio, images) are dropped before storage. Raw pages stay in raw/ (never published).
Multiplicity is preserved: rows are stored in the order served, one line per served row (no dedup by content)."""
import json, sqlite3, sys, time
from net import fetch, ROOT

DB = ROOT / "work" / "tapes.sqlite"
DROP = ("name", "pseudonym", "bio", "profile_image", "profile_image_optimized", "icon")

def db():
    con = sqlite3.connect(DB)
    con.executescript("""
    create table if not exists trades(id integer primary key, run text, condition_id text, token_id text, wallet text, side text,
      size real, price real, ts integer, tx text, outcome text, outcome_index integer, rank integer);
    create index if not exists t_run on trades(run, ts);
    create table if not exists runs(run text primary key, condition_id text, taker_only integer, cutoff integer, started real,
      finished real, pages integer, rows integer, complete integer, last_ts integer, note text);
    """)
    return con

def fetch_tape(condition, cutoff=0, taker_only=False, limit=1000, max_pages=2000, pause=0.15):
    con = db()
    run = f"{condition}:{'T' if taker_only else 'A'}"
    if con.execute("select complete from runs where run=?", (run,)).fetchone() == (1,):
        return run
    con.execute("delete from trades where run=?", (run,)); con.execute("delete from runs where run=?", (run,))
    con.execute("insert into runs(run,condition_id,taker_only,cutoff,started,pages,rows,complete) values(?,?,?,?,?,0,0,0)",
                (run, condition, int(taker_only), cutoff, time.time()))
    cursor, rank, pages, last_ts, note = None, 0, 0, None, ""
    while pages < max_pages:
        url = (f"https://data-api.polymarket.com/v2/trades?condition={condition}&limit={limit}"
               f"&taker_only={'true' if taker_only else 'false'}" + (f"&cursor={cursor}" if cursor else ""))
        s, b, m = fetch(url, tag="tape", pause=pause)
        if s != 200:
            note = f"HTTP {s} at page {pages}: {b[:200]!r}"; break
        j = json.loads(b)
        rows = j.get("data") or []
        pages += 1
        stop = False
        batch = []
        for r in rows:
            ts = int(r["timestamp"])
            if last_ts is not None and ts > last_ts:
                note = f"order violation at page {pages}"  # recorded, not hidden
            last_ts = ts
            if ts < cutoff: stop = True; break
            rank += 1
            batch.append((run, r["condition_id"], str(r["token_id"]), r["proxy_wallet"].lower(), r["side"], float(r["size"]),
                          float(r["price"]), ts, r["transaction_hash"], r.get("outcome"), r.get("outcome_index"), rank))
        con.executemany("insert into trades(run,condition_id,token_id,wallet,side,size,price,ts,tx,outcome,outcome_index,rank) "
                        "values(?,?,?,?,?,?,?,?,?,?,?,?)", batch)
        con.execute("update runs set pages=?, rows=?, last_ts=? where run=?", (pages, rank, last_ts, run)); con.commit()
        pg = j.get("pagination") or {}
        cursor = pg.get("next_cursor")
        if stop or not pg.get("has_more") or not cursor:
            con.execute("update runs set complete=1, finished=?, note=? where run=?",
                        (time.time(), note or ("cutoff reached" if stop else "exhausted"), run)); con.commit()
            return run
    con.execute("update runs set finished=?, note=? where run=?", (time.time(), note or "max_pages reached (INCOMPLETE)", run)); con.commit()
    return run

if __name__ == "__main__":
    cond = sys.argv[1]; cutoff = int(sys.argv[2]) if len(sys.argv) > 2 else 0
    for to in (False, True):
        run = fetch_tape(cond, cutoff, to)
        print(db().execute("select run,pages,rows,complete,last_ts,note,round(finished-started,1) from runs where run=?", (run,)).fetchone())
