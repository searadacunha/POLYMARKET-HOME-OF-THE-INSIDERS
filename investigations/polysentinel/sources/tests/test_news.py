import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from polysentinel.db import Store
from polysentinel.news import parse_feed, collect_news, relevant
ROOT=Path(__file__).resolve().parents[1]
SOURCE={'name':'Official','url':'https://www.federalreserve.gov/feeds/press_all.xml','allowed_hosts':['www.federalreserve.gov']}
XML='''<rss><channel><item><title>Federal Reserve interest rate decision</title><link>https://www.federalreserve.gov/release</link><pubDate>Tue, 27 Oct 2026 10:00:00 GMT</pubDate><description>Public statement &lt;script&gt;run()&lt;/script&gt; data only</description></item></channel></rss>'''
class NewsTests(unittest.TestCase):
    def test_dates_source_claims_and_no_execution(self):
        entry=parse_feed(XML,SOURCE,2_000_000_000)['items'][0]
        self.assertNotEqual(entry['publication_claimed_at'],entry['first_observed_at'])
        self.assertNotIn('run()',entry['content'])
        self.assertEqual(entry['proof_level'],'affirmation d’une source')
        self.assertTrue(relevant(entry,{'title':'Federal Reserve interest rate decision'}))
    def test_untrusted_urls_and_entities(self):
        parsed=parse_feed(XML.replace('https://www.federalreserve.gov/release','http://127.0.0.1/secret'),SOURCE,10)
        self.assertEqual(parsed['items'],[])
        self.assertEqual(parsed['dropped_links'],1)
        with self.assertRaises(ValueError):parse_feed('<!DOCTYPE x><rss/>',SOURCE,10)
class Fake:
    async def request(self,url):return SimpleNamespace(body=XML,observed_at=1_793_109_000,evidence_id='evidence')
class MilestoneTests(unittest.IsolatedAsyncioTestCase):
    def test_public_information_before_resolution_is_not_prepublic_activity(self):
        from polysentinel.news import public_timing
        event={'observed_at':160,'payload':dict(verified=True,result_available=True,
            milestone_type='public_information',public_at=150,source_url='https://example.org/statement',evidence_id='announcement')}
        self.assertEqual(public_timing(event,170,180)['status'],'after_public_information')
        self.assertEqual(public_timing(event,140,180)['status'],'before_verified_public_information')
        self.assertEqual(public_timing(event,140,155)['status'],'unknown')
        resolution={'observed_at':200,'payload':dict(event['payload'],public_at=200,
            milestone_type='official_resolution',source_url='https://data-api.polymarket.com/v2/resolutions')}
        result=public_timing(resolution,170,210)
        self.assertEqual(result['status'],'resolution_only');self.assertIsNone(result['first_public_at'])

    async def test_legacy_resolution_is_not_reported_as_first_public_information(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp)
            store.put('public_milestone','event',dict(verified=True,result_available=True,
                source_url='https://data-api.polymarket.com/v2/resolutions',evidence_id='r',public_at=100),observed_at=100)
            result=await collect_news(store,Fake(),{'root':str(ROOT)},{'id':'event'})
            self.assertFalse(result['public_result']);self.assertTrue(result['official_resolution_known'])
            store.close()

    async def test_article_not_result_and_future_milestone_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);event={'id':'event','title':'Federal Reserve interest rate decision','tags':['fed']}
            first=await collect_news(store,Fake(),{'root':str(ROOT)},event)
            self.assertFalse(first['public_result'])
            store.put('public_milestone','event',dict(verified=True,result_available=True,source_url='https://www.federalreserve.gov/release',evidence_id='x',public_at=9_999_999_999))
            second=await collect_news(store,Fake(),{'root':str(ROOT)},event)
            self.assertFalse(second['public_result'])
            self.assertEqual(second['availability'],'première disponibilité publique inconnue')
            store.close()


class ResolutionTests(unittest.IsolatedAsyncioTestCase):
    async def test_one_resolved_sibling_does_not_end_event(self):
        from polysentinel.news import resolution_state
        class ResolutionFake:
            def __init__(self,all_resolved):self.all_resolved=all_resolved
            async def request(self,url,params=None):
                data=[{'condition_id':'a','status':'resolved'},{'condition_id':'b','status':'resolved' if self.all_resolved else 'active'}]
                return SimpleNamespace(body={'data':data},observed_at=100,evidence_id='resolution')
        with tempfile.TemporaryDirectory() as tmp:
            store=Store(tmp);event={'id':'123','raw':{}}
            for cid in ('a','b'):store.put('market',cid,{'id':cid,'event_id':'123','condition_id':cid})
            a=await resolution_state(store,ResolutionFake(False),event)
            self.assertFalse(a['all_known_conditions_resolved'])
            self.assertIsNone(store.get('public_milestone','123'))
            condition=store.get('public_condition','a')['payload']
            self.assertTrue(condition['verified'])
            self.assertTrue(condition['result_available'])
            b=await resolution_state(store,ResolutionFake(True),event)
            self.assertTrue(b['all_known_conditions_resolved'])
            self.assertEqual(store.get('public_milestone','123')['payload']['public_at'],100)
            store.put('public_milestone','123',dict(milestone_type='public_information',
                verified=True,result_available=True,public_at=50,evidence_id='announcement',
                source_url='https://example.org/statement'),observed_at=60)
            await resolution_state(store,ResolutionFake(True),event)
            self.assertEqual(store.get('public_milestone','123')['payload']['evidence_id'],'announcement')
            store.close()

class FeedCapTests(unittest.TestCase):
    def test_feed_truncation_counted(self):
        item='<item><title>Fed rate decision</title><link>https://www.federalreserve.gov/release</link></item>'
        parsed=parse_feed('<rss><channel>'+item*57+'</channel></rss>',SOURCE,10)
        self.assertEqual(parsed['total_entries'],57)
        self.assertEqual(parsed['processed_entries'],50)
        self.assertEqual(parsed['remaining_entries'],7)
        self.assertTrue(parsed['truncated'])
