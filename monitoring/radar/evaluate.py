"""Evaluate a sealed alert using bounded historical price observations and a separate settlement label."""
from bisect import bisect_left
from datetime import datetime, timezone
import json
import math

HORIZONS = {"1h": 3600, "6h": 6 * 3600, "24h": 24 * 3600}
MAX_MARK_DELAY = 600
VERSION = "radar-evaluation/2"
CLOB, GAMMA = "https://clob.polymarket.com", "https://gamma-api.polymarket.com"


def as_list(v):
    """Gamma returns some list fields as JSON strings and some as lists."""
    if isinstance(v, list):
        return v
    try:
        x = json.loads(v or "[]")
    except (TypeError, ValueError):
        return []
    return x if isinstance(x, list) else []


class PriceHistory:
    """Ordered chart observations. Conflicting values at the first eligible timestamp are ambiguous."""

    def __init__(self, points):
        prices = {}
        for stamp, value in points:
            if value is None or isinstance(value, bool):
                raise ValueError("invalid price-history value")
            price = float(value)
            if not math.isfinite(stamp) or not 0 <= price <= 1:
                raise ValueError("invalid price-history timestamp or price")
            prices[stamp] = price if prices.get(stamp, price) == price else None
        self.times = sorted(prices)
        self.prices = prices

    def first(self, target, as_of, tolerance=MAX_MARK_DELAY):
        pos = bisect_left(self.times, target)
        if pos == len(self.times):
            return None
        stamp = self.times[pos]
        if stamp > min(target + tolerance, as_of) or self.prices[stamp] is None:
            return None
        return {"t": stamp, "price": self.prices[stamp], "delay_s": stamp - target}


def shadow(entry_price, outcome_won, fee_rate):
    """Return per hypothetical USD using the stated all-in fee convention."""
    if entry_price is None or outcome_won is None or not 0 < entry_price < 1:
        return None
    return round((1.0 - fee_rate) / entry_price - 1.0 if outcome_won else -1.0, 6)


def resolution(m, outcome_index, now=None):
    """Latest Gamma label, gated on recorded close time when supplied. Only binary payouts qualify."""
    if m.get("closed") is not True:
        return None, "open"
    if now is not None and m.get("closedTime"):
        try:
            close = datetime.fromisoformat(m["closedTime"].replace("Z", "+00:00"))
            if close.tzinfo is None:
                close = close.replace(tzinfo=timezone.utc)
            if close.timestamp() > now:
                return None, "close after evaluation"
        except (AttributeError, TypeError, ValueError, OverflowError):
            return None, "invalid close time"
    try:
        prices = [float(x) for x in as_list(m.get("outcomePrices"))]
    except (TypeError, ValueError):
        return None, "invalid settlement prices"
    if sorted(prices) != [0.0, 1.0] or outcome_index not in (0, 1):
        return None, "not settled at 0 and 1"
    status = m.get("umaResolutionStatus")
    if status is not None and status != "resolved":
        return None, f"UMA status {status}"
    return prices[outcome_index] == 1.0, "uma" if status == "resolved" else "settled prices"


def evaluate(rec, get_json, now, fee_rate=0.0):
    """Price references for one alert. A chart observation never supplies bid, ask, quantity or a fill."""
    if not 0 <= fee_rate < 1:
        raise ValueError("fee must be in [0, 1)")
    t0 = rec.get("emitted_t")
    if t0 is None or now < t0 + HORIZONS["1h"]:
        return None
    cid = (rec["market"].get("condition_id") or "").lower()
    outcome = rec["market"].get("outcome")
    base = {"alert": rec["id"], "engine_alert_id": rec.get("engine_alert_id"), "class": rec["risk"]["class"],
            "evaluation_version": VERSION}
    if not cid:
        return dict(base, status="DATA_UNAVAILABLE", why="missing condition id")
    found = []
    for q in (f"{GAMMA}/markets?condition_ids={cid}&closed=true", f"{GAMMA}/markets?condition_ids={cid}"):
        got = get_json(q)
        found = [m for m in (got if isinstance(got, list) else []) if str(m.get("conditionId", "")).lower() == cid]
        if found:
            break
    if len(found) != 1:
        return dict(base, status="DATA_UNAVAILABLE", why=f"{len(found)} Gamma markets with this condition id")
    m = found[0]
    outs = as_list(m.get("outcomes"))
    ids = as_list(m.get("positionIds") if m.get("version") == "v2" else m.get("clobTokenIds"))
    if (len(outs) != 2 or outs.count(outcome) != 1 or len(ids) != 2
            or not all(str(t).isdigit() for t in ids) or str(ids[0]) == str(ids[1])):
        return dict(base, status="DATA_UNAVAILABLE", why="ambiguous binary outcome or token")
    i = outs.index(outcome)
    end = math.floor(min(now, t0 + HORIZONS["24h"] + MAX_MARK_DELAY))
    data = get_json(f"{CLOB}/prices-history?market={ids[i]}&startTs={int(t0) - 60}&endTs={end}&fidelity=1")
    if not isinstance(data, dict) or not isinstance(data.get("history"), list):
        return dict(base, status="DATA_UNAVAILABLE", why="missing price history")
    try:
        history = PriceHistory((float(h["t"]), h["p"]) for h in data["history"])
    except (KeyError, TypeError, ValueError, OverflowError):
        return dict(base, status="DATA_UNAVAILABLE", why="invalid price history")
    entry = history.first(t0, now)
    marks = {k: history.first(t0 + s, now) for k, s in HORIZONS.items()}
    path = {k: "NOT_YET" if now < t0 + s else marks[k]["price"] if marks[k] else None
            for k, s in HORIZONS.items()}
    won, basis = resolution(m, i, now)
    price = entry["price"] if entry else None
    result = shadow(price, won, fee_rate)
    return dict(base, emitted_t=t0, max_mark_delay_s=MAX_MARK_DELAY,
                entry={**(entry or {"t": None, "price": None, "delay_s": None}),
                       "kind": "PRICE_HISTORY_DEPTH_UNKNOWN" if entry else "DATA_UNAVAILABLE"},
                trigger_fill_price=rec["price_and_depth"].get("price_at_alert"),
                printed_price_after_emission=path, horizon_observations=marks,
                outcome_won=won, resolution_basis=basis, closed_time=m.get("closedTime"),
                shadow={"fee_rate": fee_rate, "net_return_per_usd": result},
                status="FINAL" if result is not None and all(marks.values()) else "PARTIAL")
