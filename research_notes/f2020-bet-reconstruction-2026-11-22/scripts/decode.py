"""Offline decoders for Polygon receipts: Polymarket v2 fills, conditional-token transfers, collateral transfers, redemptions.

Layouts were read from live receipts (2026-11-22) and agree with monitoring/phi_monitor/chain.py of this repository:
OrderFilled(bytes32 orderHash, address maker, address taker, uint8 side, uint256 tokenId, uint256 makerAmountFilled,
uint256 takerAmountFilled, uint256 fee, ...). One log per filled order, seen from its owner (`maker`); the taker's own order
has the exchange contract as `taker`. side 0 = BUY (owner pays collateral, receives tokens), 1 = SELL.
"""
from decimal import Decimal

ORDER_FILLED = "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
TRANSFER_SINGLE = "0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62"
TRANSFER_BATCH = "0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb"
PAYOUT_REDEMPTION = "0x2682012a4a4f1973119f1c9b90745d1bd91fa2bab387344f044cb3586864d18d"
CONDITION_RESOLUTION = "0xb44d84d3289691f71497564b85d4233648d9dbae8cbdbb4329f301c3a0185894"
EXCHANGES = {"0xe111180000d2663c0091e4f400237545b87b996b": "CTF Exchange v2",
             "0xe2222d279d744050d28e00520010520000310f59": "Neg Risk CTF Exchange v2",
             "0xe3333700ca9d93003f00f0f71f8515005f6c00aa": "Exchange v3"}
U6 = Decimal(10) ** 6
ZERO = "0x" + "0" * 40


def addr(word):
    return "0x" + word[-40:].lower()


def words(data):
    d = data[2:]
    if len(d) % 64:
        raise ValueError("data is not a whole number of words")
    return [int(d[i:i + 64], 16) for i in range(0, len(d), 64)]


def fill(log):
    t, w = log["topics"], words(log["data"])
    if t[0] != ORDER_FILLED or len(t) != 4 or len(w) < 5 or w[0] not in (0, 1):
        raise ValueError(f"unexpected OrderFilled shape in {log['transactionHash']}#{int(log['logIndex'], 16)}")
    side = "BUY" if w[0] == 0 else "SELL"
    cash, shares = (w[2], w[3]) if side == "BUY" else (w[3], w[2])
    return {"log_index": int(log["logIndex"], 16), "exchange": log["address"].lower(), "order_hash": t[1],
            "owner": addr(t[2]), "counterparty": addr(t[3]), "side": side, "token_id": str(w[1]),
            "shares": Decimal(shares) / U6, "cash": Decimal(cash) / U6, "fee": Decimal(w[4]) / U6,
            "role": "taker" if addr(t[3]) in EXCHANGES else "maker"}


def erc1155(log):
    t = log["topics"]
    if t[0] == TRANSFER_SINGLE:
        w = words(log["data"])
        return [{"log_index": int(log["logIndex"], 16), "operator": addr(t[1]), "from": addr(t[2]), "to": addr(t[3]),
                 "token_id": str(w[0]), "shares": Decimal(w[1]) / U6}]
    if t[0] == TRANSFER_BATCH:
        w = words(log["data"])  # two dynamic arrays: offsets, then length-prefixed ids and values
        ids_at, vals_at = w[0] // 32, w[1] // 32
        n = w[ids_at]
        ids, vals = w[ids_at + 1: ids_at + 1 + n], w[vals_at + 1: vals_at + 1 + n]
        return [{"log_index": int(log["logIndex"], 16), "operator": addr(t[1]), "from": addr(t[2]), "to": addr(t[3]),
                 "token_id": str(i), "shares": Decimal(v) / U6} for i, v in zip(ids, vals)]
    return []


def erc20(log):
    t = log["topics"]
    if t[0] != TRANSFER or len(t) != 3:
        return None
    return {"log_index": int(log["logIndex"], 16), "token": log["address"].lower(), "from": addr(t[1]), "to": addr(t[2]),
            "amount": Decimal(int(log["data"], 16)) / U6}


def redemption(log):
    t = log["topics"]
    if t[0] != PAYOUT_REDEMPTION:
        return None
    w = words(log["data"])  # conditionId, offset(indexSets), payout, then the index set array
    return {"log_index": int(log["logIndex"], 16), "redeemer": addr(t[1]), "collateral": addr(t[2]),
            "condition_id": "0x" + format(w[0], "064x"), "payout": Decimal(w[2]) / U6}


def wallet_view(rec, wallet):
    """Everything in one receipt that moves value for `wallet`: its own filled orders, token and collateral transfers."""
    wallet = wallet.lower()
    out = {"tx": rec["receipt"]["transactionHash"], "block": int(rec["receipt"]["blockNumber"], 16),
           "ts": int(rec["block_timestamp"], 16), "status": int(rec["receipt"]["status"], 16),
           "sender": rec["receipt"]["from"].lower(), "to": (rec["receipt"]["to"] or "").lower(),
           "fills": [], "fills_against": [], "tokens": [], "collateral": [], "redemptions": []}
    for log in rec["receipt"]["logs"]:
        if log.get("removed"):
            continue
        t0 = log["topics"][0] if log["topics"] else None
        if t0 == ORDER_FILLED:
            f = fill(log)
            if f["owner"] == wallet:
                out["fills"].append(f)
            elif f["counterparty"] == wallet:
                out["fills_against"].append(f)
        elif t0 in (TRANSFER_SINGLE, TRANSFER_BATCH):
            out["tokens"] += [x for x in erc1155(log) if wallet in (x["from"], x["to"])]
        elif t0 == TRANSFER:
            x = erc20(log)
            if x and wallet in (x["from"], x["to"]):
                out["collateral"].append(x)
        elif t0 == PAYOUT_REDEMPTION:
            x = redemption(log)
            if x and x["redeemer"] == wallet:
                out["redemptions"].append(x)
    return out


def word_int(hexstr):
    return int(hexstr, 16)
