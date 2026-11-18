# Analysis plan, written before the table is frozen and before any rate is computed

Question: on Polymarket, do large purchases that look unusual at the moment they are made (fresh funding spent on one
side, a dormant account reactivated, a bet far out of character, wallets paid by the same plain key, or a rare
combination of such features) win more often than the price paid implies, and more often than ordinary large purchases
at the same price and horizon?

The plan tries to destroy each hypothesis, not to confirm it. It is fixed here, before the analytic table exists; any
later change is an amendment (amendements/NNN-*.md) and is listed at the end of results.md as a deviation.

Why this study is not the previous one. The frozen study of 14 November 2026 (lonely thin ignitions, verdict
NOT_SUPPORTED) started from price jumps and asked who bought. Its sample was conditioned on a move of the price and on
the closing date of the market. This study starts from the purchases themselves, whether or not the price moved, and
dates markets by their scheduled end, known in advance. The four simple rules of pull request 70 (volume, wallet new to
the market, synchronised buying, concentration in one hour) are not retested. No threshold below was chosen by looking
at an outcome: they come from round numbers, from the unvalidated flags of the installed TriAgent collector, and from
the documented cases, all of which are placed in the discovery set.

## Data

- Catalogue (`code/col_05_catalogue.py`): Gamma event listings with an event volume of 50,000 USD or more. Closed
  events: the catalogue read on 13 November 2026 for the previous study (158,494 events, sha256 in
  `data/catalogue_counts.json`). Open events: read on 14 November 2026 (1,531 events), because their already closed
  markets are absent from a listing of closed events, and leaving them out would keep a "by date" market only when its
  whole event has ended, which depends on the outcome.
- Fills (`code/col_20_fills.py`): data API `v2/trades?condition=...&filter_type=CASH&filter_amount=1000`,
  `taker_only=false`, full history of each market of the universe. One row per order fill of 1,000 USD or more, seen
  from the owner of the order (maker or taker). A second pass with `taker_only=true` marks aggressor rows; it is used
  for description only. Fills of one second are taken in the order the source served them, which fixes the entry
  chosen inside a second.
- Wallet histories (`code/col_30_activity.py`, `code/col_31_asof.py`): data API `v2/activity` with deposits and
  withdrawals. First 1,000 rows of each wallet, oldest first; for an entry that lies beyond that page, the 500 rows
  before the entry, and the rows of the 24 hours after it when the entry must be watched. The age of the wallet is
  always taken from its first row, on the first page; a view built from the 500 rows is marked, and the entries whose
  500 rows cover less than 24 hours are counted.
- Funding (`code/col_40_funding.py`): Polygon receipt of each deposit made in the 24 hours before an entry by a thin
  or dormant wallet; apparent payer read from the Transfer logs of that transaction (`code/chainfund.py`). When the
  apparent payer is a contract (a pool, a settler, a ramp), the deposit is usually the wallet's own money being
  swapped into the collateral token, so the collateral transfers received by the wallet in the 10,000 blocks (about
  four hours) before the deposit are read from the logs as well. Every address met is described by code, number of
  transactions sent (read today) and public name tags (Blockscout metadata); one further hop, over the same window,
  for an address that is a key with five transactions or fewer. This step was added before the freeze, after the
  reader had been run on the documented Nobel 2025 account: its deposit is paid by a Uniswap pool, and the key that
  funded it sits 39 blocks earlier. No outcome had been read. Every deposit of the 24 hours is traced (a first version
  kept the last three only; the pre-freeze audit found 1,526 deposits left out).
- Funding received on the chain (`code/col_41_inflows.py`): the activity listing calls DEPOSIT only some of the ways
  money reaches a wallet. The pre-freeze code audit of 14 November 2026 (`audit/sfh_collecteurs_20261114.txt`) measured
  the share of first trades with no deposit row before them at 1.6 % or less until October 2025 and 26 % in August 2026,
  and eight such wallets drawn at random had all received collateral on the chain in the 24 hours before; no outcome had
  been read. The Transfer logs of USDC, USDC.e and pUSD to the wallet are therefore read, for every entry whose class
  depends on it: thin or dormant entries not fresh by their deposit rows (window of 24 hours), and the R1 candidates
  (window of 30 days). The block range comes from an interpolation of block times widened by a margin, checked
  against the block headers; rows are kept by their own block timestamp, strictly before the entry.
- Collection accounting, reported in results: requested / answered / errored / rate-limited per run, appended to
  `data/collect_counts.jsonl` (from the corrected code on; the counts of earlier runs survive only where their logs do,
  a limit reported in results). An error is never counted as an empty result: collectors raise or store an error row,
  and errors are retried.
- Known source traps checked before freezing: the trade stream is newest first (asserted on every page); the size
  filter is honoured (asserted on every row); a row belongs to the market asked for (asserted); with
  `taker_only=false` a purchase appears once as a BUY row of the buyer, so buy cash is not double counted; identical
  rows are distinct fills and are kept; a few rows are served with size times price a little under 1,000 USD (16
  markets of 32,552): the source decides, they are kept and counted (the size filter is counted, not asserted); the global feed without a market stops at 1 October 2026, so history is read
  market by market; the activity listing is oldest first and belongs to the wallet asked for (asserted); a public node
  can answer `null` for a receipt it does not hold, so a null is believed only when every endpoint says null; profile
  text fields are never stored.
- The analytic table is written once by `code/ana_00_freeze.py`; its sha256 goes into PROTOCOL.lock with this plan.

## Unit of analysis and effective n

- Entry: the first BUY fill of 1,000 USD or more of one wallet on one side (Yes or No) of one market.
- Alert of a class: the moment an entry meets the class (defined below), with the price the wallet paid at that moment.
- Unit of every test: one alert per event, the earliest of the class in that event. Several markets of one event, both
  sides of one market, and several wallets on one side are not independent; they collapse into one alert.
- Clusters: the event. Stories that span several events (a war, an election night) remain a dependence between events;
  a robustness variant resamples calendar weeks instead of events.
- Every nominal n is reported with its number of events and of distinct wallets.

## Population

- Events: volume of 50,000 USD or more, with none of the tags `games`, `esports`, `crypto-prices`, `hit-price`,
  `up-or-down`, `multi-strikes`, `weather`, `tweets-markets`, `mention-markets` (outcomes produced in public view).
- Markets: outcomes exactly Yes/No, two token ids, volume of 10,000 USD or more, SCHEDULED end date (`endDate`) between
  2025-01-01 and 2026-10-31 UTC, closed and resolved to 1/0 or 0/1 when the catalogue was read. Markets in the period
  that are still open or resolved otherwise are counted (146) and not scored. 32,552 markets in 7,554 events.
- Two families, fixed from the tag vocabulary alone (`code/feat_10_universe.py`):
  INFO (21,165 markets): the outcome is an event, a decision or an announcement.
  PUBLIC_PROCESS (11,387 markets): season-long sports, listed prices, public counters. Nobody can hold the outcome in
  advance there. It is the negative-control family: a class that "works" there is not detecting private information.
- Eligible entry: price of the fill at 0.90 or less, and time of the fill before the scheduled end plus 24 hours when the
  scheduled end falls at 00:00 UTC (that is, before the end of the day it names), before the scheduled end otherwise. The scheduled end is a date: 17,630 of the 32,552 end dates fall at 00:00 UTC and
  the event happens during that day (the Nobel 2025 market "ends" nine hours before the announcement). A first rule
  stopped at the scheduled end itself; read on the dates alone, before any outcome, it removed 24,450 entries, 11,514
  of them in the 24 hours after the end date, that is the day of the event for most markets. The strict rule is kept
  as a robustness variant. An end at any other time is a deadline ("by 30 April, 23:55"), not a date: the day after it is
  not included there (pre-freeze leakage audit, 14 November 2026: 3,668 eligible entries lay after such an end, some of
  them bought at 0.84 to 0.89 once the deadline had passed; no outcome had been read). 210,021 eligible entries.
- Screen: wallet histories are read for eligible entries that pass a screen computed from the fills alone: at most two
  other markets of the universe with a fill before (possibly thin), or no fill for 60 days (possibly dormant), or a
  fill at least five times the median of at least five earlier fills and larger than all of them (possibly out of
  character). In INFO every screened wallet is read; of the wallets seen only in PUBLIC_PROCESS, 25 % are read, chosen
  by a hash of the address (a wallet also seen in INFO is read whole, so the PUBLIC_PROCESS entries evaluated are not a
  25 % sample of entries: the count is reported). For that reason a PUBLIC_PROCESS entry counts as evaluated only when
  its wallet is in the hash sample: a wallet read because it also bought in INFO, possibly later, would make the
  negative-control family depend on the wallet's future. Entries outside the screen cannot be thin, so they cannot belong
  to C1, C6 or C7; the screen's "no fill for 60 days" uses fills of 1,000 USD or more on any market while DORMANT uses
  every trade on other markets, so a few dormant wallets lie outside the screen (they are controls of C2, C4 and C5:
  stated limit). C3, R1 and the M classes are defined inside the screen.
- Survivorship: only resolved markets can be scored. The scheduled-end rule keeps a market whether it ended early or
  late. A market that never reached 10,000 USD, or an event under 50,000 USD, is outside: small markets are not covered.

## Labels

- Label of an alert: win = 1 when the market resolved to the side bought (Gamma `outcomePrices`), else 0.
- Reference price: the price paid by the alerted wallet in the fill that makes the alert. Never a chart price.
- The label and the real closing time are written to `derived/labels.jsonl` by `feat_10`, read by no feature code, and
  joined last by `ana_00_freeze.py`.
- Excess of an alert: win minus reference price, in probability points.
- What followed an entry (later buying of the wallet, next price paid by somebody else five minutes later or more) is
  kept in a separate table and used only to describe results: lead time and the price a follower would have paid.
- Missing histories, receipts or chain reads: complete-case (excluded and counted), never scored. An entry whose
  membership of a class is unknown (chain read missing for a class that needs it; a deposit, payer description or
  swap inflow missing for C4 and C5) is neither an alert nor a control of that class.

## Features and point-in-time rule

- Every quantity attached to an entry uses fills dated strictly before it, wallet rows dated strictly before it, and
  the entry fill itself. Fills of the same second belong to the same matches and are not "before".
- The class that needs the wallet to keep buying (C7) is evaluated by advancing through the wallet's rows after the
  entry, one at a time, for 24 hours; the alert is dated at the first row where the condition holds and uses only rows
  up to it (`code/asof.py`, `watch`).
- A payer's description is read today (code, transaction count, tags): an address that became a service after the
  entry is treated as a service. This can only remove links. The fan-out of a payer is counted as of the entry.
- The same code computes the features in the study and in the live engine.

## Classes (each is a yes/no property of an entry, with its alert moment)

Wallet terms, as of the entry: THIN = at most 2 other markets traded before, at most 50 trades on them, and fewer than
1,000 activity rows before. FRESH = a deposit row, or a collateral transfer received on the chain from an address that
is not one of Polymarket's contracts (exchanges, conditional tokens, adapters, ramps), in the 24 hours before. DORMANT = at least one earlier trade on another
market, the latest of them 60 days or more before. HEAVY at a moment = net buying of the side since 24 hours before the
entry reaches 10,000 USD.

A first draft asked for "concentration": half of the deposits of the last 7 days on one side. Read on the wallets of
the discovery set before any outcome, it kept 87 % of the fresh entries of thin or dormant wallets, so it selected
almost nothing, and it missed the documented Nobel 2025 account, which spread 40,000 USD over three markets and kept
depositing. It was replaced by an amount, and the classes below were rewritten once, before the freeze.

| Class | Definition | Alert moment and price |
|---|---|---|
| C1 FRESH_FUNDED_BET | THIN and FRESH | the entry |
| C2 DORMANT_REACTIVATION | DORMANT and FRESH | the entry |
| C3 OUT_OF_CHARACTER | at least 20 earlier trades among the rows read (the whole history, or its last 500 rows for a wallet with more than 1,000), the first of them at least 7 days before the entry; entry fill 10 times their median or more, and larger than all of them. The 7 days were added before the freeze, after the first live alert of the engine named a wallet whose 1,000 newest rows covered 3.8 hours. No outcome had been read | the entry |
| C4 COFUNDED_GROUP | (THIN or DORMANT) and FRESH; a plain key behind a deposit of the wallet is also behind a deposit of another such wallet that entered a market of the same event in the 7 days before | the entry that completes the pair |
| C5 RECURRENT_FUNDER | (THIN or DORMANT) and FRESH; a plain key behind a deposit of the wallet was behind a deposit of another such wallet that entered a market of a different event at least 7 days earlier | the entry |
| C6 QUIET_FRESH_LOW | C1, no fill of 1,000 USD or more by another wallet on the market in the 6 hours before the entry, entry price at 0.50 or less | the entry |
| C7 HEAVY_NEWCOMER | C1, and HEAVY within 24 hours of the entry | the first fill at which HEAVY holds, at the price paid in it |
| R1 S_FRESH_REPLICATION | the rule S_FRESH of the Maduro and Iran file (phase 8, pre-registered there, found "promising, weak" on 30 events and to be retested unchanged on a larger sample): wallet 48 hours old or less at the entry, and at most 2 earlier fills in the universe. The unit differs (entries of 1,000 USD or more here, taker trades of 100 USD or more there). The age is the one pre-registered there: entry time minus the first inflow of collateral not related to trading, read here as the earlier of the wallet's first activity row and the first collateral transfer it received in the 30 days before the entry (before its first row a wallet holds no position, so any transfer is funding). A first version used the first deposit row, which missed chain-only funding and, beyond the first page, read the first deposit of the 500 rows; corrected before the freeze. Money received more than 30 days before a first row is not seen (stated limit) | the entry |
| M1 RARITY_TOP1 | rarity score (sum over eight directed features of minus log10 of the tail share in discovery) at or above the 99th percentile of discovery | the entry |
| M2 IFOREST_TOP1 | isolation-forest score at or above the 99th percentile of discovery | the entry |
| M3 EDGE_TOP5 | predicted probability minus price, from a logistic model with the price as offset fitted on discovery outcomes (INFO entries with a history read, made on 31 March 2026 or earlier, outside the documented cases), at or above the 95th percentile of those entries. Validation entries made on or before 31 March 2026 are contemporary with the outcomes learnt: M3 is unknown there (pre-freeze leakage audit) | the entry |
| B1 BIG | entry fill of 10,000 USD or more (baseline: size alone) | the entry |
| B2 AFTER_MOVE | price of the entry at least 0.10 above the price of the last fill an hour or more earlier (baseline: momentum) | the entry |
| B3 THIN_NOT_FRESH | THIN and not FRESH (baseline: newness alone) | the entry |

FRESH in detail. Money received on the chain counts from 1 USD and is not funding when it is: the transfer of a deposit
row; in the same second as an activity row that is not a deposit (a sale paid by the counterparty, a redemption, a
reward, a withdrawal: the activity time is the block time); sent by one of Polymarket's contracts (the list of
`chainfund.INFRA`, which includes Wrapped Collateral, and every address whose public name tag names Polymarket); or pUSD
minted to the wallet whose receipt shows no payer other than the wallet. A pUSD mint paid by somebody else counts, with
that payer as its sender. A first version counted any sender outside the contract list: the second pre-freeze audit
found that 69 of the 83 entries it made fresh on a sample were redemptions, rewards and sales; corrected before any
outcome was read. Every transfer left out is counted by reason. Chain inflows are traced like deposits, so their payers
can be roots of C4 and C5. The features of the M classes keep the deposit rows only, one definition for every entry.

A plain key: no code, no public name tag, fewer than 1,000 transactions sent, and at most 10 wallets of this dataset
paid as of the entry. A key is "behind a deposit" when it is the apparent payer, or a sender of what the wallet
received in the 10,000 blocks before a deposit paid by a contract, or the sender that paid a pass-through key behind
either; a pass-through key is read over the window of each payment it made. Every other address is a service and never
links two wallets. An alert whose price is above 0.90, or whose moment is after the eligibility limit above, is not
counted (and is counted as such). An entry of C1 that did not turn heavy is not a control of C7 (its status depends on
the 24 hours that follow); an entry of C1 whose 24 hours were not read and that is not heavy has C7 unknown. Entries made
after the real close of the market are kept and counted (the close is known only afterwards); the robustness variants
of lead time describe them.

## Splits

- DISCOVERY: events whose last scheduled end is 31 March 2026 or earlier, and every event of a case already documented
  in this repository whatever its date: the events listed in `data/documented_cases_20261113.json` (17 events found).
  A first version also caught every slug containing "nobel-peace-prize", which put the 2026 prize, documented nowhere,
  in discovery; removed before the freeze. The last scheduled end is taken over the markets of the event in the period
  whatever their resolution. 4,915 events, 19,958 markets.
- VALIDATION: the other events, scheduled ends from 1 April to 31 October 2026. 2,639 events (1,924 INFO, 715
  PUBLIC_PROCESS), 12,594 markets. Read once, by the frozen code. An event is placed by its scheduled end, not its
  entries: some validation entries were made before 1 April 2026 (the M3 rule above). Documented cases stay in discovery
  whatever their date, which removes from validation events that are documented because somebody won (stated limit).
- An event is in one set with all its markets. A wallet can appear in both; the M scores are fitted on discovery only,
  and the thresholds of M1, M2 and M3 are quantiles of discovery.
- Known contamination: the previous study published the outcome of 45 alerted markets of its validation set. They
  stay where the rule puts them.

## Tests

- T1, per class, on VALIDATION and INFO: exact one-sided test that the alerted sides win more often than their prices
  say (sum of independent Bernoulli with the alert prices, one alert per event).
- T2, per class, same population: difference of mean excess between the alerts and the control entries (eligible
  entries of the same set and family that are not alerts of the class, one mean per event and stratum), inside strata
  of price (cuts 0.10, 0.25, 0.50, 0.75) and of hours to the scheduled end (cuts 24, 168, 720), events resampled whole;
  one-sided p = (hits + 1) / (draws + 1), hits being the resamples with a difference of zero or less. 2,000 draws, then
  20,000 when fewer than 2 % are hits, then 100,000 when fewer than 0.2 % are, then 500,000 when fewer than 0.05 % are.
- Declared comparisons: 11 classes (C1 to C7, R1, M1 to M3) x 2 tests = 22; 3 baselines x 2 tests = 6; T1 of the 11
  classes on VALIDATION and PUBLIC_PROCESS (negative control) = 11; T1 of the 11 classes on DISCOVERY and INFO
  (description of the set the scores were fitted on) = 11; one sweep of 11 cells for C1 (5 price bands, 4 horizons, 2
  halves of the period, cut at the median alert time); one placebo line (200 random classes of the size of C1 inside its strata: the share with
  p < 0.05 is one diagnostic number); one line for the robustness variants (estimates and intervals, no p-value).
  Total 63. Every computed test goes into registre/tests.jsonl; the threshold uses the registry count. Correction:
  Bonferroni, alpha 0.05, so 0.05 / 63 = 0.00079 if nothing else is computed.
- A p with 0 hits is reported as a bound (p < 3/draws), never as an estimate.

## Positive controls (before freezing)

- The whole analysis (classes to alerts, T1, T2, the edge model, the verdict) on synthetic tables of the shape of the
  analytic table (`code/ctrl_10_positive_controls.py`), where entries of one market side share one outcome: nothing
  planted (20 seeds), and a planted excess of 3, 5, 10 and 15 points on one class (6 seeds), each for about 150, 500
  and 1,500 alert events; one variant with outcomes correlated across the events of one week; one variant where every
  entry beats its price by 5 points (T1 must fire and the verdict must not). The collection and feature code is
  checked separately, by self-tests and on documented accounts of the discovery set.
- Freezing is allowed only if the null stays silent and the power table is written (`controles/positive_controls.md`).

## Robustness variants (fixed now, reported, never used to pick)

- Calendar weeks resampled instead of events. Any single event removed (range of the excess).
- Alerts strictly before the scheduled end date only (the first eligibility rule).
- Alerts at least 6 hours before the real close, and at least 24 hours before (the close is known only afterwards: this
  describes how early an alert was, it does not select alerts).
- The price a follower would have paid: next fill of another wallet five minutes or more after the entry (for C7, the
  entry, not the later alert moment: stated limit), among followers paying 0.90 or less.
- Entry fills of 2,000 USD or more, and of 5,000 USD or more.
- Description by coarse category (geopolitics, politics, technology and business, economy, culture, crypto, other: fixed
  from the tag vocabulary), by half of the period, the number of alert events a week, and the share of the winning
  entries bought at 0.30 or less that a class holds against its share of all entries bought at 0.30 or less.

## Verdict

Computed by code (`code/ana_90_verdict.py`) for each class, wording fixed now:

- SUPPORTED: at least 30 alert events, T1 and T2 both under the corrected threshold, and an excess of 5 points or more.
- NOT_SUPPORTED_EFFECT_EXCLUDED: not supported, and the upper end of the 95 % interval of the excess (events
  resampled) is under 5 points: an advantage of 5 points is ruled out at this sample size.
- NOT_SUPPORTED_UNDERPOWERED: not supported, and that interval still contains 5 points.
- INCONCLUSIVE: fewer than 30 alert events.
- A class SUPPORTED on INFO whose T1 on PUBLIC_PROCESS is also under the threshold is reported as NOT_SPECIFIC.

Documented cases. `code/ana_70_cases.py` lists, for each event of a case already documented in this repository, the
classes that fire and when. It is a listing, with no rate and no test: those events are in the repository because
somebody won.

What a verdict will not cover: identity, intent, or private information of anybody. A class that wins more than its
price is a class of trades that was profitable over this period; it says nothing about one account. Fees are ignored.
Markets under the volume floors, purchases split into fills under 1,000 USD, and the period before 2025 are outside.

## What this plan must not do

- No threshold, window, label or population chosen after looking at VALIDATION.
- No removal of observations after seeing their outcome.
- No new test promoted to "primary" after results.

## Amendments

None at freeze. Later changes: `amendements/NNN-<date>.md`, each with the date, the reason and the line
`resultats_vus: oui|non`. Any analysis changed after results were seen is EXPLORATORY in results.md.
