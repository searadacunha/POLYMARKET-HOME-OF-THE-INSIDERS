"""Offline reconstruction of the four funded bets, every later position, controls and scores. Reads data/raw only.

usage: python3 -I scripts/reconstruct.py [--out results]
Money is pUSD/USDC with 6 decimals, handled as Decimal and written with 6 decimals. Times are UTC.
"""
import csv
import glob
import gzip
import hashlib
import io
import json
import math
import sys
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
from decode import EXCHANGES, erc20, wallet_view  # noqa: E402
from focus import F2020, FOCUS, MISSION_WALLET4, PUSD, USDC, USDC_E  # noqa: E402

NOTE = Path(__file__).resolve().parents[1]
RAW = NOTE / "data/raw"
D0 = Decimal(0)
Q6 = Decimal("0.000001")
TOKEN_NAME = {USDC: "USDC", USDC_E: "USDC.e", PUSD: "pUSD"}
# Payment recipient seen in W2's own transactions after its orders; not a Polymarket contract (see REPORT.md).
FEE_PEERS = {"0xdc9c35bf"}


def load(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def d(x):
    return Decimal(str(x))


def m6(x):
    return str(Decimal(x).quantize(Q6))


def dur(seconds):
    s = int(seconds)
    h, r = divmod(s, 3600)
    mi, se = divmod(r, 60)
    return (f"{h} h " if h else "") + f"{mi} min {se:02d} s"


# ------------------------------------------------------------------ markets
def markets():
    """Full Gamma records for the markets of the four wallets, projected records for the control traders' other markets."""
    out = {}
    for p in sorted(glob.glob(str(RAW / "gamma/markets_*.json.gz"))):
        for m in load(p)["markets"]:
            out[m["conditionId"].lower()] = m
    proj = RAW / "gamma/control_markets_projected.json.gz"
    if proj.exists():
        for m in load(proj)["markets"]:
            out.setdefault(m["conditionId"].lower(), m)
    return out


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


# ------------------------------------------------------------------ position accounting from the activity rows
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


def positions_tokens(rows, mk, since):
    """(condition, token) of every later position where the API rows leave shares: the tokens whose balance is read on chain."""
    out = []
    for p in positions(rows, mk, {}, since=since):
        for t in p["left_tokens"]:
            out.append((p["condition_id"], t))
    return sorted(set(out))


# ------------------------------------------------------------------ focus positions from the receipts
def focus_reconstruction(f, mk):
    raw = load(RAW / f"chain/focus_{f['id']}.json.gz")
    m = mk[f["cid"]]
    outcomes, tokens = json.loads(m["outcomes"]), json.loads(m["clobTokenIds"])
    st = raw["state"]
    den = int(st["payoutDenominator"], 16)
    pay = [Decimal(int(x, 16)) / den for x in st["payoutNumerators"]]
    # The ERC-1155 id of each outcome slot, recomputed on chain from (collateral, condition, index set).
    slot_of = {}
    for key, pid in st["positions"].items():
        idx_set, coll = key.split(":")
        slot_of.setdefault(str(int(pid, 16)), []).append((int(idx_set), coll))
    views = sorted((wallet_view(r, f["wallet"]) for r in raw["receipts"].values()), key=lambda v: v["block"])
    fund = next(v for v in views if v["tx"] == f["funding_tx"])
    credit = [c for c in fund["collateral"] if c["from"] == F2020 and c["to"] == f["wallet"]]
    assert len(credit) == 1, "the funding receipt must hold exactly one f2020 credit to the wallet"
    credit = credit[0]
    ops, bal = [], defaultdict(lambda: D0)
    for v in views:
        tok_moves = [t for t in v["tokens"] if t["token_id"] in tokens]
        for x in v["fills"]:
            if x["token_id"] not in tokens:
                continue
            i = tokens.index(x["token_id"])
            sign = 1 if x["side"] == "BUY" else -1
            bal[x["token_id"]] += sign * x["shares"]
            net_cash = -(x["cash"] + x["fee"]) if x["side"] == "BUY" else x["cash"] - x["fee"]
            ops.append({"time": iso(v["ts"]), "ts": v["ts"], "block": v["block"], "tx": v["tx"], "op": x["side"], "role": x["role"],
                        "exchange": EXCHANGES[x["exchange"]], "outcome": outcomes[i], "token_id": x["token_id"],
                        "shares": x["shares"], "price": x["cash"] / x["shares"], "gross_cash": x["cash"], "fee": x["fee"],
                        "net_cash": net_cash, "position_after": bal[x["token_id"]]})
        if not v["fills"] and tok_moves:  # redemption: tokens leave the wallet, collateral arrives in the same receipt
            paid = sum((c["amount"] for c in v["collateral"] if c["to"] == f["wallet"]), D0)
            for t in tok_moves:
                if t["from"] == f["wallet"] and t["shares"] > 0:
                    bal[t["token_id"]] -= t["shares"]
                    i = tokens.index(t["token_id"])
                    ops.append({"time": iso(v["ts"]), "ts": v["ts"], "block": v["block"], "tx": v["tx"], "op": "REDEEM", "role": "",
                                "exchange": t["to"], "outcome": outcomes[i], "token_id": t["token_id"], "shares": t["shares"],
                                "price": pay[i], "gross_cash": paid, "fee": D0, "net_cash": paid, "position_after": bal[t["token_id"]]})
    # Cross-check every running position against the on-chain balanceOf reads at the same blocks.
    for tok, by_block in st["token_balances"].items():
        for o in ops:
            if o["token_id"] == tok and str(o["block"]) in by_block:
                chain_bal = Decimal(int(by_block[str(o["block"])], 16)) / 10**6
                assert chain_bal == o["position_after"], f"{f['id']} balance mismatch at block {o['block']}"
    first = next(o for o in ops if o["op"] == "BUY")
    assert first["tx"] == f["bet_tx"], f"{f['id']}: first buy is not the mission's bet transaction"
    tok = first["token_id"]
    idx = tokens.index(tok)
    slot = slot_of.get(tok, [])
    assert any(s[0] == 1 << idx for s in slot), f"{f['id']}: token id does not derive from outcome slot {idx}"
    res = raw["state"]["resolution_logs"]
    assert len(res) == 1, "exactly one ConditionResolution log expected"
    res = res[0]
    assert res["topics"][3].lower() == m["questionID"].lower(), "resolution questionId differs from Gamma"
    left = {t: b for t, b in bal.items() if b > 0}
    settle = sum((b * pay[tokens.index(t)] for t, b in left.items()), D0)
    cash = sum((o["net_cash"] for o in ops), D0)
    buys = [o for o in ops if o["op"] == "BUY"]
    # First lot alone, first in first out: the shares of the mission's transaction and what became of them.
    lot = first["shares"]
    lot_cash = first["net_cash"]
    remaining = lot
    for o in ops:
        if o is first or o["token_id"] != tok or remaining <= 0:
            continue
        if o["op"] == "SELL":
            take = min(remaining, o["shares"])
            lot_cash += o["net_cash"] * take / o["shares"]
            remaining -= take
        elif o["op"] == "REDEEM":
            take = min(remaining, o["shares"])
            lot_cash += take * o["price"]
            remaining -= take
    lot_cash += remaining * pay[idx]
    balances = {k: {TOKEN_NAME[t]: Decimal(int(v, 16)) / 10**6 for t, v in b["values"].items()} | {"block": b["block"]}
                for k, b in raw["balances"].items()}
    before = sum((v for k, v in balances["before_first_trade"].items() if k != "block"), D0)
    return {
        "focus": f, "market": m, "outcomes": outcomes, "tokens": tokens, "payouts": pay, "ops": ops,
        "funding": {"tx": f["funding_tx"], "log_index": credit["log_index"], "block": fund["block"], "time": iso(fund["ts"]),
                    "ts": fund["ts"], "token": TOKEN_NAME[credit["token"]], "amount": credit["amount"]},
        "first": first, "outcome_bought": outcomes[idx], "outcome_won": outcomes[pay.index(1)] if 1 in pay else "",
        "direction_correct": pay[idx] == 1, "resolution_tx": res["transactionHash"], "resolution_block": int(res["blockNumber"], 16),
        "oracle": "0x" + res["topics"][2][-40:], "question_id": res["topics"][3],
        "capital": sum((-o["net_cash"] for o in buys), D0), "shares_bought": sum((o["shares"] for o in buys), D0),
        "fees": sum((o["fee"] for o in ops), D0), "sales": sum((o["net_cash"] for o in ops if o["op"] == "SELL"), D0),
        "redemptions": sum((o["net_cash"] for o in ops if o["op"] == "REDEEM"), D0),
        "unredeemed_value": settle, "left_shares": sum(left.values(), D0), "net_pnl": cash + settle,
        "first_lot_pnl": lot_cash, "balances": balances, "balance_before_first_trade": before,
        "wrap": [{"tx": v["tx"], "time": iso(v["ts"]), "moves": [(TOKEN_NAME.get(c["token"], c["token"]), c["from"], c["to"], c["amount"])
                                                                  for c in v["collateral"]]}
                 for v in views if fund["block"] < v["block"] < first["block"] and v["collateral"] and not v["fills"]],
    }


# ------------------------------------------------------------------ BTC context
class Klines:
    def __init__(self):
        raw = load(RAW / "external/binance_btcusdt_1m_20260917_20261121.json.gz")["rows"]
        self.t = [r[0] for r in raw]
        self.open = {r[0]: d(r[1]) for r in raw}
        self.close = {r[0]: d(r[2]) for r in raw}

    def move(self, start, ts):
        """Binance BTCUSDT change from the open of the window's first minute to the close of the minute before `ts`."""
        if start not in self.open:
            return None
        k = (ts // 60) * 60 - 60
        if k < start:
            return D0 if ts - start < 60 else None
        return self.close.get(k, None) - self.open[start] if k in self.close else None


def second_prices(f):
    raw = load(RAW / f"external/binance_btcusdt_1s_{f['window_start']}.json.gz")["rows"]
    return {r[0] // 1000: (d(r[1]), d(r[4])) for r in raw}


# ------------------------------------------------------------------ METAR
def metar_rows():
    text = load(RAW / "external/iem_metar_rkpk_20260925_27.json.gz")["csv"]
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        if r["tmpc"] in ("M", ""):
            continue
        ts = int(datetime.strptime(r["valid"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc).timestamp())
        rows.append({"ts": ts, "utc": r["valid"], "kst": datetime.fromtimestamp(ts + 9 * 3600, timezone.utc).strftime("%Y-%m-%d %H:%M"),
                     "tmpc": d(r["tmpc"]), "metar": r["metar"]})
    return rows


# ------------------------------------------------------------------ calibration
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


def calibration_main_side(pos):
    """First version of the test, kept for comparison: the side with the larger buy notional and its average price.
    Biased when a trader adds to a side after it moved, which is why `calibration` replaced it."""
    alt = [{**p, "first_buy_price": p["main_avg_price"], "first_buy_won": p["main_won"]} for p in pos if p["main_avg_price"] is not None]
    return calibration(alt)


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


def ledger_series(f):
    """Collateral balance after every stablecoin transfer, from the opening balance read on chain; checked against the closing read."""
    raw = load(RAW / f"chain/ledger_{f['id']}.json.gz")
    w = f["wallet"]
    bal = {t: Decimal(int(v, 16)) / 10**6 for t, v in raw["opening_balances"]["values"].items()}
    events = []
    seen = set()
    for l in raw["logs_in"] + raw["logs_out"]:
        key = (l["transactionHash"], l["logIndex"])
        if key in seen or l.get("removed"):
            continue
        seen.add(key)
        x = erc20(l)
        if x:
            events.append((int(l["blockNumber"], 16), int(l["logIndex"], 16), l["transactionHash"], x))
    events.sort()
    series, peers = [], defaultdict(lambda: D0)
    for blk, li, tx, x in events:
        sign = 1 if x["to"] == w else -1
        if x["to"] == w and x["from"] == w:
            sign = 0
        bal[x["token"]] += sign * x["amount"]
        other = x["from"] if sign > 0 else x["to"]
        peers[(TOKEN_NAME[x["token"]], "in" if sign > 0 else "out", other)] += x["amount"]
        series.append((blk, tx, sum(bal.values(), D0)))
    closing = {t: Decimal(int(v, 16)) / 10**6 for t, v in raw["closing_balances"]["values"].items()}
    return {"opening": raw["opening_balances"], "closing_read": closing, "closing_replayed": dict(bal),
            "balanced": all(closing[t] == bal[t] for t in closing), "series": series, "peers": peers,
            "peer_has_code": raw["peer_has_code"], "from_block": raw["from_block"], "to_block": raw["to_block"]}


# ------------------------------------------------------------------ controls
def control_metrics(mk, payouts):
    out = []
    for f in FOCUS:
        raw = load(RAW / f"controls/control_activity_{f['id']}.json.gz")
        for w, c in raw["controls"].items():
            # A capped history is complete only up to its last row: keep markets first bought a day before that.
            until = None if c["complete"] else max(r["timestamp"] for r in c["rows"]) - 86400
            pos = positions(c["rows"], mk, payouts, since=f["funding_ts"], until=until)
            cal = calibration(event_dedupe([p for p in pos if p["status"] != "UNKNOWN_TOKEN"]))
            s = summary(pos)
            out.append({"focus": f["id"], "wallet": w, "complete": c["complete"], "rows": len(c["rows"]), "markets": s.get("markets", 0),
                        "net_pnl": s.get("net_pnl"), "capital": s.get("capital_engaged"), **{"cal_" + k: v for k, v in cal.items()}})
    return out


def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (m6(v) if isinstance(v, Decimal) else v) for k, v in r.items()})


V2_FROM = 1777334400  # 2026-04-28 00:00 UTC: before this day the exchange took fees in shares, so API share counts run high


def lifetime_check(rows, mk, snap):
    """Lifetime PnL from the activity rows up to the user-pnl point PR 110 recorded, against that point."""
    pos = positions([r for r in rows if r["timestamp"] < snap["timestamp"]], mk, {})
    mine = sum((p["net_pnl"] for p in pos), D0)
    ref = d(snap["realized_pnl"]) + d(snap["unrealized_pnl"])
    return {"at": iso(snap["timestamp"]), "reconstructed": m6(mine), "user_pnl_realized_plus_unrealized": m6(ref), "difference": m6(mine - ref),
            "reconstructed_unredeemed_value": m6(sum((p["unredeemed_value"] for p in pos), D0)),
            "of_which_opened_before_2026_04_28": m6(sum((p["unredeemed_value"] for p in pos if p["first_buy"] < V2_FROM), D0))}


def inflow_by(external):
    out = defaultdict(lambda: D0)
    for e in external:
        if e["direction"] == "in":
            out[e["counterparty"]] += e["amount"]
    return out


def account_info(wallet):
    a = load(RAW / "chain/accounts.json.gz")
    r = a["accounts"][wallet]
    kind = "key (no code)" if not r["code_bytes"] else "Safe proxy" if r.get("getOwners") not in (None, "0x") and len(r["getOwners"]) > 130 \
        else "deposit wallet" if r.get("owner") not in (None, "0x") else "contract"
    owners = []
    if kind == "Safe proxy":
        h = r["getOwners"][2:]
        n = int(h[64:128], 16)
        owners = ["0x" + h[128 + 64 * i + 24:192 + 64 * i] for i in range(n)]
    elif kind == "deposit wallet":
        owners = ["0x" + r["owner"][-40:]]
    return {"kind": kind, "owners": owners, "nonce": r["nonce"], "block": a["block"]}


# ------------------------------------------------------------------ main
INFRA = {
    "0x0000000000000000000000000000000000000000": "mint/burn",
    "0xe111180000d2663c0091e4f400237545b87b996b": "CTF Exchange v2", "0xe2222d279d744050d28e00520010520000310f59": "Neg Risk CTF Exchange v2",
    "0xe3333700ca9d93003f00f0f71f8515005f6c00aa": "Exchange v3", PUSD: "pUSD contract", "0x4d97dcd97ec945f40cf65f87097ace5ea0476045": "CTF",
    "0x3a3bd7bb9528e159577f7c2e685cc81a765002e2": "Neg Risk wrapped collateral", "0xd91e80cf2e7be2e162c6513ced06f1dd0da35296": "Neg Risk adapter",
}


def ledger_reconcile(f, rows, L):
    """Split every stablecoin transfer by transaction: API-listed (trades, redemptions, rewards...), conversions, other.
    The API-listed part must equal the cash the API rows report for the same window."""
    raw = load(RAW / f"chain/ledger_{f['id']}.json.gz")
    w = f["wallet"]
    api_tx = defaultdict(set)
    for r in rows:
        if r.get("transaction_hash"):
            api_tx[r["transaction_hash"].lower()].add(r["type"])
    t0 = load(RAW / "chain/ledger_bounds.json.gz")["bounds"][f["id"]]["from_block"]["timestamp"]  # first second of the ledger window
    buckets = defaultdict(lambda: D0)
    external = []
    seen = set()
    for l in raw["logs_in"] + raw["logs_out"]:
        key = (l["transactionHash"], l["logIndex"])
        if key in seen:
            continue
        seen.add(key)
        x = erc20(l)
        tx = l["transactionHash"].lower()
        sign = 1 if x["to"] == w else -1
        other = x["from"] if sign > 0 else x["to"]
        types = api_tx.get(tx, set())
        if types - {"DEPOSIT", "WITHDRAWAL"}:
            buckets["api_listed"] += sign * x["amount"]
        elif other in INFRA or other in ("0xd36ec33c8bed5a9f7b6630855f1533455b98a418", "0xc417fd8e9661c0d2120b64a04bb3278c17e99db1",
                                         "0x03f115b015b210f812829ea076a7643ac80c2c97", "0x1ca8dd7e4b0f8162ff899162cd3b1025f02c177b",
                                         "0xab9a2da3d97a3b10f5cb5a856354e12b57412c1a", "0x115f48dc2a731aa16251c6d6e1befc42f92accc9"):
            buckets["conversion_or_infra"] += sign * x["amount"]
        else:
            buckets["external"] += sign * x["amount"]
            external.append({"block": int(l["blockNumber"], 16), "tx": tx, "token": TOKEN_NAME[x["token"]], "direction": "in" if sign > 0 else "out",
                             "counterparty": other, "counterparty_has_code": raw["peer_has_code"].get(other), "amount": x["amount"]})
    # Cash reported by the API rows inside the same window, every type except deposits/withdrawals (conversions).
    api_cash = D0
    for r in rows:
        if r["timestamp"] < t0 or r["type"] in ("DEPOSIT", "WITHDRAWAL"):
            continue
        u = d(r.get("usdc_size") or 0)
        api_cash += -u if r["type"] == "TRADE" and r["side"] == "BUY" or r["type"] == "SPLIT" else u
    delta = sum(L["closing_read"].values(), D0) - sum(Decimal(int(v, 16)) / 10**6 for v in raw["opening_balances"]["values"].values())
    return {"window_start_block": raw["from_block"], "window_end_block": raw["to_block"], "balance_change": delta,
            "api_listed_onchain": buckets["api_listed"], "api_rows_cash": api_cash, "api_gap": buckets["api_listed"] - api_cash,
            "conversions_and_infra": buckets["conversion_or_infra"], "external_net": buckets["external"],
            "identity_gap": delta - sum(buckets.values(), D0), "external": sorted(external, key=lambda e: (e["block"], e["tx"]))}


def fee_payments(external, small=Decimal("0.10"), min_count=20):
    """Recurring small payments out of the wallet to one counterparty, in transactions the Polymarket API does not list.
    Larger transfers to the same counterparty are reported apart: their purpose is not inferred."""
    by = defaultdict(list)
    for e in external:
        if e["direction"] == "out":
            by[e["counterparty"]].append(e)
    out = []
    for peer, es in sorted(by.items()):
        tiny = [e for e in es if e["amount"] <= small]
        if len(tiny) >= min_count:
            big = [e for e in es if e["amount"] > small]
            out.append({"counterparty": peer, "counterparty_has_code": es[0]["counterparty_has_code"], "small_payments": len(tiny),
                        "small_total": sum((e["amount"] for e in tiny), D0), "small_max": max(e["amount"] for e in tiny),
                        "larger_transfers": len(big), "larger_total": sum((e["amount"] for e in big), D0),
                        "first_block": min(e["block"] for e in es), "last_block": max(e["block"] for e in es)})
    return out


def capital(L, f, fund_ts_block):
    series = L["series"]
    after = [(b, x) for b, _, x in series if b >= fund_ts_block]
    vals = [x for _, x in after]
    return {"at_funding_block": vals[0] if vals else None, "peak": max(vals) if vals else None, "trough": min(vals) if vals else None,
            "closing": sum(L["closing_read"].values(), D0)}


def provenance(f, pr110_rows, ext):
    """Inputs of score A: how often the wallet used the f2020 rail, and its share of the new money in the window."""
    rail = [r for r in pr110_rows if r["wallet"] == f["wallet"] and r["source_address"] == F2020]
    inflow = sum((e["amount"] for e in ext if e["direction"] == "in"), D0)
    f2020_in = sum((e["amount"] for e in ext if e["direction"] == "in" and e["counterparty"] == F2020), D0)
    return {"f2020_receipts_W16_W46": len(rail), "observed_external_inflow": inflow,
            "f2020_share_of_inflow": f2020_in / inflow if inflow else None}


def level_a(i):
    """High when the rail recurs or brings most new money; never Low, because f2020 hides the originator."""
    share = i["f2020_share_of_inflow"]
    return "High" if i["f2020_receipts_W16_W46"] >= 10 or (share is not None and share >= Decimal("0.5")) else "Medium"


def level(flags):
    n = sum(flags.values())
    return "Low" if n == 0 else "Medium" if n == 1 else "High"


def main(argv):
    out = NOTE / "results"
    if "--out" in argv:
        out = Path(argv[argv.index("--out") + 1])
    out.mkdir(parents=True, exist_ok=True)
    mk = markets()
    payouts = load(RAW / "chain/payouts.json.gz")["conditions"]
    hold_raw = load(RAW / "chain/holdings.json.gz")["balances"]
    holdings = defaultdict(dict)
    for k, v in hold_raw.items():
        w, t = k.split(":")
        holdings[w][t] = Decimal(int(v["balance"], 16)) / 10**6
    pr110 = list(csv.DictReader(open(NOTE / "data/inputs/pr110_wallet_funding_slim.csv", encoding="utf-8")))
    prov = json.loads((NOTE / "data/inputs/pr110_provenance.json").read_text(encoding="utf-8"))
    kl = Klines()

    # Funding-to-first-buy delays of every f2020 receipt in PR 110 that was followed by a buy (base rate).
    def ts(s):
        return int(datetime.strptime(s, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())
    delays = sorted(ts(r["first_buy_time"]) - ts(r["funding_time"]) for r in pr110 if r["first_buy_time"] not in ("", "UNKNOWN"))

    focus_rows, ops_rows, pos_rows, wallets_json, ctx = [], [], [], {}, {}
    for f in FOCUS:
        rows = load(RAW / f"activity/{f['wallet']}.json.gz")["rows"]
        rec = focus_reconstruction(f, mk)
        m = rec["market"]
        api_ops = [r for r in rows if (r.get("condition_id") or "").lower() == f["cid"]]
        # The API rows of the focus market must match the decoded receipts one for one (cash to the micro-unit).
        api_cash = sorted(d(r["usdc_size"]) for r in api_ops if r["type"] in ("TRADE", "REDEEM"))
        chain_cash = sorted(abs(o["net_cash"]) for o in rec["ops"])
        assert api_cash == chain_cash, f"{f['id']}: API cash flows differ from the receipts"
        delay = rec["first"]["ts"] - rec["funding"]["ts"]
        pct = sum(1 for x in delays if x <= delay) / len(delays)
        ev = m["events"][0]
        later_ops = [o for o in rec["ops"] if o is not rec["first"]]
        exact = (f"BUY {rec['outcome_bought']} (outcome index {rec['tokens'].index(rec['first']['token_id'])}), "
                 f"{m6(rec['first']['shares'])} shares at {rec['first']['price']:.4f} as {rec['first']['role']}")
        if later_ops:
            exact += "; then " + "; ".join(f"{o['op']} {m6(o['shares'])} {o['outcome']}" + (f" at {o['price']:.2f}" if o["op"] != "REDEEM" else "")
                                          for o in later_ops)
        sold = any(o["op"] == "SELL" for o in rec["ops"])
        # Context at the moment of the first buy.
        c = {"elapsed_s": None}
        if f["kind"] == "btc5m":
            sp = second_prices(f)
            s0, b, e = f["window_start"], rec["first"]["ts"], f["window_start"] + 300
            meta = ev.get("eventMetadata") or {}
            c = {"window_start": iso(s0), "elapsed_s": b - s0, "binance_open_at_start": sp[s0][0], "binance_close_before_buy": sp[b - 1][1],
                 "binance_move_at_buy": sp[b - 1][1] - sp[s0][0], "binance_move_at_end": sp[e - 1][1] - sp[s0][0],
                 "chainlink_price_to_beat": d(meta["priceToBeat"]), "chainlink_final_price": d(meta["finalPrice"]),
                 "chainlink_margin": d(meta["finalPrice"]) - d(meta["priceToBeat"])}
            c["bought_with_visible_move"] = (c["binance_move_at_buy"] < 0) == (rec["outcome_bought"] == "Down") if c["binance_move_at_buy"] else None
        else:
            met = metar_rows()
            day = [r for r in met if "2026-09-26" == r["kst"][:10]]
            before = [r for r in day if r["ts"] <= rec["first"]["ts"]]
            c = {"station": "RKPK (Gimhae Intl, Busan)", "local_day": "2026-09-26 KST (UTC+9)", "observations": len(day),
                 "max_so_far_at_buy": max(r["tmpc"] for r in before), "max_so_far_first_seen_kst": next(r["kst"] for r in before if r["tmpc"] == max(x["tmpc"] for x in before)),
                 "last_obs_before_buy": f"{before[-1]['kst']} KST {before[-1]['tmpc']} C", "day_max": max(r["tmpc"] for r in day),
                 "readings_at_day_max": [r["kst"] for r in day if r["tmpc"] == max(x["tmpc"] for x in day)],
                 "readings_after_buy_max": max(r["tmpc"] for r in day if r["ts"] > rec["first"]["ts"]),
                 "max_without_first_report": max(r["tmpc"] for r in day[1:]), "first_report_kst": day[0]["kst"],
                 "fill_kst": datetime.fromtimestamp(rec["first"]["ts"] + 9 * 3600, timezone.utc).strftime("%H:%M")}
        trades = load(RAW / f"controls/market_trades_{f['id']}.json.gz")["rows"]
        buys = [r for r in trades if r["side"] == "BUY"]
        by = defaultdict(lambda: defaultdict(Decimal))
        for r in buys:
            by[r["proxy_wallet"].lower()][r["outcome"]] += d(r["price"]) * d(r["size"])
        main_side = {w: max(v, key=v.get) for w, v in by.items()}
        near = [r for r in buys if abs(r["timestamp"] - rec["first"]["ts"]) <= 30 and r["outcome"] == rec["outcome_bought"]
                and r["proxy_wallet"].lower() != f["wallet"]]
        other_side = rec["outcomes"][1 - rec["tokens"].index(rec["first"]["token_id"])]
        recent = [d(r["price"]) for r in trades if r["outcome"] == other_side and 0 <= rec["first"]["ts"] - r["timestamp"] <= 600]
        notional = sorted(((sum(v.values()), w) for w, v in by.items()), reverse=True)
        c.update({"market_buyers": len(by), "buyers_main_side_won_share": round(sum(1 for o in main_side.values() if o == rec["outcome_won"]) / len(by), 4),
                  "same_outcome_buys_within_30s": len(near), "same_outcome_wallets_within_30s": len({r["proxy_wallet"] for r in near}),
                  "same_outcome_price_range_30s": [f"{min(d(r['price']) for r in near):.3f}", f"{max(d(r['price']) for r in near):.3f}"] if near else None,
                  "other_outcome_min_price_10min_before": f"{min(recent):.3f}" if recent else None, "other_outcome": other_side,
                  "wallet_notional_rank": next((i + 1 for i, (_, w) in enumerate(notional) if w == f["wallet"]), None),
                  "median_buyer_notional": sorted(x for x, _ in notional)[len(notional) // 2]})
        ctx[f["id"]] = c
        res_word = "WIN" if rec["direction_correct"] else "LOSS"
        focus_rows.append({
            "wallet_id": f["id"], "wallet": f["wallet"], "market": m["question"], "condition_id": f["cid"], "market_slug": m["slug"],
            "event_url": f"https://polymarket.com/event/{ev['slug']}", "outcome_bought": rec["outcome_bought"],
            "token_id": rec["first"]["token_id"], "exact_position": exact, "role_first_fill": rec["first"]["role"],
            "funding_tx": f["funding_tx"], "funding_time": rec["funding"]["time"], "funding_amount": rec["funding"]["amount"],
            "funding_token": rec["funding"]["token"], "bet_tx": f["bet_tx"], "bet_time": rec["first"]["time"],
            "delay_after_funding": dur(delay), "delay_seconds": delay, "delay_percentile_vs_f2020_receipts": round(pct, 3),
            "first_stake_total": -rec["first"]["net_cash"], "first_price": rec["first"]["price"], "first_shares": rec["first"]["shares"],
            "first_fee": rec["first"]["fee"], "capital_engaged": rec["capital"], "shares_bought": rec["shares_bought"],
            "average_price_incl_fees": rec["capital"] / rec["shares_bought"], "fees": rec["fees"], "sales": rec["sales"],
            "redemptions": rec["redemptions"], "unredeemed_value": rec["unredeemed_value"], "net_pnl": rec["net_pnl"],
            "first_lot_pnl": rec["first_lot_pnl"], "outcome_won": rec["outcome_won"], "result": res_word,
            "sold_before_resolution": "YES" if sold else "NO", "resolution_tx": rec["resolution_tx"], "oracle": rec["oracle"],
            "balance_before_first_trade": rec["balance_before_first_trade"],
            "stake_share_of_balance": round(float(-rec["first"]["net_cash"] / rec["balance_before_first_trade"]), 4),
            "funding_share_of_balance": round(float(rec["funding"]["amount"] / rec["balance_before_first_trade"]), 4),
        })
        for o in rec["ops"]:
            ops_rows.append({"wallet_id": f["id"], **{k: o[k] for k in ("time", "block", "tx", "op", "role", "exchange", "outcome", "token_id",
                                                                         "shares", "price", "gross_cash", "fee", "net_cash", "position_after")}})

        # ---------------- later positions (first buy at or after the funding)
        after = positions(rows, mk, payouts, since=f["funding_ts"], chain_bal=holdings.get(f["wallet"], {}))
        before = positions(rows, mk, payouts, until=f["funding_ts"])
        for p in after:
            if p["event_start"] and "up/down" in p["family"]:
                p["elapsed_at_first_buy_s"] = p["first_buy"] - int(datetime.strptime(p["event_start"], "%Y-%m-%dT%H:%M:%SZ")
                                                                    .replace(tzinfo=timezone.utc).timestamp())
            if p["family"] == "BTC up/down 5m" and p["event_start"]:
                s0 = int(datetime.strptime(p["event_start"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc).timestamp())
                mv = kl.move(s0, p["first_buy"])
                p["btc_move_at_first_buy"] = mv
                p["bought_with_visible_move"] = None if not mv else (mv < 0) == (p["main_outcome"] == "Down")
            pos_rows.append({"wallet_id": f["id"], **p, "first_buy": iso(p["first_buy"]), "last_op": iso(p["last_op"]),
                             "main_avg_price": "" if p["main_avg_price"] is None else f"{p['main_avg_price']:.6f}",
                             "main_won": "" if p["main_won"] is None else ("YES" if p["main_won"] else "NO")})
        # Chain vs Gamma agreement on every later market that both resolve.
        disagree = 0
        for p in after:
            ch = payouts.get(p["condition_id"])
            g = mk.get(p["condition_id"])
            if ch and ch.get("numerators") and g and g.get("closed"):
                gp = [d(x) for x in json.loads(g["outcomePrices"])]
                if sorted(gp) == [0, 1] and [Decimal(int(x, 16)) for x in ch["numerators"]] != gp:
                    disagree += 1
        L = ledger_series(f)
        rcn = ledger_reconcile(f, rows, L)
        fees3 = fee_payments(rcn["external"])
        win = [p for p in after if p["first_buy"] < f["funding_ts"] + 30 * 86400]
        cal_after = calibration(event_dedupe(after))
        cal_win = calibration(event_dedupe(win))
        cal_win_main = calibration_main_side(event_dedupe(win))
        btc = [p for p in after if p.get("bought_with_visible_move") is not None]
        a_inputs = provenance(f, pr110, rcn["external"])
        el = sorted(p["elapsed_at_first_buy_s"] for p in after if p.get("elapsed_at_first_buy_s") is not None)
        lo_b, hi_b = rec["ops"][0]["block"], rec["ops"][-1]["block"] + 10
        focus_fee3 = sum((e["amount"] for e in rcn["external"] for x in fees3 if e["counterparty"] == x["counterparty"]
                          and e["direction"] == "out" and e["amount"] <= Decimal("0.10") and lo_b <= e["block"] <= hi_b), D0)
        wallets_json[f["id"]] = {
            "wallet": f["wallet"], "funding_ts": f["funding_ts"], "focus": {k: v for k, v in focus_rows[-1].items()},
            "context": c, "after_funding": summary(after), "before_funding": summary(before),
            "calibration_after": cal_after, "calibration_first_30_days": cal_win, "calibration_main_side_first_30_days": cal_win_main, "calibration_before": calibration(event_dedupe(before)),
            "btc5m_with_visible_move": {"bets": len(btc), "with_move": sum(1 for p in btc if p["bought_with_visible_move"]),
                                        "won_when_with_move": sum(1 for p in btc if p["bought_with_visible_move"] and p["main_won"]),
                                        "won_when_against_move": sum(1 for p in btc if not p["bought_with_visible_move"] and p["main_won"])},
            "median_stake_before": str(sorted(p["cash_out"] for p in before)[len(before) // 2]) if before else None,
            "median_stake_after": str(sorted(p["cash_out"] for p in after)[len(after) // 2]) if after else None,
            "rewards_and_rebates_after": m6(sum((d(r.get("usdc_size") or 0) for r in rows if r["timestamp"] >= f["funding_ts"]
                                                 and r["type"] in ("REWARD", "MAKER_REBATE", "TAKER_REBATE")), D0)),
            "third_party_fee_payments": fees3, "focus_third_party_payments": focus_fee3,
            "updown_elapsed_at_first_buy_s": {"n": len(el), "median": el[len(el) // 2] if el else None,
                                              "share_within_30s": round(sum(1 for x in el if x <= 30) / len(el), 4) if el else None}, "ledger": {k: v for k, v in rcn.items() if k != "external"},
            "ledger_balanced": L["balanced"], "external_transfers": rcn["external"],
            "capital": capital(L, f, rec["funding"]["block"]), "chain_gamma_disagreements": disagree,
            "api_residue_not_on_chain": m6(sum((p["api_left_shares"] - p["left_shares"] for p in after if p["api_left_shares"] > p["left_shares"]), D0)),
            "score_A_inputs": a_inputs, "score_A": level_a(a_inputs),
            "pause_before_funding_s": f["funding_ts"] - max(r["timestamp"] for r in rows if r["timestamp"] < f["funding_ts"]),
            "max_stake_before": m6(max((p["cash_out"] for p in before), default=D0)), "max_stake_after": m6(max((p["cash_out"] for p in after), default=D0)),
            "markets_ge_100_before": sum(1 for p in before if p["cash_out"] >= 100), "markets_ge_100_after": sum(1 for p in after if p["cash_out"] >= 100),
            "lifetime_vs_user_pnl": lifetime_check(rows, mk, prov["user_pnl_snapshot"][f["wallet"]]),
            "chain_gamma_compared": sum(1 for p in after if (payouts.get(p["condition_id"]) or {}).get("numerators") and mk.get(p["condition_id"], {}).get("closed")),
            "ops_seconds": [o["ts"] - rec["first"]["ts"] for o in rec["ops"]],
            "external_inflow_by_counterparty": {k2: m6(v2) for k2, v2 in sorted(inflow_by(rcn["external"]).items())},
            "external_outflow_counterparties": len({e["counterparty"] for e in rcn["external"] if e["direction"] == "out"}),
            "account": account_info(f["wallet"]),
            "pr110_user_pnl_snapshot": prov["user_pnl_snapshot"][f["wallet"]],
            "pr110_sampled_buys_found": sum(1 for b in prov["sampled_buys"][f["wallet"]]
                                            if any(r.get("transaction_hash") == b[1] and r.get("side") == "BUY" for r in rows)),
            "pr110_sampled_buys": len(prov["sampled_buys"][f["wallet"]]),
        }

    # ---------------- controls
    ctrl = control_metrics(mk, payouts)
    pooled = sorted(c["cal_z"] for c in ctrl if c.get("cal_z") is not None)
    for k, wj in wallets_json.items():
        zs = sorted(c["cal_z"] for c in ctrl if c["focus"] == k and c.get("cal_z") is not None)
        z = wj["calibration_first_30_days"].get("z")
        wj["controls"] = {"n": len([c for c in ctrl if c["focus"] == k]), "with_z": len(zs),
                          "z_percentile": None if z is None or not zs else round(sum(1 for x in zs if x <= z) / len(zs), 3),
                          "z_percentile_pooled": None if z is None else round(sum(1 for x in pooled if x <= z) / len(pooled), 3),
                          "z_median": zs[len(zs) // 2] if zs else None, "z_max": zs[-1] if zs else None}
    controls_pooled = {"n": len(pooled), "median": pooled[len(pooled) // 2], "min": pooled[0], "max": pooled[-1],
                       "share_abs_z_ge_2": round(sum(1 for x in pooled if abs(x) >= 2) / len(pooled), 3)}

    # ---------------- scores B and C (rules in REPORT.md)
    for k, wj in wallets_json.items():
        fo = wj["focus"]
        flags_b = {
            "fast_after_funding": fo["delay_percentile_vs_f2020_receipts"] <= 0.10,
            "stake_change_after_funding": bool(wj["median_stake_before"] and wj["median_stake_after"] and
                                               (Decimal(wj["median_stake_after"]) >= 3 * Decimal(wj["median_stake_before"]) or
                                                Decimal(wj["median_stake_after"]) * 3 <= Decimal(wj["median_stake_before"]))),
            "profits_concentrated": (wj["after_funding"].get("top3_share_of_gains") or 0) >= 0.5,
            "focus_stake_majority_of_balance": fo["stake_share_of_balance"] >= 0.5,
        }
        cal = wj["calibration_first_30_days"]
        flags_c = {
            "focus_bet_won_against_visible_information": fo["result"] == "WIN" and wj["context"].get("bought_with_visible_move") is False,
            "calibration_z_ge_2": (cal.get("z") or 0) >= 2,
            "calibration_z_ge_3": (cal.get("z") or 0) >= 3,
            "above_95pct_of_controls": (wj["controls"]["z_percentile"] or 0) >= 0.95 and (cal.get("z") or 0) > 0,
        }
        wj["score_B"], wj["score_B_flags"] = level(flags_b), flags_b
        wj["score_C"], wj["score_C_flags"] = level(flags_c), flags_c

    write_csv(out / "focus_bets.csv", focus_rows, list(focus_rows[0]))
    write_csv(out / "focus_operations.csv", ops_rows, list(ops_rows[0]))
    pf = ["wallet_id", "condition_id", "title", "slug", "family", "first_buy", "last_op", "main_outcome", "main_avg_price", "main_won",
          "sides_bought", "buy_shares", "cash_out", "sales", "redeemed", "merged", "fees", "left_shares", "api_left_shares",
          "unredeemed_value", "net_pnl", "status", "resolution_source", "sold_before_resolution", "n_trades", "elapsed_at_first_buy_s",
          "btc_move_at_first_buy", "bought_with_visible_move"]
    write_csv(out / "positions_after_funding.csv", pos_rows, pf)
    write_csv(out / "controls.csv", ctrl, ["focus", "wallet", "complete", "rows", "markets", "capital", "net_pnl", "cal_n", "cal_wins",
                                           "cal_expected_wins", "cal_win_rate", "cal_mean_price", "cal_excess_wins", "cal_z", "cal_p_two_sided"])
    caps = {}
    for p in sorted(glob.glob(str(RAW / "activity/*.json.gz"))):
        caps[Path(p).name[:10]] = load(p)["captured_utc"]
    bounds = load(RAW / "chain/ledger_bounds.json.gz")["bounds"]
    ctrl_raw = [load(RAW / f"controls/control_activity_{f['id']}.json.gz") for f in FOCUS]
    stamps = sorted(load(Path(x))["captured_utc"] for x in glob.glob(str(RAW / "**/*.json.gz"), recursive=True))
    payload_meta = {"activity_captured_utc": sorted(caps.values()), "first_capture_utc": stamps[0], "last_capture_utc": stamps[-1], "chain_last_block": bounds["W1"]["to_block"]["block"],
                    "chain_last_block_utc": iso(bounds["W1"]["to_block"]["timestamp"]), "payout_conditions": len(payouts),
                    "payout_block": load(RAW / "chain/payouts.json.gz")["block"],
                    "controls_capped": sum(1 for c in ctrl_raw for v in c["controls"].values() if not v["complete"]),
                    "controls_total": sum(len(c["controls"]) for c in ctrl_raw),
                    "ledger_lead_blocks": {f["id"]: wallets_json[f["id"]]["focus"] and
                                           (bounds[f["id"]]["from_block"]["block"]) for f in FOCUS}}
    payload = {"generated_from": "data/raw and data/inputs only", "mission_wallet4_as_given": MISSION_WALLET4, "meta": payload_meta,
               "controls_pooled": controls_pooled,
               "delay_base_rate": {"receipts": len(delays), "rule": "first BUY strictly after each f2020 receipt of PR 110 (W16-W46) that has one",
                                   "quantiles_s": {str(q): delays[int(q * (len(delays) - 1))] for q in (0.1, 0.25, 0.5, 0.75, 0.9)}},
               "wallets": wallets_json}
    (out / "results.json").write_text(json.dumps(payload, indent=1, sort_keys=True, default=lambda x: m6(x) if isinstance(x, Decimal) else str(x)) + "\n",
                                      encoding="utf-8")
    import report  # noqa: E402  the human-readable report is rendered from the same objects
    (out / "REPORT.md").write_text(report.render(payload, focus_rows, ctx), encoding="utf-8")
    print("wrote", len(focus_rows), "focus rows,", len(pos_rows), "later positions,", len(ctrl), "controls to", out)


if __name__ == "__main__":
    main(sys.argv[1:])
