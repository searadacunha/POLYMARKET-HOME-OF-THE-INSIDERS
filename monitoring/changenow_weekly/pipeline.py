"""From raw transfers to customer-facing flows of one chain and one week.

Order of work: recognised tokens, measured role of each registered address, the one-time deposit addresses that feed
the service, then two lists: payouts (service to outside address) and customer deposits (outside address to a deposit
address). Service plumbing is counted and set aside, never listed as a customer flow.
"""
import time
from collections import Counter, defaultdict

from phi_monitor import net

from . import chainio as io
from . import collect, prices, registry

SINGLE_USE_NONCE = 2        # a deposit address signs its sweep, and at most one more transaction, in its life
EIP7702 = "0xef0100"


def unique_rows(store):
    """Registry-stream rows without the repeats that a transfer between two registered addresses creates."""
    seen = {}
    for stream in ("reg_out", "reg_in", "reg_nat_out", "reg_nat_in", "native"):
        for r in store.rows(stream):
            seen[(r["tx"], r["log_index"], r.get("trace", ""), r["src"], r["dst"], r["raw"])] = r
    return list(seen.values())


def nonces(chain, addresses):
    """Latest transaction count of many addresses, by JSON-RPC batch. Raises when no endpoint serves a batch."""
    out = {}
    for part in io.chunks(sorted(addresses), io.BATCH.get(chain, 40)):
        time.sleep(0.12)
        for url in io.CHAINS[chain]["state"]:
            try:
                body = net.get_json(url, data=[dict(jsonrpc="2.0", id=i, method="eth_getTransactionCount", params=[a, "latest"]) for i, a in enumerate(part)])
            except net.SourceError:
                continue
            if isinstance(body, list) and len(body) == len(part) and all("result" in x for x in body):
                for x in body:
                    out[part[x["id"]]] = int(x["result"], 16)
                break
        else:
            raise net.SourceError(f"chain {chain}: no endpoint served a nonce batch")
    return out


def frequent_counterparties(chain, store, reg, book, paid=3, most_paid=300):
    """Outside addresses worth a label check, from the rows on disk and the tokens already recognised: those that paid a
    registered address at least `paid` times in the week (a one-time deposit address pays once), and the recipients a
    registered address paid most often."""
    into, out = Counter(), Counter()
    for r in unique_rows(store):
        if r["raw"] <= 0 or not book.data["tokens"].get(prices.coin(chain, r["token"])):
            continue
        if r["dst"] in reg and r["src"] not in reg:
            into[r["src"]] += 1
        if r["src"] in reg and r["dst"] not in reg:
            out[r["dst"]] += 1
    return sorted(({a for a, n in into.items() if n >= paid} | {a for a, _ in out.most_common(most_paid)}) - {io.ZERO})


def population(chain, store, reg, book, say=print):
    """Roles, deposit addresses, payouts and the counts of everything set aside, from the registry streams on disk."""
    rows = unique_rows(store)
    tokens = book.recognise(chain, sorted({r["token"] for r in rows}))
    good = [r for r in rows if r["token"] in tokens and r["raw"] > 0]
    roles = registry.roles(good, reg)
    usable = registry.usable(reg)
    sources = sorted(a for a, v in roles.items() if a in usable and v["role"] == "PAYOUT_HOT")
    funders = sorted(a for a, v in roles.items() if v["role"] == "GAS_FUNDER")
    gas_paid = {r["dst"] for r in good if r["src"] in funders and r["token"] == "native"}
    into = defaultdict(set)                                  # outside sender -> sources it paid
    for r in good:
        if r["dst"] in sources and r["src"] not in reg:
            into[r["src"]].add(r["dst"])
    token_deposits = set(into) & gas_paid                    # funded with gas by the service, then swept into it
    maybe_single = sorted(set(into) - gas_paid)              # others: kept only when a plain key that signed one or two transactions in its life
    native_deposits = set()
    if maybe_single:
        codes = io.get_codes(chain, maybe_single)
        count = nonces(chain, [a for a in maybe_single if codes[a] in ("0x", "0x0")])
        native_deposits = {a for a, n in count.items() if 1 <= n <= SINGLE_USE_NONCE}
    deposits = token_deposits | native_deposits
    other_senders = sorted(set(into) - deposits)
    stats = Counter()
    payouts = []
    for r in good:
        if r["src"] not in sources:
            continue
        if r["dst"] in reg:
            stats["payout_side_internal_to_registry"] += 1
        elif r["dst"] in deposits or r["dst"] in gas_paid:
            stats["payout_side_to_own_deposit_address"] += 1
        elif r["dst"] == io.ZERO:
            stats["payout_side_burn"] += 1
        else:
            payouts.append(r)
    stats.update(rows=len(rows), recognised_rows=len(good), unrecognised_token_rows=len(rows) - len(good), payouts=len(payouts),
                 payout_recipients=len({r["dst"] for r in payouts}), deposit_addresses_gas_funded=len(token_deposits), deposit_addresses_single_use=len(native_deposits),
                 gas_funded_addresses=len(gas_paid), other_senders_into_sources=len(other_senders))
    say(f"  {io.CHAINS[chain]['name']}: sources {sources}, gas funders {funders}, " + ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))
    return dict(chain=chain, tokens=tokens, roles=roles, sources=sources, funders=funders, deposits=deposits, token_deposits=token_deposits,
                native_deposits=native_deposits, gas_paid=gas_paid, other_senders=other_senders, payouts=payouts, good=good, stats=dict(stats), swept={a: sorted(v) for a, v in into.items() if a in deposits})


def customer_deposits(chain, store, pop, reg, blocks, book, say=print):
    """Transfers into the week's deposit addresses from outside addresses, with the sweep that ties each address to the service.
    Native deposits are read on Polygon only, where they leave a log; elsewhere they are counted as not read."""
    deposits = pop["deposits"]
    stats = dict(deposit_addresses=len(deposits))
    swept = None
    if io.CHAINS[chain].get("by_contract"):
        # this chain's own node serves too few blocks a call for a whole week of every token: the read names the tokens
        # the deposit addresses swept into the service, which a node that serves wide ranges accepts
        swept = sorted({r["token"] for r in pop["good"] if r["src"] in deposits and r["dst"] in pop["sources"] and r["token"] != "native"})
    if swept is None or swept:
        stats["tokens"] = collect.dependent_stream(store, chain, "dep_in", blocks, deposits, "dst", tokens=swept, say=say)
    else:                                                    # no token was swept: nothing to read, and no row of an earlier run is kept
        store.drop("dep_in")
        stats["tokens"] = dict(read=None, rows=0, addresses=len(deposits), windows=0, heavy=[])
    stats["token_filter"] = None if swept is None else len(swept)
    rows = list(store.rows("dep_in"))
    if chain == 137:
        stats["native"] = collect.dependent_stream(store, chain, "dep_nat_in", blocks, deposits, "dst", native=True, say=say)
        rows += list(store.rows("dep_nat_in"))
    pop["tokens"].update(book.recognise(chain, sorted({r["token"] for r in rows})))
    inside = set(reg) | deposits | set(pop["funders"])
    out = [r for r in rows if r["token"] in pop["tokens"] and r["raw"] > 0 and r["src"] not in inside and r["src"] != io.ZERO]
    stats.update(rows=len(rows), customer_deposits=len(out), senders=len({r["src"] for r in out}), native_read=chain == 137,
                 deposit_addresses_without_customer_row=len(deposits - {r["dst"] for r in out}))
    say(f"  {io.CHAINS[chain]['name']}: {len(out)} customer deposits from {stats['senders']} senders into {len(deposits)} deposit addresses")
    return out, stats


def delegated(chain, addresses):
    """{address: delegate} for addresses carrying an EIP-7702 delegation on this chain."""
    codes = io.get_codes(chain, sorted(addresses))
    return {a: "0x" + c[8:48].lower() for a, c in codes.items() if c.lower().startswith(EIP7702)}
