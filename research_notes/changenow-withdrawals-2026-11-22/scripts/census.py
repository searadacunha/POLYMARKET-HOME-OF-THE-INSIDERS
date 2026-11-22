"""Withdrawal census of one ISO week: Polymarket trading wallets whose money reached a ChangeNOW deposit address.

Network collector. It reuses `monitoring/changenow_weekly` unchanged (block-window collector, ChangeNOW register and
deposit-address rules, Polymarket wallet classifier, backward walker) and keeps the withdrawal direction only:

1. On each chain read, every transfer from or to a registered ChangeNOW address (and, on Ethereum, the native lists of
   the active ones), the measured role of each address, the one-time deposit addresses swept into a payout wallet,
   and every outside transfer into those deposit addresses (customer deposits).
2. The customer deposits whose sender can carry Polymarket money are walked back with `trace.explain`: a trading
   wallet itself, Polymarket's collateral ramp, a key that owns a trading wallet, a light address that received
   collateral from a trading wallet in the week or the three days before, and Relay solver payments on every chain.
3. Everything is written to `<raw>/<week>/withdrawals.json`: population counts, starts by category, every walk with
   its hops or its stopping reason, the attributed parts, and the keys that own a wallet without a confirmed walk.

Classification into evidence classes, valuation and every published table are made offline by `build.py`.
Raw rows stay in `--raw`, outside the repository. A refusal by a node raises; it is never read as an empty result.
"""
import argparse
import json
import os
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "monitoring"))
sys.dont_write_bytecode = True

from changenow_weekly import collect, pipeline, prices, registry, trace  # noqa: E402
from changenow_weekly import chainio as io  # noqa: E402
from changenow_weekly import polymarket as pm  # noqa: E402

HEAVY_NONCE = 2000      # a sender that signed more transactions than this is a service or a bot: set aside and counted
# Chains searched for the escrow deposit of a Relay order. Base is left out: its keyless archive node answered
# 403 "Archive requests require a personal token" on 2026-11-22. A Polymarket withdrawal starts on Polygon; a fill
# whose origin was elsewhere stays unresolved on chain and goes to Relay's own record (relay_api.py).
WALK_CHAINS = (137, 1)
# Addresses named in one log filter. Measured on 2026-11-22: tenderly's Polygon gateway served 1,500 topics over 50,000
# blocks in 2.2 s; a refusal halves the list (collect.dependent_stream), so a smaller limit elsewhere costs time only.
collect.DEPENDENT_SIZE.update({137: 1500, 1: 1000, 8453: 1000})
# Latest-state reads (codes, nonces, multicalls) on Polygon, measured on 2026-11-22: publicnode, drpc, quiknode and
# tenderly each serve batches of 10; drpc and quiknode refuse 40, publicnode and tenderly throttle 40 under load.
io.BATCH.update({137: 10})
POLYGON_STATE = ["https://polygon-bor-rpc.publicnode.com", "https://polygon.drpc.org", "https://rpc-mainnet.matic.quiknode.pro",
                 "https://gateway.tenderly.co/public/polygon"]

# Latest-state answers repeat from week to week (exchange wallets, routers, returning customers): one process keeps
# them. A code or a nonce read minutes earlier in the same run is the value at that time; both stay latest-state reads.
_codes, _nonces = {}, {}
_get_codes, _get_nonces = io.get_codes, pipeline.nonces


def cached_codes(chain, addresses, size=None):
    missing = sorted({a for a in addresses if (chain, a) not in _codes})
    if missing:
        for a, c in _get_codes(chain, missing, size).items():
            _codes[(chain, a)] = c
    return {a: _codes[(chain, a)] for a in addresses}


def cached_nonces(chain, addresses):
    missing = sorted({a for a in addresses if (chain, a) not in _nonces})
    if missing:
        for a, n in _get_nonces(chain, missing).items():
            _nonces[(chain, a)] = n
    return {a: _nonces[(chain, a)] for a in addresses}


io.get_codes, pipeline.nonces = cached_codes, cached_nonces
VERSION = "census-1"
# Relay solvers beyond the one labelled in investigations/polysentinel: 0xada5bb90... is listed in Relay's own chain
# registry (api.relay.link/chains, solverAddresses), as archived in
# investigations/ballon-dor-flow-trace/sources/data/service_attributions.csv.
EXTRA_SOLVERS = {"0xada5bb90d0de0bd1b6f3938708f49295a8d1f7cb"}


def tag(chains):
    return "+".join(str(c) for c in sorted(chains))


def output(raw, week, chains):
    """One census file per week and chain set: a Polygon lane and an Ethereum lane never write the same file."""
    return Path(raw) / week / f"withdrawals-{tag(chains)}.json"


def done(raw, week, chains):
    """A week is done for these chains when its file exists and every chain read was past the end of the week."""
    path = output(raw, week, chains)
    if not path.exists():
        return False
    return all(b.get("closed") for b in json.loads(path.read_text())["blocks"].values())


def say(message):
    print(time.strftime("%H:%M:%S"), message, flush=True)


def load_key(env_file):
    """Put ETHERSCAN_API_KEY in the environment from one line of an env file. The value is never printed."""
    if os.environ.get("ETHERSCAN_API_KEY") or not env_file:
        return bool(os.environ.get("ETHERSCAN_API_KEY"))
    for line in Path(env_file).expanduser().read_text().splitlines():
        name, _, value = line.partition("=")
        if name.strip() == "ETHERSCAN_API_KEY" and value.strip():
            os.environ["ETHERSCAN_API_KEY"] = value.strip().strip("'\"")
            return True
    return False


def ref(row):
    return dict(chain=row["chain"], tx=row["tx"], log_index=row["log_index"], block=row["block"], block_hash=row.get("block_hash", ""), ts=row.get("ts"),
                src=row["src"], dst=row["dst"], token=row["token"], raw=str(row["raw"]))


def order(row):
    """Walk order across chains: time first, so that the first-in first-out accounting follows the money."""
    return (row.get("ts") or 0, row["chain"], row["block"], row["log_index"] if row["log_index"] >= 0 else 10 ** 9)


def relay_routers():
    return {a for a, v in pm.ff_flows.LABELS.items() if v["name"].startswith("Relay") and "outer" in v["name"]}


def batch(chain, calls):
    """One JSON-RPC batch on the chain's archive endpoints. Raises when no endpoint serves the whole batch."""
    for url in io.CHAINS[chain]["rpc"] + io.CHAINS[chain]["state"]:
        io._pace()
        try:
            body = pm.net.get_json(url, data=[dict(jsonrpc="2.0", id=i, method=m, params=p) for i, (m, p) in enumerate(calls)])
        except pm.net.SourceError:
            continue
        if isinstance(body, list) and len(body) == len(calls) and all("result" in x for x in body):
            return [x["result"] for x in sorted(body, key=lambda x: x["id"])]
    raise pm.net.SourceError(f"chain {chain}: no endpoint served a batch of {len(calls)} calls")


def signed(chain, blocks, addresses):
    """Transactions signed by each registered address inside the week, from its nonce before and at the end.
    Same result as `collect.activity`, read twenty addresses a call instead of one."""
    out = {}
    for part in io.chunks(sorted(addresses), 5):                 # ten calls: the archive endpoints refuse larger batches
        calls = [("eth_getTransactionCount", [a, hex(b)]) for a in part for b in (blocks["first"] - 1, blocks["last"])]
        try:
            got = batch(chain, calls)
        except pm.net.SourceError:
            got = [io.rpc(chain, m, p) for m, p in calls]          # one by one, still raising on failure
        for i, a in enumerate(part):
            before, after = int(got[2 * i], 16), int(got[2 * i + 1], 16)
            if after:
                out[a] = dict(before=before, after=after, sent=after - before)
    return out


def week_blocks(store, chain, week):
    """Block range of the week, read once: a closed week's range is kept on disk and never searched again."""
    kept = store.meta("blocks")
    if kept and kept.get("closed") and kept.get("week") == week:
        return kept
    blocks = dict(io.week_blocks(chain, week), week=week)
    if blocks["closed"]:
        store.meta("blocks", blocks)
    return blocks


def compact_snd(store, span, shaped, owner_of, snd):
    """Keep on disk only the collateral inflows of light senders that the census uses as evidence: those paid by
    Polymarket's collateral ramp or by an address with a trading wallet's bytecode, and a wallet paying its own key.
    Exchanges and routers can pay one light key tens of thousands of times a week; those rows are counted in `snd`
    (the full read), then dropped, because no walk or class reads them (walks read their own inflows by address)."""
    kept = [r for r in store.rows("snd_in") if r["raw"] > 0 and (trace.is_ramp(r["src"]) or r["src"] in shaped or owner_of.get(r["src"]) == r["dst"])]
    snd["rows_read"] = snd.get("rows")
    snd["rows_kept_as_evidence"] = len(kept)
    store.drop("snd_in")
    store.write("snd_in", span["first"], span["last"], kept)


_traders = {}


def eoa_traders(addresses):
    """Addresses that Polymarket's public activity feed lists as their own trading account (a TRADE row whose
    proxy_wallet is the address). One call each, kept for the whole run; a refused call raises."""
    for a in addresses:
        if a in _traders:
            continue
        body = pm.net.get_json(f"{pm.DATA_API}?user={a}&limit=1&type=TRADE")
        rows = body.get("data") if isinstance(body, dict) else None
        if rows is None:
            raise pm.net.SourceError(f"activity of {a}: unexpected answer")
        _traders[a] = bool(rows) and (rows[0].get("proxy_wallet") or "").lower() == a
        time.sleep(0.12)
    return {a for a in addresses if _traders.get(a)}


def eoa_wallet(address):
    return dict(type="EOA_TRADING_ACCOUNT", owners=[address], polymarket_factory=None,
                evidence="Polymarket's public activity feed (data-api v2) lists trades of this key as its own trading account; it has no wallet contract")


def solver_native_fills(chain, blocks, solvers, deposits):
    """Native coin sent by a Relay solver straight to a deposit address of the week, from Etherscan lists of the
    solver (its fills leave no log on Ethereum). One day of 0xf70da978 on 2026-11-09: 2,690 transactions, 514 native fills."""
    out, seen = [], set()
    for solver in sorted(solvers):
        for action, index in (("txlist", -1), ("txlistinternal", -2)):
            for r in io.etherscan_rows(chain, action, solver, blocks["first"], blocks["last"]):
                dst = (r.get("to") or "").lower()
                if r.get("isError", "0") != "0" or int(r["value"] or 0) == 0 or r["from"].lower() != solver or dst not in deposits:
                    continue
                row = dict(chain=chain, block=int(r["blockNumber"]), block_hash=r.get("blockHash", ""), tx=r["hash"].lower(), log_index=index,
                           trace=r.get("traceId", ""), ts=int(r["timeStamp"]), token="native", src=solver, dst=dst, raw=int(r["value"]))
                k = (row["tx"], row["log_index"], row["trace"], row["dst"])
                if k not in seen:
                    seen.add(k)
                    out.append(row)
    return sorted(out, key=lambda r: (r["block"], r["tx"], r["log_index"], r["trace"]))


def read_chain(raw, week, chain, reg):
    """Stage 1 of `analyse.read_chain` without its address-by-address nonce reads: the registry streams on every
    chain, and on Ethereum the native lists of the registered addresses that signed a transaction in the week."""
    store = collect.Store(raw, week, chain)
    blocks = week_blocks(store, chain, week)
    addresses = [a for a, r in reg.items() if r["tier"] != "X_NOT_SERVICE"]
    stats = collect.registry_streams(store, chain, blocks, addresses, say=say)
    stats["native"] = None
    if chain != 137:
        if io.CHAINS[chain]["etherscan_free"] and io.etherscan_key():
            active = signed(chain, blocks, addresses)
            store.meta("activity", dict(first=blocks["first"], last=blocks["last"], nonces=active))
            stats["native"] = collect.native_lists(store, chain, blocks, {a: v["sent"] for a, v in active.items() if v["sent"]}, say=say)
        else:
            say(f"  {io.CHAINS[chain]['name']}: native transfers not read (no free list for this chain, or no key)")
    store.meta("blocks", blocks)
    store.meta("stage1", stats)
    return blocks, stats


def census(raw, week, chains, solvers, say=say):
    reg = registry.load()
    pm.net.COUNTS.clear()                                     # request counts are per week, not per process
    week_prices = Path(raw) / week / f"prices-{tag(chains)}.json"   # one price file per week and chain set: lanes run in parallel
    week_prices.parent.mkdir(parents=True, exist_ok=True)
    if not week_prices.exists() and (Path(raw) / "prices.json").exists():
        week_prices.write_text((Path(raw) / "prices.json").read_text())
    book = prices.Book(week_prices)
    blocks, stage1, pops, deps, depstats, stores = {}, {}, {}, {}, {}, {}
    for chain in chains:
        stores[chain] = collect.Store(raw, week, chain)
        say(f"{week} {io.CHAINS[chain]['name']}: reading")
        blocks[chain], stage1[chain] = read_chain(raw, week, chain, reg)
        pops[chain] = pipeline.population(chain, stores[chain], reg, book, say)
        deps[chain], depstats[chain] = pipeline.customer_deposits(chain, stores[chain], pops[chain], reg, blocks[chain], book, say)
        if chain != 137 and io.CHAINS[chain]["etherscan_free"] and io.etherscan_key() and "native" in pops[chain]["tokens"]:
            extra = solver_native_fills(chain, blocks[chain], solvers, pops[chain]["deposits"])
            have = {(d["tx"], d["log_index"], d["dst"]) for d in deps[chain]}
            extra = [d for d in extra if (d["tx"], d["log_index"], d["dst"]) not in have]
            deps[chain] += extra
            depstats[chain]["solver_native_fills"] = len(extra)
            say(f"  {io.CHAINS[chain]['name']}: {len(extra)} native fills by a Relay solver into deposit addresses")
    book.save()

    walk_blocks = {c: b for c, b in blocks.items() if c in WALK_CHAINS}
    for c in WALK_CHAINS:                                 # Relay origins are searched on these chains even when their own census runs apart
        if c not in walk_blocks:
            walk_blocks[c] = week_blocks(collect.Store(raw, week, c), c, week)
    ctx = trace.Context(walk_blocks, {c: set(pops[c]["sources"]) for c in chains}, [], service=set(reg))
    poly = deps.get(137, [])
    senders = {d["src"] for d in poly}
    wallets_self, _ = pm.trading_wallets(senders, say)
    for a, c in wallets_self.items():
        ctx.wallets[a] = c
    rest = sorted(senders - set(wallets_self))
    owned = pm.owned_wallets(rest, say)

    # Light senders: plain or delegated keys that are not services. Their collateral inflows over the week and the
    # lookback show which of them were fed by a trading wallet. Heavy senders are counted and not read: any walk
    # through them would stop on mixed funds.
    routers = relay_routers()
    plain = [a for a in rest if not trace.is_ramp(a) and a not in solvers and a not in routers and a not in reg and not pm.ff_flows.label_of(a)]
    codes = io.get_codes(137, plain)
    keys = [a for a in plain if codes[a] in ("0x", "0x0") or codes[a].lower().startswith(pipeline.EIP7702)]
    count = pipeline.nonces(137, keys) if keys else {}
    light = sorted(a for a in keys if count[a] <= HEAVY_NONCE)
    heavy = sorted(a for a in keys if count[a] > HEAVY_NONCE)
    span = dict(walk_blocks[137], first=max(1, walk_blocks[137]["first"] - trace.look(137)))
    snd = collect.dependent_stream(stores[137], 137, "snd_in", span, light, "dst", tokens=[pm.USDC_E, pm.USDC, pm.PUSD], say=say) if light else dict(rows=0, addresses=0, heavy=[])
    payers, wallet_paid_key = defaultdict(set), defaultdict(list)
    owner_of = {w["wallet"]: o for o, ws in owned.items() for w in ws}
    for r in (stores[137].rows("snd_in") if light else []):
        if r["raw"] > 0:
            payers[r["dst"]].add(r["src"])
            if owner_of.get(r["src"]) == r["dst"]:
                wallet_paid_key[(r["src"], r["dst"])].append(r["ts"])
    # A sender is fed when one of its payers is Polymarket's collateral ramp or has the bytecode of a trading wallet.
    # The shape is enough to choose where a walk starts; the walk itself classifies every wallet it relies on in full.
    every = sorted({p for a in light for p in payers.get(a, ()) if p != io.ZERO})
    ctx.preload_codes(every)
    shaped = {p for p in every if ctx.codes[(137, p)][2:].startswith(trace.WALLET_SHAPES) and p not in pm.ff_flows.LABELS}
    fed_payers = {a: sorted(p for p in payers.get(a, ()) if p != io.ZERO and (trace.is_ramp(p) or p in shaped)) for a in light}
    fed_payers = {a: v for a, v in fed_payers.items() if v}
    fed = set(fed_payers)
    if light:
        compact_snd(stores[137], span, shaped, owner_of, snd)

    # Accounts that trade from the key itself, with no wallet contract: the walker only knows contract wallets, so
    # Polymarket's public activity feed is asked whether each light sender of collateral is its own trading account.
    eoa = eoa_traders(sorted({d["src"] for d in poly if d["src"] in set(keys) and d["token"] in pm.COLLATERAL}))
    for a in eoa:
        ctx.wallets[a] = eoa_wallet(a)

    starts = {}

    def add(category, d):
        starts.setdefault(trace.key(d), (category, d))

    for d in poly:
        if d["src"] in wallets_self or d["src"] in eoa:
            add("WALLET", d)
        elif trace.is_ramp(d["src"]) and d["src"] != io.ZERO:
            add("COLLATERAL_RAMP", d)
        elif d["src"] in owned and d["token"] in pm.COLLATERAL:
            add("OWNER_KEY", d)
        elif d["src"] in fed and d["token"] in pm.COLLATERAL:
            add("FED_BY_WALLET", d)
    for c in chains:
        for d in deps[c]:
            if d["src"] in solvers:
                add("RELAY_SOLVER", d)
            elif d["src"] in routers:
                add("RELAY_ROUTER", d)
    say(f"withdrawals: {len(starts)} deposits to walk: {dict(Counter(c for c, _ in starts.values()))}")

    walks, parts = [], []

    def walk_all(todo):
        for _, (category, d) in sorted(todo.items(), key=lambda kv: order(kv[1][1])):
            result = trace.explain(ctx, trace.WITHDRAWAL, d)
            walks.append(dict(category=category, status=result["status"], start=ref(d), hops=result["hops"], detail=result["detail"]))
            if result["status"] == "CONFIRMED":
                trace.commit(ctx, result)
                for origin, raw_origin, raw_start in result["parts"]:
                    parts.append(dict(start=ref(d), origin=ref(origin), origin_raw=str(raw_origin), start_raw=str(raw_start), account=origin["src"]))

    walk_all(starts)
    # Second pass: a Relay order whose depositor on Polygon is an account trading from its key stopped there in the
    # first pass. Those depositors are asked once; their walks are read again with the accounts known.
    depositors = {h["src"] for w in walks if w["status"] != "CONFIRMED" for h in w["hops"] if h["kind"] == "RELAY_ORDER" and h["chain"] == 137}
    more = eoa_traders(sorted(a for a in depositors - set(eoa) if not ctx.wallets.get(a)))
    if more:
        for a in more:
            ctx.wallets[a] = eoa_wallet(a)
        again = {trace.key(dict(w["start"], raw=int(w["start"]["raw"]))): w for w in walks
                 if w["status"] != "CONFIRMED" and any(h["kind"] == "RELAY_ORDER" and h["src"] in more for h in w["hops"])}
        walks[:] = [w for w in walks if trace.key(dict(w["start"], raw=int(w["start"]["raw"]))) not in again]
        redo = {}
        for k, w in again.items():
            d = dict(w["start"], raw=int(w["start"]["raw"]))
            redo[k] = (w["category"], d)
        walk_all(redo)
        eoa |= more
    say(f"  accounts trading from their key: {len(eoa)} ({len(more)} found as Relay depositors)")

    def value(chain, token, raw_amount, ts):
        """USD at the ChangeNOW-side transfer, from the token's own price nearest in time (refused beyond one hour)."""
        info = pops[chain]["tokens"].get(token)
        if not info:
            return dict(error="token not recognised")
        try:
            price, price_ts = book.at(chain, token, ts)
        except pm.net.SourceError as exc:
            return dict(error=str(exc)[:160])
        symbol = pm.COLLATERAL[token][0] if chain == 137 and token in pm.COLLATERAL else info["symbol"]
        amount = raw_amount / 10 ** info["decimals"]
        return dict(symbol=symbol, decimals=info["decimals"], amount=amount, price_usd=price, price_ts=price_ts, usd=round(amount * price, 2))

    wallets = {}
    for p in parts:
        c = ctx.wallet(p["account"])
        wallets[p["account"]] = dict(type=c["type"], owners=c.get("owners"), evidence=c.get("evidence"))
        p["value"] = value(p["start"]["chain"], p["start"]["token"], int(p["start_raw"]), p["start"]["ts"])
    candidates = []
    for o, ws in sorted(owned.items()):
        rows = [ref(d) for d in poly if d["src"] == o]
        for r in rows:
            r["value"] = value(r["chain"], r["token"], int(r["raw"]), r["ts"])
        candidates.append(dict(owner=o, wallets=ws, deposits=rows, wallet_paid_key=sorted({ts for w in ws for ts in wallet_paid_key.get((w["wallet"], o), [])})))
    start, end = io.week_bounds(week)
    totals = {}
    for c in chains:                                     # size of the population the accounts are drawn from, one price an hour
        counts = Counter(d["token"] for d in deps[c])
        hourly = book.hourly(c, sorted(t for t, n in counts.items() if n >= 20), start, end)
        usd, unvalued = 0.0, 0
        for d in deps[c]:
            price = hourly.get(d["token"], {}).get(d["ts"] - d["ts"] % 3600) if d.get("ts") else None
            if price is None:
                unvalued += 1
            else:
                usd += d["raw"] / 10 ** pops[c]["tokens"][d["token"]]["decimals"] * price
        totals[str(c)] = dict(customer_deposits=len(deps[c]), senders=len({d["src"] for d in deps[c]}), deposit_addresses=len(pops[c]["deposits"]),
                              usd_hourly_prices=round(usd, 2), unvalued_transfers=unvalued)
    book.save()
    # Evidence that ties each walked deposit address to the service: the sweep into a payout wallet that follows the
    # deposit, the gas the service paid it, and which of the two deposit-address rules it met.
    endpoints = {}
    for w in walks:
        c, d = w["start"]["chain"], w["start"]["dst"]
        if (c, d) in endpoints:
            continue
        pop = pops[c]
        rows = sorted((r for r in pop["good"] if r["src"] == d and r["dst"] in pop["sources"]), key=trace.position)
        later = [r for r in rows if trace.position(r) > (w["start"]["block"], w["start"]["log_index"])]
        gas = sorted((r for r in pop["good"] if r["dst"] == d and r["src"] in pop["funders"] and r["token"] == "native"), key=trace.position)
        endpoints[(c, d)] = dict(chain=c, address=d, rule="GAS_FUNDED" if d in pop["token_deposits"] else "SINGLE_USE_KEY" if d in pop["native_deposits"] else "NONE",
                                 sinks=pop["swept"].get(d, []), sweep=ref(later[0]) if later else (ref(rows[-1]) if rows else None),
                                 sweeps=len(rows), gas=ref(gas[0]) if gas else None)
    tokens = {str(c): {t: v for t, v in pops[c]["tokens"].items()} for c in chains}
    out = dict(version=VERSION, week=week, generated_ts=int(time.time()), chains=list(chains), solvers=sorted(solvers), routers=sorted(routers),
               blocks={str(c): blocks[c] for c in chains}, stage1={str(c): stage1[c] for c in chains},
               population={str(c): dict(stats=pops[c]["stats"], sources=pops[c]["sources"], funders=pops[c]["funders"],
                                        roles={a: v for a, v in pops[c]["roles"].items() if a in pops[c]["sources"] or a in pops[c]["funders"]},
                                        deposits=depstats[c]) for c in chains},
               deposit_rows={str(c): len(deps[c]) for c in chains},
               deposit_senders={str(c): len({d["src"] for d in deps[c]}) for c in chains},
               endpoints=sorted(endpoints.values(), key=lambda e: (e["chain"], e["address"])),
               linking=dict(polygon_senders=len(senders), trading_wallets=len(wallets_self), keys_owning_a_wallet=len(owned), light_keys=len(light), heavy_keys=len(heavy),
                            heavy_examples=heavy[:50], fed_by_wallet=len(fed), snd_in=snd),
               fed_payers={a: v for a, v in fed_payers.items() if any(s["start"]["src"] == a for s in walks)},
               eoa_traders=sorted(eoa),
               tokens=tokens, walks=walks, parts=parts, wallets=wallets, candidates=candidates, totals=totals,
               requests=dict(pm.net.COUNTS))
    path = output(raw, week, chains)
    tmp = path.with_suffix(f".{os.getpid()}.tmp")
    tmp.write_text(json.dumps(out, indent=1))
    os.replace(tmp, path)
    status = Counter(f"{w['category']}:{w['status']}" for w in walks)
    say(f"{week}: {len(parts)} attributed parts from {len(walks)} walks, {len({p['account'] for p in parts})} wallets; {dict(status)}")
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--raw", required=True, help="folder outside the repository for raw rows and checkpoints")
    p.add_argument("--week", action="append", required=True, help="ISO week, e.g. 2026-W46; repeat for several")
    p.add_argument("--chains", default="137,1,8453")
    p.add_argument("--env-file", help="file holding ETHERSCAN_API_KEY=..., read for that one variable")
    p.add_argument("--solver", action="append", default=[], help="extra Relay solver address (lower case)")
    p.add_argument("--rotate", type=int, default=0, help="start the Polygon state endpoints at this index, to spread parallel runs")
    args = p.parse_args(argv)
    k = args.rotate % len(POLYGON_STATE)
    io.CHAINS[137]["state"] = POLYGON_STATE[k:] + POLYGON_STATE[:k]
    chains = tuple(int(c) for c in args.chains.split(","))
    if 1 in chains and not load_key(args.env_file):
        p.error("ETHERSCAN_API_KEY is required to read Ethereum (native transfers and solver fills); pass --env-file")
    solvers = set(trace.RELAY_SOLVERS) | EXTRA_SOLVERS | {s.lower() for s in args.solver}
    trace.RELAY_SOLVERS.clear()
    trace.RELAY_SOLVERS.update(solvers)
    for week in args.week:
        if done(args.raw, week, chains):
            say(f"{week}: already done for chains {tag(chains)}, skipped")
            continue
        census(args.raw, week, chains, solvers)
    return 0


if __name__ == "__main__":
    sys.exit(main())
