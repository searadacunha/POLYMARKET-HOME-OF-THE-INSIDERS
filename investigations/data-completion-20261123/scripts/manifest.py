"""Write data_manifest.json and local_only_hashes.sha256.gz for the raw data that stays on this Mac.

Each raw directory is one local_only entry (file count, bytes, SHA-256 of its sorted hash list); every file inside is
listed with its own SHA-256 in local_only_hashes.sha256.gz. The private backup-index join (audit/) is listed without
per-file hashes. Nothing here claims a public archive.
"""

import argparse
import gzip
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROLES = {
    "ledger": "cohort Polygon logs: accepted ranges (gzip JSON), checkpoint.jsonl, plan.json",
    "ledger_pr111": "regression cohort (PR 111 wallets) Polygon logs, same layout",
    "sources": "cohort market sources: Gamma markets, ConditionResolution payouts, balances, Data API activity, marks",
    "sources_pr111": "regression cohort market sources, same layout",
    "results_pr111": "ledger outputs of the regression cohort",
    "relay_v2": "Relay v2 history pages (every HTTP exchange), plan.json, run.log",
    "agents/contracts": "contract-semantics receipts and probe log",
    "agents/sources": "public source probes (raw responses, profile fields removed)",
    "agents/crosschain": "Arbitrum and Polygon receipts and probe log",
    "agents/ethweeks": "Ethereum W16..W38 stream packs, explorer pages and probe log",
    "agents/prospective": "prospective data-quality probes",
}
PRIVATE = {"audit": "private join with the encrypted backup index (pack names), not for publication"}


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--inv", type=Path, required=True)
    a = ap.parse_args()
    files, lines = [], []
    for rel, role in ROLES.items():
        d = a.raw / rel
        if not d.exists():
            files.append({"path": rel + "/", "status": "absent", "role": role, "reason": "absent at manifest time"})
            continue
        entries = []
        for root, _, names in os.walk(d):
            for n in sorted(names):
                p = Path(root) / n
                if "__pycache__" in p.parts or n.endswith(".pyc"):
                    continue
                r = str(p.relative_to(a.raw))
                entries.append((r, sha_file(p), p.stat().st_size))
        entries.sort()
        listing = "".join(f"{s}  {r}\n" for r, s, _ in entries)
        lines.append(listing)
        files.append({"path": rel + "/", "status": "local_only", "role": role, "files": len(entries),
                      "size": sum(e[2] for e in entries), "sha256": hashlib.sha256(listing.encode()).hexdigest(),
                      "reason": "raw data over the repository's size policy or agent working files; hashes in "
                                "local_only_hashes.sha256.gz"})
    for rel, why in PRIVATE.items():
        files.append({"path": rel + "/", "status": "local_only", "role": "private", "reason": why})
    m = {"id": "data-completion-20261123", "origin": "~/.cache/phi-work/data-completion-raw-20261123",
         "snapshot_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
         "note": "Native investigation. local_only: present on the original machine only, NOT archived here. "
                 "Derived results are in results/ with their SHA-256 in EVIDENCE.md.",
         "counts": {k: sum(f["status"] == k for f in files) for k in ("local_only", "absent")}, "files": files}
    (a.inv / "data_manifest.json").write_text(json.dumps(m, indent=1) + "\n")
    with gzip.GzipFile(a.inv / "local_only_hashes.sha256.gz", "wb", mtime=0) as g:
        g.write("".join(lines).encode())
    print(json.dumps([{k: f.get(k) for k in ("path", "files", "size")} for f in files], indent=0))


if __name__ == "__main__":
    main()
