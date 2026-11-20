import gzip
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import relay_graph as rg

A, B, C, D = "0x" + "a" * 40, "0x" + "b" * 40, "0x" + "c" * 40, "0x" + "d" * 40


def order(order_id, sender, recipient, usd="10"):
    return {"id": order_id, "status": "success", "user": sender, "recipient": recipient, "data": {
        "inTxs": [{"chainId": 137, "hash": "0xin" + order_id, "timestamp": 1}],
        "outTxs": [{"chainId": 1, "hash": "0xout" + order_id, "timestamp": 2}],
        "metadata": {"sender": sender, "recipient": recipient,
                     "currencyIn": {"amountFormatted": "10.0", "amountUsd": usd, "currency": {"symbol": "USDC"}},
                     "currencyOut": {"amountFormatted": "9.9", "currency": {"symbol": "USDT"}}}}}


def archive(root, pages, complete=True, corrupt=None):
    """pages: {address: [orders]}; writes queue.tsv, manifest.jsonl and raw/ like the archiver does."""
    root = Path(root)
    (root / "raw").mkdir()
    queue, manifest = [], []
    for address, orders in pages.items():
        body = json.dumps({"requests": orders}).encode()
        name = f"raw/user_{address}_p000.json.gz"
        (root / name).write_bytes(gzip.compress(body))
        queue.append(f"user\t{address}\t[cohort of {address[2]}] test")
        manifest.append(json.dumps({"kind": "user", "value": address, "status": 200, "file": name, "complete": complete,
                                    "sha256_body": "0" * 64 if corrupt == address else hashlib.sha256(body).hexdigest()}))
    (root / "queue.tsv").write_text("\n".join(queue) + "\n")
    (root / "manifest.jsonl").write_text("\n".join(manifest) + "\n")
    return root


class RelayGraphTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_direct_and_via_edges_and_what_is_not_a_transfer(self):
        direct, to_c, c_to_b, self_bridge = order("1", A.upper().replace("0X", "0x"), B), order("2", A, C), order("3", C, B), order("4", A, A)
        root = archive(self.tmp.name, {A: [direct, to_c, self_bridge], B: [direct, c_to_b]})
        labels, complete, orders = rg.load(root)
        self.assertEqual((set(labels), complete, set(orders)), ({A, B}, {A, B}, {"1", "2", "3", "4"}))  # order 1 once
        rows = rg.transfers(orders)
        self.assertEqual([r["order"] for r in rows], ["1", "2", "3"])  # the self bridge is not a transfer
        self.assertEqual(rows[0]["sender"], A)  # EVM addresses compare in lower case
        edges = rg.account_edges(rows, complete)
        self.assertEqual([(e["from"], e["to"], e["via"], e["orders"], e["orders_via"]) for e in edges],
                         [(A, B, None, ["1"], []), (A, B, C, ["2"], ["3"])])
        self.assertEqual(edges[1]["via_pays"], 1)

    def test_a_refunded_order_is_not_a_payment(self):
        refunded = dict(order("1", A, B), status="refund")
        root = archive(self.tmp.name, {A: [refunded, order("2", A, C)], B: [refunded], D: [dict(order("3", D, C), status="refund")]})
        labels, complete, orders = rg.load(root)
        rows = rg.transfers(orders)
        self.assertEqual(rg.account_edges(rows, complete), [])
        self.assertEqual(rg.shared_counterparties(rows, {A: "one", D: "two"}), {})

    def test_shared_counterparty_needs_two_cohorts(self):
        root = archive(self.tmp.name, {A: [order("1", A, C)], B: [order("2", B, C)], D: [order("3", D, C.replace("c", "e"))]})
        labels, complete, orders = rg.load(root)
        shared = rg.shared_counterparties(rg.transfers(orders), {A: "one", B: "two", D: "two"})
        self.assertEqual(shared, {C: {"one": {A: ["1"]}, "two": {B: ["2"]}}})
        self.assertEqual(rg.shared_counterparties(rg.transfers(orders), {A: "one", B: "one"}), {})

    def test_a_page_that_does_not_match_its_hash_is_refused(self):
        root = archive(self.tmp.name, {A: [order("1", A, B)]}, corrupt=A)
        with self.assertRaises(ValueError):
            rg.load(root)

    def test_an_incomplete_history_is_not_read(self):
        root = archive(self.tmp.name, {A: [order("1", A, B)]}, complete=False)
        self.assertEqual(rg.load(root)[1:], (set(), {}))


if __name__ == "__main__":
    unittest.main()
