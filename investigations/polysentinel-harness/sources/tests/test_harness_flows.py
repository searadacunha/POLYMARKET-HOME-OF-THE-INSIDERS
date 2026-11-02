"""The paths toward live sources, on real public receipts and the fund-flow module's own output format, without a network."""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('SIGNAL_ENGINE_STATE', tempfile.mkdtemp(prefix='engine_state_'))

from harness import pipeline, recover, sources, verify  # noqa: E402
from harness.runner import load_config  # noqa: E402
from harness.store import Harness  # noqa: E402
from polysentinel import chain  # noqa: E402
from signal_engine.fund_flow import links  # noqa: E402

A, B, C = '0x' + 'a' * 40, '0x' + 'b' * 40, '0x' + 'c' * 40
TX = '0x' + '1' * 64


def section(wallet, incoming=(), outgoing=()):
    return dict(wallet=wallet, incoming=list(incoming), outgoing=list(outgoing), upstream=[], ownership=links.OWNERSHIP)


class FundingClaims(unittest.TestCase):
    def link(self, state, source=A, target=B, **kwargs):
        return links.relation(state, source, target, tx=TX, log_index=4, basis='test', **kwargs)

    def test_a_confirmed_transfer_between_flagged_wallets_is_a_route_with_its_transaction(self):
        flows = dict(wallets=[section(A, outgoing=[self.link(links.ONCHAIN_CONFIRMED)]), section(B, incoming=[self.link(links.ONCHAIN_CONFIRMED)])])
        found = pipeline.relations_from_flows(flows, [A, B])
        self.assertEqual(len(found), 1, 'one transfer read from both ends is one claim')
        self.assertEqual((found[0]['claimed'], found[0]['transaction_hash'], found[0]['log_index']), ('COMMON_FUNDING_ROUTE', TX, 4))
        self.assertEqual(verify.relations(dict(relations=found))['status'], 'PASS')

    def test_a_candidate_by_time_and_amount_never_becomes_a_route(self):
        found = pipeline.relations_from_flows(dict(wallets=[section(A, outgoing=[self.link(links.CROSSCHAIN_CANDIDATE)])]), [A, B])
        self.assertEqual(found[0]['claimed'], 'BEHAVIORAL_SIMILARITY')
        self.assertEqual(verify.relations(dict(relations=found))['status'], 'PASS')

    def test_a_service_paying_two_wallets_links_nothing(self):
        flows = dict(wallets=[section(A, outgoing=[self.link(links.ONCHAIN_CONFIRMED, source_is_service=True)])])
        self.assertEqual(pipeline.relations_from_flows(flows, [A, B]), [])

    def test_a_link_to_someone_outside_the_case_is_not_a_claim(self):
        flows = dict(wallets=[section(A, outgoing=[self.link(links.ONCHAIN_CONFIRMED, target=C)])])
        self.assertEqual(pipeline.relations_from_flows(flows, [A, B]), [])

    def test_states_with_no_public_proof_make_no_claim(self):
        for state in (links.OFFCHAIN_RECORD_REQUIRED, links.XMR_VISIBILITY_BOUNDARY, links.INSUFFICIENT_EVIDENCE, links.SERVICE_INTERACTION):
            self.assertEqual(pipeline.relations_from_flows(dict(wallets=[section(A, outgoing=[self.link(state)])]), [A, B]), [], state)


class FundingTask(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix='funding_')
        self.h = Harness(self.dir)
        self.config = load_config(self.dir)

    def tearDown(self):
        self.h.close()
        shutil.rmtree(self.dir, ignore_errors=True)

    def run_task(self):
        output = self.h.put_artifact(dict(event_key='ev', pairs=[dict(wallet=A), dict(wallet=B)]))
        recover.enqueue(self.h, 'f', 'case_funding')
        context = pipeline.Context(self.h, recover.claim(self.h, 'o'), self.config)
        return pipeline.case_funding(context, 1, output, 0)

    def test_no_source_says_not_traced_instead_of_empty_success(self):
        self.assertEqual(self.run_task(), dict(status='not_traced', relations=[]))

    def test_a_file_of_flows_reaches_the_claim(self):
        path = Path(self.dir) / 'flows.json'
        path.write_text(json.dumps(dict(ev=dict(wallets=[section(A, outgoing=[links.relation(links.ONCHAIN_CONFIRMED, A, B, tx=TX, log_index=1, basis='t')])]))))
        self.config['funding'] = dict(type='file', path=str(path))
        out = self.run_task()
        self.assertEqual((out['status'], len(out['relations'])), ('traced', 1))
        self.assertEqual(self.h.get_artifact(out['flows'])['wallets'][0]['wallet'], A)

    def test_an_event_absent_from_the_file_was_not_traced(self):
        path = Path(self.dir) / 'flows.json'
        path.write_text('{}')
        self.config['funding'] = dict(type='file', path=str(path))
        self.assertEqual(self.run_task()['status'], 'not_traced')

    def test_a_tracer_that_failed_says_so_instead_of_finding_no_link(self):
        failed = dict(status='TRACED', wallets=[dict(wallet=A, errors=['ChainError: all nodes down']), section(B)])
        self.config['funding'] = dict(type='trace')
        with mock.patch('signal_engine.service.trace_fund_flows', return_value=failed):
            out = self.run_task()
        self.assertEqual((out['status'], out['untraced'], out['traced']), ('partial', [A], 1))

    def test_a_case_larger_than_the_whole_daily_budget_stops_instead_of_waiting_forever(self):
        self.config['funding'] = dict(type='trace', max_wallets=8)
        self.config['budgets'] = dict(self.config['budgets'], api_requests_per_day=100)
        with self.assertRaises(recover.Permanent):
            self.run_task()

    def test_tracing_is_capped_and_starts_with_the_largest_wallets(self):
        traced = []
        def trace(wallets, config):
            traced.extend(wallets)
            return dict(wallets=[])
        output = self.h.put_artifact(dict(event_key='ev', pairs=[dict(wallet=f'w{n}', measures=dict(max_market_spend=n)) for n in range(9)]))
        recover.enqueue(self.h, 'f', 'case_funding')
        self.config['funding'] = dict(type='trace')
        with mock.patch('signal_engine.service.trace_fund_flows', trace):
            out = pipeline.case_funding(pipeline.Context(self.h, recover.claim(self.h, 'o'), self.config), 1, output, 0)
        self.assertEqual(traced, ['w8', 'w7', 'w6'])
        self.assertEqual(out['of_wallets'], 9)

    def test_an_unknown_source_is_refused(self):
        self.config['funding'] = dict(type='guess')
        with self.assertRaises(recover.Permanent):
            self.run_task()


class RpcReceipts(unittest.TestCase):
    """A log in the exchange's ABI, through the collector's own decoder. Laid out as tests/test_chain.py does: these fixtures hold real receipts reduced to transfers, without order logs."""

    @classmethod
    def setUpClass(cls):
        def word(value):
            return f'{value:064x}'
        tx, wallet = '0x' + '2' * 64, A
        data = '0x' + ''.join(word(v) for v in (0, 12345, 30_000_000, 100_000_000, 0, 0, 0))
        log = dict(address='0xe111180000d2663c0091e4f400237545b87b996b', topics=[chain.ORDER_V2, '0x' + '3' * 64, '0x' + '0' * 24 + wallet[2:], '0x' + '0' * 24 + B[2:]], data=data, blockNumber='0x64', blockHash='0x' + '4' * 64, transactionHash=tx, logIndex='0x1')
        cls.order = dict(transactionHash=tx, status='0x1', blockNumber='0x64', logs=[log])

    def fills(self, receipt):
        tx = receipt['transactionHash']
        with mock.patch('signal_engine.fund_flow.client.Client.receipt', return_value=receipt), mock.patch('signal_engine.fund_flow.client.Client.head', return_value=int(receipt.get('blockNumber', '0x64'), 16) + 256):
            return tx, sources.rpc_fills(tx)

    def test_decoded_fills_pass_the_validator_and_the_verifier(self):
        if self.order is None:
            self.skipTest('No order fill among these receipts')
        tx, out = self.fills(self.order)
        self.assertIsNone(sources.receipt_problem(tx)(out))
        self.assertEqual(out['status'], 1)
        fill = out['fills'][0]
        wallet = fill['maker'].lower()
        total = sum(int(f['nominal_raw']) for f in out['fills'] if f['token_id'] == fill['token_id'] and wallet == f['maker'].lower() and f['side'] == 'BUY') / 1e6
        one = dict(tx=tx.lower(), wallet=wallet, token_id=fill['token_id'], nominal=total, is_buy=True)
        self.assertEqual(verify.chain(dict(event_rows=[one], receipts={tx.lower(): out}), {wallet})['status'], 'PASS')
        self.assertEqual(verify.chain(dict(event_rows=[dict(one, nominal=total * 3)], receipts={tx.lower(): out}), {wallet})['status'], 'FAIL')

    def test_a_block_that_can_still_be_reorganised_stays_open(self):
        with mock.patch('signal_engine.fund_flow.client.Client.receipt', return_value=self.order), mock.patch('signal_engine.fund_flow.client.Client.head', return_value=0x64 + 255):
            self.assertIsNone(sources.rpc_fills(self.order['transactionHash']))

    def test_an_unknown_transaction_stays_open(self):
        with mock.patch('signal_engine.fund_flow.client.Client.receipt', return_value=None):
            self.assertIsNone(sources.rpc_fills(TX))

    def test_a_failed_node_is_transient(self):
        from signal_engine.fund_flow.client import ChainError
        with mock.patch('signal_engine.fund_flow.client.Client.receipt', side_effect=ChainError('all nodes down')):
            with self.assertRaises(recover.Transient):
                sources.rpc_fills(TX)

    def test_a_receipt_the_decoder_cannot_read_is_invalid_not_empty(self):
        """A log from a known exchange with a damaged ABI must not read as a transaction with no fills."""
        if self.order is None:
            self.skipTest('No order fill among these receipts')
        contracts = chain.registry(ROOT)
        damaged = json.loads(json.dumps(self.order))
        log = next(entry for entry in damaged['logs'] if chain.decode_order(entry, contracts))
        log['topics'] = log['topics'][:2]
        with mock.patch('signal_engine.fund_flow.client.Client.receipt', return_value=damaged), mock.patch('signal_engine.fund_flow.client.Client.head', return_value=0x64 + 256):
            with self.assertRaises(recover.InvalidResponse):
                sources.rpc_fills(damaged['transactionHash'])


class Screening(unittest.TestCase):
    def test_the_count_covers_the_24_hours_before_the_decision_and_nothing_after(self):
        folder = tempfile.mkdtemp(prefix='screen_')
        try:
            h = Harness(folder)
            now = 1_800_000_000
            hour = now // 3600
            for offset, pairs in ((-30, 1000), (-23, 5), (0, 7), (1, 900)):
                h.signal.put(f'harness:screened:{hour + offset}', pairs)
            self.assertEqual(pipeline.screened_in_24h(h.signal, now), 12)
            h.close()
        finally:
            shutil.rmtree(folder, ignore_errors=True)

    def test_a_public_source_counts_from_when_it_could_be_seen(self):
        self.assertIsNone(pipeline.known_at(dict(public_observed_at=200), 100))
        self.assertIsNotNone(pipeline.known_at(dict(public_observed_at=50), 100))
        self.assertIsNone(pipeline.known_at(None, 100))


if __name__ == '__main__':
    unittest.main()
