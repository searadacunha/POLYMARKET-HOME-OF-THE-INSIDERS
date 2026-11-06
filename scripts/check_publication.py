#!/usr/bin/env python3
"""Check committed publication candidates without fetching, editing or publishing."""
import argparse
import json
import subprocess
import sys
from pathlib import Path


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
        result = verify(args.repo, json.loads(args.policy.read_text()), args.target,
                        args.candidate, args.head, args.base_ref)
    except (PublicationError, OSError, json.JSONDecodeError) as exc:
        print(f"Publication refused: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
