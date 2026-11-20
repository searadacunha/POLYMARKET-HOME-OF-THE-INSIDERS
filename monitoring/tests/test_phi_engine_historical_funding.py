"""Offline regression tests for historically accurate Polymarket funding links.

These tests explicitly separate latest metadata from account state at deposit blocks.
They use no network and do not rewrite accepted research or frozen data.
Run: cd monitoring && python3 -m unittest discover -s tests -v
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from phi_engine import chainfund, enrich, store
from phi_monitor import net

WALLET = "0x" + "11" * 20
FUNDER = "0x" + "22" * 20
TX = "0x" + "ab" * 32


def metadata(url, missing=False, service=False):
    address = url.split("addresses=")[1]
    if missing:
        return {"addresses": {}}
    return {"addresses": {address.upper().replace("0X", "0x"):
                          {"tags": [{"name": "Known service"}] if service else []}}}


def fake_rpc(historical_code="0x", historical_nonce="0xb",
             latest_code="0x60", latest_nonce="0x3e8", archive_error=False):
    calls = []
    receipt = {"blockNumber": "0x64", "logs": [chainfund._log(chainfund.USDC_E, FUNDER, WALLET, 5_000_000, 0)]}

    def rpc(method, params, urls=None):
        if method == "eth_getTransactionReceipt":
            return receipt
        if method == "eth_getLogs":
            return []
        if method in ("eth_getCode", "eth_getTransactionCount"):
            block = params[1]
            calls.append((method, block, urls))
            if block != "latest" and archive_error:
                raise net.SourceError("archive endpoint not available")
            if method == "eth_getCode":
                return historical_code if block != "latest" else latest_code
            return historical_nonce if block != "latest" else latest_nonce
        raise AssertionError(method)
    return rpc, calls


class HistoricalStateTests(unittest.TestCase):
    def test_two_states_for_same_address_are_not_shared(self):
        db = store.connect(":memory:")
        self.addCleanup(db.close)
        calls = []

        def rpc(method, params, urls=None):
            calls.append((method, params[1], urls))
            if method == "eth_getCode":
                return "0x" if params[1] == "0x64" else "0x6000"
            return "0xb" if params[1] == "0x64" else "0x1"
        a = enrich.describe_at(db, FUNDER, 100, rpc)
        b = enrich.describe_at(db, FUNDER, 200, rpc)
        self.assertEqual((a["is_contract"], a["nonce"], a["status"]), (0, 11, "ok"))
        self.assertEqual((b["is_contract"], b["nonce"], b["status"]), (1, 1, "ok"))
        self.assertEqual(len(calls), 4)
        self.assertTrue(all(c[2] == enrich.WIDE_RPC for c in calls))
        enrich.describe_at(db, FUNDER, 100, rpc)
        self.assertEqual(len(calls), 4)  # successful historical records are cached

    def test_archive_error_never_falls_back_to_latest(self):
        db = store.connect(":memory:")
        self.addCleanup(db.close)
        rpc, calls = fake_rpc(archive_error=True)
        result = enrich.describe_at(db, FUNDER, 100, rpc)
        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["nonce"])
        self.assertEqual(calls, [("eth_getCode", "0x64", enrich.WIDE_RPC)])

    def test_malformed_historical_response_is_unresolved(self):
        db = store.connect(":memory:")
        self.addCleanup(db.close)
        rpc, _ = fake_rpc(historical_nonce="not-hex")
        got = enrich.describe_at(db, FUNDER, 100, rpc)
        self.assertEqual((got["status"], got["is_contract"], got["nonce"]), ("unavailable", None, None))

    def test_missing_label_metadata_is_not_no_service_label(self):
        db = store.connect(":memory:")
        self.addCleanup(db.close)
        rpc, _ = fake_rpc(latest_code="0x", latest_nonce="0xb")
        enrich.describe(db, [FUNDER], rpc=rpc, get_json=lambda u: metadata(u, missing=True))
        enrich.describe_at(db, FUNDER, 100, rpc)
        tags = db.execute("select tags, tags_status from addresses where address=?", (FUNDER,)).fetchone()
        self.assertEqual(tuple(tags), (None, "unavailable"))
        self.assertFalse(enrich.person_like_at(db, FUNDER, 100))


class FundingLinkTests(unittest.TestCase):
    def test_historically_plain_key_can_link_despite_present_day_contract(self):
        db = store.connect(":memory:")
        self.addCleanup(db.close)
        rpc, calls = fake_rpc(historical_code="0x", historical_nonce="0xb",
                              latest_code="0x6000", latest_nonce="0x3e8")
        enrich.trace_funding(db, WALLET, [(1000, 5.0, TX)], rpc, metadata)
        self.assertEqual(db.execute("select root from links").fetchone()[0], FUNDER)
        self.assertEqual(db.execute("select is_contract from addresses where address=?",
                                    (FUNDER,)).fetchone()[0], 1)  # current-only diagnostic
        self.assertEqual(db.execute("select is_contract from historical_addresses where address=? and block=100",
                                    (FUNDER,)).fetchone()[0], 0)
        self.assertEqual({tag for _, tag, _ in calls}, {"latest", "0x64"})

    def test_historically_contract_does_not_link_even_if_now_key(self):
        db = store.connect(":memory:")
        self.addCleanup(db.close)
        rpc, _ = fake_rpc(historical_code="0x60", historical_nonce="0x2",
                          latest_code="0x", latest_nonce="0x2")
        enrich.trace_funding(db, WALLET, [(1000, 5.0, TX)], rpc, metadata)
        self.assertEqual(db.execute("select count(*) from links").fetchone()[0], 0)
        self.assertEqual(db.execute("select count(*) from inflows").fetchone()[0], 1)
        self.assertEqual(db.execute("select count(*) from deposits").fetchone()[0], 1)

    def test_unavailable_historical_state_cannot_create_a_shared_root(self):
        db = store.connect(":memory:")
        self.addCleanup(db.close)
        rpc, calls = fake_rpc(historical_code="0x", latest_code="0x",
                              latest_nonce="0x1", archive_error=True)
        enrich.trace_funding(db, WALLET, [(1000, 5.0, TX)], rpc, metadata)
        self.assertEqual(db.execute("select count(*) from links").fetchone()[0], 0)
        self.assertEqual(db.execute("select status from historical_addresses where address=?",
                                    (FUNDER,)).fetchone()[0], "unavailable")
        self.assertEqual(db.execute("select payer from deposits").fetchone()[0], FUNDER)
        self.assertFalse(any(method == "eth_getTransactionCount" and block == "0x64"
                             for method, block, _ in calls))

    def test_tagged_service_does_not_link_even_if_historical_key(self):
        db = store.connect(":memory:")
        self.addCleanup(db.close)
        rpc, _ = fake_rpc(historical_code="0x", historical_nonce="0xb",
                          latest_code="0x", latest_nonce="0xb")
        enrich.trace_funding(db, WALLET, [(1000, 5.0, TX)], rpc,
                             lambda u: metadata(u, service=True))
        self.assertEqual(db.execute("select count(*) from links").fetchone()[0], 0)


if __name__ == "__main__":
    unittest.main()
