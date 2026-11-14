# Future hypotheses: C2, C4, C5 and M3, to be tested only on events that have not ended yet

14 November 2026. **Status: draft of a pre-registration, not frozen, nothing tested.** No outcome used below is new:
every number comes from the frozen study and its audit, and none of the four classes is retested on data already
read. A test of them is valid only on events whose outcomes did not exist when its plan was frozen. Freezing that plan
is Benjamin's decision; this page says what it would contain and how long it would take.

## Why these four, and what the past data already say

| Class | What it is (frozen definition, `study/analysis_plan.md`) | VALIDATION x INFO | Reading |
|---|---|---|---|
| C2 DORMANT_REACTIVATION | a wallet whose latest trade on another market is 60 days or more old receives collateral in the 24 hours before a first purchase of 1,000 USD or more of a side | +4.6 points, 154 events, T1 p = 0.10 | the smallest T1 p of the 14 classes; only M3 has a larger excess (+16.0, 14 events); regression towards zero is expected |
| C4 COFUNDED_GROUP | a plain key behind a deposit of the wallet is behind a deposit of another fresh wallet that entered the same event in the 7 days before | 0 alert events | the shape of the documented Nobel 2025 case, met once, in discovery |
| C5 RECURRENT_FUNDER | the same key paid another fresh wallet that entered a different event 7 days or more earlier | 0 alert events | one alert, in discovery, on a key of no documented case |
| M3 EDGE_TOP5 | top 5 % of a logistic edge model fitted on discovery outcomes | +16.0 points, 14 events | uninformative at that size; the leakage rule left out the 11,883 of 60,614 VALIDATION x INFO entries made on or before 31 March 2026 |

None of the four was shown to beat its price, and none was shown not to: [STATISTICAL_AUDIT.md](STATISTICAL_AUDIT.md)
finds that at the corrected threshold the study could detect, with 80 % power, only 13.6 points for C2 and 50.9 for
M3, and the simultaneous interval of C2 runs from -7.0 to +16.3 points.

## What would be frozen, unchanged

- **Definitions**: the frozen code, by hash, of the study folder whose lock after amendment 002 has sha256
  `6149a578934fbb84072cbd1b349848ed048e27f86a17aa97caa96de5ef56ed3b` (`data/amendment_002_manifest.json`): every
  threshold of C2, C4, C5 and M3 as they are (1,000 USD, 0.90, 60 days, 7 days, 10,000 blocks, fan-out 10, 95th
  percentile), the eligibility rules, the price and horizon strata. No threshold is chosen again in light of the
  results: that is the point of this test.
- **M3's model**: refitted by the frozen `tests_lib.fit_m3` on the frozen analytic table (sha256 in `study/PROTOCOL.lock`),
  which is deterministic; then scored on new entries only. Every new entry is made after its training outcomes, so the
  leakage rule that left out the VALIDATION entries made on or before 31 March 2026 no longer applies.
- **Population of the holdout**: INFO events (same tags and volume floors) whose markets all have a scheduled end from
  1 December 2026 onwards, inside a window fixed in the plan (below), and entries made after the freeze timestamp of the
  new plan. Alerts are rebuilt by the frozen pipeline from public data after the window, and also logged by the live
  engine as they happen (`monitoring/phi_engine`), so that the alerts tested can be checked against alerts that existed
  before the outcomes.
- **Tests**: T1 and T2 of the frozen plan, and its verdict rule: SUPPORTED needs T1 and T2 under the threshold and an
  excess of 5 points or more. C2 is the primary hypothesis at one-sided 0.05; C4, C5 and M3 share 0.05 (0.0167 each)
  and are reported INCONCLUSIVE below 30 alert events, as in the frozen verdict rules. One analysis, at the end of the
  window; no look before.
- **Negative control and positive controls**: the PUBLIC_PROCESS family as before; the frozen positive controls rerun
  on synthetic tables of the size of the holdout before it is read.

## How long it would take

From the alert rates of VALIDATION (alert events a week of scheduled ends, `data/audit_after_results.json`), for T1
alone:

| Class | Level | Alert events a week | 52 weeks: detectable at 80 % power | Power at its past estimate, 52 weeks | 104 weeks |
|---|---:|---:|---:|---:|---:|
| C2 | 0.05 | 5.04 | 6.5 points | 0.55 | 0.81 |
| M3 | 0.0167 | 0.46 or more | 29.0 points, or less | 0.31 | 0.58 |

- **A one-year test of C2 has 80 % power only for a true advantage of about 6.5 points or more** (T1, one-sided
  0.05). That value lies inside C2's past 95 % interval (-2.1 to +11.5), above its estimate. At its past estimate,
  +4.6 points, a one-year test has a 55 % chance of reaching 0.05 and a two-year test 81 %. C2 has the smallest T1 p of
  14 classes, so its estimate is more likely too high and these chances are likely optimistic. SUPPORTED also needs
  T2 under the threshold and an excess of 5 points or more.
- **The rates are upper estimates for a plan frozen at the start of its window**: they count every alert of an event,
  while the plan keeps only alerts made after the freeze. With ends spread evenly over the window, about 16 % of C2's
  alerts would be lost over 52 weeks and 8 % over 104 (STATISTICAL_AUDIT.md, last table).
- **M3's line errs both ways**: its future rate is not known (in VALIDATION it was held down by the leakage rule,
  which makes the line err low), and its past estimate of +16.0 points rests on 14 events (which makes the power at
  that estimate err high).
- **C4 and C5, at the past rate, could not be tested as rates.** See the next section: even with links up to three
  keys up, they fire too rarely for a test of their win rate. They are case-finding rules: each alert is a lead to read
  by hand, and a count of how many such groups form is the only number they can give.

The window is therefore a choice between a one-year test with a 55 % chance for T1 at C2's past estimate and a
two-year test (scheduled ends from 1 December 2026 to 30 November 2028) with 81 %. That choice is made on power alone,
before any new outcome exists, and is Benjamin's; so are the levels above.

## Links two and three intermediaries away

The frozen C4 and C5 read one hop: the key behind a deposit, or behind a pass-through key. An exploratory reading two
and three keys up ([FINANCIAL_LINKS.md](FINANCIAL_LINKS.md), `data/links_multihop_summary.json`) takes the study's
definitions of a service, a plain key, the window and the 1 USD floor; following every plain key upwards and counting a
key as discriminating when it is an ancestor of 2 to 10 wallets are new rules, fixed before the first run by the header
of `scripts/links_multihop.py` (18:25:12 UTC). It finds 8 groups of wallets instead of 2, recovers the second network of
the Nobel 2025 case that one hop missed, and confirms its 26 discriminating transfers on chain. Recounted with the
frozen `feat_40.classify`, C4 fires on 11 entries instead of 8 (8 of them behind the Nobel key, on one event) and C5 on
4 instead of 1 (three on DISCOVERY x INFO, one on DISCOVERY x PUBLIC_PROCESS); the overlap of the two was not counted.
**On VALIDATION, none, up to three keys up.**

So over seven months of VALIDATION events the group classes would have raised no alert at all, and over the fifteen
months of DISCOVERY (scheduled ends from January 2025 to March 2026) 15 alerted entries, most of them on the one Nobel
event. Detecting 5 points takes about 400 to 560 alert events for the other classes
(`events_for_5_points_at_0.05`, `data/audit_after_results.json`): decades at no more than 12 alerted entries a year.
If they are kept in a future plan, it is as:

- **C4 and C5 unchanged at one hop** (frozen), counted and reported, INCONCLUSIVE below 30 alert events;
- **C4 and C5 at two hops** as a new, separately declared descriptive count, the rules of `scripts/links_multihop.py`
  frozen by hash, with no win-rate test;
- every alert of either read by hand as a lead, with the receipts of its links, and nothing concluded about who
  controls the wallets.

## What would not be evidence

A class that fires on a documented case, a later reading of the same events, a new threshold found by looking at
these results, or a subset of the holdout chosen after its outcomes. A class whose alerted purchases beat their price
on the holdout would show that they did so over that period, before fees, the price move after the alert and a
follower's latency, not that any account traded on inside information.
