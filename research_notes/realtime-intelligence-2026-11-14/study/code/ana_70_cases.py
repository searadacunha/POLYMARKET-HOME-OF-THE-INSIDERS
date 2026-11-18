"""ana_70: what the classes say on the events of the cases already documented in the repository. A listing, not a test:
no rate, no p-value. These events are in the discovery set because they were documented, and they were documented
because somebody won: nothing here measures how well a class predicts.

For each documented event: entries, entries with a history read, and for each class the earliest alert (time, wallet,
price paid, cash, hours before the real close of that market). Output: derived/documented_cases.json."""
import json, os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tests_lib as T

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = lambda *p: os.path.join(ETUDE, "derived", *p)


def main():
    sets = json.load(open(D("sets.json")))
    cases = {eid: v for eid, v in sets.items() if v["documented_case"]}
    rows = [json.loads(l) for l in open(D("analytic_table.jsonl"))]
    T.fit_m3(rows)
    utc = lambda t: time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(t))
    out = {}
    for eid, v in sorted(cases.items(), key=lambda x: x[1]["slug"]):
        ev = [r for r in rows if r["event_id"] == eid]
        rec = {"slug": v["slug"], "family": v["group"], "markets": v["markets"], "eligible_entries": len(ev), "entries_with_history": sum(r["evaluated"] for r in ev),
               "wallets": len({r["address"] for r in ev}), "classes": {}}
        for cls in T.TESTED + T.BASELINES:
            alerts = sorted((a for a in (T.alert_of(r, cls)[0] for r in ev if cls not in r.get("unknown", ())) if a), key=lambda a: (a["t"], a["key"]))
            if alerts:
                a = alerts[0]
                rec["classes"][cls] = {"alerts": len(alerts), "wallets": len({x["wallet"] for x in alerts}),
                                       "first": {"utc": utc(a["t"]), "wallet": a["wallet"], "price": round(a["price"], 4), "entry_usd": round(a["cash"], 2),
                                                 "hours_before_real_close": round((a["closed_ts"] - a["t"]) / 3600.0, 1), "side_won": bool(a["win"])}}
        out[eid] = rec
    json.dump(out, open(D("documented_cases.json"), "w"), indent=1)
    print(json.dumps({v["slug"]: {c: x["alerts"] for c, x in v["classes"].items()} for v in out.values()}, indent=1))


if __name__ == "__main__":
    main()
