#!/usr/bin/env python3
"""Post-hoc timing audit. Not a pre-registered test and not a replacement verdict.

The frozen statistic uses lifetime Relay withdrawals. This script asks a different
question: at each comparator shock time T, how many shared recipients and how large
an M statistic are already implied by withdrawals created strictly before T.
"""
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PM = "funxyz|su4gnoxz14"


def shock_by_question():
    shocks = json.loads((ROOT / "data" / "shocks.json").read_text())["markets"]
    return {m["question"]: m for m in shocks}


def withdrawals_before(wallet, cutoff):
    doc = json.loads((ROOT / "data" / "relay" / f"{wallet}.json").read_text())
    out = set()
    for order in doc["orders"]:
        if not (order["user"] == wallet and order["o"] == 137 and order["status"] == "success"
                and order["referrer"] == PM and order["recipient"] != wallet):
            continue
        stamp = datetime.fromisoformat(order["created"].replace("Z", "+00:00"))
        if stamp < cutoff:
            out.add(order["recipient"])
    return out


def overlap(graph):
    holders = defaultdict(set)
    for wallet, recipients in graph.items():
        for recipient in recipients:
            holders[recipient].add(wallet)
    pair = defaultdict(int)
    for wallets in holders.values():
        if len(wallets) < 2:
            continue
        ordered = sorted(wallets)
        for i, left in enumerate(ordered):
            for right in ordered[i + 1:]:
                pair[(left, right)] += 1
    multi = {wallet for (left, right), count in pair.items() if count >= 2 for wallet in (left, right)}
    return len(multi), sum(1 for wallets in holders.values() if len(wallets) >= 2)


def main():
    shocks = shock_by_question()
    known = set((ROOT / "data" / "known_groups.txt").read_text().split())
    primary = json.loads((ROOT / "derived" / "results.json").read_text())["variants"]["primary"]["comparators"]
    rows = []
    for row in primary:
        market = shocks[row["question"]]
        cutoff = datetime.fromtimestamp(market["T"], timezone.utc)
        population = json.loads((ROOT / "data" / "populations" / f'{market["condition"]}.json').read_text())
        wallets = [w for w in population["wallets"] if w not in known]
        graph = {w: withdrawals_before(w, cutoff) for w in wallets}
        graph = {w: recipients for w, recipients in graph.items() if recipients}
        stat_m, shared = overlap(graph)
        rows.append({"question": row["question"], "T_utc": cutoff.isoformat(), "M_before_T": stat_m,
                     "shared_recipients_before_T": shared, "wallets_with_a_pre_T_withdrawal": len(graph),
                     "lifetime_M": row["M"], "lifetime_S1": row["S1"]})
    out = {"label": "POST_HOC_NOT_PREREGISTERED", "rows": rows,
           "all_comparator_M_before_T_zero": all(r["M_before_T"] == 0 for r in rows)}
    dest = ROOT / "derived" / "pre_shock_timing.json"
    dest.write_text(json.dumps(out, indent=1))
    print(json.dumps({"all_zero": out["all_comparator_M_before_T_zero"], "rows": len(rows)}))


if __name__ == "__main__":
    main()
