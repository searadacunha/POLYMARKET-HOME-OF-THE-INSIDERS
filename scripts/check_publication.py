#!/usr/bin/env python3
"""Check committed publication candidates without fetching, editing or publishing."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

MIGRATION_FILE = "scripts/publication_migration.json"
README_PATH = "README.md"


class PublicationError(Exception):
    pass


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if result.returncode:
        raise PublicationError(f"git {args[0]} failed; fetch the required history first")
    return result.stdout


def commit(repo, ref):
    return git(repo, "rev-parse", "--verify", "--end-of-options",
               f"{ref}^{{commit}}").decode().strip()


def entries(repo, revision, paths):
    result = {}
    for row in git(repo, "ls-tree", "-r", "-z", revision, "--", *paths).split(b"\0"):
        if row:
            meta, path = row.split(b"\t", 1)
            result[path.decode("utf-8", "surrogateescape")] = meta
    return result


def require_ancestor(repo, ancestor, revision):
    result = subprocess.run(["git", "-C", str(repo), "merge-base", "--is-ancestor",
                             ancestor, revision], capture_output=True)
    if result.returncode == 1:
        raise PublicationError(f"candidate omits required commit {ancestor}; merge the destination first")
    if result.returncode:
        raise PublicationError("cannot check ancestry; fetch the complete required history")


def verify(repo, policy, target, candidate="HEAD", head=None, base_ref=None):
    try:
        rule = policy["branches"][target]
        anchor = commit(repo, rule["commit"])
        paths = rule["protected_paths"]
        if not isinstance(paths, list) or not paths or any(not isinstance(p, str) or not p for p in paths):
            raise ValueError("protected_paths must be a nonempty list of paths")
    except (KeyError, TypeError, ValueError) as exc:
        raise PublicationError(f"invalid publication policy for {target}: {exc}") from exc
    candidate = commit(repo, candidate)
    head = commit(repo, head) if head else candidate
    for revision in {head, candidate}:
        require_ancestor(repo, anchor, revision)
    if base_ref:
        latest_base = commit(repo, base_ref)
        require_ancestor(repo, latest_base, head)
    protected = entries(repo, anchor, paths)
    for path in paths:
        if not any(p == path or p.startswith(path.rstrip("/") + "/") for p in protected):
            raise PublicationError(f"protected path missing from baseline: {path}")
    for revision in {head, candidate}:
        actual = entries(repo, revision, paths)
        # Compare both directions: added files in a protected directory must
        # be rejected just like changed or deleted archived evidence.
        changed = sorted(p for p in protected.keys() | actual.keys()
                         if protected.get(p) != actual.get(p))
        if changed:
            raise PublicationError("protected files added, changed or removed: " + ", ".join(changed))
    return {"target": target, "candidate": candidate, "head": head,
            "anchor": anchor, "protected_files": len(protected)}


def verify_policy_unchanged(repo, policy_file, base_ref, head, candidate):
    """A PR must not move its publication baseline unless a migration manifest matches.

    An ordinary policy edit is still refused. A manifest can move only the
    anchor commit, and only when every protected path other than README.md is
    byte-identical and the README difference is the one the manifest records.
    """
    root = Path(repo).resolve()
    try:
        relative = Path(policy_file).resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise PublicationError("publication policy must be tracked inside the repository") from exc
    base = commit(repo, base_ref)
    revisions = {commit(repo, head), commit(repo, candidate)}
    expected = entries(repo, base, [relative])
    if relative not in expected:
        raise PublicationError(f"destination lacks publication policy: {relative}")
    changed = [revision for revision in revisions if entries(repo, revision, [relative]) != expected]
    if not changed:
        return None
    if not all(_path_exists(repo, revision, MIGRATION_FILE) for revision in revisions):
        raise PublicationError(
            f"publication policy changed inside candidate: {relative}; "
            "review changes separately against the protected destination"
        )
    return _accept_migration(repo, relative, base, revisions)


def _path_exists(repo, revision, path):
    result = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "-e", f"{revision}:{path}"],
        capture_output=True,
    )
    return result.returncode == 0


def _show(repo, revision, path):
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"{revision}:{path}"],
        capture_output=True,
    )
    if result.returncode:
        return None
    return result.stdout


def _sha256(data):
    return hashlib.sha256(data).hexdigest()


def _readme_diff(repo, old, new):
    return git(
        repo, "-c", "core.abbrev=12", "diff", "--no-ext-diff", "--no-color",
        "--no-renames", "--unified=3", "--src-prefix=a/", "--dst-prefix=b/",
        old, new, "--", README_PATH,
    )


def _asset_changes(repo, old, new):
    before = entries(repo, old, ["assets"])
    after = entries(repo, new, ["assets"])
    changes = []
    for path in sorted(set(before) | set(after)):
        if before.get(path) == after.get(path):
            continue
        old_bytes = _show(repo, old, path)
        new_bytes = _show(repo, new, path)
        if path not in before:
            kind = "added"
        elif path not in after:
            kind = "removed"
        else:
            kind = "modified"
        changes.append({
            "path": path,
            "change": kind,
            "old_sha256": None if old_bytes is None else _sha256(old_bytes),
            "new_sha256": None if new_bytes is None else _sha256(new_bytes),
        })
    return changes


def expected_manifest(repo, old_anchor, new_anchor, protected_paths, authorization, reason):
    """The manifest fields the guard recomputes. Authorization text is not invented here."""
    old_readme = _show(repo, old_anchor, README_PATH)
    new_readme = _show(repo, new_anchor, README_PATH)
    if old_readme is None or new_readme is None:
        raise PublicationError("migration refused: README.md is missing from an anchor")
    return {
        "version": 1,
        "authorization": authorization,
        "reason": reason,
        "old_anchor": old_anchor,
        "new_anchor": new_anchor,
        "protected_paths": list(protected_paths),
        "readme": {
            "old_sha256": _sha256(old_readme),
            "new_sha256": _sha256(new_readme),
            "diff_sha256": _sha256(_readme_diff(repo, old_anchor, new_anchor)),
        },
        "assets": _asset_changes(repo, old_anchor, new_anchor),
    }


def _load_json(repo, revision, path, label):
    raw = _show(repo, revision, path)
    if raw is None:
        raise PublicationError(f"migration refused: missing {label}")
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise PublicationError(f"migration refused: {label} is not JSON") from exc
    if not isinstance(value, dict):
        raise PublicationError(f"migration refused: {label} must be an object")
    return value


def _policy_anchor_only(old_policy, new_policy, target):
    if old_policy.get("version") != new_policy.get("version"):
        return False
    old_branches = old_policy.get("branches")
    new_branches = new_policy.get("branches")
    if not isinstance(old_branches, dict) or not isinstance(new_branches, dict):
        return False
    if set(old_branches) != set(new_branches) or target not in new_branches:
        return False
    for name, old_rule in old_branches.items():
        new_rule = new_branches[name]
        if not isinstance(old_rule, dict) or not isinstance(new_rule, dict):
            return False
        if name != target:
            if old_rule != new_rule:
                return False
            continue
        if set(old_rule) != set(new_rule):
            return False
        for key, value in old_rule.items():
            if key != "commit" and new_rule.get(key) != value:
                return False
        if not isinstance(new_rule.get("commit"), str) or not isinstance(old_rule.get("commit"), str):
            return False
    return True


def _changed_paths(repo, base, revision):
    raw = git(repo, "diff", "--name-only", "--no-renames", base, revision)
    return [line.decode() for line in raw.splitlines() if line.strip()]


def _accept_migration(repo, policy_relative, base, revisions):
    allowed = {policy_relative, MIGRATION_FILE}
    anchors = set()
    for revision in revisions:
        extra = sorted(set(_changed_paths(repo, base, revision)) - allowed)
        if extra:
            raise PublicationError(
                "migration refused: candidate changes files other than the publication "
                "policy and the migration manifest: " + ", ".join(extra)
            )
        old_policy = _load_json(repo, base, policy_relative, "destination policy")
        new_policy = _load_json(repo, revision, policy_relative, "candidate policy")
        manifest = _load_json(repo, revision, MIGRATION_FILE, "migration manifest")
        target = "main"
        if target not in (old_policy.get("branches") or {}) or target not in (new_policy.get("branches") or {}):
            raise PublicationError("migration refused: policy has no main branch")
        if not _policy_anchor_only(old_policy, new_policy, target):
            raise PublicationError(
                "migration refused: the publication policy may change only its anchor commit"
            )
        old_anchor = commit(repo, old_policy["branches"][target]["commit"])
        new_anchor = commit(repo, new_policy["branches"][target]["commit"])
        if old_anchor == new_anchor:
            raise PublicationError("migration refused: the anchor commit did not move")
        paths = old_policy["branches"][target].get("protected_paths")
        if paths != new_policy["branches"][target].get("protected_paths"):
            raise PublicationError("migration refused: protected paths changed")
        try:
            require_ancestor(repo, old_anchor, new_anchor)
        except PublicationError as exc:
            raise PublicationError(
                "migration refused: the new anchor does not contain the previous anchor"
            ) from exc
        try:
            require_ancestor(repo, new_anchor, revision)
        except PublicationError as exc:
            raise PublicationError(
                "migration refused: the candidate does not contain the new anchor"
            ) from exc
        text = f"{manifest.get('authorization') or ''}\n{manifest.get('reason') or ''}"
        if not str(manifest.get("authorization") or "").strip() or not str(manifest.get("reason") or "").strip():
            raise PublicationError("migration refused: authorization and reason must be written")
        if old_anchor not in text or new_anchor not in text:
            raise PublicationError("migration refused: authorization text does not name both anchors")
        recomputed = expected_manifest(
            repo, old_anchor, new_anchor, paths,
            manifest.get("authorization"), manifest.get("reason"),
        )
        for key in ("version", "old_anchor", "new_anchor", "protected_paths", "readme", "assets"):
            if manifest.get(key) != recomputed[key]:
                raise PublicationError(f"migration refused: manifest {key} does not match the anchors")
        for path in paths:
            if path == README_PATH:
                continue
            if entries(repo, old_anchor, [path]) != entries(repo, new_anchor, [path]):
                raise PublicationError(
                    "migration refused: protected files other than README.md differ: " + path
                )
        anchors.add(new_anchor)
    if len(anchors) != 1:
        raise PublicationError("migration refused: head and candidate name different anchors")
    return anchors.pop()


def committed_policy(repo, policy_file, revision):
    """Read the policy from the reviewed Git object, never the working tree.

    Comparing committed policy blobs alone is insufficient if verification
    subsequently reads a locally edited copy of that same file.
    """
    root = Path(repo).resolve()
    try:
        relative = Path(policy_file).resolve().relative_to(root).as_posix()
    except ValueError as exc:
        raise PublicationError("publication policy must be tracked inside the repository") from exc
    revision = commit(repo, revision)
    recorded = entries(repo, revision, [relative]).get(relative, b"")
    if not recorded.startswith((b"100644 blob ", b"100755 blob ")):
        raise PublicationError(f"publication policy is not a tracked regular file: {relative}")
    return json.loads(git(repo, "show", f"{revision}:{relative}"))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--policy", type=Path,
                        default=Path(__file__).with_name("publication_baseline.json"))
    parser.add_argument("--target", required=True)
    parser.add_argument("--candidate", default="HEAD")
    parser.add_argument("--head", help="actual PR head, separately from its simulated merge")
    parser.add_argument("--base-ref", help="freshly fetched destination ref for a pre-push check")
    args = parser.parse_args()
    try:
        migrated_anchor = None
        if args.base_ref:
            migrated_anchor = verify_policy_unchanged(
                args.repo, args.policy, args.base_ref,
                args.head or args.candidate, args.candidate)
        policy_source = args.candidate if migrated_anchor else (args.base_ref or args.candidate)
        policy = committed_policy(args.repo, args.policy, policy_source)
        result = verify(args.repo, policy, args.target,
                        args.candidate, args.head, args.base_ref)
    except (PublicationError, OSError, json.JSONDecodeError) as exc:
        print(f"Publication refused: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
