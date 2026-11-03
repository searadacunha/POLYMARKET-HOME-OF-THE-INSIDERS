# Analysis plan, written before the table exists and before any rate of this holdout is computed

Question: on markets no one has analysed yet, when at least three distinct wallets enter one low-priced outcome within 300 seconds, does that outcome beat the price paid more than entries made at the same price, on an equally busy and equally moving token, at the same distance from the deadline?

The plan tries to destroy that hypothesis, not to confirm it. It is fixed here, before the analytic table exists. Any later change is an amendment (`amendements/NNN-*.md`), listed at the end of `results.md` as a deviation.

Nothing here can show insider trading. A set of three entrants is a timing pattern. A public report, a shared signal channel or a bot produce the same picture. No wallet is named as suspect by this study.

## Role of the data already seen

This is a second study and it is not blind to the first. That is stated here, because a reader cannot see it from the numbers.

- **`study_sync` (frozen 2026-11-03, verdict `NOT_SUPPORTED`).** Its 2,091 markets, with end dates up to 2026-09-15, and its results were read by the author of this plan. They are the **design set**. They shaped this plan through the audit of that study. They enter no confirmatory test here. Its protocol and results are not rewritten.
- **What was taken from them.** Structure for the synthetic controls: counts of entrants per token and tokens per event. How `endDate` behaves against `closedTime`. The design defects come from the audits of that study. Three choices here were made knowing its results and its audits: the primary window of 300 s, partly on its set-count ratio, which partly passes H2 before any new data; the bound of +0.10, which comes from its audit's power figures; and replacing its placebo. Its difference at 300 s (+0.0031) gave no reason to favour that window, and the bound and the control are stated before any new rate exists.
- **Holdout.** Only rows at or after 2026-09-16 00:00 UTC are scored, so no scored row falls in the first study's period, whatever market it belongs to. Earlier rows of a market still count for its features. Markets of that study are excluded. So are the catalogue, the Ballon d'Or family, and any slug that names their world facts (`derived/seen.json`, fixed at the freeze). A question that recurs under another deadline stays, because its later rows are new. The author has computed no outcome rate on the holdout at the date of this plan. The PolySentinel collector and the ChangeNOW join have read rows of that period, without any outcome rate.

## Corrections, one for each defect the audits found

| Defect in `study_sync` | Change here |
|---|---|
| The matching key `total` counts entrants over a token's life, and descends from the outcome | Removed. Every matching variable is known at the row's time |
| Reference price is a VWAP up to the trigger, so momentum looks like excess | Each arm is scored at its own row's paid price, the trigger row for a set |
| Control membership depends on later rows | A control is a row with no set at its own time. It stays a control even if a set forms later: this can only weaken the contrast |
| Controls of the same token share the outcome, so a true effect is hidden and a bound is false | Each trigger is scored only against controls from other world facts |
| Rows inside a cooldown left the base without being events | A set inside a cooldown is dropped from both arms and counted. Rows with no set stay controls |
| Lifetime volume filter reads the future | A row is eligible only if the market's taker volume strictly before it reached $25,000. Collection stops at $20,000 lifetime on Gamma's own figure, a margin so that this floor removes almost nothing the rule would keep |
| Universe of closed markets favours early resolution | Markets enter by scheduled `endDate`, read at least 30 days later. A market due later never enters because it resolved early. Those still open are counted and leave |
| `closedTime` lags the public event, so stale asks enter | Rows are out from 60 s before the token first trades at 0.90 or more, after close, and when a later row of the token within 1,800 s trades 0.10 or more above them. This reads later rows, and only to remove rows, in both arms. It lowers excess in both arms, and removes real sets close before a public move: a known cost, in favour of the null |
| Same-second rows entered `crowd` | State moves one second at a time. Crowd excludes the window itself, so a control can exist at every window. Inside a second, rows run by rising price: the tape's order is not trusted, and a set ends on its dearest row |
| Six windows at Bonferroni, floors above the stated threshold | One primary window, 0.05 two-sided, 9,999 draws. Three other windows are secondary, reported with Benjamini-Hochberg, and never change the verdict |
| H2 not monotone because of the cooldown, jitter of ten windows inverting long windows | H2 counts rows inside any set, with no cooldown, and rises with the window by construction. Offset within five windows |
| H2 moved rows independently across markets | One offset per wallet per UTC day, across all its markets |
| Clusters too fine, one world fact spanning events and ladders | Clusters are connected components over event, negRisk group and slug stripped of dates. Two differently worded markets on one fact stay apart, so a positive result must also hold with whole calendar weeks as clusters |
| Placebo keeping the cell, able to veto a true effect | Replaced by a negative control exposure, see below. It can catch confounding and cannot clear it |
| Controls ran on 3 seeds, 4 windows, some reduced. A trap passed. No power at +0.10 | 100 seeds on each null and trap at the stopping size, 20 on effects, every window, three sizes, a power table, and the stop rule comes from that table |
| No way to say "ruled out" | A bound is part of the verdict: `BOUNDED_NULL` only if the upper end is under +0.10 for the difference, for the same test with weeks as clusters, and for the raw excess of triggers against the paid price. If every token held sets, a difference with controls would show nothing, and the raw excess still would |
| No effective n, and sets could rest on a few wallets | At least 60 effective facts by the Kish formula, on top of 100 facts with a trigger. A positive result must survive removing the 5 wallets most often in sets |
| A slow public reaction looks like an early entry | A positive result must also hold after removing rows within 12 hours before a rise of 0.05, see below |
| Size filter of $100 applied at collection | All taker rows are read. An entrant is the wallet's first row of any size, and it must be at least $100 |

The label `PREDICTIVE_TIMING_PATTERN` is dropped. It claimed more than the test shows.

## Data

- Source: Gamma `/markets` for the universe, without outcomes (`code/col_10_universe.py`). Data API `/v2/trades?taker_only=true` for tapes, one file per market, all rows of the market's life (`code/col_20_tapes.py`). Seen list: `code/col_05_seen.py`.
- Outcomes are read once, after the table is frozen, by `code/col_30_outcomes.py`, into one file named by the amendment that closes the holdout. Only markets ending on exactly 1 and 0 enter.
- **What blindness rests on.** Tapes hold prices, so a final price shows an outcome to anyone who looks. No script before `ana_10_primary.py` reads or prints a price summary, and `ana_00_freeze.py` prints counts only. The guard leans on later prices, so the stopping count leaves it out. This rests on the code and on discipline, and no mechanism enforces it.
- Accounting, in `derived/freeze_counts.json` and each `derived/collection_*.json`: markets requested, kept, out of scope, excluded as seen, still open past their due date, no event, tapes missing, partial and empty, repeats across pages, rows, entrants, eligible, HTTP errors, network errors. An error is never an empty tape. A walk that ends with more rows announced, or an empty page with a cursor, raises, and the market stays unread and counted, because a cut loses the oldest rows and a later row would pass for a wallet's first.
- Traps checked: pagination runs newest first by cursor, a page cap marks the tape partial and it leaves the table; repeats are dropped across pages only, as equal fills inside one page are real; Gamma's offset pages are ordered by id, unique, so they cannot skip on ties; maker fills are not read, so a wallet's earlier resting order is invisible and "first row" means first taker row. `endDate` was checked on the first study's universe: Gamma leaves it in place when a market closes early (799 of 2,097 closed over a day before it, 95% within 18 days after it). Not checked: how often it moves before the end.

## Unit of analysis and effective n

- Unit: a trigger row against control rows of the same cell.
- Clusters: world facts as defined above. All inference is a cluster bootstrap on facts. The number of facts with a trigger is written beside every nominal n.

## Population

- Closed markets whose scheduled `endDate` falls after 2026-09-15 and at least 30 days before the read, whose slug does not match the out-of-scope rule fixed in `code/col_10_universe.py` (sports, esports, crypto price, tweet counts, weather), and that are not in `derived/seen.json`.
- Out and counted: outcome prices not exactly 1 and 0, partial tapes, tapes missing.
- Survivorship: only closed markets. A voided market leaves. Limit stated.
- **Part 0**: markets due on or before the freeze date. **Part 1**: markets due after it. Part 1's last rows could not have been seen by anyone at the freeze. The part follows the scheduled date, never the closing date.

## Labels

- `win`: final outcome price of the token, exactly 1 or 0, read once at the end.
- Excess: `win` minus the price paid on that row. Zero in expectation at a calibrated price.

## Features and point-in-time rule

t0 is the row's timestamp. A feature uses only rows of strictly earlier seconds, apart from the set itself, which uses tape order within the second.

- Entrant: a wallet's first taker row in the market, a BUY, price from 0.01 to 0.35, at least $100.
- Set at window w: at least 3 entrants of this token in (t0 - w, t0], this row included. A wallet enters a market once, so this counts wallets.
- Roles at window w: trigger, a row that completes a set outside the 21,600-second cooldown of its token. Dropped, a set inside the cooldown. Control, a row with no set at its own time.
- Eligible: guard above, prior market volume at least $25,000, and at or after 2026-09-16. Rows that fail stay countable in sets, since they happened, and cannot be scored.
- Cell: price band (0.01-0.05, 0.05-0.10, 0.10-0.20, 0.20-0.35), crowd (entrants of this token in the 24 hours ending at t0 - w, cut at 3, 6, 11, 31), momentum (last trade before t0 minus last trade at or before t0 - 3600 s: unknown, down at -0.02 or below, flat, up, strong up at +0.05 or above), time to `endDate` (under 1, 7, 30 days, or more). `endDate` is taken as read at collection, and can have moved.

No feature uses `win`, a later row other than the guard, a list of names or a report of suspicion.

## Splits

There is no tuning, so there are no training splits. Every threshold is fixed here. Part 0 and Part 1 serve as a stability check. Holdout means the whole table is read once, for the tests below.

## Stopping rule, fixed now and blind to outcomes

Tapes are collected for Part 0 in batches, then for Part 1 as markets come due and their 30 days pass. The table is built once, when the count of facts with a trigger at 300 s, without the guard, from `ana_00_freeze.py --count`, which writes no table and prints no price, reaches **N_STOP = 200**, or on **2027-06-30**, whichever comes first. N_STOP comes from the power table in `controles/controles_positifs.md`, as the smallest size with power of at least 0.80 at a planted effect of +0.25, which gives a difference of about +0.14, and a false-pass rate within the plan's limit. At that size a difference of about +0.05 passes about one time in three: this study can miss a small average effect. Outcomes are read after the table is frozen. There is no interim look at any rate.

## Tests

- **H1, primary, one test, window 300 s, two-sided, alpha 0.05.** Mean excess of triggers minus mean excess of controls of the same cell from other world facts, weighted by triggers. Cluster bootstrap on facts, 9,999 draws, seed 20261103, percentile interval. A trigger with no control elsewhere is unmatched and counted.
- **Why 300 s.** Short windows hold few sets. Long windows are mostly local crowding. At 300 s the first study's count of sets was about 2.4 times what local intensity gave, with enough sets to test. Its H1 at 300 s was near zero, so this picks no positive result. It is a choice made after seeing that study, and that is stated.
- **H2, required for a positive reading.** Eligible rows inside any set at 300 s against the same count when each wallet moves by one offset per UTC day within 5 windows, 1,999 draws, one-sided. A shared channel or a fast reaction to news passes this too.
- **Negative control exposure, required for a positive reading.** Rows with exactly one other entrant in the window, in tokens that hold no set at any time, against rows alone in their window of such tokens, same cells, same bootstrap, at least 50 matched rows. The mechanism under test needs three wallets, so this exposure cannot carry it, and it shares busy days, momentum and token size. A row of a token holding a set cannot serve here: its outcome is the token's, so it would copy a true effect and veto it. **Limit:** a hot token often holds a set, so it leaves this pool with its confounder. This control can show confounding and cannot clear it.
- **Weeks as clusters, required for a positive reading.** The same test with whole UTC weeks as clusters and controls from other weeks.
- **Strict guard, required for a positive reading.** The same test without rows that have a later row of their token within 12 hours at 0.05 or more above. A set ahead of a slow public move looks exactly like a set ahead of private news, and matching cannot tell them apart, since it fires before the price moves. Widening the main guard would stop that, at the cost of dropping from every reading the entries made hours before a public event, which are the ones this question is about. So the main guard stays narrow, the bound keeps them, and a positive result that only exists close before a rise is reported as `POSITIVE_NOT_INTERPRETABLE`. A true informed set a few hours ahead of its news will land there too: a known cost, and this choice is open to Benjamin's review.
- **Wallets, required for a positive reading.** The difference stays positive after removing every set holding one of the 5 wallets most often in sets.
- **Raw excess, required for a bound.** Mean excess of triggers against the paid price, no control, cluster bootstrap on facts.
- **Influence.** The difference after removing the 5 facts adding most to it.
- **Secondary, never changing the verdict.** The same tests at 30, 90 and 900 s, Benjamini-Hochberg over the three. Part 0 and Part 1 separately.

Every run, sensitivity included, goes through the register.

## Controls

`code/ctl_10_synth.py`, report in `controles/`: through the same functions and the same verdict. 20 seeds per scenario, at 200, 400 and 800 facts, plus 4 scenarios at every window.

- Null: calibrated prices, no group.
- Groups without information: aligned wallets, calibrated outcomes. H2 passes, H1 must stay silent.
- Planted effects of +0.05, +0.10, +0.25, +0.40 on tokens holding a group, and a subset case where one group in four carries +0.40.
- Traps, none with information in the group: tokens that attract many entrants win more; one news day with crowding and a fast price move, on a token that wins; the same with bots aligned on news days; a slow news day, 12 hours of rising price; steady upward drift on tokens that win; tokens that rise out of the price band.
- The generator writes tapes, which pass through the same parser as real tapes: repeat wallets, wallets acting in many markets, a volume floor, a price run-up on winners, stale prints for early movers.

Limits of acceptance, fixed before the report was read: at most 5 `TIMING_ASSOCIATION` in 100 seeds on any null or trap scenario, at the size N_STOP, and at most 1 false `BOUNDED_NULL` in 20 where the true average difference is +0.10 or more, including the case where all tokens hold informed sets. Power and false passes are read against facts with a trigger, the count the stop rule uses, and a planted effect is translated to the difference it gives, since planted tokens are only part of those holding sets. If a limit is missed, the plan changes before the freeze, with the reason written here, and no real data is read until it holds.

## Verdict, fixed before any result

Primary window only.

- `TIMING_ASSOCIATION`: p under 0.05, positive difference, H2 p under 0.05, negative control readable and not positive (lower end not above 0 and difference under half of H1's), p under 0.05 and positive with weeks as clusters, p under 0.05 and positive under the strict guard, same sign in Part 0 and Part 1 when both hold data, positive after removing the 5 most influential facts, positive after removing the 5 wallets most often in sets, at least 100 facts with a trigger, at least 60 effective facts, and at least 80% of triggers matched. The only allowed reading: in this holdout, entries completing a set of three in 300 s beat the paid price more than matched entries, on average.
- `POSITIVE_NOT_INTERPRETABLE`: p under 0.05 and a positive difference, with any other condition failing. The failing conditions are listed.
- `BOUNDED_NULL`: no positive result, the difference not significantly negative, at least 100 facts with a trigger and 60 effective facts, and the upper ends for the difference, for weeks as clusters and for the raw excess all under +0.10. The only allowed reading: in this holdout, entries completing a set of three in 300 s do not beat matched entries from other facts by +0.10 on average, outside the guard. A subset of informed sets stays compatible, and so do sets just before a public move, which the guard removes.
- `INCONCLUSIVE`: anything else, including an interval that reaches +0.10, too few facts, too few matched, or a significantly negative difference, which would make the matching or the guard suspect.

None of these says who knew what, or anything about legality, or what a follower could capture.

## Limits stated now

Taker rows only. Closed markets only. The guard removes true sets just before a public move, in favour of the null. The negative control reads a token's later rows, for that control only, and can catch confounding but never clear it. Markets on one world fact worded differently stay separate facts, which the weeks test only partly answers. Part 0 is short, because of the 30-day margin. A true informed set a few hours before its news can only reach `POSITIVE_NOT_INTERPRETABLE`. The bootstrap loses about 1 to 3% of trigger weight in draws where a cell has no control elsewhere, a shift the audit put at no more than 0.006. Public information cannot be separated from private information with this data: a first reaction to news that is not yet visible in the price looks the same. The out-of-scope rule works on slugs and will misclassify some markets. `endDate` can move. The same wallets can appear in both parts and in the design set. All reviewers of this plan are instances of one model family.
