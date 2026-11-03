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
sys.path.insert(0, str(HERE.parent.parent / 'engine/tools'))
from gf import account, alloc, bridges, events, explorer, graph, labels, ledger_pnl, proof, sqd, state, tracer  # noqa: E402
from gf.net import Refused, Store  # noqa: E402

A, B, C, D = '0x' + 'a' * 40, '0x' + 'b' * 40, '0x' + 'c' * 40, '0x' + 'd' * 40
USDC = '0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48'
TX1, TX2, TX3 = '0x' + '1' * 64, '0x' + '2' * 64, '0x' + '3' * 64
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

    def test_a_flow_on_solana_does_not_crash_the_case(self):
        class Fake:
            calls = 0

            def rpc(self, *a, **k):
                raise AssertionError('no EVM read on a Solana hash')

            def get(self, *a, **k):
                return dict(requests=[]), {}
        self.assertIsNone(bridges.Bridges(Fake())(dict(transaction_hash='sig', to='x', timestamp=1, **{'from': 'y'}), events.SOLANA))

    def test_a_spent_budget_or_a_failed_read_is_not_taken_for_no_bridge(self):
        class Spent:
            calls = 0

            def rpc(self, *a, **k):
                return dict(input='0x'), {}

            def get(self, *a, **k):
                raise AssertionError('no call after the budget')
        e = dict(transaction_hash=TX1, to=A, timestamp=1, **{'from': B})
        hop = bridges.Bridges(Spent(), relay_budget=0)(e, 1)
        self.assertEqual((hop['status'], hop['proof']), ('RELAY_BUDGET_SPENT', None))

        class Down:
            calls = 0

            def rpc(self, *a, **k):
                raise Refused('all nodes failed')

            def get(self, *a, **k):
                raise Refused('route down')
        hop = bridges.Bridges(Down())(e, 1)
        self.assertEqual((hop['status'], hop['proof']), ('READ_FAILED', None))

    def test_rpc_on_a_chain_without_a_node_is_a_refusal(self):
        from gf.net import Net
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(Refused):
                Net(store=Store(Path(d) / 's.sqlite3'), guard=lambda: None).rpc('eth_getBalance', ['x', 'latest'], events.TRON)

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


class Graph(unittest.TestCase):
    def trace(self, case, edges):
        return dict(case=case, wallet=B if case == 'two' else A, edges=edges, classes=[], account={})

    def hop(self, role, proof_ok, direction, sender, recipient, frm, to):
        return dict(direction=direction, role=role, other_cls=labels.SERVICE, kind='erc20', chain_id=1, block_number=1, transaction_hash=TX1, log_index=1, token='USDT', decimals=6, raw_amount='5', timestamp=9, note=json.dumps(dict(id='i' + sender, proof=proof_ok, sender=sender, recipient=recipient)), **{'from': frm, 'to': to})

    def test_a_proved_hop_joins_two_files_at_the_recipient_and_the_solver_never_does(self):
        solver, shared = '0x' + 'f' * 40, '0x' + 'd' * 40
        g = graph.Graph()
        g.add_trace(self.trace('one', [self.hop('bridge_deposit', True, 'cashout', A, shared, A, solver)]))
        g.add_trace(self.trace('two', [self.hop('bridge_deposit', True, 'cashout', B, shared, B, solver)]))
        links = g.links_between_cases()
        self.assertEqual([x['address'] for x in links], [shared])
        self.assertEqual(links[0]['relation'], 'COMMON_DESTINATION_CANDIDATE')
        self.assertEqual(links[0]['ownership'], 'OWNERSHIP_NOT_ESTABLISHED')

    def test_an_unproved_hop_joins_nothing(self):
        solver, shared = '0x' + 'f' * 40, '0x' + 'd' * 40
        g = graph.Graph()
        for case, wallet in (('one', A), ('two', B)):
            g.add_trace(self.trace(case, [self.hop('bridge_deposit', None, 'cashout', wallet, shared, wallet, solver)]))
        self.assertEqual(g.links_between_cases(), [])

    def test_flows_keep_the_proof_of_each_line(self):
        g = graph.Graph()
        g.add_trace(self.trace('one', [dict(direction='funding', role='transfer', other_cls='PERSONAL_SIZED', kind='erc20', chain_id=1, block_number=2, block_hash=BLOCK, transaction_hash=TX2, log_index=7, token='USDC', decimals=6, raw_amount='1', timestamp=3, level='REVERIFIED', **{'from': B, 'to': A})]))
        line = g.flows()['one']['funding'][0]
        self.assertEqual((line['transaction_hash'], line['log_index'], line['level']), (TX2, 7, 'REVERIFIED'))


class LightCap(unittest.TestCase):
    def test_flows_past_the_cap_are_written_as_a_stop_and_not_dropped_in_silence(self):
        from gf.tracer import Trace
        trace = Trace(None, 'case', A, [], max_flows=2)
        trace.cls = lambda address, chain, parties=None: dict(cls=labels.SERVICE)
        trace.bridge = lambda e, chain, info: None
        flows = [dict(move('0x' + str(i) * 40, A, (i + 1) * 10 ** 6, tx='0x' + str(i) * 64, log=i), token='USDC') for i in range(5)]
        trace.expand('funding', A, 1, 10 ** 9, 0, flows)
        self.assertEqual(len(trace.edges), 2)
        caps = [s for s in trace.stops if s['reason'] == 'LIGHT_FLOW_CAP']
        self.assertEqual((caps[0]['rows'], caps[0]['kept']), (3, 2))
        self.assertEqual(sorted(int(e['raw_amount']) for e in trace.edges), [4 * 10 ** 6, 5 * 10 ** 6])


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


class GraphClasses(unittest.TestCase):
    def edge(self, source, target, other_cls='PERSONAL_SIZED', role='transfer', direction='funding', tx=TX1):
        return dict(direction=direction, role=role, other_cls=other_cls, chain_id=137, block_number=1, transaction_hash=tx, kind='erc20', raw_amount='5', **{'from': source, 'to': target, 'timestamp': 5, 'token': 'USDC', 'decimals': 6, 'level': 'LISTED'})

    def file(self, case, wallet, edges, classes=()):
        return dict(case=case, wallet=wallet, edges=edges, classes=[dict(address=a, cls=c) for a, c in classes], account=dict(control_latest=dict(owners=[wallet], block=1)))

    def test_one_read_as_a_hub_is_enough_whatever_the_order_of_the_files(self):
        for order in ((labels.HUB, labels.PERSONAL), (labels.PERSONAL, labels.HUB)):
            g = graph.Graph()
            g.add_trace(self.file('one', A, [self.edge(C, A)], [(C, order[0])]))
            g.add_trace(self.file('two', B, [self.edge(C, B, tx=TX2)], [(C, order[1])]))
            self.assertEqual(g.links_between_cases(), [])

    def test_every_relation_is_the_same_whatever_the_order_of_the_files(self):
        """A move read by two files was kept for the first one only, so a link appeared or vanished with the file order."""
        import itertools
        D = '0x' + 'd' * 40
        files = [self.file('one', A, [self.edge(C, A), self.edge(A, B, other_cls=labels.CONTRACT, direction='cashout', tx=TX2)], [(C, labels.PERSONAL), (B, labels.CONTRACT)]),
                 self.file('two', B, [self.edge(C, B), self.edge(A, B, tx=TX2)], [(C, labels.HUB)]),
                 self.file('three', D, [self.edge(C, D, tx='0x' + '3' * 64)], [(C, labels.PERSONAL)])]
        seen = set()
        for order in itertools.permutations(files):
            g = graph.Graph()
            for f in order:
                g.add_trace(f)
            seen.add(json.dumps([g.links_between_cases(), g.transfers_between_accounts(), g.bridge_routes(), {k: g.nodes[k]['cls'] for k in sorted(g.nodes)}], sort_keys=True))
        self.assertEqual(len(seen), 1, 'relations hang on the order of the files')

    def test_a_move_read_by_two_files_links_them(self):
        D = '0x' + 'd' * 40
        for order in ((0, 1), (1, 0)):
            files = [self.file('one', A, [self.edge(D, C), self.edge(C, A, tx=TX2)]), self.file('two', B, [self.edge(D, C), self.edge(C, B, tx='0x' + '3' * 64)])]
            g = graph.Graph()
            for i in order:
                g.add_trace(files[i])
            found = {x['address']: x['cases'] for x in g.links_between_cases()}
            self.assertEqual(found[D], ['one', 'two'], 'the far funder is read by both files')
            self.assertEqual(found[C], ['one', 'two'])

    def test_one_wallet_listed_twice_is_one_file_and_links_to_nothing(self):
        """linkcs and d-0x0e9310b9a1 are one account, and they read as a common funder."""
        g = graph.Graph()
        g.add_trace(self.file('linkcs', A, [self.edge(C, A)]))
        self.assertFalse(g.add_trace(self.file('d-a', A, [self.edge(C, A)])))
        self.assertEqual(g.links_between_cases(), [])
        self.assertEqual(g.duplicates, {'d-a': 'linkcs'})

    def test_changenow_a_bridge_and_a_relayer_never_join_two_files(self):
        for cls in (labels.SERVICE, labels.HUB, labels.CONTRACT, labels.UNREAD):
            g = graph.Graph()
            g.add_trace(self.file('one', A, [self.edge(C, A, other_cls=cls)], [(C, cls)]))
            g.add_trace(self.file('two', B, [self.edge(C, B, other_cls=cls, tx=TX2)], [(C, cls)]))
            self.assertEqual(g.links_between_cases(), [], cls)
            self.assertEqual(g.transfers_between_accounts(), [], cls)

    def test_a_contract_wallet_paid_by_another_account_is_a_direct_transfer(self):
        g = graph.Graph()
        g.add_trace(self.file('one', A, [self.edge(A, B, other_cls=labels.CONTRACT, direction='cashout')], [(B, labels.CONTRACT)]))
        g.add_trace(self.file('two', B, []))
        self.assertEqual(g.nodes[B]['cls'], 'POLYMARKET_WALLET')
        direct = g.transfers_between_accounts()
        self.assertEqual((direct[0]['from_files'], direct[0]['to_files'], direct[0]['tx']), (['one'], ['two'], TX1))
        self.assertEqual(direct[0]['ownership'], 'OWNERSHIP_NOT_ESTABLISHED')

    def test_the_same_chains_are_no_route_and_the_same_address_is(self):
        def hop(case, wallet, far, tx):
            e = self.edge(wallet, C, other_cls=labels.SERVICE, role='bridge_deposit', direction='cashout', tx=tx)
            e['note'] = json.dumps(dict(proof=True, sender=wallet, recipient=far, origin_chain=137, destination_chain=1, id=tx, basis='x'))
            return self.file(case, wallet, [e])
        far_one, far_two = '0x' + 'd' * 40, '0x' + 'e' * 40
        g = graph.Graph()
        g.add_trace(hop('one', A, far_one, TX1))
        g.add_trace(hop('two', B, far_two, TX2))
        self.assertEqual(g.bridge_routes(), [])
        g = graph.Graph()
        g.add_trace(hop('one', A, far_one, TX1))
        g.add_trace(hop('two', B, far_one, TX2))
        self.assertEqual([(r['side'], r['address'], r['files']) for r in g.bridge_routes()], [('recipient', far_one, ['one', 'two'])])

    def test_behaviour_joins_only_traced_accounts_within_the_window(self):
        g = graph.Graph()
        g.add_trace(self.file('one', A, []))
        g.add_trace(self.file('two', B, []))
        g.add_behaviour([dict(wallet=A, token='t', ts=100, usd=1), dict(wallet=B, token='t', ts=150, usd=1), dict(wallet=C, token='t', ts=120, usd=1)])
        self.assertEqual([(e['source'], e['target']) for e in g.edges if e['layer'] == graph.BEHAVIOUR], [(A, B)])
        self.assertEqual(g.links_between_cases(), [])


class ChangeNowPath(unittest.TestCase):
    def e(self, source, target, t, role='transfer', other_cls=labels.PERSONAL, note=None):
        return dict(role=role, other_cls=other_cls, chain_id=1, transaction_hash=TX1, raw_amount='5000000', decimals=6, token='USDC', timestamp=t, level='LISTED', note=note, **{'from': source, 'to': target})

    def test_a_path_goes_forward_in_time_and_never_crosses_a_service(self):
        import cn_dossiers as cn
        self.assertEqual([h['target'] for h in cn.path_to_account([self.e(A, C, 10), self.e(C, B, 20)], A, B, 5)], [C, B])
        self.assertIsNone(cn.path_to_account([self.e(A, C, 30), self.e(C, B, 20)], A, B, 5), 'money cannot go back in time')
        self.assertIsNone(cn.path_to_account([self.e(A, C, 1), self.e(C, B, 20)], A, B, 5), 'a move before the payment is not after it')
        self.assertIsNone(cn.path_to_account([self.e(A, C, 10, other_cls=labels.SERVICE), self.e(C, B, 20)], A, B, 5), 'a service joins nothing')

    def test_only_a_proved_hop_crosses_a_bridge(self):
        import cn_dossiers as cn
        def hop(proof):
            return self.e(C, B, 20, role='bridge_payout', other_cls=labels.SERVICE, note=json.dumps(dict(proof=proof, sender=A)))
        self.assertEqual(len(cn.path_to_account([hop(True)], A, B, 5)), 1)
        self.assertIsNone(cn.path_to_account([hop(None)], A, B, 5))


class FileState(unittest.TestCase):
    """A written file is not a finished one, and money that closes is not a finished trace. Each test answers a way a file could pass as finished without being so."""

    def base(self, **kw):
        return dict(dict(wallet=A, mode='full', account=dict(history_complete=True, balances_now=dict(pUSD=5.0, open_positions=dict(current_value=0))), nodes=[dict(node=A)], edges=[dict(direction='funding', role='deposit_path', transaction_hash=TX1, token='USDC', raw_amount='5000000', decimals=6, source='rpc:137', chain_id=137, **{'from': B, 'to': A}), dict(direction='cashout', role='transfer', transaction_hash=TX2, token='POL', raw_amount='1', decimals=18, chain_id=137, **{'from': A, 'to': C})], stops=[]), **kw)

    ROWS = [dict(type='DEPOSIT', usdc_size='5', transaction_hash=TX1)]

    def stop(self, direction, reason, **kw):
        return dict(dict(direction=direction, reason=reason, address=C, chain=137), **kw)

    def state(self, *stops, rows=None, **kw):
        return state.file_state(self.base(stops=list(stops), **kw), self.ROWS if rows is None else rows)

    def with_withdrawal(self, raw):
        """A deposit of 5, then a withdrawal of 5 with a path of this size."""
        file = self.base(account=dict(history_complete=True, balances_now=dict(pUSD=0.0, open_positions=dict(current_value=0))))
        file['edges'].append(dict(direction='cashout', role='withdrawal_path', transaction_hash=TX3, token='USDC', raw_amount=str(raw), decimals=6, source='rpc:137', chain_id=137, **{'from': A, 'to': C}))
        return file, self.ROWS + [dict(type='WITHDRAWAL', usdc_size='5', transaction_hash=TX3)]

    def test_a_closed_account_with_every_branch_ended_is_complete(self):
        s = state.file_state(self.base(), self.ROWS)
        self.assertEqual((s['processing'], s['accounting'], s['chain']['residual']), (state.TRACE_COMPLETE, state.ACCOUNTING_RECONCILED, 0.0))

    def test_named_and_measured_frontiers_end_a_branch(self):
        stops = [self.stop('cashout', 'SERVICE_OR_SHARED:SERVICE', name='Binance'), self.stop('funding', 'SERVICE_OR_SHARED:CONTRACT', name='Bridgers'), self.stop('funding', 'SERVICE_OR_SHARED:HUB_MEASURED', nonce=5000), self.stop('cashout', 'HUB_AT_READ', value_counterparties=900)]
        s = self.state(*stops)
        self.assertEqual(s['processing'], state.TRACE_COMPLETE)
        self.assertEqual(s['frontiers'], dict(named=2, measured_hub=2))

    def test_reconciled_money_does_not_finish_an_open_trace(self):
        """linkcs and burdensome-mix: the books closed within 1 USD while a deposit had no funder."""
        for stop, motive in ((self.stop('funding', 'AMBIGUOUS_PATH'), 'AMBIGUOUS_PATH'), (self.stop('cashout', 'DEPTH_BUDGET'), 'DEPTH_BUDGET'), (self.stop('funding', 'HISTORY_INCOMPLETE', parts=dict(token1155tx='row budget of 30000 reached')), 'HISTORY_INCOMPLETE')):
            s = self.state(stop)
            self.assertEqual((s['accounting'], s['processing']), (state.ACCOUNTING_RECONCILED, state.WORK_LEFT), stop)
            self.assertIn(motive, s['work_left'])

    def test_a_finished_trace_with_books_that_do_not_close_is_not_finished(self):
        s = state.file_state(self.base(), [dict(type='DEPOSIT', usdc_size='500', transaction_hash=TX1)])
        self.assertEqual((s['accounting'], s['processing'], s['chain']['residual']), (state.NOT_RECONCILED, state.WORK_LEFT, -495.0))
        self.assertIn('ACCOUNTING_NOT_RECONCILED', s['work_left'])

    def test_a_budget_is_never_a_frontier(self):
        for reason in ('DEPTH_BUDGET', 'NODE_BUDGET', 'LIGHT_FLOW_CAP'):
            s = self.state(self.stop('cashout', reason))
            self.assertEqual((s['processing'], s['exits']['state']), (state.WORK_LEFT, state.WORK_LEFT), reason)
            self.assertEqual(s['frontiers'], dict(named=0, measured_hub=0), reason)

    def test_a_cap_of_ours_is_work_and_a_cap_of_the_source_is_a_written_block(self):
        ours = self.state(self.stop('cashout', 'HISTORY_INCOMPLETE', parts=dict(txlist='row budget of 30000 reached', tokentx='a full page within one block')))
        self.assertEqual(ours['processing'], state.WORK_LEFT)
        self.assertEqual(self.state(self.stop('cashout', 'HISTORY_INCOMPLETE'))['processing'], state.WORK_LEFT)  # no reason written is no reason
        source = self.state(self.stop('cashout', 'HISTORY_INCOMPLETE', parts=dict(tokentx='a full page within one block')))
        self.assertEqual((source['processing'], source['blocked_by']), (state.BLOCKED_BY_DATA, dict(EXPLORER_CANNOT_PAGE_INSIDE_A_BLOCK=1)))

    def test_a_hub_measured_on_a_partial_read_needs_no_more_reading(self):
        hub = [self.stop('cashout', 'HISTORY_INCOMPLETE', parts=dict(txlist='row budget of 30000 reached')), self.stop('cashout', 'HUB_AT_READ', value_counterparties=900)]
        self.assertEqual(self.state(*hub)['processing'], state.TRACE_COMPLETE)
        elsewhere = dict(hub[1], address=D)
        self.assertEqual(self.state(hub[0], elsewhere)['processing'], state.WORK_LEFT)

    def test_a_real_withdrawal_must_have_its_path(self):
        file, rows = self.with_withdrawal(5_000_000)
        self.assertEqual(state.file_state(file, rows)['processing'], state.TRACE_COMPLETE)
        file['edges'].pop()  # a gas transfer is left on the exit side: it stands in for nothing
        s = state.file_state(file, rows)
        self.assertEqual((s['processing'], s['exits']['state'], s['work_left']), (state.WORK_LEFT, state.WORK_LEFT, dict(WITHDRAWAL_ROW_NOT_TRACED=1)))
        self.assertEqual((s['accounting'], s['exits']['untraced_row_usd']), (state.ACCOUNTING_RECONCILED, 5.0))

    def test_a_withdrawal_traced_for_part_of_its_amount_is_not_traced(self):
        file, rows = self.with_withdrawal(2_000_000)
        self.assertIn('WITHDRAWAL_ROW_NOT_TRACED', state.file_state(file, rows)['work_left'])

    def test_a_deposit_with_no_origin_is_not_traced(self):
        file = self.base()
        file['edges'][0]['transaction_hash'] = TX3
        file['edges'][0]['source'] = 'rpc:137'
        s = state.file_state(file, self.ROWS)
        self.assertEqual(s['processing'], state.WORK_LEFT)
        self.assertIn('DEPOSIT_ROW_NOT_TRACED', s['work_left'])

    def test_no_withdrawal_needs_no_exit(self):
        file = self.base()
        file['edges'].pop()
        s = state.file_state(file, self.ROWS)
        self.assertEqual((s['exits']['state'], s['processing']), ('NONE_OBSERVED', state.TRACE_COMPLETE))

    def test_an_unnamed_contract_is_no_documented_frontier(self):
        s = self.state(self.stop('cashout', 'SERVICE_OR_SHARED:CONTRACT', kind='CONTRACT'))
        self.assertEqual((s['processing'], s['work_left']), (state.WORK_LEFT, dict(CONTRACT_NOT_IDENTIFIED=1)))
        for status, motive in (('NOT_PUBLISHED', 'CONTRACT_SOURCE_NOT_PUBLISHED'), ('NO_FREE_EXPLORER', 'CONTRACT_NAME_NOT_READABLE_ON_THIS_CHAIN')):
            s = self.state(self.stop('cashout', 'SERVICE_OR_SHARED:CONTRACT', source_status=status))
            self.assertEqual((s['processing'], s['blocked_by']), (state.BLOCKED_BY_DATA, {motive: 1}))
        self.assertEqual(self.state(self.stop('cashout', 'SERVICE_OR_SHARED:CONTRACT', source_status='READ_FAILED'))['processing'], state.WORK_LEFT)

    def test_a_frontier_with_nothing_written_is_no_frontier(self):
        self.assertEqual(self.state(self.stop('cashout', 'SERVICE_OR_SHARED:SERVICE'))['work_left'], dict(SERVICE_WITHOUT_A_NAME=1))
        self.assertEqual(self.state(self.stop('cashout', 'SERVICE_OR_SHARED:HUB_MEASURED'))['work_left'], dict(HUB_WITHOUT_A_MEASURE=1))
        self.assertEqual(self.state(self.stop('cashout', 'HUB_AT_READ'))['work_left'], dict(HUB_WITHOUT_A_MEASURE=1))

    def test_many_small_moves_are_not_dust(self):
        """linkcs: 7,927 moves under 1 USD added up to 7,722 USD."""
        self.assertEqual(self.state(self.stop('cashout', 'DUST_NOT_FOLLOWED', rows=3, usd=.4))['processing'], state.TRACE_COMPLETE)
        self.assertEqual(self.state(self.stop('cashout', 'DUST_NOT_FOLLOWED', rows=7927, usd=7722.46))['work_left'], dict(DUST_SUM_NOT_FOLLOWED=1))
        self.assertEqual(self.state(self.stop('cashout', 'DUST_NOT_FOLLOWED'))['processing'], state.WORK_LEFT)

    def test_a_read_in_windows_leaves_the_rest_of_the_history_open(self):
        s = self.state(nodes=[dict(node=A), dict(node=C, status='WINDOW_COMPLETE')])
        self.assertEqual((s['processing'], s['work_left']), (state.WORK_LEFT, dict(READ_IN_WINDOWS_ONLY=1)))
        self.assertEqual(self.state(self.stop('funding', 'WINDOW_SCAN_NEEDED'))['processing'], state.WORK_LEFT)

    def test_a_network_failure_is_work_left_and_never_an_end(self):
        for stop in (self.stop('funding', 'READ_FAILED', detail='URLError'), self.stop('funding', 'SERVICE_OR_SHARED:UNREAD'), self.stop('cashout', 'BRIDGE_HOP_NOT_PROVEN', hop_status='READ_FAILED'), self.stop('cashout', 'BRIDGE_HOP_NOT_PROVEN', hop_status='success', proof=False, proof_error='eth_call failed'), self.stop('cashout', 'BRIDGE_HOP_NOT_PROVEN', hop_status='RELAY_BUDGET_SPENT')):
            self.assertEqual(self.state(stop)['processing'], state.WORK_LEFT, stop)

    def test_a_bridge_is_blocked_only_when_both_sides_were_read(self):
        self.assertEqual(self.state(self.stop('funding', 'BRIDGE_HOP_NOT_PROVEN', hop_status='success', proof=False))['blocked_by'], dict(BRIDGE_ID_ABSENT_ON_BOTH_CHAINS=1))
        for stop in (self.stop('funding', 'BRIDGE_HOP_NOT_PROVEN', hop_status='success', proof=None), self.stop('funding', 'BRIDGE_HOP_NOT_PROVEN'), self.stop('funding', 'BRIDGE_HOP_NOT_PROVEN', hop_status='success', proof=True)):
            self.assertEqual(self.state(stop)['work_left'], dict(BRIDGE_FAR_SIDE_NOT_READ=1), stop)

    def test_work_outranks_a_block_and_the_block_stays_written(self):
        s = self.state(self.stop('funding', 'BRIDGE_HOP_NOT_PROVEN', hop_status='success', proof=False), self.stop('cashout', 'NODE_BUDGET'))
        self.assertEqual((s['processing'], s['blocked_by'], s['work_left']), (state.WORK_LEFT, dict(BRIDGE_ID_ABSENT_ON_BOTH_CHAINS=1), dict(NODE_BUDGET=1)))

    def test_a_stop_this_module_does_not_know_counts_as_work(self):
        self.assertEqual(self.state(self.stop('funding', 'SOME_NEW_REASON'))['processing'], state.WORK_LEFT)

    def test_light_files_files_with_no_mode_and_unread_wallets_keep_work_left(self):
        self.assertEqual(self.state(mode='light')['work_left'], dict(LIGHT_MODE=1))
        self.assertEqual(self.state(mode=None)['work_left'], dict(LIGHT_MODE=1))
        self.assertEqual(self.state(nodes=[])['work_left'], dict(TRADING_WALLET_HISTORY_NOT_READ=1))
        self.assertEqual(self.state(self.stop('funding', 'DEPTH_BUDGET'), mode='light')['work_left'], dict(LIGHT_MODE=1, DEPTH_BUDGET=1))

    def test_an_empty_file_is_never_complete_and_closes_nothing(self):
        s = state.file_state(self.base(edges=[]), [])
        self.assertEqual((s['processing'], s['accounting'], s['funding']['state']), (state.BLOCKED_BY_DATA, state.NOT_CHECKED, 'NONE_FOUND'))
        self.assertEqual(s['blocked_by'], dict(NO_FUNDER_OBSERVED=1))

    def test_a_cut_list_reconciles_nothing_even_at_a_zero_residual(self):
        s = state.file_state(self.base(account=dict(history_complete=False, balances_now=dict(pUSD=5.0, open_positions=dict(current_value=0)))), self.ROWS)
        self.assertEqual((s['chain']['residual'], s['accounting'], s['processing']), (0.0, state.NOT_CHECKED, state.WORK_LEFT))

    def test_a_balance_that_cannot_be_read_is_not_a_close(self):
        s = state.file_state(self.base(account=dict(history_complete=True, balances_now=dict(error='down'))), self.ROWS)
        self.assertEqual((s['accounting'], s['processing'], s['work_left']), (state.NOT_CHECKED, state.WORK_LEFT, dict(BALANCE_NOT_READ=1)))

    def test_no_activity_rows_is_no_check(self):
        s = state.file_state(self.base())
        self.assertEqual((s['accounting'], s['processing']), (state.NOT_CHECKED, state.WORK_LEFT))

    def test_a_deposit_also_read_from_the_key_is_counted_once(self):
        """nobel-6741: the key's history shows the same 90,000 as the activity's deposit row, and a double count read as a residual."""
        twice = self.base()
        twice['edges'].append(dict(direction='funding', role='internal_to_dossier', transaction_hash=TX1, token='USDC', raw_amount='5000000', decimals=6, source='etherscan', chain_id=137, **{'from': B, 'to': A}))
        self.assertEqual(state.file_state(twice, self.ROWS)['chain']['direct_in'], 0)

    def test_a_direct_move_with_no_activity_row_closes_the_account(self):
        direct = self.base()
        direct['edges'].append(dict(direction='funding', role='transfer', transaction_hash=TX2, token='USDC.e', raw_amount='5000000', decimals=6, source='etherscan', chain_id=137, **{'from': B, 'to': A}))
        s = state.file_state(direct, [])
        self.assertEqual((s['chain']['direct_in'], s['chain']['reconciled']), (5.0, True))

    def test_collateral_on_another_chain_is_not_in_the_books(self):
        """The balance is read on Polygon: the same address holding USDC on Arbitrum must not close or open the account."""
        other = self.base()
        other['edges'].append(dict(direction='funding', role='transfer', transaction_hash=TX2, token='USDC', raw_amount='9000000', decimals=6, source='etherscan', chain_id=42161, **{'from': B, 'to': A}))
        self.assertEqual(state.file_state(other, self.ROWS)['chain']['direct_in'], 0)


class NetworkErrors(unittest.TestCase):
    """A dead network must not read as an answer."""

    def net(self, error):
        class Net:
            def rpc(self, method, params, chain=137, **k):
                if method == 'eth_getCode':
                    return '0x60', {}
                raise Refused(error)
        return Net()

    def test_a_dead_network_never_makes_a_wallet_with_no_known_key(self):
        from gf import account
        with self.assertRaises(Refused):
            account.control(self.net('eth_call failed on every node: polygon-bor-rpc.publicnode.com: URLError; polygon.drpc.org: URLError'), A)

    def test_a_revert_is_the_contract_answering(self):
        from gf import account
        out = account.control(self.net("eth_call failed on every node: a: {'code': 3, 'message': 'execution reverted'}"), A)
        self.assertEqual((out['form'], out['owners']), ('CLONE_OR_OTHER', []))

    def test_a_failed_proof_read_is_written_on_the_record(self):
        rec = dict(in_txs=[(1, TX1)], out_txs=[(137, TX2)])

        class Net:
            def rpc(self, *a, **k):
                raise Refused('URLError')
        self.assertIsNone(bridges.relay_proof(Net(), rec))
        self.assertIn('URLError', rec['proof_error'])


class FilesOnDisk(unittest.TestCase):
    def setUp(self):
        import run_wallets
        self.rw = run_wallets
        self.tmp = tempfile.TemporaryDirectory(dir=os.environ.get('TMPDIR'))
        self.done = Path(self.tmp.name) / 'trace.json'

    def tearDown(self):
        self.tmp.cleanup()

    def test_a_file_first_traced_wider_keeps_its_width(self):
        for mode, width in (('light: depth 2, 14 nodes, 30 money rows', (14, None)), ('light: depth 2, 14 nodes, 12 largest flows per node, 30 money rows', (14, 12))):
            self.done.write_text(json.dumps(dict(mode=mode)))
            profile, kept = self.rw.light_profile(self.done)
            self.assertEqual(((profile['node_budget'], profile['max_flows']), kept), (width, mode))
            self.assertNotIn('chains', profile)

    def test_a_new_file_takes_the_narrow_profile(self):
        profile, mode = self.rw.light_profile(self.done)
        self.assertEqual((profile, mode), (self.rw.NARROW, self.rw.NARROW_MODE))

    def test_a_file_with_a_failed_read_is_read_again(self):
        for stops, lost in (([dict(reason='READ_FAILED')], True), ([dict(reason='SERVICE_OR_SHARED:UNREAD')], True), ([dict(reason='NO_LATER_OUTFLOW')], False)):
            self.done.write_text(json.dumps(dict(stops=stops)))
            self.assertEqual(self.rw.lost_reads(self.done), lost)


class WalletOwnHistory(unittest.TestCase):
    """Accounts with no DEPOSIT row or with no key apart from the address came out with no edge and no stop, which read as nothing to find. A fill pays a stranger, so following one would invent a funder."""

    def flow(self, tx, source=B, t=100):
        return dict(move(source, A, 5_000_000, tx=tx, t=t), token='USDC.e', decimals=6, token_known=True, chain_id=137)

    def walker(self, logs, **kw):
        class Net:
            def rpc(self, method, params, chain=137, **k):
                if logs.get(params[0]) is None:
                    raise Refused('down')
                return dict(logs=[dict(address=a) for a in logs[params[0]]]), {}
        return tracer.Trace(Net(), 'case', A, [], **kw)

    def test_fills_stay_out_and_direct_transfers_stay_in(self):
        row, ctf, plain, late, down, wrap = ['0x' + c * 64 for c in '123456']
        t = self.walker({ctf: [tracer.CONDITIONAL_TOKENS], plain: [C], late: [C]})
        t.market_txs, t.activity_end, t.positions_read = {row}, 150, True
        kept = t.money_only('funding', [self.flow(row), self.flow(ctf), self.flow(plain), self.flow(late, t=200), self.flow(down), self.flow(wrap)], 0, {wrap})
        self.assertEqual({e['transaction_hash'] for e in kept}, {plain, late})
        stops = {s['reason']: s for s in t.stops}
        self.assertEqual(stops['WALLET_FILLS_NOT_FOLLOWED']['rows'], 3)
        self.assertEqual(stops['WALLET_ROWS_PAST_ACTIVITY_LIST']['rows'], 1)
        self.assertEqual(stops['READ_FAILED']['address'], down)

    def test_rows_past_the_receipt_budget_stay_written_and_open(self):
        rows = ['0x' + f'{i:064x}' for i in range(1, tracer.WALLET_RECEIPTS + 4)]
        t = self.walker({r: [C] for r in rows})
        t.positions_read = True
        kept = t.money_only('funding', [self.flow(r) for r in rows], 0)
        self.assertEqual(len(kept), tracer.WALLET_RECEIPTS)
        self.assertEqual({s['reason']: s['rows'] for s in t.stops}, {'WALLET_ROWS_NOT_CHECKED': 3})

    def account(self, owners):
        return dict(deposits=[], withdrawals=[], first_activity=1000, control_latest=dict(owners=owners))

    def test_an_address_that_is_its_own_key_is_walked_on_every_chain(self):
        funding, cashout = self.walker({}, chains=(1, 137)).seed_account(self.account([A]))
        self.assertEqual({(n[0], n[1]) for n in funding}, {(A, 1), (A, 137)})
        self.assertEqual({(n[0], n[1]) for n in cashout}, {(A, 1), (A, 137)})

    def test_a_contract_wallet_is_walked_on_polygon_beside_its_key(self):
        funding, _ = self.walker({}, chains=(1, 137)).seed_account(self.account([B]))
        self.assertEqual({(n[0], n[1]) for n in funding}, {(A, 137), (B, 1), (B, 137)})


class BranchesNeverEndInSilence(unittest.TestCase):
    """Each of these left a branch with no stop, or read a stop that was not one."""

    def flow(self, tx='0x' + '4' * 64):
        return dict(move(B, D, 5_000_000, tx=tx, t=100), token='USDC.e', decimals=6, token_known=True, chain_id=137)

    def expand(self, hop, depth=0, **kw):
        t = tracer.Trace(None, 'case', A, [], relay=lambda e, chain, ask: hop, **kw)
        t.cls = lambda address, chain: dict(cls=labels.SERVICE, label=dict(name='Relay'))
        return t, t.expand('funding', D, 137, 10 ** 9, depth, [self.flow()])

    def reasons(self, t):
        return [s['reason'] for s in t.stops]

    def test_a_proved_hop_past_the_depth_limit_is_written(self):
        t, nodes = self.expand(dict(proof=True, sender=C, origin_chain=1), depth=8, max_depth=8)
        self.assertEqual((nodes, self.reasons(t)), ([], ['DEPTH_BUDGET']))

    def test_a_proved_hop_with_no_far_address_is_written(self):
        t, nodes = self.expand(dict(proof=True, origin_chain=1))
        self.assertEqual((nodes, self.reasons(t)), ([], ['BRIDGE_HOP_NOT_PROVEN']))

    def test_a_same_chain_swap_is_followed_and_a_cross_chain_record_is_not(self):
        same = dict(status='success', proof=None, sender=C, origin_chain=137, destination_chain=137)
        t, nodes = self.expand(same)
        self.assertEqual(([n[:2] for n in nodes], t.stops), ([(C, 137)], []))
        self.assertIsNone(json.loads(t.edges[0]['note'])['proof'])
        t, nodes = self.expand(dict(same, origin_chain=728126428, sender='TEfE77'))
        self.assertEqual((nodes, self.reasons(t)), ([], ['BRIDGE_HOP_NOT_PROVEN']))

    def test_a_deep_wallet_is_read_on_every_chain(self):
        t = tracer.Trace(None, 'case', A, [], chains=(1, 137))
        t.cls = lambda address, chain: dict(cls=labels.PERSONAL)
        self.assertEqual({n[1] for n in t.expand('funding', D, 137, 10 ** 9, 5, [self.flow()])}, {1, 137})

    def presence(self, **kw):
        return lambda address, chain: (None, dict(status='WINDOW_SCAN_NEEDED', presence=dict(dict(nonce=0, code=False, delegated=False, native=.1, tokens=dict(USDT=99.0)), **kw)))

    def walked(self, direction, **kw):
        t = tracer.Trace(None, 'case', A, [])
        t.read = self.presence(**kw)
        t.walk(direction, [(D, 56, 0, 1)])
        return self.reasons(t)

    def test_an_eoa_that_never_signed_has_no_exit_to_scan(self):
        self.assertEqual(self.walked('cashout'), ['NO_SPEND_HOLDS_VALUE'])
        self.assertEqual(self.walked('funding'), ['WINDOW_SCAN_NEEDED'])  # money still came in from somewhere
        self.assertEqual(self.walked('cashout', nonce=2), ['WINDOW_SCAN_NEEDED'])
        self.assertEqual(self.walked('cashout', code=True), ['WINDOW_SCAN_NEEDED'])  # a contract spends with nonce 0
        self.assertEqual(self.walked('cashout', delegated=True), ['WINDOW_SCAN_NEEDED'])

    def test_a_small_fill_at_the_wallet_is_a_fill_and_not_dust(self):
        """linkcs: 7,927 fills under 1 USD were written as 7,722 USD of dust."""
        tx = '0x' + '5' * 64
        t = tracer.Trace(None, 'case', A, [])
        t.market_txs, t.positions_read = {tx}, True
        t.expand('funding', A, 137, 10 ** 9, 0, [dict(move(B, A, 500_000, tx=tx, t=100), token='USDC.e', decimals=6, token_known=True, chain_id=137)])
        self.assertEqual(self.reasons(t), ['WALLET_FILLS_NOT_FOLLOWED', 'NO_FLOW_IN_WINDOW'])


class ContractSource(unittest.TestCase):
    def net(self, rows, status='1'):
        class Net:
            def etherscan_key(self):
                return 'k'

            def get(self, url, params, **k):
                return dict(status=status, message='OK', result=[rows[params['address']]] if params['address'] in rows else 'Rate limit'), {}
        return Net()

    def test_the_implementation_names_a_proxy_and_an_unpublished_one_names_nothing(self):
        impl = '0x' + 'e' * 40
        proxy = dict(ContractName='ERC1967Proxy', Proxy='1', Implementation=impl)
        self.assertEqual(explorer.contract_source(self.net({A: proxy, impl: dict(ContractName='Bridgers')}), A, 1), dict(status='VERIFIED', name='Bridgers'))
        self.assertEqual(explorer.contract_source(self.net({A: proxy, impl: dict(ContractName='')}), A, 1), dict(status='NOT_PUBLISHED', name=None))
        self.assertEqual(explorer.contract_source(self.net({A: dict(ContractName='', ABI='Contract source code not verified')}), A, 1), dict(status='NOT_PUBLISHED', name=None))

    def test_a_chain_with_no_free_explorer_says_so_and_a_failure_raises(self):
        self.assertEqual(explorer.contract_source(None, A, 8453), dict(status='NO_FREE_EXPLORER', name=None))
        with self.assertRaises(Refused):
            explorer.contract_source(self.net({}, status='0'), A, 1)

    def identified(self, net):
        return tracer.Trace(net, 'case', A, []).identify(dict(cls=labels.CONTRACT, address=A, chain=1, label=None))

    def test_a_safe_is_a_wallet_a_named_contract_a_frontier_and_a_failed_read_stays_open(self):
        safe = self.identified(self.net({A: dict(ContractName='GnosisSafeProxy')}))
        self.assertEqual((safe['cls'], safe['kind']), (labels.PERSONAL, 'SAFE'))
        named = self.identified(self.net({A: dict(ContractName='Bridgers')}))
        self.assertEqual((named['cls'], named['label']['name'], named['label']['category'], named['source_status']), (labels.CONTRACT, 'Bridgers', 'verified_contract', 'VERIFIED'))
        self.assertEqual(self.identified(self.net({}, status='0'))['source_status'], 'READ_FAILED')


class PayerInReceipt(unittest.TestCase):
    """The nine deposits written as ambiguous: the payer was in their own receipt."""
    USDC, USDCE, WPOL = '0x3c499c542cef5e3811e1192ce70d8cc03d5c3359', '0x2791bca1f2de4661ed88a30c99a7a9449aa84174', '0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270'

    def log(self, token, source, target, amount):
        return dict(address=token, topics=[account.TRANSFER, '0x' + source[2:].rjust(64, '0'), '0x' + target[2:].rjust(64, '0')], data=hex(amount))

    def test_money_entering_by_a_gateway_and_a_pool_names_its_payer(self):
        """linkcs: USDC from the payer, a fee, a swap at a pool, USDC.e to the wallet."""
        gateway, adapter, pool, solver = [c * 40 for c in '1234']
        gateway, adapter, pool, solver = ['0x' + x for x in (gateway, adapter, pool, solver)]
        logs = [self.log(self.USDC, B, gateway, 24988_150000), self.log(self.USDC, gateway, solver, 4_997600), self.log(self.USDC, gateway, adapter, 24983_152400), self.log(self.USDCE, pool, adapter, 24981_392050), self.log(self.USDC, adapter, pool, 24983_152400), self.log(self.USDCE, adapter, gateway, 24981_392050), self.log(self.USDCE, gateway, A, 24981_392050)]
        self.assertEqual(account.payer_in_receipt(dict(logs=logs), A, 24981.39), dict(kind=account.NET_PAYER, payer=B))

    def test_a_wallet_swapping_its_own_dollars_is_no_funding(self):
        """nobel-dirtycup: 20,000 USDC out to a pool, 19,995 USDC.e back."""
        logs = [self.log(self.USDCE, C, A, 19995_077683), self.log(self.USDC, A, C, 20000_000000)]
        self.assertEqual(account.payer_in_receipt(dict(logs=logs), A, 19995.08), dict(kind=account.SELF_SWAP, payer=A))

    def test_a_pool_paid_in_another_token_is_not_the_payer_and_the_operation_names_the_account(self):
        """burdensome-mix: WPOL sold to a pool, USDC.e to the wallet, under one ERC-4337 operation."""
        sender = dict(address=C, topics=[account.USER_OPERATION, '0x' + '9' * 64, '0x' + D[2:].rjust(64, '0')], data='0x')
        logs = [self.log(self.WPOL, B, C, 835 * 10 ** 18), self.log(self.USDCE, C, B, 85_926000), self.log(self.USDCE, B, A, 85_926000)]
        self.assertEqual(account.payer_in_receipt(dict(logs=logs + [sender]), A, 85.93), dict(kind=account.USEROP_SENDER, payer=D))
        self.assertIsNone(account.payer_in_receipt(dict(logs=logs), A, 85.93))  # no operation, so the receipt does not say

    def test_two_payers_stay_ambiguous(self):
        logs = [self.log(self.USDC, B, A, 100_000000), self.log(self.USDC, C, A, 100_000000)]
        self.assertIsNone(account.payer_in_receipt(dict(logs=logs), A, 100))

    def seed(self, receipt):
        class Net:
            def rpc(self, method, params, chain=137, **k):
                if receipt is None:
                    raise Refused('down')
                return receipt, {}
        t = tracer.Trace(Net(), 'case', A, [])
        t.cls = lambda address, chain: dict(cls=labels.PERSONAL)
        path = dict(origin=None, reason='only passed funds on', raw=5_000000, token=self.USDCE, log_index=1, hops=[1])
        t.seed_account(dict(deposits=[dict(tx=TX1, block=1, block_hash='0x', at=100, level='ONCHAIN_CONFIRMED', success=True, paths=[path])], withdrawals=[], first_activity=100, control_latest=dict(owners=[])))
        return t

    def test_the_seed_follows_the_payer_and_keeps_ambiguity_when_the_receipt_does_not_say(self):
        t = self.seed(dict(logs=[self.log(self.USDCE, B, A, 5_000000)]))
        self.assertEqual((t.edges[0]['from'], t.edges[0]['note'], t.stops), (B, account.NET_PAYER, []))
        self.assertIn(B, t.own)
        for down in (self.seed(None), self.seed(dict(logs=[]))):
            self.assertEqual(([s['reason'] for s in down.stops], down.edges), (['AMBIGUOUS_PATH'], []))

    def test_a_self_swap_closes_the_row_and_points_at_the_wallet(self):
        t = self.seed(dict(logs=[self.log(self.USDC, A, C, 5_010000), self.log(self.USDCE, C, A, 5_000000)]))
        self.assertEqual((t.edges[0]['role'], t.edges[0]['other_cls'], t.edges[0]['note'], t.stops), ('deposit_path', 'OWN', account.SELF_SWAP, []))


class ThreeFigures(unittest.TestCase):
    def test_reconciled_and_trace_state_are_counted_apart(self):
        import counters
        row = dict(generated=0, reconciled=0, trace_complete=0, blocked=0, work_left=0, with_wallet_history=0)
        for processing, books in ((state.WORK_LEFT, state.ACCOUNTING_RECONCILED), (state.TRACE_COMPLETE, state.ACCOUNTING_RECONCILED), (state.BLOCKED_BY_DATA, state.NOT_RECONCILED), (state.WORK_LEFT, state.NOT_CHECKED)):
            counters.count(row, dict(processing=processing, accounting=books, work_left=dict(X=1) if processing == state.WORK_LEFT else {}))
        self.assertEqual({k: row[k] for k in ('generated', 'reconciled', 'trace_complete', 'work_left', 'blocked')}, dict(generated=4, reconciled=2, trace_complete=1, work_left=2, blocked=1))


if __name__ == '__main__':
    unittest.main(verbosity=1)
