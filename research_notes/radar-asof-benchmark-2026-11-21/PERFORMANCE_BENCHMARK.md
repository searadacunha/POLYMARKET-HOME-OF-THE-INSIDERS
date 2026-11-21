# Measured performance on 21 November 2026

## Forecasting relative to the observed market price

The primary statistic is the improvement in mean Brier score, computed as market loss minus candidate loss on **all** eligible decisions. A positive number favors the candidate. Rules and time boundaries were recorded before the new calculations, after the historical corpus and earlier analyses had been published. All inputs, the seed and the fitted offsets are available. A raw trade near the alert is the probability baseline. The study supplies no historical ask or quantity at that price. [Protocol](PROTOCOL.md) · [Executable benchmark](benchmark.py) · [Machine results](results.json)

| UTC period | Decisions | Markets | Events | Market Brier | Constant 0.50 | TRAIN prevalence |
|---|---:|---:|---:|---:|---:|---:|
| TRAIN before 1 July 2025 | 73 | 72 | 67 | 0.162358 | 0.250000 | 0.163258 |
| VALID before 1 January 2026 | 110 | 110 | 99 | 0.181730 | 0.250000 | 0.267128 |
| TEST from 1 January 2026 | 372 | 368 | 273 | 0.215643 | 0.250000 | 0.274988 |

Of 587 source rows, 17 fell outside the original validation population and 15 had labels that matured too late for their split. Event grouping prevents the same event from entering more than one period. Each rule adds its TRAIN mean outcome-minus-price only to its flagged rows. The acceptance rule requires positive improvement in VALID, a positive simultaneous lower bound in TEST and at least 30 flagged TEST events. Intervals are event-clustered percentile intervals from 5,000 bootstrap draws with a Bonferroni correction across three screens. The observed population already selects for eventual resolution, volume and recorded ignition windows. No second untouched historical corpus or genuinely prospective outcome labels entered the fit.

| Frozen screen | TRAIN flags | VALID gain | TEST flags / events | TEST Brier gain | Simultaneous 98.33% interval | Pass |
|---|---:|---:|---:|---:|---|---|
| LONELY_THIN | 13 | −0.002488 | 19 / 18 | −0.003647 | [−0.009523, +0.000905] | No |
| LONELY | 53 | −0.012876 | 224 / 197 | −0.018106 | [−0.030489, −0.006546] | No |
| Concentrated longshot flow | 5 | +0.002179 | 41 / 32 | +0.001021 | [−0.000484, +0.002813] | No |

The longshot screen is the strongest of these three under the prespecified statistic. The 41 flags had an 11.90 percentage-point excess over their trigger price. The difference was only 1.48 points relative to unflagged decisions from other events in the same quarter and ten-cent price band. This is exploratory and includes no liquidity or volume balance check. The five training flags limit the fitted offset's stability. Scoring a resolved market result does not adjudicate a case of misconduct.

## How often the old evaluator selected a late price

Each scheduled probe requests entry, 1 h, 6 h and 24 h marks. Targets after the source ends are right-censored. The mature legacy column counts successful lookups using the old common 24-hour-plus-ten-minute endpoint. The new sampler additionally applies the observation clock and a separate ten-minute tolerance to each mark. Unordered conflicting values at the first accepted timestamp are withheld. The quotes and trade tape test timing logic and have different price definitions.

| Input and grid | Emissions | Legacy selected at maturity | Within ten minutes and unambiguous | Late | Conflicting | Right-censored |
|---|---:|---:|---:|---:|---:|---:|
| 38 outcome-token quote streams, hourly | 2,280 | 7,866 | 7,638 | 228 | 0 | 1,178 |
| Machado Yes chart, minutely over 12 hours | 720 | 1,842 | 1,842 | 0 | 0 | 1,038 |
| Machado Yes recorded fills, same grid | 720 | 1,740 | 1,295 | 65 | 380 | 1,140 |

The quote archive had 76 additional targets with no eligible legacy mark. Of its successful mature lookups, **228/7,866 (2.90%)** used observations more than ten minutes late. If an evaluator run at one hour receives the completed archive, 2,318/4,522 eligible legacy entry or 1 h selections come from after that evaluation clock. At a stricter tolerance of 60 seconds the new rule keeps 7,456 quote marks, versus 7,638 at 300 or 600 seconds. Multiple probes cover the same gaps. These counts measure exposure to an evaluator defect. They cannot be turned into numbers of incorrect historical alerts. [Frozen diagnostic and source digests](results.json)

## Can the published sports effect be tested one week before play?

| Historical source and selection | Direct moneylines or records | Late listings or marks | Eligible and priced | Favorite bucket [0.55, 0.60) |
|---|---:|---|---:|---|
| Independent GitHubMagnus export, T−7 sports across categories | 619 rows | 11 of 17 bucket marks after their target | 6 bucket marks as of the target | Four wins from six mixed-category events, zero eligible MLB/NBA/NFL/NHL game moneylines |
| Official catalogue, MLB event **end** 1–7 September 2026 UTC | 95 moneylines of 948 catalogue entries | 93 listed after game start minus seven days | 2 | Zero |
| Official catalogue, MLB **game start** 1–7 September 2026 UTC | 98 moneylines of 1,054 catalogue entries | 97 listed after game start minus seven days | 1 | One settled game, zero wins |

Every recorded event end in both MLB cohorts was exactly seven days after its scheduled game start. On these data, subtracting a week from the catalogue end lands at **game start**. The external study reads a dataset's `end_date` and a centered ±12 h trade window. We did not match its 120 original rows to a contemporaneous sports schedule, so we cannot attribute the same error to all its markets or reject its reported effect. The follow-up used the observed game date after the first cohort revealed the discrepancy. Each market used the first listed team's token. Historical schedule revisions and last-trade execution remain unobserved. [First capture](sports.json) · [Game-date capture](sports_game_start.json) · [Transfer arithmetic](external_results.json)

## Actual monitoring and coverage

The ordinary engine ran from 14:42:45 to 14:45:54 UTC on 21 November. It completed three passes across Polygon blocks 97,711,131–97,711,194 in order. The last pass finished after the requested two minutes. Its log counted 5,116 decoded fills, 32 retained fills, 24 large buys, two evaluated entries and **zero alerts**. The 32 retained fills had a median block-timestamp-to-local-ingestion lag of 30.57 seconds. All three exchanges are represented among retained fills. The source selection and lack of a second independent complete tape leave universe coverage unknown. No daily rate was extrapolated. [Runtime log, counters and lags](live_run.json)

A separately registered pilot queried the same active Djokovic retirement outcome three times through the official price-history API. All three responses returned HTTP 200. The three source points were respectively 56, 29 and four seconds old, all at 0.027. The elapsed time between the first and last requests was 67.63 seconds. This directly tests price-read availability. It contains no detector alerts, contemporaneous bid/ask sizes or execution. [Timestamped source receipts](pilot.json) · [Official Data API](https://data-api.polymarket.com/v2/docs)

| Operational metric | Evidence in this pass |
|---|---|
| Observed alerts and actual emission latency | Zero alerts. The first-emission clock and alert latency distribution are undefined. |
| Recall, precision and false-positive rate | Undefined. No independent live labels or sampled non-alert cases. |
| Capture proportion | 64 consecutive blocks requested. Eligible event/fill coverage relative to a second provider is unknown. |
| Daily burden and temporal stability | 189 seconds monitored. The period cannot establish a daily load or stability. |
| Predictive value and profitability | Three retrospective forecasts failed the acceptance rule. No synchronized depth, slippage, fee schedule or fills were available for these entries. |

The existing execution study assessed spread and top-of-book availability on another window. Its order-book imbalance comparison found no evidence of sufficient displayed depth for its simulated trades. Applying those prices or costs to this study would join unrelated market times. [Frozen execution research](../../EDGE_VERDICT.md) · [Existing feed comparison](../../LIVE_DETECTION.md)
