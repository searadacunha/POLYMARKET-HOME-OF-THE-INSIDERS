# Financial fingerprint negative control — archival replay (18 November 2026)

**Verdict:** An observable shared funding network is not, by itself, a validated pre-event prediction signal. This independently recalculates *arithmetic from two existing CSV archives*. It **does not** repeat chain receipt collection, establish wallet control or validate an executable edge.

## Sources and provenance

- `research_notes/financial-links-replay-2026-11-07/data/railgun_tree_accounts.csv`: 71 distinct proxy wallets and one published trade per proxy, all with the published `DISTRIBUTOR_CHILD` lineage.
- `research_notes/financial-links-replay-2026-11-07/data/kpmg_handoffs_verified.csv`: 14 recorded Relay-to-Solana-to-Polygon handoffs with source transaction anchors.
- Amounts, winner flags and market outcomes are **pre-existing archive fields**. No external intellectual property or private data imported.

## Archival arithmetic independently checked

| Railgun control | Recalculation |
|---|---:|
| Trading wallets and trades | 71 |
| Winners / losers | 5 / 66 |
| Purchase cost in recorded USDC entries | 21,965.645223 |
| Sum of 71 entry prices | 3.909500 |
| Mean entry price | 0.055063 |
| Observed win fraction | 0.070423 |
| Win fraction minus mean entry price | +0.015359 (1.54 points) |
| Payout *if redeemed*, per archived field | 53,113.161821 USDC |
| Distinct market titles | 5 |

All five winners entered the same `Maduro out by January 31, 2026?` market; the other 66 bets spread over four other markets. The markets concern related Venezuelan outcomes: **71 wallets are not 71 independent resolution events**. There is no valid IID p-value, predictive precision, proved realised profit or tradeable historical entry price in this calculation. The sum of prices is descriptive only.

| KPMG control | Recalculation |
|---|---:|
| Entries labelled `CONFIRMED` in the archive | 14 / 14 |
| L1-to-L2 delay | 18–50 seconds |
| Exact intermediary atomic credit/debit match | 14 / 14 |
| New Polygon or Solana RPC reads in this pass | 0 |

This checks the archived numbers, not the authenticity or completeness of each receipt. A bridge, contract, relayer or shared CEX does not demonstrate common ownership.

## What the negative control changes

Selecting only five winning accounts retrospectively would imply a 100% win rate. Reading the complete previously published funding tree shows 5 wins in 71 bets. A financially distinctive network with several highly visible winning addresses can also contain a much larger population of losses. This **does not refute all funding fingerprints**: it rejects treating a shared historical Railgun funding tree and some winners as sufficient evidence of pre-event informed trading.

## Reproduce

From repository root:

```bash
python3 -I research_notes/financial-cycle-negative-control-20261118/replay.py --check-archive
python3 -m unittest discover -s research_notes/financial-cycle-negative-control-20261118/tests -v
```

Standard library only, read-only. The script fails closed on missing columns, duplicate wallet/transaction identifiers, invalid prices, non-finite amounts, inconsistent win/payout labels, noncausal handoffs, and mismatching intermediary amounts. Seven synthetic tests passed locally on 18 November 2026. The full `AGENTS.md` publication suite was **not** run in this session because no complete local Git clone was available. Keep the PR in draft pending CI and reviewer inspection.

## Forward-only hypothesis: historical cash-out to future funding

The **untested** extension is an event-time graph that joins a past observed withdrawal at `t_exit` to a directly traceable later deposit at `t_funding > t_exit`, then observes a new trading entry at `t_alert >= t_funding`.

1. Only use transactions, receipts, address classifications and information actually available by `t_alert`. Do not use a later outcome, later wallet tag or later cross-chain attribution as a past predictive feature.
2. Require an exact transaction-based transfer path with UTC, block and log-index anchors. Reject shared-service edges; leave unknown service status unresolved. A graph connection is not a statement of beneficial ownership.
3. Freeze eligible population, maximum number of hops, maximum re-entry delay, minimum size, feature definitions and all comparisons **before** outcome examination. Compare against unrelated wallets matched by market, entry time, size, price and service exposure, plus activity-preserving network rewiring.
4. Split on chronology and non-overlapping **event families**, not just wallet addresses. The Railgun 71-wallet cohort is a descriptive negative control, not 71 independent draws.
5. At alert time archive the trigger, funding and exit evidence, public-information cutoff, contemporaneous book ask/depth, spread, timestamp and feed latency. Score `final_outcome - ask_at_alert` and conditional gain over the price-only model **after resolution**. Event-cluster the intervals; charge spread, fees, latency and slippage.
6. Permit a `SUPPORTED` prediction label only after an independent forward holdout, multiplicity control, sufficient power and positive **net executable** value. Otherwise keep `UNRESOLVED` or `REFUTED`.

**Minimum missing joined fields:** `withdrawal_tx`, `intermediary_transfer_tx`, `new_funding_tx`, `market_entry_tx`, `quote_at_alert`, each with actual observation timestamps, receipt hashes and data coverage manifests. Prefer the existing Polygon, `phi_engine` and `livecollect` collectors; no new paid infrastructure is justified.

**Current status:** protocol and archival arithmetic implemented; historical exit-to-future-entry predictive experiment **not run**; no new alpha claim.
