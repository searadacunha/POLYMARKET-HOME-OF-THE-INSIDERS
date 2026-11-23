"""Copy the PR 110 inputs this note reuses, from Git objects of its pinned head, with the SHA-256 of each original blob.

usage (from the repository root of a clone that has fetched PR 110's branch):
  python3 -I research_notes/f2020-bet-reconstruction-2026-11-22/scripts/pin_pr110.py
Writes data/inputs/pr110_wallet_funding_slim.csv and data/inputs/pr110_provenance.json. PR 110 files are never modified.
"""
import csv
import gzip
import hashlib
import io
import json
import subprocess
from pathlib import Path

NOTE = Path(__file__).resolve().parents[1]
COMMIT = "8b633048290e7174945bc811b16cf0b11b4d8ceb"  # head of PR 110 when this note was built (2026-11-22)
BASE = "investigations/weekly-funding-intelligence/"
KEEP = ["week", "service", "evidence", "wallet", "source_address", "source_role", "token", "amount", "funding_time", "block", "tx",
        "log_index", "relationship", "traded_after", "first_buy_status", "first_buy_time", "first_buy_tx", "first_buy_market",
        "first_buy_title", "first_buy_usd", "first_indexed_trade", "economic_pnl_usd", "pnl_time"]


def blob(path):
    return subprocess.run(["git", "show", f"{COMMIT}:{BASE}{path}"], capture_output=True, check=True, cwd=NOTE).stdout


def main():
    out = NOTE / "data/inputs"
    out.mkdir(parents=True, exist_ok=True)
    wf = blob("results/wallet_funding.csv")
    rows = list(csv.DictReader(io.StringIO(wf.decode())))
    with open(out / "pr110_wallet_funding_slim.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=KEEP, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in KEEP})
    acc = blob("snapshot/accounts.json.gz")
    profiles = json.loads(gzip.decompress(acc))["profiles"]
    wallets = ["0x9fed84d86211d077277426db9831d74756531d1b", "0xd74d2d3a4016079ff49743f831d1a31b668cccf3",
               "0x569c5f3850c31bcb8590ef1926fb69e0f42f741d", "0xadd9ab62b2c22151c661b99821cbb7433df98df9"]
    prov = {"pr": 110, "commit": COMMIT,
            "files": {BASE + "results/wallet_funding.csv": hashlib.sha256(wf).hexdigest(),
                      BASE + "snapshot/accounts.json.gz": hashlib.sha256(acc).hexdigest()},
            "rows": len(rows), "columns_kept": KEEP,
            "user_pnl_snapshot": {a: profiles[a]["pnl"] for a in wallets},
            "sampled_buys": {a: profiles[a]["buys"] for a in wallets}}
    (out / "pr110_provenance.json").write_text(json.dumps(prov, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(len(rows), "rows pinned from", COMMIT)


if __name__ == "__main__":
    main()
