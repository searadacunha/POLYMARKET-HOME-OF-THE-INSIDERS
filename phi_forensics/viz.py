"""An offline, self-contained HTML viewer of the money relations the toolkit reports.

`graph_document` turns answers of investigate.wallet_links, investigate.wallet_funding, funding.trace, cluster.links
and cluster.clusters into one document; `render_html` draws it as one page with no external request. Nothing is
inferred: a payment, a link or a cluster absent from the answers is absent from the page. A relation that is not
demonstrated is never drawn like a demonstrated one, and a shared service is drawn as a service, never as a link
between its users. No page says who controls an address.

    python3 -m phi_forensics.viz build INPUT.json [INPUT.json ...] OUT.html [--title TEXT]
    python3 -m phi_forensics.viz serve DIR [--port 8080] [--host 127.0.0.1]
"""
import argparse
import base64
import functools
import hashlib
import html
import http.server
import json
import re
import sys
from collections import defaultdict

from monitoring.phi_monitor import chain

from . import cluster, registry, sources as src
from .ledger import amount

FORMAT = "phi-forensics-graph/1"
TOKENS = {chain.USDC: "USDC", chain.USDC_E: "USDC.e", chain.PUSD: "pUSD"}
TX, ADDRESS, AMOUNT = re.compile(r"0x[0-9a-f]{64}"), re.compile(r"0x[0-9a-f]{40}"), re.compile(r"[0-9]+(\.[0-9]{1,6})?")
NOT_SHOWN = ("This page does not show who controls an address. A payment shows that money moved between two addresses, "
             "not that the same money continued or who decided it. A shared service is not a link between its users. "
             "A missing line is not evidence that no relation exists: money can pass through an exchange, a bridge or another chain.")
SERVE_POLICY = ("default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'none'; connect-src 'none'; "
                "base-uri 'none'; form-action 'none'; frame-ancestors 'none'")


def link_style(grade):
    """Solid only for the two demonstrated grades; every other grade is drawn dashed and labelled with its name."""
    return "solid" if grade in cluster.JOINING else "dashed"


def _rows(value):
    """A list of rows, or the rows of a list the command line shortened ({returned, total, rows})."""
    return list(value.get("rows") or []) if isinstance(value, dict) else list(value or [])


def _answer_kind(answer):
    if isinstance(answer, list):
        if all(isinstance(x, dict) and {"a", "b", "grade"} <= set(x) for x in answer):
            return "links"
        if all(isinstance(x, dict) and "members" in x for x in answer):
            return "clusters"
    elif isinstance(answer, dict):
        if "links" in answer or "clusters" in answer:
            return "wallet_links"
        if "start" in answer and "edges" in answer:
            return "trace"
        if "wallet" in answer and ("deposits" in answer or "withdrawals" in answer):
            return "funding"
    raise ValueError("not an answer of wallet_links, wallet_funding, funding.trace, cluster.links or cluster.clusters")


def verify_command(edge):
    """The command that re-reads one transfer from two Polygon nodes, or None when a field is not well formed."""
    fields = [edge.get("tx"), edge.get("from"), edge.get("to"), edge.get("token")]
    if not (TX.fullmatch(fields[0] or "") and all(ADDRESS.fullmatch(f or "") for f in fields[1:])):
        return None
    command = ["python3 -m phi_forensics verify_transfer", "--transaction", fields[0], "--sender", fields[1], "--recipient", fields[2],
               "--token", fields[3]]
    if AMOUNT.fullmatch(edge.get("amount") or ""):
        command += ["--amount", edge["amount"]]
    if type(edge.get("log_index")) is int and edge["log_index"] >= 0:
        command += ["--log_index", str(edge["log_index"])]
    return " ".join(command)


def _edge(row, investigated):
    sender, receiver, raw = row["from"].lower(), row["to"].lower(), row.get("amount_raw")
    token = str(row["token"]).lower() if row.get("token") else None
    direction = {(True, True): "between_investigated", (False, True): "deposit", (True, False): "withdrawal",
                 (False, False): "outside"}[(sender in investigated, receiver in investigated)]
    edge = {"id": f"{row['tx'].lower()}:{row.get('log_index')}", "tx": row["tx"].lower(), "log_index": row.get("log_index"),
            "block": row.get("block"), "ts": row.get("ts"), "time_utc": src.utc(row["ts"]) if row.get("ts") is not None else None,
            "token": token, "token_name": TOKENS.get(token), "amount": amount(int(raw)) if raw is not None else row.get("amount"),
            "amount_raw": str(int(raw)) if raw is not None else None, "from": sender, "to": receiver, "direction": direction,
            "evidence_level": row.get("evidence_level"), "hop": row.get("hop")}
    edge["verify"] = verify_command(edge)
    return {k: v for k, v in edge.items() if v is not None}


def _totals(edges, direction, side, other):
    groups = {}
    for edge in edges:
        if edge["direction"] != direction:
            continue
        group = groups.setdefault(edge[side], {"address": edge[side], "transfers": 0, "wallets": set(), "raw": defaultdict(int), "edges": []})
        group["transfers"] += 1
        group["wallets"].add(edge[other])
        group["edges"].append(edge["id"])
        if "amount_raw" in edge:
            group["raw"][edge.get("token_name") or edge.get("token") or "?"] += int(edge["amount_raw"])
    return [{"address": g["address"], "transfers": g["transfers"], "wallets": sorted(g["wallets"]), "edges": g["edges"],
             "totals": {token: amount(v) for token, v in sorted(g["raw"].items())}} for _, g in sorted(groups.items())]


def graph_document(*answers, sources=(), known=registry.known):
    """One document from toolkit answers: nodes, one edge per transfer, graded links, clusters and a timeline.

    sources: the files or findings the answers come from, shown on the page. known: the registry lookup (injectable).
    """
    investigated, classes, transfers, links, groups, stops, limits = set(), {}, {}, {}, {}, [], []

    def add(row):
        merged = transfers.setdefault((row["tx"].lower(), row.get("log_index")), {})
        for key, value in row.items():  # the same log read from two answers is one transfer
            if value is not None:
                merged.setdefault(key, value)

    for answer in answers:
        kind = _answer_kind(answer)
        if kind in ("wallet_links", "links"):
            found = (answer.get("links") or []) if kind == "wallet_links" else answer
            investigated.update(w.lower() for w in ((answer.get("wallets") or []) if kind == "wallet_links" else ()))
            for link in found:
                key = (link["a"].lower(), link["b"].lower(), link.get("type") or "", link["grade"], (link.get("via") or "").lower())
                links.setdefault(key, link)
                investigated.update((link["a"].lower(), link["b"].lower()))
        if kind in ("wallet_links", "clusters"):
            for group in ((answer.get("clusters") or []) if kind == "wallet_links" else answer):
                groups.setdefault(tuple(sorted(m.lower() for m in group["members"])), group)
        if kind == "funding":
            investigated.add(answer["wallet"].lower())
            classes.update({a.lower(): c for a, c in (answer.get("counterparties") or {}).items()})
            for name in ("deposits", "withdrawals"):
                value = answer.get(name)
                if isinstance(value, dict) and value.get("returned", 0) < value.get("total", 0):
                    limits.append(f"{answer['wallet'].lower()}: {value['returned']} of {value['total']} {name} are listed")
                for row in _rows(value):
                    add(row)
                    if row.get("counterparty") and row.get("counterparty_kind"):
                        classes.setdefault(row["counterparty"].lower(), {"kind": row["counterparty_kind"], "label": row.get("counterparty_label")})
        if kind == "trace":
            start = answer["start"].lower()
            investigated.add(start)
            classes.update({a.lower(): c for a, c in (answer.get("nodes") or {}).items()})
            for row in answer["edges"]:
                add(row)
            stops += [{"address": s["address"].lower(), "reason": s.get("reason"), "hop": s.get("hop"), "trace": start,
                       "direction": answer.get("direction")} for s in answer.get("stops") or []]
            reading = (answer.get("limits") or {}).get("reading") if isinstance(answer.get("limits"), dict) else None
            if reading:
                limits.append(f"trace {answer.get('direction')} from {start}: {reading}")
            if answer.get("payments_not_followed"):
                limits.append(f"trace {answer.get('direction')} from {start}: {answer['payments_not_followed']} payments were not followed")
        if isinstance(answer, dict) and isinstance(answer.get("limits"), list):
            limits += [str(x) for x in answer["limits"]]
    for link in links.values():
        for ref in link.get("evidence") or []:
            add(ref)

    edges = sorted((_edge(row, investigated) for row in transfers.values()),
                   key=lambda e: (e.get("block") is None, e.get("block") or 0, e.get("log_index") or 0, e["tx"]))
    out_links = []
    for index, (key, link) in enumerate(sorted(links.items(), key=lambda kv: (cluster.RANK.get(kv[0][3], 9),) + kv[0])):
        out_links.append({k: v for k, v in {
            "id": f"L{index}", "a": key[0], "b": key[1], "type": link.get("type"), "grade": link["grade"],
            "style": link_style(link["grade"]), "demonstrated": link["grade"] in cluster.JOINING, "via": key[4] or None, "note": link.get("note"),
            "evidence_count": link.get("evidence_count"),
            "edges": [f"{r['tx'].lower()}:{r.get('log_index')}" for r in link.get("evidence") or []]}.items() if v is not None})
    out_clusters = [{"id": f"C{i}", **{k: group[k] for k in ("size", "links", "grade", "types", "statement") if k in group},
                     "members": list(members)}
                    for i, (members, group) in enumerate(sorted(groups.items(), key=lambda kv: (-len(kv[0]), kv[0])))]

    addresses = set(investigated) | {s["address"] for s in stops} | {l[k] for l in out_links for k in ("a", "b", "via") if l.get(k)}
    addresses |= {e[k] for e in edges for k in ("from", "to")} | {m for c in out_clusters for m in c["members"]}
    nodes = []
    for address in sorted(addresses):
        info = classes.get(address) or known(address) or {}
        nodes.append({k: v for k, v in {"address": address, "kind": info.get("kind") or "unknown", "label": info.get("label"),
                                         "label_source": info.get("source"), "investigated": address in investigated}.items() if v is not None})
    return {"format": FORMAT, "investigated": sorted(investigated), "nodes": nodes, "edges": edges, "links": out_links,
            "clusters": out_clusters, "timeline": [e["id"] for e in edges], "stops": stops,
            "funding_sources": _totals(edges, "deposit", "from", "to"),
            "withdrawal_destinations": _totals(edges, "withdrawal", "to", "from"),
            "limits": list(dict.fromkeys(limits)), "not_shown": NOT_SHOWN, "sources": [str(s) for s in sources]}


def layout(document):
    """[column, row] of each address: investigated wallets in column 0, payers to the left, payees to the right."""
    column = {a: 0 for a in document["investigated"]}
    pairs = [(e["from"], e["to"]) for e in document["edges"]]
    grew = True
    while grew:
        grew = False
        for sender, receiver in pairs:
            if receiver in column and sender not in column:
                column[sender], grew = column[receiver] - 1, True
            elif sender in column and receiver not in column:
                column[receiver], grew = column[sender] + 1, True
    loose = max(column.values(), default=0) + 1  # reached by no payment from the investigated wallets
    placed, rows = {}, defaultdict(int)
    for node in sorted(document["nodes"], key=lambda n: (not n.get("investigated"), n["address"])):
        col = column.get(node["address"], loose)
        placed[node["address"]] = [col, rows[col]]
        rows[col] += 1
    return placed


def _json_for_script(value):
    """JSON that cannot close the script element it sits in nor open markup."""
    text = json.dumps(value, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return text.replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def _sha256(text):
    return "'sha256-" + base64.b64encode(hashlib.sha256(text.encode()).digest()).decode() + "'"


def render_html(document, title="Money relations"):
    """One HTML file: inline style and script allowed by their hashes only, no request of any kind."""
    policy = (f"default-src 'none'; script-src {_sha256(SCRIPT)}; style-src {_sha256(STYLE)}; img-src 'none'; font-src 'none'; "
              "connect-src 'none'; media-src 'none'; object-src 'none'; frame-src 'none'; worker-src 'none'; manifest-src 'none'; "
              "base-uri 'none'; form-action 'none'")
    name = html.escape(str(title))
    return "".join((
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n',
        f'<meta http-equiv="Content-Security-Policy" content="{policy}">\n',
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n<meta name="referrer" content="no-referrer">\n',
        f"<title>{name}</title>\n<style>{STYLE}</style>\n</head>\n<body>\n",
        f'<header><h1>{name}</h1>\n<p class="muted">Built by phi_forensics.viz from toolkit answers. Every value comes from them; '
        "nothing on this page is inferred.</p></header>\n",
        BODY,
        f'<script type="application/json" id="graph-data">{_json_for_script({"document": document, "layout": layout(document)})}</script>\n',
        f"<script>{SCRIPT}</script>\n</body>\n</html>\n"))


STYLE = """
:root{--bg:#ffffff;--fg:#1b1b1b;--muted:#4f4f4f;--line:#c9c9c9;--panel:#f4f4f2;--pay:#1d4f91;--fin:#1b6b2f;--ctl:#6a2c91;
--hyp:#9a4a00;--svc:#5a5a5a;--inv:#fff3c4;--focus:#0b57d0}
@media (prefers-color-scheme:dark){:root{--bg:#141414;--fg:#ececec;--muted:#b9b9b9;--line:#4a4a4a;--panel:#1f1f1f;--pay:#8ab4f8;
--fin:#81c995;--ctl:#d7aefb;--hyp:#fdb36b;--svc:#bdbdbd;--inv:#4a3f12;--focus:#a8c7fa}}
*{box-sizing:border-box}
body{margin:0;padding:0 16px 32px;background:var(--bg);color:var(--fg);font:15px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif}
header,main,footer{max-width:1200px;margin:0 auto}
h1{font-size:1.4rem;margin:16px 0 4px}h2{font-size:1.1rem;margin:24px 0 8px}
.muted{color:var(--muted)}code,.mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.85em;overflow-wrap:anywhere}
.layout{display:grid;grid-template-columns:minmax(0,1fr);gap:16px}
@media (min-width:900px){.layout{grid-template-columns:minmax(0,2fr) minmax(0,1fr)}}
.graph{border:1px solid var(--line);border-radius:6px;overflow:auto;max-height:75vh;background:var(--bg)}
svg{display:block}
aside{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:12px;min-width:0}
fieldset{border:1px solid var(--line);border-radius:6px;margin:12px 0;padding:8px 12px}
label{display:inline-flex;gap:6px;align-items:center;margin:4px 16px 4px 0}
table{border-collapse:collapse;width:100%;font-size:.9em}
th,td{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;vertical-align:top}
.scroll{overflow-x:auto}
pre{white-space:pre-wrap;overflow-wrap:anywhere}dd{margin:0 0 6px 12px;overflow-wrap:anywhere}
button{font:inherit;color:inherit;background:var(--panel);border:1px solid var(--line);border-radius:4px;padding:2px 8px;cursor:pointer}
a{color:var(--pay)}
:focus-visible{outline:3px solid var(--focus);outline-offset:2px}
.pay{stroke:var(--pay);stroke-width:2;fill:none}
.solid{stroke:var(--fin);stroke-width:3;fill:none}
.solid.control{stroke:var(--ctl);stroke-width:5}
.dashed{stroke:var(--hyp);stroke-width:2.5;stroke-dasharray:8 6;fill:none}
.ring{stroke:var(--svc);stroke-width:2;stroke-dasharray:4 4;fill:none}
.node{fill:var(--panel);stroke:var(--fg);stroke-width:1.5}
.node.investigated{fill:var(--inv);stroke-width:3}
.node.unknown{stroke-dasharray:3 3}
.tag{fill:var(--fg);font-size:12px}.tag.small{fill:var(--muted);font-size:11px}
.grade{font-size:11px;fill:var(--hyp)}.grade.ok{fill:var(--fin)}
.hit{stroke:transparent;stroke-width:14;fill:none;cursor:pointer}
.legend svg{display:inline-block;vertical-align:middle;margin-right:6px}
.legend li{margin:4px 0}
"""

BODY = """<main>
<fieldset><legend>Show (by level of confidence)</legend><div id="filters"></div>
<p class="muted">By default only demonstrated relations are shown.</p></fieldset>
<div class="layout">
<div><div class="graph" id="graph" role="group"
 aria-label="Graph of money relations. Each line and address can be focused with Tab and opened with Enter."></div>
<p class="muted">Investigated wallets are in the middle column, payers to the left, payees to the right.</p></div>
<aside id="panel" aria-live="polite"><h2>Evidence</h2><p class="muted">Select a line, a node or a row to see its evidence.</p></aside>
</div>
<section class="legend"><h2>How to read this page</h2><ul id="legend"></ul><p id="not-shown"></p></section>
<section><h2>Funding sources</h2><div class="scroll" id="sources-table"></div></section>
<section><h2>Withdrawal destinations</h2><div class="scroll" id="destinations-table"></div></section>
<section><h2>Graded links</h2><div class="scroll" id="links-table"></div></section>
<section><h2>Clusters</h2><div id="clusters"></div></section>
<section><h2>Timeline</h2><div class="scroll" id="timeline"></div></section>
<section><h2>All transfers</h2><div class="scroll" id="edges-table"></div></section>
<section><h2>Where a trace stopped</h2><div class="scroll" id="stops"></div></section>
<section><h2>Limits</h2><ul id="limits"></ul></section>
<section><h2>Sources</h2><ul id="sources"></ul></section>
</main>
"""

SCRIPT = r"""
"use strict";
(function () {
  var data = JSON.parse(document.getElementById("graph-data").textContent);
  var doc = data.document, place = data.layout, NS = "http://www.w3.org/2000/svg";
  var CONTROL = "COMMON_CONTROL_DEMONSTRATED", FINANCIAL = "FINANCIAL_RELATION_DEMONSTRATED", NOT_A_LINK = "NOT_A_LINK";
  var nodes = {}, edges = {};
  doc.nodes.forEach(function (n) { nodes[n.address] = n; });
  doc.edges.forEach(function (e) { edges[e.id] = e; });
  var GRADES = [CONTROL, FINANCIAL, "PROBABLE_COORDINATION", NOT_A_LINK];
  doc.links.forEach(function (l) { if (GRADES.indexOf(l.grade) < 0) GRADES.push(l.grade); });
  var show = {payments: true};
  GRADES.forEach(function (g) { show[g] = g === CONTROL || g === FINANCIAL; });

  function el(tag, text, cls) {
    var n = document.createElement(tag);
    if (text != null) n.textContent = String(text);
    if (cls) n.className = cls;
    return n;
  }
  function sv(tag, attrs) {
    var n = document.createElementNS(NS, tag);
    for (var k in attrs) n.setAttribute(k, String(attrs[k]));
    return n;
  }
  function put(host, value) {
    if (value instanceof Node) host.appendChild(value); else host.textContent = value == null ? "" : String(value);
    return host;
  }
  function short(a) { return a && a.length > 14 ? a.slice(0, 8) + "\u2026" + a.slice(-4) : String(a); }
  function named(a) { var n = nodes[a]; return short(a) + (n && n.label ? " (" + n.label + ")" : ""); }
  function token(e) { return e.token_name || e.token || "?"; }
  function plural(n, word) { return n + " " + word + (n === 1 ? "" : "s"); }
  function activate(node, label, fn) {
    node.setAttribute("tabindex", "0");
    node.setAttribute("role", "button");
    node.setAttribute("aria-label", label);
    node.addEventListener("click", fn);
    node.addEventListener("keydown", function (ev) {
      if (ev.key === "Enter" || ev.key === " ") { ev.preventDefault(); fn(); }
    });
  }
  function button(text, fn) { var b = el("button", text); b.type = "button"; b.addEventListener("click", fn); return b; }
  function table(head, rows) {
    if (!rows.length) return el("p", "None in the answers.", "muted");
    var t = el("table"), thead = el("thead"), tr = el("tr"), body = el("tbody");
    head.forEach(function (h) { var th = el("th", h); th.scope = "col"; tr.appendChild(th); });
    thead.appendChild(tr); t.appendChild(thead);
    rows.forEach(function (cells) {
      var r = el("tr");
      cells.forEach(function (c) { r.appendChild(put(el("td"), c)); });
      body.appendChild(r);
    });
    t.appendChild(body);
    return t;
  }
  function fill(id, child) { var host = document.getElementById(id); host.textContent = ""; host.appendChild(child); }
  function dl(pairs) {
    var d = el("dl");
    pairs.forEach(function (p) {
      if (p[1] == null || p[1] === "") return;
      d.appendChild(el("dt", p[0]));
      d.appendChild(put(el("dd"), p[1]));
    });
    return d;
  }
  function explorer(tx) {
    if (!/^0x[0-9a-f]{64}$/.test(tx)) return null;
    var a = el("a", "Open in a block explorer (leaves this page)");
    a.href = "https://polygonscan.com/tx/" + tx;
    a.rel = "noopener noreferrer";
    return a;
  }

  var panel = document.getElementById("panel");
  function openPanel(heading, parts) {
    panel.textContent = "";
    panel.appendChild(el("h2", heading));
    parts.forEach(function (p) { if (p) panel.appendChild(p); });
    panel.setAttribute("tabindex", "-1");
    panel.focus();
  }
  function edgeBlock(e) {
    var box = el("div");
    box.appendChild(dl([["Transaction", el("code", e.tx)], ["Log index", e.log_index], ["Block", e.block],
      ["Time (UTC)", e.time_utc], ["From", el("code", e.from)], ["To", el("code", e.to)],
      ["Token", token(e) + (e.token ? " " + e.token : "")], ["Amount", e.amount], ["Direction", e.direction],
      ["Evidence level in the source", e.evidence_level]]));
    if (e.verify) {
      box.appendChild(el("p", "Re-check against two Polygon nodes:"));
      box.appendChild(el("pre")).appendChild(el("code", e.verify));
    } else {
      box.appendChild(el("p", "No re-check command: a field of this transfer is missing or not well formed.", "muted"));
    }
    var x = explorer(e.tx);
    if (x) box.appendChild(x);
    return box;
  }
  function edgeBlocks(ids) {
    var parts = [];
    ids.forEach(function (id) {
      parts.push(el("hr"));
      parts.push(edges[id] ? edgeBlock(edges[id]) : el("p", "Transfer " + id + " is not in the answers.", "muted"));
    });
    return parts;
  }
  function showEdges(ids, heading) {
    openPanel(heading, [el("p", plural(ids.length, "transfer") +
      ". A payment shows that money moved; it does not show who controls either address.")].concat(edgeBlocks(ids)));
  }
  function showLink(l) {
    var count = l.evidence_count != null ? l.evidence_count : l.edges.length;
    openPanel("Link " + l.type, [dl([["Grade", l.grade], ["Type", l.type],
      ["Drawn", l.grade === NOT_A_LINK ? "as a service, not as a line between its users" : l.style],
      ["Between", el("code", l.a + " and " + l.b)], ["Through", l.via ? el("code", l.via) : null], ["Note", l.note],
      ["Supporting transfers", count + " (" + l.edges.length + " listed)"]]),
      l.demonstrated ? null : el("p", "This grade is not a demonstrated relation.", "muted")].concat(edgeBlocks(l.edges)));
  }
  function showNode(a) {
    var n = nodes[a];
    var ins = doc.edges.filter(function (e) { return e.to === a; }).length;
    var outs = doc.edges.filter(function (e) { return e.from === a; }).length;
    openPanel("Address", [dl([["Address", el("code", a)], ["Kind", n.kind], ["Label", n.label], ["Label source", n.label_source],
      ["Investigated wallet", n.investigated ? "yes" : "no"], ["Transfers received", ins], ["Transfers sent", outs]]),
      el("p", "The kind is the toolkit's classification; it does not name who controls the address.", "muted")]);
  }

  var pairs = {};
  doc.edges.forEach(function (e) { var k = e.from + ">" + e.to; (pairs[k] = pairs[k] || []).push(e.id); });
  var spots = Object.keys(place).map(function (a) { return place[a]; });
  var minCol = Math.min.apply(null, spots.map(function (p) { return p[0]; }).concat([0]));
  var maxCol = Math.max.apply(null, spots.map(function (p) { return p[0]; }).concat([0]));
  var rows = Math.max.apply(null, spots.map(function (p) { return p[1]; }).concat([0])) + 1;
  var W = 260, H = 70;
  var height = {};  // a short column is centred on the tallest one
  spots.forEach(function (p) { height[p[0]] = Math.max(height[p[0]] || 0, p[1] + 1); });
  function xy(a) { var p = place[a]; return p ? [(p[0] - minCol) * W + 110, (p[1] + (rows - height[p[0]]) / 2) * H + 50] : null; }
  var SERVICE = {protocol: 1, labelled_service: 1, contract: 1, high_volume_key: 1, mint: 1};

  function text(x, y, cls, value, anchor) {
    var t = sv("text", {x: x, y: y, "class": cls, "text-anchor": anchor || "middle"});
    t.textContent = value;
    return t;
  }
  function drawPayments(svg) {
    Object.keys(pairs).sort().forEach(function (k) {
      var ids = pairs[k], e = edges[ids[0]], p = xy(e.from), q = xy(e.to);
      if (!p || !q) return;
      // payments inside one column bend to the left, graded links to the right: neither hides the other
      var c = p[0] === q[0] ? [p[0] - 50 - 15 * Math.abs(q[1] - p[1]) / H, (p[1] + q[1]) / 2] : [(p[0] + q[0]) / 2, (p[1] + q[1]) / 2];
      var ux = q[0] - c[0], uy = q[1] - c[1], len = Math.sqrt(ux * ux + uy * uy) || 1;
      var g = sv("g", {}), d = "M" + p[0] + "," + p[1] + " Q" + c[0] + "," + c[1] + " " + (q[0] - 14 * ux / len) + "," + (q[1] - 14 * uy / len);
      g.appendChild(sv("path", {d: d, "class": "pay", "marker-end": "url(#arrow)"}));
      g.appendChild(sv("path", {d: d, "class": "hit"}));
      g.appendChild(text((p[0] + 2 * c[0] + q[0]) / 4, (p[1] + 2 * c[1] + q[1]) / 4 - 6, "tag small", plural(ids.length, "payment")));
      activate(g, plural(ids.length, "payment") + " from " + e.from + " to " + e.to,
               function () { showEdges(ids, "Payments " + short(e.from) + " to " + short(e.to)); });
      svg.appendChild(g);
    });
  }
  function drawLink(svg, l) {
    var g = sv("g", {});
    if (l.grade === NOT_A_LINK) {
      var v = l.via && xy(l.via);
      if (!v) return;
      g.appendChild(sv("circle", {cx: v[0], cy: v[1], r: 24, "class": "ring"}));
      g.appendChild(text(v[0], v[1] - 30, "grade", "shared service: " + NOT_A_LINK));
      activate(g, "Shared service " + l.via + ", not a link between " + l.a + " and " + l.b, function () { showLink(l); });
    } else {
      var a = xy(l.a), b = xy(l.b);
      if (!a || !b) return;
      var mx = (a[0] + b[0]) / 2 + 60 + 20 * (parseInt(l.id.slice(1), 10) % 3), my = (a[1] + b[1]) / 2;
      var d = "M" + a[0] + "," + a[1] + " Q" + mx + "," + my + " " + b[0] + "," + b[1];
      var cls = l.style === "solid" ? (l.grade === CONTROL ? "solid control" : "solid") : "dashed";
      g.appendChild(sv("path", {d: d, "class": cls}));
      g.appendChild(sv("path", {d: d, "class": "hit"}));
      g.appendChild(text((a[0] + 2 * mx + b[0]) / 4 + 4, (a[1] + 2 * my + b[1]) / 4, l.style === "solid" ? "grade ok" : "grade",
                         l.grade + " (" + l.type + ")", "start"));
      activate(g, "Link " + l.grade + " " + l.type + " between " + l.a + " and " + l.b, function () { showLink(l); });
    }
    svg.appendChild(g);
  }
  function drawNode(svg, n) {
    var p = xy(n.address);
    if (!p) return;
    var g = sv("g", {}), cls = "node" + (n.kind === "unknown" ? " unknown" : "") + (n.investigated ? " investigated" : "");
    g.appendChild(SERVICE[n.kind] ? sv("rect", {x: p[0] - 12, y: p[1] - 12, width: 24, height: 24, "class": cls})
                                  : sv("circle", {cx: p[0], cy: p[1], r: 12, "class": cls}));
    g.appendChild(text(p[0], p[1] + 28, "tag", short(n.address)));
    g.appendChild(text(p[0], p[1] + 42, "tag small", (n.investigated ? "investigated, " : "") + n.kind + (n.label ? ": " + n.label : "")));
    activate(g, (n.investigated ? "Investigated wallet " : "Address ") + n.address + ", kind " + n.kind + (n.label ? ", " + n.label : ""),
             function () { showNode(n.address); });
    svg.appendChild(g);
  }
  function draw() {
    var width = (maxCol - minCol) * W + 520, height = rows * H + 60;  // room on the right for the grade labels
    var svg = sv("svg", {width: width, height: height, viewBox: "0 0 " + width + " " + height});
    var defs = sv("defs", {}), m = sv("marker", {id: "arrow", viewBox: "0 0 10 10", refX: 10, refY: 5, markerWidth: 7, markerHeight: 7,
                                                 orient: "auto-start-reverse"});
    m.appendChild(sv("path", {d: "M0,0 L10,5 L0,10 z", "class": "pay"}));
    defs.appendChild(m);
    svg.appendChild(defs);
    if (show.payments) drawPayments(svg);
    doc.links.forEach(function (l) { if (show[l.grade]) drawLink(svg, l); });
    doc.nodes.forEach(function (n) { drawNode(svg, n); });
    fill("graph", svg);
    var shown = doc.links.filter(function (l) { return show[l.grade]; });
    fill("links-table", table(["Grade", "Drawn", "Type", "Wallets", "Through", "Transfers", ""], shown.map(function (l) {
      return [l.grade, l.grade === NOT_A_LINK ? "as a service" : l.style, l.type, named(l.a) + " / " + named(l.b),
              l.via ? named(l.via) : "", l.evidence_count != null ? l.evidence_count : l.edges.length,
              button("Evidence", function () { showLink(l); })];
    })));
    if (doc.links.length > shown.length) {
      document.getElementById("links-table").appendChild(
        el("p", plural(doc.links.length - shown.length, "link") + " hidden by the filters above.", "muted"));
    }
  }

  var filters = document.getElementById("filters");
  [["payments", "Demonstrated payments (solid arrows)"]].concat(GRADES.map(function (g) {
    return [g, g + " (" + doc.links.filter(function (l) { return l.grade === g; }).length + ")"];
  })).forEach(function (f) {
    var lab = el("label"), box = el("input");
    box.type = "checkbox";
    box.checked = !!show[f[0]];
    box.addEventListener("change", function () { show[f[0]] = box.checked; draw(); });
    lab.appendChild(box);
    lab.appendChild(document.createTextNode(f[1]));
    filters.appendChild(lab);
  });

  var legend = document.getElementById("legend");
  [["pay", "Solid arrow: a demonstrated payment, a token transfer read from the chain. The number counts the transfers " +
           "between the two addresses."],
   ["solid control", "Thick solid line: " + CONTROL + ", one key can sign for both wallets."],
   ["solid", "Solid line: " + FINANCIAL + ", money moved between the wallets or through a non-service address they share. " +
             "That one person controls them is not demonstrated."],
   ["dashed", "Dashed line, labelled with its grade: a relation that is not demonstrated (PROBABLE_COORDINATION or any " +
              "other grade). Hidden by default."],
   ["ring", "Dashed ring around an address: a shared service (" + NOT_A_LINK + "). It is drawn as a service, never as a line " +
            "between its users. Hidden by default."]
  ].forEach(function (r) {
    var li = el("li"), s = sv("svg", {width: 44, height: 12, "aria-hidden": "true"});
    s.appendChild(sv("path", {d: "M2,6 L42,6", "class": r[0]}));
    li.appendChild(s);
    li.appendChild(document.createTextNode(r[1]));
    legend.appendChild(li);
  });
  legend.appendChild(el("li", "Square: an address classified as a service (protocol, labelled service, contract, high-volume " +
    "key, mint). Circle: a key or a kind not established; a dotted outline means not established. Filled: an investigated wallet."));
  document.getElementById("not-shown").textContent = "What this page does not show: " + doc.not_shown;

  function flows(id, list, label) {
    fill(id, table([label, "Kind", "Transfers", "Wallets", "Totals", ""], list.map(function (g) {
      var totals = Object.keys(g.totals).map(function (t) { return g.totals[t] + " " + t; }).join("; ");
      return [named(g.address), (nodes[g.address] || {}).kind, g.transfers, g.wallets.map(short).join(", "), totals,
              button("Evidence", function () { showEdges(g.edges, label + " " + short(g.address)); })];
    })));
  }
  flows("sources-table", doc.funding_sources, "Payer");
  flows("destinations-table", doc.withdrawal_destinations, "Payee");

  var clusters = document.getElementById("clusters");
  if (!doc.clusters.length) clusters.appendChild(el("p", "No cluster in the answers.", "muted"));
  doc.clusters.forEach(function (c) {
    var box = el("div"), ul = el("ul");
    box.appendChild(el("h3", c.id + ": " + c.size + " wallets, held together by " + c.grade));
    box.appendChild(el("p", c.statement));
    box.appendChild(el("p", "Link types: " + (c.types || []).join(", "), "muted"));
    c.members.forEach(function (m) { ul.appendChild(el("li")).appendChild(button(named(m), function () { showNode(m); })); });
    box.appendChild(ul);
    clusters.appendChild(box);
  });

  fill("timeline", table(["Time (UTC)", "Block", "From", "To", "Amount", "Token", "Level in source", ""], doc.timeline.map(function (id) {
    var e = edges[id];
    return [e.time_utc, e.block, named(e.from), named(e.to), e.amount, token(e), e.evidence_level,
            button("Evidence", function () { showEdges([e.id], "Transfer"); })];
  })));
  fill("edges-table", table(["Transaction", "Log index", "Block", "Time (UTC)", "From", "To", "Token", "Amount", "Direction",
                             "Level in source"], doc.edges.map(function (e) {
    return [e.tx, e.log_index, e.block, e.time_utc, e.from, e.to, token(e), e.amount, e.direction, e.evidence_level];
  })));
  fill("stops", table(["Address", "Reason", "Hop", "Trace from", "Direction"], doc.stops.map(function (s) {
    return [s.address, s.reason, s.hop, s.trace, s.direction];
  })));
  [["limits", doc.limits, "No limit was attached to the answers."], ["sources", doc.sources, "Not stated."]].forEach(function (x) {
    var ul = document.getElementById(x[0]);
    x[1].forEach(function (item) { ul.appendChild(el("li", item)); });
    if (!x[1].length) ul.appendChild(el("li", x[2], "muted"));
  });
  draw();
})();
"""


class _Pages(http.server.SimpleHTTPRequestHandler):
    """Static pages with headers that forbid every request a page could make."""

    def end_headers(self):
        self.send_header("Content-Security-Policy", SERVE_POLICY)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        super().end_headers()


def server(directory, port=8080, host="127.0.0.1"):
    return http.server.ThreadingHTTPServer((host, port), functools.partial(_Pages, directory=str(directory)))


def _answers(document):
    """An input file holds one answer, or {"answers": [...], "sources": [...]}."""
    if isinstance(document, dict) and "answers" in document:
        return document["answers"], document.get("sources") or []
    return [document], []


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python3 -m phi_forensics.viz", description="Offline HTML viewer of money relations.")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="write one self-contained page from one or more JSON answers")
    build.add_argument("paths", nargs="+", metavar="PATH", help="INPUT.json [INPUT.json ...] OUT.html")
    build.add_argument("--title", default="Money relations")
    serve = commands.add_parser("serve", help="serve a folder of pages")
    serve.add_argument("directory")
    serve.add_argument("--port", type=int, default=8080)
    serve.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args(argv)
    if args.command == "serve":
        with server(args.directory, args.port, args.host) as httpd:
            print(f"serving {args.directory} on http://{args.host}:{httpd.server_address[1]}/", file=sys.stderr)
            httpd.serve_forever()
        return 0
    if len(args.paths) < 2:
        parser.error("build needs at least one INPUT.json and the OUT.html path")
    answers, sources = [], []
    for path in args.paths[:-1]:
        with open(path, encoding="utf-8") as handle:
            more, cited = _answers(json.load(handle))
        answers += more
        sources += cited
    page = render_html(graph_document(*answers, sources=sources), args.title)
    with open(args.paths[-1], "w", encoding="utf-8", newline="\n") as handle:
        handle.write(page)
    return 0


if __name__ == "__main__":
    sys.exit(main())
