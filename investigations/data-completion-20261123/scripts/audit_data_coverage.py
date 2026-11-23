"""Read-only, file-level audit of every investigation manifest against this Mac and the encrypted backup.

For each manifest entry (investigations/*/data_manifest.json, expanded with local_only_hashes.sha256.gz):
- imported files are re-hashed in the repository;
- local-only files are looked up at their recorded origin, hashed when present, and their volume is reported
  when it is not mounted;
- every recorded SHA-256 is looked up in the local phi-backup state (blob -> pack -> GitHub verification state).

Status vocabulary: COMPLETE, PARTIAL, UNAVAILABLE, LOCAL_ONLY, CORRUPT, UNVERIFIED, UNKNOWN.
LOCAL_ONLY means present on this Mac only, with its recorded hash. An absent file is UNAVAILABLE *now*; the
`recoverable` column says whether a verified encrypted backup or an offline volume still holds it.

Nothing is modified. Backup pack names stay in the private output (--private-out), never in the public CSV.
"""

import argparse
import csv
import fnmatch
import gzip
import hashlib
import io
import json
import os
import sqlite3
import sys
from collections import Counter, defaultdict
from pathlib import Path

STATUSES = ("COMPLETE", "PARTIAL", "UNAVAILABLE", "LOCAL_ONLY", "CORRUPT", "UNVERIFIED", "UNKNOWN")
IN_SCOPE = {"imported", "local_only", "archived"}  # evidence; excluded/refused/duplicate are withheld by policy
PUBLIC_FIELDS = (
    "investigation", "path", "expanded_from", "manifest_status", "in_scope", "size", "sha256", "origin",
    "origin_state", "observed_size", "hash_check", "repo_copy", "backup", "status", "recoverable",
    "recovery_method", "note",
)


def sha256_file(p, chunk=1 << 22):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while b := f.read(chunk):
            h.update(b)
    return h.hexdigest()


def volume_state(path):
    """PRESENT, MISSING or VOLUME_OFFLINE:<name> for a path whose parents may be links to /Volumes."""
    if os.path.lexists(path) and os.path.exists(path):
        return "PRESENT"
    real = os.path.realpath(path)
    parts = Path(real).parts
    if len(parts) > 2 and parts[1] == "Volumes" and not os.path.ismount(os.path.join("/Volumes", parts[2])):
        return "VOLUME_OFFLINE:" + parts[2]
    return "MISSING"


class HashCache:
    def __init__(self, path):
        self.path = path
        self.d = json.loads(path.read_text()) if path and path.exists() else {}

    def get(self, p):
        st = os.stat(p)
        key = f"{os.path.realpath(p)}|{st.st_size}|{st.st_mtime_ns}"
        if key not in self.d:
            self.d[key] = sha256_file(p)
        return self.d[key], st.st_size

    def save(self):
        if self.path:
            self.path.write_text(json.dumps(self.d, sort_keys=True))


def backup_index(state_db, shas):
    """sha -> (pack, gh_state). Read-only; an absent database means the column is UNKNOWN."""
    if not state_db or not Path(state_db).exists():
        return None
    con = sqlite3.connect(f"file:{state_db}?mode=ro", uri=True)
    packs = {n: s for n, s in con.execute("select name, gh_state from packs")}
    out, want = {}, sorted(shas)
    for i in range(0, len(want), 900):
        chunk = want[i:i + 900]
        q = "select sha, pack from blobs where sha in (%s)" % ",".join("?" * len(chunk))
        for sha, pack in con.execute(q, chunk):
            out[sha] = (pack, packs.get(pack))
    con.close()
    return out


def manifest_rows(repo, inv_dir):
    """Expand one investigation manifest into file-level rows (directory entries expand via the hash list)."""
    m = json.loads((inv_dir / "data_manifest.json").read_text())
    files = m["files"] if isinstance(m, dict) else m
    origin = m.get("origin") if isinstance(m, dict) else None
    hashes = {}
    hp = inv_dir / "local_only_hashes.sha256.gz"
    if hp.exists():
        for line in gzip.open(hp, "rt"):
            line = line.rstrip("\n")
            if line:
                sha, _, path = line.partition("  ")
                hashes[path] = sha
    rows, covered = [], set()
    for f in files:
        path, status = f["path"], f.get("status")
        if path.endswith("/") or "*" in path:
            pat = path + "*" if path.endswith("/") else path
            inner = {p: s for p, s in hashes.items() if fnmatch.fnmatchcase(p, pat)}
            if inner and status == "local_only":
                for p, s in sorted(inner.items()):
                    rows.append(dict(path=p, expanded_from=path, manifest_status=status, size="", sha256=s))
                    covered.add(p)
                continue
        rows.append(dict(path=path, expanded_from="", manifest_status=status, size=f.get("size", ""),
                         sha256=f.get("sha256") or "", repo_path=f.get("repo_path", ""),
                         entry_origin=f.get("origin") or ""))
        covered.add(path)
    for p, s in sorted(hashes.items()):
        if p not in covered:
            rows.append(dict(path=p, expanded_from="local_only_hashes", manifest_status="local_only", size="",
                             sha256=s))
    snap = m.get("snapshot_utc") if isinstance(m, dict) else None
    for r in rows:
        r["investigation"], r["origin"], r["snapshot_utc"] = inv_dir.name, origin or "", snap or ""
        r["in_scope"] = "YES" if r["manifest_status"] in IN_SCOPE else "NO"
    return rows, (m.get("counts") if isinstance(m, dict) else None)


def classify(r, repo, inv_dir, cache, backup, hash_limit):
    ms = r["manifest_status"]
    r.update(origin_state="", observed_size="", hash_check="", repo_copy="NOT_APPLICABLE", backup="UNKNOWN",
             recoverable="UNKNOWN", recovery_method="", note="")
    if backup is not None:
        b = backup.get(r["sha256"]) if r["sha256"] else None
        r["backup"] = "NO_REFERENCE" if not r["sha256"] else (
            "NOT_IN_BACKUP" if not b else ("VERIFIED_PACK" if b[1] == "verified" else "PACK_" + str(b[1]).upper()))
    if ms == "archived" and r.get("entry_origin", "").startswith("git:"):
        rp = repo / r["path"]
        r.update(origin_state="REPOSITORY", repo_copy="PRESENT_GIT_BLOB" if rp.exists() else "MISSING",
                 hash_check="GIT_BLOB" if rp.exists() else "", status="COMPLETE" if rp.exists() else "UNAVAILABLE",
                 recoverable="YES" if rp.exists() else "UNKNOWN", note="archived in git, no manifest SHA-256")
        return r
    if ms == "imported":
        rp = repo / (r.get("repo_path") or (str(inv_dir.relative_to(repo)) + "/sources/" + r["path"]))
        if not rp.exists():
            r.update(repo_copy="MISSING", status="UNAVAILABLE")
        elif not r["sha256"]:
            r.update(repo_copy="PRESENT_NO_REFERENCE", status="UNVERIFIED")
        else:
            got, size = cache.get(rp)
            ok = got == r["sha256"]
            r.update(repo_copy="PRESENT_MATCH" if ok else "PRESENT_MISMATCH", observed_size=size,
                     hash_check="MATCH" if ok else "MISMATCH", status="COMPLETE" if ok else "CORRUPT")
        r["recoverable"] = "YES" if r["status"] == "COMPLETE" else r["recoverable"]
        return r
    origin = os.path.expanduser(r["origin"]) if r["origin"] else ""
    p = os.path.join(origin, r["path"]) if origin else ""
    state = volume_state(p) if p else "NO_ORIGIN"
    r["origin_state"] = state
    if state == "PRESENT" and os.path.isfile(p):
        size = os.path.getsize(p)
        r["observed_size"] = size
        if not r["sha256"]:
            r.update(hash_check="NO_REFERENCE", status="UNVERIFIED")
        elif size > hash_limit:
            r.update(hash_check="NOT_HASHED_SIZE_LIMIT", status="UNVERIFIED")
        else:
            got, _ = cache.get(p)
            ok = got == r["sha256"]
            r.update(hash_check="MATCH" if ok else "MISMATCH", status="LOCAL_ONLY" if ok else "CORRUPT")
            if not ok and r["snapshot_utc"]:
                from datetime import datetime
                snap = datetime.fromisoformat(r["snapshot_utc"].replace("Z", "+00:00")).timestamp()
                if os.path.getmtime(p) > snap:
                    r["note"] = "rewritten after the manifest snapshot (live file); recorded version differs"
        r["recoverable"] = "YES" if r["status"] == "LOCAL_ONLY" else r["recoverable"]
        if r["status"] == "CORRUPT" and r["backup"] == "VERIFIED_PACK":
            r.update(recoverable="YES", recovery_method="recorded version is in a verified encrypted phi-backup pack")
    elif state == "PRESENT":  # a directory entry without a per-file hash list
        r.update(hash_check="DIRECTORY_NO_HASH_LIST", status="UNVERIFIED", recoverable="UNKNOWN")
    else:
        r["status"] = "UNAVAILABLE"
        if r["backup"] == "VERIFIED_PACK":
            r.update(recoverable="YES", recovery_method="decrypt the verified encrypted backup pack")
        elif state.startswith("VOLUME_OFFLINE:"):
            r.update(recoverable="UNKNOWN", recovery_method="mount volume " + state.split(":", 1)[1] + " and re-run")
        else:
            r.update(recoverable="NO" if r["backup"] == "NOT_IN_BACKUP" else "UNKNOWN")
    if r["backup"] == "VERIFIED_PACK" and not r["recovery_method"]:
        r["recovery_method"] = "also in a verified encrypted phi-backup pack"
    return r


def audit(repo, state_db, hash_limit, cache_path):
    cache = HashCache(cache_path)
    rows, counts = [], {}
    for inv_dir in sorted((repo / "investigations").iterdir()):
        if (inv_dir / "data_manifest.json").exists():
            rs, c = manifest_rows(repo, inv_dir)
            rows += [(inv_dir, r) for r in rs]
            counts[inv_dir.name] = c
    backup = backup_index(state_db, {r["sha256"] for _, r in rows if r["sha256"]})
    out = [classify(r, repo, d, cache, backup, hash_limit) for d, r in rows]
    cache.save()
    return out, counts, backup


def summarize(rows, counts):
    per = defaultdict(Counter)
    scoped = [r for r in rows if r["in_scope"] == "YES"]
    for r in scoped:
        per[r["investigation"]][r["status"]] += 1
        per[r["investigation"]]["manifest:" + str(r["manifest_status"])] += 1
        per[r["investigation"]]["recoverable:" + r["recoverable"]] += 1
    total = Counter(r["status"] for r in scoped)
    return dict(
        total_rows=len(rows),
        evidence_rows=len(scoped),
        withheld_by_policy_rows=len(rows) - len(scoped),
        by_status={s: total.get(s, 0) for s in STATUSES},
        recoverable=dict(Counter(r["recoverable"] for r in scoped)),
        backup=dict(Counter(r["backup"] for r in scoped)),
        origin_state=dict(Counter(r["origin_state"] or "REPOSITORY" for r in scoped)),
        not_recoverable_or_unknown=sorted(f"{r['investigation']}/{r['path']}" for r in scoped
                                          if r["recoverable"] != "YES"),
        manifest_counts_field=counts,
        per_investigation={k: dict(sorted(v.items())) for k, v in sorted(per.items())},
    )


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[3])
    ap.add_argument("--backup-db", default=os.path.expanduser("~/.local/state/phi-backup/state.sqlite3"))
    ap.add_argument("--hash-limit", type=int, default=4 << 30)
    ap.add_argument("--out", type=Path, required=True, help="public results directory")
    ap.add_argument("--private-out", type=Path, required=True, help="local-only directory (hash cache, pack join)")
    a = ap.parse_args()
    a.private_out.mkdir(parents=True, exist_ok=True)
    rows, counts, backup = audit(a.repo, a.backup_db, a.hash_limit, a.private_out / "hash_cache.json")
    a.out.mkdir(parents=True, exist_ok=True)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=PUBLIC_FIELDS, extrasaction="ignore", lineterminator="\n")
    w.writeheader()
    for r in sorted(rows, key=lambda r: (r["investigation"], r["path"])):
        w.writerow(r)
    with gzip.GzipFile(a.out / "file_inventory.csv.gz", "wb", mtime=0) as g:
        g.write(buf.getvalue().encode())
    s = summarize(rows, counts)
    (a.out / "file_inventory_summary.json").write_text(json.dumps(s, indent=1, sort_keys=True) + "\n")
    if backup is not None:
        priv = {f"{r['investigation']}/{r['path']}": backup[r["sha256"]][0] for r in rows
                if r["sha256"] and r["sha256"] in backup}
        (a.private_out / "backup_pack_join.json").write_text(json.dumps(priv, indent=1, sort_keys=True))
    print(json.dumps({k: s[k] for k in ("total_rows", "evidence_rows", "by_status", "recoverable", "backup",
                                        "origin_state", "not_recoverable_or_unknown")}))
    sys.exit(0)
