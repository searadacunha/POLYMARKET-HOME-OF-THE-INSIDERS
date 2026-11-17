"""feat_20: stage 1. First ignition of each side of each market, from the stored 10-minute price series. No outcome is read."""
import collections, json, os, sqlite3, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ignition
from col_20_prices import unpack

ETUDE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    con = sqlite3.connect(os.path.join(ETUDE, "data", "prices.sqlite"))
    c = collections.Counter(); out = open(os.path.join(ETUDE, "derived", "ignitions_stage1.jsonl"), "w")
    for line in open(os.path.join(ETUDE, "derived", "universe_markets.jsonl")):
        m = json.loads(line); c["markets"] += 1
        row = con.execute("select status, n, blob from series where condition_id=?", (m["condition_id"],)).fetchone()
        if row is None: raise RuntimeError(f"no price row for {m['condition_id']}: run col_20 to the end first")
        if row[0] != 200: c["series_error"] += 1; continue
        if not row[1]: c["series_empty"] += 1; continue
        series = sorted(unpack(row[2])); c["series_ok"] += 1
        out_of_range = sum(1 for _, p in series if not (0.0 <= p <= 1.0))
        if out_of_range:   # source artefact (a midpoint above 1 at the end of a market, one negative point): clipped and counted
            c["series_with_clipped_points"] += 1; c["clipped_points"] += out_of_range
            series = [(t, min(1.0, max(0.0, p))) for t, p in series]
        found = False
        for side in ("YES", "NO"):
            ig = ignition.first_ignition(series, side)
            if ig is None: continue
            found = True; c["ignitions_" + side] += 1
            ig.update(condition_id=m["condition_id"], event_id=m["event_id"], event_slug=m["event_slug"], closed_ts=m["closed_ts"])
            out.write(json.dumps(ig) + "\n")
        c["markets_with_ignition"] += found
    out.close()
    json.dump(dict(c), open(os.path.join(ETUDE, "derived", "stage1_counts.json"), "w"), indent=1)
    print(json.dumps(dict(c), indent=1))


if __name__ == "__main__":
    main()
