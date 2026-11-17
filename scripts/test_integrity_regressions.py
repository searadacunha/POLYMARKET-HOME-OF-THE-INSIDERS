#!/usr/bin/env python3
"""Offline integrity regressions for evidence validation, imports and recovery.

Uses temporary files, an in-memory database and synthetic archives. No GitHub
request, age binary, live source folder or external disk is needed.
"""
import contextlib
import gzip
import hashlib
import io
import json
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "backup"))
import import_snapshot as imp  # noqa: E402
import phi_backup as backup  # noqa: E402
import phi_lib as lib  # noqa: E402
import phi_repo as repo_backup  # noqa: E402
import validate_evidence as val  # noqa: E402


def gzip_member(payload, comment=b""):
    import struct
    import zlib
    flag = 0x10 if comment else 0
    header = b"\x1f\x8b\x08" + bytes([flag]) + b"\x00\x00\x00\x00\x00\xff"
    extra = (comment + b"\x00") if comment else b""
    compressor = zlib.compressobj(9, zlib.DEFLATED, -zlib.MAX_WBITS)
    deflated = compressor.compress(payload) + compressor.flush()
    trailer = struct.pack("<II", zlib.crc32(payload) & 0xFFFFFFFF, len(payload) & 0xFFFFFFFF)
    return header + extra + deflated + trailer


def archive(entries):
    """Build a readable tar, including duplicate names when explicitly requested."""
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w") as tar:
        for name, data in entries:
            info = tarfile.TarInfo(name)
            info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
    return stream.getvalue()


class EvidenceIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name)
        self.inv = self.repo / "investigations" / "case"
        (self.inv / "sources").mkdir(parents=True)
        self.source = self.inv / "sources" / "proof.md"
        self.source.write_text("The observed address is 0x1234" + "a" * 32 + "abcd.\n")
        self.original_hash = lib.sha256_file(self.source)
        (self.inv / "README.md").write_text("# Test case\n")
        (self.inv / "STATUS.md").write_text(
            "---\nid: case\ntitle: Test\nstate: IN_PROGRESS\n"
            "updated_utc: 2026-11-04T00:00:00Z\norigin: synthetic\nversion: test\n---\n")
        (self.inv / "data_manifest.json").write_text(json.dumps({"files": [{
            "path": "proof.md", "repo_path": "investigations/case/sources/proof.md",
            "status": "imported", "sha256": self.original_hash}]}))
        (self.inv / "EVIDENCE.md").write_text(
            "| File | SHA-256 | Role |\n|---|---|---|\n"
            f"| `sources/proof.md` | {self.original_hash} | Synthetic proof |\n")
        self.finding()
        self.repo_patch = patch.object(lib, "REPO", self.repo)
        self.repo_patch.start()
        self.addCleanup(self.repo_patch.stop)

    def finding(self, heading="F-001 | SUPPORTED | A documented observation", links="none", source="sources/proof.md"):
        (self.inv / "FINDINGS.md").write_text(
            f"## {heading}\n- Sources: {source}\n- Method: read bytes\n"
            f"- Limits: synthetic case\n- Links: {links}\n")

    def validate(self, fill=False, ids=None):
        errors = []
        val.check_investigation(self.inv, {}, fill, errors, ids or {"case"})
        return errors

    def test_valid_abbreviated_address_requires_matching_suffix(self):
        self.finding("F-001 | SUPPORTED | Address 0x1234…abcd appears")
        self.assertEqual(self.validate(), [])

    def test_number_inside_a_longer_integer_or_hex_is_not_a_citation(self):
        self.source.write_text("balance 21000\ntoken 0xabc1000def\n")
        self.finding("F-001 | SUPPORTED | The account paid 1000")
        errors = self.validate()
        self.assertTrue(any("1000" in error for error in errors))

    def test_exact_number_is_still_accepted(self):
        self.source.write_text("The account paid 1000 USDC.\n")
        digest = lib.sha256_file(self.source)
        for name in ("data_manifest.json", "EVIDENCE.md"):
            path = self.inv / name
            path.write_text(path.read_text().replace(self.original_hash, digest))
        self.finding("F-001 | SUPPORTED | The account paid 1000")
        self.assertEqual(self.validate(), [])

    def test_source_path_cannot_escape_the_investigation(self):
        self.finding("F-001 | SUPPORTED | The account paid 99999", source="sources/../FINDINGS.md")
        errors = self.validate()
        self.assertTrue(any("escapes" in error for error in errors))
        self.finding("F-001 | SUPPORTED | Address 0x1234…cdef appears")
        self.assertTrue(any("not in the cited sources" in e for e in self.validate()))

    def test_missing_cross_investigation_link_is_an_error(self):
        self.finding(links="missing-case:F-001")
        self.assertTrue(any("missing-case:F-001" in e for e in self.validate()))

    def test_known_investigation_without_findings_is_an_error(self):
        (self.repo / "investigations" / "other").mkdir()
        self.finding(links="other:F-001")
        self.assertTrue(any("other:F-001" in e for e in self.validate(ids={"case", "other"})))

    def test_malformed_finding_is_not_silently_discarded(self):
        for heading in ("F-001 | NOT_PROVEN | A claim", "F-01 | SUPPORTED | A claim"):
            with self.subTest(heading=heading):
                self.finding(heading)
                self.assertTrue(any("malformed finding" in e for e in self.validate()))

    def test_directory_is_not_a_source_file(self):
        (self.inv / "sources" / "folder").mkdir()
        self.finding(source="sources/folder")
        self.assertTrue(any("not a file" in e for e in self.validate()))

    def test_invalid_evidence_hash_is_not_silently_ignored(self):
        path = self.inv / "EVIDENCE.md"
        path.write_text(path.read_text().replace(self.original_hash, "mistyped-hash"))
        self.assertTrue(any("malformed evidence row" in e for e in self.validate()))

    def test_endpoint_tables_are_not_mistaken_for_file_hashes(self):
        path = self.inv / "EVIDENCE.md"
        path.write_text(path.read_text() + "\n## Primary sources\n\n"
                        "| Source | Use | Access |\n|---|---|---|\n"
                        "| `rpc.example.invalid` | Receipts | No key |\n"
                        "| `sources/report.json` | A documented endpoint | Public |\n")
        before = path.read_bytes()
        self.assertEqual(self.validate(fill=True), [])
        self.assertEqual(path.read_bytes(), before)

    def test_fill_cannot_accept_source_bytes_that_disagree_with_manifest(self):
        path = self.inv / "EVIDENCE.md"
        before = path.read_bytes()
        self.source.write_text("A changed file which has not been re-imported.\n")
        self.assertTrue(any("hash mismatch" in e for e in self.validate(fill=True)))
        self.assertEqual(path.read_bytes(), before)

    def test_invalid_finding_cannot_partially_fill_evidence(self):
        path = self.inv / "EVIDENCE.md"
        path.write_text(path.read_text().replace(self.original_hash, "auto"))
        before = path.read_bytes()
        self.finding(links="missing-case:F-001")
        self.assertTrue(self.validate(fill=True))
        self.assertEqual(path.read_bytes(), before)

    def test_fill_still_updates_an_explicitly_reimported_snapshot(self):
        self.source.write_text("New version of the source.\n")
        digest = lib.sha256_file(self.source)
        manifest = self.inv / "data_manifest.json"
        manifest.write_text(manifest.read_text().replace(self.original_hash, digest))
        self.assertEqual(self.validate(fill=True), [])
        self.assertIn(digest, (self.inv / "EVIDENCE.md").read_text())


class ImportIntegrity(unittest.TestCase):
    def test_gzip_comment_and_uppercase_suffix_are_scanned(self):
        token = b"gh" + b"p_" + b"b" * 36
        comment = gzip_member(b'{"ok": true}', comment=b"prefix " + token + b" suffix")
        upper = gzip.compress(b'{"token":"' + token + b'"}')
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)
            hidden = folder / "note.json.gz"
            renamed = folder / "note.JSON.GZ"
            hidden.write_bytes(comment)
            renamed.write_bytes(upper)
            self.assertIn("github_token", lib.scan_bytes(lib.read_for_scan(hidden)))
            self.assertIn("github_token", lib.scan_bytes(lib.read_for_scan(renamed)))

    def test_oversized_decompressed_input_is_not_a_successful_partial_scan(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(lib, "MAX_GZ_SCAN_BYTES", 32):
            source = Path(tmp) / "compressed.json.gz"
            source.write_bytes(gzip.compress(b"x" * 33))
            with self.assertRaises(ValueError):
                lib.read_for_scan(source)
            hits, skip = imp.scan_file(source, ".gz", {})
            self.assertEqual(hits, [])
            self.assertTrue(skip)

    def test_scan_covers_the_actual_copied_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "origin"
            source.mkdir()
            (source / "report.json").write_text('{"state":"safe before copy"}')
            real_copy = imp.copy_with_hash

            def changes_before_copy(src, dest):
                src.write_text('{"url":"https://example.invalid/?apikey=' + "A" * 34 + '"}')
                return real_copy(src, dest)

            with patch.object(imp, "copy_with_hash", side_effect=changes_before_copy):
                manifest = imp.import_investigation("case", source, {}, {}, repo=root / "repo", log=lambda *_: None)
            entry = next(e for e in manifest["files"] if e["path"] == "report.json")
            self.assertEqual(entry["status"], "refused")
            self.assertFalse((root / "repo/investigations/case/sources/report.json").exists())
            self.assertNotIn("repo_path", entry)


    def test_import_refuses_parent_directory_id_without_deleting_existing_data(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            origin = root / "origin"
            origin.mkdir()
            (origin / "proof.txt").write_text("new source")
            existing = root / "repo" / "sources" / "existing.txt"
            existing.parent.mkdir(parents=True)
            existing.write_text("keep this")
            with self.assertRaisesRegex(SystemExit, "invalid investigation id"):
                imp.import_investigation("..", origin, {}, {}, repo=root / "repo", log=lambda *_: None)
            self.assertEqual(existing.read_text(), "keep this")

    def test_import_refuses_origin_inside_destination_without_deleting_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            origin = root / "repo" / "investigations" / "case" / "sources"
            origin.mkdir(parents=True)
            existing = origin / "existing.txt"
            existing.write_text("keep this")
            with self.assertRaisesRegex(SystemExit, "must not overlap"):
                imp.import_investigation("case", origin, {}, {}, repo=root / "repo", log=lambda *_: None)
            self.assertEqual(existing.read_text(), "keep this")

    def test_import_refuses_origin_above_destination_without_deleting_it(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "repo" / "investigations" / "case" / "sources"
            source_dir.mkdir(parents=True)
            existing = source_dir / "existing.txt"
            existing.write_text("keep this")
            with self.assertRaisesRegex(SystemExit, "must not overlap"):
                imp.import_investigation("case", source_dir.parent, {}, {}, repo=root / "repo", log=lambda *_: None)
            self.assertEqual(existing.read_text(), "keep this")


class RecoveryIntegrity(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(patch.object(backup, "STATE", self.root))
        self.stack.enter_context(patch.object(backup, "beat"))
        self.stack.enter_context(patch.object(backup, "log"))

    def test_duplicate_tar_member_does_not_mask_a_missing_member(self):
        data = b"same contents"
        digest = hashlib.sha256(data).hexdigest()
        packed = archive([("first", data), ("first", data)])
        self.assertGreater(backup.check_members(io.BytesIO(packed), "pack", {"first": digest, "second": digest}, False), 0)

    def test_complete_archive_still_verifies(self):
        first, second = b"first data", b"second data"
        expected = {"first": hashlib.sha256(first).hexdigest(), "second": hashlib.sha256(second).hexdigest()}
        self.assertEqual(backup.check_members(io.BytesIO(archive([("first", first), ("second", second)])), "pack", expected, False), 0)

    def test_restore_reports_missing_requested_members(self):
        data = b"surviving file"
        digest = hashlib.sha256(data).hexdigest()
        rows = [{"root": "case", "rel": name, "member": name, "pack": "pack", "sha": digest,
                 "klass": "normal", "mode": 0o100644, "mtime_ns": 0} for name in ("first", "missing")]
        manifests = self.root / "manifests"
        manifests.mkdir()
        with gzip.open(manifests / "index.jsonl.gz", "wt") as fh:
            fh.write("\n".join(json.dumps(row) for row in rows) + "\n")
        (manifests / "packs.json").write_text(json.dumps([{"name": "pack", "kind": "project"}]))
        args = SimpleNamespace(source="disk", dest=str(self.root / "restored"), root=None,
                               disk=str(self.root / "disk"), manifests=str(manifests), identity=None)
        stream = io.BytesIO(gzip.compress(archive([("first", data)])))
        with patch.object(backup, "open_for_restore", return_value=(stream, lambda: None)), contextlib.redirect_stdout(io.StringIO()):
            problems = backup.restore(args, {})
        self.assertEqual(problems, 1)
        self.assertEqual((self.root / "restored/case/first").read_bytes(), data)

    def test_absent_raw_archive_must_not_erase_recorded_part_b(self):
        import importlib.util
        path = Path(__file__).resolve().parents[1] / "research_notes/x-history-2026-11-06/verification/verify.py"
        spec = importlib.util.spec_from_file_location("xhist_verify", path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        recorded = json.dumps({"checks": 2, "failed": 0, "results": [
            {"check": "B1 Ballon d'Or Q1-Q4 recomputed from the archived tapes are identical", "pass": True, "detail": ""},
            {"check": "B2 ledgers", "pass": True, "detail": ""},
        ]})
        archived = self.root / "verification.json"
        archived.write_text(recorded)
        current = self.root / "current-verification.json"
        with patch.object(mod, "HERE", self.root), patch.object(mod, "RAW", self.root / "absent-raw"), \
                patch.object(mod, "part_a"), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(mod.main([]), 0)
            self.assertEqual(archived.read_text(), recorded)
            self.assertEqual(mod.main(["--output", str(current)]), 0)
        self.assertEqual(archived.read_text(), recorded)
        fresh = json.loads(current.read_text())
        self.assertEqual(fresh["skipped"], 1)
        self.assertIsNone(fresh["results"][0]["pass"])

    def test_restore_refuses_a_path_that_escapes_the_destination(self):
        payload = b"pwned-bytes"
        row = {"root": "case", "rel": "../escaped-file", "sha": hashlib.sha256(payload).hexdigest(),
               "mode": 0o100644, "mtime_ns": 0}
        outside = self.root.parent / "escaped-file"
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(backup.restore_stream(io.BytesIO(payload), [row], self.root), (0, 1))
        self.assertFalse(outside.exists())
        self.assertFalse((self.root / "escaped-file").exists())

    def test_corrupt_restore_does_not_replace_a_good_existing_file(self):
        target = self.root / "case" / "result.md"
        target.parent.mkdir()
        target.write_bytes(b"good existing file")
        row = {"root": "case", "rel": "result.md", "sha": hashlib.sha256(b"expected file").hexdigest(),
               "mode": 0o100644, "mtime_ns": 0}
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(backup.restore_stream(io.BytesIO(b"damaged"), [row], self.root), (0, 1))
        self.assertEqual(target.read_bytes(), b"good existing file")

    def test_failed_mirror_export_is_retried_at_the_same_head(self):
        disk = self.root / "disk"
        mirror = disk / "git-backups/Polymarket-Home-of-the-Insiders.git"
        mirror.mkdir(parents=True)
        (mirror / "HEAD").write_text("ref: refs/heads/main\n")
        blocker = disk / "investigations"
        blocker.write_text("simulate a filesystem problem")
        db = sqlite3.connect(":memory:", isolation_level=None)
        self.addCleanup(db.close)
        db.row_factory = sqlite3.Row
        db.executescript(backup.SCHEMA)
        data = b"snapshot bytes"
        blob = repo_backup.blob_id(data)

        def git(_repo, *args, **kwargs):
            if args[0] == "rev-parse":
                return "head"
            if args[0] == "ls-tree":
                return f"100644 blob {blob}\tinvestigations/case/proof.md"
            raise AssertionError(args)

        def run(args, **kwargs):
            return subprocess.CompletedProcess(args, 0, stdout=data if "cat-file" in args else b"", stderr=b"")

        with patch.object(repo_backup, "git", side_effect=git), patch.object(repo_backup.subprocess, "run", side_effect=run):
            repo_backup.mirror_to_disk({"repo": "test/repo"}, db, disk, self.root)
            self.assertIsNone(backup.kv_get(db, "exported_head"))
            blocker.unlink()
            repo_backup.mirror_to_disk({"repo": "test/repo"}, db, disk, self.root)
        self.assertEqual((disk / "investigations/case/proof.md").read_bytes(), data)
        self.assertEqual(backup.kv_get(db, "exported_head"), "head")

    def test_failed_or_mismatched_blob_read_cannot_mark_export_successful(self):
        for returncode, data in ((1, b""), (0, b"wrong blob bytes")):
            with self.subTest(returncode=returncode):
                disk = self.root / f"disk-{returncode}"
                mirror = disk / "git-backups/Polymarket-Home-of-the-Insiders.git"
                mirror.mkdir(parents=True)
                (mirror / "HEAD").write_text("ref: refs/heads/main\n")
                db = sqlite3.connect(":memory:", isolation_level=None)
                self.addCleanup(db.close)
                db.row_factory = sqlite3.Row
                db.executescript(backup.SCHEMA)
                expected = repo_backup.blob_id(b"expected blob")

                def git(_repo, *args, **kwargs):
                    if args[0] == "rev-parse":
                        return "head"
                    if args[0] == "ls-tree":
                        return f"100644 blob {expected}\tinvestigations/case/proof.md"
                    raise AssertionError(args)

                def run(args, **kwargs):
                    return subprocess.CompletedProcess(args, returncode if "cat-file" in args else 0,
                                                       stdout=data if "cat-file" in args else b"", stderr=b"")

                with patch.object(repo_backup, "git", side_effect=git), patch.object(repo_backup.subprocess, "run", side_effect=run):
                    repo_backup.mirror_to_disk({"repo": "test/repo"}, db, disk, self.root)
                self.assertIsNone(backup.kv_get(db, "exported_head"))
                self.assertEqual(db.execute("SELECT COUNT(*) FROM exports").fetchone()[0], 0)
                self.assertFalse((disk / "investigations/case/proof.md").exists())


if __name__ == "__main__":
    unittest.main()
