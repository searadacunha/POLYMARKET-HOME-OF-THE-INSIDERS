"""col_41: collateral transfers received on the chain by the wallets listed in derived/inflow_todo.jsonl (feat_30).

The activity listing calls DEPOSIT only some of the ways money reaches a wallet; the share of first trades with no
deposit row before them grows from under 2 % in 2025 to 26 % in August 2026 (pre-freeze audit, 14 November 2026), and
on eight such wallets drawn at random every one had received collateral on the chain in the 24 hours before. FRESH and
the age of R1 are therefore read here, from the Transfer logs of USDC, USDC.e and pUSD to the wallet.

Each item asks for the window [from_ts, t) of one entry. The block range comes from an interpolation of block times,
widened by a margin, and its two ends are checked against the block headers before the logs are read; rows are then kept
by their own block timestamp, strictly before the entry. Output: data/inflows_chain.sqlite (table items). Resumable;
an error is stored as an error and read again on the next run, never as "nothing received"."""
import bisect, json, os, sqlite3, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chainfund, col_40_funding as cf, net
FRESH_S = 24 * 3600

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MARGIN = 3000                   # blocks; interpolation error measured on 2,000 held-out anchors: median 0.1, p99 34, max 453


def anchors():
    """(ts, block) pairs: the deposits already read, plus one header every million blocks."""
    fun = sqlite3.connect("file:" + os.path.join(ETUDE, "data", "funding.sqlite") + "?mode=ro", uri=True)
    a = set(fun.execute("select ts, block from deposits where status='ok' and block is not null"))
    heads = list(range(45_000_000, 98_000_001, 1_000_000))
    for b, h in zip(heads, cf.batch("eth_getBlockByNumber", [[hex(b), False] for b in heads])):
        if h is not None:
            a.add((int(h["timestamp"], 16), b))
    return sorted(a)


def block_at(an, ts):
    i = bisect.bisect_left(an, (ts, -1))
    (t0, b0), (t1, b1) = an[max(0, min(i - 1, len(an) - 2))], an[max(1, min(i, len(an) - 1))]
    return int(b0 + (b1 - b0) * (ts - t0) / (t1 - t0)) if t1 > t0 else b0


def ranges(an, items):
    """{id: (from_block, to_block)} whose header times enclose [from_ts, t]; widened until they do."""
    out, margin = {}, {i["id"]: MARGIN for i in items}
    left = list(items)
    tip = int(cf.batch("eth_blockNumber", [[]])[0], 16)          # never ask for a block past the head of the chain
    while left:
        cand = {i["id"]: (max(1, block_at(an, i["from_ts"]) - margin[i["id"]]), min(tip, block_at(an, i["t"]) + margin[i["id"]])) for i in left}
        ends = sorted({b for fb, tb in cand.values() for b in (fb, tb)})
        ts_of = {}
        for a in range(0, len(ends), 200):
            if a and a % 4000 == 0:
                print(time.strftime("%H:%M:%S"), "headers", a, "/", len(ends), dict(net.COUNTS), flush=True)
            part = ends[a:a + 200]
            for b, h in zip(part, cf.batch("eth_getBlockByNumber", [[hex(b), False] for b in part])):
                ts_of[b] = None if h is None else int(h["timestamp"], 16)     # a block past the tip has no header
        nxt = []
        for i in left:
            fb, tb = cand[i["id"]]
            if ts_of[tb] is None:                              # below the head every block has a header
                raise net.SourceError(f"no header for block {tb}")
            if ts_of[fb] is not None and ts_of[fb] <= i["from_ts"] and ts_of[tb] >= i["t"]:
                out[i["id"]] = (fb, tb)
            else:
                margin[i["id"]] *= 4; nxt.append(i)
        left = nxt
    return out


def main():
    con = sqlite3.connect(os.path.join(ETUDE, "data", "inflows_chain.sqlite"), timeout=60)
    con.execute("create table if not exists items(id integer primary key, wallet text, t integer, from_ts integer, from_block integer, "
                "to_block integer, status text, rows text)")
    items = [json.loads(l) for l in open(os.path.join(ETUDE, "derived", "inflow_todo.jsonl"))]
    con.execute("create table if not exists mints(tx text primary key, wallet text, status text, payer text, via text)")
    # an item is done only for the same wallet and time, with a window that covers the one asked for now
    done = {r[0]: r[1:] for r in con.execute("select id, wallet, t, from_ts from items where status='ok'")}
    todo = [i for i in items if i["id"] not in done or done[i["id"]] != (i["wallet"], i["t"], done[i["id"]][2]) or done[i["id"]][2] > i["from_ts"]]
    print(f"items listed {len(items)}, done {len(done)}, to read {len(todo)}", flush=True)
    an = anchors(); print("anchors", len(an), flush=True)
    rng = ranges(an, todo); print("ranges checked", len(rng), dict(net.COUNTS), flush=True)
    by_id = {i["id"]: i for i in todo}; st = {"n": 0, "t0": time.time(), "no_ts": 0}

    def store(key, status, rows):
        i = by_id[key]; fb, tb = rng[key]
        if status == "ok":
            if any(r["ts"] is None for r in rows):
                status, rows = "error", [{"error": "log without blockTimestamp"}]; st["no_ts"] += 1
            else:
                rows = [r for r in rows if i["from_ts"] <= r["ts"] < i["t"]]
        with con:
            con.execute("insert or replace into items values(?,?,?,?,?,?,?,?)", (key, i["wallet"], i["t"], i["from_ts"], fb, tb, status, json.dumps(rows)))
        st["n"] += 1
        if st["n"] % 500 == 0:
            print(time.strftime("%H:%M:%S"), st["n"], "/", len(todo), "rate", round(st["n"] / (time.time() - st["t0"]), 1), "/s", dict(net.COUNTS), flush=True)
    if todo:
        cf.transfers_in([(i["id"], i["wallet"], rng[i["id"]][0], rng[i["id"]][1]) for i in todo], store)
    print("logs done:", dict(con.execute("select status, count(*) from items group by status")), "no timestamp", st["no_ts"], dict(net.COUNTS), flush=True)
    mints_and_senders(con, {i["id"] for i in items})
    print("final", dict(net.COUNTS))
    return 0


def mints_and_senders(con, ids):
    """For the transfers of the 24 hours before each entry: (1) pUSD minted to the wallet (sender 0x0): the receipt says who
    paid the collateral that was wrapped (chainfund.payer_of_deposit); (2) every other sender is described like a payer
    (code, transactions sent, public name tags) in data/funding.sqlite, so that addresses tagged as Polymarket's own can be
    told apart from funding."""
    mints, senders = {}, set()
    for i, wallet, t, rows in con.execute("select id, wallet, t, rows from items where status='ok'"):
        if i not in ids:
            continue
        for r in json.loads(rows):
            if r["ts"] < t - FRESH_S:
                continue
            if r["from"] == chainfund.ZERO:
                mints[r["tx"]] = wallet
            elif r["from"] not in chainfund.INFRA and r["from"] != wallet:
                senders.add(r["from"])
    have = {r[0] for r in con.execute("select tx from mints where status='ok'")}
    todo = sorted(set(mints) - have)
    print(f"mints in the 24-hour windows {len(mints)}, receipts to read {len(todo)}", flush=True)
    for a in range(0, len(todo), 200):
        part = todo[a:a + 200]
        recs = cf.batch("eth_getTransactionReceipt", [[tx] for tx in part])
        with con:
            for tx, rec in zip(part, recs):
                if rec is None:
                    con.execute("insert or replace into mints values(?,?,?,?,?)", (tx, mints[tx], "no_receipt", None, None)); continue
                f = chainfund.payer_of_deposit(rec.get("logs") or [], mints[tx])
                con.execute("insert or replace into mints values(?,?,?,?,?)", (tx, mints[tx], "ok", f and f["payer"], f and f["via"]))
    print("mints:", dict(con.execute("select status || '|' || coalesce(via, '-'), count(*) from mints group by 1")), flush=True)
    fun = sqlite3.connect(os.path.join(ETUDE, "data", "funding.sqlite"), timeout=60)
    fun.execute("pragma journal_mode=wal"); fun.executescript(cf.SCHEMA)
    print(f"senders in the 24-hour windows {len(senders)}, described now:", cf.describe(fun, senders), flush=True)


def _selftest():
    an = [(1000, 100), (2000, 600), (3000, 1100)]
    assert block_at(an, 1500) == 350 and block_at(an, 2000) == 600 and block_at(an, 3500) == 1350 and block_at(an, 500) == -150
    print("col_41 selftest ok")


if __name__ == "__main__":
    sys.exit(_selftest() if sys.argv[1:] == ["selftest"] else main())
