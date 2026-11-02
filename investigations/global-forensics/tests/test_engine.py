"""Engine tests on synthetic inputs, no network. Each one answers a defect or risk named in AUDIT.md."""
import gzip
import json
import os
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve()
sys.path.insert(0, str(HERE.parent.parent / 'engine'))
from gf import alloc, bridges, events, ledger_pnl, proof, sqd  # noqa: E402
from gf.net import Refused, Store  # noqa: E402

A, B, C = '0x' + 'a' * 40, '0x' + 'b' * 40, '0x' + 'c' * 40
USDC = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
TX1, TX2 = '0x' + '1' * 64, '0x' + '2' * 64
BLOCK = '0x' + 'f' * 64


def move(source, target, raw, tx=TX1, log=None, t=100, kind='erc20', level=events.LISTED, block=1):
    return {'chain_id': 1, 'block_number': block, 'block_hash': BLOCK, 'transaction_hash': tx, 'log_index': log, 'kind': kind, 'contract': USDC if kind == 'erc20' else None, 'token': 'USDC', 'decimals': 6, 'raw_amount': str(raw), 'timestamp': t, 'from': source, 'to': target, 'source': 'test', 'decoding': 'test', 'level': level, 'data_class': events.SYNTHETIC}


class Events(unittest.TestCase):
    def test_a_confirmed_token_move_needs_its_log_index(self):
        with self.assertRaises(ValueError):
            events.validate(move(A, B, 1, level=events.ONCHAIN))

    def test_two_equal_unindexed_moves_stay_two(self):
        """The defect of ledger.id_of: identical rows must not merge when numbered apart."""
        first, second = move(A, B, 10), move(A, B, 10)
        first['seq'], second['seq'] = 0, 1
        self.assertEqual(len(events.merge([first, second])), 2)

    def test_same_log_read_twice_is_one_and_the_higher_level_wins(self):
        low, high = move(A, B, 10, log=7), move(A, B, 10, log=7, level=events.ONCHAIN)
        merged = events.merge([low, high])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]['level'], events.ONCHAIN)

    def test_two_readings_of_one_log_that_disagree_raise(self):
        with self.assertRaises(ValueError):
            events.merge([move(A, B, 10, log=7), move(A, B, 11, log=7)])


class Allocation(unittest.TestCase):
    def test_forced_share_is_a_lower_bound(self):
        """900 in from B, 100 in from C, 950 out: at least 850 of it must come from B, whichever unit is called which."""
        moves = [move(B, A, 900, tx=TX1, t=1), move(C, A, 100, tx=TX2, t=2), move(A, C, 950, tx='0x' + '3' * 64, t=3)]
        out = alloc.bounds(moves, A, moves[2])
        by = {s['source']: s for s in out['sources']}
        self.assertEqual(by[B]['lower_raw'], 850)
        self.assertEqual(by[C]['lower_raw'], 50)  # B holds only 900, so at least 50 of the 950 comes from C
        self.assertEqual(by[C]['upper_raw'], 100)
        self.assertEqual(out['unexplained_raw'], 0)

    def test_an_outflow_above_the_read_balance_is_unexplained(self):
        moves = [move(B, A, 10, t=1), move(A, C, 15, tx=TX2, t=2)]
        self.assertEqual(alloc.bounds(moves, A, moves[1])['unexplained_raw'], 5)
        self.assertEqual(alloc.replay(moves, A)['missing_raw'], 5)

    def test_fifo_and_lifo_differ_and_both_conserve(self):
        moves = [move(B, A, 10, tx=TX1, t=1), move(C, A, 10, tx=TX2, t=2), move(A, C, 10, tx='0x' + '3' * 64, t=3)]
        fifo, lifo = alloc.convention(moves, A, 'FIFO'), alloc.convention(moves, A, 'LIFO')
        self.assertEqual(fifo['rows'][0]['from_source'], B)
        self.assertEqual(lifo['rows'][0]['from_source'], C)
        for out in (fifo, lifo):
            self.assertEqual(sum(r['raw'] for r in out['rows']) + out['closing_raw'], 20)
            self.assertIn('convention', out['rows'][0]['meaning'])


class Accounting(unittest.TestCase):
    ROWS = [dict(type='DEPOSIT', usdc_size=100, timestamp=1), dict(type='TRADE', side='BUY', usdc_size=100, size=1000, condition_id='c', title='t', timestamp=2, outcome='Yes'),
            dict(type='REDEEM', usdc_size=1000, size=1000, condition_id='c', timestamp=3), dict(type='WITHDRAWAL', usdc_size=999, timestamp=4), dict(type='MYSTERY', usdc_size=5, timestamp=5)]

    def test_result_is_cash_by_market_not_withdrawals_minus_deposits(self):
        out = ledger_pnl.account(self.ROWS)
        self.assertEqual(Decimal(out['markets'][0]['cash_result']), Decimal(900))
        self.assertEqual(Decimal(out['computed_balance']), Decimal(1))
        self.assertEqual(out['unknown_types'], {'MYSTERY': 1})

    def test_a_held_winning_position_is_not_cash(self):
        out = ledger_pnl.account(self.ROWS[:2])
        self.assertEqual(Decimal(out['markets'][0]['cash_result']), Decimal(-100))
        self.assertEqual(Decimal(out['markets'][0]['shares_left_by_api']), Decimal(1000))


class Proof(unittest.TestCase):
    TRANSFER = proof.TRANSFER

    def receipt(self, status='0x1'):
        return dict(transactionHash=TX1, blockHash=BLOCK, blockNumber='0x10', status=status, logs=[dict(address=USDC, logIndex='0x2', topics=[self.TRANSFER, '0x' + A[2:].rjust(64, '0'), '0x' + B[2:].rjust(64, '0')], data='0x' + hex(500)[2:].rjust(64, '0'))])

    def test_a_receipt_yields_the_move_with_its_log_index(self):
        moves = proof.moves_in(1, TX1, self.receipt(), dict(value='0x0', to=B, **{'from': A}), 100, events.ONCHAIN)
        self.assertEqual(moves[0]['log_index'], 2)
        self.assertEqual((moves[0]['from'], moves[0]['to'], moves[0]['raw_amount']), (A, B, '500'))
        events.validate(moves[0])

    def test_a_reverted_transaction_is_marked(self):
        moves = proof.moves_in(1, TX1, self.receipt('0x0'), dict(value='0x5', to=B, **{'from': A}), 100, events.ONCHAIN)
        self.assertTrue(all(m['success'] is False for m in moves))

    def test_two_nodes_that_disagree_refuse(self):
        one, two = self.receipt(), self.receipt()
        two['logs'][0]['data'] = '0x' + hex(501)[2:].rjust(64, '0')
        self.assertNotEqual(proof._digest(one), proof._digest(two))


class Bridges(unittest.TestCase):
    def message_v1(self, sender):
        msg = (0).to_bytes(4, 'big') + (7).to_bytes(4, 'big') + (0).to_bytes(4, 'big') + (9).to_bytes(8, 'big') + bytes(32) * 3
        body = (0).to_bytes(4, 'big') + bytes(32) + bytes.fromhex(B[2:]).rjust(32, b'\0') + (123).to_bytes(32, 'big') + bytes.fromhex(sender[2:]).rjust(32, b'\0')
        data = msg + body
        encoded = (64).to_bytes(32, 'big') + (0).to_bytes(32, 'big') + len(data).to_bytes(32, 'big') + data
        return dict(input=bridges.CCTP_MINT + encoded.hex())

    def test_cctp_message_gives_chain_sender_and_amount_without_an_api(self):
        out = bridges.cctp_message(self.message_v1(A))
        self.assertEqual(out['origin_chain'], 137)
        self.assertEqual(out['sender'], A)
        self.assertEqual(out['recipient'], B)
        self.assertEqual(out['raw'], 123)
        self.assertIs(out['proof'], True)

    def test_another_call_is_not_a_cctp_mint(self):
        self.assertIsNone(bridges.cctp_message(dict(input='0xa9059cbb' + '0' * 128)))

    def test_relay_proof_false_when_the_id_is_absent(self):
        class Net:
            def rpc(self, method, params, chain=None):
                if method == 'eth_getTransactionByHash':
                    return (dict(input='0x' + ('ab' * 32 if params[0] == 'out' else 'cd' * 32)), {})
                return (dict(logs=[dict(data='0x00', topics=[])]), {})
        rec = dict(in_txs=[(1, 'in')], out_txs=[(137, 'out')])
        self.assertIs(bridges.relay_proof(Net(), rec), False)

    def test_relay_proof_none_on_a_same_chain_swap(self):
        self.assertIsNone(bridges.relay_proof(None, dict(in_txs=[(137, '0x1')], out_txs=[(137, None)])))


class Sqd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))

    def tearDown(self):
        self.tmp.cleanup()

    def block(self, number, logs=()):
        return json.dumps(dict(header=dict(number=number, hash=f'0x{number:064x}', timestamp=number), logs=list(logs))).encode()

    def test_scan_resumes_from_its_checkpoint_and_reads_no_block_twice(self):
        log = dict(address=USDC, topics=[sqd.TRANSFER, '0x' + A[2:].rjust(64, '0'), '0x' + B[2:].rjust(64, '0')], data='0x' + hex(5)[2:].rjust(64, '0'), transactionHash=TX1, logIndex=3, transactionIndex=0)
        calls = []

        def post(chain, query):
            calls.append(query['fromBlock'])
            start = query['fromBlock']
            if start == 10:
                return 200, self.block(11, [log]) + b'\n' + self.block(12)
            raise ConnectionError('network dropped')

        scan = sqd.Scan(1, [A], 10, 20, root=self.tmp.name, guard=lambda: None, post=post)
        with self.assertRaises(ConnectionError):
            scan.run()
        self.assertEqual(scan.state['next_block'], 13)
        calls.clear()

        def rest(chain, query):
            calls.append(query['fromBlock'])
            return 200, self.block(20)

        again = sqd.Scan(1, [A], 10, 20, root=self.tmp.name, guard=lambda: None, post=rest)
        self.assertTrue(again.run())
        self.assertEqual(calls, [13])
        rows = list(again.events())
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['log_index'], 3)
        self.assertEqual(rows[0]['block_hash'], f'0x{11:064x}')
        self.assertEqual(again.coverage()['status'], 'WINDOW_COMPLETE')

    def test_unfinished_scan_says_incomplete_with_its_range(self):
        scan = sqd.Scan(1, [A], 10, 20, root=self.tmp.name, guard=lambda: None, post=lambda c, q: (200, self.block(12)))
        scan.run(max_seconds=-1)
        out = scan.coverage()
        self.assertEqual(out['status'], 'INCOMPLETE')
        self.assertEqual(out['to_block_exclusive'], 10)

    def test_a_token_transfer_with_a_non_standard_shape_is_not_decoded_as_one(self):
        erc721 = dict(address=USDC, topics=[sqd.TRANSFER, '0x' + A[2:].rjust(64, '0'), '0x' + B[2:].rjust(64, '0'), '0x' + '0' * 64], data='0x', transactionHash=TX1, logIndex=1)
        self.assertEqual(sqd.decode_block(1, dict(header=dict(number=1, hash=BLOCK, timestamp=1), logs=[erc721])), [])


class Store_(unittest.TestCase):
    def test_answers_keep_when_and_from_whom_and_a_digest(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR')) as tmp:
            store = Store(Path(tmp) / 's.sqlite3')
            meta = store.put('k', 'request', 'host', dict(a=1))
            value, read = store.get('k')
            self.assertEqual(value, dict(a=1))
            self.assertEqual(read['sha256'], meta['sha256'])
            self.assertEqual(read['host'], 'host')
            self.assertIsNone(store.get('other'))


if __name__ == '__main__':
    unittest.main(verbosity=1)
