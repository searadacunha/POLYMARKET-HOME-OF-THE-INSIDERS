# Counterparty-network investigation

Trace executed trading relationships on Polymarket without confusing counterparty links with funding links, ownership, or profitable information.

This investigation supplements the existing financial-flow cases. It does not replace their reports or change the root README.

## What is established

The published C7 Nobel archive records four transactions in which 6741 sold 53,355.91 shares for 30,514.17 USDC to fmaduro and madurowilllose. The amounts below are independently recalculated from the **existing archived CSV**, not from a new blockchain RPC read. They do not establish a new insider or beneficial-owner finding.

[Recalculated result](results/c7_reconciled.json) | [Findings](FINDINGS.md) | [Evidence](EVIDENCE.md) | [Status](STATUS.md)

Source archive: [C7 intra-group trades](../../research_notes/early-detection-2026-11-13/data/c7_intra_group_trades.csv) and [November 13 audit](../../AUDIT_20261113.md).

## Why add this line of investigation

A shared exchange or bridge does not establish common control. Executed counterparties offer a separate graph of **who traded against whom**, even when funding origins are unresolved.

This is not a novel claim about wash trading. Prior network-based research and independent implementations are assessed, with their uncertainties, in [source review](results/source_review.md). No external code or third-party dataset has been copied into this investigation. Published third-party headline percentages are not imported as findings.

## Investigative stages

1. **Execution edge**: an on-chain V2 maker-to-taker event, linked to its transaction, log index, token and timestamp. This proves an observed execution edge, not common ownership.
2. **Repeated relationship**: the same pair appears in distinct transactions or markets. Market-makers, service accounts, self-matches and contract-mediated legs must be identified before treating repetition as unusual.
3. **Funding intersection**: compare an execution edge against independently established direct funding or return flows. A shared service or exchange is never an ownership edge.
4. **Predictive test**: ask whether a network detected with information available at time T anticipates subsequent moves at an **executable** price and improves on the market-implied probability. No such result is claimed here.

These stages are investigative workflow stages, not replacements for CONFIRMED, SUPPORTED, HYPOTHESIS, REFUTED and UNRESOLVED.

## Reproduce

From the repository root, using Python 3.10+ and only the standard library:

    python3 investigations/counterparty-network/scripts/reconcile_c7.py --output /tmp/c7_reconciled.json
    python3 -m unittest discover -s investigations/counterparty-network/tests -v

The file [scripts/counterparty_graph.py](scripts/counterparty_graph.py) reads JSONL rows produced by the existing V2 chain decoder (fields include tx, log_index, exchange, wallet, counterparty, token_id, side, cash and ts), for example:

    python3 investigations/counterparty-network/scripts/counterparty_graph.py --input /path/to/decoded_fills.jsonl --output /tmp/counterparty_edges.json

The decoder input is **not provided** in this folder; no real-time surveillance and no historical universe-wide graph have been run by this addition. The summarizer rejects unsupported exchanges, strips the taker's exchange-address synthetic leg and counts distinct transaction hashes separately from fill legs. Same-side mint/merge matching is not automatically a buyer-to-seller share transfer.

[Prospective research protocol](results/analysis_plan.md) explains the missing out-of-sample study. It is a draft, **not a preregistered or successful test**.

## Scope and publication boundaries

- Standalone addition confined to this investigation folder. No change to root README, prior findings, publication baselines or other investigations.
- The four C7 rows are an archival accounting check. To promote this to independent chain confirmation, reread the four receipts and prove the maker/taker order linkage, token and settlement amounts against independent Polygon nodes.
- A counterparty, an associated funder, a common operator, private information, and a tradeable edge are different statements.
