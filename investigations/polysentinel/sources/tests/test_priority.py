"""Operational selection checks, not detection calibration."""
import tempfile
import unittest
from unittest.mock import patch
from polysentinel.db import Store
from polysentinel.priority import announcement_scope,market_exclusion_reason,select_markets

NOW=1800000000
def event(**changes):
    return dict(dict(id='e',title='Annual awards',tags=['awards'],active=True,closed=False,
        observed_at=NOW-60,end_date=NOW+3600,raw={'resolutionSource':'https://official.example/awards'}),**changes)
def market(key='1',**changes):
    return dict(dict(id=key,event_id='e',question="Will Alice win the Ballon d'Or?",
        condition_id='0x'+f'{int(key):064x}',active=True,closed=False,observed_at=NOW-60,
        end_date=NOW+3600,tokens=[{'token_id':key,'outcome':'Yes'}],raw={}),**changes)

class ScopeTests(unittest.TestCase):
    def test_source_date_and_announcement_required(self):
        result=announcement_scope(market(),event(),NOW)
        self.assertTrue(result['eligible']);self.assertEqual(result['category'],'awards')
        for m,e in [(market(),event(raw={})),(market(end_date=None),event(end_date=None)),
                    (market(end_date='2028-01-01T12:00:00'),event())]:
            self.assertFalse(announcement_scope(m,e,NOW)['eligible'])
    def test_tags_prices_and_sport_insufficient(self):
        for title in ['Who wins the next election?','Bitcoin price above $100000?',
                      'Will Arsenal win the Premier League?','Will Team A win today?']:
            self.assertFalse(announcement_scope(market(question=title),event(tags=['politics','awards']),NOW)['eligible'])
    def test_discrete_decisions(self):
        for title,category in [('Fed interest rate decision in November?','central_bank'),
            ('Apple quarterly earnings above expectations?','earnings'),('October CPI report above 3%?','economic_data'),
            ('Will the FDA approve Drug A?','regulatory'),('Will Example launch a token?','token_launch'),
            ('Who will be nominated as chair?','nomination')]:
            with self.subTest(title=title):
                result=announcement_scope(market(question=title),event(),NOW)
                self.assertTrue(result['eligible']);self.assertEqual(result['category'],category)
    def test_future_finished_unknown_and_result(self):
        for change,reason in [({'observed_at':NOW+1},'market_future'),({'closed':True},'closed'),
            ({'closed':None},'inactive_or_unknown'),({'active':False},'inactive'),({'end_date':NOW-1},'expired'),
            ({'verified':True,'result_available':True},'public_result')]:
            self.assertEqual(market_exclusion_reason(market(**change),event(),NOW),reason)
        self.assertEqual(market_exclusion_reason(market(),event(observed_at=NOW+1),NOW),'event_future')
        self.assertIsNone(market_exclusion_reason(market(active=1,closed=0),event(),NOW))

class QueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
        self.store.put('event','e',event(),observed_at=NOW-60)
    def tearDown(self):self.store.close();self.tmp.cleanup()
    def add(self,key,attempt=None,announcement=True,**changes):
        value=market(str(key),**changes)
        if not announcement:value['question']='Will a broad political outcome occur?'
        self.store.put('market',str(key),value,observed_at=NOW-60)
        if attempt is not None:self.store.put('market_coverage',str(key),{'status':'ok'},observed_at=attempt)
    def test_cap_general_minimum_and_new_revisits(self):
        for i in range(1,25):self.add(i,attempt=NOW-1000-i if i%2 else None,announcement=i>12)
        selected,summary=select_markets(self.store,{},NOW,100)
        self.assertEqual(len(selected),10);self.assertEqual(len({m['id'] for m in selected}),10)
        self.assertGreaterEqual(summary['exploration_selected'],5)
        self.assertEqual({s['coverage_state'] for s in summary['selected']},{'never_queried','revisit'})
        self.assertEqual(summary['selected'][0]['lane'],'exploration');self.assertFalse(summary['history_complete'])
    def test_strata_use_attempt_age_not_metadata_refresh(self):
        for i in range(1,20):self.add(i)
        self.add(20,attempt=NOW-99999,announcement=False,observed_at=NOW-1)
        self.add(21,attempt=NOW-100,announcement=False,observed_at=NOW-1000)
        selected,summary=select_markets(self.store,{},NOW,10)
        strata=summary['sampling']['strata']
        self.assertTrue(any(s['stratum'].endswith('|over_24h') and s['population']==1 for s in strata))
        self.assertTrue(any(s['stratum'].endswith('|under_1h') and s['population']==1 for s in strata))
        self.assertTrue(all(s['inclusion_probability']>0 for s in strata))
    def test_single_slot_seed_reproduces_after_restart(self):
        self.add(1,attempt=NOW-1000,announcement=False);self.add(2,announcement=False)
        config={'targeting_seed':'restart-fixture'}
        selected,summary=select_markets(self.store,config,NOW,1)
        self.assertEqual(len(selected),1)
        self.assertTrue(all(s['inclusion_probability']==.5 for s in summary['sampling']['strata']))
        self.store.checkpoint('collect:queue',summary);self.store.close();self.store=Store(self.tmp.name)
        self.assertEqual(select_markets(self.store,config,NOW,1)[0][0]['id'],selected[0]['id'])
    def test_current_public_excluded_future_ignored(self):
        self.add(1);self.add(2);self.add(3,observed_at=NOW+1);self.add(4,end_date=NOW-1)
        for key,at in [('1',NOW-5),('2',NOW+5)]:
            self.store.put('public_condition',market(key)['condition_id'],
                {'verified':True,'result_available':True,'public_at':at},observed_at=at)
        selected,summary=select_markets(self.store,{},NOW,10)
        self.assertEqual([m['id'] for m in selected],['2'])
        self.assertEqual(summary['excluded'],{'public_result':1,'market_future':1,'expired':1})
        self.store.put('event','e',event(observed_at=NOW+1),observed_at=NOW+1)
        self.assertEqual(select_markets(self.store,{},NOW,10)[0],[])
    def test_reduced_zero_limits_checkpoint_decode_bound(self):
        import json,zlib
        from polysentinel.collect import Collector
        for i in range(1,11):self.add(i)
        decoded=[]
        def inflate(body):
            raw=zlib.decompress(body).decode();decoded.append(json.loads(raw).get('id'));return raw
        self.store.conn.create_function('payload_text',1,inflate,deterministic=True)
        selected,_=select_markets(self.store,{},NOW,2)
        self.assertEqual(len(selected),2);self.assertLessEqual(len(decoded),13)
        self.assertEqual(select_markets(self.store,{},NOW,0)[0],[])
        collector=Collector(self.store,None,{'market_batches':1,'markets_per_batch':2})
        with patch('polysentinel.collect.time.time',return_value=NOW):collector._fair_markets()
        summary=self.store.checkpoint('collect:queue')
        self.assertEqual(summary['selected_count'],2);self.assertTrue(summary['bounded'])
        archived=self.store.get('collection_selection',summary['selection_id'])
        self.assertEqual(archived['payload'],summary)
        before=self.store.count('collection_selection')
        original=self.store.checkpoint
        def fail_queue(key,value=None,conn=None):
            if key=='collect:queue' and value is not None:raise RuntimeError('Interrupted pre-poll commit')
            return original(key,value,conn)
        with patch.object(self.store,'checkpoint',side_effect=fail_queue):
            with self.assertRaises(RuntimeError):collector._fair_markets()
        self.assertEqual(self.store.count('collection_selection'),before)
        self.assertEqual(self.store.checkpoint('collect:queue'),summary)
    def test_known_event_result_and_future_payload_not_inflated(self):
        import json,zlib
        self.add(1)
        self.store.put('market','2',market('2',observed_at=NOW+1),observed_at=NOW+1)
        decoded=[]
        def inflate(body):
            raw=zlib.decompress(body).decode();decoded.append(json.loads(raw).get('id'));return raw
        self.store.conn.create_function('payload_text',1,inflate,deterministic=True)
        selected,_=select_markets(self.store,{},NOW,10)
        self.assertEqual([m['id'] for m in selected],['1']);self.assertNotIn('2',decoded)
        self.store.put('public_milestone','e',{'verified':True,'result_available':True,'public_at':NOW-1},observed_at=NOW-1)
        self.assertEqual(select_markets(self.store,{},NOW,10)[0],[])
