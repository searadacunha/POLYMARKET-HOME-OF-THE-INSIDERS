#!/usr/bin/env python3
"""Offline integrity audit of the *published-source* KPMG/XFM case intake.

The outputs do NOT establish the underlying transfers or independently reproduce
Bitquery/MSR blockchain analyses. They audit the local source registry, including
all eleven reported handoffs, and nine advertised XFM receipt references.

Optional --market-csv recalculates a market-level Poisson-binomial tail from
USER-SUPPLIED per-market probabilities, NOT from a fabricated average.
No network, credentials, external dependencies or file mutations.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
HEX = re.compile(r"0x[0-9a-f]{40}$")
TX = re.compile(r"0x[0-9a-f]{64}$")
SOURCE_KPMG = "https://www.bitquery.io/investigations/polymarket-insider-trading-kpmg-clients"
SOURCE_XFM = "https://msrdecode.com/cases/xfm-paired-wallets.html"


def read_csv(name: str) -> list[dict[str, str]]:
    with (HERE / name).open(newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def validate_wallets() -> dict[str, object]:
    wallets = read_csv("KPMG_WALLETS.csv")
    if len(wallets) != 22:
        raise ValueError(f"Expected 22 KPMG-examined accounts; got {len(wallets)}")
    labels = [r["public_label"].strip().lower() for r in wallets]
    if len(set(labels)) != 22:
        raise ValueError("Duplicate KPMG pseudonym")
    core = {r["public_label"] for r in wallets if r["cohort_role"] == "ORIGINAL_19"}
    extra = {r["public_label"] for r in wallets if r["cohort_role"] == "EXPANDED_3"}
    if len(core) != 19 or extra != {"perlgrow", "boosthero", "bostonguy"}:
        raise ValueError("Core 19 vs expanded 3 roster drift")
    full = [r["polygon_proxy"] for r in wallets if r["polygon_proxy"]]
    if len(full) != 4 or len(set(full)) != 4 or any(not HEX.fullmatch(a) for a in full):
        raise ValueError("Four source-linked proxy addresses expected, no placeholders")
    if any(r["financial_edge_source"] != SOURCE_KPMG for r in wallets):
        raise ValueError("Uncited or changed public account source")
    return {"core": core, "all": {r["public_label"] for r in wallets}, "published_full_proxies": len(full)}


def validate_handoffs(core: set[str]) -> dict[str, object]:
    rows = read_csv("KPMG_HANDOFFS.csv")
    if len(rows) != 11:
        raise ValueError(f"Expected 11 reported handoffs; found {len(rows)}")
    unique = set()
    nodes = set()
    total = Decimal("0")
    for row in rows:
        src, dst = row["sender_label"], row["recipient_label"]
        if src not in core or dst not in core or src == dst:
            raise ValueError("Reported handoff references unknown or identical account")
        edge = (src, dst, row["calendar_day_utc"])
        if edge in unique:
            raise ValueError(f"Duplicated dated handoff {edge}")
        unique.add(edge)
        nodes.update((src, dst))
        datetime.strptime(row["calendar_day_utc"], "%Y-%m-%d")
        amount = Decimal(row["intermediate_receipt_usdc"])
        seconds = int(row["time_out_to_final_credit_seconds"])
        if amount <= 0 or not 0 < seconds <= 60:
            raise ValueError("Invalid amount or transfer interval")
        if row["evidence_class"] != "THIRD_PARTY_CROSS_CHAIN_RECONSTRUCTION":
            raise ValueError("Do not silently upgrade reported handoffs to local receipts")
        if row["primary_tx_replay"] != "PENDING":
            raise ValueError("Source-reported handoffs were not locally replayed")
        if row["source_url"] != SOURCE_KPMG:
            raise ValueError("Handoff lacks Bitquery provenance")
        total += amount
    if len(nodes) != 16 or total != Decimal("9176.85"):
        raise ValueError(f"16 distinct named nodes and $9,176.85 reported handoffs expected: {len(nodes)}, {total}")
    return {"reported_edges":len(rows), "named_core_nodes":len(nodes), "sum_of_intermediate_handoff_amounts_USDC_NOT_PROFIT":str(total)}


def validate_xfm() -> dict[str, object]:
    rows = read_csv("XFM_NINE_SPLITS.csv")
    if len(rows) != 9:
        raise ValueError("Expected 9 XFM advertised June 23 acquisitions")
    txs=set()
    wallet_labels=set()
    total=Decimal(0)
    for row in rows:
        if not TX.fullmatch(row["polygon_tx_hash"]) or row["polygon_tx_hash"] in txs:
            raise ValueError("XFM receipt hash malformed or duplicated")
        txs.add(row["polygon_tx_hash"])
        if row["yes_wallet_alias"] == row["no_wallet_alias"]:
            raise ValueError("Complementary accounts must differ")
        wallet_labels.update((row["yes_wallet_alias"], row["no_wallet_alias"]))
        if row["utc"][:10] != "2026-06-23":
            raise ValueError("Unexpected date in selected XFM acquisition receipts")
        datetime.fromisoformat(row["utc"].replace("Z","+00:00"))
        yes, no = Decimal(row["price_yes"]), Decimal(row["price_no"])
        if yes+no != Decimal("1"):
            raise ValueError("Source claims pair prices sum to exactly one unit")
        total += Decimal(row["shares_each"])
        if row["source_url"] != SOURCE_XFM or row["receipt_status"] != "MSR_PUBLISHED_RECEIPT_NOT_REDECODED_HERE":
            raise ValueError("Source receipt not independently verified: preserve evidence class")
    if total != Decimal("1779.93") or len(wallet_labels) != 18:
        raise ValueError(f"Expected 1,779.93 shares on each side and 18 names, got {total}, {len(wallet_labels)}")
    return {"published_transaction_hashes":len(txs),"paired_wallet_names":len(wallet_labels),"shares_on_each_side":str(total)}


def poisson_binomial_tail(probabilities: list[float], wins: int) -> float:
    """P(X >= wins) with each independent market i having its own input p_i."""
    if not probabilities or not 0<=wins<=len(probabilities):
        raise ValueError("Require a non-empty market set and valid observed wins")
    if any(not math.isfinite(p) or p<0 or p>1 for p in probabilities):
        raise ValueError("Invalid probability")
    dp=[1.0]+[0.0]*len(probabilities)
    for i,p in enumerate(probabilities,1):
        for k in range(i,0,-1):
            dp[k]=dp[k]*(1-p)+dp[k-1]*p
        dp[0]*=(1-p)
    return sum(dp[wins:])


def run_probability_fixture() -> None:
    assert abs(poisson_binomial_tail([0.5,0.5],2)-0.25)<1e-12
    assert abs(poisson_binomial_tail([0.1,0.9],1)-0.91)<1e-12
    assert abs(poisson_binomial_tail([0,1],2)-0)<1e-12
    for x in ([float("nan")], [1.1], [-0.1]):
        try:
            poisson_binomial_tail(x,1)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid probabilities were not rejected")


def analyze_user_markets(path: Path) -> None:
    with path.open(newline="",encoding="utf-8") as f:
        rows=list(csv.DictReader(f))
    if len(rows)!=21:
        raise ValueError("A rerun of KPMG's 21-market case needs 21 distinct market rows")
    ids=[r["condition_id"].lower() for r in rows]
    if len(set(ids))!=21 or any(not TX.fullmatch(i) for i in ids):
        raise ValueError("Market must be a distinct full condition ID")
    probabilities=[float(Decimal(r["paid_price_implied_probability"])) for r in rows]
    outcomes=[int(r["won"]) for r in rows]
    if any(n not in (0,1) for n in outcomes):
        raise ValueError("Each market contributes one binary resolution, not one per wallet")
    print("USER MARKETS",len(rows),"market-level wins",sum(outcomes),
          "expected wins",round(sum(probabilities),6),
          "P(at least this many wins | supplied per-market prices)",poisson_binomial_tail(probabilities,sum(outcomes)))
    print("CAUTION: this is a conditional model, not an insider probability or a multiple-testing correction.")


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--market-csv",type=Path,help="Optional independent 21-market conditionId,p_i,won file. None is supplied with this PR.")
    args=parser.parse_args()
    run_probability_fixture()
    roster=validate_wallets()
    handoffs=validate_handoffs(roster["core"])
    xfm=validate_xfm()
    print("PASS: Source-scope roster",len(roster["all"]),"accounts;",roster["published_full_proxies"],"full proxy IDs.")
    print("PASS: Reported cross-chain handoffs",handoffs)
    print("PASS: MSR-published XFM references",xfm)
    print("NOTE: No new RPC calls or SEC filing timestamp validation have been performed.")
    if args.market_csv:
        analyze_user_markets(args.market_csv)


if __name__ == "__main__":
    main()
