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
                                    "page": 0, "n_requests": len(orders), "fetched_utc": "2026-11-20T00:00:00Z",
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

    def test_two_copies_of_an_order_keep_the_later_state_whatever_the_file_order(self):
        old = dict(order("1", A, B), status="pending", updatedAt="2026-11-19T10:00:00Z")
        new = dict(order("1", A, B), status="success", updatedAt="2026-11-19T11:00:00Z")
        for i, pages in enumerate(({A: [new], B: [old]}, {A: [old], B: [new]})):
            root = Path(self.tmp.name, f"r{i}")
            root.mkdir()
            stats = {}
            self.assertEqual(rg.load(archive(root, pages), stats=stats)[2]["1"]["status"], "success")
            self.assertEqual(stats["orders_restated_between_reads"], 1)

    def test_copies_that_differ_only_in_valuations_are_one_order(self):
        first, second = order("1", A, B), order("1", A, B)
        second["data"]["metadata"]["currencyIn"]["amountUsdCurrent"] = "10.2"  # the API revalues at each read
        stats = {}
        labels, complete, orders = rg.load(archive(self.tmp.name, {A: [first], B: [second]}), stats=stats)
        self.assertEqual((len(orders), stats["orders_differing_in_valuations_only"], stats["orders_restated_between_reads"]), (1, 1, 0))
        third = order("1", A, B)
        third["data"]["slippageTolerance"] = "1"  # a field the module does not read, and not a valuation: counted apart
        root = Path(self.tmp.name, "other")
        root.mkdir()
        stats = {}
        rg.load(archive(root, {A: [first], B: [third]}), stats=stats)
        self.assertEqual((stats["orders_differing_in_valuations_only"], stats["orders_differing_in_other_unread_fields"]), (0, 1))

    def test_a_contradiction_with_the_same_update_time_is_refused(self):
        a, b = dict(order("1", A, B), updatedAt="t"), dict(order("1", A, B), status="refund", updatedAt="t")
        with self.assertRaises(ValueError):
            rg.load(archive(self.tmp.name, {A: [a], B: [b]}))

    def rewrite_manifest(self, root, edit):
        lines = [json.loads(line) for line in (root / "manifest.jsonl").read_text().splitlines()]
        edit(lines)
        (root / "manifest.jsonl").write_text("\n".join(map(json.dumps, lines)) + "\n")

    def test_a_history_with_a_missing_page_is_not_complete(self):
        root = archive(self.tmp.name, {A: [order("1", A, B)]})
        self.rewrite_manifest(root, lambda lines: lines[0].update(page=1))
        stats = {}
        self.assertEqual(rg.load(root, stats=stats)[1], set())
        self.assertEqual(stats["histories_with_page_gap"], 1)

    def test_a_non_200_page_does_not_complete_a_history(self):
        root = archive(self.tmp.name, {A: [order("1", A, B)]}, complete=False)
        self.rewrite_manifest(root, lambda lines: lines.append(
            {"kind": "user", "value": A, "status": 429, "page": 1, "complete": True, "file": "raw/none.gz", "sha256_body": "0" * 64}))
        self.assertEqual(rg.load(root)[1], set())

    def test_a_page_whose_order_count_differs_from_the_manifest_is_refused(self):
        root = archive(self.tmp.name, {A: [order("1", A, B)]})
        self.rewrite_manifest(root, lambda lines: lines[0].update(n_requests=2))
        with self.assertRaises(ValueError):
            rg.load(root)

    def test_a_frozen_manifest_is_read_instead_of_the_archive_one(self):
        root = archive(self.tmp.name, {A: [order("1", A, B)], B: [order("2", B, A)]})
        frozen = root / "frozen.jsonl"
        frozen.write_text((root / "manifest.jsonl").read_text().splitlines()[0] + "\n")
        self.assertEqual(rg.load(root, manifest=frozen)[1:], ({A}, {"1": order("1", A, B)}))

    def test_non_evm_addresses_keep_their_case(self):
        sol, other = "Ab" + "1" * 40, "aB" + "1" * 40
        self.assertEqual(rg.norm(sol), sol)
        self.assertNotEqual(rg.norm(sol), rg.norm(other))

    def test_via_pays_counts_every_account_the_address_pays(self):
        root = archive(self.tmp.name, {A: [order("1", A, C)], B: [order("2", C, B)], D: [order("3", C, D)]})
        edges = [e for e in rg.account_edges(rg.transfers(rg.load(root)[2]), {A, B, D}) if e["via"]]
        self.assertEqual({(e["to"], e["via_pays"]) for e in edges}, {(B, 2), (D, 2)})

    def test_an_address_that_pays_two_cohorts_is_shared_too(self):
        root = archive(self.tmp.name, {A: [order("1", C, A)], B: [order("2", C, B)]})
        shared = rg.shared_counterparties(rg.transfers(rg.load(root)[2]), {A: "one", B: "two"})
        self.assertEqual(set(shared), {C})

    def test_every_leg_of_a_transfer_is_read_as_recorded(self):
        row = rg.transfers({"1": order("1", A, B)})[0]
        self.assertEqual((row["in_chain"], row["out_chain"], row["amount_in"], row["amount_out"], row["symbol_in"], row["symbol_out"], row["usd_in"]),
                         (137, 1, "10.0", "9.9", "USDC", "USDT", "10"))

    def test_a_round_trip_is_not_a_via_pair(self):
        root = archive(self.tmp.name, {A: [order("1", A, C)], B: [order("2", C, A)]})
        self.assertEqual(rg.account_edges(rg.transfers(rg.load(root)[2]), {A, B}), [])

    def test_an_order_naming_two_recipients_is_reported(self):
        two = order("1", A, B)
        two["recipient"] = C  # the order's own field disagrees with its metadata
        self.assertEqual(rg.field_conflicts({"1": two, "2": order("2", A, B)}), ["1"])


if __name__ == "__main__":
    unittest.main()
