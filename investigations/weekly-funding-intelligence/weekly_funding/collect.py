"""Read-only Polygon logs. Persist checked half-open UTC boundaries and individual range receipts."""

import argparse
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import sys
from pathlib import Path

from .common import (
    ETH_GATEWAY,
    ETH_RPC,
    PUBLICNODE,
    REPO,
    RPC,
    SNAP,
    STREAMS,
    bounds,
    hexstr,
    network_query,
    read,
    save,
    weeks,
)

sys.path.insert(0, str(REPO))
from monitoring.phi_monitor import net


def rpc(url, method, params):
    return net.rpc(method, params, urls=[url], timeout=25, tries=2)


@lru_cache(maxsize=1024)
def header(n, chain=137):
    b = rpc(PUBLICNODE if chain == 137 else ETH_RPC, "eth_getBlockByNumber", [hex(n), False])
    if not b or int(b["number"], 16) != n:
        raise ValueError(f"missing block {n}")
    return [n, int(b["timestamp"], 16), hexstr(b["hash"], 64)]


@lru_cache(maxsize=128)
def boundary(t, chain=137):
    # Llama gives a hint. Both adjacent timestamps are checked against actual headers.
    network = "polygon" if chain == 137 else "ethereum"
    n = int(net.get_json(f"https://coins.llama.fi/block/{network}/{t}", tries=2)["height"])
    for _ in range(32):
        prev, cur = header(n - 1, chain), header(n, chain)
        if prev[1] < t <= cur[1]:
            return [prev, cur]
        n += 1 if cur[1] < t else -1
    raise ValueError(f"cannot bracket {t}")


def pull(url, chain, stream, a, b):
    filt = dict(network_query(chain, stream), fromBlock=hex(a), toBlock=hex(b))
    rows = rpc(url, "eth_getLogs", [filt])
    if not isinstance(rows, list) or len(rows) >= 10000:
        raise ValueError("log result missing or potentially capped")
    out = []
    for row in rows:
        n = int(row["blockNumber"], 16)
        if not a <= n <= b or row.get("removed") is not False:
            raise ValueError("off-range or noncanonical log")
        h = hexstr(row["blockHash"], 64)
        if "blockTimestamp" in row:
            t = int(row["blockTimestamp"], 16)
        else:
            _, t, expected = header(n, chain)
            if expected != h:
                raise ValueError("timestamp/header fork")
        out.append(
            [
                n,
                t,
                h,
                hexstr(row["transactionHash"], 64),
                int(row["logIndex"], 16),
                row["address"].lower(),
                [x.lower() for x in row["topics"]],
                row["data"].lower(),
            ]
        )
    return out


def ranges(chain, stream, a, b, preferred, budget=None):
    if budget is None:
        budget = [128]
    failures = []
    fallback = PUBLICNODE if chain == 137 else ETH_RPC
    for url in dict.fromkeys([preferred, fallback]):
        if url == fallback and b - a >= 10000:
            continue
        if budget[0] <= 0:
            return [], [], [[a, b, ["per-stream RPC budget exhausted"]]]
        budget[0] -= 1
        try:
            rows = pull(url, chain, stream, a, b)
            return [[a, b, url, len(rows)]], rows, []
        except (net.SourceError, ValueError, KeyError, TypeError) as e:
            failures.append(str(e)[:320])
    if b - a < 500:
        return [], [], [[a, b, failures]]
    mid = (a + b) // 2
    l = ranges(chain, stream, a, mid, preferred, budget)
    r = ranges(chain, stream, mid + 1, b, preferred, budget)
    return tuple(x + y for x, y in zip(l, r))


def collect_week(w, stream, dest, refresh=False, chain=137):
    prefix = "" if chain == 137 else "ethereum-"
    path = dest / w / (prefix + stream + ".json.gz")
    from .events import verified_pack
    from datetime import datetime, timezone

    t0, t1 = bounds(w)
    if t1 > datetime.now(timezone.utc).timestamp():
        raise ValueError("an open UTC week cannot have a final block range")
    old = read(path) if path.exists() else None
    if old is not None:
        verified_pack(old, w, chain, stream)
        if not old["gaps"] and not refresh:
            return
    edges = [boundary(t0, chain), boundary(t1, chain)]
    if old and old["boundaries"] != edges:
        raise ValueError("canonical boundary changed; capture a separate revision")
    a, b = edges[0][1][0], edges[1][0][0]
    step = 100000 if stream == "changenow" else b - a + 1
    todo = [(lo, min(b, lo + step - 1)) for lo in range(a, b + 1, step)]
    coverage, logs, gaps = [], [], []
    if old and old["gaps"]:
        coverage, logs = old["ranges"][:], old["logs"][:]
        todo = [r[:2] for r in old["gaps"]]
    budget = [128]
    for lo, hi in todo:
        spans, data, missed = ranges(chain, stream, lo, hi, RPC if chain == 137 else ETH_GATEWAY, budget)
        coverage.extend(spans)
        logs.extend(data)
        gaps.extend(missed)
    coverage.sort()
    logs.sort(key=lambda x: (x[0], x[4]))
    if any(not t0 <= row[1] < t1 for row in logs):
        raise ValueError("log timestamp outside requested week")
    pack = dict(
        chain=chain,
        week=w,
        stream=stream,
        query=network_query(chain, stream),
        boundaries=edges,
        ranges=coverage,
        gaps=gaps,
        logs=logs,
    )
    verified_pack(pack, w, chain, stream)
    if old and not old["gaps"]:
        if old["logs"] != logs or gaps:
            raise ValueError("refreshed evidence changed or regressed; use a new snapshot directory")
        return
    save(path, pack)
    print(w, chain, stream, len(logs), "logs,", len(gaps), "gaps", flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--from-week", required=True)
    p.add_argument("--to-week", required=True)
    p.add_argument("--dest", type=Path, default=SNAP)
    p.add_argument("--workers", type=int, choices=range(1, 7), default=2)
    p.add_argument("--refresh", action="store_true")
    p.add_argument("--chain", type=int, choices=(1, 137), default=137)
    args = p.parse_args()
    gateways = (PUBLICNODE, RPC) if args.chain == 137 else (ETH_RPC, ETH_GATEWAY)
    if any(int(rpc(url, "eth_chainId", []), 16) != args.chain for url in gateways):
        raise ValueError("RPC chain ID mismatch")
    work = [(w, s) for w in weeks(args.from_week, args.to_week) for s in STREAMS]
    with ThreadPoolExecutor(args.workers) as pool:
        futures = [pool.submit(collect_week, w, s, args.dest, args.refresh, args.chain) for w, s in work]
        for f in futures:
            f.result()


if __name__ == "__main__":
    main()
