---
id: data-completion-20261123
title: Data completion, on-chain trade reconstruction and coverage measurement
state: IN_PROGRESS
updated_utc: 2026-11-23T20:00:00Z
origin: ~/.cache/phi-work/data-completion-raw-20261123
version: 2026-11-23 UTC collection, finalized Polygon block recorded in results/ledger_results.json
---

## Objective

Measure which evidence exists and which is missing, recover what keyless public sources still allow, rebuild the archived f2020 cohort's trades, positions and profit from Polygon logs in exact integer units, reconcile the money against on-chain balances, and extend the weekly funding and cross-chain checks of the open pull requests 109, 110 and 111 without changing them.

## Actual state

The cohort's value-moving logs are collected for every account over the whole exchange history, every stream contiguous on the primary provider, with market identities, official payout vectors, balance checkpoints and the Data API as an independent control. On pull request 111's four wallets the ledger reproduces 2,546 of its 2,548 per-market rows exactly; the two others resolved after its cut-off. Pull request 110's Ethereum log streams are recovered for the 23 missing weeks; its native Ethereum stream and its Relay history screen remain partial (the Relay screen is a dated snapshot while the collector runs until the announced Sunset). The three Arbitrum passages of pull request 109 were re-collected on several providers.

## Conclusions

See `FINDINGS.md`. Trading profit is reported per account and per market with its denominators, separately from deposits, withdrawals and service funding. No finding establishes a common owner, private information or a predictive edge; the comparative verdict stays NO_EDGE_VALIDATED.

## Limits

One public provider served the historical Polygon logs; a second provider was compared on samples only. Open positions without a timestamped price stay UNKNOWN. Relay v2 announced a Sunset of 2026-11-24T00:00:00Z and v3 needs a key, so Relay histories not read by then cannot be completed. The native Ethereum stream of pull request 110 is partial for 17 weeks. Platform-wide denominators remain unknown.

## Links

Builds on [weekly funding (PR 110)](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/110), [the four reconstructed bets (PR 111)](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/111) and [the radar benchmark (PR 109)](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/109).
