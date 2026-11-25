"""Costs applied to the same-day price gap. There is no separate signal to trade.

The day-level gap is already the difference between two buy prices. A round trip
still pays the spread. EDGE_VERDICT.md measured 0.1 to 1.9 cents per share before
any edge, on a later and different universe. Those cents are a published toll, not
a new order-book reconstruction. Alert-time depth is not in this repository.
"""

from .same_cell import summarize


def assess(payload: dict, round_trip_low=0.001, round_trip_high=0.019) -> dict:
    summary = summarize(payload)
    point = summary["mean_delta_day"]
    interval = summary["ci95_delta_day"]
    upper = None if interval is None else interval[1]
    return {
        "signal": "same-day price gap of the 45 frozen alerts",
        "point_estimate": point,
        "ci95": interval,
        "upper_clears_high_toll": None if upper is None else upper > round_trip_high,
        "point_is_positive": None if point is None else point > 0,
        "surviving_executable_signal": False,
        "reason": (
            "The day-level interval includes zero, so there is no demonstrated cheapness "
            "to trade. The causal comparison is negative. Alert-time order-book depth is not available. "
            "NO_EDGE_VALIDATED is unchanged."
        ),
        "round_trip_toll_cited": [round_trip_low, round_trip_high],
    }
