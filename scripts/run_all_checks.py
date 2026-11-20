#!/usr/bin/env python3
"""Run locally every check the CI workflow runs, from the workflow file itself.

The list of record is .github/workflows/repository-integrity.yml: this script reads its steps, so the two cannot
drift. The one step that needs GitHub's event variables (the publication guard) is run in its local form, against
origin/main. Run from a clean tree: the last step fails when a check left a tracked file changed.

usage: python3 scripts/run_all_checks.py [--list] [--keep-going]
Standard library only.
"""
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "repository-integrity.yml"
LOCAL_GUARD = "python3 scripts/check_publication.py --target main --candidate HEAD --base-ref origin/main"


def job(text, name="integrity"):
    """The lines of one job: a job that calls this script must never be read back by it."""
    lines = text.splitlines()
    start = lines.index(f"  {name}:")
    end = next((i for i in range(start + 1, len(lines)) if re.match(r"^  \S", lines[i])), len(lines))
    return "\n".join(lines[start:end])


def steps(text):
    """[(name, env, script)] for each step with a run block. Handles this workflow's YAML, not YAML in general."""
    out, lines, i = [], text.splitlines(), 0
    name, env = None, {}
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^(\s*)- name:\s*(.+)$", line)
        if m:
            name, env = m.group(2).strip(), {}
        m = re.match(r"^(\s*)env:\s*$", line)
        if m and name:
            indent = len(m.group(1))
            while i + 1 < len(lines) and len(lines[i + 1]) - len(lines[i + 1].lstrip()) > indent:
                i += 1
                key, _, value = lines[i].strip().partition(":")
                if "${{" not in value:
                    env[key] = value.strip().strip('"')
        m = re.match(r"^(\s*)run:\s*(.*)$", line)
        if m and name:
            indent, rest = len(m.group(1)), m.group(2).strip()
            block = [] if rest == "|" else [rest]
            while rest == "|" and i + 1 < len(lines) and (not lines[i + 1].strip() or len(lines[i + 1]) - len(lines[i + 1].lstrip()) > indent):
                i += 1
                block.append(lines[i][indent + 2:])
            script = "\n".join(block).strip()
            out.append((name, env, LOCAL_GUARD if "PUBLICATION_BEFORE" in script else script))
            name = None
        i += 1
    return out


def main(argv):
    todo = steps(job(WORKFLOW.read_text(encoding="utf-8")))
    if "--list" in argv:
        print("\n".join(f"{name}\n    {script}" for name, _, script in todo))
        return 0
    failed = []
    caches = set(ROOT.rglob("__pycache__"))  # python3 -I ignores PYTHONDONTWRITEBYTECODE: remove what this run adds
    print(f"python {sys.version.split()[0]} on {sys.platform}, {len(todo)} steps")
    for name, env, script in todo:
        start = time.time()
        done = subprocess.run(["bash", "-euo", "pipefail", "-c", script], cwd=ROOT, capture_output=True, text=True,
                              env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", **env})
        print(f"{'ok  ' if done.returncode == 0 else 'FAIL'} {time.time() - start:6.1f}s  {name}")
        if done.returncode:
            failed.append(name)
            print("\n".join("      " + l for l in (done.stdout + done.stderr).strip().splitlines()[-12:]))
            if "--keep-going" not in argv:
                break
    for cache in set(ROOT.rglob("__pycache__")) - caches:
        shutil.rmtree(cache, ignore_errors=True)
    print(f"{len(todo) - len(failed)}/{len(todo)} steps pass" if not failed or "--keep-going" in argv else f"stopped at: {failed[0]}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
