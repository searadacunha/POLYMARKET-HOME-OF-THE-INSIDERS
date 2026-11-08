#!/usr/bin/env python3
"""Each security correction must fail on the pre-fix tree and pass now.

The historical modules are loaded from commit ab7ca23, the reviewed base.
No network and no real tokens.
"""
import gzip
import importlib.util
import io
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
BASE = "ab7ca23d7824cdf65962c62a736364da27964ec4"
SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "backup"))
import audit_public_repository as new_audit  # noqa: E402
import phi_backup as new_backup  # noqa: E402
import validate_evidence as new_val  # noqa: E402


def load_at(commit, repo_path, name):
    source = subprocess.check_output(["git", "-C", str(ROOT), "show", f"{commit}:{repo_path}"])
    folder = Path(tempfile.mkdtemp(prefix="hist-"))
    path = folder / Path(repo_path).name
    path.write_bytes(source)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def gzip_member(payload, comment=b"", corrupt_deflate=False):
    flag = 0x10 if comment else 0
    header = b"\x1f\x8b\x08" + bytes([flag]) + b"\x00\x00\x00\x00\x00\xff"
    extra = (comment + b"\x00") if comment else b""
    comp = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    deflated = comp.compress(payload) + comp.flush()
    if corrupt_deflate:
        deflated = b"\x00\x01\x00" + deflated
    trailer = struct.pack("<II", zlib.crc32(payload) & 0xFFFFFFFF, len(payload) & 0xFFFFFFFF)
    return header + extra + deflated + trailer


class HistoricalFailures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_audit = load_at(BASE, "scripts/audit_public_repository.py", "audit_public_repository_ab7")
        cls.old_val = load_at(BASE, "scripts/validate_evidence.py", "validate_evidence_ab7")
        cls.old_backup = load_at(BASE, "scripts/backup/phi_backup.py", "phi_backup_ab7")

    def test_gzip_comment_was_accepted_and_is_now_refused(self):
        token = b"gh" + b"p_" + b"a" * 36
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rel = Path("research_notes/comment.json.gz")
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_bytes(gzip_member(b'{"ok":true}', comment=b"note " + token + b" end"))
            with patch.object(self.old_audit, "ROOT", root), patch.object(self.old_audit, "tracked_paths", return_value=[rel]):
                self.assertEqual(self.old_audit.check(), 0)
            with patch.object(new_audit, "ROOT", root), patch.object(new_audit, "tracked_paths", return_value=[rel]):
                self.assertEqual(new_audit.check(), 1)

    def test_uppercase_over_cap_was_accepted_and_now_fails(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rel = Path("research_notes/unread_tail.JSON.GZ")
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_bytes(gzip.compress(b"A" * 129))
            with patch.object(self.old_audit, "ROOT", root), patch.object(self.old_audit, "tracked_paths", return_value=[rel]), patch.object(self.old_audit, "MAX_GZ_UNCOMPRESSED", 128):
                self.assertEqual(self.old_audit.check(), 0)
            with patch.object(new_audit, "ROOT", root), patch.object(new_audit, "tracked_paths", return_value=[rel]), patch.object(new_audit, "MAX_GZ_UNCOMPRESSED", 128):
                self.assertEqual(new_audit.check(), 1)

    def test_zlib_error_used_to_escape_and_is_now_a_file_error(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rel = Path("research_notes/baddeflate.json.gz")
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_bytes(gzip_member(b"hi", corrupt_deflate=True))
            with patch.object(self.old_audit, "ROOT", root), patch.object(self.old_audit, "tracked_paths", return_value=[rel]):
                with self.assertRaises(zlib.error):
                    self.old_audit.check()
            with patch.object(new_audit, "ROOT", root), patch.object(new_audit, "tracked_paths", return_value=[rel]):
                self.assertEqual(new_audit.check(), 1)

    def test_embedded_number_used_to_count_and_now_does_not(self):
        self.assertIn("1000", self.old_val.normalize_numbers("balance 21000"))
        self.assertIn("1000", self.old_val.normalize_numbers("token 0xabc1000def"))
        self.assertFalse(new_val.number_in_text("1000", "balance 21000\ntoken 0xabc1000def\n"))
        self.assertTrue(new_val.number_in_text("1000", "The account paid 1000 USDC.\n"))
        self.assertTrue(new_val.number_in_text("1,000", "The account paid 1000 USDC.\n"))

    def test_parent_source_path_used_to_be_read_and_is_now_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            inv = Path(d) / "case"
            (inv / "sources").mkdir(parents=True)
            (inv / "FINDINGS.md").write_text(
                "## F-001 | SUPPORTED | paid 99999\n"
                "- Sources: sources/../FINDINGS.md\n- Method: read\n- Limits: synthetic\n- Links: none\n")
            errors = []
            self.old_val.check_findings(inv, errors)
            self.assertFalse(any("escapes" in e for e in errors))
            self.assertFalse(any("99999" in e for e in errors))
            self.assertIsNone(new_val.source_inside(inv, "sources/../FINDINGS.md"))
            new_errors = []
            new_val.check_findings(inv, new_errors)
            self.assertTrue(any("escapes" in e for e in new_errors))

    def test_restore_escape_used_to_write_outside(self):
        payload = b"pwned-bytes"
        row = {"root": "..", "rel": "escaped-file", "sha": __import__("hashlib").sha256(payload).hexdigest(),
               "mode": 0o100644, "mtime_ns": 0}
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            dest = root / "dest"
            dest.mkdir()
            outside = root / "escaped-file"
            try:
                with patch.object(self.old_backup, "print"):
                    self.old_backup.restore_stream(io.BytesIO(payload), [row], dest)
                self.assertTrue(outside.is_file())
                self.assertEqual(outside.read_bytes(), payload)
            finally:
                outside.unlink(missing_ok=True)
            with patch.object(new_backup, "print"):
                self.assertEqual(new_backup.restore_stream(io.BytesIO(payload), [row], dest), (0, 1))
            self.assertFalse(outside.exists())

    def test_missing_done_marker_used_to_look_complete(self):
        old = load_at(BASE, "research_notes/g38-proof-tier-audit-2026-11-08/verify.py", "g38_verify_ab7")
        new = load_at("HEAD", "research_notes/g38-proof-tier-audit-2026-11-08/verify.py", "g38_verify_head")
        self.assertFalse(hasattr(old, "require_etherscan_complete"))
        with tempfile.TemporaryDirectory() as d:
            evidence = Path(d)
            folder = evidence / "etherscan" / "0xabc"
            folder.mkdir(parents=True)
            (folder / "137_tokentx_p1.json").write_text('{"status":"1","message":"OK","result":[{"hash":"0x1"}]}')
            old.EVIDENCE = evidence
            self.assertEqual(len(old.fetch_rows("0xabc", 137, "tokentx")), 1)
            new.EVIDENCE = evidence
            with self.assertRaises(AssertionError):
                new.require_etherscan_complete("0xabc", 137, "tokentx")


if __name__ == "__main__":
    unittest.main()
