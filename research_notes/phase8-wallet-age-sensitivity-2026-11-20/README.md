# Phase 8 wallet age: how S_FRESH responds to pUSD collateral (exploratory, 20 Nov 2026)

**Type:** EXPLORATORY, post hoc sensitivity analysis of a frozen study. Every new figure below is exploratory and
post hoc. The phase 8 study of `investigations/maduro-iran` is frozen and is not modified: its protocol, report,
scripts and tables stay as published, and its verdict stands as recorded (no exploitable signal; S_FRESH graded
"PROMETTEUR (faible)" and named as the lead to re-test). This note is **not** the pre-registered re-test that the
phase 8 report asks for, and it changes no classification. Everything below is re-checked offline by
[`verify.py`](verify.py) from committed files.

## Result (exploratory, post hoc)

- **(a) Definition.** The frozen protocol dates a wallet from its first USDC inflow (USDC.e or native) that is not
  trading. The frozen code dates it from the first transfer of USDC.e or native USDC of any kind, in either
  direction. The phase 8 report does not mention the difference.
- **(b) pUSD.** The frozen feature reads only those two tokens, so it cannot see a wallet whose first collateral
  arrives as pUSD, which appears in the funding sample from late April 2026. Under the frozen rule such a wallet has
  an unknown age and is scored as not fresh. Counting pUSD moves the S_FRESH event counts from 333/242/33 to
  333/251/65 (TRAIN/VALID/TEST). Every change is from not fresh to fresh, in VALID as well as in TEST.
- **(c) Estimate.** On TEST at the resolution horizon, the point estimate moves from +8.14 points (n = 30) to
  -0.67 points (n = 60, 40 markets). Neither market-clustered interval excludes zero. The published TEST estimate
  rests on about 20 to 26 effectively independent events. Counting pUSD is an amendment of the written definition,
  and 38 of the 41 changed events rest on a pUSD mint. The frozen verdict stands as recorded.

## What was checked

- **Inputs.** The frozen tables are read in place from `investigations/maduro-iran/sources/phase8/`
  (`event_study.csv`, `wallet_features.csv`, `backtest_results.csv`), with the protocol, the report and the scripts
  `p8_funding.py`, `p8_fundfeat.py` and `p8_analysis.py`. The only added input is
  [`data/pusd_first_transfer.jsonl`](data/pusd_first_transfer.jsonl), the first pUSD transfer of each of the 1,506
  funding-sample wallets ([provenance](data/PROVENANCE.md)). All are pinned in
  [`data/SHA256SUMS`](data/SHA256SUMS).
- **Frozen flags reproduced.** [`sensitivity.py`](sensitivity.py) recomputes `wallet_age_h` and S_FRESH from
  `wallet_features.csv` (`first_any`) with the frozen thresholds (48 hours, at most 2 earlier trades): 0 flag
  mismatches on 30,108 events and 0 age mismatches on the 4,294 funding-sample events.
- **Estimator reproduced.** A standard-library port of the audit's independent implementation of the stratified
  difference of `p8_analysis.py` (price bucket x TRAIN momentum tercile, weights = signal events, baseline strata of
  at least 10 events) returns the published resolution effects at 1 point of cost: +0.65 (TRAIN), +1.23 (VALID) and
  +8.14 (TEST).
- **One alternative definition, computed once.** `first_any` is replaced by the earlier of the first USDC.e/USDC
  transfer and the first pUSD transfer, any direction, mints included. Nothing else changes: same thresholds, same
  sample, same strata, same outcome column. No variant was tuned. The earlier exploratory work of the audit session
  computed this same definition three times with identical results; the audit counted the resulting comparison family
  at 288 + 36 = 324 comparisons (Bonferroni threshold 1.54e-4), of which 48 + 6 = 54 primary (threshold 9.3e-4). No
  p-value is claimed here. The audit also recomputed intervals under 4 resampling schemes for the 6 split cells, plus
  1 descriptive subgroup. This note recomputes 6 intervals for cells that are already in the family. None of these is
  a new hypothesis.
- **Intervals.** Percentile 95% intervals (2.5 and 97.5 percentiles, linear interpolation) by a market-clustered bootstrap: 4,000 draws, seed 20261120, Python's Mersenne
  Twister. Each draw resamples markets with replacement once, and the signal and baseline events of a drawn market
  enter together. The published phase 8 intervals use another scheme (signal and baseline markets resampled
  separately, 1,000 draws, seed 8, numpy) and are quoted from `backtest_results.csv`, not recomputed.

## 1. The written definition and the frozen code differ

| Source | Wallet age |
|---|---|
| `PROTOCOLE_PREENREGISTRE.md`, Features table, row `wallet_age_h` | T minus the first USDC inflow (USDC.e or native) not linked to trading, on the Polygon proxy |
| `p8_funding.py` line 6 | token set `TOK` = USDC.e and native USDC only |
| `p8_funding.py` line 18 | `first_any` = timestamp of the first `tokentx` row of either token, before any filter on direction or sender |
| `p8_fundfeat.py` line 24 | `wallet_age_h` = (T minus `first_any`) / 3600, empty when there is no transfer before T |
| `p8_fundfeat.py` line 32 | S_FRESH = `wallet_age_h` <= 48 and `prior_trades_univ` <= 2; an empty age gives False |

The published tables come from the code. `RAPPORT_PHASE8.md` lists three deviations from the protocol; none
concerns the wallet age, and the report never names `first_any` or pUSD.

## 2. The frozen feature cannot see collateral that first arrives as pUSD (exploratory, post hoc)

The earliest first pUSD transfer among the 1,506 wallets is dated 2026-04-23 22:47:54 UTC (a bound from this
sample, not the token's deployment date); 975 of the 1,506 wallets have a pUSD transfer at some point.

| Split | S_FRESH, frozen rule | S_FRESH, pUSD counted | Not fresh to fresh | Fresh to not fresh | Events with pUSD before T | Candidates with unknown age, frozen rule |
|---|---:|---:|---:|---:|---:|---:|
| TRAIN | 333 | 333 | 0 | 0 | 0 | 0 |
| VALID | 242 | 251 | 9 | 0 | 132 | 12 |
| TEST | 33 | 65 | 32 | 0 | 324 | 48 |

Candidates are funding-sample events with at most 2 earlier trades. With pUSD counted, no candidate keeps an
unknown age. The splits are cut on the market end date, so trades of VALID and TEST overlap in time; by trade month,
the frozen rule loses the fresh wallets from May 2026 on:

| Trade month (UTC) | Candidates | Unknown age, frozen rule | Fresh, frozen rule | Fresh, pUSD counted |
|---|---:|---:|---:|---:|
| 2026-04 | 305 | 0 | 41 | 41 |
| 2026-05 | 94 | 19 | 2 | 18 |
| 2026-06 | 62 | 22 | 0 | 16 |
| 2026-07 | 47 | 17 | 0 | 7 |
| 2026-08 | 23 | 2 | 1 | 3 |
| 2026-09 | 2 | 0 | 0 | 0 |

41 events change, in 27 wallets and 27 markets, all traded between 2026-05-03 22:18:30 and 2026-08-19 13:22:24 UTC.
All 41 had an unknown age under the frozen rule, so the frozen rule counted them as not fresh and placed them in the
S_FRESH baseline. For 16 of them the wallet never has a USDC.e or USDC transfer, and for the other 25 its first one
comes after the trade. 38 of the 41 changed events rest on a first pUSD transfer that is a mint from the zero
address. A mint is not shown to be outside funding. Under the pUSD rule 649 events are flagged in total
(333 + 251 + 65).

## 3. TEST and VALID estimates at the resolution horizon (exploratory, post hoc)

Stratified difference with the funding-sample baseline, in probability points, resolution horizon, 1 point of cost:

| Split | Wallet age rule | Events with outcome (in used strata) | Markets | Wallets | Effect, points | Market-clustered 95% interval | Kish n_eff, market / wallet |
|---|---|---:|---:|---:|---:|---|---|
| TRAIN | frozen | 333 (331) | 147 | 221 | +0.65 | [-2.50, +4.03] | 79.5 / 182.7 |
| TRAIN | pUSD counted | 333 (331) | 147 | 221 | +0.65 | [-2.47, +3.91] | 79.5 / 182.7 |
| VALID | frozen | 242 (242) | 103 | 185 | +1.23 | [-1.38, +4.03] | 55.7 / 155.8 |
| VALID | pUSD counted | 251 (251) | 107 | 192 | +1.26 | [-1.36, +3.95] | 58.5 / 161.1 |
| TEST | frozen | 30 (29) | 23 | 28 | +8.14 | [-3.71, +22.97] | 19.6 / 26.5 |
| TEST | pUSD counted | 60 (59) | 40 | 47 | -0.67 | [-7.99, +7.42] | 30.5 / 39.1 |

The frozen rows are the published effects. The published intervals, from `backtest_results.csv`:

| Split | Published effect | Published 95% interval | n |
|---|---:|---|---:|
| TRAIN | +0.65 | [-2.78, +4.28] | 333 |
| VALID | +1.23 | [-1.74, +4.45] | 242 |
| TEST | +8.14 | [-4.73, +21.94] | 30 |

- Neither TEST interval excludes zero: this holds for both rules under this note's scheme, and for the frozen rule under
  the published scheme. The pUSD row was not recomputed under the published scheme.
- The Kish effective sample size counts the events as if each market (or each wallet) were one draw: the published
  TEST estimate rests on about 20 to 26 effectively independent events, the pUSD-counted one on about 30 to 39.
  These are one-way sizes. A conservative two-way (market and wallet) count in the audit is about 9 (frozen) and 17
  (pUSD counted); it was not recomputed here.
- The 30 TEST events that change and have an outcome sit in 18 markets and 19 wallets, with a mean gross `ret_res`
  of -6.96 points. The move of the point estimate rests on them.
- With 2.8 times the market-clustered standard error as a rough minimum detectable effect at 80% power, TEST can
  detect about 18.9 points with the frozen flags and about 10.9 points with pUSD counted.
- TRAIN is unchanged. VALID moves from +1.23 to +1.26 points.

## What is not shown

- The frozen phase 8 verdict is **not** changed, overturned or corrected. S_FRESH keeps its recorded grade; no new
  classification is recorded here.
- S_FRESH is **not** shown to have no effect, and the published effect is **not** shown to be false. Both TEST
  intervals contain zero, and the test can only detect effects of roughly 11 to 19 points.
- The gap is **not** a TEST-only problem: it reaches the end of VALID too (9 changed events). And counting pUSD
  **is** a re-definition: the protocol, written on 30/09/2026, names the tokens. This is a post hoc amendment of the
  written feature, made to restore what the feature was meant to measure.
- The frozen rule does **not** use "the first USDC.e inflow that is not trading": the code counts native USDC as
  well and takes the first transfer of any kind.
- A pUSD mint is **not** shown to be outside funding. Nothing here says who funded the changed wallets, that any
  wallets share an owner, who anyone is, or that anyone traded on inside information.
- The outcomes were **not** recomputed from raw data: `ret_res` and the prices come from the published
  `event_study.csv`. The pUSD-counted figure is exploratory, not confirmatory.
- No corrected S_FASTFUND or S_MOONPAY figure exists: neither was computed, and the pUSD file holds only each
  wallet's first pUSD transfer, not its later inflows.

## Reproduce

From the repository root, offline:

```bash
python3 -B research_notes/phase8-wallet-age-sensitivity-2026-11-20/sensitivity.py
python3 -B research_notes/phase8-wallet-age-sensitivity-2026-11-20/verify.py
```

`sensitivity.py` prints every figure as JSON (a few seconds, standard library only, no file written). `verify.py`
checks the SHA-256 list, re-runs `sensitivity.py`, compares each figure of this note with the recomputed value under
a named check, re-reads the frozen protocol and code lines of section 1, and runs a negative self-test: moving one
changed wallet's first pUSD transfer after its trades must lower the TEST count. It prints PASS or FAIL per check
and exits 1 on any failure.

## Limits

- No network. The first pUSD timestamps come from one Etherscan lookup per wallet on 19 November 2026; the raw
  responses were not archived and the file was not re-fetched. The USDC history (`first_any`) is taken from the
  published `wallet_features.csv`.
- Only the first pUSD transfer of each wallet was collected. pUSD variants without mints, or counting inflows only,
  were not computed.
- The bootstrap intervals carry Monte Carlo noise and depend on the generator: the same scheme drawn with another
  generator moves the endpoints by Monte Carlo noise. The point estimates, counts and Kish sizes are exact.
- Kish sizes and a one-way market bootstrap do not capture clustering by market and wallet at the same time; a
  two-way scheme gives wider intervals than those shown.
- The funding sample keeps the first 4 events of each wallet plus up to 4 at random, a deviation the phase 8 report
  already lists. TEST remains small.
- The audit that set what this note may say read the published S_FRESH rows and the phase 8 report: it was not
  blind. An address is not a person.
