"""ana_00: write the analytic table ONCE (one row per ignition kept by stage 2), joining features, initiator baseline,
classes, evaluation set and, last, the outcome label. No rate, no test and no summary of the outcome is computed here."""
import collections, json, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tapefeat

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ETUDE, "derived", "analytic_table.jsonl")


def main():
    if os.path.exists(OUT): raise SystemExit("analytic_table.jsonl already exists: it is written once")
    d = json.load(open(os.path.join(ETUDE, "derived", "discovery_events.json")))
    disc, disc_conds = set(d["event_slugs"]), set(d["condition_ids"])
    tags = {}
    for line in open(os.path.join(ETUDE, "derived", "universe_markets.jsonl")):
        m = json.loads(line); tags[m["condition_id"]] = (m["tags"], m["volume"], m["neg_risk"])
        if m["condition_id"].lower() in disc_conds: disc.add(m["event_slug"])   # the whole event of a documented market
    win = {}
    for line in open(os.path.join(ETUDE, "derived", "labels.jsonl")):
        j = json.loads(line); win[j["condition_id"]] = j["winner"]
    con = sqlite3.connect(os.path.join(ETUDE, "data", "baselines.sqlite"))
    c = collections.Counter(); rows = []
    for line in open(os.path.join(ETUDE, "derived", "ignitions_features.jsonl")):
        f = json.loads(line); c["features"] += 1
        b = con.execute("select status, body from baseline where wallet=? and t_first=?", (f["initiator"], f["t_first"])).fetchone()
        if b is None: raise RuntimeError("missing baseline row: run col_40 to the end first")
        if b[0] != "ok": c["excluded_baseline_error"] += 1; continue
        bl = json.loads(b[1])
        cl = tapefeat.classify(f, bl["prior_markets"])
        age = lambda t: None if t is None else round((f["t_first"] - t) / 3600, 2)
        tg, vol, neg = tags[f["condition_id"]]
        row = dict(f); row.update(bl); row.update(cl)
        row.update(first_activity_age_h=age(bl["first_activity"]), profile_age_h=age(bl["profile_created"]), tags=tg, market_volume=vol,
                   neg_risk=neg, eval_set="DISCOVERY" if f["event_slug"] in disc else "VALIDATION",
                   win=int(win[f["condition_id"]] == f["side"]))
        rows.append(row); c["rows"] += 1; c["set_" + row["eval_set"]] += 1
    rows.sort(key=lambda r: (r["t_first"], r["condition_id"], r["side"]))
    with open(OUT, "w") as o:
        for r in rows: o.write(json.dumps(r, sort_keys=True) + "\n")
    json.dump(dict(c), open(os.path.join(ETUDE, "derived", "table_counts.json"), "w"), indent=1)
    print(json.dumps(dict(c), indent=1))


if __name__ == "__main__":
    main()
