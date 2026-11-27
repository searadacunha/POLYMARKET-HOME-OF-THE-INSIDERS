"""How far the trading of a few wallets overlaps, and whether their timing is closer than chance.

Per pair of wallets: the markets both traded, their Jaccard overlap, the outcomes both ended up net buyers of, the
outcomes both bought within 60 and 600 seconds of each other, and the transactions they share. A shared transaction
is usually a batch or the two sides of one match, so it is listed as NOT_A_LINK. The co-timing of the whole set is
then compared with the repository's circular-shift null model (integrations/forensic-intelligence/temporal.py).

Beating that null is at most PROBABLE_COORDINATION: no money link and no common control is shown, and similar timing
on a market that everybody rushes into after public news proves nothing.
"""
from bisect import bisect_left
from collections import defaultdict
from decimal import Decimal
from itertools import combinations

from . import _legacy
from .cluster import COORDINATION, NOT_A_LINK
from .ledger import amount, units
from .sources import ADDRESS, SourceError, utc

WINDOWS = (60, 600)
NULL_WINDOW = 60  # the null model offers 5, 30, 60, 300, 900 and 3600 seconds; 600 is not one of them


def _closest(times, others):
    """Smallest gap in seconds between a time of one sorted list and a time of the other."""
    best = None
    for t in times:
        i = bisect_left(others, t)
        near = min(abs(o - t) for o in others[max(0, i - 1):i + 1])
        best = near if best is None else min(best, near)
    return best


def _trading(rows):
    markets, net, buys, txs = set(), defaultdict(int), defaultdict(list), set()
    for row in rows:
        if row.get("transaction_hash"):
            txs.add(row["transaction_hash"].lower())
        if row.get("type") != "TRADE":
            continue
        if row.get("side") not in ("BUY", "SELL") or not row.get("condition_id"):
            raise SourceError(f"trade row without side or market in {row.get('transaction_hash')}")
        key = (row["condition_id"], row.get("outcome_index"))
        markets.add(row["condition_id"])
        net[key] += units(row.get("size") or 0) * (1 if row["side"] == "BUY" else -1)
        if row["side"] == "BUY":
            buys[key].append(row["timestamp"])
    return {"markets": markets, "net": net, "buys": {k: sorted(v) for k, v in buys.items()}, "txs": txs}


def _pair(a, b, x, y):
    both, either = x["markets"] & y["markets"], x["markets"] | y["markets"]
    gaps = [_closest(x["buys"][k], y["buys"][k]) for k in x["buys"].keys() & y["buys"].keys()]
    same = sorted((k for k in x["net"].keys() & y["net"].keys() if x["net"][k] > 0 and y["net"][k] > 0), key=lambda k: (k[0], str(k[1])))
    shared = sorted(x["txs"] & y["txs"])
    return {"a": a, "b": b, "markets_both": sorted(both), "markets_both_count": len(both),
            "jaccard": round(len(both) / len(either), 6) if either else None,
            "same_side_net_buys": [{"condition_id": c, "outcome_index": i} for c, i in same],
            **{f"bought_within_{w}s": sum(g <= w for g in gaps) for w in WINDOWS},
            "shared_transactions": {"count": len(shared), "transactions": shared, "grade": NOT_A_LINK,
                                    "note": "a shared transaction is usually a batch or the two sides of one match, not a relation"}}


def _null_rows(wallet, rows):
    """Buys in the row schema of temporal.py. A buy whose cash is not above 0 and at most its size has no price in (0, 1]."""
    out, excluded = [], 0
    for position, row in enumerate(rows):
        if row.get("type") != "TRADE" or row.get("side") != "BUY":
            continue
        size, cash = units(row.get("size") or 0), units(row.get("usdc_size") or 0)
        if not 0 < cash <= size:
            excluded += 1
            continue
        out.append({"wallet": wallet, "market_id": row["condition_id"], "outcome_id": str(row.get("outcome_index")),
                    "timestamp_utc": utc(row["timestamp"]), "observed_at_utc": utc(row["timestamp"]),
                    "transaction_hash": row["transaction_hash"],
                    "fill_id": position, "nominal": amount(cash), "price": str(Decimal(cash) / Decimal(size))})
    return out, excluded


def compare_traders(sources, wallets, max_rows=50000):
    """Pairwise overlap of 2 to 10 trading wallets and a null test of their co-timing, from their activity rows."""
    if not isinstance(wallets, (list, tuple)) or not 2 <= len(wallets) <= 10:
        raise ValueError("give 2 to 10 wallets")
    if not all(isinstance(w, str) and ADDRESS.fullmatch(w) for w in wallets):
        raise ValueError("every wallet must be a 0x address of 40 hex digits")
    wallets = [w.lower() for w in wallets]
    if len(set(wallets)) != len(wallets):
        raise ValueError("a wallet is listed twice")
    if type(max_rows) is not int or max_rows < 1:
        raise ValueError("max_rows must be a positive integer")
    reads = {w: sources.activity(w, max_rows=max_rows) for w in wallets}
    seen = {w: _trading(r["rows"]) for w, r in reads.items()}
    summary = [{"wallet": w, "rows": len(r["rows"]), "trade_rows": sum(row.get("type") == "TRADE" for row in r["rows"]),
                "markets": len(seen[w]["markets"]), "pages": r["pages"], "complete": r["complete"]} for w, r in reads.items()]
    pairs = [_pair(a, b, seen[a], seen[b]) for a, b in combinations(wallets, 2)]

    temporal = _legacy.temporal()
    if temporal is None:
        null = {"available": False, "reason": "the repository checkout with integrations/forensic-intelligence/temporal.py is absent"}
    else:
        rows, excluded = [], 0
        for w, r in reads.items():
            found, skipped = _null_rows(w, r["rows"])
            rows, excluded = rows + found, excluded + skipped
        as_of = utc(max((row["timestamp"] for r in reads.values() for row in r["rows"]), default=0))
        null = {"available": True, "window_s": NULL_WINDOW, "buys_used": len(rows), "buys_excluded_cash_not_in_0_to_size": excluded,
                "statistic": "distinct wallet pairs of the set that bought the same outcome of a market within window_s, summed",
                **temporal.circular_shift_null(rows, as_of, window_s=NULL_WINDOW)}

    cut = [s["wallet"] for s in summary if not s["complete"]]
    limits = [(f"activity capped at max_rows={max_rows} and NOT complete for {', '.join(cut)}: counts are of the rows read only" if cut
               else "activity read to the end for every wallet"),
              "shared transactions are listed as NOT_A_LINK: a batch or the two sides of one match put two wallets in one transaction",
              f"the null test runs at {NULL_WINDOW} seconds only, the null model has no 600-second horizon; it is exploratory, not validated",
              "the null shifts each wallet's buys within each market and outcome; it does not model a shared public trigger"]
    return {"wallets": summary, "pairs": pairs, "co_timing_null": null,
            "statement": f"Co-timing beyond the null model is at most {COORDINATION}: no money link and no common control is shown. "
                         "Similar timing on a market that everybody rushes into after public news proves nothing.",
            "limits": limits}
