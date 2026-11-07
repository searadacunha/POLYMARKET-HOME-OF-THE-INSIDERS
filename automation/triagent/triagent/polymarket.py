"""Polymarket surveillance beyond the known cohorts.

1. Global large-trade feed (Data API v2 /v2/trades, cash filter, cursor, checkpoint, backfill).
2. Wallet profile from /v2/activity (full history ascending), point-in-time features.
3. Funding origin and withdrawal destination from the Polygon receipt of each DEPOSIT /
   WITHDRAWAL row, archived as evidence; edges are stored with their transaction.
4. Flags -> alerts -> missions, only when the trade is confirmed on chain.

PolyBolt streams reference prices only (and needs CLOB credentials): it carries no trade
tape, so the trade feed is polled. First order submission is not observable here: the
earliest observable event is the first executed fill or deposit.
"""
from __future__ import annotations

import json
import urllib.parse
from pathlib import Path
from typing import Any

from .config import Config
from .detector import features_asof, flags_for
from .store import Store, canonical, now, sha256_bytes
from .util import ProviderError, get_json, http

DATA = "https://data-api.polymarket.com"
LABELS = "https://metadata.services.blockscout.com/api/v1/metadata"
GAMMA = "https://gamma-api.polymarket.com"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
ZERO = "0x" + "0" * 40
COLLATERAL = "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"   # Polymarket USD collateral (pUSD)
USDC_E = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
USDC = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
STABLES = {COLLATERAL, USDC_E, USDC}
PM_INFRA = {COLLATERAL, "0xc417fd8e9661c0d2120b64a04bb3278c17e99db1", "0x4bfb41d5b3570defd03c39a9a4d8de6bd8b8982e",
            "0xc5d563a36ae78145c45a50134d48a1215220f80a", "0x4d97dcd97ec945f40cf65f87097ace5ea0476045", ZERO}
PERSONAL = ("name", "pseudonym", "bio", "profile_image", "profile_image_optimized", "icon")
TRADE_FIELDS = {"proxy_wallet": str, "side": str, "token_id": str, "condition_id": str, "size": (int, float),
                "price": (int, float), "timestamp": int, "transaction_hash": str}


def strip(row: dict) -> dict:
    return {k: v for k, v in row.items() if k not in PERSONAL}


def well_formed(row: Any) -> bool:
    return isinstance(row, dict) and all(isinstance(row.get(k), t) and not isinstance(row.get(k), bool)
                                         for k, t in TRADE_FIELDS.items()) \
        and row["transaction_hash"].startswith("0x") and row["proxy_wallet"].startswith("0x")


# ---------------------------------------------------------------- 1. trade feed
def collect_trades(cfg: Config, store: Store, fetch=get_json) -> dict:
    base = (f"{DATA}/v2/trades?limit=500&taker_only=false&filter_type=CASH"
            f"&filter_amount={cfg.int('ALERT_MIN_USDC')}")
    checkpoint = int(store.get_kv("trades_checkpoint_ts", "0"))
    cursor, pages, inserted, malformed, newest, reached = None, 0, 0, 0, checkpoint, False
    while True:
        page = fetch(base + (f"&cursor={urllib.parse.quote(cursor)}" if cursor else ""))
        rows = page.get("data") if isinstance(page, dict) else None
        if not isinstance(rows, list):
            raise ProviderError("permanent", "trades feed: unexpected payload shape")
        with store.conn(immediate=True) as c:
            for row in rows:
                if not well_formed(row):
                    malformed += 1
                    continue
                ts = row["timestamp"]
                if checkpoint and ts < checkpoint - 300:  # 5 min overlap absorbs same-second ordering
                    reached = True
                    continue
                newest = max(newest, ts)
                cur = c.execute(
                    """INSERT OR IGNORE INTO trades(tx_hash,proxy_wallet,condition_id,token_id,side,size,price,usdc,
                       ts,title,outcome,seen_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (row["transaction_hash"].lower(), row["proxy_wallet"].lower(), row["condition_id"],
                     row["token_id"], row["side"], float(row["size"]), float(row["price"]),
                     round(float(row["size"]) * float(row["price"]), 6), ts, str(row.get("title", ""))[:300],
                     str(row.get("outcome", ""))[:80], now()))
                inserted += cur.rowcount
        pages += 1
        pag = page.get("pagination") or {}
        cursor = pag.get("next_cursor")
        if reached or not cursor or not checkpoint or pages >= cfg.int("BACKFILL_MAX_PAGES"):
            break
    if checkpoint and not reached and cursor:
        store.log("collector", f"backfill stopped after {pages} pages before reaching checkpoint {checkpoint}: "
                  "a gap may exist in the large-trade record", level="warning")
    if malformed:
        store.log("collector", f"{malformed} malformed trade rows skipped", level="warning")
    store.set_kv("trades_checkpoint_ts", newest)
    store.set_kv("last_collect_ok", now())
    return {"pages": pages, "inserted": inserted, "malformed": malformed, "reached_checkpoint": reached}


# ---------------------------------------------------------------- 2. wallet profile
def activity(address: str, fetch=get_json, max_pages: int = 3) -> tuple[list[dict], bool]:
    url = (f"{DATA}/v2/activity?user={address}&start=1&sort_by=TIMESTAMP&sort_direction=ASC"
           f"&exclude_deposits_withdrawals=false&limit=1000")
    rows, cursor = [], None
    for _ in range(max_pages):
        page = fetch(url + (f"&cursor={urllib.parse.quote(cursor)}" if cursor else ""))
        data = page.get("data") if isinstance(page, dict) else None
        if not isinstance(data, list):
            raise ProviderError("permanent", "activity: unexpected payload shape")
        rows += [strip(r) for r in data if isinstance(r, dict) and isinstance(r.get("timestamp"), int)]
        cursor = (page.get("pagination") or {}).get("next_cursor")
        if not cursor:
            return rows, False
    return rows, True  # truncated: more history exists than was read


# ---------------------------------------------------------------- 3. receipts
def rpc(cfg: Config, method: str, params: list, post=http) -> Any:
    last: Exception | None = None
    for endpoint in cfg.get("POLYGON_RPC").split(","):
        try:
            _, raw = post(endpoint.strip(), method="POST", timeout=30,
                          body={"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
            payload = json.loads(raw)
            if "error" in payload:
                raise ProviderError("transient", f"rpc error {payload['error']}")
            return payload.get("result"), raw
        except (ProviderError, json.JSONDecodeError) as exc:
            last = exc
    raise ProviderError("transient", f"all Polygon RPC endpoints failed: {last}")


def archive(cfg: Config, store: Store, raw: bytes, ref: str) -> str:
    sha = sha256_bytes(raw)
    path = cfg.evidence_dir / f"{sha}.json"
    if not path.exists():
        cfg.evidence_dir.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    store.add_evidence(sha, "collector", ref, path, len(raw), chain="polygon")
    return sha


def transfers(receipt: dict) -> list[dict]:
    out = []
    for log in receipt.get("logs", []):
        topics = log.get("topics", [])
        if len(topics) == 3 and topics[0] == TRANSFER:
            out.append({"token": log["address"].lower(), "from": "0x" + topics[1][-40:].lower(),
                        "to": "0x" + topics[2][-40:].lower(), "value": int(log.get("data") or "0x0", 16)})
    return out


def deposit_source(receipt: dict, proxy: str) -> dict | None:
    """Who paid a DEPOSIT: a stablecoin sent straight to the proxy, or the USDC that was wrapped
    into the collateral minted to the proxy. Amount matching is used only inside one transaction."""
    proxy = proxy.lower()
    logs = transfers(receipt)
    for t in logs:
        if t["to"] == proxy and t["token"] in STABLES and t["from"] not in PM_INFRA:
            return upstream(logs, {"funder": t["from"], "token": t["token"], "value": t["value"], "via": "direct"})
    minted = [t for t in logs if t["token"] == COLLATERAL and t["from"] == ZERO and t["to"] == proxy]
    for m in minted:
        for t in logs:
            if t["token"] in (USDC_E, USDC) and t["to"] == COLLATERAL and t["value"] == m["value"] \
                    and t["from"] not in PM_INFRA:
                return upstream(logs, {"funder": t["from"], "token": t["token"], "value": t["value"], "via": "wrapped"})
    return None


def upstream(logs: list[dict], found: dict) -> dict:
    """Walk back, inside the same transaction, through contracts that only relay the same amount
    (deposit wallet, on-ramp contract) to the first sender. The relays are kept in `path`."""
    path, current = [], found["funder"]
    for _ in range(5):
        prev = next((t for t in logs if t["to"] == current and t["from"] != current and t["value"] == found["value"]
                     and t["token"] in STABLES and t["from"] not in PM_INFRA), None)
        if not prev:
            break
        path.append(current)
        current = prev["from"]
    return {**found, "funder": current, "path": path}


def withdrawal_destination(receipt: dict, proxy: str) -> dict | None:
    proxy = proxy.lower()
    logs = transfers(receipt)
    burned = [t["value"] for t in logs if t["token"] == COLLATERAL and t["to"] == ZERO]
    out_of_proxy = [t for t in logs if t["from"] == proxy and t["token"] in STABLES and t["to"] not in PM_INFRA]
    if out_of_proxy:
        t = out_of_proxy[0]
        return {"destination": t["to"], "token": t["token"], "value": t["value"], "via": "direct"}
    for t in logs:
        if t["token"] in (USDC_E, USDC) and t["from"] in PM_INFRA and t["to"] not in PM_INFRA and t["value"] in burned:
            return {"destination": t["to"], "token": t["token"], "value": t["value"], "via": "unwrapped"}
    return None


def confirmed(cfg: Config, tx: str, post=http) -> tuple[str, dict | None, bytes]:
    """'confirmed' | 'pending' | 'missing' (reorged or never mined) for a trade transaction."""
    receipt, raw = rpc(cfg, "eth_getTransactionReceipt", [tx], post)
    if not receipt:
        return "missing", None, raw
    head, _ = rpc(cfg, "eth_blockNumber", [], post)
    depth = int(head, 16) - int(receipt["blockNumber"], 16)
    if receipt.get("status") != "0x1":
        return "missing", receipt, raw
    return ("confirmed" if depth >= cfg.int("CONFIRMATIONS") else "pending"), receipt, raw


def labels(store: Store, addresses: list[str], fetch=get_json) -> dict[str, list[str]] | None:
    """Public name tags (Blockscout metadata, chain 137), cached 30 days. None when unavailable:
    callers must then refrain from any link signal rather than guess."""
    addresses = sorted({a.lower() for a in addresses if a})
    if not addresses:
        return {}
    marks = ",".join("?" * len(addresses))
    cached = {r["address"]: json.loads(r["tags_json"]) for r in store.query(
        f"SELECT * FROM labels WHERE address IN ({marks}) AND fetched_at > ?", (*addresses, now() - 30 * 86400))}
    missing = [a for a in addresses if a not in cached]
    if missing:
        try:
            page = fetch(f"{LABELS}?chainId=137&addresses={','.join(missing[:100])}")
        except ProviderError:
            return None
        found = {k.lower(): [t.get("name") for t in v.get("tags", []) if t.get("name")]
                 for k, v in (page.get("addresses") or {}).items()} if isinstance(page, dict) else None
        if found is None:
            return None
        for a in missing:
            cached[a] = found.get(a, [])
            store.execute("INSERT INTO labels(address,tags_json,source,fetched_at) VALUES (?,?,?,?) "
                          "ON CONFLICT(address) DO UPDATE SET tags_json=excluded.tags_json, fetched_at=excluded.fetched_at",
                          (a, canonical(cached[a]), "blockscout-metadata", now()))
    return cached


# ---------------------------------------------------------------- 4. profile, flags, alerts
def fanout(store: Store, address: str, t: int, *, as_source: bool) -> int:
    col, other = ("src", "dst") if as_source else ("dst", "src")
    row = store.query(f"SELECT count(DISTINCT {other}) AS n FROM edges WHERE {col}=? AND kind='DIRECT_TRANSFER' "
                      "AND (ts IS NULL OR ts<?)", (address, t))
    return row[0]["n"]


def profile_wallet(cfg: Config, store: Store, address: str, t: int, trade_usdc: float,
                   fetch=get_json, post=http) -> dict:
    rows, truncated = activity(address, fetch)
    feats = features_asof(rows, t, trade_usdc)
    examined = []
    deposits = [r for r in rows if r.get("type") == "DEPOSIT" and r["timestamp"] < t][-2:]
    withdrawals = [r for r in rows if r.get("type") == "WITHDRAWAL" and r["timestamp"] < t][-2:]
    funders, destinations = [], []
    for row, kind in [(r, "deposit") for r in deposits] + [(r, "withdrawal") for r in withdrawals]:
        tx = str(row.get("transaction_hash", "")).lower()
        if not tx.startswith("0x"):
            continue
        receipt, raw = rpc(cfg, "eth_getTransactionReceipt", [tx], post)
        if not receipt:
            continue
        sha = archive(cfg, store, raw, f"polygon:eth_getTransactionReceipt:{tx}")
        found = deposit_source(receipt, address) if kind == "deposit" else withdrawal_destination(receipt, address)
        examined.append({"kind": kind, "tx": tx, "evidence": sha, "result": found})
        if not found:
            continue
        other = found.get("funder") or found.get("destination")
        src, dst = (other, address) if kind == "deposit" else (address, other)
        store.add_edge(src, dst, "DIRECT_TRANSFER", chain="polygon", tx_hash=tx, token=found["token"],
                       amount=str(found["value"]), ts=row["timestamp"], method=f"{kind}-receipt-v1",
                       level="receipt_verified", evidence_sha256=sha)
        (funders if kind == "deposit" else destinations).append(other)
    service = cfg.int("SERVICE_FANOUT")
    tags = labels(store, funders + destinations, fetch)
    if tags is None:  # unknown labels: a bridge or pool could pass for a common funder, so no link flag
        people_funders, people_dest = [], []
    else:
        people_funders = [f for f in funders if not tags.get(f)]
        people_dest = [d for d in destinations if not tags.get(d)]
    shared_funder = any(1 < fanout(store, f, t, as_source=True) <= service for f in people_funders)
    shared_dest = any(1 < fanout(store, d, t, as_source=False) <= service for d in people_dest)
    known = store.query(
        f"SELECT DISTINCT address, source_path FROM known_addresses WHERE address IN ({','.join('?' * (1 + len(people_funders)))})",
        [address, *people_funders])
    co = store.query(
        """SELECT count(DISTINCT t.proxy_wallet) AS n FROM trades t JOIN wallets w ON w.address=t.proxy_wallet
           WHERE t.condition_id=(SELECT condition_id FROM trades WHERE proxy_wallet=? AND ts=? LIMIT 1)
           AND t.outcome=(SELECT outcome FROM trades WHERE proxy_wallet=? AND ts=? LIMIT 1)
           AND t.side='BUY' AND t.proxy_wallet<>? AND t.ts BETWEEN ? AND ?
           AND w.first_activity_ts IS NOT NULL AND t.ts - w.first_activity_ts < 604800""",
        (address, t, address, t, address, t - 21600, t))[0]["n"]
    liquidity = None
    if now() - t < 600:  # displayed liquidity is only point-in-time right after the trade
        cid = store.query("SELECT condition_id FROM trades WHERE proxy_wallet=? AND ts=? LIMIT 1", (address, t))
        if cid:
            try:
                market = fetch(f"{GAMMA}/markets?condition_ids={cid[0]['condition_id']}")
                liq = float((market[0] if isinstance(market, list) and market else {}).get("liquidityNum") or 0)
                liquidity = trade_usdc / liq if liq > 0 else None
            except (ProviderError, ValueError, TypeError):
                liquidity = None
    flags = flags_for(feats, shared_funder=shared_funder, shared_destination=shared_dest, co_entrants=co,
                      known_reuse=bool(known), liquidity_share=liquidity)
    first_dep = next((r["timestamp"] for r in rows if r.get("type") == "DEPOSIT"), None)
    first_trade = next((r["timestamp"] for r in rows if r.get("type") == "TRADE"), None)
    profile = {"features": feats, "flags": flags, "funders": funders, "destinations": destinations,
               "service_labels": tags if tags is not None else "unavailable",
               "co_entrants": co, "liquidity_share": liquidity, "known": known, "receipts": examined,
               "truncated": truncated}
    store.execute("""INSERT INTO wallets(address,first_seen,profiled_at,first_activity_ts,first_deposit_ts,first_trade_ts,
                     n_events,truncated,profile_json) VALUES (?,?,?,?,?,?,?,?,?)
                     ON CONFLICT(address) DO UPDATE SET profiled_at=excluded.profiled_at,
                     first_activity_ts=excluded.first_activity_ts, first_deposit_ts=excluded.first_deposit_ts,
                     first_trade_ts=excluded.first_trade_ts, n_events=excluded.n_events,
                     truncated=excluded.truncated, profile_json=excluded.profile_json""",
                  (address, now(), now(), rows[0]["timestamp"] if rows else None, first_dep, first_trade,
                   len(rows), int(truncated), canonical(profile)))
    return profile


def scan(cfg: Config, store: Store, fetch=get_json, post=http) -> dict:
    """Profile a few recent large BUYs of wallets not profiled in the last day; raise alerts."""
    todo = store.query(
        """SELECT t.proxy_wallet, t.ts, t.usdc, t.condition_id, t.tx_hash, t.title, t.outcome FROM trades t
           LEFT JOIN wallets w ON w.address=t.proxy_wallet
           WHERE t.side='BUY' AND t.onchain='pending' AND t.ts > ?
             AND (w.profiled_at IS NULL OR w.profiled_at < ?)
           GROUP BY t.proxy_wallet ORDER BY max(t.usdc) DESC LIMIT ?""",
        (now() - 3 * 86400, now() - 86400, cfg.int("PROFILES_PER_TICK")))
    alerts = 0
    for row in todo:
        state, _, _ = confirmed(cfg, row["tx_hash"], post)
        if state == "pending":
            continue
        store.execute("UPDATE trades SET onchain=? WHERE tx_hash=?", (state, row["tx_hash"]))
        if state == "missing":
            store.log("collector", f"trade {row['tx_hash']} not found on chain (reorg or indexer error); ignored",
                      level="warning")
            continue
        profile = profile_wallet(cfg, store, row["proxy_wallet"], row["ts"], row["usdc"], fetch, post)
        if len(profile["flags"]) >= cfg.int("ALERT_MIN_FLAGS"):
            alerts += raise_alert(cfg, store, row, profile)
    return {"profiled": len(todo), "alerts": alerts}


def raise_alert(cfg: Config, store: Store, trade: dict, profile: dict) -> int:
    score = len(profile["flags"])
    n = store.execute("""INSERT OR IGNORE INTO alerts(created,address,condition_id,trade_ts,usdc,score,flags_json,
                         features_json) VALUES (?,?,?,?,?,?,?,?)""",
                      (now(), trade["proxy_wallet"], trade["condition_id"], trade["ts"], trade["usdc"], score,
                       canonical(profile["flags"]), canonical(profile)))
    if not n:
        return 0
    store.log("alert", f"{trade['proxy_wallet']} {trade['usdc']:.0f} USDC on '{trade['title'][:80]}' "
              f"flags={profile['flags']}")
    today = store.query("SELECT count(*) AS n FROM jobs WHERE origin='collector' AND created>=?",
                        (now() - now() % 86400,))[0]["n"]
    if today >= cfg.int("ALERT_MISSIONS_DAY"):
        return 1
    people = [f for f in profile["funders"] if isinstance(profile.get("service_labels"), dict)
              and not profile["service_labels"].get(f)]
    cluster = (people or [trade["proxy_wallet"]])[0]
    key = f"alert {cluster} {trade['condition_id']}"
    task = (f"Automatic alert (selection signal, NOT evidence of insider trading). Account {trade['proxy_wallet']} "
            f"bought {trade['usdc']:.0f} USDC of '{trade['outcome']}' on market {trade['condition_id']} "
            f"('{trade['title'][:150]}') at {trade['ts']} (tx {trade['tx_hash']}). Flags: {profile['flags']}. "
            f"Point-in-time features: {canonical(profile['features'])}. Funders seen: {profile['funders']}. "
            f"Public service labels: {canonical(profile.get('service_labels'))}. "
            "Reconstruct the funding path upstream (depth 2, stop at services/exchanges), the account's other "
            "positions and withdrawals, and test against representative traders of the same market who are "
            "not flagged. Report whether the flags survive.")
    job = store.enqueue("claude", "analysis", key, task, origin="collector", priority=min(5, score),
                        falsifier="If unflagged comparable traders of this market show the same funding pattern, "
                                  "the alert is not distinctive.")
    if job:
        store.execute("UPDATE alerts SET job_id=?, status='mission' WHERE address=? AND condition_id=?",
                      (job, trade["proxy_wallet"], trade["condition_id"]))
    return 1


def verify_reported_edges(cfg: Config, store: Store, job_id: str, edges: list[dict], post=http) -> list[dict]:
    """Independent replay of the transfers an agent reports: only a matching log in the
    receipt upgrades an edge to receipt_verified. Other chains stay agent_reported."""
    results = []
    for e in edges[:30]:
        src, dst = str(e.get("src", "")).lower(), str(e.get("dst", "")).lower()
        tx = str(e.get("tx_hash", "")).lower()
        level, sha = "agent_reported", None
        if e.get("kind") not in ("DIRECT_TRANSFER", "BRIDGE_ORDER", "SAME_FUNDER", "SAME_DEPOSIT_ADDRESS",
                                 "SHARED_SERVICE", "TEMPORAL_CORRELATION", "HYPOTHESIS"):
            continue
        if e.get("kind") == "HYPOTHESIS":
            level = "hypothesis"
        elif e.get("kind") == "DIRECT_TRANSFER" and e.get("chain") == "polygon" and len(tx) == 66:
            try:
                receipt, raw = rpc(cfg, "eth_getTransactionReceipt", [tx], post)
                if receipt:
                    sha = archive(cfg, store, raw, f"polygon:eth_getTransactionReceipt:{tx}")
                    if any(t["from"] == src and t["to"] == dst for t in transfers(receipt)):
                        level = "receipt_verified"
            except ProviderError:
                pass
        if src.startswith(("0x", "T")) and dst:
            store.add_edge(src, dst, e["kind"], chain=str(e.get("chain", "")), tx_hash=tx,
                           token=str(e.get("token", "")), amount=str(e.get("amount", "")),
                           ts=e.get("timestamp") or None, method=f"agent:{str(e.get('method', ''))[:80]}",
                           level=level, evidence_sha256=sha, job_id=job_id)
        results.append({"src": src, "dst": dst, "kind": e.get("kind"), "tx": tx, "level": level})
    return results
