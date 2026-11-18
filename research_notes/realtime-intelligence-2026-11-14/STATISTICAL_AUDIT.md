# Statistical audit of the frozen study, after its results

14 November 2026. **Exploratory**: everything on this page was computed after the results of the frozen study were
read. It computes no new p-value, changes no class, test, threshold or verdict, and the verdicts of
[RESULTS.md](RESULTS.md) stand as frozen. It asks how much those verdicts can carry: power, simultaneous intervals,
corrections, dependence between events, timing, fees, and the price somebody alerted could really have paid.

The numbers come from `scripts/audit_after_results.py`: `offline` reads only the published tables
(`data/study_export/alerts.jsonl`, the registry) and writes `data/audit_after_results.json`, which `verify.py` recomputes;
`local` reads the study's fills of 1,000 USD or more and its frozen analytic table, which name wallets and are not
published, refits M3 with the frozen code to rebuild the alerts, and writes `data/audit_accessible_prices.json`. The tables below are rendered from those two files (`render --check`). Population:
VALIDATION x INFO, one alert per event, as in the tests.

## Power and simultaneous intervals

<!-- audit:power -->
| Class | Alert events | Excess, points | 95 % interval (published) | Simultaneous interval, 63 comparisons | Detectable at the corrected threshold | Detectable at 0.05 | Power for +5 points, corrected |
|---|---:|---:|---|---|---:|---:|---:|
| C1_FRESH_FUNDED_BET | 360 | -3.7 | -8.3 to +0.7 | -11.4 to +4.0 | 8.8 | 5.5 | 0.19 |
| C2_DORMANT_REACTIVATION | 154 | +4.6 | -2.1 to +11.5 | -7.0 to +16.3 | 13.6 | 8.5 | 0.05 |
| C3_OUT_OF_CHARACTER | 406 | -1.3 | -5.2 to +2.6 | -7.9 to +5.4 | 8.1 | 5.1 | 0.24 |
| C6_QUIET_FRESH_LOW | 136 | -5.8 | -12.9 to +1.4 | -17.8 to +6.2 | 15.0 | 9.3 | 0.03 |
| C7_HEAVY_NEWCOMER | 95 | -6.7 | -15.7 to +1.7 | -21.7 to +8.3 | 17.0 | 10.6 | 0.02 |
| R1_S_FRESH_REPLICATION | 375 | -6.0 | -10.3 to -1.6 | -13.4 to +1.4 | 8.5 | 5.3 | 0.21 |
| M1_RARITY_TOP1 | 18 | -2.0 | -22.0 to +16.3 | -34.8 to +30.8 | 39.8 | 24.8 | 0.00 |
| M2_IFOREST_TOP1 | 44 | +0.6 | -13.2 to +14.4 | -22.9 to +24.0 | 24.4 | 15.2 | 0.01 |
| M3_EDGE_TOP5 | 14 | +16.0 | -7.2 to +36.8 | -22.8 to +54.8 | 50.9 | 31.6 | 0.00 |
| B1_BIG | 204 | -0.4 | -6.4 to +5.5 | -10.6 to +9.8 | 11.7 | 7.3 | 0.07 |
| B2_AFTER_MOVE | 646 | -2.2 | -5.4 to +1.1 | -8.0 to +3.6 | 6.8 | 4.2 | 0.41 |
| B3_THIN_NOT_FRESH | 156 | +1.3 | -5.2 to +7.8 | -9.9 to +12.6 | 13.4 | 8.3 | 0.05 |
<!-- /audit:power -->

"Detectable" is the excess, in points, that the one-sided test finds 80 % of the time, from the null variance of the
alerted prices (normal approximation of the exact test). The simultaneous interval is the excess plus or minus 3.355
standard errors, the two-sided width that keeps 95 % coverage over the 63 comparisons counted in the registry
(Bonferroni); it ignores the dependence below.

- **At the corrected threshold of 0.00079 the study could only have found large advantages**: 8 to 17 points for the
  classes C1 to C7 and R1, and 40 to 51 points for M1 and M3. Its chance of finding an advantage of 5 points was 2 to
  24 % for those classes.
- **"Effect excluded" holds for C1, R1 and B2 only, once the intervals are made simultaneous.** The frozen label
  `NOT_SUPPORTED_EFFECT_EXCLUDED` uses the 95 % interval of each class alone, as the plan says, and stays the verdict.
  Over 63 comparisons the upper bound is +4.0 points for C1, +1.4 for R1 and +3.6 for B2, but +5.4 for C3, +6.2 for C6
  and +8.3 for C7, which therefore do not exclude 5 points at simultaneous coverage.
- **Corrections other than Bonferroni change nothing.** Over the 44 p-values of the registry that belong to one
  comparison each, with m = 63, the smallest is 0.102 (C2, T1); Holm and Benjamini-Hochberg reject nothing at 0.05.

## Dependence between events, and timing

<!-- audit:dependence -->
| Class | Design effect, day of real close | Design effect, day of scheduled end | 95 % interval, standard error clustered by day of real close | Alert events 0-24 h before the real close | after it |
|---|---:|---:|---|---:|---:|
| C1_FRESH_FUNDED_BET | 0.90 | 0.98 | -8.0 to +0.5 | 25 | 0 |
| C2_DORMANT_REACTIVATION | 1.18 | 1.60 | -2.8 to +12.1 | 8 | 0 |
| C3_OUT_OF_CHARACTER | 1.14 | 0.93 | -5.4 to +2.9 | 22 | 0 |
| C6_QUIET_FRESH_LOW | 0.97 | 0.86 | -12.7 to +1.1 | 5 | 0 |
| C7_HEAVY_NEWCOMER | 1.10 | 1.38 | -15.9 to +2.5 | 6 | 0 |
| R1_S_FRESH_REPLICATION | 1.00 | 1.14 | -10.3 to -1.6 | 25 | 0 |
| M1_RARITY_TOP1 | 1.04 | 1.23 | -21.6 to +17.6 | 1 | 0 |
| M2_IFOREST_TOP1 | 0.92 | 1.29 | -12.6 to +13.7 | 12 | 0 |
| M3_EDGE_TOP5 | 1.37 | 1.21 | -10.5 to +42.5 | 0 | 0 |
| B1_BIG | 1.21 | 0.91 | -6.9 to +6.2 | 10 | 0 |
| B2_AFTER_MOVE | 0.79 | 0.97 | -5.2 to +0.8 | 79 | 0 |
| B3_THIN_NOT_FRESH | 0.98 | 0.92 | -5.1 to +7.8 | 9 | 0 |
<!-- /audit:dependence -->

Inside an event the tests already keep one alert and resample events whole. Between events, outcomes can still move
together: events that end the same day often turn on the same news. The design effect is the squared ratio of the
cluster-robust standard error (alerts grouped by UTC day) to the independent one; above 1, the published intervals are
too narrow by its square root. The interval of the table is the excess plus or minus 1.96 clustered standard errors
(normal approximation); nothing is resampled there.

- **Dependence is moderate and does not move a reading.** Design effects run from 0.79 to 1.60. The largest, 1.60 for C2
  grouped by day of scheduled end, widens its standard error by 26 %; C2's interval with the standard error clustered
  by day of real close, -2.8 to +12.1 points, still holds zero. R1's stays below zero (-10.3 to -1.6), as with weeks
  resampled in RESULTS.md. These intervals are not corrected for the number of comparisons.
- **No alert falls after the real close, and none in its last hour**: the analytic table holds no entry made after
  the real close (`rows_entered_after_real_close` = 0, `study/derived/table_counts.json`); why none falls in the last
  hour was not established. Alerts within 24 hours of the real close are 0 to 79 events per class; RESULTS.md already
  reports the variant without them.
- **A selection that looks ahead: the volume floors.** A market enters the universe when its volume reached
  10,000 USD and its event 50,000 USD, volumes read after the close, so they include trading after the alert. A
  market that stayed thin after a large purchase is outside. The direction of this effect on the excess is not
  known and was not measured; a live alert cannot apply this rule at the time of the purchase.
- **Weeks and rates.** RESULTS.md gives alert events a week over the span of the alerts (3.88 for C1); the table
  of the last section divides by the 30.6 weeks of scheduled ends of VALIDATION (11.8 for C1), which is the rate at
  which a holdout of future events fills.

## Fees, and the price a follower could get

<!-- audit:prices -->
| Class | Excess at the alerted price | after the taker fee | Fee-free share | With a later purchase (6 s) | Without | Without: excess at the alerted price | With: excess at the alerted price | With: at the follower's price, after fee | 95 % interval | Price move, points |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|
| C1_FRESH_FUNDED_BET | -3.7 | -4.1 | 0.53 | 172 | 188 | -11.2 | +4.4 | +2.6 | -3.1 to +8.3 | +1.6 |
| C2_DORMANT_REACTIVATION | +4.6 | +4.3 | 0.59 | 88 | 66 | -0.8 | +8.7 | +6.6 | -2.2 to +14.7 | +1.8 |
| C3_OUT_OF_CHARACTER | -1.3 | -1.6 | 0.49 | 201 | 205 | -4.5 | +2.0 | +0.7 | -4.5 to +5.6 | +1.0 |
| C6_QUIET_FRESH_LOW | -5.8 | -6.2 | 0.46 | 39 | 97 | -6.4 | -4.3 | -6.7 | -19.6 to +6.9 | +1.9 |
| C7_HEAVY_NEWCOMER | -6.7 | -7.0 | 0.65 | 72 | 23 | -16.6 | -3.5 | -3.2 | -12.5 to +6.3 | -0.6 |
| R1_S_FRESH_REPLICATION | -6.0 | -6.3 | 0.51 | 175 | 200 | -11.9 | +0.8 | -1.4 | -7.6 to +4.4 | +1.9 |
| M1_RARITY_TOP1 | -2.0 | -2.2 | 0.67 | 11 | 7 | -31.1 | +16.5 | +16.6 | -0.6 to +30.3 | -0.3 |
| M2_IFOREST_TOP1 | +0.6 | +0.4 | 0.66 | 30 | 14 | +5.1 | -1.6 | -1.6 | -18.3 to +14.1 | -0.2 |
| M3_EDGE_TOP5 | +16.0 | +15.7 | 0.71 | 13 | 1 | +36.8 | +14.4 | +15.4 | -10.1 to +37.6 | -1.3 |
| B1_BIG | -0.4 | -0.7 | 0.61 | 147 | 57 | -3.8 | +1.0 | -0.1 | -6.9 to +6.0 | +0.8 |
| B2_AFTER_MOVE | -2.2 | -2.6 | 0.48 | 287 | 359 | -5.5 | +1.9 | -1.8 | -6.7 to +2.9 | +3.4 |
| B3_THIN_NOT_FRESH | +1.3 | +1.0 | 0.56 | 105 | 51 | +3.6 | +0.3 | -2.0 | -9.7 to +6.3 | +1.9 |
<!-- /audit:prices -->

<!-- audit:lags -->
| Class | Lag | With a later purchase | At the follower's price, after fee | Median wait, hours |
|---|---:|---:|---:|---:|
| C1_FRESH_FUNDED_BET | 6 s | 172 | +2.6 | 2.5 |
| C1_FRESH_FUNDED_BET | 60 s | 170 | +2.2 | 2.7 |
| C1_FRESH_FUNDED_BET | 300 s | 167 | +2.8 | 2.7 |
| C1_FRESH_FUNDED_BET | 3600 s | 155 | +3.9 | 5.8 |
| C2_DORMANT_REACTIVATION | 6 s | 88 | +6.6 | 1.1 |
| C2_DORMANT_REACTIVATION | 60 s | 85 | +5.8 | 1.3 |
| C2_DORMANT_REACTIVATION | 300 s | 79 | +6.5 | 1.7 |
| C2_DORMANT_REACTIVATION | 3600 s | 71 | +3.6 | 2.8 |
| R1_S_FRESH_REPLICATION | 6 s | 175 | -1.4 | 2.4 |
| R1_S_FRESH_REPLICATION | 60 s | 174 | -1.2 | 2.6 |
| R1_S_FRESH_REPLICATION | 300 s | 173 | -1.4 | 2.7 |
| R1_S_FRESH_REPLICATION | 3600 s | 157 | -0.9 | 5.2 |
<!-- /audit:lags -->

**Fees.** Polymarket's fee page (`docs.polymarket.com/trading/fees.md`, read on 14 November 2026) charges takers
`rate x p x (1 - p)` a share, with a rate of 0 on geopolitics, 0.04 on politics and tech, 0.05 on culture, economy
and other, 0.07 on crypto; makers pay nothing. The table applies that schedule, by the category of each market, to a
taker buying at the alerted price and at the follower's price. 46 to 71 % of the alerted events of each class are on
fee-free geopolitics markets, and the fee costs 0.20 to 0.44 points on average: it changes no reading. The page gives today's
schedule, not the dates at which each rate began, so the alerted wallets may have paid less; a follower today pays
this.

**The price a follower could get.** The historical data hold the fills of 1,000 USD or more, not the order book.
"A later purchase" is the first purchase of the same outcome by another wallet at least L seconds after the alert, in
the 24 hours after it, at its own price. At L = 6 s the median wait runs from 0.05 hour (M3) to 5.7 hours (C6); for
C1, C2 and R1 it is 1.1 to 2.5 hours at 6 s and 2.8 to 5.8 hours at 3,600 s. This is therefore the price of the next
large buyer, not the price on the book six seconds after the alert; that price needs the books, which
`monitoring/livecollect` records only for the markets it follows and only from now on.

- **Whether a later large purchase follows is itself information from the future.** Between 7 % (M3, 1 of 14) and
  71 % (C6, 97 of 136) of the alerted events of a class see none within 24 hours (C1 188 of 360, R1 200 of 375). In 9
  of the 12 classes those do worse at the alerted price: for C1, -11.2 points without a later purchase against +4.4
  with one; for R1, -11.9 against +0.8. M2, M3 and B3 go the other way. Any result computed only where a follower
  traded (including the robustness line "at the price a follower paid" of RESULTS.md, which takes the next fill of
  another wallet five minutes or more after the entry) is conditioned on that future event and is not a return
  anybody alerted could have planned. The rule of the plan's follower is found again by this script on 1,442 of 1,641
  alert-class pairs (88 %; an alert counts in each of its classes, C7 and alerts with no follower price left out);
  the 199 others were not investigated.
- **At the follower's price and after fees, no class shows an advantage that the data separate from zero**: every
  95 % interval of the table holds zero (at 6 s, uncorrected, on the subset followed by a later purchase, itself
  conditioned on the future). C2 is +6.6 points at the follower's price after fee on 88 of its 154 events, interval
  -2.2 to +14.7; M1 and M3 have 11 and 13 such events. At a lag of 300 s, M1's 10 followed events give +23.4 points,
  interval +14.3 to +33.9 (`data/audit_accessible_prices.json`): on 10 events chosen by the future, after the results,
  uncorrected, it is a description and nothing more.

## How long an out-of-sample test would take

<!-- audit:prospective -->
| Class | Alert events a week of scheduled ends | Weeks to detect +5 points at 0.05 | at 0.0167 | Detectable after 52 weeks at 0.05 | at 0.0167 | Alerts made before a freeze at the start, 52 weeks | 104 weeks |
|---|---:|---:|---:|---:|---:|---:|---:|
| C1_FRESH_FUNDED_BET | 11.78 | 37 | 53 | 4.2 | 5.0 | 14 % | 7 % |
| C2_DORMANT_REACTIVATION | 5.04 | 88 | 126 | 6.5 | 7.8 | 16 % | 8 % |
| C3_OUT_OF_CHARACTER | 13.28 | 31 | 45 | 3.9 | 4.6 | 13 % | 7 % |
| C6_QUIET_FRESH_LOW | 4.45 | 106 | 151 | 7.1 | 8.5 | 20 % | 10 % |
| C7_HEAVY_NEWCOMER | 3.11 | 137 | 195 | 8.1 | 9.7 | 15 % | 8 % |
| R1_S_FRESH_REPLICATION | 12.27 | 34 | 48 | 4.0 | 4.8 | 14 % | 7 % |
| M1_RARITY_TOP1 | 0.59 | 751 | 1070 | 19.0 | 22.7 | 31 % | 16 % |
| M2_IFOREST_TOP1 | 1.44 | 281 | 401 | 11.6 | 13.9 | 7 % | 3 % |
| M3_EDGE_TOP5 | 0.46 | 1225 | 1747 | 24.3 | 29.0 | 11 % | 5 % |
| B1_BIG | 6.67 | 65 | 92 | 5.6 | 6.7 | 16 % | 8 % |
| B2_AFTER_MOVE | 21.13 | 22 | 32 | 3.3 | 3.9 | 11 % | 5 % |
| B3_THIN_NOT_FRESH | 5.10 | 85 | 121 | 6.4 | 7.6 | 13 % | 6 % |
<!-- /audit:prospective -->

T1 alone, one-sided, 80 % power, the alert rate and the price mix of VALIDATION x INFO held fixed; 0.0167 is the
share of each of C4, C5 and M3 when they split 0.05 in the future plan, C2 having 0.05 to itself. The rate counts
every alert of an event, while a plan frozen at the start of its window keeps only alerts made after the freeze: the
last two columns estimate the share lost that way (events ending evenly over the window, from the hours between each
alert and its scheduled end), so the weeks of the table are lower bounds. C2, the only class of C1 to C7 above its
price, would need at least 88 weeks of new scheduled ends to detect 5 points at 0.05; in one year, only an advantage
of 6.5 points could be detected. The rate of M3 in VALIDATION is held down by the rule that leaves out entries made on
or before 31 March 2026, contemporary with the outcomes it learnt: 11,883 of the 60,614 eligible VALIDATION x INFO
entries, 4,527 of the 16,738 evaluated ones (`data/audit_accessible_prices.json`). On new events every entry is out of
sample, so its future rate is probably higher than 0.46 a week, by an amount not measured. What follows from these
numbers is in [FUTURE_HYPOTHESES.md](FUTURE_HYPOTHESES.md).

## Independent recomputation

`scripts/independent_recompute.py` was written by a separate agent from the plan and the published tables only,
without reading `verify.py`, the frozen code or the renderer (by its own header and report), then compared with the
published numbers (`data/independent_recompute.json`; `--check`, 8 s). Of 729 quantities, 718 match: every count of
alert events (100 of 100), every T1 p, every T2 difference and the 14 verdicts. The 11 others change no test: C7 shows 524 alerted entries against 519, because the
exported class cells hold the alerts and the refused alerts together (that the 5 are refused alerts was not
verified), and the robustness line "entry of 5,000 USD or more" cannot be rebuilt from an export that keeps the first
alert of each event only. Four readings of the plan were chosen by that agent after comparing with the published
numbers, among two to four candidates each: the side of T2 (the alerts of one per event, in the stratum of their own
price and horizon), the weighting of its strata (by alert events), the weeks of the weeks-resampled interval
(seven-day blocks from 1 January 1970) and the median of an even count (the upper one). Its agreement on those four
points shows that a reading of the plan gives the published numbers, not that the plan is unambiguous there.
