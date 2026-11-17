"""Independent price-move detectors. phi_monitor thresholds are not used.

A missing series is never scored as a quiet market. Thresholds for the two
fitted rules come only from markets whose end date is before 2026-04-01.
The August-November 2026 draw is not used to choose them.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict

HORIZONS = {"1h": 3600, "6h": 6 * 3600, "24h": 24 * 3600, "48h": 48 * 3600}
MOVE = 0.15
FIXED_RETURN = 0.05
CEILING = 0.85


def family_key(question: str) -> str:
    words = []
    token = []
    for char in (question or "").lower():
        if char.isalnum():
            token.append(char)
        elif token:
            words.append("".join(token))
            token = []
    if token:
        words.append("".join(token))
    return " ".join(words[:6])


def assign_splits(markets: list[dict]) -> None:
    """Keep a later market out of validation when its family was already used.

    Markets already examined are not pulled back into discovery, so they cannot
    move the locked threshold.
    """
    families = defaultdict(set)
    for market in markets:
        market["family"] = family_key(market.get("question") or market["condition_id"])
        families[market["family"]].add(market["split"])
    for market in markets:
        if market["split"] != "validation_new":
            continue
        if families[market["family"]] & {"discovery", "calibration", "validation_seen"}:
            market["split"] = "excluded_related"


def _median_gap(series: list[tuple[int, float]]) -> float | None:
    if len(series) < 2:
        return None
    gaps = [series[i][0] - series[i - 1][0] for i in range(1, len(series))]
    gaps.sort()
    return gaps[len(gaps) // 2]


def coverage(series: list[tuple[int, float]] | None, horizon: int) -> str:
    """Classify one market at one horizon. Missing data is not 'no alert'."""
    if not series:
        return "missing"
    span = series[-1][0] - series[0][0]
    if span < horizon:
        return "unusable_window"
    gap = _median_gap(series)
    if gap is None or gap > horizon:
        return "too_sparse"
    evaluable = 0
    for index, (stamp, price) in enumerate(series):
        if price > CEILING:
            continue
        future = next((point for point in series[index + 1:] if point[0] > stamp), None)
        if future and future[0] - stamp <= horizon:
            evaluable += 1
    if evaluable < 3:
        return "too_sparse"
    return "sufficient"


def _price_at_or_before(series, stamp):
    found = None
    for time_stamp, price in series:
        if time_stamp <= stamp:
            found = price
        else:
            break
    return found


def _future_move(series, index, horizon) -> bool | None:
    stamp, price = series[index]
    if price > CEILING:
        return None
    future = [point[1] for point in series[index + 1:] if 0 < point[0] - stamp <= horizon]
    if not future:
        return None
    return max(future) - price >= MOVE


def _feature(series, index) -> float | None:
    stamp, price = series[index]
    previous = _price_at_or_before(series, stamp - 3600)
    if previous is None:
        return None
    return price - previous


def evaluate_market(series, threshold: float):
    """Alerts and labels at each usable time. Features use only the past."""
    rows = []
    if not series:
        return rows
    for index, (stamp, price) in enumerate(series):
        change = _feature(series, index)
        if change is None or price > CEILING:
            continue
        labels = {name: _future_move(series, index, seconds) for name, seconds in HORIZONS.items()}
        if all(value is None for value in labels.values()):
            continue
        rows.append({
            "t": stamp,
            "signal": change >= threshold,
            "fixed": change >= FIXED_RETURN,
            "change": change,
            "labels": labels,
        })
    return rows


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        raise ValueError("no discovery values")
    ordered = sorted(values)
    index = min(len(ordered) - 1, max(0, math.ceil(fraction * len(ordered)) - 1))
    return ordered[index]


def discovery_threshold(markets: list[dict]) -> float:
    values = []
    for market in markets:
        if market.get("split") != "discovery":
            continue
        for index in range(len(market.get("series") or [])):
            change = _feature(market["series"], index)
            if change is not None:
                values.append(change)
    return percentile(values, 0.90)


def wilson(successes: int, total: int) -> list[float] | None:
    if total <= 0:
        return None
    z = 1.96
    proportion = successes / total
    denominator = 1 + z * z / total
    centre = (proportion + z * z / (2 * total)) / denominator
    margin = z * math.sqrt(proportion * (1 - proportion) / total + z * z / (4 * total * total)) / denominator
    return [max(0.0, centre - margin), min(1.0, centre + margin)]


def metrics(rows: list[dict], horizon: str, mode: str, seed: int) -> dict:
    usable = [row for row in rows if row["labels"][horizon] is not None]
    if mode == "signal":
        alerts = [row for row in usable if row["signal"]]
    elif mode == "fixed":
        alerts = [row for row in usable if row["fixed"]]
    elif mode == "random":
        rate = sum(row["signal"] for row in usable) / len(usable) if usable else 0
        rng = random.Random(seed)
        alerts = [row for row in usable if rng.random() < rate]
    else:
        raise ValueError(mode)
    moves = [row for row in usable if row["labels"][horizon]]
    hits = [row for row in alerts if row["labels"][horizon]]
    precision = (len(hits) / len(alerts)) if alerts else None
    recall = (len(hits) / len(moves)) if moves else None
    return {
        "evaluable_times": len(usable),
        "alerts": len(alerts),
        "moves": len(moves),
        "hits": len(hits),
        "precision": precision,
        "precision_ci": wilson(len(hits), len(alerts)),
        "recall": recall,
        "recall_ci": wilson(len(hits), len(moves)),
    }


def lead_hours(rows: list[dict], series, horizon: str) -> float | None:
    delays = []
    window = HORIZONS[horizon]
    for row in rows:
        if not row["signal"] or not row["labels"][horizon]:
            continue
        start_price = _price_at_or_before(series, row["t"])
        for stamp, price in series:
            if row["t"] < stamp <= row["t"] + window and price - start_price >= MOVE:
                delays.append((stamp - row["t"]) / 3600)
                break
    if not delays:
        return None
    delays.sort()
    return delays[len(delays) // 2]
