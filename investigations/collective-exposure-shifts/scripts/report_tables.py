#!/usr/bin/env python3
"""Publication tables: executable readings and the verifiable alert lists.

For every S4 primary alert the script finds, inside the alert's own window, the largest executed fill on the alert
side and the last executed fill of the contributing wallets. Those two rows (tx hash, timestamp, size, price) are
what a reader can check against the public tape. No midpoint, no estimated ask: the historical order book is not
archived, and the plan says so.
"""
import argparse, json, os, sqlite3, urllib.parse

SLIPPAGE = (0.0, 0.005, 0.01, 0.02, 0.05)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scored", required=True)
    ap.add_argument("--tapes", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()
    con = sqlite3.connect(f"file:{urllib.parse.quote(os.path.abspath(a.tapes))}?mode=ro", uri=True)

    rows = [json.loads(l) for l in open(a.scored)]
    s4 = [r for r in rows if r["variant"] == "S4" and r.get("primary")]

    def fills(cid, t0, t1, side):
        return con.execute(
            "select ts, wallet, side, outcome, size, price, tx from trades "
            "where condition_id=? and ts>? and ts<=? and outcome=? order by ts", (cid, t0, t1, side)).fetchall()

    out_rows = []
    for r in s4:
        fs = fills(r["condition_id"], r["t"] - 3600, r["t"], r["side"])
        wset = set(r["wallets"])
        mine = [f for f in fs if f[1] in wset]
        biggest = max(fs, key=lambda f: f[4] * f[5]) if fs else None
        last = mine[-1] if mine else None
        out_rows.append({
            "condition_id": r["condition_id"], "event_slug": r.get("event_slug"), "side": r["side"],
            "split": r.get("split"), "t": r["t"], "price": r["price"], "n_wallets": r["n_wallets"],
            "total_usd": r["total_usd"], "largest_share": r["largest_share"],
            "signal_available_ts": last[0] if last else None,
            "wallets": r["wallets"], "shift_usd": r["shift_usd"],
            "largest_fill": ({"ts": biggest[0], "wallet": biggest[1], "size": biggest[4], "price": biggest[5],
                              "tx": biggest[6]} if biggest else None),
            "winner": r["winner"], "win": r["win"], "excess": round(r["excess"], 4),
            "payoff_at_slippage": {str(s): r[f"payoff_{s}"] for s in SLIPPAGE},
        })

    def mean(xs):
        return sum(xs) / len(xs) if xs else None

    by_slip = {str(s): {"n": len(s4), "mean_payoff": mean([r[f"payoff_{s}"] for r in s4]),
                        "win_rate": mean([r["win"] for r in s4]), "mean_price": mean([r["price"] for r in s4])}
               for s in SLIPPAGE}
    # break-even slippage: largest s in the grid with a non-negative mean payoff
    be = None
    for s in SLIPPAGE:
        if by_slip[str(s)]["mean_payoff"] is not None and by_slip[str(s)]["mean_payoff"] >= 0:
            be = s
    winners = sorted([r for r in out_rows if r["win"] == 1], key=lambda r: -r["total_usd"])[:a.top]
    losers = sorted([r for r in out_rows if r["win"] == 0], key=lambda r: -r["total_usd"])[:a.top]
    out = {"n_s4_primary": len(s4), "by_slippage": by_slip, "break_even_slippage_upper_bound": be,
           "order_book_archived": False,
           "note": ("The historical order book (ask, depth, spread) is not archived for these markets. Payoffs use the "
                    "last executed price and the declared slippage grid; a reader must not read them as fillable prices."),
           "alerts_that_won": winners, "alerts_that_lost": losers,
           "by_split": {sp: {"n": sum(1 for r in out_rows if r["split"] == sp),
                             "wins": sum(1 for r in out_rows if r["split"] == sp and r["win"] == 1),
                             "mean_price": mean([r["price"] for r in out_rows if r["split"] == sp]),
                             "mean_payoff_1pct": mean([r["payoff_at_slippage"]["0.01"] for r in out_rows if r["split"] == sp])}
                        for sp in ("TRAIN", "VALID", "TEST")}}
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps({"n_s4_primary": len(s4), "by_slippage": by_slip, "break_even": be}, indent=1))


if __name__ == "__main__":
    main()
