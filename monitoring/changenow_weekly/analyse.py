"""One week, end to end: read what is new, find the customer-facing flows, link them to Polymarket accounts,
explain each link hop by hop, value it, and write a single analysis file that the report is built from.

Levels follow the mission text. CONFIRMED: every hop is a transaction read from the chain, a bridge hop carries the
protocol's own order id on both sides, and the ChangeNOW end is a registered address used in its measured role.
PROBABLE: the key that received a payout (or paid a deposit address) owns the wallet and money moved between the two
in the same token window, but one material step is missing. HYPOTHETICAL: ownership and timing only.
"""
import hashlib
import json
import os
import time
from collections import Counter, defaultdict
from pathlib import Path

from . import chainio as io
from . import collect, pipeline, prices, registry, trace
from . import polymarket as pm

CHAINS = (137, 1, 8453)                     # chains with a registered service wallet active in the week (see COVERAGE)
PROBED = (42161, 10, 56, 43114)             # chains where the registered addresses are only checked for activity


def say(message):
    print(time.strftime("%H:%M:%S"), message, flush=True)


def read_chain(raw, week, chain, reg, with_native=True):
    """Stage 1 for one chain: settle the block range, extend the registry streams, read nonces and native lists."""
    store = collect.Store(raw, week, chain)
    blocks = dict(io.week_blocks(chain, week), week=week)
    addresses = [a for a, r in reg.items() if r["tier"] != "X_NOT_SERVICE"]
    stats = collect.registry_streams(store, chain, blocks, addresses, say=say)
    act = collect.activity(store, chain, blocks, addresses)
    active = {a: v["sent"] for a, v in act.items() if v["sent"]}
    stats["native"] = None
    if chain != 137:
        if with_native and io.CHAINS[chain]["etherscan_free"] and io.etherscan_key():
            stats["native"] = collect.native_lists(store, chain, blocks, active, say=say)
        else:
            say(f"  {io.CHAINS[chain]['name']}: native transfers not read (no free list for this chain, or no key)")
    store.meta("blocks", blocks)
    store.meta("stage1", stats)
    return blocks, stats, active


def probe_other_chains(week, reg, chains=PROBED):
    """Did any registered address sign a transaction this week on the chains that are not collected? From nonces.
    A chain whose node does not serve the old state is reported with its error, never as silent."""
    addresses = sorted(a for a, r in reg.items() if r["tier"] != "X_NOT_SERVICE")
    out = {}
    for chain in chains:
        try:
            b = io.week_blocks(chain, week)
            sent, ever = {}, 0
            for a in addresses:
                after = int(io.rpc(chain, "eth_getTransactionCount", [a, hex(b["last"])]), 16)
                if after:
                    ever += 1
                    before = int(io.rpc(chain, "eth_getTransactionCount", [a, hex(b["first"] - 1)]), 16)
                    if after > before:
                        sent[a] = after - before
            out[str(chain)] = dict(first=b["first"], last=b["last"], addresses_tested=len(addresses), ever_used=ever, signed_this_week=sent)
        except Exception as exc:                      # the probe is a coverage statement: its failure is reported as such
            out[str(chain)] = dict(error=f"{type(exc).__name__}: {str(exc)[:160]}")
        say(f"  probe {io.CHAINS[chain]['name']}: {out[str(chain)].get('signed_this_week', out[str(chain)].get('error'))}")
    return out


def _event_id(direction, cn_row, pm_row):
    text = "|".join(str(x) for x in (direction, cn_row["chain"], cn_row["tx"], cn_row["log_index"], cn_row.get("trace", ""), pm_row["tx"], pm_row["log_index"]))
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def _ref(row):
    return dict(chain=row["chain"], tx=row["tx"], log_index=row["log_index"], block=row["block"], block_hash=row.get("block_hash", ""), ts=row.get("ts"),
                src=row["src"], dst=row["dst"], token=row["token"], raw=str(row["raw"]))


def analyse(raw, week, chains=CHAINS, read=True):
    reg = registry.load()
    book = prices.Book(Path(raw) / "prices.json")
    start, end = io.week_bounds(week)
    blocks, stage1, pops, deps, depstats, stores, active = {}, {}, {}, {}, {}, {}, {}
    for chain in chains:
        stores[chain] = collect.Store(raw, week, chain)
        if read:
            blocks[chain], stage1[chain], active[chain] = read_chain(raw, week, chain, reg)
        else:
            blocks[chain], stage1[chain] = stores[chain].meta("blocks"), stores[chain].meta("stage1")
            blocks[chain]["week"] = week
            active[chain] = {a: v["sent"] for a, v in stores[chain].meta("activity")["nonces"].items() if v["sent"]}
        pops[chain] = pipeline.population(chain, stores[chain], reg, book, say)
        deps[chain], depstats[chain] = pipeline.customer_deposits(chain, stores[chain], pops[chain], reg, blocks[chain], book, say)
    payouts = [p for c in chains for p in pops[c]["payouts"]]
    ctx = trace.Context(blocks, {c: set(pops[c]["sources"]) for c in chains}, payouts, service=set(reg))
    recipients = {c: {p["dst"] for p in pops[c]["payouts"]} for c in chains}
    senders = {c: {d["src"] for d in deps[c]} for c in chains}
    everyone = set().union(*recipients.values(), *senders.values())

    say(f"linking {len(everyone)} counterparties to Polymarket")
    poly_parties = recipients.get(137, set()) | senders.get(137, set())
    wallets_self, _ = pm.trading_wallets(poly_parties, say)
    for a, c in wallets_self.items():
        ctx.wallets[a] = c
    owned = pm.owned_wallets(everyone - set(wallets_self), say)
    owner_of = {w["wallet"]: o for o, ws in owned.items() for w in ws}

    events, walks, walked = [], [], set()

    def walk(direction, start_row, wallet=None):
        """Explain one transfer once, however many starts reach it: a second walk would only find its origin spent."""
        k = (direction,) + trace.key(start_row)
        if k not in walked:
            walked.add(k)
            record(direction, start_row, trace.explain(ctx, direction, start_row), wallet)

    def record(direction, start_row, result, wallet=None):
        walks.append(dict(direction=direction, status=result["status"], start=_ref(start_row), wallet=wallet, hops=result["hops"], detail=result["detail"]))
        if result["status"] != "CONFIRMED":
            return
        trace.commit(ctx, result)
        for origin, raw_origin, raw_start in result["parts"]:
            cn_row, cn_raw, pm_row, pm_raw = (origin, raw_origin, start_row, raw_start) if direction == trace.FUNDING else (start_row, raw_start, origin, raw_origin)
            account = pm_row["dst"] if direction == trace.FUNDING else pm_row["src"]
            cn_address = cn_row["src"] if direction == trace.FUNDING else cn_row["dst"]
            events.append(dict(event_id=_event_id(direction, cn_row, pm_row), week=week, direction=direction, level="CONFIRMED", account=account,
                               cn=_ref(cn_row), cn_address=cn_address, cn_counterparty=cn_row["dst"] if direction == trace.FUNDING else cn_row["src"],
                               cn_raw=str(cn_raw), pm=_ref(pm_row), pm_raw=str(pm_raw), hops=result["hops"], bound=result["detail"]))

    # ---- funding ---------------------------------------------------------------------------------------------
    for p in pops.get(137, {}).get("payouts", []):                       # F1: a payout straight into a trading wallet
        if p["dst"] in wallets_self:
            walk(trace.FUNDING, p, p["dst"])
    all_recipients = set().union(*recipients.values()) - set(wallets_self)
    out_stats = collect.dependent_stream(stores[137], 137, "rcp_out", blocks[137], all_recipients, "src", tokens=[pm.USDC_E, pm.USDC, pm.PUSD], say=say)
    starts = {}
    ctx.preload_codes({r["dst"] for r in stores[137].rows("rcp_out")})
    for r in stores[137].rows("rcp_out"):                                # F2: a recipient's collateral reaching a wallet
        if r["raw"] <= 0:
            continue
        if trace.is_ramp(r["dst"]):
            for m in pm.ff_flows.transfers(ctx.receipt(137, r["tx"]), 137):
                if m["token"] == pm.PUSD and m["source"] == io.ZERO and m["raw"] == r["raw"] and m["log_index"] > r["log_index"] and ctx.wallet(m["target"]):
                    starts[(m["tx"], m["log_index"])] = dict(chain=137, tx=m["tx"], log_index=m["log_index"], block=m["block"], block_hash=r.get("block_hash", ""), ts=r.get("ts"),
                                                             src=io.ZERO, dst=m["target"], token=pm.PUSD, raw=m["raw"])
        elif ctx.wallet(r["dst"]):
            starts[(r["tx"], r["log_index"])] = r
    owner_wallets = sorted({w["wallet"] for o, ws in owned.items() if o in all_recipients for w in ws})
    in_stats = collect.dependent_stream(stores[137], 137, "own_in", blocks[137], owner_wallets, "dst", tokens=[pm.USDC_E, pm.USDC, pm.PUSD], say=say)
    first_payout = {}
    for p in payouts:
        first_payout[p["dst"]] = min(first_payout.get(p["dst"], p["ts"]), p["ts"])
    skipped_before = 0
    for r in stores[137].rows("own_in"):                                 # F3: outside credits of a recipient-owned wallet, after its key was first paid
        if r["raw"] > 0 and (r["src"] == io.ZERO or not pm.ff_flows.label_of(r["src"])):
            if r["ts"] < first_payout[owner_of[r["dst"]]]:
                skipped_before += 1
                continue
            starts.setdefault((r["tx"], r["log_index"]), r)
    say(f"funding: {len(starts)} wallet credits to explain")
    for _, row in sorted(starts.items(), key=lambda kv: trace.position(kv[1])):
        walk(trace.FUNDING, row, row["dst"])

    # ---- withdrawals -----------------------------------------------------------------------------------------
    poly_senders = senders.get(137, set()) - set(wallets_self)
    snd_stats = collect.dependent_stream(stores[137], 137, "snd_in", blocks[137], poly_senders, "dst", tokens=[pm.USDC_E, pm.USDC, pm.PUSD], say=say)
    payers_of, wallet_paid_key = defaultdict(set), defaultdict(list)
    for r in stores[137].rows("snd_in"):
        if r["raw"] > 0:
            payers_of[r["dst"]].add(r["src"])
            if owner_of.get(r["src"]) == r["dst"]:
                wallet_paid_key[(r["src"], r["dst"])].append(r["ts"])
    fed = fed_senders(ctx, payers_of, {d["src"] for d in deps.get(137, []) if d["token"] in pm.COLLATERAL} - set(wallets_self))
    todo = [d for d in deps.get(137, []) if d["src"] in wallets_self or (d["src"] in fed and d["token"] in pm.COLLATERAL)]
    for c in chains:                                                     # a bridge solver paying a deposit address directly
        todo += [d for d in deps[c] if d["src"] in trace.RELAY_SOLVERS]
    say(f"withdrawals: {len(todo)} deposits into ChangeNOW deposit addresses to explain ({len(fed)} senders fed by a wallet)")
    for d in sorted(todo, key=trace.position):
        walk(trace.WITHDRAWAL, d)

    # ---- value, describe, classify what is not confirmed -------------------------------------------------------
    for e in events:
        chain, token = e["cn"]["chain"], e["cn"]["token"]
        info = pops[chain]["tokens"][token]
        price, price_ts = book.at(chain, token, e["cn"]["ts"])
        amount = int(e["cn_raw"]) / 10 ** info["decimals"]
        cn_address = e["cn_address"]
        swept = pops[chain]["swept"].get(cn_address, []) if e["direction"] == trace.WITHDRAWAL else [cn_address]
        tiers = sorted({reg[a]["tier"] for a in swept})
        symbol = pm.COLLATERAL[token][0] if chain == 137 and token in pm.COLLATERAL else info["symbol"]      # the price source calls both Polygon USDC contracts "USDC"
        e.update(symbol=symbol, decimals=info["decimals"], amount=amount, price_usd=price, price_ts=price_ts, usd=round(amount * price, 2),
                 cn_role="PAYOUT_HOT" if e["direction"] == trace.FUNDING else "DEPOSIT_ADDRESS", cn_attribution=tiers, cn_service_wallets=swept)
    accounts = {}
    horizon = end if all(blocks[c]["closed"] for c in chains) else min(blocks[c]["head_ts"] for c in chains)     # where the chain data stop
    moments = defaultdict(set)                                           # when each confirmed movement touched the wallet itself
    for e in events:
        if e["pm"].get("ts"):
            moments[e["account"]].add((e["direction"], e["pm"]["ts"]))
    for wallet in sorted({e["account"] for e in events}):
        c = ctx.wallet(wallet)
        accounts[wallet] = dict(wallet=wallet, type=c["type"], owners=c["owners"], evidence=c["evidence"], profile=pm.profile(wallet), summary=pm.account_summary(wallet, start, end),
                                around=pm.around(wallet, sorted(moments[wallet]), horizon))
    candidates = unconfirmed(week, pops, deps, owned, events, walks, book, chains, wallet_paid_key)
    totals = population_totals(pops, deps, book, start, end, chains)
    probes = probe_other_chains(week, reg) if read else (json.loads((Path(raw) / week / "probes.json").read_text()) if (Path(raw) / week / "probes.json").exists() else {})
    (Path(raw) / week / "probes.json").write_text(json.dumps(probes, indent=1))
    out = dict(week=week, start=start, end=end, generated_ts=int(time.time()), closed=all(blocks[c]["closed"] for c in chains),
               blocks={str(c): blocks[c] for c in chains}, stage1={str(c): stage1[c] for c in chains}, active={str(c): active[c] for c in chains},
               population={str(c): dict(stats=pops[c]["stats"], sources=pops[c]["sources"], funders=pops[c]["funders"], roles=pops[c]["roles"], deposits=depstats[c],
                                        other_senders=pops[c]["other_senders"][:200]) for c in chains},
               dependent=dict(rcp_out=out_stats, own_in=in_stats, snd_in=snd_stats), linking=dict(counterparties=len(everyone), trading_wallets_among_counterparties=len(wallets_self),
               keys_owning_a_wallet=len(owned), recipients={str(c): len(recipients[c]) for c in chains}, senders={str(c): len(senders[c]) for c in chains}),
               events=events, accounts=accounts, candidates=candidates, totals=totals, other_chains=probes,
               payout_times={str(c): sorted(p["ts"] for p in pops[c]["payouts"]) for c in chains},
               walks=dict(counts=dict(Counter(f"{w['direction']}:{w['status']}" for w in walks)), unresolved=[w for w in walks if w["status"] == "UNRESOLVED"][:400]),
               requests=dict(io_counts=dict(pm.net.COUNTS)))
    path = Path(raw) / week / "analysis.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=1))
    os.replace(tmp, path)
    say(f"analysis written: {len(events)} confirmed events for {len(accounts)} accounts, {len(candidates)} unconfirmed candidates")
    return out


def fed_senders(ctx, payers_of, senders):
    """Senders into ChangeNOW deposit addresses that received collateral during the week from a trading wallet or a
    collateral ramp. One such payer is enough, so payers are classified a batch at a time and the search stops at the
    first: a router paid by fifty thousand addresses is not classified fifty thousand times."""
    fed = set()
    for target in sorted(set(senders) & set(payers_of)):
        who = payers_of[target]
        if any(p != io.ZERO and trace.is_ramp(p) for p in who):
            fed.add(target)
            continue
        for part in io.chunks(sorted(who), 40):
            ctx.preload_codes(part)
            if any(ctx.wallet(p) for p in part):
                fed.add(target)
                break
    return fed


def unconfirmed(week, pops, deps, owned, events, walks, book, chains, wallet_paid_key):
    """Accounts linked by key ownership whose flows are not confirmed, with the level each one earns and why.
    PROBABLE needs money read moving between the key and its own wallet on the right side of the ChangeNOW transfer:
    after a payout for funding, before a deposit for a withdrawal. Ownership and timing alone stay HYPOTHETICAL.
    Nothing here enters the confirmed ranking, and the amounts are upper bounds of what could be involved."""
    confirmed = {(e["direction"], e["cn"]["tx"], e["cn"]["log_index"]) for e in events}
    credits = defaultdict(list)                       # wallet -> walks that started from one of its credits
    for w in walks:
        if w["direction"] == trace.FUNDING and w["wallet"]:
            credits[w["wallet"]].append(w)
    out = []
    for direction, rows_by_chain in ((trace.FUNDING, {c: pops[c]["payouts"] for c in chains}), (trace.WITHDRAWAL, deps)):
        side = "dst" if direction == trace.FUNDING else "src"
        per_owner = defaultdict(list)
        for c in chains:
            for r in rows_by_chain[c]:
                if r[side] in owned and (direction, r["tx"], r["log_index"]) not in confirmed:
                    per_owner[r[side]].append(r)
        for owner, rows in per_owner.items():
            usd, unpriced = 0.0, 0
            for r in rows:
                try:
                    usd += r["raw"] / 10 ** pops[r["chain"]]["tokens"][r["token"]]["decimals"] * book.at(r["chain"], r["token"], r["ts"])[0]
                except Exception:
                    unpriced += 1
            first_ts, last_ts = min(r["ts"] for r in rows), max(r["ts"] for r in rows)
            for w in owned[owner]:
                if direction == trace.FUNDING:
                    through = [x for x in credits.get(w["wallet"], []) if x["start"]["ts"] >= first_ts and any(h["src"] == owner for h in x["hops"])]
                    moved, reasons = bool(through), sorted({x["detail"].get("reason", "") for x in through if x["status"] != "CONFIRMED"})
                else:
                    moved = any(ts <= last_ts for ts in wallet_paid_key.get((w["wallet"], owner), []))
                    reasons = sorted({x["detail"].get("reason", "") for x in walks if x["direction"] == trace.WITHDRAWAL and x["start"]["src"] == owner and x["status"] != "CONFIRMED"})
                out.append(dict(week=week, direction=direction, level="PROBABLE" if moved else "HYPOTHETICAL", account=w["wallet"], wallet_kind=w["kind"], owner=owner,
                                ownership_proof=w["proof"], changenow_transfers=len(rows), usd_upper_bound=round(usd, 2), unpriced_transfers=unpriced,
                                chains=sorted({r["chain"] for r in rows}), first_ts=first_ts, last_ts=last_ts,
                                transfers=[dict(chain=r["chain"], tx=r["tx"], log_index=r["log_index"], ts=r["ts"], token=r["token"], raw=str(r["raw"]),
                                                counterparty=r["src" if side == "dst" else "dst"]) for r in rows[:50]],
                                missing=[x for x in reasons if x][:4] or (["money moved between this key and its wallet, but no transfer could be tied to the ChangeNOW one amount by amount"] if moved
                                                                          else ["no transfer between this key and its wallet was read on the relevant side of the ChangeNOW transfer"])))
    return sorted(out, key=lambda c: -c["usd_upper_bound"])


def population_totals(pops, deps, book, start, end, chains):
    """Size of the whole ChangeNOW population the accounts are drawn from, valued with one price an hour."""
    out = {}
    for c in chains:
        tokens = pops[c]["tokens"]
        for name, rows, side in (("payouts", pops[c]["payouts"], "dst"), ("customer_deposits", deps[c], "src")):
            counts = Counter(r["token"] for r in rows)
            hourly = book.hourly(c, sorted(t for t, n in counts.items() if n >= 20), start, end)       # rarer tokens stay unvalued and counted
            usd, unvalued, per_token = 0.0, 0, Counter()
            for r in rows:
                price = hourly.get(r["token"], {}).get(r["ts"] - r["ts"] % 3600) if r.get("ts") else None
                if price is None:
                    unvalued += 1
                    continue
                value = r["raw"] / 10 ** tokens[r["token"]]["decimals"] * price
                usd += value
                per_token[tokens[r["token"]]["symbol"]] += value
            out[f"{c}:{name}"] = dict(transfers=len(rows), addresses=len({r[side] for r in rows}), usd=round(usd, 2), unvalued_transfers=unvalued,
                                      by_token={k: round(v, 2) for k, v in per_token.most_common(8)})
    return out
