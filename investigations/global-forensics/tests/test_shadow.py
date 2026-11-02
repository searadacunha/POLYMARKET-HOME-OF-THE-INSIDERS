"""Shadow engine on synthetic rows. No network, and the collector's files are not touched."""
import os
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'engine'))
from gf import shadow  # noqa: E402


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


if __name__ == '__main__':
    unittest.main(verbosity=1)
