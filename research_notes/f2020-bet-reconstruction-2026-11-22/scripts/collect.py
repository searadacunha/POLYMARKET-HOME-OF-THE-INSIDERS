"""Network capture for the f2020 bet reconstruction. Writes gzip JSON under data/raw/. Nothing here interprets results.

usage: python3 -I scripts/collect.py <step> [--out data/raw]
steps, in order: activity gamma chain ledger bounds accounts payouts holdings external klines participants controls gamma_controls
Each step is idempotent per file: an existing file is kept, so a capture can resume. Delete a file to recapture it.
"""
import gzip
import hashlib
import json
import sys
import time
from pathlib import Path
from urllib.parse import urlencode

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
from net import SourceError, get_json, rpc, rpc_batch  # noqa: E402
from focus import CTF, FOCUS, PUSD, USDC, USDC_E, WALLETS  # noqa: E402
from fetch_activity import activity  # noqa: E402

NOTE = Path(__file__).resolve().parents[1]
GAMMA = "https://gamma-api.polymarket.com/markets?"
TOPIC_TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOPIC_RESOLUTION = "0xb44d84d3289691f71497564b85d4233648d9dbae8cbdbb4329f301c3a0185894"
SEL = {"payoutNumerators": "0x0504c814", "payoutDenominator": "0xdd34de67", "getCollectionId": "0x856296f7",
       "getPositionId": "0x39dd7530", "balanceOf1155": "0x00fdd58e", "balanceOf20": "0x70a08231"}
ARCHIVE = ["https://polygon.drpc.org", "https://gateway.tenderly.co/public/polygon"]


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def save(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".part")
    with gzip.GzipFile(tmp, "wb", mtime=0) as f:  # mtime=0: same bytes for the same content
        f.write(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode())
    tmp.replace(path)


def load(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def w32(x):
    return x[2:].lower().rjust(64, "0") if isinstance(x, str) else format(x, "064x")


def call(to, data, block, urls=None):
    return rpc("eth_call", [{"to": to, "data": data}, block if isinstance(block, str) else hex(block)], urls=urls)


# ---------------------------------------------------------------- activity
def step_activity(out):
    for w in WALLETS:
        p = out / "activity" / f"{w}.json.gz"
        if not p.exists():
            save(p, activity(w))
        print("activity", w, len(load(p)["rows"]))


# ---------------------------------------------------------------- gamma
def condition_ids():
    cids = set()
    for w in WALLETS:
        for r in load(NOTE / "data/raw/activity" / f"{w}.json.gz")["rows"]:
            if r.get("condition_id"):
                cids.add(r["condition_id"].lower())
    return sorted(cids)


def step_gamma(out):
    cids = condition_ids()
    chunk = 2000
    for part in range(0, len(cids), chunk):
        p = out / "gamma" / f"markets_{part // chunk:02d}.json.gz"
        if p.exists():
            continue
        ids, got, queries = cids[part:part + chunk], {}, []
        for i in range(0, len(ids), 100):
            batch = ids[i:i + 100]
            for closed in ("true", "false"):
                todo = [c for c in batch if c not in got]
                if not todo:
                    break
                url = GAMMA + f"closed={closed}&limit=500&" + "&".join("condition_ids=" + c for c in todo)
                rows = get_json(url)
                queries.append({"closed": closed, "requested": len(todo), "returned": len(rows)})
                for m in rows:
                    got[m["conditionId"].lower()] = m
            time.sleep(0.15)
        missing = [c for c in ids if c not in got]
        save(p, {"captured_utc": now(), "endpoint": GAMMA + "closed=<true|false>&limit=500&condition_ids=<up to 100>",
                 "requested": ids, "missing": missing, "queries": queries, "markets": [got[c] for c in ids if c in got]})
        print("gamma part", part // chunk, len(got), "markets,", len(missing), "missing")


# ---------------------------------------------------------------- chain: focus positions
def receipt(tx):
    rec, node = rpc("eth_getTransactionReceipt", [tx])
    txo, _ = rpc("eth_getTransactionByHash", [tx])
    blk, _ = rpc("eth_getBlockByNumber", [rec["blockNumber"], False])
    return {"receipt": rec, "transaction": txo, "block_timestamp": blk["timestamp"], "block_hash": blk["hash"], "node": node}


def logs(flt, urls=None, span=20000, min_span=500):
    """eth_getLogs over [fromBlock, toBlock] in spans; a refused span is halved, every block must be answered once."""
    out, a, b = [], int(flt["fromBlock"], 16), int(flt["toBlock"], 16)
    while a <= b:
        z = min(b, a + span - 1)
        try:
            res, node = rpc("eth_getLogs", [{**flt, "fromBlock": hex(a), "toBlock": hex(z)}], urls=urls or ARCHIVE, tries=1)
        except SourceError:
            if span <= min_span:
                raise
            span //= 2
            continue
        out.extend(res)
        a = z + 1
    return out


def focus_txs(f):
    rows = load(NOTE / "data/raw/activity" / f"{f['wallet']}.json.gz")["rows"]
    ops = [r for r in rows if (r.get("condition_id") or "").lower() == f["cid"]]
    return [f["funding_tx"]] + [r["transaction_hash"] for r in ops], ops


def step_chain(out):
    latest = int(rpc("eth_blockNumber", [])[0], 16) - 64  # a settled block, recorded with every state read
    for f in FOCUS:
        p = out / "chain" / f"focus_{f['id']}.json.gz"
        if p.exists():
            continue
        txs, ops = focus_txs(f)
        recs = {tx: receipt(tx) for tx in dict.fromkeys(txs)}
        fund_block = int(recs[f["funding_tx"]]["receipt"]["blockNumber"], 16)
        op_blocks = sorted(int(recs[r["transaction_hash"]]["receipt"]["blockNumber"], 16) for r in ops)
        # Collateral ledger of the wallet from 2 000 blocks (about an hour) before the funding to the first trade on the market.
        topic_w = "0x" + w32(f["wallet"])
        lo, hi = fund_block - 2000, op_blocks[0]
        coll = []
        for direction in ("out", "in"):
            topics = [TOPIC_TRANSFER, topic_w, None] if direction == "out" else [TOPIC_TRANSFER, None, topic_w]
            coll += logs({"fromBlock": hex(lo), "toBlock": hex(hi), "address": [USDC, USDC_E, PUSD], "topics": topics})
        for tx in sorted({l["transactionHash"] for l in coll} - set(recs)):
            recs[tx] = receipt(tx)
        # Balances of the three collateral tokens just before the funding and just before the first trade.
        bal = {}
        for label, blk in (("before_funding", fund_block - 1), ("before_first_trade", op_blocks[0] - 1)):
            bal[label] = {"block": blk, "values": {t: call(t, SEL["balanceOf20"] + w32(f["wallet"]), blk, ARCHIVE)[0]
                                                    for t in (USDC, USDC_E, PUSD)}}
        # Condition state, outcome slots and position ids at one settled block.
        cid = f["cid"]
        state = {"block": latest,
                 "payoutDenominator": call(CTF, SEL["payoutDenominator"] + w32(cid), latest)[0],
                 "payoutNumerators": [call(CTF, SEL["payoutNumerators"] + w32(cid) + w32(i), latest)[0] for i in (0, 1)],
                 "collections": {}, "positions": {}}
        collaterals = sorted({l["address"].lower() for r in recs.values() for l in r["receipt"]["logs"]} | {USDC_E, PUSD})
        for idx_set in (1, 2):
            coll_id = call(CTF, SEL["getCollectionId"] + w32(0) + w32(cid) + w32(idx_set), latest)[0]
            state["collections"][str(idx_set)] = coll_id
            for c in collaterals:
                pid = call(CTF, SEL["getPositionId"] + w32(c) + w32(coll_id), latest)[0]
                state["positions"][f"{idx_set}:{c}"] = pid
        # Token balance of the wallet before the first trade, after each operation block, and at the settled block.
        tokens = sorted({int(r["token_id"]) for r in ops})
        blocks = sorted({op_blocks[0] - 1, *op_blocks, latest})
        state["token_balances"] = {str(t): {str(b): call(CTF, SEL["balanceOf1155"] + w32(f["wallet"]) + w32(t), b, ARCHIVE)[0]
                                            for b in blocks} for t in tokens}
        # Resolution event: from the end of the market window, 30 000 blocks (about 17 hours).
        end_block = max(op_blocks[0], fund_block)
        state["resolution_logs"] = logs({"fromBlock": hex(end_block), "toBlock": hex(min(latest, end_block + 30000)),
                                         "address": CTF, "topics": [TOPIC_RESOLUTION, "0x" + w32(cid)]})
        save(p, {"captured_utc": now(), "focus": f, "receipts": recs, "collateral_logs": coll, "balances": bal, "state": state})
        print("chain focus", f["id"], len(recs), "receipts", len(coll), "collateral logs", len(state["resolution_logs"]), "resolution logs")


# ---------------------------------------------------------------- chain: payouts of every market traded after the funding
def step_payouts(out, batch=10):
    p = out / "chain" / "payouts.json.gz"
    if p.exists():
        return
    latest = int(rpc("eth_blockNumber", [])[0], 16) - 64
    cids = set()
    for f in FOCUS:
        for r in load(NOTE / "data/raw/activity" / f"{f['wallet']}.json.gz")["rows"]:
            if r.get("condition_id") and r["timestamp"] >= f["funding_ts"]:
                cids.add(r["condition_id"].lower())
    cids, res, nodes = sorted(cids), {}, set()
    for i in range(0, len(cids), batch):
        part = cids[i:i + batch]
        calls = []
        for cid in part:
            calls.append(("eth_call", [{"to": CTF, "data": SEL["payoutDenominator"] + w32(cid)}, hex(latest)]))
            calls += [("eth_call", [{"to": CTF, "data": SEL["payoutNumerators"] + w32(cid) + w32(k)}, hex(latest)]) for k in (0, 1)]
        try:  # publicnode answered 30-call batches on 2026-11-22; drpc and tenderly only up to 10
            vals, node = rpc_batch(calls, urls=["https://polygon-bor-rpc.publicnode.com"])
        except SourceError:
            vals, node = [], None
            for k in range(0, len(calls), 9):
                v, node = rpc_batch(calls[k:k + 9], urls=["https://polygon.drpc.org", "https://gateway.tenderly.co/public/polygon"])
                vals += v
        nodes.add(node)
        for j, cid in enumerate(part):
            den, n0, n1 = vals[3 * j: 3 * j + 3]
            res[cid] = {"denominator": den, "numerators": [n0, n1] if int(den, 16) else None}
        time.sleep(0.2)
    save(p, {"captured_utc": now(), "block": latest, "contract": CTF, "nodes": sorted(nodes), "conditions": res})
    print("payouts", len(res), "conditions,", sum(1 for v in res.values() if v["numerators"]), "resolved on chain")


# ---------------------------------------------------------------- external: BTC 1 s prices, Busan METAR
def step_external(out):
    for f in FOCUS:
        if f["kind"] != "btc5m":
            continue
        p = out / "external" / f"binance_btcusdt_1s_{f['window_start']}.json.gz"
        if p.exists():
            continue
        a, b = (f["window_start"] - 300) * 1000, (f["window_start"] + 600) * 1000 - 1
        rows, url0 = [], None
        while a <= b:
            url = "https://api.binance.com/api/v3/klines?" + urlencode(dict(symbol="BTCUSDT", interval="1s", startTime=a, endTime=b, limit=1000))
            url0 = url0 or url
            page = get_json(url)
            if not page:
                break
            rows.extend(page)
            a = page[-1][0] + 1000
        save(p, {"captured_utc": now(), "endpoint": url0, "rows": rows})
        print("binance", f["id"], len(rows))
    p = out / "external" / "iem_metar_rkpk_20260925_27.json.gz"
    if not p.exists():
        url = ("https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py?station=RKPK&data=tmpc&data=metar&year1=2026&month1=9&day1=25"
               "&hour1=0&year2=2026&month2=9&day2=27&hour2=23&tz=Etc/UTC&format=onlycomma&latlon=no&missing=M&trace=T&direct=no"
               "&report_type=3&report_type=4")
        import urllib.request
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "phi-research/1.0"}), timeout=60) as r:
            text = r.read().decode()
        save(p, {"captured_utc": now(), "endpoint": url, "csv": text})
        print("metar rows", text.count("\n") - 1)


# ---------------------------------------------------------------- ledger: every stablecoin transfer of each wallet after its funding
def step_ledger(out):
    latest = int(rpc("eth_blockNumber", [])[0], 16) - 64
    for f in FOCUS:
        p = out / "chain" / f"ledger_{f['id']}.json.gz"
        if p.exists():
            continue
        fund = load(out / "chain" / f"focus_{f['id']}.json.gz")["receipts"][f["funding_tx"]]
        start = int(fund["receipt"]["blockNumber"], 16) - 2000
        topic_w = "0x" + w32(f["wallet"])
        got = {}
        for direction, topics in (("out", [TOPIC_TRANSFER, topic_w, None]), ("in", [TOPIC_TRANSFER, None, topic_w])):
            got[direction] = logs({"fromBlock": hex(start), "toBlock": hex(latest), "address": [USDC, USDC_E, PUSD],
                                   "topics": topics}, span=250000)
        opening = {t: call(t, SEL["balanceOf20"] + w32(f["wallet"]), start - 1, ARCHIVE)[0] for t in (USDC, USDC_E, PUSD)}
        closing = {t: call(t, SEL["balanceOf20"] + w32(f["wallet"]), latest, ARCHIVE)[0] for t in (USDC, USDC_E, PUSD)}
        peers = sorted({"0x" + l["topics"][2][-40:] for l in got["out"]} | {"0x" + l["topics"][1][-40:] for l in got["in"]})
        code = {a: len(rpc("eth_getCode", [a, hex(latest)])[0]) > 2 for a in peers}
        save(p, {"captured_utc": now(), "wallet": f["wallet"], "from_block": start, "to_block": latest, "tokens": [USDC, USDC_E, PUSD],
                 "logs_out": got["out"], "logs_in": got["in"], "opening_balances": {"block": start - 1, "values": opening},
                 "closing_balances": {"block": latest, "values": closing}, "peer_has_code": code})
        print("ledger", f["id"], len(got["out"]), "out", len(got["in"]), "in", len(peers), "peers")


# ---------------------------------------------------------------- BTC minute prices over the later trading periods (directional context)
def step_klines(out):
    p = out / "external" / "binance_btcusdt_1m_20260917_20261121.json.gz"
    if p.exists():
        return
    a, b = 1789603200 * 1000, 1795305600 * 1000 - 1  # 2026-09-17 00:00 to 2026-11-22 00:00 UTC
    rows, url0 = [], None
    while a <= b:
        url = "https://api.binance.com/api/v3/klines?" + urlencode(dict(symbol="BTCUSDT", interval="1m", startTime=a, endTime=b, limit=1000))
        url0 = url0 or url
        page = get_json(url)
        if not page:
            break
        rows.extend([r[0] // 1000, r[1], r[4]] for r in page)  # open time (s), open, close
        a = page[-1][0] + 60000
        time.sleep(0.1)
    save(p, {"captured_utc": now(), "endpoint": url0, "fields": ["open_time_s", "open", "close"], "rows": rows})
    print("binance 1m", len(rows))


# ---------------------------------------------------------------- market participants of the four focus markets
def market_trades(cid):
    rows, cursor, pages = [], None, 0
    while True:
        q = dict(condition=cid, limit=1000, taker_only="false")
        if cursor:
            q["cursor"] = cursor
        v = get_json("https://data-api.polymarket.com/v2/trades?" + urlencode(q))
        data, pg = v["data"], v["pagination"]
        for r in data:
            if (r.get("condition_id") or "").lower() != cid:
                raise ValueError("trade row for another market")
        rows += [{k: x for k, x in r.items() if k not in ("name", "pseudonym", "bio", "profile_image", "profile_image_optimized")}
                 for r in data]
        pages += 1
        if pg.get("has_more") != bool(pg.get("next_cursor")):
            raise ValueError("ambiguous pagination")
        if not pg.get("has_more"):
            return rows, pages
        cursor = pg["next_cursor"]
        time.sleep(0.2)


def step_participants(out):
    for f in FOCUS:
        p = out / "controls" / f"market_trades_{f['id']}.json.gz"
        if p.exists():
            continue
        rows, pages = market_trades(f["cid"])
        save(p, {"captured_utc": now(), "condition_id": f["cid"], "pages": pages,
                 "endpoint": "https://data-api.polymarket.com/v2/trades?condition=<cid>&limit=1000&taker_only=false&cursor=...",
                 "rows": rows})
        print("participants", f["id"], len(rows), "fills", pages, "pages")


# ---------------------------------------------------------------- control traders: same focus market, similar size, same period
def bounded_activity(wallet, lo, hi, max_pages=20, limit=500):
    rows, cursor, pages = [], None, 0
    while True:
        q = dict(user=wallet, limit=limit, sort_by="TIMESTAMP", sort_direction="ASC", start=lo, end=hi)
        if cursor:
            q["cursor"] = cursor
        v = get_json("https://data-api.polymarket.com/v2/activity?" + urlencode(q))
        data, pg = v["data"], v["pagination"]
        for r in data:
            if r["proxy_wallet"].lower() != wallet or not lo <= r["timestamp"] <= hi:
                raise ValueError("activity endpoint did not honour the wallet/time filter")
        rows += [{k: x for k, x in r.items() if k not in ("name", "pseudonym", "bio", "profile_image", "profile_image_optimized")}
                 for r in data]
        pages += 1
        if pg.get("has_more") != bool(pg.get("next_cursor")):
            raise ValueError("ambiguous pagination")
        if not pg.get("has_more"):
            return rows, pages, True
        if pages >= max_pages:
            return rows, pages, False
        cursor = pg["next_cursor"]
        time.sleep(0.25)


def control_candidates(f, rows, n=15):
    """Small buyers of the same market, ranked by sha256(market + wallet): independent of outcome, pnl and later behaviour."""
    notional = {}
    for r in rows:
        if r["side"] == "BUY":
            w = r["proxy_wallet"].lower()
            notional[w] = notional.get(w, 0) + float(r["price"]) * float(r["size"])  # trade rows carry no usdc_size
    focus_wallets = set(WALLETS)
    pool = [w for w, x in notional.items() if 0.5 <= x <= 20 and w not in focus_wallets]
    return sorted(pool, key=lambda w: hashlib.sha256((f["cid"] + w).encode()).hexdigest())[:n], len(pool)


def step_controls(out):
    for f in FOCUS:
        p = out / "controls" / f"control_activity_{f['id']}.json.gz"
        if p.exists():
            continue
        rows = load(out / "controls" / f"market_trades_{f['id']}.json.gz")["rows"]
        picked, pool = control_candidates(f, rows)
        lo, hi = f["funding_ts"] - 7 * 86400, f["funding_ts"] + 30 * 86400
        res = {}
        for w in picked:
            a, pages, complete = bounded_activity(w, lo, hi)
            res[w] = {"rows": a, "pages": pages, "complete": complete}
            print("control", f["id"], w[:10], len(a), "rows", "complete" if complete else "CAPPED")
        save(p, {"captured_utc": now(), "condition_id": f["cid"], "window": [lo, hi], "pool_size": pool,
                 "rule": "buyers of the same market with 0.5-20 USDC buy notional there, not a focus wallet, first 15 by sha256(cid+wallet)",
                 "controls": res})


# ---------------------------------------------------------------- holdings: on-chain balance of every later position the API leaves open
def step_holdings(out):
    p = out / "chain" / "holdings.json.gz"
    if p.exists():
        return
    sys.path.insert(0, str(Path(__file__).parent))
    from reconstruct import markets, positions_tokens  # noqa: E402
    latest = int(rpc("eth_blockNumber", [])[0], 16) - 64
    mk = markets()
    todo = []
    for f in FOCUS:
        rows = load(NOTE / "data/raw/activity" / f"{f['wallet']}.json.gz")["rows"]
        for cid, tok in positions_tokens(rows, mk, f["funding_ts"]):
            todo.append((f["wallet"], cid, tok))
    res = {}
    for i in range(0, len(todo), 9):
        part = todo[i:i + 9]
        calls = [("eth_call", [{"to": CTF, "data": SEL["balanceOf1155"] + w32(w) + w32(int(t))}, hex(latest)]) for w, c, t in part]
        vals, node = rpc_batch(calls, urls=["https://polygon-bor-rpc.publicnode.com", "https://polygon.drpc.org"])
        for (w, c, t), v in zip(part, vals):
            res[f"{w}:{t}"] = {"condition_id": c, "balance": v}
    save(p, {"captured_utc": now(), "block": latest, "contract": CTF, "balances": res})
    print("holdings", len(res), "balances read")


# ---------------------------------------------------------------- bounds: timestamps of the ledger window edges
def step_bounds(out):
    p = out / "chain" / "ledger_bounds.json.gz"
    if p.exists():
        return
    res = {}
    for f in FOCUS:
        raw = load(out / "chain" / f"ledger_{f['id']}.json.gz")
        res[f["id"]] = {}
        for k in ("from_block", "to_block"):
            blk, node = rpc("eth_getBlockByNumber", [hex(raw[k]), False])
            res[f["id"]][k] = {"block": raw[k], "timestamp": int(blk["timestamp"], 16), "hash": blk["hash"]}
    save(p, {"captured_utc": now(), "bounds": res})
    print("bounds", res)


# ---------------------------------------------------------------- accounts: what each studied address is (Safe, deposit wallet, key)
def step_accounts(out):
    p = out / "chain" / "accounts.json.gz"
    if p.exists():
        return
    latest = int(rpc("eth_blockNumber", [])[0], 16) - 64
    res = {}
    for f in FOCUS:
        w = f["wallet"]
        code, _ = rpc("eth_getCode", [w, hex(latest)])
        nonce, _ = rpc("eth_getTransactionCount", [w, hex(latest)])
        r = {"code_bytes": (len(code) - 2) // 2, "code_sha256": hashlib.sha256(bytes.fromhex(code[2:])).hexdigest() if len(code) > 2 else None,
             "nonce": int(nonce, 16)}
        for name, sel in (("getOwners", "0xa0e67e2b"), ("owner", "0x8da5cb5b")):
            try:
                r[name] = call(w, sel, latest)[0]
            except SourceError as e:
                r[name] = None
                r[name + "_error"] = str(e)[:160]
        res[w] = r
    save(p, {"captured_utc": now(), "block": latest, "accounts": res})
    print("accounts", {w: {k: (v if not isinstance(v, str) or len(v) < 80 else v[:80]) for k, v in r.items()} for w, r in res.items()})


# ---------------------------------------------------------------- gamma for control markets: projected fields only (size)
PROJ = ("conditionId", "question", "slug", "outcomes", "clobTokenIds", "outcomePrices", "closed", "umaResolutionStatus",
        "endDate", "eventStartTime", "negRisk", "questionID")


def step_gamma_controls(out):
    p = out / "gamma" / "control_markets_projected.json.gz"
    if p.exists():
        return
    have = set(condition_ids())
    cids = set()
    for f in FOCUS:
        raw = load(out / "controls" / f"control_activity_{f['id']}.json.gz")
        for c in raw["controls"].values():
            cids |= {(r.get("condition_id") or "").lower() for r in c["rows"] if r.get("condition_id")}
    cids = sorted(cids - have)
    got, queries = {}, []
    for i in range(0, len(cids), 100):
        batch = cids[i:i + 100]
        for closed in ("true", "false"):
            todo = [c for c in batch if c not in got]
            if not todo:
                break
            rows = get_json(GAMMA + f"closed={closed}&limit=500&" + "&".join("condition_ids=" + c for c in todo))
            queries.append({"closed": closed, "requested": len(todo), "returned": len(rows)})
            for m in rows:
                ev = (m.get("events") or [{}])[0]
                got[m["conditionId"].lower()] = {**{k: m.get(k) for k in PROJ}, "event_slug": ev.get("slug")}
        time.sleep(0.1)
    save(p, {"captured_utc": now(), "fields": list(PROJ) + ["event_slug"], "requested": len(cids),
             "missing": [c for c in cids if c not in got], "queries": queries, "markets": [got[c] for c in cids if c in got]})
    print("gamma controls", len(got), "of", len(cids))


STEPS = {"activity": step_activity, "gamma": step_gamma, "chain": step_chain, "ledger": step_ledger, "payouts": step_payouts,
         "external": step_external, "klines": step_klines, "holdings": step_holdings, "bounds": step_bounds, "accounts": step_accounts, "gamma_controls": step_gamma_controls, "participants": step_participants, "controls": step_controls}

if __name__ == "__main__":
    args = sys.argv[1:]
    out = NOTE / "data/raw"
    if "--out" in args:
        out = Path(args[args.index("--out") + 1])
    for s in [a for a in args if a in STEPS] or list(STEPS):
        try:
            STEPS[s](out)
        except SourceError as e:
            sys.exit(f"{s}: source unavailable, nothing recorded for the failing file: {e}")
