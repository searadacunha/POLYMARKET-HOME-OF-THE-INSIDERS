"""The 21 tools as mcp/server.py registers them, called through Server.handle in both protocol eras.

Live tools read tests/world.py through the real readers: the source reader each handler creates and the chain helpers that
call monitoring.phi_monitor.net.rpc are pointed at the world, and any real network request fails the test. Archive tools
read this checkout. Expected figures are worked out by hand from the scenario (see test_investigate.py for the ledgers).
"""
import builtins
import io
import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from phi_forensics import archive, cli, repository_root, sources
from phi_forensics.mcp import protocol, server
from phi_forensics.tests import world
from phi_forensics.tests.world import C1, C3, D, EXCHANGE, F, K, P, S, USDC_E, V, W, tx

NAMES = ["investigate_wallet", "reconstruct_positions", "trace_funding", "trace_address", "find_related_wallets", "link_wallets",
         "verify_transfer", "verify_fill", "generate_report", "investigate_market", "compare_traders", "profile_behaviour",
         "list_investigations", "search_findings", "find_address", "list_datasets", "query_dataset", "list_checks", "reproduce_check",
         "query_alerts", "server_status"]
ARCHIVE = {"list_investigations", "search_findings", "find_address", "list_datasets", "query_dataset", "list_checks", "reproduce_check",
           "query_alerts", "server_status"}
CHAIN_ONLY = {"trace_address", "verify_transfer", "verify_fill"}  # their reads are JSON-RPC calls, which provenance does not record
MODERN_META = {protocol.META_VERSION: protocol.MODERN, protocol.META_CAPABILITIES: {}}
TABLE = "investigations/data-completion-20261123/results/coverage_by_chain.csv"


def fake_run_check(root, name, timeout=600):
    return {"name": name, "passed": True, "seconds": 0.0, "output_tail": "ok"}


class Tools(unittest.TestCase):
    def setUp(self):
        self.world = world.World()
        world.offline(self, self.world)
        patch = mock.patch.object(sources, "Sources", self.world.sources)
        patch.start()
        self.addCleanup(patch.stop)
        self.logged = []
        self.server = self.build()

    def build(self):
        built = server.build()
        built.log, built.rate = self.logged.append, protocol.RateLimit(calls=10 ** 6)
        built.handle({"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-11-25", "capabilities": {}}})
        return built

    def call(self, name, arguments, modern=False, on=None):
        params = {"name": name, "arguments": arguments, **({"_meta": MODERN_META} if modern else {})}
        return (on or self.server).handle({"jsonrpc": "2.0", "id": 7, "method": "tools/call", "params": params})

    def ok(self, name, **arguments):
        """The structured answer, checked identical in the legacy and the 2026-07-28 form, with its provenance."""
        legacy, modern = self.call(name, arguments)["result"], self.call(name, arguments, modern=True)["result"]
        self.assertEqual((legacy["isError"], modern["isError"], modern["resultType"]), (False, False, "complete"),
                         legacy["content"][0]["text"][:300])
        self.assertNotIn("resultType", legacy)
        self.assertEqual(legacy["structuredContent"], modern["structuredContent"])
        got = legacy["structuredContent"]
        self.assertEqual(json.loads(legacy["content"][0]["text"]), got)
        provenance = got["provenance"]
        self.assertRegex(provenance["answers_sha256"], "^[0-9a-f]{64}$")
        self.assertEqual(provenance["read_utc"], "2026-05-28T20:27:40Z")
        self.assertEqual(len(provenance["first_answers"]), min(10, provenance["http_answers"]))
        self.assertEqual(provenance["http_answers"] == 0, name in ARCHIVE | CHAIN_ONLY, name)
        return got

    def refused(self, name, arguments):
        result = self.call(name, arguments)["result"]
        self.assertTrue(result["isError"])
        self.assertNotIn("structuredContent", result)
        self.assertNotIn("Traceback", result["content"][0]["text"])
        return result["content"][0]["text"]


class Live(Tools):
    def test_investigate_wallet(self):
        got = self.ok("investigate_wallet", wallet=W)
        self.assertEqual((got["trading"]["trading_cash"], got["trading"]["net_trading_result"], got["trading"]["markets_not_valued"]),
                         ("42.500000", None, 1))
        self.assertEqual([m["condition_id"] for m in got["largest_markets"]], [C1, C3, world.C2, world.E])
        self.assertEqual((got["owner_keys"], got["funding"]["deposits"], got["funding"]["withdrawals"]), ([K], 2, 1))
        self.assertEqual(len(got["limits"]), 7)

    def test_reconstruct_positions(self):
        got = self.ok("reconstruct_positions", wallet=W, exact=True, limit=2)
        # Markets by |net|: C1 140, then C3 -30 and C4 30 in ledger order, C2 19.4, the event 0.
        self.assertEqual((got["markets"]["returned"], got["markets"]["total"]), (2, 5))
        self.assertEqual([m["condition_id"] for m in got["markets"]["rows"]], [C1, C3])
        self.assertEqual((got["amounts"], got["totals"]["net_trading_result"]), ("CHAIN", "159.400000"))
        self.assertEqual(got["platform_positions_check"]["differ"], 0)
        past = self.ok("reconstruct_positions", wallet=W, as_of="2026-05-08T14:20:00Z")
        self.assertEqual((past["as_of_utc"], past["totals"]["net_trading_result"], past["markets"]["total"]),
                         ("2026-05-08T14:20:00Z", "131.000000", 2))
        self.assertTrue(past["limits"])

    def test_trace_funding(self):
        got = self.ok("trace_funding", wallet=W)
        self.assertEqual((got["deposits"]["returned"], got["deposits"]["total"]), (2, 2))
        self.assertEqual([r["counterparty"] for r in got["deposits"]["rows"]], [F, S])
        self.assertEqual(got["collateral_check"]["difference"], "5.000000")
        self.assertEqual(self.ok("trace_funding", wallet=W, full_history=True)["collateral_check"]["closes"], True)

    def test_trace_address(self):
        # F paid W 1000, V 200, P 70 after block 88 000 000. W is a contract: stop. V and P are keys: followed. V paid D 150 (hop
        # limit) and the exchange 25 (a protocol contract); P paid nobody.
        got = self.ok("trace_address", address=F, direction="downstream", at_block=88_000_000, hops=2)
        self.assertEqual([(e["tx"], e["to"], e["amount"], e["hop"]) for e in got["edges"]],
                         [(tx(2), W, "1000.000000", 1), (tx(4), V, "200.000000", 1), (tx(3), P, "70.000000", 1),
                          (tx(18), D, "150.000000", 2), (tx(11), EXCHANGE, "25.000000", 2)])
        self.assertEqual(got["stops"], [{"address": W, "reason": "contract", "hop": 1}, {"address": D, "reason": "hop limit", "hop": 2},
                                        {"address": EXCHANGE, "reason": "CTF Exchange (2026)", "hop": 2}])
        self.assertEqual(got["payments_not_followed"], 0)
        self.assertIn("reading", got["limits"])

    def test_find_related_wallets(self):
        got = self.ok("find_related_wallets", wallet=W)
        self.assertEqual([(c["address"], c["via"]) for c in got["candidates"]], [(V, F), (P, F)])
        self.assertEqual([s["address"] for s in got["shared_services_ignored"]], [D])
        self.assertEqual(len(got["limits"]), 3)

    def test_link_wallets(self):
        got = self.ok("link_wallets", wallets=[V, W])
        self.assertEqual([(l["type"], l["grade"]) for l in got["links"]],
                         [("COMMON_DESTINATION", "FINANCIAL_RELATION_DEMONSTRATED"), ("COMMON_FUNDER", "FINANCIAL_RELATION_DEMONSTRATED"),
                          ("SHARED_SERVICE", "NOT_A_LINK")])
        self.assertEqual(got["clusters"][0]["members"], [W, V])

    def test_verify_transfer(self):
        claim = {"transaction": tx(2), "sender": F, "recipient": W, "amount": "1000", "log_index": 0}
        got = self.ok("verify_transfer", **claim)
        self.assertEqual((got["verdict"], got["nodes_agreeing"], got["block"], got["time_utc"]),
                         ("CONFIRMED", 2, 88_000_000, "2026-04-12T13:20:00Z"))
        self.assertEqual(got["matching_logs"], [{"token": USDC_E, "from": F, "to": W, "amount": "1000000000", "log_index": 0}])
        self.assertEqual(self.ok("verify_transfer", **{**claim, "amount": "999.999999"})["verdict"], "NOT_IN_RECEIPT")
        self.assertEqual(self.ok("verify_transfer", **{**claim, "transaction": tx(99)})["verdict"], "NOT_FOUND")
        one, two = server.evidence.ENDPOINTS
        self.world.unknown_on = {one}
        self.assertEqual(self.ok("verify_transfer", **claim)["verdict"], "SEEN_ON_ONE_NODE")
        self.world.unknown_on, self.world.tamper_on = set(), {two}
        self.assertEqual(self.ok("verify_transfer", **claim)["verdict"], "ENDPOINTS_DISAGREE")
        self.world.tamper_on = set()
        self.world.fail_rpc("eth_getTransactionReceipt")
        self.assertEqual(self.ok("verify_transfer", **claim)["verdict"], "UNREACHABLE")

    def test_verify_fill(self):
        got = self.ok("verify_fill", transaction=tx(7), wallet=W, side="BUY")
        self.assertEqual((got["verdict"], got["fills_in_receipt"]), ("CONFIRMED", 1))
        self.assertEqual(got["matching_logs"], [{"log_index": 2, "exchange": EXCHANGE, "version": "v2", "wallet": W, "counterparty": EXCHANGE,
                                                 "side": "BUY", "token_id": "101", "shares_raw": "200000000", "cash_raw": "60000000",
                                                 "fee_raw": "0"}])
        self.assertEqual(self.ok("verify_fill", transaction=tx(7), wallet=W, side="SELL")["verdict"], "NOT_IN_RECEIPT")

    def test_generate_report(self):
        got = self.ok("generate_report", wallet=V)
        self.assertEqual((got["wallet"], got["format"]), (V, "markdown"))
        self.assertTrue(got["report"].startswith(f"# Wallet report: `{V}`"))
        self.assertIn("**75.000000**", got["report"])

    def test_investigate_market(self):
        got = self.ok("investigate_market", condition=C1, limit=1)
        self.assertEqual((got["market"]["resolved"], got["market"]["payouts"]), (True, ["1", "0"]))
        # Price points of token 101: 0.30, 0.80, 0.90, 0.95; only the last two are within six hours (20 000 s): a rise of 0.05.
        path = got["price_path"]
        self.assertEqual((path["points"], path["min"], path["max"], path["largest_rise"]["change"], path["largest_fall"]),
                         (4, 0.3, 0.95, 0.05, None))
        self.assertEqual(path["largest_rise"]["start"]["ts"], 1_778_240_000)
        self.assertEqual([(h["token_id"], h["listed_total"], h["top_1_share"]) for h in got["holders"]],
                         [("101", "400.000000", 0.75), ("102", "0.000000", None)])
        lines = got["trades"]["by_wallet_outcome"]
        self.assertEqual((lines["returned"], lines["total"], got["trades"]["rows"]), (1, 2, 2))
        self.assertEqual({k: lines["rows"][0][k] for k in ("proxy_wallet", "cash_bought", "shares_bought", "average_buy_price")},
                         {"proxy_wallet": W, "cash_bought": "60.000000", "shares_bought": "200.000000", "average_buy_price": "0.300000"})
        # Before 1 778 240 000 only W had bought (V bought at 1 778 300 000): 200 shares, 1 840 000 seconds ahead.
        early = got["positioned_before_move"]
        self.assertEqual((early["reference_utc"], early["outcome"], early["wallets"]["total"]), ("2026-05-08T11:33:20Z", "Yes", 1))
        self.assertEqual({k: early["wallets"]["rows"][0][k] for k in ("proxy_wallet", "net_shares", "net_cash_paid", "lead_seconds")},
                         {"proxy_wallet": W, "net_shares": "200.000000", "net_cash_paid": "60.000000", "lead_seconds": 1_840_000})
        self.assertEqual(len(got["limits"]), 6)

    def test_compare_traders(self):
        got = self.ok("compare_traders", wallets=[W, V])
        pair = got["pairs"][0]
        # W traded C1, C2 and C3, V only C1: one market of three in common, both net buyers of its Yes, buys 1 900 000 s apart.
        self.assertEqual((pair["markets_both"], pair["jaccard"], pair["same_side_net_buys"]),
                         ([C1], 0.333333, [{"condition_id": C1, "outcome_index": 0}]))
        self.assertEqual((pair["bought_within_60s"], pair["bought_within_600s"], pair["shared_transactions"]["count"]), (0, 0, 0))
        self.assertEqual([(s["wallet"], s["rows"], s["trade_rows"], s["markets"]) for s in got["wallets"]], [(W, 7, 4, 3), (V, 2, 1, 1)])
        self.assertEqual((got["co_timing_null"]["available"], got["co_timing_null"]["buys_used"]), (True, 4))

    def test_profile_behaviour(self):
        got = self.ok("profile_behaviour", wallet=W)
        profile = got["profile"]
        # Buys: 60 (tx 7), 40 (tx 8), 30 (tx 14); one sale of 22.5. Only C1 is resolved: its Yes, bought at 0.3, won.
        self.assertEqual((profile["buys"], profile["sells"], profile["cash_bought"], profile["cash_sold"], profile["markets"]),
                         (3, 1, "130.000000", "22.500000", 4))
        record = profile["track_record"]
        self.assertEqual((record["resolved_markets"], record["wins"], record["skipped_markets"]), (1, 1, {"not_resolved": 2}))
        self.assertAlmostEqual(record["p_at_least_these_wins"], 0.3)
        self.assertEqual({s["decision"] for s in got["changes"]["series"].values()}, {"INSUFFICIENT_DATA"})
        self.assertEqual(len(got["limits"]), 2)


class Archive(Tools):
    def test_archive_tools_read_the_checkout(self):
        self.assertTrue(self.ok("list_investigations")["investigations"])
        found = self.ok("search_findings", level="CONFIRMED", limit=2)
        self.assertLessEqual(len(found["findings"]), 2)
        self.assertEqual({f["level"] for f in found["findings"]}, {"CONFIRMED"})
        self.assertGreaterEqual(self.ok("find_address", address=S.upper().replace("0X", "0x"))["files_total"], 1)
        listed = self.ok("list_datasets", text="coverage_by_chain")
        self.assertEqual((listed["matched"], listed["datasets"][0]["path"]), (1, TABLE))
        rows = self.ok("query_dataset", path=TABLE, where={"status": "PARTIAL"}, columns=["dataset", "records"])
        self.assertEqual((rows["rows"], rows["rows_scanned"], rows["rows_matched"]),
                         ([{"dataset": "1/changenow_native", "records": "121116"}], 5, 1))
        self.assertTrue(all(c["name"] and c["command"] for c in self.ok("list_checks")["checks"]))
        alerts = self.ok("query_alerts", limit=1)
        self.assertEqual(len(alerts["tables"]), 2)
        self.assertTrue(all(len(t["alerts"]) <= 1 for t in alerts["tables"]))
        status = self.ok("server_status")
        self.assertEqual((status["read_only"], status["archive_tools_available"], status["repository_checkout"]),
                         (True, True, str(repository_root())))

    def test_reproduce_check_runs_only_a_named_step(self):
        with mock.patch.object(archive, "run_check", fake_run_check):
            built = self.build()
        got = self.call("reproduce_check", {"name": "Verify archived Relay trace"}, on=built)["result"]["structuredContent"]
        self.assertEqual((got["name"], got["passed"]), ("Verify archived Relay trace", True))
        self.assertIn("ValueError: not an offline step", self.refused("reproduce_check", {"name": "rm -rf /"}))


class Refusals(Tools):
    def test_bad_missing_and_unknown_arguments(self):
        self.assertIn("does not match", self.refused("investigate_wallet", {"wallet": "0x123"}))
        self.assertIn("arguments.wallet: required", self.refused("investigate_wallet", {}))
        self.assertIn("arguments.zzz: unknown argument", self.refused("investigate_wallet", {"wallet": W, "zzz": 1}))
        self.assertIn("expected boolean", self.refused("reconstruct_positions", {"wallet": W, "exact": "yes"}))
        self.assertIn("out of range", self.refused("trace_address", {"address": F, "direction": "upstream", "at_block": -1}))
        for modern in (False, True):
            answer = self.call("no_such_tool", {}, modern=modern)
            self.assertEqual(answer["error"]["code"], protocol.INVALID_PARAMS)

    def test_a_source_failure_is_a_tool_error_without_a_traceback(self):
        self.world.fail_http("/v2/activity", 500, b"upstream down", times=10)
        self.assertTrue(self.refused("investigate_wallet", {"wallet": W}).startswith("SourceError: HTTP 500"))
        self.world.fail_rpc("eth_getLogs")
        self.assertIn("SourceError", self.refused("trace_funding", {"wallet": V}))
        self.assertEqual(self.logged, [])

    def test_a_refusal_of_the_question_itself(self):
        self.assertEqual(self.refused("link_wallets", {"wallets": [W, W]}), "ValueError: give between 2 and 25 wallets")
        self.assertEqual(self.refused("profile_behaviour", {"wallet": F}), "this wallet has no activity row")

    def test_a_malformed_answer_is_reported_and_the_traceback_only_logged(self):
        self.world.fail_http("/v2/positions", 200, b'{"data": [{"current_size": 1}], "pagination": {}}')
        self.assertEqual(self.refused("reconstruct_positions", {"wallet": V}), "the tool failed (KeyError); nothing was returned")
        self.assertIn("Traceback", self.logged[0])


class Catalogue(Tools):
    def test_the_tool_list_is_the_documented_one(self):
        for modern in (False, True):
            params = {"_meta": MODERN_META} if modern else {}
            listed = self.server.handle({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": params})["result"]["tools"]
            self.assertEqual([t["name"] for t in listed], NAMES)
            for tool in listed:
                self.assertEqual({k: tool["annotations"][k] for k in ("readOnlyHint", "destructiveHint", "idempotentHint")},
                                 {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True}, tool["name"])
                self.assertEqual(tool["annotations"]["openWorldHint"], tool["name"] not in ARCHIVE, tool["name"])
                self.assertIs(tool["inputSchema"]["additionalProperties"], False)
                self.assertEqual(protocol.validate({"not_an_argument": 1}, tool["inputSchema"])[-1], "arguments.not_an_argument: unknown argument")
        self.assertEqual(len(NAMES), 21)

    def test_every_tool_the_documentation_names_exists(self):
        named = set(re.findall(r"\b[a-z]+(?:_[a-z]+)+\b", server.INSTRUCTIONS)) | set(re.findall(r"-m phi_forensics (\w+)", cli.__doc__))
        named |= set(re.findall(r"-m phi_forensics (\w+)", Path(server.report.__file__).read_text(encoding="utf-8")))
        self.assertTrue(named)
        self.assertLessEqual(named - {"mcp", "tools", "graph"}, set(NAMES))   # graph is the offline viewer, not a tool

    def test_no_handler_writes_a_file(self):
        writes = []
        real_open = builtins.open

        def guarded(file, mode="r", *args, **kwargs):
            if any(flag in mode for flag in "wax+"):
                writes.append((str(file), mode))
                raise PermissionError(f"write refused in a read-only tool: {file}")
            return real_open(file, mode, *args, **kwargs)

        calls = [("investigate_wallet", {"wallet": W}), ("reconstruct_positions", {"wallet": W, "exact": True}), ("trace_funding", {"wallet": V}),
                 ("trace_address", {"address": F, "direction": "downstream", "at_block": 88_000_000}), ("find_related_wallets", {"wallet": V}),
                 ("link_wallets", {"wallets": [W, V]}), ("verify_transfer", {"transaction": tx(2)}),
                 ("verify_fill", {"transaction": tx(7), "wallet": W}),
                 ("generate_report", {"wallet": W}), ("investigate_market", {"condition": C1}), ("compare_traders", {"wallets": [W, V]}),
                 ("profile_behaviour", {"wallet": V}), ("list_investigations", {}), ("search_findings", {"limit": 1}),
                 ("find_address", {"address": S}),
                 ("list_datasets", {"limit": 1}), ("query_dataset", {"path": TABLE}), ("list_checks", {}), ("reproduce_check", {"name": "x"}),
                 ("query_alerts", {"limit": 1}), ("server_status", {})]
        self.assertEqual([name for name, _ in calls], NAMES)
        with mock.patch.object(archive, "run_check", fake_run_check):
            built = self.build()
        with tempfile.TemporaryDirectory() as home:
            here = os.getcwd()
            try:
                os.chdir(home)
                with (mock.patch.dict(os.environ, {"HOME": home}), mock.patch.object(builtins, "open", guarded),
                      mock.patch.object(io, "open", guarded)):
                    for name, arguments in calls:
                        result = self.call(name, arguments, on=built)["result"]
                        self.assertFalse(result["isError"], (name, result["content"][0]["text"][:200]))
            finally:
                os.chdir(here)
            self.assertEqual((writes, os.listdir(home)), ([], []))

    def test_archive_tools_leave_no_bytecode_behind(self):
        root = str(repository_root())
        with tempfile.TemporaryDirectory() as prefix:
            saved = (sys.dont_write_bytecode, sys.pycache_prefix)
            sys.dont_write_bytecode, sys.pycache_prefix = False, prefix  # a cold cache elsewhere: whatever is written lands here
            archive._script.cache_clear()
            try:
                for name, arguments in (("list_investigations", {}), ("list_checks", {}), ("compare_traders", {"wallets": [W, V]})):
                    self.assertFalse(self.call(name, arguments)["result"]["isError"])
            finally:
                sys.dont_write_bytecode, sys.pycache_prefix = saved
                archive._script.cache_clear()
            written = [str(p) for p in Path(prefix).rglob("*.pyc") if root.lstrip("/") in str(p)]
        self.assertEqual(written, [])


if __name__ == "__main__":
    unittest.main()
