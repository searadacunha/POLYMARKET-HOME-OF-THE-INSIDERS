#!/usr/bin/env python3
"""Score candidate alerts. This is the ONLY script that reads the outcome file.

For each alert: win/loss from labels.jsonl, price at the alert (executed price carried by the alert),
gross result per share, and the same at a declared slippage grid.
Also draws the S1 matched placebo: for every alert, `--placebo-n` points taken from OTHER markets
whose YES-equivalent price at a uniformly random time lies in the same 0.05 band.
Seed is fixed and declared (20261116). No midpoint is ever used.
"""
import argparse, bisect, json, os, random, sqlite3, urllib.parse

SLIPPAGE = (0.0, 0.005, 0.01, 0.02, 0.05)
SEED = 20261116
BAND = 0.05


def price_grid(con, cid, step=600):
    """Last executed YES price per 10-minute bucket, plus side-aware lookup."""
    rows = con.execute(
        "select ts, outcome, price from trades where condition_id=? order by ts", (cid,)).fetchall()
    grid = []
    for ts, oc, price in rows:
        b = ts // step
        if grid and grid[-1][0] == b:
            grid[-1][1].setdefault(oc, price)
            grid[-1][1][oc] = price
        else:
            grid.append([b, {oc: price}])
    return grid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alerts", required=True)
    ap.add_argument("--labels", required=True)
    ap.add_argument("--tapes", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--placebo-n", type=int, default=5)
    ap.add_argument("--no-placebo", action="store_true")
    a = ap.parse_args()

    winner = {}
    for line in open(a.labels):
        r = json.loads(line)
        winner[r["condition_id"]] = r["winner"].strip().lower()
    con = sqlite3.connect(f"file:{urllib.parse.quote(os.path.abspath(a.tapes))}?mode=ro", uri=True)
    alerts = [json.loads(l) for l in open(a.alerts)]

    grids = {}
    for cid in {al["condition_id"] for al in alerts}:
        grids[cid] = price_grid(con, cid)
    rng = random.Random(SEED)
    scored = []
    for al in alerts:
        cid, side, p = al["condition_id"], al["side"], al["price"]
        w = winner.get(cid)
        if w is None:
            continue
        win = 1 if w == side.lower() else 0
        rec = dict(al)
        rec["winner"] = w
        rec["win"] = win
        rec["excess"] = win - p
        for s in SLIPPAGE:
            entry = min(p + s, 0.999)
            rec[f"payoff_{s}"] = round((1 - entry) if win else -entry, 6)
        scored.append(rec)

    # S1 matched placebo, drawn INSIDE the alert's own market (amendment 003):
    # same side, same price band, a uniformly random bucket at least 6 hours from the alert.
    placebo = []
    for al in scored:
        cid, side, p = al["condition_id"], al["side"], al["price"]
        grid = grids.get(cid) or []
        cands = [(b, oc.get(side)) for b, oc in grid]
        cands = [(b, pp) for b, pp in cands if pp is not None and abs(pp - p) <= BAND and abs(b * 600 - al["t"]) >= 6 * 3600]
        if not cands:
            continue
        w = winner.get(cid)
        if w is None:
            continue
        for _ in range(a.placebo_n):
            b, pp = cands[rng.randrange(len(cands))]
            win = 1 if w == side.lower() else 0
            placebo.append({"for_alert": f'{cid}:{side}:{al["t"]}', "condition_id": cid, "side": side,
                            "price": pp, "win": win, "excess": win - pp,
                            "event_id": al.get("event_id"), "split": al.get("split")})

    # control: a matched placebo must be calibrated; a systematic gap means the label join is broken
    if placebo:
        pr = sum(r["win"] for r in placebo) / len(placebo)
        pm = sum(r["price"] for r in placebo) / len(placebo)
        if abs(pr - pm) > 0.15:
            raise SystemExit(f"label join control failed: placebo win rate {pr:.3f} vs placebo mean price {pm:.3f}")

    with open(a.out, "w") as f:
        for r in scored:
            f.write(json.dumps(r) + "\n")
    with open(a.out + ".placebo.jsonl", "w") as f:
        for r in placebo:
            f.write(json.dumps(r) + "\n")
    print(json.dumps({"alerts": len(scored), "placebo": len(placebo), "seed": SEED,
                      "slippage_grid": SLIPPAGE}))


if __name__ == "__main__":
    main()
