import gzip
import json
from pathlib import Path
import tempfile
import unittest

from polysentinel.db import Store
from polysentinel.reports import daily_report
from polysentinel import monitoring


class SustainabilityTests(unittest.TestCase):
    def test_daily_report_compresses_full_snapshot_and_keeps_html_small(self):
        with tempfile.TemporaryDirectory() as root:
            store=Store(root);self.addCleanup(store.close)
            store.put('case','c',dict(id='c',evidence=['proof '*10000]))
            path=Path(daily_report(store,dict(verdict='unknown',counts=dict(trade=1))))
            packed=path.with_suffix('.json.gz')
            self.assertTrue(packed.is_file())
            payload=json.loads(gzip.decompress(packed.read_bytes()))
            self.assertEqual(payload['cases'][0]['evidence'],['proof '*10000])
            self.assertIn(packed.name,path.read_text())
            self.assertLess(path.stat().st_size,10000)
            self.assertFalse(path.with_suffix('.json').exists())

    def test_cycle_counts_new_content_separately_from_reobservations(self):
        with tempfile.TemporaryDirectory() as root:
            store=Store(root);self.addCleanup(store.close)
            store.put('trade','a',dict(wallet='a',timestamp=1),observed_at=1)
            before=monitoring.cycle_storage_start(store)
            store.put('trade','a',dict(wallet='a',timestamp=1),observed_at=2)
            store.put('trade','b',dict(wallet='b',timestamp=2),observed_at=2)
            store.evidence('api',{},200,b'new raw response',observed_at=2)
            delta=monitoring.cycle_storage_delta(store,before)
            self.assertEqual(delta['unique_contents'],2)
            self.assertEqual(delta['new_trade_keys'],1)
            self.assertEqual(delta['history_observations'],2)
            self.assertEqual(delta['response_observations'],1)
            self.assertGreater(delta['compressed_content_bytes'],0)
            self.assertEqual(delta['history_by_kind'],dict(trade=2))
