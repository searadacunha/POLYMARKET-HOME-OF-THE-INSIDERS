# Results of the frozen study of large purchases

Question: on Polymarket, do large purchases that look unusual at the moment they are made (fresh funding on a new
wallet, a dormant wallet reactivated, a bet far out of character, wallets paid by the same plain key, a rare
combination of features) win more often than the price paid implies, and more often than ordinary large purchases at
the same price and horizon?

**Answer: no class does.** None reaches SUPPORTED. The newcomer classes do worse than their price on the validation
events: a freshly funded new wallet (C1) is 3.7 points under its price, and an advantage of 5 points is excluded at this
sample size; the pre-registered rule of the Maduro and Iran file (R1) is 6.0 points under its price, with an interval
entirely below zero. A dormant wallet reactivated with fresh money (C2) is 4.6 points above its price, which is not
significant and cannot be told apart from zero or from 5 points. The group classes (C4, C5) raise no alert on the
validation events. Every class of the live engine therefore stays EXPLORATORY.

A class that wins more than its price says nothing about one account, and a class that does not says nothing about one
account either. Nothing here is a finding about any person.

## What was done

- **Plan** written before the analytic table existed (`study/analysis_plan.md`), corrected twice before the freeze after
  independent audits of the code (`study/audit/`), each correction made before any outcome was read and stated in the
  plan. Frozen on 14 November 2026 at 17:12:40 UTC (`study/PROTOCOL.lock`, 38 files, then one export added by
  amendment 001).
- **Population**: 32,552 Yes/No markets in 7,554 events with a scheduled end from January 2025 to October 2026, outside
  the kinds whose outcome is produced in public view. 2,851,593 fills of 1,000 USD or more, read market by market;
  675,747 entries (first large purchase of one wallet on one side), 210,021 of them eligible (price 0.90 or less, before
  the end); 77,191 passed the screen and 57,592 were evaluated with the wallet's history.
- **Funding**: deposits read from the activity listing and, because that listing names only some ways of funding (a
  quarter of the new wallets of August 2026 show no deposit row), collateral received on the chain over 18,780 windows,
  with Polymarket's own transfers left out (`study/code/asof.py`, `chain_rows`). 712 entries are fresh by the chain
  alone; their senders are bridges and solvers (Relay), exchanges, swap pools and third-party wraps
  (`study/audit/chk_fresh_by_chain_20261114.txt`). The payer of each deposit of a thin or dormant fresh wallet was traced
  for 20,070 entries, none of them left incomplete.
- **Unit**: one alert per event, the earliest of the class. VALIDATION = events whose scheduled ends fall from April to
  October 2026 (2,639 events, 1,924 INFO); DISCOVERY = earlier events and the documented cases (4,915 events).
- **Tests**: T1, exact test that the alerted sides win more than their prices say; T2, difference of mean excess with
  the control entries of the same price and horizon strata, events resampled whole. Bonferroni over every comparison of
  the registry.
- **Positive controls** before the freeze (`study/controles/positive_controls.md`): 0 false SUPPORTED in 180 runs with
  nothing planted, 0 when every entry beats its price by 5 points, 0 with outcomes correlated by week. With about 390
  alert events an excess of 10 points was SUPPORTED in 6 runs of 6 and one of 5 points in 3 of 6; with about 124 events,
  10 points in 3 of 6.
- **Reproduction**: the whole analysis run twice in fresh copies, every output identical
  (`study/audit/REPRODUCTION.txt`). `verify.py` recomputes every T1, every T2 difference and every verdict from the
  published tables.

## Verdicts, VALIDATION x INFO

<!-- table:header -->
Comparisons on real data counted in the registry: 63; corrected threshold 0.05 / 63 = 0.00079. Population sizes (eligible entries): validation_info 60,614, validation_public_process 31,291, discovery_info 90,568. M3 was fitted on 30,366 discovery entries.
<!-- /table:header -->

<!-- table:primary -->
| Class | Verdict | Alert events | Wallets | Excess, points | 95 % interval | T1 p | T2 difference, points | T2 p | Negative control T1 p |
|---|---|---:|---:|---:|---|---:|---:|---:|---:|
| C1_FRESH_FUNDED_BET | NOT_SUPPORTED_EFFECT_EXCLUDED | 360 | 352 | -3.7 | -8.3 to +0.7 | 0.96 | -5.5 | 0.99 | 0.98 |
| C2_DORMANT_REACTIVATION | NOT_SUPPORTED_UNDERPOWERED | 154 | 154 | +4.6 | -2.1 to +11.5 | 0.10 | +3.6 | 0.16 | 0.69 |
| C3_OUT_OF_CHARACTER | NOT_SUPPORTED_EFFECT_EXCLUDED | 406 | 397 | -1.3 | -5.2 to +2.6 | 0.75 | -3.2 | 0.95 | 0.70 |
| C4_COFUNDED_GROUP | INCONCLUSIVE | 0 | 0 |  |  |  |  |  |  |
| C5_RECURRENT_FUNDER | INCONCLUSIVE | 0 | 0 |  |  |  |  |  |  |
| C6_QUIET_FRESH_LOW | NOT_SUPPORTED_EFFECT_EXCLUDED | 136 | 135 | -5.8 | -12.9 to +1.4 | 0.95 | -3.7 | 0.84 | 0.72 |
| C7_HEAVY_NEWCOMER | NOT_SUPPORTED_EFFECT_EXCLUDED | 95 | 93 | -6.7 | -15.7 to +1.7 | 0.95 | -8.1 | 0.97 | 0.82 |
| R1_S_FRESH_REPLICATION | NOT_SUPPORTED_EFFECT_EXCLUDED | 375 | 365 | -6.0 | -10.3 to -1.6 | 1.00 | -7.8 | 1.00 | 0.90 |
| M1_RARITY_TOP1 | INCONCLUSIVE | 18 | 18 | -2.0 | -22.0 to +16.3 | 0.69 | -5.8 | 0.72 | 0.98 |
| M2_IFOREST_TOP1 | NOT_SUPPORTED_UNDERPOWERED | 44 | 44 | +0.6 | -13.2 to +14.4 | 0.54 | -2.2 | 0.62 | 1.00 |
| M3_EDGE_TOP5 | INCONCLUSIVE | 14 | 14 | +16.0 | -7.2 to +36.8 | 0.16 | +11.6 | 0.17 | 0.82 |
| B1_BIG | NOT_SUPPORTED_UNDERPOWERED | 204 | 180 | -0.4 | -6.4 to +5.5 | 0.59 | -3.1 | 0.86 |  |
| B2_AFTER_MOVE | NOT_SUPPORTED_EFFECT_EXCLUDED | 646 | 505 | -2.2 | -5.4 to +1.1 | 0.91 | -3.6 | 0.98 |  |
| B3_THIN_NOT_FRESH | NOT_SUPPORTED_UNDERPOWERED | 156 | 152 | +1.3 | -5.2 to +7.8 | 0.38 | -0.4 | 0.55 |  |
<!-- /table:primary -->

Excess = share of alerted sides that won minus the mean price paid, in probability points. The interval resamples
events. NOT_SUPPORTED_EFFECT_EXCLUDED means that an advantage of 5 points is outside the interval;
NOT_SUPPORTED_UNDERPOWERED means it is not; INCONCLUSIVE means fewer than 30 alert events.

How to read it:

- **Newness and fresh money do not predict winning.** C1, C6, C7 and R1, the classes built on a new wallet that has
  just received money, are all under their price, and their T2 differences with ordinary large purchases at the same
  price and horizon are negative. On these events, money that arrives on a new wallet and is spent at once is, on
  average, a slightly worse bet than the price.
- **C2 is the only class above its price**, by 4.6 points on 154 events, with p = 0.10 against a threshold of 0.0008.
  It is not a result. It is the one class worth watching in the next period, unchanged.
- **M3**, the edge model fitted on discovery outcomes, has 14 alert events: validation entries made before April 2026
  are contemporary with the outcomes it learnt and are left out (pre-freeze leakage audit). Its +16 points mean nothing
  at that size.
- **C4 and C5** (wallets paid by the same plain key) raise no alert on the validation events. In discovery, the only
  C4 alert event is the documented Nobel 2025 case (below), and the only C5 one is a wallet paid 87.71 USD by a key that
  had paid 150,000 USD to another wallet about 17 days earlier ([FINANCIAL_LINKS.md](FINANCIAL_LINKS.md)).
- **No baseline is significantly above its price**: size alone (B1) and buying after a move (B2) are under it, newness
  without funding (B3) is 1.3 points above it with p = 0.38.

## Negative control and discovery

<!-- table:other -->
| Class | VALIDATION x PUBLIC_PROCESS: events, excess, p | DISCOVERY x INFO: events, excess, p |
|---|---|---|
| C1_FRESH_FUNDED_BET | 61, -10.8, 0.98 | 887, -3.7, 1.00 |
| C2_DORMANT_REACTIVATION | 36, -2.2, 0.69 | 312, -6.2, 1.00 |
| C3_OUT_OF_CHARACTER | 65, -2.1, 0.70 | 709, +1.1, 0.26 |
| C4_COFUNDED_GROUP | 0 | 1, +50.6, 0.49 |
| C5_RECURRENT_FUNDER | 0 | 1, +10.8, 0.89 |
| C6_QUIET_FRESH_LOW | 25, -3.1, 0.72 | 376, -5.6, 0.99 |
| C7_HEAVY_NEWCOMER | 16, -6.9, 0.82 | 289, -2.6, 0.85 |
| R1_S_FRESH_REPLICATION | 64, -5.7, 0.90 | 877, -5.2, 1.00 |
| M1_RARITY_TOP1 | 4, -35.3, 0.98 | 183, -3.6, 0.87 |
| M2_IFOREST_TOP1 | 4, -50.3, 1.00 | 64, +1.4, 0.46 |
| M3_EDGE_TOP5 | 2, -6.4, 0.82 | 61, +3.1, 0.36 |
<!-- /table:other -->

The negative-control family (season-long sports, listed prices) shows no class above its price. The discovery set,
where the thresholds were fixed, does not show the newcomer classes above their price either: the rules did not fail
only out of sample.

## Robustness (estimates only, no p-value)

<!-- table:robustness -->
| Variant | C1 | C2 | C3 | R1 |
|---|---:|---:|---:|---:|
| Excess, one alert per event | -3.7 (n 360) | +4.6 (n 154) | -1.3 (n 406) | -6.0 (n 375) |
| Weeks resampled, 95 % interval | -8.7 to +1.8 | -2.1 to +10.9 | -6.1 to +3.4 | -10.7 to -1.5 |
| Any single event left out, range | -4.0 to -3.5 | +4.1 to +5.2 | -1.5 to -1.1 | -6.2 to -5.7 |
| Strictly before the scheduled end | -3.9 (n 351) | +4.2 (n 148) | -1.6 (n 392) | -6.2 (n 364) |
| At least 24 h before the real close | -3.3 (n 335) | +4.8 (n 146) | -1.6 (n 384) | -6.1 (n 350) |
| Entry of 5,000 USD or more | -9.3 (n 105) | -1.1 (n 58) | -0.7 (n 104) | -5.3 (n 96) |
| At the price a follower paid | +2.1 (n 223) | +3.7 (n 115) | -0.3 (n 211) | -1.9 (n 224) |
| First half, second half | -3.9, -3.6 | +1.0, +8.3 | -0.4, -2.2 | -7.4, -4.6 |
| Alert events a week | 3.88 | 1.66 | 4.6 | 4.07 |
| Median hours from alert to real close | 499 | 528 | 529 | 500 |
<!-- /table:robustness -->

R1 stays under its price in every variant (leaving any event out, resampling weeks, alerts strictly before the
scheduled end, at least 24 hours before the real close, large entries only, the follower's price). C1 does too, except
at the price a follower paid five minutes or more later, which describes a later price, not the alerted purchase. C2 stays above its
price in most variants but falls under it on entries of 5,000 USD or more, and its two halves differ widely.

<!-- table:sweep -->
| Cell of C1 | Events | Excess, points | p |
|---|---:|---:|---:|
| price_band_0 | 27 | -2.1 | 0.80 |
| price_band_1 | 29 | +6.5 | 0.24 |
| price_band_2 | 76 | -5.9 | 0.89 |
| price_band_3 | 103 | -4.6 | 0.86 |
| price_band_4 | 125 | -4.3 | 0.92 |
| horizon_0 | 26 | -7.3 | 0.87 |
| horizon_1 | 57 | -2.5 | 0.74 |
| horizon_2 | 121 | -7.8 | 0.98 |
| horizon_3 | 156 | -0.4 | 0.58 |
| first_half | 180 | -3.9 | 0.91 |
| second_half | 180 | -3.6 | 0.89 |

Placebo: 200 random classes of the size of C1 inside its strata, share with p < 0.05: 0.07, median p 0.48.
<!-- /table:sweep -->

## Documented cases (a listing, no test)

`study/code/ana_70_cases.py` lists, for each event of a case already documented in this repository, the classes that
fire and when (its output names wallets and stays on the machine that computed it). Those events are in discovery
because somebody won there. On them the newcomer classes fire, but early and on many wallets: on the Nobel 2025 winner
event the first C1 alert is on 14 August 2025, 1,373 hours before the close, before any of the documented accounts
existed (their profiles were created on 9 and 10 October 2025, `investigations/followup-20261113/sources/data/nobel_accounts.csv`). The documented accounts
themselves are all C1 and most of them C7 (`study/controles/nobel_features.txt`), and the group class C4 fires on them
11.3 hours before the real close, at 0.49, when the second wallet paid by the key 0xe206961002feebd9edb152eed9b630a351874043
enters the same market. A class that fires on a documented case is not evidence that it predicts: these events were
chosen because they ended well for those wallets.

## Deviations and data notes

- **Corrections before the freeze**, all made before any outcome was read and written in the plan with their reason:
  FRESH extended to collateral received on the chain, with Polymarket's own transfers, transfers in the second of a
  trade or redemption, wraps of the wallet's own money and amounts under 1 USD left out; R1 dated by the first inflow of
  collateral as pre-registered (a first version used the first deposit row); every deposit of the 24 hours traced (a
  first version kept three); the day after a scheduled end included only for ends at 00:00 UTC; the 2026 Nobel prize,
  documented nowhere, moved back to validation; M3 learnt only from discovery entries made before April 2026; entries of
  C1 that did not turn heavy taken out of the controls of C7; negative-control entries evaluated only through the 25 %
  hash sample; unknown membership excluded and counted, for the classes concerned only (7 entries; 12 for C7). The audit
  reports are in `study/audit/`; which version of the code produced which data is in `study/code/PROVENANCE.md`.
- **Amendment 001** (after the computation, `resultats_vus: oui`): `ana_98_control_exclusions.py` exports the cells of
  the entries kept out of the controls, so that `verify.py` recomputes the T2 difference of C7 and M3; no test changed.
  Its header gives 17:40 UTC; it was registered at 17:21:22 UTC (`study/PROTOCOL.lock`).
- **pUSD minted to a wallet** with no payer found in its receipt (504 of 3,672) is treated as the wallet's own money,
  so FRESH can be missed there.
- **One hop.** A key is linked to a wallet when it paid the deposit, or the money swapped into it in the 10,000 blocks
  before, or a pass-through key behind either. The second network of the Nobel 2025 case, which shares a key two hops
  away, is not seen as a group.
- **Collection accounting** before the corrected code survives only where the logs do (`study/code/PROVENANCE.md`). The
  old log ranges come from one public endpoint; at 16:20 UTC it answered in 6 to 11 s a call.
- **Outside the study**: markets under 10,000 USD and events under 50,000 USD, purchases split into fills under
  1,000 USD, fees, and everything before 2025.

## Reproduce

```sh
python3 -I research_notes/realtime-intelligence-2026-11-14/verify.py
python3 -I research_notes/realtime-intelligence-2026-11-14/scripts/render_results.py --check
```
