"""Second reading of a published week: every transaction a confirmed event rests on is fetched again, by hash, from
nodes other than the one used for the block scan, and compared field by field with what was published.

A transfer found by a log scan must still be there, in the same block, with the same sender, recipient, token and
amount. A Relay hop must still carry its order id on both sides. The escrow deposit of a withdrawal is a
RelayErc20Deposit event, not an ERC-20 Transfer: it is read by its own ABI (depositor, token, amount, order id) and
must be backed by exactly one token movement of the same transaction from that depositor to the escrow. Anything
else is reported as a mismatch. Native transfers made inside another transaction cannot be re-read from a receipt
and are counted as not checked; a receipt no endpoint serves is unavailable, never a pass and never a mismatch.
"""
import json
import time
from collections import defaultdict

from phi_monitor import net

from . import chainio as io
from . import report

RECEIPT_TRIES = 3              # bounded: a public node that answers null once may serve the receipt on the next call
RECEIPT_BACKOFF = 1.5


def _receipt(chain, tx, cache):
    if (chain, tx) not in cache:
        last = None
        for attempt in range(RECEIPT_TRIES):
            try:
                got = io.rpc(chain, "eth_getTransactionReceipt", [tx], state=True)
            except net.SourceError as exc:
                last = exc
            else:
                if got:
                    cache[(chain, tx)] = got
                    return got
                last = net.SourceError(f"chain {chain}: receipt of {tx} not served")
            if attempt < RECEIPT_TRIES - 1:
                time.sleep(RECEIPT_BACKOFF * (attempt + 1))
        raise net.SourceError(str(last) if last else f"chain {chain}: receipt of {tx} not served")
    return cache[(chain, tx)]


def _header(ref, receipt):
    """Chain, transaction hash, receipt success, block number and block hash. None when every check holds."""
    if (receipt.get("transactionHash") or "").lower() != ref["tx"].lower():
        return "MISMATCH: receipt is for another transaction"
    chain_id = receipt.get("chainId")
    if chain_id is not None:
        try:
            got = int(chain_id, 16)
        except (TypeError, ValueError):
            return "MISMATCH: receipt chain is unreadable"
        if got != ref["chain"]:
            return f"MISMATCH: receipt chain {got} instead of {ref['chain']}"
    if int(receipt.get("status", "0x1"), 16) != 1:
        return "MISMATCH: transaction failed"
    if ref.get("block") is not None and int(receipt["blockNumber"], 16) != ref["block"]:
        return f"MISMATCH: block {int(receipt['blockNumber'], 16)} instead of {ref['block']}"
    if ref.get("block_hash") and receipt["blockHash"].lower() != ref["block_hash"].lower():
        return "MISMATCH: block hash changed"
    return None


def _differing(expected, actual, label):
    diffs = {key: {"expected": expected[key], "actual": actual[key]} for key in expected if actual[key] != expected[key]}
    return ("MISMATCH: " + label + " differs: " + json.dumps(diffs, sort_keys=True)) if diffs else "ok"


def _relay_common(ref, dep, orders):
    """Field-by-field checks shared by an escrow deposit and an escrow log read inside a Relay hop."""
    diffs = {}
    if dep["depositor"].lower() != ref["src"].lower():
        diffs["src"] = {"expected": ref["src"].lower(), "actual": dep["depositor"].lower()}
    if (ref.get("dst") or "").lower() != io.RELAY_DEPOSITORY:
        diffs["dst"] = {"expected": ref.get("dst"), "actual": io.RELAY_DEPOSITORY}
    if (ref.get("token") or "").lower() != dep["token"].lower():
        diffs["token"] = {"expected": ref.get("token"), "actual": dep["token"].lower()}
    if int(ref["raw"]) != dep["raw"]:
        diffs["raw"] = {"expected": int(ref["raw"]), "actual": dep["raw"]}
    wanted = {o.lower() for o in orders}
    if dep["order"].lower() not in wanted:
        diffs["order"] = {"expected": sorted(wanted), "actual": dep["order"].lower()}
    return diffs


def _erc20_relay_deposit(ref, receipt, dep, orders):
    """The deposit event must be corroborated by the token movement of the same transaction: exactly one
    ERC-20 Transfer of that token, from the depositor, to the shared escrow, for the same raw amount."""
    if not orders:
        return "MISMATCH: Relay deposit log without a correlated Relay order"
    diffs = _relay_common(ref, dep, orders)
    if diffs:
        return "MISMATCH: Relay deposit differs: " + json.dumps(diffs, sort_keys=True)
    moved = []
    for log in receipt.get("logs", []):
        topics = log.get("topics") or []
        if (len(topics) == 3 and topics[0].lower() == io.TRANSFER and log["address"].lower() == dep["token"].lower()
                and "0x" + topics[1][-40:] == dep["depositor"].lower() and "0x" + topics[2][-40:] == io.RELAY_DEPOSITORY
                and int(log.get("data", "0x0"), 16) == dep["raw"]):
            moved.append(log)
    if len(moved) == 1:
        return "ok"
    if not moved:
        return "MISMATCH: Relay deposit has no matching token transfer"
    return f"MISMATCH: ambiguous Relay deposit: {len(moved)} matching token transfers"


def _native_relay_deposit(ref, chain, receipt, dep, orders):
    """A native escrow deposit carries no token log; its corroboration is the sending transaction itself."""
    if not orders:
        return "MISMATCH: Relay deposit log without a correlated Relay order"
    diffs = _relay_common(ref, dep, orders)
    if diffs:
        return "MISMATCH: Relay deposit differs: " + json.dumps(diffs, sort_keys=True)
    sent = io.rpc(chain, "eth_getTransactionByHash", [ref["tx"]], state=True)
    if not sent:
        raise net.SourceError(f"chain {chain}: transaction {ref['tx']} not served")
    if (sent.get("hash") or "").lower() != ref["tx"].lower():
        return "MISMATCH: native escrow deposit names another transaction"
    if (sent.get("from") or "").lower() != dep["depositor"].lower() or (sent.get("to") or "").lower() != io.RELAY_DEPOSITORY:
        return "MISMATCH: native escrow deposit was not sent by the depositor to the escrow"
    if int(sent.get("value", "0x0"), 16) != dep["raw"]:
        return "MISMATCH: native escrow deposit value differs"
    return "ok"


def check_transfer(ref, cache, relay_orders=()):
    """'ok', 'not checked: <why>' or 'MISMATCH: <what>' for one published transfer reference.
    `relay_orders` are the order ids the same event ties to this escrow log; empty for an ordinary transfer."""
    chain, tx, index = ref["chain"], ref["tx"], ref["log_index"]
    if index == -2:
        return "not checked: native value moved inside another transaction, absent from the receipt"
    receipt = _receipt(chain, tx, cache)
    bad = _header(ref, receipt)
    if bad:
        return bad
    if index == -1:
        sent = io.rpc(chain, "eth_getTransactionByHash", [tx], state=True)
        if not sent:
            raise net.SourceError(f"chain {chain}: transaction {tx} not served")
        if (sent.get("hash") or "").lower() != tx.lower():
            return "MISMATCH: transaction names another hash"
        if sent.get("chainId") is not None and int(sent["chainId"], 16) != chain:
            return "MISMATCH: transaction chain differs"
        same = (sent["from"].lower() == ref["src"].lower() and (sent.get("to") or "").lower() == ref["dst"].lower()
                and int(sent["value"], 16) == int(ref["raw"]))
        return "ok" if same else "MISMATCH: native transaction differs"
    for log in receipt["logs"]:
        if int(log["logIndex"], 16) == index:
            row = io.decode_transfer(dict(log, blockTimestamp=None), chain)
            if row:
                actual = {"src": str(row["src"]).lower(), "dst": str(row["dst"]).lower(),
                          "token": str(row["token"]).lower(), "raw": int(row["raw"])}
                expected = {"src": str(ref["src"]).lower(), "dst": str(ref["dst"]).lower(),
                            "token": str(ref["token"]).lower(), "raw": int(ref["raw"])}
                return _differing(expected, actual, "log")
            dep = io.decode_relay_deposit(log)
            if dep:
                return _erc20_relay_deposit(ref, receipt, dep, relay_orders)
            native = io.decode_native_relay_deposit(log)
            if native:
                return _native_relay_deposit(ref, chain, receipt, native, relay_orders)
            return "MISMATCH: receipt log is neither a decoded transfer nor a Relay deposit"
    return "MISMATCH: log index absent from the receipt"


def check_relay(hop, cache):
    """The escrow log must be a Relay deposit of this order, and the solver's payment must end with the same id."""
    order = hop["order"][2:].lower()
    receipt = _receipt(hop["chain"], hop["tx"], cache)
    bad = _header(hop, receipt)
    if bad:
        return bad
    escrow = next((l for l in receipt["logs"] if int(l["logIndex"], 16) == hop["log_index"]), None)
    if not escrow:
        return "MISMATCH: relay escrow log index absent from the receipt"
    dep = io.decode_relay_deposit(escrow)
    if dep:
        diffs = _relay_common(hop, dep, (hop["order"],))
    else:
        native = io.decode_native_relay_deposit(escrow)
        if not native:
            return "MISMATCH: escrow log is not a Relay deposit"
        diffs = _relay_common(dict(hop, token="native"), native, (hop["order"],))
    if diffs:
        return "MISMATCH: relay escrow deposit differs: " + json.dumps(diffs, sort_keys=True)
    paid = io.rpc(hop["fill_chain"], "eth_getTransactionByHash", [hop["fill_tx"]], state=True)
    if not paid:
        raise net.SourceError(f"chain {hop['fill_chain']}: solver payment {hop['fill_tx']} not served")
    if (paid.get("hash") or "").lower() != hop["fill_tx"].lower():
        return "MISMATCH: solver payment names another transaction"
    if paid.get("chainId") is not None and int(paid["chainId"], 16) != hop["fill_chain"]:
        return "MISMATCH: solver payment chain differs"
    if not paid["input"].lower().endswith(order):
        return "MISMATCH: order id absent from the solver's payment"
    return "ok"


def _safe_check(fn, item, cache, *args):
    """An RPC failure is an unavailable check, never a passing check or factual mismatch.
    A receipt whose shape cannot be read is a failed check, not a pass."""
    try:
        return fn(item, cache, *args)
    except net.SourceError as exc:
        return f"UNAVAILABLE: {exc}"
    except (KeyError, ValueError, TypeError, IndexError) as exc:
        return f"MISMATCH: unreadable receipt: {type(exc).__name__}: {exc}"


def reconcile(week, out=None):
    data = json.loads(((out or report.OUT) / "weeks" / week / "transactions.json").read_text())
    orders = defaultdict(set)                      # escrow (chain, tx, log index) -> Relay order ids of this week
    for e in data["events"]:
        for h in e["hops"]:
            if h["kind"] == "RELAY_ORDER":
                orders[(h["chain"], h["tx"], h["log_index"])].add(h["order"])
    cache, results, seen = {}, [], set()
    for e in data["events"]:
        refs = [("changenow side", e["cn"]), ("polymarket side", e["pm"])] + [(h["kind"], h) for h in e["hops"]]
        for name, ref in refs:
            if name == "RELAY_ORDER":
                # Relay escrow event is NOT an ERC-20 Transfer log: verify its own semantics.
                relay_key = ("relay", ref["chain"], ref["tx"], ref["fill_chain"],
                             ref["fill_tx"], ref["log_index"], ref["order"])
                if relay_key not in seen:
                    seen.add(relay_key)
                    results.append((e["event_id"], "relay order id", ref["chain"],
                                    ref["tx"], _safe_check(check_relay, ref, cache)))
                continue
            relay_orders = tuple(sorted(orders.get((ref["chain"], ref["tx"], ref["log_index"]), ())))
            k = (ref["chain"], ref["tx"], ref["log_index"], ref["src"], ref["dst"], str(ref["raw"]), relay_orders)
            if k not in seen:
                seen.add(k)
                results.append((e["event_id"], name, ref["chain"], ref["tx"],
                                _safe_check(check_transfer, ref, cache, relay_orders)))
    bad = [r for r in results if r[4].startswith("MISMATCH")]
    skipped = [r for r in results if r[4].startswith("not checked")]
    unavailable = [r for r in results if r[4].startswith("UNAVAILABLE:")]
    for r in bad:
        print("FAIL", *r)
    for r in unavailable:
        print("UNAVAILABLE", *r)
    print(f"{week}: {len(data['events'])} events, {len(results)} references read again from {len(cache)} receipts: {len(results) - len(bad) - len(skipped) - len(unavailable)} ok, {len(skipped)} not checked, {len(bad)} mismatches, {len(unavailable)} unavailable")
    return dict(week=week, events=len(data["events"]), references=len(results), receipts=len(cache), ok=len(results) - len(bad) - len(skipped) - len(unavailable), not_checked=len(skipped), mismatches=[list(r) for r in bad], unavailable=[list(r) for r in unavailable])
