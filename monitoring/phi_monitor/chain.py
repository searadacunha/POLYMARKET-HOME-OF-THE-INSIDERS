"""Polygon reads: exchange fills (OrderFilled, protocol v2), token transfers to a proxy, Safe owners.

One OrderFilled log is one order being filled, seen from the order owner (`maker` in the event). The taker's own order
appears as its own log, with the exchange as counterparty. One log therefore equals one row of the Polymarket data API
(`/v2/trades?taker_only=false`): a purchase of a token appears once, as a BUY of the buyer, maker or taker.
Addresses below were read from live receipts on 2026-11-13 and match docs.polymarket.com/resources/contracts.
"""
from functools import lru_cache

from . import net

EXCHANGES = ["0xe111180000d2663c0091e4f400237545b87b996b",   # CTF Exchange
             "0xe2222d279d744050d28e00520010520000310f59",   # Neg Risk CTF Exchange
             "0xe3333700ca9d93003f00f0f71f8515005f6c00aa"]   # ExchangeV3 of Polymarket Protocol V2: same OrderFilled event; about 1 % of
                                                             # the fills on 2026-11-14, new markets move to it from 2026-11-23
# keccak256("OrderFilled(bytes32,address,address,uint8,uint256,uint256,uint256,uint256,bytes32,bytes32)")
ORDER_FILLED = "0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee"
TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"  # ERC-20 Transfer(address,address,uint256)
USDC = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"                              # native USDC on Polygon, 6 decimals
USDC_E = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"                            # bridged USDC.e, 6 decimals
PUSD = "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"                              # Polymarket collateral since 2026, 6 decimals
STABLES = [USDC, USDC_E, PUSD]
ZERO = "0x" + "0" * 40
# Old log ranges: only this public gateway accepted wide ranges on 2026-11-13 (others: 50 blocks, or no archive)
WIDE_RPC = ["https://gateway.tenderly.co/public/polygon", "https://polygon.drpc.org"]
GET_OWNERS = "0xa0e67e2b"                                                         # Safe getOwners()


def _addr(topic):
    return "0x" + topic[-40:]


def decode_fill(log):
    """OrderFilled v2 log -> fill dict, or None for a log marked removed (reorganisation). Raises on an unexpected shape."""
    if log.get("removed"):
        return None
    t, d = log["topics"], log["data"][2:]
    if t[0] != ORDER_FILLED or len(t) != 4 or len(d) < 64 * 4 or len(d) % 64:
        raise ValueError(f"not an OrderFilled v2 log: {log.get('transactionHash')} #{log.get('logIndex')}")
    w = [int(d[i:i + 64], 16) for i in range(0, 64 * 4, 64)]
    if w[0] not in (0, 1):
        raise ValueError(f"unknown side {w[0]} in {log['transactionHash']}")
    cash, shares = (w[2], w[3]) if w[0] == 0 else (w[3], w[2])          # BUY: the order gives collateral and receives tokens
    if shares == 0:
        raise ValueError(f"zero shares in {log['transactionHash']}")
    return {"tx": log["transactionHash"], "log_index": int(log["logIndex"], 16), "block": int(log["blockNumber"], 16),
            "ts": int(log["blockTimestamp"], 16) if log.get("blockTimestamp") else None, "exchange": log["address"].lower(),
            "wallet": _addr(t[2]), "counterparty": _addr(t[3]), "token_id": str(w[1]), "side": "BUY" if w[0] == 0 else "SELL",
            "shares": shares / 1e6, "cash": cash / 1e6, "price": cash / shares}


def head():
    return int(net.rpc("eth_blockNumber", []), 16)


@lru_cache(maxsize=4096)
def block_ts(number):
    return int(net.rpc("eth_getBlockByNumber", [hex(number), False])["timestamp"], 16)


def fills(from_block, to_block, bad=None):
    """All fills of the exchanges in [from_block, to_block], in chain order. Block times are filled in when the node omits them.
    With a list as `bad`, a log that cannot be decoded is appended to it instead of raising: the caller journals it, and one
    strange log no longer stops the feed at the same block on every restart."""
    logs = net.rpc("eth_getLogs", [{"fromBlock": hex(from_block), "toBlock": hex(to_block), "address": EXCHANGES, "topics": [ORDER_FILLED]}])
    out, times = [], {}
    for log in logs:
        try:
            f = decode_fill(log)
        except ValueError as e:
            if bad is None:
                raise
            bad.append({"tx": log.get("transactionHash"), "log_index": log.get("logIndex"), "why": str(e)[:120]}); continue
        if f is None:
            continue
        if f["ts"] is None:
            f["ts"] = times.get(f["block"]) or times.setdefault(f["block"], block_ts(f["block"]))
        out.append(f)
    return sorted(out, key=lambda f: (f["block"], f["log_index"]))


def block_at(ts):
    """Last block whose timestamp is <= ts. Bracket by growing steps, then bisect: about 30 cached calls."""
    hi = head()
    if block_ts(hi) <= ts:
        return hi
    lo, step = hi, 200_000
    while lo > 1 and block_ts(lo) > ts:
        hi, lo, step = lo, max(1, lo - step), step * 4
    while hi - lo > 1:                                    # invariant: block_ts(lo) <= ts < block_ts(hi)
        mid = (lo + hi) // 2
        if block_ts(mid) <= ts:
            lo = mid
        else:
            hi = mid
    return lo


def transfers_to(address, from_block, to_block, tokens=None, chunk=40000):
    """Transfers of the official collateral tokens received by `address`: who paid, when, how much (6 decimals).
    Only the listed token contracts count: look-alike tokens and zero-value spam are ignored by construction."""
    topic = "0x" + "0" * 24 + address[2:].lower(); out = []
    for a in range(from_block, to_block + 1, chunk):
        logs = net.rpc("eth_getLogs", [{"fromBlock": hex(a), "toBlock": hex(min(to_block, a + chunk - 1)), "address": tokens or STABLES,
                                        "topics": [TRANSFER, None, topic]}], urls=WIDE_RPC)
        out += [{"tx": l["transactionHash"], "log_index": int(l["logIndex"], 16), "block": int(l["blockNumber"], 16),
                 "ts": int(l["blockTimestamp"], 16) if l.get("blockTimestamp") else None, "payer": _addr(l["topics"][1]),
                 "to": address.lower(), "token": l["address"].lower(), "amount": int(l["data"], 16) / 1e6}
                for l in logs if not l.get("removed") and int(l["data"], 16) > 0]
    return out


def safe_owners(proxy):
    """Owner keys of a Safe proxy, or None when the address does not answer getOwners() (deposit wallet, plain key)."""
    try:
        raw = net.rpc("eth_call", [{"to": proxy, "data": GET_OWNERS}, "latest"])
    except net.SourceError:
        return None
    d = raw[2:]
    if len(d) < 128:
        return None
    n = int(d[64:128], 16)
    return ["0x" + d[128 + 64 * i:192 + 64 * i][-40:] for i in range(n)]


def account_kind(address, block=None):
    """Behavioural description of a payer: code present, outgoing transaction count. Never a name, never a person.
    With a block number, the count is read as of that block when a node serves the old state; otherwise the latest count is used
    and flagged, because a count read today is not what an observer saw then."""
    code = net.rpc("eth_getCode", [address, "latest"])
    as_of = "latest"
    if block is not None:
        try:
            nonce = int(net.rpc("eth_getTransactionCount", [address, hex(block)], urls=WIDE_RPC), 16); as_of = block
        except net.SourceError:
            nonce = int(net.rpc("eth_getTransactionCount", [address, "latest"]), 16)
    else:
        nonce = int(net.rpc("eth_getTransactionCount", [address, "latest"]), 16)
    kind = "mint" if address.lower() == ZERO else ("contract" if code not in ("0x", "0x0") else ("high_volume_key" if nonce >= 1000 else "key"))
    return {"address": address.lower(), "kind": kind, "nonce": nonce, "nonce_as_of": as_of}
