"""Shadow engine on synthetic rows. No network, and the collector's files are not touched."""
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'engine'))
from gf import shadow, shadow2  # noqa: E402


def row(wallet, ts, usd=500.0, price=.1, token='T', market='M', buy=1, observed=None):
    return dict(wallet=wallet, ts=ts, observed_at=ts + 2 if observed is None else observed, event_key='E', market_id='m', condition_id=market, token_id=token, is_buy=buy, size=usd / price, price=price, nominal=usd, tx=f'0x{wallet}{ts}', outcome='Yes')


class Shadow(unittest.TestCase):
    def run_rows(self, rows):
        engine, alerts = shadow.Engine(), []
        for r in sorted(rows, key=lambda x: x['observed_at']):
            alerts += engine.feed(r, r['observed_at'])
        return engine, alerts

    def test_three_entrants_inside_the_tightest_window_fire_once(self):
        _, alerts = self.run_rows([row('a', 1000), row('b', 1002), row('c', 1003), row('d', 1004)])
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['components']['synchronised_entrants']['window_s'], 5)

    def test_spaced_entrants_do_not_fire(self):
        _, alerts = self.run_rows([row('a', 1000), row('b', 9000), row('c', 19000)])
        self.assertEqual(alerts, [])

    def test_a_second_buy_of_a_wallet_is_not_an_entrant(self):
        _, alerts = self.run_rows([row('a', 900), row('a', 1000), row('a', 1001), row('b', 1002)])
        self.assertEqual(alerts, [])

    def test_high_price_and_small_size_do_not_count(self):
        self.assertEqual(self.run_rows([row('a', 1000, price=.6), row('b', 1001, price=.6), row('c', 1002, price=.6)])[1], [])
        self.assertEqual(self.run_rows([row('a', 1000, usd=50), row('b', 1001, usd=50), row('c', 1002, usd=50)])[1], [])

    def test_a_row_not_yet_observed_is_refused(self):
        engine = shadow.Engine()
        with self.assertRaises(ValueError):
            engine.feed(row('a', 1000, observed=2000), 1500)

    def test_alert_says_what_is_missing_and_what_else_explains_it(self):
        _, alerts = self.run_rows([row('a', 1000), row('b', 1001), row('c', 1002)])
        self.assertTrue(alerts[0]['missing'] and alerts[0]['alternatives'])
        self.assertIn('Not a finding', alerts[0]['meaning'])

    def test_hash_chain_detects_an_edit(self):
        _, alerts = self.run_rows([row('a', 1000), row('b', 1001), row('c', 1002), row('d', 50000, token='U', market='N'), row('e', 50001, token='U', market='N'), row('f', 50002, token='U', market='N')])
        self.assertEqual(len(alerts), 2)
        self.assertIsNone(shadow.verify_chain(alerts))
        alerts[0]['components']['total_usd'] = 1
        self.assertEqual(shadow.verify_chain(alerts), 0)

    def test_same_pairs_across_markets_are_seen_only_after_the_first_market(self):
        rows = [row(w, 1000 + i, token='T', market='M') for i, w in enumerate('abc')] + [row(w, 90000 + i, token='U', market='N') for i, w in enumerate('abc')]
        _, alerts = self.run_rows(rows)
        self.assertEqual(alerts[0]['components']['same_pairs_on_other_markets'], [])
        self.assertEqual(alerts[1]['components']['same_pairs_on_other_markets'], ['M'])

    def test_a_collection_gap_is_written_into_the_next_alert(self):
        _, alerts = self.run_rows([row('x', 100, price=.9), row('a', 5000), row('b', 5001), row('c', 5002)])
        self.assertTrue(any('Collection gap' in m for m in alerts[0]['missing']))

    def test_the_module_cannot_read_outcomes(self):
        source = (Path(shadow.__file__)).read_text()
        code = source[source.index('class Engine'):]
        for word in ('outcomePrices', 'resolved_', "['win']", 'closed_at', 'redeem'):
            self.assertNotIn(word, code)

    def test_read_only_database_cannot_be_written(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as tmp:
            path = Path(tmp) / 's.sqlite3'
            cx = sqlite3.connect(path)
            cx.execute('CREATE TABLE trades(wallet, ts, observed_at, event_key, market_id, condition_id, token_id, is_buy, size, price, nominal, tx, outcome)')
            cx.commit()
            cx.close()
            ro, cursor = shadow.read_rows(path)
            with self.assertRaises(sqlite3.OperationalError):
                ro.execute('INSERT INTO trades(wallet) VALUES(1)')
            ro.close()


class Shadow2(unittest.TestCase):
    def run_rows(self, rows):
        engine, alerts = shadow2.Engine2(), []
        for r in sorted(rows, key=lambda x: x['observed_at']):
            alerts += engine.feed(r, r['observed_at'])
        return engine, alerts

    def out_of_order(self):
        """Trades spread over 2 100 s in trade time, the earliest seen last. shadow-1 reads them as a 5 s set."""
        return [row('a', 1000, observed=1002), row('b', 3000, observed=3002), row('c', 900, observed=3100)]

    def test_shadow1_defect_still_shown_on_its_own_engine(self):
        engine, alerts = shadow.Engine(), []
        for r in self.out_of_order():
            alerts += engine.feed(r, r['observed_at'])
        self.assertEqual(alerts[0]['components']['synchronised_entrants']['window_s'], 5)
        trades = alerts[0]['trades']
        self.assertEqual(max(t['ts'] for t in trades) - min(t['ts'] for t in trades), 2100)

    def test_a_set_must_fit_inside_its_stated_window(self):
        alert = self.run_rows(self.out_of_order())[1][0]
        self.assertEqual(alert['components']['synchronised_entrants']['window_s'], 3600)

    def test_a_real_burst_arriving_out_of_order_is_found_and_marked_late(self):
        rows = [row('a', 1003, observed=9000), row('b', 1001, observed=9001), row('c', 1002, observed=9002)]
        alerts = self.run_rows(rows)[1]
        self.assertEqual(len(alerts), 1)
        spread = max(t['ts'] for t in alerts[0]['trades']) - min(t['ts'] for t in alerts[0]['trades'])
        self.assertLessEqual(spread, alerts[0]['components']['synchronised_entrants']['window_s'])
        self.assertEqual(alerts[0]['timing']['state'], 'LATE')

    def test_a_fresh_burst_is_live_and_a_batch_says_so(self):
        self.assertEqual(self.run_rows([row('a', 1000), row('b', 1001), row('c', 1002)])[1][0]['timing']['state'], 'LIVE')
        same = [row(w, 1000 + i, observed=5000) for i, w in enumerate('abc')]
        self.assertTrue(self.run_rows(same)[1][0]['timing']['one_batch'])

    def test_a_late_row_older_than_a_trigger_stays_under_the_cooldown(self):
        rows = [row(w, 100000 + i) for i, w in enumerate('abc')] + [row(w, 99000 + i, observed=100500) for i, w in enumerate('def')]
        self.assertEqual(len(self.run_rows(rows)[1]), 1)

    def test_hash_chain_covers_timing_labels(self):
        rows = [row('a', 1000), row('b', 1001), row('c', 1002), row('d', 50000, token='U', market='N'), row('e', 50001, token='U', market='N'), row('f', 50002, token='U', market='N')]
        alerts = self.run_rows(rows)[1]
        self.assertEqual(len(alerts), 2)
        self.assertIsNone(shadow.verify_chain(alerts))
        alerts[1]['timing']['state'] = 'LIVE!'
        self.assertEqual(shadow.verify_chain(alerts), 1)

    def test_no_outcome_field_in_the_module(self):
        text = (Path(shadow2.__file__)).read_text()
        for word in ('win', 'resolved', 'outcome_prices'):
            self.assertNotRegex(text, rf"\b{word}\b")

if __name__ == '__main__':
    unittest.main(verbosity=1)
