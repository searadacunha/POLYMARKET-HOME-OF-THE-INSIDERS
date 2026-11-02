# Capability gap analysis (read-only baseline)

**Date:** 2026-11-02. **Baseline main:** `9abeda91df2bc91aea1a83cbc7cbcb1b7326429d`. **Method:** reading the GitHub branch, core source modules and existing case reports. Neither Mac source directories nor the attached external drive are mounted here. No inference of live service health, local `git remote -v`, or disk free space is possible.

## Evidence baseline, unchanged

The central report contains **14 investigations and 89 classified findings**. Relevant documented results:

- Ballon d'Or: 11 named accounts; 46 deposits $304,137.63 and 25 withdrawals $493,094.76. This is gross flow, NOT profit. $129,367.79 is the settled-account subset.
- Financial transfer: `brace227` EOA pays `kraben006` EOA **0.002048944 ETH**, Ethereum tx `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98` (2026-10-04). Does not prove common control.
- Additional funded account: `brace227` pays **2,210 + 2,960 USDC** to `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d` (2026-10-09 and 10), whose relation to proxy `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5` is in the original report. Whether same owner is unresolved.
- ChangeNOW: `kraben006` receives **834.848793 USDC** from an address attributed to ChangeNOW; no order-level payin-payout match, no demonstrated path into its bets, and no XMR proof. A busy shared service wallet is specifically **not** a common-ownership link.
- Maduro/Iran: 8 accounts connected by funds; $151,084.40 external capital, $660,708.94 external outflows and calculated $509,993.25 PnL for that scope. Selected among large winners, so inference on rarity and private information is circular.
- Prospective: `Thin-Disclaimer-Life` conditional rank 1 in a small replay; **not** prioritized in the broader sealed S_A replay. Real counterfactual pre-publication capacity **NON_ESTIMABLE**. Eight preregistered historical trade signals failed to demonstrate executable out-of-sample edge.

Sources: [MASTER_REPORT](../../MASTER_REPORT.md), [METHODOLOGY](../../METHODOLOGY.md), [ballon-dor-flow-trace](../../investigations/ballon-dor-flow-trace/FINDINGS.md), [changenow-proof](../../investigations/changenow-proof/FINDINGS.md), [maduro-iran](../../investigations/maduro-iran/FINDINGS.md), [polysentinel](../../investigations/polysentinel/FINDINGS.md).

## Existing ability vs missing proof

| Requirement | Implemented baseline | Gap / risk | Proposed intervention |
|---|---|---|---|
| Bidirectional traced receipts | `signal_engine/fund_flow/trace.py`, `flows.py`, `links.py` and `ledger.py` | BSC/Base history, labels, fee/internal traces and cross-chain coverage not uniform; no full per-chain completeness proof | Bounded provider-independent retrieval with block ranges and completeness certificates |
| Wallet relations | `funding_graph.py`, Ballon d'Or `direct_links.py`, proof-level links | Service labels can contaminate common-funder features; unknown role is not an individual | New strict interchange `ledger.py` excludes service/unknown by construction |
| Shared-service and ChangeNOW flows | Proof and outflow protocols, false-positive controls | Attribution confidence and payer-to-payout internal mapping unavailable; 90-day scope bounded | Provider records only where public protocol identifiers link; stop at private ledger |
| Temporal coordination | `collective_behavior.py`, frozen tests and market tapes | Six systematic time windows and independent wallet-train null not a unified export; timestamp and taker selection uncertain | New `temporal.py` supplies read-only, explicitly exploratory six-window comparisons |
| Scored prospective alerts | PolySentinel frozen logic, hash-chained dossier | Coverage partial, closed markets, size filters, rotation and sleep; not prospectively validated | Measure coverage/gaps first, then shadow-only comparisons on new future events |
| V1/V2 transactions and pricing | Existing CTF/pUSD reconstructors and some V2 handling | Historic V1, April-2026 CLOB V2 and later protocol V2 must not share a schema without explicit era/range mapping | Event registry keyed by chain, address, ABI hash, block interval and settlement product; reconcile against receipts |
| PnL | Existing activity PnL and cash-out reconciliations | Partial history, cost basis, split/merge and actual settlement fees change meaning of profit | Per-asset inventory ledger and bounds; never derive realized PnL from deposits-minus-withdrawals alone |
| Dataset provenance | `data_manifest.json`, `EVIDENCE.md`, source hashes | Local-only raw files are not available through ordinary Git clone; hashes alone do not restore bytes | Content-addressed encrypted backup, verify actual restore and an independent replay |
| Statistical controls | Frozen plans, positive controls, multiple-testing registers | Post-hoc markets/winners, missing comparators and limited independent affairs | Predefine populations by trade participation and liquidity; block-permutation with sensitivity analysis |
| Graph export | Graph algorithms and JSON per investigation | No common schema carrying all minimum provenance fields into a single portable edge export | New financial CSV/JSON/GraphML bridge preserving transaction and evidence fields |

## Engineering evidence gates

- **Green for this branch:** read-only modular files, no runtime secrets, no RPC, deterministic fixture replay, exact raw-unit validation, 3 evidence graphs *as separate logical categories* (financial transfers, verified control, temporal resemblance).
- **Not green:** end-to-end collector integration, parity on 19 GB unpublished raw data, first-funding completeness, maker side/wallet attribution, balance/PnL reconciliation across all networks, real-time alert performance, full external replay and disk restore.
- The interchange is **EVM-only initially** because its transaction-hash validation assumes 32-byte EVM hashes. Solana/TRON need separate typed adapters, not a forced EVM address format.
- The GraphML export includes only confirmed financial edges and preserves all required fields. The behavioural outputs are separate records, **not a wallet-identity graph**.
- `log_index=null` for a native transfer is accepted, but multi-log ERC-20 records require an index for exhaustive event identity; missing indices mean completeness cannot be certified.

## Operational blockers

As of the backup report timestamp **2026-11-02 19:20 UTC**, 41,860 of 124,901 source files lacked two independently verified copies; 83,041 had GitHub-backed verification and 124,899 had external disk verification. This is a generated status snapshot, **not a direct disk audit**. Never delete, compress in place, reinstall or relocate original data to speed up this investigation.

The stored PolySentinel signal-engine status refused a run in reduced collector mode; `prospective_v2_status.json` recorded an interrupted state and 367 capture failures. These are snapshots, not a current process observation. Existing active processes must not be modified from this branch.

Sources: [BACKUP_STATUS](../../BACKUP_STATUS.md), [PolySentinel status](../../investigations/polysentinel/STATUS.md), [shared index](../../shared/README.md).

## Outcome of this stage

A narrow **tested capability gain** (validated data interchange + duplication guardrails + temporal window/null experiment) exists. **No increase in real-world insider detection rate is established**, and no claim of a newly traced wallet is made.


## Addendum: new gates versus unresolved gaps

A second pass on the isolated research branch hardened monetary deduplication, trade deduplication and coverage accounting. The added \`coverage.py\` provides **provider-reported range coverage only**. It does not prove the provider omitted no logs, and it cannot infer contract deployment ranges or ABI signatures from its caller's labels. Full V1/V2 compatibility remains unvalidated.

The \`source_ingest.py\` adapter reuses the archived ChangeNOW receipt table (30 rows, 22 ERC-20 and 8 native, three missing ERC-20 log indices) rather than recollecting the chain. Its \`protocol=None\` rule intentionally prevents a copied service label from becoming independent attribution. Actual replay of all 30 rows within Python against the user's original clone has not yet been performed.

The new tests demonstrate specific **engineering safeguards** and reveal no new insider, common wallet owner or service-internal payout. Separately, the old first-pass 13-test result remains historically accurate, but the current suite has 31 discovered tests (30 PASS / 1 SKIP in the isolated runtime). Details: [TOOLS_BENCHMARK.md](TOOLS_BENCHMARK.md).
