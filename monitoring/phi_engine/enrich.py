"""From an entry to its alerts: wallet history, funding, links, classes. Every network read is in this file.

  history   the wallet's public activity (data API), newest 1,000 rows. An answer that does not contain the entry's own
            fill is a source that has not caught up, never "a wallet without history": the entry waits and is read again.
  funding   for a fresh deposit of a thin or dormant wallet: the receipt, the apparent payer, and when that payer is a
            contract, what the wallet received in the 10,000 blocks before (the deposit is then its own money, swapped).
  links     plain keys behind those deposits. Contracts, tagged addresses and busy keys are services: never a link.
  classes   the classes of the frozen study (asof.py, same code), and the two group classes from the links stored so far.
            An entry is read again while its wallet keeps buying: the heavy class fires when the net buying reaches 10,000 USD.
"""
import hashlib, json, time
from phi_monitor import net
from . import asof, chainfund, contracts, models, report, store

DATA = "https://data-api.polymarket.com"
LABELS = "https://metadata.services.blockscout.com/api/v1/metadata?chainId=137&addresses="
WIDE_RPC = ["https://gateway.tenderly.co/public/polygon", "https://polygon.drpc.org"]     # accept 10,000 blocks on old logs (measured 2026-11-14)
WINDOW = 10000                  # blocks before a deposit or a payment: about four hours
SLICE_RPC = ["https://polygon-bor-rpc.publicnode.com"]   # 10,000 blocks at most a call, block times included (measured 2026-11-14)
SLICE, SHORT_SPAN = 9000, 120000
PASS_THROUGH_NONCE, BUSY_NONCE, FANOUT_MAX, WEEK = 5, 1000, 10, 7 * 86400
R1_AGE_S, R1_PRIOR, R1_LOOKBACK_S = 48 * 3600, 2, 30 * 86400     # the study's R1 (phase-8 S_FRESH), as in feat_30
CODE = {"TRADE": "T", "DEPOSIT": "D", "WITHDRAWAL": "W", "REDEEM": "R", "CONVERSION": "C", "SPLIT": "S", "MERGE": "M"}
RETRY_S = (60, 120, 300, 300, 600, 900, 1800)     # waits before an entry whose sources are not ready is tried again


class NotReady(RuntimeError):
    """A source has not caught up or did not answer: the entry is tried again later, nothing is concluded."""


def history(wallet, get_json=net.get_json):
    """Newest 1,000 activity rows of a wallet, oldest first, slim. Returns (rows, more_exist)."""
    j = get_json(f"{DATA}/v2/activity?user={wallet}&sort_by=TIMESTAMP&sort_direction=DESC&exclude_deposits_withdrawals=false&limit=1000")
    data = j.get("data") if isinstance(j, dict) else None
    if not isinstance(data, list):
        raise net.SourceError("activity: unexpected answer")
    rows = []
    for r in reversed(data):
        if str(r.get("proxy_wallet", "")).lower() != wallet:
            raise net.SourceError("activity: row of another wallet")
        typ = CODE.get(r.get("type"), "X")
        rows.append([int(r["timestamp"]), typ, r.get("condition_id") if typ == "T" else None, r.get("side") if typ == "T" else None,
                     float(r.get("usdc_size") or 0), float(r.get("price") or 0) if typ == "T" else None,
                     int(r["outcome_index"]) if typ == "T" and r.get("outcome_index") not in (None, "") else None,
                     r.get("transaction_hash") if typ in ("D", "W") else None])
    return rows, bool((j.get("pagination") or {}).get("has_more"))


def describe(con, addresses, rpc=net.rpc, get_json=net.get_json):
    """Code, transaction count and public tags of addresses not described yet. Unavailable tags are stored as such."""
    known = {r[0] for r in con.execute("select address from addresses")}
    for a in sorted(set(addresses) - known):
        code = rpc("eth_getCode", [a, "latest"]); nonce = rpc("eth_getTransactionCount", [a, "latest"])
        if code is None or nonce is None:
            raise NotReady(f"code or nonce of {a} not served")
        try:
            j = get_json(LABELS + a)
            found = {k.lower(): v for k, v in (j.get("addresses") or {}).items()}      # the service answers with checksummed addresses
            tags, status = json.dumps([t.get("name") for t in (found.get(a) or {}).get("tags", []) if t.get("name")]), "ok"
        except net.SourceError:
            tags, status = None, "unavailable"
        with con:
            con.execute("insert or replace into addresses values(?,?,?,?,?,?)", (a, int(code not in ("0x", "0x0")), int(nonce, 16), tags, status, time.time()))


def person_like(con, a):
    """No code, no public tag, not busy. A tag that could not be read keeps the address out: unknown is never a link."""
    r = con.execute("select is_contract, nonce, tags, tags_status from addresses where address=?", (a,)).fetchone()
    return bool(r) and r[0] == 0 and r[3] == "ok" and r[2] == "[]" and r[1] < BUSY_NONCE


def transfers_in(address, to_block, rpc=net.rpc):
    topic = "0x" + "0" * 24 + address[2:]
    logs = rpc("eth_getLogs", [{"fromBlock": hex(max(1, to_block - WINDOW + 1)), "toBlock": hex(to_block), "address": sorted(chainfund.STABLES),
                                "topics": [chainfund.TRANSFER, None, topic]}], urls=WIDE_RPC)
    if not isinstance(logs, list):
        raise NotReady("logs not served")
    return [{"from": "0x" + l["topics"][1][-40:].lower(), "token": l["address"].lower(), "value": int(l["data"], 16), "block": int(l["blockNumber"], 16),
             "tx": l["transactionHash"]} for l in logs if not l.get("removed") and int(l["data"], 16) > 0]


def chain_inflows(wallet, from_ts, t, rpc=net.rpc):
    """Collateral transfers received by the wallet with from_ts <= block time < t: the study's col_41 reading. The range
    starts at a block whose header is at or before from_ts; every log must carry its block time."""
    def head(b):
        h = rpc("eth_getBlockByNumber", [hex(b), False])
        if not h or not h.get("timestamp"):
            raise NotReady(f"header {b} not served")
        return int(h["timestamp"], 16)
    tip = int(rpc("eth_blockNumber", []), 16); tip_ts = head(tip)
    if tip_ts < t:
        raise NotReady("the node has not reached the entry yet")
    fb = max(1, tip - int((tip_ts - from_ts) / 1.5) - 1000)
    while fb > 1 and head(fb) > from_ts:
        fb = max(1, fb - (tip - fb))
    q = lambda lo, hi: {"fromBlock": hex(lo), "toBlock": hex(hi), "address": sorted(chainfund.STABLES),
                        "topics": [chainfund.TRANSFER, None, "0x" + "0" * 24 + wallet[2:]]}
    if tip - fb <= SHORT_SPAN:          # a day or two: slices that the capped endpoints serve (measured 2026-11-14)
        logs = []
        for lo in range(fb, tip + 1, SLICE):
            part = rpc("eth_getLogs", [q(lo, min(tip, lo + SLICE - 1))], urls=SLICE_RPC)
            if not isinstance(part, list):
                raise NotReady("logs not served")
            logs += part
    else:                               # the 30 days of R1: one wide call, on the endpoint that accepts it
        logs = rpc("eth_getLogs", [q(fb, tip)], urls=WIDE_RPC)
        if not isinstance(logs, list):
            raise NotReady("logs not served")
    out = []
    for l in logs:
        if l.get("removed") or int(l["data"], 16) <= 0:
            continue
        if not l.get("blockTimestamp"):
            raise NotReady("a log without its block time")
        ts = int(l["blockTimestamp"], 16)
        if from_ts <= ts < t:
            out.append({"from": "0x" + l["topics"][1][-40:].lower(), "value": int(l["data"], 16), "tx": l["transactionHash"], "ts": ts})
    return out


def trace_funding(con, wallet, deposits, rpc=net.rpc, get_json=net.get_json):
    """Store the payer of each deposit [(ts, usdc, tx)], what came before it when the payer is a contract, and the links."""
    for ts, usdc, tx in deposits:
        if con.execute("select 1 from deposits where wallet=? and tx=? and status='ok'", (wallet, tx)).fetchone():
            continue
        rec = rpc("eth_getTransactionReceipt", [tx])
        if rec is None:                                    # a node that does not hold the receipt: not "no payer"
            raise NotReady(f"receipt {tx} not served")
        f = chainfund.payer_of_deposit(rec.get("logs") or [], wallet)
        sha = hashlib.sha256(json.dumps(rec, sort_keys=True).encode()).hexdigest(); block = int(rec["blockNumber"], 16)
        payer = f and f["payer"]
        if payer:
            describe(con, [payer], rpc, get_json)
        senders = []
        if payer and con.execute("select is_contract from addresses where address=?", (payer,)).fetchone()[0]:
            rows = transfers_in(wallet, block, rpc)
            senders = [r for r in rows if r["tx"] != tx and r["from"] != wallet]
            describe(con, [r["from"] for r in senders], rpc, get_json)
            with con:
                con.execute("insert or replace into inflows values(?,?,?,?,?)", (wallet, tx, block, "ok", json.dumps(rows)))
        roots = [(payer, 0, block)] if payer and payer != wallet and person_like(con, payer) else []
        roots += [(r["from"], 2, r["block"]) for r in senders if person_like(con, r["from"])]
        for a, kind, blk in list(roots):                   # one hop behind a key that has almost no transaction of its own
            if con.execute("select nonce from addresses where address=?", (a,)).fetchone()[0] <= PASS_THROUGH_NONCE:
                hop = [r for r in transfers_in(a, blk, rpc) if r["from"] not in (a, wallet)]
                describe(con, [r["from"] for r in hop], rpc, get_json)
                with con:
                    con.execute("insert or replace into hops values(?,?,?,?)", (a, blk, "ok", json.dumps(hop)))
                roots += [(r["from"], 1, r["block"]) for r in hop if person_like(con, r["from"])]
        with con:
            con.execute("insert or replace into deposits values(?,?,?,?,?,?,?,?,?)", (wallet, tx, ts, usdc, "ok" if f else "no_credit", payer, f and f["via"], block, sha))
            con.executemany("insert or ignore into links values(?,?,?,?,?)", [(wallet, a, kind, tx, ts) for a, kind, _ in roots])


def group_classes(con, e, event_slug):
    """C4 and C5 for one entry, from the links stored so far and dated before it. Returns {class: {other, root}}."""
    out = {}
    for root, tx in con.execute("select root, tx from links where wallet=? and ts<? and ts>=?", (e["wallet"], e["t"], e["t"] - asof.FRESH_S)).fetchall():
        fan = con.execute("select count(distinct wallet) from links where root=? and ts<?", (root, e["t"])).fetchone()[0]
        if fan > FANOUT_MAX:
            continue
        for w2, t2, slug2 in con.execute("select en.wallet, en.t, m.event_slug from links l join entries en on en.wallet=l.wallet "
                                         "join markets m on m.condition_id=en.condition_id where l.root=? and l.wallet!=? and en.t<=? and l.ts<=en.t",
                                         (root, e["wallet"], e["t"])):
            if slug2 == event_slug and e["t"] - WEEK <= t2 and "C4_COFUNDED_GROUP" not in out:
                out["C4_COFUNDED_GROUP"] = {"other_wallet": w2, "root": root, "deposit_tx": tx}
            if slug2 != event_slug and t2 <= e["t"] - WEEK and "C5_RECURRENT_FUNDER" not in out:
                out["C5_RECURRENT_FUNDER"] = {"other_wallet": w2, "root": root, "deposit_tx": tx}
    return out


def context(con, e, token_id):
    """Market context of the entry from the fills of 1,000 USD or more stored before it (same definitions as the study)."""
    toks = [r[0] for r in con.execute("select token_id from tokens where condition_id=? order by oi", (e["condition_id"],))]
    q = "select ts, wallet, token_id, side, cash, price from fills where token_id in (?,?) and cash>=? and ts<? and ts>=? order by ts"
    recent = [r for r in con.execute(q, (*toks, contracts.MIN_ENTRY_USD, e["t"], e["t"] - 86400)) if r["wallet"] != e["wallet"]]
    hour = con.execute("select token_id, price from fills where token_id in (?,?) and cash>=? and ts<=? order by ts desc limit 1",
                       (*toks, contracts.MIN_ENTRY_USD, e["t"] - 3600)).fetchone()
    price_1h = None if hour is None else (hour["price"] if hour["token_id"] == token_id else 1.0 - hour["price"])
    buyers = len({r["wallet"] for r in recent if r["token_id"] == token_id and r["side"] == "BUY" and r["ts"] >= e["t"] - 6 * 3600})
    # earlier large fills of the wallet on markets that are not of an excluded kind (the study counts them on its universe);
    # a fill on a token the store never resolved is not counted
    before = con.execute("select count(*) from fills f join tokens t on t.token_id=f.token_id join markets m on m.condition_id=t.condition_id "
                         "where f.wallet=? and f.cash>=? and f.ts<? and m.family!='EXCLUDED'", (e["wallet"], contracts.MIN_ENTRY_USD, e["t"])).fetchone()[0]
    return {"mk_fills_24h": len(recent), "mk_fills_6h": sum(1 for r in recent if r["ts"] >= e["t"] - 6 * 3600),
            "side_buy_cash_24h": sum(r["cash"] for r in recent if r["token_id"] == token_id and r["side"] == "BUY"), "price_1h": price_1h,
            "co_entrants_6h": buyers, "w_fills_before": before}


def evaluate(con, e, rpc=net.rpc, get_json=net.get_json, now=time.time, rarity=None):
    """All classes of one entry as of now. Returns (list of new alert bodies, watch) or raises NotReady."""
    m = con.execute("select * from markets where condition_id=?", (e["condition_id"],)).fetchone()
    token_id = con.execute("select token_id from tokens where condition_id=? and oi=?", (e["condition_id"], e["oi"])).fetchone()[0]
    rows, more = history(e["wallet"], get_json)
    if not any(r[1] == "T" and r[2] == e["condition_id"] and r[6] == e["oi"] and r[3] == "BUY" and r[0] >= e["t"] - 2 for r in rows):
        raise NotReady("the wallet's history does not show the entry yet")
    floor = asof.THIN_ROWS if more and rows and rows[0][0] < e["t"] else 0
    w = asof.watch(rows, e["t"], e["condition_id"], e["oi"], e["cash"], rows_before_floor=floor)
    v, f = w["view"], w["flags"]
    v0 = dict(v)                                                     # the model features keep the deposit rows only, as in the study
    ctx = context(con, e, token_id)
    # as in the study: money received on the chain counts as funding, and R1 dates the wallet by its first inflow
    first_seen = rows[0][0] if rows and not more else None          # newest 1,000 rows: the first row is the wallet's only without more
    need24 = (f["thin"] or f["dormant"]) and not f["fresh"]
    need_r1 = ctx["w_fills_before"] <= R1_PRIOR and first_seen is not None and first_seen >= e["t"] - R1_AGE_S
    earliest = None
    if need24 or need_r1:
        got = chain_inflows(e["wallet"], e["t"] - (R1_LOOKBACK_S if need_r1 else asof.FRESH_S), e["t"], rpc)
        day = [g for g in got if g["ts"] >= e["t"] - asof.FRESH_S]
        mint_payer = {}
        for g in day:                                                # pUSD minted to the wallet: who paid the wrapped collateral
            if g["from"] == asof.ZERO:
                rec = rpc("eth_getTransactionReceipt", [g["tx"]])
                if rec is None:
                    raise NotReady(f"receipt {g['tx']} not served")
                fd = chainfund.payer_of_deposit(rec.get("logs") or [], e["wallet"]); mint_payer[g["tx"]] = fd and fd["payer"]
        describe(con, {g["from"] for g in day if g["from"] not in chainfund.INFRA and g["from"] != e["wallet"]}, rpc, get_json)
        tagged = {r[0] for r in con.execute("select address from addresses where tags like '%Polymarket%'")}
        extra, earliest, _ = asof.chain_rows(got, e["wallet"], e["t"], {r[7] for r in rows if r[1] == "D"}, chainfund.INFRA | tagged,
                                             busy_ts={r[0] for r in rows if r[1] not in ("D", "I")}, mint_payer=mint_payer)
        extra = [x for x in extra if x[0] >= e["t"] - asof.FRESH_S] if need24 else []
        if extra:
            w = asof.watch(sorted(rows + extra, key=lambda r: r[0]), e["t"], e["condition_id"], e["oi"], e["cash"], rows_before_floor=floor)
            v, f = w["view"], w["flags"]
    if first_seen is not None:
        v["age_h"] = (e["t"] - first_seen) / 3600.0 if first_seen < e["t"] else None
    if f["fresh"] and (f["thin"] or f["dormant"]):
        trace_funding(con, e["wallet"], [d for d in v["deposits_7d"] if d[0] >= e["t"] - asof.FRESH_S and d[2]], rpc, get_json)
    fired = {k: {"t": (x[0] or e["t"]), "price": (x[1] if x[1] is not None else e["price"])} for k, x in asof.classes(w).items() if x and k[0] == "C"}
    if "C1_FRESH_FUNDED_BET" in fired and ctx["mk_fills_6h"] == 0 and e["price"] <= 0.50:
        fired["C6_QUIET_FRESH_LOW"] = {"t": e["t"], "price": e["price"]}
    for cls, link in group_classes(con, e, m["event_slug"]).items():
        if f["fresh"] and (f["thin"] or f["dormant"]):
            fired[cls] = {"t": e["t"], "price": e["price"], "link": link}
    r1_age = first_seen if (first_seen is not None and first_seen < e["t"] - R1_AGE_S) else (
        min(x for x in (first_seen, earliest) if x is not None) if need_r1 else None)
    if r1_age is not None and e["t"] - r1_age <= R1_AGE_S and ctx["w_fills_before"] <= R1_PRIOR:
        fired["R1_S_FRESH_REPLICATION"] = {"t": e["t"], "price": e["price"]}
    x = models.vector(dict(e, hours_to_end=((m["end_ts"] - e["t"]) / 3600.0 if m["end_ts"] else 0.0), **{k: v[k] for k in (
        "prior_trades", "prior_other_markets", "age_h", "prior_trade_median", "last_other_trade_ts")}, dep_24h=v0["dep_24h"], dep_7d=v0["dep_7d"], **ctx))
    score = None
    if rarity:
        s, parts = models.rarity_score(rarity["model"], x)
        score = {"score": round(s, 3), "parts": {k: round(p, 2) for k, p in parts.items()}, "threshold_top1pct": rarity["threshold"]}
        if s >= rarity["threshold"]:
            fired["M1_RARITY_TOP1"] = {"t": e["t"], "price": e["price"]}
    new = []
    for cls, a in fired.items():
        if a["price"] is None or a["price"] > contracts.PRICE_MAX or (m["end_ts"] is not None and a["t"] >= m["end_ts"] + contracts.END_GRACE_S):
            continue                                       # same admissibility rule as the study
        body = report.build(con, e, m, cls, a, w, ctx, score, now())
        with con:
            cur = con.execute("insert or ignore into alerts values(?,?,?,?,?,?,?,?)", (body["id"], cls, a["t"], now(), e["wallet"], e["condition_id"], e["oi"],
                                                                                   json.dumps(body, sort_keys=True)))
            if cur.rowcount:
                store.journal(con, "alert", {"id": body["id"], "class": cls, "wallet": e["wallet"], "condition_id": e["condition_id"], "oi": e["oi"],
                                             "t_alert": a["t"], "evidence_tx": body["evidence"]["fills"][:3]})
                new.append(body)
    with con:
        con.execute("insert or replace into views values(?,?,?,?,?)", (e["wallet"], e["condition_id"], e["oi"], json.dumps({"view": v, "flags": f, "heavy": w["heavy"], "net_buy": w["net_buy"],
                                                                                                                      "context": ctx, "rarity": score}), now()))
    return new, w


def work(con, db_path=None, budget=15, rpc=net.rpc, get_json=net.get_json, now=time.time, rarity=None):
    """Evaluate the entries that are due. An entry is watched for 24 hours: it is read again when its wallet bought more of
    the same side. A source that is not ready postpones the entry; after the last wait it is marked unavailable, visibly."""
    t = now(); alerts = []; counts = {"evaluated": 0, "not_ready": 0, "unavailable": 0, "closed": 0}
    due = con.execute("select * from entries where state in ('new','watching') and next_try<=? order by next_try, t limit ?", (t, budget)).fetchall()
    for e in due:
        e = dict(e)
        if e["state"] == "watching":
            if t > e["t"] + asof.WATCH_S:
                with con:
                    con.execute("update entries set state='done' where wallet=? and condition_id=? and oi=?", (e["wallet"], e["condition_id"], e["oi"]))
                counts["closed"] += 1; continue
            tok = con.execute("select token_id from tokens where condition_id=? and oi=?", (e["condition_id"], e["oi"])).fetchone()[0]
            seen = con.execute("select fetched from views where wallet=? and condition_id=? and oi=?", (e["wallet"], e["condition_id"], e["oi"])).fetchone()
            more = con.execute("select 1 from fills where wallet=? and token_id=? and side='BUY' and seen>? limit 1", (e["wallet"], tok, seen[0] if seen else 0)).fetchone()
            if not more:                                   # nothing new from this wallet on this side: look again in ten minutes
                with con:
                    con.execute("update entries set next_try=? where wallet=? and condition_id=? and oi=?", (t + 600, e["wallet"], e["condition_id"], e["oi"]))
                continue
        try:
            new, _ = evaluate(con, e, rpc, get_json, now, rarity)
        except (NotReady, net.SourceError) as err:
            tries = e["tries"] + 1; gone = tries > len(RETRY_S)
            with con:
                con.execute("update entries set tries=?, next_try=?, state=?, note=? where wallet=? and condition_id=? and oi=?",
                            (tries, t + RETRY_S[min(tries, len(RETRY_S)) - 1], "unavailable" if gone else e["state"], str(err)[:200],
                             e["wallet"], e["condition_id"], e["oi"]))
                if gone:
                    store.journal(con, "entry_unavailable", {"wallet": e["wallet"], "condition_id": e["condition_id"], "oi": e["oi"], "why": str(err)[:200]})
            counts["unavailable" if gone else "not_ready"] += 1; continue
        counts["evaluated"] += 1
        with con:
            con.execute("update entries set state='watching', tries=0, next_try=?, note=null where wallet=? and condition_id=? and oi=?",
                        (t + 600, e["wallet"], e["condition_id"], e["oi"]))
        for body in new:
            if db_path:
                store.append_alert_file(db_path, body)
            alerts.append(body)
    return alerts, counts
