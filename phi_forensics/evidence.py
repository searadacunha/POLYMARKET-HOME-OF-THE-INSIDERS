"""Check a claimed transaction against the chain, on two independent public nodes.

A claim such as "A paid B 5,170 USDC.e in transaction T" is compared with the receipt itself, never with an API
summary of it. The verdict says exactly what was seen: confirmed on two nodes, seen on one, absent, reverted,
ambiguous, or contradicted. Amounts are exact integers in the token's smallest unit.
"""
import hashlib
import json

from monitoring.livecollect import decode

from . import sources as src

ENDPOINTS = ("https://polygon-bor-rpc.publicnode.com", "https://gateway.tenderly.co/public/polygon")
SHOWN = 40  # logs listed in an answer; the counts always cover the whole receipt


def receipt_digest(receipt):
    """SHA-256 of what a receipt asserts (block, status and every log), independent of how a node formats the rest."""
    logs = [[log["address"].lower(), [t.lower() for t in log["topics"]], log["data"].lower(), int(log["logIndex"], 16)]
            for log in receipt.get("logs", [])]
    core = [receipt.get("blockHash"), receipt.get("status"), sorted(logs, key=lambda item: item[3])]
    return hashlib.sha256(json.dumps(core, separators=(",", ":")).encode()).hexdigest()


def read_receipts(sources, tx, endpoints=ENDPOINTS):
    """What each node says about one transaction: FOUND with its receipt, NOT_FOUND, or UNREACHABLE."""
    seen = []
    for endpoint in endpoints:
        try:
            receipt = sources.receipt(tx, endpoint)
        except src.SourceError as err:
            seen.append({"endpoint": endpoint, "state": "UNREACHABLE", "detail": str(err)[:160]})
            continue
        if not receipt:
            seen.append({"endpoint": endpoint, "state": "NOT_FOUND"})
        else:
            seen.append({"endpoint": endpoint, "state": "FOUND", "digest": receipt_digest(receipt), "receipt": receipt})
    return seen


def _agreed(seen):
    """(verdict or None, receipt, public view of the nodes). A verdict here means the claim cannot be checked at all."""
    view = [{k: v for k, v in s.items() if k != "receipt"} for s in seen]
    found = [s for s in seen if s["state"] == "FOUND"]
    if not found:
        return ("UNREACHABLE" if all(s["state"] == "UNREACHABLE" for s in seen) else "NOT_FOUND"), None, view
    if len({s["digest"] for s in found}) > 1:
        return "ENDPOINTS_DISAGREE", None, view
    if found[0]["receipt"].get("status") != "0x1":
        return "REVERTED", found[0]["receipt"], view
    return None, found[0]["receipt"], view


def _base(sources, tx, verdict, receipt, view):
    out = {"transaction": tx.lower(), "verdict": verdict, "nodes": view, "nodes_agreeing": sum(1 for v in view if v["state"] == "FOUND")}
    if receipt:
        block = int(receipt["blockNumber"], 16)
        out.update(block=block, block_hash=receipt.get("blockHash"), time_utc=src.utc(sources.block_time(block)),
                   receipt_sha256=receipt_digest(receipt))
    return out


def _conclude(out, matches, what):
    """Shared ending: one match on two nodes is CONFIRMED; on one node it is only SEEN_ON_ONE_NODE."""
    out["matching_logs"] = matches[:SHOWN]
    if not matches:
        out["verdict"] = "NOT_IN_RECEIPT"
    elif len(matches) > 1:
        out["verdict"], out["note"] = "AMBIGUOUS", f"{len(matches)} {what} match the claim: give log_index to name one"
    else:
        out["verdict"] = "CONFIRMED" if out["nodes_agreeing"] >= 2 else "SEEN_ON_ONE_NODE"
    return out


def verify_transfer(sources, tx, sender=None, recipient=None, token=None, amount_raw=None, log_index=None, endpoints=ENDPOINTS):
    """Compare a claimed ERC-20 transfer with the receipt. Every field given must match one Transfer log.

    Verdicts: CONFIRMED (two nodes agree and exactly one log matches), SEEN_ON_ONE_NODE, AMBIGUOUS, NOT_IN_RECEIPT,
    REVERTED, NOT_FOUND, ENDPOINTS_DISAGREE, UNREACHABLE, and DECODED when no field was given to check.
    A confirmed transfer shows that money moved between two addresses. It says nothing about who controls them.
    """
    claim = {"from": sender.lower() if sender else None, "to": recipient.lower() if recipient else None,
             "token": token.lower() if token else None, "amount": str(amount_raw) if amount_raw is not None else None,
             "log_index": log_index}
    verdict, receipt, view = _agreed(read_receipts(sources, tx, endpoints))
    out = _base(sources, tx, verdict, receipt, view) | {"claim": {k: v for k, v in claim.items() if v is not None}}
    if verdict:
        return out
    transfers = decode.decode_logs(receipt["logs"])["transfers"]
    out["transfers_in_receipt"] = len(transfers)
    if not out["claim"]:
        return out | {"verdict": "DECODED", "transfers": transfers[:SHOWN]}
    matches = [t for t in transfers if all(v is None or t[k] == v for k, v in claim.items())]
    return _conclude(out, matches, "transfers")


def verify_fill(sources, tx, wallet, token_id=None, side=None, log_index=None, endpoints=ENDPOINTS):
    """Compare a claimed Polymarket fill with the OrderFilled logs of the receipt.

    One OrderFilled log is one order being filled, seen from its owner (`maker` in the event). `shares_raw` and
    `cash_raw` are in 1e-6 units; the price is their ratio and is not rounded here.
    """
    wallet = wallet.lower()
    verdict, receipt, view = _agreed(read_receipts(sources, tx, endpoints))
    claim = {k: v for k, v in {"wallet": wallet, "token_id": token_id, "side": side, "log_index": log_index}.items() if v is not None}
    out = _base(sources, tx, verdict, receipt, view) | {"claim": claim}
    if verdict:
        return out
    fills = []
    for fill in decode.decode_logs(receipt["logs"])["fills"]:
        buy = fill["side"] == "BUY"
        fills.append({"log_index": fill["log_index"], "exchange": fill["exchange"], "version": fill["version"], "wallet": fill["maker"],
                      "counterparty": fill["taker"], "side": fill["side"], "token_id": fill["token_id"],
                      "shares_raw": fill["taker_amount_filled"] if buy else fill["maker_amount_filled"],
                      "cash_raw": fill["maker_amount_filled"] if buy else fill["taker_amount_filled"], "fee_raw": fill["fee"]})
    out["fills_in_receipt"] = len(fills)
    matches = [f for f in fills if all(f[k] == v for k, v in claim.items())]
    return _conclude(out, matches, "fills")
