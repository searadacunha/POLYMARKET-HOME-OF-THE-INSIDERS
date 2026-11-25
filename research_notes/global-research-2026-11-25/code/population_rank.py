"""Wallet-level Poisson-binomial ranks on the committed ignition table.

The population is the 587 ignition rows, not the exchange. One wallet can have
several rows. Benjamini-Hochberg is applied to the wallet p-values. A rejection
here would still be post hoc relative to the frozen market-level protocol.
"""

import json
from pathlib import Path

from .frozen_replay import poisson_binomial_upper


def bh(p_values, alpha=0.05):
    """Return the set of indexes rejected by Benjamini-Hochberg."""
    order = sorted(range(len(p_values)), key=lambda index: p_values[index])
    cutoff = -1
    size = len(p_values)
    for rank, index in enumerate(order, start=1):
        if p_values[index] <= alpha * rank / size:
            cutoff = rank
    if cutoff < 0:
        return []
    return [order[rank - 1] for rank in range(1, cutoff + 1)]


def rank_table(path: Path) -> dict:
    rows = [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]
    by = {}
    for row in rows:
        by.setdefault(row["initiator"], []).append(row)
    scored = []
    for wallet, group in by.items():
        stat = poisson_binomial_upper(group)
        scored.append({"wallet": wallet, "n": stat["n"], "wins": stat["wins"], "excess": stat["excess"], "p": stat["p"]})
    scored.sort(key=lambda item: (item["p"], item["wallet"]))
    rejected = bh([item["p"] for item in scored])
    return {
        "population": "ignition rows in analytic_table.jsonl",
        "rows": len(rows),
        "wallets": len(scored),
        "rejected_bh_0.05": len(rejected),
        "smallest_p": scored[0]["p"] if scored else None,
        "smallest_p_wallet": scored[0]["wallet"] if scored else None,
        "smallest_p_n": scored[0]["n"] if scored else None,
    }
