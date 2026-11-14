"""Incremental collection. Every step is resumable from a checkpoint written in the same transaction as its rows.

watch_chain  exchange fills from Polygon logs (complete and about 2.5 s late, measured 2026-11-13) -> fills + triggers
resolve      token -> market and tags (Gamma), on demand
fetch_prices 10-minute price points of the YES token (CLOB prices-history, at most 14 days per request)
fetch_tape   complete tape of one market down to a time (data API, newest first, cursor pagination)
baseline     history of a wallet strictly before a time (data API activity, `end` asserted)
funding      who paid a wallet (Polygon logs of the official collateral tokens)
"""
import datetime as dt, json, statistics, time
from . import chain, net, store, ws

GAMMA, DATA, CLOB = "https://gamma-api.polymarket.com", "https://data-api.polymarket.com", "https://clob.polymarket.com"
CONFIRMATIONS = 3          # blocks left unread behind the head
CHUNK = 20                 # blocks per eth_getLogs call
MAX_CATCHUP = 1800         # blocks (about one hour): a longer outage is journaled as a gap, never silently skipped
EXCLUDED_TAGS = {"games", "esports", "crypto-prices", "hit-price", "up-or-down", "multi-strikes", "weather", "tweets-markets",
                 "mention-markets"}   # outcomes produced in public; same list as the frozen study
TRIGGER_MIN_CASH = 100.0
REF_MAX, MULT, ABS_STEP = 0.15, 3.0, 0.10
PROFILE_FIELDS = ("name", "pseudonym", "bio", "profile_image", "profile_image_optimized", "icon")


def watch_chain(con, max_chunks=30, head=None):
    """Read new exchange fills up to head - CONFIRMATIONS. Returns {"fills": n, "triggers": n, "from": b, "to": b}."""
    head = (head if head is not None else chain.head()) - CONFIRMATIONS
    last = (store.checkpoint(con, "chain") or {}).get("block")
    if last is None:
        last = head - 1                                   # first start: no history is claimed
    elif head - last > MAX_CATCHUP:
        store.journal(con, "gap", {"stream": "chain", "from_block": last + 1, "to_block": head - 1, "reason": "outage longer than MAX_CATCHUP"})
        last = head - 1
    out = {"fills": 0, "triggers": 0, "from": last + 1, "to": last}
    for _ in range(max_chunks):
        if last >= head:
            break
        hi = min(head, last + CHUNK)
        fills = chain.fills(last + 1, hi)
        with con:                                        # rows, triggers and checkpoint commit together
            out["fills"] += store.add_fills(con, fills, "chain")
            out["triggers"] += sum(_trigger(con, f) for f in fills)
            store.checkpoint(con, "chain", {"block": hi, "t": time.time()})
        last = out["to"] = hi
    return out


def _trigger(con, f):
    """Cheap pre-filter on one new fill; the official rule is applied later on the price series. Returns 1 if a candidate was opened."""
    if f["side"] != "BUY" or f["cash"] < TRIGGER_MIN_CASH or f["price"] > 0.90:
        return 0
    ref = [r[0] for r in con.execute("select price from fills where token_id=? and ts between ? and ? and source='chain'",
                                     (f["token_id"], f["ts"] - 7 * 3600, f["ts"] - 3600))]
    if len(ref) >= 5:
        m = statistics.median(ref)
        if m > REF_MAX or f["price"] < max(MULT * m, m + ABS_STEP):
            return 0
    elif f["price"] < ABS_STEP + 0.03:                   # history unknown: let the price series decide, but only for a visible price
        return 0
    known = con.execute("select condition_id, outcome from tokens where token_id=?", (f["token_id"],)).fetchone()
    if known is None:                                    # market not resolved yet: scan() resolves it once
        return con.execute("insert or ignore into candidates values(?,?,?,?,?)", ("token:" + f["token_id"], "?", f["ts"], "new", "")).rowcount
    # a side already judged is looked at again only for a later move (one hour after its previous first sight)
    return con.execute("insert into candidates values(?,?,?,?,?) on conflict(condition_id, side) do update set "
                       "first_seen=excluded.first_seen, state='pending', note='' "
                       "where candidates.state in ('closed','expired') and excluded.first_seen - candidates.first_seen > 3600",
                       (known[0], "YES" if known[1] == "Yes" else "NO", f["ts"], "pending", "")).rowcount


def resolve(con, token_id):
    """Market of a token (Gamma), stored. Returns the market row or None when Gamma does not know the token."""
    r = con.execute("select condition_id from tokens where token_id=?", (token_id,)).fetchone()
    if r is None:
        j = net.get_json(f"{GAMMA}/markets?clob_token_ids={token_id}") or net.get_json(f"{GAMMA}/markets?clob_token_ids={token_id}&closed=true")
        if not j:
            return None
        m = j[0]; toks = json.loads(m["clobTokenIds"]); outs = json.loads(m["outcomes"])
        if outs != ["Yes", "No"] or len(toks) != 2:
            return None                                   # not a Yes/No market: outside the validated population
        slug = (m.get("events") or [{}])[0].get("slug")
        tags = [t.get("slug") for t in (net.get_json(f"{GAMMA}/events/slug/{slug}").get("tags") or [])] if slug else []
        end = m.get("endDate")
        with con:
            store.put_market(con, {"condition_id": m["conditionId"], "event_slug": slug, "title": m.get("question"), "tags": tags,
                                   "neg_risk": m.get("negRisk"), "yes_token": toks[0], "no_token": toks[1], "closed": m.get("closed"),
                                   "end_ts": int(dt.datetime.fromisoformat(end.replace("Z", "+00:00")).timestamp()) if end else None})
        r = (m["conditionId"],)
    return con.execute("select * from markets where condition_id=?", (r[0],)).fetchone()


def fetch_prices(con, yes_token, start, end):
    """10-minute points of the YES token in [start, end] (at most 14 days). Returns the number of points stored."""
    j = net.get_json(f"{CLOB}/prices-history?market={yes_token}&startTs={int(start)}&endTs={int(end)}&fidelity=10")
    h = j.get("history")
    if not isinstance(h, list):
        raise net.SourceError("unexpected prices-history schema")
    with con:
        con.executemany("insert or replace into prices values(?,?,?)", [(yes_token, int(p["t"]), float(p["p"])) for p in h])
    return len(h)


def fetch_tape(con, condition_id, down_to, max_pages=300, fresh=False):
    """Complete tape (maker and taker rows) from the latest trade down to `down_to`. Rows replace the earlier copy of the
    same window, so a re-read never doubles a fill. Returns {"rows": n, "pages": n, "complete": bool}."""
    rows, cursor, pages, last = [], None, 0, None
    while pages < max_pages:
        url = f"{DATA}/v2/trades?condition={condition_id}&limit=1000&taker_only=false" + (f"&cursor={cursor}" if cursor else "")
        if fresh and not cursor:
            url += f"&cb={int(time.time() * 1000)}"       # the first page is served from a 300 s cache otherwise (measured)
        j = net.get_json(url); data = j.get("data")
        if not isinstance(data, list):
            raise net.SourceError("unexpected trades schema")
        pages += 1
        for r in data:
            ts = int(r["timestamp"])
            if last is not None and ts > last:
                raise net.SourceError("tape not newest-first")
            last = ts
            if ts >= down_to:
                rows.append({"tx": r["transaction_hash"], "log_index": -len(rows) - 1, "block": None, "ts": ts, "wallet": r["proxy_wallet"].lower(),
                             "counterparty": None, "token_id": str(r["token_id"]), "side": r["side"], "shares": float(r["size"]),
                             "cash": float(r["size"]) * float(r["price"]), "price": float(r["price"])})
        pg = j.get("pagination") or {}; cursor = pg.get("next_cursor")
        if (last is not None and last < down_to) or not pg.get("has_more") or not cursor:
            with con:
                con.execute("delete from fills where source='api' and ts>=? and token_id in (select token_id from tokens where condition_id=?)",
                            (down_to, condition_id))
                store.add_fills(con, rows, "api")
            return {"rows": len(rows), "pages": pages, "complete": True}
    return {"rows": 0, "pages": pages, "complete": False}   # too deep: nothing stored, the caller records it


def baseline(con, wallet, as_of):
    """History of `wallet` strictly before `as_of` (cached). Text fields of the profile are never read or stored."""
    r = con.execute("select body from baselines where wallet=? and as_of=?", (wallet, as_of)).fetchone()
    if r:
        return json.loads(r[0])
    q = f"{DATA}/v2/activity?user={wallet}&sort_by=TIMESTAMP&exclude_deposits_withdrawals=false"
    first = net.get_json(q + "&limit=1&sort_direction=ASC").get("data") or []
    j = net.get_json(q + f"&limit=500&sort_direction=DESC&end={int(as_of) - 1}")
    prior = j.get("data") or []
    if any(int(x["timestamp"]) >= as_of for x in prior):
        raise net.SourceError("activity `end` filter not honoured")
    tr = [x for x in prior if x.get("type") == "TRADE"]; cash = [float(x.get("usdc_size") or 0) for x in tr]
    dep = [x for x in prior if x.get("type") == "DEPOSIT" and int(x["timestamp"]) >= as_of - 72 * 3600]
    status, body = net.fetch(f"{GAMMA}/public-profile?address={wallet}")
    if status not in (200, 404):                              # 404 = no profile; any other answer is a failed source, not "no date"
        raise net.SourceError(f"HTTP {status} for the public profile of {wallet}", status)
    created = json.loads(body).get("createdAt") if status == 200 else None
    out = {"first_activity": int(first[0]["timestamp"]) if first else None,
           "profile_created": dt.datetime.fromisoformat(created.replace("Z", "+00:00")).timestamp() if created else None,
           "prior_rows": len(prior), "prior_rows_capped": bool((j.get("pagination") or {}).get("has_more")),
           "prior_trades": len(tr), "prior_markets": len({x.get("condition_id") for x in tr}),
           "prior_trade_median": statistics.median(cash) if cash else None,
           "deposits_72h": [{"ts": int(x["timestamp"]), "usdc": float(x.get("usdc_size") or 0), "tx": x.get("transaction_hash")} for x in dep]}
    with con:
        con.execute("insert or replace into baselines values(?,?,?,?)", (wallet, as_of, json.dumps(out), time.time()))
    return out


PASS_THROUGH_NONCE = 2      # a key that had made at most this many transactions when it paid is read one hop further
UPSTREAM_WINDOW = 48 * 3600


def funding(con, proxy, t_from, t_to, hops=1):
    """Direct collateral transfers received by `proxy` in [t_from, t_to], from Polygon logs, with each payer described by
    behaviour only: mint (bridge credit, origin unknown here), contract, key, or high-volume key (service-like).
    Only a plain key with few transactions can later count as a shared payer; a bridge or a hot wallet never does.
    When the payer is a brand-new key (a pass-through), its own payers are read too, once: money often reaches a new
    account through a key created for it."""
    done = store.checkpoint(con, f"funding:{proxy}:{int(t_from)}:{int(t_to)}")
    if not done:
        rows = chain.transfers_to(proxy, chain.block_at(t_from), chain.block_at(t_to) + 20)
        kinds = {}
        for r in rows:
            k = kinds.get(r["payer"]) or kinds.setdefault(r["payer"], chain.account_kind(r["payer"], r["block"]))  # as of its first transfer
            r.update(proxy=proxy, payer_kind=k["kind"], payer_nonce=k["nonce"], ts=r["ts"] or chain.block_ts(r["block"]))
        with con:
            con.executemany("insert or replace into funding values(:tx,:log_index,:block,:ts,:proxy,:payer,:token,:amount,:payer_kind,:payer_nonce)", rows)
            store.checkpoint(con, f"funding:{proxy}:{int(t_from)}:{int(t_to)}", {"rows": len(rows)})
    out = [dict(r) for r in con.execute("select * from funding where proxy=? and ts between ? and ? order by ts", (proxy, t_from, t_to))]
    if hops > 0:
        for r in out:
            if r["payer_kind"] == "key" and r["payer_nonce"] <= PASS_THROUGH_NONCE:
                funding(con, r["payer"], r["ts"] - UPSTREAM_WINDOW, r["ts"], hops - 1)
    return out


MARKET_WS = "wss://ws-subscriptions-clob.polymarket.com/ws/market"


def _ws_rows(data, seen):
    """Trade prints of one market-channel message: (token, ms, price, size, side, tx, seen). The channel carries no wallet."""
    if data[:1] not in (b"{", b"["):
        return []                                         # keep-alive replies
    msgs = json.loads(data); msgs = msgs if isinstance(msgs, list) else [msgs]
    return [(m["asset_id"], int(m["timestamp"]), float(m["price"]), float(m["size"]), m.get("side"), m.get("transaction_hash") or "", seen)
            for m in msgs if isinstance(m, dict) and m.get("event_type") == "last_trade_price"]


def watch_prices(con, token_ids, stop_at):
    """Record every trade print of the given tokens from the public market channel until `stop_at`.
    The client reconnects by itself (backoff 1 s to 30 s, and after 2 minutes without any message); returns its connection events."""
    def on_open(sock):
        sock.send(json.dumps({"assets_ids": list(token_ids), "type": "market"}))

    def on_msg(kind, data, t):
        if kind == "text":
            rows = _ws_rows(data, t)
            if rows:
                with con:
                    con.executemany("insert or ignore into ws_trades values(?,?,?,?,?,?,?)", rows)
    return ws.run_forever(MARKET_WS, on_open, on_msg, stop_at, ping_every=8, silence_timeout=120)
