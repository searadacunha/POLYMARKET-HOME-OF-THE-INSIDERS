"""How a trading wallet trades, and whether that changed over time, from its activity rows alone.

`profile` describes the rows: their kinds, when they happened, how much cash was bought and sold, at what prices, how
long positions were held and, given resolution payouts, how the main bet of each market ended against what its price
implied. `changes` looks for the point in time where the stakes, the rhythm or the prices paid shifted, with a rank
CUSUM and a permutation p-value.

What it does not show: who is behind the wallet, why it traded, or that anyone knew anything in advance. A good record
has ordinary explanations (skill, luck among many wallets, hedges held elsewhere), and a change of behaviour is a
description found in hindsight. Cash is `usdc_size`, fees included; prices are the API's fill prices. Nothing here
reads a network.
"""
import statistics
from collections import Counter, defaultdict

from . import stats
from .ledger import amount, units
from .sources import utc

DRAWS = 2_000
LEVEL = 0.01
QUARTILES = {"min": 0, "q1": 0.25, "median": 0.5, "q3": 0.75, "max": 1}
LONGSHOT, FAVOURITE = 0.10, 0.90
TRACK_RECORD_WARNING = (
    "The bets of one wallet on one event are not independent, so this tail probability overstates how surprising the record "
    "is. Among thousands of wallets, some small p-values are expected by chance. A wallet selected because it won cannot be "
    "tested on the wins that selected it: only bets made after the selection can test it. Winning at low prices shows what "
    "happened, not that anyone had information: skill, luck and positions held elsewhere are ordinary explanations.")
CHANGE_READING = (
    "A change of behaviour is a description of the rows (bigger stakes, a new rhythm, other prices), not evidence of anything "
    "about who trades or why. The change point is found in hindsight over the whole history; the p-value says how often a "
    "random order of the same values gives as sharp a break. A new bankroll, a new strategy, automation or other markets "
    "are ordinary causes.")


def _ordered(rows):
    rows = list(rows)
    if not rows:
        raise ValueError("no activity row")
    if any(not isinstance(r.get("timestamp"), int) for r in rows):
        raise ValueError("every row needs an integer timestamp")
    return sorted(rows, key=lambda r: r["timestamp"])


def _trades(rows, side):
    return [r for r in rows if r.get("type") == "TRADE" and r.get("side") == side]


def _spread(values, money=False):
    """Minimum, quartiles and maximum (linear interpolation), or None without a value."""
    if not values:
        return None
    ordered = sorted(values)
    return {name: (amount if money else float)(stats._percentile(ordered, q)) for name, q in QUARTILES.items()}


def profile(rows, prices=None):
    """Description of one wallet's activity rows. With `prices` (the shape `ledger.build` takes), its track record."""
    rows = _ordered(rows)
    buys, sells = _trades(rows, "BUY"), _trades(rows, "SELL")
    cash = [units(r.get("usdc_size") or 0) for r in buys]
    paid = [float(r["price"]) for r in buys]
    bought, by_market = sum(cash), defaultdict(int)
    for r, c in zip(buys, cash):
        by_market[r.get("condition_id") or ""] += c
    largest = max(by_market, key=lambda k: (by_market[k], k)) if bought else None
    first_buy, last_exit, first_sell, first_redeem = {}, {}, {}, {}
    for r in rows:
        condition, kind, ts = r.get("condition_id"), r.get("type"), r["timestamp"]
        if not condition:
            continue
        if kind == "TRADE" and r.get("side") == "BUY":
            first_buy.setdefault(condition, ts)
        elif (kind == "TRADE" and r.get("side") == "SELL") or kind == "REDEEM":
            last_exit[condition] = ts
            (first_sell if kind == "TRADE" else first_redeem).setdefault(condition, ts)
    holding = [last_exit[c] - t for c, t in first_buy.items() if last_exit.get(c, -1) >= t]
    exited = [c for c in first_buy if c in last_exit]
    sold_first = [c for c in exited if c in first_sell and first_sell[c] < first_redeem.get(c, float("inf"))]
    hours = [0] * 24
    for r in rows:
        if r.get("type") == "TRADE":
            hours[r["timestamp"] // 3600 % 24] += 1
    out = {"rows": len(rows), "row_types": dict(sorted(Counter(str(r.get("type")) for r in rows).items())),
           "first_utc_ts": rows[0]["timestamp"], "first_utc": utc(rows[0]["timestamp"]),
           "last_utc_ts": rows[-1]["timestamp"], "last_utc": utc(rows[-1]["timestamp"]),
           "active_days_utc": len({r["timestamp"] // 86_400 for r in rows}),
           "markets": len({r["condition_id"] for r in rows if r.get("condition_id")}),
           "events": len({r["event_slug"] for r in rows if r.get("event_slug")}),
           "buys": len(buys), "sells": len(sells), "cash_bought": amount(bought),
           "cash_sold": amount(sum(units(r.get("usdc_size") or 0) for r in sells)),
           "buy_cash": _spread(cash, money=True),
           "largest_market": {"condition_id": largest, "share_of_cash_bought": by_market[largest] / bought} if bought else None,
           "buy_price": _spread(paid),
           "cash_share_bought_under_0_10": sum(c for c, p in zip(cash, paid) if p < LONGSHOT) / bought if bought else None,
           "cash_share_bought_over_0_90": sum(c for c, p in zip(cash, paid) if p > FAVOURITE) / bought if bought else None,
           "trade_hours_utc": hours,
           "median_holding_hours": statistics.median(holding) / 3600 if holding else None, "markets_with_holding_time": len(holding),
           "markets_exited": len(exited), "markets_sold_before_redemption": len(sold_first),
           "share_sold_before_redemption": len(sold_first) / len(exited) if exited else None,
           "definitions": {"holding": "first buy to last sell or redemption of a market",
                           "exited": "a market bought, then sold or redeemed",
                           "sold_before_redemption": "an exited market with a sell earlier than its first redemption, or no redemption"},
           "limits": "a description of the activity rows: it does not show who trades or why"}
    if prices is not None:
        out["track_record"] = _track_record(buys, prices)
    return out


def _track_record(buys, prices):
    """The main outcome of each resolved market (largest cash bought), its average price and whether it won."""
    cash, shares, names, titles = defaultdict(int), defaultdict(int), {}, {}
    for r in buys:
        key = (r.get("condition_id") or "", r.get("outcome_index"))
        cash[key] += units(r.get("usdc_size") or 0)
        shares[key] += units(r.get("size") or 0)
        names.setdefault(key, r.get("outcome"))
        titles.setdefault(key[0], r.get("title"))
    bets, skipped = [], Counter()
    for condition in sorted({c for c, _ in cash if c}):
        quote = prices.get(condition) or {}
        if quote.get("source") != "RESOLUTION_PAYOUT":
            skipped["not_resolved"] += 1
            continue
        index = max((i for c, i in cash if c == condition), key=lambda i: cash[condition, i])  # a tie keeps the outcome bought first
        payout = (quote.get("prices") or {}).get(index)
        if payout is None:
            raise ValueError(f"no payout for outcome {index} of {condition}")
        if payout not in (0, 1):
            skipped["payout_not_0_or_1"] += 1
            continue
        if not shares[condition, index]:
            raise ValueError(f"buy rows without size in {condition}")
        price = min(1.0, cash[condition, index] / shares[condition, index])  # fees can lift the cash per share above 1
        bets.append({"condition_id": condition, "title": titles[condition], "outcome_index": index, "outcome": names[condition, index],
                     "cash_bought": amount(cash[condition, index]), "average_price": price, "won": payout == 1})
    wins = sum(b["won"] for b in bets)
    return {"bets": bets, "resolved_markets": len(bets), "wins": wins, "expected_wins": sum(b["average_price"] for b in bets),
            "p_at_least_these_wins": stats.poisson_binomial_tail(wins, [b["average_price"] for b in bets]),
            "skipped_markets": dict(sorted(skipped.items())),
            "null_model": "each bet wins with the probability of its average price paid, fees included, independently",
            "warning": TRACK_RECORD_WARNING}


def _centred_ranks(values):
    """Twice the centred mid-rank of each value: integers, so that comparisons under permutation are exact."""
    order, out, i = sorted(range(len(values)), key=values.__getitem__), [0] * len(values), 0
    while i < len(order):
        j = i
        while j + 1 < len(order) and values[order[j + 1]] == values[order[i]]:
            j += 1
        for k in order[i:j + 1]:
            out[k] = i + j + 2 - (len(values) + 1)
        i = j + 1
    return out


def _peak(scores):
    """(maximum absolute cumulative sum, number of values before the peak); (0, None) when the sums stay at zero."""
    best, at, running = 0, None, 0
    for k, score in enumerate(scores[:-1], 1):
        running += score
        if abs(running) > best:
            best, at = abs(running), k
    return best, at


def changes(rows, min_rows=30, seed=0):
    """Change of behaviour over the BUY rows in time order: cash per trade, hours between trades, price paid.

    Each series is replaced by its ranks, so heavy tails do not dominate. The statistic is the largest absolute
    cumulative sum of centred ranks; its p-value shuffles the order (`DRAWS` draws, seeded) and is Holm-adjusted over
    the three series. `change_index` is the position, among the BUY rows, of the first trade after the change.
    """
    if min_rows < 3:
        raise ValueError("min_rows must be at least 3")
    buys = _trades(_ordered(rows), "BUY")
    times = [r["timestamp"] for r in buys]
    series = {"cash_per_trade": ([units(r.get("usdc_size") or 0) for r in buys], 0, amount),
              "hours_between_trades": ([(b - a) / 3600 for a, b in zip(times, times[1:])], 1, float),
              "price": ([float(r["price"]) for r in buys], 0, float)}
    out = {}
    for name, (values, offset, shown) in series.items():
        if len(buys) < min_rows:
            out[name] = {"values": len(values), "decision": "INSUFFICIENT_DATA"}
            continue
        scores = _centred_ranks(values)
        # Splitting off one value lets the two-sample test shuffle the whole sequence; the statistic reads it joined.
        test = stats.permutation_test(scores[:1], scores[1:], statistic=lambda a, b: _peak(a + b)[0], draws=DRAWS, seed=seed)
        best, at = _peak(scores)
        row = None if at is None else at + offset
        out[name] = {"values": len(values), "statistic": best / 2, "change_index": row,
                     "change_utc_ts": None if row is None else times[row], "change_utc": None if row is None else utc(times[row]),
                     "median_before": None if at is None else shown(statistics.median(values[:at])),
                     "median_after": None if at is None else shown(statistics.median(values[at:])),
                     "p": test["p"], "hits": test["hits"]}
    tested = [name for name in out if "p" in out[name]]
    for name, adjusted in zip(tested, stats.holm([out[name]["p"] for name in tested])):
        out[name].update(p_holm=adjusted, decision="CHANGE_DETECTED" if adjusted < LEVEL else "NO_CHANGE_DETECTED")
    return {"buys": len(buys), "min_rows": min_rows, "draws": DRAWS, "seed": seed, "level": LEVEL, "series": out,
            "reading": CHANGE_READING}
