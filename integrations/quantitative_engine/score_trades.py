"""Score the four behavior rules on cursor-exhausted tapes only.

Incomplete tapes are counted and then left out of every precision and recall.
A price move is the target. It is not evidence of non-public information.
No evaluation stamp or trade at or after 2026-11-14T00:00:00Z is used.
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from pathlib import Path

from behavior import CONCENTRATION, MIN_CASH, SYNC_CASH, SYNC_WALLETS, SYNC_WINDOW, alerts_at
from pass4 import MOVE, wilson

HORIZONS = {"1h": 3600, "6h": 6 * 3600, "24h": 24 * 3600}
RULES = ("volume", "new_wallet", "sync", "concentration")
# 2026-11-14T00:00:00Z. This pass runs on 2026-11-13 and stops before the next day.
CUTOFF = 1794614400


def _label(series, stamp: int, horizon: int):
    past = None
    future = []
    hit_at = None
    for time_stamp, price in series:
        if time_stamp <= stamp:
            past = price
        elif time_stamp - stamp <= horizon:
            future.append(price)
            if past is not None and hit_at is None and price - past >= MOVE:
                hit_at = time_stamp
    if past is None or past > 0.85 or not future:
        return None, None
    moved = max(future) - past >= MOVE
    lead = ((hit_at - stamp) / 3600) if moved and hit_at is not None else None
    return moved, lead


def _price_signal(series, stamp: int) -> bool | None:
    now = previous = None
    for time_stamp, price in series:
        if time_stamp <= stamp:
            now = price
        if time_stamp <= stamp - 3600:
            previous = price
    if now is None or previous is None:
        return None
    return now - previous >= 0.05


def _median(values: list[float]):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[len(ordered) // 2]


def _block(rows, rule: str, rate: float) -> dict:
    block = {}
    for horizon in HORIZONS:
        usable = [row for row in rows if row["labels"][horizon] is not None]
        alerts = [row for row in usable if row["flags"][rule]]
        moves = [row for row in usable if row["labels"][horizon]]
        hits = [row for row in alerts if row["labels"][horizon]]
        rng = random.Random(20261113)
        random_alerts = [row for row in usable if rng.random() < rate]
        random_hits = [row for row in random_alerts if row["labels"][horizon]]
        price_alerts = [row for row in usable if row["price"]]
        price_hits = [row for row in price_alerts if row["labels"][horizon]]
        leads = [row["leads"][horizon] for row in hits if row["leads"][horizon] is not None]
        block[horizon] = {
            "evaluable": len(usable),
            "alerts": len(alerts),
            "moves": len(moves),
            "hits": len(hits),
            "precision": (len(hits) / len(alerts)) if alerts else None,
            "precision_ci": wilson(len(hits), len(alerts)),
            "recall": (len(hits) / len(moves)) if moves else None,
            "recall_ci": wilson(len(hits), len(moves)),
            "random_alerts": len(random_alerts),
            "random_precision": (len(random_hits) / len(random_alerts)) if random_alerts else None,
            "random_recall": (len(random_hits) / len(moves)) if moves else None,
            "price_rule_alerts": len(price_alerts),
            "price_rule_precision": (len(price_hits) / len(price_alerts)) if price_alerts else None,
            "price_rule_precision_ci": wilson(len(price_hits), len(price_alerts)),
            "price_rule_recall": (len(price_hits) / len(moves)) if moves else None,
            "median_lead_h": _median(leads),
        }
    return block


def _market_level(market_points, rule: str, horizon: str, price: bool = False) -> dict:
    """One count per market. Overlapping stamps must not inflate the sample size."""
    alerts = hits = moves = evaluable = 0
    for points in market_points:
        usable = [point for point in points if point["labels"][horizon] is not None]
        if not usable:
            continue
        evaluable += 1
        if price:
            alerted = [point for point in usable if point["price"]]
        else:
            alerted = [point for point in usable if point["flags"][rule]]
        moved = any(point["labels"][horizon] for point in usable)
        hit = any(point["labels"][horizon] for point in alerted)
        alerts += bool(alerted)
        hits += bool(hit)
        moves += bool(moved)
    return {
        "markets": evaluable,
        "markets_alerting": alerts,
        "markets_moving": moves,
        "markets_hit": hits,
        "precision": (hits / alerts) if alerts else None,
        "precision_ci": wilson(hits, alerts),
        "recall": (hits / moves) if moves else None,
        "recall_ci": wilson(hits, moves),
    }


def score_dir(trade_dir: Path, series_path: Path) -> dict:
    series = {}
    for line in series_path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            kept = [tuple(pair) for pair in row["series"] if pair[0] < CUTOFF]
            series[row["condition_id"]] = kept
    grouped = defaultdict(list)
    by_market = defaultdict(list)
    coverage = defaultdict(lambda: {"complete": 0, "incomplete": 0, "empty": 0})
    markets = []
    scored_markets = defaultdict(int)
    span_days = defaultdict(float)
    alert_points = defaultdict(lambda: defaultdict(int))
    for path in sorted(trade_dir.glob("*.json")):
        body = json.loads(path.read_text())
        split = body.get("split") or "unknown"
        rows = [row for row in (body.get("rows") or []) if row["t"] < CUTOFF]
        entry = {
            "condition_id": body.get("condition_id"),
            "split": split,
            "category": body.get("category"),
            "question": body.get("question"),
            "n": len(rows),
            "complete": bool(body.get("complete")),
            "pages": body.get("pages"),
            "scored": False,
        }
        if not body.get("complete"):
            coverage[split]["incomplete"] += 1
            markets.append(entry)
            continue
        if not rows:
            coverage[split]["empty"] += 1
            markets.append(entry)
            continue
        coverage[split]["complete"] += 1
        market_series = series.get(body["condition_id"]) or []
        if len(market_series) < 2:
            markets.append(entry)
            continue
        stamps = [stamp for stamp, _ in market_series][::6]
        usable_stamps = []
        market_points = []
        for stamp in stamps:
            flags = alerts_at(rows, stamp)
            labels = {}
            leads = {}
            for name, seconds in HORIZONS.items():
                moved, lead = _label(market_series, stamp, seconds)
                labels[name] = moved
                leads[name] = lead
            if all(value is None for value in labels.values()):
                continue
            usable_stamps.append(stamp)
            point = {
                "flags": flags,
                "labels": labels,
                "leads": leads,
                "price": _price_signal(market_series, stamp),
                "stamp": stamp,
            }
            grouped[split].append(point)
            market_points.append(point)
            for rule in RULES:
                if flags[rule]:
                    alert_points[split][rule] += 1
        if not usable_stamps:
            markets.append(entry)
            continue
        entry["scored"] = True
        by_market[split].append(market_points)
        scored_markets[split] += 1
        span_days[split] += max((market_series[-1][0] - market_series[0][0]) / 86400, 1 / 24)
        markets.append(entry)
    discovery_rows = grouped.get("discovery") or []
    discovery_rate = {}
    for rule in RULES:
        fired = [row for row in discovery_rows if row["flags"][rule]]
        discovery_rate[rule] = (len(fired) / len(discovery_rows)) if discovery_rows else 0.0
    report = {
        "complete_only": True,
        "cutoff": "2026-11-14T00:00:00Z",
        "page_cap": 3,
        "taker_only_default": True,
        "period_filter_trusted": False,
        "thresholds": {
            "move": MOVE,
            "min_cash": MIN_CASH,
            "sync_cash": SYNC_CASH,
            "sync_wallets": SYNC_WALLETS,
            "sync_window_s": SYNC_WINDOW,
            "concentration": CONCENTRATION,
            "price_rule_1h_return": 0.05,
        },
        "coverage": {key: dict(value) for key, value in coverage.items()},
        "scored_markets": dict(scored_markets),
        "discovery_alert_rate": discovery_rate,
        "splits": {},
        "market_level": {},
        "markets": markets,
    }
    for split, rows in grouped.items():
        block = {}
        for rule in RULES:
            measured = _block(rows, rule, discovery_rate[rule])
            days = span_days[split]
            measured["alerts_per_market_day"] = (alert_points[split][rule] / days) if days else None
            measured["market_days"] = days
            block[rule] = measured
        report["splits"][split] = block
        level = {}
        points = by_market[split]
        for rule in RULES:
            level[rule] = {horizon: _market_level(points, rule, horizon) for horizon in HORIZONS}
        level["price_rule"] = {horizon: _market_level(points, "volume", horizon, price=True) for horizon in HORIZONS}
        report["market_level"][split] = level
    return report
