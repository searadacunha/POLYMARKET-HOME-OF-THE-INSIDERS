#!/usr/bin/env python3
"""Freeze the protocol: hash the plan, the code, the tests and the sample definition.

Writes PROTOCOL.lock. tests/test_freeze.py fails if any frozen file later changes, so a post-freeze edit is
detected instead of being silently absorbed. Any intended change is a dated amendment in amendements/.
"""
import datetime as dt, hashlib, json, os, sys

STUDY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FROZEN = ["analysis_plan.md", "scripts/build_alerts.py", "scripts/score.py", "scripts/stats.py",
          "scripts/split.py", "scripts/reproduce_feb28.py", "scripts/collect_tapes.py",
          "scripts/interval_reading.py", "tests/test_exposure.py"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lock(extra=None):
    files = {}
    for rel in FROZEN:
        p = os.path.join(STUDY, rel)
        if os.path.exists(p):
            files[rel] = sha256(p)
    doc = {"study": "collective-exposure-shifts",
           "frozen_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "files": files}
    if extra:
        doc.update(extra)
    return doc


def main():
    extra = {}
    if len(sys.argv) > 1:
        extra = json.load(open(sys.argv[1]))
    doc = lock(extra)
    json.dump(doc, open(os.path.join(STUDY, "PROTOCOL.lock"), "w"), indent=1, sort_keys=True)
    print(json.dumps(doc, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
