# Measured gaps and proposed falsification programme

**Date:** 2026-11-17. These are **proposals**, not runs. Source pointers refer to [SOURCES.csv](SOURCES.csv), not to files already downloaded. No trade execution, accusation or live surveillance is authorized by this note.

## G0 — Baseline and completeness audit (must precede new numbers)

**Existing:** `METHODOLOGY.md`, `INVENTORY.md`, `EDGE_VERDICT.md`, `investigations/collective-exposure-shifts/METHODS_REUSE.md` and historical frozen case evidence. These must remain unchanged.

1. Produce a de-duplicated **source-to-case graph** where every URL has an original publisher, source lineage, release date, reviewed date, method class, sample window, denominator, nonpublic/public outcome label, DOI or commit, license and extraction status.
2. For a source that claims "X suspected wallets", keep three denominators: candidate wallets, actually analyzed wallets, and unique operator hypotheses. Never silently sum Inca 39 + ACDC 152 + Bubblemaps 9: they can overlap, are selected by different rules and mostly do not represent legal findings.
3. Audit against public **positive controls** (DOJ/CFTC EXT-015–018), clean/negative controls (ordinary successful traders, event-market pairs with public information), and **time-causal data**. Do not use target-name labels in model fitting, feature selection or tuning.
4. Compare **as-of** availability for each feature. A later court filing or retrospective press article is not a feature available before the event.
5. Publish a coverage matrix (event families by exchange era, market category, EVM chain, wallet graph, order-book availability, pricing, reports and court cases) with explicit NOT-COVERED cells.

**Gate:** only after deduplication and event-time audit may an outside wallet become a locally tested candidate; never elevate to `CONFIRMED` from a published suspicion.

## G1 — Independent replication of Inca and ACDC

**Sources:** EXT-001–006, EXT-043, EXT-049.

| Question | Frozen design | Most likely failure mode / falsifier |
| --- | --- | --- |
| Do Inca's narrow-selection wallets remain unusual after controls? | Recreate the exact ≤10-market, ≥$30k realised-PnL selection if/when the original report is fully examined; choose matched controls by market opportunity, tenure, category and capital | Winners were preselected: naive high win rate is expected; reported 39 are **not** a ground truth |
| Do ACDC's Orcas lead ordinary traders? | Freeze longshot threshold (stake ≥$2500, entry ≤0.35), wallet category boundaries and events; compare Orca first **publicly observable** fill to other contemporaneous fills | A single public news shock may cause both; unequal feed latency, clustering by event, and posthoc winner selection |
| Do Whales/Bots measurably follow Orcas? | Placebo: matched non-Orca large trade in same market, local time and price state; event-clustered bootstrap and family correction | Pseudo-followers also track price/news even without Orca flow; copying opportunity smaller than spread |
| Does any such follower strategy beat the market price? | Walk-forward and pre-event frozen features; observed ask/depth at the candidate timestamp, fees and execution delays, holdout by event | Expected return ≤0 after costs, or no historical quotes, or sensitivity to one market |

**Important:** The 2026-11-17 exposure-shift audit showed that choosing the largest 6-hour signal can select a future firing and change a negative TEST sign. New follower work must use **first causal firing**, not ex-post maximum; otherwise the analysis is invalid.

## G2 — Population-scale wash-trade and matched-beneficiary graph

**Sources:** EXT-022–026, EXT-051, EXT-054–056.

- **Ingest into separate, licensed local storage**, do not commit third-party raw data. Get actual `OrderFilled` contract logs with `tx_hash`, `log_index`, block, timestamp, exchange, token/asset, maker, taker, size, price, fill direction and collateral. Reconcile with Data API on sampled markets across **V1, V2 and negRisk**; avoid treating two maker/taker event rows as two independent trades.
- Analyze: (i) same economic party on both legs if on-chain graph supports a **direct** linkage, (ii) rapid back-and-forth within a wallet, (iii) time-resolved strongly connected wallet components, (iv) mutually exclusive outcome round trips. These are **different suspicion tiers**, not a single `wash=true` predicate.
- Compare with matched market makers, airdrop/activity incentives, temporary arbitrage and common public event reaction. Measure null false positives by category, time, liquidity and volume tier. Use negative controls on high-turnover legitimate maker cohorts.
- Publish volume bounds with **economic trades as denominator**, wallet de-dup rules, pairwise confidence intervals, and a separate `UNKNOWN_BENEFICIAL_OWNER` outcome. Do **not** claim the Columbia ~25% estimate as independently reproduced.

**Gate:** source-level reconciliation passes; sensitivity to self-match definition and volume denominator reported; no unsupported actor identity.

## G3 — Resolution / oracle market abuse

**Sources:** EXT-027–030, EXT-040–042, EXT-074–075. 

- Build new `oracle_events` table: `condition_id`, frozen original rules, version/change timestamps, on-chain request, proposer address, bond, dispute, UMA voter/voting power, DVM process, retry/reset, final oracle result and redemption evidence. Pin Ethereum + Polygon blocks.
- Establish **what contract promised**, **what happened outside the contract**, and **what oracle finally decided** as three distinct entities. A controversial outcome can reflect ambiguous wording, timing, or adjudication, without proving collusion.
- Test whether wallet flows into UMA stakes, oracle voting and market outcome positions form **direct** funding/control edges beyond what ordinary governance participants show. Shared hot wallets and timing alone are insufficient.
- Start with Ukraine mineral deal, Zelenskyy suit and Strategy BTC sale disputes (CASES.md). Add Paris-CDG suspected sensor interference as a separate **physical reference-input** attack, with sensor audit and independent station baselines. Blind-review terms *before* looking at payout.
- Independently validate Fidonis/Bitquery rates with the same market cohort and dispute definition.

**Gate:** no market manipulation claim without event-state trace and documented non-manipulative alternatives.

## G4 — Adversarial reference data and complete market event history

**Sources:** EXT-034–039, EXT-050–053, EXT-072–073.

Data-source triage:

| Dataset | Promised asset | Critical validation before ingest |
| --- | --- | --- |
| SII-WANGZJ/Polymarket_data | Author reports 1.1bn trades, 107 GB, 268k+ markets | Contract/chain coverage, V1/V2/negRisk, licenses, duplicate logs, missed ranges, timestamps, inclusion of maker/taker both sides |
| ForesightFlow/datasets | Insider-case market IDs, resolution types and event/news timestamps | CC-BY attribution, actual block identifiers, tier1 UMA vs GDELT vs LLM-imputed time, no forward leakage |
| DineshKumar8399/polymarket-orderbook-dataset | Historical book observations, Jul–Aug 2026 | Sampling interval, depth vs top-of-book, side timestamps, update losses, execution-order fidelity |
| usepancake/polymarket-history | Daily price history / resolutions | **Synthetic last-price observations are NOT trades**; never use for wallet reconciliation or fills |
| OpenMarket | Synchronized Binance/Polymarket high-frequency study | Compare frozen market universe, missing-day intervals, fees, slippage and negative benchmark |
| alphalab wash datasets | Older V1 NegRisk transaction window | CC-BY-NC constraints and out-of-era extrapolation |

**Gate:** all archived snapshots use hashes, date of retrieval, original license, completeness statement, UTC time rules and reproducible raw-to-derived transformations. Missing data stays marked missing, never zero.

## G5 — X and independent media source provenance

**Sources:** EXT-007–014, EXT-062, EXT-066–069, EXT-071.

- Read exact post `created_at`, edit state, note-tweet long text, embeds/media, and archived screenshot **only when permitted**; map referenced contract and wallet identifiers. Save external content pointers/hashes rather than unlicensed republication.
- Collect origin timestamps for breaking-news claims from primary agencies; keep Reuters/AP/Guardian/Bloomberg/WSJ derivatives as **separate publishers but not independent transaction observations**.
- Ask for falsifiers: did wallets have public information earlier? Was the order placed before or after news? Was the position visible from actual fills? Did the market resolve based on event fact or semantic oracle rule?
- The indexed original X post links are **unverified social leads** (original posts inaccessible); the separate author-thread mirror is readable but does not authenticate the complete original media/edits. X trending pages/search summaries must **never** be used as wallet proof.

## G6 — Independent legal case anchor / evaluation

**Sources:** EXT-015–020, EXT-031–033, EXT-076.

Build a time-stamped case table storing `prosecutor_or_regulator`, `complaint_date`, `alleged_party`, `alleged_wallet`, `named_markets`, `trade_interval`, `public_docket`, `legal_status_asof`, `proof_type`, `reconciliation_status` and `source_url`.

**Do not** assert that official charging instruments establish guilt. Do not treat alleged names as reproducible on-chain ground truth until the public transaction/wallet correspondence has been independently matched and dated. Use separate independent blind detection cohort as negative control.

## Recommended execution order

1. **P0, low-cost:** finish the source registry and source-lineage / licensing review; download **nothing** into git.
2. **P0, highest information gain:** on-chain fill reconciliation and dedup (G2), plus the causal-first-signal correction (G1). If this fails, other pattern scores may be measuring artifacts.
3. **P0:** legal reference event-time matching of Google and Maduro with negative controls (G6).
4. **P1:** ACDC/Orca follower replication with holdout and public-news matched placebo (G1).
5. **P1:** oracle-resolution dispute graph and rule-interpretation checks (G3).
6. **P2:** larger V1-V2 archives and social archive coverage (G4–G5), only if provenance and rights allow.

`NO_EDGE_VALIDATED` remains the trading conclusion. The purpose is **forensic coverage and falsification**, not to claim a profitable or proven insider detector.
