"""Historical payer-state regression tests: no present-day contamination of forensic links.

Run from monitoring/: python3 -m unittest discover -s tests -v
All network calls are mocked; no keys, API access, or historical archives are needed.
"""
import os
import sys
import unittest
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from phi_monitor import chain, collect, net, store  # noqa: E402


ADDR = "0x" + "1" * 40
PROXY = "0x" + "2" * 40


class HistoricalAccountKind(unittest.TestCase):
    def test_historical_key_stays_key_despite_later_contract_and_high_nonce(self):
        requests = []

        def rpc(method, params, **kwargs):
            requests.append((method, params, kwargs))
            self.assertEqual(params, [ADDR, "0x64"])
            self.assertEqual(kwargs["urls"], chain.WIDE_RPC)
            return "0x" if method == "eth_getCode" else "0x2"

        with mock.patch.object(net, "rpc", side_effect=rpc):
            got = chain.account_kind(ADDR, 100)
        self.assertEqual((got["kind"], got["nonce"], got["nonce_as_of"], got["code_as_of"]),
                         ("key", 2, 100, 100))
        self.assertEqual([x[0] for x in requests], ["eth_getCode", "eth_getTransactionCount"])

    def test_historical_contract_is_not_relabelled_by_current_code(self):
        with mock.patch.object(net, "rpc", side_effect=lambda method, params, **kw:
                               "0x60006000" if method == "eth_getCode" else "0x1"):
            got = chain.account_kind(ADDR, 150)
        self.assertEqual((got["kind"], got["nonce_as_of"]), ("contract", 150))

    def test_unavailable_code_fails_closed_without_latest_fallback(self):
        calls = []

        def rpc(method, params, **kw):
            calls.append(params[1])
            raise net.SourceError("archive state unavailable")

        with mock.patch.object(net, "rpc", side_effect=rpc):
            got = chain.account_kind(ADDR, 50)
        self.assertEqual(got["kind"], "unknown")
        self.assertIsNone(got["nonce"])
        self.assertEqual(calls, ["0x32"])

    def test_unavailable_nonce_fails_closed_without_latest_fallback(self):
        calls = []

        def rpc(method, params, **kw):
            calls.append((method, params[1]))
            if method == "eth_getCode":
                return "0x"
            raise net.SourceError("missing historical nonce")

        with mock.patch.object(net, "rpc", side_effect=rpc):
            got = chain.account_kind(ADDR, 64)
        self.assertEqual(got["kind"], "unknown")
        self.assertEqual(calls, [("eth_getCode", "0x40"), ("eth_getTransactionCount", "0x40")])

    def test_malformed_historical_response_is_not_assumed_to_be_a_key(self):
        with mock.patch.object(net, "rpc", side_effect=lambda method, params, **kw: None):
            got = chain.account_kind(ADDR, 20)
        self.assertEqual(got["kind"], "unknown")

    def test_explicit_live_lookup_remains_available(self):
        queries = []

        def rpc(method, params, **kw):
            queries.append((method, params[1]))
            return "0x" if method == "eth_getCode" else "0x3e8"

        with mock.patch.object(net, "rpc", side_effect=rpc):
            got = chain.account_kind(ADDR)
        self.assertEqual((got["kind"], got["nonce_as_of"], got["code_as_of"]),
                         ("high_volume_key", "latest", "latest"))
        self.assertEqual(queries, [("eth_getCode", "latest"), ("eth_getTransactionCount", "latest")])

    def test_live_source_error_is_not_silently_relabelled(self):
        with mock.patch.object(net, "rpc", side_effect=net.SourceError("offline")):
            with self.assertRaises(net.SourceError):
                chain.account_kind(ADDR)

    def test_zero_address_is_explicit_mint_without_rpc(self):
        with mock.patch.object(net, "rpc") as rpc:
            got = chain.account_kind(chain.ZERO, 42)
        self.assertEqual((got["kind"], got["nonce"]), ("mint", 0))
        rpc.assert_not_called()

    def test_invalid_historical_block_rejected(self):
        for block in (-1, False, "100"):
            with self.subTest(block=block):
                with self.assertRaises(ValueError):
                    chain.account_kind(ADDR, block)


class HistoricalFunding(unittest.TestCase):
    def test_state_cached_per_payer_and_block_not_per_payer_only(self):
        rows = [
            dict(tx="0x" + "a" * 64, log_index=0, block=10, ts=11, payer=ADDR, to=PROXY,
                 token=chain.USDC, amount=20.0),
            dict(tx="0x" + "b" * 64, log_index=0, block=10, ts=12, payer=ADDR, to=PROXY,
                 token=chain.USDC, amount=30.0),
            dict(tx="0x" + "c" * 64, log_index=0, block=20, ts=21, payer=ADDR, to=PROXY,
                 token=chain.USDC, amount=50.0),
        ]
        def account_kind(payer, block):
            return dict(kind="key", nonce=2) if block == 10 else dict(kind="contract", nonce=3)

        with store.connect(":memory:") as con:
            with (mock.patch.object(chain, "block_at", return_value=1),
                  mock.patch.object(chain, "transfers_to", return_value=rows),
                  mock.patch.object(chain, "account_kind", side_effect=account_kind) as classifier):
                output = collect.funding(con, PROXY, 0, 100, hops=0)
            self.assertEqual([(x["block"], x["payer_kind"], x["payer_nonce"]) for x in output],
                             [(10, "key", 2), (10, "key", 2), (20, "contract", 3)])
            self.assertEqual(classifier.call_count, 2)
            classifier.assert_any_call(ADDR, 10)
            classifier.assert_any_call(ADDR, 20)

    def test_unknown_historical_state_cannot_create_an_upstream_root(self):
        row = dict(tx="0x" + "d" * 64, log_index=0, block=10, ts=11, payer=ADDR,
                   to=PROXY, token=chain.USDC, amount=50.0)
        with store.connect(":memory:") as con:
            with (mock.patch.object(chain, "block_at", return_value=1),
                  mock.patch.object(chain, "transfers_to", return_value=[row]) as source,
                  mock.patch.object(chain, "account_kind", return_value=dict(kind="unknown", nonce=None))):
                output = collect.funding(con, PROXY, 0, 100, hops=1)
            self.assertEqual((output[0]["payer_kind"], output[0]["payer_nonce"]), ("unknown", None))
            self.assertEqual(source.call_count, 1)


if __name__ == "__main__":
    unittest.main()
