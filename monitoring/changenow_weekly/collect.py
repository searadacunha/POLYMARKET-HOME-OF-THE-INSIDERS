"""Collection by block window, resumable. Raw rows live outside the repository, one gzip file per stream and range.

Registry streams (every transfer from or to a registered address) are incremental: a run reads only blocks after the
last range on disk. Dependent streams (transfers into the deposit addresses found, collateral moved by recipients)
depend on a set that grows between runs, so they are read again over the whole week for the current set.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path

from phi_monitor import net

from . import chainio as io

SPAN = {1: 10000, 137: 20000, 8453: 20000}      # blocks per file; an interrupted run loses one file at most
DEFAULT_SPAN = 10000


class Store:
    def __init__(self, raw, week, chain):
        self.dir = Path(raw) / week / str(chain)
        self.dir.mkdir(parents=True, exist_ok=True)

    def ranges(self, stream):
        out = []
        for p in self.dir.glob(f"{stream}__*.jsonl.gz"):
            a, b = p.name[len(stream) + 2:-9].split("_")
            out.append((int(a), int(b)))
        return sorted(out)

    def next_block(self, stream, first):
        """First block not yet on disk. Ranges must be contiguous from `first`: a hole is an error, never skipped."""
        cursor = first
        for a, b in self.ranges(stream):
            if a != cursor:
                raise RuntimeError(f"{self.dir}/{stream}: range {a}-{b} does not continue from block {cursor}")
            cursor = b + 1
        return cursor

    def write(self, stream, first, last, rows):
        path = self.dir / f"{stream}__{first}_{last}.jsonl.gz"
        tmp = path.with_suffix(f".{os.getpid()}.tmp")
        with gzip.open(tmp, "wt") as f:
            for row in rows:
                f.write(json.dumps(row, separators=(",", ":")) + "\n")
        os.replace(tmp, path)

    def drop(self, stream):
        for p in self.dir.glob(f"{stream}__*.jsonl.gz"):
            p.unlink()

    def rows(self, stream):
        for a, b in self.ranges(stream):
            with gzip.open(self.dir / f"{stream}__{a}_{b}.jsonl.gz", "rt") as f:
                for line in f:
                    yield json.loads(line)

    def meta(self, name, value=None):
        path = self.dir / f"{name}.json"
        if value is None:
            return json.loads(path.read_text()) if path.exists() else None
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(value, indent=1))
        os.replace(tmp, path)


def _rows(chain, logs):
    out, odd = [], 0
    for log in logs:
        row = io.decode_transfer(log, chain)
        if row is None:
            odd += 1
        else:
            out.append(row)
    return out, odd


def log_stream(store, chain, stream, first, last, topics, address=None, say=print):
    """Incremental read of one log filter over [first, last]. Returns dict(read=(a, b) or None, rows, other_shapes, windows)."""
    cursor, total, odd_total, windows = store.next_block(stream, first), 0, 0, 0
    start = cursor
    span = SPAN.get(chain, DEFAULT_SPAN)
    while cursor <= last:
        end = min(cursor + span - 1, last)
        logs, read = io.get_logs(chain, cursor, end, topics, address)
        rows, odd = _rows(chain, logs)
        store.write(stream, cursor, end, rows)
        total, odd_total, windows = total + len(rows), odd_total + odd, windows + len(read)
        say(f"  {io.CHAINS[chain]['name']} {stream} {cursor}-{end}: {len(rows)} rows")
        cursor = end + 1
    return dict(read=(start, last) if start <= last else None, rows=total, other_shapes=odd_total, windows=windows)


def registry_streams(store, chain, blocks, addresses, say=print):
    """Every ERC-20 transfer from or to a registered address, and on Polygon every native move, for the week so far.
    Ranges on disk hold the transfers of one set of addresses. When the register changes they are dropped and the week
    is read again from its first block: an address added later would otherwise miss its transfers in the blocks already read."""
    topics = [io.pad(a) for a in sorted(addresses)]
    first, last = blocks["first"], blocks["last"]
    names = ("reg_out", "reg_in", "reg_nat_out", "reg_nat_in") if chain == 137 else ("reg_out", "reg_in")
    mark = hashlib.sha256("".join(topics).encode()).hexdigest()
    if (store.meta("register") or {}).get("sha256") != mark:
        if any(store.ranges(name) for name in names):
            say(f"  {io.CHAINS[chain]['name']}: the register is not the one the ranges on disk were read for; reading the week again from its first block")
        for name in names:
            store.drop(name)
        store.meta("register", dict(sha256=mark, addresses=len(topics)))
    out = dict(reg_out=log_stream(store, chain, "reg_out", first, last, [io.TRANSFER, topics], say=say),
               reg_in=log_stream(store, chain, "reg_in", first, last, [io.TRANSFER, None, topics], say=say))
    if chain == 137:
        out["reg_nat_out"] = log_stream(store, chain, "reg_nat_out", first, last, [io.POL_LOG_TRANSFER, None, topics], io.POL_SYSTEM, say=say)
        out["reg_nat_in"] = log_stream(store, chain, "reg_nat_in", first, last, [io.POL_LOG_TRANSFER, None, None, topics], io.POL_SYSTEM, say=say)
    return out


def activity(store, chain, blocks, addresses):
    """Outgoing transaction count of each registered address during the week so far, from account nonces at two blocks."""
    out = {}
    for a in sorted(addresses):
        before = int(io.rpc(chain, "eth_getTransactionCount", [a, hex(blocks["first"] - 1)]), 16)
        after = int(io.rpc(chain, "eth_getTransactionCount", [a, hex(blocks["last"])]), 16)
        if after:
            out[a] = dict(before=before, after=after, sent=after - before)
    store.meta("activity", dict(first=blocks["first"], last=blocks["last"], nonces=out))
    return out


def native_lists(store, chain, blocks, active, say=print):
    """Native transfers of the active registered addresses from Etherscan lists (chains whose native moves leave no log).
    `active` maps each address to the transactions it signed in the range, from its nonces: the list must hold as many.
    Read again in full each run: a list restarted at a block boundary is simpler to prove complete than an appended one."""
    rows, counts = [], {}
    for a in sorted(active):
        n = 0
        for action in ("txlist", "txlistinternal"):
            listed = io.etherscan_rows(chain, action, a, blocks["first"], blocks["last"])
            if action == "txlist":                          # invariant: the list holds every transaction the account signed
                signed = len({r["hash"] for r in listed if r["from"].lower() == a})
                if signed != active[a]:
                    raise net.SourceError(f"chain {chain} {a}: list holds {signed} signed transactions, the nonce moved by {active[a]}")
            for r in listed:
                if r.get("isError", "0") != "0" or int(r["value"] or 0) == 0 or not r.get("to"):
                    continue
                rows.append(dict(chain=chain, block=int(r["blockNumber"]), block_hash=r.get("blockHash", ""), tx=r["hash"].lower(), log_index=-1 if action == "txlist" else -2,
                                 trace=r.get("traceId", ""), ts=int(r["timeStamp"]), token="native", src=r["from"].lower(), dst=r["to"].lower(), raw=int(r["value"])))
                n += 1
        counts[a] = n
        say(f"  {io.CHAINS[chain]['name']} native list {a}: {n} value rows")
    seen, unique = set(), []
    for r in rows:                                          # a transfer between two listed addresses is served twice
        key = (r["tx"], r["log_index"], r["trace"], r["src"], r["dst"], r["raw"])
        if key not in seen:
            seen.add(key)
            unique.append(r)
    store.drop("native")
    store.write("native", blocks["first"], blocks["last"], unique)
    return dict(read=(blocks["first"], blocks["last"]), rows=len(unique), per_address=counts)


DEPENDENT_SIZE = {}         # addresses named in one filter, by chain; unset chains use 150. A caller may raise it for a node
                            # measured to accept more (tenderly's Polygon gateway served 1,500 on 2026-11-22)


def dependent_stream(store, chain, stream, blocks, addresses, side, tokens=None, native=False, say=print, size=None):
    """Transfers from (`side='src'`) or to (`side='dst'`) a derived address set, over the whole week, replacing the last read.
    An address whose transfers alone exceed what a node serves is set aside and returned in `heavy`, never silently dropped.
    On a chain with a `by_contract` node the token list is cut into the groups that node accepts, each read with larger
    address lists; the rows of every group are merged in chain order."""
    first, last = blocks["first"], blocks["last"]
    rows, heavy, calls = [], [], 0
    wide = io.CHAINS[chain].get("by_contract") if tokens and not native else None
    groups = [list(g) for g in io.chunks(sorted(tokens), wide["contracts"])] if wide else [tokens]
    size = size or DEPENDENT_SIZE.get(chain, 150)
    pending = [(group, list(part)) for group in groups for part in io.chunks(sorted(addresses), wide["addresses"] if wide else size)]
    while pending:
        group, part = pending.pop()
        topics = [io.pad(a) for a in part]
        if native:
            flt = [io.POL_LOG_TRANSFER, None, topics] if side == "src" else [io.POL_LOG_TRANSFER, None, None, topics]
            address = io.POL_SYSTEM
        else:
            flt = [io.TRANSFER, topics] if side == "src" else [io.TRANSFER, None, topics]
            address = group
        try:
            logs, read = io.get_logs(chain, first, last, flt, address)
        except net.SourceError:
            if len(part) == 1:
                if part[0] not in heavy:
                    heavy.append(part[0])
                continue
            pending += [(group, part[:len(part) // 2]), (group, part[len(part) // 2:])]
            continue
        calls += len(read)
        got, _ = _rows(chain, logs)
        rows += got
    rows.sort(key=lambda r: (r["block"], r["log_index"]))
    store.drop(stream)
    store.write(stream, first, last, rows)
    say(f"  {io.CHAINS[chain]['name']} {stream}: {len(rows)} rows for {len(addresses)} addresses, {calls} windows, {len(heavy)} set aside")
    return dict(read=(first, last), rows=len(rows), addresses=len(addresses), windows=calls, heavy=heavy)
