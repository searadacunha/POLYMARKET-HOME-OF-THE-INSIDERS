"""col_30: complete trade tape (maker and taker rows) around each stage-1 ignition, from data-api /v2/trades.
The stream is newest-first and ignores time filters, so pages are read from the latest trade down to the window.
A market needing more than MAX_PAGES pages is recorded as too_deep (excluded and counted, never treated as empty).
Profile text fields are never stored. Resumable."""
import collections, json, os, sqlite3, sys, time
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net
from tapefeat import PRE, W_LONELY

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(ETUDE, "data", "tapes.sqlite")
MAX_PAGES = 300
MARGIN = 60
WORKERS = 12


def windows():
    w = collections.defaultdict(list)
    for line in open(os.path.join(ETUDE, "derived", "ignitions_stage1.jsonl")):
        g = json.loads(line)
        w[g["condition_id"]].append((g["t0"] - PRE - MARGIN, g["t1"] + W_LONELY + MARGIN))
    return w


def one(item):
    cid, wins = item
    lo = min(a for a, _ in wins); rows = []; cursor = None; pages = 0; last = None
    while True:
        if pages >= MAX_PAGES:
            return cid, "too_deep", pages, last, []
        url = (f"https://data-api.polymarket.com/v2/trades?condition={cid}&limit=1000&taker_only=false"
               + (f"&cursor={cursor}" if cursor else ""))
        s, b, _ = net.fetch(url, tag="tape", archive=False, pause=0.1, timeout=60)
        if s != 200:
            return cid, f"http_{s}", pages, last, []
        j = json.loads(b); data = j.get("data")
        if not isinstance(data, list):
            raise RuntimeError(f"unexpected trades schema for {cid}")
        pages += 1
        for r in data:
            ts = int(r["timestamp"])
            if last is not None and ts > last:
                raise RuntimeError(f"tape not newest-first for {cid} at page {pages}")
            last = ts
            if any(a <= ts <= z for a, z in wins):
                rows.append((cid, ts, r["proxy_wallet"].lower(), r["side"], r.get("outcome"), float(r["size"]), float(r["price"]),
                             r["transaction_hash"]))
        pg = j.get("pagination") or {}
        cursor = pg.get("next_cursor")
        if (last is not None and last < lo) or not pg.get("has_more") or not cursor:
            return cid, "ok", pages, last, rows


def main():
    con = sqlite3.connect(DB)
    con.executescript("""create table if not exists rows(condition_id text, ts integer, wallet text, side text, outcome text,
        size real, price real, tx text);
      create index if not exists rows_c on rows(condition_id, ts);
      create table if not exists status(condition_id text primary key, status text, pages integer, oldest_ts integer, n_rows integer);""")
    done = {r[0] for r in con.execute("select condition_id from status")}
    todo = [(c, w) for c, w in windows().items() if c not in done]
    print("markets with an ignition:", len(done) + len(todo), "todo:", len(todo), flush=True)
    n = 0; t0 = time.time()
    with ThreadPoolExecutor(WORKERS) as ex:
        for cid, status, pages, oldest, rows in ex.map(one, todo):
            con.executemany("insert into rows values(?,?,?,?,?,?,?,?)", rows)
            con.execute("insert or replace into status values(?,?,?,?,?)", (cid, status, pages, oldest, len(rows)))
            con.commit(); n += 1
            if n % 50 == 0:
                print(time.strftime("%H:%M:%S"), n, "/", len(todo), f"{n / (time.time() - t0):.2f}/s", net.COUNTS, flush=True)
    c = dict(con.execute("select status, count(*) from status group by status").fetchall())
    print("DONE", c, net.COUNTS, flush=True)
    json.dump({"by_status": c, "http_this_run": net.COUNTS}, open(os.path.join(ETUDE, "data", "col_30_counts.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
