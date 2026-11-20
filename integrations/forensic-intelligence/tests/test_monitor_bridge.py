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
from monitor_bridge import SIX_DECIMAL_TOKENS, funding_to_edges, normalise_alert  # noqa: E402
from phi_monitor import chain, detect  # noqa: E402

sys.path.insert(0, str(MONITORING / 'tests'))
import test_engine as engine_case  # noqa: E402  (modules, not classes: their tests are not collected twice)
import test_replay as replay_case  # noqa: E402

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


class NormaliseAlert(unittest.TestCase):
    KEYS = ['condition_id', 'evidence_tx', 'id', 'level', 'reasons', 'side_or_outcome', 'source', 't_alert', 't_first', 'wallet']

    def test_phi_monitor_alert_of_the_replayed_evening(self):
        con, fx = replay_case.load(); self.addCleanup(con.close)
        body = detect.evaluate(con, fx['market']['condition_id'], 'YES', replay_case.T_ALERT)[1]
        a = normalise_alert(json.loads(json.dumps(body)))             # the same body as stored in the alerts table
        self.assertEqual(sorted(a), self.KEYS)
        self.assertEqual((a['source'], a['level'], a['side_or_outcome'], a['wallet'], a['t_first'], a['t_alert']),
                         ('phi_monitor', 'LONELY_THIN', 'YES', replay_case.ACCOUNT, replay_case.T_FIRST, replay_case.T_ALERT))
        self.assertEqual((a['id'], a['evidence_tx'], a['reasons']), (body['id'], body['evidence_tx'], body['reasons']))

    def test_phi_engine_alert_of_the_fresh_funded_bet(self):
        e_ = engine_case
        con, _ = e_.db(self); entry = e_.Evaluation.setup(self, con, e_.W1, e_.T0)
        rows = {e_.W1: [[e_.T0 - 100, 'D', None, None, 40000.0, None, None, '0xdep1'], [e_.T0, 'T', e_.COND, 'BUY', 2000.0, 0.06, 0, None]]}
        rpc = e_.chain_rpc({'0xdep1': e_.swap_receipt(e_.W1, 39_991_000_000, 900)},
                           [(e_.W1, e_.FUNDER, 40_000_000_000, 880, '0xfund1'), (e_.W1, e_.POOL, 39_991_000_000, 900, '0xdep1')])
        alerts, _ = e_.enrich.evaluate(con, entry, rpc=rpc, get_json=e_.activity(rows), now=lambda: e_.T0 + 400)
        body = next(x for x in alerts if x['class'] == 'C1_FRESH_FUNDED_BET')
        a = normalise_alert(body)
        self.assertEqual(sorted(a), self.KEYS)
        self.assertEqual((a['source'], a['level'], a['condition_id'], a['side_or_outcome'], a['wallet'], a['t_first'], a['t_alert']),
                         ('phi_engine', 'C1_FRESH_FUNDED_BET', e_.COND, 'Yes', e_.W1, None, e_.T0))
        self.assertEqual(a['evidence_tx'], [f['tx'] for f in body['evidence']['fills']]); self.assertTrue(a['evidence_tx'])
        self.assertEqual(a['reasons'][1:], body['anomaly']['signals'])

    def test_an_unknown_body_is_refused(self):
        with self.assertRaises(ValueError):
            normalise_alert({'id': 'x', 'level': 'LONELY'})


if __name__ == '__main__':
    unittest.main()
