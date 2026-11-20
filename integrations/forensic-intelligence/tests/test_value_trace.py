"""Offline tests of value_trace.py on synthetic indexer pages. No network: http is never called, or is replaced."""
import csv
import json
import sys
import tempfile
import unittest
from decimal import Decimal as D
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import value_trace as tr  # noqa: E402

USDT = tr.TOKENS[('ethereum', 'USDT')][0]


def addr(n):
    return '0x' + f'{n:040x}'


S, E, X, A, B, Z = addr(1), addr(2), addr(3), '0x0d40' + 'a' * 32 + 'dcc1', addr(5), addr(6)
BAIT = '0x0d40' + 'b' * 32 + 'dcc1'  # shares the first and last four characters of A
SEED_TX = '0x' + f'{2:064x}'


def party(address, tag=None):
    return {'hash': address, 'name': None, 'is_contract': False, 'proxy_type': None, 'metadata': {'tags': [{'name': tag}]} if tag else None}


def item(n, sender, recipient, amount, token=USDT, tag=None):
    """Transfer number n: block n, log index n, transaction hash n, amount in whole tokens."""
    return {'transaction_hash': '0x' + f'{n:064x}', 'log_index': n, 'block_number': n, 'timestamp': f'2026-04-16T00:00:{n:02d}.000000Z',
            'from': party(sender), 'to': party(recipient, tag), 'token': {'address_hash': token},
            'total': {'value': str(amount * 10 ** 6), 'decimals': '6'}}


BASE = [item(1, X, S, 100), item(2, E, S, 300), item(3, S, A, 250), item(4, S, B, 150)]


def build(folder, ledgers, next_page=None, **overrides):
    """Write case.json and one saved page per address; next_page marks an address whose page says more exist."""
    case = {'chain': 'ethereum', 'token': 'USDT', 'start': S, 'seed_transactions': [SEED_TX], 'min_follow': '10',
            'max_depth': 3, 'max_addresses': 10, 'max_pages_per_address': 5, 'stop_fan_in': 25, **overrides}
    Path(folder, 'case.json').write_text(json.dumps(case))
    store = tr.Store(folder)
    for address, items in ledgers.items():
        page = {'items': items, 'next_page_params': {'index': 1} if address == next_page else None}
        store.save(f'ethereum_{address.lower()}_USDT_p000', 'test', json.dumps(page).encode())
    return store


def path_rows(outputs):
    return {(r['from'], r['to']): r for r in csv.DictReader(outputs['path.csv'].decode().splitlines())}


class TraceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = self.tmp.name
        self.addCleanup(self.tmp.cleanup)

    def test_two_conventions_and_exact_totals(self):
        build(self.dir, {S: BASE, A: [BASE[2]], B: [BASE[3]]})
        out = tr.compute(self.dir, offline=True)
        rows = path_rows(out)
        self.assertEqual((D(rows[(E, S)]['tracked_others_first']), rows[(E, S)]['recipient_status']), (300, 'seed'))
        # 100 of other funds sit in S: "others first" sends them out before any followed value
        self.assertEqual((D(rows[(S, A)]['tracked_others_first']), D(rows[(S, A)]['tracked_first'])), (150, 250))
        self.assertEqual((D(rows[(S, B)]['tracked_others_first']), D(rows[(S, B)]['tracked_first'])), (150, 50))
        for column in ('tracked_others_first', 'tracked_first'):  # each convention places exactly the seed amount
            self.assertEqual(D(rows[(S, A)][column]) + D(rows[(S, B)][column]), 300)
        node = json.loads(out['nodes.json'])['read'][0]
        self.assertEqual((node['address'], D(node['in_total']), D(node['out_total']), D(node['balance_from_ledger']), node['overdrawn']), (S, 400, 400, 0, False))

    def test_no_other_funds_means_conventions_agree(self):
        build(self.dir, {S: [BASE[1], item(3, S, A, 300)], A: [item(3, S, A, 300)]})
        row = path_rows(tr.compute(self.dir, offline=True))[(S, A)]
        self.assertEqual(row['tracked_others_first'], row['tracked_first'])

    def test_spoofed_token_zero_value_and_duplicates(self):
        fake = item(7, E, S, 999, token=addr(99))
        build(self.dir, {S: BASE + [fake, item(8, S, Z, 0)], A: [BASE[2]], B: [BASE[3]]})
        out = tr.compute(self.dir, offline=True)
        package = json.loads(out['package.json'])
        self.assertEqual(package['spoofed_token_items_skipped'], 1)
        self.assertEqual(package['edges'], 5)  # four transfers plus the zero-value log; S to A is in two pages, counted once
        self.assertNotIn((S, Z), path_rows(out))

    def test_lookalike_bait_is_flagged_and_kept_out_of_the_sender_count(self):
        build(self.dir, {S: BASE + [item(5, BAIT, S, 1)], A: [BASE[2]], B: [BASE[3]]})
        node = json.loads(tr.compute(self.dir, offline=True)['nodes.json'])['read'][0]
        self.assertEqual(node['lookalike_counterparties'], [sorted([A, BAIT])])
        self.assertEqual((node['senders'], node['senders_above_dust']), (3, 2))

    def test_stop_reasons(self):
        build(self.dir, {S: BASE}, stop_fan_in=1)  # two real senders: the recipients of S are not read
        self.assertEqual({r['recipient_status'] for k, r in path_rows(tr.compute(self.dir, offline=True)).items() if k[0] == S}, {'sender_commingled'})
        tagged = [BASE[0], BASE[1], item(3, S, A, 250, tag='Some Exchange: Hot Wallet'), BASE[3]]
        with tempfile.TemporaryDirectory() as other:
            build(other, {S: tagged, B: [BASE[3]]})
            out = tr.compute(other, offline=True)
            self.assertEqual(path_rows(out)[(S, A)]['recipient_status'], 'public_tag')
            end = json.loads(out['nodes.json'])['terminals'][0]  # the tagged recipient is where the followed value stops
            self.assertEqual((end['address'], end['status'], D(end['tracked_others_first']), D(end['tracked_first'])), (A, 'public_tag', 150, 250))
            self.assertEqual(json.loads(out['labels.json'])[A]['tags'], ['Some Exchange: Hot Wallet'])

    def test_page_cap_marks_the_ledger_incomplete(self):
        build(self.dir, {S: BASE, A: [BASE[2], item(9, A, Z, 200)], B: [BASE[3]]}, next_page=A, max_pages_per_address=1)
        rows = path_rows(tr.compute(self.dir, offline=True))
        self.assertEqual(rows[(S, A)]['recipient_status'], 'ledger_incomplete')
        self.assertNotIn((A, Z), rows)  # nothing is attributed out of a ledger that was not read to its first transfer

    def test_overdrawn_ledger_is_reported(self):
        build(self.dir, {S: [BASE[1], item(3, S, A, 900)], A: [item(3, S, A, 900)]})
        self.assertTrue(json.loads(tr.compute(self.dir, offline=True)['nodes.json'])['read'][0]['overdrawn'])

    def test_missing_or_altered_page_fails_closed(self):
        store = build(self.dir, {S: BASE, A: [BASE[2]]})
        with self.assertRaises(FileNotFoundError):  # B is needed and was never saved
            tr.compute(self.dir, offline=True)
        store.save(f'ethereum_{B}_USDT_p000', 'test', json.dumps({'items': [BASE[3]], 'next_page_params': None}).encode())
        tr.compute(self.dir, offline=True)
        raw = Path(self.dir, 'raw', f'ethereum_{B}_USDT_p000.json.gz')
        raw.write_bytes(tr.gzip.compress(b'{"items": [], "next_page_params": null}', mtime=0))
        with self.assertRaises(ValueError):
            tr.compute(self.dir, offline=True)

    def test_check_reproduces_bytes_and_detects_an_edit(self):
        build(self.dir, {S: BASE, A: [BASE[2]], B: [BASE[3]]})
        tr.write(self.dir, tr.compute(self.dir, offline=True))
        with self.assertRaises(SystemExit) as ok:
            tr.main(['value_trace.py', 'check', self.dir])
        self.assertEqual(ok.exception.code, 0)
        path = Path(self.dir, 'path.csv')
        path.write_text(path.read_text().replace('250.000000', '251.000000'))
        with self.assertRaises(SystemExit) as bad:
            tr.main(['value_trace.py', 'check', self.dir])
        self.assertEqual(bad.exception.code, 1)

    def test_replay_needs_the_exact_log_on_every_endpoint(self):
        build(self.dir, {S: BASE, A: [BASE[2]], B: [BASE[3]]})
        tr.write(self.dir, tr.compute(self.dir, offline=True))

        def topic(address):
            return '0x' + address[2:].rjust(64, '0')

        def fake_http(url, payload=None, tries=4):
            method, param = payload['method'], payload['params'][0]
            if method == 'eth_getBlockByNumber':
                return json.dumps({'result': {'timestamp': hex(1776297600 + int(param, 16))}}).encode()  # 2026-04-16T00:00:00Z plus n seconds
            n = int(param, 16)
            sender, recipient, amount = {2: (E, S, 300), 3: (S, A, 250), 4: (S, B, 150)}[n]
            if n == 4 and url.endswith('drpc.org'):
                amount = 151  # the second endpoint disagrees on one transfer
            log = {'logIndex': hex(n), 'address': USDT, 'topics': [tr.TRANSFER_TOPIC, topic(sender), topic(recipient)], 'data': hex(amount * 10 ** 6)}
            return json.dumps({'result': {'status': '0x1', 'blockNumber': hex(n), 'from': sender, 'to': USDT, 'logs': [log]}}).encode()

        real_http, tr.http = tr.http, fake_http
        self.addCleanup(setattr, tr, 'http', real_http)
        result = tr.replay(self.dir)
        self.assertEqual(sorted(v['ok'] for v in result.values()), [False, True, True])
        self.assertTrue(result[f'1:{SEED_TX}:2']['ok'])
        self.assertTrue(result[f"1:0x{3:064x}:3"]['holder_signed'])
        levels = {r['transaction_hash']: r['evidence_level'] for r in csv.DictReader(tr.compute(self.dir, offline=True)['evidence_edges.csv'].decode().splitlines())}
        self.assertEqual(levels[SEED_TX], 'ONCHAIN_CONFIRMED')
        self.assertEqual(levels['0x' + f'{4:064x}'], 'CANDIDATE')

    def test_rpc_retries_a_null_answer_and_returns_the_late_one(self):
        answers = [b'{"result": null}'] * 3 + [b'{"result": {"status": "0x1"}}']
        real_http, real_sleep = tr.http, tr.time.sleep
        tr.http, tr.time.sleep = (lambda url, payload=None, tries=4: answers.pop(0)), (lambda seconds: None)
        self.addCleanup(setattr, tr, 'http', real_http)
        self.addCleanup(setattr, tr.time, 'sleep', real_sleep)
        store = tr.Store(self.dir)
        self.assertEqual(tr.rpc(store, 'r', 'u', 'eth_getTransactionReceipt', ['0x1']), {'status': '0x1'})
        self.assertTrue(store.has('r'))  # the null answers were never saved as evidence

    def test_offline_rpc_fails_closed_on_a_missing_response(self):
        real_http = tr.http
        tr.http = lambda *a, **k: self.fail('offline rpc made a network call')
        self.addCleanup(setattr, tr, 'http', real_http)
        with self.assertRaises(FileNotFoundError):
            tr.rpc(tr.Store(self.dir), 'missing', 'u', 'eth_getTransactionReceipt', ['0x1'], offline=True)


if __name__ == '__main__':
    unittest.main()
