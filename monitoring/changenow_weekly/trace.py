"""Hop-by-hop explanation of a money movement between a Polymarket wallet and a ChangeNOW-attributed address.

One walker serves both directions. It starts from a transfer whose sender must be explained and walks backward,
transfer by transfer, until it meets an origin: a ChangeNOW payout wallet (funding) or a Polymarket trading wallet
(withdrawal). It stops at the first step it cannot prove and says why. It never bridges a gap with an amount or a time.

Mixed funds: when an address held or received other money, only the part that could not have come from that other
money is attributed. For an outflow x of an address that received tracked money, with balance b before the first
tracked inflow and other inflows o since, the attributed part is max(0, x - b - o), capped by the tracked money not
yet attributed. It is a lower bound, and each tracked transfer is used once.
"""
from collections import defaultdict

from phi_monitor import net

from . import chainio as io
from . import polymarket as pm
from .polymarket import COLLATERAL, PUSD, USDC, USDC_E, ff_flows, ff_wallets

RELAY_SOLVERS = {a for a, v in ff_flows.LABELS.items() if v["name"] == "Relay EVM solver"}
DEPOSITORY = ff_flows.RELAY_DEPOSITORY
ERC20_DEPOSIT = ff_flows.DEPOSITORY_EVENT                                             # RelayErc20Deposit(address,address,uint256,bytes32)
NATIVE_DEPOSIT = "0x" + pm.kk.keccak(b"RelayNativeDeposit(address,uint256,bytes32)").hex()   # seen on Ethereum on 2026-11-15, three data words
PLAIN_CALLS = {"0xa9059cbb": 2 + 2 * (4 + 64), "0x23b872dd": 2 + 2 * (4 + 96)}       # transfer(), transferFrom(): calldata length without an order id
RAMPS = {PUSD} | {a for a, v in ff_flows.LABELS.items() if v["name"] in ("Polymarket CollateralOnramp", "Polymarket CollateralOfframp", "Polymarket PermissionedRamp")}
RELAY_CHAINS = (137, 1, 8453, 42161, 10)       # origin chains searched for a Relay order; others are reported as not read
BALANCE_OF = "70a08231"
MAX_DEPTH = 6
LOOKBACK = {1: 21600, 137: 129600}              # blocks searched backward for the inflow that paid an outflow (about three days)
NARROW_SPAN = 20000                             # widest range read on a chain whose node serves 1,000 blocks a call
WALLET_SHAPES = (ff_wallets.CLONE_PREFIX, ff_wallets.ERC1967_PREFIX, ff_wallets.BEACON_PREFIX, "608060405273ffffffffffffffffffffffffffffffffffffffff")
FUNDING, WITHDRAWAL = "FUNDING", "WITHDRAWAL"


class Unresolved(Exception):
    """The walk cannot continue on public data. The message is the reason kept in the report."""


def position(row):
    return (row["block"], row["log_index"] if row["log_index"] >= 0 else 10 ** 9)


def key(row):
    return (row["chain"], row["tx"], row["log_index"], row.get("trace", ""), row["src"], row["dst"])


def look(chain):
    return LOOKBACK.get(chain, NARROW_SPAN)


def is_ramp(address):
    """Collateral plumbing of Polymarket: the pUSD contract, the documented ramps, the reserve that holds the USDC.e."""
    return address in RAMPS or address == io.ZERO or address.startswith(ff_flows.COLLATERAL_RESERVE)


class Context:
    """What the walks share: week block ranges, ChangeNOW payouts per recipient, caches, and the running account of
    what has already been attributed, so that no origin transfer is counted twice."""

    def __init__(self, blocks, sources, payouts, service=()):
        self.blocks = blocks                      # {chain: dict(first, last, head, head_ts, week)}
        self.sources = sources                    # {chain: set(payout source address)}
        self.service = set(service)               # every registered address: money paid by one is not an outside origin
        self.payouts = defaultdict(list)          # (chain, recipient) -> payout rows, in chain order
        for p in sorted(payouts, key=lambda r: (r["chain"], position(r))):
            self.payouts[(p["chain"], p["dst"])].append(p)
        self.used = defaultdict(int)              # origin transfer key -> raw already attributed
        self.out_used = defaultdict(int)          # outflow of a tracked recipient -> raw of its lower bound already attributed
        self.ledgers, self.receipts, self.txs, self.codes, self.wallets, self.cache, self.natives = {}, {}, {}, {}, {}, {}, {}

    def receipt(self, chain, tx):
        if (chain, tx) not in self.receipts:
            self.receipts[(chain, tx)] = io.receipt(chain, tx)
        return self.receipts[(chain, tx)]

    def tx(self, chain, tx):
        if (chain, tx) not in self.txs:
            got = io.rpc(chain, "eth_getTransactionByHash", [tx])
            if not got:
                raise net.SourceError(f"chain {chain}: transaction {tx} not served")
            self.txs[(chain, tx)] = got
        return self.txs[(chain, tx)]

    def preload_codes(self, addresses):
        """Polygon code of many addresses in a few batched calls, so that wallet() rarely needs a call of its own."""
        missing = sorted({a for a in addresses if (137, a) not in self.codes})
        for a, code in io.get_codes(137, missing).items():
            self.codes[(137, a)] = code.lower()

    def wallet(self, address):
        """Classification of a Polygon address when it is a Polymarket trading wallet, else None. Cached.
        Only bytecode with the shape of one of the three wallet kinds is sent to the full classifier."""
        if address not in self.wallets:
            if (137, address) not in self.codes:
                self.codes[(137, address)] = io.rpc(137, "eth_getCode", [address, "latest"], state=True).lower()
            found = None
            if self.codes[(137, address)][2:].startswith(WALLET_SHAPES) and address not in ff_flows.LABELS:
                c = pm.classify(address)
                if c["type"] in (ff_wallets.DEPOSIT, ff_wallets.PROXY) or (c["type"] == ff_wallets.SAFE and c.get("polymarket_factory")):
                    found = c
            self.wallets[address] = found
        return self.wallets[address]

    def moves(self, chain, address, token, lo, hi, incoming):
        """Transfers of one asset into (incoming) or out of one address over blocks [lo, hi], in chain order. Cached.
        Tokens come from logs of that token contract. Native coin comes from logs on Polygon and from Etherscan lists
        where the free plan serves the chain; elsewhere it cannot be listed and the walk stops."""
        lo = max(1, lo)
        side = "dst" if incoming else "src"
        if (chain, address) in self.ledgers:                 # rows supplied in advance (offline tests)
            return [r for r in self.ledgers[(chain, address)]["rows"] if r["token"] == token and lo <= r["block"] <= hi and r[side] == address]
        k = (chain, address, token, lo, hi, incoming)
        if k in self.cache:
            return self.cache[k]
        if io.CHAINS[chain]["window"] < 5000 and hi - lo > NARROW_SPAN:
            raise Unresolved(f"transfers of {address} on {io.CHAINS[chain]['name']} need a log source that serves wide ranges")
        if token != "native":
            topics = [io.TRANSFER, None, io.pad(address)] if incoming else [io.TRANSFER, io.pad(address)]
            rows = [io.decode_transfer(log, chain) for log in io.get_logs(chain, lo, hi, topics, token)[0]]
        elif chain == 137:
            topics = [io.POL_LOG_TRANSFER, None, None, io.pad(address)] if incoming else [io.POL_LOG_TRANSFER, None, io.pad(address)]
            rows = [io.decode_transfer(log, chain) for log in io.get_logs(chain, lo, hi, topics, io.POL_SYSTEM)[0]]
        elif io.CHAINS[chain]["etherscan_free"] and io.etherscan_key():
            rows = [r for r in self.native_list(chain, address) if lo <= r["block"] <= hi and r[side] == address]
        else:
            raise Unresolved(f"native transfers of {address} cannot be listed on {io.CHAINS[chain]['name']} without a paid source")
        self.cache[k] = sorted([r for r in rows if r and r["raw"] > 0], key=position)
        return self.cache[k]

    def native_list(self, chain, address):
        """Native value transfers of one address over the week and the days before it, from Etherscan lists. Cached."""
        if (chain, address) not in self.natives:
            first, last = max(1, self.blocks[chain]["first"] - look(chain)), self.blocks[chain]["last"]
            rows = {}
            for action, index in (("txlist", -1), ("txlistinternal", -2)):
                for r in io.etherscan_rows(chain, action, address, first, last):
                    if r.get("isError", "0") == "0" and int(r["value"] or 0) > 0 and r.get("to"):
                        row = dict(chain=chain, block=int(r["blockNumber"]), block_hash="", tx=r["hash"].lower(), log_index=index, ts=int(r["timeStamp"]), token="native",
                                   src=r["from"].lower(), dst=r["to"].lower(), raw=int(r["value"]), trace=r.get("traceId", ""))
                        rows[key(row)] = row
            self.natives[(chain, address)] = sorted(rows.values(), key=position)
        return self.natives[(chain, address)]


def balance_before(chain, address, token, block):
    """Balance of one token (or the native coin) at the end of the block before `block`, from archive state."""
    if token == "native":
        return int(io.rpc(chain, "eth_getBalance", [address, hex(block - 1)]), 16)
    return int(io.rpc(chain, "eth_call", [dict(to=token, data="0x" + BALANCE_OF + "0" * 24 + address[2:]), hex(block - 1)]), 16)


def hop(kind, row, **extra):
    return dict(kind=kind, chain=row["chain"], tx=row["tx"], log_index=row["log_index"], block=row["block"], block_hash=row.get("block_hash", ""), ts=row.get("ts"),
                src=row["src"], dst=row["dst"], token=row["token"], raw=str(row["raw"]), **extra)


def relay_order(ctx, chain, row):
    """A payment made by Relay's documented solver carries its order id as the last 32 bytes of the calldata. That holds
    for one plain payment: transfer() or transferFrom() called on the token itself, or a native send straight to the
    recipient, each followed by the 32-byte id (all 37 Relay fills of the week's first pass had this shape). A payment
    made inside another contract call can settle several orders, so its calldata tail is not tied to this transfer and
    the walk stops. A plain payment without an id is the solver's own money: None."""
    if row["src"] not in RELAY_SOLVERS:
        return None
    tx = ctx.tx(chain, row["tx"])
    data, to = tx["input"].lower(), (tx.get("to") or "").lower()
    if row["token"] == "native":
        bare = 2 if to == row["dst"] else None                                      # a native send carries no call: "0x", then the id
    else:
        bare = PLAIN_CALLS.get(data[:10]) if to == row["token"] else None
    if bare is not None and len(data) == bare + 64:
        return data[-64:]
    if bare is not None and len(data) == bare:
        return None
    raise Unresolved(f"Relay fill {row['tx']} is not one plain payment: its calldata does not tie an order id to this transfer")


def relay_origin(ctx, order, ts):
    """The escrow log holding the same order id on an origin chain: who deposited, what, how much.
    Searched from seventy minutes before the fill to ten minutes after, on the chains read here."""
    for chain in RELAY_CHAINS:
        b = ctx.blocks.get(chain)
        if not b:
            continue
        start = io.week_bounds(b["week"])[0]
        rate = (b["head_ts"] - start) / max(1, b["head"] - b["first"])              # seconds a block, over the week so far
        guess = b["first"] + int((ts - start) / rate)
        lo, hi = max(1, guess - int(4200 / rate)), min(b["head"], guess + int(600 / rate))
        for log in io.get_logs(chain, lo, hi, [[ERC20_DEPOSIT, NATIVE_DEPOSIT]], DEPOSITORY)[0]:
            data = log["data"][2:].lower()
            words = [data[i:i + 64] for i in range(0, len(data), 64)]
            kind = log["topics"][0].lower() if log.get("topics") else ""
            if kind == NATIVE_DEPOSIT and len(words) == 3 and words[2] == order:          # depositor, amount, id
                token, depositor, raw = "native", "0x" + words[0][-40:], int(words[1], 16)
            elif kind == ERC20_DEPOSIT and len(words) == 4 and words[3] == order:         # depositor, token, amount, id
                token, depositor, raw = "0x" + words[1][-40:], "0x" + words[0][-40:], int(words[2], 16)
            else:
                continue                                                            # another order, or another event of the escrow
            return dict(chain=chain, block=int(log["blockNumber"], 16), block_hash=log.get("blockHash", ""), tx=log["transactionHash"].lower(), log_index=int(log["logIndex"], 16),
                        ts=int(log["blockTimestamp"], 16) if log.get("blockTimestamp") else None, src=depositor, dst=DEPOSITORY, token=token, raw=raw)
    return None


def conversion(ctx, row, into):
    """The other leg of a 1:1 collateral conversion inside one Polygon transaction: the transfer of the same amount
    that enters the collateral contracts (into=True, a wrap) or leaves a holder toward them (into=False, an unwrap).
    None, or legs from several holders, is not a proof and raises."""
    wanted = (USDC_E, USDC) if into else (PUSD,)
    legs = [m for m in ff_flows.transfers(ctx.receipt(137, row["tx"]), 137)
            if m["raw"] == row["raw"] and m["token"] in wanted and is_ramp(m["target"]) and not is_ramp(m["source"]) and m["log_index"] < row["log_index"]]
    if len({m["source"] for m in legs}) != 1:
        raise Unresolved(f"{len(legs)} same-amount legs for the collateral conversion in {row['tx']}")
    m = legs[-1]
    return dict(chain=137, tx=m["tx"], log_index=m["log_index"], block=m["block"], block_hash=row.get("block_hash", ""), ts=row.get("ts"),
                src=m["source"], dst=m["target"], token=m["token"], raw=m["raw"])


def tracked_inflows(ctx, direction, chain, address, token, before):
    """Origin transfers already received by `address` in this asset: ChangeNOW payouts, or transfers from trading wallets."""
    if direction == FUNDING:
        return [p for p in ctx.payouts.get((chain, address), []) if p["token"] == token and position(p) < before]
    if chain != 137 or token not in COLLATERAL:
        return []
    rows = [r for r in ctx.moves(chain, address, token, before[0] - look(chain), before[0], True) if position(r) < before]
    ctx.preload_codes({r["src"] for r in rows})
    return [r for r in rows if ctx.wallet(r["src"])]


def attribute(ctx, chain, address, out_row, tracked):
    """Lower bound of tracked money in one outflow, split first-in first-out over the tracked inflows.
    Returns ([(origin_row, raw_part)], detail)."""
    token, first = out_row["token"], tracked[0]
    keys = {key(p) for p in tracked}
    rows = ctx.moves(chain, address, token, first["block"], out_row["block"], True)
    before = balance_before(chain, address, token, first["block"])
    same_block = sum(r["raw"] for r in rows if r["block"] == first["block"] and position(r) < position(first))
    others = sum(r["raw"] for r in rows if position(first) < position(r) < position(out_row) and key(r) not in keys)
    left = max(0, out_row["raw"] - before - same_block - others - ctx.out_used[key(out_row)])     # the bound of one outflow is spent once
    parts = []
    for p in tracked:
        take = min(p["raw"] - ctx.used[key(p)], left)
        if take > 0:
            parts.append((p, take))
            left -= take
    return parts, dict(outflow_raw=str(out_row["raw"]), balance_before_first_tracked_inflow=str(before + same_block), other_inflows_between=str(others),
                       tracked_inflows=len(tracked), attributed_raw=str(sum(t for _, t in parts)))


def pass_through(ctx, chain, address, out_row, hops):
    """The inflow that paid for one outflow of an address that is neither an origin nor a tracked recipient: the latest
    earlier inflow of the same asset, accepted only when the address held almost nothing before it and it covers the
    outflow. Anything else is mixing, and the walk stops."""
    token = out_row["token"]
    ins = [r for r in ctx.moves(chain, address, token, out_row["block"] - look(chain), out_row["block"], True) if position(r) < position(out_row)]
    if not ins:
        raise Unresolved(f"no earlier inflow of this asset to {address} in the {look(chain)} blocks before")
    last = ins[-1]
    held = balance_before(chain, address, token, last["block"]) + sum(r["raw"] for r in ins[:-1] if r["block"] == last["block"])
    spent = sum(r["raw"] for r in ctx.moves(chain, address, token, last["block"], out_row["block"], False) if position(last) < position(r) < position(out_row))
    allowance = last["raw"] // (20 if token == "native" else 100)        # a native balance pays gas, so a little more is tolerated
    if held > allowance:
        raise Unresolved(f"{address} already held this asset before its last inflow: funds are mixed")
    if last["raw"] + (held if token == "native" else 0) - spent < out_row["raw"]:
        raise Unresolved(f"the last inflow to {address} does not cover the outflow")
    hops.append(hop("TRANSFER", last, note=f"only inflow that can have paid the next step; balance held before it: {held}"))
    return last, held


def explain(ctx, direction, start):
    """Walk backward from `start`, a transfer whose sender must be explained, to its origin.
    Returns dict(status, hops, parts, outflow, detail). parts: [(origin_row, raw in origin units, raw in start units)].
    status CONFIRMED, NOT_ORIGIN (a proven origin of another kind) or UNRESOLVED (reason in detail)."""
    hops, steps, chain, point = [], [], start["chain"], dict(start)
    try:
        for _ in range(MAX_DEPTH):
            payer = point["src"]
            if direction == FUNDING and hops and payer == start["dst"]:
                return dict(status="NOT_ORIGIN", hops=hops, parts=[], detail=dict(reason="the wallet moved or converted its own balance: not a new credit"))
            if chain == 137 and point["token"] in COLLATERAL and is_ramp(payer):
                point = conversion(ctx, point, into=point["token"] == PUSD)
                hops.append(hop("CONVERSION_1_TO_1", point))
                continue
            origin_kind = "CHANGENOW_PAYOUT" if direction == FUNDING else "POLYMARKET_WALLET_DEBIT"
            if (direction == FUNDING and payer in ctx.sources.get(chain, ())) or (direction == WITHDRAWAL and chain == 137 and ctx.wallet(payer)):
                free = point["raw"] - ctx.used[key(point)]
                if free <= 0:
                    raise Unresolved("this origin transfer is already attributed in full")
                hops.append(hop(origin_kind, point))
                return finish(start, hops, steps, [(point, free)], None, dict(direct=True))
            order = relay_order(ctx, chain, point)
            if order:
                origin = relay_origin(ctx, order, point.get("ts") or io.block_time(chain, point["block"]))
                if not origin:
                    raise Unresolved(f"Relay order 0x{order}: escrow log not found on the origin chains read here")
                hops.append(hop("RELAY_ORDER", origin, order="0x" + order, fill_tx=point["tx"], fill_chain=chain, fill_raw=str(point["raw"]), fill_token=point["token"]))
                steps.append(("scale", point["raw"], origin["raw"]))
                chain, point = origin["chain"], origin
                continue
            label = ff_flows.label_of(payer)
            if label or payer in ctx.service or is_ramp(payer):
                who = label["name"] if label else "a registered ChangeNOW address" if payer in ctx.service else "Polymarket collateral plumbing"
                return dict(status="NOT_ORIGIN", hops=hops, parts=[], detail=dict(reason=f"paid by {who}"))
            tracked = tracked_inflows(ctx, direction, chain, payer, point["token"], position(point))
            if tracked:
                parts, detail = attribute(ctx, chain, payer, point, tracked)
                if not parts:
                    raise Unresolved("funds are mixed: other money available to this address covers the whole outflow")
                for p, take in parts:
                    hops.append(hop(origin_kind, p, attributed_raw=str(take)))
                return finish(start, hops, steps, parts, key(point), detail)
            inflow, held = pass_through(ctx, chain, payer, point, hops)
            steps.append(("part", inflow["raw"] + held, point["raw"]))             # the small balance held before is other money too
            point = inflow
        raise Unresolved(f"no origin within {MAX_DEPTH} steps")
    except Unresolved as stop:
        return dict(status="UNRESOLVED", hops=hops, parts=[], detail=dict(reason=str(stop)))


def finish(start, hops, steps, parts, outflow, detail):
    """Carry the tracked amount found at the origin forward to the transfer being explained.
    A Relay order turns its whole input into its output, so the amount scales with it. An address that passes on only
    part of an inflow may have passed on the untracked part first, so only max(0, part - untracked) continues."""
    amount = float(sum(take for _, take in parts))             # in the origin's units
    scale = 1.0
    for kind, a, b in reversed(steps):                         # from the origin toward the start
        if kind == "scale":                                    # a: what the solver paid, b: what was deposited
            amount, scale = amount * a / b, scale * a / b
        else:                                                  # a: inflow of the address and what it held before, b: the outflow that continues
            amount = max(0.0, b - (a - amount))
    amount = int(min(amount, start["raw"]))
    if amount <= 0:
        raise Unresolved("funds are mixed on the way: nothing is left to attribute to this transfer")
    out, left = [], amount / scale                             # back in the origin's units, split first-in first-out
    for origin, take in parts:
        give = int(min(take, left))
        if give > 0:
            out.append((origin, give, min(amount, int(give * scale))))
            left -= give
    return dict(status="CONFIRMED", hops=hops, parts=out, outflow=outflow, detail=dict(detail, attributed_to_this_transfer_raw=str(amount)))


def commit(ctx, result):
    """Record what a confirmed walk attributed, so that later walks cannot reuse it."""
    for origin, raw, _ in result["parts"]:
        ctx.used[key(origin)] += raw
    if result.get("outflow"):
        ctx.out_used[result["outflow"]] += sum(raw for _, raw, _ in result["parts"])
