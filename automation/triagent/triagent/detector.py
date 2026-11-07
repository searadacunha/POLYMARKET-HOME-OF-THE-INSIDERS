"""Point-in-time features, selection flags and a leak-free backtest harness.

Flags select wallets worth an investigation. The score is a count of flags, NOT a
calibrated probability of insider trading.
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Callable

DAY = 86400
FLAG_RULES = {
    "NEW_WALLET": "first public Polymarket activity less than 7 days before the trade",
    "FRESH_FUNDING": "last deposit less than 24 h before the trade",
    "FEW_PRIOR_TRADES": "fewer than 5 earlier trades",
    "CONCENTRATED": "trade worth at least half of all deposits made before it",
    "SHARED_FUNDER": "funder also funded another observed account, and is not a high fan-out service",
    "SHARED_DESTINATION": "withdrew to an address another observed account withdrew to (not a service)",
    "COORDINATED_ENTRY": "2+ other new accounts bought the same outcome in the 6 h before",
    "KNOWN_INFRA_REUSE": "wallet or funder appears in an earlier investigation of the repository",
    "LIQUIDITY_SHARE": "trade at least 25% of displayed market liquidity (live only, not point-in-time later)",
}


class LeakError(AssertionError):
    pass


class AsOf:
    """Gives access only to rows strictly before `t`; any later row is a leak."""

    def __init__(self, rows: list[dict], t: int):
        self.t = t
        self.rows = [r for r in rows if int(r.get("timestamp", 0)) < t]

    def check(self, values: list[dict]):
        late = [r for r in values if int(r.get("timestamp", 0)) >= self.t]
        if late:
            raise LeakError(f"{len(late)} rows at or after t={self.t} used")


def features_asof(activity: list[dict], t: int, trade_usdc: float) -> dict:
    view = AsOf(activity, t)
    rows = view.rows
    trades = [r for r in rows if r.get("type") == "TRADE"]
    deposits = [r for r in rows if r.get("type") == "DEPOSIT"]
    view.check(trades + deposits)
    first = min((int(r["timestamp"]) for r in rows), default=None)
    last_dep = max((int(r["timestamp"]) for r in deposits), default=None)
    dep_usdc = sum(float(r.get("usdc_size") or 0) for r in deposits)
    return {
        "t": t, "trade_usdc": round(trade_usdc, 2),
        "account_age_s": (t - first) if first is not None else 0,
        "funding_to_trade_s": (t - last_dep) if last_dep is not None else None,
        "n_trades_before": len(trades),
        "n_markets_before": len({r.get("condition_id") for r in trades}),
        "deposits_usdc_before": round(dep_usdc, 2),
        "position_vs_deposits": round(trade_usdc / dep_usdc, 3) if dep_usdc > 0 else None,
    }


def flags_for(f: dict, *, shared_funder: bool = False, shared_destination: bool = False,
              co_entrants: int = 0, known_reuse: bool = False, liquidity_share: float | None = None) -> list[str]:
    out = []
    if f["account_age_s"] < 7 * DAY:
        out.append("NEW_WALLET")
    if f["funding_to_trade_s"] is not None and f["funding_to_trade_s"] < DAY:
        out.append("FRESH_FUNDING")
    if f["n_trades_before"] < 5:
        out.append("FEW_PRIOR_TRADES")
    if f["position_vs_deposits"] is not None and f["position_vs_deposits"] >= 0.5:
        out.append("CONCENTRATED")
    if shared_funder:
        out.append("SHARED_FUNDER")
    if shared_destination:
        out.append("SHARED_DESTINATION")
    if co_entrants >= 2:
        out.append("COORDINATED_ENTRY")
    if known_reuse:
        out.append("KNOWN_INFRA_REUSE")
    if liquidity_share is not None and liquidity_share >= 0.25:
        out.append("LIQUIDITY_SHARE")
    return out


# ---------------------------------------------------------------- backtest
@dataclass
class Case:
    address: str
    t: int              # decision time: the trade under test
    label: int          # 1 = case from a verified investigation, 0 = control
    event_ts: int       # time the bet resolved or the market moved (for lead time)
    trade_usdc: float


def evaluate(cases: list[Case], activity_for: Callable[[str], list[dict]], split_ts: int,
             thresholds: tuple[int, ...] = (2, 3, 4, 5)) -> dict[str, Any]:
    """Chronological out-of-sample evaluation. The threshold is chosen on cases with t < split_ts
    only, then applied unchanged to t >= split_ts. Features see only data before each case's t."""
    scored = []
    for c in cases:
        f = features_asof(activity_for(c.address), c.t, c.trade_usdc)
        scored.append((c, len(flags_for(f))))
    train = [(c, s) for c, s in scored if c.t < split_ts]
    test = [(c, s) for c, s in scored if c.t >= split_ts]

    def metrics(rows, th):
        tp = sum(1 for c, s in rows if c.label and s >= th)
        fp = sum(1 for c, s in rows if not c.label and s >= th)
        pos = sum(1 for c, _ in rows if c.label)
        neg = len(rows) - pos
        leads = sorted(c.event_ts - c.t for c, s in rows if c.label and s >= th)
        return {"n": len(rows), "positives": pos, "negatives": neg, "tp": tp, "fp": fp,
                "precision": tp / (tp + fp) if tp + fp else None, "recall": tp / pos if pos else None,
                "fp_per_1000": 1000 * fp / neg if neg else None,
                "median_lead_s": leads[len(leads) // 2] if leads else None}

    def f1(m):
        p, r = m["precision"] or 0, m["recall"] or 0
        return 2 * p * r / (p + r) if p + r else 0

    best = max(thresholds, key=lambda th: f1(metrics(train, th)))
    pos_test = sum(1 for c, _ in test if c.label)
    return {"threshold_from_train": best, "configurations_tried": len(thresholds),
            "train": metrics(train, best), "test": metrics(test, best),
            "labels_sufficient": pos_test >= 20 and len(test) - pos_test >= 200,
            "note": "score = number of flags; not a probability. Bonferroni: divide alpha by configurations_tried."}


def placebo(cases: list[Case], activity_for: Callable[[str], list[dict]], shift_days: int = 30,
            seed: int = 7, draws: int = 200) -> dict:
    """Permutation test on positives: is the real decision time more flagged than random shifted times?"""
    rng = random.Random(seed)
    pos = [c for c in cases if c.label]
    if not pos:
        return {"p_value": None, "reason": "no positives"}
    acts = {c.address: activity_for(c.address) for c in pos}
    real = sum(len(flags_for(features_asof(acts[c.address], c.t, c.trade_usdc))) for c in pos)
    hits = 0
    for _ in range(draws):
        total = 0
        for c in pos:
            t = c.t + rng.randint(-shift_days, shift_days) * DAY
            total += len(flags_for(features_asof(acts[c.address], t, c.trade_usdc)))
        hits += total >= real
    return {"real_flag_total": real, "draws": draws, "p_value": (hits + 1) / (draws + 1),
            "mc_se": math.sqrt(((hits + 1) / (draws + 1)) * (1 - (hits + 1) / (draws + 1)) / draws)}
