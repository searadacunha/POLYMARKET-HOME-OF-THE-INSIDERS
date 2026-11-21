"""Replay the frozen timing and forecast comparisons from committed inputs, using only the standard library."""
import argparse
from bisect import bisect_left, bisect_right
from collections import Counter, defaultdict
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
from math import ceil, floor
from pathlib import Path
import random
from statistics import mean
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "monitoring"))
from radar.evaluate import HORIZONS, MAX_MARK_DELAY, PriceHistory

NOBEL = ROOT / "research_notes/nobel-strict-replay-2026-11-20/data"
CHART = NOBEL / "machado_yes_prices_10min.json"
TAPE = NOBEL / "machado_tape.csv"
QUOTES = ROOT / "edge_research/data/quotes.jsonl.gz"
TABLE = ROOT / "research_notes/early-detection-2026-11-13/study/derived/analytic_table.jsonl"
BOUNDARIES = (1751328000, 1767225600)  # 2025-07-01, 2026-01-01 UTC
SPLITS = ("TRAIN", "VALID", "TEST")
RULES = ("LONELY_THIN", "LONELY", "longshot_flow")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def compare_marks(series, emissions):
    times = series.times
    out = Counter()
    for t0 in emissions:
        out["emissions"] += 1
        last = t0 + HORIZONS["24h"] + MAX_MARK_DELAY
        for label, offset in {"entry": 0, **HORIZONS}.items():
            target = t0 + offset
            if target > times[-1]:
                out["right_censored"] += 1
                continue
            pos = bisect_left(times, target)
            stamp = times[pos]
            if stamp > last:
                out["legacy_missing"] += 1
                continue
            out["legacy_selected"] += 1
            if offset <= HORIZONS["1h"]:
                out["early_legacy_selected"] += 1
                out["after_evaluation_clock_at_1h"] += int(stamp > t0 + HORIZONS["1h"])
            mark = series.first(target, last)
            if mark:
                out["bounded_selected"] += 1
            elif stamp > target + MAX_MARK_DELAY:
                out["withheld_late"] += 1
                out["late_" + label] += 1
            else:
                out["withheld_conflicting_first_timestamp"] += 1
            for tolerance in (60, 300):
                out[f"selected_{tolerance}s"] += int(series.first(target, last, tolerance) is not None)
    return out


def timing():
    announcement = int(datetime(2025, 10, 10, 9, tzinfo=timezone.utc).timestamp())
    grid = range(announcement - 43200, announcement, 60)
    chart = PriceHistory(json.loads(CHART.read_text())["history"])
    with TAPE.open() as f:
        tape = PriceHistory((int(r["t"]), r["price"]) for r in csv.DictReader(f) if r["outcome"].lower() == "yes")
    by_token = defaultdict(list)
    invalid = 0
    with gzip.open(QUOTES, "rt") as f:
        for line in f:
            token, received, bid, ask, _, _ = json.loads(line)
            if bid is None or ask is None or not 0 <= bid <= ask <= 1:
                invalid += 1
                continue
            by_token[token].append((received, (bid + ask) / 2))
    quotes = Counter()
    for points in by_token.values():
        series = PriceHistory(points)
        grid_hours = range(ceil(series.times[0] / 3600) * 3600, floor(series.times[-1]) + 1, 3600)
        quotes.update(compare_marks(series, grid_hours))
    return {"nobel_chart": dict(compare_marks(chart, grid)), "nobel_yes_fills": dict(compare_marks(tape, grid)),
            "quote_archive": dict(quotes), "quote_tokens": len(by_token), "invalid_quotes": invalid}


def flag(r, rule):
    if rule == "longshot_flow":
        return r["initiator_cash"] >= 2500 and r["p_alert"] <= 0.35
    return bool(r[rule.lower()])


def clean_split(rows):
    counts = Counter()
    events = defaultdict(list)
    for r in rows:
        counts["source"] += 1
        if r["eval_set"] != "VALIDATION":
            counts["outside_source_validation"] += 1
        elif r["t_alert"] >= r["closed_ts"]:
            counts["at_or_after_close"] += 1
        else:
            events[r["event_id"]].append(r)
    result = {split: [] for split in SPLITS}
    for rows in events.values():
        parts = {bisect_right(BOUNDARIES, r["t_alert"]) for r in rows}
        if len(parts) != 1:
            counts["overlapping_event_rows"] += len(rows)
            continue
        index = parts.pop()
        if index < len(BOUNDARIES) and max(r["closed_ts"] for r in rows) >= BOUNDARIES[index]:
            counts["unresolved_at_split_rows"] += len(rows)
            continue
        result[SPLITS[index]].extend(rows)
    return result, dict(counts)


def quantile(ordered, p):
    x = (len(ordered) - 1) * p
    return ordered[floor(x)] * (1 - x % 1) + ordered[ceil(x)] * (x % 1)


def clustered_interval(deltas):
    """Resample event clusters, retaining the row-weighted Brier estimand."""
    if len(deltas) < 2:
        return None
    pairs = [(sum(v), len(v)) for _, v in sorted(deltas.items())]
    rng = random.Random(20261121)
    samples = []
    for _ in range(5000):
        draw = rng.choices(pairs, k=len(pairs))
        samples.append(sum(s for s, _ in draw) / sum(n for _, n in draw))
    samples.sort()
    tail = 0.05 / (2 * len(RULES))
    return [round(quantile(samples, p), 8) for p in (tail, 1 - tail)]


def matched_residual(rows, rule):
    """Exploratory same-quarter / ten-cent-band comparison, excluding the flagged event."""
    controls = defaultdict(list)
    def cell(r):
        t = datetime.fromtimestamp(r["t_alert"], timezone.utc)
        return t.year, (t.month - 1) // 3, floor(r["p_alert"] * 10)
    for r in rows:
        if not flag(r, rule):
            controls[cell(r)].append((r["event_id"], r["win"] - r["p_alert"]))
    differences = []
    for r in rows:
        if flag(r, rule):
            peers = [v for event, v in controls[cell(r)] if event != r["event_id"]]
            if peers:
                differences.append(r["win"] - r["p_alert"] - mean(peers))
    return {"matched_rows": len(differences), "difference_pp": round(mean(differences) * 100, 4) if differences else None}


def metrics(rows, rule, offset, is_test=False):
    affected = [r for r in rows if flag(r, rule)]
    deltas = defaultdict(list)
    for r in rows:
        p, y = r["p_alert"], r["win"]
        estimate = min(1, max(0, p + offset)) if flag(r, rule) else p
        deltas[r["event_id"]].append((y - p)**2 - (y - estimate)**2)
    values = [d for group in deltas.values() for d in group]
    return {"flagged": len(affected), "flagged_events": len({r["event_id"] for r in affected}),
            "flagged_markets": len({r["condition_id"] for r in affected}),
            "excess_pp": round(100 * mean(r["win"] - r["p_alert"] for r in affected), 4) if affected else None,
            "brier_improvement": round(mean(values), 8) if values else None,
            "simultaneous_ci": clustered_interval(deltas) if is_test else None,
            "matched": matched_residual(rows, rule) if is_test else None}


def forecast():
    rows = [json.loads(line) for line in TABLE.read_text().splitlines()]
    parts, exclusions = clean_split(rows)
    rules = {}
    for rule in RULES:
        fit = [r["win"] - r["p_alert"] for r in parts["TRAIN"] if flag(r, rule)]
        offset = mean(fit) if fit else 0.0
        res = {k: metrics(v, rule, offset, k == "TEST") for k, v in parts.items()}
        ci = res["TEST"]["simultaneous_ci"]
        passed = bool(ci and ci[0] > 0 and res["TEST"]["flagged_events"] >= 30
                      and (res["VALID"]["brier_improvement"] or 0) > 0)
        rules[rule] = {"train_offset": round(offset, 8), "passed": passed, **res}
    train_mean = mean(r["win"] for r in parts["TRAIN"])
    splits = {k: {"rows": len(v), "events": len({r["event_id"] for r in v}),
                  "markets": len({r["condition_id"] for r in v}),
                  "market_brier": round(mean((r["win"] - r["p_alert"])**2 for r in v), 8) if v else None,
                  "half_brier": 0.25 if v else None,
                  "train_prevalence_brier": round(mean((r["win"] - train_mean)**2 for r in v), 8) if v else None}
              for k, v in parts.items()}
    return {"exclusions": exclusions, "splits": splits, "screens": rules, "train_prevalence": round(train_mean, 8)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="compare with the committed result")
    args = parser.parse_args()
    result = {"inputs": {str(p.relative_to(ROOT)): digest(p) for p in (TABLE, QUOTES, CHART, TAPE, HERE / "PROTOCOL.md")},
              "timing": timing(), "forecast": forecast()}
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.check:
        if rendered != (HERE / "results.json").read_text():
            raise SystemExit("result differs from committed results.json")
        print("timing and forecast results reproduced")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
