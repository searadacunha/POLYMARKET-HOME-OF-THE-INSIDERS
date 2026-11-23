"""Compare this ledger, run on PR #111's four wallets, with PR #111's published per-market results (pinned 58c964b).

Every PR #111 row of positions_after_funding.csv is matched on (wallet, condition). A difference is EXPLAINED only when
PR #111 listed the market as OPEN at its cut-off and this ledger sees its official resolution after that cut-off;
anything else is UNEXPLAINED.
"""

import argparse
import csv
import gzip
import io
import json
import subprocess
from decimal import Decimal
from pathlib import Path

PR111 = "58c964b5aa5063d90e4dd7d72dab50d916a81bd7"
NOTE = "research_notes/f2020-bet-reconstruction-2026-11-22/"
TOL = Decimal("0.000001")


def show(repo, path):
    return subprocess.run(["git", "-C", str(repo), "show", f"{PR111}:{NOTE}{path}"], check=True,
                          capture_output=True).stdout.decode()


def compare(repo, summary_csv):
    focus = list(csv.DictReader(io.StringIO(show(repo, "results/focus_bets.csv"))))
    ids = {r["wallet_id"]: r["wallet"].lower() for r in focus}
    theirs = list(csv.DictReader(io.StringIO(show(repo, "results/positions_after_funding.csv"))))
    cutoff = json.loads(show(repo, "results/results.json"))["meta"]["chain_last_block_utc"]
    fh = gzip.open(summary_csv, "rt") if str(summary_csv).endswith(".gz") else open(summary_csv)
    mine = {(r["account"], r["market"]): r for r in csv.DictReader(fh)}
    rows, counts = [], {"EXACT": 0, "EXPLAINED_LATER_RESOLUTION": 0, "UNEXPLAINED": 0, "MISSING": 0}
    for r in theirs:
        m = mine.get((ids[r["wallet_id"]], r["condition_id"].lower()))
        if m is None:
            verdict, diff = "MISSING", ""
        elif m["net_position_pnl"] == "UNKNOWN":
            verdict, diff = "UNEXPLAINED", "UNKNOWN"
        else:
            d = Decimal(m["net_position_pnl"]) - Decimal(r["net_pnl"])
            diff = str(d)
            if abs(d) <= TOL:
                verdict = "EXACT"
            elif r["status"] == "OPEN" and m["status"] == "RESOLVED":
                verdict = "EXPLAINED_LATER_RESOLUTION"
            else:
                verdict = "UNEXPLAINED"
        counts[verdict] += 1
        if verdict != "EXACT":
            rows.append({"wallet_id": r["wallet_id"], "condition_id": r["condition_id"], "title": r["title"],
                         "pr111_status": r["status"], "pr111_net_pnl": r["net_pnl"],
                         "ledger_status": m["status"] if m else "", "ledger_net_pnl": m["net_position_pnl"] if m else "",
                         "difference": diff, "verdict": verdict})
    focus_rows = []
    for r in focus:
        m = mine.get((r["wallet"].lower(), r["condition_id"].lower()))
        focus_rows.append({"wallet_id": r["wallet_id"], "condition_id": r["condition_id"], "pr111_net_pnl": r["net_pnl"],
                           "ledger_net_pnl": m["net_position_pnl"] if m else "MISSING",
                           "exact": bool(m) and abs(Decimal(m["net_position_pnl"]) - Decimal(r["net_pnl"])) <= TOL})
    return {"pr111_commit": PR111, "pr111_cutoff_utc": cutoff, "positions_compared": len(theirs), "counts": counts,
            "differences": rows, "focus_bets": focus_rows,
            "focus_net_sum_ledger": str(sum(Decimal(f["ledger_net_pnl"]) for f in focus_rows))}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--summary", type=Path, required=True, help="wallet_position_summary.csv of the PR #111 cohort")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    res = compare(a.repo, a.summary)
    a.out.write_text(json.dumps(res, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: res[k] for k in ("positions_compared", "counts", "focus_net_sum_ledger")}, indent=1))


if __name__ == "__main__":
    main()
