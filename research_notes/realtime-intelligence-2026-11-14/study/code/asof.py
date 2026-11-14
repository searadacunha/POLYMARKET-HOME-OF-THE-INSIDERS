"""Point-in-time view of one wallet and the alert classes fixed by the plan. Pure functions, no I/O, no outcome.

A wallet history is a list of slim activity rows, oldest first:
    [ts, type, condition_id, side, usdc, price, outcome_index, tx]      type: T trade, D deposit, W withdrawal, other letters
Type I is a collateral transfer received by the wallet from outside Polymarket's contracts, read on the chain (col_41):
money that the activity listing does not call a deposit. It counts as funding (FRESH, deposits), never as an activity row.
An ENTRY is (t, condition_id, outcome_index, cash): the first BUY fill of 1,000 USD or more of that wallet on that side.

Point-in-time rule: `view` reads rows dated strictly before t. `watch` then advances through the rows dated t or later,
one by one, and returns the first moment the wallet's net buying of the side reaches HEAVY_USD, using only rows dated
at or before that moment.
The same code runs in the study (on stored histories) and in the live engine (on histories read at alert time).
"""
THIN_MARKETS = 2             # THIN: at most this many OTHER markets traded before the entry,
THIN_TRADES = 50             # and at most this many trades on them (a bot working one market for months is not a newcomer),
THIN_ROWS = 1000             # and fewer than this many activity rows of any kind
FRESH_S = 24 * 3600          # FRESH: a deposit, or a collateral transfer received on the chain, in the 24 hours before the entry
DEPOSIT_WINDOW_S = 7 * 86400  # deposits reported next to the buying (a reading, not a condition)
HEAVY_USD = 10000.0          # HEAVY: net buying of the side reaches this amount
WATCH_S = 24 * 3600          # an entry is watched for 24 hours
DORMANT_S = 60 * 86400       # DORMANT: last trade on another market at least 60 days before the entry
OOC_MIN_TRADES = 20          # OUT_OF_CHARACTER: at least 20 earlier trades,
OOC_MIN_SPAN_S = 7 * 86400   # spread over at least 7 days among the rows read (the last hours of a very active wallet are not a character),
OOC_MULT = 10.0              # the entry fill is 10 times their median size or more, and larger than all of them
QUIET_S = 6 * 3600


def view(rows, t, cond):
    """History of the wallet strictly before t. Returns a dict of plain numbers; `rows_before` is 0 for a wallet never seen."""
    trades = other = 0; markets = set(); cash = []; first = last_other = last_any = first_trade = None
    dep_24h = dep_7d = dep_total = 0.0; n_dep = 0; deposits = []; first_dep = None
    for r in rows:
        ts = r[0]
        if ts >= t:
            break
        if r[1] != "I":
            first = ts if first is None else first; last_any = ts
        if r[1] == "T":
            trades += 1; cash.append(r[4]); first_trade = ts if first_trade is None else first_trade
            if r[2] != cond:
                other += 1; markets.add(r[2]); last_other = ts
        elif r[1] in ("D", "I"):
            n_dep += 1; dep_total += r[4]; first_dep = ts if first_dep is None else first_dep
            if ts >= t - DEPOSIT_WINDOW_S:
                dep_7d += r[4]; deposits.append((ts, r[4], r[7]))
            if ts >= t - FRESH_S:
                dep_24h += r[4]
    cash.sort()
    med = None if not cash else (cash[len(cash) // 2] if len(cash) % 2 else (cash[len(cash) // 2 - 1] + cash[len(cash) // 2]) / 2)
    return {"rows_before": sum(1 for r in rows if r[0] < t and r[1] != "I"), "first_ts": first, "age_h": None if first is None else (t - first) / 3600.0,
            "prior_trades": trades, "prior_other_trades": other, "prior_other_markets": len(markets), "prior_trade_median": med,
            "prior_trade_max": cash[-1] if cash else None, "first_trade_ts": first_trade, "last_other_trade_ts": last_other, "last_any_ts": last_any,
            "dep_24h": dep_24h, "dep_7d": dep_7d, "dep_total": dep_total, "n_dep": n_dep, "first_dep_ts": first_dep,
            "deposits_7d": deposits}


def flags_at_entry(v, cash):
    """Classes that depend only on the history before the entry and on the entry fill."""
    thin = v["prior_other_markets"] <= THIN_MARKETS and v["prior_other_trades"] <= THIN_TRADES and v["rows_before"] < THIN_ROWS
    fresh = v["dep_24h"] > 0
    dormant = v["last_other_trade_ts"] is not None and v["_t"] - v["last_other_trade_ts"] >= DORMANT_S
    ooc = (v["prior_trades"] >= OOC_MIN_TRADES and v["_t"] - v["first_trade_ts"] >= OOC_MIN_SPAN_S and v["prior_trade_median"]
           and cash >= OOC_MULT * v["prior_trade_median"] and cash > v["prior_trade_max"])
    return {"thin": thin, "fresh": fresh, "dormant": bool(dormant), "ooc": bool(ooc)}


def watch(rows, t, cond, oi, cash, rows_before_floor=0):
    """Follow one entry for WATCH_S. Returns {"view", "flags", "heavy": None | {"t", "price", "net_buy", "deposits"}, ...}.

    heavy is the first moment, from the entry on, at which the net buying of this side since 24 h before the entry reaches
    HEAVY_USD; its price is the price the wallet paid in that fill, and `deposits` is what the wallet had received in the
    7 days before that moment. Sells of the same side are subtracted.
    `rows_before_floor` is given when the rows passed are only the end of a longer history (it then cannot be thin).
    (A first definition asked for half of the recent deposits on one side. Read on the wallets of the discovery set before
    any outcome, it kept 87 % of the fresh entries and missed the documented Nobel account, which spread 40,000 USD over
    three markets: it was replaced by an amount.)"""
    v = view(rows, t, cond); v["_t"] = t
    v["rows_before"] = max(v["rows_before"], rows_before_floor)   # history known to be longer than the rows read
    f = flags_at_entry(v, cash)
    net = 0.0; deps = []; heavy = None; saw_entry = False
    for r in rows:
        ts = r[0]
        if ts < t - FRESH_S:
            if r[1] in ("D", "I") and ts >= t - DEPOSIT_WINDOW_S:
                deps.append((ts, r[4]))
            continue
        if ts > t + WATCH_S:
            break
        if r[1] in ("D", "I"):
            deps.append((ts, r[4]))
        elif r[1] == "T" and r[2] == cond and r[6] == oi:
            net += r[4] if r[3] == "BUY" else -r[4]
            saw_entry = saw_entry or ts >= t
            if ts >= t and r[3] == "BUY" and heavy is None and net >= HEAVY_USD:
                d = sum(u for (dts, u) in deps if dts >= ts - DEPOSIT_WINDOW_S)
                heavy = {"t": ts, "price": r[5], "net_buy": round(net, 2), "deposits": round(d, 2)}
    v.pop("_t")
    return {"view": v, "flags": f, "heavy": heavy, "net_buy": round(net, 2), "entry_seen_in_history": saw_entry}


def classes(w):
    """Alert classes of one watched entry: name -> (alert time, reference price) or None. (None, None) means 'the entry fill
    itself'. C7 fires when the net buying reaches HEAVY_USD; the others fire at the entry."""
    f, heavy = w["flags"], w["heavy"]
    out = {"C1_FRESH_FUNDED_BET": None, "C2_DORMANT_REACTIVATION": None, "C3_OUT_OF_CHARACTER": None, "C7_HEAVY_NEWCOMER": None,
           "B3_THIN_NOT_FRESH": None}
    if f["thin"] and f["fresh"]:
        out["C1_FRESH_FUNDED_BET"] = (None, None)
        if heavy:
            out["C7_HEAVY_NEWCOMER"] = (heavy["t"], heavy["price"])
    if f["dormant"] and f["fresh"]:
        out["C2_DORMANT_REACTIVATION"] = (None, None)
    if f["ooc"]:
        out["C3_OUT_OF_CHARACTER"] = (None, None)
    if f["thin"] and not f["fresh"]:
        out["B3_THIN_NOT_FRESH"] = (None, None)
    return out


MIN_INFLOW_USD = 1.0         # a transfer on the chain counts as funding from 1 USD (dust and address-poisoning transfers do not)
ZERO = "0x" + "0" * 40


def chain_rows(item, wallet, t, d_txs, infra, busy_ts=(), mint_payer=None):
    """Type I rows from a col_41 answer: money received on the chain strictly before t that is not related to trading.
    Left out, and counted in the third value returned:
      dep_row    the transfer of a deposit row already in the history (its tx);
      same_second  a transfer in the same second as an activity row that is not a deposit (a sale paid by the counterparty,
                 a redemption, a reward, a withdrawal): the activity time is the block time (pre-freeze audit);
      polymarket a sender among Polymarket's contracts (`infra`: chainfund.INFRA, plus the addresses whose public name tag
                 names Polymarket), or the wallet itself;
      mint_own   pUSD minted to the wallet whose receipt shows no payer other than the wallet (its own money wrapped);
                 a mint paid by somebody else counts, with that payer as sender (`mint_payer`: tx -> payer from col_41);
      mint_unread  a mint whose receipt was not read: the caller treats the read as missing;
      dust       under MIN_INFLOW_USD.
    A kept row is [ts, "I", None, sender, usdc, None, None, tx] (the side field holds the sender).
    Also returns the earliest transfer of any kind before t: before its first row a wallet holds no position, so for the
    age of R1 any transfer is funding."""
    rows, earliest, drop = [], None, {}
    mint_payer = mint_payer or {}
    for r in item:
        if r["ts"] >= t:
            continue
        earliest = r["ts"] if earliest is None else min(earliest, r["ts"])
        why, sender = None, r["from"]
        if r["tx"] in d_txs:
            why = "dep_row"
        elif r["ts"] in busy_ts:
            why = "same_second"
        elif sender == ZERO:
            if r["tx"] not in mint_payer:
                why = "mint_unread"
            else:
                sender = mint_payer[r["tx"]]
                if sender is None or sender == wallet or sender in infra:
                    why = "mint_own"
        elif sender in infra or sender == wallet:
            why = "polymarket"
        if why is None and r["value"] / 1e6 < MIN_INFLOW_USD:
            why = "dust"
        if why:
            drop[why] = drop.get(why, 0) + 1; continue
        rows.append([r["ts"], "I", None, sender, r["value"] / 1e6, None, None, r["tx"]])
    return rows, earliest, drop


def _selftest():
    C, O = "0xmarket", "0xother"
    T = 1_000_000
    rows = [[T - 100, "D", None, None, 40000.0, None, None, "0xdep"],
            [T - 20, "T", C, "BUY", 900.0, 0.05, 0, None],              # small fill before the entry: same market, not "another market"
            [T, "T", C, "BUY", 2000.0, 0.06, 0, None],                  # the entry fill
            [T + 60, "T", C, "BUY", 5000.0, 0.10, 0, None],
            [T + 120, "T", C, "SELL", 1000.0, 0.12, 0, None],
            [T + 300, "T", C, "BUY", 4000.0, 0.30, 0, None],            # net 900+2000+5000-1000+4000 = 10900 >= 10000
            [T + 400, "T", C, "BUY", 5000.0, 0.31, 0, None]]
    w = watch(rows, T, C, 0, 2000.0)
    assert w["view"]["prior_other_markets"] == 0 and w["view"]["dep_24h"] == 40000.0 and w["view"]["prior_trades"] == 1, w["view"]
    assert w["flags"] == {"thin": True, "fresh": True, "dormant": False, "ooc": False}, w["flags"]
    assert w["heavy"] == {"t": T + 300, "price": 0.30, "net_buy": 10900.0, "deposits": 40000.0}, w["heavy"]
    k = classes(w)
    assert k["C1_FRESH_FUNDED_BET"] == (None, None) and k["C7_HEAVY_NEWCOMER"] == (T + 300, 0.30) and k["C2_DORMANT_REACTIVATION"] is None
    # nothing after the alert moment is used: cutting the history there gives the same alert, cutting before gives none
    assert watch(rows[:6], T, C, 0, 2000.0)["heavy"] == w["heavy"] and watch(rows[:5], T, C, 0, 2000.0)["heavy"] is None
    assert classes(watch(rows[:3], T, C, 0, 2000.0))["C1_FRESH_FUNDED_BET"] == (None, None)        # C1 needs nothing after the entry
    # a deposit older than 24 h is not fresh; buying the other side does not count
    old = [[T - 2 * 86400, "D", None, None, 3000.0, None, None, "0x"], [T, "T", C, "BUY", 2000.0, 0.5, 0, None],
           [T + 10, "T", C, "BUY", 20000.0, 0.5, 1, None]]
    wo = watch(old, T, C, 0, 2000.0)
    assert wo["flags"]["fresh"] is False and wo["heavy"] is None and wo["net_buy"] == 2000.0
    assert classes(wo)["C1_FRESH_FUNDED_BET"] is None and classes(wo)["B3_THIN_NOT_FRESH"] == (None, None)
    # dormant: one trade elsewhere 90 days ago, fresh deposit
    dorm = [[T - 90 * 86400, "T", O, "BUY", 50.0, 0.5, 0, None], [T - 3600, "D", None, None, 24000.0, None, None, "0xd"],
            [T, "T", C, "BUY", 13000.0, 0.7, 0, None]]
    wd = watch(dorm, T, C, 0, 13000.0)
    assert wd["flags"]["dormant"] and wd["flags"]["thin"] and classes(wd)["C2_DORMANT_REACTIVATION"] == (None, None)
    assert classes(wd)["C7_HEAVY_NEWCOMER"] == (T, 0.7)                                         # reached by the entry fill itself
    # out of character: 25 trades of 100 USD over ten days, then 5,000 USD
    hist = [[T - 10 * 86400 + i, "T", f"0xm{i}", "BUY", 100.0, 0.5, 0, None] for i in range(25)] + [[T, "T", C, "BUY", 5000.0, 0.4, 0, None]]
    wc = watch(hist, T, C, 0, 5000.0)
    assert wc["flags"] == {"thin": False, "fresh": False, "dormant": False, "ooc": True} and classes(wc)["C3_OUT_OF_CHARACTER"] == (None, None)
    assert watch(hist[:19] + hist[-1:], T, C, 0, 5000.0)["flags"]["ooc"] is False      # 19 earlier trades: not enough history
    busy = [[T - 3 * 3600 + i, "T", f"0xm{i}", "BUY", 8.0, 0.5, 0, None] for i in range(900)] + [[T, "T", C, "BUY", 2400.0, 0.8, 0, None]]
    assert watch(busy, T, C, 0, 2400.0)["flags"]["ooc"] is False                          # 900 trades in three hours are not a character
    bot = [[T - 5000 + i, "T", O, "BUY", 10.0, 0.5, 0, None] for i in range(51)] + [[T, "T", C, "BUY", 1500.0, 0.2, 0, None]]
    assert watch(bot, T, C, 0, 1500.0)["flags"]["thin"] is False and watch(bot[1:], T, C, 0, 1500.0)["flags"]["thin"] is True
    # a wallet never seen before: thin, not fresh (no deposit row), nothing fires but the baseline
    assert classes(watch([[T, "T", C, "BUY", 1500.0, 0.2, 0, None]], T, C, 0, 1500.0))["B3_THIN_NOT_FRESH"] == (None, None)
    assert watch(rows, T, C, 0, 2000.0, rows_before_floor=1000)["flags"]["thin"] is False
    # money received on the chain, with no deposit row: fresh, and not an activity row (age and row count unchanged)
    chain = [[T - 50, "I", None, None, 3000.0, None, None, "0xin"], [T, "T", C, "BUY", 1500.0, 0.2, 0, None]]
    wi = watch(chain, T, C, 0, 1500.0)
    assert wi["flags"]["fresh"] and wi["view"]["rows_before"] == 0 and wi["view"]["first_ts"] is None and classes(wi)["C1_FRESH_FUNDED_BET"]
    assert len(view([[T - 10 - i, "D", None, None, 1.0, None, None, f"0x{i}"] for i in range(5)][::-1], T, C)["deposits_7d"]) == 5   # every deposit kept
    # chain rows: what is funding and what is not
    K, P, M = "0x" + "aa" * 20, "0x" + "cc" * 20, "0x" + "dd" * 20
    item = [{"from": K, "ts": T - 100, "value": 2_500_000_000, "tx": "0xa"},          # a key sends 2,500 USD: funding
            {"from": P, "ts": T - 90, "value": 9_000_000, "tx": "0xb"},               # in the second of a sale: not funding
            {"from": K, "ts": T - 80, "value": 1_000_000, "tx": "0xdep"},             # already a deposit row
            {"from": "0xinfra", "ts": T - 70, "value": 5_000_000, "tx": "0xc"},       # a Polymarket contract
            {"from": ZERO, "ts": T - 60, "value": 7_000_000, "tx": "0xm1"},          # pUSD minted, paid by a third party
            {"from": ZERO, "ts": T - 50, "value": 7_000_000, "tx": "0xm2"},          # pUSD minted from the wallet's own money
            {"from": K, "ts": T - 40, "value": 500_000, "tx": "0xd"},                # 0.50 USD: dust
            {"from": K, "ts": T, "value": 1_000_000, "tx": "0xe"}]                   # not before the entry
    rows, earliest, drop = chain_rows(item, "0xw", T, {"0xdep"}, {"0xinfra"}, busy_ts={T - 90}, mint_payer={"0xm1": M, "0xm2": "0xw"})
    assert [r[7] for r in rows] == ["0xa", "0xm1"] and rows[1][3] == M and rows[0][4] == 2500.0 and earliest == T - 100, rows
    assert drop == {"same_second": 1, "dep_row": 1, "polymarket": 1, "mint_own": 1, "dust": 1}, drop
    assert chain_rows(item[4:5], "0xw", T, set(), set())[2] == {"mint_unread": 1}
    print("asof selftest ok")


if __name__ == "__main__":
    _selftest()
