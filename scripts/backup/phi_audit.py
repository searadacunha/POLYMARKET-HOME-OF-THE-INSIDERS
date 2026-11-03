#!/usr/bin/env python3
"""Audit of the three locations from bytes read now: every source file, every pack on the disk, every asset on GitHub.

A manifest only says which volumes to read. A file counts as present only if its SHA-256 came out of a real read of the
pack, decrypted for GitHub. Reads only, and writes only its own report.

  phi_audit.py --out DIR [--no-github]    results per pack are kept in DIR: run it again on the same DIR to resume
"""
import argparse
import gzip
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tarfile
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phi_backup as core  # noqa: E402

CATEGORIES = ("COMPLETE", "MISSING_GITHUB", "MISSING_DISK", "MISSING_BOTH", "CORRUPTED", "IN_PROGRESS", "UNRECOVERABLE")
READ_ERRORS = (OSError, EOFError, ValueError, tarfile.TarError, subprocess.SubprocessError)


def hash_stream(stream):
    digest, size = hashlib.sha256(), 0
    for chunk in iter(lambda: stream.read(core.CHUNK), b""):
        digest.update(chunk)
        size += len(chunk)
    return digest.hexdigest(), size


def read_members(stream, kind):
    """What a pack really holds. The compressed stream is read to its end, so a cut or altered volume fails its checksum."""
    source = gzip.GzipFile(fileobj=stream) if kind != "rawz" else stream
    if kind == "db":
        return {"<sqlite pages>": hash_stream(source)}
    members = {}
    with tarfile.open(fileobj=source, mode="r|") as tar:
        for member in tar:
            if member.isfile():
                members[member.name] = hash_stream(tar.extractfile(member))
    for _ in iter(lambda: source.read(core.CHUNK), b""):
        pass
    return members


def decrypt_members(cfg, kind, pump):
    """Run `pump(age stdin)` in a thread and read the decrypted pack. Returns the members and what went wrong."""
    proc = subprocess.Popen([cfg["age_bin"], "-d", "-i", os.path.expanduser(cfg["identity"])], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    errors, members = [], {}
    thread = threading.Thread(target=pump, args=(proc.stdin, errors), daemon=True)
    thread.start()
    try:
        members = read_members(proc.stdout, kind)
    except READ_ERRORS as exc:
        errors.append(f"unreadable: {type(exc).__name__}")
    for _ in iter(lambda: proc.stdout.read(core.CHUNK), b""):  # or age and the pump would block
        pass
    thread.join()
    if proc.wait() != 0:
        errors.append("age could not decrypt")
    return members, errors


def check_disk(cfg, disk, pack):
    if not disk:
        return {"members": {}, "errors": ["disk not connected"]}
    errors = []
    for which in ("clear", "enc"):
        for path, volume in core.pack_row_volumes(pack, disk, which):
            if path is None or not str(path).startswith(str(disk)) or not path.exists():
                errors.append(f"{which} volume absent: {volume['name']}")
            elif path.stat().st_size != volume["size"] or core.hash_file(path) != volume["sha"]:
                errors.append(f"{which} volume altered: {volume['name']}")
    clear = [p for p, _ in core.pack_row_volumes(pack, disk, "clear")]
    enc = [p for p, _ in core.pack_row_volumes(pack, disk, "enc")]
    if clear and all(p and p.exists() for p in clear):
        try:
            return {"members": read_members(core.ConcatReader(clear), pack["kind"]), "errors": errors}
        except READ_ERRORS as exc:
            return {"members": {}, "errors": errors + [f"unreadable: {type(exc).__name__}"]}
    if not enc or not all(p and p.exists() for p in enc):
        return {"members": {}, "errors": errors}

    def pump(sink, _errors):
        core.feed(core.ConcatReader(enc), sink)
    members, more = decrypt_members(cfg, pack["kind"], pump)
    return {"members": members, "errors": errors + more}


def check_github(cfg, gh, pack, assets):
    volumes = json.loads(pack["enc_volumes"] or "[]")
    if not volumes:
        return {"members": {}, "errors": [], "not_sent": True}  # a daily database image: only some go to GitHub

    def pump(sink, errors):
        try:
            for volume in volumes:
                asset = assets.get(volume["name"])
                if not asset or asset.get("state") != "uploaded" or asset.get("size") != volume["size"]:
                    errors.append(f"asset absent: {volume['name']}")
                    return
                download = gh.open_asset(asset["id"])
                digest = hashlib.sha256()
                for chunk in iter(lambda: download.stdout.read(core.CHUNK), b""):
                    digest.update(chunk)
                    sink.write(chunk)
                download.wait()
                if digest.hexdigest() != volume["sha"]:
                    errors.append(f"asset altered: {volume['name']}")
        except OSError as exc:
            errors.append(type(exc).__name__)
        finally:
            sink.close()
    members, errors = decrypt_members(cfg, pack["kind"], pump)
    return {"members": members, "errors": errors}


def cached(folder, name, compute):
    """A pack checked without error is not read again when the audit resumes."""
    path = folder / (name + ".json")
    if path.exists():
        return json.loads(path.read_text())
    result = compute()
    if not result["errors"]:
        folder.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result))
    return result


def load_manifest():
    """Which sha belongs in which member of which pack, and the versions kept for each path."""
    expected, versions, index = {}, {}, {}
    for name in ("index.jsonl.gz", "versions.jsonl.gz"):
        path = core.STATE / name
        if not path.exists():
            continue
        with gzip.open(path, "rt") as fh:
            for line in fh:
                row = json.loads(line)
                if row.get("pack") and row.get("sha"):
                    expected.setdefault(row["pack"], {})[row["member"]] = row["sha"]
                if name.startswith("index"):
                    index[(row["root"], row["rel"])] = row
                elif row.get("sha"):
                    versions.setdefault((row["root"], row["rel"]), set()).add(row["sha"])
    return expected, versions, index


def check_location(packs, expected, folder, check):
    """Returns the shas really read from this location, the shas that should have been and were not, and the errors."""
    present, bad, errors = {}, set(), []
    for pack in packs:
        result = cached(folder, pack["name"], lambda p=pack: check(p))
        if result.get("not_sent"):
            continue
        for problem in result["errors"]:
            errors.append(f"{pack['name']}: {problem}")
        got = {sha: size for sha, size in result["members"].values()}
        present.update(got)
        if any("absent" in e or "not connected" in e for e in result["errors"]):
            continue  # nothing there to call corrupted: its files come out as missing
        for member, sha in expected.get(pack["name"], {}).items():
            if result["members"].get(member, [None])[0] != sha:
                bad.add(sha)
    return present, bad - set(present), errors


def scan_mac(cfg):
    """Every source file, read now. The list of roots is the only thing taken from the service."""
    rows, wait = [], cfg.get("debounce_s", 300) + cfg.get("pack_max_wait_s", 3600) + 600
    for root in core.discover_roots(cfg):
        if root.get("skip_known") or (root.get("path") and not os.path.isdir(root["path"])):
            continue
        for rel, full in core.walk_root(root):
            try:
                st = os.lstat(full)
                row = {"root": root["name"], "rel": rel, "size": st.st_size, "recent": time.time() - st.st_mtime < wait}
                if stat.S_ISLNK(st.st_mode):
                    rows.append({**row, "size": 0, "link": os.readlink(full)})
                elif not stat.S_ISREG(st.st_mode):
                    continue
                elif full.endswith("-shm") or (full.endswith("-wal") and os.path.exists(full[:-4])):
                    rows.append({**row, "sidecar": True})
                elif core.is_live_db(full, st):
                    rows.append({**row, "live": True})
                else:
                    rows.append({**row, "sha": core.hash_file(full)})
            except OSError as exc:
                rows.append({"root": root["name"], "rel": rel, "size": 0, "error": type(exc).__name__})
    return rows


def classify(row, on_disk, on_gh, corrupted, versions, index):
    if row.get("error"):
        return "MISSING_BOTH"
    if row.get("sidecar"):
        return "IN_PROGRESS"  # part of a database in use, carried by its image
    if "link" in row:
        saved = index.get((row["root"], row["rel"]), {}).get("link") == row["link"]
        return "COMPLETE" if saved else ("IN_PROGRESS" if row["recent"] else "MISSING_BOTH")
    shas = versions.get((row["root"], row["rel"]), set()) if row.get("live") else {row["sha"]}
    disk, github = bool(shas & on_disk.keys()), bool(shas & on_gh.keys())
    if row.get("live") and disk and github:
        return "IN_PROGRESS"  # keeps changing, and a consistent image of it is verified in both places
    if disk and github:
        return "COMPLETE"
    if shas & corrupted:
        return "CORRUPTED"
    if row["recent"]:
        return "IN_PROGRESS"
    return "MISSING_GITHUB" if disk else ("MISSING_DISK" if github else "MISSING_BOTH")


def run(cfg, out, github=True):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    disk = core.disk_root(cfg)
    rows = scan_mac(cfg)  # first: the pack list read afterwards then covers every file this long read has seen
    packs = json.loads((core.STATE / "packs.json").read_text()) if (core.STATE / "packs.json").exists() else []
    packs = [p for p in packs if p["disk_clear"] != -2]  # released after a failed check: its files were packed again
    expected, versions, index = load_manifest()
    on_disk, bad_disk, errors_disk = check_location(packs, expected, out / "disk", lambda p: check_disk(cfg, disk, p))
    on_gh, bad_gh, errors_gh = {}, set(), []
    if github:
        gh = core.backend(cfg)
        assets = {a["name"]: a for release in gh.releases() for a in gh.assets(release["id"])}
        on_gh, bad_gh, errors_gh = check_location(packs, expected, out / "github", lambda p: check_github(cfg, gh, p, assets))
    seen = {(r["root"], r["rel"]) for r in rows}
    # What the backup holds and the Mac no longer has: not lost if it can be read, lost if it cannot.
    gone = kept = 0
    for key, row in index.items():
        if key in seen or not row.get("sha") or row["klass"] == "link":
            continue
        if row["root"] == "disk-only":
            rows.append({"root": row["root"], "rel": row["rel"], "size": row["size"], "recent": False, "sha": row["sha"]})
            continue
        gone += 1
        if row["sha"] in on_disk or row["sha"] in on_gh:
            kept += 1
        else:
            rows.append({"root": row["root"], "rel": row["rel"], "size": row["size"], "recent": False, "sha": row["sha"], "category": "UNRECOVERABLE"})
    corrupted = bad_disk | bad_gh
    counts = dict.fromkeys(CATEGORIES, 0)
    with gzip.open(out / "files.jsonl.gz", "wt") as fh:
        for row in rows:
            row.setdefault("category", classify(row, on_disk, on_gh, corrupted, versions, index))
            counts[row["category"]] += 1
            fh.write(json.dumps(row) + "\n")

    def absent(location):
        missing = [r for r in rows if r.get("sha") and r["sha"] not in location and r["category"] != "IN_PROGRESS"]
        return len(missing), sum(r["size"] for r in missing)
    regular = [r for r in rows if "link" not in r and r["category"] != "UNRECOVERABLE" and r["root"] != "disk-only"]
    hashed = [r for r in regular if r.get("sha")]
    in_disk = [r for r in rows if r.get("sha") in on_disk]
    in_gh = [r for r in rows if r.get("sha") in on_gh]
    missing_disk, missing_gh = absent(on_disk), absent(on_gh)
    stamp_disk = max((p["created"] for p in packs), default=0)
    stamp_gh = max((p.get("verified_at") or 0 for p in packs), default=0)
    summary = {
        "written": core.iso(time.time()), "counts": counts, "gone_from_mac": gone, "gone_with_copy": kept,
        "mac": {"files": len(regular), "bytes": sum(r["size"] for r in regular), "hashed": len(hashed)},
        "disk": {"files": len(in_disk), "bytes": sum(r["size"] for r in in_disk), "missing": missing_disk[0], "missing_bytes": missing_disk[1], "corrupted": len(bad_disk), "packs_with_errors": len(errors_disk), "last": core.iso(stamp_disk)},
        "github": {"files": len(in_gh), "bytes": sum(r["size"] for r in in_gh), "missing": missing_gh[0], "missing_bytes": missing_gh[1], "corrupted": len(bad_gh), "packs_with_errors": len(errors_gh), "last": core.iso(stamp_gh), "checked": github},
        "packs": len(packs), "errors": (errors_disk + errors_gh)[:200], "disk_path": str(disk) if disk else None,
        "clean": github and not any(counts[c] for c in CATEGORIES if c not in ("COMPLETE", "IN_PROGRESS")) and not errors_disk and not errors_gh,
    }
    (out / "summary.json").write_text(json.dumps(summary, indent=1))
    report = render(summary)
    (out / "AUDIT_REPORT.md").write_text(report)
    shutil.copyfile(out / "AUDIT_REPORT.md", core.STATE / "AUDIT_REPORT.md")
    if disk:
        shutil.copyfile(out / "AUDIT_REPORT.md", disk / "manifests" / "AUDIT_REPORT.md")
    return summary, report


def render(s):
    m, d, g = s["mac"], s["disk"], s["github"]
    size = core.gb
    lines = [
        "# Backup audit\n", f"Written {s['written']}. Hashes come from bytes read during this audit. {s['packs']} packs read.\n",
        "| Indicator | Mac | External disk | GitHub |\n|---|---:|---:|---:|",
        f"| Files | {m['files']:,} | {d['files']:,} | {g['files']:,} |",
        f"| Volume (before compression) | {size(m['bytes'])} | {size(d['bytes'])} | {size(g['bytes'])} |",
        f"| Verified by SHA-256 | {m['hashed']:,} | {d['files']:,} | {g['files']:,} |",
        f"| Missing | n/a | {d['missing']:,} | {g['missing']:,} |",
        f"| Corrupted | n/a | {d['corrupted']:,} | {g['corrupted']:,} |",
        f"| Remaining to transfer | n/a | {size(d['missing_bytes'])} | {size(g['missing_bytes'])} |",
        f"| Last synchronisation | now | {d['last']} | {g['last']} |\n",
        "| Category | Files |\n|---|---:|",
    ]
    lines += [f"| {name} | {n:,} |" for name, n in s["counts"].items()]
    lines.append(f"\nGone from the Mac: {s['gone_from_mac']:,}, of which still readable in the backup: {s['gone_with_copy']:,}.")
    if s["errors"]:
        lines += ["\n## Errors\n"] + [f"- {e}" for e in s["errors"]]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", required=True)
    parser.add_argument("--no-github", action="store_true")
    args = parser.parse_args()
    os.nice(15)  # the collectors come first
    summary, report = run(core.load_config(), args.out, github=not args.no_github)
    print(report)
    return 0 if summary["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
