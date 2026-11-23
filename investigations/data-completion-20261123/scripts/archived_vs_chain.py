"""Compare the archived Data API PnL of the f2020 cohort (pm_pnl2.csv) with this on-chain ledger, account by account.

The archived rows are deduplicated by account (five accounts appear in two bettor records). The on-chain side is the
sum of trading_pnl over the account's markets first entered no later than the archived last_trade of that account,
which approximates the archived observation window. Records flagged incomplete in the archive (capped at 5,500 events)
are compared separately.
"""

import argparse
import csv
import gzip
import json
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

STATE = "investigations/changenow-polymarket/sources/state/"


def compare(repo, summary_gz):
    arch, traders = {}, {}
    for r in csv.DictReader(open(repo / STATE / "pm_pnl2.csv")):
        arch.setdefault(r["account"].lower(), r)
    for r in csv.DictReader(open(repo / STATE / "pm_traders.csv")):
        traders.setdefault(r["account"].lower(), r)
    win, life, buy = defaultdict(Decimal), defaultdict(Decimal), defaultdict(Decimal)
    unknown = defaultdict(int)
    for p in csv.DictReader(gzip.open(summary_gz, "rt")):
        a = p["account"]
        buy[a] += Decimal(p["buy_cash"])
        if p["trading_pnl"] == "UNKNOWN":
            unknown[a] += 1
            continue
        v = Decimal(p["trading_pnl"])
        life[a] += v
        t = traders.get(a)
        if t and t["last_trade"] and p["first_entry_utc"]:
            last = datetime.fromtimestamp(int(t["last_trade"]), timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            if p["first_entry_utc"] <= last:
                win[a] += v
    groups = {"capped": [], "uncapped": []}
    for a, r in arch.items():
        groups["capped" if r["incomplete"] == "True" else "uncapped"].append(a)
    out = {"accounts_archived": len(arch), "groups": {}}
    for g, accts in groups.items():
        diffs = sorted(win[a] - Decimal(arch[a]["total_pnl"]) for a in accts)
        out["groups"][g] = {
            "accounts": len(accts),
            "archived_total_pnl": str(sum(Decimal(arch[a]["total_pnl"]) for a in accts)),
            "chain_trading_pnl_in_archived_window": str(sum(win[a] for a in accts)),
            "chain_trading_pnl_lifetime": str(sum(life[a] for a in accts)),
            "archived_buy": str(sum(Decimal(arch[a]["buy"]) for a in accts)),
            "chain_buy_cash": str(sum(buy[a] for a in accts)),
            "accounts_within_1_usd": sum(1 for a in accts if abs(win[a] - Decimal(arch[a]["total_pnl"])) <= 1),
            "median_difference": str(diffs[len(diffs) // 2]) if diffs else "",
            "accounts_with_unknown_positions": sum(1 for a in accts if unknown[a]),
        }
    out["note"] = ("archived values are whole dollars from the Data API; the chain values are exact. The window "
                   "match uses each account's archived last_trade, an approximation of the archive's observation time")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    a = ap.parse_args()
    res = compare(a.repo, a.results / "wallet_position_summary.csv.gz")
    (a.results / "archived_vs_chain.json").write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
