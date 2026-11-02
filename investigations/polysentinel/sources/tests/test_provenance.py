import tempfile
import unittest
from polysentinel.db import Store
from polysentinel.provenance import record_sources,source_sets


class SourceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
        self.trade={'id':'first:1','condition_id':'0x'+'a'*64,'timestamp':100}
    def tearDown(self):self.store.close();self.tmp.cleanup()
    def record(self,query):
        with self.store.transaction() as cx:
            return record_sources(self.store,[self.trade],query,'evidence',200,cx)
    def test_overlap_is_two_sources_but_duplicate_observations_do_not_grow(self):
        self.assertEqual(self.record({'filter_type':'CASH','filter_amount':1000}),1)
        self.assertEqual(self.record({'filter_type':'CASH','filter_amount':1000}),0)
        self.assertEqual(self.record({'condition':self.trade['condition_id']}),1)
        self.assertEqual(self.record({'condition':self.trade['condition_id']}),0)
        self.assertEqual(self.store.count('source_coverage'),2)
        self.assertEqual(self.store.conn.execute("SELECT COUNT(*) FROM history_refs WHERE kind='source_coverage'").fetchone()[0],2)
        self.assertEqual(source_sets(self.store,9e9)[self.trade['condition_id']],{'global','individual'})
        self.assertEqual(source_sets(self.store,1),{})
    def test_evidence_and_checkpoint_rollback_together(self):
        with self.assertRaises(RuntimeError):
            with self.store.transaction() as cx:
                record_sources(self.store,[self.trade],{},'e',200,cx)
                self.store.checkpoint('test',{'cursor':'next'},conn=cx)
                raise RuntimeError('interruption')
        self.assertEqual(self.store.count('source_coverage'),0)
        self.assertIsNone(self.store.checkpoint('test'))
