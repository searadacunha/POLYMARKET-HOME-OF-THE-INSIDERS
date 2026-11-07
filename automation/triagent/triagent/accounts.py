"""Shadow collector: new Polymarket accounts (factory events on Polygon) and the payer of their first deposit.

It records only: no alert, no mission, no notification. The rows are prospective, point-in-time data for a
study to be frozen before any rate is computed (proposal kept outside the repository). Each row keeps the
block time of the creation AND the time this collector observed it; `bursts(as_of=T)` reads only what was
observed by T. A shared bridge, exchange or relayer is a service, not a link: labelled payers and payers of
many accounts are left out of the bursts.
"""
from __future__ import annotations

from .config import Config
from .polymarket import activity, deposit_source, labels, rpc
from .store import Store, now, sha256_bytes
from .util import ProviderError, get_json, http

# Decoded on 2026-11-07 from deployments listed in investigations/ballon-dor-census (wallet_deploy.json):
FACTORY_2026 = "0x00000000000fb5c9adea0298d729a0cb3823cc07"   # topic1 = proxy, topic2 = owner key
SAFE_FACTORY = "0xaacfeea03eb1561c4e67d661e40682bd20e3541b"   # ProxyCreation(proxy, singleton), both in data
NEW_2026 = "0x7441de0ad639fe5d2bf1c22447715a0528b682385736bb40ae8dd92555eb8276"
SAFE_TOPIC = "0x4f51faf6"                                       # prefix of ProxyCreation(address,address)
MAX_BLOCKS = 500                                                # per tick: catches up after sleep at ~12x real time


def decode(log: dict) -> tuple[str, str] | None:
    addr, topics, data = log.get("address", "").lower(), log.get("topics") or [], log.get("data") or ""
    if addr == FACTORY_2026 and len(topics) >= 3 and topics[0] == NEW_2026:
        return "0x" + topics[1][-40:].lower(), "0x" + topics[2][-40:].lower()
    if addr == SAFE_FACTORY and topics and topics[0].startswith(SAFE_TOPIC) and len(data) >= 66:
        return "0x" + data[26:66].lower(), ""
    return None


def scan_creations(cfg: Config, store: Store, post=http) -> int:
    head = int(rpc(cfg, "eth_blockNumber", [], post)[0], 16) - cfg.int("CONFIRMATIONS")
    start = int(store.get_kv("accounts_block") or head - 30) + 1
    end = min(head, start + MAX_BLOCKS - 1)
    if end < start:
        return 0
    added, block_ts = 0, {}
    for factory in (FACTORY_2026, SAFE_FACTORY):  # one address per call: some endpoints refuse a list
        logs, _ = rpc(cfg, "eth_getLogs", [{"address": factory, "fromBlock": hex(start), "toBlock": hex(end)}], post)
        if not isinstance(logs, list):
            raise ProviderError("transient", "eth_getLogs returned no list")
        for log in logs:
            found = None if log.get("removed") else decode(log)
            if not found:
                continue
            block = int(log["blockNumber"], 16)
            ts = log.get("blockTimestamp")
            if ts is None and block not in block_ts:
                header, _ = rpc(cfg, "eth_getBlockByNumber", [hex(block), False], post)
                block_ts[block] = header and header.get("timestamp")
            ts = ts or block_ts.get(block)
            added += store.execute("INSERT OR IGNORE INTO new_accounts(proxy,factory,owner,block,tx_hash,created_ts,"
                                   "observed_at) VALUES (?,?,?,?,?,?,?)",
                                   (found[0], factory, found[1], block, log["transactionHash"].lower(),
                                    int(ts, 16) if ts else None, now()))
    store.set_kv("accounts_block", end)  # only after both factories were read for the whole range
    return added


def trace_first_deposits(cfg: Config, store: Store, fetch=get_json, post=http) -> dict:
    """Payer of the first deposit, looked up 10 min, 1 h, 6 h and 24 h after an account was observed, newest first.
    Measured 2026-11-07: ~750 accounts/h and 4 of 25 funded within the hour, so a fixed 30-min re-check for 24 h
    would need ~23 lookups/min; this schedule needs ~2."""
    todo = store.query("""SELECT proxy FROM new_accounts WHERE first_deposit_tx IS NULL AND checks<4 AND ? >= observed_at +
                          CASE checks WHEN 0 THEN 600 WHEN 1 THEN 3600 WHEN 2 THEN 21600 ELSE 86400 END
                          ORDER BY observed_at DESC LIMIT ?""", (now(), cfg.int("ACCOUNTS_PER_TICK")))
    out = {"checked": 0, "funded": 0, "traced": 0}
    for row in todo:
        proxy = row["proxy"]
        rows, _ = activity(proxy, fetch, max_pages=1)
        out["checked"] += 1
        dep = next((r for r in rows if r.get("type") == "DEPOSIT"), None)
        trade = next((r["timestamp"] for r in rows if r.get("type") == "TRADE"), None)
        store.execute("UPDATE new_accounts SET checked_at=?, checks=checks+1, first_trade_ts=? WHERE proxy=?",
                      (now(), trade, proxy))
        tx = str((dep or {}).get("transaction_hash", "")).lower()
        if not tx.startswith("0x"):
            continue
        out["funded"] += 1
        receipt, raw = rpc(cfg, "eth_getTransactionReceipt", [tx], post)
        found = deposit_source(receipt, proxy) if receipt else None
        out["traced"] += bool(found)
        store.execute("UPDATE new_accounts SET first_deposit_tx=?, first_deposit_ts=?, receipt_sha256=?, funder=?, "
                      "funder_via=?, deposit_token=?, deposit_value=? WHERE proxy=?",
                      (tx, dep["timestamp"], sha256_bytes(raw) if receipt else None,
                       found and found["funder"], found and found["via"], found and found["token"],
                       found and str(found["value"]), proxy))
        if found:
            labels(store, [found["funder"]], fetch)  # cached; unavailable labels keep the payer out of bursts
    return out


def bursts(store: Store, *, k: int = 3, window: int = 3600, fanout_cap: int = 25, as_of: int | None = None,
           lookback: int = 86400) -> list[dict]:
    """Payers whose first deposits reached >= k new accounts within `window`, using only rows observed by
    `as_of`. Display only (shadow): thresholds are not calibrated and nothing is sent anywhere."""
    t = as_of or now()
    rows = store.query("""SELECT n.funder, n.proxy, n.first_deposit_ts, n.first_trade_ts, l.tags_json FROM new_accounts n
                          LEFT JOIN labels l ON l.address=n.funder
                          WHERE n.funder IS NOT NULL AND n.observed_at<=? AND n.checked_at<=?
                            AND n.first_deposit_ts BETWEEN ? AND ? ORDER BY n.funder, n.first_deposit_ts""",
                       (t, t, t - lookback, t))
    by: dict[str, list[dict]] = {}
    for r in rows:
        by.setdefault(r["funder"], []).append(r)
    out = []
    for funder, accts in by.items():
        if accts[0]["tags_json"] is None or accts[0]["tags_json"] != "[]" or len(accts) > fanout_cap:
            continue  # labelled, label unknown, or a high fan-out payer: a service until shown otherwise
        times = [a["first_deposit_ts"] for a in accts]
        best, lo = 0, 0
        for hi in range(len(times)):  # largest group of deposits inside one window
            while times[hi] - times[lo] > window:
                lo += 1
            best = max(best, hi - lo + 1)
        if best >= k:
            out.append({"funder": funder, "accounts": best, "accounts_24h": len(accts),
                        "first_deposit": times[0], "last_deposit": times[-1],
                        "traded_when_traced": sum(1 for a in accts if a["first_trade_ts"] and a["first_trade_ts"] <= t),
                        "proxies": [a["proxy"] for a in accts][:20]})
    return sorted(out, key=lambda b: -b["accounts"])


def tick(cfg: Config, store: Store) -> dict:
    added = scan_creations(cfg, store)
    return {"created": added, **trace_first_deposits(cfg, store)}
