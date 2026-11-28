"""The command line: the same tools as the server, one sub-command per tool, against tests/world.py and this checkout."""
import contextlib
import io
import json
import sys
import unittest
from unittest import mock

from phi_forensics import cli, sources
from phi_forensics.mcp import server
from phi_forensics.tests import world
from phi_forensics.tests.world import F, P, V, W, tx

TABLE = "investigations/data-completion-20261123/results/coverage_by_chain.csv"


class Cli(unittest.TestCase):
    def setUp(self):
        self.world = world.World()
        world.offline(self, self.world)
        patch = mock.patch.object(sources, "Sources", self.world.sources)
        patch.start()
        self.addCleanup(patch.stop)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = cli.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def answer(self, *argv):
        code, out, err = self.run_cli(*argv)
        self.assertEqual((code, err), (0, ""), err)
        return json.loads(out)

    def test_the_tools_listing_has_the_names_of_the_server(self):
        listed = self.answer("tools")
        self.assertEqual([t["name"] for t in listed], list(server.build().tools))
        self.assertEqual(len(listed), 21)
        self.assertTrue(all(t["title"] and t["description"] for t in listed))

    def test_a_string_argument(self):
        got = self.answer("investigate_wallet", "--wallet", W)
        self.assertEqual((got["wallet"], got["trading"]["trading_cash"]), (W, "42.500000"))
        self.assertIn("provenance", got)

    def test_a_boolean_flag(self):
        got = self.answer("reconstruct_positions", "--wallet", W, "--exact")
        self.assertEqual((got["amounts"], got["totals"]["net_trading_result"]), ("CHAIN", "159.400000"))  # see test_investigate

    def test_integer_arguments(self):
        # One hop from F: W is a contract, V and P are keys at the hop limit.
        got = self.answer("trace_address", "--address", F, "--direction", "downstream", "--at_block", "88000000", "--hops", "1")
        self.assertEqual([(s["address"], s["reason"]) for s in got["stops"]], [(W, "contract"), (V, "hop limit"), (P, "hop limit")])

    def test_an_array_argument(self):
        got = self.answer("link_wallets", "--wallets", W, V)
        self.assertEqual([l["type"] for l in got["links"]], ["COMMON_DESTINATION", "COMMON_FUNDER", "SHARED_SERVICE"])

    def test_a_json_object_argument(self):
        got = self.answer("query_dataset", "--path", TABLE, "--where", '{"status": "COMPLETE"}', "--columns", "dataset", "--limit", "2")
        self.assertEqual((got["rows"], got["rows_matched"], got["cut"]), ([{"dataset": "cohort logs"}, {"dataset": "1/changenow"}], 4, True))

    def test_generate_report_prints_markdown(self):
        code, out, err = self.run_cli("generate_report", "--wallet", V)
        self.assertEqual((code, err), (0, ""))
        self.assertTrue(out.startswith(f"# Wallet report: `{V}`\n"))
        self.assertIn("- Net trading result: **75.000000**", out)

    def test_invalid_arguments_exit_1_with_a_message(self):
        code, out, err = self.run_cli("investigate_wallet", "--wallet", "0x12")
        self.assertEqual((code, out), (1, ""))
        self.assertTrue(err.startswith("invalid arguments: arguments.wallet: does not match"), err)

    def test_a_tool_error_exits_1_with_a_message(self):
        self.world.fail_http("/v2/activity", 500, b"upstream down", times=10)
        code, out, err = self.run_cli("investigate_wallet", "--wallet", W)
        self.assertEqual((code, out), (1, ""))
        self.assertTrue(err.startswith("SourceError: HTTP 500"), err)
        self.assertNotIn("Traceback", err)

    def test_argparse_refusals_exit_2(self):
        for argv in (["no_such_command"], ["query_dataset", "--path", TABLE, "--where", "{not json"], ["trace_address", "--address", F]):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                cli.main(argv)
            self.assertEqual(caught.exception.code, 2, argv)

    def test_mcp_serves_the_same_tools_over_stdio(self):
        lines = [{"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-11-25"}},
                 {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}]
        stdin = io.TextIOWrapper(io.BytesIO("".join(json.dumps(m) + "\n" for m in lines).encode()))
        out = io.BytesIO()
        stdout = io.TextIOWrapper(out)  # kept: a collected wrapper closes the buffer under it
        with mock.patch.object(sys, "stdin", stdin), mock.patch.object(sys, "stdout", stdout):
            cli.main(["mcp"])
        answers = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual([a["id"] for a in answers], [1, 2])
        self.assertEqual([t["name"] for t in answers[1]["result"]["tools"]], list(server.build().tools))

    def test_an_integer_argument_of_zero_is_kept(self):
        code, _, err = self.run_cli("trace_address", "--address", F, "--direction", "upstream", "--at_block", "0")
        self.assertEqual((code, err), (0, ""))

    def test_the_check_command_of_the_report_keeps_log_index_zero(self):
        got = self.answer("verify_transfer", "--transaction", tx(4), "--recipient", V, "--log_index", "0")
        self.assertEqual(got["claim"], {"to": V, "log_index": 0})


    def test_graph_hands_over_to_the_offline_viewer(self):
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as folder:
            source, page = Path(folder) / "links.json", Path(folder) / "graph.html"
            source.write_text(json.dumps({"wallets": [W, V], "links": [], "clusters": [], "graph_mermaid": "graph LR", "limits": []}))
            with contextlib.redirect_stdout(io.StringIO()):
                code = cli.main(["graph", "build", str(source), str(page)])
            self.assertEqual(code or 0, 0)
            self.assertIn("<!doctype html>", page.read_text().lower())


if __name__ == "__main__":
    unittest.main()
