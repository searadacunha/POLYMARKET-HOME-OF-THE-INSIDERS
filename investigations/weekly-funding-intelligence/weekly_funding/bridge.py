"""Bounded, historical Ethereum-to-Polygon Relay screen, with exact order and destination receipts."""

import argparse
import hashlib
from threading import Event
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from .accounts import activity_page, registry
from .archive import infrastructure, native_archive
from .collect import net, rpc
from .common import PUBLICNODE, RPC, SNAP, TOKENS, TRANSFER, ZERO, addr_topic, save, weeks
from .events import load_stream
from .routes import capture_proof, guaranteed


def fill_match(order, receipt):
    if not (receipt["transactionHash"] == order["out_tx"] and int(receipt["status"], 16) == 1):
        return None
    matches = [
        r
        for r in receipt["logs"]
        if r["address"].lower() == order["out_token"]
        and len(r["topics"]) == 3
        and r["topics"][0] == TRANSFER
        and r["topics"][2] == addr_topic(order["recipient"])
        and r["transactionHash"] == order["out_tx"]
        and r["blockHash"] == receipt["blockHash"]
        and not r.get("removed", False)
        and int(r["data"], 16) == order["out_units"]
    ]
    return matches[0] if len(matches) == 1 else None


def orders(a, lo, hi):
    cursor = None
    seen = set()
    matches = {}
    for _ in range(4):
        q = {"user": a, "originChainId": 1, "destinationChainId": 137, "limit": 50}
        if cursor:
            q["continuation"] = cursor
        response = net.get_json(
            "https://api.relay.link/requests/v2?" + urlencode(q), tries=2, timeout=15
        )
        for o in response["requests"]:
            data = o.get("data", {})
            ins, outs = data.get("inTxs", []), data.get("outTxs", [])
            if (
                o.get("status") != "success"
                or o.get("user", "").lower() != a
                or len(ins) != 1
                or len(outs) != 1
                or ins[0].get("chainId") != 1
                or outs[0].get("chainId") != 137
                or ins[0].get("status") != "success"
                or outs[0].get("status") != "success"
            ):
                continue
            i, j = ins[0], outs[0]
            meta = data["metadata"]
            curr_in, curr_out = meta["currencyIn"], meta["currencyOut"]
            if (
                curr_in["currency"]["address"].lower() != ZERO
                or curr_in["currency"]["chainId"] != 1
                or curr_out["currency"]["chainId"] != 137
                or curr_out["currency"]["address"].lower() not in TOKENS
                or not lo <= i["timestamp"] <= hi
            ):
                continue
            recipient = o["recipient"].lower()
            if meta.get("recipient", "").lower() != recipient:
                continue
            row = dict(
                id=o["id"],
                user=a,
                recipient=recipient,
                in_tx=i["hash"].lower(),
                out_tx=j["hash"].lower(),
                in_to=i["data"]["to"].lower(),
                in_time=i["timestamp"],
                out_time=j["timestamp"],
                in_units=int(curr_in["amount"]),
                out_units=int(curr_out["amount"]),
                out_token=curr_out["currency"]["address"].lower(),
            )
            if o["id"] in matches and matches[o["id"]] != row:
                raise ValueError("conflicting provider order")
            matches[o["id"]] = row
        cursor = response.get("continuation")
        if not cursor:
            return list(matches.values()), "EXHAUSTED"
        if cursor in seen or not response["requests"]:
            raise ValueError("stalled Relay cursor")
        seen.add(cursor)
    return list(matches.values()), "PAGE_CAP"


def backed(seed, o, proof, receipt):
    if (
        seed.chain != 1
        or seed.asset != "native"
        or seed.recipient != o["user"]
        or proof["tx"]["hash"] != o["in_tx"]
        or proof["tx"]["to"] != o["in_to"]
        or int(proof["tx"]["value"], 16) != o["in_units"]
        or o["in_units"] <= 0
        or o["out_token"] not in TOKENS
        or o["out_units"] <= 0
        or guaranteed(seed, proof, bridge=True) != o["in_units"]
    ):
        return None
    return fill_match(o, receipt)


def capture(snap, first, last, cutoff):
    members, _ = registry(snap)
    excluded = infrastructure()
    archived, _ = native_archive()
    roots = defaultdict(list)
    for w in weeks(first, last):
        rs = load_stream(snap, w, 1, "tornado")[0] + archived.get(w, [])
        # Match a known trading endpoint, or use a deterministic 16-payee audit sample per source/week.
        for s in ("changenow", "tornado"):
            eligible = [
                e
                for e in rs
                if e.stream == s and e.asset == "native" and (1, e.recipient) not in excluded
            ]
            addresses = {e.recipient for e in eligible}
            ranked = sorted(addresses, key=lambda a: hashlib.sha256((w + s + a).encode()).digest())
            selected = (addresses & members.keys()) | set(ranked[:16])
            for e in eligible:
                if e.recipient in selected:
                    roots[e.recipient].append(e)

    exhausted = Event()

    def one(a):
        if exhausted.is_set():
            return {"status": "NOT_QUERIED_QUOTA", "orders": [], "proofs": []}
        rs = roots[a]
        out = {"orders": [], "proofs": []}
        try:
            os, state = orders(a, min(x.ts for x in rs), min(cutoff - 1, max(x.ts for x in rs) + 604800))
            out["status"] = state
            for o in os:
                seeds = [e for e in rs if e.ts <= o["in_time"] <= e.ts + 604800]
                if not seeds or (137, o["recipient"]) in excluded:
                    continue
                out["orders"].append(o)
                pm, _ = activity_page(o["recipient"], 1, cutoff - 1, 1)
                if not pm:
                    continue
                for e in seeds:
                    pf = capture_proof(e, o["in_tx"])
                    receipts = [
                        rpc(host, "eth_getTransactionReceipt", [o["out_tx"]])
                        for host in (RPC, PUBLICNODE)
                    ]
                    if not all(receipts):
                        raise ValueError("destination receipt not served")
                    lg = backed(e, o, pf, receipts[0])
                    lg2 = backed(e, o, pf, receipts[1])
                    if (
                        not lg
                        or not lg2
                        or (lg["blockHash"], lg["logIndex"]) != (lg2["blockHash"], lg2["logIndex"])
                    ):
                        continue
                    b = rpc(RPC, "eth_getBlockByHash", [lg["blockHash"], False])
                    out["proofs"].append(
                        dict(
                            seed=list(e.key),
                            order=o,
                            origin=pf,
                            pm_fill=pm[0],
                            destination_time=int(b["timestamp"], 16),
                            destination=dict(
                                transactionHash=o["out_tx"],
                                blockHash=lg["blockHash"],
                                status="0x1",
                                logs=receipts[0]["logs"],
                            ),
                            second_destination_log=lg2,
                        )
                    )
        except (net.SourceError, ValueError, KeyError, TypeError) as exc:
            if isinstance(exc, net.SourceError) and exc.status in {403, 410, 429}:
                exhausted.set()
            out.update(status="PARTIAL", error=str(exc)[:260])
        return out

    keys = sorted(roots)
    with ThreadPoolExecutor(4) as pool:
        result = dict(zip(keys, pool.map(one, keys), strict=True))
    save(snap / "bridge.json.gz", dict(from_week=first, to_week=last, cutoff=cutoff, accounts=result))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    p.add_argument("--asof", type=int, required=True)
    p.add_argument("--dest", type=Path, default=SNAP)
    args = p.parse_args()
    capture(args.dest, args.from_week, args.to_week, args.asof)
