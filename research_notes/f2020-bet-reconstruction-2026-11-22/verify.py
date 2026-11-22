#!/usr/bin/env python3
"""Offline replay of the f2020 bet reconstruction.

1. Every evidence file under data/ matches SHA256SUMS.
2. With network sockets blocked, scripts/reconstruct.py rebuilds results/ in a temporary folder; every file is byte-equal.
3. The facts the report leads with still hold (outcomes, exact PnL, ledger reconciliation, chain vs Gamma).
usage: python3 -I research_notes/f2020-bet-reconstruction-2026-11-22/verify.py
"""
import csv
import hashlib
import json
import socket
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
NOTE = Path(__file__).resolve().parent
sys.path.insert(0, str(NOTE / "scripts"))


def no_network(*a, **k):
    raise OSError("network disabled during offline verification")


socket.socket = no_network  # type: ignore[assignment]
socket.create_connection = no_network  # type: ignore[assignment]

import reconstruct  # noqa: E402

failures = []


def check(cond, msg):
    print(("ok   " if cond else "FAIL ") + msg)
    if not cond:
        failures.append(msg)


def main():
    sums = {}
    for line in (NOTE / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
        h, p = line.split("  ", 1)
        sums[p] = h
    files = sorted(str(p.relative_to(NOTE)) for p in (NOTE / "data").rglob("*") if p.is_file())
    check(sorted(sums) == files, f"SHA256SUMS lists exactly the {len(files)} evidence files")
    for p in files:
        if p in sums:
            check(hashlib.sha256((NOTE / p).read_bytes()).hexdigest() == sums[p], f"sha256 {p}")
    with tempfile.TemporaryDirectory() as tmp:
        reconstruct.main(["--out", tmp])
        for p in sorted((NOTE / "results").iterdir()):
            check((Path(tmp) / p.name).read_bytes() == p.read_bytes(), f"rebuilt results/{p.name} is byte-identical")
        extra = sorted(x.name for x in Path(tmp).iterdir()) == sorted(x.name for x in (NOTE / "results").iterdir())
        check(extra, "results/ holds exactly the rebuilt files")
    focus = {r["wallet_id"]: r for r in csv.DictReader(open(NOTE / "results/focus_bets.csv", encoding="utf-8"))}
    expect = {"W1": ("Down", "Down", "WIN", "2.824012", "4.302889"), "W2": ("Down", "Down", "WIN", "0.560130", "1.250400"),
              "W3": ("Down", "Up", "LOSS", "-2.407870", "2.407870"), "W4": ("No", "Yes", "LOSS", "-0.149839", "0.005539")}
    for k, (bought, won, res, net, stake) in expect.items():
        r = focus[k]
        check((r["outcome_bought"], r["outcome_won"], r["result"], r["net_pnl"], r["first_stake_total"]) == (bought, won, res, net, stake),
              f"{k}: bought {bought}, {won} won, {res}, net {net}, stake {stake}")
    res = json.loads((NOTE / "results/results.json").read_text(encoding="utf-8"))
    for k, w in res["wallets"].items():
        check(w["ledger_balanced"], f"{k}: opening balance + transfers = closing balanceOf")
        check(w["ledger"]["api_gap"] == "0.000000", f"{k}: API cash equals on-chain transfers in API-listed transactions")
        check(w["chain_gamma_disagreements"] == 0, f"{k}: chain payouts agree with Gamma on every later market")
        check(w["pr110_sampled_buys_found"] == w["pr110_sampled_buys"], f"{k}: every PR 110 sampled buy is in the activity")
    print(f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
