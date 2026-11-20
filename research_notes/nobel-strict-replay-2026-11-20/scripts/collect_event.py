"""Part C of PLAN.md: public data of the Nobel Peace Prize 2025 event for the night of 9-10 October 2025.

    python3 -I collect_event.py RAW_DIR            # resumable: a response already saved is not asked again

Writes, under RAW_DIR: every HTTP or JSON-RPC response exactly as received (gzip), and `index.jsonl` with its URL or
request, SHA-256 of the body, size and fetch time. Nothing is parsed into conclusions here (see analyse.py).
Sources: Gamma `events/slug`, data API `v2/activity` (bounded by `end`) and `v2/trades` (whole tape of a market, newest
first, cursor pages), CLOB `prices-history`, Polygon `eth_getLogs` (collateral received by the eight accounts)."""
import gzip, hashlib, json, os, sys, time, urllib.error, urllib.request

GAMMA, DATA, CLOB = "https://gamma-api.polymarket.com", "https://data-api.polymarket.com", "https://clob.polymarket.com"
LOG_RPC = ["https://gateway.tenderly.co/public/polygon", "https://polygon.drpc.org"]
UA = {"User-Agent": "Mozilla/5.0 (compatible; research-client/1.0)", "Accept": "application/json"}
SLUG = "nobel-peace-prize-winner-2025"
T_DOWN = 1759957200            # 2025-10-08 21:00:00 UTC: 24 hours before the night window opens
T_ANN = 1760086800             # 2025-10-10 09:00:00 UTC: announcement (11:00 in Oslo)
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOKENS = {"USDC": "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359", "USDC.e": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"}
BLOCKS = (77440000, 77495000)  # about 2025-10-09 04:34 to 2025-10-10 11:10 UTC (block headers read below, used by analyse_timeline.py)


class Raw:
    def __init__(self, d):
        self.d = d; os.makedirs(d, exist_ok=True); self.idx = os.path.join(d, "index.jsonl")
        self.seen = {}
        if os.path.exists(self.idx):
            for l in open(self.idx):
                r = json.loads(l); self.seen[r["key"]] = r

    def get(self, key, fetch):
        if key in self.seen:
            with gzip.open(os.path.join(self.d, self.seen[key]["file"])) as f:
                return json.loads(f.read())
        body = fetch()
        h = hashlib.sha256(body).hexdigest(); name = h[:20] + ".json.gz"
        with gzip.open(os.path.join(self.d, name), "wb") as f:
            f.write(body)
        r = {"key": key, "file": name, "sha256": h, "bytes": len(body), "fetched_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        with open(self.idx, "a") as f:
            f.write(json.dumps(r) + "\n")
        self.seen[key] = r
        return json.loads(body)


def http(url, data=None, tries=5):
    for a in range(tries):
        try:
            req = urllib.request.Request(url, data=None if data is None else json.dumps(data).encode(),
                                         headers=dict(UA, **({"Content-Type": "application/json"} if data else {})))
            with urllib.request.urlopen(req, timeout=45) as r:
                body = r.read()
            json.loads(body)                      # an HTML page or a truncated body is a failure, never data
            return body
        except (urllib.error.URLError, OSError, ValueError) as e:
            last = e; time.sleep(2 * (a + 1))
    raise RuntimeError(f"failed after {tries} tries: {url} :: {last!r}")


def rpc_logs(raw, address_topic, token, lo, hi):
    """Transfer logs of `token` to the padded address, in slices of 9,000 blocks; an error stops the run."""
    out = []
    for a in range(lo, hi + 1, 9000):
        b = min(hi, a + 8999)
        req = {"jsonrpc": "2.0", "id": 1, "method": "eth_getLogs",
               "params": [{"fromBlock": hex(a), "toBlock": hex(b), "address": token, "topics": [TRANSFER, None, address_topic]}]}
        def fetch():
            for url in LOG_RPC:
                body = http(url, req)
                j = json.loads(body)
                if "result" in j:
                    return body
            raise RuntimeError(f"no endpoint served logs {a}-{b}: {j.get('error')}")
        j = raw.get(f"logs:{token}:{address_topic}:{a}:{b}", fetch)
        out += j["result"]
    return out


def main(d):
    raw = Raw(d)
    ev = raw.get(f"gamma:{SLUG}", lambda: http(f"{GAMMA}/events/slug/{SLUG}"))
    markets = {m["conditionId"]: m for m in ev["markets"]}
    print(f"event {ev['id']}: {len(markets)} markets", flush=True)
    acc = [l.split(",") for l in open(os.path.join(os.path.dirname(__file__), "..", "..", "..", "investigations", "followup-20261113",
                                                   "sources", "data", "nobel_accounts.csv")).read().split("\n")[1:] if l]
    traded = set()
    for row in acc:
        proxy = row[1]
        rows, cursor_end = [], T_ANN
        u = f"{DATA}/v2/activity?user={proxy}&limit=500&sort_by=TIMESTAMP&sort_direction=DESC&exclude_deposits_withdrawals=false&end={cursor_end}"
        j = raw.get(f"activity:{proxy}:{cursor_end}", lambda u=u: http(u))
        rows = j.get("data") if isinstance(j, dict) else j
        if len(rows) >= 500:                       # paging by end= can skip rows of one second: refuse instead of guessing
            raise RuntimeError(f"{row[0]}: 500 activity rows or more before the announcement; paging not implemented")
        traded |= {r.get("condition_id") or r.get("conditionId") for r in rows if (r.get("type") or "").upper() == "TRADE"}
        print(f"  {row[0]}: {len(rows)} activity rows before the announcement", flush=True)
        for name, tok in TOKENS.items():
            logs = rpc_logs(raw, "0x" + proxy[2:].rjust(64, "0"), tok, *BLOCKS)
            print(f"    {name} received: {len(logs)} logs", flush=True)
            for n in sorted({int(l["blockNumber"], 16) for l in logs}):     # block times: logs of these nodes carry none
                req = {"jsonrpc": "2.0", "id": 1, "method": "eth_getBlockByNumber", "params": [hex(n), False]}
                raw.get(f"block:{n}", lambda req=req: next(b for b in (http(u, req) for u in LOG_RPC[::-1]) if json.loads(b).get("result")))
    traded.discard(None)
    top = sorted(markets, key=lambda c: -float(markets[c].get("volumeNum") or 0))[:5]
    for cid in sorted(traded | set(top)):
        cursor, pages, last = None, 0, None
        while True:
            u = f"{DATA}/v2/trades?condition={cid}&limit=1000&taker_only=false" + (f"&cursor={cursor}" if cursor else "")
            j = raw.get(f"trades:{cid}:{cursor or 'first'}", lambda u=u: http(u))
            data = j.get("data") or []; pages += 1
            if data:
                last = min(int(r["timestamp"]) for r in data)
            pg = j.get("pagination") or {}; cursor = pg.get("next_cursor")
            if last is not None and last < T_DOWN or not pg.get("has_more") or not cursor:
                break
            if pages >= 400:
                raise RuntimeError(f"tape of {cid} deeper than 400 pages: incomplete, stopped")
        title = (markets.get(cid) or {}).get("groupItemTitle") or cid
        complete = (last is not None and last < T_DOWN) or not pg.get("has_more")
        if not complete:
            raise RuntimeError(f"tape of {title} stopped before {T_DOWN} without the API saying it ended")
        print(f"  tape {title}: {pages} pages, oldest {last}, complete to T_DOWN", flush=True)
    for m in markets.values():
        if m["conditionId"] in traded | set(top):
            yes = json.loads(m["clobTokenIds"])[0]
            for fid in (1, 10):                    # 10 minutes is the grid of the phi_monitor confirmation rule
                raw.get(f"prices:{yes}:{fid}", lambda yes=yes, fid=fid: http(f"{CLOB}/prices-history?market={yes}&startTs={T_DOWN}&endTs={T_ANN + 3600}&fidelity={fid}"))
    print("done", flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
