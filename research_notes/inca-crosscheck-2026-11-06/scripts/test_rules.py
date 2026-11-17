"""Positive and negative controls of rules.py (PLAN_CONTROLS.md). Run: python3 -I scripts/test_rules.py"""
import json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from rules import withdrawal_recipients, deposit_funders, links  # noqa: E402

PR27 = HERE.parent.parent / "iran-cluster-e-network-2026-11-05" / "evidence" / "polygon"


def receipt(h):
    return json.loads((PR27 / f"{h}.eth_getTransactionReceipt.json").read_text())["result"]


r1 = withdrawal_recipients(receipt("0x014ba2e43ddf94aaedf272d0a769893c8fb197caa8bb13f4050a0f37b89ae3b6"),
                           "0xcb18ea2923d957bd9cf049cce60a87638722f867")
assert r1 == [("0x519fa16e9897132b7633f634b76306a327839e06", 19811.868294, "USDC")], r1
r2 = withdrawal_recipients(receipt("0x03d11843c2a23996cabc601a52ecd4f7f52d0125cd74616dccc068fbd161c404"),
                           "0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a")
assert r2 == [("0x9063493a4233006be654da772ef4dc38720cac55", 9998.976392, "USDC")], r2
# the same receipt read for another proxy gives nothing
assert withdrawal_recipients(receipt("0x03d11843c2a23996cabc601a52ecd4f7f52d0125cd74616dccc068fbd161c404"),
                             "0xcb18ea2923d957bd9cf049cce60a87638722f867") == []

# synthetic deposit through the pool: X pays USDC to the pool, the pool pays USDC.e to the proxy
T = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
pad = lambda a: "0x" + "0" * 24 + a[2:]
P, X, POOL = "0x" + "11" * 20, "0x" + "22" * 20, "0xd36ec33c8bed5a9f7b6630855f1533455b98a418"
syn = {"logs": [
    {"address": "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359", "topics": [T, pad(X), pad(POOL)], "data": hex(5_000_000)},
    {"address": "0x2791bca1f2de4661ed88a30c99a7a9449aa84174", "topics": [T, pad(POOL), pad(P)], "data": hex(4_990_000)}]}
assert deposit_funders(syn, P) == [(X, 5.0, "USDC")]

# M3: two matched legs are a pair; one leg, or a 4 % fee, is not; a same-hash leg is direct
A, B, C = "0xa", "0xb", "0xc"
row = lambda w, t, ts, u, h: {"wallet": w, "type": t, "ts": ts, "usdc": u, "hash": h}
rows = [row(A, "WITHDRAWAL", 0, 10, "h1"), row(B, "DEPOSIT", 1100, 9.88, "h2"),
        row(A, "WITHDRAWAL", 700, 1138, "h3"), row(B, "DEPOSIT", 1800, 1124.77, "h4"),
        row(A, "WITHDRAWAL", 5000, 100, "h5"), row(C, "DEPOSIT", 5100, 99, "h6"),
        row(C, "WITHDRAWAL", 9000, 100, "h7"), row(A, "DEPOSIT", 9100, 96, "h8"),
        row(C, "WITHDRAWAL", 9500, 100, "h9"), row(A, "DEPOSIT", 9600, 95.9, "h10"),
        row(B, "WITHDRAWAL", 20000, 50, "h11"), row(C, "DEPOSIT", 20000, 50, "h11")]
direct, matched = links(rows)
assert set(matched) == {(A, B)}, matched
assert [(a["wallet"], b["wallet"]) for a, b in direct] == [(B, C)], direct
print("test_rules: 8 checks passed")
