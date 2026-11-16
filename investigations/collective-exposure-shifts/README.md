# Collective exposure shifts, does coordinated exposure beat the price?

**Verdict: `NOT_SUPPORTED` on the pre-declared replication, `INCONCLUSIVE` on the smaller primary sample. No edge
over the price, no advantage over any declared comparator, and no positive net result. In TEST the alerted side won
*less* often than its own price implied (−4.3 points on 48 alerts).**

This investigation asks one question: when several wallets increase their **net exposure to the same outcome** inside
one hour, does that outcome win more often than the market price implies, and more often than (a) the price alone,
(b) naive buy-side consensus, (c) a single wallet's shift? It also checks whether such a signal would survive execution.

## What already existed, and what was checked first

The hypothesis comes from the Iran / 28 February 2026 cohort. The archived contrast (**20 of 36** cohort accounts had a
NO buy strictly before a YES buy on that market, against **16 of 733** other accounts created the same days) is
reproduced exactly here from the archived tape, with its SHA-256 checked:
[`results/feb28_recheck.json`](results/feb28_recheck.json), [`scripts/reproduce_feb28.py`](scripts/reproduce_feb28.py).

**The archived tape is censored, and this changes the figure.** The archive holds the newest 84 pages of 500 fills. On
the same band the complete v2 tape holds 101,163 fills; the whole market holds 217,997. Every archived row is present
in the complete tape (0 rows missing), so the difference is missing data, not a different definition:

| Reading | Cohort (36) | Other (733) | Fills used |
|---|---:|---:|---:|
| Archived 42,000-row tape (as published) | 20 NO→YES | 16 | 42,000 |
| Complete tape, same band start | **35** | **27** | 101,163 |
| Complete tape, full market history | **35** | **28** | 217,997 |

The band's first and last second are exactly the tape's first and last second, which is what a page cap looks like when
the window is defined from the collected rows. The cohort pattern is therefore *more* uniform than published (35/36),
and the comparator base rate is *higher* (27/733, 3.7 % instead of 2.2 %). Both readings stay descriptive: the cohort
was selected after its outcome, and `p_value` was already null in the archive. Correcting the numerator and the
denominator does not turn a selected cohort into a test.

## Method in one page

- **Population, not selected on winners.** The 34,413-market catalogue frozen on 13 November 2026 for the early-detection
  study (closed events ≥ 50,000 USD, public-price and match-level tags excluded, Yes/No markets ≥ 10,000 USD, resolved),
  reused unmodified.
- **Sample, blind to outcome.** Markets with volume < 1,000,000 USD and `sha256(condition_id) mod 1000 < 25`:
  **763 markets in 688 events**. The hash sees only the condition id.
- **Positions from executed fills only.** `q(w,o,t)` = net shares bought minus sold; `X = q(YES) − q(NO)` in YES-share
  equivalents (a NO share is a short YES share); `X_s = ±X` for side `s`. Coexistence (holding YES and NO at once) is
  flagged and never reported as an inversion. Two-sided high-turnover wallets (market making, hedging, rebalancing) are
  excluded from the collective count and kept in a separate variant. Splits, merges, redemptions and neg-risk
  conversions are **not** in the trade tape and are not reconstructed.
- **Signals at 900-second steps.** S4 (primary): ≥ 3 wallets each raising exposure by ≥ 500 USD inside the same hour,
  total ≥ 3,000 USD, no wallet above 60 % of it, price between 0.05 and 0.90. S2: naive buy consensus (≥ 3 buyers,
  ≥ 3,000 USD, no exposure requirement). S3: a single wallet's shift ≥ 3,000 USD. S4b: S4 with two-sided wallets kept.
  S1: the price alone, as forecast and as matched placebo. One alert per market and side (the first firing), so an
  ongoing position change is not counted repeatedly.
- **Outcome joined last.** `win` comes from `labels.jsonl`, read only by `scripts/score.py`.
- **Statistics.** 8 declared tests plus 3 declared sweep cells, 10 comparisons, Bonferroni `0.05/10` and
  Benjamini–Hochberg. Confidence intervals resample whole events (10,000 draws, seed 20261116). Chronological splits:
  TRAIN 2025, VALID 2026 H1, TEST 2026-07-01 → 2026-10-31. Verdict wording and rule fixed before any rate.

## Results, primary sample (763 markets, 129 collective alerts, 97 events)

| Signal | Alerts | Win rate | Mean price | Excess | Win-rate CI (events) |
|---|---:|---:|---:|---:|---|
| S4 collective exposure shift | 129 | 71.3 % | 71.5 % | **−0.2 pt** | 65.7 … 77.3 % |
| S4 in TEST only | 16 | 68.8 % | 69.0 % | −0.2 pt |, |
| S2 naive buy consensus | 392 | 53.3 % |, | +0.3 pt |, |
| S3 single-wallet shift | 166 | 63.3 % |, | −3.3 pt |, |
| S1 matched placebo | 8,132 | 63.1 % | 63.1 % | 0.0 pt |, |

| Test | Comparison | Result | p | After correction |
|---|---|---|---:|---|
| T1 | S4 vs its own price | −0.23 pt | 0.567 | not significant |
| T2 | S4 vs matched placebo | −2.69 pt | 1.000 | not significant |
| T3 | S4 vs naive buy consensus | −0.56 pt | 1.000 | not significant |
| T4 | S4 vs single-wallet shift | +3.08 pt | 0.140 | not significant |
| T5 | S4 net payoff at 1 % slippage | −0.0123 / share | 0.696 | not significant |
| T6 | S4b (two-sided kept) vs S4 | +0.04 pt | 0.359 | not significant |
| T7 | TEST only, S4 vs price | −0.21 pt | 0.625 | not significant |
| T8 | declared sweep (3 cells) | +1.27 / +1.20 / −2.40 pt | 0.367 | not significant |

**Execution.** With no order book archived, the result is computed at the last **executed** price and across a declared
slippage grid. It is negative at zero cost:

| Slippage | Mean result per share | Win rate |
|---|---:|---:|
| 0 % | **−0.0023** | 71.3 % |
| 0.5 % | −0.0073 | 71.3 % |
| 1 % | −0.0123 | 71.3 % |
| 2 % | −0.0223 | 71.3 % |
| 5 % | −0.0523 | 71.3 % |

There is no break-even slippage: the strategy loses before paying anything. TRAIN, VALID and TEST are all negative at
1 % (−1.89 pt, −0.79 pt, −1.21 pt).

## Results, replication (1,579 markets, 266 collective alerts, 197 events)

The replication uses the same rule, code, thresholds, splits and decision rule, on the same population with the hash
threshold moved from 25 to 50 per thousand. It is the run that reaches the declared 30-alert threshold in TEST.

| Split | Alerts | Win rate | Mean price | Excess | Result at 1 % slippage |
|---|---:|---:|---:|---:|---:|
| TRAIN (2025) | 90 | 74.4 % | 71.8 % | +2.7 pt | +1.67 pt |
| VALID (2026 H1) | 128 | 70.3 % | 73.8 % | −3.5 pt | −4.54 pt |
| TEST (2026 H2) | 48 | 70.8 % | 75.2 % | **−4.3 pt** | **−5.34 pt** |
| All | 266 | 71.8 % | 73.4 % | −1.6 pt | −2.58 pt |

| Test | Comparison | Result | p | After correction |
|---|---|---|---:|---|
| T1 | S4 vs its own price | −1.58 pt | 0.745 | not significant |
| T2 | S4 vs within-market placebo | −2.13 pt (CI −5.0 … +0.8) | 1.000 | not significant |
| T3 | S4 vs naive buy consensus | −1.41 pt | 1.000 | not significant |
| T4 | S4 vs single-wallet shift | +0.61 pt | 0.377 | not significant |
| T5 | net payoff at 1 % slippage | −0.0258 / share | 0.936 | not significant |
| T7 | TEST only, S4 vs price | −4.34 pt | 0.808 | not significant |

The sign flips between periods: positive in TRAIN, negative in VALID and TEST. That is what a rule with no edge looks
like when it is fitted to nothing and watched across three periods, and it is reported as such rather than as a
TRAIN result.

## What is new, what was recalculated, what is not testable

- **New and reproducible:** the censoring of the archived Iran tape and its corrected counts; the 763-market
  exposure-shift study with its frozen protocol, code, tests and results; the execution table; the negative verdict.
- **Recalculated:** the archived 20/36 and 16/733 from the archived rows (exact reproduction, hash verified).
- **Not testable here:** *(i)* **execution**, because no historical order book (ask, depth, spread) is archived for
  these markets, the paper result is a gross result at executed prices, not a fillable one; *(ii)* **financially
  linked collective shifts** (S5), because reconstructing direct funding links at population scale needs an on-chain
  pass that was not run, the arm is `UNRESOLVED`, not refuted; *(iii)* **splits, merges and redemptions**, absent from
  fill tapes, so exposure net of fills is an upper bound on true inventory; *(iv)* the deep tail of very large markets
  (volume ≥ 1 M USD), excluded by the sample rule because their tapes exceed the collector budget, that is exactly
  where the largest coordinated positions would sit.

## Case B, in the required vocabulary

Across the sample, 60 events hold two or more deadlines and wallets with ≥ 500 USD marked positions in at least two of
them. Their side sequences are NO,NO (9) and YES,YES (4); **no** NO(D1) → YES(D2) interval position appears at that
threshold ([`results/interval_reading.json`](results/interval_reading.json)). So case B is not what drives the S4
alerts here, and "a NO buy before a YES buy" is not read as an inversion anywhere in this study.

## Reproduce

```bash
python3 scripts/collect_tapes.py tapes.sqlite <condition_id> ...   # resumable, 1000 rows/page, cursor pagination
python3 scripts/split.py sample_markets.jsonl splits.json
python3 scripts/build_alerts.py --tapes tapes.sqlite --universe sample_markets.jsonl \
        --splits splits.json --out results/alerts.jsonl --status results/alerts_status.json
python3 scripts/score.py --alerts results/alerts.jsonl --labels labels.jsonl --tapes tapes.sqlite \
        --out results/scored.jsonl
python3 scripts/stats.py --scored results/scored.jsonl --placebo results/scored.jsonl.placebo.jsonl \
        --sweep results/sweep_1_scored.jsonl results/sweep_2_scored.jsonl results/sweep_3_scored.jsonl \
        --out results/tests.json
python3 scripts/report_tables.py --scored results/scored.jsonl --tapes tapes.sqlite --out results/tables.json
python3 scripts/reproduce_feb28.py --archive feb28.jsonl --created feb22_25.csv --v2 feb28_v2.sqlite \
        --out results/feb28_recheck.json
python3 -m unittest discover -s tests -v
```

`PROTOCOL.lock` records the SHA-256 of the plan and of every script; `tests/test_freeze.py` fails if a frozen file is
edited afterwards. Two dated amendments document what changed and when: the excess-based group tests (001) and the
pre-declared replication (002).

## Documentation

- [Analysis plan](analysis_plan.md), frozen before the first rate.
- [FINDINGS.md](FINDINGS.md), classified findings with sources and limits.
- [STATUS.md](STATUS.md), machine-read state.
- [EVIDENCE.md](EVIDENCE.md), every result file with its hash.
- `results/tables.json`, the alerts that won and the alerts that lost, with the executable transaction of each.
- `results/interval_reading.json`, `results/feb28_recheck.json`, `results/tests.json`.

## Limits, stated plainly

- 129 collective alerts in 97 events is a small sample; the event-clustered intervals are wide, and T7 has 16 alerts.
  The study can exclude a large edge, not a 5-point one.
- Alerts are evaluated at 900-second steps with the price of the last executed fill, never a chart point.
- The population inherits the exclusions fixed on 13 November 2026; they were not re-audited.
- The sample is 2.2 % of the catalogue (763 of 34,413 markets), and market selection inside an event is not controlled.
- A negative result here concerns this rule on these markets. It does not say that coordinated trading never precedes
  a move; it says this measurable version of it does not beat the price.
