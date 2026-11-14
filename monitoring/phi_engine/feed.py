"""Chain feed: every OrderFilled of every registered exchange, then the entries they open.

  watch     reads new blocks from the checkpoint to the finalized block, however long the engine was off. Nothing is
            skipped: a long outage is caught up over several passes, and the lag is journaled while it lasts. The query
            names no contract: fills of an emitter the registry does not know are counted and journaled, never kept.
  sentinel  asks the chain for OrderFilled logs WITHOUT naming a contract, on a few blocks, and journals any emitter the
            registry does not know: a new exchange must never go unseen again.
  resolve   token -> market, outcome index, tags (Gamma). A token Gamma does not know yet is asked again later.
  entries   a BUY fill of 1,000 USD or more at 0.90 or less, on a market whose outcome is not produced in public view,
            before the end of the day that follows its scheduled end date: the first one of a wallet on a side of a
            market is an entry."""
import datetime as dt, json, time
from phi_monitor import net
from . import contracts, store

GAMMA = "https://gamma-api.polymarket.com"
CONFIRMATIONS = 3
CHUNK = 20                      # blocks per eth_getLogs call
LAG_GUARD = 10                  # blocks: a chunk ending closer than this to the tip must show its last block in the answer
# shortcut: a logs node more than LAG_GUARD blocks behind the finalized block would still answer short unseen; upgrade by
# reading the tip and the logs from one pinned endpoint if the reorg probe ever shows such a lag
RETRY_UNKNOWN_S = 600           # a token unknown to Gamma is asked again after this long
UNKNOWN_EVERY_S = 3600          # an emitter outside the registry is journaled again after this long


def decode(log):
    """OrderFilled log -> fill dict. One log is one order being filled, seen from its owner; the taker's own order has the
    exchange as counterparty. Raises ValueError on an unexpected shape."""
    t, d = log["topics"], log["data"][2:]
    if t[0] != contracts.ORDER_FILLED or len(t) != 4 or len(d) < 64 * 4 or len(d) % 64:
        raise ValueError("not an OrderFilled log")
    w = [int(d[i:i + 64], 16) for i in range(0, min(len(d), 64 * 5), 64)]
    if w[0] not in (0, 1) or w[2] == 0 or w[3] == 0:
        raise ValueError(f"side {w[0]}, amounts {w[2]} and {w[3]}")
    cash, shares = (w[2], w[3]) if w[0] == 0 else (w[3], w[2])          # BUY: the order gives collateral and receives tokens
    return {"tx": log["transactionHash"], "log_index": int(log["logIndex"], 16), "block": int(log["blockNumber"], 16),
            "ts": int(log["blockTimestamp"], 16) if log.get("blockTimestamp") else None, "exchange": log["address"].lower(),
            "wallet": "0x" + t[2][-40:], "counterparty": "0x" + t[3][-40:], "token_id": str(w[1]), "side": "BUY" if w[0] == 0 else "SELL",
            "shares": shares / 1e6, "cash": cash / 1e6, "fee": (w[4] / 1e6 if len(w) > 4 else None), "price": cash / shares}


def head(rpc=net.rpc):
    return int(rpc("eth_blockNumber", []), 16)


def finalized(rpc=net.rpc):
    """Newest finalized block. Polygon finalizes by milestones, 1 to 4 blocks behind the head on 14 November 2026
    (median 3, measured on public nodes): reading only up to it keeps blocks that can still be reorganized out of the store."""
    b = rpc("eth_getBlockByNumber", ["finalized", False])
    if not b or not b.get("number"):
        raise net.SourceError("finalized block not served")
    return int(b["number"], 16)


def _block(log):
    try:
        return int(log["blockNumber"], 16)
    except (KeyError, TypeError, ValueError):
        return None


def read_fills(lo, hi, rpc=net.rpc):
    """(fills, rejected) of every OrderFilled emitter in [lo, hi], in chain order. The query names no contract, so a fill
    of an exchange outside the registry is read too (its `exchange` is not in contracts.EXCHANGES): the caller counts it."""
    logs = rpc("eth_getLogs", [{"fromBlock": hex(lo), "toBlock": hex(hi), "topics": [contracts.ORDER_FILLED]}])
    if not isinstance(logs, list):
        raise net.SourceError("eth_getLogs did not return a list")
    fills, bad, times = [], [], {}
    for log in logs:
        try:
            if log.get("removed"):
                raise ValueError("removed: the node reports this log as reorganized away")
            f = decode(log)
        except (ValueError, KeyError, IndexError) as e:                # one strange log must not stop the feed: it is journaled
            bad.append({"tx": log.get("transactionHash"), "log_index": log.get("logIndex"), "block": _block(log), "why": str(e)[:120]}); continue
        if f["ts"] is None:
            if f["block"] not in times:
                b = rpc("eth_getBlockByNumber", [hex(f["block"]), False])
                if not b:
                    raise net.SourceError(f"block {f['block']} not served")
                times[f["block"]] = int(b["timestamp"], 16)
            f["ts"] = times[f["block"]]
        fills.append(f)
    return sorted(fills, key=lambda f: (f["block"], f["log_index"])), bad


def watch(con, max_chunks=30, rpc=net.rpc, now=time.time):
    """Advance the chain checkpoint by at most max_chunks chunks, up to the finalized block. Returns counts; never skips
    a block. Fills of an emitter outside the registry are counted (coverage, journal) and never kept as rows."""
    tip = finalized(rpc)
    last = (store.checkpoint(con, "chain") or {}).get("block")
    if last is None:
        last = tip - 1                                                 # first start: history before it is not claimed
        with con:
            store.journal(con, "start", {"first_block": tip})
    out = {"fills": 0, "stored": 0, "big_buys": 0, "unknown": 0, "from": last + 1, "to": last, "behind": max(0, tip - last)}
    strangers = {}
    for _ in range(max_chunks):
        if last >= tip:
            break
        hi = min(tip, last + CHUNK)
        fills, bad = read_fills(last + 1, hi, rpc)
        top = max([f["block"] for f in fills] + [b["block"] for b in bad if b["block"] is not None], default=last)
        if top < hi:                                # a node behind the others answers up to its own head without saying so (drpc,
            hi = max(top, min(hi, tip - LAG_GUARD))  # measured 2026-11-14): a block near the tip counts once the answer shows it
            if hi <= last:
                break
        other = [f for f in fills if f["exchange"] not in contracts.EXCHANGES]
        fills = [f for f in fills if f["exchange"] in contracts.EXCHANGES]
        for f in other:
            strangers[f["exchange"]] = strangers.get(f["exchange"], 0) + 1
        watched = {r[0] for r in con.execute("select distinct wallet from entries where state in ('new','watching')")}
        keep = [f for f in fills if f["cash"] >= contracts.MIN_ENTRY_USD or f["wallet"] in watched]
        cover = {}
        for f in fills + other:                                        # every fill is counted, whether its row is kept or not
            c = cover.setdefault((f["ts"] // 3600 * 3600, f["exchange"]), [0, 0, 0.0])
            c[0] += 1; c[1] += f["cash"] >= contracts.MIN_ENTRY_USD; c[2] += f["cash"]
        with con:                                                      # rows, counts, journal and checkpoint commit together
            before = con.total_changes
            con.executemany("insert or ignore into fills values(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                            [(f["tx"], f["log_index"], f["block"], f["ts"], f["exchange"], f["wallet"], f["counterparty"], f["token_id"], f["side"],
                              f["shares"], f["cash"], f["fee"], f["price"], now()) for f in keep])
            out["stored"] += con.total_changes - before
            for (hour, exchange), (n, large, cash) in cover.items():
                con.execute("insert into coverage values(?,?,?,?,?) on conflict(hour, exchange) do update set fills=fills+excluded.fills, "
                            "large=large+excluded.large, cash=cash+excluded.cash", (hour, exchange, n, large, cash))
            for b in bad:
                store.journal(con, "removed_log" if b["why"].startswith("removed") else "undecodable_log", b)
            store.checkpoint(con, "chain", {"block": hi, "t": now(), "block_ts": fills[-1]["ts"] if fills else None})
        out["fills"] += len(fills); out["unknown"] += len(other)
        out["big_buys"] += sum(1 for f in fills if f["side"] == "BUY" and f["cash"] >= contracts.MIN_ENTRY_USD and f["price"] <= contracts.PRICE_MAX)
        last = out["to"] = hi
    out["behind"] = max(0, tip - last)
    if strangers:                                                      # each emitter journaled once an hour while it lasts
        said = store.checkpoint(con, "unknown_journaled") or {}
        new = {a: n for a, n in strangers.items() if a not in said or now() - said[a] > UNKNOWN_EVERY_S}
        if new:
            with con:
                store.journal(con, "unknown_exchange", {"blocks": [out["from"], last], "emitters": new})
                store.checkpoint(con, "unknown_journaled", dict(said, **{a: now() for a in new}))
    if out["behind"] > 4 * CHUNK * max_chunks:                         # far behind: said once an hour while it lasts
        seen = store.checkpoint(con, "lag_journaled") or {}
        if now() - seen.get("t", 0) > 3600:
            with con:
                store.journal(con, "catching_up", {"blocks_behind": out["behind"], "at_block": last})
                store.checkpoint(con, "lag_journaled", {"t": now()})
    return out


def sentinel(con, rpc=net.rpc, blocks=4):
    """Journal any OrderFilled emitter that the registry does not list. Returns {address: logs}."""
    tip = head(rpc) - CONFIRMATIONS
    logs = rpc("eth_getLogs", [{"fromBlock": hex(tip - blocks + 1), "toBlock": hex(tip), "topics": [contracts.ORDER_FILLED]}])
    unknown = contracts.unknown_emitters(logs if isinstance(logs, list) else [])
    if unknown:
        with con:
            store.journal(con, "unknown_exchange", {"blocks": [tip - blocks + 1, tip], "emitters": unknown})
    return unknown


def _ts(s):
    return int(dt.datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()) if s else None


def resolve(con, token_id, get_json=net.get_json, now=time.time, exchange=None):
    """Market of a token, stored. Returns the token row, with status ok, unknown (asked again later), not_binary, or combo
    (a combinatorial position of Protocol V2: not a side of one market, never asked to the catalogue)."""
    r = con.execute("select * from tokens where token_id=?", (token_id,)).fetchone()
    if r is not None and (r["status"] != "unknown" or now() - r["checked"] < RETRY_UNKNOWN_S):
        return r
    if exchange is not None and contracts.is_combo(exchange, token_id):
        with con:
            con.execute("insert or replace into tokens values(?,?,?,?,?)", (token_id, None, None, "combo", now()))
        return con.execute("select * from tokens where token_id=?", (token_id,)).fetchone()
    j = (get_json(f"{GAMMA}/markets?clob_token_ids={token_id}") or get_json(f"{GAMMA}/markets?clob_token_ids={token_id}&closed=true")
         or get_json(f"{GAMMA}/markets?position_ids={token_id}&closed=any"))
    with con:
        if not j:
            con.execute("insert or replace into tokens values(?,?,?,?,?)", (token_id, None, None, "unknown", now()))
        else:
            # Protocol V2 markets list their outcomes in `positionIds` (a list; `clobTokenIds` may be null): the field is chosen
            # by `version`, as docs.polymarket.com/migrate/polymarket-v2/api-integrations says (read 2026-11-14)
            m = j[0]; ids = m.get("positionIds") if m.get("version") == "v2" else m.get("clobTokenIds")
            toks = [str(x) for x in (json.loads(ids) if isinstance(ids, str) else ids or [])]; outs = json.loads(m.get("outcomes") or "[]")
            if len(toks) != 2 or token_id not in toks:
                con.execute("insert or replace into tokens values(?,?,?,?,?)", (token_id, m.get("conditionId"), None, "not_binary", now()))
            else:
                slug = (m.get("events") or [{}])[0].get("slug")
                tags = [t.get("slug") for t in ((get_json(f"{GAMMA}/events/slug/{slug}") or {}).get("tags") or [])] if slug else []
                con.execute("insert or replace into markets values(?,?,?,?,?,?,?,?,?,?)",
                            (m["conditionId"], slug, m.get("question"), json.dumps(outs), json.dumps(tags), contracts.family(tags) if slug else "UNKNOWN",
                             int(bool(m.get("negRisk"))), m.get("version"), _ts(m.get("endDate")), now()))
                for i, tok in enumerate(toks):
                    con.execute("insert or replace into tokens values(?,?,?,?,?)", (tok, m["conditionId"], i, "ok", now()))
    return con.execute("select * from tokens where token_id=?", (token_id,)).fetchone()


GIVE_UP_UNKNOWN_S = 2 * 3600    # a token still unknown to the catalogue after this long is journaled and left


def open_entries(con, since_rowid=0, get_json=net.get_json, limit=400, now=time.time):
    """Turn the large BUY fills stored after `since_rowid` into entries. A fill whose token the catalogue does not know yet
    is put aside and looked at again at the next passes: it never holds back the fills behind it.
    Returns (new entries, last rowid seen, counts)."""
    q = "select rowid, * from fills where %s and side='BUY' and cash>=? and price<=? order by rowid limit ?"
    waiting = dict(con.execute("select rowid_fill, first_seen from pending_fills").fetchall())
    rows = (con.execute(q % f"rowid in ({','.join(map(str, waiting)) or 'null'})", (contracts.MIN_ENTRY_USD, contracts.PRICE_MAX, limit)).fetchall()
            + con.execute(q % "rowid>?", (since_rowid, contracts.MIN_ENTRY_USD, contracts.PRICE_MAX, limit)).fetchall())
    new, c = 0, {"large_buys": 0, "excluded_family": 0, "unknown_token": 0, "not_binary": 0, "after_scheduled_end": 0, "not_first": 0, "given_up": 0, "combo": 0}
    last = since_rowid
    for f in rows:
        fresh = f["rowid"] not in waiting
        c["large_buys"] += fresh; last = max(last, f["rowid"])
        tok = resolve(con, f["token_id"], get_json, now, exchange=f["exchange"])
        if tok["status"] == "combo":
            c["combo"] += 1; continue
        if tok["status"] == "unknown":
            c["unknown_token"] += 1
            with con:
                if fresh:
                    con.execute("insert or ignore into pending_fills values(?,?,?)", (f["rowid"], f["token_id"], now()))
                elif now() - waiting[f["rowid"]] > GIVE_UP_UNKNOWN_S:
                    con.execute("delete from pending_fills where rowid_fill=?", (f["rowid"],)); c["given_up"] += 1
                    store.journal(con, "token_never_resolved", {"token_id": f["token_id"], "tx": f["tx"], "exchange": f["exchange"]})
            continue
        if not fresh:
            with con:
                con.execute("delete from pending_fills where rowid_fill=?", (f["rowid"],))
        if tok["status"] != "ok":
            c["not_binary"] += 1; continue
        m = con.execute("select family, end_ts from markets where condition_id=?", (tok["condition_id"],)).fetchone()
        if m["family"] == "EXCLUDED":                                   # checked at every fill, not only the first time the token is seen
            c["excluded_family"] += 1; continue
        if m["end_ts"] is not None and f["ts"] >= m["end_ts"] + contracts.END_GRACE_S:
            c["after_scheduled_end"] += 1; continue
        with con:
            cur = con.execute("insert or ignore into entries(wallet, condition_id, oi, t, block, price, cash, tx, log_index, state) values(?,?,?,?,?,?,?,?,?,?)",
                              (f["wallet"], tok["condition_id"], tok["oi"], f["ts"], f["block"], f["price"], f["cash"], f["tx"], f["log_index"], "new"))
        new += cur.rowcount; c["not_first"] += 1 - cur.rowcount
    return new, last, c
