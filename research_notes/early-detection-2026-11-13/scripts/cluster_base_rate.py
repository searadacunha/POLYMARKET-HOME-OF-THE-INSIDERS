"""EXPLORATORY, run after the results of the frozen study were seen: how often does an alert of the tested class come
with a funded group?

    python3 research_notes/early-detection-2026-11-13/scripts/cluster_base_rate.py WORK_DB OUT_JSON

For each alert of the class (validation and documented cases) the market is replayed by the monitor from one hour
before the first buy to twelve hours after the alert, on the price window the study read. A funded group is two or
more accounts that bought the alerted side for 1,000 USD or more, had traded two markets or fewer before, and were paid
by the same plain key, directly or through a brand-new key. Bridges, contracts and high-volume keys never count. Each
row also counts the other buyers of 1,000 USD or more and how many of them had almost no history: without two such
accounts no group can exist. Network needed.

This is a count on 48 markets chosen by the alert itself. It measures how common the second stage is among alerts; it
is not a test, and nothing here was fixed before the outcomes were known.
"""
import gzip, json, os, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "..", "monitoring"))
from phi_monitor import collect, detect, net, store, tapefeat   # noqa: E402

STUDY = os.path.join(HERE, "..", "study", "derived")
AFTER = 12 * 3600


def main(db, out):
    con = store.connect(db)
    tokens = {}
    with gzip.open(os.path.join(STUDY, "universe_markets.jsonl.gz"), "rt") as f:
        for line in f:
            m = json.loads(line); tokens[m["condition_id"]] = m["yes_token"]
    alerts = [r for r in map(json.loads, open(os.path.join(STUDY, "analytic_table.jsonl"))) if r["lonely_thin"]]
    res = json.load(open(out)) if os.path.exists(out) else []
    done = {(r["condition_id"], r["side"]) for r in res}
    for a in sorted(alerts, key=lambda r: r["t_first"]):
        if (a["condition_id"], a["side"]) in done:
            continue
        row = {"condition_id": a["condition_id"], "side": a["side"], "event_slug": a["event_slug"], "eval_set": a["eval_set"], "win": a["win"],
               "t_alert": a["t_alert"], "initiator": a["initiator"]}
        try:
            m = collect.resolve(con, tokens[a["condition_id"]])
            end = a["t_alert"] + AFTER
            for lo in range(a["closed_ts"] - 14 * 86400, end, 13 * 86400):   # the price window of the study; the endpoint serves about 14 days per call
                collect.fetch_prices(con, m["yes_token"], lo, min(end, lo + 13 * 86400))
            tape = collect.fetch_tape(con, a["condition_id"], a["t0"] - 700)
            if not tape["complete"]:
                row["status"] = "tape_too_deep"
            else:
                r = detect.backtest(con, a["condition_id"], a["t_first"] - 3600, end)[a["side"]]
                same = r.get("level") == "LONELY_THIN" and r["features"]["initiator"] == a["initiator"] and r["t_alert"] == a["t_alert"]
                groups = ([{"shared_payer": s["new"][0]["shared_payer"], "wallets": sorted({a["initiator"]} | {x["wallet"] for st in r["cluster_timeline"] for x in st["new"]}),
                            "includes_initiator": True, "first_seen": r["cluster_timeline"][0]["as_of"]} for s in r["cluster_timeline"][:1]] if r.get("cluster_timeline") else [])
                groups += [{"shared_payer": g["shared_payer"], "wallets": g["wallets"], "includes_initiator": False, "first_seen": g["as_of"]} for g in (r.get("other_groups") or [])]
                others = con.execute("select wallet, min(ts) from fills where token_id=? and side='BUY' and ts between ? and ? and wallet != ? "
                                     "group by wallet having sum(cash) >= ?",   # the buyers detect.followup looks at
                                     (m["yes_token"] if a["side"] == "YES" else m["no_token"], a["t_first"], end, a["initiator"], detect.FOLLOW_MIN_CASH)).fetchall()
                read = [json.loads(b[0]) for b in (con.execute("select body from baselines where wallet=? and as_of=?", tuple(o)).fetchone() for o in others) if b]
                row.update(status="replayed", alert_reproduced=same, other_buyers=len(others), other_buyers_read=len(read),
                           thin_other_buyers=sum(b["prior_markets"] <= tapefeat.THIN_MARKETS for b in read), funded_groups=groups)
        except net.SourceError as e:
            row.update(status="source_error", error=str(e)[:200])
        res.append(row)
        json.dump(res, open(out, "w"), indent=1)
        print(time.strftime("%H:%M:%S"), a["event_slug"][:40], a["side"], row["status"], "groups:", len(row.get("funded_groups") or []), "reproduced:", row.get("alert_reproduced"), flush=True)
    ok = [r for r in res if r["status"] == "replayed"]
    with_group = [r for r in ok if r["funded_groups"]]
    print(f"replayed {len(ok)} of {len(res)} | with a funded group: {len(with_group)} | of which the side won: {sum(r['win'] for r in with_group)} | requests: {dict(net.COUNTS)}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
