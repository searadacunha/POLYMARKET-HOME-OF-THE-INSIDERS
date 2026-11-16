#!/usr/bin/env python3
"""Case B: NO on an earlier deadline and YES on a later deadline, read at event level.

Inside one market a NO share is a short YES share. Across two deadline markets of the same event it is not:
NO(D1) + YES(D2) pays on the interval (D1, D2]. This script reads each wallet's closing position in every market of
one event, orders the markets by closing time, and counts the side sequences. It is descriptive: no test is run on
it, and no position is called an inversion across deadlines.
"""
import argparse, collections, json, os, sqlite3, urllib.parse

MIN_USD = 500.0


def side_of(x_yes_equiv, p_yes):
    """Side of the position from the sign of the YES-equivalent exposure, with its marked size."""
    marked = abs(x_yes_equiv) * p_yes
    if marked < MIN_USD:
        return None, marked
    return ("YES" if x_yes_equiv > 0 else "NO"), marked


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tapes", required=True)
    ap.add_argument("--universe", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    taps = os.path.abspath(a.tapes)

    meta = {}
    for line in open(a.universe):
        m = json.loads(line)
        meta[m["condition_id"]] = m
    con = sqlite3.connect(f"file:{urllib.parse.quote(taps)}?mode=ro", uri=True)
    cids = [r[0] for r in con.execute("select condition_id from status where status='ok'")]

    events = collections.defaultdict(list)
    for cid in cids:
        m = meta.get(cid)
        if m:
            events[m["event_slug"]].append(m)

    multi = {k: v for k, v in events.items() if len({x["closed_ts"] for x in v}) >= 2}
    patterns = collections.Counter()
    intervals = []
    for slug, markets in multi.items():
        markets = sorted(markets, key=lambda m: m["closed_ts"])
        positions = collections.defaultdict(dict)
        last_price = {}
        for m in markets:
            rows = con.execute(
                "select wallet, side, outcome, size, price from trades where condition_id=? order by ts",
                (m["condition_id"],)).fetchall()
            x = collections.defaultdict(float)
            for w, side, oc, size, price in rows:
                d = size if side == "BUY" else -size
                x[w] += d if oc == "Yes" else -d
                if oc == "Yes":
                    last_price[m["condition_id"]] = price
            for w, xx in x.items():
                s, marked = side_of(xx, last_price.get(m["condition_id"], 0.5))
                if s:
                    positions[w][m["condition_id"]] = (s, round(marked, 2))
        for w, pos in positions.items():
            if len(pos) < 2:
                continue
            seq = [pos[m["condition_id"]][0] for m in markets if m["condition_id"] in pos]
            patterns[",".join(seq)] += 1
            if len(seq) >= 2 and seq[0] == "NO" and seq[-1] == "YES":
                intervals.append({"event_slug": slug, "wallet": w,
                                  "deadlines_utc": [m["closed_ts"] for m in markets if m["condition_id"] in pos],
                                  "sides": seq,
                                  "marked_usd": [pos[m["condition_id"]][1] for m in markets if m["condition_id"] in pos]})
    out = {"events_with_multiple_deadlines": len(multi),
           "wallet_side_sequences": patterns.most_common(20),
           "no_then_yes_interval_positions": len(intervals),
           "examples": intervals[:20],
           "note": ("A NO-then-YES sequence across deadlines is a coherent interval bet, not an inversion. "
                    "Marked sizes use the last executed YES price of each market; splits, merges and redemptions "
                    "are not reconstructed.")}
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "examples"}, indent=1))


if __name__ == "__main__":
    main()
