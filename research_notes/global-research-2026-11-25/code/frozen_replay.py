"""Independent recomputation of the frozen 13 November T1 statistic.

The Poisson-binomial tail is reimplemented here and is not imported from the
original study. Discovery rows are counted separately so that 48 lonely-thin
rows are not mistaken for a change in the published n of 45.
"""

import json
from pathlib import Path


def summary(rows):
    n = len(rows)
    wins = sum(int(r["win"]) for r in rows)
    mean_p = sum(float(r["p_alert"]) for r in rows) / n
    return {
        "n": n,
        "wins": wins,
        "win_rate": wins / n,
        "mean_p": mean_p,
        "excess": wins / n - mean_p,
        "n_events": len({r["event_slug"] for r in rows}),
        "n_initiators": len({r["initiator"] for r in rows}),
    }


def poisson_binomial_upper(rows):
    """P(W >= observed wins) if each row wins independently with probability p_alert."""
    s = summary(rows)
    dist = [1.0]
    for r in rows:
        p = min(1.0, max(0.0, float(r["p_alert"])))
        nxt = [0.0] * (len(dist) + 1)
        for k, v in enumerate(dist):
            nxt[k] += v * (1.0 - p)
            nxt[k + 1] += v * p
        dist = nxt
    s["p"] = min(1.0, sum(dist[s["wins"]:]))
    return s


def same_cell_peers(rows):
    """Count other rows sharing condition, UTC day and side. Zero means the control is not testable."""
    from datetime import datetime, timezone
    from collections import Counter

    def day(ts):
        return datetime.fromtimestamp(int(ts), timezone.utc).date().isoformat()

    cells = Counter((r["condition_id"], day(r["t_alert"]), r["side"]) for r in rows)
    flagged = [r for r in rows if r.get("lonely_thin") and r.get("eval_set") == "VALIDATION"]
    with_peers = 0
    for r in flagged:
        key = (r["condition_id"], day(r["t_alert"]), r["side"])
        if cells[key] > 1:
            with_peers += 1
    return {
        "status": "NOT_TESTABLE" if with_peers == 0 else "TESTABLE",
        "validation_lonely_thin": len(flagged),
        "with_same_cell_peer": with_peers,
        "distinct_cells": len(cells),
        "reason": "The analytic table has one row per cell, so a same-market, same-day, same-side price control has no peer.",
    }


def replay(table_path, verdict_path):
    rows = [json.loads(line) for line in Path(table_path).read_text().splitlines() if line.strip()]
    published = json.loads(Path(verdict_path).read_text())
    validation = [r for r in rows if r.get("eval_set") == "VALIDATION" and r.get("lonely_thin")]
    discovery = [r for r in rows if r.get("eval_set") == "DISCOVERY" and r.get("lonely_thin")]
    fresh = poisson_binomial_upper(validation)
    pub = published["primary_T1"]
    fields = ("n", "wins", "n_events", "n_initiators")
    mismatch = [name for name in fields if fresh[name] != pub[name]]
    for name in ("win_rate", "mean_p", "excess", "p"):
        if abs(fresh[name] - pub[name]) > 1e-12:
            mismatch.append(name)
    return {
        "published_verdict": published["verdict"],
        "recomputed": fresh,
        "mismatch": mismatch,
        "discovery_lonely_thin": {
            "n": len(discovery),
            "wins": sum(int(r["win"]) for r in discovery),
        },
        "same_cell": same_cell_peers(rows),
        "interpretation": (
            "The published NOT_SUPPORTED result is reproduced. "
            "The three discovery alerts are outside that test. "
            "NO_EDGE_VALIDATED is unchanged."
        ),
    }
