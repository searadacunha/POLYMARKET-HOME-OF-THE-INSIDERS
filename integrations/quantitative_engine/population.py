"""Seeded public-market sample for the frozen monitor.

Price series are the last 14 days before each market's end, from the public
data API, then reduced to a 10-minute grid so the monitor's point count is the
one it was written for. Thresholds in phi_monitor are not changed. Raw pages
stay under .local and are not committed.
"""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SEED = 20261113
VOLUME_ORDINARY = (5_000, 50_000)
VOLUME_HIGH = (500_000, None)
PERIODS = (
    ("discovery", "2025-10-01T00:00:00Z", "2026-04-01T00:00:00Z"),
    ("calibration", "2026-04-01T00:00:00Z", "2026-08-01T00:00:00Z"),
    ("validation", "2026-08-01T00:00:00Z", "2026-11-01T00:00:00Z"),
)
TARGET_PER_CELL = 40
PAGES_PER_CELL = 4
PAGE = 100

GEO = ("iran", "israel", "ukraine", "gaza", "maduro", "venezuela", "war", "strike", "nato", "election", "president", "trump")
SPORTS = ("nba", "nfl", "mlb", "nhl", "ufc", "tennis", "soccer", "football", "ballon", "champions league", "world cup")
CRYPTO = ("bitcoin", "ethereum", "crypto", "btc", "eth ")


def category_of(question: str) -> str:
    text = (question or "").lower()
    if any(word in text for word in GEO):
        return "geopolitics"
    if any(word in text for word in SPORTS):
        return "sports"
    if any(word in text for word in CRYPTO):
        return "crypto"
    return "other"


def liquidity_of(volume: float) -> str:
    if volume >= VOLUME_HIGH[0]:
        return "high"
    if volume < VOLUME_ORDINARY[1]:
        return "ordinary"
    return "mid"


def split_of(end_iso: str) -> str:
    if end_iso < PERIODS[1][1] and end_iso >= PERIODS[0][1]:
        return "calibration"
    if end_iso >= PERIODS[2][1]:
        return "validation"
    if end_iso < "2026-04-01T00:00:00Z":
        return "discovery"
    return "calibration"


def sample_frame(frame: list[dict], per_cell: int = TARGET_PER_CELL, seed: int = SEED) -> list[dict]:
    """Stratify by split, category and liquidity. The seed fixes the draw."""
    rng = random.Random(seed)
    groups = {}
    for row in frame:
        groups.setdefault((row["split"], row["category"], row["liquidity"]), []).append(row)
    chosen = []
    for key in sorted(groups):
        rows = groups[key][:]
        rng.shuffle(rows)
        chosen.extend(rows[:per_cell])
    chosen.sort(key=lambda row: (row["end"], row["condition_id"]))
    return chosen


def to_ten_minute(points: list[tuple[int, float]]) -> list[tuple[int, float]]:
    buckets = {}
    for stamp, price in points:
        buckets[int(stamp) - int(stamp) % 600] = float(price)
    return sorted(buckets.items())


def _get(url: str, pause: float = 0.12):
    time.sleep(pause)
    request = urllib.request.Request(url, headers={"User-Agent": "research-client/1.0", "Accept": "application/json"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=40) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 429 and attempt < 3:
                time.sleep(2.0 * (attempt + 1))
                continue
            raise
    raise RuntimeError(url)


def fetch_frame() -> list[dict]:
    """Public Gamma pages. This is the sampling frame, not yet the analysis sample."""
    frame = []
    seen = set()
    bands = (("ordinary", 5_000, 50_000), ("mid", 50_000, 500_000), ("high", 500_000, None))
    for split, start, end in PERIODS:
        for liquidity, low, high in bands:
            for page in range(PAGES_PER_CELL):
                url = (
                    "https://gamma-api.polymarket.com/markets?closed=true&limit="
                    f"{PAGE}&offset={page * PAGE}&volume_num_min={low}&end_date_min={start}&end_date_max={end}"
                )
                if high is not None:
                    url += f"&volume_num_max={high}"
                try:
                    rows = _get(url)
                except urllib.error.HTTPError:
                    break
                if not rows:
                    break
                for market in rows:
                    condition = (market.get("conditionId") or "").lower()
                    if not condition or condition in seen:
                        continue
                    tokens = market.get("clobTokenIds")
                    if isinstance(tokens, str):
                        tokens = json.loads(tokens)
                    if not tokens:
                        continue
                    volume = float(market.get("volumeNum") or 0)
                    end_iso = market.get("endDate") or ""
                    question = market.get("question") or ""
                    seen.add(condition)
                    frame.append({
                        "condition_id": condition,
                        "question": question,
                        "end": end_iso,
                        "volume": volume,
                        "category": category_of(question),
                        "liquidity": liquidity_of(volume) if liquidity != "high" else "high",
                        "split": split,
                        "yes_token": tokens[0],
                    })
    return frame


def fetch_prices(token: str, end_iso: str) -> list[tuple[int, float]]:
    end = int(datetime.fromisoformat(end_iso.replace("Z", "+00:00")).timestamp())
    start = end - 14 * 86400
    url = (
        "https://data-api.polymarket.com/v2/prices-history?tokenId="
        f"{token}&start={start}&end={end}&bucketSize=60"
    )
    payload = _get(url)
    points = []
    for row in payload.get("data") or []:
        if row.get("price") is None or row.get("timestamp") is None:
            continue
        points.append((int(row["timestamp"]), float(row["price"])))
    return to_ten_minute(points)


def fetch_window(condition: str, start: int, end: int, page_cap: int = 8) -> tuple[list[tuple], bool]:
    """Newest-first trade walk, stopped at `start` or at the page cap."""
    cursor = None
    rows = []
    complete = False
    for _ in range(page_cap):
        url = f"https://data-api.polymarket.com/v2/trades?condition={condition}&limit=1000"
        if cursor:
            url += "&cursor=" + urllib.parse.quote(cursor)
        payload = _get(url, pause=0.15)
        data = payload.get("data") or []
        if not data:
            complete = True
            break
        for row in data:
            stamp = int(row.get("timestamp") or 0)
            if stamp < start:
                complete = True
                continue
            if stamp > end:
                continue
            rows.append((
                stamp, str(row.get("proxy_wallet") or "").lower(), row.get("side"),
                row.get("outcome"), float(row.get("size") or 0), float(row.get("price") or 0),
            ))
        if complete:
            break
        cursor = (payload.get("pagination") or {}).get("next_cursor")
        if not cursor:
            complete = True
            break
    return rows, complete


def score_series(series, tape_rows):
    """Apply the frozen monitor and the pre-registered simple rules to one series.

    `tape_rows` may be empty. Rules that need trades are then unevaluable, not negative.
    """
    from monitoring.phi_monitor import ignition, tapefeat
    yes = ignition.first_ignition(series, "YES")
    no = ignition.first_ignition(series, "NO")
    chosen = yes or no
    out = {
        "yes_ignition": yes is not None,
        "no_ignition": no is not None,
        "monitor": "NO_IGNITION" if chosen is None else "NO_TAPE",
        "simple_large_low": None,
        "simple_volume_spike": None,
    }
    if chosen is None or not tape_rows:
        return out
    side = chosen["side"]
    features, why = tapefeat.alert_features(tape_rows, side, chosen["base"], chosen["t0"], chosen["t1"])
    if features is None:
        out["monitor"] = "NO_ALERT"
        out["feature_reason"] = why
        return out
    lonely = features["share15"] >= tapefeat.LONELY_SHARE
    out["monitor"] = "LONELY_SHARE" if lonely else "NO_ALERT"
    out["share15"] = features["share15"]
    out["n_buyers15"] = features["n_buyers15"]
    out["t_first"] = features["t_first"]
    out["t_alert"] = features["t_alert"]
    out["base"] = chosen["base"]
    token = "Yes" if side == "YES" else "No"
    window = [row for row in tape_rows if features["t_first"] <= row[0] <= features["t_first"] + 900 and row[2] == "BUY" and row[3] == token]
    out["simple_large_low"] = any(row[5] <= 0.25 and row[4] * row[5] >= 5000 for row in window)
    prior = [row for row in tape_rows if chosen["t0"] - 6 * 3600 <= row[0] < features["t_first"]]
    buckets = {}
    for row in prior:
        if row[3] != token or row[2] != "BUY":
            continue
        bucket = row[0] - row[0] % 600
        buckets[bucket] = buckets.get(bucket, 0.0) + row[4] * row[5]
    baseline = sorted(buckets.values())
    median = baseline[len(baseline) // 2] if baseline else 0.0
    burst = sum(row[4] * row[5] for row in window)
    out["simple_volume_spike"] = bool(baseline) and burst >= 1000 and burst >= 3 * median
    return out


def main(cache: Path, summary: Path) -> dict:
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    cache.mkdir(parents=True, exist_ok=True)
    frame_path = cache / "frame.json"
    if frame_path.exists():
        frame = json.loads(frame_path.read_text())
    else:
        frame = fetch_frame()
        frame_path.write_text(json.dumps(frame))
    chosen = sample_frame(frame, per_cell=12)
    price_path = cache / "prices.jsonl"
    done = {}
    if price_path.exists():
        for line in price_path.read_text().splitlines():
            if line:
                row = json.loads(line)
                done[row["condition_id"]] = row
    with price_path.open("a") as handle:
        for market in chosen:
            if market["condition_id"] in done:
                continue
            try:
                series = fetch_prices(market["yes_token"], market["end"])
                scored = score_series(series, [])
                row = {**market, "grid_points": len(series), "scored": scored, "price_error": None}
            except Exception as exc:
                row = {**market, "grid_points": 0, "scored": None, "price_error": type(exc).__name__}
            done[market["condition_id"]] = row
            handle.write(json.dumps(row) + "\n")
            handle.flush()
    ignited = [row for row in done.values() if row.get("scored") and (row["scored"]["yes_ignition"] or row["scored"]["no_ignition"])]
    tape_path = cache / "tapes.jsonl"
    taped = {}
    if tape_path.exists():
        for line in tape_path.read_text().splitlines():
            if line:
                row = json.loads(line)
                taped[row["condition_id"]] = row
    with tape_path.open("a") as handle:
        for market in ignited:
            if market["condition_id"] in taped:
                continue
            series = fetch_prices(market["yes_token"], market["end"])
            from monitoring.phi_monitor import ignition
            side = "YES" if market["scored"]["yes_ignition"] else "NO"
            found = ignition.first_ignition(series, side)
            window, complete = fetch_window(market["condition_id"], found["t0"] - 7 * 3600, found["t1"] + 3600)
            scored = score_series(series, window)
            row = {"condition_id": market["condition_id"], "tape_rows": len(window), "tape_complete": complete, "scored": scored}
            taped[market["condition_id"]] = row
            handle.write(json.dumps(row) + "\n")
            handle.flush()
    summary_body = {
        "seed": SEED,
        "frame": len(frame),
        "sampled": len(chosen),
        "priced": sum(1 for row in done.values() if row.get("grid_points")),
        "price_errors": sum(1 for row in done.values() if row.get("price_error")),
        "ignitions": len(ignited),
        "tapes": len(taped),
        "cells": {},
    }
    for row in chosen:
        key = f"{row['split']}|{row['category']}|{row['liquidity']}"
        summary_body["cells"][key] = summary_body["cells"].get(key, 0) + 1
    summary.write_text(json.dumps(summary_body, indent=2) + "\n")
    return summary_body


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    print(json.dumps(main(root / ".local" / "population", root / ".local" / "population" / "summary.json"), indent=2))
