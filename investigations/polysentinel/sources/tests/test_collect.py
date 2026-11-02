"""Synthetic transport fixtures, separate from the real evidence database."""
from copy import deepcopy
import tempfile
import unittest
from unittest.mock import AsyncMock, patch
import httpx
from polysentinel.collect import Collector, normalize_market
from polysentinel.db import Store
from polysentinel.net import Net, Response, SourceError
NOW=1800000000
WALLET='0x'+'a'*40
CONDITION='0x'+'b'*64
TX='0x'+'c'*64

def trade(ts=NOW-10,tx=TX):
    return dict(proxy_wallet=WALLET,transaction_hash=tx,condition_id=CONDITION,token_id='123456',side='BUY',
                size=100,price=.25,timestamp=ts,outcome='Arbitrary label',event_slug='event-test',slug='market-test')
def page(rows,cursor=None):
    return dict(data=rows,pagination=dict(next_cursor=cursor,has_more=bool(cursor),limit=2,offset=0))
def state(cursor=None):
    return {'active':dict(cursor=cursor,cutoff=NOW-100,counts={},count_timestamp=None)}
class FakeNet:
    def __init__(self,replies):self.replies=list(replies);self.calls=[]
    async def request(self,url,params=None,**kwargs):
        self.calls.append((url,deepcopy(params)));reply=self.replies.pop(0)
        if isinstance(reply,Exception):raise reply
        return Response(reply,200,NOW,'synthetic-response',{})
class CollectorTests(unittest.IsolatedAsyncioTestCase):
    async def test_dormant_market_second_head_does_not_expand_initial_window(self):
        old=trade(NOW-30*86400)
        c=Collector(self.store,FakeNet([page([old]),page([old])]),self.cfg)
        with patch('polysentinel.collect.time.time',return_value=NOW):
            first=await c._trade_stream('dormant',{},1,({},{}))
        with patch('polysentinel.collect.time.time',return_value=NOW+60):
            second=await c._trade_stream('dormant',{},1,({},{}))
        self.assertEqual(first['outside_window'],1);self.assertEqual(second['outside_window'],1)
        self.assertEqual(second['cutoff'],first['cutoff']);self.assertEqual(self.store.count('trade'),0)

    async def test_old_rows_stay_in_raw_evidence_without_filling_analysis_window(self):
        c=Collector(self.store,FakeNet([page([trade(),trade(NOW-200,tx='0x'+'d'*64)])]),self.cfg);s=state()
        result=await c._walk_trades('test',{},s,s['active'],1,({},{}))
        self.assertEqual(result['rows'],2);self.assertEqual(result['matched_rows'],1)
        self.assertEqual(result['outside_window'],1);self.assertEqual(self.store.count('trade'),1)
        self.assertTrue(s['active']['done']);self.assertEqual(s['active']['oldest'],NOW-200)

    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
        self.cfg={'priority_tags':['awards'],'initial_lookback_seconds':3600,'overlap_seconds':180,'trade_pages':2}
    def tearDown(self):self.store.close();self.tmp.cleanup()
    async def test_pages_preserve_filters_and_identical_multiplicity(self):
        net=FakeNet([page([trade()],'opaque'),page([trade()])]);c=Collector(self.store,net,self.cfg);s=state()
        result=await c._walk_trades('test',{'condition':CONDITION,'taker_only':'true'},s,s['active'],2,({},{}))
        self.assertEqual(result['inserted'],2)
        self.assertEqual(net.calls[1][1],dict(condition=CONDITION,taker_only='true',cursor='opaque'))
        self.assertEqual({r['payload']['occurrence'] for r in self.store.list('trade')},{1,2})
    async def test_interruption_resume(self):
        c=Collector(self.store,FakeNet([page([trade()],'opaque'),SourceError('offline')]),self.cfg);s=state()
        with self.assertRaises(SourceError):await c._walk_trades('test',{},s,s['active'],2,({},{}))
        saved=self.store.checkpoint('test');self.assertEqual(saved['active']['cursor'],'opaque');self.assertEqual(self.store.count('trade'),1)
        c.net=FakeNet([page([trade(NOW-20,tx='0x'+'d'*64)])]);await c._walk_trades('test',{},saved,saved['active'],1,({},{}))
        self.assertEqual(self.store.count('trade'),2)
    async def test_insert_failure_rolls_back_checkpoint(self):
        c=Collector(self.store,FakeNet([page([trade()],'opaque')]),self.cfg);s=state();self.store.checkpoint('test',s)
        with patch.object(self.store,'put',side_effect=RuntimeError('disk failure')):
            with self.assertRaises(RuntimeError):await c._walk_trades('test',{},s,s['active'],1,({},{}))
        self.assertEqual(self.store.count('trade'),0);self.assertIsNone(self.store.checkpoint('test')['active']['cursor'])
    async def test_empty_capped_and_error_distinct(self):
        for name,replies,expected in [('empty',[page([])],'empty'),('capped',[page([trade()],'a'),page([trade(NOW-20)],'b')],'capped')]:
            c=Collector(self.store,FakeNet(replies),self.cfg)
            with patch('polysentinel.collect.time.time',return_value=NOW):result=await c._trade_stream(name,{},1,({},{}))
            self.assertEqual(result['status'],expected)
        c=Collector(self.store,FakeNet([SourceError('failed',503)]),self.cfg)
        with self.assertRaises(SourceError):await c._trade_stream('error',{},1,({},{}))
        self.assertIsNone(self.store.checkpoint('error').get('last_success'))
    async def test_crash_after_final_page_commit_does_not_replay_done_walk(self):
        c=Collector(self.store,FakeNet([page([trade(NOW-20)])]),self.cfg);s=state()
        await c._walk_trades('test',{},s,s['active'],1,({},{}))
        self.assertTrue(self.store.checkpoint('test')['active']['done'])
        c.net=FakeNet([page([trade(NOW-10,tx='0x'+'d'*64)])])
        result=await c._trade_stream('test',{},1,({},{}))
        self.assertEqual(result['inserted'],1);self.assertEqual(self.store.count('trade'),2)
        self.assertEqual(len(c.net.calls),1);self.assertEqual(self.store.checkpoint('test')['pending'],[])
        self.assertEqual(self.store.checkpoint('test')['watermark'],NOW-10)
    async def test_changed_filters_keep_old_pending_cursor_scope(self):
        old={'filter_type':'CASH','filter_amount':1000};new={'filter_type':'CASH','filter_amount':2000}
        walk=dict(cursor='opaque-old',cutoff=NOW-500,counts={},count_timestamp=NOW-100,done=False)
        self.store.checkpoint('test',dict(params=old,watermark=NOW-100,pending=[walk]))
        c=Collector(self.store,FakeNet([page([trade()]),page([trade(NOW-120)])]),self.cfg)
        await c._trade_stream('test',new,1,({},{}))
        self.assertEqual(c.net.calls[0][1],new)
        self.assertEqual(c.net.calls[1][1],dict(old,cursor='opaque-old'))
        self.assertEqual(self.store.count('gap'),1)
    async def test_bad_cursor_recovery(self):
        net=FakeNet([SourceError('invalid cursor',400),page([trade()])]);c=Collector(self.store,net,self.cfg);s=state('bad')
        result=await c._walk_trades('test',{'condition':CONDITION},s,s['active'],1,({},{}))
        self.assertTrue(result['recovered']);self.assertEqual(self.store.count('gap'),1);self.assertEqual(net.calls[1][1],{'condition':CONDITION})
    async def test_duplicate_first_observation_immutable(self):
        c=Collector(self.store,FakeNet([page([trade()]),page([trade()])]),self.cfg)
        for _ in range(2):
            s=state();await c._walk_trades('test',{},s,s['active'],1,({},{}))
        self.assertEqual(self.store.count('trade'),1);self.assertEqual(self.store.list('trade')[0]['payload']['observed_at'],NOW)
        self.assertEqual(self.store.conn.execute("SELECT count(*) FROM history WHERE kind='trade'").fetchone()[0],1)
    async def test_bad_schema_does_not_advance(self):
        for body in [dict(data=[trade()],pagination={'has_more':True,'next_cursor':None})]:
            c=Collector(self.store,FakeNet([body]),self.cfg);s=state()
            with self.assertRaises(SourceError):await c._walk_trades('test',{},s,s['active'],1,({},{}))
            self.assertIsNone(self.store.checkpoint('test'))
    async def test_malformed_trade_quarantine_and_checkpoint(self):
        c=Collector(self.store,FakeNet([page([dict(trade(),side='WRONG')])]),self.cfg);s=state()
        result=await c._walk_trades('test',{},s,s['active'],1,({},{}))
        self.assertEqual(result['rejected'],1);self.assertEqual(self.store.count('rejected_trade'),1)
        self.assertEqual(self.store.count('trade'),0);self.assertTrue(self.store.checkpoint('test')['active']['done'])
    async def test_gamma_both_versions_and_tag_rotation(self):
        self.cfg.update(catalog_pages=2,catalog_page_size=10,priority_tags=['awards','earnings'])
        net=FakeNet([{'events':[]} for _ in range(12)]);c=Collector(self.store,net,self.cfg)
        await c.catalog();await c.catalog()
        self.assertEqual({p['version'] for _,p in net.calls},{'v1','v2'})
        self.assertEqual({p['tag_slug'] for _,p in net.calls if 'tag_slug' in p},{'awards','earnings'})
    async def test_gamma_resume(self):
        c=Collector(self.store,FakeNet([{'events':[],'next_cursor':'next'}]),self.cfg)
        await c._catalog_page({'closed':'false','version':'v2'},'gamma',True)
        c.net=FakeNet([{'events':[],'next_cursor':None}]);await c._catalog_page({'closed':'false','version':'v2'},'gamma',True)
        self.assertEqual(c.net.calls[0][1]['after_cursor'],'next')
    def test_explicit_token_labels(self):
        e=dict(id='1',end_date=None,priority=True)
        m=normalize_market(dict(id='2',clobTokenIds='["123","124"]',outcomes='["Alice","Bob"]'),e,NOW)
        self.assertEqual(m['tokens'][0],dict(token_id='123',outcome='Alice'))
        self.assertEqual(normalize_market(dict(id='2',clobTokenIds='["123"]',outcomes='[]'),e,NOW)['mapping_quality'],'unavailable')
    def test_fair_rotation(self):
        for i in range(12):self.store.put('market',str(i),dict(id=str(i),event_id='1',condition_id='0x'+f'{i:064x}',active=True,closed=False,priority=i<8,tokens=[{'token_id':'1','outcome':'A'}]))
        c=Collector(self.store,FakeNet([]),dict(self.cfg,market_batches=1,markets_per_batch=4));first=c._fair_markets()
        for m in first:self.store.put('market_coverage',m['id'],{'status':'ok'})
        self.assertTrue({m['id'] for m in c._fair_markets()}-{m['id'] for m in first})
class NetTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
    def tearDown(self):self.store.close();self.tmp.cleanup()
    async def test_retry_and_evidence(self):
        calls=[]
        def handler(r):
            calls.append(r)
            return httpx.Response(429,headers={'Retry-After':'0'},json={'error':'busy'}) if len(calls)==1 else httpx.Response(200,json={'data':[]})
        async with Net(self.store,dict(request_attempts=2,requests_per_cycle=3)) as net:
            await net._client.aclose();net._client=httpx.AsyncClient(transport=httpx.MockTransport(handler));net._public_url=AsyncMock(return_value='api.example.com')
            self.assertEqual((await net.request('https://api.example.com/test')).body,{'data':[]});self.assertEqual(net.requests_used,2)
            self.assertEqual(self.store.conn.execute('SELECT count(*) FROM responses').fetchone()[0],2)
            h=self.store.get('health','http:api.example.com')['payload']
            self.assertEqual((h['responses_total'],h['rate_limited_total'],h['empty_responses_total']),(2,1,1))
    async def test_budget_rss_and_readonly_guard(self):
        async with Net(self.store,dict(request_attempts=1,requests_per_cycle=1)) as net:
            await net._client.aclose();net._client=httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,text='<rss/>',headers={'Content-Type':'application/rss+xml'})));net._public_url=AsyncMock(return_value='api.example.com')
            self.assertEqual((await net.request('https://api.example.com/rss')).body,'<rss/>')
            with self.assertRaises(SourceError):await net.request('https://api.example.com/rss')
            with self.assertRaises(SourceError):await net.request('https://api.example.com',method='POST',json_body={'method':'eth_sendRawTransaction'})
    async def test_size_ceiling(self):
        async with Net(self.store,dict(response_max_bytes=4,request_attempts=1)) as net:
            await net._client.aclose();net._client=httpx.AsyncClient(transport=httpx.MockTransport(lambda r:httpx.Response(200,text='too large')));net._public_url=AsyncMock(return_value='api.example.com')
            with self.assertRaisesRegex(SourceError,'plafond'):await net.request('https://api.example.com/test')
            self.assertEqual(self.store.list('health')[0]['payload']['status'],'error')
    async def test_dns_failure_preserves_cumulative_and_last_success(self):
        self.store.health('http:api.example.com','ok','previous',requests_total=12,responses_total=11,last_success=NOW)
        async with Net(self.store,{}) as net:
            net._public_url=AsyncMock(side_effect=OSError('DNS offline'))
            with self.assertRaises(SourceError):await net.request('https://api.example.com/test')
        h=self.store.get('health','http:api.example.com')['payload']
        self.assertEqual(h['requests_total'],12);self.assertEqual(h['responses_total'],11)
        self.assertEqual(h['last_success'],NOW);self.assertEqual(h['dns_errors_total'],1)
    async def test_disk_guard(self):
        async with Net(self.store,dict(min_free_bytes=10**30)) as net:
            net._public_url=AsyncMock(return_value='api.example.com')
            with self.assertRaisesRegex(SourceError,'disque'):await net.request('https://api.example.com/test')
            self.assertEqual(net.requests_used,0)
if __name__=='__main__':unittest.main()
