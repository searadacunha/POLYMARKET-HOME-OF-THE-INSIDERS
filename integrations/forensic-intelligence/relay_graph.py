"""Relay orders archived from the public requests API, read as transfers between accounts. Offline, standard library.

An archive is a folder holding queue.tsv (kind, value, label: the addresses that were asked for), manifest.jsonl (one
line per stored page with the SHA-256 of its decompressed body) and raw/ (gzip pages). A page is used only after its
hash is checked, and only the pages of addresses whose history is complete are read.

A Relay order moves value from a sender to a recipient. When the two differ, the order is a transfer between two
parties. That is a money-movement fact and nothing more: it does not say who controls either address, and a router, a
bridge or an exchange deposit address is shared by unrelated users.
"""
import gzip
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def norm(address):
    """EVM addresses compare in lower case; Solana, Tron and Bitcoin addresses are case sensitive and stay as written."""
    return address.lower() if isinstance(address, str) and address.startswith("0x") else address


def load(archive):
    """(labels, complete, orders): label of each queried address, the addresses fully read, orders by request id."""
    archive = Path(archive)
    labels = {}
    for line in (archive / "queue.tsv").read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] == "user":
            labels.setdefault(norm(parts[1].strip()), parts[2] if len(parts) > 2 else "")
    pages, complete = defaultdict(list), set()
    for line in (archive / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
        page = json.loads(line)
        if page["kind"] == "user" and page.get("status") == 200:
            pages[norm(page["value"])].append(page)
            if page.get("complete"):
                complete.add(norm(page["value"]))
    orders = {}
    for address in sorted(complete):
        for page in pages[address]:
            body = gzip.decompress((archive / page["file"]).read_bytes())
            if hashlib.sha256(body).hexdigest() != page["sha256_body"]:
                raise ValueError(f"archived page does not match its manifest hash: {page['file']}")
            for order in json.loads(body).get("requests") or []:
                orders[order["id"]] = order
    return labels, complete, orders


def transfers(orders):
    """One row per order whose sender and recipient differ, with both legs as the API recorded them."""
    rows = []
    for order_id, order in sorted(orders.items()):
        data = order.get("data") or {}
        meta = data.get("metadata") or {}
        sender, recipient = norm(meta.get("sender") or order.get("user")), norm(meta.get("recipient") or order.get("recipient"))
        if not sender or not recipient or sender == recipient:
            continue
        leg_in, leg_out = (data.get("inTxs") or [{}])[0], (data.get("outTxs") or [{}])[0]
        cur_in, cur_out = meta.get("currencyIn") or {}, meta.get("currencyOut") or {}
        rows.append({
            "order": order_id, "status": order.get("status"), "sender": sender, "recipient": recipient,
            "in_chain": leg_in.get("chainId"), "in_tx": leg_in.get("hash"), "in_time": leg_in.get("timestamp"),
            "out_chain": leg_out.get("chainId"), "out_tx": leg_out.get("hash"), "out_time": leg_out.get("timestamp"),
            "amount_in": cur_in.get("amountFormatted"), "symbol_in": (cur_in.get("currency") or {}).get("symbol"),
            "amount_out": cur_out.get("amountFormatted"), "symbol_out": (cur_out.get("currency") or {}).get("symbol"),
            "usd_in": cur_in.get("amountUsd"),
        })
    return rows


def account_edges(rows, accounts):
    """Transfers from one account of the set to another: direct, or through one address outside the set.

    "via" means: X sent to C, and C is the sender of archived orders into Y. Orders of C towards addresses that were
    never archived are invisible here, so via_pays counts only the accounts of the set that C is seen paying.
    """
    paid_by = defaultdict(lambda: defaultdict(list))
    for row in rows:
        paid_by[row["sender"]][row["recipient"]].append(row["order"])
    edges = []
    for x in sorted(a for a in accounts if a in paid_by):
        for c, orders_xc in sorted(paid_by[x].items(), key=lambda item: str(item[0])):
            if c in accounts:
                edges.append({"from": x, "to": c, "via": None, "via_pays": None, "orders": sorted(orders_xc), "orders_via": []})
                continue
            reached = {y: o for y, o in paid_by.get(c, {}).items() if y in accounts and y != x}
            for y, orders_cy in sorted(reached.items(), key=lambda item: str(item[0])):
                edges.append({"from": x, "to": y, "via": c, "via_pays": len(reached), "orders": sorted(orders_xc), "orders_via": sorted(orders_cy)})
    return edges


def shared_counterparties(rows, cohort_of):
    """Addresses that exchanged orders with accounts of two or more cohorts: {address: {cohort: {account: [orders]}}}."""
    seen = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for row in rows:
        for account, other in ((row["sender"], row["recipient"]), (row["recipient"], row["sender"])):
            if account in cohort_of:
                seen[other][cohort_of[account]][account].append(row["order"])
    return {other: {c: dict(a) for c, a in cohorts.items()} for other, cohorts in seen.items() if len(cohorts) >= 2}
