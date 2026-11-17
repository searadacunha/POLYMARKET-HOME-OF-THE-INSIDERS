"""col_20: YES-token price history (CLOB /prices-history, 10-minute points) for the last 14 days before each market closed.
One request per market. A non-200 answer is stored as an error row (never as an empty series). Resumable.
Series are stored packed in data/prices.sqlite; the body hash of every answer is in the request index."""
import json, os, sqlite3, struct, sys, threading, time, zlib
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARKETS = os.path.join(ETUDE, "derived", "universe_markets.jsonl")
DB = os.path.join(ETUDE, "data", "prices.sqlite")
WINDOW = 14 * 86400
FIDELITY = 10  # minutes, fixed by the plan
WORKERS = 6


def pack(history):
    return zlib.compress(b"".join(struct.pack("<If", int(h["t"]), float(h["p"])) for h in history), 6)


def unpack(blob):
    raw = zlib.decompress(blob)
    return [struct.unpack_from("<If", raw, i) for i in range(0, len(raw), 8)]


def one(m):
    end = int(m["closed_ts"]); start = end - WINDOW
    url = f"https://clob.polymarket.com/prices-history?market={m['yes_token']}&startTs={start}&endTs={end}&fidelity={FIDELITY}"
    s, b, meta = net.fetch(url, tag="prices", archive=False, pause=0.05, timeout=40)
    if s != 200:
        return (m["condition_id"], m["yes_token"], start, end, s, 0, meta["sha256"], None)
    h = json.loads(b).get("history")
    if not isinstance(h, list):
        raise RuntimeError(f"unexpected prices-history schema for {m['condition_id']}")
    return (m["condition_id"], m["yes_token"], start, end, 200, len(h), meta["sha256"], pack(h))


def main():
    con = sqlite3.connect(DB)
    con.execute("create table if not exists series(condition_id text primary key, token text, start_ts integer, end_ts integer, "
                "status integer, n integer, sha256 text, blob blob)")
    done = {r[0] for r in con.execute("select condition_id from series")}
    todo = [m for m in map(json.loads, open(MARKETS)) if m["condition_id"] not in done]
    print("markets:", len(done) + len(todo), "already done:", len(done), "todo:", len(todo), flush=True)
    t0 = time.time(); n = 0
    with ThreadPoolExecutor(WORKERS) as ex:
        for row in ex.map(one, todo):
            con.execute("insert or replace into series values(?,?,?,?,?,?,?,?)", row)
            n += 1
            if n % 500 == 0:
                con.commit()
                print(time.strftime("%H:%M:%S"), n, "/", len(todo), f"{n / (time.time() - t0):.1f}/s", net.COUNTS, flush=True)
    con.commit()
    c = dict(con.execute("select case when status=200 and n>0 then 'ok' when status=200 then 'empty' else 'error' end k, count(*) "
                         "from series group by k").fetchall())
    print("DONE requested", len(done) + len(todo), "| stored:", c, "| http:", net.COUNTS, flush=True)
    json.dump({"requested": len(done) + len(todo), "by_state": c, "http_this_run": net.COUNTS},
              open(os.path.join(ETUDE, "data", "col_20_counts.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
