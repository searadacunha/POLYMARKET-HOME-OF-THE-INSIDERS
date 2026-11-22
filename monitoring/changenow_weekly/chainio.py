"""Block-window reads over public JSON-RPC, Multicall3 views and optional Etherscan v2 lists.

A refusal raises: it never becomes an empty list. Log windows shrink when a node refuses their size and every window
read is returned with its exact block range, so coverage is measured, not assumed. The Etherscan key is read from the
environment only and never enters an error message or a file.
"""
import json
import os
import time
import urllib.parse
from datetime import date, datetime, timedelta, timezone

from phi_monitor import net

TRANSFER = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"   # ERC-20 Transfer(address,address,uint256)
POL_LOG_TRANSFER = "0xe6497e3ee548a3372136af2fcb0696db31fc6cf20260707645068bd3fe97f3c4"  # native POL moves, Polygon only
POL_SYSTEM = "0x0000000000000000000000000000000000001010"
# Relay's escrow emits its own event, not an ERC-20 Transfer. The topics below are the keccak hashes of the named
# signatures (checked against the deposits of 2026-W46): RelayErc20Deposit(address,address,uint256,bytes32) and
# RelayNativeDeposit(address,uint256,bytes32). The depository is shared by every user, so the event's depositor field
# and the token movement of the same transaction are what tie a deposit to one account.
RELAY_DEPOSITORY = "0x4cd00e387622c35bddb9b4c962c136462338bc31"
RELAY_ERC20_DEPOSIT = "0x49fed1d0b752ce30eee63c7a81133f3363b532fec5d4d7dd1ccfd005de4555e1"
RELAY_NATIVE_DEPOSIT = "0x8032066556caf3967d8fec4ad22a2d9e1e9576556b2903a0fcd5b1fd201e3477"
ZERO = "0x" + "0" * 40
MULTICALL3 = "0xca11bde05977b3631167028862be2a173976ca11"
ETHERSCAN = "https://api.etherscan.io/v2/api"

# window = widest log range the first endpoint accepted without a key (measured 2026-11-14); depth = blocks held back
# when the node has no `finalized` tag. etherscan_free: the free plan serves this chain (measured the same day).
# by_contract = a node that serves `window` blocks a call when the filter names at most `contracts` token contracts
# (measured 2026-11-15 with 1,500 addresses in the filter). It is used for such filters only.
CHAINS = {
    1: dict(name="ethereum", native="ETH", llama="ethereum", window=50000, depth=96, etherscan_free=True, explorer="https://etherscan.io",
            rpc=["https://gateway.tenderly.co/public/mainnet"], state=["https://ethereum-rpc.publicnode.com", "https://gateway.tenderly.co/public/mainnet"]),
    137: dict(name="polygon", native="POL", llama="polygon", window=50000, depth=256, etherscan_free=True, explorer="https://polygonscan.com",
              rpc=["https://gateway.tenderly.co/public/polygon", "https://rpc-mainnet.matic.quiknode.pro"],
              state=["https://polygon-bor-rpc.publicnode.com", "https://gateway.tenderly.co/public/polygon"]),
    8453: dict(name="base", native="ETH", llama="base", window=1000, depth=7200, etherscan_free=False, explorer="https://basescan.org",
               rpc=["https://gateway.tenderly.co/public/base"], state=["https://base-rpc.publicnode.com", "https://gateway.tenderly.co/public/base"],
               by_contract=dict(url="https://base-rpc.publicnode.com", window=50000, contracts=10, addresses=1500)),
    42161: dict(name="arbitrum", native="ETH", llama="arbitrum", window=10000, depth=20000, etherscan_free=True, explorer="https://arbiscan.io",
                rpc=["https://gateway.tenderly.co/public/arbitrum", "https://arb1.arbitrum.io/rpc"], state=["https://gateway.tenderly.co/public/arbitrum"]),
    10: dict(name="optimism", native="ETH", llama="optimism", window=10000, depth=7200, etherscan_free=False, explorer="https://optimistic.etherscan.io",
             rpc=["https://gateway.tenderly.co/public/optimism", "https://mainnet.optimism.io"], state=["https://gateway.tenderly.co/public/optimism"]),
    56: dict(name="bsc", native="BNB", llama="bsc", window=500, depth=64, etherscan_free=False, explorer="https://bscscan.com",
             rpc=["https://56.rpc.thirdweb.com"], state=["https://56.rpc.thirdweb.com"]),
    43114: dict(name="avalanche", native="AVAX", llama="avax", window=2000, depth=64, etherscan_free=False, explorer="https://snowtrace.io",
                rpc=["https://api.avax.network/ext/bc/C/rpc"], state=["https://api.avax.network/ext/bc/C/rpc"]),
}
PACE = 0.22          # seconds between calls to one public gateway; it answered 429 above about 5 calls a second
_last = [0.0]


def _pace():
    wait = PACE - (time.time() - _last[0])
    if wait > 0:
        time.sleep(wait)
    _last[0] = time.time()


def rpc(chain, method, params, state=False, urls=None):
    """One JSON-RPC read. `state=True` uses the endpoints kept for latest-state calls, which accept more load."""
    _pace()
    return net.rpc(method, params, urls=urls or CHAINS[chain]["state" if state else "rpc"])


def pad(address):
    return "0x" + "0" * 24 + address[2:].lower()


def week_bounds(week):
    """'2026-W46' -> (start, end) in epoch seconds, Monday 00:00:00 UTC to the next Monday, end exclusive."""
    year, number = week.split("-W")
    monday = date.fromisocalendar(int(year), int(number), 1)
    start = int(datetime(monday.year, monday.month, monday.day, tzinfo=timezone.utc).timestamp())
    return start, start + 7 * 86400


def week_of(ts):
    iso = datetime.fromtimestamp(ts, timezone.utc).isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def next_week(week):
    return week_of(week_bounds(week)[1] + 3600)


def iso(ts):
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def block_time(chain, number):
    block = rpc(chain, "eth_getBlockByNumber", [hex(number), False])
    if not block:
        raise net.SourceError(f"chain {chain}: block {number} not served")
    return int(block["timestamp"], 16)


def safe_head(chain):
    """Last block treated as settled: the node's `finalized` block, or head minus a fixed depth. Returns (number, ts, rule)."""
    try:
        block = rpc(chain, "eth_getBlockByNumber", ["finalized", False])
        if block and block.get("number"):
            return int(block["number"], 16), int(block["timestamp"], 16), "finalized"
    except net.SourceError:
        pass
    number = int(rpc(chain, "eth_blockNumber", []), 16) - CHAINS[chain]["depth"]
    return number, block_time(chain, number), f"head-{CHAINS[chain]['depth']}"


def first_block_at(chain, ts, hi):
    """First block whose timestamp is >= ts, by bisection below `hi` (a block already known to be at or after ts)."""
    lo = 1
    while lo < hi:
        mid = (lo + hi) // 2
        if block_time(chain, mid) < ts:
            lo = mid + 1
        else:
            hi = mid
    return lo


def week_blocks(chain, week, now=None):
    """Block range of the week on one chain, cut at the settled head while the week is still open.
    Returns dict(first, last, closed, head, head_ts, rule): `last` is the last block inside the week that is settled."""
    start, end = week_bounds(week)
    head, head_ts, rule = safe_head(chain)
    if head_ts < start:
        raise net.SourceError(f"chain {chain}: settled head is before the week start")
    first = first_block_at(chain, start, head)
    closed = head_ts >= end
    last = first_block_at(chain, end, head) - 1 if closed else head
    return dict(first=first, last=last, closed=closed, head=head, head_ts=head_ts, rule=rule)


def wide_node(chain, address):
    """The chain's `by_contract` entry when the filter names token contracts it accepts, else None."""
    wide = CHAINS[chain].get("by_contract")
    named = [address] if isinstance(address, str) else list(address or [])
    return wide if wide and 0 < len(named) <= wide["contracts"] else None


def get_logs(chain, first, last, topics, address=None, min_window=20):
    """Every log of [first, last] matching the filter, in chain order, with the list of windows actually read.
    The window halves when the node refuses the range or the answer size; below `min_window` the refusal is raised.
    A filter that names few enough token contracts is sent to the chain's `by_contract` node, which serves wider ranges."""
    wide = wide_node(chain, address)
    widest = wide["window"] if wide else CHAINS[chain]["window"]
    logs, windows, cursor, step = [], [], first, widest
    while cursor <= last:
        end = min(cursor + step - 1, last)
        query = dict(fromBlock=hex(cursor), toBlock=hex(end), topics=topics)
        if address:
            query["address"] = address
        try:
            got = rpc(chain, "eth_getLogs", [query], urls=[wide["url"]]) if wide else rpc(chain, "eth_getLogs", [query])
        except net.SourceError:
            if step <= min_window:
                raise
            step = max(min_window, step // 2)
            continue
        if any(l.get("removed") for l in got):
            raise net.SourceError(f"chain {chain}: removed log in settled range {cursor}-{end}")
        logs += got
        windows.append((cursor, end, len(got)))
        cursor = end + 1
        if step < widest and len(got) < 2000:
            step = min(widest, step * 2)
    return logs, windows


def decode_transfer(log, chain):
    """One ERC-20 Transfer or Polygon native move as a flat row, or None for another shape (ERC-721 has four topics)."""
    topics = log["topics"]
    if not topics:
        return None
    base = dict(chain=chain, block=int(log["blockNumber"], 16), block_hash=log["blockHash"], tx=log["transactionHash"].lower(),
                log_index=int(log["logIndex"], 16), ts=int(log["blockTimestamp"], 16) if log.get("blockTimestamp") else None)
    if topics[0] == TRANSFER and len(topics) == 3 and len(log["data"]) == 66:
        return dict(base, token=log["address"].lower(), src="0x" + topics[1][-40:], dst="0x" + topics[2][-40:], raw=int(log["data"], 16))
    if topics[0] == POL_LOG_TRANSFER and len(topics) == 4 and log["address"].lower() == POL_SYSTEM:
        return dict(base, token="native", src="0x" + topics[2][-40:], dst="0x" + topics[3][-40:], raw=int(log["data"][2:66], 16))
    return None


def decode_relay_deposit(log):
    """One RelayErc20Deposit of the escrow as a flat row, or None for any other log.
    Strict shape: the escrow contract, exactly one topic (the event hash) and four data words
    (depositor, token, amount, order id). A look-alike event elsewhere cannot pass for a deposit."""
    topics = log.get("topics") or []
    data = log.get("data") or ""
    if (len(topics) != 1 or topics[0].lower() != RELAY_ERC20_DEPOSIT
            or (log.get("address") or "").lower() != RELAY_DEPOSITORY or len(data) != 2 + 64 * 4):
        return None
    words = [data[2 + 64 * i:2 + 64 * (i + 1)] for i in range(4)]
    return dict(depositor="0x" + words[0][-40:], token="0x" + words[1][-40:], raw=int(words[2], 16), order="0x" + words[3])


def decode_native_relay_deposit(log):
    """One RelayNativeDeposit of the escrow: depositor, amount, order id, in three data words."""
    topics = log.get("topics") or []
    data = log.get("data") or ""
    if (len(topics) != 1 or topics[0].lower() != RELAY_NATIVE_DEPOSIT
            or (log.get("address") or "").lower() != RELAY_DEPOSITORY or len(data) != 2 + 64 * 3):
        return None
    words = [data[2 + 64 * i:2 + 64 * (i + 1)] for i in range(3)]
    return dict(depositor="0x" + words[0][-40:], token="native", raw=int(words[1], 16), order="0x" + words[2])


def chunks(items, size):
    items = list(items)
    for i in range(0, len(items), size):
        yield items[i:i + size]


def aggregate3(chain, calls, block="latest", size=300):
    """Multicall3.aggregate3 with allowFailure: [(ok, returndata_hex)] in call order. calls = [(target, calldata_hex)].
    A call to an address without code succeeds with empty data, so an empty answer means "no such contract"."""
    out = []
    for part in chunks(calls, size):
        head = "82ad56cb" + (32).to_bytes(32, "big").hex() + len(part).to_bytes(32, "big").hex()
        offsets, bodies, cursor = [], [], 32 * len(part)
        for target, data in part:
            payload = bytes.fromhex(data)
            body = (bytes(12) + bytes.fromhex(target[2:]) + (1).to_bytes(32, "big") + (96).to_bytes(32, "big")
                    + len(payload).to_bytes(32, "big") + payload + bytes((32 - len(payload) % 32) % 32))
            offsets.append(cursor)
            bodies.append(body)
            cursor += len(body)
        data = "0x" + head + "".join(o.to_bytes(32, "big").hex() for o in offsets) + "".join(b.hex() for b in bodies)
        raw = bytes.fromhex(rpc(chain, "eth_call", [dict(to=MULTICALL3, data=data), block])[2:])
        count = int.from_bytes(raw[32:64], "big")
        if count != len(part):
            raise net.SourceError(f"chain {chain}: multicall returned {count} results for {len(part)} calls")
        for i in range(count):
            at = 64 + int.from_bytes(raw[64 + 32 * i:96 + 32 * i], "big")
            data_at = at + int.from_bytes(raw[at + 32:at + 64], "big")
            length = int.from_bytes(raw[data_at:data_at + 32], "big")
            out.append((bool(int.from_bytes(raw[at:at + 32], "big")), raw[data_at + 32:data_at + 32 + length].hex()))
    return out


BATCH = {}           # calls in one JSON-RPC batch, by chain; unset chains use 40. drpc and quiknode refuse more than 10 (measured 2026-11-22)


def get_codes(chain, addresses, size=None):
    """eth_getCode at latest for many addresses, by JSON-RPC batch on the state endpoints. Returns {address: code_hex}."""
    out = {}
    size = size or BATCH.get(chain, 40)
    for part in chunks(addresses, size):
        _pace()
        for url in CHAINS[chain]["state"]:
            try:
                body = net.get_json(url, data=[dict(jsonrpc="2.0", id=i, method="eth_getCode", params=[a, "latest"]) for i, a in enumerate(part)])
            except net.SourceError:
                continue
            if isinstance(body, list) and len(body) == len(part) and all("result" in x for x in body):
                for x in body:
                    out[part[x["id"]]] = x["result"]
                break
        else:
            for a in part:                                   # no endpoint took the batch: one by one, still raising on failure
                out[a] = rpc(chain, "eth_getCode", [a, "latest"], state=True)
    return out


def receipt(chain, tx):
    """Receipt with its transaction, from the log endpoints. A null answer is a failure here, never an absence."""
    got = rpc(chain, "eth_getTransactionReceipt", [tx])
    if not got or got.get("transactionHash", "").lower() != tx.lower():
        raise net.SourceError(f"chain {chain}: receipt of {tx} not served")
    return got


def etherscan_key():
    return os.environ.get("ETHERSCAN_API_KEY") or None


def etherscan(chain, **params):
    """One Etherscan v2 call. 'No transactions found' is an empty list; any other refusal raises without the key."""
    key = etherscan_key()
    if not key:
        raise net.SourceError("ETHERSCAN_API_KEY is not set")
    url = ETHERSCAN + "?" + urllib.parse.urlencode(dict(chainid=chain, apikey=key, **params))
    last = "no answer"
    for attempt in range(5):
        time.sleep(0.25)
        try:
            status, body = net.fetch(url, timeout=60)
        except net.SourceError:
            last = "transport failure"
            continue
        try:
            answer = json.loads(body)
        except ValueError:
            last = f"HTTP {status}, not JSON"
            continue
        if answer.get("status") == "1":
            return answer["result"]
        message = f"{answer.get('message')} {str(answer.get('result'))[:120]}"
        if str(answer.get("message", "")).startswith("No "):
            return []
        last = message
        if not any(w in message.lower() for w in ("rate limit", "busy", "timeout", "unexpected", "try again")):
            break
        time.sleep(2 * (attempt + 1))
    raise net.SourceError(f"etherscan chain {chain} {params.get('action')}: {last}".replace(key, "<key>"))


def etherscan_rows(chain, action, address, first, last):
    """Every row of one list for [first, last], ascending. A page is never trusted to be the last because it is short:
    on 2026-11-14 the free plan served 996 rows in the middle of a list. The read restarts at the last block seen until
    a page comes back empty and repeats are dropped. A block that alone fills a page is read by page number, which the
    service allows up to 10,000 rows; a block beyond that raises, because nothing public could prove it complete."""
    seen, rows, start = set(), [], first

    def keep(page):
        for row in page:
            key = (row.get("hash"), row.get("traceId"), row.get("logIndex"), row.get("from"), row.get("to"), row.get("value"), row.get("contractAddress"))
            if key not in seen:
                seen.add(key)
                rows.append(row)

    def ask(a, b, page):
        return etherscan(chain, module="account", action=action, address=address, startblock=a, endblock=b, page=page, offset=1000, sort="asc")

    while start <= last:
        page = ask(start, last, 1)
        if not page:
            break
        keep(page)
        reached = int(page[-1]["blockNumber"])
        if reached > start:
            start = reached                     # the last block may be cut: read it again from its first row
            continue
        if len(page) >= 900:                    # this block alone fills a page: read it whole, by page number
            for number in range(2, 11):
                more = ask(reached, reached, number)
                if not more:
                    break
                keep(more)
            else:                               # ten pages and still rows: past what the service can serve for one block
                raise net.SourceError(f"etherscan chain {chain} {action} {address}: block {reached} holds 10,000 rows or more")
        start = reached + 1
    return rows
