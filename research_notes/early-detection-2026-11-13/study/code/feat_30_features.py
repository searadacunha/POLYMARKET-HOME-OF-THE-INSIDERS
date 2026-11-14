"""feat_30: stage 2. Point-in-time tape features of each stage-1 ignition. No outcome is read. Exclusions are counted."""
import collections, json, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tapefeat

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    con = sqlite3.connect(os.path.join(ETUDE, "data", "tapes.sqlite"))
    status = dict(con.execute("select condition_id, status from status"))
    c = collections.Counter(); out = open(os.path.join(ETUDE, "derived", "ignitions_features.jsonl"), "w")
    for line in open(os.path.join(ETUDE, "derived", "ignitions_stage1.jsonl")):
        g = json.loads(line); c["stage1"] += 1
        st = status.get(g["condition_id"])
        if st is None: raise RuntimeError(f"no tape status for {g['condition_id']}: run col_30 to the end first")
        if st != "ok": c["tape_" + st] += 1; continue
        rows = con.execute("select ts, wallet, side, outcome, size, price from rows where condition_id=? order by ts", (g["condition_id"],)).fetchall()
        f, why = tapefeat.alert_features(rows, g["side"], g["base"], g["t0"], g["t1"])
        if f is None: c["excluded_" + why] += 1; continue
        c["kept"] += 1
        f.update({k: g[k] for k in ("condition_id", "event_id", "event_slug", "side", "t0", "t1", "base", "closed_ts")})
        out.write(json.dumps(f) + "\n")
    out.close()
    json.dump(dict(c), open(os.path.join(ETUDE, "derived", "stage2_counts.json"), "w"), indent=1)
    print(json.dumps(dict(c), indent=1))


if __name__ == "__main__":
    main()
