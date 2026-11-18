#!/usr/bin/env python3
"""Freeze guard: fails if any file listed in PROTOCOL.lock has changed since the freeze."""
import hashlib, json, os, unittest

STUDY = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOCK = os.path.join(STUDY, "PROTOCOL.lock")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class TestFreeze(unittest.TestCase):
    def test_lock_exists(self):
        self.assertTrue(os.path.exists(LOCK), "PROTOCOL.lock missing")

    def test_frozen_files_unchanged(self):
        lock = json.load(open(LOCK))
        for rel, digest in lock["files"].items():
            p = os.path.join(STUDY, rel)
            self.assertTrue(os.path.exists(p), f"frozen file missing: {rel}")
            self.assertEqual(sha256(p), digest,
                             f"{rel} changed after the freeze; declare a dated amendment and re-freeze")


if __name__ == "__main__":
    unittest.main()
