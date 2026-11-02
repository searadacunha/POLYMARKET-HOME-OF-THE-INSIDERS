# Next investigations — ranked by decisive evidence, not excitement

**Date:** 2026-11-02. Priorities are proposals, not actions performed. No paid service was invoked, no live process interrupted, and no user Mac/SSD path verified. All research must remain on isolated branches and retain every negative result.

| Rank | Question and available evidence | Necessary experiment / likely decisive evidence | Budget and stop criterion | Expected conclusion |
|---|---|---|---|---|
| **P0** | Are all cases recoverable? [Backup status](../../BACKUP_STATUS.md) reports 41,860 files without two verified copies at 19:20 UTC. | On the **Mac itself**, verify actual `git remote -v` and disk UUID/free space, `phi_audit.py`, GitHub encrypted pack restore in isolated directory, and SHA-256 on restore. Resolve backup PR #3 after review. | Zero new chain API queries; bounded temporary restore directory, require measured free disk and permission. Stop on any secret/index exposure. | Binary restore/coverage verdict; protect evidence first |
| **P0** | Are PolySentinel alerts complete and timely? The stored engine reports reduced mode, the prospective snapshot shows capture failures. | Local read-only health check: process state, missed block ranges, sealed decision timestamps, source snapshots, notification proof. No restart/threshold changes. | Local telemetry only; stop on agent interference. | Actual coverage intervals, not a claim of live insider detection |
| **P1** | Do V1 and 2026 V2 fills reconcile? Official CTF V2 introduces `side`, `tokenId`, `builder`, `metadata`; protocol V2 external adds different position architecture. | Versioned ABI/contract registry with deployment block intervals; confirm maker/taker, fees and collateral per chain on 10 preselected logged receipts; compare exact historical PnL. | Start 10 receipts, then scale only if parity passes. Zero trades. | Demonstrated completeness or specific missing-event schema defect |
| **P1** | Can full BSC/Base histories restore missing paths in Ballon d'Or and Maduro? Existing reports say incomplete. | Pilot read-only `hypersync-client-python` vs available RPC, fixed short block windows on known addresses, record source costs, traces and terminal gaps. | Provider/API price *unknown*; check allowances, cap requests and bytes **before** use. | New confirmed receipt links or documented provider visibility boundary |
| **P1** | Who funded the wallet `0xa8e64a3c…`? 5,170 USDC directly received from brace227 key. | Confirm `owner()` at historical block, upstream SwftSwap inputs and downstream withdrawals, including distinct signer/proxy accounts; compare against an independently sampled cohort of funded wallets. | Reuse already cached `flow-trace` data; target dozens, not a global crawl. | A transaction/protocol link, **not** a presumed human owner |
| **P1** | Does ChangeNOW have an identifiable per-order path? 834.848793 USDC to kraben key from attributed service address. | Independently audit hildobby/Etherscan label lineages, obtain protocol order IDs if public, compare complete payout windows and **negative transfer controls**. If no identifiers, stop at service. | Existing `changenow-proof`/`changenow-outflows` first; no speculative 1:1 temporal attribution. | Either new order-level proof or explicit OFFCHAIN_REQUIRED |
| **P1** | Does a prospective detector catch unusual wallets before public information? Conditional Ballon d'Or replay contradicts wider S_A. | Finish sealed S_C/S_G/S_B/S_L scenarios, then freeze the next future events and alerts; independent outcome/news timeline; model visibility and false alarms per 24h. | Local replays first; query budgets already prescribed in existing protocol. | Prospective *capacity* plus measurable missed-data/false-positive costs |
| **P2** | Are multi-wallet low-implied-price synchronized bets rare? Earlier funding/timing tests often refuted. | Market census selected before wins, strata by category, price, liquidity, market age and time; six windows, wallet-block permutations and event-level max-statistic. | Begin with one complete market family; no global 2026 crawl until observed coverage certification. | Calibrated anomaly frequency, **not** probability of insider trading |
| **P2** | Where do winning withdrawals go after Relay/DEX? First exits partially traced, 74% retained on first addresses on snapshot. | Trace only on public chain after last observed recipient; conservation per token; stop at exchange and record all uncertain allocations. Include native transfers and contract traces. | Known case addresses first, depth/tx/byte cap; cache by chain+block+hash. | Explicit terminal public addresses, no invented 'final beneficiary' |
| **P2** | Can multi-case source labels be trusted? Some KuCoin/Revolut/ChangeNOW tags derive from one lineage. | Label-source independence graph and historical snapshots, verify behavior apart from aliases, refuse combined labels if one dataset copied another. | Manual sampling; no need full GraphSense server. | Supported service attribution or downgrade |
| **P3** | Do optional DuckDB/Polars/NetworkX components outperform stdlib? | Benchmark identical cached fixture at 1k/100k/1M rows with memory limit and comparable outputs; compare against existing module. | Install in isolated venv after license and available disk check. | Adopt only if actual time/peak memory or completeness improves |

## External tool decisions

- **First verified engineering addition:** `ledger.py` + `temporal.py`, strict schema, basic financial graph, exploratory windows; 13 tests passed. This does **not** replace `fund_flow`.
- **Pilot after approvals/cost limits:** Polymarket PublicClient (`Polymarket/py-sdk`, MIT) and HyperSync (MPL-2.0), in read-only mode on already verified blocks.
- **Reference only:** Polymarket CTF V2/protocol V2 **BSL**, Relay kit, Circle CCTP contracts, GraphSense tags.
- **Blocked pending license or independent test:** `moose-code` no license, `poly_data` conflicting GPL/MIT, all unknown-label attribution; `vsbtc` retrospective winners-first score is not prospective proof.
- **Do not install by default:** Neo4j, full GraphSense, another Docker/Postgres/Redis detection service. Hardware capacity and measured marginal benefit not established.

## Acceptance tests before asking to merge

1. Exact-source transaction, receipt, block and log-index parity of known cases with external sources, on fixed inputs.
2. All six time windows and null-model comparisons on a frozen **non-winner-selected** market universe; report multiplicity and negative controls.
3. Full point-in-time coverage report by contract/block/chain and explicit treatment of missing logs/traces/price sources.
4. Real backfill/bridge/provider cost measurement; independent source comparison and retry logs.
5. Restore of external disk/GitHub backups verified **locally on the Mac**, without changing source directories.
6. Replay that leaves PolySentinel historical signed decisions and thresholds byte-identical.
7. Review external licenses and security; unit tests run in Mac arm64 isolated runtime; CI passes in the **research branch**.

## GitHub branch scope and local boundaries

This branch intentionally changes **only** `integrations/forensic-intelligence/`. It does not touch `investigations/*`, `scripts/backup/`, generated `MASTER_REPORT.md`, current collectors or `main`.

The GitHub connector can read the private central repo but cannot inspect mounted Mac volumes, running `launchd` agents or actual local Git remotes. Those requirements remain **PENDING_LOCAL**; do not mark them done based on `INVENTORY.md` path strings.

**Overall mission verdict: PARTIAL.** New reliable export/cross-wallet test plumbing is demonstrated; complete market-to-person money tracing, current collector reliability and empirically useful pre-publication detection remain unresolved.


## Follow-up order after the 31-test pass

1. **P0 — byte-level backup and Mac baseline:** restore actual source bytes under a new read-only mount from the existing verified packs, check origin remote with `git remote -v` on the Mac, free space by volume ID, and run the 31 tests. Do not assume a GitHub manifest implies a complete available archive. The source backup report still showed incomplete GitHub verification.
2. **P0 — deployment/ABI ledger for 2026:** obtain official receipt+code block evidence for historic V1, CTF Exchange V2 and Protocol V2 contracts, plus upgrades, and record actual start/end blocks; never copy BSL contract source into production. Then pilot `coverage.py` on one narrow historical contract+topic window.
3. **P0 — replay the actual 30-row ChangeNOW receipt CSV:** run `source_ingest.read_changenow_transfers` in the real clone, compare each hash/source/log to `node_proof_file`, and resolve 3 rows missing ERC-20 `log_index` by independent receipts. This is an audit of transfer identity, **not** payin-to-payout reconstruction.
4. **P1 — one-market prospective cohort census:** build a wallet population on actual trades before outcome, with event-window coverage and priced fill evidence, then compare six timing windows with pre-specified null models and multiple-test correction. No hindsight winners as starting population.
5. **P1 — bounded HyperSync and official Python SDK pilots:** pin exact versions, establish arm64 availability/API quotas and test on **already cached ranges**, comparing events and hashes to current code. Expanding into BSC/Base only after the missing historical range is documented.
6. **P2 — cross-chain and service provenance:** reconcile Relay, CCTP, Across and deBridge by actual message/order identifiers, and stop at internal ChangeNOW/CEX/Monero ledgers unless a specific off-chain record authorizes the link.

Resource estimates **remain not measured** without the Mac, external disk and provider quotas. Each pilot must output bytes processed, source hashes, requests, run time, peak RAM, completeness gaps, false-match controls and a documented negative result if no gain appears.
