"""Offline weekly funding ledger. Observed zero, unknown and unpriced have different representations."""

import argparse
import csv
import io
import json
from bisect import bisect_right
from collections import Counter, defaultdict
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from .accounts import PRIOR_PNL, TRADERS, TRADES, registry
from .archive import (
    LABELS,
    NATIVE_SOURCES,
    STATE,
    historic_cohort,
    infrastructure,
    native_archive,
    native_coverage,
)
from .common import (
    ETH_TOKENS,
    HOME,
    LEVELS,
    REPO,
    SERVICES,
    SNAP,
    STREAMS,
    TOKENS,
    UTC,
    atomic,
    bounds,
    digest,
    read,
    week_of,
    weeks,
)
from .events import Credit, load_stream
from .routes import guaranteed
from .statistics import analyze
from .token_routes import RELAY, amount_onward

PROVEN = set(LEVELS[:2])
CENT = Decimal(".01")
D = Decimal


def money(v):
    return str(v.quantize(CENT))


def iso(ts):
    return datetime.fromtimestamp(ts, UTC).isoformat().replace("+00:00", "Z")


def json_text(v):
    return json.dumps(v, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


class Quotes:
    def __init__(self, pack):
        self.series = {}
        for asset, identifier in pack["ids"].items():
            series = pack["series"].get(identifier, {})
            quotes = sorted(
                (p["timestamp"], D(str(p["price"])))
                for p in series.get("prices", [])
                if D(str(p["price"])).is_finite() and D(str(p["price"])) > 0
            )
            if float(series.get("confidence", 0)) >= 0.9 and quotes:
                self.series[asset] = ([q[0] for q in quotes], quotes)

    def quote(self, e):
        if f"{e.chain}:{e.asset}" in self.series:
            times, quotes = self.series[f"{e.chain}:{e.asset}"]
            i = bisect_right(times, e.ts) - 1
            if i >= 0 and e.ts - times[i] <= 36 * 3600:
                return quotes[i]
        return None, None


def post(profile, ts):
    first = profile.get("first_trade")
    buys = sorted({tuple(r) for r in profile.get("buys", []) if r[0] > ts})
    covered = next((r for r in profile.get("intervals", []) if r[0] <= ts + 1 <= r[1]), None)
    candidate = next((r for r in buys if covered and r[0] <= covered[1]), None)
    after = profile.get("first_after", {}).get(str(ts))
    if buys or after or first and first[0] > ts:
        traded = "YES"
    elif str(ts) in profile.get("first_after", {}) and after is None:
        traded = "NO_IN_OBSERVED_WINDOW"
    else:
        traded = "UNKNOWN"
    return traded, candidate, buys


def info(
    e, level, account, root, reason, profile, source_ref, known, quote, price_time, path, previous=None
):
    traded, buy, buys = post(profile, e.ts)
    token = "POL" if e.chain == 137 else "ETH"
    if e.asset != "native":
        token = (TOKENS if e.chain == 137 else ETH_TOKENS)[e.asset][0]
    pnl = profile.get("pnl") or {}
    prior = profile.get("first_trade") or []
    markets = defaultdict(Decimal)
    for r in buys:
        markets[r[3]] += D(r[5])
    return dict(
        week=week_of(e.ts),
        service=SERVICES[root.stream],
        evidence=level,
        wallet=account,
        wallet_chain=137,
        chain=e.chain,
        receipt_recipient=e.recipient,
        source_address=root.sender,
        source_role=root.role,
        source_confidence={
            "commingled_route": "POSSIBLE",
            "consolidation": "LABELLED_CONSOLIDATION",
            "withdrawal_pool": "OFFICIAL_POOL",
            "labelled_hot_wallet": "SUPPORTED_PUBLIC_LABEL",
        }[root.role],
        token=token,
        token_contract=e.asset,
        amount=str(e.amount),
        usd_known=money(e.amount * quote) if quote is not None else "UNKNOWN",
        verified_funding_usd=(money(e.amount * quote) if quote is not None else "UNKNOWN")
        if level in PROVEN
        else "UNVERIFIED",
        usd_price=str(quote) if quote is not None else "UNKNOWN",
        price_time=iso(price_time) if price_time is not None else "UNKNOWN",
        funding_time=iso(e.ts),
        block=e.block,
        tx=e.tx,
        log_index="native:root" if e.idx == -1 else e.idx,
        path=json_text(path),
        intermediaries=len(path) - 1
        if reason in ("exact_trading_address", "verified_forward")
        else "UNKNOWN",
        relationship=reason,
        pm_evidence=known,
        source_evidence=source_ref,
        traded_after=traded,
        first_buy_status="OBSERVED"
        if buy
        else (
            "NO_IN_OBSERVED_WINDOW"
            if any(
                lo <= e.ts + 1 <= hi and exhausted for lo, hi, exhausted in profile.get("intervals", [])
            )
            else "UNKNOWN"
        ),
        first_buy_time=iso(buy[0]) if buy else "UNKNOWN",
        first_buy_tx=buy[1] if buy else "UNKNOWN",
        first_buy_market=buy[3] if buy else "UNKNOWN",
        first_buy_title=buy[6] if buy else "UNKNOWN",
        first_buy_usd=buy[5] if buy else "UNKNOWN",
        subsequent_observed_market_buy_usd=json_text({k: str(v) for k, v in sorted(markets.items())}),
        activity_scope="sampled ascending pages; distinct observable fills; lower bound",
        first_indexed_trade=iso(prior[0]) if prior else "UNKNOWN",
        known_trade_before=("YES" if prior[0] < e.ts else "NO_IN_INDEX") if prior else "UNKNOWN",
        pnl_time=iso(pnl["timestamp"]) if pnl and pnl["timestamp"] >= e.ts else "UNKNOWN",
        economic_pnl_usd=pnl["economic_pnl"] if pnl and pnl["timestamp"] >= e.ts else "UNKNOWN",
        archived_pnl_usd=(previous or {}).get("total_pnl", "UNKNOWN"),
        archived_pnl_incomplete=(previous or {}).get("incomplete", "UNKNOWN"),
    )


def leg(e):
    return {
        "chain": e.chain,
        "tx": e.tx,
        "log": "native:root" if e.idx == -1 else e.idx,
        "block": e.block,
        "from": e.sender,
        "to": e.recipient,
        "asset": e.asset,
        "raw": str(e.units),
        "timestamp": e.ts,
    }


def classify(e, known, owners, excluded):
    if (e.chain, e.recipient) in excluded:
        return "REFUTED", None, excluded[e.chain, e.recipient]
    if e.recipient in known:
        if e.chain != 137:
            return "POSSIBLE", e.recipient, "same_address_on_other_chain"
        if e.role == "commingled_route":
            return "POSSIBLE", e.recipient, "exact_trading_address"
        if e.role == "consolidation":
            return "POSSIBLE", e.recipient, "consolidation_route"
        return "CONFIRMED_DIRECT", e.recipient, "exact_trading_address"
    if e.chain == 137 and e.recipient in owners:
        return "POSSIBLE", owners[e.recipient], "signer_only_no_final_transfer"
    return ("POSSIBLE" if e.role == "commingled_route" else "UNKNOWN"), None, "unassigned_recipient"


class Group:
    def __init__(self):
        self.rec = set()
        self.raw_labeled = set()
        self.raw_mixed = set()
        self.pm = set()
        self.exact = set()
        self.direct = set()
        self.indirect = set()
        self.post = set()
        self.unassigned = set()
        self.tested = set()
        self.unknown_posts = set()
        self.raw = Decimal(0)
        self.raw_missing = 0
        self.by_account = defaultdict(Decimal)
        self.pm_missing = set()
        self.exact_by_wallet = defaultdict(Decimal)
        self.exact_post = set()
        self.exact_usd = D(0)
        self.exact_missing = 0

    def record(self, e, lvl, account, relation, usd, traded, profile_status, final=False):
        pair = (e.chain, e.recipient)
        # Forwarded legs affect the destination totals only. Source gross is counted once.
        if not final:
            self.rec.add(pair)
            if e.role == "commingled_route":
                self.raw_mixed.add(pair)
            else:
                self.raw_labeled.add(pair)
            if usd is None:
                self.raw_missing += 1
            else:
                self.raw += usd
            if e.chain == 137 and profile_status in {"NO_INDEXED_TRADE", "TRADE_OBSERVED"}:
                self.tested.add(pair)
            if not account and lvl != "REFUTED":
                self.unassigned.add(pair)
        if account:
            self.pm.add(account)
            if relation == "exact_trading_address":
                self.exact.add(account)
                if traded == "YES":
                    self.exact_post.add(account)
                if usd is None:
                    self.exact_missing += 1
                else:
                    self.exact_usd += usd
                    self.exact_by_wallet[account] += usd
            if lvl in PROVEN:
                (self.direct if lvl == "CONFIRMED_DIRECT" else self.indirect).add(account)
                if usd is None:
                    self.pm_missing.add(account)
                else:
                    self.by_account[account] += usd
                if traded == "YES":
                    self.post.add(account)
                elif traded == "UNKNOWN":
                    self.unknown_posts.add(account)

    def row(self, week, service, lvl, prior, frame, observed=True):
        funded = self.direct | self.indirect
        usd = sum(self.by_account.values(), D(0))
        out = dict(
            week=week,
            service=service,
            evidence=lvl,
            source_recipients=len(self.rec),
            labelled_or_official_source_recipients=len(self.raw_labeled),
            commingled_route_recipients=len(self.raw_mixed),
            exact_pm_recipients=len(self.exact),
            linked_pm_accounts=len(self.pm),
            exact_pm_traded_after_observed=len(self.exact_post),
            exact_pm_receipts_ge_1000_observed=sum(v >= 1000 for v in self.exact_by_wallet.values()),
            exact_pm_receipts_ge_10000_observed=sum(v >= 10000 for v in self.exact_by_wallet.values()),
            confirmed_direct=len(self.direct),
            supported_indirect=len(self.indirect),
            funded_distinct=len(funded),
            new_in_observed_history=len(funded - prior),
            first_ever="UNKNOWN",
            traded_after_observed=len(self.post),
            post_trade_unknown=len(self.unknown_posts - self.post),
            gross_source_usd="UNKNOWN" if self.raw_missing else money(self.raw),
            priced_source_subtotal_usd=money(self.raw),
            unpriced_source_events=self.raw_missing,
            exact_pm_receipt_usd="UNKNOWN" if self.exact_missing else money(self.exact_usd),
            funding_usd="UNKNOWN" if self.pm_missing else money(usd),
            priced_funding_subtotal_usd=money(usd),
            funded_ge_1000_observed=sum(v >= 1000 for v in self.by_account.values()),
            funded_ge_10000_observed=sum(v >= 10000 for v in self.by_account.values()),
            unpriced_funded_wallets=len(self.pm_missing),
            unassigned_recipient_pairs=len(self.unassigned),
            exact_recipient_api_lookups=len(self.tested),
            covered_active_pm=len(frame),
            funded_in_frame=len(funded & frame),
            rate_in_covered_active_pm=(
                f"{len(funded & frame) / len(frame):.8f}" if frame and observed else "UNKNOWN"
            ),
            platform_denominator="UNKNOWN",
            platform_total="UNKNOWN",
        )
        if not observed:
            for k in out.keys() - {"week", "service", "evidence", "covered_active_pm"}:
                out[k] = "UNKNOWN"
        return out


def forward_index(snap, root_by_key, excluded, known):
    accepted = defaultdict(list)
    bridge_legs = {}
    metrics = {}
    rfile = snap / "routes.json.gz"
    if rfile.exists():
        r = read(rfile)
        tally = Counter()
        for item in r["accounts"].values():
            tally.update(item["tally"])
            for c in item["proofs"]:
                root = root_by_key.get(tuple(c["seed"]))
                if not root:
                    continue
                proof = c["proof"]
                units = guaranteed(root, proof)
                tx = proof["tx"]
                if units and (137, tx["to"]) not in excluded:
                    e = Credit(
                        137,
                        root.stream,
                        int(tx["blockNumber"], 16),
                        int(proof["header"]["timestamp"], 16),
                        tx["hash"],
                        -1,
                        root.recipient,
                        tx["to"],
                        "native",
                        units,
                        "withdrawal_pool",
                    )
                    accepted[e.key].append((root, e, "snapshot/routes.json.gz"))
        metrics["polygon_native"] = {
            "from": r["from_week"],
            "through": r["to_week"],
            "screened_intermediaries": len(r["accounts"]),
            **tally,
        }
    tfile = snap / "token_routes.json.gz"
    if tfile.exists():
        t = read(tfile)
        metrics["signer_to_proxy"] = {
            "weeks": t["weeks"],
            "candidate_forwards": len(t["candidates"]),
            "signer_pairs": len(t["pairs"]),
        }
        metrics["relay"] = {
            "exact_origin_transactions_screened": t["relay_origin_keys"],
            "exact_hits_pending_receipt_replay": t["relay_exact_hits"],
        }
        for c in t["candidates"]:
            root = root_by_key.get(tuple(c["seed"]))
            if not root or "opening" not in c:
                continue
            raw = c["out"]
            units = amount_onward(root, raw, c["ledger"], c["opening"])
            if units and (137, c["proxy"]) not in excluded:
                e = Credit(
                    137,
                    root.stream,
                    int(raw["blockNumber"], 16),
                    c["time"],
                    raw["transactionHash"],
                    int(raw["logIndex"], 16),
                    root.recipient,
                    c["proxy"],
                    root.asset,
                    units,
                    root.role,
                )
                accepted[e.key].append((root, e, "snapshot/token_routes.json.gz"))
    cross = snap / "bridge.json.gz"
    if cross.exists():
        from .bridge import backed

        b = read(cross)
        checks = Counter()
        for item in b["accounts"].values():
            checks[item["status"]] += 1
            checks["orders_in_window"] += len(item["orders"])
            for candidate in item["proofs"]:
                root = root_by_key.get(tuple(candidate["seed"]))
                if not root:
                    continue
                o = candidate["order"]
                log = backed(root, o, candidate["origin"], candidate["destination"])
                other = candidate["second_destination_log"]
                if not log or any(
                    log[k] != other[k]
                    for k in ("address", "topics", "data", "blockHash", "logIndex", "transactionHash")
                ):
                    raise ValueError("bridge funding proof mismatch")
                if (137, o["recipient"]) in excluded or candidate["destination_time"] < root.ts:
                    continue
                e = Credit(
                    137,
                    root.stream,
                    int(log["blockNumber"], 16),
                    candidate["destination_time"],
                    log["transactionHash"],
                    int(log["logIndex"], 16),
                    "0x" + log["topics"][1][-40:],
                    o["recipient"],
                    o["out_token"],
                    o["out_units"],
                    root.role,
                )
                known.setdefault(e.recipient, "snapshot/bridge.json.gz#" + candidate["pm_fill"][1])
                accepted[e.key].append((root, e, "snapshot/bridge.json.gz"))
                bridge_legs[e.key] = dict(
                    chain=1,
                    tx=o["in_tx"],
                    order=o["id"],
                    asset="native",
                    raw=str(o["in_units"]),
                    sender=root.recipient,
                    recipient=o["in_to"],
                    method="Relay",
                )
                checks["backed_routes"] += 1
        metrics["ethereum_to_polygon"] = {"accounts_screened": len(b["accounts"]), **checks}
    # Competing paths to one economic terminal are never added together.
    metrics["ambiguous_terminal_events"] = sum(len(v) > 1 for v in accepted.values())
    forwards = defaultdict(list)
    for v in accepted.values():
        if len(v) == 1:
            forwards[week_of(v[0][1].ts)].append(v[0])
    return forwards, metrics, bridge_legs


def write_csv(path, rows, fields):
    buf = io.StringIO(newline="")
    writer = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    atomic(path, buf.getvalue().encode())


def date_set(a):
    return sorted(a)


def build(snap, out, first=None, last=None, previous_report=None, standalone=False):
    from .registry_evidence import check

    check(read(HOME / "pool_registry.json"))
    from .render import render
    from .frame import frame_members

    folders = sorted(p.name for p in snap.glob("????-W??") if p.is_dir())
    if (HOME / "PROTOCOL.lock").read_text().split()[0] != digest(HOME / "PROTOCOL.md"):
        raise ValueError("frozen protocol hash mismatch")
    if not folders:
        raise ValueError("no funding snapshot")
    first, last = first or folders[0], last or folders[-1]
    calendar = list(weeks(min(folders[0], first), last))
    selected = set(weeks(first, last))
    out.mkdir(parents=True, exist_ok=True)
    p = (
        read(snap / "accounts.json.gz")
        if (snap / "accounts.json.gz").exists()
        else {"profiles": {}, "asof_exclusive": None}
    )
    profiles = p["profiles"]
    known, owners = registry(snap)
    for a, r in profiles.items():
        if r["status"] == "TRADE_OBSERVED":
            if a != r["address"] or not r["first_trade"] or r["first_trade"][0] >= r["asof_exclusive"]:
                raise ValueError("invalid wallet activity witness")
            known[a] = "snapshot/accounts.json.gz#" + a
    price_file = snap / "prices.json.gz"
    quotes = Quotes(read(price_file) if price_file.exists() else {"ids": {}, "series": {}})
    excluded = infrastructure()
    archived, window = native_archive()
    with PRIOR_PNL.open() as f:
        old_pnl = {r["account"].lower(): r for r in csv.DictReader(f)}
    records, coverage = {}, {}
    roots = {}
    for w in calendar:
        records[w] = []
        coverage[w] = {}
        for s in STREAMS:
            for chain in (137, 1):
                events, meta = load_stream(snap, w, chain, s)
                coverage[w][f"{chain}/{s}"] = meta
                records[w].extend(events)
        records[w].extend(archived.get(w, []))
        coverage[w]["1/changenow_native_archive"] = native_coverage(w, window)
        for e in records[w]:
            if e.key in roots:
                raise ValueError("duplicate cross-stream funding event")
            roots[e.key] = e
    forwards, route_metrics, bridge_legs = forward_index(snap, roots, excluded, known)
    prior = defaultdict(set)
    last_seen = {}
    last_wallets = {}
    prior_exact = defaultdict(set)
    prev_rows = {}
    prev_signature = {}
    history_start = calendar[0]
    continuous = not standalone
    if previous_report:
        old = read(previous_report)
        carry = old["continuation"]
        if bounds(old["last_week"])[1] != bounds(calendar[0])[0] or old["protocol_sha256"] != digest(
            HOME / "PROTOCOL.md"
        ):
            raise ValueError("previous report is not a contiguous compatible snapshot")
        history_start = old["history_start"]
        continuous = carry["continuous"]
        for stream in STREAMS:
            prior[stream] = set(carry["seen"][stream])
            last_wallets[stream] = set(old["sets"][old["last_week"]][SERVICES[stream]]["funded"])
            for lvl in LEVELS:
                prior_exact[stream, lvl] = set(carry["seen_exact"][stream][lvl])
            last_seen[stream] = carry["last_counts"][stream]
            prev_signature[stream] = tuple(map(tuple, carry["signatures"][stream]))
            for lvl in LEVELS:
                prev_rows[stream, lvl] = carry["tiers"][stream][lvl]
    weekly, detail, series, sets = [], [], {}, {}
    for w in calendar:
        frame_file = snap / w / "frame.json.gz"
        frame = frame_members(read(frame_file), w) if frame_file.exists() else set()
        coverage[w]["pm_sample"] = {
            "ranges": read(frame_file)["ranges"] if frame_file.exists() else [],
            "status": "SAMPLED" if frame_file.exists() else "UNKNOWN",
            "unique_active": len(frame),
        }
        groups = defaultdict(Group)
        for root, e, ref in [(x, x, None) for x in records[w]] + forwards[w]:
            lvl, account, reason = classify(e, known, owners, excluded)
            if ref:
                if (
                    e.recipient not in known
                    or (root.chain == 137 and root.recipient in known)
                    or e.key in roots
                ):
                    continue
                account, reason = e.recipient, "verified_forward"
                lvl = (
                    "POSSIBLE"
                    if root.role in {"commingled_route", "consolidation"}
                    else "SUPPORTED_INDIRECT"
                )
            p_r = profiles.get(account or e.recipient, {})
            ts, price = quotes.quote(e)
            usd = e.amount * price if price is not None else None
            if account:
                traded = post(p_r, e.ts)[0]
            else:
                traded = "UNKNOWN"
            for group in [groups[root.stream, lvl], groups[root.stream, "ALL"]]:
                group.record(
                    e,
                    lvl,
                    account,
                    reason,
                    usd,
                    traded,
                    profiles.get(e.recipient, {}).get("status"),
                    bool(ref),
                )
            if account and w in selected:
                if ref:
                    source_ref = ref
                elif e.idx < 0:
                    source_ref = "changenow-outflows/out_full/1_" + e.sender + "_txlist.csv.gz"
                else:
                    source_ref = (
                        f"snapshot/{w}/" + ("ethereum-" if e.chain == 1 else "") + e.stream + ".json.gz"
                    )
                path = [leg(root)] if not ref else [leg(root), leg(e)]
                if e.key in bridge_legs:
                    path.insert(1, bridge_legs[e.key])
                detail.append(
                    info(
                        e,
                        lvl,
                        account,
                        root,
                        reason,
                        p_r,
                        source_ref,
                        known[account],
                        price,
                        ts,
                        path,
                        old_pnl.get(account),
                    )
                )
        summary = {}
        week_sets = {}
        for stream, service in SERVICES.items():
            allg = groups[stream, "ALL"]
            funded = allg.direct | allg.indirect
            has_data = any(
                m["status"] in {"SCOPED_COMPLETE", "ARCHIVED_OBSERVATIONS"}
                or m.get("range_count", 0) > 0
                for k, m in coverage[w].items()
                if stream in k
            )
            signature = tuple(
                (k, m["status"], m.get("entire_week_in_archive_window"))
                for k, m in coverage[w].items()
                if stream in k
            )
            for level in LEVELS:
                tier_row = groups[stream, level].row(w, service, level, prior[stream], frame, has_data)
                tier_row["new_exact_pm_observed"] = (
                    len(groups[stream, level].exact - prior_exact[stream, level])
                    if has_data and continuous
                    else "UNKNOWN"
                )
                prior_exact[stream, level].update(groups[stream, level].exact)
                previous = prev_rows.get((stream, level))
                comparable = has_data and previous and prev_signature.get(stream) == signature
                tier_row["delta_funded_observed"] = (
                    tier_row["funded_distinct"] - previous["funded_distinct"]
                    if comparable
                    else "UNKNOWN"
                )
                tier_row["delta_funding_usd"] = (
                    money(D(tier_row["funding_usd"]) - D(previous["funding_usd"]))
                    if comparable and "UNKNOWN" not in {tier_row["funding_usd"], previous["funding_usd"]}
                    else "UNKNOWN"
                )
                if not continuous:
                    tier_row["new_in_observed_history"] = "UNKNOWN"
                prev_rows[stream, level] = tier_row
                if w in selected:
                    weekly.append(tier_row)
            if w in selected:
                summary[service] = allg.row(w, service, "ALL", prior[stream], frame, has_data)
                summary[service]["delta_observed"] = (
                    len(funded) - last_seen[stream]
                    if stream in last_seen and has_data and signature == prev_signature[stream]
                    else "UNKNOWN"
                )
                summary[service]["candidate_exact_pm"] = len(groups[stream, "POSSIBLE"].exact)
                summary[service]["candidate_exact_pm_usd"] = (
                    money(groups[stream, "POSSIBLE"].exact_usd)
                    if not groups[stream, "POSSIBLE"].exact_missing
                    else "UNKNOWN"
                )
                summary[service]["also_observed_on_other_chain_or_via_signer"] = len(
                    allg.pm - allg.exact - allg.indirect
                )
                summary[service]["source_recipients_by_chain"] = {
                    str(chain): len({a for c, a in allg.rec if c == chain}) for chain in (1, 137)
                }
                week_sets[service] = {
                    k: date_set(v)
                    for k, v in dict(
                        direct=allg.direct,
                        indirect=allg.indirect,
                        traded_after=allg.post,
                        funded_ge_1000={a for a, v in allg.by_account.items() if v >= 1000},
                        funded_ge_10000={a for a, v in allg.by_account.items() if v >= 10000},
                        funded=funded,
                        new_observed=funded - prior[stream],
                        possible=groups[stream, "POSSIBLE"].pm,
                        possible_exact_pm=groups[stream, "POSSIBLE"].exact,
                        covered_active_funded=funded & frame,
                    ).items()
                }
                scope_match = (
                    stream in last_wallets and signature == prev_signature.get(stream) and has_data
                )
                week_sets[service]["entered_vs_previous"] = (
                    sorted(funded - last_wallets[stream]) if scope_match else None
                )
                week_sets[service]["left_vs_previous"] = (
                    sorted(last_wallets[stream] - funded) if scope_match else None
                )
                if not continuous:
                    summary[service]["new_in_observed_history"] = "UNKNOWN"
                    week_sets[service]["new_observed"] = None
            prior[stream].update(funded)
            last_wallets[stream] = funded
            last_seen[stream] = len(funded)
            prev_signature[stream] = signature
        if w in selected:
            a, b = (set(week_sets[s]["funded"]) for s in SERVICES.values())
            week_sets.update(
                intersection=sorted(a & b),
                union=sorted(a | b),
                changenow_only=sorted(a - b),
                tornado_only=sorted(b - a),
            )
            series[w] = summary
            sets[w] = week_sets
    hist = {
        service: len(set().union(*(set(v[service]["funded"]) for v in sets.values())))
        for service in SERVICES.values()
    }
    inputs = [
        HOME / "pool_registry.json",
        TRADERS,
        TRADES,
        PRIOR_PNL,
        TRADERS.parent.parent / "f2020_recipients.json",
        RELAY,
        LABELS,
        STATE / "window.json",
        STATE / "recipient_tags.jsonl",
    ]
    for a in NATIVE_SOURCES:
        inputs.extend((STATE / "out_full").glob(f"1_{a}_txlist.*"))
    hashes = {str(path.relative_to(REPO)): digest(path) for path in sorted(inputs)}
    hashes.update(
        {"snapshot/" + str(path.relative_to(snap)): digest(path) for path in sorted(snap.rglob("*.gz"))}
    )
    if previous_report:
        hashes["previous_report"] = digest(previous_report)
    missing = [
        k
        for k in (
            "accounts.json.gz",
            "routes.json.gz",
            "token_routes.json.gz",
            "prices.json.gz",
            "bridge.json.gz",
        )
        if not (snap / k).exists()
    ]
    from .statistics import eligible_panel

    panel = eligible_panel(
        snap / "matched_panel.json", sets, digest(HOME / "PROTOCOL.md"), p["asof_exclusive"]
    )
    if (snap / "matched_panel.json").exists():
        hashes["snapshot/matched_panel.json"] = digest(snap / "matched_panel.json")
    activity_coverage = {
        "screened": len(profiles),
        "returned_trade": sum(v["status"] == "TRADE_OBSERVED" for v in profiles.values()),
        "no_indexed_trade": sum(v["status"] == "NO_INDEXED_TRADE" for v in profiles.values()),
        "unknown": sum(v["status"] == "UNKNOWN" for v in profiles.values()),
        "profiles_with_errors": sum(bool(v["errors"]) for v in profiles.values()),
    }
    payload = dict(
        schema=1,
        first_week=first,
        last_week=last,
        activity_asof_exclusive=p["asof_exclusive"],
        timezone="UTC",
        history_start=history_start,
        continuation=dict(
            continuous=continuous,
            seen={k: sorted(v) for k, v in prior.items()},
            last_counts=last_seen,
            seen_exact={s: {lvl: sorted(prior_exact[s, lvl]) for lvl in LEVELS} for s in STREAMS},
            signatures=prev_signature,
            tiers={
                s: {
                    lvl: {k: prev_rows[s, lvl][k] for k in ("funded_distinct", "funding_usd")}
                    for lvl in LEVELS
                }
                for s in STREAMS
            },
        ),
        series=series,
        sets=sets,
        coverage={w: coverage[w] for w in series},
        proof_levels=LEVELS,
        coverage_scope="bounded Polygon and Ethereum registry; platform total UNKNOWN",
        path_screening=route_metrics,
        missing_inputs=missing,
        inputs_sha256=hashes,
        protocol_sha256=digest(HOME / "PROTOCOL.md"),
        historical_f2020_cohort=historic_cohort(),
        account_ascertainment=activity_coverage,
        statistics=analyze(panel, hist),
    )
    weekly.sort(key=lambda r: (r["week"], r["service"], LEVELS.index(r["evidence"])))
    detail.sort(
        key=lambda r: (
            r["week"],
            r["funding_time"],
            r["chain"],
            r["tx"],
            str(r["log_index"]),
            r["wallet"],
        )
    )
    write_csv(out / "weekly_funding.csv", weekly, weekly[0].keys())
    fields = detail[0].keys() if detail else WALLET_FIELDS
    write_csv(out / "wallet_funding.csv", detail, fields)
    atomic(
        out / "weekly_funding.json",
        (json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=1) + "\n").encode(),
    )
    render(out, payload, weekly)
    return payload


WALLET_FIELDS = (
    "week service evidence wallet wallet_chain chain receipt_recipient source_address source_role source_confidence "
    "token token_contract amount usd_known verified_funding_usd usd_price price_time funding_time block tx log_index path intermediaries relationship "
    "pm_evidence source_evidence traded_after first_buy_status first_buy_time first_buy_tx first_buy_market first_buy_title first_buy_usd "
    "subsequent_observed_market_buy_usd activity_scope first_indexed_trade known_trade_before pnl_time economic_pnl_usd "
    "archived_pnl_usd archived_pnl_incomplete"
).split()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    sel = p.add_mutually_exclusive_group()
    sel.add_argument("--week")
    sel.add_argument("--from-week")
    p.add_argument("--to-week")
    p.add_argument("--snapshot", type=Path, default=SNAP)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--previous-report", type=Path)
    p.add_argument(
        "--standalone", action="store_true", help="mark earlier first-seen history as unknown"
    )
    args = p.parse_args()
    if args.week and args.to_week:
        p.error("choose a single week or a range")
    build(
        args.snapshot,
        args.out,
        args.week or args.from_week,
        args.week or args.to_week,
        args.previous_report,
        args.standalone,
    )


if __name__ == "__main__":
    main()
