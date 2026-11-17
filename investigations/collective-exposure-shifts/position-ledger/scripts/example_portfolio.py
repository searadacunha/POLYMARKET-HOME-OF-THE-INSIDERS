#!/usr/bin/env python3
"""Verifiable example: one wallet in one market, rebuilt as of several instants, from the tape alone and from the
tape plus the wallet's public activity feed (which shows SPLIT / MERGE / REDEEM / CONVERSION, invisible in fills).

Every row carries its Polygon transaction hash and block timestamp, so anyone can check it on a block explorer.
Reads no outcome label; stops at the market's last fill (before any redemption).

usage: example_portfolio.py --tapes tapes.sqlite --cid 0x.. --wallet 0x.. --meta gamma_meta.jsonl --out DIR
       [--activity cached.json]   (re-use a saved activity file instead of fetching)
"""
import argparse, collections, datetime as dt, hashlib, json, os, sqlite3, sys, time, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger as L  # noqa: E402

ACT = "https://data-api.polymarket.com/v2/activity"
PROFILE = {"name", "pseudonym", "bio", "profile_image", "profile_image_optimized", "icon", "title", "slug",
           "event_slug", "profileImage", "profileImageOptimized", "eventSlug"}


def iso(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def fetch_activity(wallet, cid):
    rows, cursor = [], None
    for _ in range(100):
        url = f"{ACT}?user={wallet}&condition={cid}&limit=500" + (f"&cursor={cursor}" if cursor else "")
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-client"}),
                                    timeout=60) as r:
            j = json.loads(r.read())
        if "data" not in j:
            raise RuntimeError(f"activity error: {j}")
        rows += [{k: v for k, v in x.items() if k not in PROFILE} for x in j["data"]]
        pg = j.get("pagination") or {}
        cursor = pg.get("next_cursor")
        if not pg.get("has_more") or not cursor:
            return rows
    raise RuntimeError("activity pagination did not end after 100 pages")


def activity_events(rows, cid):
    """Protocol events from the activity feed. Unmapped types are returned separately, never dropped silently."""
    out, unmapped = [], []
    for i, x in enumerate(rows):
        t, ts, tx = x["type"], int(x["timestamp"]), x.get("transaction_hash")
        src = f"activity#{i}"
        if t == "SPLIT":
            out.append(L.make_event(ts, x["proxy_wallet"], cid, "SPLIT", qty=x["size"], tx=tx, seq=10 ** 9 + i, src=src))
        elif t == "MERGE":
            out.append(L.make_event(ts, x["proxy_wallet"], cid, "MERGE", qty=x["size"], tx=tx, seq=10 ** 9 + i, src=src))
        elif t == "TRADE":
            continue      # fills come from the tape; compared below, not double counted
        elif t == "REDEEM":  # no outcome index in the feed: burns every token of the condition held
            out.append(L.make_event(ts, x["proxy_wallet"], cid, "REDEEM", oi=None, qty=x.get("size") or 0.0,
                                    usdc=x.get("usdc_size"), tx=tx, seq=10 ** 9 + i, src=src))
        else:
            unmapped.append(x)   # REDEEM without outcome index, CONVERSION, REWARD...: listed in the report
    return out, unmapped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tapes", required=True)
    ap.add_argument("--cid", required=True)
    ap.add_argument("--wallet", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--activity")
    a = ap.parse_args()
    cid, wallet = a.cid.lower(), a.wallet.lower()
    os.makedirs(a.out, exist_ok=True)
    g = next(json.loads(l) for l in open(a.meta) if json.loads(l)["condition_id"] == cid)

    con = sqlite3.connect(f"file:{urllib.parse.quote(os.path.abspath(a.tapes))}?mode=ro&immutable=1", uri=True)
    status = con.execute("select status from status where condition_id=?", (cid,)).fetchone()[0]
    rows = con.execute("select rowid, condition_id, ts, wallet, side, outcome, outcome_index, size, price, tx "
                       "from trades where condition_id=? order by ts, rowid", (cid,)).fetchall()
    fills = L.events_from_tape_rows(rows, os.path.basename(a.tapes))
    last_fill = max(e["ts"] for e in fills)

    if a.activity:
        act = json.load(open(a.activity))
    else:
        act = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "source": ACT,
               "query": {"user": wallet, "condition": cid}, "rows": fetch_activity(wallet, cid)}
        p = os.path.join(a.out, f"activity_{wallet[:10]}_{cid[:10]}.json")
        json.dump(act, open(p, "w"), indent=1)
        act["sha256"] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    proto, unmapped = activity_events(act["rows"], cid)
    proto_pre = [e for e in proto if e["ts"] <= last_fill]

    base = {"history_complete": status == "ok", "neg_risk": g.get("negRisk"), "fees_enabled": g.get("feesEnabled")}
    tape_lg = L.Ledger(fills, {cid: {**base, "coverage": L.TAPE_COVERAGE}})
    # this wallet only: its activity feed shows splits and merges (conversions too: none may be unmapped below);
    # transfers stay unseen; every other wallet of the market stays at tape coverage
    cov = {**L.TAPE_COVERAGE, "split_merge": True, "convert": not unmapped, "redeem": True}
    full_lg = L.Ledger(fills + proto_pre, {cid: {**base, "coverage": L.TAPE_COVERAGE, "wallet_coverage": {wallet: cov}}})

    # cross-check: wallet fills in the tape vs TRADE rows in the activity feed, per tx and side/outcome
    def agg(items):
        c = collections.Counter()
        for tx, side, oi, size in items:
            c[(tx, side, oi)] += round(size, 4)
        return c
    tape_w = agg((e["tx"], e["kind"], e["oi"], e["qty"]) for e in tape_lg.events if e["wallet"] == wallet)
    act_w = agg((x["transaction_hash"].lower(), x["side"], x["outcome_index"], x["size"])
                for x in act["rows"] if x["type"] == "TRADE" and int(x["timestamp"]) <= last_fill)
    keys = set(tape_w) | set(act_w)
    mism = sorted(k for k in keys if abs(tape_w.get(k, 0) - act_w.get(k, 0)) > 1e-3)

    wev = full_lg.by_book.get((wallet, cid), [])
    instants = sorted({e["ts"] for e in wev})
    lines = []
    for t in instants:
        st, sf = tape_lg.snapshot(wallet, cid, t), full_lg.snapshot(wallet, cid, t)
        lines.append({"as_of_utc": iso(t), "as_of": t,
                      "events": [{"kind": e["kind"], "oi": e["oi"], "qty": round(e["qty"], 6), "price": e["price"],
                                  "tx": e["tx"], "src": e["src"]} for e in wev if e["ts"] == t],
                      "tape_only": {"x": round(st["observable"]["x_yes_equiv"], 6), "x_status": st["x_status"],
                                    "flow": [round(st["observable"]["flow_yes"], 6), round(st["observable"]["flow_no"], 6)],
                                    "inv_lo": st["inventory"]["lo"] and [round(v, 6) for v in st["inventory"]["lo"]],
                                    "inv_hi": st["inventory"]["hi"], "reasons": st["reasons"]},
                      "tape_plus_activity": {"x": round(sf["observable"]["x_yes_equiv"], 6), "x_status": sf["x_status"],
                                             "inventory": [round(sf["observable"]["flow_yes"], 6), round(sf["observable"]["flow_no"], 6)],
                                             "inv_status": sf["inventory"]["status"], "reasons": sf["reasons"]}})
        assert abs(st["observable"]["x_yes_equiv"] - sf["observable"]["x_yes_equiv"]) < 1e-6, "X must ignore split/merge"
    fam = L.family_binary(cid)
    windows = sorted({L.window_index(t) for t in instants})
    cls = [{"t0_utc": iso(k * 3600), "t1_utc": iso((k + 1) * 3600),
            "tape_only": L.classify(tape_lg, wallet, fam, k * 3600, (k + 1) * 3600)["class"],
            "tape_plus_activity": L.classify(full_lg, wallet, fam, k * 3600, (k + 1) * 3600)["class"]} for k in windows]
    res = {"wallet": wallet, "condition_id": cid, "question": g.get("question"), "neg_risk": g.get("negRisk"),
           "fees_enabled": g.get("feesEnabled"), "gamma_version": g.get("version"), "tape_status": status,
           "tape": os.path.basename(a.tapes), "last_fill_utc": iso(last_fill),
           "activity": {"fetched_at": act.get("fetched_at"), "sha256": act.get("sha256"),
                        "types": collections.Counter(x["type"] for x in act["rows"]),
                        "protocol_events_applied": len(proto_pre), "after_last_fill": len(proto) - len(proto_pre),
                        "unmapped": [{k: x.get(k) for k in ("type", "timestamp", "size", "usdc_size", "transaction_hash")}
                                     for x in unmapped]},
           "trade_crosscheck": {"tape_keys": len(tape_w), "activity_keys": len(act_w), "mismatches": mism[:20],
                                "n_mismatches": len(mism)},
           "tx_checks_market": collections.Counter(tape_lg.tx_verdicts.values()),
           "timeline": lines, "windows": cls}
    json.dump(res, open(os.path.join(a.out, "example_portfolio.json"), "w"), indent=1, default=list)
    print(json.dumps({k: v for k, v in res.items() if k not in ("timeline",)}, indent=1, default=list)[:4000])


if __name__ == "__main__":
    main()
