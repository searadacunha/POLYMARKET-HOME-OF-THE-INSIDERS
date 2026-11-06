#!/usr/bin/env python3
"""Copy one investigation into investigations/<id>/sources/, read-only on the origin.

Every file of the origin ends up in data_manifest.json with its size and SHA-256, whether it
was imported or not, and why. Relative paths are kept so that scripts still find their files.

  python3 scripts/import_snapshot.py --id <id> --origin <folder>

Rules per investigation live in scripts/import_rules.json. The default rules are enough for a
new investigation: raw HTTP caches, large files, secrets and profile fields stay out.
"""
import argparse
import fnmatch
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phi_lib as lib  # noqa: E402

EXCLUDED_DIRS = {".venv": "environment, rebuilt from requirements.lock",
                 "__pycache__": "Python cache", ".git": "git history, handled separately",
                 "node_modules": "dependencies", "graphify-out": "derived graph, can be regenerated",
                 ".pytest_cache": "cache", ".claude": "local settings"}
# A copied .gitignore would make git silently drop imported evidence.
EXCLUDED_NAMES = (".DS_Store", "*.pyc", ".env", ".env.*", "*.pem", "*.key", "*.sqlite3-shm", "*.sqlite3-wal", "*.swp",
                  ".gitignore", ".gitattributes", ".gitmodules")
RAW_CACHE_PARTS = ("http_cache/", "raw/http/")
DEFAULT_LOCAL_ONLY_EXT = {".sqlite3", ".sqlite", ".db", ".zst", ".zip", ".pkl", ".parquet", ".tar", ".tgz", ".npy"}
GZ_SCAN_LIMIT = 40_000_000
HASH_LIST_NAME = "local_only_hashes.sha256.gz"


def matches(rel, patterns):
    return any(rel == p.rstrip("/") or rel.startswith(p if p.endswith("/") else p + "/") or fnmatch.fnmatch(rel, p)
               for p in patterns)


def group_of(rel, rules):
    """Large sets of local files get one manifest line; their hashes go to a compressed list."""
    for part in RAW_CACHE_PARTS:
        if part in rel:
            return rel[:rel.index(part) + len(part)]
    return next((p for p in rules.get("summarize", []) if matches(rel, [p])), None)


def now_utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def mtime_utc(st):
    return datetime.fromtimestamp(st.st_mtime, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def classify(rel, st, rules):
    """Decide from the name and size alone. Content checks come after the hash."""
    if matches(rel, rules.get("live", [])):
        return "local_only", "live file, written continuously: no stable hash", False
    if any(part in rel for part in RAW_CACHE_PARTS):
        return "local_only", "raw HTTP cache: may hold profile fields", True
    if matches(rel, rules.get("local_only", [])):
        return "local_only", rules.get("local_only_reason", "kept out of git by this investigation's rules"), True
    if Path(rel).name in lib.AGENT_FILES:
        return "local_only", "agent working file, not for publication", True
    if st.st_size > lib.MAX_FILE_BYTES:
        return "local_only", f"larger than {lib.MAX_FILE_BYTES // 1_000_000} MB", True
    suffix = Path(rel).suffix.lower()
    if suffix in DEFAULT_LOCAL_ONLY_EXT:
        return "local_only", "binary format the scan cannot read", True
    if suffix in lib.IMAGE_EXT:
        return "local_only", "image or PDF: the scan cannot read it, may be third-party content", True
    return "imported", "", True


def walk(origin, only=None):
    """Return (files, excluded entries), noting excluded directories once instead of descending into them.

    only: file names to consider. Everything else in a folder shared with unrelated notes stays unlisted.
    """
    excluded = []
    files = []
    for dirpath, dirnames, filenames in os.walk(origin, followlinks=False):
        for name in sorted(dirnames):
            full = os.path.join(dirpath, name)
            if name in EXCLUDED_DIRS or os.path.islink(full):
                dirnames.remove(name)
                rel = os.path.relpath(full, origin)
                reason = "symbolic link" if os.path.islink(full) else EXCLUDED_DIRS[name]
                excluded.append({"path": rel + "/", "status": "excluded", "reason": reason})
        for name in sorted(filenames):
            if only is not None and name not in only:
                continue
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, origin)
            try:
                st = os.lstat(full)
            except OSError as exc:
                excluded.append({"path": rel, "status": "unreadable", "reason": str(exc)})
                continue
            if os.path.islink(full):
                excluded.append({"path": rel, "status": "excluded", "reason": "symbolic link to " + os.readlink(full).replace(os.path.expanduser("~"), "~")})
            elif any(fnmatch.fnmatch(name, pattern) for pattern in EXCLUDED_NAMES):
                excluded.append({"path": rel, "status": "excluded", "reason": "name reserved for secrets, git or the system"})
            else:
                files.append((rel, st))
    return files, excluded


def copy_with_hash(src, dst):
    """Hash exactly the bytes that are copied, so that a file changing during the copy cannot mislead."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256()
    with open(src, "rb") as fin, open(dst, "wb") as fout:
        for chunk in iter(lambda: fin.read(1 << 20), b""):
            digest.update(chunk)
            fout.write(chunk)
    st = os.stat(src)
    os.utime(dst, (st.st_atime, st.st_mtime))
    return digest.hexdigest()


def scan_file(path, suffix, known):
    """Scan a candidate before it enters the repo. Returns (hits, skip reason)."""
    if suffix == ".gz" and os.path.getsize(path) > GZ_SCAN_LIMIT:
        return [], "gzip too large for the scan"
    try:
        return lib.scan_bytes(lib.read_for_scan(path), known), ""
    except (OSError, EOFError, ValueError) as exc:
        return [], f"unreadable by the scan: {type(exc).__name__}"


def import_investigation(inv_id, origin, rules, known, repo=lib.REPO, dedupe_index=None, log=print):
    # An invalid id could otherwise escape investigations/ and delete an
    # unrelated sources/ directory at the start of a replacement import.
    if not isinstance(inv_id, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", inv_id):
        raise SystemExit("invalid investigation id (use lowercase letters, digits and hyphens)")
    origin = Path(origin).expanduser().resolve()
    if not origin.is_dir():
        raise SystemExit(f"origin not found: {origin}")
    inv_dir = Path(repo).resolve() / "investigations" / inv_id
    sources = inv_dir / "sources"
    # Never remove the input tree, or any of its ancestors, while replacing
    # sources/. Resolve symlinks before checking this relationship.
    destination = sources.resolve()
    if origin == destination or origin in destination.parents or destination in origin.parents:
        raise SystemExit("origin and sources destination must not overlap")
    if sources.exists():
        shutil.rmtree(sources)
    files, entries = walk(origin, set(rules["only"]) if "only" in rules else None)
    summaries = {}
    group_hashes = []
    counts = {"imported": 0, "local_only": 0, "duplicate": 0, "refused": 0}
    imported_bytes = 0
    budget = rules.get("budget_bytes", 400_000_000)
    for rel, st in files:
        full = origin / rel
        status, reason, hashable = classify(rel, st, rules)
        group = group_of(rel, rules)
        if group and status != "imported":
            summary = summaries.setdefault(group, {"path": group, "status": status, "reason": reason, "files": 0, "size": 0})
            summary["files"] += 1
            summary["size"] += st.st_size
            if hashable:
                try:
                    group_hashes.append(f"{lib.sha256_file(full)}  {rel}")
                except OSError as exc:
                    group_hashes.append(f"UNREADABLE({type(exc).__name__})  {rel}")
            continue
        entry = {"path": rel, "size": st.st_size, "mtime_utc": mtime_utc(st), "status": status}
        if reason:
            entry["reason"] = reason
        try:
            if status == "imported":
                suffix = Path(rel).suffix.lower()
                hits, skip = scan_file(full, suffix, known)
                if hits or skip:
                    entry.update(status="refused" if hits else "local_only",
                                 reason=("scan: " + ", ".join(sorted(set(hits)))) if hits else skip,
                                 sha256=lib.sha256_file(full))
                elif imported_bytes + st.st_size > budget:
                    entry.update(status="local_only", reason="investigation budget exceeded", sha256=lib.sha256_file(full))
                else:
                    target = sources / rel
                    digest = copy_with_hash(full, target)
                    entry["sha256"] = digest
                    copied_size = target.stat().st_size
                    entry["size"] = copied_size
                    # The source can change between the first scan and the
                    # copy, especially while another session is collecting.
                    # Validate the exact bytes whose digest we publish.
                    copied_hits, copied_skip = scan_file(target, suffix, known)
                    if copied_hits or copied_skip:
                        target.unlink()
                        entry.update(status="refused" if copied_hits else "local_only",
                                     reason=("scan: " + ", ".join(sorted(set(copied_hits)))) if copied_hits else copied_skip)
                    elif copied_size > lib.MAX_FILE_BYTES or imported_bytes + copied_size > budget:
                        target.unlink()
                        entry.update(status="local_only", reason="copied file exceeds the size or investigation budget")
                    else:
                        entry["repo_path"] = f"investigations/{inv_id}/sources/{rel}"
                        previous = dedupe_index.get(digest) if dedupe_index is not None else None
                        if previous and copied_size > 0:
                            target.unlink()
                            entry.update(status="duplicate", repo_path=previous, reason="same content already imported")
                        else:
                            imported_bytes += copied_size
            elif hashable:
                entry["sha256"] = lib.sha256_file(full)
            else:
                entry["sha256"] = None
        except OSError as exc:
            entry.update(status="unreadable", reason=str(exc))
        counts[entry["status"]] = counts.get(entry["status"], 0) + 1
        entries.append(entry)
    for summary in summaries.values():
        summary["sha256_list"] = HASH_LIST_NAME
        counts[summary["status"]] = counts.get(summary["status"], 0) + summary["files"]
        entries.append(summary)
    inv_dir.mkdir(parents=True, exist_ok=True)
    hash_list = inv_dir / HASH_LIST_NAME
    if group_hashes:
        # mtime=0 keeps the archive identical when nothing changed.
        with open(hash_list, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0, filename="") as fh:
            fh.write(("\n".join(sorted(group_hashes, key=lambda line: line.split("  ", 1)[1])) + "\n").encode())
    elif hash_list.exists():
        hash_list.unlink()
    entries.sort(key=lambda e: e["path"])
    # shortcut: empty directories are not recorded, git could not keep them anyway.
    manifest = {
        "id": inv_id,
        "origin": str(origin).replace(os.path.expanduser("~"), "~"),
        "snapshot_utc": now_utc(),
        "note": "local_only: present on the original machine only, NOT archived here.",
        "counts": counts,
        "imported_bytes": imported_bytes,
        "files": entries,
    }
    (inv_dir / "data_manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    log(f"{inv_id}: {counts}; {imported_bytes / 1e6:.1f} MB imported")
    return manifest


def add_to_index(index, manifest):
    """Files of another investigation can stand in for a copy; inside one investigation every path stays in place."""
    for entry in (manifest or {"files": []})["files"]:
        if entry.get("status") == "imported":
            index.setdefault(entry["sha256"], entry["repo_path"])


def load_rules(inv_id):
    path = Path(__file__).resolve().parent / "import_rules.json"
    return json.loads(path.read_text()).get(inv_id, {}) if path.exists() else {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--id", required=True)
    parser.add_argument("--origin", required=True)
    args = parser.parse_args()
    known = lib.known_secret_values(lib.env_files_from_environment())
    rules = load_rules(args.id)
    index = {}
    # Only declared families: a re-import elsewhere must never break this investigation's files.
    for other in rules.get("dedupe_against", []):
        add_to_index(index, lib.load_manifest(lib.REPO / "investigations" / other))
    import_investigation(args.id, args.origin, rules, known, dedupe_index=index)


if __name__ == "__main__":
    main()
