import tempfile
import gzip
import json
import unittest
from pathlib import Path
from polysentinel.reports import export_dossier


class ReportTests(unittest.TestCase):
    def test_reexport_of_same_evidence_ignores_filename_and_does_not_rewrite(self):
        with tempfile.TemporaryDirectory() as folder:
            case = {'id':'case', 'wallet':'wallet', 'status':'données insuffisantes'}
            first = export_dossier(folder, case)
            archived=json.loads(gzip.decompress((Path(folder)/'reports'/(first+'.json.gz')).read_bytes()))
            self.assertEqual(archived,{'case':case,'investigation':None})
            files = list((Path(folder)/'reports').iterdir())
            before = {p.name:(p.stat().st_mtime_ns,p.read_bytes()) for p in files}
            case['report'] = first
            self.assertEqual(first, export_dossier(folder, case))
            after = {p.name:(p.stat().st_mtime_ns,p.read_bytes()) for p in (Path(folder)/'reports').iterdir()}
            self.assertEqual(before, after)
            case['evidence'] = ['new proof']
            self.assertNotEqual(first, export_dossier(folder, case))
            self.assertEqual(len(list((Path(folder)/'reports').iterdir())),4)
