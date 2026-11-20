#!/usr/bin/env python3
"""The local runner must read the CI workflow as it is: every run block, step environments, and the local guard."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_all_checks as r

text = r.job(r.WORKFLOW.read_text(encoding="utf-8"))
found = r.steps(text)
by_name = {name: (env, script) for name, env, script in found}

assert len(found) == text.count(" run:"), (len(found), text.count(" run:"))
assert by_name["Test publication safeguards"] == ({}, "python3 scripts/test_publication.py")
assert by_name["Preserve accepted README and archived Relay evidence"][1] == r.LOCAL_GUARD
assert by_name["Recheck historical X and chain evidence offline"][0] == {"XLEADS_RAW": "/tmp/phi-no-local-x-raw"}
multi = by_name["Check C1/C5/C7 research register integrity"][1].splitlines()
assert multi == ["python3 research_notes/c5-c7-recovery-overlaps-2026-11-07/verify.py",
                 "python3 research_notes/c1-c7-primary-anchors-2026-11-07/verify.py"], multi
assert found[-1][2] == "git diff --exit-code HEAD --"
sample = "jobs:\n  a:\n    steps:\n      - name: one\n        run: echo 1\n      - name: two\n        env:\n          K: v\n        run: |\n          echo 2\n          echo 3\n"
assert r.steps(sample) == [("one", {}, "echo 1"), ("two", {"K": "v"}, "echo 2\necho 3")]
assert r.job("jobs:\n  integrity:\n    a: 1\n  other:\n    b: 2") == "  integrity:\n    a: 1"
assert not any("scripts/run_all_checks.py" in script for _, _, script in found), "the runner would call itself"
print(f"ok: {len(found)} steps read from the workflow")
