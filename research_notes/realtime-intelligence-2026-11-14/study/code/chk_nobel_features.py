"""Pre-freeze check of the collection and feature code on the documented Nobel 2025 accounts (discovery set).
Reads entries, wallet features and funding groups; no outcome, no label. The accounts come from the repository
(investigations/followup-20261113/sources/data/nobel_accounts.csv), passed as the first argument.

    python3 -I code/chk_nobel_features.py <nobel_accounts.csv> > controles/nobel_features.txt"""
import csv, json, os, sqlite3, sys

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ro = lambda p: sqlite3.connect("file:" + os.path.join(ETUDE, "derived", p) + "?mode=ro", uri=True)


def main(path):
    acc = {r["proxy"].lower(): r for r in csv.DictReader(open(path))}
    events = {json.loads(l)["event_id"] for l in open(os.path.join(ETUDE, "derived", "universe_markets.jsonl")) if "nobel-peace-prize" in l}
    ent, wf, gr = ro("entries.sqlite"), ro("wallet_features.sqlite"), ro("groups.sqlite")
    q = f"select id, address, t, condition_id, oi, price, cash, tier1, eligible, w_fills_before from entries where event_id in ({','.join('?' * len(events))}) order by t"
    cols_wf = [r[1] for r in wf.execute("pragma table_info(wf)")]
    print("accounts", len(acc), "events", sorted(events))
    seen = set()
    for eid, a, t, cond, oi, price, cash, tier1, elig, prior in ent.execute(q, sorted(events)):
        if a not in acc:
            continue
        seen.add(a)
        w = wf.execute("select * from wf where id=?", (eid,)).fetchone(); w = dict(zip(cols_wf, w)) if w else {}
        g = gr.execute("select n_roots, c4, c4_root, c5, complete from groups where id=?", (eid,)).fetchone()
        roots = [r[0] for r in gr.execute("select distinct root from roots where id=?", (eid,))]
        print(json.dumps({"handle": acc[a]["handle"], "t": t, "oi": oi, "price": round(price, 4), "cash": round(cash), "eligible": elig, "tier1": tier1,
                          "prior_fills": prior, **{k: w.get(k) for k in ("view_ok", "thin", "fresh", "dormant", "chain", "fresh_by_chain_only", "dep_24h",
                                                                         "r1_age_ts", "heavy_t", "heavy_price")},
                          "groups": g, "roots": roots}))
    print("accounts with no entry on these events:", sorted(acc[a]["handle"] for a in set(acc) - seen))


if __name__ == "__main__":
    main(sys.argv[1])
