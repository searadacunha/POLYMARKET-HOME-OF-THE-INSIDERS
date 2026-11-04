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
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path

import phi_backup as core

TRAILER = "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>\n"
ILLEGAL_ON_FAT = re.compile(r'[<>:"\\|?*\x00-\x1f]')
REPORT_PATHS = ("MASTER_REPORT.md", "INVENTORY.md", "datasets/manifests/local_only.json")
GENERATED_PATHS = REPORT_PATHS + ("BACKUP_STATUS.md", "datasets/backup/packs.json",
                                 "datasets/backup/pending.json", "datasets/backup/index-latest.jsonl.gz")
PUBLICATION_CHECKS = (("scripts/test_publication.py",),
                      ("research_notes/relay-followup-2026-11-04/verify.py",),
                      ("scripts/test_phi.py",), ("scripts/test_integrity_regressions.py",),
                      ("scripts/test_parallel_publication.py",),
                      ("scripts/validate_evidence.py",), ("scripts/build_master_report.py", "--check"))


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
    result = subprocess.run([sys.executable, *args], cwd=str(clone), capture_output=True, text=True,
                            env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"), timeout=3600)
    return result.returncode == 0, (result.stdout + result.stderr).strip()[-500:]


def clean_main(clone):
    if git(clone, "status", "--porcelain", "-uno"):
        core.log("repo_skip", reason="tracked files changed in the central clone")
        return False
    if git(clone, "symbolic-ref", "--quiet", "--short", "HEAD", check=False) != "main":
        core.log("repo_skip", reason="central clone is not on main")
        return False
    git(clone, "fetch", "-q", "origin", "--prune")
    if git(clone, "rev-list", "--count", "origin/main..main") != "0":
        core.log("repo_skip", reason="local main has unpublished commits; preserve and review them")
        return False
    git(clone, "merge", "-q", "--ff-only", "origin/main")
    return True


@contextmanager
def temporary_worktree(clone, ref):
    """Only this disposable worktree is cleaned; the caller's index is never used."""
    with tempfile.TemporaryDirectory(prefix="phi-publication-") as directory:
        work = Path(directory) / "candidate"
        git(clone, "worktree", "add", "--quiet", "--detach", str(work), ref)
        try:
            yield work
        finally:
            git(clone, "worktree", "remove", "--force", str(work))


def stage_publication(work, paths, investigation=None):
    changed = set(filter(None, git(work, "diff", "--name-only", "-z", "HEAD").split("\0")))
    changed.update(filter(None, git(work, "ls-files", "--others", "--exclude-standard", "-z").split("\0")))
    outside = [p for p in changed if p not in paths and not (investigation and p.startswith(f"investigations/{investigation}/"))]
    if outside:
        raise OSError(f"publication changed {len(outside)} paths outside its scope")
    if changed:
        git(work, "add", "-A", "--", *sorted(changed))
    return bool(changed)


def check_candidate(work, base):
    commands = (("scripts/check_publication.py", "--target", "main", "--candidate", "HEAD", "--base-ref", base),) + PUBLICATION_CHECKS
    for command in commands:
        ok, tail = python(work, *command)
        if not ok:
            return f"{command[0]} failed: {tail[-160:]}"
    return None


def ci_hold(cfg, pr, head):
    """A missing or pending run is a hold, rechecked on the next service pass."""
    current = json.loads(gh(cfg, "pr", "view", str(pr["number"]), "--repo", cfg["repo"],
                            "--json", "headRefOid,baseRefName,isDraft"))
    if current.get("isDraft", True):
        return "draft PR awaits review"
    if current.get("headRefOid") != head or current.get("baseRefName") != "main":
        return "PR head or destination changed; retry the current version"
    runs = json.loads(gh(cfg, "run", "list", "--repo", cfg["repo"], "--workflow", "repository-integrity.yml",
                         "--event", "pull_request", "--commit", head, "--limit", "100",
                         "--json", "databaseId,headSha,headBranch,status,conclusion,updatedAt"))
    matching = [r for r in runs if r.get("headSha") == head and r.get("headBranch") == pr["headRefName"]]
    if not matching:
        return "Repository integrity has no run for this PR head yet"
    latest = max(matching, key=lambda r: (r.get("updatedAt", ""), r["databaseId"]))
    if latest.get("status") != "completed" or latest.get("conclusion") != "success":
        return f"Repository integrity is {latest.get('conclusion') or latest.get('status')} for this PR head"
    return None


def refresh_snapshot(cfg, clone, pr, base):
    """Integrate main into a service snapshot, resolving only generated reports."""
    with temporary_worktree(clone, pr["headRefOid"]) as work:
        result = subprocess.run(["git", "-C", str(work), "merge", "--no-commit", "--no-ff", base], capture_output=True)
        conflicts = set(git(work, "diff", "--name-only", "--diff-filter=U").splitlines())
        if result.returncode and (not conflicts or not conflicts.issubset(REPORT_PATHS)):
            return "snapshot conflicts with current main; review the source changes"
        ok, tail = python(work, "scripts/build_master_report.py")
        if not ok:
            return f"snapshot reports failed: {tail[-160:]}"
        git(work, "add", "-A", "--", *REPORT_PATHS)
        git(work, "commit", "-q", "-m", "Integrate current main into the pending snapshot")
        reason = check_candidate(work, base)
        if reason:
            return reason
        git(work, "push", "-q", "origin", f"HEAD:refs/heads/{pr['headRefName']}")
    return "snapshot updated with current main; waiting for Repository integrity"


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
    prs = json.loads(gh(cfg, "pr", "list", "--repo", cfg["repo"], "--state", "open", "--json", "number,headRefName,baseRefName,headRefOid,title,isDraft"))
    holds = core.kv_get(db, "holds", {})
    open_ids = set()
    for pr in prs:
        match = re.fullmatch(r"investigation/([a-z0-9-]+)", pr["headRefName"])
        snapshot = re.fullmatch(r"auto-sync/([a-z0-9-]+)-\d{8}-\d{6}", pr["headRefName"])
        if snapshot and snapshot.group(1) in cfg.get("investigations", {}):
            match = snapshot
        if not match or pr["baseRefName"] != "main":
            continue
        inv, head, label = match.group(1), pr["headRefOid"], f"PR #{pr['number']} {pr['headRefName']}"
        open_ids.add(inv)
        reasons = ["draft PR awaits review"] if pr.get("isDraft", True) else []
        try:
            if not reasons:
                git(clone, "fetch", "-q", "origin", "--prune")
                base = git(clone, "rev-parse", "origin/main")
                outside = [f for f in git(clone, "diff", "--name-only", f"{base}...{head}").splitlines()
                           if not f.startswith(f"investigations/{inv}/") and not (snapshot and f in REPORT_PATHS)]
                reasons += [f"touches {len(outside)} files outside its scope"] if outside else []
                reasons += review_hold(clone, inv, head)
                ancestor = subprocess.run(["git", "-C", str(clone), "merge-base", "--is-ancestor", base, head], capture_output=True)
                if not reasons and ancestor.returncode:
                    reasons.append(refresh_snapshot(cfg, clone, pr, base) if snapshot else "session must merge current main before publication")
            if not reasons:
                reason = ci_hold(cfg, pr, head)
                if reason:
                    reasons.append(reason)
            if not reasons:
                with temporary_worktree(clone, head) as work:
                    reason = check_candidate(work, base)
                    if reason:
                        reasons.append(reason)
                    check = work / "investigations" / inv / "tests" / "check_published.py"
                    if not reasons and check.exists():
                        ok, tail = python(work, str(check))
                        if not ok:
                            reasons.append(f"check_published failed: {tail[-160:]}")
            if not reasons:
                git(clone, "fetch", "-q", "origin", "main")
                if git(clone, "rev-parse", "origin/main") != base:
                    reasons.append("main changed during checks; retry against its current version")
                else:
                    reason = ci_hold(cfg, pr, head)
                    if reason:
                        reasons.append(reason)
            if not reasons:
                gh(cfg, "pr", "merge", str(pr["number"]), "--repo", cfg["repo"], "--squash", "--match-head-commit", head,
                   "--subject", pr["title"], "--body", "Merged after current-head Repository integrity and local publication checks." + TRAILER)
        except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
            reasons.append(f"publication check unavailable: {type(exc).__name__}")
        if reasons:
            holds[label] = "; ".join(reasons)
            core.log("pr_hold", pr=pr["number"], reasons=reasons)
            continue
        holds.pop(label, None)
        core.log("pr_merged", pr=pr["number"])
        core.kv_set(db, "generated_stale", True)
    core.kv_set(db, "holds", holds)
    return open_ids


def set_status_time(clone, inv):
    manifest = json.loads((clone / "investigations" / inv / "data_manifest.json").read_text())
    path = clone / "investigations" / inv / "STATUS.md"
    path.write_text(re.sub(r"^updated_utc: .*$", f"updated_utc: {manifest['snapshot_utc']}", path.read_text(), count=1, flags=re.M))


def auto_snapshots(cfg, db, clone, open_ids):
    """Queue snapshots for CI; merge_prs revisits them on subsequent passes."""
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
        holds = core.kv_get(db, "holds", {})
        try:
            git(clone, "fetch", "-q", "origin", "--prune")
            base = git(clone, "rev-parse", "origin/main")
            with temporary_worktree(clone, base) as work:
                ok, tail = python(work, "scripts/import_snapshot.py", "--id", inv, "--origin", origin)
                if not ok:
                    raise OSError(f"snapshot import failed: {tail[-160:]}")
                set_status_time(work, inv)
                for command in (("scripts/validate_evidence.py", f"investigations/{inv}", "--fill"), ("scripts/build_master_report.py",)):
                    ok, tail = python(work, *command)
                    if not ok:
                        raise OSError(f"{command[0]} failed: {tail[-160:]}")
                if stage_publication(work, REPORT_PATHS, inv):
                    git(work, "commit", "-q", "-m", f"{inv}: snapshot of the source folder{TRAILER}")
                    reason = check_candidate(work, base)
                    if reason:
                        raise OSError(reason)
                    branch = f"auto-sync/{inv}-{core.stamp()}"
                    git(work, "push", "-q", "origin", f"HEAD:refs/heads/{branch}")
                    gh(cfg, "pr", "create", "--repo", cfg["repo"], "--base", "main", "--head", branch,
                       "--title", f"{inv}: snapshot of the source folder",
                       "--body", "Automatic source snapshot with manifests, evidence hashes, update time and regenerated central reports. Local checks passed; Repository integrity must pass before merge.")
                    open_ids.add(inv)
                    core.log("snapshot_queued", inv=inv, branch=branch)
            holds.pop(f"snapshot {inv}", None)
            core.kv_set(db, f"import:{inv}", time.time())
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            holds[f"snapshot {inv}"] = str(exc)[-300:]
            core.log("snapshot_refused", inv=inv)
        core.kv_set(db, "holds", holds)


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
        target = disk / rel
        try:
            result = subprocess.run(["git", "-C", str(mirror), "cat-file", "blob", blob], capture_output=True)
            if result.returncode != 0 or blob_id(result.stdout) != blob:
                raise OSError("git blob read failed verification")
            data = result.stdout
            target.parent.mkdir(parents=True, exist_ok=True)
            if target.exists() and rel in known and blob_id(target.read_bytes()) != known[rel]:
                # Someone changed this copy on the disk: keep both.
                os.replace(target, target.with_name(f"{target.name}.disk-{core.stamp()}"))
            target.write_bytes(data)
            if blob_id(target.read_bytes()) != blob:
                raise OSError("exported file failed verification")
            db.execute("INSERT OR REPLACE INTO exports VALUES(?,?)", (rel, blob))
        except OSError as exc:
            failures += 1
            core.log("export_error", rel=rel, error=type(exc).__name__)
        core.beat()
    if not failures:
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
    """Build on current main in isolation; regenerate after a rejected concurrent push."""
    stale = core.kv_get(db, "generated_stale", False)
    if not stale and time.time() - core.kv_get(db, "generated_at", 0) < cfg.get("publish_every_s", 3600):
        return
    failed_base = None
    for attempt in range(3):
        try:
            git(clone, "fetch", "-q", "origin", "main")
            base = git(clone, "rev-parse", "origin/main")
            if base == failed_base:
                return  # A permission/network failure is not a concurrent update.
            with temporary_worktree(clone, base) as work:
                ok, tail = python(work, "scripts/build_master_report.py")
                if not ok:
                    raise OSError(f"report generation failed: {tail[-160:]}")
                folder = work / "datasets" / "backup"
                folder.mkdir(parents=True, exist_ok=True)
                if (core.STATE / "BACKUP_STATUS.md").exists():
                    shutil.copyfile(core.STATE / "BACKUP_STATUS.md", work / "BACKUP_STATUS.md")
                if (core.STATE / "packs.json").exists():
                    packs = json.loads((core.STATE / "packs.json").read_text())
                    (folder / "packs.json").write_text(json.dumps(packs, indent=0) + "\n")
                (folder / "pending.json").write_text(json.dumps(registry, indent=1) + "\n")
                week = time.strftime("%Y-%W", time.gmtime())
                copy_index = core.kv_get(db, "index_committed_week") != week and (core.STATE / "index.jsonl.gz").exists()
                if copy_index:
                    shutil.copyfile(core.STATE / "index.jsonl.gz", folder / "index-latest.jsonl.gz")
                if stage_publication(work, GENERATED_PATHS):
                    git(work, "commit", "-q", "-m", f"Update backup status and generated reports{TRAILER}")
                    reason = check_candidate(work, base)
                    if reason:
                        raise OSError(reason)
                    result = subprocess.run(["git", "-C", str(work), "push", "-q", "origin", "HEAD:refs/heads/main"],
                                            capture_output=True, text=True, env=dict(os.environ, GIT_TERMINAL_PROMPT="0"))
                    if result.returncode:
                        failed_base = base
                        core.log("push_error", attempt=attempt + 1, error=result.stderr.strip()[:200])
                        continue
                if copy_index:
                    core.kv_set(db, "index_committed_week", week)
                core.kv_set(db, "generated_stale", False)
                core.kv_set(db, "generated_at", time.time())
                return
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            core.log("generated_hold", reason=str(exc)[-300:])
            return
    core.log("generated_hold", reason="main changed during all three publication attempts; retry next pass")


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
    if not clean_main(clone):
        return
    auto_snapshots(cfg, db, clone, open_ids)
    registry = registry_and_missing(cfg, db, clone)
    publish_generated(cfg, db, clone, registry)
