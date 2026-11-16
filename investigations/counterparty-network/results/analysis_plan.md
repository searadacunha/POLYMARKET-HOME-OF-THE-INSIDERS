# Prospective test plan (draft, NOT frozen)

The question is not merely whether two wallets trade with each other. It is whether a **point-in-time network feature** predicts an outcome or a capturable price move better than the price already does.

This plan is a proposal, not a completed statistical test. No thresholds have been tuned to the Nobel, Iran or Maduro case outcomes in this file.

## Population and scope

- Assemble V2 CTF and NegRisk order fills, plus any subsequently active exchange contracts, for all eligible informational Yes/No markets in a defined future or held-out period. Do not restrict the population to named cases, profitable wallets or events with a large post-hoc price change.
- Preserve token, condition, side, order hash, maker/taker, block, log index, amount, contract version and execution timestamp. Exclude synthetic exchange-counterparty legs and deduplicate by chain, transaction hash and log index.
- Distinguish complementary matching from mint/merge and never infer a buyer-seller share transfer from a maker-side label alone. Resolve any ambiguous fill group with the underlying receipt and matching call rather than guessed greedy pairing.
- Construct the graph only from trades with block timestamps no later than the evaluation cutoff. Track whether an edge was **observable by a live indexer** at that cutoff.

## Features to consider (before outcome labels)

- Unique executed non-contract counterparties per account in a trailing window; pair exposure concentration versus broad market-maker baseline.
- Reciprocal execution patterns, repeated interactions across independent events, and anomalous closed components after filtering high-degree liquidity providers.
- Graph temporal concentration compared with same-market price, dollar volume, active participants and liquidity at the same clock time.
- A **separate** source-of-funds overlay using confirmed direct transfers, not automatically joining accounts through exchange hot wallets or bridges.
- Explicit falsification cases: ordinary inventory rebalancing, legitimate market-making, event-time crowd entries, smart-order routing, multi-leg order settlement and self-matches.

## Design required to measure alpha

1. Create chronological TRAIN, VALID and untouched TEST splits before feature fitting; exclude all case files used to generate hypotheses from TEST.
2. On TRAIN only, select thresholds, graph look-back windows and market exclusions. Log every searched variant and positive/negative control.
3. Alert time is **after** an execution is confirmed and processed. Estimate a follower's available bid/ask, depth, queue, slippage, transaction costs and latency at that exact decision time.
4. Compare realized net return and calibration excess over the contemporaneous market-implied probability using event- and component-clustered uncertainty. Use matched market/hour/liquidity/price-band controls, not a winners-only comparison.
5. Check that the result survives excluding one event, one cluster and known market-makers, and holds in an untouched prospective live shadow period.
6. If the signal fails the TEST or disappears after costs, record REFUTED or NOT_SUPPORTED and do not deploy a strategy.

## What counts as a deliverable

A frozen machine-readable protocol, a provenance-complete event tape, graph-feature snapshots with hashes, all positive and null results, a walk-forward backtest, and the list of actually alerted wallets at their original alert times. A graph image or a list of unusual wallets alone does not qualify.

## Current outcome

No dataset meeting these conditions has been built or tested in this investigation. Predictive value, ROI, statistical power, and insider attribution remain **UNRESOLVED**.
