"""Tape features of one ignition. Pure functions, no I/O.

Point-in-time rule: every quantity returned by `alert_features` uses only tape rows with ts <= t_alert and the grid
baseline computed at t1 <= t_alert. Nothing here reads an outcome.

Tape rows are those of data-api /v2/trades?condition=...&taker_only=false : one row per taker order AND one row per
maker order consumed, each from the point of view of its own wallet. A purchase of token S therefore appears exactly
once, as a BUY row on S by the buyer, whether the buyer was maker or taker.
"""
START_MULT = 1.5      # a buy counts as part of the move when its price >= START_MULT * baseline
PRE = 600             # trades are searched from t0 - PRE
W_LONELY = 900        # the initiator and its share are measured on the first 15 minutes
MIN_BUYER_CASH = 20.0
MIN_BURST_CASH = 500.0  # buys of S in the 15 minutes opened by the first buy of the move
MIN_MOVE_CASH = 1000.0
POST_MAX = 0.90
LONELY_SHARE = 0.5
THIN_MARKETS = 2


def alert_features(rows, side, base, t0, t1):
    """rows: iterable of (ts, wallet, side, outcome, size, price). Returns (features dict, None) or (None, reason)."""
    tok = "Yes" if side == "YES" else "No"
    buys = sorted((r for r in rows if r[2] == "BUY" and r[3] == tok), key=lambda r: r[0])
    move = [r for r in buys if t0 - PRE <= r[0] <= t1 and r[5] >= START_MULT * base]
    if not move:
        return None, "no_trade_confirmation"
    # The move starts at the first such buy that opens a burst: a dust trade above a low baseline does not start the clock.
    t_first = next((r[0] for r in move if sum(x[4] * x[5] for x in buys if r[0] <= x[0] <= r[0] + W_LONELY) >= MIN_BURST_CASH), None)
    if t_first is None:
        return None, "no_burst"
    t_alert = max(t1, t_first + W_LONELY)
    upto = [r for r in buys if t_first <= r[0] <= t_alert]
    cash_move = sum(r[4] * r[5] for r in upto)
    if cash_move < MIN_MOVE_CASH:
        return None, "move_below_min_cash"
    p_alert = upto[-1][5]
    if p_alert > POST_MAX:
        return None, "price_above_post_max"
    w15 = [r for r in upto if r[0] <= t_first + W_LONELY]
    per, first_ts = {}, {}
    for r in w15:
        per[r[1]] = per.get(r[1], 0.0) + r[4] * r[5]
        first_ts.setdefault(r[1], r[0])
    total15 = sum(per.values())
    initiator = sorted(per, key=lambda w: (-per[w], first_ts[w], w))[0]
    own = [r for r in upto if r[1] == initiator]
    return {
        "t_first": t_first, "t_alert": t_alert, "p_alert": round(p_alert, 6), "cash_move": round(cash_move, 2),
        "initiator": initiator, "share15": round(per[initiator] / total15, 6), "total15": round(total15, 2),
        "n_buyers15": sum(1 for v in per.values() if v >= MIN_BUYER_CASH),
        "initiator_cash": round(sum(r[4] * r[5] for r in own), 2),
        "initiator_first_price": round(own[0][5], 6), "initiator_max_price": round(max(r[5] for r in own), 6),
        "escalation": round(max(r[5] for r in own) / own[0][5], 4) if own[0][5] > 0 else None,
        "n_buy_rows": len(upto),
    }, None


def classify(feat, prior_markets):
    """Alert classes fixed by the plan. prior_markets: distinct conditions traded by the initiator before t_first."""
    lonely = feat["share15"] >= LONELY_SHARE
    thin = prior_markets is not None and prior_markets <= THIN_MARKETS
    return {"lonely": lonely, "thin": thin, "lonely_thin": lonely and thin}


def _selftest():
    base, t0, t1 = 0.03, 1000, 4000
    rows = [(900, "old", "BUY", "Yes", 100, 0.03),            # below the move threshold: ignored for t_first
            (1500, "A", "BUY", "Yes", 20000, 0.05), (1600, "A", "BUY", "Yes", 15000, 0.10),
            (1700, "B", "BUY", "Yes", 500, 0.12), (1800, "C", "BUY", "No", 9000, 0.70),   # C bets against: not a buy of S
            (2000, "A", "BUY", "Yes", 30000, 0.30), (3900, "D", "BUY", "Yes", 100, 0.41),
            (5000, "E", "BUY", "Yes", 99999, 0.95)]            # after t_alert: must not be seen
    f, why = alert_features(rows, "YES", base, t0, t1)
    assert why is None and f["t_first"] == 1500 and f["t_alert"] == 4000 and f["initiator"] == "A", (f, why)
    assert f["p_alert"] == 0.41 and f["n_buyers15"] == 2 and abs(f["share15"] - 11500 / 11560) < 1e-6, f
    assert f["escalation"] == 6.0 and f["initiator_cash"] == 11500.0
    assert classify(f, 0)["lonely_thin"] and not classify(f, 3)["thin"] and not classify(f, None)["thin"]
    assert alert_features(rows[:1], "YES", base, t0, t1) == (None, "no_trade_confirmation")
    far = [(450, "Z", "BUY", "Yes", 5, 0.05)] + rows          # dust more than 15 minutes before the burst does not open it
    assert alert_features(far, "YES", base, t0, t1)[0] == f
    near, _ = alert_features([(1100, "Z", "BUY", "Yes", 5, 0.05)] + rows, "YES", base, t0, t1)
    assert near["t_first"] == 1100 and near["initiator"] == "A" and abs(near["share15"] - 11500 / 11560.25) < 1e-6  # dust inside the burst window
    assert alert_features([(1100, "Z", "BUY", "Yes", 5, 0.05), (3000, "A", "BUY", "Yes", 20000, 0.05)], "YES", base, t0, t1)[0]["t_first"] == 3000
    assert alert_features([(1100, "Z", "BUY", "Yes", 5, 0.05)], "YES", base, t0, t1) == (None, "no_burst")
    assert alert_features([(1500, "A", "BUY", "Yes", 100, 0.05)], "YES", base, t0, t1) == (None, "no_burst")
    assert alert_features([(1500, "A", "BUY", "Yes", 12000, 0.05)], "YES", base, t0, t1) == (None, "move_below_min_cash")  # 600 USD burst, under 1,000
    assert alert_features([(1500, "A", "BUY", "Yes", 9000, 0.95)], "YES", base, t0, t1) == (None, "price_above_post_max")
    g, _ = alert_features([(t, w, s, "No" if o == "Yes" else "Yes", z, p) for t, w, s, o, z, p in rows], "NO", base, t0, t1)
    assert g == f                                              # symmetric on the NO side
    print("tapefeat selftest ok")


if __name__ == "__main__":
    _selftest()
