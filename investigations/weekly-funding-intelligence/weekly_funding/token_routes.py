"""Verify stablecoin forwarding to a documented trading proxy, plus exact Relay order-key searches."""

import argparse
from collections import defaultdict
from pathlib import Path
from .accounts import registry
from .archive import native_archive
from .collect import net, rpc
from .common import (
    REPO,
    RPC,
    SNAP,
    STREAMS,
    TOKENS,
    TRANSFER,
    addr_topic,
    address_word,
    bounds,
    hexstr,
    read,
    save,
    weeks,
)
from .events import load_stream

RELAY = REPO / "investigations/ballon-dor-census/sources/derived/relay.json"


def amount_onward(seed, raw, ledger, opening):
    # Reconstruct same-token flow from before the seed block to the final log.
    # Credit only a pass-through with zero initial balance and no intervening competing flows.
    if int(opening, 16) != 0 or raw["address"].lower() != seed.asset or raw["removed"] is not False:
        return 0
    start = (seed.block, seed.idx)
    end = int(raw["blockNumber"], 16), int(raw["logIndex"], 16)
    if end <= start or raw["topics"][:2] != [TRANSFER, addr_topic(seed.recipient)]:
        return 0
    checked = {}
    for r in ledger:
        if r["address"].lower() != seed.asset or r["removed"] is not False or r["topics"][0] != TRANSFER:
            raise ValueError("invalid intermediate ledger")
        key = r["transactionHash"], int(r["logIndex"], 16)
        if key in checked and checked[key] != r:
            raise ValueError("conflicting intermediate log")
        checked[key] = r
    events = [
        r
        for r in checked.values()
        if (int(r["blockNumber"], 16), int(r["logIndex"], 16)) <= end and int(r["data"], 16) > 0
    ]
    events.sort(key=lambda r: (int(r["blockNumber"], 16), int(r["logIndex"], 16)))
    if len(events) != 2:
        return 0
    source, dest = events
    if (
        source["transactionHash"],
        int(source["logIndex"], 16),
        source["topics"],
        int(source["data"], 16),
    ) != (
        seed.tx,
        seed.idx,
        [TRANSFER, addr_topic(seed.sender), addr_topic(seed.recipient)],
        seed.units,
    ) or dest != raw:
        return 0
    onward = int(raw["data"], 16)
    return onward if 0 < onward <= seed.units else 0


def capture(snap, first, last):
    _, owners = registry(snap)
    _, end = bounds(last)
    keys, roots = {}, defaultdict(list)
    historical, _ = native_archive()
    for w in weeks(first, last):
        for chain in (1, 137):
            for stream in STREAMS:
                events, _ = load_stream(snap, w, chain, stream)
                for e in events:
                    keys[(e.chain, e.tx)] = True
                    if chain == 137 and e.recipient in owners and e.asset in TOKENS:
                        roots[(e.recipient, e.asset)].append(e)
        for e in historical.get(w, []):
            keys[(1, e.tx)] = True
    # The repository's Relay deposit orders can join on the exact origin transaction.
    # Flag any hit for independent two-leg receipt replay before assigning it to a wallet.
    origins = set()
    hits = set()
    for v in read(RELAY).values():
        for r in v["requests"]:
            data = r.get("data", {})
            currency = data.get("metadata", {}).get("currencyOut", {}).get("currency", {})
            if r.get("status") != "success" or currency.get("chainId") != 137:
                continue
            for tx in data.get("inTxs", []):
                key = (tx["chainId"], tx["hash"].lower())
                origins.add(key)
                if key in keys:
                    hits.add((r["id"], *key))
    pack = {
        "from_week": first,
        "to_week": last,
        "relay_origin_keys": len(origins),
        "relay_exact_hits": sorted(hits),
        "pairs": sorted(owners.items()),
        "weeks": {},
        "candidates": [],
    }
    for w in weeks(first, last):
        p = snap / w / "changenow.json.gz"
        if not p.exists():
            continue
        bounds_ = read(p)["boundaries"]
        a, b = bounds_[0][1][0], bounds_[1][0][0]
        filt = dict(
            fromBlock=hex(a),
            toBlock=hex(b),
            address=sorted(TOKENS),
            topics=[
                TRANSFER,
                sorted(map(addr_topic, owners)),
                sorted(map(addr_topic, set(owners.values()))),
            ],
        )
        try:
            rows = rpc(RPC, "eth_getLogs", [filt])
            if not isinstance(rows, list) or len(rows) >= 10000:
                raise ValueError("ambiguous indexed-forward page")
            pack["weeks"][w] = {"status": "SCANNED", "range": [a, b], "logs": len(rows)}
            for raw in rows:
                mid, dst = [address_word(hexstr(t, 64)[2:]) for t in raw["topics"][1:]]
                if owners.get(mid) != dst or int(raw["data"], 16) <= 0:
                    continue
                n = int(raw["blockNumber"], 16)
                ts = (
                    int(raw["blockTimestamp"], 16)
                    if raw.get("blockTimestamp")
                    else int(rpc(RPC, "eth_getBlockByNumber", [hex(n), False])["timestamp"], 16)
                )
                candidates = [
                    s
                    for s in roots[(mid, raw["address"].lower())]
                    if 0 <= ts - s.ts <= 604800 and (s.block, s.idx) < (n, int(raw["logIndex"], 16))
                ]
                if not candidates:
                    continue
                s = max(candidates, key=lambda s: (s.block, s.idx))
                evidence = dict(seed=list(s.key), out=raw, time=ts, proxy=dst)
                try:
                    opening = rpc(
                        RPC,
                        "eth_call",
                        [dict(to=s.asset, data="0x70a08231" + addr_topic(mid)[2:]), hex(s.block - 1)],
                    )
                    ledger = []
                    for topics in ([TRANSFER, addr_topic(mid)], [TRANSFER, None, addr_topic(mid)]):
                        ls = rpc(
                            RPC,
                            "eth_getLogs",
                            [
                                dict(
                                    address=s.asset,
                                    topics=topics,
                                    fromBlock=hex(s.block),
                                    toBlock=hex(n),
                                )
                            ],
                        )
                        if len(ls) >= 10000:
                            raise ValueError("intermediate ledger capped")
                        ledger.extend(ls)
                    evidence.update(
                        opening=opening,
                        ledger=ledger,
                        attributable_units=amount_onward(s, raw, ledger, opening),
                    )
                except (net.SourceError, KeyError, ValueError, TypeError) as e:
                    evidence["error"] = str(e)[:260]
                pack["candidates"].append(evidence)
        except (net.SourceError, KeyError, ValueError, TypeError) as e:
            pack["weeks"][w] = {"status": "UNKNOWN", "error": str(e)[:260]}
    save(snap / "token_routes.json.gz", pack)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    p.add_argument("--dest", type=Path, default=SNAP)
    a = p.parse_args()
    capture(a.dest, a.from_week, a.to_week)
