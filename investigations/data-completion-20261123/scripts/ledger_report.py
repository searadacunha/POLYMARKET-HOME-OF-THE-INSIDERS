"""Offline: build the cohort ledger outputs from the collected logs and the cached market sources.

Writes, under --results:
  wallet_fills.parquet           one row per OrderFilled owned by a cohort account (the canonical trade ledger)
  wallet_position_ledger.parquet one row per (account, transaction, outcome token) leg with its collateral share
                                 (both from full CSV tables written to --local, which may exceed the size policy)
  wallet_position_summary.csv.gz one row per (account, market)
  wallet_summary.csv             one row per account
  coverage_by_contract.csv       logs per emitter x month x event family x provider
  coverage_by_market.csv.gz      per market: accounts, fills, resolution status
  reconciliation_failures.csv    every failed or skipped check, with its reason
  ledger_results.json            totals with their denominators, coverage of every stream, check counts
"""

import argparse
import csv
import gzip
import hashlib
import io
import json
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ledger_build as B  # noqa: E402

FAMILY = {B.TRANSFER: "erc20_transfer", B.TRANSFER_SINGLE: "erc1155_transfer", B.TRANSFER_BATCH: "erc1155_transfer",
          B.V1_FILL: "order_filled", B.V2_FILL: "order_filled"}


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if ts else ""


def load_cache(p, default):
    return json.loads(gzip.decompress(p.read_bytes())) if p.exists() else default


def write_csv(path, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n", extrasaction="ignore")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    data = buf.getvalue().encode()
    if path.suffix == ".gz":
        with gzip.GzipFile(path, "wb", mtime=0) as g:
            g.write(data)
    else:
        path.write_bytes(data)
    return hashlib.sha256(path.read_bytes()).hexdigest()


def market_maps(markets, resolutions):
    cond_of, info = {}, {}
    for t, m in markets.get("tokens", {}).items():
        if m["condition_id"]:
            cond_of[(B.CTF, int(t))] = (m["condition_id"], m["outcome_index"], m["outcome"])
            info[m["condition_id"]] = m
    payout = {c: (v["payout_numerators"], v["denominator"]) for c, v in resolutions.get("conditions", {}).items()
              if v["denominator"]}
    return cond_of, info, payout


MAX_BYTES = 24_000_000  # the repository refuses files over 25 MB


def to_parquet(csv_gz, pq, order, exclude=()):
    """One Parquet file, or numbered parts split by account (sorted) when one file would exceed MAX_BYTES.
    Returns {published name: sha256}."""
    import duckdb
    cols = f"* EXCLUDE ({', '.join(exclude)})" if exclude else "*"
    src = f"(SELECT {cols} FROM read_csv('{csv_gz}', all_varchar=true))"
    for old in pq.parent.glob(pq.stem + "*.parquet"):
        old.unlink()
    duckdb.sql(f"COPY (SELECT * FROM {src} ORDER BY {order}) TO '{pq}' (FORMAT PARQUET, COMPRESSION ZSTD)")
    size = pq.stat().st_size
    if size <= MAX_BYTES:
        return {pq.name: hashlib.sha256(pq.read_bytes()).hexdigest()}
    pq.unlink()
    k = -(-size // (MAX_BYTES * 3 // 4))
    accounts = [r[0] for r in duckdb.sql(f"SELECT DISTINCT account FROM {src} ORDER BY account").fetchall()]
    out = {}
    for i in range(k):
        group = accounts[i * len(accounts) // k:(i + 1) * len(accounts) // k]
        part = pq.with_name(f"{pq.stem}.part{i + 1}of{k}.parquet")
        inlist = ", ".join(f"'{a}'" for a in group)
        duckdb.sql(f"COPY (SELECT * FROM {src} WHERE account IN ({inlist}) ORDER BY {order}) "
                   f"TO '{part}' (FORMAT PARQUET, COMPRESSION ZSTD)")
        if part.stat().st_size > MAX_BYTES:
            raise RuntimeError(f"{part.name} still exceeds the size policy")
        out[part.name] = hashlib.sha256(part.read_bytes()).hexdigest()
    return out


def build(raw, src, results, archived_pnl=None, traders=None, local=None):
    """local: folder for the full CSV tables that exceed the repository's file-size policy (default: results)."""
    t0 = time.time()
    plan, coverage, logs, problems = B.load(raw)
    recs, unknown = B.account_txs(logs, plan["accounts"])
    markets = load_cache(src / "markets.json.gz", {"tokens": {}, "missing": []})
    resol = load_cache(src / "resolutions.json.gz", {"conditions": {}, "queried": []})
    bal = load_cache(src / "balances.json.gz", {})
    act = load_cache(src / "activity.json.gz", {"accounts": {}})
    cond_of, info, payout = market_maps(markets, resol)
    mk = load_cache(src / "marks.json.gz", {"tokens": {}})
    marks = {(B.CTF, int(t)): {"price": v["price"], "source": "CLOB prices-history",
                               "time_utc": iso(v["point_ts"]) if v["point_ts"] else ""}
             for t, v in mk["tokens"].items() if v["price"] is not None}
    pos, market_cash, flags, fills_ct, wallet, ledger = B.book(recs, cond_of, payout, marks)
    results.mkdir(parents=True, exist_ok=True)
    local = local or results
    local.mkdir(parents=True, exist_ok=True)
    out_hash, failures = {}, []

    # ---- canonical fills table
    fill_rows = []
    for r in recs.values():
        for f in r["fills"]:
            k = (f["position_contract"], f["token"]) if f["token"] is not None else None
            c = cond_of.get(k) if k else None
            fill_rows.append({
                "chain_id": 137, "block": r["block"], "time_utc": iso(r["ts"]), "tx": r["tx"],
                "log_index": f["log_index"], "exchange": f["exchange"], "version": f["version"],
                "account": r["account"], "role": "taker" if f["taker"] == f["exchange"] else "maker",
                "counterparty_field": f["taker"], "order_hash": f["order_hash"], "side": f["side"],
                "token_id": str(f["token"]), "condition_id": c[0] if c else "", "outcome": c[2] if c else "",
                "shares": B.fmt(Fraction(f["shares"])), "cash": B.fmt(Fraction(f["cash"])),
                "fee_nominal": B.fmt(Fraction(f["fee"])),
                "price": f"{Fraction(f['cash'], f['shares']).__float__():.6f}" if f["shares"] else ""})
    fill_rows.sort(key=lambda x: (x["block"], x["log_index"], x["account"]))
    out_hash["wallet_fills.csv.gz"] = write_csv(local / "wallet_fills.csv.gz", fill_rows, list(fill_rows[0]) if fill_rows else ["tx"])

    # ---- leg ledger
    for row in ledger:
        c = cond_of.get((row["position_contract"], int(row["token_id"])))
        row["outcome"] = c[2] if c else ""
        row["time_utc"] = iso(row["ts"])
        row["share_delta"] = B.fmt(Fraction(row["share_delta"]))
    lf = ["account", "market", "outcome", "position_contract", "token_id", "tx", "block", "time_utc", "kinds", "leg",
          "share_delta", "cash_delta"]
    out_hash["wallet_position_ledger.csv.gz"] = write_csv(local / "wallet_position_ledger.csv.gz", ledger, lf)
    try:
        # order hash and counterparty field are not part of a fill's identity (chain, block, tx, log index,
        # contract); they stay in the full local table so the published one fits the size policy
        out_hash.update(to_parquet(local / "wallet_fills.csv.gz", results / "wallet_fills.parquet",
                                   "CAST(block AS BIGINT), CAST(log_index AS INTEGER), account",
                                   exclude=("order_hash", "counterparty_field")))
        out_hash.update(to_parquet(local / "wallet_position_ledger.csv.gz", results / "wallet_position_ledger.parquet",
                                   "CAST(block AS BIGINT), tx, account, token_id"))
    except ImportError:
        failures.append({"check": "parquet_export", "status": "SKIPPED", "reason": "duckdb not importable"})

    # ---- per (account, market)
    rows, identity_bad = [], 0
    totals = defaultdict(Fraction)
    for (a, mk), toks in sorted(pos.items()):
        inv_value, source = B.value_inventory(toks, cond_of, payout, marks)
        cash = market_cash[(a, mk)]
        realized = sum((p.realized for p in toks.values()), Fraction(0))
        out_cost = sum((p.transfer_out_cost for p in toks.values()), Fraction(0))
        remaining = sum((p.cost for p in toks.values()), Fraction(0))
        unreal = None if inv_value is None else inv_value - remaining
        net = None if inv_value is None else cash + inv_value
        trading = None if net is None else realized + unreal   # = net + transfer_out_cost
        ok = None if net is None else (realized + unreal - out_cost == net)  # arithmetic self-check only
        if ok is False:
            identity_bad += 1
        m = info.get(mk, {})
        status = "RESOLVED" if mk in payout else ("UNKNOWN_MARKET" if mk.startswith("token:") else "OPEN_OR_UNRESOLVED")
        inv = ";".join(f"{(cond_of.get(k) or (None, None, str(k[1])))[2]}:{B.fmt(Fraction(p.qty))}"
                       for k, p in sorted(toks.items()) if p.qty)
        fl = flags.get((a, mk), {})
        if any(p.negative_inventory for p in toks.values()):
            fl = dict(fl, NEGATIVE_INVENTORY=1)
        fc = fills_ct.get((a, mk), {})
        first = min((p.first_entry for p in toks.values() if p.first_entry), default=None)
        row = {
            "account": a, "market": mk, "question": m.get("question", ""), "slug": m.get("slug", ""),
            "neg_risk": m.get("neg_risk", ""), "status": status,
            "payout": "/".join(map(str, payout[mk][0])) if mk in payout else "",
            "fills": fc.get("fills", 0), "buy_fills": fc.get("buy_fills", 0), "sell_fills": fc.get("sell_fills", 0),
            "first_entry_utc": iso(first) if first else "",
            "shares_bought": B.fmt(Fraction(sum(p.bought for p in toks.values()))),
            "shares_sold": B.fmt(Fraction(sum(p.sold for p in toks.values()))),
            "split_shares": B.fmt(Fraction(sum(p.split_in for p in toks.values()))),
            "merged_shares": B.fmt(Fraction(sum(p.merged_out for p in toks.values()))),
            "redeemed_shares": B.fmt(Fraction(sum(p.redeemed for p in toks.values()))),
            "transfer_in_shares": B.fmt(Fraction(sum(p.transfer_in for p in toks.values()))),
            "transfer_out_shares": B.fmt(Fraction(sum(p.transfer_out for p in toks.values()))),
            "buy_cash": B.fmt(sum((p.buy_cash for p in toks.values()), Fraction(0))),
            "sell_cash": B.fmt(sum((p.sell_cash for p in toks.values()), Fraction(0))),
            "fee_v2_v3_paid": B.fmt(Fraction(sum(p.fees for p in toks.values()))),
            "fee_nominal_all": B.fmt(Fraction(fc.get("fee_nominal", 0))),
            "remaining_inventory": inv, "inventory_value": B.fmt(inv_value), "valuation_source": source,
            "cash_pnl": B.fmt(cash), "realized_pnl": B.fmt(realized), "unrealized_pnl": B.fmt(unreal),
            "transfer_out_cost": B.fmt(out_cost), "net_position_pnl": B.fmt(net), "trading_pnl": B.fmt(trading),
            "identity_check": {True: "PASS", False: "FAIL", None: "NOT_EVALUATED"}[ok],
            "flags": "|".join(f"{k}:{v}" for k, v in sorted(fl.items())),
        }
        rows.append(row)
        totals["cash_pnl"] += cash
        if net is not None:
            totals["net_known"] += net
    sf = list(rows[0]) if rows else ["account"]
    out_hash["wallet_position_summary.csv.gz"] = write_csv(results / "wallet_position_summary.csv.gz", rows, sf)

    # ---- per account
    per = defaultdict(lambda: Counter())
    nets = defaultdict(Fraction)
    for r in rows:
        a = r["account"]
        per[a]["markets"] += 1
        per[a][r["status"]] += 1
        per[a]["fills"] += r["fills"]
        if r["trading_pnl"] != "UNKNOWN":
            nets[a] += Fraction(r["trading_pnl"]) / B.SIX
        else:
            per[a]["unknown_valuation_markets"] += 1
        if r["flags"]:
            per[a]["flagged_markets"] += 1
    cash_by = defaultdict(lambda: defaultdict(int))
    for r in recs.values():
        for tok, v in r["cash"].items():
            cash_by[r["account"]][tok] += v
    wrows, no_code = [], [0]
    for a in plan["accounts"]:
        rec = {"account": a}
        if traders:
            rec["records_in_pm_traders"] = len(traders.get(a, []))
            rec["account_type"] = "|".join(sorted({t["account_type"] for t in traders.get(a, [])}))
        rec.update(markets=per[a]["markets"], fills=per[a]["fills"], resolved=per[a]["RESOLVED"],
                   open_or_unresolved=per[a]["OPEN_OR_UNRESOLVED"], unknown_market=per[a]["UNKNOWN_MARKET"],
                   unknown_valuation_markets=per[a]["unknown_valuation_markets"],
                   flagged_markets=per[a]["flagged_markets"],
                   trading_pnl_known=B.fmt(nets[a]) if per[a]["markets"] else "0.000000",
                   trading_pnl_status="COMPLETE" if not per[a]["unknown_valuation_markets"] else "PARTIAL",
                   non_trading_cash_in=B.fmt(Fraction(wallet[a]["non_trading_cash_in"])),
                   non_trading_cash_out=B.fmt(Fraction(wallet[a]["non_trading_cash_out"])))
        # collateral reconciliation: sum of deltas == balance(end) - balance(start-1), per token
        col = bal.get("collateral")
        if col:
            res = []
            for tok in B.COLLATERAL:
                b0 = col.get(f"{a}|{tok}|{plan['start_block'] - 1}")
                b1 = col.get(f"{a}|{tok}|{plan['end_block']}")
                no_code[0] += (b0 == "NO_CODE") + (b1 == "NO_CODE")
                b0, b1 = (0 if b == "NO_CODE" else b for b in (b0, b1))
                d = cash_by[a].get(tok, 0)
                okc = b0 is not None and b1 is not None and b1 - b0 == d
                res.append(okc)
                if not okc:
                    failures.append({"check": "collateral_balance", "account": a, "token": B.COLLATERAL[tok],
                                     "status": "FAIL", "expected": b1 - b0 if None not in (b0, b1) else "",
                                     "observed_sum_of_deltas": d, "reason": "sum of collateral transfers differs "
                                     "from the on-chain balance change over the window"})
            rec["collateral_reconciled"] = "PASS" if all(res) else "FAIL"
        else:
            rec["collateral_reconciled"] = "NOT_RUN"
        if archived_pnl is not None:
            rec["archived_total_pnl_pm_pnl2"] = archived_pnl.get(a, "")
        a_act = act.get("accounts", {}).get(a)
        if a_act and a_act.get("status") != "EXHAUSTED":
            rec["api_status"] = a_act.get("status")   # a truncated API history is never compared as complete
        elif a_act:
            rec["api_status"] = "EXHAUSTED"
            trade_tx = {x["tx"] for x in a_act["rows"] if x["type"] == "TRADE"}
            chain_tx = {r["tx"] for r in recs.values() if r["account"] == a and r["fills"]}
            rec["api_trade_rows"] = sum(1 for x in a_act["rows"] if x["type"] == "TRADE")
            rec["api_trade_txs"] = len(trade_tx)
            rec["chain_fill_txs"] = len(chain_tx)
            rec["api_txs_missing_on_chain"] = len(trade_tx - chain_tx)
            rec["chain_txs_missing_in_api"] = len(chain_tx - trade_tx)
            if trade_tx - chain_tx:
                failures.append({"check": "api_trades_on_chain", "account": a, "status": "FAIL",
                                 "expected": len(trade_tx), "observed_sum_of_deltas": len(trade_tx & chain_tx),
                                 "reason": "Data API TRADE transactions without a cohort OrderFilled in the "
                                           "collected logs"})
        wrows.append(rec)
    out_hash["wallet_summary.csv"] = write_csv(results / "wallet_summary.csv", wrows, list(wrows[0]))

    # ---- independent checks (not true by construction)
    redeem = Counter()
    resid = Counter()
    for r in recs.values():
        ks = set(r["kinds"])
        cash = sum(r["cash"].values())
        if ks & {"REDEEM", "BURN_FOR_COLLATERAL"} and r["shares"] and all(v < 0 for v in r["shares"].values()):
            exp, known = Fraction(0), True
            for k, ds in r["shares"].items():
                c = cond_of.get(k)
                pv = payout.get(c[0]) if c else None
                if not pv:
                    known = False
                    break
                exp += B.payout_units(-ds, pv, c[1])
            if not known:
                redeem["NOT_EVALUABLE"] += 1
            elif exp == cash:
                redeem["PASS"] += 1
            else:
                redeem["FAIL"] += 1
                failures.append({"check": "redeemed_cash_equals_payout_value", "account": r["account"], "token": r["tx"],
                                 "status": "FAIL", "expected": B.fmt(exp), "observed_sum_of_deltas": cash,
                                 "reason": "collateral received differs from the official payout value of the shares"})
        if "TRADE" in ks and set(r["kinds"]) == {"TRADE"}:
            e = sum(B.expected_cash(f) for f in r["fills"])
            versions = "+".join(sorted({f["version"] for f in r["fills"]}))
            resid[f"{versions}:{'zero' if cash == e else 'above' if cash > e else 'below'}"] += 1

    # ---- share balance sample
    pos_bal = bal.get("positions") or {}
    share_ok = share_bad = 0
    held = defaultdict(int)
    for r in recs.values():
        for k, v in r["shares"].items():
            held[(r["account"], k[0], k[1])] += v
    for key, onchain in sorted(pos_bal.items()):
        a, contract, tid, blk = key.split("|")
        mine = held.get((a, contract, int(tid)), 0)
        if mine == onchain:
            share_ok += 1
        else:
            share_bad += 1
            failures.append({"check": "position_balance", "account": a, "token": tid, "status": "FAIL",
                             "expected": onchain, "observed_sum_of_deltas": mine,
                             "reason": f"ERC-1155 balanceOf at block {blk} differs from the reconstructed inventory"})

    # ---- coverage by contract x month x family
    cov = Counter()
    for x in logs.values():
        fam = FAMILY.get(x["topics"][0] if x["topics"] else "", None)
        if fam is None:
            fam = B.EVENTS.get(x["topics"][0], ("other",))[0].lower() if x["topics"] else "other"
        cov[(x["address"], iso(x["ts"])[:7], fam)] += 1
    crow = [{"chain_id": 137, "contract": c, "month": mth, "event_family": f, "provider": plan["provider"],
             "logs": n} for (c, mth, f), n in sorted(cov.items())]
    out_hash["coverage_by_contract.csv"] = write_csv(results / "coverage_by_contract.csv", crow,
                                                     ["chain_id", "contract", "month", "event_family", "provider", "logs"])
    mrow = []
    by_market = defaultdict(lambda: Counter())
    for r in rows:
        by_market[r["market"]]["accounts"] += 1
        by_market[r["market"]]["fills"] += r["fills"]
        by_market[r["market"]]["status:" + r["status"]] += 1
    for mk, c in sorted(by_market.items()):
        m = info.get(mk, {})
        mrow.append({"market": mk, "question": m.get("question", ""), "accounts": c["accounts"], "fills": c["fills"],
                     "resolved_on_chain": "YES" if mk in payout else "NO",
                     "gamma_closed": m.get("closed", ""), "gamma_outcome_prices": "/".join(m.get("gamma_outcome_prices", []))})
    out_hash["coverage_by_market.csv.gz"] = write_csv(results / "coverage_by_market.csv.gz", mrow,
                                                      list(mrow[0]) if mrow else ["market"])
    # Gamma vs on-chain payouts on resolved markets
    disagree = 0
    for mk, (nums, den) in payout.items():
        gp = info.get(mk, {}).get("gamma_outcome_prices") or []
        if gp and len(gp) == len(nums):
            if [Fraction(str(g)) for g in gp] != [Fraction(n, den) for n in nums]:
                disagree += 1
                failures.append({"check": "gamma_vs_chain_payout", "account": "", "token": mk, "status": "FAIL",
                                 "expected": "/".join(map(str, nums)), "observed_sum_of_deltas": "/".join(gp),
                                 "reason": "Gamma outcomePrices differ from the ConditionResolution payout vector"})
    out_hash["reconciliation_failures.csv"] = write_csv(
        results / "reconciliation_failures.csv", failures,
        ["check", "account", "token", "status", "expected", "observed_sum_of_deltas", "reason"])

    kinds = Counter(k for r in recs.values() for k in r["kinds"])
    resolved_cond = {mk for mk in by_market if mk in payout}
    summary = {
        "plan": {k: plan[k] for k in ("made_utc", "provider", "start_block", "end_block", "end_block_hash",
                                      "end_block_time_utc", "cohort_source", "cohort_records", "cohort_csv_sha256")},
        "accounts_in_cohort": len(plan["accounts"]),
        "accounts_with_any_log": len({r["account"] for r in recs.values()}),
        "accounts_with_fills": len({r["account"] for r in recs.values() if r["fills"]}),
        "accounts_with_positions": len({a for a, _ in pos}),
        "stream_coverage": coverage,
        "all_streams_complete": all(v["complete"] for v in coverage.values()) and len(coverage) == 7 * (
            -(-len(plan["accounts"]) // plan["chunk_size"])),  # seven filters per account chunk
        "unique_logs": len(logs), "load_problems": problems[:50], "load_problem_count": len(problems),
        "unknown_topic_logs": sum(unknown.values()),
        "account_transactions": len(recs), "transaction_kinds": dict(kinds),
        "fills": len(fill_rows),
        "fills_by_version": dict(Counter(f["version"] for f in fill_rows)),
        "markets": {"account_market_positions": len(rows), "distinct_markets": len(by_market),
                    "resolved_on_chain": len(resolved_cond),
                    "unknown_market_tokens": sum(1 for mk in by_market if mk.startswith("token:"))},
        "gamma": {"tokens_known": len(markets.get("tokens", {})), "tokens_missing": len(markets.get("missing", []))},
        "checks": {
            "identity_fail": identity_bad,
            "identity_pass": sum(1 for r in rows if r["identity_check"] == "PASS"),
            "identity_not_evaluated": sum(1 for r in rows if r["identity_check"] == "NOT_EVALUATED"),
            "collateral_reconciled_accounts": sum(1 for r in wrows if r.get("collateral_reconciled") == "PASS"),
            "collateral_failed_accounts": sum(1 for r in wrows if r.get("collateral_reconciled") == "FAIL"),
            "position_balance_sample_pass": share_ok, "position_balance_sample_fail": share_bad,
            "gamma_vs_chain_payout_disagreements": disagree,
            "redeemed_cash_vs_payout_value": dict(redeem),
            "trade_cash_vs_fill_rules": dict(resid),
            "collateral_reads_without_contract_code": no_code[0],
        },
        "resolutions": {"conditions_in_markets": len({m["condition_id"] for m in markets.get("tokens", {}).values()
                                                      if m["condition_id"]}),
                        "conditions_queried": len(resol.get("queried", [])),
                        "conditions_resolved": len(resol.get("conditions", {}))},
        "exchange_v3": {"fills": sum(1 for f in fill_rows if f["version"] == "v3"),
                        "positions_unmapped": sum(1 for r in rows if r["market"].startswith("token:" + B.POSITION_MANAGER)),
                        "note": "PositionManager ids have their own numbering; unmapped V3 positions stay UNKNOWN"},
        "totals": {"cash_pnl_all_markets": B.fmt(totals["cash_pnl"]),
                   "net_pnl_markets_with_known_valuation": B.fmt(totals["net_known"]),
                   "positions_with_unknown_valuation": sum(1 for r in rows if r["net_position_pnl"] == "UNKNOWN")},
        "outputs_sha256": out_hash,
        "runtime_s": round(time.time() - t0, 1),
    }
    (results / "ledger_results.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
    return summary, rows, wrows


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", type=Path, required=True)
    ap.add_argument("--sources", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    ap.add_argument("--repo", type=Path, default=HERE.parents[2])
    ap.add_argument("--local", type=Path, help="folder for full CSV tables over the size policy (local only)")
    a = ap.parse_args()
    st = a.repo / "investigations/changenow-polymarket/sources/state"
    archived, traders = None, None
    if (st / "pm_pnl2.csv").exists():
        archived = {}
        for r in csv.DictReader(open(st / "pm_pnl2.csv")):
            archived.setdefault(r["account"].lower(), r["total_pnl"])
        traders = defaultdict(list)
        for r in csv.DictReader(open(st / "pm_traders.csv")):
            traders[r["account"].lower()].append(r)
    s, _, _ = build(a.raw, a.sources, a.results, archived, traders, a.local)
    print(json.dumps({k: s[k] for k in ("accounts_in_cohort", "accounts_with_fills", "fills", "markets", "checks",
                                        "totals", "all_streams_complete", "runtime_s")}, indent=1))


if __name__ == "__main__":
    main()
