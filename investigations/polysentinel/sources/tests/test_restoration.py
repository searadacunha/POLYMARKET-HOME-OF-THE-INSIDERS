import gzip
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest

from polysentinel.db import Store
from polysentinel.quality import case_quality
from polysentinel.storage_budget import resource_blockers
from scripts.compress_reports import compress_reports


class RestorationTests(unittest.TestCase):
    def test_cycle_resumes_with_same_store_and_preserves_observations(self):
        import asyncio
        from unittest.mock import AsyncMock, Mock, patch
        from polysentinel.engine import run_cycle
        from polysentinel.config import load_config
        with tempfile.TemporaryDirectory() as root:
            store=Store(root);self.addCleanup(store.close)
            store.put('observation','retained',dict(proof='unique'))
            store.checkpoint('continuity',dict(cursor='saved'))
            config=dict(load_config(),root=root,notifications=False,investigations_per_cycle=0)
            net=Mock(requests_used=0)
            collector=Mock()
            collector.catalog=AsyncMock(return_value={})
            collector.trades=AsyncMock(return_value={})
            weak=dict(id='weak',event_id='e',priority=False)
            strong=dict(id='strong',event_id='e',priority=True)
            usage=dict(project_data_bytes=100,free_bytes=1)
            with patch('polysentinel.engine.resources',side_effect=[usage,dict(usage,free_bytes=20_000_000_000),dict(usage,free_bytes=20_000_000_000)]), \
                 patch('polysentinel.collect.Collector',return_value=collector), \
                 patch('polysentinel.signals.evaluate',return_value=[weak,strong]), \
                 patch('polysentinel.engine.daily_report'), patch('polysentinel.engine.export_dossier',return_value='report'):
                paused=asyncio.run(run_cycle(store,config,net))
                self.assertEqual(paused['resource_mode'],'paused')
                collector.trades.assert_not_called()
                resumed=asyncio.run(run_cycle(store,config,net))
            self.assertEqual(resumed['resource_mode'],'normal')
            collector.trades.assert_awaited_once()
            self.assertEqual(store.checkpoint('continuity'),dict(cursor='saved'))
            self.assertEqual(store.get('observation','retained')['payload'],dict(proof='unique'))
            self.assertIsNone(store.get('case','weak'))
            self.assertIsNotNone(store.get('case','strong'))
            self.assertEqual(resumed['observation_only_candidates'],1)

    def test_shared_receipt_reconciles_each_owner_without_last_writer_context(self):
        with tempfile.TemporaryDirectory() as root:
            store = Store(root)
            self.addCleanup(store.close)
            store.put('receipt', 'tx', dict(status='confirmed', reconciliation=dict(status='unmatched'), fills=[
                dict(maker='a', token_id='1', side='BUY', log_index=1, shares_raw='1000000', nominal_raw='500000'),
                dict(maker='b', token_id='1', side='BUY', log_index=2, shares_raw='2000000', nominal_raw='1000000')]), observed_at=10)
            for wallet, size in [('a', 1), ('b', 2)]:
                case=dict(wallet=wallet, alerts=[dict(transaction_hash='tx',token_id='1',side='BUY',size=size,nominal=size*.5,timestamp=5)])
                self.assertTrue(case_quality(store,case,now=20)['requirements']['receipt'])
                case['alerts'][0]['size'] += 1
                self.assertFalse(case_quality(store,case,now=20)['requirements']['receipt'])

    def test_receipt_queue_advances_over_actual_signal_transactions(self):
        from polysentinel.investigation import pending_signal_receipts
        with tempfile.TemporaryDirectory() as root:
            store=Store(root)
            self.addCleanup(store.close)
            case=dict(alerts=[dict(transactions=['tx1','tx2'])])
            samples=[dict(transaction_hash='later',nominal=999999)]
            self.assertEqual(pending_signal_receipts(store,case,samples),[('tx1',None)])
            store.put('receipt','tx1',dict(status='confirmed'))
            self.assertEqual(pending_signal_receipts(store,case,samples),[('tx2',None)])
            store.put('receipt','tx2',dict(status='confirmed'))
            self.assertEqual(pending_signal_receipts(store,case,samples),[])

    def test_comparator_excludes_future_and_subject_wallet(self):
        from scripts.review_restoration import comparison
        with tempfile.TemporaryDirectory() as root:
            store=Store(root);self.addCleanup(store.close)
            for key,wallet,ts,observed in [('peer','b',90,95),('future','b',110,95),('late','b',90,110),('self','a',90,95)]:
                store.put('trade',key,dict(wallet=wallet,timestamp=ts,condition_id='c',token_id='t',side='BUY'),observed_at=observed)
            result=comparison(store,dict(wallet='a',calculated_at=100,alerts=[dict(condition_id='c',token_id='t',side='BUY')]))
            self.assertEqual(result['trade_ids'],['peer']);self.assertFalse(result['sufficient'])

    def test_monitor_reports_counts_without_global_payload_scan(self):
        from polysentinel.monitoring import measure
        with tempfile.TemporaryDirectory() as root:
            store=Store(root)
            store.put('trade','x',dict(wallet='a',timestamp=90),observed_at=95)
            store.conn.execute("INSERT INTO cycles(start,end,status) VALUES(1,2,'ok')");store.conn.commit();store.close()
            result=measure(Path(root))
            self.assertIsNone(result['db_pages'])
            self.assertEqual(result['objects'][0]['rows'],1)
            self.assertIsNone(result['objects'][0]['payload_bytes'])

    def test_precise_disk_and_quota_reasons(self):
        config=dict(min_free_bytes=10_000_000_000,data_quota_bytes=5_000_000_000)
        usage=dict(free_bytes=9_440_000_000,project_data_bytes=2_550_000_000)
        self.assertEqual(resource_blockers(config,usage),[dict(code='volume_free_space',free_bytes=9_440_000_000,required_bytes=10_060_000_000,deficit_bytes=620_000_000)])
        usage.update(free_bytes=12_000_000_000,project_data_bytes=4_950_000_000)
        self.assertEqual(resource_blockers(config,usage)[0]['code'],'project_quota')
        usage['project_data_bytes']=2_000_000_000
        self.assertEqual(resource_blockers(config,usage),[])

    def test_archive_roundtrip_idempotence_and_original_url(self):
        from polysentinel.dashboard import server
        with tempfile.TemporaryDirectory() as root:
            Store(root).close()
            reports=Path(root)/'reports';reports.mkdir()
            raw=('<html>'+('preuve '*1000)+'</html>').encode()
            (reports/'case.html').write_bytes(raw)
            (reports/'quotidien-test.json').write_text('{}')
            self.assertGreater(compress_reports(root),0)
            self.assertEqual(compress_reports(root),0)
            self.assertEqual(gzip.decompress((reports/'case.html.gz').read_bytes()),raw)
            self.assertTrue((reports/'quotidien-test.json').exists())
            httpd=server(root,0);thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
            try:
                conn=http.client.HTTPConnection('127.0.0.1',httpd.server_port)
                conn.request('GET','/reports/case.html');response=conn.getresponse()
                self.assertEqual(response.status,200);self.assertEqual(response.read(),raw)
                conn.close()
            finally:
                httpd.shutdown();httpd.server_close();thread.join()
