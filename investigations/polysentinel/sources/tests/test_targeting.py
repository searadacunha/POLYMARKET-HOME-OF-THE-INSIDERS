"""Operational targeting and exact sampling probabilities; synthetic data only."""
from copy import deepcopy
import math
import tempfile
import unittest
from unittest.mock import patch
from polysentinel.db import Store
from polysentinel.priority import market_changes,stratified_sample,select_markets,_history_samples,_recent_activity

NOW=1800000000
def market(key='1',at=NOW-60,price=.2,volume=100,question='Will an outcome occur?'):
    return dict(id=key,event_id='e',condition_id='0x'+f'{int(key):064x}',active=True,closed=False,
        observed_at=at,end_date=NOW+3600,version='v2',question=question,
        tokens=[dict(token_id=key+'0',outcome='Yes'),dict(token_id=key+'1',outcome='No')],
        raw=dict(outcomePrices=[price,1-price],volume=volume,resolutionSource='https://official.example/source'))

class ChangeTests(unittest.TestCase):
    def test_rates_use_real_duration_and_cumulative_counter(self):
        before=market(at=NOW-360,price=.2,volume=100)
        current=market(price=.3,volume=250)
        change=market_changes(current,before,NOW)
        self.assertEqual(change['span_seconds'],300)
        self.assertAlmostEqual(change['price_rate_600s'],.2)
        self.assertEqual(change['cumulative_volume_delta'],150)
        self.assertEqual(change['volume_rate_600s'],300)
        for row in (before,current):row['raw'].pop('volume');row['raw']['volume24hr']=999999
        self.assertIsNone(market_changes(current,before,NOW)['volume_rate_600s'])
    def test_missing_future_stale_reset_and_changed_tokens(self):
        before=market(at=NOW-660,volume=200);current=market(volume=100)
        self.assertEqual(market_changes(current,before,NOW)['volume_unknown'],'counter_reset')
        for row in (market(at=NOW+1),market(at=NOW-1000)):
            self.assertIsNone(market_changes(row,before,NOW)['price_rate_600s'])
        current['tokens'][0]['outcome']='Alice'
        self.assertEqual(market_changes(current,before,NOW)['price_unknown'],'token_identity_changed')
        before['observed_at']=NOW+1
        self.assertEqual(market_changes(current,before,NOW)['price_unknown'],'future_observation')
        self.assertIsNone(market_changes(current,None,NOW)['price_rate_600s'])

class SamplingTests(unittest.TestCase):
    def test_two_stage_probability_positive_reproducible_and_random(self):
        strata={str(i):[f'{i}-{j}' for j in range(i+2)] for i in range(8)}
        chosen,design=stratified_sample(strata,5,'seed-a')
        self.assertEqual((chosen,design),stratified_sample(strata,5,'seed-a'))
        self.assertNotEqual(chosen,stratified_sample(strata,5,'seed-b')[0])
        self.assertEqual(len(chosen),5);self.assertEqual(len({r[0] for r in chosen}),5)
        for row in design['strata']:
            self.assertAlmostEqual(row['inclusion_probability'],5/(8*row['population']))
            self.assertGreater(row['inclusion_probability'],0)
        self.assertEqual(sum(row['sample_size'] for row in design['strata']),5)
    def test_more_slots_than_strata_and_small_strata_saturation(self):
        for sizes,slots in [([1,2,10],5),([2,3,10],4),([1,1],9)]:
            strata={str(i):[f'{i}-{j}' for j in range(n)] for i,n in enumerate(sizes)}
            selected,design=stratified_sample(strata,slots,13)
            self.assertEqual(len(selected),min(slots,sum(sizes)))
            self.assertAlmostEqual(sum(s['population']*s['inclusion_probability'] for s in design['strata']),len(selected))
            if sizes==[1,2,10]:self.assertEqual([s['inclusion_probability'] for s in design['strata']],[1,1,.2])
            if sizes==[2,3,10]:
                for row in design['strata']:self.assertAlmostEqual(row['inclusion_probability'],(1+1/3)/row['population'])
        self.assertEqual(stratified_sample({'a':['x']},0,1)[0],[])

class TargetingStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
        self.store.put('event','e',dict(id='e',active=True,closed=False,observed_at=NOW-100,end_date=NOW+3600,tags=[]),observed_at=NOW-100)
    def tearDown(self):self.store.close();self.tmp.cleanup()
    def put_market(self,value):self.store.put('market',value['id'],value,observed_at=value['observed_at'])
    def put_trade(self,key,at,wallet,observed=NOW-1):
        self.store.put('trade',key,dict(wallet=wallet,timestamp=at,condition_id=market()['condition_id']),observed_at=observed)
    def test_count_concentration_equal_windows_without_trade_payloads(self):
        self.put_trade('a',NOW-900,'wallet-a');self.put_trade('b',NOW-800,'wallet-b')
        for i,at in enumerate((NOW-200,NOW-100,NOW-50)):self.put_trade('c'+str(i),at,'wallet-a')
        self.put_trade('future-known',NOW-20,'wallet-c',NOW+1)
        self.put_trade('future-time',NOW+1,'wallet-c')
        self.store.conn.create_function('payload_text',1,lambda _:self.fail('trade payload decompressed'))
        values,status=_recent_activity(self.store,NOW);value=values[market()['condition_id']]
        self.assertEqual((value['previous_count'],value['current_count']),(2,3))
        self.assertEqual(value['activity_change'],1);self.assertEqual(value['concentration_change'],.5)
        self.assertEqual(status['future_observations_excluded'],1)
        with patch('polysentinel.priority.ACTIVITY_LIMIT',2):
            values,status=_recent_activity(self.store,NOW)
        self.assertEqual(values,{});self.assertEqual(status['status'],'capped');self.assertEqual(status['rows_read'],3)
    def test_history_cap_applies_before_payload_decompression(self):
        import json,zlib
        for key in ('1','2','3'):self.put_market(market(key,at=NOW-660))
        decoded=[]
        def inflate(body):
            raw=zlib.decompress(body).decode();decoded.append(json.loads(raw)['id']);return raw
        self.store.conn.create_function('payload_text',1,inflate,deterministic=True)
        with patch('polysentinel.priority.HISTORY_LIMIT',2):values,status=_history_samples(self.store,NOW)
        self.assertEqual(status['status'],'capped');self.assertEqual(status['references_read'],3)
        self.assertEqual(status['snapshots_used'],2);self.assertEqual(len(decoded),2)
    def test_half_random_cooldown_categories_and_reopen_reproducibility(self):
        for i in range(1,21):
            title='October CPI report?' if i%2 else 'Bitcoin price above $100000?'
            if i<=10:self.put_market(market(str(i),at=NOW-660,question=title))
            self.put_market(market(str(i),price=.2+i/100 if i<=10 else .2,volume=100+i*10,question=title))
        self.store.put('market_coverage','10',{'status':'ok'},observed_at=NOW-10)
        config={'targeting_seed':'replay'}
        selected,summary=select_markets(self.store,config,NOW,100)
        self.assertEqual(len(selected),10);self.assertEqual(summary['targeting_selected'],5)
        self.assertEqual(summary['exploration_selected'],5)
        targets=[r for r in summary['selected'] if r['lane']=='targeting']
        self.assertNotIn('10',{r['market_id'] for r in targets})
        self.assertEqual(len({r['category'] for r in targets}),1)
        self.assertTrue(all(r['announcement_eligible'] for r in targets))
        self.assertGreater(sum(s['population'] for s in summary['sampling']['strata'] if s['stratum'].startswith('price|')),0)
        self.assertEqual(len({r['market_id'] for r in summary['selected']}),10)
        self.assertTrue(all(r['inclusion_probability']>0 for r in summary['sampling']['strata']))
        self.assertFalse(summary['history_complete']);self.assertNotIn('_audit_frame',summary)
        self.store.close();self.store=Store(self.tmp.name)
        again=select_markets(self.store,config,NOW,100)[1]
        self.assertEqual(summary['selected'],again['selected'])
        self.assertEqual(summary['sampling']['frame_sha256'],again['sampling']['frame_sha256'])
        for limit in (0,2):
            chosen,state=select_markets(self.store,config,NOW,limit)
            self.assertEqual(len(chosen),limit);self.assertGreaterEqual(state['exploration_selected'],math.ceil(limit/2))
    def test_future_comparator_and_capped_activity_remain_unknown(self):
        old=market(at=NOW+1)
        self.store.put('market','1',old,observed_at=NOW-660)
        self.put_market(market(price=.9,volume=900))
        for i in range(3):self.put_trade(str(i),NOW-100-i,'same-wallet')
        with patch('polysentinel.priority.ACTIVITY_LIMIT',2):
            _,summary=select_markets(self.store,{'targeting_seed':5},NOW,10)
        self.assertEqual(summary['targeting_selected'],0)
        self.assertEqual(summary['targeting']['activity']['status'],'capped')
        for count in summary['targeting']['unknown_components'].values():self.assertEqual(count,1)
