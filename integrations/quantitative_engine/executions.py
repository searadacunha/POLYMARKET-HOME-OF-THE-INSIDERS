"""One economic execution per matched fill.

A CTF Exchange match emits OrderFilled once for each order. Those two logs are
the maker view and the taker view of a single execution. Summing both counts the
same notional twice. A displayed book change is not an execution and carries no
wallet.
"""

from __future__ import annotations

from collections import defaultdict

from contracts import CTF_EXCHANGE_V2, poly_data_v2_claim

_EXCHANGE = {CTF_EXCHANGE_V2}


def _addr(value: str, label: str) -> str:
    if not isinstance(value, str) or len(value) != 42 or not value.startswith("0x"):
        raise ValueError(f"invalid {label}")
    return value.lower()


def _amount(value, label: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return value


def inspect_poly_data_csv_row(row: dict) -> dict:
    """Describe one published poly_data orderFilled.csv row without promoting it.

    That CSV keeps timestamp, maker, taker, asset ids, amounts and a transaction
    hash. It drops log index, order hash, fee, builder and metadata, and it never
    contains the neg-risk exchange. Without a log index the row cannot certify a
    unique on-chain log, so this function returns no economic execution.
    """
    if not isinstance(row, dict):
        raise ValueError("row must be a dict")
    claim = poly_data_v2_claim(str(row.get("timestamp_utc", "")), CTF_EXCHANGE_V2)
    return {
        "object_kind": "POLY_DATA_CSV_ROW",
        "coverage": claim,
        "economic_execution": None,
        "wallet_identified": False,
        "reason": "schema without log_index cannot be deduplicated to one on-chain log",
    }


def economic_executions(logs: list[dict]) -> list[dict]:
    """Collapse mirrored OrderFilled logs that share a transaction.

    Each log must already carry chain_id, transaction hash, log_index, contract,
    protocol_variant, timestamp, maker, taker and integer amounts. Conflicting
    duplicates of the same log index are rejected.
    """
    grouped = defaultdict(list)
    seen = {}
    for row in logs:
        if row.get("protocol_variant") != "CTF_EXCHANGE_V2":
            raise ValueError("protocol_variant must be explicit; V1 and V2 do not mix")
        claim = poly_data_v2_claim(row["timestamp_utc"], row["contract"])
        if claim != "SINGLE_V2_CONTRACT_ONLY":
            raise ValueError(claim)
        chain = row["chain_id"]
        if type(chain) is not int or chain < 1:
            raise ValueError("chain_id must be a positive integer")
        tx = row["transaction_hash"].lower()
        if not isinstance(tx, str) or len(tx) != 66 or not tx.startswith("0x"):
            raise ValueError("invalid transaction hash")
        index = row["log_index"]
        if type(index) is not int or index < 0:
            raise ValueError("log_index required; a missing index cannot prove a distinct log")
        identity = (chain, tx, index)
        fingerprint = (
            _addr(row["maker"], "maker"),
            _addr(row["taker"], "taker"),
            str(row["maker_asset"]),
            str(row["taker_asset"]),
            _amount(row["maker_amount"], "maker_amount"),
            _amount(row["taker_amount"], "taker_amount"),
        )
        if identity in seen and seen[identity] != fingerprint:
            raise ValueError(f"conflicting OrderFilled log {identity}")
        seen[identity] = fingerprint
        grouped[(chain, tx)].append({
            "chain_id": chain,
            "transaction_hash": tx,
            "log_index": index,
            "timestamp_utc": row["timestamp_utc"],
            "contract": row["contract"].lower(),
            "maker": fingerprint[0],
            "taker": fingerprint[1],
            "maker_asset": fingerprint[2],
            "taker_asset": fingerprint[3],
            "maker_amount": fingerprint[4],
            "taker_amount": fingerprint[5],
        })

    executions = []
    for (chain, tx), items in sorted(grouped.items()):
        items.sort(key=lambda item: item["log_index"])
        used = set()
        for i, left in enumerate(items):
            if i in used:
                continue
            partner = None
            for j in range(i + 1, len(items)):
                if j not in used and _mirror(left, items[j]):
                    partner = j
                    break
            used.add(i)
            right = None
            if partner is not None:
                used.add(partner)
                right = items[partner]
            executions.append(_execution(left, right))
    return executions


def _mirror(left: dict, right: dict) -> bool:
    return (
        left["maker"] == right["taker"]
        and left["taker"] == right["maker"]
        and left["maker_asset"] == right["taker_asset"]
        and left["taker_asset"] == right["maker_asset"]
        and left["maker_amount"] == right["taker_amount"]
        and left["taker_amount"] == right["maker_amount"]
        and left["log_index"] != right["log_index"]
    )


def _usdc(log: dict):
    if log["maker_asset"] == "0":
        return log["maker_amount"]
    if log["taker_asset"] == "0":
        return log["taker_amount"]
    return None


def _party(address: str) -> dict:
    if address in _EXCHANGE:
        return {"address": address, "role": "EXCHANGE_CONTRACT", "wallet": None}
    return {"address": address, "role": "FILL_PARTICIPANT", "wallet": address}


def _execution(left: dict, right) -> dict:
    notional = _usdc(left)
    if right is not None and _usdc(right) not in (None, notional):
        raise ValueError("mirrored logs disagree on the USDC amount")
    indexes = [left["log_index"]]
    if right is not None:
        indexes.append(right["log_index"])
    return {
        "object_kind": "ECONOMIC_EXECUTION",
        "chain_id": left["chain_id"],
        "transaction_hash": left["transaction_hash"],
        "log_indexes": indexes,
        "views": 2 if right is not None else 1,
        "notional_usdc_raw": notional,
        "counted_once": True,
        "maker": _party(left["maker"]),
        "taker": _party(left["taker"]),
        "timestamp_utc": left["timestamp_utc"],
        "contract": left["contract"],
        "coverage": "SINGLE_V2_CONTRACT_ONLY",
        "unpaired": right is None,
    }
