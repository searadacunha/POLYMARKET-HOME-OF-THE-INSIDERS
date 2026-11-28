"""Where the money of a trading wallet came from and where it went.

Deposits and withdrawals are the collateral transfers of the wallet that are not legs of its own trading. Each
counterparty is classified as of the block of the payment, never from its present state: a key that became an
exchange wallet later was not one then. A trace follows payers (upstream) or payees (downstream) for a bounded
number of hops and stops, with a stated reason, at anything that is not a plain key: a protocol contract, a
labelled service, a contract, a key with a long history. An edge shows that a payment happened; it does not show
that the same money continued, and it says nothing about who controls an address.
"""
from collections import defaultdict

from monitoring.phi_monitor import chain

from . import registry
from .ledger import amount

LOOK_BLOCKS = 2_000_000   # about six weeks of Polygon blocks on either side of a payment
PERSONAL = "key"


def classify(address, block=None, kind_reader=chain.account_kind):
    """Class of an address: from the registries when they know it, else from its code and nonce at `block`."""
    address = address.lower()
    known = registry.known(address)
    if known:
        return {"address": address, **known}
    state = kind_reader(address, block)
    return {"address": address, "kind": state["kind"], "nonce": state.get("nonce"), "as_of_block": block,
            **({"unresolved": state["unresolved"]} if state.get("unresolved") else {})}


def _edge(row, hop=0):
    return {"tx": row["tx"], "log_index": row["log_index"], "block": row["block"], "ts": row["ts"], "from": row["from"], "to": row["to"],
            "token": row["token"], "amount_raw": row["amount_raw"], "amount": amount(row["amount_raw"]), "hop": hop}


def cash_flows(sources, wallet, trading_txs=(), from_block=0, to_block=None, kind_reader=chain.account_kind):
    """Deposits into and withdrawals from a trading wallet, with each counterparty classified at its first payment.

    trading_txs: transaction hashes of the wallet's own trades, splits, merges and redemptions (from its activity
    rows). Every transfer inside those transactions is a trading leg, not funding.

    The other transactions are read one by one, because the collateral changes form on its way in and out: a deposit
    can arrive as one stablecoin and be wrapped into another in the same transaction, and a withdrawal can be unwrapped
    before it leaves. What a transaction brings in or takes out is its net over the three collateral tokens:
      - net zero: a conversion (wrap, unwrap or exchange of one stablecoin for another), neither deposit nor withdrawal;
      - net positive: a deposit, shown by the legs received from addresses outside the protocol; when there is none
        (collateral minted to the wallet through the protocol's onramp or a bridge) by the mint or unwrap legs, whose
        payer is then not visible in the wallet's own transfers, and the row says so;
      - net negative: a withdrawal, the same way round.
    A transaction with outside legs on both sides passes money through the wallet in one step and is counted apart. A
    transaction that moves collateral with the trading contracts only, and that the activity rows do not list, is not
    funding: it is counted as an unlisted trading transaction.
    """
    wallet = wallet.lower()
    trading = {t.lower() for t in trading_txs}
    read = {"in": sources.transfers(wallet, "in", from_block, to_block), "out": sources.transfers(wallet, "out", from_block, to_block)}
    by_tx, order = defaultdict(lambda: {"in": [], "out": []}), []
    for direction in ("in", "out"):
        for row in read[direction]["rows"]:
            if row["tx"] not in by_tx:
                order.append(row["tx"])
            by_tx[row["tx"]][direction].append(row)
    flows, legs, conversions, swaps, classes, hidden, unlisted = {"in": [], "out": []}, 0, 0, 0, {}, 0, 0
    net_totals, passed = {"in": 0, "out": 0}, 0

    def inside(row, other):
        role = registry.known(row[other])
        return row[other] == wallet or bool(role and role["kind"] in ("protocol", "mint"))

    for tx in sorted(order, key=lambda t: min((r["block"], r["log_index"]) for d in ("in", "out") for r in by_tx[t][d])):
        got, sent = by_tx[tx]["in"], by_tx[tx]["out"]
        if tx.lower() in trading:
            legs += len(got) + len(sent)
            continue
        net = sum(r["amount_raw"] for r in got) - sum(r["amount_raw"] for r in sent)
        outside = {"in": [r for r in got if not inside(r, "from")], "out": [r for r in sent if not inside(r, "to")]}
        if outside["in"] and outside["out"]:
            swaps += len(got) + len(sent)   # received from and paid to outside addresses at once: passed through, or exchanged
            passed += net
            continue
        if net == 0:
            conversions += len(got) + len(sent)
            continue
        direction, other = ("in", "from") if net > 0 else ("out", "to")
        shown = outside[direction] or [r for r in by_tx[tx][direction] if registry.is_collateral_ramp(r[other])]
        if not shown:
            unlisted += 1
            legs += len(got) + len(sent)
            continue
        if not outside[direction]:
            hidden += 1
        legs += len(got) + len(sent) - len(shown)
        net_totals[direction] += abs(net)
        for row in shown:
            party = row[other]
            if party not in classes:
                classes[party] = classify(party, row["block"], kind_reader)
            flows[direction].append({**_edge(row), "counterparty": party, "counterparty_kind": classes[party]["kind"],
                                     "counterparty_label": classes[party].get("label"), "transaction_net": amount(abs(net)),
                                     **({} if outside[direction] else {"payer_not_in_own_transfers" if net > 0 else "payee_not_in_own_transfers": True})})
    totals = {}
    for direction in ("in", "out"):
        by_token = defaultdict(int)
        for row in flows[direction]:
            by_token[row["token"]] += row["amount_raw"]
        totals["deposited" if direction == "in" else "withdrawn"] = {token: amount(value) for token, value in sorted(by_token.items())}
    totals["net_deposited"], totals["net_withdrawn"] = amount(net_totals["in"]), amount(net_totals["out"])   # every collateral token at par
    totals["net_of_pass_through_transactions"] = amount(passed)   # what exchanging or relaying inside one transaction left or cost
    return {"wallet": wallet, "deposits": flows["in"], "withdrawals": flows["out"], "counterparties": classes, "totals": totals,
            "first_deposit": flows["in"][0] if flows["in"] else None, "trading_legs_excluded": legs, "conversion_legs_excluded": conversions,
            "collateral_swap_legs_excluded": swaps, "transactions_through_the_protocol_only": hidden,
            "trading_contract_transactions_without_activity_row": unlisted,
            "net_collateral_moved_raw": sum(r["amount_raw"] for r in read["in"]["rows"]) - sum(r["amount_raw"] for r in read["out"]["rows"]),
            "scan": {"from_block": read["in"]["from_block"], "to_block": read["in"]["to_block"], "calls": read["in"]["calls"] + read["out"]["calls"]}}


def trace(sources, start, direction, at_block, hops=2, branch=4, look_blocks=LOOK_BLOCKS, min_amount_raw=1_000_000,
          kind_reader=chain.account_kind):
    """Follow payers (`upstream`) or payees (`downstream`) of `start` around `at_block`, a bounded number of hops.

    Upstream reads the payments received in the `look_blocks` before the block considered; downstream reads the
    payments sent in the `look_blocks` after. At each address the `branch` largest payments are followed, the others
    are counted in `payments_not_followed`. Stops are listed with their reason; nothing is followed through a stop.
    """
    if direction not in ("upstream", "downstream"):
        raise ValueError("direction must be 'upstream' or 'downstream'")
    start = start.lower()
    nodes, edges, stops, cut, seen = {}, [], [], 0, {start}
    frontier = [(start, at_block)]
    head = sources.head() if direction == "downstream" else None
    for hop in range(1, hops + 1):
        following = []
        for address, block in frontier:
            window = (max(0, block - look_blocks), block) if direction == "upstream" else (block, min(head, block + look_blocks))
            rows = sources.transfers(address, "in" if direction == "upstream" else "out", *window)["rows"]
            rows = sorted((r for r in rows if r["amount_raw"] >= min_amount_raw), key=lambda r: -r["amount_raw"])
            cut += max(0, len(rows) - branch)
            for row in rows[:branch]:
                party = row["from"] if direction == "upstream" else row["to"]
                edges.append(_edge(row, hop))
                if party in seen:
                    continue
                seen.add(party)
                nodes[party] = classify(party, row["block"], kind_reader)
                if nodes[party]["kind"] != PERSONAL:
                    stops.append({"address": party, "reason": nodes[party].get("label") or nodes[party]["kind"], "hop": hop})
                elif hop == hops:
                    stops.append({"address": party, "reason": "hop limit", "hop": hop})
                else:
                    following.append((party, row["block"]))
        frontier = following
    return {"start": start, "direction": direction, "at_block": at_block, "nodes": nodes, "edges": edges, "stops": stops,
            "payments_not_followed": cut,
            "limits": {"hops": hops, "branch": branch, "look_blocks": look_blocks, "min_amount": amount(min_amount_raw),
                       "reading": "an edge is a payment between two addresses; it does not show that the same money continued, "
                                  "and it does not show who controls either address"}}


def pass_throughs(deposits, withdrawals, within_seconds=86_400):
    """Withdrawals that send out exactly an amount received shortly before: the wallet relayed it rather than traded it."""
    out = []
    for sent in withdrawals:
        for got in deposits:
            if got["amount_raw"] == sent["amount_raw"] and got["token"] == sent["token"] and 0 <= sent["ts"] - got["ts"] <= within_seconds:
                out.append({"received": got["tx"], "sent": sent["tx"], "amount": amount(sent["amount_raw"]), "token": sent["token"],
                            "seconds_between": sent["ts"] - got["ts"], "from": got["from"], "to": sent["to"]})
                break
    return out
