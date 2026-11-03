# Results: synchronised entries on low-priced outcomes

Plan and lock: `analysis_plan.md`, `PROTOCOL.lock`. Computed once by `code/run_all.sh` from the frozen table after the freeze of 2026-11-03 01:37:07 UTC. Read under `amendements/001-2026-11-03.md`, written before these numbers were opened. Audits: `audit/AUDIT_SUMMARY.md`.

**Verdict of the plan: NOT_SUPPORTED, on all six windows.**

The allowed reading: no large average excess was found among matched bursts. This is not "no effect", and it says nothing about any wallet. No wallet is named, and nothing here touches insider trading either way.

## Primary test

Excess is the outcome minus the price paid. Difference is bursts minus entrants of the same cell (price band, crowd of the previous 24 hours, entrants of the token over its life). Interval at 1 - 0.05/6, cluster bootstrap on Gamma events, 4,000 draws. Files flagged or suspected partial are out.

| Window | Bursts | Events | Matched share | Difference | Interval | p | VALID / TEST | H2 observed / null median / p | Placebo difference / p | Verdict |
|---|---:|---:|---:|---:|---|---:|---|---|---|---|
| 5 s | 177 | 76 | 1.000 | -0.0192 | -0.0942 to 0.0674 | 0.5059 | -0.0225 / -0.0366 | 177 / 12 / 0.002 | -0.0136 / 0.5749 | NOT_SUPPORTED |
| 30 s | 256 | 110 | 1.000 | -0.0246 | -0.0825 to 0.0365 | 0.2679 | -0.0244 / -0.0359 | 256 / 49 / 0.002 | 0.0223 / 0.3754 | NOT_SUPPORTED |
| 90 s | 367 | 149 | 1.000 | -0.0054 | -0.0521 to 0.0475 | 0.7763 | 0.0016 / -0.0374 | 367 / 120 / 0.002 | -0.0081 / 0.6948 | NOT_SUPPORTED |
| 300 s | 713 | 208 | 1.000 | 0.0031 | -0.0294 to 0.0395 | 0.7773 | -0.0096 / -0.0129 | 713 / 296 / 0.002 | -0.0151 / 0.4994 | NOT_SUPPORTED |
| 900 s | 1149 | 253 | 1.000 | 0.0090 | -0.0165 to 0.0347 | 0.3539 | 0.0010 / -0.0251 | 1149 / 622 / 0.002 | 0.0090 / 0.6343 | NOT_SUPPORTED |
| 3600 s | 2322 | 336 | 0.999 | 0.0040 | -0.0160 to 0.0251 | 0.6013 | -0.0095 / -0.0113 | 2322 / 1707 / 0.002 | 0.0036 / 0.8448 | NOT_SUPPORTED |

What these numbers say, and how far:

- **Wallets do align.** At every window, entrants group more than local intensity allows. p sits at its floor of 0.002 at all six: it is a bound, not an estimate. A shared channel, a bot or a fast reaction to public news produces that too, and these counts were partly seen before the freeze, so H2 is not a blind result.
- **On average, that alignment did not come with an excess over the price paid.** Differences run from -0.0246 to 0.0090. The upper ends of the intervals run from 0.0251 to 0.0674.
- **Limits of that bound.** It covers an average over matched bursts. A small subset of informed bursts, one in four or fewer, stays compatible with it. Synthetic medium effects of +0.10 on all bursts passed 0 of 12 runs, partly because of the sign and threshold rules. The `total` key can hide an informed burst followed by an exit from the price band, and rows just before an upward exit stay in the base, so the difference may be pulled toward zero. The size of those biases was not measured.

## Strata, descriptive, never used to choose

Difference (bursts, events). Thin strata are not citable.

| Window | TRAIN | No shock before | At least half fresh | Partial files back | 0.01-0.10 | 0.10-0.20 | 0.20-0.35 |
|---|---|---|---|---|---|---|---|
| 5 s | -0.005 (37, 17) | -0.023 (165, 71) | -0.024 (146, 60) | -0.015 (191, 79) | -0.022 (80, 37) | 0.011 (42, 17) | -0.039 (55, 36) |
| 30 s | -0.009 (61, 28) | -0.031 (229, 101) | -0.039 (180, 75) | -0.022 (291, 119) | -0.025 (100, 47) | 0.028 (62, 35) | -0.059 (94, 57) |
| 90 s | 0.009 (111, 48) | -0.006 (325, 137) | -0.031 (220, 91) | -0.007 (428, 159) | -0.009 (123, 59) | 0.023 (91, 52) | -0.019 (153, 91) |
| 300 s | 0.016 (243, 79) | 0.006 (635, 182) | -0.007 (389, 119) | 0.003 (832, 219) | -0.008 (226, 82) | 0.018 (197, 92) | 0.001 (290, 137) |
| 900 s | 0.026 (414, 99) | 0.011 (1042, 225) | 0.003 (617, 146) | 0.009 (1341, 264) | -0.001 (360, 111) | 0.020 (317, 133) | 0.009 (472, 164) |
| 3600 s | 0.014 (937, 141) | 0.008 (2167, 306) | -0.000 (1249, 212) | 0.002 (2670, 348) | 0.001 (691, 174) | 0.012 (665, 187) | 0.001 (966, 229) |

`no_shock` does not clear public news: a first reaction to news counts as no shock.

## Bursts, descriptive

| Window | Bursts | Events | Shock | No shock | Unknown | Median CV of sizes | Mean fresh share | Median USD |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 5 s | 177 | 76 | 4 | 165 | 8 | 0.122 | 0.825 | 545 |
| 30 s | 256 | 110 | 19 | 229 | 8 | 0.196 | 0.710 | 599 |
| 90 s | 367 | 149 | 34 | 325 | 8 | 0.289 | 0.617 | 681 |
| 300 s | 713 | 208 | 67 | 635 | 11 | 0.357 | 0.559 | 780 |
| 900 s | 1149 | 253 | 91 | 1042 | 16 | 0.384 | 0.539 | 830 |
| 3600 s | 2322 | 336 | 112 | 2167 | 43 | 0.431 | 0.536 | 874 |

## Catalogue, exploratory

Selected on suspicion and on outcome, so this is no test of insider trading. Largest number of entrants inside each window, in the 8 days before the public event, against tokens of the same volume decile. In the universe: khamenei-out-mar31, maduro-out-jan31, nobel-2025-machado. Not in it: biden-pardon-fauci, ceasefire-apr7, iran-strike-feb28. Khamenei is a capped file, so its entrants are unreliable. Peers' windows hold their closing news while catalogue windows stop before the event, so catalogue tokens look ordinary by construction. Treat a flag as a reason to look.

| Market | Token | Partial file | Window, s | Largest group | Peers | Share of peers at or above | BH flag |
|---|---|---|---:|---:|---:|---:|---|
| nobel-2025-machado | won | no | 5 | 1 | 414 | 0.26329 | no |
| nobel-2025-machado | won | no | 30 | 1 | 414 | 0.26329 | no |
| nobel-2025-machado | won | no | 90 | 1 | 414 | 0.26329 | no |
| nobel-2025-machado | won | no | 300 | 1 | 414 | 0.26329 | no |
| nobel-2025-machado | won | no | 900 | 1 | 414 | 0.26329 | no |
| nobel-2025-machado | won | no | 3600 | 2 | 414 | 0.16667 | no |
| nobel-2025-machado | lost | no | 5 | 2 | 414 | 0.03865 | no |
| nobel-2025-machado | lost | no | 30 | 2 | 414 | 0.06039 | no |
| nobel-2025-machado | lost | no | 90 | 3 | 414 | 0.0314 | no |
| nobel-2025-machado | lost | no | 300 | 5 | 414 | 0.00966 | yes |
| nobel-2025-machado | lost | no | 900 | 10 | 414 | 0.00242 | yes |
| nobel-2025-machado | lost | no | 3600 | 24 | 414 | 0.0 | yes |
| maduro-out-jan31 | won | no | 5 | 1 | 340 | 0.21765 | no |
| maduro-out-jan31 | won | no | 30 | 2 | 340 | 0.12647 | no |
| maduro-out-jan31 | won | no | 90 | 2 | 340 | 0.15588 | no |
| maduro-out-jan31 | won | no | 300 | 4 | 340 | 0.08235 | no |
| maduro-out-jan31 | won | no | 900 | 5 | 340 | 0.08529 | no |
| maduro-out-jan31 | won | no | 3600 | 11 | 340 | 0.07059 | no |
| maduro-out-jan31 | lost | no | 5 | 2 | 340 | 0.09118 | no |
| maduro-out-jan31 | lost | no | 30 | 4 | 340 | 0.01765 | no |
| maduro-out-jan31 | lost | no | 90 | 6 | 340 | 0.00588 | yes |
| maduro-out-jan31 | lost | no | 300 | 9 | 340 | 0.01176 | no |
| maduro-out-jan31 | lost | no | 900 | 11 | 340 | 0.02647 | no |
| maduro-out-jan31 | lost | no | 3600 | 12 | 340 | 0.06176 | no |
| khamenei-out-mar31 | won | yes | 5 | 7 | 340 | 0.0 | yes |
| khamenei-out-mar31 | won | yes | 30 | 7 | 340 | 0.0 | yes |
| khamenei-out-mar31 | won | yes | 90 | 7 | 340 | 0.0 | yes |
| khamenei-out-mar31 | won | yes | 300 | 7 | 340 | 0.01765 | no |
| khamenei-out-mar31 | won | yes | 900 | 10 | 340 | 0.02941 | no |
| khamenei-out-mar31 | won | yes | 3600 | 10 | 340 | 0.07941 | no |
| khamenei-out-mar31 | lost | yes | 5 | 0 | 340 | 1.0 | no |
| khamenei-out-mar31 | lost | yes | 30 | 0 | 340 | 1.0 | no |
| khamenei-out-mar31 | lost | yes | 90 | 0 | 340 | 1.0 | no |
| khamenei-out-mar31 | lost | yes | 300 | 0 | 340 | 1.0 | no |
| khamenei-out-mar31 | lost | yes | 900 | 0 | 340 | 1.0 | no |
| khamenei-out-mar31 | lost | yes | 3600 | 0 | 340 | 1.0 | no |

## Accounting

{
"bursts_30": 291,
"bursts_300": 832,
"bursts_3600": 2670,
"bursts_5": 191,
"bursts_90": 428,
"bursts_900": 1341,
"entrants": 67466,
"excluded_not_resolved_1_0": 6,
"files_flagged_truncated": 42,
"files_suspect_partial_page_multiple": 7,
"first_row_is_sell": 114707,
"first_row_price_out_of_range": 690618,
"first_row_under_100": 1586,
"group_event": 2091,
"markets_read": 2091,
"markets_universe": 2097,
"oldest_row_minus_market_start_days": {
"median": 2.6593287037037037,
"n": 2091,
"over_2_days": 1096,
"p90": 91.01746527777777
},
"rows_after_close_dropped": 61,
"rows_read": 2507375,
"tokens_universe": 4182,
"tokens_with_entrants": 1841,
"wallets_first_seen": 268792
}

The table's rebuild from the frozen code gave identical decompressed bytes (`derived/table.jsonl.gz`, `tokens.jsonl.gz`, counts, hashes), which lifts the audit's question about file dates.

## Multiple comparisons

114 real comparisons in the register, 120 counting pre-freeze looks at counts. Threshold of the verdict: 0.05/6. The register's threshold, 0.05/114 = 0.00044, cannot be reached as coded: the floors are 0.0005 for H1 and 0.002 for H2. The plan promised a result at that threshold and it was not written: this is a limit of resolution. It changes nothing here, since no H1 is anywhere near.

## Deviations and data notes

- Controls did not fully pass: the combined news-day trap passed once in 3 at 300 s, against the plan's "must fail all four". The design was tuned on these scenarios, so 1 of 72 is closer to a training error than to a false-pass rate.
- `crowd` counts the row itself and same-second rows, against "earlier rows only". The cooldown adds rows to `members` outside a trigger, so they are neither events nor comparators. No H2 run with partial files, against the plan. Catalogue peers exclude partial files and catalogue tokens, against "every other token". The verdict requires both signs positive, stricter than "same sign". A placebo with no value would not block a pass: none occurred.
- H2 is not monotone at long windows, because of the cooldown. It passed here at all six, so this changes nothing in this run.
- One bounded read of Gamma, 105 requests, outside the guard of the network layer, wrote `derived/events.json` on the external volume.
- The archive's `/trades` route has been retired, so the source cannot be re-read: only hashes of the archive files bind the table.
- All auditors are instances of the same model family.

## What a second study would change

Listed in amendment 001. Benjamin's decision.
