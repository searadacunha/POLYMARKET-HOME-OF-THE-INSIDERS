# Positive and negative controls, second study

Written by the author from `controles/synth_v2_prefreeze.json`, the output of `code/ctl_10_synth.py` on the code frozen with this report. 1510 runs on synthetic tapes, 400 bootstrap draws and 49 draws for H2 per run, against 9,999 and 1,999 in the real run. No real outcome and no real rate enter here. `controles/synth_v1_before_audit.json` holds an earlier run on code the audits then corrected: it decides nothing.

The generator writes tapes, which pass through the same parser as real tapes. Its power is an upper reference: real tokens are messier, and synthetic prices are calibrated by construction. Planted tokens are only part of those holding sets, so a planted effect gives a smaller average difference, shown in the tables.

## At the stopping size: about 200 facts with a trigger

| Scenario | Seeds | Median facts with a trigger | Mean difference | `TIMING_ASSOCIATION` | `POSITIVE_NOT_INTERPRETABLE` | `BOUNDED_NULL` | `INCONCLUSIVE` | H1 positive at 0.05 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| null | 100 | 39 | -0.001 | 0 | 0 | 0 | 100 | 0 |
| bots_no_information | 100 | 199 | +0.003 | 0 | 2 | 84 | 14 | 2 |
| trap_crowded_win | 100 | 39 | +0.001 | 0 | 0 | 0 | 100 | 0 |
| trap_news_day | 100 | 49 | +0.005 | 0 | 3 | 0 | 97 | 3 |
| trap_news_day_bots | 100 | 59 | +0.006 | 0 | 1 | 0 | 99 | 1 |
| trap_slow_news | 100 | 172 | +0.087 | 0 | 88 | 0 | 12 | 88 |
| trap_slow_news_bots | 100 | 219 | +0.106 | 5 | 95 | 0 | 0 | 100 |
| trap_momentum | 100 | 187 | -0.002 | 2 | 1 | 36 | 61 | 3 |
| trap_rising_exit | 100 | 176 | -0.005 | 1 | 2 | 47 | 50 | 3 |
| plant_0.05 | 20 | 201 | +0.029 | 2 | 0 | 11 | 7 | 2 |
| plant_0.10 | 20 | 201 | +0.052 | 7 | 4 | 3 | 6 | 11 |
| plant_0.25 | 20 | 200 | +0.138 | 20 | 0 | 0 | 0 | 20 |
| plant_0.40 | 20 | 200 | +0.221 | 20 | 0 | 0 | 0 | 20 |
| subset_quarter_0.40 | 20 | 201 | +0.056 | 8 | 3 | 2 | 7 | 11 |
| all_tokens_informed_0.25 | 20 | 390 | -0.002 | 0 | 0 | 0 | 20 | 0 |
| few_wallets_0.25 | 20 | 198 | +0.137 | 8 | 12 | 0 | 0 | 20 |

## Against the plan's limits

| Limit | Result |
|---|---|
| At most 5 `TIMING_ASSOCIATION` in 100 seeds on any null or trap | Holds, and only just: 5 in 100 on `trap_slow_news_bots`, 2 on `trap_momentum`, 1 on `trap_rising_exit`, 0 on the others |
| At most 1 false `BOUNDED_NULL` in 20 where the true average difference is +0.10 or more | Holds: 0 on `plant_0.25`, `plant_0.40`, `all_tokens_informed_0.25` and `few_wallets_0.25` |
| Power of at least 0.80 at a planted +0.25, a difference of about +0.14 | 20 of 20 at about 200 facts with a trigger. 4 of 10 at about 100 facts, where 6 more only reach `POSITIVE_NOT_INTERPRETABLE` |

So **N_STOP = 200 facts with a trigger**.

## What the study can and cannot see at that size

- A difference of about +0.14 is found in 20 of 20 runs. A difference of about +0.05, from a planted +0.10, passes in 7 of 20, with 4 more `POSITIVE_NOT_INTERPRETABLE`. A difference of about +0.03 passes in 2 of 20.
- One group in four carrying +0.40 passes in 8 of 20.
- `null` and `trap_crowded_win` rarely reach the floor of 100 facts at this size, so they test little beyond H1: 0 H1 positives in 100 on each.
- `trap_slow_news`: a slow public reaction with no information in the sets. H1 is positive in 88 of 100 and 100 of 100 with bots. The gates catch nearly all of it: this is the study's main weakness, and why a positive result needs the strict guard.
- `all_tokens_informed_0.25`: every token holds informed sets, so a difference with controls shows nothing (about 0), and the raw excess gate turns all 20 into `INCONCLUSIVE`, no false bound.
- `few_wallets_0.25`: planted sets come from 5 wallets. 12 of 20 land on `POSITIVE_NOT_INTERPRETABLE`, and 8 still pass, since sets without those wallets remain, some of them on the same informed tokens. These 8 were not read one by one. A positive finding would need its wallets read by hand.

## Other sizes

### About 100 facts with a trigger

| Scenario | Seeds | Median facts with a trigger | Mean difference | `TIMING_ASSOCIATION` | `POSITIVE_NOT_INTERPRETABLE` | `BOUNDED_NULL` | `INCONCLUSIVE` | H1 positive at 0.05 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| null | 10 | 20 | +0.018 | 0 | 0 | 0 | 10 | 0 |
| bots_no_information | 10 | 102 | +0.010 | 0 | 0 | 3 | 7 | 0 |
| trap_crowded_win | 10 | 20 | -0.025 | 0 | 0 | 0 | 10 | 0 |
| trap_news_day | 10 | 24 | +0.009 | 0 | 0 | 0 | 10 | 0 |
| trap_news_day_bots | 10 | 29 | +0.018 | 0 | 0 | 0 | 10 | 0 |
| trap_slow_news | 10 | 87 | +0.085 | 0 | 6 | 0 | 4 | 6 |
| trap_slow_news_bots | 10 | 108 | +0.096 | 0 | 8 | 0 | 2 | 8 |
| trap_momentum | 10 | 92 | -0.006 | 0 | 0 | 0 | 10 | 0 |
| trap_rising_exit | 10 | 88 | -0.015 | 0 | 0 | 0 | 10 | 0 |
| plant_0.05 | 10 | 102 | +0.039 | 0 | 0 | 1 | 9 | 0 |
| plant_0.10 | 10 | 102 | +0.064 | 1 | 2 | 0 | 7 | 3 |
| plant_0.25 | 10 | 102 | +0.147 | 4 | 6 | 0 | 0 | 10 |
| plant_0.40 | 10 | 102 | +0.228 | 4 | 6 | 0 | 0 | 10 |
| subset_quarter_0.40 | 10 | 102 | +0.065 | 1 | 5 | 0 | 4 | 6 |
| all_tokens_informed_0.25 | 10 | 194 | -0.006 | 0 | 0 | 0 | 10 | 0 |
| few_wallets_0.25 | 10 | 98 | +0.143 | 1 | 8 | 0 | 1 | 9 |

### About 400 facts with a trigger

| Scenario | Seeds | Median facts with a trigger | Mean difference | `TIMING_ASSOCIATION` | `POSITIVE_NOT_INTERPRETABLE` | `BOUNDED_NULL` | `INCONCLUSIVE` | H1 positive at 0.05 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| null | 10 | 78 | +0.007 | 0 | 0 | 1 | 9 | 0 |
| bots_no_information | 10 | 403 | +0.004 | 0 | 0 | 10 | 0 | 0 |
| trap_crowded_win | 10 | 78 | -0.000 | 0 | 0 | 0 | 10 | 0 |
| trap_news_day | 10 | 99 | +0.032 | 0 | 0 | 0 | 10 | 0 |
| trap_news_day_bots | 10 | 117 | +0.015 | 0 | 0 | 0 | 10 | 0 |
| trap_slow_news | 10 | 349 | +0.100 | 0 | 10 | 0 | 0 | 10 |
| trap_slow_news_bots | 10 | 437 | +0.101 | 1 | 9 | 0 | 0 | 10 |
| trap_momentum | 10 | 374 | -0.004 | 0 | 0 | 4 | 6 | 0 |
| trap_rising_exit | 10 | 353 | -0.005 | 0 | 0 | 4 | 6 | 0 |
| plant_0.05 | 10 | 403 | +0.029 | 2 | 1 | 6 | 1 | 3 |
| plant_0.10 | 10 | 403 | +0.053 | 8 | 2 | 0 | 0 | 10 |
| plant_0.25 | 10 | 403 | +0.133 | 9 | 1 | 0 | 0 | 10 |
| plant_0.40 | 10 | 402 | +0.213 | 9 | 1 | 0 | 0 | 10 |
| subset_quarter_0.40 | 10 | 403 | +0.056 | 7 | 3 | 0 | 0 | 10 |
| all_tokens_informed_0.25 | 10 | 779 | -0.000 | 0 | 0 | 0 | 10 | 0 |
| few_wallets_0.25 | 10 | 399 | +0.140 | 3 | 7 | 0 | 0 | 10 |

## Other windows, secondary, about 200 facts in total

| Window and scenario | Seeds | Median facts with a trigger | Mean difference | `TIMING_ASSOCIATION` | `POSITIVE_NOT_INTERPRETABLE` | `BOUNDED_NULL` | `INCONCLUSIVE` | H1 positive at 0.05 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 30 s, null | 10 | 3 | -0.013 | 0 | 0 | 0 | 10 | 0 |
| 30 s, bots_no_information | 10 | 93 | +0.004 | 0 | 0 | 1 | 9 | 0 |
| 30 s, plant_0.25 | 10 | 92 | +0.164 | 0 | 9 | 0 | 1 | 9 |
| 30 s, trap_news_day_bots | 10 | 15 | +0.040 | 0 | 0 | 0 | 10 | 0 |
| 30 s, trap_slow_news_bots | 10 | 133 | +0.094 | 0 | 7 | 0 | 3 | 7 |
| 90 s, null | 10 | 13 | +0.009 | 0 | 0 | 0 | 10 | 0 |
| 90 s, bots_no_information | 10 | 182 | +0.004 | 0 | 0 | 9 | 1 | 0 |
| 90 s, plant_0.25 | 10 | 181 | +0.158 | 9 | 1 | 0 | 0 | 10 |
| 90 s, trap_news_day_bots | 10 | 32 | +0.055 | 0 | 1 | 0 | 9 | 1 |
| 90 s, trap_slow_news_bots | 10 | 204 | +0.120 | 0 | 10 | 0 | 0 | 10 |
| 900 s, null | 10 | 90 | -0.011 | 0 | 0 | 0 | 10 | 0 |
| 900 s, bots_no_information | 10 | 228 | +0.009 | 0 | 0 | 9 | 1 | 0 |
| 900 s, plant_0.25 | 10 | 227 | +0.092 | 9 | 0 | 0 | 1 | 9 |
| 900 s, trap_news_day_bots | 10 | 102 | +0.007 | 0 | 0 | 1 | 9 | 0 |
| 900 s, trap_slow_news_bots | 10 | 241 | +0.093 | 0 | 10 | 0 | 0 | 10 |

## Collection code

The collection scripts were tried on the live routes on 2026-11-03, on two days of the universe and three tapes, counts only: 1,564 markets read, 298 kept, 1,263 out of scope, 3 tapes, 3,923 rows, no error. No price summary and no outcome was read. Those three tapes stay and are not read again, since a run keeps existing tapes.

## Audits before the freeze

Three agents read the plan and code before this report: `leakage-auditor`, `silent-failure-hunter`, `stats-auditor`. All their findings, 5 blocking and 4 major, 1 blocking and 3 major, 3 blocking and 5 major, were treated in the plan and the code, apart from these limits written in the plan: a negative control that cannot clear confounding, differently worded markets on one fact, and a small loss of trigger weight in bootstrap draws. The same model family wrote the study and audited it.
