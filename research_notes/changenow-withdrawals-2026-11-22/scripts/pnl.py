"""Offline accounting of a wallet's bets from Polymarket's public activity rows: per market and before a given time.

The per-market engine (`positions`, `resolved_payouts`, `calibration`, `event_dedupe`, `summary`, `family`, `d`, `m6`)
is copied unchanged from PR 111, research_notes/f2020-bet-reconstruction-2026-11-22/scripts/reconstruct.py at commit
58c964b5aa5063d90e4dd7d72dab50d916a81bd7 (sha256 of that file e723c121...e759). Its rules, measured there: a BUY's
usdc_size is price x size plus the fee, a SELL's is net of it, a REDEEM pays its usdc_size and burns the whole token
balance, fees were taken in shares before 2026-04-28. Rows of types REWARD, MAKER_REBATE, TAKER_REBATE, TIP,
DEPOSIT, WITHDRAWAL never enter a market's result.

`before(...)` adds what the mission asks for each withdrawal at time T, without claiming where the withdrawn money
came from: profit realized on markets closed before T, the largest of them, gains closed in the day and the week
before T, and how long before T they closed.
"""
import json
import math
from collections import defaultdict
from datetime import datetime
from decimal import Decimal

D0 = Decimal(0)
Q6 = Decimal("0.000001")


def d(x):
    return Decimal(str(x))


def m6(x):
    return str(Decimal(x).quantize(Q6))


def family(slug, title):
    s = (slug or "").lower()
    if s.startswith("btc-updown-5m"):
        return "BTC up/down 5m"
    if s.startswith("btc-updown-15m"):
        return "BTC up/down 15m"
    if s.startswith("bitcoin-up-or-down"):
        return "BTC up/down 1h"
    if s.startswith("btc-updown"):
        return "BTC up/down other"
    for k, v in (("eth-", "ETH up/down"), ("ethereum-up-or-down", "ETH up/down"), ("sol-", "SOL up/down"),
                 ("solana-up-or-down", "SOL up/down"), ("xrp-", "XRP up/down"), ("hype-", "HYPE up/down"),
                 ("xau", "Gold up/down"), ("xag", "Silver up/down"), ("highest-temperature", "Weather: highest temperature"),
                 ("lowest-temperature", "Weather: lowest temperature")):
        if s.startswith(k):
            return v
    return "Other"


def resolved_payouts(m, chain):
    """(payout per outcome index, source). Chain payouts win over Gamma; UNKNOWN when neither says the market is final."""
    if chain and chain.get("numerators") and int(chain["denominator"], 16):
        den = int(chain["denominator"], 16)
        return [Decimal(int(x, 16)) / den for x in chain["numerators"]], "chain"
    if m and m.get("closed") and m.get("umaResolutionStatus") == "resolved":
        prices = [d(x) for x in json.loads(m["outcomePrices"])]
        if sorted(prices) == [0, 1]:
            return prices, "gamma"
    return None, "unresolved"


def positions(rows, mk, payouts, since=None, until=None, chain_bal=None):
    """Per market: cash out, cash in, fees, shares per token, settlement. A market enters when its first BUY is in [since, until)."""
    by = defaultdict(list)
    for r in rows:
        cid = (r.get("condition_id") or "").lower()
        if cid and r["type"] in ("TRADE", "REDEEM", "MERGE", "SPLIT", "CONVERSION"):
            by[cid].append(r)
    out = []
    for cid, rs in by.items():
        buys = [r for r in rs if r["type"] == "TRADE" and r["side"] == "BUY"]
        if not buys:
            continue
        first = min(r["timestamp"] for r in buys)
        if since is not None and first < since or until is not None and first >= until:
            continue
        m = mk.get(cid)
        pay, src = resolved_payouts(m, payouts.get(cid))
        outcomes = json.loads(m["outcomes"]) if m else []
        tokens = json.loads(m["clobTokenIds"]) if m else []
        held = defaultdict(lambda: D0)
        bought = defaultdict(lambda: [D0, D0])  # token -> [shares, cash excluding fee]
        cash_out = cash_in = fees = redeemed = sold = merged = D0
        for r in sorted(rs, key=lambda r: (r["timestamp"], r["type"])):
            size, usdc = d(r.get("size") or 0), d(r.get("usdc_size") or 0)
            tok = str(r.get("token_id") or "")
            if r["type"] == "TRADE":
                gross = (d(r["price"]) * size)
                if r["side"] == "BUY":
                    held[tok] += size
                    bought[tok][0] += size
                    bought[tok][1] += gross
                    cash_out += usdc
                    fees += max(D0, usdc - gross)
                else:
                    held[tok] -= size
                    cash_in += usdc
                    sold += usdc
                    fees += max(D0, gross - usdc)
            elif r["type"] == "REDEEM":
                cash_in += usdc
                redeemed += usdc
                # redeemPositions burns the whole balance of the redeemed slots: the API size can be smaller when a
                # pre-2026-04-28 fee was taken in shares, so a redeemed token is set to zero, never decremented.
                if tok:
                    held[tok] = D0
                else:
                    held.clear()
            elif r["type"] == "MERGE":
                cash_in += usdc
                merged += usdc
                for t in list(held):
                    held[t] -= size
            elif r["type"] == "SPLIT":
                cash_out += usdc
                for t in tokens:
                    held[t] += size
        # Shares left after the recorded operations; tiny negatives are rounding of the API.
        left = {t: s for t, s in held.items() if s > Decimal("0.000001")}
        api_left = sum(left.values(), D0)
        if chain_bal is not None:  # the on-chain balance at the pinned block replaces the API residue when it was read
            left = {t: chain_bal.get(t, s) for t, s in left.items()}
            left = {t: s for t, s in left.items() if s > 0}
        settle = D0
        status = "SETTLED"
        if left:
            if pay is None:
                status = "OPEN"
            else:
                for t, s in left.items():
                    if t in tokens:
                        settle += s * pay[tokens.index(t)]
                    else:
                        status = "UNKNOWN_TOKEN"
                if settle > 0:
                    status = "WON_UNREDEEMED"
        fb = min(buys, key=lambda r: (r["timestamp"], r["transaction_hash"]))
        fb_tok = str(fb.get("token_id") or "")
        fb_idx = tokens.index(fb_tok) if fb_tok in tokens else None
        main = max(bought, key=lambda t: bought[t][1])
        main_idx = tokens.index(main) if main in tokens else None
        main_price = bought[main][1] / bought[main][0] if bought[main][0] else None
        main_won = None if pay is None or main_idx is None else pay[main_idx] == 1
        net = cash_in + settle - cash_out
        out.append({
            "condition_id": cid, "title": (m or {}).get("question") or rs[0].get("title", ""), "slug": (m or {}).get("slug") or rs[0].get("slug", ""),
            "event_slug": (((m.get("events") or [{}])[0].get("slug") or m.get("event_slug") or "") if m else rs[0].get("event_slug", "")),
            "family": family((m or {}).get("slug") or rs[0].get("slug"), rs[0].get("title")),
            "first_buy": first, "last_op": max(r["timestamp"] for r in rs),
            "main_outcome": outcomes[main_idx] if main_idx is not None and outcomes else "", "main_avg_price": main_price,
            "main_won": main_won, "sides_bought": len(bought),
            "first_buy_outcome": outcomes[fb_idx] if fb_idx is not None and outcomes else "", "first_buy_price": d(fb["price"]),
            "first_buy_won": None if pay is None or fb_idx is None else pay[fb_idx] == 1, "buy_shares": sum(v[0] for v in bought.values()),
            "cash_out": cash_out, "sales": sold, "redeemed": redeemed, "merged": merged, "fees": fees,
            "unredeemed_value": settle, "left_shares": sum(left.values(), D0), "left_tokens": sorted(left), "api_left_shares": api_left, "status": status, "resolution_source": src,
            "net_pnl": net, "n_trades": sum(1 for r in rs if r["type"] == "TRADE"),
            "sold_before_resolution": any(r["type"] == "TRADE" and r["side"] == "SELL" for r in rs),
            "end_date": (m or {}).get("endDate"), "event_start": (m or {}).get("eventStartTime"),
            "neg_risk": bool((m or {}).get("negRisk")),
        })
    return sorted(out, key=lambda p: (p["first_buy"], p["condition_id"]))


def calibration(pos):
    """One observation per market: the first buy, its price p and whether its outcome won. Later buys, sales and the
    choice of side after a price move do not enter, so under no information beyond the price E[won] = p holds at entry.
    z = (wins - sum p) / sqrt(sum p(1-p))."""
    obs = [(float(p["first_buy_price"]), 1 if p["first_buy_won"] else 0) for p in pos
           if p["first_buy_won"] is not None and 0 < p["first_buy_price"] < 1]
    n = len(obs)
    if not n:
        return {"n": 0}
    exp = sum(p for p, _ in obs)
    var = sum(p * (1 - p) for p, _ in obs)
    wins = sum(y for _, y in obs)
    z = (wins - exp) / math.sqrt(var) if var else None
    return {"n": n, "wins": wins, "expected_wins": round(exp, 3), "win_rate": round(wins / n, 4),
            "mean_price": round(exp / n, 4), "excess_wins": round(wins - exp, 3), "z": None if z is None else round(z, 3),
            "p_two_sided": None if z is None else round(math.erfc(abs(z) / math.sqrt(2)), 4)}


def event_dedupe(pos):
    """Weather brackets of one city-day are one event: keep the bracket bought first, so observations are independent."""
    best = {}
    for p in pos:
        key = p["event_slug"] if p["family"].startswith("Weather") and p["event_slug"] else p["condition_id"]
        if key not in best or (p["first_buy"], p["condition_id"]) < (best[key]["first_buy"], best[key]["condition_id"]):
            best[key] = p
    return list(best.values())


def summary(pos):
    if not pos:
        return {"markets": 0}
    pnl = sorted((p["net_pnl"] for p in pos), reverse=True)
    gains = [x for x in pnl if x > 0]
    res = [p for p in pos if p["status"] != "OPEN"]
    total_gain = sum(gains, D0)
    top = sorted(pos, key=lambda p: p["net_pnl"], reverse=True)
    bottom = sorted(pos, key=lambda p: p["net_pnl"])
    return {
        "markets": len(pos), "trades": sum(p["n_trades"] for p in pos), "open": sum(1 for p in pos if p["status"] == "OPEN"),
        "profitable": sum(1 for p in res if p["net_pnl"] > 0), "unprofitable": sum(1 for p in res if p["net_pnl"] < 0),
        "flat": sum(1 for p in res if p["net_pnl"] == 0),
        "direction_won": sum(1 for p in pos if p["main_won"] is True), "direction_lost": sum(1 for p in pos if p["main_won"] is False),
        "sold_before_resolution": sum(1 for p in pos if p["sold_before_resolution"]),
        "capital_engaged": m6(sum((p["cash_out"] for p in pos), D0)), "fees": m6(sum((p["fees"] for p in pos), D0)),
        "net_pnl": m6(sum((p["net_pnl"] for p in pos), D0)),
        "return_on_capital": None if not sum(p["cash_out"] for p in pos) else
        round(float(sum((p["net_pnl"] for p in pos), D0) / sum((p["cash_out"] for p in pos), D0)), 4),
        "largest_gain": {"pnl": m6(top[0]["net_pnl"]), "title": top[0]["title"], "condition_id": top[0]["condition_id"]},
        "largest_loss": {"pnl": m6(bottom[0]["net_pnl"]), "title": bottom[0]["title"], "condition_id": bottom[0]["condition_id"]},
        "top1_share_of_gains": None if not total_gain else round(float(gains[0] / total_gain), 4),
        "top3_share_of_gains": None if not total_gain else round(float(sum(gains[:3], D0) / total_gain), 4),
        "gain_hhi": None if not total_gain else round(sum(float(g / total_gain) ** 2 for g in gains), 4),
        "longshot_wins": sum(1 for p in pos if p["main_won"] and p["main_avg_price"] is not None and p["main_avg_price"] <= Decimal("0.2")),
        "longshot_bets": sum(1 for p in pos if p["main_avg_price"] is not None and p["main_avg_price"] <= Decimal("0.2")),
        "families": dict(sorted(defaultdict(int, {k: sum(1 for p in pos if p["family"] == k) for k in {p["family"] for p in pos}}).items())),
    }



# ------------------------------------------------------------------ added for the withdrawal study
def closed_ts(m):
    """When Gamma says a market closed (resolution proposed and settled), as epoch seconds, or None."""
    for k in ("closedTime", "umaEndDate", "endDate"):
        v = (m or {}).get(k)
        if v:
            text = v.replace("Z", "+00:00").replace(" ", "T")
            if "+" not in text[10:] and "-" not in text[10:]:
                text += "+00:00"
            try:
                return int(datetime.fromisoformat(text).timestamp())
            except ValueError:
                continue
    return None


def before(rows, mk, T, day=86400):
    """Markets of one wallet as they stood at time T, from the rows strictly before T.
    A market is closed at T when no share is left after those rows (sold, redeemed or merged), or when Gamma's
    close time is before T (then shares left are valued at the resolution payout). Open markets at T are capital at
    risk and enter no realized figure. Returns totals and the closed markets, with the time each one closed."""
    rows = [r for r in rows if r["timestamp"] < T]
    pos = positions(rows, mk, {})
    closed, opened = [], []
    for p in pos:
        m = mk.get(p["condition_id"])
        ct = closed_ts(m)
        resolved = p["resolution_source"] != "unresolved" and ct is not None and ct < T
        exits = [r["timestamp"] for r in rows if (r.get("condition_id") or "").lower() == p["condition_id"]]
        if not p["left_tokens"]:
            p["closed_at"] = max(exits)
            p["realized"] = p["net_pnl"]
            closed.append(p)
        elif resolved:
            p["closed_at"] = ct
            p["realized"] = p["net_pnl"]
            closed.append(p)
        else:
            opened.append(p)
    gains = [p for p in closed if p["realized"] > 0]
    best = max(closed, key=lambda p: (p["realized"], -p["closed_at"]), default=None)
    recent = [p for p in closed if T - day <= p["closed_at"] < T]
    week = [p for p in closed if T - 7 * day <= p["closed_at"] < T]
    last_gain = max((p for p in gains), key=lambda p: p["closed_at"], default=None)
    return dict(markets_closed=len(closed), markets_open=len(opened),
                realized_before=m6(sum((p["realized"] for p in closed), D0)),
                capital_open=m6(sum((p["cash_out"] - p["sales"] - p["redeemed"] - p["merged"] for p in opened), D0)),
                best=None if best is None else dict(title=best["title"], condition_id=best["condition_id"], realized=m6(best["realized"]),
                                                     closed_at=best["closed_at"], outcome=best["main_outcome"], avg_price=None if best["main_avg_price"] is None else float(best["main_avg_price"])),
                realized_day_before=m6(sum((p["realized"] for p in recent), D0)), gains_day_before=m6(sum((p["realized"] for p in recent if p["realized"] > 0), D0)),
                realized_week_before=m6(sum((p["realized"] for p in week), D0)),
                biggest_gain_day_before=None if not [p for p in recent if p["realized"] > 0] else
                dict((lambda p: dict(title=p["title"], condition_id=p["condition_id"], realized=m6(p["realized"]), closed_at=p["closed_at"],
                                     seconds_before=T - p["closed_at"], outcome=p["main_outcome"],
                                     avg_price=None if p["main_avg_price"] is None else float(p["main_avg_price"])))(max((p for p in recent if p["realized"] > 0), key=lambda p: p["realized"]))),
                seconds_since_last_gain=None if last_gain is None else T - last_gain["closed_at"])


def lifetime(rows, mk):
    """Every market of a wallet: realized result of closed ones, open capital, the first-buy calibration test."""
    pos = positions(rows, mk, {})
    now = max((r["timestamp"] for r in rows), default=0) + 1
    state = before(rows, mk, now)
    resolved = [p for p in pos if p["first_buy_won"] is not None and p["status"] != "UNKNOWN_TOKEN"]
    cal = calibration(event_dedupe(resolved))
    s = summary(pos)
    return dict(markets=len(pos), realized=state["realized_before"], markets_closed=state["markets_closed"], markets_open=state["markets_open"],
                best=state["best"], calibration=cal, summary=s,
                rewards=m6(sum((d(r.get("usdc_size") or 0) for r in rows if r["type"] in ("REWARD", "MAKER_REBATE", "TAKER_REBATE")), D0)),
                first_trade=min((r["timestamp"] for r in rows if r["type"] == "TRADE"), default=None),
                last_trade=max((r["timestamp"] for r in rows if r["type"] == "TRADE"), default=None))
