"""The graph document and the offline page, on hand-written answers and hostile strings."""
import json
import re
import threading
import unittest
import urllib.request
from pathlib import Path
from tempfile import TemporaryDirectory

from phi_forensics import cluster, viz

W = ["0x" + f"{i:040x}" for i in (1, 2, 3)]
KEY, HOT, OUTSIDE = ("0x" + c * 40 for c in "17e")
USDC = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
HOSTILE = '"><img src=x onerror=alert(1)></script><script>alert(2)</script>' + chr(0x2028) + '&amp;'


def move(n, sender, receiver, amount=1_000_000, **extra):
    return {"tx": "0x" + f"{n:064x}", "log_index": n, "block": 100 + n, "ts": 1_760_000_000 + n, "token": USDC, "amount_raw": amount,
            "from": sender, "to": receiver, **extra}


ROWS = [move(1, KEY, W[0]), move(2, KEY, W[1]), move(3, HOT, W[1]), move(4, HOT, W[2]), move(5, W[0], W[2], 5_530_000)]
CLASSES = {KEY: {"kind": "key"}, HOT: {"kind": "labelled_service", "label": "exchange hot wallet"}}
COORDINATED = {"a": W[1], "b": W[2], "type": "CO_TIMING", "grade": cluster.COORDINATION, "evidence_count": 0, "evidence": []}


def links_answer():
    found = cluster.links(W, ROWS, CLASSES) + [COORDINATED]
    return {"wallets": W, "links": found, "clusters": cluster.clusters(W, found), "limits": ["set limit"]}


def funding_answer():
    return {"wallet": W[0], "deposits": {"returned": 1, "total": 3, "rows": [{**ROWS[0], "counterparty": KEY, "counterparty_kind": "key"}]},
            "withdrawals": [ROWS[4]], "counterparties": {KEY: CLASSES[KEY]}, "limits": ["funding limit"]}


def trace_answer():
    return {"start": W[2], "direction": "downstream", "at_block": 100, "nodes": {OUTSIDE: {"kind": "contract"}},
            "edges": [move(6, W[2], OUTSIDE, 2_000_000, hop=1)], "stops": [{"address": OUTSIDE, "reason": "contract", "hop": 1}],
            "payments_not_followed": 2, "limits": {"reading": "an edge is a payment"}}


def no_registry(address):
    return None


def page_payload(page):
    raw = re.search(r'<script type="application/json" id="graph-data">(.*?)</script>', page, re.S).group(1)
    return json.loads(raw)


class Document(unittest.TestCase):
    def setUp(self):
        self.doc = viz.graph_document(links_answer(), funding_answer(), trace_answer(), sources=["file.csv"], known=no_registry)

    def test_every_transfer_is_one_edge_and_nothing_is_invented(self):
        ids = [e["id"] for e in self.doc["edges"]]
        self.assertEqual(ids, [f"0x{n:064x}:{n}" for n in range(1, 7)])  # five from the links and the funding, one from the trace
        self.assertEqual(self.doc["timeline"], ids)
        payment = self.doc["edges"][4]
        self.assertEqual((payment["amount"], payment["amount_raw"], payment["direction"], payment["token_name"]),
                         ("5.530000", "5530000", "between_investigated", "USDC"))
        self.assertEqual(payment["time_utc"], "2025-10-09T08:53:25Z")
        self.assertNotIn("evidence_level", payment)
        self.assertEqual({e["direction"] for e in self.doc["edges"]}, {"deposit", "between_investigated", "withdrawal"})

    def test_every_node_is_accounted_for_with_its_class_or_unknown(self):
        nodes = {n["address"]: n for n in self.doc["nodes"]}
        self.assertEqual(set(nodes), set(W) | {KEY, HOT, OUTSIDE})
        self.assertEqual(nodes[KEY]["kind"], "key")
        self.assertEqual(nodes[OUTSIDE]["kind"], "contract")
        self.assertEqual(nodes[HOT]["kind"], "unknown")  # the links answer carries no class: none is assumed
        self.assertNotIn("label", nodes[HOT])
        self.assertEqual({a for a, n in nodes.items() if n["investigated"]}, set(W))

    def test_every_grade_and_cluster_is_carried_with_its_evidence(self):
        got = {(l["type"], l["grade"], l["style"]) for l in self.doc["links"]}
        self.assertEqual(got, {("DIRECT_TRANSFER", cluster.FINANCIAL, "solid"), ("COMMON_FUNDER", cluster.FINANCIAL, "solid"),
                               ("SHARED_SERVICE", cluster.NOT_A_LINK, "dashed"), ("CO_TIMING", cluster.COORDINATION, "dashed")})
        funder = next(l for l in self.doc["links"] if l["type"] == "COMMON_FUNDER")
        self.assertEqual((funder["via"], funder["edges"]), (KEY, [f"0x{1:064x}:1", f"0x{2:064x}:2"]))
        self.assertEqual([c["members"] for c in self.doc["clusters"]], [W])
        self.assertEqual(self.doc["clusters"][0]["grade"], cluster.FINANCIAL)

    def test_views_limits_and_stops_come_from_the_answers(self):
        self.assertEqual([(g["address"], g["transfers"], g["totals"]) for g in self.doc["funding_sources"]],
                         [(KEY, 2, {"USDC": "2.000000"}), (HOT, 2, {"USDC": "2.000000"})])
        self.assertEqual([g["address"] for g in self.doc["withdrawal_destinations"]], [OUTSIDE])
        self.assertIn(f"{W[0]}: 1 of 3 deposits are listed", self.doc["limits"])
        self.assertIn("set limit", self.doc["limits"])
        self.assertTrue(any("2 payments were not followed" in x for x in self.doc["limits"]))
        self.assertEqual(self.doc["stops"][0]["address"], OUTSIDE)
        self.assertEqual(self.doc["sources"], ["file.csv"])

    def test_an_empty_answer_gives_an_empty_document(self):
        doc = viz.graph_document({"wallets": [], "links": [], "clusters": []}, known=no_registry)
        self.assertEqual([doc[k] for k in ("nodes", "edges", "links", "clusters", "timeline")], [[], [], [], [], []])

    def test_bare_lists_of_links_and_clusters_are_accepted(self):
        found = cluster.links(W, ROWS, CLASSES)
        doc = viz.graph_document(found, cluster.clusters(W, found), known=no_registry)
        self.assertEqual(len(doc["links"]), len(found))
        self.assertEqual(len(doc["clusters"]), 1)

    def test_an_unknown_answer_is_refused(self):
        with self.assertRaises(ValueError):
            viz.graph_document({"rows": []})

    def test_the_registry_labels_a_known_address(self):
        doc = viz.graph_document({"wallets": [W[0], "0x" + "0" * 40], "links": []})
        zero = next(n for n in doc["nodes"] if n["address"] == "0x" + "0" * 40)
        self.assertEqual(zero["kind"], "mint")


class Styles(unittest.TestCase):
    def test_only_demonstrated_grades_are_solid(self):
        for grade in cluster.RANK:
            self.assertEqual(viz.link_style(grade), "solid" if grade in cluster.JOINING else "dashed", grade)
        self.assertEqual(viz.link_style("ANY_NEW_GRADE"), "dashed")

    def test_the_dashed_and_ring_classes_are_dashed_and_the_page_draws_them(self):
        self.assertRegex(viz.STYLE, r"\.dashed\{[^}]*stroke-dasharray")
        self.assertRegex(viz.STYLE, r"\.ring\{[^}]*stroke-dasharray")
        self.assertNotRegex(re.search(r"\.solid\{[^}]*\}", viz.STYLE).group(0), "dasharray")
        self.assertIn('l.style === "solid" ? (l.grade === CONTROL ? "solid control" : "solid") : "dashed"', viz.SCRIPT)

    def test_filters_default_to_demonstrated_relations(self):
        self.assertIn("show[g] = g === CONTROL || g === FINANCIAL;", viz.SCRIPT)

    def test_a_shared_service_is_never_a_line_between_its_users(self):
        start = viz.SCRIPT.index("if (l.grade === NOT_A_LINK) {")
        branch = viz.SCRIPT[start:viz.SCRIPT.index("} else {", start)]
        self.assertNotIn("xy(l.a)", branch)
        self.assertIn('"ring"', branch)


class Page(unittest.TestCase):
    def hostile_document(self):
        rows = [move(1, KEY, W[0]), move(2, KEY, W[1])]
        found = cluster.links(W[:2], rows, CLASSES)
        found[0]["note"] = HOSTILE
        funding = {"wallet": W[0], "deposits": [{**rows[0], "counterparty": KEY, "counterparty_kind": HOSTILE, "counterparty_label": HOSTILE,
                                                 "evidence_level": HOSTILE}], "limits": [HOSTILE]}
        return viz.graph_document({"wallets": W[:2], "links": found, "clusters": []}, funding, sources=[HOSTILE], known=no_registry)

    def test_hostile_strings_cannot_add_markup_or_script(self):
        page = viz.render_html(self.hostile_document(), title=HOSTILE)
        self.assertEqual(re.findall(r"<script[^>]*>", page), ['<script type="application/json" id="graph-data">', "<script>"])
        self.assertEqual(page.count("</script>"), 2)
        self.assertNotIn("<img", page)
        raw = re.search(r'id="graph-data">(.*?)</script>', page, re.S).group(1)
        self.assertNotIn(chr(0x2028), raw)  # a raw line separator ends a string in older JavaScript engines
        self.assertIn("&lt;img src=x onerror=alert(1)&gt;", page)  # the title, escaped
        payload = page_payload(page)
        self.assertEqual(payload["document"]["limits"], [HOSTILE])  # the data survive intact, as text
        self.assertNotIn("innerHTML", viz.SCRIPT)
        self.assertNotIn("insertAdjacentHTML", viz.SCRIPT)
        self.assertNotIn("document.write", viz.SCRIPT)

    def test_hostile_fields_get_no_recheck_command(self):
        edge = {"tx": "0x" + "a" * 64 + "; rm -rf /", "from": KEY, "to": W[0], "token": USDC, "amount": "1.000000"}
        self.assertIsNone(viz.verify_command(edge))
        edge = {**edge, "tx": "0x" + "a" * 64, "amount": "1; curl x", "log_index": True}
        self.assertEqual(viz.verify_command(edge), f"python3 -m phi_forensics verify_transfer --transaction 0x{'a' * 64} --sender {KEY} "
                                                   f"--recipient {W[0]} --token {USDC}")

    def test_the_page_loads_nothing_from_outside(self):
        page = viz.render_html(viz.graph_document(links_answer(), funding_answer(), trace_answer(), known=no_registry), "t")
        policy = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)">', page).group(1)
        for directive in ("default-src 'none'", "connect-src 'none'", "img-src 'none'", "font-src 'none'", "form-action 'none'", "base-uri 'none'"):
            self.assertIn(directive, policy)
        self.assertNotIn("unsafe-inline", policy)
        self.assertIn(viz._sha256(viz.SCRIPT), policy)
        self.assertIn(viz._sha256(viz.STYLE), policy)
        self.assertNotRegex(page, r"(?i)\s(src|href|srcset|action|poster)\s*=")
        self.assertNotRegex(page, r"(?i)@import|url\(\s*['\"]?http|<link|<iframe|<img|<object|<embed")
        for call in ("fetch(", "XMLHttpRequest", "WebSocket", "EventSource", "sendBeacon", "import(", "new Image", ".src ="):
            self.assertNotIn(call, viz.SCRIPT)
        urls = set(re.findall(r"https?://[^\"'\s<>)]+", page))
        self.assertEqual(urls, {"http://www.w3.org/2000/svg", "https://polygonscan.com/tx/"})  # a namespace and a plain anchor

    def test_same_input_gives_same_bytes(self):
        build = lambda: viz.render_html(viz.graph_document(links_answer(), funding_answer(), trace_answer(), known=no_registry), "t")
        self.assertEqual(build(), build())
        reordered = viz.graph_document(trace_answer(), funding_answer(), links_answer(), known=no_registry)
        self.assertEqual(reordered["edges"], viz.graph_document(links_answer(), funding_answer(), trace_answer(), known=no_registry)["edges"])

    def test_layout_puts_payers_left_and_payees_right(self):
        doc = viz.graph_document(links_answer(), trace_answer(), known=no_registry)
        place = viz.layout(doc)
        self.assertEqual({place[w][0] for w in W}, {0})
        self.assertEqual((place[KEY][0], place[HOT][0], place[OUTSIDE][0]), (-1, -1, 1))


class Command(unittest.TestCase):
    def test_build_writes_a_page_from_several_inputs(self):
        with TemporaryDirectory() as folder:
            first, second, out = Path(folder, "a.json"), Path(folder, "b.json"), Path(folder, "out.html")
            first.write_text(json.dumps(links_answer()))
            second.write_text(json.dumps({"answers": [funding_answer()], "sources": ["published.csv"]}))
            self.assertEqual(viz.main(["build", str(first), str(second), str(out), "--title", "Case"]), 0)
            payload = page_payload(out.read_text(encoding="utf-8"))
            self.assertEqual(payload["document"]["sources"], ["published.csv"])
            self.assertEqual(len(payload["document"]["edges"]), 5)

    def test_serve_binds_to_loopback_and_sends_the_policy(self):
        with TemporaryDirectory() as folder:
            Path(folder, "page.html").write_text("<!doctype html><title>x</title>", encoding="utf-8")
            httpd = viz.server(folder, port=0)
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            try:
                self.assertEqual(httpd.server_address[0], "127.0.0.1")
                with urllib.request.urlopen(f"http://127.0.0.1:{httpd.server_address[1]}/page.html", timeout=5) as answer:
                    self.assertEqual(answer.status, 200)
                    self.assertIn("connect-src 'none'", answer.headers["Content-Security-Policy"])
                    self.assertEqual(answer.headers["X-Content-Type-Options"], "nosniff")
            finally:
                httpd.shutdown()
                httpd.server_close()


if __name__ == "__main__":
    unittest.main()
