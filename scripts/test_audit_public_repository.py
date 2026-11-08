#!/usr/bin/env python3
"""Fail-closed public artifact scan regressions; no network or real tokens."""
import gzip
import importlib.util
import io
import struct
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location(
    "audit_public_repository", Path(__file__).with_name("audit_public_repository.py"))
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


class PublicArtifactScanTests(unittest.TestCase):
    def test_complete_gzip_without_secret_is_accepted(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rel = Path("research_notes/sample.json.gz")
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_bytes(gzip.compress(b"safe public historical events" * 10))
            with patch.object(audit, "ROOT", root), patch.object(audit, "tracked_paths", return_value=[rel]):
                self.assertEqual(audit.check(), 0)

    def test_oversize_gzip_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rel = Path("research_notes/unread_tail.json.gz")
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_bytes(gzip.compress(b"A" * 129))
            with (patch.object(audit, "ROOT", root),
                  patch.object(audit, "tracked_paths", return_value=[rel]),
                  patch.object(audit, "MAX_GZ_UNCOMPRESSED", 128)):
                self.assertEqual(audit.check(), 1)

    def test_secret_crossing_chunk_boundary_is_detected(self):
        value = b"gh" + b"p_" + b"x" * 36
        with patch.object(audit, "BUFFER_SIZE", 21):
            hits, count, complete = audit.inspect_stream(io.BytesIO(b" " * 17 + value), Path("sample.txt"))
        self.assertTrue(complete)
        self.assertIn("github_classic_token", hits)

    def test_corrupt_gzip_is_refused(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rel = Path("research_notes/corrupt.json.gz")
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_bytes(gzip.compress(b"valid payload")[:-5])
            with patch.object(audit, "ROOT", root), patch.object(audit, "tracked_paths", return_value=[rel]):
                self.assertEqual(audit.check(), 1)

    def test_secret_in_gzip_comment_is_refused(self):
        token = b"gh" + b"p_" + b"a" * 36
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rel = Path("research_notes/comment.json.gz")
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_bytes(gzip_member(b'{"ok":true}', comment=b"note " + token + b" end"))
            with patch.object(audit, "ROOT", root), patch.object(audit, "tracked_paths", return_value=[rel]):
                self.assertEqual(audit.check(), 1)

    def test_uppercase_gzip_over_cap_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rel = Path("research_notes/unread_tail.JSON.GZ")
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_bytes(gzip.compress(b"A" * 129))
            with (patch.object(audit, "ROOT", root),
                  patch.object(audit, "tracked_paths", return_value=[rel]),
                  patch.object(audit, "MAX_GZ_UNCOMPRESSED", 128)):
                self.assertEqual(audit.check(), 1)

    def test_zlib_error_is_a_per_file_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rel = Path("research_notes/baddeflate.json.gz")
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_bytes(gzip_member(b"hi", corrupt_deflate=True))
            with patch.object(audit, "ROOT", root), patch.object(audit, "tracked_paths", return_value=[rel]):
                self.assertEqual(audit.check(), 1)


def gzip_member(payload, comment=b"", corrupt_deflate=False):
    """Build one gzip member. Comment is stored uncompressed in the header."""
    flag = 0x10 if comment else 0
    header = b"\x1f\x8b\x08" + bytes([flag]) + b"\x00\x00\x00\x00\x00\xff"
    extra = (comment + b"\x00") if comment else b""
    comp = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    deflated = comp.compress(payload) + comp.flush()
    if corrupt_deflate:
        deflated = b"\x00\x01\x00" + deflated
    trailer = struct.pack("<II", zlib.crc32(payload) & 0xFFFFFFFF, len(payload) & 0xFFFFFFFF)
    return header + extra + deflated + trailer


if __name__ == "__main__":
    unittest.main()
