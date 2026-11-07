"""tg-fetch: the only network tool given to Claude missions.

Read-only by construction: GET on an allowlist of public hosts and read-only JSON-RPC
methods. Every response is archived in the mission's evidence folder under its SHA-256,
so a report can cite primary sources that the supervisor can re-check byte for byte.
Self-contained (stdlib only) because it runs with `python -I`.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

GET_HOSTS = {
    "data-api.polymarket.com", "gamma-api.polymarket.com", "clob.polymarket.com",
    "api.trongrid.io", "apilist.tronscanapi.com", "api.relay.link", "dln.debridge.finance",
    "stats-api.dln.trade", "eth.blockscout.com", "explorer.optimism.io",
    "metadata.services.blockscout.com", "api.github.com", "raw.githubusercontent.com",
}
RPC = {
    "polygon": ["https://polygon.drpc.org", "https://polygon-bor-rpc.publicnode.com"],
    "ethereum": ["https://eth.drpc.org", "https://ethereum-rpc.publicnode.com"],
    "base": ["https://base.drpc.org", "https://mainnet.base.org"],
    "arbitrum": ["https://arbitrum-one-rpc.publicnode.com", "https://arbitrum.drpc.org"],
    "optimism": ["https://optimism.drpc.org", "https://optimism-rpc.publicnode.com"],
    "bsc": ["https://bsc-dataseed.bnbchain.org", "https://56.rpc.thirdweb.com"],
    "solana": ["https://api.mainnet-beta.solana.com"],
}
EVM_METHODS = {"eth_getTransactionReceipt", "eth_getTransactionByHash", "eth_getLogs", "eth_getBalance",
               "eth_call", "eth_getCode", "eth_blockNumber", "eth_getBlockByNumber", "eth_getBlockByHash",
               "eth_getTransactionCount", "eth_chainId", "trace_transaction", "debug_traceTransaction"}
SOLANA_METHODS = {"getTransaction", "getSignaturesForAddress", "getAccountInfo", "getBalance",
                  "getTokenAccountsByOwner", "getSlot", "getBlockTime", "getTokenAccountBalance"}
MAX_CALLS = int(os.getenv("TRIAGENT_FETCH_MAX_CALLS", "400"))
MAX_BYTES = int(float(os.getenv("TRIAGENT_FETCH_MAX_MB", "50")) * 1_000_000)
PRINT_CHARS = 40_000


def mission_dir() -> Path:
    d = Path(os.getenv("TRIAGENT_MISSION_DIR") or os.getcwd())
    if not (d / "MISSION.md").is_file():
        sys.exit("tg-fetch: not inside a TriAgent mission folder")
    return d


def budget(evdir: Path) -> tuple[int, int]:
    index = evdir / "index.jsonl"
    if not index.is_file():
        return 0, 0
    rows = [json.loads(line) for line in index.read_text().splitlines() if line.strip()]
    return len(rows), sum(r.get("bytes", 0) for r in rows)


def archive(evdir: Path, ref: dict, status: int, raw: bytes) -> str:
    sha = hashlib.sha256(raw).hexdigest()
    (evdir / f"{sha}.raw").write_bytes(raw)
    entry = {"sha256": sha, "fetched_at": int(time.time()), "status": status, "bytes": len(raw), **ref}
    with (evdir / "index.jsonl").open("a") as f:
        f.write(json.dumps(entry, sort_keys=True) + "\n")
    return sha


def call(url: str, body: dict | None) -> tuple[int, bytes]:
    data = None if body is None else json.dumps(body).encode()
    headers = {"accept": "application/json", "user-agent": "triagent-research/1.0 (read-only)"}
    if data:
        headers["content-type"] = "application/json"
    for attempt in range(4):
        req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
        try:
            with urllib.request.urlopen(req, timeout=45) as resp:
                return resp.status, resp.read(MAX_BYTES)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 502, 503, 504) and attempt < 3:
                time.sleep(float(exc.headers.get("Retry-After") or 2 ** (attempt + 1)))
                continue
            return exc.code, exc.read(200_000)
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < 3:
                time.sleep(2 ** (attempt + 1))
                continue
            return 0, json.dumps({"network_error": str(exc)}).encode()
    return 0, b"{}"


def emit(sha: str, status: int, raw: bytes, evdir: Path):
    text = raw.decode("utf-8", "replace")
    print(f"[evidence sha256={sha} http={status} bytes={len(raw)} file={evdir / (sha + '.raw')}]")
    print(text[:PRINT_CHARS] + (f"\n[truncated: use `tg-fetch show {sha} OFFSET` to read more]" if len(text) > PRINT_CHARS else ""))


def main(argv: list[str]) -> int:
    if not argv or argv[0] not in ("get", "rpc", "show", "list"):
        print(__doc__)
        print("usage: tg-fetch get URL | rpc CHAIN METHOD [PARAMS_JSON] | show SHA256 [OFFSET] | list")
        return 2
    mdir = mission_dir()
    evdir = mdir / "evidence"
    evdir.mkdir(exist_ok=True)
    if argv[0] == "list":
        print((evdir / "index.jsonl").read_text() if (evdir / "index.jsonl").is_file() else "(no evidence yet)")
        return 0
    if argv[0] == "show":
        sha = argv[1] if len(argv) > 1 else ""
        if not (len(sha) == 64 and all(c in "0123456789abcdef" for c in sha)):
            return print("show: expects a sha256") or 2
        offset = int(argv[2]) if len(argv) > 2 else 0
        text = (evdir / f"{sha}.raw").read_bytes().decode("utf-8", "replace")
        print(text[offset:offset + PRINT_CHARS])
        return 0
    calls, used = budget(evdir)
    if calls >= MAX_CALLS or used >= MAX_BYTES:
        print(f"tg-fetch: mission fetch budget exhausted ({calls} calls, {used} bytes)")
        return 3
    if argv[0] == "get":
        url = argv[1] if len(argv) > 1 else ""
        parts = urllib.parse.urlsplit(url)
        if parts.scheme != "https" or parts.hostname not in GET_HOSTS:
            print(f"tg-fetch: host not allowed ({parts.hostname}); allowed: {sorted(GET_HOSTS)}")
            return 2
        status, raw = call(url, None)
        sha = archive(evdir, {"kind": "get", "url": url}, status, raw)
        emit(sha, status, raw, evdir)
        return 0 if 200 <= status < 300 else 1
    chain = argv[1] if len(argv) > 1 else ""
    method = argv[2] if len(argv) > 2 else ""
    allowed = SOLANA_METHODS if chain == "solana" else EVM_METHODS
    if chain not in RPC or method not in allowed:
        print(f"tg-fetch: chain/method not allowed; chains {sorted(RPC)}; methods {sorted(allowed)}")
        return 2
    try:
        params = json.loads(argv[3]) if len(argv) > 3 else []
    except json.JSONDecodeError as exc:
        print(f"tg-fetch: PARAMS_JSON is not JSON: {exc}")
        return 2
    body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params}
    status, raw = 0, b""
    for endpoint in RPC[chain]:
        status, raw = call(endpoint, body)
        if status == 200 and b'"error"' not in raw[:200]:
            break
    sha = archive(evdir, {"kind": "rpc", "chain": chain, "method": method, "params": params,
                          "endpoint": endpoint}, status, raw)
    emit(sha, status, raw, evdir)
    return 0 if status == 200 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
