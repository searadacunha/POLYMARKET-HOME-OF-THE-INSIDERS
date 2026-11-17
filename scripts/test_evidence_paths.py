#!/usr/bin/env python3
"""Evidence path containment and corrupt-deflate regressions on temporary files."""
import json
import sys
import tempfile
import unittest
import zlib
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import phi_lib as lib  # noqa: E402
import validate_evidence as val  # noqa: E402


class EvidencePathsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.repo = self.root / 'repo'
        self.inv = self.repo / 'investigations/case'
        (self.inv / 'sources').mkdir(parents=True)
        self.outside = self.root / 'outside.txt'
        self.outside.write_text('Unrelated file: 1234.50\n')
        self.digest = lib.sha256_file(self.outside)
        self.repo_patch = patch.object(lib, 'REPO', self.repo)
        self.repo_patch.start()
        self.addCleanup(self.repo_patch.stop)

    def manifest(self, repo_path, status='imported', source_path='proof.txt'):
        (self.inv / 'data_manifest.json').write_text(json.dumps({'files': [{
            'path': source_path, 'repo_path': repo_path, 'status': status,
            'sha256': self.digest}]}))

    def finding(self, source):
        (self.inv / 'FINDINGS.md').write_text(
            '## F-001 | CONFIRMED | A recorded observation\n'
            f'- Sources: {source}\n- Method: temporary test\n'
            '- Limits: synthetic\n- Links: none\n')

    def evidence(self, source):
        path = self.inv / 'EVIDENCE.md'
        path.write_text('| File | SHA-256 | Role |\n|---|---|---|\n'
                        f'| `{source}` | auto | Synthetic proof |\n')
        return path

    def test_source_helper_rejects_parent_absolute_and_symlink_escape(self):
        (self.inv / 'sources/link.txt').symlink_to(self.outside)
        for rel in ('sources/../../../../outside.txt', str(self.outside),
                    str(self.inv / 'sources/proof.txt'), 'sources/link.txt'):
            with self.subTest(rel=rel):
                self.assertIsNone(val.source_inside(self.inv, rel))

    def test_findings_never_read_escaped_sources(self):
        (self.inv / 'sources/link.txt').symlink_to(self.outside)
        for rel in ('sources/../../../../outside.txt', str(self.outside), 'sources/link.txt'):
            with self.subTest(rel=rel), patch.object(val, 'read_text', side_effect=AssertionError('escaped read')):
                self.finding(rel)
                errors = []
                val.check_findings(self.inv, errors)
                self.assertTrue(errors)

    def test_evidence_fill_never_hashes_or_writes_escaped_sources(self):
        (self.inv / 'sources/link.txt').symlink_to(self.outside)
        for rel in ('sources/../../../../outside.txt', str(self.outside), 'sources/link.txt'):
            with self.subTest(rel=rel), patch.object(lib, 'sha256_file', side_effect=AssertionError('escaped hash')):
                path = self.evidence(rel)
                before = path.read_bytes()
                errors = []
                val.fill_or_check_evidence(self.inv, True, errors)
                self.assertTrue(any('escapes' in error for error in errors))
                self.assertEqual(path.read_bytes(), before)

    def test_manifest_rejects_parent_and_absolute_repo_targets(self):
        for rel in ('../outside.txt', str(self.outside), str(self.inv / 'sources/proof.txt')):
            with self.subTest(rel=rel), patch.object(lib, 'sha256_file', side_effect=AssertionError('escaped hash')):
                self.manifest(rel)
                errors = []
                val.check_manifest(self.inv, errors)
                self.assertTrue(any('escapes the repository' in error for error in errors))

    def test_manifest_rejects_symlink_target_outside_repo(self):
        (self.repo / 'outside-link.txt').symlink_to(self.outside)
        self.manifest('outside-link.txt', status='duplicate')
        errors = []
        with patch.object(lib, 'sha256_file', side_effect=AssertionError('escaped hash')):
            val.check_manifest(self.inv, errors)
        self.assertTrue(any('escapes the repository' in error for error in errors))

    def test_imported_entry_cannot_substitute_another_investigation(self):
        other = self.repo / 'investigations/other/sources/proof.txt'
        other.parent.mkdir(parents=True)
        other.write_bytes(self.outside.read_bytes())
        self.manifest('investigations/other/sources/proof.txt')
        errors = []
        val.check_manifest(self.inv, errors)
        self.assertTrue(any('does not match its own sources' in error for error in errors))

    def test_imported_entry_cannot_substitute_a_different_local_filename(self):
        (self.inv / 'sources/different.txt').write_bytes(self.outside.read_bytes())
        self.manifest('investigations/case/sources/different.txt')
        errors = []
        val.check_manifest(self.inv, errors)
        self.assertTrue(any('does not match its own sources' in error for error in errors))

    def test_imported_source_path_cannot_traverse_or_be_absolute(self):
        for source in ('../proof.txt', str(self.outside)):
            with self.subTest(source=source):
                self.manifest('investigations/case/sources/proof.txt', source_path=source)
                errors = []
                val.check_manifest(self.inv, errors)
                self.assertTrue(any('path escapes sources' in error for error in errors))

    def test_imported_symlink_cannot_leave_its_sources_directory(self):
        other = self.repo / 'investigations/other/sources/proof.txt'
        other.parent.mkdir(parents=True)
        other.write_bytes(self.outside.read_bytes())
        (self.inv / 'sources/proof.txt').symlink_to(other)
        self.manifest('investigations/case/sources/proof.txt')
        errors = []
        val.check_manifest(self.inv, errors)
        self.assertTrue(any('path escapes sources' in error for error in errors))

    def test_sources_directory_symlink_cannot_escape_investigation(self):
        (self.inv / 'sources').rmdir()
        (self.inv / 'sources').symlink_to(self.root, target_is_directory=True)
        self.manifest('investigations/case/sources/outside.txt', source_path='outside.txt')
        errors = []
        with patch.object(lib, 'sha256_file', side_effect=AssertionError('escaped hash')):
            val.check_manifest(self.inv, errors)
        self.assertTrue(any('sources directory escapes' in error for error in errors))

    def test_cross_investigation_duplicate_remains_valid(self):
        other = self.repo / 'investigations/other/sources/proof.txt'
        other.parent.mkdir(parents=True)
        other.write_bytes(self.outside.read_bytes())
        self.manifest('investigations/other/sources/proof.txt', status='duplicate')
        errors = []
        val.check_manifest(self.inv, errors)
        self.assertEqual(errors, [])
        path = self.evidence('sources/proof.txt')
        val.fill_or_check_evidence(self.inv, True, errors)
        self.assertEqual(errors, [])
        self.assertIn(self.digest, path.read_text())

    def test_normal_import_and_evidence_fill_remain_valid(self):
        (self.inv / 'sources/proof.txt').write_bytes(self.outside.read_bytes())
        self.manifest('investigations/case/sources/proof.txt')
        errors = []
        val.check_manifest(self.inv, errors)
        path = self.evidence('sources/proof.txt')
        val.fill_or_check_evidence(self.inv, True, errors)
        self.assertEqual(errors, [])
        self.assertIn(self.digest, path.read_text())

    def test_scan_does_not_read_a_symlink_outside_investigation(self):
        (self.inv / 'sources/link.txt').symlink_to(self.outside)
        errors = []
        with patch.object(lib, 'read_for_scan', side_effect=AssertionError('escaped scan')):
            val.check_scan(self.inv, {}, errors)
        self.assertTrue(any('scan path escapes' in error for error in errors))

    def test_corrupt_deflate_is_a_validation_error_instead_of_an_uncaught_exception(self):
        broken = self.inv / 'sources/broken.json.gz'
        # Valid gzip header, then a reserved DEFLATE block type and a dummy trailer.
        broken.write_bytes(b'\x1f\x8b\x08\x00' + b'\x00' * 6 + b'\x07' + b'\x00' * 8)
        with self.assertRaises(zlib.error):
            lib.read_for_scan(broken)
        self.finding('sources/broken.json.gz')
        errors = []
        val.check_findings(self.inv, errors)
        self.assertTrue(any('source unreadable' in error for error in errors))
        errors = []
        val.check_scan(self.inv, {}, errors)
        self.assertTrue(any('unreadable by the scan' in error for error in errors))


if __name__ == '__main__':
    unittest.main()
