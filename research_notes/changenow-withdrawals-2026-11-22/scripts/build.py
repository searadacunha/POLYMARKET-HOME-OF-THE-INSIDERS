"""Offline: classify, value, deduplicate and rank the withdrawals found by census.py; write the published tables.

Inputs, all under --raw (outside the repository) unless copied into the snapshot:
- <week>/withdrawals.json from census.py (walks, attributed parts, keys owning a wallet, endpoint evidence);
- relay_api/hash/*.json and relay_api/checked.json from relay_api.py (optional: Relay's record of unresolved fills);
- bets/<wallet>.json from bets.py (optional: activity, markets, profit before each withdrawal).

Evidence classes (mission text, section 6), one per ChangeNOW-side transfer and attributed part:
- CONFIRMED_DIRECT: the wallet's debit and the arrival in a ChangeNOW deposit address are the same transaction
  (a transfer from the wallet, or Polymarket's collateral unwrap in that transaction), every leg read on chain.
- SUPPORTED_INDIRECT: every hop read on chain, through an intermediate address (balance rule, lower bound) or a Relay
  order whose id is on both sides; or a Relay fill whose origin transaction Relay's own record names, when that
  origin transaction was read on chain as a debit of the wallet (link_source=relay_api).
- POSSIBLE: a key that owns a trading wallet paid a ChangeNOW deposit address and no walk proved the continuity.
- UNRESOLVED: a deposit sent by an address that a trading wallet fed, or by the collateral ramp, whose walk stopped.
Everything else that was walked (Relay fills with an origin elsewhere, refuted walks) is counted in the coverage.
"""
import argparse
import csv
import hashlib
import io as _io
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTE = HERE.parent
REPO = HERE.parents[2]
CLASSES = ("CONFIRMED_DIRECT", "SUPPORTED_INDIRECT", "POSSIBLE", "UNRESOLVED")
ESTABLISHED = ("CONFIRMED_DIRECT", "SUPPORTED_INDIRECT")
EXPLORER = {1: "https://etherscan.io/tx/", 137: "https://polygonscan.com/tx/", 8453: "https://basescan.org/tx/", 42161: "https://arbiscan.io/tx/",
            10: "https://optimistic.etherscan.io/tx/", 56: "https://bscscan.com/tx/"}
CHAIN_NAME = {1: "Ethereum", 137: "Polygon", 8453: "Base", 42161: "Arbitrum", 10: "Optimism", 56: "BNB Chain"}
RAMP_NAMES = ("Polymarket CollateralOnramp", "Polymarket CollateralOfframp", "Polymarket PermissionedRamp")
DEPOSITORY = "0x4cd00e387622c35bddb9b4c962c136462338bc31"
COLLATERAL_TOKENS = {"0x2791bca1f2de4661ed88a30c99a7a9449aa84174", "0x3c499c542cef5e3811e1192ce70d8cc03d5c3359", "0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb"}


def utc(ts):
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%d %H:%M:%S") if ts else ""


def week_of(ts):
    iso = datetime.fromtimestamp(int(ts), timezone.utc).isocalendar()
    return f"{iso[0]}-W{iso[1]:02d}"


def key(r):
    return (int(r["chain"]), r["tx"].lower(), int(r["log_index"]))


def event_id(start, origin):
    text = "|".join(str(x) for x in key(start) + key(origin))
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def registry(path=REPO / "monitoring/changenow_weekly/registry.csv"):
    with open(path, newline="") as f:
        return {r["address"]: r for r in csv.DictReader(f)}


def endpoint_grades(path=NOTE / "inputs" / "endpoint_grades.csv"):
    """Grade of every ChangeNOW-side wallet, read from the repository's evidence on 2026-11-22, one row per address with
    its labels, lineages, structural evidence, counter-evidence and sources: A public ChangeNOW label from two
    independent lineages and service behaviour; B structural tie to a labelled wallet or one lineage; C behaviour only."""
    if not path.exists():
        return {}
    with open(path, newline="") as f:
        return {r["address"].lower(): r["grade"] for r in csv.DictReader(f)}


GRADES = {}


def grade(sinks, reg):
    """Attribution of a deposit address through the payout wallets it swept into: the best grade among them. Without
    a graded row, the register's tier: A_LABELLED counts as B (one lineage is the register's minimum), B_STRUCTURAL as B."""
    order = {"A": 0, "B": 1, "C": 2, "X": 3}
    found = []
    for s in sinks:
        g = GRADES.get(s)
        if not g:
            g = "B" if reg.get(s, {}).get("tier") in ("A_LABELLED", "B_STRUCTURAL") else "C"
        found.append(g)
    return min(found, key=order.get) if found else ""


def intermediaries(walk, part):
    """Addresses that held the funds between the wallet and the ChangeNOW deposit address, in order, and the count.
    Polymarket's collateral ramps and the Relay escrow are plumbing, not holders; a Relay order counts as one bridge."""
    start = walk["start"]
    held = []
    for h in reversed(walk["hops"]):                      # from the wallet toward ChangeNOW
        if h["kind"] == "RELAY_ORDER":
            held.append(f"Relay order {h.get('order', '')[:10]} ({CHAIN_NAME.get(h['chain'], h['chain'])} to {CHAIN_NAME.get(h.get('fill_chain'), h.get('fill_chain'))})")
        elif h["kind"] in ("TRANSFER", "POLYMARKET_WALLET_DEBIT"):
            d = h["dst"]
            if d not in (start["dst"], DEPOSITORY, "0x" + "0" * 40) and d not in RAMP_ADDRESSES and d not in held:
                held.append(d)
    return held


RAMP_ADDRESSES = set()


def load_ramps():
    sys.path.insert(0, str(REPO / "investigations/polysentinel/sources/signal_engine"))
    sys.dont_write_bytecode = True
    from fund_flow import flows as ff                 # noqa: E402  documented Polymarket contracts
    RAMP_ADDRESSES.update(a for a, v in ff.LABELS.items() if v["name"] in RAMP_NAMES)
    RAMP_ADDRESSES.add(ff.PUSD)
    return ff


def path_text(walk):
    kinds = [h["kind"] for h in reversed(walk["hops"])]
    return " > ".join(kinds + ["CHANGENOW_DEPOSIT_ADDRESS"])


def links(refs):
    return ";".join(f"{EXPLORER.get(c, '')}{t}" for c, t in refs)


def underlying(walk, part):
    """Every transaction of the path, origin first, once each."""
    seen, out = set(), []
    hops = list(reversed(walk["hops"]))
    for h in hops:
        for c, t in ((h["chain"], h["tx"]), (h.get("fill_chain"), h.get("fill_tx"))):
            if c and t and (c, t) not in seen:
                seen.add((c, t))
                out.append((c, t))
    s = walk["start"]
    if (s["chain"], s["tx"]) not in seen:
        out.append((s["chain"], s["tx"]))
    return out


def load(raw):
    """Census files of every week: <raw>/<week>/withdrawals.json, or the gzip copy kept in the snapshot."""
    weeks = {}
    for p in sorted(Path(raw).glob("20*-W*/withdrawals.json*")):
        w = read_gz(p) if p.suffix == ".gz" else json.loads(p.read_text())
        weeks[w["week"]] = w
    return weeks


def relay_records(raw):
    """Relay's answers by fill transaction, and the on-chain check of the origins they name (relay_api.py --check)."""
    out = {}
    folder = Path(raw) / "relay_api" / "hash"
    for p in sorted(folder.glob("*.json")) if folder.exists() else []:
        a = json.loads(p.read_text())
        if a["status"] == 200 and a["body"] and a["body"].get("requests"):
            out[p.stem] = a["body"]["requests"]
    checked = Path(raw) / "relay_api" / "checked.json"
    return out, (json.loads(checked.read_text()) if checked.exists() else {})


def forward_rows(forward, rows, reg, stats):
    """Withdrawals found forward from known wallets (cohort.py) that the census did not list: a deposit address the
    wallet paid, swept within a day into a registered payout wallet, a plain key with at most two transactions.
    Paid by the wallet itself: CONFIRMED_DIRECT. Paid by the wallet's key after the wallet paid it: POSSIBLE, because
    no balance rule ties the key's outflow to the wallet's money. Each is counted where the census would count it."""
    have = {(r["changenow_tx"], str(r["changenow_log_index"])) for r in rows}
    weeks_read = {r["week"] for r in rows}
    out = []
    for f in (forward or {}).get("found", []):
        if f.get("kind") != "DEPOSIT_ADDRESS":
            continue
        leg, debit = f["leg"], f["debit"]
        k = (leg["tx"], str(leg["log_index"]))
        if k in have:
            stats["forward_hit_also_in_census"] += 1
            continue
        week = week_of(leg["ts"])
        stats["forward_hit_in_a_census_week" if week in weeks_read else "forward_hit_outside_census_weeks"] += 1
        s = dict(chain=137, tx=leg["tx"], log_index=leg["log_index"], block=leg["block"], ts=leg["ts"], src=leg["src"], dst=leg["dst"], token=leg["token"], raw=str(leg["raw"]))
        o = dict(chain=137, tx=debit["tx"], log_index=debit["log_index"], block=debit["block"], ts=debit["ts"], src=debit["src"], dst=debit["dst"], token=debit["token"], raw=str(debit["raw"]))
        end = dict(rule="SINGLE_USE_KEY", sinks=[f["sink"]], sweep=dict(tx=f["sweep"]["tx"]), gas=None)
        cls = "POSSIBLE" if f.get("via_key") else "CONFIRMED_DIRECT"
        note = "found forward from the wallet (cohort.py)" + ("; the wallet paid its key, which paid the deposit address within three days" if f.get("via_key") else "")
        row = make_row(week, cls, "forward_check", None, s, o, f["wallet"], int(leg["raw"]), f.get("value") or {}, end, reg, {}, note=note,
                       origin_raw=int(debit["raw"]) if not f.get("via_key") else None)
        row["intermediary_count"] = 0 if cls == "CONFIRMED_DIRECT" else ""
        row["intermediaries"] = "" if cls == "CONFIRMED_DIRECT" else leg["src"]
        out.append(row)
        have.add(k)
    return out


def rows_from(weeks, reg, relay=None, checked=None, forward=None):
    """One row per attributed part or candidate deposit, each ChangeNOW-side transfer in one class only."""
    rows, stats = _rows_from(weeks, reg, relay, checked)
    rows += forward_rows(forward, rows, reg, stats)
    for r in rows:
        if r["evidence_class"] in ESTABLISHED and r["changenow_endpoint_grade"] in ("C", "X"):
            r["note"] = (r["note"] + "; " if r["note"] else "") + f"every hop read, but the ChangeNOW payout wallet swept into is graded {r['changenow_endpoint_grade']} (behaviour only): kept as POSSIBLE"
            r["evidence_class"] = "POSSIBLE"
            r["intermediary_count"] = ""
            stats["established_path_weak_endpoint"] += 1
    return rows, stats


def _rows_from(weeks, reg, relay=None, checked=None):
    relay, checked = relay or {}, checked or {}
    rows, seen_start = [], {}
    stats = Counter()
    used = defaultdict(int)          # Polymarket debit -> raw already attributed, across weeks: each week's walker only knows its own
    for week in sorted(weeks):
        w = weeks[week]
        walks = {key(x["start"]): x for x in w["walks"]}
        ends = {(e["chain"], e["address"]): e for e in w.get("endpoints", [])}
        prior = set(seen_start)
        for p in w["parts"]:
            walk = walks[key(p["start"])]
            s, o = p["start"], p["origin"]
            if key(s) in prior:                                      # read again in a later week: counted once, where first found
                stats["part_seen_in_an_earlier_week"] += 1
                continue
            take, start_raw, value = int(p["origin_raw"]), int(p["start_raw"]), dict(p.get("value") or {})
            left = int(o["raw"]) - used[key(o)]
            if left <= 0:
                stats["debit_already_attributed_in_full"] += 1
                continue
            if take > left:                                          # a later week reached a debit already partly spent: keep the remainder only
                stats["part_capped_by_earlier_attribution"] += 1
                start_raw = start_raw * left // take
                for f in ("amount", "usd"):
                    if f in value:
                        value[f] = round(value[f] * left / take, 6 if f == "amount" else 2)
                take = left
            used[key(o)] += take
            direct = o["chain"] == s["chain"] and o["tx"] == s["tx"]
            rows.append(make_row(week, "CONFIRMED_DIRECT" if direct else "SUPPORTED_INDIRECT", "chain", walk, s, o, p["account"], start_raw,
                                 value, ends.get((s["chain"], s["dst"])), reg, w, origin_raw=take))
            seen_start[key(s)] = rows[-1]["evidence_class"]
        for x in w["walks"]:                                         # Relay's record for the fills the chain did not tie
            k = key(x["start"])
            if k in seen_start or x["category"] not in ("RELAY_SOLVER", "RELAY_ROUTER") or x["status"] == "CONFIRMED":
                continue
            check = checked.get(x["start"]["tx"])
            if check and check.get("verdict") == "WALLET_DEBIT_VERIFIED":
                o = check["origin"]
                rows.append(make_row(week, "SUPPORTED_INDIRECT", "relay_api", x, x["start"], o, o["src"], int(x["start"]["raw"]),
                                     check.get("value") or {}, ends.get((x["start"]["chain"], x["start"]["dst"])), reg, w, note=check.get("note", ""),
                                     origin_raw=int(o["raw"])))
                seen_start[k] = "SUPPORTED_INDIRECT"
            elif check and check.get("verdict") == "KEY_OF_WALLET":
                o = check["origin"]
                rows.append(make_row(week, "POSSIBLE", "relay_api", x, x["start"], o, check["wallet"], int(x["start"]["raw"]),
                                     check.get("value") or {}, ends.get((x["start"]["chain"], x["start"]["dst"])), reg, w, note=check.get("note", "")))
                seen_start[k] = "POSSIBLE"
            else:
                stats["relay_fill_not_tied_to_polymarket"] += 1
        for c in w["candidates"]:                                    # keys that own a trading wallet
            wallets = [x["wallet"] for x in c["wallets"]]
            for d in c["deposits"]:
                k = key(d)
                if k in seen_start:
                    continue
                walk = walks.get(k)
                moved = any(ts <= d["ts"] for ts in c.get("wallet_paid_key", []))
                note = ("money moved from the wallet to this key before the deposit; continuity not shown" if moved else
                        "key owns the wallet; no transfer between them read before the deposit")
                if walk and walk["status"] != "CONFIRMED":
                    note += f"; walk stopped: {walk['detail'].get('reason', '')}"
                account = wallets[0] if len(wallets) == 1 else "|".join(wallets)
                rows.append(make_row(week, "POSSIBLE", "key_ownership", walk, d, None, account, int(d["raw"]), d.get("value") or {},
                                     ends.get((d["chain"], d["dst"])), reg, w, owner=c["owner"], note=note, ownership=[x["proof"] for x in c["wallets"]]))
                seen_start[k] = "POSSIBLE"
        for x in w["walks"]:                                         # fed senders and ramp deposits whose walk stopped
            k = key(x["start"])
            if k in seen_start or x["status"] == "CONFIRMED" or x["category"] not in ("FED_BY_WALLET", "COLLATERAL_RAMP"):
                if x["status"] == "NOT_ORIGIN":
                    stats[f"refuted_{x['category'].lower()}"] += 1
                continue
            if x["status"] == "NOT_ORIGIN":
                stats[f"refuted_{x['category'].lower()}"] += 1
                continue
            payers = w.get("fed_payers", {}).get(x["start"]["src"], [])
            rows.append(make_row(week, "UNRESOLVED", "walk_stopped", x, x["start"], None, "|".join(payers) or "", int(x["start"]["raw"]),
                                 {}, ends.get((x["start"]["chain"], x["start"]["dst"])), reg, w, note=x["detail"].get("reason", "")))
            seen_start[k] = "UNRESOLVED"
    return rows, stats


FIELDS = ["event_id", "evidence_class", "link_source", "week", "changenow_arrival_utc", "changenow_chain", "changenow_deposit_address",
          "changenow_deposit_rule", "changenow_service_wallets", "changenow_endpoint_grade", "changenow_tx", "changenow_log_index", "changenow_block",
          "token", "amount", "price_usd", "price_utc", "usd", "polymarket_wallet", "polymarket_debit_tx", "polymarket_debit_log_index", "polymarket_debit_block", "polymarket_debit_amount",
          "polymarket_debit_utc", "delay_seconds", "intermediaries", "intermediary_count", "path", "walk_category", "key_owner", "ownership_proof",
          "attribution_detail", "note", "sweep_tx", "gas_tx", "underlying_transactions", "explorer_links"]


def make_row(week, cls, source, walk, s, o, account, raw_amount, value, end, reg, w, owner="", note="", ownership=(), origin_raw=None):
    end = end or {}
    sinks = end.get("sinks", [])
    tx_list = underlying(walk, None) if walk else [(s["chain"], s["tx"])]
    if source in ("relay_api", "forward_check") and o:
        tx_list = [(o["chain"], o["tx"])] + [t for t in tx_list if t != (o["chain"], o["tx"])]
    held = intermediaries(walk, None) if (walk and cls in ESTABLISHED and source == "chain") else []
    if source == "relay_api":
        held = [f"Relay order (record of api.relay.link) {CHAIN_NAME.get(o['chain'], o['chain'])} to {CHAIN_NAME.get(s['chain'], s['chain'])}"]
    detail = walk["detail"] if walk else {}
    return dict(event_id=event_id(s, o or s), evidence_class=cls, link_source=source, week=week, changenow_arrival_utc=utc(s.get("ts")),
                changenow_chain=CHAIN_NAME.get(s["chain"], s["chain"]), changenow_deposit_address=s["dst"], changenow_deposit_rule=end.get("rule", ""),
                changenow_service_wallets="|".join(sinks), changenow_endpoint_grade=grade(sinks, reg) if sinks else "",
                changenow_tx=s["tx"], changenow_log_index=s["log_index"], changenow_block=s["block"], token=value.get("symbol", ""),
                amount=f"{value['amount']:.6f}" if "amount" in value else "", price_usd=value.get("price_usd", ""), price_utc=utc(value.get("price_ts")),
                usd=f"{value['usd']:.2f}" if "usd" in value else "", polymarket_wallet=account, polymarket_debit_tx=(o or {}).get("tx", ""),
                polymarket_debit_log_index=(o or {}).get("log_index", ""), polymarket_debit_block=(o or {}).get("block", ""),
                polymarket_debit_amount=f"{origin_raw / 1e6:.6f}" if origin_raw is not None and (o or {}).get("token") in COLLATERAL_TOKENS else "", polymarket_debit_utc=utc((o or {}).get("ts")),
                delay_seconds=(s["ts"] - o["ts"]) if o and o.get("ts") and s.get("ts") else "", intermediaries="|".join(held), intermediary_count=len(held) if cls in ESTABLISHED else "",
                path=path_text(walk) if walk and cls in ESTABLISHED and source == "chain" else "", walk_category=walk["category"] if walk else "",
                key_owner=owner, ownership_proof="|".join(ownership), attribution_detail=json.dumps({k: v for k, v in detail.items() if k != "direct"}, sort_keys=True) if detail else "",
                note=note, sweep_tx=(end.get("sweep") or {}).get("tx", ""), gas_tx=(end.get("gas") or {}).get("tx", ""),
                underlying_transactions=";".join(f"{c}:{t}" for c, t in tx_list), explorer_links=links(tx_list), _raw=raw_amount,
                _usd=value.get("usd"), _ts=s.get("ts"), _debit_ts=(o or {}).get("ts"))


def csv_text(rows, fields):
    buf = _io.StringIO()
    out = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
    out.writeheader()
    for r in rows:
        out.writerow(r)
    return buf.getvalue()


def weekly(rows, weeks):
    """Per ISO week of arrival at ChangeNOW: distinct wallets, transfers and USD by class, new and recurring wallets."""
    seen_before = set()
    out = []
    for week in sorted(weeks):
        w = weeks[week]
        mine = [r for r in rows if r["week"] == week]
        est = [r for r in mine if r["evidence_class"] in ESTABLISHED]
        wallets = {r["polymarket_wallet"] for r in est}
        transfers = {(r["changenow_chain"], r["changenow_tx"], r["changenow_log_index"]) for r in est}
        row = dict(week=week, wallets_established=len(wallets), transfers_established=len(transfers),
                   usd_established=round(sum(r["_usd"] or 0 for r in est), 2), unpriced_established=sum(1 for r in est if r["_usd"] is None),
                   new_wallets=len(wallets - seen_before), recurring_wallets=len(wallets & seen_before))
        for cls in CLASSES:
            part = [r for r in mine if r["evidence_class"] == cls]
            row[f"{cls.lower()}_transfers"] = len({(r["changenow_chain"], r["changenow_tx"], r["changenow_log_index"]) for r in part})
            row[f"{cls.lower()}_wallets"] = len({r["polymarket_wallet"] for r in part if r["polymarket_wallet"]})
            row[f"{cls.lower()}_usd"] = round(sum(r["_usd"] or 0 for r in part), 2)
        seen_before |= wallets
        cover = []
        for c, b in sorted(w["blocks"].items()):
            cover.append(f"{CHAIN_NAME.get(int(c), c)} {b['first']}-{b['last']}{'' if b.get('closed') else ' (open)'}")
        row["chains_read"] = "; ".join(cover)
        row["week_closed"] = all(b.get("closed") for b in w["blocks"].values())
        for c, t in sorted(w.get("totals", {}).items()):
            name = CHAIN_NAME.get(int(c), c).lower().replace(" ", "_")
            row[f"{name}_changenow_customer_deposits"] = t["customer_deposits"]
            row[f"{name}_changenow_deposit_usd"] = t["usd_hourly_prices"]
        row["polygon_senders_tested"] = w["linking"]["polygon_senders"]
        row["polygon_heavy_senders_set_aside"] = w["linking"]["heavy_keys"]
        row["walks"] = len(w["walks"])
        row["walks_unresolved"] = sum(1 for x in w["walks"] if x["status"] == "UNRESOLVED")
        out.append(row)
    return out


def f2020_cohort(path=REPO / "investigations/changenow-polymarket/sources/state/pm_traders.csv"):
    """Trading accounts paid by 0xf2020cbf... between 2026-04-14 and 2026-06-22 (archived study, unchanged)."""
    if not path.exists():
        return set()
    with open(path, newline="") as f:
        return {r["account"].lower() for r in csv.DictReader(f) if r.get("account")}


def rankings(rows, bets, cohort=frozenset()):
    by = defaultdict(list)
    for r in rows:
        if r["polymarket_wallet"] and "|" not in r["polymarket_wallet"]:
            by[r["polymarket_wallet"]].append(r)
    out = []
    for wallet, rs in by.items():
        est = [r for r in rs if r["evidence_class"] in ESTABLISHED]
        pos = [r for r in rs if r["evidence_class"] == "POSSIBLE"]
        b = bets.get(wallet) or {}
        last = max((r["_ts"] for r in est), default=None)
        out.append(dict(wallet=wallet, withdrawals_established=len({(r["changenow_chain"], r["changenow_tx"], r["changenow_log_index"]) for r in est}),
                        changenow_usd_established=round(sum(r["_usd"] or 0 for r in est), 2),
                        changenow_usd_confirmed_direct=round(sum(r["_usd"] or 0 for r in est if r["evidence_class"] == "CONFIRMED_DIRECT"), 2),
                        changenow_usd_supported_indirect=round(sum(r["_usd"] or 0 for r in est if r["evidence_class"] == "SUPPORTED_INDIRECT"), 2),
                        withdrawals_possible=len(pos), changenow_usd_possible_upper_bound=round(sum(r["_usd"] or 0 for r in pos), 2),
                        first_withdrawal_utc=utc(min((r["_ts"] for r in est), default=None)), last_withdrawal_utc=utc(last),
                        confidence=("CONFIRMED_DIRECT" if any(r["evidence_class"] == "CONFIRMED_DIRECT" for r in est) else
                                    "SUPPORTED_INDIRECT" if est else "POSSIBLE" if pos else "UNRESOLVED"),
                        endpoint_grades="|".join(sorted({r["changenow_endpoint_grade"] for r in est + pos if r["changenow_endpoint_grade"]})),
                        realized_pnl_lifetime_usd=b.get("realized_pnl_usd", ""), realized_pnl_complete=b.get("complete", ""),
                        biggest_win_market=b.get("biggest_win", {}).get("title", ""), biggest_win_usd=b.get("biggest_win", {}).get("pnl_usd", ""),
                        biggest_win_utc=utc(b.get("biggest_win", {}).get("resolved_ts")), first_buy_z=b.get("first_buy_z", ""),
                        markets_resolved=b.get("markets_resolved", ""), win_rate=b.get("win_rate", ""),
                        in_f2020_funded_cohort="yes" if wallet in cohort else "no"))
    out.sort(key=lambda r: (-r["changenow_usd_established"], -r["changenow_usd_possible_upper_bound"], r["wallet"]))
    for i, r in enumerate(out, 1):
        r["rank"] = i
    return out


FAST_GAIN_USD = 100          # descriptive screen of the mission's "rapid withdrawal after a large gain", not a test
FAST_GAIN_SHARE = 0.5        # the gain closed in the day before is at least half of what the wallet sent


def read_gz(path):
    import gzip
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return json.load(f)


def bets_analysis(raw, rows):
    """Bets of every wallet with activity on disk: lifetime results and, for each established withdrawal, the profit
    realized before the wallet's debit, the largest gain closed in the day before, and the share of the wallet's
    collateral that left. Fills per-row fields in place; returns {wallet: lifetime summary}."""
    import pnl
    folder = Path(raw) / "bets"
    if not (folder / "markets.json.gz").exists():
        return {}
    mk = read_gz(folder / "markets.json.gz")["markets"]
    bal = read_gz(folder / "balances.json.gz") if (folder / "balances.json.gz").exists() else {}
    controls = read_gz(folder / "controls.json.gz") if (folder / "controls.json.gz").exists() else {}
    out = {}
    by = defaultdict(list)
    for r in rows:
        if "|" not in r["polymarket_wallet"] and r["polymarket_wallet"]:
            by[r["polymarket_wallet"]].append(r)
    for wallet, rs in sorted(by.items()):
        path = folder / "activity" / f"{wallet}.json.gz"
        if not path.exists():
            continue
        a = read_gz(path)
        acts = a["rows"]
        last_row = max((x["timestamp"] for x in acts), default=0)
        life = pnl.lifetime(acts, mk)
        cal = life["calibration"]
        out[wallet] = dict(complete=a["complete"], rows=len(acts), realized=life["realized"], markets=life["markets"], markets_closed=life["markets_closed"],
                           markets_open=life["markets_open"], best=life["best"], calibration=cal, rewards=life["rewards"],
                           first_trade=life["first_trade"], last_trade=life["last_trade"], net_pnl_with_open=life["summary"].get("net_pnl"))
        c = controls.get(wallet)
        if c and c.get("controls"):
            zs = []
            for x in c["controls"]:
                cp = folder / "activity" / f"{x}.json.gz"
                if cp.exists():
                    z = pnl.lifetime(read_gz(cp)["rows"], mk)["calibration"].get("z")
                    if z is not None:
                        zs.append(z)
            z0 = cal.get("z")
            out[wallet]["controls"] = dict(market=c["condition_id"], pool=c["pool"], read=len(c["controls"]), with_z=len(zs), z=sorted(zs),
                                           share_below=None if z0 is None or not zs else round(sum(1 for z in zs if z < z0) / len(zs), 3))
        for r in rs:
            if r["evidence_class"] not in ESTABLISHED or not r["_debit_ts"]:
                continue
            T = int(r["_debit_ts"])
            b = pnl.before(acts, mk, T)
            r["activity_complete_at_debit"] = a["complete"] or T <= last_row
            r["realized_before_usd"] = b["realized_before"]
            r["markets_closed_before"] = b["markets_closed"]
            r["best_market_before"] = (b["best"] or {}).get("title", "")
            r["best_market_before_usd"] = (b["best"] or {}).get("realized", "")
            r["gains_24h_before_usd"] = b["gains_day_before"]
            g = b["biggest_gain_day_before"] or {}
            r["biggest_gain_24h_market"] = g.get("title", "")
            r["biggest_gain_24h_usd"] = g.get("realized", "")
            r["biggest_gain_24h_outcome"] = g.get("outcome", "")
            r["biggest_gain_24h_avg_price"] = g.get("avg_price", "")
            r["seconds_from_biggest_gain_24h"] = g.get("seconds_before", "")
            r["seconds_since_last_gain"] = b["seconds_since_last_gain"] if b["seconds_since_last_gain"] is not None else ""
            k = f"{wallet}@{r['polymarket_debit_block']}"
            if k in bal and r["polymarket_debit_amount"]:
                held = sum(int(v) for v in bal[k]["raw"].values()) / 1e6
                r["collateral_before_debit"] = f"{held:.6f}"
                r["share_of_collateral_withdrawn"] = round(float(r["polymarket_debit_amount"]) / held, 4) if held else ""
    return out


def fast_after_gains(rows):
    """Established withdrawals that followed, within a day, closed gains of at least FAST_GAIN_USD and at least
    FAST_GAIN_SHARE of the amount sent. Per wallet: how many, and how often it repeated."""
    hits = defaultdict(list)
    for r in rows:
        if r["evidence_class"] not in ESTABLISHED or r.get("gains_24h_before_usd") in (None, ""):
            continue
        gain = float(r["gains_24h_before_usd"])
        sent = r["_usd"] or 0
        if gain >= FAST_GAIN_USD and sent and gain >= FAST_GAIN_SHARE * sent:
            hits[r["polymarket_wallet"]].append(r)
    out = []
    for w, rs in hits.items():
        out.append(dict(wallet=w, withdrawals_after_gain=len({(r["changenow_chain"], r["changenow_tx"], r["changenow_log_index"]) for r in rs}),
                        gains_24h_before_usd=round(max(float(r["gains_24h_before_usd"]) for r in rs), 2), sent_usd=round(sum(r["_usd"] or 0 for r in rs), 2),
                        largest_gain_market=max(rs, key=lambda r: float(r["biggest_gain_24h_usd"] or 0))["biggest_gain_24h_market"],
                        largest_gain_usd=max(float(r["biggest_gain_24h_usd"] or 0) for r in rs),
                        fastest_seconds_from_gain=min((int(r["seconds_from_biggest_gain_24h"]) for r in rs if r["seconds_from_biggest_gain_24h"] != ""), default=""),
                        first_utc=utc(min(r["_ts"] for r in rs)), last_utc=utc(max(r["_ts"] for r in rs))))
    out.sort(key=lambda x: (-x["withdrawals_after_gain"], -x["gains_24h_before_usd"], x["wallet"]))
    return out


BET_FIELDS = ["activity_complete_at_debit", "realized_before_usd", "markets_closed_before", "best_market_before", "best_market_before_usd",
              "gains_24h_before_usd", "biggest_gain_24h_market", "biggest_gain_24h_usd", "biggest_gain_24h_outcome", "biggest_gain_24h_avg_price",
              "seconds_from_biggest_gain_24h", "seconds_since_last_gain", "collateral_before_debit", "share_of_collateral_withdrawn"]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--raw", required=True)
    p.add_argument("--out", default=str(NOTE / "results"))
    args = p.parse_args(argv)
    load_ramps()
    reg = registry()
    GRADES.update(endpoint_grades())
    weeks = load(args.raw)
    relay, checked = relay_records(args.raw)
    fpath = Path(args.raw) / "cohort" / "forward.json"
    forward = json.loads(fpath.read_text()) if fpath.exists() else None
    rows, stats = rows_from(weeks, reg, relay, checked, forward)
    life = bets_analysis(args.raw, rows)
    bets = {w: dict(realized_pnl_usd=v["realized"], complete=v["complete"], first_buy_z=(v["calibration"] or {}).get("z", ""),
                    markets_resolved=(v["calibration"] or {}).get("n", ""), win_rate=(v["calibration"] or {}).get("win_rate", ""),
                    biggest_win=dict(title=(v["best"] or {}).get("title", ""), pnl_usd=(v["best"] or {}).get("realized", ""),
                                     resolved_ts=(v["best"] or {}).get("closed_at"))) for w, v in life.items()}
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rows.sort(key=lambda r: (r["_ts"] or 0, r["changenow_chain"], r["changenow_tx"], r["changenow_log_index"], r["event_id"]))
    (out / "changenow_outflows.csv").write_text(csv_text(rows, FIELDS + BET_FIELDS))
    fast = fast_after_gains(rows)
    (out / "fast_withdrawals_after_gains.csv").write_text(csv_text(fast, ["wallet", "withdrawals_after_gain", "gains_24h_before_usd", "sent_usd", "largest_gain_market",
                                                                          "largest_gain_usd", "fastest_seconds_from_gain", "first_utc", "last_utc"]))
    (out / "wallet_bets.json").write_text(json.dumps(life, indent=1, sort_keys=True, default=str) + "\n")
    wk = weekly(rows, weeks)
    (out / "weekly_outflows.csv").write_text(csv_text(wk, list(wk[0].keys()) if wk else ["week"]))
    rk = rankings(rows, bets, f2020_cohort())
    rk_fields = ["rank", "wallet", "withdrawals_established", "changenow_usd_established", "changenow_usd_confirmed_direct", "changenow_usd_supported_indirect",
                 "withdrawals_possible", "changenow_usd_possible_upper_bound", "realized_pnl_lifetime_usd", "realized_pnl_complete", "biggest_win_market",
                 "biggest_win_usd", "biggest_win_utc", "first_withdrawal_utc", "last_withdrawal_utc", "confidence", "endpoint_grades", "first_buy_z",
                 "markets_resolved", "win_rate", "in_f2020_funded_cohort"]
    (out / "wallet_rankings.csv").write_text(csv_text(rk, rk_fields))
    summary = dict(weeks=sorted(weeks), classes={c: dict(rows=sum(1 for r in rows if r["evidence_class"] == c),
                                                         transfers=len({(r["changenow_chain"], r["changenow_tx"], r["changenow_log_index"]) for r in rows if r["evidence_class"] == c}),
                                                         wallets=len({r["polymarket_wallet"] for r in rows if r["evidence_class"] == c and r["polymarket_wallet"]}),
                                                         usd=round(sum(r["_usd"] or 0 for r in rows if r["evidence_class"] == c), 2)) for c in CLASSES},
                   established_wallets=len({r["polymarket_wallet"] for r in rows if r["evidence_class"] in ESTABLISHED}),
                   established_usd=round(sum(r["_usd"] or 0 for r in rows if r["evidence_class"] in ESTABLISHED), 2),
                   by_grade={g: round(sum(r["_usd"] or 0 for r in rows if r["evidence_class"] in ESTABLISHED and r["changenow_endpoint_grade"] == g), 2) for g in "ABC"},
                   other=dict(stats))
    (out / "summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
