"""Offline test of relay_check.py: one archived Relay request, receipts served by a stand-in for the network."""
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import relay_check  # noqa: E402
import value_trace as tr  # noqa: E402

USER, SOLVER, DEPOSITORY = '0x' + '1' * 40, '0x' + '2' * 40, '0x' + '3' * 40
USDC, USDT = tr.TOKENS[('polygon', 'USDC')][0], tr.TOKENS[('ethereum', 'USDT')][0]
PAY, DELIVER = '0x' + 'a' * 64, '0x' + 'b' * 64


def topic(address):
    return '0x' + address[2:].rjust(64, '0')


class RelayCheckTest(unittest.TestCase):
    def run_check(self, delivered_on_chain):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        archive, out = Path(tmp.name, 'archive'), Path(tmp.name, 'out')
        (archive / 'raw').mkdir(parents=True)
        request = {'id': '0x' + 'c' * 64, 'status': 'success', 'user': USER, 'recipient': USER, 'createdAt': '2026-04-15T04:12:31.493Z',
                   'data': {'inTxs': [{'chainId': 137, 'hash': PAY}], 'outTxs': [{'chainId': 1, 'hash': DELIVER}],
                            'metadata': {'currencyIn': {'currency': {'address': USDC.lower()}, 'amount': '1000'},
                                         'currencyOut': {'currency': {'address': USDT.lower()}, 'amount': '990'}}}}
        with gzip.open(archive / 'raw' / f'user_{USER}_p000.json.gz', 'wt') as handle:
            json.dump({'requests': [request]}, handle)

        def fake_http(url, payload=None, tries=4):
            if payload['method'] == 'eth_getBlockByNumber':
                return json.dumps({'result': {'timestamp': hex(1776226350)}}).encode()
            paying = payload['params'][0] == PAY
            log = {'address': USDC if paying else USDT, 'data': hex(1000 if paying else delivered_on_chain),
                   'topics': [tr.TRANSFER_TOPIC, topic(USER if paying else SOLVER), topic(DEPOSITORY if paying else USER)]}
            return json.dumps({'result': {'status': '0x1', 'blockNumber': hex(7), 'logs': [log]}}).encode()

        real_http, tr.http = tr.http, fake_http
        self.addCleanup(setattr, tr, 'http', real_http)
        return {r['side']: r for r in relay_check.check(str(archive), str(out), [USER])}

    def test_both_legs_verified_with_their_counterparties(self):
        rows = self.run_check(delivered_on_chain=990)
        self.assertEqual((rows['origin']['verified'], rows['origin']['counterparty']), ('true', DEPOSITORY))
        self.assertEqual((rows['destination']['verified'], rows['destination']['counterparty'], rows['destination']['time_utc']),
                         ('true', SOLVER, '2026-04-15T04:12:30Z'))

    def test_a_delivery_that_differs_from_the_record_is_not_verified(self):
        rows = self.run_check(delivered_on_chain=989)
        self.assertEqual((rows['origin']['verified'], rows['destination']['verified']), ('true', 'false'))


if __name__ == '__main__':
    unittest.main()
