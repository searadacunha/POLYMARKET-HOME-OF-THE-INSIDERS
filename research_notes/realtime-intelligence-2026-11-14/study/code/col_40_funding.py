"""col_40: who paid the deposits listed in derived/funding_todo.jsonl (fresh deposits of thin or dormant wallets).

  A. receipt of each deposit transaction (Polygon JSON-RPC, batches) -> apparent payer inside that transaction
     (chainfund.py);
  B. every address met is described by behaviour: contract or key, number of transactions sent (read today), public
     name tags (Blockscout metadata). A tagged address, a contract or a busy key is a service used by many people;
  E. when the apparent payer is a contract (a pool, a settler, a ramp), the deposit is usually the wallet's OWN money
     being swapped into the collateral token: the money arrived just before, in another transaction. The transfers of
     collateral tokens received by the wallet in the WINDOW blocks before the deposit are then read from the logs.
     Found on the documented Nobel 2025 account: its deposit is paid by a Uniswap pool, and the key that funded it
     appears 39 blocks earlier;
  C. for a payer or sender that is a key with very few transactions (a pass-through), the transfers it received in the
     WINDOW blocks before, read the same way: money often reaches a new account through a key made for it;
  D. the senders found in C are described like any address.

A public node sometimes answers `null` for a receipt it does not hold: a null is retried on the other endpoints and is
stored as `no_receipt` only when every endpoint said null. Errors are stored as errors, never as "no payer". Resumable."""
import hashlib, json, os, queue, sqlite3, sys, threading, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chainfund, net

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BATCH_RPC = [("https://polygon-bor-rpc.publicnode.com", 25), ("https://gateway.tenderly.co/public/polygon", 15)]
SINGLE_RPC = ["https://polygon.drpc.org", "https://polygon-bor-rpc.publicnode.com", "https://gateway.tenderly.co/public/polygon"]
# Old log ranges, measured 2026-11-14: one public endpoint serves them (five requests a call, one call a second; ten
# requests a call are refused). drpc refuses every old range whatever its width, publicnode and 1rpc have no archive.
# Three calls may be in flight on it, with one shared pace of one call a second: at 14/11 16:20 UTC the endpoint answered a
# call in 6 to 11 s, and two simultaneous calls each in the time of one (latency, not a rate limit; no 429 seen).
LOG_RPC = [("https://gateway.tenderly.co/public/polygon", 5, 1.0)] * 3
LABELS = "https://metadata.services.blockscout.com/api/v1/metadata?chainId=137&addresses="
PASS_THROUGH_NONCE = 5          # a key that has sent at most this many transactions is read one hop further
WINDOW = 10000                  # blocks read before a deposit or a payment: about 4 hours at 1.5 s a block
pace = net.Pace(0.5)

SCHEMA = """
create table if not exists deposits(wallet text, tx text, ts integer, usdc real, status text, payer text, via text, token text, value integer,
  path text, block integer, sha256 text, note text, primary key(wallet, tx));
create table if not exists payers(address text primary key, is_contract integer, nonce_today integer, tags text, tags_status text, fetched real);
create table if not exists hops(payer text, block integer, status text, rows text, primary key(payer, block));
create table if not exists inflows(wallet text, tx text, block integer, status text, rows text, primary key(wallet, tx));
"""


def batch(method, params_list):
    """One answer per request, in order; None where every endpoint answered null. Raises when no endpoint answers at all."""
    out = [None] * len(params_list); left = list(range(len(params_list))); answered = False; last = None
    for url, size in BATCH_RPC:
        nxt = []
        for a in range(0, len(left), size):
            idx = left[a:a + size]
            try:
                j, _ = net.get(url, data=[{"jsonrpc": "2.0", "id": i, "method": method, "params": params_list[i]} for i in idx], pace=pace, tries=3)
            except net.SourceError as e:
                last = e; nxt += idx; continue
            if not isinstance(j, list):
                last = net.SourceError(f"{url}: batch not answered as a list"); nxt += idx; continue
            answered = True; got = {x.get("id"): x for x in j if isinstance(x, dict)}
            for i in idx:
                x = got.get(i)
                if x is None or "error" in x or x.get("result") is None:
                    nxt.append(i)
                else:
                    out[i] = x["result"]
        left = nxt
        if not left:
            return out
    for i in left:                                      # singles, on every endpoint, before a null is believed
        nulls = 0
        for url in SINGLE_RPC:
            try:
                j, _ = net.get(url, data={"jsonrpc": "2.0", "id": 1, "method": method, "params": params_list[i]}, pace=pace, tries=2)
            except net.SourceError as e:
                last = e; continue
            answered = True
            if "error" in j:
                last = net.SourceError(str(j["error"])[:200]); continue
            if j.get("result") is None:
                nulls += 1; continue
            out[i] = j["result"]; break
        else:
            if nulls < len(SINGLE_RPC):                 # a null is believed only when every endpoint said null
                raise net.SourceError(f"no endpoint answered {method} {params_list[i]}: {last}")
    if not answered:
        raise net.SourceError(f"no endpoint answered {method}: {last}")
    return out


def transfers_in(items, on_done):
    """items: [(key, address, from_block, to_block)]. For each, the collateral transfers received by `address` in those
    blocks. An item that is refused is tried again; after 4 refusals it is an error.
    on_done(key, status, rows) is called from the calling thread."""
    todo, done = queue.Queue(), queue.Queue()
    for it in items:
        todo.put((it, 0))
    topic = lambda a: "0x" + "0" * 24 + a[2:]

    def req(i, address, from_block, to_block):
        return {"jsonrpc": "2.0", "id": i, "method": "eth_getLogs", "params": [{
            "fromBlock": hex(max(1, from_block)), "toBlock": hex(to_block), "address": sorted(chainfund.STABLES),
            "topics": [chainfund.TRANSFER, None, topic(address)]}]}

    def rows_of(result):
        return [{"from": "0x" + l["topics"][1][-40:].lower(), "token": l["address"].lower(), "value": int(l["data"], 16),
                 "block": int(l["blockNumber"], 16), "tx": l["transactionHash"],
                 "ts": int(l["blockTimestamp"], 16) if l.get("blockTimestamp") else None}
                for l in result if not l.get("removed") and int(l["data"], 16) > 0]

    paces, lock = {}, threading.Lock()
    for url, _, gap in LOG_RPC:
        paces.setdefault(url, net.Pace(gap))

    def worker(url, size, gap):
        def p():                                        # one pace per endpoint, shared by its workers
            with lock:
                paces[url]()
        while True:
            part = []
            try:
                part.append(todo.get(timeout=3))
                while len(part) < size:
                    part.append(todo.get_nowait())
            except queue.Empty:
                if not part:
                    return
            body = [req(i, it[1], it[2], it[3]) for i, (it, _) in enumerate(part)]
            answers, err = {}, None
            try:
                j, _ = net.get(url, data=body if size > 1 else body[0], pace=p, tries=2)
                answers = {x.get("id"): x for x in j if isinstance(x, dict)} if isinstance(j, list) else {0: j}
            except net.SourceError as e:
                err = str(e)[:160]
            for i, (it, tries) in enumerate(part):
                x = answers.get(i)
                if x is not None and isinstance(x.get("result"), list):
                    done.put((it[0], "ok", rows_of(x["result"])))
                elif tries >= 3:
                    done.put((it[0], "error", [{"error": str((x or {}).get("error") or err or "no result")[:160]}]))
                else:
                    todo.put((it, tries + 1)); time.sleep(0.2)
    threads = [threading.Thread(target=worker, args=cfg, daemon=True) for cfg in LOG_RPC]
    for t in threads:
        t.start()
    n = 0
    while n < len(items):
        try:
            key, status, rows = done.get(timeout=5)
        except queue.Empty:
            if not any(t.is_alive() for t in threads) and done.empty():
                raise net.SourceError("log readers stopped before every item was answered")
            continue
        on_done(key, status, rows); n += 1
    return n


def describe(con, addresses):
    """Code, transaction count and public tags of addresses not described yet."""
    new = sorted(set(addresses) - {r[0] for r in con.execute("select address from payers")})
    for a in range(0, len(new), 100):
        part = new[a:a + 100]
        codes = batch("eth_getCode", [[p, "latest"] for p in part]); nonces = batch("eth_getTransactionCount", [[p, "latest"] for p in part])
        try:
            j, _ = net.get(LABELS + ",".join(part), pace=pace, tries=3)
            tags = {k.lower(): [t.get("name") for t in (v.get("tags") or []) if t.get("name")] for k, v in (j.get("addresses") or {}).items()}
            tstat = "ok"
        except net.SourceError:                         # labels unavailable: recorded as unknown, and an unknown address is never a link
            tags, tstat = {}, "unavailable"
        with con:
            for p, code, nonce in zip(part, codes, nonces):
                if code is None or nonce is None:
                    raise net.SourceError(f"null code or nonce for {p}")
                con.execute("insert or replace into payers values(?,?,?,?,?,?)", (p, int(code not in ("0x", "0x0")), int(nonce, 16),
                                                                                  json.dumps(tags.get(p, [])) if tstat == "ok" else None, tstat, time.time()))
    return len(new)


def main():
    con = sqlite3.connect(os.path.join(ETUDE, "data", "funding.sqlite"), timeout=60)
    con.execute("pragma journal_mode=wal"); con.executescript(SCHEMA)
    want = {}
    for l in open(os.path.join(ETUDE, "derived", "funding_todo.jsonl")):
        e = json.loads(l)
        for ts, usdc, tx in e["deposits"]:
            want[(e["wallet"], tx)] = (ts, usdc)
    done = {(r[0], r[1]) for r in con.execute("select wallet, tx from deposits where status in ('ok','no_credit')")}   # no_receipt is read again
    todo = [k for k in want if k not in done]
    print(f"A. deposits listed {len(want)}, done {len(done & set(want))}, to read {len(todo)}", flush=True)
    for a in range(0, len(todo), 200):
        part = todo[a:a + 200]
        recs = batch("eth_getTransactionReceipt", [[tx] for _, tx in part])
        with con:
            for (wallet, tx), rec in zip(part, recs):
                ts, usdc = want[(wallet, tx)]
                if rec is None:
                    row = ("no_receipt", None, None, None, None, None, None, None, "every endpoint answered null")
                else:
                    f = chainfund.payer_of_deposit(rec.get("logs") or [], wallet)
                    sha = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest()
                    if f is None:
                        row = ("no_credit", None, None, None, None, None, int(rec["blockNumber"], 16), sha, "no collateral transfer to the wallet in this transaction")
                    else:
                        row = ("ok", f["payer"], f["via"], f["token"], f["value"], json.dumps(f["path"]), int(rec["blockNumber"], 16), sha, None)
                con.execute("insert or replace into deposits values(?,?,?,?,?,?,?,?,?,?,?,?,?)", (wallet, tx, ts, usdc) + row)
        if (a // 200) % 10 == 0:
            print(time.strftime("%H:%M:%S"), "A", a + len(part), "/", len(todo), dict(net.COUNTS), flush=True)
    print("A done:", dict(con.execute("select status, count(*) from deposits group by status")), dict(con.execute("select via, count(*) from deposits group by via")))

    n = describe(con, [r[0] for r in con.execute("select distinct payer from deposits where payer is not null")])
    print(f"B. payers described now {n}:", con.execute("select count(*), sum(is_contract), sum(tags_status!='ok') from payers").fetchone(), flush=True)

    # E. deposits paid by a contract: what the wallet received just before
    cand = con.execute("select d.wallet, d.tx, d.block from deposits d join payers p on p.address=d.payer where d.status='ok' and p.is_contract=1 "
                       "and not exists (select 1 from inflows i where i.wallet=d.wallet and i.tx=d.tx and i.status='ok')").fetchall()
    by_wallet = {}
    for w, tx, b in cand:
        by_wallet.setdefault(w, []).append((tx, b))
    print(f"E. deposits paid by a contract, inflows to read {len(cand)} for {len(by_wallet)} wallets (one request a wallet)", flush=True)
    state = {"n": 0, "t": time.time()}

    def store_inflow(wallet, status, rows):                    # one answer covers every deposit of the wallet: each keeps its own window
        with con:
            for tx, b in by_wallet[wallet]:
                mine = rows if status != "ok" else [r for r in rows if b - WINDOW < r["block"] <= b]
                con.execute("insert or replace into inflows values(?,?,?,?,?)", (wallet, tx, b, status, json.dumps(mine)))
        state["n"] += 1
        if state["n"] % 500 == 0:
            print(time.strftime("%H:%M:%S"), "E", state["n"], "/", len(by_wallet), "wallets, rate", round(state["n"] / (time.time() - state["t"]), 1), "/s", dict(net.COUNTS), flush=True)
    transfers_in([(w, w, min(b for _, b in ds) - WINDOW + 1, max(b for _, b in ds)) for w, ds in by_wallet.items()], store_inflow)
    print("E done:", dict(con.execute("select status, count(*) from inflows group by status")))
    senders = set()
    for wallet, rows in con.execute("select wallet, rows from inflows where status='ok'"):
        senders |= {r["from"] for r in json.loads(rows) if r["from"] != wallet}
    print("E senders described now:", describe(con, senders), flush=True)

    # C. pass-through keys among payers and senders: plain, untagged, almost no transaction of their own
    # every payment made by a pass-through key is read over its own window (a first version read the last one only)
    paid = set(con.execute("select payer, block from deposits where status='ok' and payer is not null"))
    for wallet, rows in con.execute("select wallet, rows from inflows where status='ok'"):
        paid |= {(r["from"], r["block"]) for r in json.loads(rows) if r["from"] != wallet}
    plain = {r[0] for r in con.execute("select address from payers where is_contract=0 and nonce_today<=? and tags='[]'", (PASS_THROUGH_NONCE,))}
    have = set(con.execute("select payer, block from hops where status='ok'"))
    cand = sorted(x for x in paid if x[0] in plain and x not in have)
    print(f"C. pass-through keys to read {len(cand)}", flush=True)

    def store_hop(key, status, rows):
        with con:
            con.execute("insert or replace into hops values(?,?,?,?)", (key[0], key[1], status, json.dumps(rows)))
    transfers_in([((a, b), a, b - WINDOW + 1, b) for a, b in cand], store_hop)
    print("C done:", dict(con.execute("select status, count(*) from hops group by status")))

    senders = set()
    for payer, rows in con.execute("select payer, rows from hops where status='ok'"):
        senders |= {r["from"].lower() for r in json.loads(rows) if "from" in r}
    print("D. hop senders described now:", describe(con, senders))
    print("final", dict(net.COUNTS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
