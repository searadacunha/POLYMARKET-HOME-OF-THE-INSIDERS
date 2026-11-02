import json
import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from ledger import validate_edge, canonical_edges, financial_graph, control_graph, pair_links, save_exports
from temporal import synchronized_pairs, circular_shift_null

ROOT = Path(__file__).resolve().parents[1]
EDGES = json.loads((ROOT / 'fixtures/ballon_dor_documented.json').read_text())['edges']


def trade(wallet, txnum, sec, outcome='YES', observed_shift=1):
    from datetime import datetime, timezone, timedelta
    t = datetime.fromtimestamp(1791000000 + sec, timezone.utc)
    return {'wallet': wallet, 'market_id': 'm', 'outcome_id': outcome, 'transaction_hash': '0x' + f'{txnum:064x}',
            'timestamp_utc': t.isoformat(), 'observed_at_utc': (t + timedelta(seconds=observed_shift)).isoformat(),
            'nominal': '100', 'price': '0.08'}


class EvidenceTest(unittest.TestCase):
    def test_documented_ballon_edges_exact(self):
        self.assertEqual(len(financial_graph(EDGES)), 3)
        self.assertEqual(sum(int(e['raw_amount']) for e in EDGES[1:]), 5170000000)
        links = pair_links(EDGES, [EDGES[0]['from'], EDGES[0]['to']], {})
        self.assertEqual(len(links['financial_links']), 1)
        self.assertEqual(links['financial_links'][0]['ownership'], 'NOT_ESTABLISHED')

    def test_duplicates_do_not_inflate(self):
        self.assertEqual(len(canonical_edges(EDGES + [EDGES[1]])), 3)

    def test_incorrect_decimals_rejected(self):
        bad = dict(EDGES[1], token_decimals=18)
        with self.assertRaises(ValueError): validate_edge(bad)

    def test_floats_rejected(self):
        bad = dict(EDGES[1], raw_amount=2210000000.0)
        with self.assertRaises(ValueError): validate_edge(bad)

    def test_time_requires_explicit_utc(self):
        with self.assertRaises(ValueError): validate_edge(dict(EDGES[1], timestamp_utc='2026-10-09 20:28:35'))

    def test_service_and_unknown_common_funder_not_identified(self):
        base = dict(EDGES[1]); x = dict(base, transaction_hash='0x' + '1' * 64, to=EDGES[0]['to'])
        targets = [base['to'], x['to']]
        for label in ['SERVICE', 'UNKNOWN', 'EXCHANGE']:
            got = pair_links([base, x], targets, {base['from']: label})
            self.assertEqual(got['financial_links'], [])
            self.assertEqual(len(got['excluded_or_unresolved']), 1)
        proven = pair_links([base, x], targets, {base['from']: 'PERSONAL_NONCUSTODIAL_CONFIRMED'})
        self.assertEqual(len(proven['financial_links']), 1)
        self.assertEqual(proven['financial_links'][0]['ownership'], 'NOT_ESTABLISHED')

    def test_candidate_is_not_money_edge(self):
        candidate = dict(EDGES[0], evidence_level='CANDIDATE')
        self.assertEqual(financial_graph([candidate]), [])
        self.assertEqual(control_graph(EDGES), [])

    def test_exports_parse_and_never_overwrite(self):
        from xml.etree import ElementTree as ET
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root) / 'new'
            info = save_exports(EDGES, dest)
            self.assertEqual(info['financial_edges'], 3)
            ET.parse(dest / 'financial.graphml')
            self.assertEqual((dest / 'evidence_edges.csv').read_text().count('\n'), 4)
            with self.assertRaises(FileExistsError): save_exports(EDGES, dest)


class TemporalTest(unittest.TestCase):
    def setUp(self):
        self.trades = [trade('a', 101, 0), trade('b', 102, 3), trade('c', 103, 50), trade('d', 104, 800)]
        self.now = '2026-10-03T23:00:00Z'

    def test_all_windows_and_first_delta(self):
        result = synchronized_pairs(self.trades, self.now)
        ab = [x for x in result if x['wallet_a'] == 'a' and x['wallet_b'] == 'b']
        self.assertEqual([r['window_s'] for r in ab], [5, 30, 60, 300, 900, 3600])
        self.assertTrue(all(r['min_delta_s'] == 3 for r in ab))

    def test_future_observation_never_enters(self):
        future = trade('e', 105, 2, observed_shift=500000)
        with_future = synchronized_pairs(self.trades + [future], self.now)
        without = synchronized_pairs(self.trades, self.now)
        self.assertEqual(with_future, without)

    def test_other_outcome_not_coordinated(self):
        other = trade('e', 106, 2, 'NO')
        result = synchronized_pairs(self.trades + [other], self.now)
        self.assertFalse(any(x['wallet_a'] == 'a' and x['wallet_b'] == 'e' for x in result))

    def test_null_is_reproducible_and_not_insider_probability(self):
        one = circular_shift_null(self.trades, self.now, window_s=5, simulations=99, seed=7)
        two = circular_shift_null(self.trades, self.now, window_s=5, simulations=99, seed=7)
        self.assertEqual(one, two)
        self.assertEqual(one['status'], 'EXPLORATORY_NOT_VALIDATED')
        self.assertTrue(0 < one['p_value'] <= 1)

if __name__ == '__main__': unittest.main()
