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

    def check_gzip_bytes(self, data):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rel = Path("research_notes/members.json.gz")
            path = root / rel
            path.parent.mkdir()
            path.write_bytes(data)
            with patch.object(audit, "ROOT", root), patch.object(audit, "tracked_paths", return_value=[rel]):
                return audit.check(), audit.phi_lib.scan_bytes(audit.phi_lib.read_for_scan(path))

    def test_later_member_header_is_scanned_by_both_scanners(self):
        token = b"gh" + b"p_" + b"z" * 36
        data = gzip.compress(b"{}") + gzip_member(b"{}", comment=b" " + token + b" ")
        result, hits = self.check_gzip_bytes(data)
        self.assertEqual(result, 1)
        self.assertIn("github_token", hits)

    def test_later_filename_extra_and_header_crc_are_checked(self):
        token = b"gh" + b"p_" + b"z" * 36
        for field in ("filename", "extra"):
            with self.subTest(field=field):
                second = gzip_member(b"{}", header_crc=True, **{field: b" " + token + b" "})
                result, hits = self.check_gzip_bytes(gzip.compress(b"{}") + second)
                self.assertEqual(result, 1)
                self.assertIn("github_token", hits)
        member = bytearray(gzip_member(b"public", header_crc=True))
        member[10] ^= 1
        with self.assertRaisesRegex(ValueError, "header CRC mismatch"):
            list(audit.phi_lib.iter_gzip_for_scan(io.BytesIO(member), 1000))

    def test_body_token_split_between_members_is_still_detected(self):
        token = b"gh" + b"p_" + b"z" * 36
        data = gzip_member(b" " + token[:17]) + gzip_member(token[17:] + b" ", comment=b"public")
        result, hits = self.check_gzip_bytes(data)
        self.assertEqual(result, 1)
        self.assertIn("github_token", hits)

    def test_valid_concatenated_members_and_padding_are_preserved(self):
        body = b"public" * 30000
        data = gzip.compress(body) + b"\0" * 23 + gzip.compress(b" evidence") + b"\0" * 9
        decoded = b"".join(audit.phi_lib.iter_gzip_for_scan(io.BytesIO(data), len(body) + 9))
        self.assertEqual(decoded, body + b" evidence")
        self.assertEqual(self.check_gzip_bytes(data), (0, []))

    def test_later_member_truncation_and_crc_corruption_fail_closed(self):
        first = gzip.compress(b"public")
        second = gzip.compress(b" evidence")
        corrupt = second[:-8] + bytes([second[-8] ^ 1]) + second[-7:]
        for tail in (second[:-3], corrupt):
            with self.subTest(tail=tail):
                with self.assertRaises((ValueError, EOFError, zlib.error)):
                    list(audit.phi_lib.iter_gzip_for_scan(io.BytesIO(first + tail), 1000))

    def test_reads_and_header_metadata_are_bounded(self):
        class BoundedReader(io.BytesIO):
            def read(self, size=-1):
                self.assert_size(size)
                return super().read(size)

            def assert_size(self, size):
                if not 0 < size <= audit.phi_lib.GZ_CHUNK_BYTES:
                    raise AssertionError("unbounded compressed read")

        safe = BoundedReader(gzip.compress(b"public" * 20000))
        self.assertEqual(len(b"".join(audit.phi_lib.iter_gzip_for_scan(safe, 120000))), 120000)
        with patch.object(audit.phi_lib, "MAX_GZ_HEADER_BYTES", 64):
            with self.assertRaises(audit.phi_lib.GzipScanLimit):
                list(audit.phi_lib.iter_gzip_for_scan(io.BytesIO(gzip_member(b"", comment=b"x" * 65)), 1000))
        with self.assertRaises(audit.phi_lib.GzipScanLimit):
            list(audit.phi_lib.iter_gzip_for_scan(io.BytesIO(gzip.compress(b"a" * 101)), 100))
        with patch.object(audit.phi_lib, "MAX_GZ_HEADER_BYTES", 64):
            with self.assertRaisesRegex(audit.phi_lib.GzipScanLimit, "compressed gzip input"):
                list(audit.phi_lib.iter_gzip_for_scan(io.BytesIO(gzip.compress(b"a") + b"\0" * 1000), 100))

    def test_zlib_error_is_a_per_file_refusal(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            rel = Path("research_notes/baddeflate.json.gz")
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_bytes(gzip_member(b"hi", corrupt_deflate=True))
            with patch.object(audit, "ROOT", root), patch.object(audit, "tracked_paths", return_value=[rel]):
                self.assertEqual(audit.check(), 1)


def gzip_member(payload, comment=b"", corrupt_deflate=False, filename=b"", extra=b"", header_crc=False):
    """Build one gzip member. Comment is stored uncompressed in the header."""
    flag = (0x10 if comment else 0) | (0x08 if filename else 0) | (0x04 if extra else 0) | (0x02 if header_crc else 0)
    header = b"\x1f\x8b\x08" + bytes([flag]) + b"\x00\x00\x00\x00\x00\xff"
    if extra:
        header += struct.pack("<H", len(extra)) + extra
    if filename:
        header += filename + b"\0"
    if comment:
        header += comment + b"\0"
    if header_crc:
        header += struct.pack("<H", zlib.crc32(header) & 0xffff)
    comp = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    deflated = comp.compress(payload) + comp.flush()
    if corrupt_deflate:
        deflated = b"\x00\x01\x00" + deflated
    trailer = struct.pack("<II", zlib.crc32(payload) & 0xFFFFFFFF, len(payload) & 0xFFFFFFFF)
    return header + deflated + trailer


if __name__ == "__main__":
    unittest.main()
