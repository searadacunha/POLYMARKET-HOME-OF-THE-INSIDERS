#!/usr/bin/env python3
"""EXPLORATORY ONLY (Iran cohort, never VALID or TEST): payoff vectors of cohort wallets across the nested deadlines
of the event 'US strikes Iran by ...', from each wallet's own fills and activity feed.

Question it answers descriptively: for the cohort wallets that bought NO before YES on the 28 February market, was
the change a reversal of exposure (A) or an interval package across deadlines (B), once every deadline the wallet
traded is read together? No rate, no test, no verdict.

Data: Gamma event (rules text of every member), /v2/trades?user= (taker_only=false) and /v2/activity?user= for each
wallet, cached under --cache with fetch times. Transaction conservation cannot be checked (counterparty rows are not
fetched), which is stated in the output. Reads no outcome label.

usage: example_ladder_iran.py --cohort data/iran_cohort_wallets.json --feb28 ../../../feb28_v2.sqlite
       --cache data/iran_example --out out/iran_exploratory/ladder_example.json
"""
import argparse, collections, datetime as dt, json, os, sqlite3, sys, time, urllib.parse, urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ledger as L  # noqa: E402
from example_portfolio import PROFILE  # noqa: E402

FEB28 = "0x3488f31e6449f9803f99a8b5dd232c7ad883637f1c86e6953305a2ef19c77f20"
EVENT = "us-strikes-iran-by"


def get(url):
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "research-client"}),
                                        timeout=60) as r:
                return json.loads(r.read())
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 * (attempt + 1))


def paged(base):
    rows, cursor = [], None
    for _ in range(200):
        j = get(base + (f"&cursor={cursor}" if cursor else ""))
        if "data" not in j:
            raise RuntimeError(f"API error: {j}")
        rows += [{k: v for k, v in x.items() if k not in PROFILE} for x in j["data"]]
        pg = j.get("pagination") or {}
        cursor = pg.get("next_cursor")
        if not pg.get("has_more") or not cursor:
            return rows
    raise RuntimeError("pagination did not end")


def cached(path, fn):
    if os.path.exists(path):
        return json.load(open(path))
    d = {"fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "data": fn()}
    json.dump(d, open(path, "w"))
    return d


def iso(t):
    return dt.datetime.fromtimestamp(t, dt.timezone.utc).strftime("%Y-%m-%d %H:%M")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cohort", required=True)
    ap.add_argument("--feb28", required=True)
    ap.add_argument("--cache", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.cache, exist_ok=True)
    cohort = json.load(open(a.cohort))["wallets"]

    # cohort wallets whose first NO buy precedes their first YES buy on 28 February (complete v2 tape)
    con = sqlite3.connect(f"file:{urllib.parse.quote(os.path.abspath(a.feb28))}?mode=ro&immutable=1", uri=True)
    first = collections.defaultdict(dict)
    for w, oi, ts in con.execute("select wallet, outcome_index, min(ts) from trades where condition_id=? and side='BUY' "
                                 "group by wallet, outcome_index", (FEB28,)):
        first[w.lower()][oi] = ts
    no_then_yes = [w for w in cohort if 1 in first[w] and 0 in first[w] and first[w][1] < first[w][0]]
    tape_feb28 = collections.defaultdict(collections.Counter)   # wallet -> (tx, side, oi) -> shares, complete tape
    for w, tx, side, oi, size in con.execute("select wallet, tx, side, outcome_index, size from trades "
                                             "where condition_id=?", (FEB28,)):
        if w.lower() in no_then_yes:
            tape_feb28[w.lower()][(tx.lower(), side, int(oi))] += size

    ev = cached(os.path.join(a.cache, "gamma_event.json"), lambda: get(f"https://gamma-api.polymarket.com/events?slug={EVENT}"))
    metas = {m["conditionId"].lower(): m for m in ev["data"][0]["markets"]}

    results = []
    for w in no_then_yes:
        tr = cached(os.path.join(a.cache, f"trades_{w}.json"),
                    lambda: paged(f"https://data-api.polymarket.com/v2/trades?user={w}&limit=1000&taker_only=false"))
        ac = cached(os.path.join(a.cache, f"activity_{w}.json"),
                    lambda: paged(f"https://data-api.polymarket.com/v2/activity?user={w}&limit=500"))
        rows = [x for x in tr["data"] if x["condition_id"].lower() in metas]
        acts = [x for x in ac["data"] if x["condition_id"].lower() in metas]
        cids = sorted({x["condition_id"].lower() for x in rows})
        mine = collections.Counter()
        for x in rows:
            if x["condition_id"].lower() == FEB28:
                mine[(x["transaction_hash"].lower(), x["side"], int(x["outcome_index"]))] += float(x["size"])
        ref = tape_feb28[w]
        feb28_mismatch = sum(1 for k in set(mine) | set(ref) if abs(mine[k] - ref[k]) > 1e-3)
        res = {"wallet": w, "ladder_markets_traded": len(cids), "trade_rows": len(rows),
               "feb28_user_fetch_vs_complete_tape": {"keys_user_fetch": len(mine), "keys_tape": len(ref),
                                                      "mismatches": feb28_mismatch},
               "activity_types": collections.Counter(x["type"] for x in acts),
               "fetched_at": [tr["fetched_at"], ac["fetched_at"]]}
        if len(cids) < 2:
            res["reading"] = "single deadline traded: no cross-deadline package possible"
            results.append(res)
            continue
        fam = L.prove_ladder([metas[c] for c in cids])
        if fam["type"] != "ladder":
            res["reading"] = f"UNRESOLVED_FAMILY: {fam['proof']}"
            results.append(res)
            continue
        last = max(int(x["timestamp"]) for x in rows)
        evs, unmapped, redeems_before_last = [], collections.Counter(), 0
        for i, x in enumerate(rows):
            evs.append(L.make_event(int(x["timestamp"]), w, x["condition_id"], x["side"], oi=int(x["outcome_index"]),
                                    qty=x["size"], price=x["price"], tx=x.get("transaction_hash"), seq=i,
                                    src=f"trades_{w[:10]}#{i}"))
        for i, x in enumerate(acts):
            t = int(x["timestamp"])
            if x["type"] in ("SPLIT", "MERGE") and t <= last:
                evs.append(L.make_event(t, w, x["condition_id"], x["type"], qty=x["size"], tx=x.get("transaction_hash"),
                                        seq=10 ** 9 + i, src=f"activity_{w[:10]}#{i}"))
            elif x["type"] == "REDEEM":
                if t <= last:   # an earlier deadline resolved while the wallet still traded: burns that position
                    evs.append(L.make_event(t, w, x["condition_id"], "REDEEM", oi=None, qty=x.get("size") or 0.0,
                                            usdc=x.get("usdc_size"), tx=x.get("transaction_hash"), seq=10 ** 9 + i,
                                            src=f"activity_{w[:10]}#{i}"))
                    redeems_before_last += 1
            elif x["type"] in ("TRADE", "SPLIT", "MERGE"):
                continue
            else:
                unmapped[x["type"]] += 1
        cov = {**L.TAPE_COVERAGE, "split_merge": True, "redeem": True}
        info = {c: {"history_complete": True, "neg_risk": False, "fees_enabled": metas[c].get("feesEnabled"),
                    "coverage": cov} for c in cids}
        lg = L.Ledger(evs, info, check_tx=False)   # counterparties not fetched: conservation not checkable
        windows = sorted({L.window_index(e["ts"]) for e in lg.events})
        classes = collections.Counter()
        timeline = []
        for k in windows:
            t0, t1 = k * 3600, (k + 1) * 3600
            r = L.classify(lg, w, fam, t0, t1)
            classes[r["class"]] += 1
            if r["class"] not in ("NONE",):
                v1 = L.payoff_vector(lg, w, fam, t1)
                timeline.append({"window_utc": [iso(t0), iso(t1)], "class": r["class"],
                                 "shape_t1": [round(x, 2) for x in v1["shape"]],
                                 "txs": sorted({e["tx"] for c in fam["members"] for e in lg.window_events(w, c, t0, t1)
                                                if e["tx"]})[:5]})
        vend = L.payoff_vector(lg, w, fam, last)
        res.update({"worlds": fam["worlds"], "deadlines": fam["deadlines"], "classes": classes,
                    "unmapped_activity": unmapped, "redeems_applied_before_last_fill": redeems_before_last,
                    "final_shape": [round(x, 2) for x in vend["shape"]],
                    "final_status": vend["status"], "final_reasons": vend["reasons"], "timeline": timeline,
                    "limits": "wallet-only fetch: tx conservation not checked (reason TX_UNCHECKED); transfers "
                              "not covered; a REDEEM before the last fill burns the resolved deadline's position"})
        results.append(res)
    out = {"label": "EXPLORATORY_IRAN: descriptive, never part of a rate, a test or VALID/TEST",
           "cohort_n": len(cohort), "no_then_yes_on_feb28_full_tape": len(no_then_yes),
           "event_markets": len(metas), "wallets": results,
           "class_totals": sum((collections.Counter(r.get("classes", {})) for r in results), collections.Counter())}
    json.dump(out, open(a.out, "w"), indent=1, default=dict)
    print(json.dumps({k: v for k, v in out.items() if k != "wallets"}, indent=1, default=dict))
    for r in results:
        print(r["wallet"][:10], r["ladder_markets_traded"], dict(r.get("classes", {})) or r.get("reading"))


if __name__ == "__main__":
    main()
