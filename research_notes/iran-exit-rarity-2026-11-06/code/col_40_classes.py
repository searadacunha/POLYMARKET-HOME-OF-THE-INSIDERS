"""Class of every recipient shared by two or more wallets of one population. Network, one worker.

python3 -I -B code/col_40_classes.py      # after col_30 has finished

Primary class: SERVICE if at least SERVICE_USERS distinct Relay users pay the recipient on its first
SERVICE_PAGES pages, CUSTOMER otherwise. Also recorded, for sensitivity D: whether the recipient has contract
code that is not an EIP-7702 delegation on a destination chain (keyless public RPC, eth_getCode at latest), or
is a Solana account owned by a program other than the System Program, or executable. A destination chain that
no listed RPC serves (Bitcoin, Tron, others) is written in `unchecked_chains`, never read as "no code".
Writes data/classes.json atomically after each recipient. Resumable; a recipient is re-checked when a new
destination chain appears for it.
"""
import json
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (DATA, DELEGATION_PREFIX, ETUDE, RAW, SERVICE_PAGES, SERVICE_USERS, SYSTEM_PROGRAM,  # noqa: E402
                    fetch, flat, is_withdrawal, low, relay_page, select_comparators, write_atomic)

SOLANA = 792703809
RPC = {1: "https://ethereum-rpc.publicnode.com", 10: "https://mainnet.optimism.io", 56: "https://bsc-dataseed.bnbchain.org",
       137: "https://polygon.drpc.org", 8453: "https://mainnet.base.org", 42161: "https://arb1.arbitrum.io/rpc",
       43114: "https://api.avax.network/ext/bc/C/rpc", 59144: "https://rpc.linea.build", 130: "https://mainnet.unichain.org",
       SOLANA: "https://api.mainnet-beta.solana.com"}


def rpc(chain, method, params, out, counters):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    for i in range(6):
        d = fetch(RPC[chain], out, counters, body=body, wait=5)
        if isinstance(d, dict) and "result" in d:
            return d["result"]
        counters["rpc_error"] = counters.get("rpc_error", 0) + 1
        time.sleep(5 * (i + 1))  # an RPC error object is retried, never read as an empty account
    raise SystemExit(f"{method} on {chain}: {str(d)[:200]}")


def relay_users(addr, counters):
    users, cur, n = set(), None, 0
    while n < SERVICE_PAGES:
        u = f"https://api.relay.link/requests/v2?user={addr}&limit=50" + (f"&continuation={cur}" if cur else "")
        rs, cur = relay_page(fetch(u, RAW / "classes" / f"relay_{addr}_p{n:03d}.json", counters), f"recipient {addr} page {n}")
        n += 1
        for r in rs:
            o = flat(r)
            if o["recipient"] == low(addr):
                users.add(o["user"])
        time.sleep(13)
        if not cur:
            return users, n, "END"
    return users, n, "MAX_PAGES"


def targets():
    """Recipients held by >= 2 wallets of one selected population (known groups included) or of the reference."""
    kept, _ = select_comparators()
    pops = [("relay", m["wallets_with_known"]) for m in kept]
    pops.append(("relay_reference", (ETUDE.parent / "iran-cluster-e-network-2026-11-05" / "population.txt").read_text().split()))
    chains, need, missing = defaultdict(set), set(), 0
    for folder, ws in pops:
        holders = defaultdict(set)
        for w in ws:
            p = DATA / folder / f"{w}.json"
            if not p.exists():
                missing += 1
                continue  # that population is excluded by the analysis (exit data incomplete)
            for o in json.loads(p.read_text())["orders"]:
                if is_withdrawal(o, w):
                    holders[o["recipient"]].add(w); chains[o["recipient"]].add(o["d"])
        need |= {r for r, h in holders.items() if len(h) >= 2}
    return sorted(need), chains, missing


def main():
    out = DATA / "classes.json"
    done = json.loads(out.read_text()) if out.exists() else {}
    need, chains, missing = targets()
    print("recipients to classify", len(need), "wallet files missing", missing, flush=True)
    for r in need:
        cs = {c for c in chains[r]}
        if r in done and set(done[r]["chains_seen"]) >= {str(c) for c in cs}:
            continue
        counters, contract, code, unchecked = {}, [], {}, []
        for c in sorted(cs, key=str):
            if c is None or c not in RPC:
                unchecked.append(c); continue
            if c == SOLANA:
                v = rpc(c, "getAccountInfo", [r, {"encoding": "base64", "dataSlice": {"offset": 0, "length": 0}}],
                        RAW / "classes" / f"sol_{r}.json", counters)
                v = v.get("value") if isinstance(v, dict) else None
                code[str(c)] = None if v is None else {"owner": v["owner"], "executable": v["executable"]}
                if v is not None and (v["executable"] or v["owner"] != SYSTEM_PROGRAM):
                    contract.append(f"solana owner {v['owner']}")
            else:
                b = rpc(c, "eth_getCode", [r, "latest"], RAW / "classes" / f"code_{c}_{r}.json", counters)
                if not isinstance(b, str) or not b.startswith("0x"):
                    raise SystemExit(f"eth_getCode {c} {r}: {str(b)[:100]}")
                code[str(c)] = len(b) // 2 - 1
                if b != "0x" and not b.lower().startswith(DELEGATION_PREFIX):
                    contract.append(f"contract on chain {c}")
        users, pages, term = relay_users(r, counters)
        service = len(users) >= SERVICE_USERS
        done[r] = {"class": "SERVICE" if service else "CUSTOMER", "relay_distinct_users": len(users), "relay_pages": pages,
                   "relay_termination": term, "contract": contract, "code": code, "unchecked_chains": unchecked,
                   "chains_seen": sorted(str(c) for c in cs), "http": counters}
        write_atomic(out, json.dumps(done, indent=1, sort_keys=True).encode())
        print(r, done[r]["class"], len(users), contract, unchecked, flush=True)
    print("classified", len(done), "needed", len(need))


if __name__ == "__main__":
    main()
