"""Extraction rules fixed by PLAN_CONTROLS.md. Same code for the Inca accounts and the controls."""
from collections import defaultdict

TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TOKENS = {"0x2791bca1f2de4661ed88a30c99a7a9449aa84174": "USDC.e", "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359": "USDC"}
POOL = "0xd36ec33c8bed5a9f7b6630855f1533455b98a418"  # Uniswap USDC/USDC.e pool used by Polymarket withdrawals
MATCH_S, MATCH_FEE = 3600, 0.97


def transfers(receipt):
    out = []
    for lg in receipt["logs"]:
        if lg["address"].lower() in TOKENS and lg["topics"] and lg["topics"][0] == TRANSFER and len(lg["topics"]) == 3:
            out.append(("0x" + lg["topics"][1][-40:], "0x" + lg["topics"][2][-40:],
                        int(lg["data"], 16) / 1e6, TOKENS[lg["address"].lower()]))
    return out


def withdrawal_recipients(receipt, proxy):
    """[(recipient, amount, token)]; a hop through the pool is followed to the pool's outgoing transfer."""
    t, proxy, res = transfers(receipt), proxy.lower(), []
    for f, to, amt, tok in t:
        if f != proxy or to == proxy:
            continue
        if to == POOL:
            res += [(to2, a2, k2) for f2, to2, a2, k2 in t if f2 == POOL and to2 not in (proxy, POOL)]
        else:
            res.append((to, amt, tok))
    return res


def deposit_funders(receipt, proxy):
    """[(funder, amount, token)]; a hop through the pool is followed to the pool's incoming transfer."""
    t, proxy, res = transfers(receipt), proxy.lower(), []
    for f, to, amt, tok in t:
        if to != proxy or f == proxy:
            continue
        if f == POOL:
            res += [(f2, a2, k2) for f2, to2, a2, k2 in t if to2 == POOL and f2 not in (proxy, POOL)]
        else:
            res.append((f, amt, tok))
    return res


def links(rows):
    """rows: [{wallet, type DEPOSIT|WITHDRAWAL, ts, usdc, hash}].
    Returns (direct, matched): direct = same hash as A's WITHDRAWAL and B's DEPOSIT;
    matched = {(A, B): [(w, d)]} pairs with >= 2 matched legs (B deposits y within MATCH_S after A withdraws x,
    MATCH_FEE * x <= y <= x), each deposit used once, legs with a direct hash excluded."""
    w = [r for r in rows if r["type"] == "WITHDRAWAL"]
    d = [r for r in rows if r["type"] == "DEPOSIT"]
    dh = defaultdict(list)
    for r in d:
        dh[r["hash"]].append(r)
    direct = [(a, b) for a in w for b in dh.get(a["hash"], []) if b["wallet"] != a["wallet"]]
    used, legs = set(), defaultdict(list)
    for a in sorted(w, key=lambda r: r["ts"]):
        if a["hash"] in dh:
            continue
        for b in sorted(d, key=lambda r: r["ts"]):
            if (b["wallet"] != a["wallet"] and b["hash"] not in used and 0 < b["ts"] - a["ts"] <= MATCH_S
                    and MATCH_FEE * a["usdc"] <= b["usdc"] <= a["usdc"]):
                used.add(b["hash"]); legs[(a["wallet"], b["wallet"])].append((a, b)); break
    return direct, {k: v for k, v in legs.items() if len(v) >= 2}
