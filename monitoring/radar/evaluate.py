"""Deferred evaluation of sealed alerts, written to a separate chain; an alert record is never touched.

For each sealed alert whose horizon has passed: the printed price of the alerted outcome 1 h, 6 h and 24 h after the
trigger (CLOB price history), the market's resolution once Gamma says it is closed, and a shadow trade bought at the
price printed at the trigger, net of a fee. The order book of the trigger moment is usually not archived: the shadow
entry is then marked `PRINTED_PRICE_DEPTH_UNKNOWN` (optimistic) and no slippage is invented. No real order is ever
sent. One alert is one observation of a class; a class is judged only on a pre-registered set of alerts, never here."""
import json

HORIZONS = {"1h": 3600, "6h": 6 * 3600, "24h": 24 * 3600}
CLOB, GAMMA = "https://clob.polymarket.com", "https://gamma-api.polymarket.com"


def price_at(history, t):
    """Last printed point at or before t, or None. history: [{"t", "p"}] sorted or not."""
    pts = [(int(h["t"]), float(h["p"])) for h in history if int(h["t"]) <= t]
    return max(pts)[1] if pts else None


def shadow(entry_price, outcome_won, fee_rate):
    """Net return per 1 USD of a buy at entry_price held to resolution; the fee is charged on the amount paid."""
    if entry_price is None or outcome_won is None or not 0 < entry_price < 1:
        return None
    return round((1.0 if outcome_won else 0.0) / entry_price - 1.0 - fee_rate, 6)


def evaluate(rec, get_json, now, fee_rate=0.0):
    """One evaluation for one sealed record, from public sources only, or None when no horizon has passed yet."""
    t0 = rec.get("trigger_t")
    if t0 is None or now < t0 + HORIZONS["1h"]:
        return None
    cid, outcome = rec["market"]["condition_id"], rec["market"]["outcome"]
    mk = get_json(f"{GAMMA}/markets?condition_ids={cid}&closed=true") or get_json(f"{GAMMA}/markets?condition_ids={cid}")
    m = (mk or [None])[0] if isinstance(mk, list) else None
    if not m:
        return {"alert": rec["id"], "status": "DATA_UNAVAILABLE", "why": "market not served by Gamma"}
    outs, toks = json.loads(m.get("outcomes") or "[]"), json.loads(m.get("clobTokenIds") or "[]")
    if outcome not in outs or len(toks) != len(outs):
        return {"alert": rec["id"], "status": "DATA_UNAVAILABLE", "why": "outcome not found in the market"}
    tok = toks[outs.index(outcome)]
    h = (get_json(f"{CLOB}/prices-history?market={tok}&startTs={t0 - 3600}&endTs={t0 + HORIZONS['24h'] + 600}&fidelity=10") or {}).get("history") or []
    path = {k: (price_at(h, t0 + s) if now >= t0 + s else "NOT_YET") for k, s in HORIZONS.items()}
    won = None
    if m.get("closed") and m.get("umaResolutionStatus", "resolved") in ("resolved", None):
        prices = [float(x) for x in json.loads(m.get("outcomePrices") or "[]")]
        if prices and max(prices) >= 0.99:
            won = prices[outs.index(outcome)] >= 0.99
    p0 = rec["price_and_depth"]["price_at_alert"]
    return {"alert": rec["id"], "engine_alert_id": rec["engine_alert_id"], "class": rec["risk"]["class"], "evaluated_at": int(now),
            "trigger_t": t0, "price_at_trigger": p0, "printed_price_after": path,
            "resolved": won is not None, "outcome_won": won, "closed_time": m.get("closedTime"),
            "shadow": {"entry": "PRINTED_PRICE_DEPTH_UNKNOWN" if rec["price_and_depth"]["depth"] == "DATA_UNAVAILABLE" else "BOOK",
                       "fee_rate": fee_rate, "net_return_per_usd": shadow(p0, won, fee_rate)},
            "status": "FINAL" if won is not None and all(v != "NOT_YET" for v in path.values()) else "PARTIAL"}
