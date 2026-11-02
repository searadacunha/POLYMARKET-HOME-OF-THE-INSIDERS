# Forensic architecture — proposed, not deployed

**Scope:** architecture of a read-only, deterministic investigation system. Current integration is a small **offline adapter** (`ledger.py`, `temporal.py`, synthetic tests), not a replacement of the existing PolySentinel daemon. No remote services, wallets, node listeners or production databases were changed.

## End-to-end evidence path

```text
market/condition ID
  -> versioned Gamma/Data API market metadata + observation timestamp
  -> enumerated trading accounts [coverage by endpoint, direction, block, time]
  -> CLOB V1/V2 / protocol ABI mapping [chain, contract, deployed block interval]
  -> on-chain fills and settlements [dedup by chain + tx + log index]
  -> separate signer / EOA / Safe / deposit proxy / trading-account identities
  -> confirmed transfer receipts [native, ERC20, ERC1155, internal/traces]
  -> bounded backwards funding and forwards exits [per-chain history]
  -> explicit bridge message/order mapping [sender and destination verified]
  -> service visibility stop [CEX, change service, privacy boundary]
  -> financial graph + verified contract control graph + behavioral similarity graph
  -> market-price and liquidity **as observed before each decision**
  -> matched controls, null simulations, multiplicity and holdout analysis
  -> sealed report with counter-explanations and all unobserved coverage
```

A parallel **post-event analysis** may calculate resolved outcomes, PnL and subsequent price paths, but these must never enter a past prospective signal.

## Canonical ledger and graph semantics

The new EVM **interchange edge** requires `chain_id`, `transaction_hash`, `block_number`, UTC time, nullable `log_index`, sender/receiver, token address, decimals, raw integer amount, normalized decimal amount, optional supported USD valuation, protocol, evidence source, relation type, and evidence level.

- **Financial graph**: only observed transfers with receipts; each edge remains an asset-specific transfer, not proof of a person's control. Mint from zero is not a personal funder. A swap, bridge or relay can generate multiple observed legs but must not be presented as an identical token moving through an opaque service.
- **Control graph**: signer/owner, proxy/Safe or deposit-wallet relationships **read from an on-chain contract state/event at a specified block**. Code includes the `contract_control` edge type but no live owner resolver yet. No graph edges are fabricated.
- **Behavioral graph**: separately modeled wallet pairs sharing market/outcome and observed within 5/30/60/300/900/3600 seconds. Time resemblance never upgrades to a financial or control link. Comparators and null simulations are prerequisites to a `SUPPORT` conclusion.
- **Address roles**: `SERVICE`, `EXCHANGE`, `BRIDGE`, `OMNIBUS`, `CONTRACT`, `UNKNOWN`, or positively supported `PERSONAL_NONCUSTODIAL_CONFIRMED`. Unknown is **not** personal.
- **Evidence classes**: `ONCHAIN_CONFIRMED`, `PROTOCOL_LINK_CONFIRMED`, `SERVICE_INTERACTION`, `CANDIDATE`, `OFFCHAIN_REQUIRED`, `INSUFFICIENT_EVIDENCE`. Ownership always `NOT_ESTABLISHED` unless independently established by a contract (contract control is not human identity).

**Important limitation:** current `ledger.py` supports EVM transaction hashes. Non-EVM evidence, ERC-1155 token IDs, cross-chain message identities, trace address and block/reorg finality require typed extensions before declaring full multi-chain coverage.

## Retrieval, gaps and limits

- Use cached histories and local manifests first; do not recollect data available and hashed already.
- Each provider read must record provider/endpoint version, URL template (without secrets), request time, block range, requested filters, returned total, next cursor, dedup count, truncated/partial/error state, earliest/latest covered block, raw digest and chain finality.
- Backfills use bounded inclusive block intervals with explicit exclusive upper bound handling; paginate until exhaustion, then check gaps against confirmed events or an independent source. Preserve *missing* ranges as data.
- Timestamp rule: `block_timestamp` establishes chain ordering, `first_observed_at` governs whether the detector could have known it. Do not use the present Gamma catalogue to reconstruct a previous observation.
- USD valuations require a price source with recorded `observed_at <= trade_time`, named quote asset and confidence. pUSD/USDC/USDC.e/PMCT remain distinct token contracts, not synonyms.
- For an unknown previous transfer, never call the first observed activity a wallet creation event.
- For CEX deposits, private exchange routing, ChangeNOW internal orders or Monero privacy, stop at the exact public edge with `OFFCHAIN_REQUIRED` / `INSUFFICIENT_EVIDENCE`. Matching volume/time provides a *candidate*, with placebo collision rate.

## Polymarket 2026 compatibility: three eras to distinguish

1. **Historical CLOB V1/CTF**: legacy OrderFilled asset IDs and USDC.e collateral; legacy exchange and neg-risk contracts.
2. **CLOB V2 cutover April 28, 2026**: `CTFExchangeV2` at `0xE111180000d2663C0091e4f400237545B87B996B` and neg-risk `0xe2222d279d744050d28e00520010520000310F59` (Polygon, official CTF V2 source); the V2 fill has explicit side/tokenId plus builder/metadata, with pUSD wrapped collateral.
3. **Polymarket Protocol V2 external source**: separate `PositionManager`, router and position ID format. This repo describes additional deployed contracts; don't silently equate its architecture or order lifecycle to *all* April-October historical CLOB V2 transactions.

Authoritative inspected sources at pinned commits: [CTF Exchange V2](https://github.com/Polymarket/ctf-exchange-v2/blob/ccc0596074f4dfd62c944fbca4de252893b82b4b/README.md), [Protocol V2](https://github.com/Polymarket/polymarket-v2-external/blob/741f8bbe88c3f29a1c55d1248a3dd411f622f111/README.md). **BSL restrictions apply** to both codebases; use as ABI reference only. Confirm per-contract block deployment and exact event decoding before computing historical PnL. The CLOB V2 `OrderFilled` ordering and meaning is not the V1 event.

## Per-market outputs and operational requirements

A market dossier should have immutable: market/version/chain scope, traded accounts observed, missing makers and small trades, receipt hashes, ledger edges, separated graphs, temporal candidates, controls, selected null, significance corrected over all explored hypotheses, exits and service boundaries, unexplained dollars/coverage, possible false positives, provenance manifest, and the local **decision timestamp**.

Start with JSONL + CSV + GraphML and streaming DuckDB/Parquet only after a reproducible baseline. Neo4j/GraphSense full deployment is deferred. The present adapter exports GraphML and evidence tables but **not** a comprehensive multi-chain market dossier.

### Safety gates for any later rollout

- Offline sandbox and immutable input copies; no third-party code executed with the live Mac secrets.
- Read-only chain clients; explicit forbidden transaction/trading endpoints and no automatic token signing.
- Shadow-only output, zero mutation of scores, existing collectors or hashed historical decisions.
- Alert budget and coverage gates: a missing market or lag is an error, not evidence of no insider.
- Source archives, external disk free capacity and backup verification must be checked locally before any volume-intensive backfill.
- Per-chain provider budgets and audit logs, always resumable; no bypass of anti-bot/rate limits.

See [CAPABILITY_GAP_ANALYSIS](CAPABILITY_GAP_ANALYSIS.md) and [GITHUB_FORENSIC_DISCOVERY](GITHUB_FORENSIC_DISCOVERY.md).


## Implemented offline boundary and versioning gate (second pass)

The research branch now contains four stdlib components, still disconnected from production: `ledger.py` validates economic units and quarantines conflicting transaction/log identities; `temporal.py` detects pre-observed coordinated entries without future prices/outcomes; `coverage.py` audits **provider-reported** half-open block intervals by `(chain_id, contract_address, topic0, protocol_variant)`; `source_ingest.py` loads existing `verified_transfers.csv` rows with original receipt hashes.

This is **not** a comprehensive V1/V2 decoder. The future registry must distinguish at least three noninterchangeable systems: historical CTF Exchange V1; **CTF Exchange V2** (`Polymarket/ctf-exchange-v2`, with explicit `side` + `tokenId` fill semantics); and **Polymarket Protocol V2** (`Polymarket/polymarket-v2-external`, with structured position IDs and PositionManager). Do not infer event era from timestamp alone. Each on-chain contract registry entry requires chain, verified deployment block, exact proxy address, ABI/topic hashes, upgrade boundaries and post-upgrade event mapping. Official repository READMEs are references, **not independent contract bytecode verification**.

Provider cursor exhaustion / successful HTTP responses do not prove all logs exist, nor that a historical Gamma market was visible at decision time. A second archive/RPC or reconciled block-receipt audit is required to promote provider-reported ranges to independently verified completeness. Any extra `observed_at` from the future disqualifies a prospective replay. No re-run may update the sealed scores or frozen protocol in the current PolySentinel daemon.

Source importers must maintain separate columns for `service_label` and `service_label_provenance` instead of using those labels as `protocol` proof. The current importer discards that attribution field from financial edges by design while preserving raw transfer tx provenance. An optional label sidecar can be built after independent lineage review.
