"""Synthetic low quotas: no live disk filling or evidence deletion."""
import json
from pathlib import Path
import tempfile
import unittest
import asyncio
from unittest.mock import patch
from polysentinel.storage_budget import storage_usage,require_capacity
from polysentinel.reports import atomic_write
from polysentinel.engine import resource_mode

class BudgetTests(unittest.TestCase):
    def test_network_quota_pause_and_recovery_on_same_client(self):
        from polysentinel.db import Store
        from polysentinel.net import Net,SourceError
        from unittest.mock import AsyncMock
        import httpx
        async def exercise(root):
            store=Store(root);config={'min_free_bytes':0,'data_quota_bytes':1,'request_attempts':1}
            try:
                async with Net(store,config) as net:
                    await net._client.aclose()
                    net._client=httpx.AsyncClient(transport=httpx.MockTransport(lambda request:httpx.Response(200,json={'data':[]})))
                    net._public_url=AsyncMock(return_value='api.example.com')
                    with self.assertRaises(SourceError):await net.request('https://api.example.com/test')
                    self.assertEqual(net.requests_used,0)
                    config['data_quota_bytes']=5_000_000_000
                    self.assertEqual((await net.request('https://api.example.com/test')).body,{'data':[]})
                    self.assertEqual(net.requests_used,1)
            finally:store.close()
        with tempfile.TemporaryDirectory() as root:asyncio.run(exercise(root))
    def test_prolonged_pause_keeps_database_fixed_and_reports_live_state(self):
        from polysentinel.db import Store
        from polysentinel.engine import run_cycle
        from polysentinel.monitoring import runtime_status
        from polysentinel.dashboard import snapshot
        import time
        with tempfile.TemporaryDirectory() as d:
            store=Store(d)
            try:
                before=store.conn.total_changes
                with patch('polysentinel.engine.resources',return_value={'free_bytes':1,'project_data_bytes':100}):
                    for _ in range(3):
                        result=asyncio.run(run_cycle(store,{'min_free_bytes':10,'data_quota_bytes':1000},None))
                        self.assertEqual(result['resource_mode'],'paused')
                self.assertEqual(store.conn.total_changes,before)
                runtime_status(d,{'at':time.time(),'running':True,'resource_mode':'paused'})
                self.assertTrue(snapshot(store)['live']);self.assertIn('suspendue',snapshot(store)['verdict'])
            finally:store.close()
    def test_all_runtime_folders_and_sqlite_sidecars_are_counted(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for name in ('data/db-wal','data/db-shm','evidence/backup','cache/item','tmp/item','logs/x','reports/x','metrics/x'):
                p=root/name;p.parent.mkdir(exist_ok=True);p.write_bytes(b'x'*300)
            (root/'.venv').mkdir();(root/'.venv/dependency').write_bytes(b'x'*10000)
            usage=storage_usage(root)
            self.assertEqual(usage['project_data_bytes'],8*300)
            self.assertGreaterEqual(usage['quota_accounted_bytes'],usage['allocated_bytes'])
            with self.assertRaises(RuntimeError):require_capacity(root,{'min_free_bytes':0,'data_quota_bytes':usage['quota_accounted_bytes']},1)
    def test_export_refused_preserves_previous_report(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'reports').mkdir();p=root/'reports/test.html';p.write_text('old')
            (root/'config.json').write_text(json.dumps({'min_free_bytes':0,'data_quota_bytes':1}))
            with self.assertRaises(RuntimeError):atomic_write(p,'new')
            self.assertEqual(p.read_text(),'old');self.assertFalse(p.with_name(p.name+'.tmp').exists())
    def test_pause_reduced_and_recovery_keep_reserve(self):
        config={'min_free_bytes':10_000_000_000,'data_quota_bytes':5_000_000_000}
        m={'free_bytes':11_000_000_000,'project_data_bytes':4_990_000_000}
        self.assertEqual(resource_mode(config,m),'paused')
        m['project_data_bytes']=4_600_000_000
        self.assertEqual(resource_mode(config,m),'reduced')
        m['project_data_bytes']=1_000_000_000
        self.assertEqual(resource_mode(config,m),'normal')
        m['free_bytes']=10_010_000_000
        self.assertEqual(resource_mode(config,m),'paused')
