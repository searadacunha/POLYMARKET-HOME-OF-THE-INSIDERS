#!/usr/bin/env python3
"""Recompute the headline figures from sources/state/pm_pnl2.csv into results/recompute_pm_pnl2.json."""
import csv
import json
import statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
rows = list(csv.DictReader((HERE / "sources/state/pm_pnl2.csv").open()))
pnl = [float(r["total_pnl"]) for r in rows]
# Rounded to the dollar: a few cents either way is a flat account, as in the September 25 count.
rounded = [round(p) for p in pnl]
out = {
    "source": "sources/state/pm_pnl2.csv",
    "accounts": len(rows),
    "total_pnl": round(sum(pnl)),
    "staked_buy_plus_split": round(sum(float(r["buy"]) + float(r["split"]) for r in rows)),
    "winners": sum(p > 0 for p in rounded),
    "losers": sum(p < 0 for p in rounded),
    "flat": sum(p == 0 for p in rounded),
    "median": round(statistics.median(pnl)),
    "max": round(max(pnl)),
    "min": round(min(pnl)),
    "incomplete": sum(r["incomplete"] == "True" for r in rows),
}
assert out["accounts"] == out["winners"] + out["losers"] + out["flat"]
(HERE / "results/recompute_pm_pnl2.json").write_text(json.dumps(out, indent=1) + "\n")
print(out)
