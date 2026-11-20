#!/usr/bin/env python3
"""Fetch the transactions of the two verified transfers from two public RPC nodes per chain (network, read-only).

Not needed to verify the note: verify.py reads evidence/receipts/. A node that has no answer is skipped and logged;
a transaction is written only when two different nodes returned its receipt.

usage: python3 -I collect_receipts.py
"""
import json
import time
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / "evidence" / "receipts"
NODES = {
    "ethereum": ["https://eth.drpc.org", "https://mainnet.gateway.tenderly.co", "https://ethereum-rpc.publicnode.com", "https://1rpc.io/eth"],
    "polygon": ["https://polygon.drpc.org", "https://polygon.gateway.tenderly.co", "https://polygon-bor-rpc.publicnode.com", "https://1rpc.io/matic"],
}
TXS = [  # the two transfers of REPORT.md, leg by leg
    ("polygon", "0xc716f77872770540b5adf34aef6a694aa2f8085fd5697cfca6f810f18b58d73e"),
    ("ethereum", "0xdb13cf16ebea06f3bcc37ec86ab84ea9f770476e026278c0466d2dbdcfb63ad7"),
    ("ethereum", "0xa41680707227f6697248fd9ee404d454edb3efe821282f57d160f7c40f856a47"),
    ("polygon", "0xade90fd9b144864fdf66fdcfc18f40de0053c9c7c78986c02c3dd907247d8223"),
    ("polygon", "0xf99eddffe076296abeeef8bc8236acea0c86c7e183a470c0b633f1647b4e3b14"),
    ("polygon", "0x473aef761609e901ba8eb51fc93119b445de00a31903068f7a8d46afcdd7320b"),
    ("polygon", "0x00704662785e55c0aceff117cd806a968f435163ab0d4568a9a701c61da1b7ea"),
]
DEPOSIT_ADDRESS = "0x29ec3716a63cf27c7873831e9458f0486e819031"
ACCOUNTS = ("0xfd66d7ed45d7962ad009e669cdaec9319e38fb6d", "0x1fa1be3eab546e06e4290839bf4c1d7abfbf1fa9",
            "0xecb14ac6e9ca447ce2f2912e6217b43d7b655da3", "0xe25b9180f5687aa85bd94ee309bb72a464320f1b")


def call(url, method, params):
    body = json.dumps({"jsonrpc": "2.0", "id": 1, "method": method, "params": params}).encode()
    request = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "User-Agent": "phi-research-note"})
    try:
        with urllib.request.urlopen(request, timeout=40) as response:
            return json.load(response).get("result")
    except Exception as error:  # a failed node is not an empty answer: it is skipped, and two answers are required
        print("   node failed:", url, repr(error)[:80])
        return None
    finally:
        time.sleep(0.7)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for chain, tx_hash in TXS:
        nodes = {}
        for url in NODES[chain]:
            receipt = call(url, "eth_getTransactionReceipt", [tx_hash])
            if not receipt:
                continue
            tx = call(url, "eth_getTransactionByHash", [tx_hash])
            block = call(url, "eth_getBlockByNumber", [receipt["blockNumber"], False])
            if tx and block:
                nodes[url] = {"tx": tx, "receipt": receipt, "block_timestamp": int(block["timestamp"], 16)}
            if len(nodes) == 2:
                break
        if len(nodes) < 2:
            raise SystemExit(f"fewer than two nodes answered for {chain} {tx_hash}")
        (OUT / f"{chain}_{tx_hash}.json").write_text(json.dumps({"chain": chain, "tx_hash": tx_hash, "nodes": nodes}, indent=1, sort_keys=True) + "\n")
        print("ok", chain, tx_hash[:12], list(nodes))
    codes = {}
    for chain in NODES:
        for url in NODES[chain]:
            code = call(url, "eth_getCode", [DEPOSIT_ADDRESS, "latest"])
            nonce = call(url, "eth_getTransactionCount", [DEPOSIT_ADDRESS, "latest"])
            if code and nonce:
                codes.setdefault(chain, {})[url] = {"code": code, "nonce": int(nonce, 16)}
            if len(codes.get(chain, {})) == 2:
                break
    (OUT / "deposit_address_code.json").write_text(json.dumps({"address": DEPOSIT_ADDRESS, "chains": codes}, indent=1, sort_keys=True) + "\n")
    print("ok code", {c: list(v) for c, v in codes.items()})
    accounts = {}
    for address in ACCOUNTS:
        for url in NODES["polygon"]:
            code = call(url, "eth_getCode", [address, "latest"])
            if code:
                accounts.setdefault(address, {})[url] = code
            if len(accounts.get(address, {})) == 2:
                break
    (OUT / "accounts_code_polygon.json").write_text(json.dumps(accounts, indent=1, sort_keys=True) + "\n")
    print("ok accounts", {a[:10]: len(v) for a, v in accounts.items()})


if __name__ == "__main__":
    main()
