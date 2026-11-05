#!/usr/bin/env python3
"""Offline tests against code in the archived snapshot, without importing its collectors."""
from __future__ import annotations

import ast
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("changenow_fix", ROOT / "scripts/prepare_changenow_fix.py")
fix = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fix)
NET = (ROOT / "sources/code/net.py").read_text()
RECIPIENTS = (ROOT / "sources/code/ana_75_cn_recipients.py").read_text()


class FetchError(RuntimeError):
    pass


class CappedAPI:
    def __init__(self, rows):
        self.rows, self.calls = rows, []

    def __call__(self, url, params, secret=None):
        self.calls.append(dict(params))
        selected = [r for r in self.rows if params["startblock"] <= int(r["blockNumber"]) <= params["endblock"]]
        return {"status": "1", "result": selected[:min(params["offset"], 1000)]}


def records(n, per_block=1):
    return [{"blockNumber": str(i // per_block + 1), "test_id": i} for i in range(n)]


def collector(api, corrected=True):
    text = fix.patched_text("net.py", NET) if corrected else NET
    function = next(n for n in ast.parse(text).body if isinstance(n, ast.FunctionDef) and n.name == "es_all")
    env = {"get": api, "etherscan_key": lambda: "TEST_ONLY", "FetchError": FetchError}
    exec(compile(ast.Module(body=[function], type_ignores=[]), "net.py", "exec"), env)
    return env["es_all"]


def classify(funcs, address, chain, lab=None, tags=(), corrected=True):
    text = fix.patched_text("ana_75_cn_recipients.py", RECIPIENTS) if corrected else RECIPIENTS
    tree = ast.parse(text)
    assignments = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ("known_cn", "is_cn"):
                assignments[node.targets[0].id] = node
    decision = next(n for n in ast.walk(tree) if isinstance(n, ast.If) and isinstance(n.test, ast.Name) and n.test.id == "is_cn")
    nodes = [assignments["known_cn"], assignments["is_cn"], decision]
    env = {"funcs": funcs, "a": address, "c": chain, "lab": lab, "tags": tags,
           "cat": lab["category"] if lab else None, "n_cn": 0, "n_tag": 0}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "recipients.py", "exec"), env)
    return env["kind"]


class PaginationTests(unittest.TestCase):
    def test_original_silently_stops_at_1000(self):
        api = CappedAPI(records(2505))
        self.assertEqual(len(collector(api, False)(1, "tokentx")), 1000)
        self.assertEqual(len(api.calls), 1)

    def test_corrected_reads_all_2505(self):
        rows = records(2505)
        api = CappedAPI(rows)
        self.assertEqual(collector(api)(1, "tokentx"), rows)
        self.assertEqual(len(api.calls), 3)
        self.assertTrue(all(p["offset"] == 1000 for p in api.calls))

    def test_empty_and_short_pages(self):
        for n in (0, 1, 27, 999):
            with self.subTest(n=n):
                rows = records(n)
                self.assertEqual(collector(CappedAPI(rows))(1, "txlist"), rows)

    def test_exact_full_page(self):
        rows = records(1000)
        self.assertEqual(collector(CappedAPI(rows))(1, "txlist"), rows)

    def test_boundary_block_replayed(self):
        rows = records(2505, 7)
        self.assertEqual(collector(CappedAPI(rows))(1, "tokentx"), rows)

    def test_duplicate_legitimate_events_kept(self):
        rows = records(1500, 5)
        rows[998] = dict(rows[999])
        self.assertEqual(collector(CappedAPI(rows))(1, "tokentx"), rows)

    def test_dense_block_fails_closed(self):
        rows = [{"blockNumber": "42", "test_id": i} for i in range(1001)]
        with self.assertRaisesRegex(FetchError, "completeness unresolved"):
            collector(CappedAPI(rows))(137, "tokentx")

    def test_filters_preserved(self):
        api = CappedAPI(records(2505))
        out = collector(api)(137, "tokentx", "wallet", 9, 1507, "token")
        self.assertEqual(len(out), 1499)
        self.assertTrue(all(p["chainid"] == 137 and p["address"] == "wallet" and p["contractaddress"] == "token" for p in api.calls))

    def test_invalid_response_raises(self):
        with self.assertRaises(FetchError):
            collector(lambda *a, **k: {"result": "NOTOK"})(1, "tokentx")


class AttributionTests(unittest.TestCase):
    def setUp(self):
        self.address = "0xd51077510d57266a709d40fa53a8953d483b65d8"
        self.funcs = {"entry": {"address": self.address, "chain": 1, "level": "B2", "function": "AUTRE_SERVICE"}}
        self.lab = {"name": "Bybit: Deposit Address", "category": "exchange"}

    def test_original_overrides_service(self):
        self.assertEqual(classify(self.funcs, self.address, 1, self.lab, corrected=False), "INTERNE_CHANGENOW")

    def test_other_service_retained(self):
        self.assertEqual(classify(self.funcs, self.address, 1, self.lab), "SERVICE")

    def test_router_retained(self):
        self.assertEqual(classify(self.funcs, self.address, 1, {"name": "Metamask: Swap Router", "category": "dex_or_router"}), "SERVICE")

    def test_unattributed_neighbor_is_only_candidate(self):
        self.assertEqual(classify(self.funcs, self.address, 1), "CLIENT_CANDIDAT")

    def test_level_a_remains_internal(self):
        self.funcs["entry"]["level"] = "A"
        self.assertEqual(classify(self.funcs, self.address, 1), "INTERNE_CHANGENOW")

    def test_chain_scoped_membership(self):
        self.funcs["entry"]["level"] = "A"
        self.assertEqual(classify(self.funcs, self.address, 137), "CLIENT_CANDIDAT")

    def test_chain_and_address_normalized(self):
        self.funcs["entry"].update(level="A", chain="1", address=self.address.upper())
        self.assertEqual(classify(self.funcs, self.address, 1), "INTERNE_CHANGENOW")

    def test_explicit_changenow_label_retained(self):
        self.assertEqual(classify({}, self.address, 1, tags=["ChangeNOW: hot wallet"]), "INTERNE_CHANGENOW")


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "original"
        (self.project / "code").mkdir(parents=True)
        (self.project / "derived").mkdir()
        (self.project / "code/net.py").write_text(NET)
        (self.project / "code/ana_75_cn_recipients.py").write_text(RECIPIENTS)
        (self.project / "derived/cn_universe.csv").write_text("address,chain,sources\n")
        (self.project / "derived/cn_links.json").write_text('{"stale": true}')
        (self.project / "derived/cn_result.json").write_text('{"verdict": "NON_SOUTENU"}')
        (self.project / ".env").write_text("DO_NOT_COPY=private\n")
        self.output = Path(self.temp.name) / "new"

    def test_prepares_without_mutating_original_or_copying_stale_state(self):
        before = {p.relative_to(self.project): p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        result = fix.prepare(self.project, self.output)
        after = {p.relative_to(self.project): p.read_bytes() for p in self.project.rglob("*") if p.is_file()}
        self.assertEqual(before, after)
        self.assertFalse((self.output / "derived/cn_links.json").exists())
        self.assertFalse((self.output / "derived/cn_result.json").exists())
        self.assertFalse((self.output / ".env").exists())
        self.assertFalse(result["network_executed"])
        self.assertEqual(list((self.output / "raw/http").iterdir()), [])
        self.assertEqual((self.output / "code/net.py").read_text(), fix.patched_text("net.py", NET))
        self.assertIn("derived/census_trades.jsonl.gz", result["missing_optional_inputs"])

    def test_existing_output_refused(self):
        self.output.mkdir()
        with self.assertRaises(fix.FixError):
            fix.prepare(self.project, self.output)

    def test_nested_output_refused(self):
        with self.assertRaises(fix.FixError):
            fix.prepare(self.project, self.project / "output")

    def test_drift_refused_before_output_created(self):
        path = self.project / "code/net.py"
        path.write_text(NET.replace("offset=10000", "offset=500"))
        with self.assertRaises(fix.FixError):
            fix.prepare(self.project, self.output)
        self.assertFalse(self.output.exists())

    def test_symlink_input_refused(self):
        path = self.project / "derived/cn_universe.csv"
        path.unlink()
        path.symlink_to(self.project / ".env")
        with self.assertRaises(fix.FixError):
            fix.prepare(self.project, self.output)

    def test_missing_universe_refused(self):
        (self.project / "derived/cn_universe.csv").unlink()
        with self.assertRaises(fix.FixError):
            fix.prepare(self.project, self.output)

    def test_patch_idempotent(self):
        for name, text in (("net.py", NET), ("ana_75_cn_recipients.py", RECIPIENTS)):
            corrected = fix.patched_text(name, text)
            self.assertEqual(fix.patched_text(name, corrected), corrected)

    def test_unrelated_code_preserved(self):
        text = NET + "\n# Independent session addition.\n"
        self.assertTrue(fix.patched_text("net.py", text).endswith("# Independent session addition.\n"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
