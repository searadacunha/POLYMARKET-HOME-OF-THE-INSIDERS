import gzip
import http.client
import json
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch

from polysentinel.db import Store
from polysentinel.quality import case_quality, measure_quality, targeted_context


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.store = Store(self.tmp.name)
        self.addCleanup(self.store.close)
        self.case = dict(id='c', wallet='wallet', event_id='event', current=True, priority=True,
                         score=2, calculated_at=145, preliminary=True,
                         alerts=[dict(transaction_hash='tx', token_id='token', side='BUY', timestamp=140,size=1,nominal=0.5)])

    def proofs(self, kind='public_information'):
        self.store.put('receipt', 'tx', dict(status='confirmed', reconciliation=dict(status='matched', log_indices=[7],nominal_tolerance=0.000001),
                       fills=[dict(log_index=7, maker='wallet', token_id='token', side='BUY',shares_raw='1000000',nominal_raw='500000')]), observed_at=160)
        self.store.put('public_milestone', 'event', dict(milestone_type=kind, verified=True, result_available=True,
                       public_at=150, source_url='https://example.org/statement', evidence_id='source'), observed_at=160)
        self.case.update(comparator=dict(sufficient=True, evidence_ids=['control']),
                         historical_exposure=dict(verified=True, at_signal=True, evidence_ids=['inventory']))

    def test_four_sourced_requirements(self):
        result = case_quality(self.store, self.case, now=200)
        self.assertFalse(result['exploitable'])
        self.assertEqual(set(result['missing']), {'receipt', 'public_time', 'comparator', 'inventory_at_signal'})
        self.case['actual_inventory'] = 100
        self.assertFalse(case_quality(self.store, self.case, now=200)['requirements']['inventory_at_signal'])
        self.proofs()
        self.assertTrue(case_quality(self.store, self.case, now=200,scope={'eligible_for_automatic_investigation':True})['exploitable'])
        documented=case_quality(self.store, self.case, now=200,scope={'eligible_for_automatic_investigation':False})
        self.assertTrue(documented['documentary_complete'])
        self.assertTrue(documented['exploitable'])
        self.assertFalse(documented['scope_eligible'])
        self.case['calculated_at']=150
        self.assertFalse(case_quality(self.store,self.case,now=200,scope={'eligible_for_automatic_investigation':True})['exploitable'])
        self.assertEqual(self.case['score'], 2)

    def test_resolution_future_information_and_wrong_owner_do_not_pass(self):
        self.proofs('official_resolution')
        result = case_quality(self.store, self.case, now=200)
        self.assertFalse(result['exploitable'])
        self.assertEqual(result['public_timing'][0]['status'], 'resolution_only')
        self.proofs()
        self.assertFalse(case_quality(self.store, self.case, now=155)['exploitable'])
        self.case['wallet'] = 'other'
        self.assertFalse(case_quality(self.store, self.case, now=200)['requirements']['receipt'])
        self.case['alerts'][0]['timestamp'] = 170
        self.assertEqual(case_quality(self.store, self.case, now=200)['public_timing'][0]['status'], 'after_public_information')

    def test_denominators_diagnostics_and_cache_invalidation(self):
        self.store.put('case', 'c', self.case, observed_at=180)
        self.store.put('case', 'old', dict(id='old', priority=True, current=False), observed_at=180)
        self.store.put('case', 'learning', dict(id='learning', priority=False), observed_at=180)
        self.store.put('rejected_trade', 'bad', dict(reason='token unmapped'), observed_at=180)
        self.store.put('health', 'analysis', dict(diagnostics=dict(examined_recent_buy_pairs=17)), observed_at=180)
        queries=[];self.store.conn.set_trace_callback(queries.append)
        with patch('polysentinel.quality.case_scope', return_value=dict(eligible_for_automatic_investigation=False, reason='No announcement')):
            result = measure_quality(self.store, now=200)
            self.assertIs(measure_quality(self.store, now=201), result)
            self.assertEqual(result['counts']['all_cases'], 3)
            self.assertEqual(result['counts']['current_priority'], 1)
            self.assertEqual(result['counts']['current_nonpriority'], 1)
            self.assertEqual(result['counts']['historical_cases'], 1)
            self.assertEqual(result['counts']['exploitable'], 0)
            self.assertEqual(result['rejected_reasons'], {'token unmapped': 1})
            self.assertEqual(result['latest_analysis']['diagnostics']['examined_recent_buy_pairs'], 17)
            self.store.put('case', 'new', dict(self.case, id='new'), observed_at=202)
            self.assertEqual(measure_quality(self.store, now=203)['counts']['current_priority'], 2)
        self.assertFalse(any("kind='trade'" in query for query in queries))

    def test_targeted_context_is_limited_to_case_and_wallet(self):
        path=Path(self.tmp.name)/'evidence/targeted_20261027/inquiries/display.json'
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps(dict(receipts=[dict(case_id='c',wallet='wallet',transaction_hash='yes'),
            dict(case_id='other',wallet='other',transaction_hash='no')], balances=[dict(wallet='wallet',balance='1'),
            dict(wallet='other',balance='999')],balance_observed_utc_start='2026-10-27T21:45:32Z')))
        result=targeted_context(Path(self.tmp.name), self.case)
        self.assertEqual(len(result['receipts']),1);self.assertEqual(len(result['balances']),1)
        self.assertEqual(result['balance_observed_utc_start'],'2026-10-27T21:45:32Z')
        self.assertFalse(result['historical_net_inventory_reconstructed'])
        self.assertIsNone(targeted_context(Path(self.tmp.name),dict(self.case,id='unrelated')))

    def test_condition_resolution_is_not_announcement_and_one_fill_is_not_two_groups(self):
        self.case['alerts'][0]['condition_id']='condition'
        self.store.put('public_condition','condition',dict(milestone_type='official_resolution',verified=True,
            result_available=True,public_at=150,source_url='https://example.org/resolutions',evidence_id='proof'),observed_at=160)
        result=case_quality(self.store,self.case,now=200)
        self.assertEqual(result['public_timing'][0]['status'],'resolution_only')
        self.assertFalse(result['requirements']['public_time'])
        self.proofs()
        self.case['alerts'][0]['size']=2
        self.assertFalse(case_quality(self.store,self.case,now=200)['requirements']['receipt'])
        self.case['alerts'][0]['size']=1
        self.case['alerts'].append(dict(self.case['alerts'][0]))
        self.assertFalse(case_quality(self.store,self.case,now=200)['requirements']['receipt'])


class DashboardDownloadTests(unittest.TestCase):
    def test_gzip_preserves_bytes_and_content_type(self):
        from polysentinel.dashboard import server
        with tempfile.TemporaryDirectory() as root:
            store=Store(root);store.close()
            reports=Path(root)/'reports';reports.mkdir()
            raw=gzip.compress(b'{"proof":true}',mtime=0)
            (reports/'evidence.json.gz').write_bytes(raw)
            httpd=server(root,0);thread=threading.Thread(target=httpd.serve_forever,daemon=True);thread.start()
            try:
                conn=http.client.HTTPConnection('127.0.0.1',httpd.server_port)
                conn.request('GET','/reports/evidence.json.gz');response=conn.getresponse()
                self.assertEqual(response.status,200)
                self.assertEqual(response.getheader('Content-Type'),'application/gzip')
                self.assertEqual(response.read(),raw)
                conn.close()
            finally:
                httpd.shutdown();httpd.server_close();thread.join()
