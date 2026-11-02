"""Synthetic catalogue size checks; temporary databases, no network."""
from copy import deepcopy
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
import httpx

from polysentinel import collect
from polysentinel import net as netmod
from polysentinel.db import Store

PARAMS=dict(closed='false',limit=50,version='v2',order='createdAt',ascending='true')
KEY='catalog:sweep:v2'
def too_large(status=200):return netmod.ResponseTooLarge('Réponse tronquée: plafond octets atteint',status=status)
def page(start,size,total=30):
    end=min(start+size,total)
    return netmod.Response(dict(events=[dict(id=str(i),title='Event '+str(i),markets=[]) for i in range(start,end)],
        next_cursor='opaque:'+str(end) if end<total else None),200,1800000000,'synthetic',{})
class Fake:
    def __init__(self,handler):self.calls=[];self.handler=handler
    async def request(self,url,params):
        self.calls.append(deepcopy(params));return self.handler(params,len(self.calls))

class CandidateTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Store(self.tmp.name)
        self.initial=dict(cursor='opaque:0',params=PARAMS,rows=0,complete=False)
        self.store.checkpoint(KEY,self.initial)
    def tearDown(self):self.store.close();self.tmp.cleanup()
    def collector(self,handler):
        return collect.Collector(self.store,Fake(handler),{'priority_tags':[]})
    async def test_smaller_success_atomic_resume_and_no_missing_rows(self):
        def handler(p,n):
            if p['limit']>12:raise too_large()
            return page(int(p['after_cursor'].split(':')[1]),p['limit'])
        c=self.collector(handler);first=await c._catalog_page(PARAMS,KEY,True)
        self.assertEqual([p['limit'] for p in c.net.calls],[50,25,12])
        self.assertTrue(all(p['after_cursor']=='opaque:0' for p in c.net.calls))
        self.assertEqual(first['size_reductions'],2)
        self.assertEqual(self.store.checkpoint(KEY)['page_limit'],12)
        self.store.close();self.store=Store(self.tmp.name);c=self.collector(handler)
        await c._catalog_page(PARAMS,KEY,True);await c._catalog_page(PARAMS,KEY,True)
        self.assertEqual([p['limit'] for p in c.net.calls],[12,12])
        self.assertEqual({r['key'] for r in self.store.list('event')},{str(i) for i in range(30)})
        self.assertTrue(self.store.checkpoint(KEY)['complete'])
        for p in c.net.calls:
            self.assertEqual({k:v for k,v in p.items() if k not in ('limit','after_cursor')},
                             {k:v for k,v in PARAMS.items() if k!='limit'})
    async def test_size_one_failure_preserves_cursor_and_does_not_skip(self):
        def handler(p,n):raise too_large()
        c=self.collector(handler)
        with self.assertRaises(netmod.ResponseTooLarge):await c._catalog_page(PARAMS,KEY,True)
        self.assertEqual([p['limit'] for p in c.net.calls],[50,25,12,6,3,1])
        self.assertTrue(all(p['after_cursor']=='opaque:0' for p in c.net.calls))
        self.assertEqual(self.store.checkpoint(KEY),self.initial)
        self.assertEqual(self.store.count('event'),0);self.assertEqual(self.store.count('gap'),0)
    async def test_rejected_resized_cursor_does_not_restart_from_head(self):
        def handler(p,n):
            if n==1:raise too_large()
            raise netmod.SourceError('Cursor rejected',422)
        c=self.collector(handler)
        with self.assertRaises(netmod.SourceError):await c._catalog_page(PARAMS,KEY,True)
        self.assertEqual(len(c.net.calls),2);self.assertEqual(self.store.checkpoint(KEY),self.initial)
        self.assertEqual(self.store.count('gap'),0)
    async def test_atomic_failure_rolls_back_rows_size_and_cursor(self):
        def handler(p,n):
            if n==1:raise too_large()
            return page(0,2)
        c=self.collector(handler);original=self.store.put
        def interrupted(kind,key,*args,**kwargs):
            if kind=='event' and key=='1':raise RuntimeError('Synthetic interruption')
            return original(kind,key,*args,**kwargs)
        with patch.object(self.store,'put',side_effect=interrupted):
            with self.assertRaises(RuntimeError):await c._catalog_page(PARAMS,KEY,True)
        self.assertEqual(self.store.checkpoint(KEY),self.initial);self.assertEqual(self.store.count('event'),0)
    async def test_unrelated_http_error_is_not_resized(self):
        def handler(p,n):raise too_large(status=503)
        c=self.collector(handler)
        with self.assertRaises(netmod.SourceError):await c._catalog_page(PARAMS,KEY,True)
        self.assertEqual(len(c.net.calls),1);self.assertEqual(self.store.checkpoint(KEY),self.initial)
    async def test_malformed_page_after_reduction_not_committed(self):
        def handler(p,n):
            if n==1:raise too_large()
            return netmod.Response({},200,1800000000,'bad-schema',{})
        c=self.collector(handler)
        with self.assertRaises(netmod.SourceError):await c._catalog_page(PARAMS,KEY,True)
        self.assertEqual(self.store.checkpoint(KEY),self.initial)
    async def test_real_byte_guard_and_request_budget_unchanged(self):
        cfg=dict(request_attempts=1,requests_per_cycle=1,response_max_bytes=8000000,min_free_bytes=0,data_quota_bytes=1000000000)
        async with netmod.Net(self.store,cfg) as network:
            await network._client.aclose()
            network._client=httpx.AsyncClient(transport=httpx.MockTransport(
                lambda request:httpx.Response(200,content=b'x'*8000001,headers={'Content-Type':'application/json'})))
            network._public_url=AsyncMock(return_value='gamma-api.polymarket.com')
            c=collect.Collector(self.store,network,{})
            with self.assertRaisesRegex(netmod.SourceError,'Budget de requêtes'):await c._catalog_page(PARAMS,KEY,True)
            self.assertEqual(network.requests_used,1)
            self.assertEqual(self.store.checkpoint(KEY),self.initial)
            self.assertEqual(self.store.count('event'),0)
            error=self.store.get('health','http:gamma-api.polymarket.com')['payload']
            self.assertEqual(error['detail'],'Réponse tronquée: plafond octets atteint')

if __name__=='__main__':unittest.main()
