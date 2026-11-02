"""Synthetic pagination/funding tests; no statistical detection claims."""
import tempfile
import unittest
from types import SimpleNamespace
from polysentinel.db import Store
from polysentinel.investigation import wallet_feed,funding_graph,activity_sequences,Budget,BudgetExceeded
WALLET='0x'+'1'*40
OTHER='0x'+'2'*40
FUNDER='0x'+'3'*40

def row(tx='a',kind='TRADE'):return dict(proxy_wallet=WALLET,transaction_hash='0x'+tx*64,timestamp=90,token_id='1',condition_id='c',side='BUY',size=10,price=.5,type=kind)
def page(items,cursor=None):return SimpleNamespace(body=dict(data=items,pagination=dict(has_more=bool(cursor),next_cursor=cursor)),observed_at=100,evidence_id='e')
class Fake:
    def __init__(self,responses):self.responses=list(responses);self.calls=[]
    async def request(self,url,params=None,**kwargs):
        self.calls.append((url,dict(params or {})));value=self.responses.pop(0)
        if isinstance(value,Exception):raise value
        return value
class BadCursor(Exception):status=400
class FeedTests(unittest.IsolatedAsyncioTestCase):
    async def test_event_scope_has_own_cursor_and_cache(self):
        from polysentinel.investigation import _wallet_rows
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);cfg={'investigation_history_pages':1}
            await wallet_feed(store,Fake([page([row()],'global-cursor')]),cfg,WALLET,'trades',100)
            net=Fake([page([dict(row('b'),event_id='123')],'event-cursor')])
            result=await wallet_feed(store,net,cfg,WALLET,'trades',100,event_id='123')
            self.assertNotIn('cursor',net.calls[0][1]);self.assertEqual(net.calls[0][1]['event_id'],'123')
            self.assertEqual(store.checkpoint('investigate:'+WALLET+':trades')['cursor'],'global-cursor')
            self.assertEqual(result['event_scope'],'123')
            rows,total=_wallet_rows(store,'trades',WALLET,event_id='123')
            self.assertEqual(total,1);self.assertEqual(rows[0]['row']['event_id'],'123')
            wrong=Fake([page([dict(row('c'),event_id='999')])])
            result=await wallet_feed(store,wrong,cfg,WALLET,'trades',100,event_id='123')
            self.assertEqual(result['status'],'error')
            self.assertEqual(store.checkpoint('investigate:'+WALLET+':trades:event:123')['cursor'],'event-cursor')
            self.assertEqual(store.count('wallet_trades'),2);store.close()

    async def test_resume_filters_atomic_and_dedup(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);config={'investigation_history_pages':1};net=Fake([page([row()],'opaque')])
            first=await wallet_feed(store,net,config,WALLET,'trades',100)
            self.assertEqual(first['status'],'capped');store.close();store=Store(tmp)
            net2=Fake([page([row(),row('b')])]);second=await wallet_feed(store,net2,config,WALLET,'trades',100)
            self.assertEqual(second['status'],'complete');self.assertEqual(net2.calls[0][1]['end'],100)
            self.assertEqual(net2.calls[0][1]['cursor'],'opaque');self.assertEqual(store.count('wallet_trades'),2)
            self.assertEqual(store.checkpoint('investigate:'+WALLET+':trades')['rows'],3);store.close()
    async def test_empty_error_and_corrupt_cursor_distinct(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);config={'investigation_history_pages':1}
            a=await wallet_feed(store,Fake([page([])]),config,WALLET,'activity',100)
            self.assertEqual(a['status'],'empty')
            b=await wallet_feed(store,Fake([RuntimeError('outage')]),config,OTHER,'activity',100)
            self.assertEqual(b['status'],'error')
            await wallet_feed(store,Fake([page([row()],'broken')]),config,WALLET,'trades',100)
            c=await wallet_feed(store,Fake([BadCursor('bad cursor')]),config,WALLET,'trades',100)
            self.assertEqual(c['status'],'error');self.assertIsNone(store.checkpoint('investigate:'+WALLET+':trades')['cursor'])
            d=await wallet_feed(store,Fake([page([row()])]),config,WALLET,'trades',100)
            self.assertEqual(d['status'],'complete');self.assertEqual(store.count('wallet_trades'),1);store.close()
    async def test_wrong_wallet_page_not_committed(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);bad=row();bad['proxy_wallet']=OTHER
            a=await wallet_feed(store,Fake([page([bad])]),{'investigation_history_pages':1},WALLET,'trades',100)
            self.assertEqual(a['status'],'error');self.assertEqual(store.count('wallet_trades'),0)
            self.assertIsNone(store.checkpoint('investigate:'+WALLET+':trades'));store.close()
    async def test_budget_explicit(self):
        net=Budget(Fake([page([])]),{'investigation_max_seconds':30,'investigation_max_requests':1})
        await net.request('https://test.invalid')
        with self.assertRaises(BudgetExceeded):await net.request('https://test.invalid')
class GraphTests(unittest.TestCase):
    def test_shared_infrastructure_never_merges_wallets(self):
        edges=[dict(source=FUNDER,target=w,transaction_hash='a',log_index=i,infrastructure=True) for i,w in enumerate([WALLET,OTHER])]
        g=funding_graph(edges,[WALLET,OTHER],8)
        self.assertEqual(len(g['nodes']),3);self.assertEqual(g['ownership_clusters'],[])
        self.assertFalse(g['shared_counterparties'][0]['coordination_proven'])
    def test_graph_bound_visible(self):
        edges=[dict(source=FUNDER,target=WALLET,transaction_hash='a',log_index=1,infrastructure=False)]
        self.assertEqual(funding_graph(edges,[WALLET],1)['dropped_edges_budget'],1)
    def test_sequence_is_descriptive(self):
        rows=[]
        for i,k in enumerate(['DEPOSIT','TRADE','WITHDRAWAL']):
            v=row(str(i),k);v['timestamp']=i+1;rows.append({'row':v})
        found=activity_sequences(rows)
        self.assertEqual(len(found),1);self.assertIn('non établies',found[0]['interpretation'])

class InvestigationCoverageTests(unittest.IsolatedAsyncioTestCase):
    async def test_uncovered_news_propagates_and_wallet_filter_precedes_cap(self):
        from pathlib import Path
        from polysentinel.investigation import investigate
        from polysentinel.config import load_config
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp)
            config=load_config()
            config['investigation_history_pages']=1
            net=Fake([page([]),page([]),page([])])
            result=await investigate(store,net,config,WALLET)
            self.assertTrue(any(e['stage']=='news:configuration' for e in result['errors']))
            health=store.get('health','investigation:'+WALLET)
            self.assertEqual(health['payload']['status'],'degraded')
            self.assertEqual(result['coverage']['local_trades']['total'],0)
            store.close()


class FreshHeadTests(unittest.IsolatedAsyncioTestCase):
    async def test_recent_rows_collected_while_historical_cursor_stays_pending(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp)
            cfg={'investigation_history_pages':1,'overlap_seconds':5}
            await wallet_feed(store,Fake([page([row()], 'historic-cursor')]),cfg,WALLET,'trades',100)
            fresh=row('f');fresh['timestamp']=190
            old=row('b');old['timestamp']=80
            net=Fake([page([fresh]),page([old],'historic-next')])
            cfg['investigation_history_pages']=2
            result=await wallet_feed(store,net,cfg,WALLET,'trades',200)
            self.assertEqual(net.calls[0][1]['start'],95)
            self.assertEqual(net.calls[0][1]['end'],200)
            self.assertNotIn('cursor',net.calls[0][1])
            self.assertEqual(net.calls[1][1]['cursor'],'historic-cursor')
            self.assertEqual(net.calls[1][1]['end'],100)
            self.assertEqual(store.checkpoint('investigate:'+WALLET+':trades')['cursor'],'historic-next')
            self.assertEqual(store.count('wallet_trades'),3)
            self.assertEqual(result['status'],'capped')
            self.assertEqual(result['recent_head']['status'],'complete')
            self.assertEqual(result['pages_this_run'],2)
            store.close()

    async def test_capped_head_tail_checkpoint_survives_new_head(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);cfg={'investigation_history_pages':1,'overlap_seconds':5}
            await wallet_feed(store,Fake([page([row()], 'old')]),cfg,WALLET,'activity',100)
            newest=row('f');newest['timestamp']=190
            result=await wallet_feed(store,Fake([page([newest], 'recent-tail')]),cfg,WALLET,'activity',200)
            gap_key='investigate:'+WALLET+':activity:gap:95:200'
            self.assertEqual(store.checkpoint(gap_key)['cursor'],'recent-tail')
            self.assertEqual(store.checkpoint('investigate:'+WALLET+':activity')['cursor'],'old')
            next_head=row('c');next_head['timestamp']=290
            gap_row=row('d');gap_row['timestamp']=160
            old_row=row('e');old_row['timestamp']=70
            cfg['investigation_history_pages']=3
            net=Fake([page([next_head]),page([gap_row]),page([old_row],'old-next')])
            result=await wallet_feed(store,net,cfg,WALLET,'activity',300)
            self.assertEqual(net.calls[0][1]['start'],195)
            self.assertEqual(net.calls[1][1]['cursor'],'recent-tail')
            self.assertEqual(net.calls[1][1]['end'],200)
            self.assertEqual(net.calls[2][1]['cursor'],'old')
            self.assertTrue(store.checkpoint(gap_key)['complete'])
            self.assertEqual(result['pending_recent_windows'],0)
            self.assertEqual(result['pages_this_run'],3)
            store.close()

class FreshHeadAtomicityTests(unittest.IsolatedAsyncioTestCase):
    async def test_fresh_rows_head_and_gap_roll_back_together(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);cfg={'investigation_history_pages':1,'overlap_seconds':5}
            await wallet_feed(store,Fake([page([row()], 'old')]),cfg,WALLET,'trades',100)
            original=store.checkpoint
            def interrupt(key,value=None,conn=None):
                if ':gap:' in key and value is not None:raise RuntimeError('synthetic interruption')
                return original(key,value,conn)
            store.checkpoint=interrupt
            fresh=row('f');fresh['timestamp']=190
            with self.assertRaises(RuntimeError):
                await wallet_feed(store,Fake([page([fresh], 'tail')]),cfg,WALLET,'trades',200)
            self.assertEqual(store.count('wallet_trades'),1)
            self.assertIsNone(store.checkpoint('investigate:'+WALLET+':trades:head'))
            self.assertEqual(store.checkpoint('investigate:'+WALLET+':trades')['cursor'],'old')
            store.close()

class TargetTests(unittest.IsolatedAsyncioTestCase):
    async def test_invalid_target_fails_without_network(self):
        from polysentinel.investigation import investigate
        from polysentinel.config import load_config
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);net=Fake([])
            for target in ('0x123','http://localhost/','../secrets','','0'):
                with self.subTest(target=target),self.assertRaises(ValueError):await investigate(store,net,load_config(),target)
            self.assertEqual(net.calls,[]);store.close()
    async def test_event_slug_resolves_to_numeric_id(self):
        from polysentinel.investigation import investigate
        from polysentinel.config import load_config
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp)
            gamma=SimpleNamespace(body={'id':'123','slug':'new-event','title':'New event','markets':[]},status=200,observed_at=100,evidence_id='gamma')
            net=Fake([gamma,SimpleNamespace(body={'data':[]},status=200,observed_at=101,evidence_id='resolution'),page([])])
            result=await investigate(store,net,load_config(),'new-event')
            self.assertEqual(result['event_id'],'123')
            self.assertTrue(net.calls[0][0].endswith('/events/slug/new-event'))
            self.assertEqual(net.calls[1][1]['event_id'],'123')
            self.assertIsNotNone(store.get('event','123'));store.close()

class UnmappedCaseTests(unittest.IsolatedAsyncioTestCase):
    async def test_case_slug_sentinel_resolves_and_keeps_unmapped_local_trade(self):
        from polysentinel.investigation import investigate
        from polysentinel.config import load_config
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp)
            store.put('trade','local',{'id':'local','wallet':WALLET,'timestamp':90,'event_id':'','event_slug':'some-event','nominal':50,'size':100,'price':.5})
            gamma=SimpleNamespace(body={'id':'123','slug':'some-event','title':'Some event','markets':[]},status=200,observed_at=100,evidence_id='gamma')
            net=Fake([gamma,SimpleNamespace(body={'data':[]},observed_at=101,evidence_id='resolution'),page([]),page([]),page([])])
            result=await investigate(store,net,load_config(),{'id':'case-slug','wallet':WALLET,'event_id':'unmapped:some-event','score':2})
            self.assertEqual(result['event_id'],'123')
            self.assertEqual(result['event_mapping']['input'],'unmapped:some-event')
            self.assertTrue(net.calls[0][0].endswith('/events/slug/some-event'))
            self.assertEqual(result['coverage']['local_trades']['total'],1)
            self.assertIsNotNone(store.get('investigation','case-slug'));store.close()
    async def test_condition_sentinel_investigates_wallet_without_fake_slug(self):
        from polysentinel.investigation import investigate
        from polysentinel.config import load_config
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);net=Fake([page([]),page([]),page([])])
            result=await investigate(store,net,load_config(),{'id':'case-condition','wallet':WALLET,'event_id':'unmapped:0x'+'a'*64,'score':3})
            self.assertEqual(result['event_id'],'')
            self.assertEqual(result['event_mapping']['scope'],'wallet_only')
            self.assertTrue(all('/v2/' in url for url,_ in net.calls))
            self.assertTrue(any(e['stage']=='event_mapping' for e in result['errors']))
            self.assertIsNotNone(store.get('investigation','case-condition'));store.close()
    async def test_metadata_failure_does_not_abort_valid_wallet_case(self):
        from polysentinel.investigation import investigate
        from polysentinel.config import load_config
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);net=Fake([RuntimeError('Gamma unavailable'),page([]),page([]),page([])])
            result=await investigate(store,net,load_config(),{'id':'case-unavailable','wallet':WALLET,'event_id':'unmapped:some-event','score':2})
            self.assertEqual(len(result['histories']),3)
            self.assertEqual(result['event_mapping']['status'],'unknown')
            self.assertTrue(any('Gamma unavailable' in e['error'] for e in result['errors']))
            self.assertIsNotNone(store.get('investigation','case-unavailable'));store.close()


class IndexedLocalTradeTests(unittest.TestCase):
    def test_wallet_event_filters_count_order_and_cap_equal_legacy(self):
        import json
        import zlib
        from polysentinel.investigation import _local_trades
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp)
            try:
                # Canonical numeric event ID and unresolved event slug both match.
                selected=[('a',WALLET,123,''),('b',WALLET.upper(),'','event-slug'),
                          ('c',WALLET,'123',''),('different-event',WALLET,'999','other')]
                selected += [(f'unrelated-{i}',OTHER,'123','event-slug') for i in range(80)]
                for i,(key,wallet,event_id,slug) in enumerate(selected):
                    store.put('trade',key,dict(id=key,wallet=wallet,timestamp=90+i,
                        event_id=event_id,event_slug=slug),observed_at=100+i)
                legacy_where="kind='trade' AND (CAST(json_extract(payload,'$.event_id') AS TEXT)=? OR json_extract(payload,'$.event_slug')=?) AND lower(json_extract(payload,'$.wallet'))=?"
                params=('123','event-slug',WALLET)
                expected_total=store.conn.execute('SELECT COUNT(*) FROM objects WHERE '+legacy_where,params).fetchone()[0]
                expected=[json.loads(r['payload']) for r in store.conn.execute(
                    'SELECT payload FROM objects WHERE '+legacy_where+' ORDER BY observed_at DESC LIMIT 2',params)]
                seen=[]
                def decode(body):
                    raw=zlib.decompress(body).decode();seen.append(json.loads(raw)['id']);return raw
                store.conn.create_function('payload_text',1,decode,deterministic=True)
                rows,total=_local_trades(store,WALLET.upper(),'123','event-slug',limit=2)
                self.assertEqual((rows,total),(expected,expected_total))
                self.assertEqual(total,3)
                self.assertEqual([p['id'] for p in rows],['c','b'])
                self.assertFalse(any(key.startswith('unrelated-') for key in seen))
                rows,total=_local_trades(store,WALLET,'','',limit=2)
                self.assertEqual(total,4)
                self.assertEqual([p['id'] for p in rows],['different-event','c'])
                rows,total=_local_trades(store,FUNDER,'123','event-slug')
                self.assertEqual((rows,total),([],0))
                rows,total=_local_trades(store,'','123','event-slug',limit=2)
                self.assertEqual(total,83)
                self.assertEqual([p['id'] for p in rows],['unrelated-79','unrelated-78'])
            finally:store.close()
