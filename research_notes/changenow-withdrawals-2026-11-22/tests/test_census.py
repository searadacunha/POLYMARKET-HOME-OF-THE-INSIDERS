"""Offline tests of the collector's own helpers (no network: every remote read is replaced in the test)."""
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(HERE.parent / "scripts"))

import census  # noqa: E402
from changenow_weekly import chainio as io, collect  # noqa: E402

SOLVER = "0xf70da97812cb96acdf810712aa562db8dfa3dbef"
DEP = "0x" + "d1" * 20
OTHER = "0x" + "e1" * 20


class EoaTraders(unittest.TestCase):
    def setUp(self):
        self.saved, self.sleep = census.pm.net.get_json, census.time.sleep
        census.time.sleep = lambda s: None
        census._traders.clear()

    def tearDown(self):
        census.pm.net.get_json, census.time.sleep = self.saved, self.sleep
        census._traders.clear()

    def test_only_an_address_that_is_its_own_trading_account_counts(self):
        trader, keyholder, quiet = "0x" + "a1" * 20, "0x" + "a2" * 20, "0x" + "a3" * 20
        answers = {trader: [dict(proxy_wallet=trader)], keyholder: [dict(proxy_wallet="0x" + "99" * 20)], quiet: []}
        calls = []

        def fake(url, **kw):
            a = url.split("user=")[1].split("&")[0]
            calls.append(a)
            return dict(data=answers[a])

        census.pm.net.get_json = fake
        self.assertEqual(census.eoa_traders([trader, keyholder, quiet]), {trader})
        self.assertEqual(census.eoa_traders([trader]), {trader})
        self.assertEqual(calls.count(trader), 1)                      # asked once a run

    def test_an_answer_without_data_raises_instead_of_reading_as_no_trader(self):
        census.pm.net.get_json = lambda url, **kw: dict(error="busy")
        with self.assertRaises(census.pm.net.SourceError):
            census.eoa_traders(["0x" + "a4" * 20])


class SolverNativeFills(unittest.TestCase):
    def test_keeps_successful_value_sends_of_the_solver_into_deposit_addresses_once(self):
        def rows(chain, action, address, first, last):
            base = dict(blockNumber="10", blockHash="0xb", timeStamp="100", isError="0", traceId="")
            if action == "txlist":
                return [dict(base, hash="0xA", **{"from": SOLVER, "to": DEP, "value": "5"}),
                        dict(base, hash="0xB", **{"from": SOLVER, "to": OTHER, "value": "5"}),        # not a deposit address
                        dict(base, hash="0xC", **{"from": SOLVER, "to": DEP, "value": "0"}),          # no value
                        dict(base, hash="0xD", isError="1", **{"from": SOLVER, "to": DEP, "value": "5"}),
                        dict(base, hash="0xE", **{"from": OTHER, "to": DEP, "value": "5"}),           # not the solver
                        dict(base, hash="0xA", **{"from": SOLVER, "to": DEP, "value": "5"})]          # served twice
            return [dict(base, hash="0xF", traceId="0_1", **{"from": SOLVER, "to": DEP, "value": "7"})]
        saved, io.etherscan_rows = io.etherscan_rows, rows
        try:
            got = census.solver_native_fills(1, dict(first=1, last=20), {SOLVER}, {DEP})
        finally:
            io.etherscan_rows = saved
        self.assertEqual([(r["tx"], r["log_index"], r["raw"]) for r in got], [("0xa", -1, 5), ("0xf", -2, 7)])
        self.assertTrue(all(r["token"] == "native" and r["src"] == SOLVER for r in got))


class CompactInflows(unittest.TestCase):
    def test_only_rows_used_as_evidence_stay_on_disk_and_the_full_count_is_kept(self):
        wallet, key, exchange, light = "0x" + "a1" * 20, "0x" + "b1" * 20, "0x" + "c9" * 20, "0x" + "e2" * 20
        ramp = census.pm.PUSD
        rows = [dict(chain=137, block=b, tx=f"0x{b}", log_index=0, ts=b, src=s, dst=d, token=census.pm.USDC_E, raw=raw)
                for b, s, d, raw in ((1, ramp, light, 5), (2, wallet, light, 5), (3, exchange, light, 5), (4, wallet, key, 5), (5, wallet, light, 0))]
        with tempfile.TemporaryDirectory() as tmp:
            store = collect.Store(tmp, "2026-W01", 137)
            store.write("snd_in", 1, 9, rows)
            snd = dict(rows=len(rows))
            census.compact_snd(store, dict(first=1, last=9), {wallet}, {wallet: key}, snd)
            kept = [(r["src"], r["dst"]) for r in store.rows("snd_in")]
        self.assertEqual(kept, [(ramp, light), (wallet, light), (wallet, key)])
        self.assertEqual((snd["rows_read"], snd["rows_kept_as_evidence"]), (5, 3))


class WeekBlocks(unittest.TestCase):
    def test_a_closed_week_is_read_once_and_an_open_one_every_time(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = collect.Store(tmp, "2026-W01", 137)
            calls = []

            def fake(chain, week):
                calls.append(week)
                return dict(first=1, last=9, closed=len(calls) > 1, head=10, head_ts=0, rule="finalized")
            saved, io.week_blocks = io.week_blocks, fake
            try:
                self.assertFalse(census.week_blocks(store, 137, "2026-W01")["closed"])
                self.assertTrue(census.week_blocks(store, 137, "2026-W01")["closed"])
                self.assertTrue(census.week_blocks(store, 137, "2026-W01")["closed"])
            finally:
                io.week_blocks = saved
            self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
