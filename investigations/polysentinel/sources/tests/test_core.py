"""Synthetic fixtures: durable history and local service boundaries."""
import tempfile
import unittest
import asyncio
from types import SimpleNamespace
from unittest.mock import patch, AsyncMock
from polysentinel.db import Store
from polysentinel.engine import payloads, instance
from polysentinel.dashboard import snapshot
from polysentinel import service

class CoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.store=Store(self.tmp.name);self.addCleanup(self.store.close)
    def test_atomic_page_rollback(self):
        with self.assertRaises(RuntimeError):
            with self.store.transaction() as cx:
                self.store.put('trade','a',{'size':1},conn=cx)
                self.store.checkpoint('page',{'cursor':'next'},conn=cx)
                raise RuntimeError('interruption')
        self.assertIsNone(self.store.get('trade','a'))
        self.assertIsNone(self.store.checkpoint('page'))
    def test_history_return_to_old_value(self):
        for at,value in ((1,'A'),(2,'B'),(3,'A')):
            self.store.put('event','x',{'title':value},observed_at=at)
        self.assertEqual(payloads(self.store,'event',as_of=3)[0]['title'],'A')
        self.assertEqual(payloads(self.store,'event',as_of=2)[0]['title'],'B')
    def test_single_instance(self):
        with instance(self.tmp.name):
            with self.assertRaises(RuntimeError):
                with instance(self.tmp.name):pass
    def test_stop_removes_supervision(self):
        with patch.object(service,'status',side_effect=[{'loaded':True},{'loaded':False}]),patch.object(service.subprocess,'run') as call:
            self.assertFalse(service.stop()['loaded'])
            self.assertEqual([c.args[0][1] for c in call.call_args_list],['bootout','disable'])
    def test_launch_policy_keeps_nice_without_background_cpu_throttle(self):
        import plistlib
        from pathlib import Path
        path=Path(self.tmp.name)/'service.plist'
        with patch.object(service,'plist_path',return_value=path):
            service.install({'root':self.tmp.name})
        plist=plistlib.loads(path.read_bytes())
        self.assertEqual(plist['ProcessType'],'Standard');self.assertEqual(plist['Nice'],5)
        self.assertTrue(plist['KeepAlive'])
    def test_learning_case_not_priority(self):
        self.store.health('trades:global','ok','valide')
        self.store.put('case','x',{'priority':False,'score':1})
        self.assertIn('aucun dossier prioritaire',snapshot(self.store)['verdict'])
    def test_empty_and_unavailable_differ(self):
        self.assertIn('indisponible',snapshot(self.store)['verdict'])
        self.store.health('trades:global','empty','valide')
        self.assertIn('aucun dossier prioritaire',snapshot(self.store)['verdict'])
    def test_successful_investigation_replaces_stale_failure(self):
        from polysentinel.engine import investigations
        self.store.health('investigation','error','ancien échec')
        self.store.put('task','t',{'target':'event','status':'pending'})
        config={'investigations_per_cycle':1,'investigation_max_requests':18,'requests_per_cycle':100}
        with patch('polysentinel.investigation.investigate',new=AsyncMock(return_value={'id':'event','errors':[]})),patch('polysentinel.engine.export_dossier'):
            asyncio.run(investigations(self.store,config,SimpleNamespace(requests_used=0),{'errors':[]}))
        self.assertEqual(self.store.get('health','investigation')['payload']['status'],'ok')
        self.assertEqual(self.store.get('task','t')['payload']['status'],'done')
    def test_automatic_enrichment_interval_does_not_delay_manual_task(self):
        import time
        from polysentinel.engine import investigations
        self.store.put('case','c',{'id':'c','current':True,'priority':True})
        self.store.checkpoint('engine:last_auto_investigation',time.time())
        config={'investigations_per_cycle':1,'investigation_max_requests':18,'requests_per_cycle':100,'automatic_investigation_interval':600}
        with patch('polysentinel.investigation.investigate',new=AsyncMock(return_value={'id':'event','errors':[]})) as query,patch('polysentinel.engine.export_dossier'):
            asyncio.run(investigations(self.store,config,SimpleNamespace(requests_used=0),{'errors':[]}))
            query.assert_not_awaited()
            self.store.put('task','manual',{'target':'event','status':'pending'})
            asyncio.run(investigations(self.store,config,SimpleNamespace(requests_used=0),{'errors':[]}))
            query.assert_awaited_once()

class MappingTests(unittest.TestCase):
    def test_live_trade_limit_bounds_decoding_preserves_ties_and_time_cutoffs(self):
        import zlib
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as root:
            store=Store(root)
            try:
                with store.transaction() as cx:
                    for i in range(1,501):
                        key=f'{i:04d}'
                        store.put('trade',key,{'id':key,'wallet':'w','timestamp':i,'raw':{'source':'retained'}},observed_at=900,conn=cx)
                    for key,stamp,observed in [('tie-b',499,900),('tie-a',499,900),('future-observation',700,1001),('future-trade',1100,900)]:
                        store.put('trade',key,{'id':key,'wallet':'w','timestamp':stamp},observed_at=observed,conn=cx)
                decoded=[]
                def decode(body):
                    decoded.append(1)
                    return zlib.decompress(body).decode()
                store.conn.create_function('payload_text',1,decode,deterministic=True)
                with patch('polysentinel.engine.time.time',return_value=1000):
                    rows=payloads(store,'trade',limit=4)
                self.assertEqual([p['id'] for p in rows],['0500','0499','tie-a','tie-b'])
                self.assertTrue(all('raw' not in p and p['observed_at']==900 for p in rows))
                self.assertLessEqual(len(decoded),8,'A small live limit must not decompress the whole trade history')
            finally:store.close()

    def test_recent_transaction_is_not_evicted_by_newly_ingested_old_history(self):
        with tempfile.TemporaryDirectory() as root:
            store=Store(root)
            try:
                store.put('trade','recent',{'wallet':'w','timestamp':90},observed_at=100)
                store.put('trade','backfill',{'wallet':'w','timestamp':1},observed_at=200)
                self.assertEqual(payloads(store,'trade',limit=1)[0]['timestamp'],90)
                self.assertEqual(payloads(store,'trade',limit=1,as_of=200)[0]['timestamp'],90)
            finally:store.close()
    def test_catalog_later_enriches_analysis_without_rewriting_trade(self):
        from polysentinel.engine import map_trades
        trade={'id':'t','condition_id':'c','token_id':'tok','event_id':'','market_id':'','observed_at':10}
        market={'id':'m','event_id':'e','condition_id':'c','tokens':[{'token_id':'tok'}],'observed_at':20}
        self.assertEqual(map_trades([trade],[market],[],15)[0]['market_id'],'')
        self.assertEqual(map_trades([trade],[market],[],25)[0]['market_id'],'m')
        self.assertEqual(trade['market_id'],'')
        self.assertEqual(map_trades([trade],[market],[],25)[0]['observed_at'],10)
    def test_stale_case_no_longer_priority(self):
        from polysentinel.engine import expire_cases
        with tempfile.TemporaryDirectory() as root:
            store=Store(root)
            try:
                store.put('case','x',{'priority':True,'score':2,'preliminary':True})
                expire_cases(store,set(),100)
                c=store.get('case','x')['payload']
                self.assertFalse(c['priority']);self.assertEqual(c['score'],2)
            finally:store.close()

class PublicKnowledgeTests(unittest.TestCase):
    def test_wallet_history_respects_observation_cutoff_and_analysis_cap(self):
        from polysentinel.engine import wallet_history
        with tempfile.TemporaryDirectory() as root:
            store=Store(root)
            try:
                store.put('trade','old',{'wallet':'w','timestamp':10},observed_at=20)
                store.put('trade','recent',{'wallet':'w','timestamp':90},observed_at=100)
                store.put('trade','late_discovery',{'wallet':'w','timestamp':1},observed_at=150)
                self.assertEqual(wallet_history(store,100)['w']['first_timestamp'],10)
                self.assertEqual(wallet_history(store,200)['w']['first_timestamp'],1)
            finally:store.close()
    def test_replay_keeps_only_known_milestone(self):
        from polysentinel.engine import apply_public_knowledge
        with tempfile.TemporaryDirectory() as root:
            store=Store(root)
            try:
                store.put('public_milestone','e',{'verified':True,'result_available':True,'public_at':20,'public_observed_at':20},observed_at=20)
                before=[{'id':'e'}];after=[{'id':'e'}]
                apply_public_knowledge(store,before,[],15)
                apply_public_knowledge(store,after,[],25)
                self.assertNotIn('public_at',before[0]);self.assertEqual(after[0]['public_at'],20)
            finally:store.close()
