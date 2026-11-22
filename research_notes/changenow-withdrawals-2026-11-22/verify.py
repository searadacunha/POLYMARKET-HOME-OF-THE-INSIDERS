#!/usr/bin/env python3
"""Offline replay of the ChangeNOW withdrawal census.

1. Every evidence file under data/ matches SHA256SUMS, and SHA256SUMS lists exactly those files.
2. The unit tests pass.
3. With network sockets blocked, scripts/build.py rebuilds results/ from data/ in a temporary folder; every file is
   byte-equal to the published one, and no other file is produced.
4. Invariants of the published tables: one evidence class per ChangeNOW-side transfer, no attributed part twice,
   every established row names its Polymarket debit and at least one transaction link, weekly counts of distinct
   wallets equal the outflow table, totals in summary.json equal the sums of the rows.
usage: python3 -I research_notes/changenow-withdrawals-2026-11-22/verify.py
"""
import csv
import hashlib
import json
import socket
import sys
import tempfile
import unittest
from collections import defaultdict
from pathlib import Path

sys.dont_write_bytecode = True
NOTE = Path(__file__).resolve().parent
sys.path.insert(0, str(NOTE / "scripts"))


def no_network(*a, **k):
    raise OSError("network disabled during offline verification")


socket.socket = no_network  # type: ignore[assignment]
socket.create_connection = no_network  # type: ignore[assignment]

import build  # noqa: E402
import report  # noqa: E402

failures = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


def rows(name):
    with open(NOTE / "results" / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main():
    sums = {}
    for line in (NOTE / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        h, p = line.split("  ", 1)
        sums[p] = h
    files = sorted(str(p.relative_to(NOTE)) for p in (NOTE / "data").rglob("*") if p.is_file())
    check(sorted(sums) == files, f"SHA256SUMS lists exactly the {len(files)} evidence files")
    bad = [p for p in files if p in sums and hashlib.sha256((NOTE / p).read_bytes()).hexdigest() != sums[p]]
    check(not bad, f"sha256 of every evidence file ({len(bad)} differ)")

    suite = unittest.defaultTestLoader.discover(str(NOTE / "tests"), top_level_dir=str(NOTE))
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    check(result.wasSuccessful(), f"{result.testsRun} unit tests pass")

    with tempfile.TemporaryDirectory() as tmp:
        build.main(["--raw", str(NOTE / "data"), "--out", tmp])
        report.main([tmp])
        for p in sorted((NOTE / "results").iterdir()):
            check((Path(tmp) / p.name).exists() and (Path(tmp) / p.name).read_bytes() == p.read_bytes(), f"rebuilt results/{p.name} is byte-identical")
        made = sorted(x.name for x in Path(tmp).iterdir())
        have = sorted(x.name for x in (NOTE / "results").iterdir())
        check(made == have, "results/ holds exactly the rebuilt files")

    out = rows("changenow_outflows.csv")
    per_transfer = defaultdict(set)
    parts, twice = set(), []
    for r in out:
        per_transfer[(r["changenow_chain"], r["changenow_tx"], r["changenow_log_index"])].add(r["evidence_class"])
        k = (r["changenow_chain"], r["changenow_tx"], r["changenow_log_index"], r["polymarket_debit_tx"], r["polymarket_debit_log_index"])
        if k in parts:
            twice.append(r["event_id"])
        parts.add(k)
    check(not twice, f"every attributed part is listed once ({len(twice)} repeated)")
    check(all(len(v) == 1 for v in per_transfer.values()), f"one evidence class per ChangeNOW-side transfer ({len(per_transfer)} transfers)")
    est = [r for r in out if r["evidence_class"] in build.ESTABLISHED]
    check(all(r["polymarket_wallet"] and r["polymarket_debit_tx"] and r["explorer_links"] for r in est),
          f"every established row names its wallet, its debit and its transactions ({len(est)} rows)")
    check(all(r["changenow_endpoint_grade"] in ("A", "B") for r in est), "every established row ends at a deposit address swept into a grade A or B wallet")
    check(all(r["intermediary_count"] == "0" for r in est if r["evidence_class"] == "CONFIRMED_DIRECT"), "confirmed direct rows have no intermediary")
    weekly = {r["week"]: r for r in rows("weekly_outflows.csv")}
    for week, r in weekly.items():
        wallets = {x["polymarket_wallet"] for x in est if x["week"] == week}
        check(int(r["wallets_established"]) == len(wallets), f"{week}: {len(wallets)} distinct wallets with an established withdrawal")
    summary = json.loads((NOTE / "results" / "summary.json").read_text(encoding="utf-8"))
    total = round(sum(float(r["usd"] or 0) for r in est), 2)
    check(abs(summary["established_usd"] - total) < 0.011, f"summary established USD {summary['established_usd']} equals the rows ({total})")
    print(f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
