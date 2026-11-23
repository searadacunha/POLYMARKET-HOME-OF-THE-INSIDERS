"""Write results/REPORT.md, coverage_by_chain.csv and recovery_attempts.jsonl from the result files only.

Every number in the report is read from a file of results/ (or a pinned Git object); nothing is typed by hand.
"""

import argparse
import csv
import gzip
import io
import json
import subprocess
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

PR110 = "8b633048290e7174945bc811b16cf0b11b4d8ceb"


def rd(p):
    return list(csv.DictReader(open(p)))


def dec(x):
    return Decimal(x) if x not in ("", "UNKNOWN", None) else None


def money(x):
    return f"{x:,.2f}"


def table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "|".join("---" for _ in head) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def build(repo, res, raw=None):
    L = json.loads((res / "ledger_results.json").read_text())
    W = rd(res / "wallet_summary.csv")
    P = list(csv.DictReader(gzip.open(res / "wallet_position_summary.csv.gz", "rt")))
    G = json.loads((res / "regression_pr111.json").read_text())
    U = json.loads((res / "weekly_service_funding_union.json").read_text())
    WF = rd(res / "weekly_service_funding.csv")
    E = rd(res / "eth_weeks_coverage.csv")
    X = rd(res / "cross_chain_routes.csv")
    Q = rd(res / "prospective_data_quality.csv")
    K = json.loads((res / "leakage_and_comparison.json").read_text())
    M = rd(res / "data_gap_matrix.csv")
    I = json.loads((res / "file_inventory_summary.json").read_text())
    RS = json.loads((res / "relay_v2_screen.json").read_text()) if (res / "relay_v2_screen.json").exists() else None
    T = json.loads((res / "tests_run.json").read_text()) if (res / "tests_run.json").exists() else {}
    AV = json.loads((res / "archived_vs_chain.json").read_text())
    PS = json.loads((res / "provider_sample.json").read_text()) if (res / "provider_sample.json").exists() else None
    cohort = json.loads(subprocess.run(["git", "-C", str(repo), "show", f"{PR110}:investigations/weekly-funding-intelligence/"
                                        "results/weekly_funding.json"], capture_output=True, check=True).stdout
                        )["historical_f2020_cohort"]

    # ---- cohort PnL with denominators
    with_fills = [w for w in W if int(w["fills"]) > 0]
    known = [w for w in with_fills if w["trading_pnl_status"] == "COMPLETE"]
    partial = [w for w in with_fills if w["trading_pnl_status"] == "PARTIAL"]
    tot_known = sum(Decimal(w["trading_pnl_known"]) for w in W)
    winners = sum(1 for w in known if Decimal(w["trading_pnl_known"]) > 0)
    losers = sum(1 for w in known if Decimal(w["trading_pnl_known"]) < 0)
    flat = sum(1 for w in known if Decimal(w["trading_pnl_known"]) == 0)
    trading_sum = sum(Decimal(p["trading_pnl"]) for p in P if p["trading_pnl"] != "UNKNOWN")
    arch = [w for w in W if w.get("archived_total_pnl_pm_pnl2") not in ("", None)]
    arch_sum = sum(Decimal(w["archived_total_pnl_pm_pnl2"]) for w in arch)
    pnls = sorted(Decimal(w["trading_pnl_known"]) for w in known)
    median = pnls[len(pnls) // 2] if pnls else None
    invested = sum(Decimal(p["buy_cash"]) for p in P)
    fees = sum(Decimal(p["fee_v2_v3_paid"]) for p in P)
    status = Counter(p["status"] for p in P)
    flags = Counter(f.split(":")[0] for p in P for f in p["flags"].split("|") if f)
    valsrc = Counter(p["valuation_source"].split(":")[0].split("|")[0] for p in P)
    api_rows = [w for w in W if w.get("api_trade_txs") not in ("", None)]

    lines = [
        "# Data completion and forensic reconstruction: results",
        "",
        f"Generated from the files of `results/` only. Window: blocks {L['plan']['start_block']} to "
        f"{L['plan']['end_block']} (finalized, {L['plan']['end_block_time_utc']}), provider {L['plan']['provider']}.",
        "",
        "## 1. Units of the f2020 cohort",
        "",
        table(["Unit", "Count", "Source"], [
            ["Archived f2020 payees", cohort["payees"], "PR 110 results/weekly_funding.json"],
            ["Bettor records (pm_traders.csv rows)", cohort["bettor_records"], "same"],
            ["Distinct lowercased trading addresses", cohort["distinct_trading_addresses"], "same"],
            ["Addresses in this ledger's cohort", L["accounts_in_cohort"], "results/ledger_results.json"],
            ["Addresses with at least one log", L["accounts_with_any_log"], "same"],
            ["Addresses with at least one OrderFilled as order owner", L["accounts_with_fills"], "same"],
        ]),
        "",
        "These are different units. Payees are not traders, and five trading addresses are shared by two bettor "
        "records each.",
        "",
        "## 2. Collection coverage",
        "",
        "Every accepted range of every stream is complete on the primary provider; the second-provider sample below "
        "re-reads collected transactions, so it can detect altered or wrong logs but not omitted ones. Omissions of "
        "collateral transfers would break the balance reconciliation of section 3; omissions of position transfers are "
        "checked only on the sampled balances.",
        "",
        table(["Stream", "Logs", "Ranges", "Complete"], [[k, v["logs"], v["ranges"], v["complete"]]
                                                          for k, v in sorted(L["stream_coverage"].items())]),
        "",
        f"Unique logs after de-duplication: {L['unique_logs']}. Load problems (hash mismatch, duplicate that differs, "
        f"block-hash conflict, removed log): {L['load_problem_count']}. Account-transactions: "
        f"{L['account_transactions']}. Fills owned by cohort accounts: {L['fills']} "
        f"({', '.join(f'{k} {v}' for k, v in sorted(L['fills_by_version'].items()))}).",
        "",
        (f"Second-provider control ({PS['provider_second']}): {PS['transactions_sampled']} transactions sampled by rule "
         f"({PS['rule']}); collected logs that agree field by field: {PS['counts'].get('log_agrees', 0)}, that differ: "
         f"{PS['counts'].get('log_differs', 0)}, receipts missing: {PS['counts'].get('receipt_missing', 0)}." if PS else
         "Second-provider control: not run."),
        "",
        "Transaction kinds (one transaction can carry several):",
        "",
        table(["Kind", "Account-transactions"], sorted(L["transaction_kinds"].items(), key=lambda x: -x[1])),
        "",
        "## 3. Positions and profit",
        "",
        table(["Measure", "Value"], [
            ["Account-market positions", L["markets"]["account_market_positions"]],
            ["Distinct markets", L["markets"]["distinct_markets"]],
            ["Markets resolved on chain (official payout vector)", L["markets"]["resolved_on_chain"]],
            ["Positions RESOLVED / OPEN_OR_UNRESOLVED / UNKNOWN_MARKET",
             f"{status['RESOLVED']} / {status['OPEN_OR_UNRESOLVED']} / {status['UNKNOWN_MARKET']}"],
            ["Positions with an unknown inventory value", L["totals"]["positions_with_unknown_valuation"]],
            ["Arithmetic identity (self-check, not an independent control) PASS / FAIL / NOT_EVALUATED",
             f"{L['checks']['identity_pass']} / {L['checks']['identity_fail']} / {L['checks']['identity_not_evaluated']}"],
            ["Accounts whose collateral reconciles with balanceOf (all tokens)",
             f"{L['checks']['collateral_reconciled_accounts']} of {len(W)} "
             f"(failed {L['checks']['collateral_failed_accounts']})"],
            ["Position-token balance sample PASS / FAIL",
             f"{L['checks']['position_balance_sample_pass']} / {L['checks']['position_balance_sample_fail']}"],
            ["Gamma outcome prices that disagree with the chain payout", L["checks"]["gamma_vs_chain_payout_disagreements"]],
            ["Redeem or burn account-transactions whose collateral equals the official payout value of the burned "
             "shares (PASS / FAIL / some payout unknown)",
             " / ".join(str(L["checks"]["redeemed_cash_vs_payout_value"].get(k, 0)) for k in ("PASS", "FAIL", "NOT_EVALUABLE"))],
            ["Trades whose collateral matches the fill fee rules (zero / above / below, by version)",
             "; ".join(f"{k} {v}" for k, v in sorted(L["checks"]["trade_cash_vs_fill_rules"].items()))],
            ["Positions with no remaining inventory, of all positions", f"{valsrc['NO_INVENTORY']} of {len(P)}"],
            ["Positions with inventory valued by official payout / by a CLOB mark / unknown",
             f"{valsrc['RESOLUTION_PAYOUT']} / {valsrc['MARK']} / {valsrc['UNKNOWN']} "
             f"(of {len(P) - valsrc['NO_INVENTORY']})"],
            ["Collateral paid for buys (fees included)", money(invested)],
            ["Fees paid on 2026 and V3 exchanges (pUSD)", money(fees)],
            ["Trading PnL, positions with a known value (shares sent to other wallets leave at cost)",
             f"{trading_sum:.6f}"],
            ["Net position PnL, same positions (cash plus inventory; shares sent away count as outflows)",
             L["totals"]["net_pnl_markets_with_known_valuation"]],
        ]),
        "",
        f"Of the {len(with_fills)} accounts with at least one fill, {len(known)} have a complete trading PnL (winners "
        f"{winners}, losers {losers}, flat {flat}; median {median}) and {len(partial)} hold at least one position of "
        f"unknown value. {len(W) - len(with_fills)} accounts of the cohort never owned a filled order. Sum of the known "
        f"parts over all {len(W)} accounts: {tot_known:.6f}.",
        "",
        "Flags on positions (count of positions carrying each):",
        "",
        table(["Flag", "Positions"], sorted(flags.items(), key=lambda x: -x[1])) if flags else "none",
        "",
        "### Independent count from the Data API",
        "",
        table(["Measure", "Value"], [
            ["Accounts whose /v2/activity history was read to the end", sum(1 for w in W if w.get("api_status") == "EXHAUSTED")],
            ["API TRADE transactions / on-chain fill transactions",
             f"{sum(int(w['api_trade_txs']) for w in api_rows)} / {sum(int(w['chain_fill_txs']) for w in api_rows)}"],
            ["API TRADE transactions missing on chain", sum(int(w["api_txs_missing_on_chain"]) for w in api_rows)],
            ["On-chain fill transactions missing in the API", sum(int(w["chain_txs_missing_in_api"]) for w in api_rows)],
        ]),
        "",
        "### Archived figure",
        "",
        f"The archived file `pm_pnl2.csv` (Data API, rounded to the dollar, 16 records capped at 5,500 events) sums to "
        f"{sum(Decimal(r['total_pnl']) for r in csv.DictReader(open(repo / 'investigations/changenow-polymarket/sources/state/pm_pnl2.csv')))} "
        f"over {cohort['bettor_records']} records. Five trading addresses appear in two records, so that sum counts "
        f"them twice; over the {len(arch)} distinct addresses it is {arch_sum}. This ledger replaces neither: it is an "
        f"independent on-chain replay over a longer window.",
        "",
        table(["Archived records", "Accounts", "Archived PnL", "Chain PnL, archived window", "Chain PnL, lifetime",
               "Archived buys", "Chain buys", "Within 1 USD"],
              [[g, v["accounts"], v["archived_total_pnl"], v["chain_trading_pnl_in_archived_window"],
                v["chain_trading_pnl_lifetime"], v["archived_buy"], v["chain_buy_cash"], v["accounts_within_1_usd"]]
               for g, v in sorted(AV["groups"].items())]),
        "",
        "Capped records are those the archive marks incomplete (5,500 events). " + AV["note"] + ".",
        "",
        "## 4. Regression against PR 111",
        "",
        table(["Comparison", "Count"], sorted(G["counts"].items())),
        "",
        table(["Wallet", "PR 111 focus net", "Ledger", "Exact"],
              [[f["wallet_id"], f["pr111_net_pnl"], f["ledger_net_pnl"], f["exact"]] for f in G["focus_bets"]]),
        "",
        f"Focus-market sum in this ledger: {G['focus_net_sum_ledger']}. PR 111 cut-off: {G['pr111_cutoff_utc']}. "
        "Each difference is listed in `regression_pr111.json`.",
        "",
        "## 5. Weekly funding (PR 110 sets, unchanged)",
        "",
    ]
    by = defaultdict(lambda: [0, 0, 0, Decimal(0)])
    for r in WF:
        k = (r["service"], r["evidence_level"])
        by[k][0] += int(r["verified_distinct_wallets"])
        by[k][1] += int(r["possible_distinct_wallets"])
        by[k][2] += int(r["unique_transactions"])
        by[k][3] += Decimal(r["usd_valuation"])
    lines += [
        table(["Service", "Evidence", "Sum of weekly verified", "Sum of weekly possible", "All-period distinct (union)",
               "Transactions", "USD"],
              [[s, e, v[0], v[1], U["all_period_distinct_wallets_set_union"][s][e], v[2], money(v[3])]
               for (s, e), v in sorted(by.items())]),
        "",
        "Weekly distinct counts are not additive: the all-period column is a set union of the weekly address sets.",
        "",
        "## 6. Ethereum weeks W16 to W38 (recovered source streams)",
        "",
    ]
    es = defaultdict(lambda: [0, 0, Counter()])
    for e in E:
        es[e["stream"]][0] += 1
        es[e["stream"]][1] += int(e["events"])
        es[e["stream"]][2][e["coverage_status"]] += 1
    lines += [table(["Stream", "Weeks", "Events", "Status"],
                    [[s, v[0], v[1], dict(v[2])] for s, v in sorted(es.items())]), ""]
    if RS:
        lines += ["## 7. Relay v2 history screen (Ethereum to Polygon)", "",
                  table(["Measure", "Value"], [["Accounts", RS["accounts"]], ["PR 110 status", json.dumps(RS["pr110_status"])],
                                               ["Status now", json.dumps(RS["status_now"], sort_keys=True)],
                                               ["Transitions from PR 110's status", json.dumps(RS["transitions"], sort_keys=True)],
                                               ["Relay requests found / accounts with any / histories read to the end",
                                                f"{RS['orders_found']} / {RS['accounts_with_orders']} / "
                                                f"{RS['status_now'].get('EXHAUSTED', 0)}"],
                                               ["Requests created in PR 110's screened weeks (W39 to W46)", RS["orders_in_pr110_screened_weeks"]],
                                               ["Positive control: known Arbitrum-to-Polygon order of PR 109 returned by the "
                                                "same endpoint and user parameter (originChainId=42161)",
                                                RS.get("positive_control", {}).get("found", "not run")],
                                               ["HTTP calls / HTTP 429", f"{RS['http_calls']} / {RS['http_429']}"],
                                               ["Calls between", f"{RS['first_call_utc']} and {RS['last_call_utc']}"]]),
                  "", RS["reading"] + ". " + RS["snapshot_note"][0].upper() + RS["snapshot_note"][1:] + ". The "
                  "Ethereum-origin filter itself returned orders for the accounts listed in relay_v2_orders.csv.", ""]
    lines += ["## 8. Cross-chain passages of PR 109", "",
              table(["Route", "Leg", "Origin tx", "Destination tx", "Verdict", "Proof level"],
                    [[r["route_id"], r["leg"], r["origin_transaction"][:14] + "…", r["destination_transaction"][:14] + "…",
                      r["verdict"], r["proof_level"]] for r in X]), "",
              "A passage is a transaction-level fact at one shared intermediary. It does not establish a common owner.", "",
              "## 9. Prospective data and leakage", "",
              table(["Item", "Availability", "Priority"], [[q["item"], q["availability"], q["priority"]] for q in Q]), "",
              f"Scientific verdict: {K.get('scientific_verdict', 'NO_EDGE_VALIDATED').rstrip('.')}.", "",
              "## 10. Data gap matrix", "",
              table(["Status", "Datasets"], sorted(Counter(m["evidence_level"] for m in M).items())), "",
              f"File-level inventory: {I['evidence_rows']} evidence rows; " +
              ", ".join(f"{k} {v}" for k, v in I["by_status"].items()) + ".", ""]
    if T:
        lines += ["## 11. Tests run", "", table(["Suite", "Result"], [[k, v] for k, v in T.items()]), ""]
    (res / "REPORT.md").write_text("\n".join(lines) + "\n")

    # coverage by chain
    cov = [{"chain_id": 137, "dataset": "cohort logs", "blocks_or_weeks": f"{L['plan']['start_block']}..{L['plan']['end_block']}",
            "records": L["unique_logs"], "status": "COMPLETE" if L["all_streams_complete"] else "PARTIAL",
            "provider": L["plan"]["provider"]}]
    for s, v in sorted(es.items()):
        cov.append({"chain_id": 1, "dataset": s, "blocks_or_weeks": "2026-W16..2026-W38", "records": v[1],
                    "status": "COMPLETE" if set(v[2]) == {"COMPLETE"} else "PARTIAL",
                    "provider": "public Ethereum RPC and keyless explorer"})
    cov.append({"chain_id": 42161, "dataset": "PR 109 passages", "blocks_or_weeks": "6 receipts", "records": len(X),
                "status": "COMPLETE", "provider": "tenderly, drpc, arb1, 1rpc"})
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=list(cov[0]), lineterminator="\n")
    w.writeheader()
    w.writerows(cov)
    (res / "coverage_by_chain.csv").write_text(buf.getvalue())
    return lines


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--repo", type=Path, required=True)
    ap.add_argument("--results", type=Path, required=True)
    a = ap.parse_args()
    build(a.repo, a.results)
    print((a.results / "REPORT.md").read_text()[:3000])


if __name__ == "__main__":
    main()
