# Analysis plan, collective exposure shifts (written before any outcome is joined)

Study id: `collective-exposure-shifts`. Plan version 1, written 2026-11-16, before the tape collection finished
and before `labels.jsonl` was joined to any feature. Every later change is a dated amendment in `amendements/`.

## Question

When several wallets increase their **net exposure to the same outcome** of a market within a short window, does that
outcome win more often than its price implies, and more often than under (a) the price alone, (b) naive buy-side
consensus, (c) a single wallet's shift? And would the edge survive executable costs?

The plan tries to destroy the hypothesis. A negative answer must be demonstrable, so every comparator is declared
here, and the decision rule is fixed in advance.

## What is deliberately excluded

- **The Iran / 28 February 2026 cohort (36 accounts).** It is the case that suggested the hypothesis. It is used
  only to (i) verify the archived descriptive figures and (ii) give a descriptive sensitivity reading. It is never
  part of a rate, a test or a verdict.
- **Financial-link arm (signal S5) at population scale.** Reconstructing direct funding links at that scale needs
  on-chain work that is not available here (see Limits). S5 is therefore evaluated only on the archived G38 network,
  descriptively, and is declared UNRESOLVED for the population.

## Data

- **Population of markets.** Reused, unmodified, from `research_notes/early-detection-2026-11-13/study/derived/`
  (`universe_markets.jsonl`, `labels.jsonl`), whose inclusion rules were frozen on 13 November 2026 and do not use
  the outcome: closed events of ≥ 50,000 USD volume without tags `games, esports, crypto-prices, hit-price,
  up-or-down, multi-strikes, weather, tweets-markets, mention-markets`; Yes/No markets of ≥ 10,000 USD; closed
  2025-01-01 → 2026-10-31 UTC; resolved to 1/0. 34,413 markets in 7,783 events.
- **Sampling, fixed now and blind to outcome.** From that population, keep markets with `volume < 1,000,000` USD and
  `int(sha256(condition_id)[:8], 16) mod 1000 < 25`. This yields 763 markets in 688 events. The hash is computed on
  the condition id only; no outcome, price or result enters the sample definition. The volume cap excludes the
  deepest markets, whose tapes exceed the collector's page budget; that exclusion is stated, not silent.
- **Tapes.** Polymarket data-api `v2/trades?condition=<id>&limit=1000&taker_only=false`, paginated by
  `pagination.next_cursor` until `has_more` is false. A market needing more than 300 pages is recorded `too_deep`
  and excluded from scoring (counted, never treated as empty). Profile text fields are never stored.
- **Labels.** `labels.jsonl` (`winner` = YES or NO). Joined **last**, by `scripts/score.py`, which no feature script
  imports.

## Positions, from executed fills only

For wallet `w`, outcome `o ∈ {YES, NO}`, at time `t`:

- `q(w,o,t) = Σ_{fills ≤ t} size · (+1 if BUY, −1 if SELL)`, net **shares** held, in share units.
- `p_o(t)`, price of the last executed fill of token `o` at or before `t` (never a midpoint, never a later price).
- Net exposure to the market outcome, in YES-share equivalents: `X(w,t) = q(w,YES,t) − q(w,NO,t)`.
  Economically a NO share is a short YES share, so this is the only quantity whose sign is a directional bet.
- Directional exposure to side `s` (`s = YES` → `d=+1`, `s = NO` → `d=−1`): `X_s(w,t) = d · X(w,t)`.
- Marked USD exposure: `M(w,t) = X(w,t) · p_YES(t)`; gross two-sided exposure:
  `G(w,t) = q(w,YES,t)·p_YES(t) + q(w,NO,t)·p_NO(t)`.

This construction separates the four required cases:

- **A (true change on one outcome):** `ΔX_s > 0` on a wallet that already holds `X_s > 0`.
- **D (coexistence, not inversion):** `q(YES) > 0` and `q(NO) > 0` at the same time; `X` stays small. Detected and
  counted explicitly (`coexistence` flag); never reported as an inversion.
- **C (liquidity / hedging / rebalancing):** in `[t−W, t]` the wallet both buys and sells, and its gross traded
  notional is ≥ 5× its net exposure change. Such wallets are excluded from the collective count (variant S4b keeps
  them).
- **B (NO on deadline D1 → YES on deadline D2):** cannot be read inside one market. It is measured at **event** level
  across markets of one `event_slug` with distinct closing times, as a portfolio payoff per realisation interval
  (section "Interval reading"). Descriptive only.

What this **cannot** see: splits (mints), merges, redemptions and neg-risk conversions are protocol events, not
fills; they do not appear in the trade tape. A position built by a split and then sold on one leg is visible only as
a SELL. The bias this creates is stated in Limits and is not corrected silently.

## Signals, all evaluated at time `t` on a 900-second grid over each market's traded life

`W = 3600 s`. For side `s`: `Δ_s(w,t) = X_s(w,t) − X_s(w,t−W)`.

**Qualifying wallet** for side `s` at `t`: `Δ_s(w,t) · p_s(t) ≥ 500 USD` **and** `Δ_s(w,t) ≥ 0.25 · G(w,t−W)`
(or any positive change when `G(w,t−W) < 500 USD`).

- **S4, collective exposure shift (primary).** `≥ 3` distinct qualifying wallets, not flagged two-sided;
  `Σ Δ_s·p_s ≥ 3,000 USD`; largest wallet `≤ 60 %` of that total; `0.05 ≤ p_s(t) ≤ 0.90`; `t` at least 60 minutes
  after the market's first fill. Alerts are de-duplicated per `(market, side)` by keeping the largest total inside
  any 6-hour block (non-maximum suppression fixed here, not tuned), then **only the first firing of each
  `(market, side, signal)` is used as a statistical unit** (`primary: true`). Later firings are kept in the output as
  `primary: false` repeats and are used descriptively only. This avoids counting the same ongoing position change
  many times and avoids selecting the largest alert after the fact.
- **S4b**, S4 with two-sided wallets included (tests whether the exclusion drives the result).
- **S3, individual shift.** Exactly one qualifying wallet with `Δ_s·p_s ≥ 3,000 USD`, same price and time rules.
- **S2, naive buy consensus.** `≥ 3` distinct wallets with a BUY fill of `s` inside `[t−W, t]` totalling
  `≥ 3,000 USD`, `0.05 ≤ p_s ≤ 0.90`, no concentration rule, no prior-exposure requirement. This is the
  "collective BUY" definition the mission asks to replace.
- **S1, price alone.** No alert. Used as (i) the probabilistic forecast `p_s(t)` for calibration, and (ii) the
  matched placebo rule: buy the side priced in the same band at a uniformly random time.
- **S5, collective shift restricted to wallets with an independently observed financial link.** Population scale:
  **UNRESOLVED, not tested** (no on-chain funding reconstruction at this scale). Documented cohort only,
  descriptive.

### Declared threshold sweep (part of the test family, not a rescue)

Primary values above, plus three declared cells: `(250 USD, 1,500 USD total, 3 wallets, W=60 min)`,
`(500, 3,000, 4 wallets, 60 min)`, `(500, 3,000, 3 wallets, W=180 min)`.

## Outcome and executable reading

- **Label:** `win_s = 1` iff `winner == s`, joined after freezing.
- **Calibration:** `excess_s = rate(win_s) − mean(p_s(t))` at alert time.
- **Executable reading.** Gross result per share bought at `p_s(t)`: `+ (1 − p_s)` on a win, `− p_s` on a loss.
  The historical **order book is not archived**: ask, depth and spread at the alert second are unknowable here, so
  the execution price is the last **executed** price and the result is reported across a declared slippage grid
  `{0, 0.005, 0.01, 0.02, 0.05}`. Replacing the ask by a midpoint is forbidden; no midpoint is used anywhere.
  The report states the break-even slippage and the share of the edge that execution consumes.
- **Prospective simulation (no real order):** the same rule run on the most recent 30 days of the sample, recorded
  as a paper-trading log with a fixed, declared size.

## Statistical protocol

- **Unit:** one alert `(market, side, t)`. **Clusters:** the event (`event_id`) and the market; confidence intervals
  resample whole events (10,000 draws), because markets of one event are not independent.
- **Declared tests (8), all one-sided where an excess is claimed:**
  - **T1** S4 win rate vs the price at the alert (exact binomial against `mean p`, event-clustered bootstrap).
  - **T2** S4 minus S1 matched placebo (price band ±0.05, random time), event-clustered bootstrap.
  - **T3** S4 minus S2 (naive buy consensus), event-clustered bootstrap.
  - **T4** S4 minus S3 (individual shift), event-clustered bootstrap.
  - **T5** S4 net gross result at 1 % slippage > 0 (event-clustered bootstrap of the mean payoff).
  - **T6** S4b minus S4 (does the two-sided exclusion matter?).
  - **T7** S4 alerts in TEST only: win rate vs price (the out-of-sample verdict, no re-fitting).
  - **T8** the declared threshold sweep: 3 cells, reported as 3 comparisons inside the family.
- **Correction:** Bonferroni `0.05 / 10` over the 8 tests and 3 sweep cells (10 comparisons); Benjamini–Hochberg at
  `q = 0.05` reported alongside. A test counts as SUPPORTED only if it passes Bonferroni **and** survives BH.
- **Positive control, before the freeze.** Synthetic tapes of 2,000 fills are generated with a planted collective
  shift (3 wallets, ≥ 3,000 USD, same side, inside 10 minutes) and identical tapes without it. The detector must fire
  on ≥ 90 % of 200 planted tapes and on ≤ 5 % of 200 null tapes, or the code is not used.
- **Chronology.** `TRAIN` closed 2025-01-01 → 2025-12-31, `VALID` 2026-01-01 → 2026-06-30, `TEST`
  2026-07-01 → 2026-10-31. No threshold, filter or rule may change after TEST is read. Results are reported per
  split, and the verdict is taken on TEST (T7).
- **Selection.** The sample is fixed by hash before any rate; the Iran cohort is excluded; documented cases are
  excluded from rates by construction (they are not in the sample selection rule, and their condition ids are
  listed and removed).

## Verdict, wording fixed before the results

- `EXPLOITABLE`, T7 passes after correction, the mean gross result at 1 % slippage is positive in TEST, and TEST has
  ≥ 30 alerts.
- `NOT_SUPPORTED`, T7 does not pass, with ≥ 30 alerts in TEST (the sample can see an effect of the declared size).
- `INCONCLUSIVE`, fewer than 30 alerts in TEST; the sample cannot separate the hypothesis from noise.

## Limits declared now

- Fills only: no splits, merges, redemptions, conversions; net-of-fills exposure is an upper bound on true inventory.
- No historical order book: execution at the executed price with a declared slippage grid; spread and depth unknown.
- Markets below 1 M USD volume only; the deepest tapes are excluded by the page cap, and that tail is where large
  coordinated positions are most likely to hide.
- Outcome-based exclusions of the population remain those of 13 November 2026 and are not audited again here.
- The 763-market sample is 2.2 % of the population; event clustering bounds the effective n.
