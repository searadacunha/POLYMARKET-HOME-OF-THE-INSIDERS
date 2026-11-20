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


def load(archive, manifest=None, stats=None):
    """(labels, complete, orders): label of each queried address, the addresses fully read, orders by request id.

    manifest: another manifest file to read instead of the archive's own, for example the frozen list of pages of a
    published snapshot. stats: a dict that receives the counts of what was read, merged or left out.
    """
    archive = Path(archive)
    labels = {}
    for line in (archive / "queue.tsv").read_text(encoding="utf-8").splitlines():
        parts = line.split("\t")
        if len(parts) >= 2 and parts[0] == "user":
            labels.setdefault(norm(parts[1].strip()), parts[2] if len(parts) > 2 else "")
    pages, claimed = defaultdict(list), set()
    for line in Path(manifest or archive / "manifest.jsonl").read_text(encoding="utf-8").splitlines():
        page = json.loads(line)
        if page["kind"] == "user" and page.get("status") == 200:
            pages[norm(page["value"])].append(page)
            if page.get("complete"):
                claimed.add(norm(page["value"]))
    # a history counts as complete only when its pages are 0..n with no gap: a page lost to an error is not skipped silently
    complete = {a for a in claimed if sorted(p["page"] for p in pages[a]) == list(range(len(pages[a])))}
    orders, seen_twice, revalued, other, restated = {}, 0, 0, 0, 0
    for address in sorted(complete):
        for page in pages[address]:
            body = gzip.decompress((archive / page["file"]).read_bytes())
            if hashlib.sha256(body).hexdigest() != page["sha256_body"]:
                raise ValueError(f"archived page does not match its manifest hash: {page['file']}")
            requests = json.loads(body)["requests"]
            if len(requests) != page["n_requests"]:
                raise ValueError(f"page holds {len(requests)} orders, manifest says {page['n_requests']}: {page['file']}")
            for order in requests:
                prev = orders.get(order["id"])
                if prev is not None:
                    seen_twice += 1
                    if order_row(order["id"], prev) == order_row(order["id"], order):
                        changed = list(differing_paths(prev, order))
                        if changed:  # USD valuations of amounts and fees are recomputed by the API at each read
                            revalued += all("Usd" in path for path in changed)
                            other += not all("Usd" in path for path in changed)
                        continue
                    # the facts of the order changed between two reads: keep the later state, never the last file read
                    restated += 1
                    old, new = prev.get("updatedAt") or "", order.get("updatedAt") or ""
                    if old == new:
                        raise ValueError(f"order {order['id']} differs between two histories with the same updatedAt")
                    if old > new:
                        continue
                orders[order["id"]] = order
    if stats is not None:
        stats.update({"pages_read": sum(len(pages[a]) for a in complete), "histories_marked_complete": len(claimed),
                      "histories_with_page_gap": len(claimed - complete), "orders_seen_in_two_histories": seen_twice,
                      "orders_differing_in_valuations_only": revalued, "orders_differing_in_other_unread_fields": other,
                      "orders_restated_between_reads": restated})
    return labels, complete, orders


def differing_paths(a, b, path=""):
    """Paths, such as .data.feesUsd.gas, where two JSON values differ."""
    if isinstance(a, dict) and isinstance(b, dict):
        for key in sorted(set(a) | set(b)):
            if a.get(key) != b.get(key):
                yield from differing_paths(a.get(key), b.get(key), f"{path}.{key}")
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            yield from differing_paths(x, y, f"{path}[{i}]")
    elif a != b:
        yield path


def order_row(order_id, order):
    """The fields of an order that this module reads, as the API recorded them."""
    data = order.get("data") or {}
    meta = data.get("metadata") or {}
    leg_in, leg_out = (data.get("inTxs") or [{}])[0], (data.get("outTxs") or [{}])[0]
    cur_in, cur_out = meta.get("currencyIn") or {}, meta.get("currencyOut") or {}
    return {
        "order": order_id, "status": order.get("status"),
        "sender": norm(meta.get("sender") or order.get("user")), "recipient": norm(meta.get("recipient") or order.get("recipient")),
        "in_chain": leg_in.get("chainId"), "in_tx": leg_in.get("hash"), "in_time": leg_in.get("timestamp"),
        "out_chain": leg_out.get("chainId"), "out_tx": leg_out.get("hash"), "out_time": leg_out.get("timestamp"),
        "amount_in": cur_in.get("amountFormatted"), "symbol_in": (cur_in.get("currency") or {}).get("symbol"),
        "amount_out": cur_out.get("amountFormatted"), "symbol_out": (cur_out.get("currency") or {}).get("symbol"),
        "usd_in": cur_in.get("amountUsd"),
    }


def transfers(orders):
    """One row per order whose sender and recipient differ, with both legs as the API recorded them."""
    rows = [order_row(order_id, order) for order_id, order in sorted(orders.items())]
    return [r for r in rows if r["sender"] and r["recipient"] and r["sender"] != r["recipient"]]


def field_conflicts(orders):
    """Ids of orders whose metadata recipient differs from the order's own recipient field. transfers() reads the
    metadata, so such an order may be dropped as a self-bridge or credited to the other address: count it."""
    out = []
    for order_id, order in sorted(orders.items()):
        meta = (order.get("data") or {}).get("metadata") or {}
        if meta.get("recipient") and order.get("recipient") and norm(meta["recipient"]) != norm(order["recipient"]):
            out.append(order_id)
    return out


def account_edges(rows, accounts):
    """Transfers from one account of the set to another: direct, or through one address outside the set.

    "via" means: X sent to C, and C is the sender of archived orders into Y. Orders of C towards addresses that were
    never archived are invisible here, so via_pays counts only the accounts of the set that C is seen paying.
    """
    paid_by = defaultdict(lambda: defaultdict(list))
    for row in rows:
        if row["status"] == "success":  # a refunded order returned to its sender: it paid nobody
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
            if account in cohort_of and row["status"] == "success":
                seen[other][cohort_of[account]][account].append(row["order"])
    return {other: {c: dict(a) for c, a in cohorts.items()} for other, cohorts in seen.items() if len(cohorts) >= 2}
