"""What one market did: its state, its price path, who held it, who traded it, and who had bought before its move.

Every figure is a fact of the public record: a catalogue field, a price point, a listed holding, a fill. A wallet that
bought an outcome before its price rose is a timing fact. It does not show who controls the wallet, and it does not
show that anyone knew something the public did not: the same public news, the price itself or a plain view that
turned out right explain the same rows. Cash of a fill is size x price as the trades endpoint reports it, fees left
out. The holders endpoint lists the largest holders of each side only, so concentration is among those listed.
"""
import json
from collections import deque
from datetime import datetime
from fractions import Fraction

from .ledger import UNIT, amount, units
from .sources import SourceError, utc

FIDELITY = 10            # minutes between price points
MOVE_WINDOW = 6 * 3600   # the largest rise and fall are measured within any window this long
HOLDERS_LISTED = 100     # the endpoint's cap per side
TOPS = (1, 5, 10)


def _listed(record, field):
    try:
        value = json.loads(record.get(field) or "")
    except ValueError:
        value = None
    if not isinstance(value, list):
        raise SourceError(f"catalogue field {field} is not a JSON list")
    return value


def _when(text):
    """A catalogue date ('2025-07-08T15:43:10.159Z' or '2025-10-10 12:11:22+00') as UTC seconds, or None."""
    try:
        return int(datetime.fromisoformat(text).timestamp())
    except (TypeError, ValueError):
        return None


def _point(ts, price):
    return {"ts": ts, "utc": utc(ts), "price": price}


def _moves(points):
    """Largest rise and largest fall within any MOVE_WINDOW, in one pass with a rising and a falling monotonic queue."""
    low, high, rise, fall = deque(), deque(), (0, None, None), (0, None, None)
    for j, point in enumerate(points):
        for queue in (low, high):
            while queue and point["t"] - points[queue[0]]["t"] > MOVE_WINDOW:
                queue.popleft()
        if low and point["p"] - points[low[0]]["p"] > rise[0]:
            rise = (point["p"] - points[low[0]]["p"], low[0], j)
        if high and points[high[0]]["p"] - point["p"] > fall[0]:
            fall = (points[high[0]]["p"] - point["p"], high[0], j)
        while low and points[low[-1]]["p"] >= point["p"]:
            low.pop()
        low.append(j)
        while high and points[high[-1]]["p"] <= point["p"]:
            high.pop()
        high.append(j)
    return [None if i is None else {"start": _point(points[i]["t"], points[i]["p"]), "end": _point(points[j]["t"], points[j]["p"]),
                                    "change": round(points[j]["p"] - points[i]["p"], 6)} for _, i, j in (rise, fall)]


def _price_at(points, ts):
    """The last price at or before ts, or None when the path starts later."""
    before = [p for p in points if p["t"] <= ts]
    return before[-1] if before else None


def _book(rows):
    """Per (wallet, outcome index): shares and cash (size x price, in 1e-6 units) bought and sold, first buy."""
    book = {}
    for row in rows:
        if row.get("side") not in ("BUY", "SELL") or not row.get("proxy_wallet"):
            raise SourceError(f"trade row without side or wallet in {row.get('transaction_hash')}")
        entry = book.setdefault((row["proxy_wallet"].lower(), row.get("outcome_index")),
                                {"outcome": row.get("outcome"), "BUY": [0, Fraction(0)], "SELL": [0, Fraction(0)], "first_buy_ts": None})
        shares = units(row["size"])
        entry[row["side"]][0] += shares
        entry[row["side"]][1] += shares * Fraction(str(row["price"]))
        if row["side"] == "BUY" and (entry["first_buy_ts"] is None or row["timestamp"] < entry["first_buy_ts"]):
            entry["first_buy_ts"] = row["timestamp"]
    return book


def _line(key, entry):
    (wallet, index), (bought, paid), (sold, received) = key, entry["BUY"], entry["SELL"]
    return {"proxy_wallet": wallet, "outcome_index": index, "outcome": entry["outcome"], "cash_bought": amount(paid),
            "cash_sold": amount(received), "shares_bought": amount(bought), "shares_sold": amount(sold), "first_buy_ts": entry["first_buy_ts"],
            "average_buy_price": amount(paid / bought * UNIT) if bought else None}


def market_report(sources, condition, event_ts=None, max_trade_rows=20000):
    """State, price path, holder concentration and trading of one market, and the wallets net long before its move.

    event_ts: a sourced UTC time of the event the caller studies. Without it the reference is the start of the
    largest 6-hour rise of the first outcome. The report says which one was used.
    """
    if event_ts is not None and (type(event_ts) is not int or event_ts < 0):
        raise ValueError("event_ts must be unix seconds")
    if type(max_trade_rows) is not int or max_trade_rows < 1:
        raise ValueError("max_trade_rows must be a positive integer")
    record = sources.market(condition)
    if record is None:
        raise SourceError(f"the catalogue does not know the market {condition}")
    outcomes, tokens = _listed(record, "outcomes"), [str(t) for t in _listed(record, "clobTokenIds")]
    if len(outcomes) != 2 or len(tokens) != 2:
        raise SourceError(f"market {condition} is not a two-outcome market with two tokens")
    resolved = record.get("umaResolutionStatus") == "resolved"
    state = {"condition_id": record.get("conditionId"), "question": record.get("question"), "slug": record.get("slug"), "outcomes": outcomes,
             "token_ids": tokens, "closed": bool(record.get("closed")), "closed_time": record.get("closedTime"),
             "start_date": record.get("startDate"), "end_date": record.get("endDate"), "neg_risk": bool(record.get("negRisk")),
             "volume": record.get("volume"), "resolution_status": record.get("umaResolutionStatus"), "resolved": resolved,
             "payouts": _listed(record, "outcomePrices") if resolved else None}

    # The life of the market bounds the price read: without bounds the source returns nothing for an old market.
    opened, ended = _when(record.get("startDate")), _when(record.get("closedTime")) or _when(record.get("endDate"))
    if opened is not None and (ended is None or not record.get("closed")):
        ended = int(sources.clock())
    try:
        points = sorted(({"t": int(x["t"]), "p": float(x["p"])} for x in sources.price_history(tokens[0], opened, ended, fidelity=FIDELITY)),
                        key=lambda x: x["t"])
    except (KeyError, TypeError, ValueError):
        raise SourceError(f"malformed price point for token {tokens[0]}") from None
    rise, fall = _moves(points)
    path = {"token_id": tokens[0], "outcome": outcomes[0], "fidelity_minutes": FIDELITY, "points": len(points),
            "first": _point(points[0]["t"], points[0]["p"]) if points else None,
            "last": _point(points[-1]["t"], points[-1]["p"]) if points else None,
            "min": min(p["p"] for p in points) if points else None, "max": max(p["p"] for p in points) if points else None,
            "window_hours": MOVE_WINDOW // 3600, "largest_rise": rise, "largest_fall": fall}

    names = dict(zip(tokens, outcomes))
    holders = []
    for side in sources.holders(condition):
        held = sorted((units(h.get("amount") or 0) for h in side["holders"]), reverse=True)
        total = sum(held)
        holders.append({"token_id": str(side["token_id"]), "outcome": names.get(str(side["token_id"])), "holders_listed": len(held),
                        "listed_total": amount(total), "may_be_truncated": len(held) >= HOLDERS_LISTED,
                        **{f"top_{n}_share": round(sum(held[:n]) / total, 6) if total else None for n in TOPS}})

    read = sources.trades(condition=condition, max_rows=max_trade_rows)
    rows = read["rows"]
    book = _book(rows)
    trading = {"rows": len(rows), "pages": read["pages"], "complete": read["complete"], "max_trade_rows": max_trade_rows,
               "wallets": len({wallet for wallet, _ in book}),
               "by_wallet_outcome": [_line(k, e) for k, e in sorted(book.items(), key=lambda kv: (-kv[1]["BUY"][1], kv[0][0], str(kv[0][1])))]}

    if event_ts is not None:
        reference, source = event_ts, "event_ts supplied by the caller"
        before, after = _price_at(points, event_ts), _price_at(points, event_ts + MOVE_WINDOW)
        rose = None if before is None or after is None or before["p"] == after["p"] else 0 if after["p"] > before["p"] else 1
    elif rise:
        reference, source = rise["start"]["ts"], "start of the largest 6-hour rise of the first outcome"
        before, after, rose = {"t": reference, "p": rise["start"]["price"]}, {"t": rise["end"]["ts"], "p": rise["end"]["price"]}, 0
    else:
        reference, source, before, after, rose = None, "none: no event_ts given and the price path never rose", None, None, None
    positioned = {"reference_ts": reference, "reference_utc": utc(reference) if reference is not None else None, "reference_source": source,
                  "price_at_reference": before and _point(before["t"], before["p"]), "price_after": after and _point(after["t"], after["p"]),
                  "outcome_index": rose, "outcome": outcomes[rose] if rose is not None else None, "wallets": None,
                  "statement": "These wallets bought the outcome that then rose, before the reference time. That is a timing fact. It does "
                               "not show who controls a wallet, nor that anyone had non-public information: public news, the price itself "
                               "or a view that turned out right explain the same rows."}
    if rose is None:
        positioned["reason"] = "no reference time" if reference is None else "the price path does not show a move after the reference time"
    else:
        early = _book([r for r in rows if r["timestamp"] < reference])
        ahead = sorted(((k, e) for k, e in early.items() if k[1] == rose and e["BUY"][0] > e["SELL"][0]),
                      key=lambda kv: (kv[1]["SELL"][1] - kv[1]["BUY"][1], kv[0][0]))
        positioned["wallets"] = [{**_line(k, e), "net_shares": amount(e["BUY"][0] - e["SELL"][0]),
                                  "net_cash_paid": amount(e["BUY"][1] - e["SELL"][1]),
                                  "lead_seconds": reference - e["first_buy_ts"]} for k, e in ahead]

    limits = [(f"trades: {len(rows)} rows in {read['pages']} pages, read to the end" if read["complete"] else
               f"trades: capped at max_trade_rows={max_trade_rows}; {len(rows)} rows in {read['pages']} pages, complete=False, "
               "so wallets, cash and positions are of the rows read only"),
              "cash of a fill is size x price from the trades endpoint; fees are not included, so cash is approximate",
              f"holders: the endpoint lists at most {HOLDERS_LISTED} holders per side; shares are of the listed total, not of the supply, "
              "and only the listed holders are known",
              "a wallet that bought before a move may have read the same public news as everyone, or followed the price: buying "
              "first is not knowing first",
              f"the price path is the first outcome token at {FIDELITY}-minute points; a faster move is smoothed",
              "positioned before the move nets buys and sells of the outcome that rose only; buying the opposite outcome is not netted"]
    return {"market": state, "price_path": path, "holders": holders, "trades": trading, "positioned_before_move": positioned, "limits": limits}
