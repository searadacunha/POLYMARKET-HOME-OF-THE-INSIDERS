# Pattern research: what was tested, what held, what did not

**No pattern passed.** The one pattern tested under a frozen protocol does not predict the outcome better than the
price does. It does single out, hours ahead, the two documented cases of its own kind. That makes it a cheap way to
find cases worth investigating, and nothing more: an alert is not evidence about the account it names.

The study is archived in [research_notes/early-detection-2026-11-13/study](research_notes/early-detection-2026-11-13/study/analysis_plan.md):
plan, code, lock, positive controls, analytic table, registry of every test, results. `verify.py` in the same note
recomputes the main result from the table.

## The pattern

It comes from one case, the night before the Nobel Peace Prize 2025
([NEW_LEADS.md](NEW_LEADS.md), NB-1): a quiet outcome priced at 0.03 is bought up by a single account that has never
traded, and the price follows.

| Step | Rule, fixed before any other market was read |
|---|---|
| Ignition | On 10-minute prices of one side of a Yes/No market: a six-hour median at 0.15 or less, with no point above 0.20, then a price at three times that median and at least 0.10 above it |
| Confirmed by trades | A first buy at 1.5 times the median or more that opens a burst of at least 500 USD of buying in fifteen minutes, and 1,000 USD by the time of the alert |
| Still open | The last buy before the alert is at 0.90 or less; above that the move is a public resolution |
| Lonely | One wallet supplied at least half of the buying in those fifteen minutes |
| Thin | That wallet had traded two markets or fewer before |
| Alert time | The later of the price point that shows the move and the first buy plus fifteen minutes |

Everything used at the alert is dated before the alert. The outcome is joined last, from a file no feature code reads.

## The protocol

- **Population.** Every closed event of the catalogue with a volume of 50,000 USD or more (158,494 events), minus
  those whose outcome is produced in public view: match-level sports, e-sports, price ladders, weather, counting
  markets. Then every Yes/No market of 10,000 USD or more, closed between January 2025 and October 2026 and resolved to
  one side: 34,413 markets in 7,783 events.
- **Discovery and validation.** Every event that holds a market of a case already documented in this repository is
  set aside as discovery: 23 cases, including the Nobel event that produced the rule. The tests run on all the other
  events.
- **Tests.** Does the tested class win more often than the price at the alert says (exact test)? Does it do so more
  than the other ignitions (permutation inside price bands, 200,000 draws)? Nine declared tests and one sweep of nine
  cells: 18 comparisons, threshold 0.05 / 18 = 0.0028.
- **Verdict by code**, wording fixed in advance: SUPPORTED needs both tests under the threshold and an excess of 15
  points; fewer than 10 alerts or 8 events is INCONCLUSIVE.
- **Positive controls before the freeze.** The same code on synthetic tables: 2 false positives in 600 tables with no
  effect; with 40 alerts, a planted excess of 30 points is found in 48 tables of 60, one of 15 points in 13 of 60.
- **Frozen** on 14 November 2026 at 01:03:19 UTC, before any rate was computed. Two rules were fixed during
  collection, before any outcome was read, and are written in the plan: the burst condition, after the replay of the
  Nobel case showed a 0.16 USD trade starting the clock; and the clipping of price points outside 0 to 1 (14 series).

## The result

| From | To | Count |
|---|---|---:|
| Markets of the population | with a price ignition in their last 14 days | 7,358 of 34,413 |
| Price ignitions (both sides) | | 7,471 |
| | no buy at the moved price in the window | 3,044 |
| | no burst of 500 USD | 3,410 |
| | under 1,000 USD by the alert | 311 |
| | already above 0.90 | 119 |
| **Ignitions confirmed by trades** | | **587** |
| | in documented cases (discovery) | 17 |
| | **in validation** | **570**, from 454 events |

| Class, validation | Alerts | Events | Won | Win rate (95 % interval) | Mean price at the alert | Excess | p |
|---|---:|---:|---:|---|---:|---:|---:|
| **Lonely and thin (the tested class)** | **45** | 44 | 13 | **28.9 %** (17.7 to 43.4) | 25.4 % | **+3.5 points** | **0.33** |
| Lonely, any history | 362 | 329 | 130 | 35.9 % (31.1 to 41.0) | 33.9 % | +2.0 | 0.19 |
| Thin, any share | 49 | 48 | 16 | 32.7 % (21.2 to 46.6) | 25.4 % | +7.2 | 0.14 |
| All confirmed ignitions | 570 | 454 | 206 | 36.1 % (32.3 to 40.2) | 35.0 % | +1.2 | 0.27 |

**Verdict: NOT_SUPPORTED.** For the tested class the excess is 3.5 points, with an interval from -9.8 to +17.9 when
whole events are resampled. Against the other ignitions the difference is 2.5 points (p = 0.42). With any single
event removed, the excess stays between -0.1 and 5.2 points and the p-value between 0.24 and 0.58.

What the table says beyond the verdict:

- **The market is calibrated after an ignition.** An outcome bought up to 0.35 wins about 36 % of the time, whoever
  did the buying. The price already contains what the move means.
- **Neither variable adds anything measurable.** "One wallet did it" adds 2 points, "the wallet is new" 7 points, both
  inside their noise. Together they add 3.5.
- **The sweep finds no better cell.** Nine combinations of thresholds, the best at +7.2 points (p = 0.14).
- **Time.** In the first half of the period the class is at -0.5 points (30 alerts), in the second at +11.5 (15
  alerts, p = 0.22). Too few to read anything into.
- **The planted-effect table bounds what could have been missed.** An excess of 30 points or more would probably have
  been found; one of 15 points probably not.

**What an alert is worth.** In this population the tested class fires 45 times in 96 weeks: about one alert every two
weeks. Thirteen of the 45 named the winning side, at a median of about a day before the price reached 0.95. Thirty-two
did not. Read as a predictor, the alert is no better than the price. Read as a queue of cases to examine, it is short.

## On the documented cases

The same rule, on the events set aside. Counts by case are in
[discovery_cases_summary.json](research_notes/early-detection-2026-11-13/data/discovery_cases_summary.json).

- The tested class fires three times and the side won three times: the Nobel market (the account published as 6741),
  "Maduro out by February 28, 2026?" (the account the Maduro file calls SBet365), and "Will US or Israel strike Iran
  by February 28, 2026?" (an account no file names). Two of the three accounts are ones the files had reached by
  other means.
- It fires on none of the others: no Ballon d'Or market, no Biden pardon market, none of the 46 Google Year in Search
  markets of the population, not the main Maduro market, not the Israel market of June 2025.

Three for three is not a rate. These cases are in the repository because they ended well for someone; the 45 alerts
of the validation are the unselected version of the same measurement.

## The seven families of signals

| Family | What was done | Result |
|---|---|---|
| A. Accumulation before the reveal | The ignition rule above, on 34,413 markets | Tested. No excess over the price |
| B. Coordinated funding and trading | Funding read one and two hops back for the leading account and for other new buyers of an alerted market; direct transfers among the 45 largest buyers of the Nobel market | Finds the documented group of eight (direct payer) and a second group (two hops) on the Nobel night. Whether such groups are rarer among ordinary traders is **not measured**: one market |
| C. Fresh or dormant wallet | The "thin" variable | +7 points, not significant. And on the Nobel night two "new" accounts were operated by an account two years old: a fresh wallet is not a new person |
| D. Several linked markets | The eight accounts of the Nobel group, all their trades | Three of them bought No on the favourite for 39,291 USD. The first also bought 13,529 USD of a candidate who lost. One case, not tested at scale |
| E. Conviction against the account's own past | Purchase size against the median of past trades, for the 45 largest Nobel buyers | Descriptive. The largest buyer spent 59,000 times its median trade. No class was frozen for it |
| F. Early informed cluster | Alert plus a funded group in the hours after | Seen on the Nobel night at 00:50 UTC. Not part of the frozen test |
| G. Structures not looked for | Graph of direct transfers between large buyers; trades between accounts of one funder | Four linked groups made 60 % of the purchases before the Nobel announcement; the first account sold 53,356 shares to two accounts of its own funder. No formal unsupervised method was run, and no base rate exists yet |

What earlier work in this repository had already ruled out stays ruled out: funding within the hour before a first
buy is not distinctive, synchronised entries of new wallets carry no average excess, and a shared service is not a
link.

## The same day, independently

[Pull request 70](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/70) tested an earlier copy of the
same rule on 381 sampled markets and reports no ignition at all. It read prices from an endpoint that returns a
point every 30 minutes; the rule asks for 18 points in six hours and can never be met on that grid, as that report
says itself. On 10-minute points the rule finds a price ignition in one market in five. The two results do not
conflict: that one could not evaluate the rule, this one evaluates it and finds no advantage. That report also finds
no advantage for four simpler rules (volume, new wallet, synchronised buying, concentration).

## The thirteen alerts that named the winning side

None has been investigated. Each is a lead of the same kind as NB-1, with the same caveat: the 32 alerts that named
the losing side look the same at the time of the alert. All 45 are in
[results_tests.json](research_notes/early-detection-2026-11-13/study/derived/results_tests.json).

| First buy, UTC | Event | Side | Price at the alert | Share of the buying | Bought by the alert, USD | Markets traded before |
|---|---|---|---:|---:|---:|---:|
| 2025-05-04 07:16 | israel-military-action-on-yemen-before-june | Yes | 0.29 | 85 % | 1,439 | 0 |
| 2025-07-26 08:11 | thailand-strikes-cambodia-by-friday | Yes | 0.60 | 97 % | 6,175 | 0 |
| 2025-12-13 16:02 | tiktok-sale-announced-in-2025 | Yes | 0.03 | 100 % | 3,500 | 0 |
| 2025-12-25 17:36 | will-trump-meet-with-zelenskyy-by | Yes | 0.10 | 99 % | 5,000 | 0 |
| 2025-12-25 18:21 | what-day-will-the-lighter-airdrop-be | Yes | 0.26 | 97 % | 1,455 | 1 |
| 2026-01-10 13:55 | next-country-us-strikes-759 | Yes | 0.19 | 100 % | 3,020 | 0 |
| 2026-02-10 17:38 | january-inflation-argentina-monthly | Yes | 0.50 | 76 % | 1,200 | 1 |
| 2026-06-03 17:31 | 2026-seoul-mayoral-election-winner | Yes | 0.40 | 57 % | 2,612 | 2 |
| 2026-06-10 02:37 | another-us-strike-on-venezuela-by | Yes | 0.52 | 100 % | 1,525 | 0 |
| 2026-06-21 18:18 | will-russia-capture-dorozhnie-by | Yes | 0.64 | 55 % | 1,192 | 1 |
| 2026-07-30 13:11 | largest-company-end-of-july | Yes | 0.17 | 61 % | 1,113 | 2 |
| 2026-07-30 13:27 | largest-company-end-of-july | No | 0.21 | 57 % | 300 | 1 |
| 2026-10-17 19:19 | of-views-of-grand-theft-auto-vi-launch-trailer | Yes | 0.26 | 90 % | 3,728 | 0 |

## Limits

- **The label is the resolution, not information.** A win does not show that a buyer knew; a loss does not show that
  nobody did.
- **Only moves are seen.** A buyer who accumulates in a deep market without tripling the price raises nothing. The
  largest documented Maduro position was built that way and is not caught.
- **Last 14 days of each market only**, because the price endpoint serves no more per request.
- **Some public-price markets remain** (stock prices carry no tag that separates them from earnings markets).
- **History is read from the last 500 activity rows** before the buy. None of the thin accounts reached that cap.
- **One test family.** Clusters, conviction and linked markets were described on one night and not tested.
- **No independent audit yet.** The blind audits this kind of study normally gets (leakage, statistics, conformity to
  the plan, conclusions) were not run in this pass.
- **A catalogue page was read twice** after a restart (23 repeated event lines); markets are de-duplicated by
  identifier, so no market counts twice.
