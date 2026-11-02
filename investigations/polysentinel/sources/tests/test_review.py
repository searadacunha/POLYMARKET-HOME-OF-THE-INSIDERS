import asyncio
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock,patch
from polysentinel.db import Store
from polysentinel.engine import investigations


class ReviewSelectionTests(unittest.TestCase):
    def test_excluded_head_does_not_starve_admissible_case_after_scan_cap(self):
        with tempfile.TemporaryDirectory() as root:
            store=Store(root);self.addCleanup(store.close)
            with store.transaction() as cx:
                for i in range(251):
                    store.put('case',str(i),dict(id=str(i),priority=True,preliminary=True,current=True,score=2),observed_at=i+1,conn=cx)
            config=dict(investigations_per_cycle=1,investigation_max_requests=18,requests_per_cycle=100)
            def scoped(store,case,*args):return {'eligible_for_automatic_investigation':case['id']=='250'}
            with patch('polysentinel.review.case_scope',side_effect=scoped),patch('polysentinel.investigation.investigate',new=AsyncMock(return_value={'id':'proof','errors':[]})) as query,patch('polysentinel.engine.export_dossier',return_value='report'):
                asyncio.run(investigations(store,config,SimpleNamespace(requests_used=0),{'errors':[]}))
                query.assert_not_awaited()
                self.assertEqual(store.checkpoint('engine:investigation_scan'),250)
                asyncio.run(investigations(store,config,SimpleNamespace(requests_used=0),{'errors':[]}))
                query.assert_awaited_once()
                self.assertEqual(query.await_args.args[-1]['id'],'250')

    def test_one_case_observation_per_evaluation_with_report_reference(self):
        from polysentinel.engine import run_cycle
        with tempfile.TemporaryDirectory() as root:
            store=Store(root);self.addCleanup(store.close)
            config=dict(min_free_bytes=0,data_quota_bytes=10**9,catalog_interval=600,
                        notifications=False,investigations_per_cycle=0)
            case=dict(id='c',wallet='w',event_id='e',priority=True,preliminary=True,score=2)
            collector=SimpleNamespace(catalog=AsyncMock(return_value={'status':'ok'}),
                                      trades=AsyncMock(return_value={'status':'ok'}))
            net=SimpleNamespace(begin_cycle=lambda:None,requests_used=0)
            with patch('polysentinel.collect.Collector',return_value=collector),patch('polysentinel.signals.evaluate',return_value=[case]),patch('polysentinel.engine.daily_report'),patch('polysentinel.engine.resources',return_value={'free_bytes':10**12,'project_data_bytes':0}):
                asyncio.run(run_cycle(store,config,net))
            self.assertEqual(store.conn.execute("SELECT COUNT(*) FROM history_refs WHERE kind='case'").fetchone()[0],1)
            self.assertTrue(store.get('case','c')['payload']['report'])
            self.assertEqual(store.count('alert'),1)

    def test_no_automatic_investigation_without_admissible_announcement(self):
        with tempfile.TemporaryDirectory() as root:
            store=Store(root)
            self.addCleanup(store.close)
            store.put('case','c',dict(id='c',priority=True,preliminary=True,current=True))
            config=dict(investigations_per_cycle=1,investigation_max_requests=18,requests_per_cycle=100)
            metrics={'errors':[]}
            with patch('polysentinel.review.case_scope',return_value={'eligible_for_automatic_investigation':False}),patch('polysentinel.investigation.investigate',new=AsyncMock()) as query:
                asyncio.run(investigations(store,config,SimpleNamespace(requests_used=0),metrics))
                query.assert_not_awaited()
            self.assertEqual(metrics['investigation_selection']['scanned'],1)
            self.assertEqual(metrics['investigation_selection']['eligible'],0)
            store.put('task','manual',{'target':'event','status':'pending'})
            with patch('polysentinel.review.case_scope',return_value={'eligible_for_automatic_investigation':False}),patch('polysentinel.investigation.investigate',new=AsyncMock(return_value={'id':'i','errors':[]})) as query,patch('polysentinel.engine.export_dossier',return_value='report'):
                asyncio.run(investigations(store,config,SimpleNamespace(requests_used=0),{'errors':[]}))
                query.assert_awaited_once()
