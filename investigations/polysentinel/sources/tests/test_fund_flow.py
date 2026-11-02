"""Fund flows on real public receipts where possible; synthetic rows only prove mechanics. Nothing here reaches the network."""
import json
import random
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signal_engine.fund_flow import graph as graphs  # noqa: E402
from signal_engine.fund_flow import ledger, links, wallets  # noqa: E402
from signal_engine.fund_flow.client import BudgetExhausted, ChainError, Client  # noqa: E402
from signal_engine.fund_flow.flows import COLLATERAL_RESERVE, PUSD, RELAY_DEPOSITORY, TRANSFER, USDC_E, ZERO, label_of, transfers, tx_flow  # noqa: E402
from signal_engine.fund_flow.keccak import keccak256, selector, topic, word  # noqa: E402

DATA = json.loads((ROOT / 'tests/fixtures/fund_flow_receipts.json').read_text())
REAL = DATA['receipts']
T0 = 1_800_000_000


def sample(kind, wallet_type=None, tag=None):
    return next(r for r in REAL if r['kind'] == kind and (wallet_type is None or r.get('wallet_type') == wallet_type) and (tag is None or r.get('tag') == tag))


def address(n):
    return '0x' + format(n, '040x')


def log(token, source, target, raw, index, tx='0x' + 'a' * 64):
    return dict(address=token, topics=[TRANSFER, '0x' + word(source).hex(), '0x' + word(target).hex()], data='0x' + format(raw, '064x'), logIndex=hex(index), transactionHash=tx, blockNumber='0x10')


def receipt(logs, tx='0x' + 'a' * 64):
    return dict(transactionHash=tx, blockNumber='0x10', status='0x1', logs=logs)


class Fake:
    """Answers from a table: a wrong call raises, so a test cannot pass by reaching something unplanned."""

    def __init__(self, code=None, calls=None, receipts=None, http=None):
        self.code, self.calls, self.receipts, self.http_answers = code or {}, calls or {}, receipts or {}, http or {}
        self.rpc_used = self.http_used = 0

    def rpc(self, method, params, chain=137):
        if method == 'eth_getCode':
            return self.code.get(params[0], '0x')
        raise AssertionError('Unplanned ' + method)

    def call(self, to, data, block='latest', chain=137):
        answer = self.calls.get((to, data[:10]))
        if answer is None:
            raise ChainError('reverted')
        return answer

    def receipt(self, tx, chain=137):
        return self.receipts.get((chain, tx))

    def get_json(self, url, params=None):
        return self.http_answers[url]


class Hashing(unittest.TestCase):
    def test_known_vectors(self):
        self.assertEqual(keccak256(b'').hex(), 'c5d2460186f7233c927e7db2dcc703c0e500b653ca82273b7bfad8045d85a470')
        self.assertEqual(topic('Transfer(address,address,uint256)'), TRANSFER)
        self.assertEqual(selector('balanceOf(address)'), '0x70a08231')
        self.assertEqual(len(keccak256(b'x' * 136)), 32)
        self.assertEqual(len(keccak256(b'x' * 135)), 32)


class WalletTypes(unittest.TestCase):
    def test_a_real_legacy_proxy_derives_from_its_signer_only(self):
        v = DATA['proxy_vector']
        self.assertEqual(wallets.proxy_address(v['signer'], v['implementation']), v['wallet'])
        self.assertNotEqual(wallets.proxy_address(address(5), v['implementation']), v['wallet'])
        self.assertTrue(v['official_view_agrees'])

    def test_a_deposit_wallet_derives_from_its_owner(self):
        self.assertEqual(wallets.deposit_wallet_address('0x08d409aae84f9b7b6a798c97c457a0f41e856c7b', '0x58ca52ebe0dadfdf531cde7062e76746de4db1eb'), '0x5008c44a36c52f03de75d7aa98c15c14397e2302')

    def test_the_relayer_is_not_the_signer(self):
        v = DATA['proxy_vector']
        client = Fake(calls={(wallets.PROXY_FACTORY, selector('getImplementation()')): '0x' + word(v['implementation']).hex()})
        relayed = dict({'from': address(77)}, input='0x405cec67' + word(address(88)).hex())
        result = wallets.resolve_proxy_signer(client, v['wallet'], [relayed])
        self.assertEqual((result['signer'], result['signer_status']), (None, wallets.SIGNER_UNKNOWN))
        self.assertIn(address(77), result['submitters'])

    def test_a_signer_in_calldata_is_proved_by_derivation(self):
        v = DATA['proxy_vector']
        calls = {(wallets.PROXY_FACTORY, selector('getImplementation()')): '0x' + word(v['implementation']).hex(), (wallets.LEGACY_EXCHANGE, selector('getPolyProxyWalletAddress(address)')): '0x' + word(v['wallet']).hex()}
        relayed = dict({'from': address(77)}, input='0x405cec67' + word(v['signer']).hex())
        result = wallets.resolve_proxy_signer(Fake(calls=calls), v['wallet'], [relayed])
        self.assertEqual((result['signer'], result['official_view_agrees'], result['signer_also_submitted']), (v['signer'], True, False))

    def test_the_four_types_from_bytecode(self):
        eoa, proxy, safe, deposit, other = address(1), address(2), address(3), address(4), address(9)
        impl = '44e999d5c2f66ef0861317f9a4805ac2e90aeb4f'
        owners = '0x' + (32).to_bytes(32, 'big').hex() + (1).to_bytes(32, 'big').hex() + word(address(50)).hex()
        client = Fake(code={proxy: '0x' + wallets.CLONE_PREFIX + impl + '5af43d', safe: '0x6080604052600080546001600160a01b0316813563', deposit: '0x' + wallets.BEACON_PREFIX + wallets.DEPOSIT_BEACON[2:], other: '0x60016002'},
                      calls={(wallets.PROXY_FACTORY, selector('getImplementation()')): '0x' + '0' * 24 + impl, (safe, selector('getOwners()')): owners, (safe, selector('getThreshold()')): '0x1', (wallets.SAFE_FACTORY, selector('computeProxyAddress(address)')): '0x' + word(safe).hex(), (deposit, selector('owner()')): '0x' + word(address(60)).hex()})
        self.assertEqual(wallets.classify_wallet(client, eoa)['type'], wallets.EOA)
        kept = wallets.classify_wallet(client, proxy)
        self.assertEqual((kept['type'], kept['signer_status']), (wallets.PROXY, wallets.SIGNER_UNKNOWN))
        got = wallets.classify_wallet(client, safe)
        self.assertEqual((got['type'], got['owners'], got['threshold'], got['polymarket_factory']), (wallets.SAFE, [address(50)], 1, True))
        got = wallets.classify_wallet(client, deposit)
        self.assertEqual((got['type'], got['owners']), (wallets.DEPOSIT, [address(60)]))
        self.assertIn('Session signers', got['limit'])
        self.assertEqual(wallets.classify_wallet(client, other)['type'], wallets.OTHER)

    def test_a_clone_of_another_implementation_is_not_a_polymarket_proxy(self):
        proxy = address(2)
        client = Fake(code={proxy: '0x' + wallets.CLONE_PREFIX + 'ab' * 20}, calls={(wallets.PROXY_FACTORY, selector('getImplementation()')): '0x' + '0' * 24 + 'cd' * 20})
        self.assertEqual(wallets.classify_wallet(client, proxy)['type'], wallets.OTHER)


class RealReceipts(unittest.TestCase):
    def test_a_deposit_names_the_funder_behind_the_mint(self):
        checked = 0
        for r in REAL:
            if r['kind'] == 'DEPOSIT' and r.get('tag') != 'direct_pusd':
                flow = tx_flow(r['receipt'], r['wallet'])
                self.assertTrue(flow['conversions']['minted'])
                self.assertAlmostEqual(flow['wallet_net_raw'] / 1e6, r['usd'], places=4)
                self.assertNotIn(ZERO, flow['sources'])
                self.assertFalse(any(a.startswith(COLLATERAL_RESERVE) for a in flow['sources']))
                self.assertEqual(sum(flow['sources'].values()), sum(flow['sinks'].values()))
                self.assertIn(r['wallet'], flow['sinks'])
                self.assertEqual(flow['unexplained_raw'], 0)
                self.assertEqual(sum(p['raw'] for p in flow['inflows']), flow['wallet_net_raw'])
                checked += 1
        self.assertGreaterEqual(checked, 3)

    def test_a_batch_of_strangers_deposits_credits_only_this_wallets_funder(self):
        batches = 0
        for r in REAL:
            flow = tx_flow(r['receipt'], r['wallet'])
            if r['kind'] == 'DEPOSIT' and len(flow['sources']) > 1:
                batches += 1
                self.assertEqual(len(flow['inflows']), 1)
                paying = next(l for l in flow['logs'] if l['log_index'] == flow['inflows'][0]['hops'][0])
                self.assertEqual(paying['target'], PUSD)
                self.assertEqual(int(paying['raw']), flow['wallet_net_raw'])
                self.assertEqual(flow['inflows'][0]['origin'], paying['source'])
                self.assertFalse(flow['inflows'][0]['unclear'])
        self.assertGreaterEqual(batches, 1)

    def test_same_amounts_in_one_transaction_stop_the_pairing(self):
        w, other = address(1), address(2)
        flow = tx_flow(receipt([log(USDC_E, address(3), PUSD, 50, 1), log(USDC_E, address(4), PUSD, 50, 2), log(PUSD, ZERO, other, 50, 3), log(PUSD, ZERO, w, 50, 4)]), w)
        self.assertTrue(flow['inflows'][0]['unclear'])

    def test_a_mint_with_no_visible_payer_names_no_origin(self):
        w = address(1)
        flow = tx_flow(receipt([log(PUSD, ZERO, w, 50, 1)]), w)
        self.assertIsNone(flow['inflows'][0]['origin'])

    def test_a_multi_hop_path_reaches_the_first_sender(self):
        w, first, hop = address(1), address(2), address(3)
        flow = tx_flow(receipt([log(USDC_E, first, hop, 50, 1), log(USDC_E, hop, PUSD, 50, 2), log(PUSD, ZERO, w, 50, 3)]), w)
        self.assertEqual((flow['inflows'][0]['origin'], flow['inflows'][0]['hops']), (first, [1, 2, 3]))

    def test_a_direct_withdrawal_names_its_destination(self):
        w, out = address(1), address(2)
        flow = tx_flow(receipt([log(USDC_E, w, out, 50, 1)]), w)
        self.assertEqual((flow['outflows'][0]['destination'], flow['unexplained_raw']), (out, 0))

    def test_a_source_paying_a_fee_too_is_credited_only_what_reached_the_wallet(self):
        from signal_engine.fund_flow.trace import inspect_flow
        w, funder, fee = address(1), address(2), address(3)
        tx = '0x' + 'e' * 64
        client = Fake(receipts={(137, tx): receipt([log(USDC_E, funder, w, 90, 1, tx), log(USDC_E, funder, fee, 10, 2, tx)], tx)})
        client.block_time = lambda number: T0
        client.head = lambda: 10 ** 6
        relations, found = [], dict(origins=[], destinations=[], services=set())
        inspect_flow(client, tx, w, wallets.EOA, relations, found, [])
        self.assertEqual((relations[0]['raw'], found['origins'][0]['raw']), ('90', '90'))

    def test_a_withdrawal_ends_at_the_bridge_escrow_with_its_order_id(self):
        for wallet_type in (wallets.SAFE, wallets.PROXY, wallets.DEPOSIT):
            r = sample('WITHDRAWAL', wallet_type)
            flow = tx_flow(r['receipt'], r['wallet'])
            self.assertEqual(list(flow['sinks']), [RELAY_DEPOSITORY], wallet_type)
            self.assertEqual(flow['events']['orders'][0]['raw'], -flow['wallet_net_raw'])
            self.assertEqual(flow['events']['orders'][0]['depositor'], r['wallet'])
            self.assertEqual(len(flow['events']['orders'][0]['order_id']), 66)
            self.assertFalse(any(a.startswith(COLLATERAL_RESERVE) for a in flow['sources']))

    def test_a_relayer_is_not_taken_for_a_party_on_real_relayed_transactions(self):
        for r in REAL:
            flow = tx_flow(r['receipt'], r['wallet'])
            if flow['submitter'] != r['wallet'] and r.get('wallet_type'):
                self.assertNotIn(flow['submitter'], list(flow['sources']) + list(flow['sinks']), r['receipt']['transactionHash'])

    def test_a_real_swap_router_is_not_the_funder_and_the_submitter_can_be(self):
        for case in DATA['swap_cases']:
            flow = tx_flow(case['receipt'], case['wallet'])
            path = next(p for p in flow['inflows'] if p['log_index'] == case['log_index'])
            self.assertIsNotNone(path['passed_through'])
            self.assertEqual(path['origin'], case['funder'])
            self.assertEqual(path['origin'], flow['submitter'])
            self.assertTrue(path['paid'])

    def test_a_router_with_two_payers_behind_it_names_nobody(self):
        w, router, a, b, pool = address(1), address(2), address(3), address(4), address(5)
        other = address(70)
        flow = tx_flow(receipt([log(other, a, router, 10, 1), log(other, b, router, 10, 2), log(other, router, pool, 20, 3), log(USDC_E, pool, router, 19, 4), log(USDC_E, router, w, 19, 5)]), w)
        self.assertIsNone(flow['inflows'][0]['origin'])
        self.assertTrue(flow['inflows'][0]['unclear'])

    def test_a_contract_keeping_part_of_the_money_stays_the_named_sender(self):
        w, payer = address(1), address(2)
        flow = tx_flow(receipt([log(USDC_E, payer, w, 19, 1)]), w)
        self.assertEqual(flow['inflows'][0]['origin'], payer)

    def test_a_bridge_router_is_a_stop_on_the_way_not_the_source(self):
        r = sample('DEPOSIT', tag='relay_multihop')
        flow = tx_flow(r['receipt'], r['wallet'])
        self.assertIn('Relay v3 Router', flow['services'])
        self.assertEqual(label_of(flow['inflows'][0]['origin'])['name'], 'Relay EVM solver')
        self.assertGreater(len(flow['inflows'][0]['hops']), 2)

    def test_a_direct_transfer_has_no_conversion(self):
        r = sample('DEPOSIT', tag='direct_pusd')
        flow = tx_flow(r['receipt'], r['wallet'])
        self.assertFalse(flow['conversions']['minted'])
        self.assertGreater(flow['wallet_net_raw'], 0)

    def test_each_transfer_of_a_transaction_keeps_its_own_identity(self):
        moves = [t for r in REAL for t in transfers(r['receipt'])]
        keys = {(t['chain_id'], t['tx'], t['log_index']) for t in moves}
        self.assertEqual(len(keys), len(moves))
        self.assertGreater(len(moves), len({t['tx'] for t in moves}))

    def test_a_removed_log_is_refused(self):
        bad = receipt([dict(log(USDC_E, address(1), address(2), 5, 1), removed=True)])
        with self.assertRaises(ValueError):
            transfers(bad)


class Ambiguity(unittest.TestCase):
    def test_two_senders_and_two_receivers_are_not_paired(self):
        a, b, c, d = address(1), address(2), address(3), address(4)
        flow = tx_flow(receipt([log(USDC_E, a, c, 10, 1), log(USDC_E, b, d, 20, 2)]), c)
        self.assertTrue(flow['ambiguous'])

    def test_one_receiver_of_two_senders_is_not_ambiguous_about_the_receiver(self):
        a, b, c = address(1), address(2), address(3)
        flow = tx_flow(receipt([log(USDC_E, a, c, 10, 1), log(USDC_E, b, c, 20, 2)]), c)
        self.assertFalse(flow['ambiguous'])
        self.assertEqual(flow['sinks'], {c: 30})

    def test_a_wrap_and_unwrap_in_one_transaction_nets_out(self):
        w = address(1)
        flow = tx_flow(receipt([log(USDC_E, w, PUSD, 50, 1), log(PUSD, ZERO, w, 50, 2)]), w)
        self.assertEqual((flow['wallet_net_raw'], flow['sources'], flow['sinks']), (0, {}, {}))


class Ledgers(unittest.TestCase):
    def moved(self, source, target, raw, index, token=USDC_E, tx='0x1'):
        return dict(chain_id=137, tx=tx, log_index=index, block=1, token=token, source=source, target=target, raw=raw)

    def test_logs_against_balances_exact_or_a_stated_residual(self):
        w = address(1)
        moves = [self.moved(address(2), w, 100, 1), self.moved(w, address(3), 30, 2)]
        zero = dict(pUSD=0, USDC=0)
        exact = ledger.reconcile_chain(moves, w, {**zero, 'USDC.e': 5}, {**zero, 'USDC.e': 75})
        self.assertEqual(exact['USDC.e']['residual_raw'], 0)
        off = ledger.reconcile_chain(moves, w, {**zero, 'USDC.e': 5}, {**zero, 'USDC.e': 70})
        self.assertEqual(off['USDC.e']['residual_raw'], -5)

    def test_an_eoa_to_safe_transfer_is_counted_once_in_a_consolidated_account(self):
        eoa, safe = address(1), address(2)
        inner = self.moved(eoa, safe, 100, 5)
        result = ledger.consolidate({eoa: [self.moved(address(9), eoa, 100, 1), inner], safe: [inner, self.moved(safe, address(8), 40, 6)]})
        self.assertEqual((result['internal_raw'], result['internal_count'], result['received_raw'], result['sent_raw']), (100, 1, 100, 40))

    def test_two_transfers_of_one_transaction_stay_two(self):
        w = address(1)
        result = ledger.consolidate({w: [self.moved(address(9), w, 100, 1), self.moved(address(9), w, 100, 2)]})
        self.assertEqual(result['received_raw'], 200)

    def test_api_cash_says_what_it_is_not_and_keeps_unknown_types_apart(self):
        rows = [dict(type='DEPOSIT', usdc_size=100), dict(type='TRADE', side='BUY', usdc_size=40), dict(type='TRADE', side='SELL', usdc_size=10), dict(type='REDEEM', usdc_size=5), dict(type='WITHDRAWAL', usdc_size=20), dict(type='NEW_THING', usdc_size=9)]
        cash = ledger.cash_from_activity(rows)
        self.assertEqual((cash['computed_balance'], cash['deposits'], cash['withdrawals'], cash['unknown_types']), (55.0, 100.0, 20.0, dict(NEW_THING=1)))
        self.assertIn('not a profit', cash['note'])
        self.assertAlmostEqual(cash['trading_cash_flow'], -25.0)

    def test_a_failed_window_is_a_gap(self):
        class Flaky:
            def rpc(self, method, params, chain=137):
                if int(params[0]['fromBlock'], 16) >= 1000:
                    raise ChainError('limit')
                return []
        scan = ledger.scan_collateral(Flaky(), address(1), 0, 1500, chunk=1000)
        self.assertFalse(scan['complete'])
        self.assertEqual(scan['gaps'][0]['start'], 1000)


class Bridges(unittest.TestCase):
    ORDER = dict(order_id='0x' + 'b' * 64, log_index=3)

    def test_an_unknown_order_is_an_offchain_record_not_a_destination(self):
        client = Fake(http={'https://api.relay.link/intents/status/v3': (200, dict(status='unknown'))})
        self.assertEqual(links.relay_order_status(client, self.ORDER)['state'], links.OFFCHAIN_RECORD_REQUIRED)

    def test_a_finished_order_needs_a_destination_receipt(self):
        tx = '0x' + 'c' * 64
        answer = dict(status='success', txHashes=[tx], destinationChainId=8453)
        moved = receipt([log(USDC_E, address(1), address(2), 9, 1, tx)], tx)
        self.assertEqual(links.relay_order_status(Fake(http={'https://api.relay.link/intents/status/v3': (200, answer)}, receipts={(8453, tx): moved}), self.ORDER)['state'], links.PROTOCOL_LINK_CONFIRMED)
        self.assertEqual(links.relay_order_status(Fake(http={'https://api.relay.link/intents/status/v3': (200, answer)}), self.ORDER)['state'], links.OFFCHAIN_RECORD_REQUIRED)

    def record(self, **kw):
        return dict(dict(fromChainId='1', fromTokenAddress=address(70), fromAmountBaseUnit='1000000000', toChainId='137', status='COMPLETED', txHash='0x' + 'd' * 64, createdTimeMs=(T0 - 600) * 1000), **kw)

    def test_a_bridge_record_verified_on_its_chain_is_confirmed_upstream_and_a_candidate_downstream(self):
        src, origin = address(5), address(6)
        tx = '0x' + 'd' * 64
        client = Fake(http={f'https://bridge.polymarket.com/status/{src}': (200, dict(transactions=[self.record()]))}, receipts={(1, tx): receipt([log(address(70), origin, src, 1000000000, 1, tx)], tx)})
        result = links.bridge_upstream(client, src, 995000000, T0)
        self.assertEqual(result['state'], links.CROSSCHAIN_CANDIDATE)
        self.assertEqual((result['relations'][0]['state'], result['relations'][0]['source']), (links.PROTOCOL_LINK_CONFIRMED, origin))

    def test_a_hash_not_found_on_its_chain_stays_a_candidate_and_says_so(self):
        src = address(5)
        client = Fake(http={f'https://bridge.polymarket.com/status/{src}': (200, dict(transactions=[self.record(), self.record(fromChainId='137', fromAmountBaseUnit='995000000')]))})
        result = links.bridge_upstream(client, src, 995000000, T0)
        self.assertEqual((result['state'], result['relations'], result['exact_same_chain_record']), (links.CROSSCHAIN_CANDIDATE, [], True))
        self.assertIn('not found', result['unverified'][0])

    def test_a_record_whose_receipt_disagrees_confirms_nothing(self):
        src = address(5)
        tx = '0x' + 'd' * 64
        client = Fake(http={f'https://bridge.polymarket.com/status/{src}': (200, dict(transactions=[self.record()]))}, receipts={(1, tx): receipt([log(address(70), address(6), src, 999, 1, tx)], tx)})
        result = links.bridge_upstream(client, src, 995000000, T0)
        self.assertEqual(result['relations'], [])
        self.assertIn('no transfer', result['unverified'][0])

    def test_no_comparable_record_is_insufficient(self):
        src = address(5)
        client = Fake(http={f'https://bridge.polymarket.com/status/{src}': (200, dict(transactions=[self.record(fromAmountBaseUnit='5')]))})
        self.assertEqual(links.bridge_upstream(client, src, 995000000, T0)['state'], links.INSUFFICIENT_EVIDENCE)


class RelayOnChain(unittest.TestCase):
    def client(self, payout_input, logs, origin=None, paid_by=links.RELAY_SOLVER, wallet=None):
        payout = '0x' + 'e' * 64
        receipts = dict(origin or {})
        if wallet:
            receipts[137, payout] = receipt([log(USDC_E, paid_by, wallet, 5, 1, payout)], payout)
        self.payout = payout

        class Chain(Fake):
            def rpc(inner, method, params, chain=137):
                if method == 'eth_getTransactionByHash':
                    return dict(input=payout_input)
                if method == 'eth_getLogs':
                    return logs
                raise AssertionError(method)
            def head(inner, chain=137):
                return 1000
            def block_time(inner, number, chain=137):
                return T0 + (number - 1000) * 12
        return Chain(receipts=receipts)

    def test_the_real_order_id_links_a_polygon_payout_to_its_origin(self):
        case = DATA['relay_link']
        client = self.client(case['payout_input'], case['escrow_logs'], {(1, case['origin_receipt']['transactionHash']): case['origin_receipt']}, wallet=case['wallet'])
        result = links.relay_origin_from_payout(client, self.payout, T0, case['wallet'], case['received_raw'], chains=(1,))
        self.assertEqual((result['state'], result['origin_sender']), (links.PROTOCOL_LINK_CONFIRMED, case['sender']))
        self.assertNotEqual(result['origin_submitter'], case['sender'])
        relation = result['relations'][0]
        self.assertEqual((relation['raw_meaning'], relation['received_raw'], relation['chain_id']), ('left_source_on_origin_chain', case['received_raw'], 1))
        self.assertEqual(relation['order_id'], result['order_id'])

    def test_a_copied_id_on_someone_elses_transfer_links_nothing(self):
        case = DATA['relay_link']
        client = self.client(case['payout_input'], case['escrow_logs'], {(1, case['origin_receipt']['transactionHash']): case['origin_receipt']}, paid_by=address(66), wallet=case['wallet'])
        self.assertIsNone(links.relay_origin_from_payout(client, self.payout, T0, case['wallet'], case['received_raw'], chains=(1,)))

    def test_a_service_that_paid_is_not_called_the_funder(self):
        from signal_engine.fund_flow.trace import last_origin
        solver = dict(address=links.RELAY_SOLVER, name='Relay EVM solver', tx='0x1', upstream=dict(state=links.OFFCHAIN_RECORD_REQUIRED))
        self.assertEqual((last_origin([solver])['funder_shown'], last_origin([solver])['is_service']), (False, True))
        proven = dict(solver, upstream=dict(state=links.PROTOCOL_LINK_CONFIRMED, origin_sender=address(5), origin_chain=1, origin_tx='0x2'))
        self.assertEqual((last_origin([proven])['address'], last_origin([proven])['chain_id']), (address(5), 1))

    def test_in_a_bundle_only_the_transfer_behind_this_escrow_log_counts(self):
        wallet, stranger, sender, token = address(1), address(2), address(3), address(70)
        order = 'cd' * 32
        tx = '0x' + 'f' * 64
        def escrow(payer, raw, identifier, index):
            return dict(address=RELAY_DEPOSITORY, topics=['0x49fed1d0b752ce30eee63c7a81133f3363b532fec5d4d7dd1ccfd005de4555e1'], data='0x' + word(payer).hex() + word(token).hex() + format(raw, '064x') + identifier, logIndex=hex(index), transactionHash=tx, blockNumber='0x10')
        logs = [log(token, stranger, RELAY_DEPOSITORY, 500, 1, tx), escrow(stranger, 500, 'ef' * 32, 2), log(token, sender, RELAY_DEPOSITORY, 700, 3, tx), escrow(sender, 700, order, 4)]
        client = self.client('0xa9059cbb' + word(wallet).hex() + format(1, '064x') + order, logs[1::2], {(1, tx): receipt(logs, tx)}, wallet=wallet)
        result = links.relay_origin_from_payout(client, self.payout, T0, wallet, '690', chains=(1,))
        self.assertEqual((result['origin_sender'], result['relations'][0]['raw']), (sender, '700'))

    def test_another_id_links_nothing(self):
        case = DATA['relay_link']
        other = case['payout_input'][:-64] + 'ab' * 32
        client = self.client(other, case['escrow_logs'], wallet=case['wallet'])
        self.assertIsNone(links.relay_origin_from_payout(client, self.payout, T0, case['wallet'], '1', chains=(1,)))

    def test_ordinary_calldata_is_not_an_order_id(self):
        plain = '0xa9059cbb' + word(address(1)).hex() + format(5, '064x')
        client = self.client(plain, [], wallet=address(1))
        self.assertIsNone(links.relay_origin_from_payout(client, self.payout, T0, address(1), '1', chains=(1,)))

    def test_the_block_search_converges_on_a_drifted_rate(self):
        class Drift:
            def head(self, chain=137):
                return 10 ** 6
            def block_time(self, number, chain=137):
                return T0 + number * 3
        block, _ = links.block_near(Drift(), 1, T0 + 500000 * 3, rate_s=12)
        self.assertLessEqual(abs(block - 500000) * 3, 300)


class RelayFills(unittest.TestCase):
    URL = 'https://api.relay.link/requests/v2'

    def answer(self, wallet, sender, origin):
        return (200, dict(requests=[dict(id='0xabc', status='success', recipient=wallet.upper().replace('0X', '0x'), user=sender, data=dict(metadata=dict(sender=sender, recipient=wallet), inTxs=[dict(chainId=1, hash=origin)]))]))

    def test_a_bundler_is_not_the_sender(self):
        wallet, sender, bundler = address(1), address(2), address(3)
        tx = '0x' + 'f' * 64
        origin = dict(receipt([log(address(70), sender, address(9), 100, 4, tx)], tx), **{'from': bundler})
        result = links.relay_fill_origin(Fake(http={self.URL: self.answer(wallet, sender, tx)}, receipts={(1, tx): origin}), '0x1', wallet)
        self.assertEqual((result['state'], result['origin_sender'], result['origin_submitter']), (links.PROTOCOL_LINK_CONFIRMED, sender, bundler))
        self.assertEqual(result['relations'][0]['source'], sender)

    def test_a_named_sender_the_receipt_does_not_show_stays_a_candidate(self):
        wallet, tx = address(1), '0x' + 'f' * 64
        origin = receipt([log(address(70), address(5), address(9), 100, 4, tx)], tx)
        result = links.relay_fill_origin(Fake(http={self.URL: self.answer(wallet, address(2), tx)}, receipts={(1, tx): origin}), '0x1', wallet)
        self.assertEqual((result['state'], result['relations']), (links.CROSSCHAIN_CANDIDATE, []))

    def test_a_record_for_someone_else_links_nothing(self):
        result = links.relay_fill_origin(Fake(http={self.URL: self.answer(address(8), address(2), '0xaa')}), '0x1', address(1))
        self.assertEqual(result['state'], links.INSUFFICIENT_EVIDENCE)

    def test_no_public_record_is_an_offchain_record(self):
        self.assertEqual(links.relay_fill_origin(Fake(http={self.URL: (429, None)}), '0x1', address(1))['state'], links.OFFCHAIN_RECORD_REQUIRED)


class ChangeNowAndMonero(unittest.TestCase):
    def test_four_levels_stay_apart(self):
        self.assertEqual(links.changenow_tier(labelled=True)['tier'], 1)
        self.assertEqual(links.changenow_tier(candidate=True)['state'], links.CROSSCHAIN_CANDIDATE)
        self.assertEqual(links.changenow_tier(record={}, record_verified=True)['tier'], 3)
        self.assertEqual(links.changenow_tier()['state'], links.OFFCHAIN_RECORD_REQUIRED)

    def swap(self, **kw):
        payin, payout = '0x' + '1' * 64, '0x' + '2' * 64
        return dict(dict(id='abc', record_source='exchange_api_authorized', payinHash=payin, payoutHash=payout, fromChainId=137, toChainId=1, payinAddress=address(7), payoutAddress=address(8), amountSendRaw=100, amountReceiveRaw=90, toCurrency='usdc'), **kw), {(137, payin): receipt([log(USDC_E, address(1), address(7), 100, 1, payin)], payin), (1, payout): receipt([log(USDC_E, address(9), address(8), 90, 1, payout)], payout)}

    def test_an_authorized_record_with_both_hashes_is_verified(self):
        record, receipts = self.swap()
        self.assertEqual(links.verify_exchange_record(Fake(receipts=receipts), record)['tier'], 3)

    def test_a_record_of_unknown_origin_or_a_wrong_amount_does_not_confirm(self):
        record, receipts = self.swap(record_source='pasted')
        self.assertEqual(links.verify_exchange_record(Fake(receipts=receipts), record)['state'], links.CROSSCHAIN_CANDIDATE)
        record, receipts = self.swap(amountReceiveRaw=91)
        result = links.verify_exchange_record(Fake(receipts=receipts), record)
        self.assertEqual(result['checks']['payout'], 'NOT_FOUND')
        self.assertNotEqual(result['state'], links.PROTOCOL_LINK_CONFIRMED)

    def test_a_swap_to_monero_stops_at_the_boundary(self):
        record, receipts = self.swap(toCurrency='XMR', payoutHash=None)
        result = links.verify_exchange_record(Fake(receipts=receipts), record)
        self.assertEqual((result['state'], result['tracing_continues']), (links.XMR_VISIBILITY_BOUNDARY, False))

    def test_a_later_transparent_exit_stays_independent(self):
        result = links.later_transparent_exit(dict(tx='0x1', address=address(1)))
        self.assertEqual((result['linked_to_monero_entry'], result['state']), (False, links.INSUFFICIENT_EVIDENCE))

    def test_spend_secrets_are_refused(self):
        for field in ('spend_key', 'seed', 'Mnemonic', 'wallet_password'):
            with self.assertRaises(ValueError):
                links.verify_monero_proof({field: 'x', 'kind': 'tx_key'})

    def test_a_proof_without_a_local_wallet_is_not_checked_and_goes_nowhere_else(self):
        self.assertEqual(links.verify_monero_proof(dict(kind='tx_key', txid='a'))['proof_verified'], False)
        with self.assertRaises(ValueError):
            links.verify_monero_proof(dict(kind='tx_key', txid='a'), 'https://node.example', post=lambda *_: {})

    def test_a_checked_proof_keeps_no_key_and_links_nothing(self):
        answer = dict(result=dict(received=7, confirmations=3))
        result = links.verify_monero_proof(dict(kind='tx_key', txid='t', tx_key='SECRETKEY', address='addr'), 'http://127.0.0.1:18082/json_rpc', post=lambda url, body: answer)
        self.assertTrue(result['proof_verified'])
        self.assertEqual(result['state'], links.XMR_VISIBILITY_BOUNDARY)
        self.assertNotIn('SECRETKEY', json.dumps(result))
        self.assertIn('links to no EVM flow', result['reading'])


class Graphs(unittest.TestCase):
    def edge(self, source, target, state=links.ONCHAIN_CONFIRMED, index=1, tx='0x1'):
        return links.relation(state, source, target, tx=tx, log_index=index, raw=5, basis='test')

    def test_one_edge_per_log_however_often_it_is_read(self):
        e = self.edge(address(1), address(2))
        self.assertEqual(len(graphs.build_graph([e, dict(e)])['edges']), 1)
        self.assertEqual(len(graphs.build_graph([e, self.edge(address(1), address(2), index=2)])['edges']), 2)

    def test_a_shared_bridge_router_or_exchange_makes_no_cluster(self):
        for shared in ('0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f', '0xe111180000d2663c0091e4f400237545b87b996b', ZERO):
            built = graphs.build_graph([self.edge(shared, address(1)), self.edge(shared, address(2), index=2)])
            self.assertEqual(graphs.clusters(built), [], shared)

    def test_a_high_fanout_address_becomes_a_question_and_links_nobody(self):
        hub = address(99)
        built = graphs.build_graph([self.edge(hub, address(i + 1), index=i) for i in range(graphs.FANOUT_LIMIT)])
        self.assertEqual(built['nodes'][hub]['kind'], 'POTENTIAL_INFRASTRUCTURE')
        self.assertEqual(graphs.clusters(built), [])

    def test_a_busy_address_under_the_limit_is_still_unknown_and_named_nothing(self):
        built = graphs.build_graph([self.edge(address(99), address(1))])
        self.assertEqual((built['nodes'][address(99)]['kind'], built['nodes'][address(99)]['name']), ('UNKNOWN', None))

    def test_a_cluster_says_why_and_never_who(self):
        built = graphs.build_graph([self.edge(address(1), address(2)), self.edge(address(2), address(1), index=2)], dict([(address(2), 'STUDIED_WALLET')]))
        found = graphs.clusters(built)
        self.assertEqual(found[0]['members'], [address(1), address(2)])
        self.assertEqual(found[0]['corroborating'][0]['kind'], 'TWO_WAY_TRANSFERS')
        self.assertEqual(found[0]['corroborating'][0]['tx'], '0x1')
        self.assertTrue(found[0]['alternatives'])
        self.assertEqual(found[0]['ownership'], links.OWNERSHIP)

    def test_a_solver_paying_two_wallets_links_neither(self):
        solver = '0xf70da97812cb96acdf810712aa562db8dfa3dbef'
        built = graphs.build_graph([self.edge(solver, address(1)), self.edge(solver, address(2), index=2), self.edge(address(1), solver, index=3)], {address(1): 'STUDIED_WALLET', address(2): 'STUDIED_WALLET'})
        self.assertEqual(graphs.clusters(built), [])

    def test_one_payment_groups_nobody(self):
        built = graphs.build_graph([self.edge(address(1), address(2))], dict([(address(2), 'STUDIED_WALLET')]))
        self.assertEqual(graphs.clusters(built), [])

    def test_a_candidate_never_joins_a_cluster(self):
        built = graphs.build_graph([self.edge(address(1), address(2), links.CROSSCHAIN_CANDIDATE), self.edge(address(2), address(1), links.CROSSCHAIN_CANDIDATE, index=2)])
        self.assertEqual(graphs.clusters(built), [])

    def test_control_on_chain_is_a_link_of_its_own_kind(self):
        built = graphs.build_graph([])
        found = graphs.clusters(built, [dict(owner=address(1), wallet=address(2), basis='OWNERS_READ_ONCHAIN')])
        self.assertTrue(found[0]['control_only'])


class AccidentalMatches(unittest.TestCase):
    def test_a_match_on_amount_and_time_is_only_a_candidate_and_ignores_the_same_owner(self):
        target = dict(owner='a', at=T0, amount=1000.0)
        pool = [dict(owner='b', at=T0 + 60, amount=995.0), dict(owner='a', at=T0 + 60, amount=995.0), dict(owner='c', at=T0 + 60, amount=500.0), dict(owner='d', at=T0 - 60, amount=995.0)]
        self.assertEqual([p['owner'] for p in links.candidate_matches(target, pool)], ['b'])

    def test_in_a_dense_pool_the_rule_finds_accidents_as_often_as_on_real_times(self):
        rng = random.Random(1)
        pool = [dict(owner=f'p{i}', at=T0 + rng.randrange(40 * 86400), amount=rng.choice((100.0, 500.0, 1000.0))) for i in range(40000)]
        targets = [dict(owner='t', at=T0 + 15 * 86400 + rng.randrange(5 * 86400), amount=1000.0) for _ in range(100)]
        result = links.chance_rate(targets, pool)
        self.assertEqual(result['control_rate'], 1.0)
        self.assertEqual(result['real_with_candidate'], 100)

    def test_the_control_is_reproducible(self):
        rng = random.Random(2)
        pool = [dict(owner=f'p{i}', at=T0 + rng.randrange(40 * 86400), amount=rng.uniform(10, 5000)) for i in range(2000)]
        targets = [dict(owner='t', at=T0 + 20 * 86400, amount=rng.uniform(10, 5000)) for _ in range(50)]
        self.assertEqual(links.chance_rate(targets, pool), links.chance_rate(targets, pool))


class ClientLimits(unittest.TestCase):
    def test_no_write_method_and_no_other_host(self):
        client = Client(pause_s=0)
        self.addCleanup(client.close)
        with self.assertRaises(ValueError):
            client.rpc('eth_sendRawTransaction', ['0x'])
        with self.assertRaises(ValueError):
            client.get_json('https://api.changenow.io/v2/exchange')

    def test_budget_stops_the_run(self):
        client = Client(rpc_limit=0, http_limit=0, pause_s=0)
        self.addCleanup(client.close)
        with self.assertRaises(BudgetExhausted):
            client.rpc('eth_chainId', [])
        with self.assertRaises(BudgetExhausted):
            client.get_json('https://bridge.polymarket.com/status/0x0')


if __name__ == '__main__':
    unittest.main()
