"""Part A of PLAN.md: the state of each payer at the block of each payment, read from archive JSON-RPC nodes.

    python3 -I pit_state.py STUDY_DIR WORK_DIR            # resumable; reads the frozen study read-only

STUDY_DIR is the frozen study of 14 November 2026 (`data/funding.sqlite`, `derived/funding_todo.jsonl`). WORK_DIR receives
`state.sqlite` (every answer, with its endpoint and time) and `need.json`. A failed read is stored as an error and asked
again on the next run; it is never turned into "no code" or "nonce 0".

Calls are saved only by properties that hold on the chain (PLAN.md, part A): a nonce never decreases, and the code of a
contract that is not an EIP-7702 delegation does not disappear (SELFDESTRUCT clears code only in its creation
transaction since EIP-6780, before the period studied)."""
import collections, json, os, sqlite3, sys, threading, time, urllib.error, urllib.request

WINDOW = 10000
BUSY = 1000
ARCHIVE = [("https://gateway.tenderly.co/public/polygon", 15, 1.0), ("https://polygon.drpc.org", 1, 0.25)]
LATEST = [("https://polygon-bor-rpc.publicnode.com", 25, 0.3), ("https://gateway.tenderly.co/public/polygon", 15, 1.0)]
UA = "Mozilla/5.0 (compatible; research-client/1.0)"


def is_7702(code):
    return isinstance(code, str) and len(code) == 2 + 46 and code.lower().startswith("0xef0100")


def post(url, body, timeout=40):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), headers={"Content-Type": "application/json", "User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def needed(study):
    """{address: sorted blocks}: every block at which build_links describes an address (payer, swapped-money sender, hop sender)."""
    ro = lambda p: sqlite3.connect(f"file:{study}/{p}?mode=ro&immutable=1", uri=True)
    fun = ro("data/funding.sqlite")
    todo = [json.loads(l) for l in open(os.path.join(study, "derived", "funding_todo.jsonl"))]
    current = {(e["wallet"], d[2]) for e in todo for d in e["deposits"]}
    dep = [r for r in fun.execute("select wallet, tx, payer, block from deposits where status='ok' and payer is not null") if (r[0], r[1]) in current]
    inflows = {(r[0], r[1]): json.loads(r[2]) for r in fun.execute("select wallet, tx, rows from inflows where status='ok'") if (r[0], r[1]) in current}
    hops = collections.defaultdict(list)
    for payer, block, rows in fun.execute("select payer, block, rows from hops where status='ok'"):
        for r in json.loads(rows):
            if r not in hops[payer]:
                hops[payer].append(r)
    need = collections.defaultdict(set)
    for w, tx, p, b in dep:
        need[p.lower()].add(b)
        for r in inflows.get((w, tx), []):
            if r["tx"] != tx and b - WINDOW <= r["block"] <= b:
                need[r["from"].lower()].add(r["block"])
    for a, bs in list(need.items()):
        for h in hops.get(a, []):
            s = h.get("from", "").lower()
            if s and any(bb - WINDOW <= h["block"] <= bb for bb in bs):
                need[s].add(h["block"])
    today = {r[0].lower(): r[1:] for r in fun.execute("select address, is_contract, nonce_today from payers")}
    return {a: sorted(bs) for a, bs in need.items()}, today


class Store:
    def __init__(self, path):
        self.con = sqlite3.connect(path, check_same_thread=False, timeout=60); self.lock = threading.Lock()
        self.con.execute("create table if not exists st(address text, block text, what text, value text, status text, source text, at real, "
                         "primary key(address, block, what))")

    def get(self, a, b, what):
        with self.lock:
            r = self.con.execute("select value, status from st where address=? and block=? and what=?", (a, str(b), what)).fetchone()
        return r

    def put(self, rows):
        with self.lock, self.con:
            self.con.executemany("insert or replace into st values(?,?,?,?,?,?,?)", rows)


def run_calls(store, calls, endpoints):
    """calls: [(address, block or 'latest', what)]; what is 'code' or 'nonce'. Answers stored as ok or error."""
    todo = [c for c in calls if (store.get(*c) or (None, None))[1] != "ok"]
    print(f"  {len(todo)} calls to make ({len(calls) - len(todo)} already stored)", flush=True)
    q = collections.deque(todo); lk = threading.Lock(); done = [0]

    def worker(url, size, gap):
        while True:
            with lk:
                chunk = [q.popleft() for _ in range(min(size, len(q)))]
            if not chunk:
                return
            body = [{"jsonrpc": "2.0", "id": i, "method": "eth_getTransactionCount" if w == "nonce" else "eth_getCode",
                     "params": [a, b if b == "latest" else hex(int(b) if w == "code_end" else int(b) - 1)]} for i, (a, b, w) in enumerate(chunk)]
            t0 = time.time(); rows = []
            try:
                j = post(url, body if size > 1 else body[0])
                j = j if isinstance(j, list) else [dict(j, id=0)]
                got = {x.get("id"): x for x in j if isinstance(x, dict)}
                for i, (a, b, w) in enumerate(chunk):
                    x = got.get(i)
                    if x is None or "error" in x or x.get("result") is None:
                        rows.append((a, str(b), w, json.dumps((x or {}).get("error"))[:300], "error", url, time.time()))
                    else:
                        rows.append((a, str(b), w, x["result"], "ok", url, time.time()))
            except (urllib.error.URLError, OSError, ValueError) as e:
                rows = [(a, str(b), w, repr(e)[:300], "error", url, time.time()) for a, b, w in chunk]
                time.sleep(3)
            store.put(rows)
            with lk:
                done[0] += len(chunk)
                if done[0] % 1500 < len(chunk):
                    print(f"    {done[0]}/{len(todo)} ({sum(r[4] == 'ok' for r in rows)}/{len(rows)} ok on {url.split('/')[2]})", flush=True)
            time.sleep(max(0.0, gap - (time.time() - t0)))
    ts = [threading.Thread(target=worker, args=e) for e in endpoints]
    for t in ts:
        t.start()
    for t in ts:
        t.join()


def main(study, work):
    os.makedirs(work, exist_ok=True)
    need, today = needed(study)
    json.dump(need, open(os.path.join(work, "need.json"), "w"))
    st = Store(os.path.join(work, "state.sqlite"))
    print(f"addresses {len(need)}, pairs {sum(map(len, need.values()))}", flush=True)
    for attempt in range(5):                                   # prerequisites first, then what they leave open; errors asked again
        print("1. code today", flush=True)
        run_calls(st, [(a, "latest", "code") for a in need], LATEST)
        calls = []
        for a, bs in need.items():
            c, s = st.get(a, "latest", "code") or (None, None)
            if s != "ok":
                continue
            n_today = (today.get(a) or (None, None))[1]
            if c not in ("0x", "0x0") and not is_7702(c):          # a contract today: is it one at the earliest block?
                cb, sb = st.get(a, bs[0], "code") or (None, None)
                if sb != "ok":
                    calls.append((a, bs[0], "code")); continue
                if cb in ("0x", "0x0"):                             # deployed later: every block is read
                    calls += [(a, b, "code") for b in bs] + [(a, b, "nonce") for b in bs]
                continue
            # no code today, or a delegation today: code and nonce at every block, except where the nonce settles it
            if n_today is not None and n_today >= BUSY:
                nb, sb = st.get(a, bs[0], "nonce") or (None, None)
                if sb != "ok":
                    calls.append((a, bs[0], "nonce")); continue
                if int(nb, 16) >= BUSY:
                    continue                                        # busy at the earliest block, hence at every later one
            calls += [(a, b, "code") for b in bs]
            if n_today is None or n_today > 5 or is_7702(c):        # under 1,000 is known; the pass-through bound is not
                calls += [(a, b, "nonce") for b in bs]
        calls = sorted({x for x in calls if (st.get(*x) or (None, None))[1] != "ok"})
        print(f"2. archive reads, pass {attempt + 1}: {len(calls)}", flush=True)
        if not calls:
            break
        run_calls(st, calls, ARCHIVE)
    # amendment 2: an address without code at b - 1 but with code today may have been deployed or delegated in block b
    for attempt in range(3):
        calls = []
        for a, bs in need.items():
            now_c, s = st.get(a, "latest", "code") or (None, None)
            if s != "ok" or now_c in ("0x", "0x0"):
                continue
            for b in bs:
                cb, sb = st.get(a, b, "code") or (None, None)
                if sb == "ok" and cb in ("0x", "0x0") and (st.get(a, b, "code_end") or (None, None))[1] != "ok":
                    calls.append((a, b, "code_end"))
        print(f"3. code at the end of the block, pass {attempt + 1}: {len(calls)}", flush=True)
        if not calls:
            break
        run_calls(st, calls, ARCHIVE)
    err = st.con.execute("select what, count(*) from st where status!='ok' group by what").fetchall()
    print("left as errors:", err, flush=True)


if __name__ == "__main__":
    main(*sys.argv[1:3])
