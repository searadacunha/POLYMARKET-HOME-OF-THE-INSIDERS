# Methods reuse, five external Polymarket repositories read against this investigation

**Date: 2026-11-17. Mission 2 of 7. Read-only: nothing here was implemented, run or copied.**

This note reads the code of five public repositories, not only their READMEs, and decides for each method whether it
should be **ADOPT**ed (usable as is, at the level of the idea or a trivial rule), **ADAPT**ed (useful, but only after a
stated correction) or **REJECT**ed. The criterion is not "more data" but "can this method refute something we claim
or assume". It builds on the 16 November first pass
([`research_notes/collective-exposure-methods-2026-11-16/EXTERNAL_METHODS.md`](../../research_notes/collective-exposure-methods-2026-11-16/EXTERNAL_METHODS.md),
branch `research/collective-exposure-methods-20261116`), which worked from documentation; this one works from code.

Mission 1 (`BASELINE_AUDIT.md`, written outside the repository because `git worktree add` was refused by
`protocol_guard`) found that this branch already holds a complete study, verified the archived 20/36 vs 16/733
baseline, and listed the open items: S5 funding graph, book recorder, markets ≥ 1 M USD, splits / merges / conversions,
V1-era coverage, a stale `tapes2.sqlite` manifest and a 175,997 vs 217,997 typo in `FINDINGS.md`. This note maps the
external methods onto those items.

The investigation itself is closed (`STATUS.md`: `DONE`, verdict `NOT_SUPPORTED` on the replication). Nothing below
changes its frozen protocol. Any method marked ADOPT or ADAPT can only enter through a new dated amendment or a new
study decided by Benjamin.

## Pinned versions read

| Repository | Commit read | Licence file | What GitHub reports |
|---|---|---|---|
| [SoweluAvanzo/intelliFi_anomaly_detection](https://github.com/SoweluAvanzo/intelliFi_anomaly_detection/tree/a1707ad4b1d25aac9300eff0f582bd6a9f223fc3) | `a1707ad4b1d25aac9300eff0f582bd6a9f223fc3` | none | no licence |
| [TheophilusChinomona/polymarket-intel](https://github.com/TheophilusChinomona/polymarket-intel/tree/6d530aa1cd3efe8f208520019c7b9b5bdf5c452a) | `6d530aa1cd3efe8f208520019c7b9b5bdf5c452a` | none | no licence |
| [darrnhard/polymarket-smart-money](https://github.com/darrnhard/polymarket-smart-money/tree/5c9be8be7b3790095ff65aa332dc9c0901f96abe) | `5c9be8be7b3790095ff65aa332dc9c0901f96abe` | none (README shows an "MIT" badge only) | no licence |
| [ScrapingBee/polymarket-api](https://github.com/ScrapingBee/polymarket-api/tree/10e18702fb1341634d1aeeb39f03f5abe20bc95d) | `10e18702fb1341634d1aeeb39f03f5abe20bc95d` | `LICENSE` | MIT |
| [PerlanLabs/polymarket-paper-trader](https://github.com/PerlanLabs/polymarket-paper-trader/tree/b3839cf37d4f448d18ae917b0a8cc546796c1227) | `b3839cf37d4f448d18ae917b0a8cc546796c1227` | `LICENSE` | MIT |

Files were read through the GitHub API at these commits. No repository was cloned, installed or executed.

## Reported versus reproduced

**No external result has been reproduced by this note.** Every figure quoted from these repositories below is
*author-reported*. Their raw data are not in git (intelliFi's parquet store, smart-money's parquet files), or are live
snapshots that cannot be replayed (ScrapingBee, PerlanLabs). None of them enters a FINDING of this repository.

| Repository | Headline claim in its README / overview | Status here |
|---|---|---|
| intelliFi | Co-trading, lead–lag and mirroring are null against an activity-preserving null and a matched placebo; "every backtest leader set equals its matched control" on the full v2 tape (`PROJECT_OVERVIEW.md`) | author-reported, not reproduced; code read and consistent with the described method |
| polymarket-intel | Wallets scored "by win rate, P&L and volume"; consensus signals | no performance figure is claimed; nothing to reproduce |
| smart-money | "sovereign leads rn1 and swisstony in 68–82 % of shared markets, by a median of 160–400 minutes"; 6.8 M events | author-reported, not reproduced; the computation behind it is read below and is descriptive only |
| ScrapingBee | Fed ladder "monotonic", negRisk book sum 1.088 and 1.007 on 2026-10-29 | live snapshot, not reproducible by construction |
| PerlanLabs | "My AI agent hit +18 % ROI on Polymarket in one week" | marketing quote, no protocol; not a result |

---

## 1. intelliFi_anomaly_detection

### What the code actually does

- **Co-trading with an activity-preserving null.**
  [`coordination.py` `cotrade_pairs`](https://github.com/SoweluAvanzo/intelliFi_anomaly_detection/blob/a1707ad4b1d25aac9300eff0f582bd6a9f223fc3/src/intellifi/coordination.py#L33)
  counts, for every wallet pair, the fixed 300 s buckets in which both traded the same `asset_id` on the same side.
  [`cotrade_pairs_with_null`](https://github.com/SoweluAvanzo/intelliFi_anomaly_detection/blob/a1707ad4b1d25aac9300eff0f582bd6a9f223fc3/src/intellifi/coordination.py#L277)
  sets the expectation per (asset, side) stratum to `k_a · k_b / B` (each wallet's number of active buckets, over the
  stratum's occupied buckets), sums it over strata, and returns a Poisson upper-tail p and Benjamini–Hochberg q.
- **Lead–lag with the same null.**
  [`leader_lag_pairs`](https://github.com/SoweluAvanzo/intelliFi_anomaly_detection/blob/a1707ad4b1d25aac9300eff0f582bd6a9f223fc3/src/intellifi/coordination.py#L99)
  pairs every wallet in one distinct trading second with every other wallet in the *next* distinct second on the same
  (asset, side), within 600 s; same-second trades are treated as simultaneous.
  [`leader_lag_pairs_with_null`](https://github.com/SoweluAvanzo/intelliFi_anomaly_detection/blob/a1707ad4b1d25aac9300eff0f582bd6a9f223fc3/src/intellifi/coordination.py#L341)
  uses `k_a · k_b · S_adj / S²`.
- **Rapid flips, not wash.**
  [`wash_round_trips`](https://github.com/SoweluAvanzo/intelliFi_anomaly_detection/blob/a1707ad4b1d25aac9300eff0f582bd6a9f223fc3/src/intellifi/coordination.py#L170)
  matches each BUY to its nearest SELL of the same wallet and asset within 600 s and ≥ 50 % size overlap, one-to-one,
  and attaches a maker profile (buy fraction, median price) so tick-scalping market makers are not called wash.
- **Mirror backtest and placebo.**
  [`backtest.py` `matched_control_events`](https://github.com/SoweluAvanzo/intelliFi_anomaly_detection/blob/a1707ad4b1d25aac9300eff0f582bd6a9f223fc3/src/intellifi/backtest.py#L139)
  draws up to three trades by non-universe wallets on the same asset and side, ±900 s and ±0.05 in price, selected by a
  hash of the tx id. [`run_events`](https://github.com/SoweluAvanzo/intelliFi_anomaly_detection/blob/a1707ad4b1d25aac9300eff0f582bd6a9f223fc3/src/intellifi/backtest.py#L255)
  enters at the next minute-VWAP 60 s later, exits at a horizon or at the payout, charges 20 bps per side.
  [`summarise_backtest`](https://github.com/SoweluAvanzo/intelliFi_anomaly_detection/blob/a1707ad4b1d25aac9300eff0f582bd6a9f223fc3/src/intellifi/backtest.py#L350)
  reports a per-market mean and its standard error (clustered by market).
- **Counterparties.** The Stage-I feed is the data-api taker side only (stated in `PROJECT_OVERVIEW.md` and
  `REPRODUCING.md`). Stage II rebuilds the full maker/taker tape from on-chain `OrderFilled` events and checks it
  against the API row by row (12,532 / 12,532 on five markets, author-reported).
  [`scripts/42_self_dealing.py`](https://github.com/SoweluAvanzo/intelliFi_anomaly_detection/blob/a1707ad4b1d25aac9300eff0f582bd6a9f223fc3/scripts/42_self_dealing.py)
  deduplicates on `(tx_hash, evt_index)` and flags a transaction as self-dealing when one wallet is maker in one fill
  and taker in another fill of the same transaction.

### Biases and limitations found in the code

1. **The analytic null assumes uniform placement inside a stratum.** `k_a · k_b / B` ignores that activity in one
   market clusters around news. Two wallets that both react to the same headline co-occur far above this null without
   any coordination. The null is conservative only against wallets that are merely *active*, not against wallets that
   are *reactive to the same public clock*.
2. **BH family is conditioned on the outcome of the count.** q-values are computed over pairs with at least one
   co-trade event (`min_pair_events=1` before the BH step), so the zero-event pairs, which would contribute p = 1, are
   dropped from the family. That makes BH more permissive than the declared family.
3. **Outcome-dependent filter in the backtest.**
   [`build_event_ts_view`](https://github.com/SoweluAvanzo/intelliFi_anomaly_detection/blob/a1707ad4b1d25aac9300eff0f582bd6a9f223fc3/src/intellifi/backtest.py#L115)
   defines the cut-off as the last trade where *the eventual winner* was still below 0.95. Which trades survive
   therefore depends on the outcome. The authors use it to remove settlement noise, but it is a look-ahead filter and
   cannot be used to form a sample.
4. **The matched placebo is near-tautological when held to resolution.** Same asset, same side, ±0.05 price, same
   outcome: with exit at the payout, leader and control returns differ by at most the price gap. It is informative for
   the short horizons only.
5. **Stage-I sample**: top-100 markets by volume, universe built from top PnL and top calibration gap (selection on the
   dependent variable), 92 of 100 markets capped at ~4,000 fills (author-reported). The overview itself says so.

### What already exists in this repository

| intelliFi element | Here | Where |
|---|---|---|
| Outcome joined last, clustered inference | yes, event-clustered bootstrap, 10,000 draws | `scripts/score.py`, `scripts/stats.py` (`cluster_bootstrap`) |
| BH + Bonferroni over a declared family | yes, family fixed before the run (10 comparisons) | `scripts/stats.py` (`bh`), `analysis_plan.md` |
| Matched placebo | yes, within the alert's own market, same side, ±0.05, ≥ 6 h away | `amendements/003-2026-11-16-within-market-placebo.md` |
| Two-sided / market-maker exclusion | yes, `g_win ≥ 5 × net` rule, S4b variant keeps them | `scripts/build_alerts.py` (`two_sided`) |
| Activity-preserving null for co-occurrence | **no** | , |
| Tape validated against on-chain `OrderFilled` | **no** for the study's tapes (data-api `v2/trades?taker_only=false`, cursor pagination). The decoder exists on `main` for CTF Exchange V2 and NegRisk Exchange V2 only; no V1 decoder (mission 1, section 6) | `scripts/collect_tapes.py`; [`monitoring/phi_monitor/chain.py`](../../monitoring/phi_monitor/chain.py) on `main` |
| Self-dealing / same-tx both-sides check | **no** | , |

### What would be genuinely new

- **N1, tape validity (highest priority).** Our exposure `X = q(YES) − q(NO)` assumes the `taker_only=false` tape
  carries every fill of every wallet once. That has not been checked against the chain. Reconciling a hash-drawn
  sample of markets against `OrderFilled` (dedup `(tx_hash, log_index)`) can *refute the measure itself*: missing
  maker legs, a wallet counted on both legs of one transaction, or exchange-synthetic rows would bias exposure, and the
  F-003/F-009 nulls would then be nulls of a wrong variable.
- **N2, is "collective" more than chance co-activity?** The study tests whether S4 predicts outcomes; it never tests
  whether S4 groups are rarer than independent activity would produce. A null that keeps each wallet's own activity and
  breaks only the alignment can refute the premise that S4 detects coordination at all.

### Decision

| Method | Decision | Justification |
|---|---|---|
| Activity-preserving null for co-occurrence | **ADAPT** | Keep the idea (preserve each wallet's activity, break alignment). Replace the analytic `k·k/B` Poisson by a permutation null that circularly shifts each wallet's exposure series inside its market (keeps burstiness and news clustering); compute BH over the full declared family including zero counts. |
| On-chain `OrderFilled` reconciliation and same-tx both-sides check | **ADAPT** | Highest refutation value (N1). Reuse our own V2 decoder (`phi_monitor/chain.py`); a V1-exchange decoder is missing and is needed for the 2025 part of the population (mission 1 left V1 coverage unverified). Do not reuse their parquet or Dune queries. |
| Rapid-flip one-to-one matching with maker profile | **ADAPT** (low priority) | Useful as a *diagnostic* of our two-sided rule (are excluded wallets really makers?), not as a signal. |
| Same-moment matched placebo (±900 s) | **REJECT** | For hold-to-resolution it collapses onto T1. Our within-market, different-moment placebo (amendment 003) is the stricter test. |
| Mirror backtest with `market_event_ts` | **REJECT** | The cut-off uses the winning outcome; it is a look-ahead filter. |
| Flat 20 bps fee | **REJECT** | Fees depend on price and on the market's rate (see PerlanLabs below and intelliFi's own `docs/FEE_EFFECTS.md`). |

### Licence and attribution

No licence file: all rights reserved by default. **No code may be copied.** Methods (an activity-preserving null,
one-to-one flip matching, on-chain reconciliation) are general ideas and may be reimplemented; cite the repository
and commit as the source of the idea whenever one is used.

---

## 2. polymarket-intel

### What the code actually does

- [`analysis/correlation.py`](https://github.com/TheophilusChinomona/polymarket-intel/blob/6d530aa1cd3efe8f208520019c7b9b5bdf5c452a/analysis/correlation.py#L60)
  keeps **only `side == "BUY"`** trades, drops prices outside 0.05–0.95 and 5/15-minute crypto markets, keeps wallets
  whose stored score is ≥ 0.3, groups by `(slug, outcome)` over the last 6 h, and fires when ≥ 3 distinct wallets
  appear. Strength is a fixed linear mix (`0.4·n_wallets + 0.3·avg_score + 0.2·size/100 + 0.1·(1−|p−0.5|)`,
  [L108](https://github.com/TheophilusChinomona/polymarket-intel/blob/6d530aa1cd3efe8f208520019c7b9b5bdf5c452a/analysis/correlation.py#L108)).
  Input is the newest 5,000 stored trades
  ([L47](https://github.com/TheophilusChinomona/polymarket-intel/blob/6d530aa1cd3efe8f208520019c7b9b5bdf5c452a/analysis/correlation.py#L47)).
- [`analysis/wallet_scorer.py`](https://github.com/TheophilusChinomona/polymarket-intel/blob/6d530aa1cd3efe8f208520019c7b9b5bdf5c452a/analysis/wallet_scorer.py#L37)
  scores each wallet from **all markets resolved at scoring time**, trade by trade.
- [`simulation/paper_trader.py`](https://github.com/TheophilusChinomona/polymarket-intel/blob/6d530aa1cd3efe8f208520019c7b9b5bdf5c452a/simulation/paper_trader.py#L74)
  sets `est_win_prob = min(0.8, 0.5 + 0.02·n_wallets + 0.01·strength)` and enters when that "EV" is positive.

### What rests only on BUY

Everything that produces a signal: the consensus itself, the wallet count, the size and the average price. A wallet
that sells YES or buys NO in the same window is invisible; a wallet that buys YES to close a short leaves the signal
unchanged. The only place SELL enters is the score, and it is mis-accounted
([L80](https://github.com/TheophilusChinomona/polymarket-intel/blob/6d530aa1cd3efe8f208520019c7b9b5bdf5c452a/analysis/wallet_scorer.py#L80)):
a SELL of the winning outcome is booked as a "missed" loss of `size·(1−price)` and a SELL of the loser as a gain of
`size·price`, with no reference to the entry price or to the position that was sold.

### Biases and limitations

1. **Look-ahead if replayed.** Scores use every market resolved *at scoring time*; a historical evaluation of signals
   would use wallet records that include the evaluated outcomes.
2. **Per-trade, not per-position scoring**: a wallet that splits one bet into 50 fills counts 50 times.
3. **Silent truncation and silent failure.** The 5,000-row cap drops trades without a count; every HTTP failure path in
   [`api/trades.py`](https://github.com/TheophilusChinomona/polymarket-intel/blob/6d530aa1cd3efe8f208520019c7b9b5bdf5c452a/api/trades.py#L52)
   returns `[]`, indistinguishable from "no trades".
4. **The win probability is not estimated**, it is a formula with fixed coefficients; any "EV" filter on it is circular.
5. **Paper P&L is biased by construction.** Orphaned positions are forced to a loss
   ([L191](https://github.com/TheophilusChinomona/polymarket-intel/blob/6d530aa1cd3efe8f208520019c7b9b5bdf5c452a/simulation/paper_trader.py#L191));
   the 2 % fee is charged on the *exit* value
   ([L124](https://github.com/TheophilusChinomona/polymarket-intel/blob/6d530aa1cd3efe8f208520019c7b9b5bdf5c452a/simulation/paper_trader.py#L124)),
   so a losing position pays no fee and a winning one pays 2 % of the payout.

### What already exists in this repository

The comparator **S2, naive buy consensus** (≥ 3 buyers, ≥ 3,000 USD, no exposure requirement) is this detector minus
the score and the 6-hour window. It was tested: T3, S4 vs S2, −0.56 pt on the primary sample and −1.41 pt on the
replication, both null (`README.md`, `results/tests.json`, `results/replication_tests.json`).

### What would be genuinely new

Only a **point-in-time skill-weighted** consensus: count a wallet only if its record *strictly before the alert*
(positions, not trades; resolved before the alert) is positive. That is a different hypothesis ("consensus of
previously good wallets"), not a variant of S4, and it would need its own frozen protocol.

### Decision

| Method | Decision | Justification |
|---|---|---|
| BUY-only consensus as a signal | **REJECT** | Already present as comparator S2, and already beaten by nothing (T3 null). Not a candidate signal. |
| Wallet score (`wallet_scorer.py`) | **REJECT** | Look-ahead when replayed, per-trade weighting, wrong SELL accounting. |
| Paper trader | **REJECT** | Heuristic win probability, loss-forced orphans, fee on exit. |
| Point-in-time skill-weighted consensus (idea only) | **ADAPT**, low priority | Refutable as a new hypothesis if scores use only positions resolved before the alert; new study, not an amendment. |

### Licence and attribution

No licence file: no code may be copied. Nothing here is worth copying anyway.

---

## 3. polymarket-smart-money

### What the code actually does

The code lives in two notebooks.
[`notebooks/01_fetch.ipynb`](https://github.com/darrnhard/polymarket-smart-money/blob/5c9be8be7b3790095ff65aa332dc9c0901f96abe/notebooks/01_fetch.ipynb):

- **Collection** is per wallet from data-api `/activity` (types TRADE, SPLIT, MERGE, REDEEM, REWARD, MAKER_REBATE),
  in 7-day windows, `offset` pagination by 500 up to a self-imposed cap of 3,000 (`fetch_window`). When a window
  overflows it is **bisected recursively** down to a 1-hour floor (`fetch_recursive`).
- **Resume** uses a JSON ledger of completed `[start, end]` windows; each window is written to parquet and then marked
  done (`fetch_activity_full`).
- **Lead/follow** in
  [`notebooks/02_analysis.ipynb`](https://github.com/darrnhard/polymarket-smart-money/blob/5c9be8be7b3790095ff65aa332dc9c0901f96abe/notebooks/02_analysis.ipynb)
  ("Lead / follow timing analysis") takes, for each pair of the three wallets, the **minimum TRADE timestamp per
  `conditionId`** and counts which is earlier.

### Biases and limitations found in the code

1. **Dedup by transaction hash loses fills.** `fetch_window` keys records on `transactionHash` and `save_chunk`
   deduplicates on it. One transaction can carry several fills (several price levels, or several markets): all but one
   are silently dropped. The fallback key for empty hashes also differs between the two functions (`type` is omitted
   in `fetch_window`).
2. **An overflow at the 1-hour floor becomes a permanent gap.** `fetch_recursive` logs "data may be incomplete" and
   returns the truncated records; `fetch_activity_full` then marks the window done in the ledger, so a resumed run will
   never fetch it again.
3. **Lead/follow has no comparator and no null.** First entry ignores side, outcome and size; three wallets were
   selected from the leaderboard for performance; a 160–400-minute median gap is what two wallets on a different
   schedule produce without any following.
4. The README itself says (author-reported, not verified here) that auto-redeemed winning positions produce no REDEEM
   event, so P&L from `/activity` alone misclassifies about 99 % of markets as open.

### What already exists in this repository

- **Collection**: `scripts/collect_tapes.py` uses `v2/trades?condition=…` with cursor pagination, asserts newest-first
  order on every page, records a capped market as `too_deep` (never as empty) and keeps a resumable per-market status
  table. That is already stricter than the ledger above on both defects (no silent cap, no hash-only dedup).
- **Timing**: the S4 rule works inside a 1-hour window at 900 s steps; the "who moved first" question is not asked.

### What would be genuinely new

- **N3, splits and merges for the alerted wallets.** `/activity` exposes SPLIT, MERGE and (per their notebook) other
  protocol events per wallet. Our declared limit "splits, merges, redemptions and conversions are invisible, so
  exposure is an upper bound" (`STATUS.md`) could be closed **for the wallets that fired an alert only** (266 replication
  alerts, ≥ 3 wallets each), which is bounded. That can refute alerts whose "exposure increase" is in fact the sold leg
  of a split (a wallet that mints YES+NO and sells NO looks like a YES buyer on the trade tape without having bought).

### Decision

| Method | Decision | Justification |
|---|---|---|
| Per-wallet `/activity` read for split/merge/conversion events | **ADAPT** | N3. Bounded to alert wallets; must use a composite key (tx hash + log index or full row) and must refuse, not mark done, any window that overflows. |
| Time-window bisection with ledger | **ADAPT** (only if N3 is run) | Sound idea for the per-user endpoint, after fixing the two defects above. Not needed for per-market tapes, where our cursor collector already works. |
| First-entry lead/follow | **REJECT** | Three preselected wallets, no null, no comparator, side- and size-blind. The 68–82 % claim is not reproducible from git (data excluded). |

### Licence and attribution

No licence file; the README badge says "MIT" but no licence text is distributed. Treat as **unlicensed: no code
copying**. Cite the repository for the bisection idea if N3 is implemented.

---

## 4. ScrapingBee polymarket-api

### What the code actually does

[`examples/polymarket_client.py`](https://github.com/ScrapingBee/polymarket-api/blob/10e18702fb1341634d1aeeb39f03f5abe20bc95d/examples/polymarket_client.py)
reads Polymarket event pages through the paid ScrapingBee proxy and decodes the embedded event JSON.
[`examples/polymarket_analysis.py`](https://github.com/ScrapingBee/polymarket-api/blob/10e18702fb1341634d1aeeb39f03f5abe20bc95d/examples/polymarket_analysis.py#L94):

- for `negRisk` events with more than one market, sums the Yes prices (should be ≈ 1);
- for **every non-negRisk event with more than two markets**, sorts the markets by `end_date` and calls the event
  "NOT monotonic" if any step falls by more than 0.005
  ([L98](https://github.com/ScrapingBee/polymarket-api/blob/10e18702fb1341634d1aeeb39f03f5abe20bc95d/examples/polymarket_analysis.py#L98)).

### Biases and limitations

1. **Any non-negRisk multi-market event is assumed to be a deadline ladder.** A threshold ladder ("above 3 %",
   "above 4 %") should *decrease*, and unrelated sibling markets have no order at all. The code never reads the
   resolution text; nesting is inferred from `negRisk = false` and `end_date`.
2. The 0.005 tolerance is fixed and ignores spread; the price used is the displayed Yes price, not bid/ask.
3. **Snapshots only.** No history, page cache `s-maxage=300` (stated in the README); nothing can be replayed at an
   alert time. The README itself recommends Gamma for the same data.

### What already exists in this repository

`scripts/interval_reading.py` (F-007) groups markets by `event_slug`, orders them by `closed_ts` and reads each wallet's
closing YES-equivalent position per deadline. **It has the same blind spot**: it treats every event with two or more
closing times as a deadline family without checking rule equivalence or nesting. `INTERVAL_LOGIC.md` in the
16 November note states the requirement ("do not infer nesting from similar titles or matching `endDate`") but no code
enforces it.

### What would be genuinely new

- **N4, a semantic gate for interval readings.** Before any NO(D1) + YES(D2) is called an interval package: same
  resolution text up to the date, D1 < D2, `negRisk = false`, and **price monotonicity at the moment of the reading**
  (Yes(D1) ≤ Yes(D2) within the spread). A ladder that fails it cannot be read as nested, and F-007's 60 qualifying
  events would have to be re-counted on the gated subset.
- **N5, coherence as an alternative explanation.** A collective shift on one rung that *restores* monotonicity with its
  neighbours is arbitrage on an incoherent ladder, not information. Testing whether S4 alerts on ladder events coincide
  with pre-alert incoherence is a refutation of the "informed group" reading that needs no new data beyond prices
  already in the tapes.

### Decision

| Method | Decision | Justification |
|---|---|---|
| `negRisk` decides which sums mean anything | **ADOPT** | A one-line rule on Gamma metadata; no code to copy. |
| Monotonicity check of deadline ladders | **ADAPT** | N4 and N5, but only after verifying nesting from the resolution text, with a spread-aware tolerance and prices taken at the alert time from our own tapes. |
| Scraping event pages through ScrapingBee | **REJECT** | Paid, cached, snapshot-only; Gamma serves the same fields directly (the README says so). |

### Licence and attribution

MIT. Copying any portion requires keeping the copyright notice and licence text. The monotonicity check is three lines
and should be rewritten rather than copied; credit the repository for the idea.

---

## 5. PerlanLabs polymarket-paper-trader

### What the code actually does

- **Live fills against the real book.** [`engine.py`](https://github.com/PerlanLabs/polymarket-paper-trader/blob/b3839cf37d4f448d18ae917b0a8cc546796c1227/pm_trader/engine.py)
  fetches `/book` (never cached,
  [`api.py` L317](https://github.com/PerlanLabs/polymarket-paper-trader/blob/b3839cf37d4f448d18ae917b0a8cc546796c1227/pm_trader/api.py#L317))
  and the token's fee rate (`/fee-rate`, cached 5 min,
  [L327](https://github.com/PerlanLabs/polymarket-paper-trader/blob/b3839cf37d4f448d18ae917b0a8cc546796c1227/pm_trader/api.py#L327)),
  then [`orderbook.py` `simulate_buy_fill`](https://github.com/PerlanLabs/polymarket-paper-trader/blob/b3839cf37d4f448d18ae917b0a8cc546796c1227/pm_trader/orderbook.py#L72)
  walks the asks level by level for a USD amount, FOK or FAK, returns average price, levels consumed and slippage
  against the midpoint.
- **Fee** ([`calculate_fee`](https://github.com/PerlanLabs/polymarket-paper-trader/blob/b3839cf37d4f448d18ae917b0a8cc546796c1227/pm_trader/orderbook.py#L17)):
  `fee_rate_bps / 10,000 · min(p, 1 − p) · size`, minimum 0.0001. The code calls it "the exact Polymarket formula";
  **not verified here** against Polymarket's documentation.
- **Historical backtest** ([`backtest.py` `_build_synthetic_book`](https://github.com/PerlanLabs/polymarket-paper-trader/blob/b3839cf37d4f448d18ae917b0a8cc546796c1227/pm_trader/backtest.py#L89)):
  a **synthetic** three-level book around a supplied midpoint, spread 0.02 and depth 500 per level by default.

### Biases and limitations

1. **Live mode is realistic about depth, not about time.** The book is read when the simulated order is placed: no
   latency, no queue position, no impact on later fills, and the simulated order never removes liquidity for the next
   one.
2. **Backtest mode is a function of its assumptions.** With a fixed 0.02 spread and 500-share levels, its P&L says
   nothing about execution on a thin market; it is not a test of anything.
3. The fee rate is the *current* rate of the token. A historical study cannot recover the rate in force at an old alert
   from this endpoint (intelliFi's `docs/FEE_EFFECTS.md` documents a fee rollout, so rates changed over the period).
4. In what was read, the book used for each simulated fill is not stored with the trade; a paper result could not be
   audited afterwards (not exhaustively checked across `db.py`).

### What already exists in this repository

F-005 and F-008: execution is not verifiable from archived data; T5 uses the last executed price plus a declared
slippage grid (0–5 %), with fees and gas excluded, which `FINDINGS.md` already calls optimistic. F-008 names "a
prospective recorder (the repository's own live collector)". That collector is
[`monitoring/livecollect/`](../../monitoring/livecollect/README.md) on `main` (not on this branch): it already records the
book from the CLOB market WebSocket and the trades from `v2/trades`, with gap and coverage files, but for a **fixed
list of 20 markets** chosen on 13 November, not for markets where S4 fires, and it does not compute a fill for a
declared size.

### What would be genuinely new

- **N6, a fillable price at the alert.** Walking the recorded book for a declared size at each live S4 alert turns the
  gross F-005 reading into an executable one, and can refute the prospective signal. The book recording already exists
  (`livecollect`); what is new is the market selection (markets where S4 fires, not a fixed list) and the walk itself.
  This is the only way to close F-008; it cannot be done retrospectively.
- **N7, fees in T5.** Applying a price-dependent fee (`rate · min(p, 1 − p)`) on a *declared grid of rates* would
  remove the "optimistic" caveat from the retrospective payoff without pretending to know the historical rate.

### Decision

| Method | Decision | Justification |
|---|---|---|
| Level-by-level book walk at alert time, with the book stored | **ADAPT** | N6, prospective only; must persist the raw `/book` JSON and its fetch time next to the alert, and declare a latency. |
| Price-dependent fee on a declared rate grid | **ADAPT** | N7; formula to be checked against Polymarket's own fee documentation first, and the rate grid declared, never read from today's `/fee-rate` for past alerts. |
| Synthetic-book backtest | **REJECT** | Fixed spread and depth decide the result. |
| Paper P&L / leaderboard figures | **REJECT** | No protocol, no stored book, marketing claim. |

### Licence and attribution

MIT. Copying any portion requires keeping the copyright notice and licence text in the copied file. A book walk is
about thirty lines; rewrite it and credit the repository.

---

## Synthesis, ranked by refutation power

| # | Candidate | From | Can refute | Data needed | Decision |
|---|---|---|---|---|---|
| N1 | Reconcile the `taker_only=false` tape against on-chain `OrderFilled`; check same-tx both-sides wallets | intelliFi | the exposure variable behind F-003, F-004, F-009 | hash-drawn sample of already sampled markets, Polygon logs | ADAPT |
| N3 | Split / merge / conversion events for alerted wallets | smart-money (`/activity`) | individual alerts whose exposure gain is a sold split leg | per-wallet `/activity`, bounded to alert wallets | ADAPT |
| N2 | Permutation null for S4 co-occurrence | intelliFi | the premise that S4 detects coordination rather than shared reaction | existing tapes only | ADAPT |
| N4 | Semantic and monotonicity gate before interval readings | ScrapingBee | F-007's event count and every NO(D1)+YES(D2) reading | resolution text (Gamma), existing tapes | ADAPT |
| N5 | Alerts that restore ladder coherence | ScrapingBee | the "informed group" reading on ladder events | existing tapes | ADAPT |
| N6 | Book walk at live alerts | PerlanLabs | prospective executability | `livecollect` book stream, extended to markets where S4 fires | ADAPT |
| N7 | Price-dependent fees on a declared grid | PerlanLabs | the optimistic gross T5 | none new | ADAPT |
| , | Point-in-time skill-weighted consensus | polymarket-intel | a different hypothesis | positions resolved before each alert | ADAPT, low priority |

Rejected outright: intelliFi's mirror backtest (outcome-dependent cut-off) and same-moment placebo (redundant with T1),
polymarket-intel's score, BUY-only signal and paper trader, smart-money's first-entry lead/follow, ScrapingBee's scraping
route, PerlanLabs' synthetic-book backtest.

Not novel and already covered here: event-clustered inference, BH plus Bonferroni over a declared family, outcome
joined last, within-market placebo, BUY-only consensus as a comparator, two-sided wallet exclusion, cursor pagination
with explicit cap status.

## Limits of this note

- Code was read, not run. No external figure is reproduced, and none should be quoted as a result of this repository.
- Reading was targeted at the five themes of the mission. In intelliFi (261 files) the Stage-II fee and maker-economics
  study was not reviewed beyond the files cited; PerlanLabs' web stack (`pm_trader/web/`) and `db.py` were not read in
  full.
- Licence status is taken from the files present at the pinned commits and from GitHub's licence detection; it is not
  legal advice.
- Whether our `taker_only=false` tape already contains both legs of each fill exactly once is **not verified**; N1 exists
  to settle it.
