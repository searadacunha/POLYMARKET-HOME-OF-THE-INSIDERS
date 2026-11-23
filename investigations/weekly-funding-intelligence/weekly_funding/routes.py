"""Screen indexed native sends, then bound the first EOA payment with RPC balances and nonces."""

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urlencode
from .accounts import activity_page
from .archive import infrastructure
from .collect import net, rpc
from .common import ETH_GATEWAY, RPC, SNAP, ZERO, save, weeks
from .events import load_stream

EXPLORER = "https://polygon.blockscout.com/api/v2/addresses/"


def sends(a, lo, limit=4):
    params = {"filter": "from"}
    cursors = set()
    sends_by_hash = {}
    for _ in range(limit):
        raw = net.get_json(EXPLORER + a + "/transactions?" + urlencode(params), tries=2, timeout=16)
        rows = raw["items"]
        heights = [int(x["block_number"]) for x in rows]
        if heights != sorted(heights, reverse=True):
            raise ValueError("explorer transaction order")
        for x in rows:
            if x["from"]["hash"].lower() != a:
                raise ValueError("explorer sender mismatch")
            if int(x["block_number"]) >= lo:
                sends_by_hash[x["hash"].lower()] = x
        nxt = raw["next_page_params"]
        if not nxt or (heights and min(heights) < lo):
            return list(sends_by_hash.values()), "EXHAUSTED_TO_START"
        key = urlencode(sorted(nxt.items()))
        if key in cursors or not rows:
            raise ValueError("stalled explorer cursor")
        cursors.add(key)
        params = dict(nxt, filter="from")
    return list(sends_by_hash.values()), "PAGE_CAP"


def guaranteed(seed, proof, bridge=False):
    """An undelegated EOA spends exactly one nonce. Only final balance and fee can absorb the seed."""
    tx, rc, b = proof["tx"], proof["receipt"], proof["header"]
    end_block = int(b["number"], 16)
    if not (
        seed.chain == (1 if bridge else 137)
        and seed.asset == "native"
        and seed.block < end_block
        and seed.ts <= int(b["timestamp"], 16) <= seed.ts + 7 * 86400
        and tx["hash"] == rc["transactionHash"]
        and tx["from"] == rc["from"] == seed.recipient
        and tx["to"] == rc["to"]
        and tx["to"] not in {None, ZERO, seed.recipient}
        and (bridge or tx["input"] == "0x")
        and not tx.get("authorizationList")
        and tx.get("type") in ("0x0", "0x1", "0x2")
        and tx["blockHash"] == rc["blockHash"] == b["hash"]
        and tx["blockNumber"] == rc["blockNumber"] == b["number"]
        and int(rc["status"], 16) == 1
        and (bridge or int(rc["gasUsed"], 16) == 21000)
        and proof["code_before"] == proof["code_after"] == "0x"
        and int(proof["nonce_before"], 16) == int(tx["nonce"], 16) == int(proof["nonce_after"], 16) - 1
    ):
        return 0
    fee = int(rc["gasUsed"], 16) * int(rc["effectiveGasPrice"], 16)
    return min(int(tx["value"], 16), max(0, seed.units - int(proof["balance_after"], 16) - fee))


def capture_proof(seed, txhash):
    endpoint = ETH_GATEWAY if seed.chain == 1 else RPC
    tx = rpc(endpoint, "eth_getTransactionByHash", [txhash])
    rc = rpc(endpoint, "eth_getTransactionReceipt", [txhash])
    if not tx or not rc:
        raise ValueError("missing transaction/receipt")
    block = rpc(endpoint, "eth_getBlockByHash", [rc["blockHash"], False])
    proof = {
        "tx": {
            k: tx.get(k)
            for k in (
                "hash",
                "from",
                "to",
                "nonce",
                "value",
                "input",
                "type",
                "blockHash",
                "blockNumber",
                "authorizationList",
            )
        },
        "receipt": {
            k: rc[k]
            for k in (
                "transactionHash",
                "from",
                "to",
                "blockHash",
                "blockNumber",
                "status",
                "gasUsed",
                "effectiveGasPrice",
            )
        },
        "header": {k: block[k] for k in ("number", "timestamp", "hash")},
    }
    a = seed.recipient
    for name, method, blockref in [
        ("code_before", "eth_getCode", hex(seed.block - 1)),
        ("code_after", "eth_getCode", rc["blockNumber"]),
        ("nonce_before", "eth_getTransactionCount", hex(seed.block - 1)),
        ("nonce_after", "eth_getTransactionCount", rc["blockNumber"]),
        ("balance_after", "eth_getBalance", rc["blockNumber"]),
    ]:
        proof[name] = rpc(endpoint, method, [a, blockref])
    return proof


def capture(snap, first, last, asof):
    roots = defaultdict(list)
    for w in weeks(first, last):
        for e in load_stream(snap, w, 137, "tornado")[0]:
            roots[e.recipient].append(e)
    excluded = infrastructure()

    def one(item):
        a, credits = item
        tally = Counter()
        evidence = []
        try:
            rows, state = sends(a, min(c.block for c in credits))
            tally[state] += 1
            if (137, a) in excluded:
                tally["custodial_intermediary"] += 1
                return dict(tally=tally, proofs=evidence)
            for seed in credits:
                # Only simple native sends are candidates. A later nonce cannot pass the RPC test.
                out = [
                    x
                    for x in rows
                    if x["block_number"] > seed.block and x.get("to") and x.get("status") == "ok"
                ]
                if not out:
                    continue
                x = min(out, key=lambda r: int(r["nonce"]))
                if int(x["value"]) <= 0 or x.get("raw_input") != "0x":
                    continue
                terminal = x["to"]["hash"].lower()
                if terminal in {ZERO, a} or (137, terminal) in excluded:
                    continue
                from datetime import datetime

                ts = int(datetime.fromisoformat(x["timestamp"].replace("Z", "+00:00")).timestamp())
                if not seed.ts <= ts < min(asof, seed.ts + 7 * 86400 + 1):
                    continue
                tally["candidate_send"] += 1
                pm, _ = activity_page(terminal, 1, asof - 1, 1)
                if not pm:
                    tally["terminal_without_indexed_trade"] += 1
                    continue
                proof = capture_proof(seed, x["hash"].lower())
                evidence.append(dict(seed=list(seed.key), terminal_pm_fill=pm[0], rpc=RPC, proof=proof))
                tally[
                    "positive_lower_bound" if guaranteed(seed, proof) > 0 else "ambiguous_capital"
                ] += 1
        except (net.SourceError, KeyError, TypeError, ValueError) as e:
            tally["unavailable"] += 1
            return dict(tally=tally, proofs=evidence, error=str(e)[:260])
        return dict(tally=tally, proofs=evidence)

    keys = sorted(roots)
    with ThreadPoolExecutor(4) as pool:
        data = dict(zip(keys, pool.map(one, [(k, roots[k]) for k in keys]), strict=True))
    save(
        snap / "routes.json.gz", dict(from_week=first, to_week=last, asof_exclusive=asof, accounts=data)
    )


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    p.add_argument("--asof", required=True, type=int)
    p.add_argument("--dest", type=Path, default=SNAP)
    args = p.parse_args()
    capture(args.dest, args.from_week, args.to_week, args.asof)


if __name__ == "__main__":
    main()
