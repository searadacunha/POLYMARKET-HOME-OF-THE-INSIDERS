#!/usr/bin/env python3
"""Offline check: unit tests, and the published verdict matches stats.json when that file exists."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parents[1]


def main() -> int:
    tests = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(ROOT / "tests"), "-v"], cwd=REPO)
    if tests.returncode:
        return tests.returncode
    stats_path = ROOT / "data" / "stats.json"
    findings = ROOT / "FINDINGS.md"
    if not stats_path.exists():
        print("stats.json is not present; collection has not been analysed")
        return 0
    stats = json.loads(stats_path.read_text())
    text = findings.read_text()
    verdict = stats["h1_verdict"]
    answer = stats["answer"]
    if verdict not in text or answer not in text:
        print("FINDINGS.md does not contain the verdict stored in stats.json")
        return 1
    if stats["spec_sha256"] not in (ROOT / "PREREGISTRATION.md").read_text():
        print("PREREGISTRATION.md does not quote the spec hash stored with the results")
        return 1
    print("verify ok", answer, verdict)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
