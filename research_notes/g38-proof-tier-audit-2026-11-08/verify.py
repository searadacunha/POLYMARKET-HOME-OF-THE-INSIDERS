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
ARB_USDC = "0xaf88d065e77c8cc2239327c5edb3a432268e5831"
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
# Archived Relay fill calldata is not the same thing as an on-chain order id.
# These three sets are the partition of the 15 destination orders. An amount
# match must not be reported as an order-id binding.
CALLDATA_HAS_ORDER_ID = {
    "0xc9e8a1f6e5776a08de56dc03b5f5aeef1564114008324c6c382cd2e22f0c5932",
    "0xb4acf47bf25a3b09c36247c77488128a89b1c740858cb4112ce77696d7d7c0f3",
    "0x3e6e35e64261c1044f77289d259e5d52669b358162c5e576baa80df12d3e40db",
    "0x054daa58a634b653fbae44517268a7902cf1f991261ae53f122a3cf85503acbf",
}
CALLDATA_WITHOUT_ORDER_ID = {
    "0x185225703db5431baf92a98a934db81077c92b94ff2334847b5ddea2f53b7b80",
    "0xb429bc9d18c1524913a5071a12d2438408e179d5ff10d6947ecbcbaf7820acf0",
    "0x3735a0e6c36bf846b3bd98e02b1b9bc21838ec025adca7b8f85121ec0e9a92e9",
    "0xe7ddd2c42c90d24ddcb2504d980fa9a25942ba667f073eac27590b9cdfd5075a",
    "0x314eee5e87d7b60308f60e6b38e1a3652e8cebd17f98bbf7d5ab38a1304ba133",
    "0x7d1c5b0a2701710242a7bb2995a2c3ff1cc7c713e83f2e9a3a5ad71f9e095ecf",
    "0xa7fa600e15f1b2d8b93dd4c02496480ed18bb90f7ab3141013c186424a5cef70",
    "0x2802ce97c3d1b6230c67cd9d797152ef97b52f6a8c1899768ed0696244e7f5f2",
}
NO_FILL_CALLDATA = {
    "0xf9da5fce9e37f0ec9192194f290c5dcc94ed069c974e70be0a0c2f333cd0b5be",
    "0x52bcbd9dedf65618899b59a0bb475918504d66d897a124f9fb5fd1c0a633fca3",
    "0xc0ea9e6494477af9dba26baefbdf1d19ee4adda4b5572fb88dd6edf919da6137",
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
    files = sorted(p for p in folder.glob(f"{chain}_{action}_p*.json") if not p.name.endswith(".meta.json"))
    require(bool(files), f"missing archived {chain} {action} for {address}")
    rows = []
    for path in files:
        rows.extend(load(path)["result"])
    return rows


def orders_for(address: str):
    folder = EVIDENCE / "relay" / address
    files = sorted(p for p in folder.glob("p*.json") if not p.name.endswith(".meta.json"))
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


def require_etherscan_complete(address, chain, action):
    """A missing next page must not look like the end of an Etherscan pull."""
    folder = EVIDENCE / "etherscan" / address
    done_path = folder / f"{chain}_{action}_DONE.json"
    require(done_path.is_file(), f"missing {chain} {action} completion marker")
    done = load(done_path)
    require(done.get("termination") == "END", f"{chain} {action} pull did not terminate")
    pages = sorted((p for p in folder.glob(f"{chain}_{action}_p*.json")
                    if not p.name.endswith(".meta.json")),
                   key=lambda p: int(p.stem.rsplit("_p", 1)[1]))
    require(done.get("pages") == len(pages), f"{chain} {action} page count disagrees with the completion marker")
    rows = 0
    for index, path in enumerate(pages, start=1):
        require(path.name == f"{chain}_{action}_p{index}.json", f"gap or unexpected page name {path.name}")
        result = load(path)["result"]
        require(isinstance(result, list), f"{chain} {action} page {index} is not a row list")
        rows += len(result)
    require(done.get("rows") == rows, f"{chain} {action} row count disagrees with the completion marker")
    return rows


def require_relay_complete(address):
    folder = EVIDENCE / "relay" / address
    done = load(folder / "DONE.json")
    require(done.get("termination") == "END", f"Relay pull for {address} did not terminate")
    pages = sorted(p for p in folder.glob("p*.json") if not p.name.endswith(".meta.json"))
    require(done.get("pages") == len(pages), f"Relay page count disagrees for {address}")
    requests = 0
    for path in pages:
        requests += len(load(path)["requests"])
    require(done.get("requests") == requests, f"Relay request count disagrees for {address}")


def fill_calldata(order):
    txs = (order.get("data") or {}).get("outTxs") or []
    if not txs:
        return ""
    return ((txs[0].get("data") or {}).get("data") or "")


def calldata_partition(orders):
    found = {"id": set(), "no": set(), "empty": set()}
    for order in orders:
        identity = order["id"].lower()
        calldata = fill_calldata(order).lower()
        if not calldata:
            found["empty"].add(identity)
        elif identity[2:] in calldata:
            found["id"].add(identity)
        else:
            found["no"].add(identity)
    require(found["id"] == CALLDATA_HAS_ORDER_ID, "orders whose fill calldata contains the order id changed")
    require(found["no"] == CALLDATA_WITHOUT_ORDER_ID, "orders whose fill calldata omits the order id changed")
    require(found["empty"] == NO_FILL_CALLDATA, "orders without archived fill calldata changed")
    return found


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

    for action in ("tokentx", "txlist", "txlistinternal"):
        require_etherscan_complete(DEST, 137, action)
    require_etherscan_complete(DEST, 42161, "tokentx")
    for wallet in (*THREE_POLYGON_RELAY_ACCOUNTS, *OTHER_RELAY_ACCOUNTS):
        require_relay_complete(wallet)

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
    require(len(dust) == 3 and len({x["from"].lower() for x in dust}) == 2, "three small transfers from two look-alike senders must remain separately visible")
    require(all(x["contractAddress"].lower() == POLY_USDCE for x in dust) and sum(int(x["value"]) for x in dust) == 538, "micro-transfer total must remain in gross accounting")
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
    destination_orders = []
    for wallet in (*THREE_POLYGON_RELAY_ACCOUNTS, *OTHER_RELAY_ACCOUNTS):
        destination_orders.extend(recipient_orders(wallet, OTHER_RELAY_ACCOUNTS.get(wallet, 137)))
    partition = calldata_partition(destination_orders)
    require(len(partition["id"]) == 4 and len(partition["no"]) == 8 and len(partition["empty"]) == 3,
            "fill calldata versus order-id partition changed")

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
        "base_relay_orders_with_provider_fill_hash": len(base_orders),
        "archived_fill_calldata_contains_order_id": len(partition["id"]),
        "archived_fill_calldata_omits_order_id": len(partition["no"]),
        "archived_orders_without_fill_calldata": len(partition["empty"]),
        "owner_and_coinbase_account_identity": "UNRESOLVED",
    }, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
