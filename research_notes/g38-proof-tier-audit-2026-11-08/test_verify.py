#!/usr/bin/env python3
"""Adversarial controls for the G38 strict value-matching audit (offline only)."""
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location("g38_audit", Path(__file__).with_name("verify.py"))
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def order(num: int, identity: str):
    return {"id": identity, "data": {"metadata": {"currencyOut": {"amount": str(num)}}}}


def transfer(num: int):
    return {"value": str(num)}


def reject(orders, credits, description):
    try:
        audit.matched_transfers(orders, credits)
    except AssertionError:
        print("PASS rejects", description)
        return
    raise AssertionError("incorrectly accepted: " + description)


def main():
    items = [order(2_000_000, "id1"), order(3_000_000, "id2")]
    rows = [transfer(2_000_000), transfer(3_000_000)]
    assert audit.matched_transfers(items, rows) == 2
    # The aggregate 5 USDC agrees, but neither individual transfer matches.
    reject(items, [transfer(1_000_000), transfer(4_000_000)], "equal sum, wrong legs")
    reject(items, [transfer(2_000_000), transfer(3_000_001)], "one micro-USDC discrepancy")
    reject(items, [transfer(2_000_000)], "incomplete settlement")
    reject(items + [order(2_000_000, "id1")], rows + [transfer(2_000_000)], "replayed order id")
    assert audit.matched_transfers(
        [order(100, "x"), order(100, "y")],
        [transfer(100), transfer(100)]
    ) == 2, "identical amounts with distinct transactions are legitimate"
    try:
        audit.calldata_partition([{"id": "0x" + "11" * 32, "data": {"outTxs": [{"data": {"data": "0x" + "11" * 32}}]}}])
    except AssertionError:
        print("PASS rejects an order-id partition that is not the archived one")
    else:
        raise AssertionError("order-id partition accepted a foreign order")
    print("PASS G38 strict matching synthetic controls")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
