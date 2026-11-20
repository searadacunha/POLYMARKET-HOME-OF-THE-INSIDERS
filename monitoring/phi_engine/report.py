"""An alert as a record, and as text for the terminal.

Five parts, always: MARKET, WALLETS, ANOMALY, EVIDENCE, VALIDATION. The score is a set of separate readings, each with
its explanation; there is no single number and no probability of anything. What a class was worth out of sample comes
from reference/validation_status.json, written from the frozen study: a class that did not pass is marked EXPLORATORY."""
import hashlib, json, os, platform, time

HERE = os.path.dirname(os.path.abspath(__file__))
WHAT = {
    "C1_FRESH_FUNDED_BET": "a wallet with almost no history received a deposit in the 24 hours before this first large purchase",
    "C2_DORMANT_REACTIVATION": "a wallet that had not traded another market for 60 days or more received a deposit in the 24 hours before this purchase",
    "C7_HEAVY_NEWCOMER": "a wallet with almost no history, funded in the 24 hours before, has now bought 10,000 USD or more of this one side",
    "C3_OUT_OF_CHARACTER": "this fill is at least ten times the median trade of the wallet and larger than every earlier trade read",
    "C4_COFUNDED_GROUP": "a plain key behind a deposit of this wallet is also behind a deposit of another wallet that entered the same event in the 7 days before",
    "C5_RECURRENT_FUNDER": "a plain key behind a deposit of this wallet was behind a deposit of another wallet that entered a different event at least 7 days earlier",
    "C6_QUIET_FRESH_LOW": "a freshly funded wallet with almost no history buys at 0.50 or less on a market where nobody else had traded 1,000 USD in the 6 hours before",
    "R1_S_FRESH_REPLICATION": "the first deposit of the wallet is 48 hours old or less and it has at most two earlier large fills",
    "M1_RARITY_TOP1": "the combination of size, newness, concentration and market quietness is in the rarest 1 % of the reference population",
}
OTHER = ["a public report, post or broadcast that this engine does not read", "an ordinary new customer placing a first large bet",
         "an experienced trader using a new account", "a hedge of a position held elsewhere", "an attempt to move the price itself",
         "money moved between accounts of one person for reasons unrelated to this market"]


def hashed_files(folder=HERE):
    """Relative paths (with /) of the engine's code and reference data, sorted: every regular .py, .json and .gz file
    under the folder, except caches and hidden or lock files (`._x.py` on FAT volumes, `.#x.py` of editors)."""
    rels = []
    for root, dirs, files in os.walk(folder):
        dirs[:] = [d for d in dirs if d != "__pycache__" and not d.startswith(".")]
        for name in files:
            path = os.path.join(root, name)
            if name.endswith((".py", ".json", ".gz")) and not name.startswith((".", "#")) and os.path.isfile(path):
                rels.append(os.path.relpath(path, folder).replace(os.sep, "/"))
    return sorted(rels)


def code_sha256(folder=HERE):
    """(SHA-256, number of files): for each file of hashed_files(), its relative path, a NUL byte, its size as 8 bytes
    big-endian and its bytes. Text files are read with CRLF turned into LF, so a checkout with other line endings gives
    the same value."""
    h, rels = hashlib.sha256(), hashed_files(folder)
    for rel in rels:
        with open(os.path.join(folder, rel), "rb") as f:
            data = f.read()
        if not rel.endswith(".gz"):
            data = data.replace(b"\r\n", b"\n")
        h.update(rel.encode() + b"\0" + len(data).to_bytes(8, "big") + data)
    return h.hexdigest(), len(rels)


def detector():
    try:
        digest, n = code_sha256()
        return {"engine": "phi_engine", "code_sha256": digest, "files_hashed": n, "python": platform.python_version()}
    except (OSError, UnicodeError) as error:  # a file that cannot be read must not stop the engine: the alert says so
        return {"engine": "phi_engine", "code_sha256": None, "files_hashed": None, "python": platform.python_version(),
                "error": repr(error)[:200]}


# taken once, when the module is loaded: a running engine keeps the code it loaded even if the files change on disk
DETECTOR = detector()


def validation(cls):
    """What the frozen study says about a class, or EXPLORATORY when nothing was recorded for it. The status file is
    read at each alert, so its own hash is kept with the answer."""
    try:
        with open(os.path.join(HERE, "reference", "validation_status.json"), "rb") as f:
            raw = f.read()
        status, digest = json.loads(raw), hashlib.sha256(raw).hexdigest()
    except (OSError, ValueError):
        status, digest = {}, None
    v = (status.get("classes") or {}).get(cls)
    if not v:
        return {"status": "EXPLORATORY", "why": "no out-of-sample result is recorded for this class", "study": status.get("study"),
                "status_file_sha256": digest}
    return dict(v, study=status.get("study"), status_file_sha256=digest)


def utc(t):
    return time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime(t)) if t else None


def build(con, e, m, cls, a, w, ctx, score, detected_at):
    v, f, heavy = w["view"], w["flags"], w["heavy"]
    outs = json.loads(m["outcomes"] or "[]")
    tok = con.execute("select token_id from tokens where condition_id=? and oi=?", (e["condition_id"], e["oi"])).fetchone()[0]
    fills = [dict(r) for r in con.execute("select tx, log_index, block, ts, exchange, cash, price, counterparty from fills where wallet=? and token_id=? and side='BUY' "
                                          "and ts<=? order by ts limit 12", (e["wallet"], tok, a["t"]))]
    deps = [dict(r) for r in con.execute("select tx, ts, usdc, payer, via, block, sha256 from deposits where wallet=? and ts<? order by ts desc limit 3", (e["wallet"], e["t"]))]
    for d in deps:
        state = con.execute("select is_contract, nonce, status from historical_addresses where address=? and block=?",
                            (d["payer"], d["block"])).fetchone() if d["payer"] else None
        tag = con.execute("select tags, tags_status from addresses where address=?",
                          (d["payer"],)).fetchone() if d["payer"] else None
        d["payer_kind"] = (None if not d["payer"] else
                           "historical state unavailable" if state is None or state["status"] != "ok" else
                           "contract" if state["is_contract"] else
                           "tags unavailable" if tag is None or tag["tags_status"] != "ok" else
                           "tagged service" if tag["tags"] != "[]" else
                           "busy key" if state["nonce"] >= 1000 else "plain key")
    links = [dict(r) for r in con.execute(
        "select l.root, l.kind, l.tx, l.ts from links l join link_provenance p "
        "on (p.wallet=l.wallet and p.root=l.root and p.tx=l.tx) "
        "where l.wallet=? and l.ts<? and p.validator='receipt_guard_v1'",
        (e["wallet"], e["t"]))]
    med = v["prior_trade_median"]
    body = {
        "id": hashlib.sha256(f"{e['wallet']}|{e['condition_id']}|{e['oi']}|{cls}".encode()).hexdigest()[:16],
        "class": cls, "t_alert": a["t"], "t_alert_utc": utc(a["t"]), "detected_at_utc": utc(detected_at), "seconds_from_trade_to_alert": int(detected_at - a["t"]),
        "market": {"title": m["title"], "condition_id": e["condition_id"], "event_slug": m["event_slug"], "outcome": outs[e["oi"]] if len(outs) > e["oi"] else str(e["oi"]),
                   "family": m["family"], "protocol_version": m["version"], "price_at_alert": round(a["price"], 4), "scheduled_end_utc": utc(m["end_ts"])},
        "wallets": {"wallet": e["wallet"], "entry_usd": round(e["cash"], 2), "net_bought_usd": w["net_buy"],
                    "deposits": [{"tx": d["tx"], "utc": utc(d["ts"]), "usd": round(d["usdc"], 2), "apparent_payer": d["payer"], "payer_kind": d["payer_kind"], "via": d["via"]} for d in deps],
                    "plain_keys_behind_deposits": [{"key": l["root"], "how": {0: "paid the deposit", 2: "sent the money that was swapped into the deposit",
                                                                            1: "paid a pass-through key"}[l["kind"]], "deposit_tx": l["tx"]} for l in links],
                    "linked_wallet": a.get("link")},
        "anomaly": {"what": WHAT.get(cls, cls), "signals": sorted(k for k, on in f.items() if on),
                    "readings": {
                        "history_of_the_wallet": {"earlier_trades": v["prior_trades"], "other_markets": v["prior_other_markets"],
                                                  "hours_since_first_activity": None if v["age_h"] is None else round(v["age_h"], 1),
                                                  "fill_over_median_trade": None if not med else round(e["cash"] / med, 1)},
                        "funding": {"deposited_24h_usd": round(v["dep_24h"], 2), "deposited_7d_usd": round(v["dep_7d"], 2),
                                    "share_of_deposits_on_this_side": round(w["net_buy"] / v["dep_7d"], 2) if v["dep_7d"] else None},
                        "against_other_traders": {"other_large_fills_24h": ctx["mk_fills_24h"], "other_large_fills_6h": ctx["mk_fills_6h"],
                                                  "other_buying_of_this_side_24h_usd": round(ctx["side_buy_cash_24h"], 2), "other_large_buyers_of_this_side_6h": ctx["co_entrants_6h"]},
                        "timing": {"hours_to_scheduled_end": None if not m["end_ts"] else round((m["end_ts"] - a["t"]) / 3600.0, 1),
                                   "price_one_hour_before": ctx["price_1h"]},
                        "rarity": score},
                    "other_explanations": OTHER},
        "evidence": {"fills": [{"tx": x["tx"], "log_index": x["log_index"], "block": x["block"], "utc": utc(x["ts"]), "usd": round(x["cash"], 2), "price": round(x["price"], 4),
                                "exchange": x["exchange"], "taker": x["counterparty"] == x["exchange"]} for x in fills],
                     "deposit_receipts": [{"tx": d["tx"], "block": d["block"], "sha256": d["sha256"]} for d in deps],
                     "data_quality": {"source_of_fills": "Polygon OrderFilled logs", "history_rows_read": v["rows_before"],
                                      "history_complete": v["rows_before"] < 1000, "payer_tags": "Blockscout public tags, read when the alert was built",
                                      "payer_transaction_counts": "historical nonce at deposit block when archive state was served; otherwise unresolved",
                                      "funding_link_origin": "only links with receipt_guard_v1 provenance; legacy cached links remain unverified and are not displayed"}},
        "validation": validation(cls),
        "detector": dict(DETECTOR),
        "reading": "a pattern seen in public data; it says nothing about who the trader is or about private information",
    }
    return body


def render(b):
    """Plain text of one alert for the terminal."""
    m, w, an, ev, va = b["market"], b["wallets"], b["anomaly"], b["evidence"], b["validation"]
    r = an["readings"]; out = []
    out.append(f"\n=== {b['class']}  {b['t_alert_utc']}  (seen {b['seconds_from_trade_to_alert']} s after the trade)  id {b['id']}")
    out.append(f"MARKET     {m['title']}  [{m['outcome']}]  price {m['price_at_alert']}  family {m['family']}  ends {m['scheduled_end_utc']}")
    out.append(f"           condition {m['condition_id']}  event {m['event_slug']}")
    out.append(f"WALLETS    {w['wallet']}  entry {w['entry_usd']:,.0f} USD, net bought {w['net_bought_usd']:,.0f} USD")
    for d in w["deposits"]:
        out.append(f"           deposit {d['usd']:,.0f} USD at {d['utc']} paid by {d['apparent_payer']} ({d['payer_kind']}, {d['via']})  tx {d['tx']}")
    for l in w["plain_keys_behind_deposits"]:
        out.append(f"           plain key {l['key']} {l['how']}")
    if w["linked_wallet"]:
        out.append(f"           linked wallet {w['linked_wallet']['other_wallet']} through {w['linked_wallet']['root']}")
    out.append(f"ANOMALY    {an['what']}")
    h, fu, ot = r["history_of_the_wallet"], r["funding"], r["against_other_traders"]
    span = (f"first activity {h['hours_since_first_activity']} h before" if ev["data_quality"]["history_complete"]
            else f"history longer than the rows read, which cover the last {h['hours_since_first_activity']} h")
    out.append(f"           wallet: {h['earlier_trades']} earlier trades on {h['other_markets']} other markets, {span}, fill {h['fill_over_median_trade']} times its median trade")
    out.append(f"           funding: {fu['deposited_24h_usd']:,.0f} USD in 24 h, share on this side {fu['share_of_deposits_on_this_side']}")
    out.append(f"           others: {ot.get('other_large_fills_24h')} large fills in 24 h, "    # an alert written by an earlier version keeps its own field names
               f"{ot.get('other_large_buyers_of_this_side_6h', ot.get('other_first_entries_6h'))} other large buyers of this side in 6 h")
    if r["rarity"]:
        out.append(f"           rarity {r['rarity']['score']} (top 1 % from {r['rarity']['threshold_top1pct']:.2f}): " +
                   ", ".join(f"{k} {v}" for k, v in sorted(r["rarity"]["parts"].items(), key=lambda x: -x[1])[:4]))
    out.append("           other explanations: " + "; ".join(an["other_explanations"][:4]))
    out.append("EVIDENCE   " + "; ".join(f"{x['tx']}#{x['log_index']} block {x['block']} {x['usd']:,.0f} USD at {x['price']}" for x in ev["fills"][:3]))
    out.append(f"           history rows read {ev['data_quality']['history_rows_read']} (complete: {ev['data_quality']['history_complete']})")
    out.append(f"VALIDATION {va.get('status')}" + (f": {va.get('summary')}" if va.get("summary") else f": {va.get('why', '')}"))
    d = b.get("detector")  # alerts built by an engine older than this field carry no detector version
    if d:
        code = f"code {d['code_sha256'][:16]} over {d['files_hashed']} files" if d.get("code_sha256") else f"code hash unavailable: {d.get('error')}"
        out.append(f"DETECTOR   {d['engine']} {code}, Python {d.get('python')}")
    return "\n".join(out)
