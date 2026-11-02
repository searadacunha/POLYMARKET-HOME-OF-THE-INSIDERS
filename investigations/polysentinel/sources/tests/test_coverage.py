"""Synthetic coverage checks, separate from live observations."""
import json
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zlib

from polysentinel.collect import Collector
from polysentinel.coverage import measure_coverage
from polysentinel.db import Store

NOW = 1800000000
WALLET = '0x' + 'a' * 40


class CoverageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(self.tmp.name)

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def market(self, key, **extra):
        market = dict(id=key, event_id='event', active=True, closed=False,
                      condition_id='0x' + str(key).zfill(64), tokens=[{'token_id': '123'}])
        market.update(extra)
        self.store.put('market', key, market, NOW)
        return market

    def collected(self, key, status='ok', at=NOW - 10, pending=None, **extra):
        metrics = dict(status=status, last_success=at, pending_walks=len(pending or []), rejected=0)
        metrics.update(extra)
        self.store.put('market_coverage', key, metrics, at)
        self.store.checkpoint('trades:market:' + key, dict(last_success=at, pending=pending or [],
                              params={'condition': '0x' + str(key).zfill(64)}, watermark=None))
        self.store.conn.execute('UPDATE checkpoints SET updated_at=? WHERE key=?', (at, 'trades:market:' + key))
        self.store.conn.commit()

    def test_wallet_and_health_alone_are_not_market_interrogations(self):
        self.market('1'); self.market('2')
        self.store.checkpoint('investigate:' + WALLET + ':trades', {'complete': True, 'updated_at': NOW})
        self.store.checkpoint('investigate:' + WALLET + ':trades:fairness', {'turn': 1})
        self.store.checkpoint('catalog:tag_rotation', {'index': 1})
        self.store.health('trades:market:2', 'error', 'no saved attempt checkpoint')
        self.collected('1')
        report = measure_coverage(self.store, NOW, True)
        self.assertEqual(report['counts']['individually_interrogated'], 1)
        self.assertEqual(report['counts']['never_attempted'], 1)
        self.assertEqual(report['stream_scope_counts'], {'wallet': 1, 'market': 2})
        self.assertEqual([s['stream'] for s in report['streams'] if s['scope'] == 'wallet'],
                         ['investigate:' + WALLET + ':trades'])
        compact = measure_coverage(self.store, NOW)
        wallet_flow = next(s for s in report['streams'] if s['scope'] == 'wallet')
        self.assertIsNone(wallet_flow['ingested_trades'])
        self.assertNotIn('streams', compact)
        self.assertNotIn('stream_scope_counts', compact)
        self.assertLess(len(json.dumps(compact)), 4000)

    def test_global_and_individual_overlap_is_not_double_counted(self):
        from polysentinel.provenance import record_sources
        market=self.market('1')
        trade=dict(id='fill',wallet=WALLET,timestamp=NOW-1,condition_id=market['condition_id'])
        self.store.put('trade','fill',trade,NOW)
        with self.store.transaction() as cx:
            record_sources(self.store,[trade],{},'global',NOW,cx)
            record_sources(self.store,[trade],{'condition':market['condition_id']},'market',NOW,cx)
        report=measure_coverage(self.store,max(NOW, __import__('time').time())+1)
        self.assertEqual(report['source_presence']['eligible_with_trades'],{'both':1})
        self.assertEqual(report['counts']['individually_interrogated'],0)
        self.assertEqual(report['source_presence']['history_complete_certified'],0)

    def test_valid_empty_and_old_trade_are_not_failed_or_stale_collections(self):
        for key in ('1', '2', '3', '4'):
            self.market(key)
        self.collected('1', 'empty')
        self.collected('2', lag_seconds=86400)
        self.collected('3', 'error', last_attempt=NOW - 5)
        self.collected('4', at=NOW - 601)
        self.store.put('trade', 'old-trade', dict(wallet=WALLET, timestamp=NOW - 86400,
                       condition_id='0x' + '2'.zfill(64), __trade__=True), NOW - 10)
        report = measure_coverage(self.store, NOW, True)
        self.assertEqual(report['counts']['collection_recent_complete'], 2)
        self.assertEqual(report['counts']['error'], 1)
        self.assertEqual(report['counts']['stale'], 1)
        flow = next(s for s in report['streams'] if s['stream'] == 'trades:market:2')
        self.assertEqual(flow['collection_age_seconds'], 10)
        self.assertEqual(flow['latest_ingested_trade_age_seconds'], 86400)
        self.assertEqual(report['counts']['with_ingested_trades'], 1)

    def test_backlogs_rejections_and_latest_error_never_count_complete(self):
        for key in ('1', '2', '3', '4', '5'):
            self.market(key)
        walk = {'cursor': 'next', 'done': False, 'cutoff': NOW - 500,
                'oldest': NOW - 100, 'newest': NOW - 10, 'params': {'filter_amount': 123},
                'cache_age': '17', 'recovered': True}
        self.collected('1', 'capped', pending=[walk])
        self.collected('2', rejected=1)
        self.collected('3')
        self.store.put('health', 'trades:market:3', {'status': 'error', 'detail': 'offline'}, NOW - 1)
        self.collected('4')
        cp = self.store.checkpoint('trades:market:4')
        cp['active'] = dict(walk, done=True, cursor=None)
        self.store.checkpoint('trades:market:4', cp)
        self.store.put('market_coverage', '5', {'status': 'ok'}, NOW)
        report = measure_coverage(self.store, NOW, True)
        self.assertEqual(report['counts']['collection_recent_complete'], 0)
        self.assertEqual(report['counts']['backlogged'], 1)
        self.assertEqual(report['counts']['error'], 2)
        self.assertEqual(report['counts']['incomplete_unknown'], 2)
        flow = next(s for s in report['streams'] if s['stream'] == 'trades:market:1')
        self.assertEqual(flow['walks'][0]['params'], {'filter_amount': 123})
        self.assertTrue(flow['recovered'])
        self.assertEqual(flow['walks'][0]['cache_age'], '17')

    def test_eligibility_matches_collector_and_exclusion_reasons_partition(self):
        for key, values in [('1', {}), ('2', {'closed': True}), ('3', {'active': None}),
                            ('4', {'condition_id': ''}), ('5', {'tokens': []}), ('6', {}),
                            ('7', {'closed': None}), ('8', {'active': False, 'tokens': []}),
                            ('9', {'active': 1, 'closed': 0}), ('10', {})]:
            market = self.market(key, **values)
            if key in ('6', '10'):
                self.store.put('public_condition', market['condition_id'],
                               {'verified': key == '6', 'result_available': True}, NOW)
        report = measure_coverage(self.store, NOW, True)
        with patch('polysentinel.collect.time.time',return_value=NOW):
            selected = Collector(self.store, None, {'market_batches': 10, 'markets_per_batch': 10})._fair_markets()
        self.assertEqual({m['id'] for m in selected}, {m['market_id'] for m in report['market_rows'] if m['eligible']})
        self.assertEqual(report['counts']['eligible'], 3)
        self.assertEqual(sum(report['excluded_reasons'].values()), report['counts']['excluded'])
        statuses = ('collection_recent_complete', 'stale', 'error', 'backlogged', 'never_attempted', 'incomplete_unknown')
        self.assertEqual(sum(report['counts'][s] for s in statuses), report['counts']['eligible'])

    def test_ingested_trades_do_not_imply_individual_collection_and_use_v2_index(self):
        market = self.market('1')
        self.store.put('trade', 'global', dict(wallet=WALLET, timestamp=NOW - 1,
                       condition_id=market['condition_id'], __trade__=True), NOW)
        def decode_without_trade(body):
            text = zlib.decompress(body).decode()
            if '__trade__' in text:
                raise AssertionError('coverage decompressed a trade instead of reading trade_index')
            return text
        self.store.conn.create_function('payload_text', 1, decode_without_trade, deterministic=True)
        counts = measure_coverage(self.store, NOW)['counts']
        self.assertEqual(counts['with_ingested_trades'], 1)
        self.assertEqual(counts['individually_interrogated'], 0)
        self.assertEqual(counts['never_attempted'], 1)

    def test_v1_read_only_connection_supported_without_creating_store(self):
        market = self.market('1')
        self.collected('1', at=NOW - 600)
        self.store.put('trade', 'legacy', dict(wallet=WALLET, timestamp=NOW - 999,
                       condition_id=market['condition_id']), NOW)
        legacy = sqlite3.connect(':memory:')
        try:
            legacy.executescript('CREATE TABLE objects(kind,key,payload,first_seen,observed_at); '
                                 'CREATE TABLE checkpoints(key,value,updated_at);')
            legacy.executemany('INSERT INTO objects VALUES(?,?,?,?,?)', self.store.conn.execute('SELECT * FROM objects'))
            legacy.executemany('INSERT INTO checkpoints VALUES(?,?,?)', self.store.conn.execute('SELECT * FROM checkpoints'))
            legacy.commit()
            legacy.execute('PRAGMA query_only=ON')
            self.assertEqual(measure_coverage(SimpleNamespace(conn=legacy), NOW), measure_coverage(self.store, NOW))
            self.assertEqual(measure_coverage(SimpleNamespace(conn=legacy), NOW)['counts']['collection_recent_complete'], 1)
        finally:
            legacy.close()
