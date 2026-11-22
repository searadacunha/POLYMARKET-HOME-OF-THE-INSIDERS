"""Copy the evidence the published tables are built from into data/, then write SHA256SUMS.

Kept: every week's census file (gzip), Relay's answers that a row relies on and their on-chain check, and the bets
inputs of the wallets in the tables (activity feeds, the Gamma records of their markets, balances, controls).
Raw block-window rows stay in --raw: the census files hold every transfer a row uses, and the population counts.
"""
import argparse
import csv
import gzip
import hashlib
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTE = HERE.parent
sys.dont_write_bytecode = True


def gz(src_obj, dst):
    dst.parent.mkdir(parents=True, exist_ok=True)
    with gzip.GzipFile(dst, "wb", mtime=0) as f:                    # fixed header time: the same input gives the same bytes
        f.write(json.dumps(src_obj, sort_keys=True, separators=(",", ":")).encode())


def load_gz(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--raw", required=True)
    p.add_argument("--data", default=str(NOTE / "data"))
    args = p.parse_args(argv)
    raw, data = Path(args.raw), Path(args.data)
    if data.exists():
        shutil.rmtree(data)
    for w in sorted(raw.glob("20*-W*/withdrawals.json")):
        gz(json.loads(w.read_text()), data / w.parent.name / "withdrawals.json.gz")
    checked = raw / "relay_api" / "checked.json"
    used = {}
    if checked.exists():
        c = json.loads(checked.read_text())
        (data / "relay_api").mkdir(parents=True, exist_ok=True)
        (data / "relay_api" / "checked.json").write_text(json.dumps(c, indent=1, sort_keys=True))
        for tx, v in c.items():
            src = raw / "relay_api" / "hash" / f"{tx}.json"
            if v.get("verdict") in ("WALLET_DEBIT_VERIFIED", "KEY_OF_WALLET") and src.exists():
                used[tx] = json.loads(src.read_text())
        for tx, a in used.items():
            gz(a, data / "relay_api" / "hash" / f"{tx}.json.gz")
    agree = raw / "relay_api" / "agreement.json"
    if agree.exists():
        (data / "relay_api").mkdir(parents=True, exist_ok=True)
        (data / "relay_api" / "agreement.json").write_text(json.dumps(json.loads(agree.read_text()), indent=1, sort_keys=True))
    forward = raw / "cohort" / "forward.json"
    if forward.exists():
        (data / "cohort").mkdir(parents=True, exist_ok=True)
        (data / "cohort" / "forward.json").write_text(json.dumps(json.loads(forward.read_text()), indent=1, sort_keys=True))
    with open(NOTE / "results" / "changenow_outflows.csv", newline="", encoding="utf-8") as f:
        wallets = sorted({w for r in csv.DictReader(f) for w in r["polymarket_wallet"].split("|") if len(w) == 42})
    bets = raw / "bets"
    if (bets / "markets.json.gz").exists():
        controls = load_gz(bets / "controls.json.gz") if (bets / "controls.json.gz").exists() else {}
        keep = set(wallets) | {c for v in controls.values() if v.get("condition_id") for c in v["controls"]}
        cids = set()
        for w in sorted(keep):
            src = bets / "activity" / f"{w}.json.gz"
            if src.exists():
                a = load_gz(src)
                cids |= {(r.get("condition_id") or "").lower() for r in a["rows"] if r.get("condition_id")}
                gz(a, data / "bets" / "activity" / f"{w}.json.gz")
        mk = load_gz(bets / "markets.json.gz")
        gz(dict(mk, markets={k: v for k, v in mk["markets"].items() if k in cids}, missing=sorted(set(mk["missing"]) & cids)), data / "bets" / "markets.json.gz")
        for name in ("balances.json.gz", "controls.json.gz"):
            if (bets / name).exists():
                gz(load_gz(bets / name), data / "bets" / name)
    files = sorted(p for p in data.rglob("*") if p.is_file())
    (NOTE / "SHA256SUMS").write_text("".join(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(NOTE)}\n" for p in files))
    size = sum(p.stat().st_size for p in files)
    print(f"{len(files)} evidence files, {size / 1e6:.1f} MB")
    return 0


if __name__ == "__main__":
    sys.exit(main())
