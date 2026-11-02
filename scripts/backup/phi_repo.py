#!/usr/bin/env python3
"""GitHub side of the backup: merge pull requests under checks, publish snapshots of running investigations,
mirror the repository to the disk. Never force-pushes, never rewrites history, never changes a finding by itself.
"""
import gzip
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

import phi_backup as core

TRAILER = "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
ILLEGAL_ON_FAT = re.compile(r'[<>:"\\|?*\x00-\x1f]')


def git(clone, *args, check=True):
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    result = subprocess.run(["git", "-C", str(clone), *args], capture_output=True, text=True, env=env)
    if check and result.returncode != 0:
        raise OSError(f"git {args[0]}: {result.stderr.strip()[:200]}")
    return result.stdout.strip()


def gh(cfg, *args):
    result = subprocess.run([cfg["gh_bin"], *args], capture_output=True, text=True, timeout=300)
    if result.returncode != 0:
        raise OSError(f"gh {args[0]}: {result.stderr.strip()[:200]}")
    return result.stdout.strip()


def python(clone, *args):
    """Run a repository script. Returns (ok, last lines): errors are shown without file contents."""
    result = subprocess.run([sys.executable, *args], cwd=str(clone), capture_output=True, text=True, timeout=3600)
    return result.returncode == 0, (result.stdout + result.stderr).strip()[-500:]


def clean_main(clone):
    if git(clone, "status", "--porcelain", "-uno"):
        core.log("repo_skip", reason="tracked files changed in the central clone")
        return False
    git(clone, "fetch", "-q", "origin", "--prune")
    git(clone, "switch", "-q", "main")
    git(clone, "merge", "-q", "--ff-only", "origin/main")
    return True


def findings_of(clone, ref, inv):
    text = subprocess.run(["git", "-C", str(clone), "show", f"{ref}:investigations/{inv}/FINDINGS.md"], capture_output=True, text=True).stdout
    return {m.group(1): m.group(2) for m in re.finditer(r"^## (F-\d{3,}) \| ([A-Z]+) \|", text, re.M)}


def review_hold(clone, inv, head):
    """Reasons a person must look first: a finding removed or a level changed. Hypotheses must not become proofs unseen."""
    old, new = findings_of(clone, "origin/main", inv), findings_of(clone, head, inv)
    removed = sorted(set(old) - set(new))
    changed = sorted(k for k in old if k in new and old[k] != new[k])
    reasons = []
    if removed:
        reasons.append("removes " + ", ".join(removed))
    if changed:
        reasons.append("changes the level of " + ", ".join(f"{k} {old[k]} to {new[k]}" for k in changed))
    return reasons


def merge_prs(cfg, db, clone):
    prs = json.loads(gh(cfg, "pr", "list", "--repo", cfg["repo"], "--state", "open", "--json", "number,headRefName,baseRefName,headRefOid,title"))
    holds = core.kv_get(db, "holds", {})
    open_ids = set()
    for pr in prs:
        match = re.fullmatch(r"investigation/([a-z0-9-]+)", pr["headRefName"])
        if not match or pr["baseRefName"] != "main":
            continue
        inv, head, label = match.group(1), pr["headRefOid"], f"PR #{pr['number']} {pr['headRefName']}"
        open_ids.add(inv)
        if core.kv_get(db, f"pr_seen:{pr['number']}") == head:
            continue
        core.kv_set(db, f"pr_seen:{pr['number']}", head)
        git(clone, "fetch", "-q", "origin", pr["headRefName"])
        outside = [f for f in git(clone, "diff", "--name-only", f"origin/main...{head}").splitlines() if not f.startswith(f"investigations/{inv}/")]
        reasons = [f"touches {len(outside)} files outside its folder"] if outside else []
        reasons += review_hold(clone, inv, head)
        if not reasons:
            git(clone, "switch", "-q", "--detach", "origin/main")
            merged = subprocess.run(["git", "-C", str(clone), "merge", "-q", "--no-commit", "--no-ff", head], capture_output=True).returncode == 0
            if not merged:
                reasons.append("does not merge cleanly, the session must merge main first")
            else:
                for script in (["scripts/test_phi.py"], ["scripts/validate_evidence.py"]):
                    ok, tail = python(clone, *script)
                    if not ok:
                        reasons.append(f"{script[0]} failed: {tail[-160:]}")
                check = clone / "investigations" / inv / "tests" / "check_published.py"
                if check.exists():
                    ok, tail = python(clone, str(check))
                    if not ok:
                        reasons.append(f"check_published failed: {tail[-160:]}")
            subprocess.run(["git", "-C", str(clone), "merge", "--abort"], capture_output=True)
            git(clone, "reset", "-q", "--hard", "origin/main")
            git(clone, "switch", "-q", "main")
        if reasons:
            holds[label] = "; ".join(reasons)
            core.log("pr_hold", pr=pr["number"], reasons=reasons)
            continue
        gh(cfg, "pr", "merge", str(pr["number"]), "--repo", cfg["repo"], "--squash", "--match-head-commit", head, "--subject", pr["title"], "--body", "Merged by the central service after tests, validation and secret scan." + TRAILER)
        holds.pop(label, None)
        core.log("pr_merged", pr=pr["number"])
        git(clone, "fetch", "-q", "origin")
        git(clone, "merge", "-q", "--ff-only", "origin/main")
        core.kv_set(db, "generated_stale", True)
    core.kv_set(db, "holds", holds)
    return open_ids


def set_status_time(clone, inv):
    manifest = json.loads((clone / "investigations" / inv / "data_manifest.json").read_text())
    path = clone / "investigations" / inv / "STATUS.md"
    path.write_text(re.sub(r"^updated_utc: .*$", f"updated_utc: {manifest['snapshot_utc']}", path.read_text(), count=1, flags=re.M))


def auto_snapshots(cfg, db, clone, open_ids):
    """Publish what a running investigation already has. Only sources and the manifest change, findings stay its own."""
    for inv, spec in cfg.get("investigations", {}).items():
        origin = os.path.expanduser(spec["origin"])
        if inv in open_ids or not spec.get("auto") or not os.path.isdir(origin):
            continue
        last = core.kv_get(db, f"import:{inv}", 0)
        changed = db.execute("SELECT MAX(last_hashed) FROM files WHERE root=?", (spec["root"],)).fetchone()[0] or 0
        settled = time.time() - changed > cfg.get("snapshot_settle_s", 900)
        if changed <= last or time.time() - last < spec.get("min_hours", 1) * 3600 or not settled:
            continue
        core.beat()
        ok, tail = python(clone, "scripts/import_snapshot.py", "--id", inv, "--origin", origin)
        if ok:
            set_status_time(clone, inv)
            ok, tail = python(clone, "scripts/validate_evidence.py", f"investigations/{inv}", "--fill")
        holds = core.kv_get(db, "holds", {})
        if not ok:
            git(clone, "checkout", "-q", "--", f"investigations/{inv}")
            git(clone, "clean", "-fdq", f"investigations/{inv}")
            holds[f"snapshot {inv}"] = tail[-300:]
            core.kv_set(db, "holds", holds)
            core.kv_set(db, f"import:{inv}", time.time())
            core.log("snapshot_refused", inv=inv)
            continue
        holds.pop(f"snapshot {inv}", None)
        core.kv_set(db, "holds", holds)
        git(clone, "add", "-A", "--", f"investigations/{inv}")
        if git(clone, "diff", "--cached", "--name-only"):
            branch = f"auto-sync/{inv}-{core.stamp()}"
            git(clone, "switch", "-q", "-c", branch)
            git(clone, "commit", "-q", "-m", f"{inv}: snapshot of the source folder{TRAILER}")
            git(clone, "push", "-q", "-u", "origin", branch)
            gh(cfg, "pr", "create", "--repo", cfg["repo"], "--base", "main", "--head", branch, "--title", f"{inv}: snapshot of the source folder", "--body", "Automatic snapshot. Only sources, manifest, hashes and the update time changed; findings and state are untouched. Validation passed.")
            gh(cfg, "pr", "merge", branch, "--repo", cfg["repo"], "--squash", "--delete-branch", "--subject", f"{inv}: snapshot of the source folder", "--body", "Validation passed." + TRAILER)
            git(clone, "switch", "-q", "main")
            git(clone, "fetch", "-q", "origin", "--prune")
            git(clone, "merge", "-q", "--ff-only", "origin/main")
            git(clone, "branch", "-qD", branch)
            core.kv_set(db, "generated_stale", True)
            core.log("snapshot_published", inv=inv)
        core.kv_set(db, f"import:{inv}", time.time())


def blob_id(data):
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def mirror_to_disk(cfg, db, disk, clone):
    """GitHub to disk: a bare mirror for the history, and a readable copy of investigations/."""
    mirror = disk / "git-backups" / "Polymarket-Home-of-the-Insiders.git"
    url = f"https://github.com/{cfg['repo']}.git"
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    if not (mirror / "HEAD").exists():
        subprocess.run(["git", "clone", "-q", "--mirror", url, str(mirror)], check=True, env=env, capture_output=True, timeout=3600)
        subprocess.run(["git", "-C", str(mirror), "config", "core.fileMode", "false"], check=True)
    else:
        subprocess.run(["git", "-C", str(mirror), "remote", "update", "--prune"], check=True, env=env, capture_output=True, timeout=3600)
    head = git(mirror, "rev-parse", "refs/heads/main")
    if core.kv_get(db, "exported_head") == head:
        return
    known = {r["rel"]: r["sha"] for r in db.execute("SELECT rel, sha FROM exports")}
    failures = 0
    for line in git(mirror, "ls-tree", "-r", "main", "--", "investigations").splitlines():
        meta, path = line.split("\t", 1)
        blob = meta.split()[2]
        rel = ILLEGAL_ON_FAT.sub("_", path.strip('"'))
        if known.get(rel) == blob:
            continue
        data = subprocess.run(["git", "-C", str(mirror), "cat-file", "blob", blob], capture_output=True).stdout
        target = disk / rel
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and rel in known and blob_id(target.read_bytes()) != known[rel]:
                # Someone changed this copy on the disk: keep both.
                os.replace(target, target.with_name(f"{target.name}.disk-{core.stamp()}"))
            target.write_bytes(data)
            db.execute("INSERT OR REPLACE INTO exports VALUES(?,?)", (rel, blob))
        except OSError as exc:
            failures += 1
            core.log("export_error", rel=rel, error=type(exc).__name__)
        core.beat()
    core.kv_set(db, "exported_head", head)
    core.log("exported", head=head[:7], failures=failures)


def registry_and_missing(cfg, db, clone):
    """Investigations still running, and files that a repository manifest lists but the source no longer has."""
    registry, by_root, total, samples = [], {}, 0, []
    for inv_dir in sorted((clone / "investigations").iterdir()):
        status = inv_dir / "STATUS.md"
        if not status.exists():
            continue
        state = re.search(r"^state: (\S+)", status.read_text(), re.M)
        spec = cfg.get("investigations", {}).get(inv_dir.name, {})
        origin = os.path.expanduser(spec.get("origin", ""))
        if state and state.group(1) == "IN_PROGRESS":
            reports = len(list(Path(origin).glob("reports/*.md"))) if origin else 0
            last = db.execute("SELECT MAX(mtime_ns) FROM files WHERE root=?", (spec.get("root", ""),)).fetchone()[0] or 0
            registry.append({"id": inv_dir.name, "state": state.group(1), "reports": reports, "last_change": last / 1e9, "origin": spec.get("origin")})
        manifest_path = inv_dir / "data_manifest.json"
        if not manifest_path.exists() or not origin or not os.path.isdir(origin):
            continue
        paths = [e["path"] for e in json.loads(manifest_path.read_text())["files"] if "size" in e and e.get("status") in ("imported", "local_only", "refused", "duplicate") and "files" not in e]
        hashes = inv_dir / "local_only_hashes.sha256.gz"
        if hashes.exists():
            with gzip.open(hashes, "rt") as fh:
                paths += [line.split("  ", 1)[1].rstrip("\n") for line in fh if "  " in line]
        gone = [p for p in paths if not os.path.lexists(os.path.join(origin, p))]
        if gone:
            by_root[spec.get("root", inv_dir.name)] = len(gone)
            total += len(gone)
            samples += [f"{inv_dir.name}/{p}" for p in gone[:20]]
        core.beat()
    core.kv_set(db, "pending_registry", registry)
    core.kv_set(db, "missing", {"count": total, "by_root": by_root, "samples": samples[:200]})
    return registry


def publish_generated(cfg, db, clone, registry):
    """Reports and backup status, batched: at most once an hour unless a merge just happened."""
    stale = core.kv_get(db, "generated_stale", False)
    if not stale and time.time() - core.kv_get(db, "generated_at", 0) < cfg.get("publish_every_s", 3600):
        return
    python(clone, "scripts/build_master_report.py")
    folder = clone / "datasets" / "backup"
    folder.mkdir(parents=True, exist_ok=True)
    if (core.STATE / "BACKUP_STATUS.md").exists():
        shutil.copyfile(core.STATE / "BACKUP_STATUS.md", clone / "BACKUP_STATUS.md")
    if (core.STATE / "packs.json").exists():
        packs = json.loads((core.STATE / "packs.json").read_text())
        (folder / "packs.json").write_text(json.dumps(packs, indent=0) + "\n")
    (folder / "pending.json").write_text(json.dumps(registry, indent=1) + "\n")
    week = time.strftime("%Y-%W", time.gmtime())
    if core.kv_get(db, "index_committed_week") != week and (core.STATE / "index.jsonl.gz").exists():
        shutil.copyfile(core.STATE / "index.jsonl.gz", folder / "index-latest.jsonl.gz")
        core.kv_set(db, "index_committed_week", week)
    git(clone, "add", "-A", "--", "BACKUP_STATUS.md", "MASTER_REPORT.md", "INVENTORY.md", "datasets")
    if git(clone, "diff", "--cached", "--name-only"):
        git(clone, "commit", "-q", "-m", f"Update backup status and generated reports{TRAILER}")
        result = subprocess.run(["git", "-C", str(clone), "push", "-q", "origin", "main"], capture_output=True, text=True, env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
        if result.returncode != 0:
            core.log("push_error", error=result.stderr.strip()[:200])
            return
    core.kv_set(db, "generated_stale", False)
    core.kv_set(db, "generated_at", time.time())


def pass_repo(cfg):
    db = core.open_db()
    if core.on_low_battery():
        return
    clone = Path(os.path.expanduser(cfg["clone"]))
    disk = core.disk_root(cfg)
    if disk:
        try:
            mirror_to_disk(cfg, db, disk, clone)
        except (OSError, subprocess.SubprocessError) as exc:
            core.log("mirror_error", error=type(exc).__name__)
    if not clean_main(clone):
        return
    open_ids = merge_prs(cfg, db, clone)
    auto_snapshots(cfg, db, clone, open_ids)
    registry = registry_and_missing(cfg, db, clone)
    publish_generated(cfg, db, clone, registry)
