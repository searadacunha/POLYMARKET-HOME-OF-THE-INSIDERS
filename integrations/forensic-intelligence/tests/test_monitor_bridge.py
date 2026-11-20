import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[1]
MONITORING = REPO / 'monitoring'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(MONITORING))
from ledger import canonical_edges, financial_graph  # noqa: E402
from monitor_bridge import SIX_DECIMAL_TOKENS, funding_to_edges  # noqa: E402
from phi_monitor import chain  # noqa: E402

FUNDING = json.loads((MONITORING / 'fixtures/nobel_machado_20251009.json').read_text())['funding']


class FundingToEdges(unittest.TestCase):
    def test_every_stored_row_becomes_a_valid_edge_with_its_own_values(self):
        edges, refused = funding_to_edges(FUNDING)
        self.assertEqual(refused, [])
        self.assertEqual(len(canonical_edges(edges)), 2)
        self.assertEqual(len(financial_graph(edges)), 2)
        for row, edge in zip(FUNDING, edges):
            self.assertEqual((edge['transaction_hash'], edge['log_index'], edge['block_number'], edge['from'], edge['to'], edge['token_contract']),
                             (row['tx'], row['log_index'], row['block'], row['payer'], row['proxy'], row['token']))
        self.assertEqual([e['raw_amount'] for e in edges], ['40000000000', '39991023546'])
        self.assertEqual(edges[0]['timestamp_utc'], '2025-10-09T22:40:19+00:00')

    def test_a_missing_field_refuses_the_row(self):
        for field in ('tx', 'log_index', 'block', 'ts', 'proxy', 'payer', 'token', 'amount'):
            row = {k: v for k, v in FUNDING[0].items() if k != field}
            edges, refused = funding_to_edges([row])
            self.assertEqual((edges, refused[0][1]), ([], f'missing {field}'))

    def test_rows_that_cannot_be_proven_are_refused_with_a_reason(self):
        deposit = {'wallet': FUNDING[0]['proxy'], 'tx': FUNDING[0]['tx'], 'ts': 1, 'usdc': 1.0, 'status': 'ok',
                   'payer': FUNDING[0]['payer'], 'via': 'direct', 'block': 1, 'sha256': '0'}       # phi_engine deposits row
        rows = [deposit,
                dict(FUNDING[0], proxy='0xsecond', payer='0xkey', token='t'),                    # test_replay synthetic row
                dict(FUNDING[0], token='0x' + '11' * 20),                                        # not a collateral token
                dict(FUNDING[0], amount=1.0000001),                                               # not whole 6-decimal units
                dict(FUNDING[0], payer='0xkey')]
        edges, refused = funding_to_edges(rows)
        self.assertEqual(edges, [])
        reasons = [r for _, r in refused]
        self.assertEqual(reasons[0], 'missing log_index, proxy, token, amount')
        self.assertIn('decimals unknown', reasons[1])
        self.assertIn('decimals unknown', reasons[2])
        self.assertIn('6-decimal units', reasons[3])
        self.assertIn('address', reasons[4])

    def test_token_list_is_the_monitor_list(self):
        self.assertEqual(SIX_DECIMAL_TOKENS, set(chain.STABLES))


if __name__ == '__main__':
    unittest.main()
