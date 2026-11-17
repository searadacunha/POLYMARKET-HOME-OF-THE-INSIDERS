"""Pre-registered tests. Thresholds are not fit on the sample they judge.

A p-value here is a comparison with a stated null inside the scored hour. It is
not a probability that a trader used non-public information. There is no insider
label in these files, so no false-positive rate for that claim is computed.
"""

from __future__ import annotations

import math
import random
from decimal import Decimal

# Locked before scoring the downloaded 2026-10-11 hours.
SPREAD_SIGNAL_1E4 = 400
SPREAD_CONTROL_1E4 = 200
CONSUMPTION_SIGNAL = Decimal("0.5")
CONSUMPTION_CONTROL = Decimal("0.25")
BURST_MS = 2_000
ISOLATED_MS = 30_000
MIN_ARM = 8
ALPHA = 0.05
FAMILY = 3
PERMUTATIONS = 2_000
SEED = 20261113

HYPOTHESES = ("H1_DEPTH_CONSUMPTION", "H2_WIDE_SPREAD", "H3_PRINT_BURST")


def _log_choose(n: int, k: int) -> float:
    if k < 0 or k > n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def fisher_greater(a: int, b: int, c: int, d: int):
    """One-sided Fisher exact probability of at least ``a`` signal successes."""
    for value in (a, b, c, d):
        if type(value) is not int or value < 0:
            raise ValueError("counts must be non-negative integers")
    n_signal = a + b
    n_move = a + c
    total = a + b + c + d
    if n_signal == 0 or total == n_signal or total == 0:
        return None
    low = max(0, n_signal - (total - n_move))
    high = min(n_signal, n_move)
    logs = [
        _log_choose(n_move, k) + _log_choose(total - n_move, n_signal - k) - _log_choose(total, n_signal)
        for k in range(low, high + 1)
    ]
    pivot = max(logs)
    weights = [math.exp(item - pivot) for item in logs]
    mass = sum(weights)
    return sum(weight for k, weight in zip(range(low, high + 1), weights) if k >= a) / mass


def permutation_p(signal_moves: list[bool], control_moves: list[bool], seed: int = SEED):
    if not signal_moves or not control_moves:
        return None
    observed = (sum(signal_moves) / len(signal_moves)) - (sum(control_moves) / len(control_moves))
    labels = list(signal_moves) + list(control_moves)
    width = len(signal_moves)
    rng = random.Random(seed)
    beat = 0
    for _ in range(PERMUTATIONS):
        rng.shuffle(labels)
        stat = (sum(labels[:width]) / width) - (sum(labels[width:]) / (len(labels) - width))
        if stat >= observed:
            beat += 1
    return (1 + beat) / (1 + PERMUTATIONS)


def _flag(row: dict, name: str) -> bool:
    if not row["eligible_size"] or row["moved"] is None:
        return False
    spread = row["spread_1e4"]
    if name == "H1_DEPTH_CONSUMPTION":
        if row["consumption"] is None or spread is None:
            return False
        return Decimal(row["consumption"]) >= CONSUMPTION_SIGNAL and spread >= SPREAD_CONTROL_1E4
    if name == "H1_CONTROL":
        if row["consumption"] is None or spread is None:
            return False
        return Decimal(row["consumption"]) < CONSUMPTION_CONTROL
    if name == "H2_WIDE_SPREAD":
        return spread is not None and spread >= SPREAD_SIGNAL_1E4
    if name == "H2_CONTROL":
        return spread is not None and spread < SPREAD_CONTROL_1E4
    gap = row["burst_gap_ms"]
    if name == "H3_PRINT_BURST":
        return gap is not None and gap <= BURST_MS
    if name == "H3_CONTROL":
        return gap is None or gap > ISOLATED_MS
    raise ValueError(name)


def _arm(rows: list[dict], hypothesis: str):
    signal_name = hypothesis
    control_name = {
        "H1_DEPTH_CONSUMPTION": "H1_CONTROL",
        "H2_WIDE_SPREAD": "H2_CONTROL",
        "H3_PRINT_BURST": "H3_CONTROL",
    }[hypothesis]
    signal = [row for row in rows if _flag(row, signal_name)]
    control = [row for row in rows if _flag(row, control_name)]
    return signal, control


def _decision(fisher, perm, n_signal: int, n_control: int) -> str:
    if n_signal < MIN_ARM or n_control < MIN_ARM:
        return "UNDERPOWERED"
    if fisher is None or perm is None:
        return "UNDEFINED"
    threshold = ALPHA / FAMILY
    if fisher < threshold and perm < threshold:
        return "PASSES_VALIDATION"
    return "REJECTED"


def funnel(rows: list[dict]) -> dict:
    """Describe how many prints reached a label. This does not change a decision."""
    counts = {}
    for split in ("discovery", "validation"):
        chosen = [row for row in rows if row["split"] == split]
        counts[split] = {
            "prints": len(chosen),
            "prior_book": sum(row["spread_1e4"] is not None for row in chosen),
            "outcome_label": sum(row["moved"] is not None for row in chosen),
            "size_eligible": sum(row["eligible_size"] for row in chosen),
            "eligible_and_labelled": sum(
                row["eligible_size"] and row["moved"] is not None for row in chosen
            ),
        }
    return counts


def evaluate(rows: list[dict]) -> dict:
    """Evaluate the three hypotheses on the validation split only.

    Discovery rows are summarised and are not allowed to change the decision.
    """
    discovery = [row for row in rows if row["split"] == "discovery"]
    validation = [row for row in rows if row["split"] == "validation"]
    if any(row["split"] not in ("discovery", "validation") for row in rows):
        raise ValueError("every scored row needs an explicit temporal split")
    tests = {}
    for hypothesis in HYPOTHESES:
        signal, control = _arm(validation, hypothesis)
        a = sum(1 for row in signal if row["moved"])
        b = len(signal) - a
        c = sum(1 for row in control if row["moved"])
        d = len(control) - c
        fisher = fisher_greater(a, b, c, d) if signal and control else None
        perm = permutation_p([bool(row["moved"]) for row in signal], [bool(row["moved"]) for row in control])
        d_signal, d_control = _arm(discovery, hypothesis)
        tests[hypothesis] = {
            "validation": _counts(signal, control, a, b, c, d, fisher, perm),
            "discovery_counts_not_used": {
                "signal": len(d_signal),
                "control": len(d_control),
                "signal_moves": sum(1 for row in d_signal if row["moved"]),
                "control_moves": sum(1 for row in d_control if row["moved"]),
            },
            "decision": _decision(fisher, perm, len(signal), len(control)),
        }
    passed = [name for name, item in tests.items() if item["decision"] == "PASSES_VALIDATION"]
    return {
        "family": list(HYPOTHESES),
        "alpha": ALPHA,
        "bonferroni_threshold": ALPHA / FAMILY,
        "minimum_arm": MIN_ARM,
        "permutations": PERMUTATIONS,
        "seed": SEED,
        "rows": {"discovery": len(discovery), "validation": len(validation)},
        "funnel": funnel(rows),
        "tests": tests,
        "patterns_passing_validation": passed,
        "insider_probability": None,
        "insider_false_positive_rate": None,
        "note": "No insider label exists in this design. Rejection is the expected outcome when a pattern is not discriminated from its control.",
    }


def _rate(moves: int, total: int):
    if total == 0:
        return None
    return moves / total


def _counts(signal, control, a, b, c, d, fisher, perm) -> dict:
    return {
        "signal": len(signal),
        "control": len(control),
        "signal_moves": a,
        "signal_non_moves": b,
        "control_moves": c,
        "control_non_moves": d,
        "signal_move_rate": _rate(a, len(signal)),
        "control_move_rate": _rate(c, len(control)),
        "base_rate_among_arms": _rate(a + c, len(signal) + len(control)),
        "alert_rate_among_non_moves": _rate(b, b + d),
        "fisher_one_sided": fisher,
        "permutation_one_sided": perm,
    }
