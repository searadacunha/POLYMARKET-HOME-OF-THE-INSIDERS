# Analysis plan, written before the table is frozen and before any rate is computed

Question: when one account with almost no trading history supplies most of the buying that lifts a quiet, low-priced
Polymarket outcome (a "lonely thin ignition"), does that outcome win more often than the price at the time of the alert
implies, and more often than after other ignitions?

The plan tries to destroy that hypothesis, not to confirm it. It is fixed here, before the analytic table exists; any
later change is an amendment (amendements/NNN-*.md) and is listed at the end of results.md as a deviation.

Origin of the hypothesis: one case only, the Nobel Peace Prize 2025 market (account "6741", 9 October 2025). That event
is excluded from every test. The thresholds below were set from that case and from round numbers, with no other market
looked at.

## Data

- Catalogue: Gamma `events/keyset?closed=true&volume_min=50000`, all pages (`code/col_10_universe.py`), read on
  13 November 2026.
- Prices: CLOB `prices-history` of the YES token, 10-minute points, last 14 days before each market closed
  (`code/col_20_prices.py`). The endpoint refuses longer intervals; ignitions older than 14 days before the close are
  outside the study.
- Tapes: data-api `v2/trades?condition=...&taker_only=false` around each price ignition (`code/col_30_tapes.py`).
- Initiator history: data-api `v2/activity` strictly before the first buy, 500 rows at most, and Gamma
  `public-profile` (`code/col_40_baselines.py`).
- Price points outside [0, 1] are a source artefact (14 series of 34,413: a midpoint slightly above 1 at the end of a
  market, and one negative point). They are clipped to [0, 1] and counted, not excluded: excluding them would depend on
  how the market ended. A clipped point cannot create an alert by itself, since an alert needs trades at that price.
  Rule fixed on 14 November 2026 after the collection raised on the first such series, before any outcome was read.
- Collection accounting, reported in results: requested / answered / empty / errored / rate-limited per source.
  An error is never counted as an empty result: collectors raise or store an error row.
- Known source traps checked before freezing: the trades stream is newest-first and ignores time filters (asserted on
  every page); closed markets are served by the catalogue only with `closed=true`; the data API indexes the trading
  proxy, not the owner key; with `taker_only=false` a purchase appears once as a BUY row of the buyer, maker or taker,
  so buy cash is not double counted; identical rows are distinct fills and are kept; `end` is honoured by the activity
  endpoint (asserted on every answer); profile text fields are never stored.
- The analytic table is written once by `code/ana_00_freeze.py`; its sha256 goes into PROTOCOL.lock with this plan.

## Unit of analysis and effective n

- Unit: one ignition = the first ignition of one side (YES or NO) of one market.
- Clusters: the event (several markets of one event, or both sides of one market, are not independent) and the
  initiator wallet.
- Every nominal n is reported with its number of distinct events and distinct initiators. Confidence intervals
  resample whole events. The exact test T1 assumes independence; within an event at most one YES outcome can win,
  a negative dependence that makes T1 conservative.

## Population

- Events: closed, volume of at least 50,000 USD, with none of these tags: `games`, `esports` (match-level sports and
  e-sports), `crypto-prices`, `hit-price`, `up-or-down`, `multi-strikes` (public price processes), `weather`,
  `tweets-markets`, `mention-markets` (public counters and meteorology). The list is fixed from the tag vocabulary
  alone.
- Markets: outcomes exactly Yes/No, two token ids, volume of at least 10,000 USD, closed between 2025-01-01 and
  2026-10-31 UTC, resolved to 1/0 or 0/1. Markets resolved otherwise are excluded and counted.
- Ignition, side S, on the 10-minute price x of S (x = p for YES, 1 - p for NO), at grid time t1:
  baseline window [t1 - 7 h, t1 - 1 h) with at least 18 points, median <= 0.15 and maximum <= 0.20;
  x(t1) >= max(3 x median, median + 0.10). Only the first such t1 of each side is kept. t0 is the first grid time in
  [t1 - 1 h, t1] where x > 1.5 x median.
- Trade confirmation: t_first = time of the first BUY of token S at a price >= 1.5 x median in [t0 - 10 min, t1]
  that opens a burst, meaning the BUYs of S in the 15 minutes from that trade total at least 500 USD.
  No such trade: excluded and counted. (The burst condition was added after the replay of the Nobel case, the only
  case read: without it a 0.16 USD trade at 22:10 UTC started the clock and named the wrong account as initiator.
  No other market had been read when the rule was fixed.)
- Alert time: t_alert = max(t1, t_first + 15 min). Buys of S in [t_first, t_alert] must total at least 1,000 USD.
- p_alert = price of the last BUY of S at or before t_alert. Ignitions with p_alert > 0.90 are excluded and counted:
  a jump that ends near 1 is a public resolution, not a pre-reveal move.
- Tapes needing more than 300 pages (300,000 rows after the window) are excluded and counted (`too_deep`); this drops
  ignitions of very heavily traded markets and is a stated limit.
- Survivorship: only resolved markets can be scored. Open or voided markets are counted, not scored.

## Labels

- Primary label: win = 1 when the market resolved in favour of side S (Gamma `outcomePrices`), else 0.
- The label is joined last, by `ana_00_freeze.py`, from `derived/labels.jsonl`, which no feature code reads.
- Price used as the reference of the label: p_alert, an executed trade price, never a chart high.
- Sampling cadence: 10-minute points for the ignition, every trade for p_alert. Fixed now.
- An ignition is dated at its start (t_first), the alert at t_alert.
- Missing windows or failed collections: complete-case (excluded and counted), never scored as losses.
- Secondary description (no test): time from t_alert to the first 10-minute point at 0.95 or more.

## Features and point-in-time rule

- Decision time is t_alert. Every feature uses only the price points at or before t1 and the tape rows at or before
  t_alert; the initiator history uses only activity strictly before t_first.
- initiator = the wallet with the largest BUY cash on S in [t_first, t_first + 15 min] (ties: earliest buy).
- share15 = initiator BUY cash / all BUY cash on S in that window. LONELY = share15 >= 0.5.
- prior_markets = number of distinct markets traded by the initiator before t_first (within its last 500 activity
  rows). THIN = prior_markets <= 2.
- Class tested: LONELY_THIN = LONELY and THIN.
- No field computed after t_alert, no field derived from the label, no file built on a population conditioned by the
  outcome.

## Splits

- DISCOVERY: every event that holds a market of a case already documented in the repository (list frozen in
  `derived/discovery_events.json`, built from the repository before the table is written; it contains the Nobel 2025
  event that produced the hypothesis). Reported as worked cases, never tested.
- VALIDATION: all other events. Read once, by the frozen code.
- Chronological halves of VALIDATION for robustness: t_first before / from 2026-03-01 UTC.
- Entity leakage: an initiator present in both sets is reported; the tests do not use wallet identity as a feature.

## Tests

- Primary, on VALIDATION, class LONELY_THIN:
  - T1: excess = win rate - mean p_alert is greater than 0 (exact Poisson-binomial tail, one-sided).
  - T2: the excess of the class is greater than the excess of the other ignitions (label permuted inside p_alert
    strata <= 0.3, 0.3-0.6, > 0.6; 200,000 permutations; one-sided).
- Secondary, declared, reported, never used for the verdict: T1 and T2 for LONELY alone and for THIN alone (value
  added by each variable against the simpler rules); T1 for LONELY_THIN in each chronological half; T1 for all
  ignitions pooled (is the market calibrated after any ignition).
- Exploratory sweep, one registry line of 9 comparisons: T1 for share15 >= 0.3 / 0.5 / 0.7 crossed with
  prior_markets <= 0 / 2 / 5.
- Declared number of tests: 9, plus the sweep of 9. Every computed test goes into registre/tests.jsonl; the correction
  uses the registry count of comparisons on real data, not this number.
- Correction: Bonferroni, alpha 0.05.
- Monte Carlo p-values: 200,000 permutations; 0 hits is reported as a bound, never as an estimate. T1 is exact.

## Positive controls (before freezing)

- `code/ctrl_10_positive_controls.py` runs T1, T2 and the verdict on synthetic tables of 1,500 ignitions: no effect,
  an excess shared by all ignitions (must stay silent), and planted class effects of 0.15, 0.30 and 0.50, for 8 to 80
  flagged rows, 60 seeds per cell. Report: `controles/positive_controls.md`.
- Freezing is allowed only if the null cells stay silent and the power table is written.

## Robustness variants (fixed now)

- The 9 cells of the sweep; the two chronological halves; the result with each single event removed (largest change
  reported). They are reported, never used to pick.

## Verdict

- Computed by `code/ana_90_verdict.py`, wording fixed now, with n = LONELY_THIN ignitions in VALIDATION:
  - INCONCLUSIVE if n < 10 or they come from fewer than 8 distinct events.
  - SUPPORTED if T1 and T2 both pass the Bonferroni threshold and the excess is at least 0.15.
  - NOT_SUPPORTED otherwise.
- What the verdict will not cover: whether any account held private information; markets outside the population;
  ignitions older than 14 days before a close; tradability (spreads, depth and fees are ignored); the period after
  October 2026.

## What this plan must not do

- No threshold, window, label or population chosen after looking at VALIDATION.
- No removal of observations after seeing their outcome.
- No new test promoted to "primary" after results.
- A high excess is a statement about a class of trades. It is never a statement about a person, and a win is not
  evidence of private information for any single account.

## Amendments

None at freeze. Later changes: `amendements/NNN-<date>.md`, each with the date, the reason and the line
`resultats_vus: oui|non`. Any analysis changed after results were seen is EXPLORATORY in results.md.
