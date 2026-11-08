#!/usr/bin/env python3
"""Offline, independently computed evidence tiers for the 38-account Iran cohort.

Reads immutable snapshots already present on main. Does not query RPC, infer
ownership, mutate original evidence or treat a shared service as a control link.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HIST = ROOT / "research_notes/x-history-2026-11-06/verification"
FLOW = ROOT / "research_notes/financial-links-replay-2026-11-07"
DATA = HIST / "data"
EVIDENCE = HIST / "evidence"
DEST = "0xc5bb1be0407db7312911ec765d399d02461e411a"
INTERMEDIARY = "0x12d5b13fc89bcae0e68557a42d6bf9ec319b7944"
POLY_USDC = "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359"
POLY_USDCE = "0x2791bca1f2de4661ed88a30c99a7a9449aa84174"
ARB_USDC = "0xaf88d065e77c8cc2239327b3a432268e5831"
THREE_POLYGON_RELAY_ACCOUNTS = {
    "0x858d551d073e9c647c17079ad9021de830201047": 6,
    "0x5e0b017aef88af84fb3897fecce7413c6754981a": 2,
    "0x8a480b60cb78213fdf34842160dc956a831a2558": 4,
}
OTHER_RELAY_ACCOUNTS = {
    "0xb390ae2cc3fd8cb2670a62129faeb775faee106c": 8453,
    "0x95bd107886bd48d6737029603e3db242fb781652": 8453,
    "0x4ec2f11d2893eb1bc3bab7449910540c93adf7ec": 42161,
}


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise AssertionError(reason)


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def csv_rows(path: Path):
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def fetch_rows(address: str, chain: int, action: str):
    folder = EVIDENCE / "etherscan" / address
    files = sorted(folder.glob(f"{chain}_{action}_p*.json"))
    require(bool(files), f"missing archived {chain} {action} for {address}")
    rows = []
    for path in files:
        rows.extend(load(path)["result"])
    return rows


def orders_for(address: str):
    folder = EVIDENCE / "relay" / address
    files = sorted(folder.glob("p*.json"))
    require(bool(files), f"missing archived Relay responses for {address}")
    orders = []
    for p in files:
        orders.extend(load(p)["requests"])
    return orders


def recipient_orders(wallet: str, chain: int):
    orders = []
    for item in orders_for(wallet):
        out = (item.get("data", {}).get("metadata") or {}).get("currencyOut") or {}
        cur = out.get("currency") or {}
        if item.get("recipient", "").lower() != DEST or cur.get("chainId") != chain:
            continue
        require(item.get("user", "").lower() == wallet, "unexpected Relay user")
        require(item.get("status") == "success", "Relay route not settled")
        require(cur.get("decimals") == 6, "unexpected token decimals")
        token_expected = ARB_USDC if chain == 42161 else (
            POLY_USDC if chain == 137 else "0x833589fcd6edb6e08f4c7c32d4f71b54bda02913"
        )
        require(cur.get("address", "").lower() == token_expected, "wrong destination token")
        orders.append(item)
    return orders


def matched_transfers(orders, transfers):
    """Bijective, amount-exact comparison; totals and approximate timing are insufficient."""
    expected = Counter(int(x["data"]["metadata"]["currencyOut"]["amount"]) for x in orders)
    observed = Counter(int(x["value"]) for x in transfers)
    require(expected == observed, f"Relay order/receipt multiset mismatch: {expected - observed}; {observed - expected}")
    require(len({x["id"].lower() for x in orders}) == len(orders), "repeated Relay order id")
    return len(orders)


def main():
    accounts = csv_rows(DATA / "g38_accounts.csv")
    proxies = [x["proxy"].lower() for x in accounts]
    registered = {x.strip().lower() for x in (DATA / "g38_resolved_proxies.txt").read_text().splitlines() if x.strip()}
    require(len(accounts) == len(set(proxies)) == len(registered) == 38, "not 38 unique trading proxies")
    require(set(proxies) == registered, "account membership differs from frozen roster")
    require(sum(x["created"][:10] in ("2026-02-22", "2026-02-23", "2026-02-24", "2026-02-25") for x in accounts) == 36, "new-account count differs")
    early = [x for x in accounts if x["created"][:10] in ("2026-02-22", "2026-02-23", "2026-02-24", "2026-02-25")]
    require(all(x["no_before_yes"] == "True" and x["first_yes"].startswith("02-27 ") for x in early), "NO/YES sequence changed")
    unserved = [x["name"] for x in accounts if x["profile_served"] != "True"]
    require(unserved == ["Anon"], "unverified handle status changed")

    ledger = load(DATA / "ledger_g38.json")
    require(set(ledger) == registered, "per-account accounting membership changed")
    for a in accounts:
        src = ledger[a["proxy"].lower()]
        require(Decimal(src["trading_result"]).quantize(Decimal("0.01")) == Decimal(a["result"]), "PnL index differs from underlying ledger")
        require(len(src["open_share_tokens"]) == int(a["open_tokens"]), "open share token count differs")
    result_sum = sum((Decimal(r["result"]) for r in accounts), Decimal(0))
    require(result_sum == Decimal("1576522.86"), "snapshot result sum changed")
    open_accounts = sum(int(a["open_tokens"]) > 0 for a in accounts)
    require(open_accounts == 8, "open-position count changed")

    funding = csv_rows(FLOW / "data/g38_deposit_origins.csv")
    funders = defaultdict(set)
    for row in funding:
        require(row["proxy"].lower() in registered, "foreign account in funding table")
        funders[row["funding_wallet"]].add(row["proxy"].lower())
    require(len(funding) == 86 and len(funders) == 39, "inbound Relay population changed")
    require(all(len(x) == 1 for x in funders.values()), "an origin address funds multiple cohort accounts")

    polygon = fetch_rows(DEST, 137, "tokentx")
    canonical = {POLY_USDC, POLY_USDCE}
    incoming = [x for x in polygon if x["to"].lower() == DEST and
                x["contractAddress"].lower() in canonical and int(x["value"]) > 0]
    outgoing = [x for x in polygon if x["from"].lower() == DEST and
                x["contractAddress"].lower() in canonical and int(x["value"]) > 0]
    require(sum(int(x["value"]) for x in incoming) ==
            sum(int(x["value"]) for x in outgoing) == 1984038168550, "Polygon 1.984m token reconciliation failed")

    direct = [x for x in incoming if x["from"].lower() in registered]
    direct_wallets = {x["from"].lower() for x in direct}
    require(len(direct_wallets) == 32, "distinct direct Polygon account count changed")
    other = [x for x in incoming if x["from"].lower() not in registered]
    dust = [x for x in other if int(x["value"]) < 10000]
    require(len(dust) == 2 and len({x["from"].lower() for x in dust}) == 2, "look-alike dust must remain separately visible")
    relay_credits = [x for x in other if int(x["value"]) >= 10000]
    require(len(relay_credits) == 12 and all(x["contractAddress"].lower() == POLY_USDC for x in relay_credits),
            "unexpected non-cohort Polygon USDC credit")

    matched_orders = []
    for wallet, count in THREE_POLYGON_RELAY_ACCOUNTS.items():
        items = recipient_orders(wallet, 137)
        require(len(items) == count, f"unexpected number of Polygon orders for {wallet}")
        matched_orders.extend(items)
    require(matched_transfers(matched_orders, relay_credits) == 12, "non-bijective Polygon Relay receipt proof")
    require(len({x["from"].lower() for x in relay_credits}) == 3, "unexpected Polygon Relay sender count")

    arb_wallet = next(x for x, chain in OTHER_RELAY_ACCOUNTS.items() if chain == 42161)
    arb_orders = recipient_orders(arb_wallet, 42161)
    arb = fetch_rows(DEST, 42161, "tokentx")
    arb_in = [x for x in arb if x["to"].lower() == DEST and x["contractAddress"].lower() == ARB_USDC]
    arb_out = [x for x in arb if x["from"].lower() == DEST and x["contractAddress"].lower() == ARB_USDC]
    require(len(arb_orders) == len(arb_in) == len(arb_out) == 1, "Arbitrum route unexpectedly changed")
    matched_transfers(arb_orders, arb_in)
    require(arb_out[0]["value"] == arb_in[0]["value"] and
            arb_out[0]["to"].lower() == "0xa656f7d2a93a6f5878aa768f24eb38ec8c827fe2", "Arbitrum onward flow changed")

    base_orders = []
    for wallet, chain in OTHER_RELAY_ACCOUNTS.items():
        if chain == 8453:
            items = recipient_orders(wallet, 8453)
            require(len(items) == 1, f"unexpected Base order count for {wallet}")
            base_orders.extend(items)
    require(len(base_orders) == 2, "expected exactly two Relay-reported Base routes")

    # Economic control is not a function of a sum of transfers or an explorer label.
    print(json.dumps({
        "scope": "archived evidence, no live RPC, no ownership attribution",
        "unique_proxies": len(accounts), "36_account_no_to_yes_sequence": len(early),
        "unverified_display_name": unserved, "result_usdc_snapshot": str(result_sum),
        "accounts_with_open_share_tokens": open_accounts,
        "inbound_relay_deposit_orders": len(funding), "distinct_origin_addresses": len(funders),
        "polygon_direct_account_senders": len(direct_wallets),
        "polygon_relay_orders_matched_one_to_one": len(matched_orders),
        "polygon_received_and_swept_usdc_atomic": "1984038168550",
        "arbitrum_relay_order_and_inbound_receipt": 1,
        "arbitrum_onward_to_unattributed_address": 1,
        "base_relay_orders_without_archived_recipient_receipts": len(base_orders),
        "owner_and_coinbase_account_identity": "UNRESOLVED",
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
