"""Deferred evaluation of sealed alerts, written to a separate chain; an alert record is never touched.

The shadow purchase is made at the first price printed AT OR AFTER THE ALERT WAS EMITTED (trigger fill time plus the
engine's delay), never at the alerted wallet's own fill, which nobody could get after being alerted; the horizons of 1,
6 and 24 hours count from the emission too. The trigger fill's price is kept only as an upper bound, labelled so. The
order book of that moment is usually not archived: the entry is then `PRINTED_PRICE_DEPTH_UNKNOWN` and no slippage is
invented. The fee convention is all-in: one USD spent, of which the fee rate is the fee. No real order is ever sent.
One alert is one observation of a class; a class is judged only on a set of alerts fixed in advance, never here."""
import json

HORIZONS = {"1h": 3600, "6h": 6 * 3600, "24h": 24 * 3600}
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


def first_at_or_after(history, t):
    """(time, price) of the first printed point at or after t, or None."""
    pts = sorted((int(h["t"]), float(h["p"])) for h in history if int(h["t"]) >= t)
    return pts[0] if pts else None


def shadow(entry_price, outcome_won, fee_rate):
    """Net return per USD spent, the fee included in the USD: won * (1 - fee) / price - 1."""
    if entry_price is None or outcome_won is None or not 0 < entry_price < 1:
        return None
    return round((1.0 - fee_rate) / entry_price - 1.0 if outcome_won else -1.0, 6)


def resolution(m, outcome_index):
    """(won, basis) once the market is settled, else (None, why). The UMA status, when Gamma gives one, must say resolved;
    without it, only prices settled at 0 and 1 on a closed market count."""
    if not m.get("closed"):
        return None, "open"
    prices = [float(x) for x in as_list(m.get("outcomePrices"))]
    if not prices or not (max(prices) >= 0.99 and min(prices) <= 0.01):
        return None, "not settled at 0 and 1"
    status = m.get("umaResolutionStatus")
    if status is not None and status != "resolved":
        return None, f"UMA status {status}"
    return prices[outcome_index] >= 0.99, "uma" if status == "resolved" else "settled prices"


def evaluate(rec, get_json, now, fee_rate=0.0):
    """One evaluation for one sealed record, from public sources only, or None when no horizon has passed yet."""
    t0 = rec.get("emitted_t")
    if t0 is None or now < t0 + HORIZONS["1h"]:
        return None
    cid, outcome = (rec["market"].get("condition_id") or "").lower(), rec["market"].get("outcome")
    base = {"alert": rec["id"], "engine_alert_id": rec.get("engine_alert_id"), "class": rec["risk"]["class"]}
    found = []
    for q in (f"{GAMMA}/markets?condition_ids={cid}&closed=true", f"{GAMMA}/markets?condition_ids={cid}"):
        got = get_json(q)
        found = [m for m in (got if isinstance(got, list) else []) if str(m.get("conditionId", "")).lower() == cid]
        if found:
            break
    if len(found) != 1:
        return dict(base, status="DATA_UNAVAILABLE", why=f"{len(found)} Gamma markets with this condition id")
    m = found[0]
    outs, toks = as_list(m.get("outcomes")), as_list(m.get("clobTokenIds"))
    if outcome not in outs or len(toks) != len(outs):
        return dict(base, status="DATA_UNAVAILABLE", why="outcome or its token not found in the market")
    i = outs.index(outcome)
    h = (get_json(f"{CLOB}/prices-history?market={toks[i]}&startTs={int(t0) - 60}&endTs={int(t0) + HORIZONS['24h'] + 600}&fidelity=1") or {}).get("history") or []
    entry = first_at_or_after(h, t0)
    path = {k: ("NOT_YET" if now < t0 + s else (first_at_or_after(h, t0 + s) or (None, None))[1]) for k, s in HORIZONS.items()}
    won, basis = resolution(m, i)
    p_entry = entry[1] if entry else None
    final = won is not None and p_entry is not None and all(isinstance(v, float) for v in path.values())
    return dict(base, emitted_t=t0, entry={"t": entry and entry[0], "price": p_entry,
                                           "kind": "PRINTED_PRICE_DEPTH_UNKNOWN" if rec["price_and_depth"]["depth"] == "DATA_UNAVAILABLE" else "BOOK"},
                trigger_fill_price_upper_bound=rec["price_and_depth"].get("price_at_alert"), printed_price_after_emission=path,
                outcome_won=won, resolution_basis=basis, closed_time=m.get("closedTime"),
                shadow={"fee_rate": fee_rate, "net_return_per_usd": shadow(p_entry, won, fee_rate)},
                status="FINAL" if final else "PARTIAL")
