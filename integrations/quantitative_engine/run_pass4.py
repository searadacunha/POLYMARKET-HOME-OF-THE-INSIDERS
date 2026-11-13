"""Fetch public series and score independent detectors. Raw series stay in .local."""

from __future__ import annotations

import json
import sys
import urllib.error
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from population import _get, fetch_prices
from pass4 import (
    HORIZONS,
    assign_splits,
    coverage,
    discovery_threshold,
    evaluate_market,
    family_key,
    lead_hours,
    metrics,
)


def _load_drawn(path: Path) -> list[dict]:
    seen = set()
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row["condition_id"] in seen:
            continue
        seen.add(row["condition_id"])
        row["split"] = "validation_seen" if row["split"] == "validation" else row["split"]
        rows.append(row)
    return rows


def _new_validation(exclude: set[str]) -> list[dict]:
    url = (
        "https://gamma-api.polymarket.com/markets?closed=true&limit=100"
        "&end_date_min=2026-11-01T00:00:00Z&end_date_max=2026-11-14T00:00:00Z"
        "&volume_num_min=5000"
    )
    try:
        payload = _get(url)
    except urllib.error.HTTPError:
        return []
    rows = []
    for market in payload:
        condition = (market.get("conditionId") or "").lower()
        if not condition or condition in exclude:
            continue
        tokens = market.get("clobTokenIds")
        if isinstance(tokens, str):
            tokens = json.loads(tokens)
        if not tokens or not market.get("endDate"):
            continue
        rows.append({
            "condition_id": condition,
            "question": market.get("question") or "",
            "end": market["endDate"],
            "volume": float(market.get("volumeNum") or 0),
            "category": "later",
            "liquidity": "later",
            "split": "validation_new",
            "yes_token": tokens[0],
        })
    return rows


def _series_cache(path: Path) -> dict[str, list]:
    found = {}
    if not path.exists():
        return found
    for line in path.read_text().splitlines():
        if line.strip():
            row = json.loads(line)
            found[row["condition_id"]] = row["series"]
    return found


def _attach(markets: list[dict], cache: dict, handle) -> None:
    for market in markets:
        condition = market["condition_id"]
        if condition not in cache:
            try:
                series = fetch_prices(market["yes_token"], market["end"])
                cache[condition] = [[stamp, price] for stamp, price in series]
            except Exception:
                cache[condition] = []
            handle.write(json.dumps({"condition_id": condition, "series": cache[condition]}) + "\n")
            handle.flush()
        market["series"] = [tuple(pair) for pair in cache[condition]]


def _span_days(series) -> float:
    if len(series) < 2:
        return 0.0
    return max(0.0, (series[-1][0] - series[0][0]) / 86400)


def main(root: Path) -> dict:
    sys.path.insert(0, str(root))
    drawn = _load_drawn(root / ".local" / "population" / "prices.jsonl")
    fresh = _new_validation({row["condition_id"] for row in drawn})
    markets = drawn + fresh
    assign_splits(markets)
    cache_path = root / ".local" / "population" / "series.jsonl"
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache = _series_cache(cache_path)
    with cache_path.open("a") as handle:
        _attach(markets, cache, handle)
    threshold = discovery_threshold(markets)
    report = {
        "move": 0.15,
        "return_threshold_locked_on_discovery": threshold,
        "fixed_return": 0.05,
        "validation_markets_not_used_for_threshold": "end dates from 2026-08-01 through 2026-11-01",
        "new_validation": "closed markets ending 2026-11-01 to 2026-11-14, absent from the draw",
        "splits": {},
    }
    by_split = defaultdict(list)
    for market in markets:
        by_split[market["split"]].append(market)
    for split, group in sorted(by_split.items()):
        coverage_counts = {name: Counter() for name in HORIZONS}
        for market in group:
            for name, seconds in HORIZONS.items():
                coverage_counts[name][coverage(market["series"], seconds)] += 1
        rows = []
        for market in group:
            rows.extend(evaluate_market(market["series"], threshold))
        days = sum(_span_days(market["series"]) for market in group if market["series"])
        horizons = {}
        for name in HORIZONS:
            signal = metrics(rows, name, "signal", 20261113)
            fixed = metrics(rows, name, "fixed", 20261114)
            random_rule = metrics(rows, name, "random", 20261115)
            signal["alerts_per_market_day"] = (signal["alerts"] / days) if days else None
            leads = []
            for market in group:
                value = lead_hours(evaluate_market(market["series"], threshold), market["series"], name)
                if value is not None:
                    leads.append(value)
            leads.sort()
            horizons[name] = {
                "coverage": dict(coverage_counts[name]),
                "locked_return": signal,
                "fixed_5pt": fixed,
                "matched_random": random_rule,
                "median_lead_hours": leads[len(leads) // 2] if leads else None,
            }
        report["splits"][split] = {
            "markets": len(group),
            "families": len({market["family"] for market in group}),
            "horizons": horizons,
        }
    # Lead time only needs discovery series joined back; compute on validation_new if present else calibration.
    return report


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[2]
    body = main(repo)
    destination = repo / "research_notes" / "forensic-engine-2026-11-13" / "data" / "pass4_metrics.json"
    destination.write_text(json.dumps(body, indent=2) + "\n")
    print(destination)
    print(json.dumps({key: value["markets"] for key, value in body["splits"].items()}))
