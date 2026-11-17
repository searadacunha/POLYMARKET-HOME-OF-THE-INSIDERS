#!/usr/bin/env python3
"""Write data_manifest.json: what this study read, what it produced, and what stays off git.

Large collected tapes are recorded as `local_only` with their size and SHA-256: they exist on the working machine
only, and nothing in this folder may claim otherwise (CONTRIBUTING.md, "Large data").
"""
import hashlib, json, os, sys, time

STUDY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


ARCHIVED = [
    ("research_notes/independent-forensic-audit-2026-11-08/evidence/feb28_market_trades.jsonl",
     "archived 42,000-row Iran tape (read from git, unmodified)"),
    ("research_notes/independent-forensic-audit-2026-11-08/evidence/feb22_25_traders_createdAt.csv",
     "archived profile creation dates for the 769 accounts"),
    ("research_notes/early-detection-2026-11-13/study/derived/universe_markets.jsonl.gz",
     "frozen 34,413-market population (read from git, unmodified)"),
    ("research_notes/early-detection-2026-11-13/study/derived/labels.jsonl.gz",
     "outcome labels, joined last"),
]


def main():
    workdir = sys.argv[1] if len(sys.argv) > 1 else "."
    entries, counts = [], {"archived": 0, "local_only": 0}
    for path, role in ARCHIVED:
        entries.append({"path": path, "status": "archived", "role": role, "origin": "git:origin/main"})
        counts["archived"] += 1
    local = [("tapes.sqlite", "complete v2 tapes for the 763-market primary sample (1,518,268 fills)"),
             ("tapes2.sqlite", "complete v2 tapes for the expanded replication sample"),
             ("feb28_v2.sqlite", "complete v2 tape of the Iran 28 February market (217,997 fills)")]
    for name, role in local:
        p = os.path.join(workdir, name)
        if not os.path.exists(p):
            continue
        entries.append({"path": name, "status": "local_only", "role": role,
                        "size": os.path.getsize(p), "sha256": sha256(p)})
        counts["local_only"] += 1
    manifest = {"id": "collective-exposure-shifts",
                "origin": workdir.replace(os.path.expanduser("~"), "~"),
                "snapshot_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "note": "local_only: present on the original machine only, NOT archived here.",
                "counts": counts,
                "files": sorted(entries, key=lambda e: e["path"])}
    json.dump(manifest, open(os.path.join(STUDY, "data_manifest.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps({"counts": counts}, indent=1))


if __name__ == "__main__":
    main()
