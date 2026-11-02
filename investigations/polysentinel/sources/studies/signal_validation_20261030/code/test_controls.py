import json
import random
import tempfile
from unittest.mock import patch
from pathlib import Path
import unittest
import ana_signal as a

NOW=1000000
CONFIG=dict(analysis_trade_limit=50000,minimum_baseline=20,large_nominal=1000,candidate_score=2)

def fixture(seed, scale, last):
    rng=random.Random(seed)
    rows=[]
    for i,amount in enumerate([scale*(1+rng.random()*.1) for _ in range(25)]+[last]):
        rows.append(dict(id=str(i),wallet=a.TARGET,event_id=a.EVENT,market_id='market',token_id='token',
            condition_id='condition',side='BUY',price=.5,size=amount*2,timestamp=NOW-5000+i*100,
            observed_at=NOW+100000,transaction_hash='tx'+str(i)))
    return rows

class Controls(unittest.TestCase):
    def test_scenarios(self):
        for seed in (0,1,2):
            for scale,last,expected in ((5,5,0),(30,500,1),(30,5000,2)):
                rows=fixture(seed,scale,last)
                for delay in (0,60,300,900):
                    cases,diag,selected,adapted,history=a.snapshot(rows,NOW,delay,CONFIG)
                    target=a.target_case(cases)
                    self.assertEqual(target['score'] if target else 0,expected)
                    features=a.pair_features(adapted,cases,NOW,CONFIG,history)
                    self.assertEqual(len(features),diag['examined_recent_buy_pairs'])
                    self.assertTrue(features[0]['baseline_capable'])
                    self.assertEqual(features[0]['joint'],expected==2)
                strict=a.signals.evaluate(rows,[],[],now=NOW,config=CONFIG)
                self.assertEqual(strict,[])
            rows=fixture(seed,30,5000)
            cases,*_=a.snapshot(rows[:-1],NOW,0,CONFIG)
            self.assertFalse(a.target_case(cases))
            cases,*_=a.snapshot(rows,rows[-1]['timestamp']-1,0,CONFIG)
            self.assertFalse(a.target_case(cases))
            cases,*_=a.snapshot(rows,rows[-1]['timestamp'],0,CONFIG)
            self.assertEqual(a.target_case(cases)['score'],2)

    def test_queue_ties(self):
        def record(w,t,score):
            return dict(wallet=w,evaluated_ever=True,first_conditional_priority_at=t,best_score=score)
        q=a.queue([record('0x00',1,2),record(a.TARGET,2,2),record('0xff',2,3),record('0xzz',None,0)])
        self.assertEqual((q['queue_position'],q['queue_tie_interval'],q['peak_score_rank_interval']),(2,[2,3],[2,3]))
        self.assertEqual(q['priority'],3)

    def test_censored_age_uses_full_prefix(self):
        rows=fixture(0,30,5000)
        config=dict(CONFIG,analysis_trade_limit=2)
        cases,diag,_,adapted,history=a.snapshot(rows,NOW,0,config)
        features=a.pair_features(adapted,cases,NOW,config,history)
        self.assertEqual(features[0]['age_observed_hours'],5000/3600)
        self.assertEqual(diag['clipped_rows'],24)

    def test_registry_stale_witness_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'witness.json';path.write_text('{"n": 1}')
            with patch.object(a,'lire',return_value=([{},{}],[])), patch.object(a,'_nom_temoin',return_value=str(path)):
                with self.assertRaises(RuntimeError): a.verify_registry()

    def test_invalid_timestamp_rejected(self):
        rows=fixture(0,30,5000);rows[0]['timestamp']=float('nan')
        with self.assertRaises(ValueError): a.snapshot(rows,NOW,0,CONFIG)

    def test_transaction_removal_preserves_peer_context(self):
        own=fixture(0,30,5000)[-1]
        peer=dict(own,wallet='peer')
        self.assertEqual(a.drop_target_transaction([own,peer],own['transaction_hash']),[peer])

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful(): raise SystemExit(1)
    p=a.STUDY/'controles/synthetic.json'
    p.write_text(json.dumps(dict(seeds=[0,1,2],expected_scores=[0,1,2],observed_exact=True,
        checks='native kernel, availability, baseline, conjunction, deletion, queue ties',
        limitation='deterministic controls, no population power or FPR'),indent=2))
    a.registered(test='synthetic_pipeline_controls',declare=True,n=234,n_effectif=3,
        n_comparaisons=59,agent='root-signal-audit',donnees='synthetiques',sortie='controles/synthetic.json',
        note='9 fixtures de26 lignes, 3 graines; anciennes entrées n78 comptaient les lignes par niveau')
