"""Offline evidence validation and decoding. A source event alone never identifies a PM wallet."""

from bisect import bisect_right
from dataclasses import dataclass
from decimal import Decimal
from .common import (
    CN22,
    ETH_POOLS,
    ETH_TOKENS,
    F2020,
    POOLS,
    TOKENS,
    ZERO,
    address_word,
    bounds,
    hexstr,
    network_query,
    read,
)


@dataclass(frozen=True)
class Credit:
    chain: int
    stream: str
    block: int
    ts: int
    tx: str
    idx: int
    sender: str
    recipient: str
    asset: str
    units: int
    role: str

    @property
    def key(self):
        return self.chain, self.tx, self.idx

    @property
    def amount(self):
        decimals = (
            18
            if self.asset == "native"
            else (TOKENS if self.chain == 137 else ETH_TOKENS)[self.asset][1]
        )
        return Decimal(self.units).scaleb(-decimals)


def decode(chain, stream, row):
    block, ts, bh, tx, idx, emitter, topics, data = row
    hexstr(bh, 64)
    tx, emitter = hexstr(tx, 64), hexstr(emitter, 40)
    if not all(type(x) is int and x >= 0 for x in [block, ts, idx]):
        raise ValueError("invalid block, timestamp or log index")
    rule = network_query(chain, stream)
    if emitter not in rule["address"] or topics[0] != rule["topics"][0]:
        raise ValueError("unregistered emitter or wrong event")
    if stream == "tornado":
        if len(topics) != 2:
            raise ValueError("withdrawal topics")
        address_word(hexstr(topics[1], 64)[2:])  # relayer, never the payout recipient
        data = hexstr(data, 192)[2:]
        recipient = address_word(data[:64])
        asset, denom = ("native", POOLS[emitter] * 10**18) if chain == 137 else ETH_POOLS[emitter]
        units = denom - int(data[128:], 16)
        if units < 0:
            raise ValueError("fee exceeds denomination")
        sender, role = emitter, "withdrawal_pool"
    else:
        if len(topics) != 3 or topics[1] not in rule["topics"][1]:
            raise ValueError("unregistered transfer origin")
        sender, recipient = [address_word(hexstr(x, 64)[2:]) for x in topics[1:]]
        units = int(hexstr(data, 64), 16)
        asset = emitter
        role = (
            "commingled_route"
            if sender == F2020
            else "consolidation"
            if sender == CN22
            else "labelled_hot_wallet"
        )
    if not units or recipient in {ZERO, sender}:
        return None
    return Credit(chain, stream, block, ts, tx, idx, sender, recipient, asset, units, role)


def verified_pack(pack, week, chain, stream):
    """Require disjoint successful / missing ranges covering the exact UTC bracket."""
    if (pack["week"], pack["chain"], pack["stream"], pack["query"]) != (
        week,
        chain,
        stream,
        network_query(chain, stream),
    ):
        raise ValueError("pack metadata mismatch")
    for edge, instant in zip(pack["boundaries"], bounds(week), strict=True):
        left, right = edge
        if right[0] != left[0] + 1 or not left[1] < instant <= right[1]:
            raise ValueError("invalid UTC boundary")
        for h in edge:
            hexstr(h[2], 64)
    a, b = pack["boundaries"][0][1][0], pack["boundaries"][1][0][0]
    cursor = a
    for lo, hi in sorted([r[:2] for r in pack["ranges"] + pack["gaps"]]):
        if lo != cursor or hi < lo:
            raise ValueError("noncontiguous or overlapping ranges")
        cursor = hi + 1
    if cursor != b + 1:
        raise ValueError("range ends early")
    spans = sorted(pack["ranges"])
    starts = [r[0] for r in spans]
    counts = [0] * len(spans)
    t0, t1 = bounds(week)
    hashes, seen, events = {}, {}, []
    for row in pack["logs"]:
        block, ts, bh, tx, idx = row[:5]
        j = bisect_right(starts, block) - 1
        if j < 0 or block > spans[j][1] or not t0 <= ts < t1:
            raise ValueError("event outside successful time/block range")
        counts[j] += 1
        if hashes.setdefault(block, (ts, bh)) != (ts, bh):
            raise ValueError("conflicting header for block")
        obj = decode(chain, stream, row)
        k = (tx, idx)
        if k in seen:
            if seen[k] != row:
                raise ValueError("conflicting copies of receipt log")
            continue
        seen[k] = row
        if obj:
            events.append(obj)
    if counts != [s[3] for s in spans]:
        raise ValueError("range row count mismatch")
    return events


def load_stream(snap, week, chain, stream):
    path = snap / week / (("" if chain == 137 else "ethereum-") + stream + ".json.gz")
    if not path.exists():
        return [], {"status": "UNKNOWN", "reason": "no captured range"}
    pack = read(path)
    events = verified_pack(pack, week, chain, stream)
    return events, {
        "status": "PARTIAL" if pack["gaps"] else "SCOPED_COMPLETE",
        "blocks": [pack["boundaries"][0][1][0], pack["boundaries"][1][0][0]],
        "range_count": len(pack["ranges"]),
        "missing_ranges": pack["gaps"],
        "logs": len(pack["logs"]),
    }
