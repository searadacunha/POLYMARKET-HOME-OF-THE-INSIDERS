import json
from pathlib import Path
import tempfile
import unittest
from polysentinel.monitoring import storage_trends


class TrendsTests(unittest.TestCase):
    def test_growth_keeps_wal_new_data_and_allocation_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)/'metrics';folder.mkdir()
            def row(at,main,wal,n,h):
                return dict(at=at,schema_version=2,files={
                    'sqlite_main':{'logical_bytes':main,'allocated_bytes':main+512},
                    'wal':{'logical_bytes':wal,'allocated_bytes':wal}},
                    objects=[{'kind':'trade','rows':n}],history=[{'kind':'trade','rows':h}])
            (folder/'runtime.jsonl').write_text('\n'.join(json.dumps(r) for r in [row(0,100,0,5,5),row(300,200,1000,6,7)]))
            w=storage_trends(tmp)['windows'][0]
            self.assertEqual(w['files']['wal']['logical_bytes'],1000)
            self.assertEqual(w['unique_keys']['trade'],1)
            self.assertEqual(w['history_observations']['trade'],2)
            self.assertAlmostEqual(w['runtime_logical_mb_per_min'],1100/1e6/5)
            with (folder/'runtime.jsonl').open('a') as f:f.write('\nnot json')
            self.assertEqual(storage_trends(tmp)['status'],'partial')
