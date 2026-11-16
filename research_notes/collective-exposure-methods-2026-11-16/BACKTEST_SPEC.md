# One falsifiable experiment, not a new data-collection programme

**Status: proposal only, not a frozen or successful experiment.** This note is an input to the separately running investigation, not a competing implementation.

## Precondition gates

1. Freeze *which markets belong to the same event family* based on contract settlement rules, not just title similarity.
2. Obtain complete, version-aware on-chain histories to reconstruct `Q_wallet,event(T)` from BUY, SELL, ERC-1155, split/merge/redeem and NegRisk operations. Record known missing ranges and refuse invalid "position flips".
3. Separate truly independent wallets from service accounts and exchange makers using relationships independently observable before T. Do not let the post-event Coinbase payout cluster enter an alert.
4. For timestamp T, construct a deterministic feature snapshot from only data available by T, with `first_observed_at`, no case outcomes and a hash.

## Signal families to compare

- **A**: only market price, historical liquidity and time-to-deadline.
- **B**: raw same-market BUY consensus (baseline comparable to Polymarket Intel).
- **C**: NO-before-YES event sequencing without net inventory (intentionally weak baseline).
- **D**: actual net payoff-vector rotations at wallet level.
- **E**: prospective multi-wallet concentration in D, with activity-preserving group null.
- **F**: E plus direct finance/counterparty relationships established before T.
- **G**: interval-package concentration without reversal, a falsification/control class.

Report every tested family and searched threshold. Freeze event-level TRAIN/VALID/TEST splits, with **all Nobel, Maduro and Iran cases used to invent features excluded from untouched TEST**. Use market-family/event-clustered uncertainty, activity-preserving randomization, and multiple-testing control.

## No economic backtest without executable prices

For each generated alert preserve the exact earliest observable time. The first possible buy/sell is *after* that time at a contemporaneous bid/ask with documented depth and latency; include fees appropriate to market and date, slippage, partial fills, gas and reasonable inventory bounds. Distinguish markout from executable net PnL and never use retrospective closing odds as an entry price.

Required output for each model: alerts, events, rates, Brier/log score improvement relative to contemporaneous prices, event-clustered confidence bounds, gross return, **net executable return**, capacity, timestamps, failures, and a list of false positives.

If historical depth snapshots do not exist, publish the result as *predictive-only / economic feasibility unverified*; a positive mid-price result is not an exploitable edge.

## Fail-fast and stop conditions

- If no full or defensibly complete history exists for a pilot set: stop and report coverage gap, do not silently replace with 100-row Data API calls.
- If the observed rotations disappear when interval packages and market makers are separated: do not continue searching larger data sets for the same unsupported hypothesis.
- If the signal adds no benefit beyond price or is uneconomic after feasible costs: verdict **NOT_SUPPORTED** or **REFUTED** in the context of the declared experiment.
- If TEST was used for feature design, seal a new future prospective period; never relabel that same TEST as unexamined.

## Relationship to ongoing work

Do not edit or interrupt any branch implementing the user's live collective-exposure prompt. This note changes no experiment state or scanner code. It adds a source-backed checklist and an archived-case arithmetic audit that the running experiment can consult.
