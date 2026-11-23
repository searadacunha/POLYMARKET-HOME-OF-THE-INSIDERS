#!/usr/bin/env python3
"""Offline replay of this investigation's derived results, with network sockets blocked.

1. Tables derived from Git objects only (weekly funding table, data gap matrix) are rebuilt in a temporary folder and
   compared byte for byte with results/. They need the pinned commits of PR 110 and PR 111 in the clone.
2. Tables derived from the local raw logs (cohort ledger, PR 111 regression, Relay v2 screen) are rebuilt the same way
   when the raw directory is present.
A check whose input is absent is reported SKIPPED_MISSING_INPUT with the expected input; it is never counted as passed.

usage: python3 investigations/data-completion-20261123/verify.py [--raw DIR]
"""
import argparse
import csv
import io
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
sys.path.insert(0, str(HERE / "scripts"))
DEFAULT_RAW = Path(os.path.expanduser("~/.cache/phi-work/data-completion-raw-20261123"))
PINNED = {"PR 110": "8b633048290e7174945bc811b16cf0b11b4d8ceb", "PR 111": "58c964b5aa5063d90e4dd7d72dab50d916a81bd7"}
LEDGER_FILES = ["wallet_position_summary.csv.gz", "wallet_summary.csv", "coverage_by_contract.csv",
                "coverage_by_market.csv.gz", "reconciliation_failures.csv"]
LOCAL_FILES = ["wallet_fills.csv.gz", "wallet_position_ledger.csv.gz"]   # full tables kept in RAW/derived
PARQUET = {"wallet_fills.parquet": "wallet_fills.csv.gz", "wallet_position_ledger.parquet": "wallet_position_ledger.csv.gz"}


def blocked(*args, **kw):
    raise AssertionError("offline verification opened a network socket")


def ledger_inputs():
    st = REPO / "investigations/changenow-polymarket/sources/state"
    archived = {}
    for r in csv.DictReader(open(st / "pm_pnl2.csv")):
        archived.setdefault(r["account"].lower(), r["total_pnl"])
    traders = defaultdict(list)
    for r in csv.DictReader(open(st / "pm_traders.csv")):
        traders[r["account"].lower()].append(r)
    return archived, traders


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", type=Path, default=DEFAULT_RAW)
    a = ap.parse_args()
    res, raw, status = HERE / "results", a.raw, []

    def report(name, ok, detail=""):
        status.append((name, ok))
        print(f"{ {True: 'ok  ', False: 'FAIL', None: 'SKIP'}[ok]} {name} {detail}".rstrip())

    missing = [k for k, sha in PINNED.items()
               if subprocess.run(["git", "-C", str(REPO), "cat-file", "-e", sha + "^{commit}"],
                                 capture_output=True).returncode]
    have_raw = (raw / "ledger" / "checkpoint.jsonl").exists() and (raw / "sources").exists()
    have_pr111 = (raw / "ledger_pr111" / "checkpoint.jsonl").exists() and (raw / "sources_pr111").exists()
    with tempfile.TemporaryDirectory() as tmp, patch.object(socket.socket, "connect", blocked):
        tmp = Path(tmp)
        import data_gap_matrix
        import ledger_report
        import regression_pr111
        import relay_screen
        import weekly_table

        if missing:
            for name in ("weekly_service_funding.csv", "regression_pr111.json", "data_gap_matrix.json"):
                report(name, None, f"SKIPPED_MISSING_INPUT pinned commits {missing} absent from this clone")
        else:
            rows, _ = weekly_table.build(REPO, res / "eth_weeks_coverage.csv")
            buf = io.StringIO()
            w = csv.DictWriter(buf, fieldnames=weekly_table.FIELDS, lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
            report("weekly_service_funding.csv", buf.getvalue() == (res / "weekly_service_funding.csv").read_text())
            shutil.copytree(res, tmp / "gap")
            rows = data_gap_matrix.build(REPO, tmp / "gap", None)
            report("data_gap_matrix.json", json.dumps(rows, indent=1) + "\n" == (res / "data_gap_matrix.json").read_text())
            if have_pr111:
                ledger_report.build(raw / "ledger_pr111", raw / "sources_pr111", tmp / "pr111")
                reg = regression_pr111.compare(REPO, tmp / "pr111" / "wallet_position_summary.csv.gz")
                report("regression_pr111.json", json.dumps(reg, indent=1, sort_keys=True) + "\n" ==
                       (res / "regression_pr111.json").read_text(), json.dumps(reg["counts"]))
            else:
                report("regression_pr111.json", None, f"SKIPPED_MISSING_INPUT {raw / 'ledger_pr111'}")

        if have_raw:
            s, _, _ = ledger_report.build(raw / "ledger", raw / "sources", tmp / "ledger", *ledger_inputs(),
                                          local=tmp / "local")
            for name in LEDGER_FILES:
                report(name, (tmp / "ledger" / name).read_bytes() == (res / name).read_bytes())
            for name in LOCAL_FILES:
                kept = raw / "derived" / name
                report(f"{name} (local_only)", (tmp / "local" / name).read_bytes() == kept.read_bytes()
                       if kept.exists() else None, "" if kept.exists() else f"SKIPPED_MISSING_INPUT {kept}")
            try:
                import duckdb
                for pq in PARQUET:
                    stem = pq[:-len(".parquet")]
                    mine_parts = sorted(p.name for p in res.glob(stem + "*.parquet"))
                    new_parts = sorted(p.name for p in (tmp / "ledger").glob(stem + "*.parquet"))
                    same_rows = mine_parts == new_parts and all(
                        duckdb.sql(f"SELECT * FROM '{res / n}'").fetchall() ==
                        duckdb.sql(f"SELECT * FROM '{tmp / 'ledger' / n}'").fetchall() for n in mine_parts)
                    report(f"{stem} parquet rows ({len(mine_parts)} file(s))", same_rows)
            except ImportError:
                for pq in PARQUET:
                    report(pq, None, "SKIPPED_MISSING_INPUT duckdb not importable")
            mine = json.loads((res / "ledger_results.json").read_text())
            for d in (mine, s):  # wall time and the parquet encoder's bytes are not part of the replay
                d.pop("runtime_s", None)
                for name in [n for n in d.get("outputs_sha256", {}) if n.endswith(".parquet")]:
                    d["outputs_sha256"].pop(name)
            report("ledger_results.json (without runtime)", json.loads(json.dumps(s, sort_keys=True)) == mine)
        else:
            for name in LEDGER_FILES:
                report(name, None, f"SKIPPED_MISSING_INPUT {raw / 'ledger'} and {raw / 'sources'} "
                                   "(local_only, SHA-256 in data_manifest.json)")
        if (raw / "relay_v2" / "pages.jsonl").exists() and (res / "relay_v2_screen.csv").exists():
            plan = json.loads((raw / "relay_v2" / "plan.json").read_text())
            pages = [json.loads(x) for x in (raw / "relay_v2" / "pages.jsonl").read_text().splitlines() if x.strip()]
            # the page log is append-only: replay exactly the prefix the published snapshot was built from
            pages = pages[:json.loads((res / "relay_v2_screen.json").read_text())["http_calls"]]
            got = list(csv.DictReader(open(res / "relay_v2_screen.csv")))
            want = [{k: str(v) for k, v in r.items()} for r in relay_screen.classify(plan, pages)]
            report("relay_v2_screen.csv", want == got)
        else:
            report("relay_v2_screen.csv", None, f"SKIPPED_MISSING_INPUT {raw / 'relay_v2'}")

    failed = [n for n, ok in status if ok is False]
    skipped = [n for n, ok in status if ok is None]
    print(f"{len(status) - len(failed) - len(skipped)} passed, {len(failed)} failed, {len(skipped)} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
