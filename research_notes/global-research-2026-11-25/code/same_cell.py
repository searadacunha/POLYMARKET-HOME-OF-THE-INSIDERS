"""Same-market, same-UTC-day, same-outcome buy control. Exploratory, not a new verdict."""

import random


def _mean(values):
    return sum(values) / len(values) if values else None


def _weighted(rows):
    weight = sum(float(row["size"]) for row in rows)
    if weight <= 0:
        return None
    return sum(float(row["price"]) * float(row["size"]) for row in rows) / weight


def alert_delta(alert: dict):
    if not alert.get("complete"):
        return None
    peers = list(alert.get("peers") or [])
    causal = [row for row in peers if int(row["timestamp"]) <= int(alert["t_alert"])]
    flagged = float(alert["p_alert"])
    day_prices = [float(row["price"]) for row in peers]
    causal_prices = [float(row["price"]) for row in causal]
    return {
        "n_day": len(peers),
        "n_causal": len(causal),
        "delta_day": None if not day_prices else _mean(day_prices) - flagged,
        "delta_causal": None if not causal_prices else _mean(causal_prices) - flagged,
        "delta_day_size": None if not peers else _weighted(peers) - flagged,
        "delta_causal_size": None if not causal else _weighted(causal) - flagged,
    }


def bootstrap_mean(values, n_boot=5000, seed=11):
    if len(values) < 2:
        return None
    rnd = random.Random(seed)
    means = []
    size = len(values)
    for _ in range(n_boot):
        draw = [values[rnd.randrange(size)] for _ in range(size)]
        means.append(sum(draw) / size)
    means.sort()
    return [means[int(0.025 * n_boot)], means[min(n_boot - 1, int(0.975 * n_boot))]]


def summarize(payload: dict) -> dict:
    rows = [alert_delta(alert) for alert in payload["alerts"]]
    complete = [row for row in rows if row is not None]
    day = [row["delta_day"] for row in complete if row["n_day"] > 0 and row["delta_day"] is not None]
    causal = [row["delta_causal"] for row in complete if row["n_causal"] > 0 and row["delta_causal"] is not None]
    day_size = [row["delta_day_size"] for row in complete if row["delta_day_size"] is not None]
    causal_size = [row["delta_causal_size"] for row in complete if row["delta_causal_size"] is not None]
    return {
        "n_alerts": len(payload["alerts"]),
        "n_complete": len(complete),
        "n_with_day_peers": len(day),
        "n_with_causal_peers": len(causal),
        "mean_delta_day": _mean(day),
        "mean_delta_causal": _mean(causal),
        "mean_delta_day_size": _mean(day_size),
        "mean_delta_causal_size": _mean(causal_size),
        "ci95_delta_day": bootstrap_mean(day),
        "ci95_delta_causal": bootstrap_mean(causal),
        "ci95_delta_day_size": bootstrap_mean(day_size),
        "day_positive": sum(1 for value in day if value > 0),
        "causal_positive": sum(1 for value in causal if value > 0),
        "note": (
            "delta is the mean price paid by other buyers of the same outcome minus the flagged alert price. "
            "A positive delta means the flagged alert was cheaper than those buys. "
            "This comparison was not in the frozen protocol. It does not change NO_EDGE_VALIDATED."
        ),
    }
