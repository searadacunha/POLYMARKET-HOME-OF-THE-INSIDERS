"""One function per investigative question, composed from the modules. Every answer carries its sources and its limits.

Nothing here scores a wallet or calls anyone an insider. The functions reconstruct what a wallet did, where its
money came from and went, and which other wallets it has a demonstrated money relation with; what those facts mean
is left to a protocol written before the data are seen.
"""
import json
from fractions import Fraction

from monitoring.phi_monitor import chain

from . import cluster, funding, ledger, sources as src

VALUATION_CAP = 400          # markets with inventory that are looked up in the catalogue in one call
AS_OF_PRICE_CAP = 40         # outcome tokens priced from history for a past date
SLOWEST_BLOCK_SECONDS = 1.5  # Polygon never averaged less: gives a block that is certainly early enough


def block_floor(sources, timestamp, margin_blocks=500_000):
    """A block certainly before `timestamp`, from the head and the fastest block time: no search, two calls."""
    head = sources.head()
    return max(0, head - int(max(0, sources.block_time(head) - timestamp) / SLOWEST_BLOCK_SECONDS) - margin_blocks), head


def catalogue_prices(sources, conditions):
    """Payout of resolved markets and present mark of open ones, and the neg-risk event each market belongs to.

    Returns ({condition: {"prices", "source"}}, {condition: neg-risk event id}).
    """
    out, events, now = {}, {}, src.utc(sources.clock())
    for condition, record in sources.markets(conditions).items():
        if record.get("negRiskMarketID"):
            events[condition] = str(record["negRiskMarketID"]).lower()
        try:
            prices = [Fraction(p) for p in json.loads(record["outcomePrices"])]
        except (KeyError, TypeError, ValueError, ZeroDivisionError):
            continue  # the market stays not valued and is counted as such
        resolved = bool(record.get("closed")) and record.get("umaResolutionStatus") == "resolved"
        out[condition] = {"prices": dict(enumerate(prices)), "source": "RESOLUTION (catalogue)" if resolved else f"MARK (catalogue, {now})"}
    return out, events


def reconcile_positions(sources, wallet, built, tolerance=100_000):
    """The rebuilt holdings against the positions the platform reports now, token by token (tolerance 0.1 share).

    Outcomes the catalogue does not list cannot appear in the platform list: they are counted apart, not as differences.
    """
    mine, unlisted = {}, 0
    for market in built["markets"]:
        for share in market["shares"]:
            if market["condition_id"].startswith(ledger.UNLISTED):
                unlisted += 1
            else:
                mine[share["token_id"]] = ledger.units(share["held_with_sets"])
    read = sources.positions(wallet)
    theirs = {str(p["token_id"]): ledger.units(p.get("current_size") or 0) for p in read["rows"]}
    tokens = sorted(set(mine) | set(theirs))
    differ = [{"token_id": t, "rebuilt": ledger.amount(mine.get(t, 0)), "platform": ledger.amount(theirs.get(t, 0))}
              for t in tokens if abs(mine.get(t, 0) - theirs.get(t, 0)) > tolerance]
    return {"tokens_compared": len(tokens), "agree": len(tokens) - len(differ), "differ": len(differ), "differences": differ[:25],
            "tokens_of_outcomes_not_in_catalogue": unlisted, "platform_list_complete": read["complete"],
            "note": "the platform lists current positions only; a token held together with a complete set shows here as a difference"}


def past_prices(sources, built, as_of):
    """Last traded price at or before `as_of` for each outcome still held: nothing later than the date is read."""
    tokens = [(m["condition_id"], s) for m in built["markets"] if m["status"] == "INVENTORY_NOT_VALUED" for s in m["shares"]]
    out = {}
    for condition, share in tokens[:AS_OF_PRICE_CAP]:
        history = [p for p in sources.price_history(share["token_id"], start=as_of - 7 * 86400, end=as_of, fidelity=60) if p["t"] <= as_of]
        if history and share["outcome_index"] is not None:
            entry = out.setdefault(condition, {"prices": {}, "source": f"MARK (price history at or before {src.utc(as_of)})"})
            entry["prices"][share["outcome_index"]] = Fraction(str(history[-1]["p"]))
    return out


def exact_window(sources, rows, block_at):
    """Blocks to read for the rows of a wallet: from just before its first row to the head, or to well after its last row
    when the wallet has been silent for a month (an old wallet then costs a few calls instead of a scan of the whole chain)."""
    first, last = min(r["timestamp"] for r in rows), max(r["timestamp"] for r in rows)
    head = sources.head()
    quiet = sources.block_time(head) - last > 30 * 86400
    return max(0, block_at(first) - 10), min(head, block_at(last) + 400_000) if quiet else head


def wallet_ledger(sources, wallet, as_of=None, exact=False, max_rows=200_000, block_at=chain.block_at, valuation_cap=VALUATION_CAP):
    """Positions and P&L of a wallet. `exact` takes every amount from the chain; `as_of` rebuilds a past date.

    `valuation_cap` bounds the markets priced from the catalogue in one call; None prices every market with inventory.
    """
    read = sources.activity(wallet, end=as_of, max_rows=max_rows)
    rows, deltas, homes = read["rows"], None, None
    converted = {r["condition_id"].lower() for r in rows if r.get("type") == "CONVERSION"}
    settled = {}
    if exact and rows:
        first, last = exact_window(sources, rows, block_at)
        parts = [sources.transfers(wallet, "in", first, last), sources.transfers(wallet, "out", first, last),
                 sources.position_transfers(wallet, "in", first, last), sources.position_transfers(wallet, "out", first, last)]
        deltas = ledger.chain_deltas(*[p["rows"] for p in parts])
        by_event = {r["condition_id"].lower(): set(deltas.get(r["transaction_hash"].lower(), {"tokens": {}})["tokens"])
                    for r in rows if r.get("type") == "CONVERSION"}
        listed = {r["transaction_hash"].lower() for r in rows if r.get("transaction_hash")}
        unlisted = {t for tx, d in deltas.items() if tx not in listed for t, moved in d["tokens"].items() if moved}  # the API misses these
        wanted = set().union(unlisted, *by_event.values())
        homes = sources.markets_by_tokens(wanted) if wanted else {}
        if as_of is None:
            for event, tokens in by_event.items():  # one outcome of a neg-risk event pays: once it is known, every other is worth nothing
                won = any(h["neg_risk_event"] == event and h["resolved"] and h["outcome_index"] == 0
                          and json.loads(h["outcome_prices"] or "[]")[:1] == ["1"] for h in homes.values())
                if won:
                    settled.update({ledger.UNLISTED + t: {"prices": {0: 0}, "source": "NEG-RISK EVENT SETTLED ON ANOTHER OUTCOME (catalogue)"}
                                    for t in tokens if t not in homes})
    draft = ledger.build(rows, as_of=as_of, chain=deltas, token_markets=homes)
    open_markets = [m["condition_id"] for m in draft["markets"] if m["status"] == "INVENTORY_NOT_VALUED" and not m["condition_id"].startswith(ledger.UNLISTED)]
    unreliable = {}
    if as_of is not None:
        prices = past_prices(sources, draft, as_of)
    else:
        prices, events = catalogue_prices(sources, open_markets[:valuation_cap])
        prices.update(settled)
        if converted and not exact:  # the API row of a conversion does not say which markets of the event lost or gained shares
            unreliable = {c: "IN_A_CONVERTED_NEG_RISK_EVENT" for c, event in events.items() if event in converted}
    built = ledger.build(rows, prices, as_of=as_of, chain=deltas, token_markets=homes, unreliable=unreliable) if prices or unreliable else draft
    built.update(wallet=wallet.lower(), as_of_utc=src.utc(as_of) if as_of is not None else None, history_complete=read["complete"],
                 activity_rows=len(rows), markets_with_inventory=len(open_markets), conversions=len([r for r in rows if r.get("type") == "CONVERSION"]))
    if as_of is None:
        built["platform_positions_check"] = reconcile_positions(sources, wallet, built)
    built["limits"] = [limit for limit in (
        None if read["complete"] else f"history cut at {max_rows} rows: totals are partial",
        None if exact else "amounts are those of the API: on markets traded before 28 April 2026 11:00 UTC a fee could be taken in shares, "
                           f"and the API shows sizes and proceeds before it; those markets carry the flag {ledger.GROSS}; ask for exact "
                           "amounts to take them from the chain",
        f"{built['chain']['chain_only_transactions_not_placed']} transactions of this wallet move outcome tokens, are not listed by the API "
        "and could not be placed in a market: the markets of those tokens are incomplete"
        if exact and built["chain"] and built["chain"]["chain_only_transactions_not_placed"] else None,
        "this wallet converted neg-risk shares: without exact amounts the markets of those events are not valued and shares received "
        "by conversion do not appear" if converted and not exact else None,
        f"{len(open_markets) - valuation_cap} markets with inventory were not priced"
        if as_of is None and valuation_cap is not None and len(open_markets) > valuation_cap else None,
        "an open position is valued at a mark, which is not a price at which its size could be sold") if limit]
    return built


def wallet_funding(sources, wallet, full_history=False, owners_reader=chain.safe_owners, kind_reader=chain.account_kind):
    """Deposits, withdrawals, classified counterparties, relayed amounts and owner keys of a wallet."""
    read = sources.activity(wallet, max_rows=200_000)
    profile = sources.profile(wallet)
    stamps = [r["timestamp"] for r in read["rows"]]
    first_block = 0
    if not full_history and stamps:
        first_block, _ = block_floor(sources, min(stamps) - 180 * 86400)  # a deposit can precede the first trade by months
    flows = funding.cash_flows(sources, wallet, {r["transaction_hash"] for r in read["rows"] if r.get("transaction_hash")}, first_block,
                               kind_reader=kind_reader)
    flows.update(profile=profile, owner_keys=owners_reader(wallet), relayed=funding.pass_throughs(flows["deposits"], flows["withdrawals"]),
                 first_trade_utc=src.utc(min(stamps)) if stamps else None)
    if flows["first_deposit"] and stamps:
        flows["seconds_from_first_deposit_to_first_trade"] = min(stamps) - flows["first_deposit"]["ts"]
    balance, moved = sum(sources.collateral_balance(wallet).values()), flows.pop("net_collateral_moved_raw")
    # Everything the wallet received minus everything it sent must be what it holds: a gap means a transfer older than the scan.
    flows["collateral_check"] = {"received_minus_sent_since_scan_start": ledger.amount(moved), "balance_now": ledger.amount(balance),
                                 "difference": ledger.amount(balance - moved), "closes": balance == moved}
    flows["limits"] = [limit for limit in (
        None if full_history else f"transfers read from block {first_block}: an older deposit would not appear (ask for the full history)",
        None if read["complete"] else "trading history cut: some trade legs may be listed as deposits or withdrawals",
        "only USDC, USDC.e and pUSD on Polygon are read: money arriving through another chain is seen from its arrival on Polygon",
        "a counterparty of kind 'key' is a plain address with a short history, which is not the same as a known person",
        "the owner keys are absent when the address is not a Safe that answers getOwners()") if limit]
    return flows


def wallet_links(sources, wallets, owners_reader=chain.safe_owners, kind_reader=chain.account_kind):
    """Graded links among the given wallets, and the clusters they form."""
    wallets = sorted({w.lower() for w in wallets})
    if not 2 <= len(wallets) <= 25:
        raise ValueError("give between 2 and 25 wallets")
    transfers, classes, owners, limits = [], {}, {}, []
    for wallet in wallets:
        flows = wallet_funding(sources, wallet, owners_reader=owners_reader, kind_reader=kind_reader)
        transfers += flows["deposits"] + flows["withdrawals"]
        classes.update(flows["counterparties"])
        owners[wallet] = flows["owner_keys"] or []
    for wallet in wallets:  # a wallet of the set paying another one is a plain address to the classifier, not a service
        classes.setdefault(wallet, {"kind": "key"})
    found = cluster.links(wallets, transfers, classes, owners)
    return {"wallets": wallets, "links": found, "clusters": cluster.clusters(wallets, found), "counterparties": classes,
            "graph_mermaid": cluster.mermaid(found),
            "limits": limits + ["the popularity of a shared address is counted inside this set of wallets only: an address that pays many "
                                "other wallets would be a service and is not recognised as one here unless its history is long",
                                "no link found is not evidence of absence: money can pass through an exchange or another chain"]}


def associated_wallets(sources, wallet, per_address=25, owners_reader=chain.safe_owners, kind_reader=chain.account_kind):
    """Other addresses paid by the same personal funder, or paying the same personal destination, as `wallet`."""
    wallet = wallet.lower()
    flows = wallet_funding(sources, wallet, owners_reader=owners_reader, kind_reader=kind_reader)
    candidates, services, head = [], [], sources.head()
    for rows, mine, theirs, relation in ((flows["deposits"], "from", "to", "PAID_BY_THE_SAME_ADDRESS"),
                                         (flows["withdrawals"], "to", "from", "PAYS_THE_SAME_ADDRESS")):
        seen = set()
        for row in sorted(rows, key=lambda r: -r["amount_raw"]):
            via = row[mine]
            if via in seen or row["counterparty_kind"] != "key":
                continue
            seen.add(via)
            window = (max(0, row["block"] - funding.LOOK_BLOCKS), min(head, row["block"] + funding.LOOK_BLOCKS))
            others = sources.transfers(via, "out" if relation.startswith("PAID") else "in", *window)["rows"]
            peers = sorted({r[theirs] for r in others} - {wallet, via})
            if len(peers) + 1 > cluster.MAX_PERSONAL_FANOUT:
                services.append({"address": via, "relation": relation, "addresses_reached": len(peers) + 1,
                                 "note": "too many counterparties to be a personal address: treated as a service, no candidate drawn"})
                continue
            for peer in peers[:per_address]:
                evidence = [r for r in others if r[theirs] == peer][:3]
                candidates.append({"address": peer, "relation": relation, "via": via, "grade": cluster.FINANCIAL,
                                   "evidence": [{"tx": e["tx"], "log_index": e["log_index"], "block": e["block"], "amount": ledger.amount(e["amount_raw"])}
                                                for e in evidence], "own_evidence": {"tx": row["tx"], "log_index": row["log_index"]}})
    return {"wallet": wallet, "owner_keys": flows["owner_keys"], "candidates": candidates, "shared_services_ignored": services,
            "limits": ["a candidate shares a paying or paid address with the wallet within about six weeks: a demonstrated money relation "
                       "through a third address, not a common owner",
                       "wallets linked only through an exchange, a bridge or another chain are not found",
                       "wallets owned by the same key cannot be listed from the chain without an index of all smart wallets"]}


def wallet_overview(sources, wallet, owners_reader=chain.safe_owners, kind_reader=chain.account_kind):
    """A first reading of a wallet: who it says it is, what it traded and with what result, how it was funded."""
    book = wallet_ledger(sources, wallet)
    flows = wallet_funding(sources, wallet, owners_reader=owners_reader, kind_reader=kind_reader)
    by_size = sorted(book["markets"], key=lambda m: -abs(Fraction(m["net"] if m["net"] is not None else m["cash"])))
    kinds = {}
    for deposit in flows["deposits"]:
        kinds[deposit["counterparty_kind"]] = kinds.get(deposit["counterparty_kind"], 0) + deposit["amount_raw"]
    return {"wallet": wallet.lower(), "profile": flows["profile"], "owner_keys": flows["owner_keys"],
            "trading": {**book["totals"], "activity_rows": book["activity_rows"], "history_complete": book["history_complete"],
                        "first_trade_utc": flows["first_trade_utc"], "unknown_row_types": book["unknown_row_types"]},
            "largest_markets": [{k: m[k] for k in ("condition_id", "title", "net", "cash", "status", "flags")} for m in by_size[:10]],
            "funding": {"deposits": len(flows["deposits"]), "withdrawals": len(flows["withdrawals"]), "totals": flows["totals"],
                        "first_deposit": flows["first_deposit"],
                        "seconds_from_first_deposit_to_first_trade": flows.get("seconds_from_first_deposit_to_first_trade"),
                        "deposited_by_counterparty_kind": {k: ledger.amount(v) for k, v in sorted(kinds.items())},
                        "relayed": flows["relayed"]},
            "limits": sorted(set(book["limits"] + flows["limits"])),
            "reading": "These are facts about transactions. They do not show who controls the wallet or what its owner knew."}
