# Analysis plan, written before the table is frozen and before any rate is computed

Question: when several distinct wallets enter the same low-priced outcome within a tight window, does that outcome win more often than its price implied, compared with other entries at the same prices, and are such bursts more frequent than wallet timing alone explains?

The plan tries to destroy that hypothesis, not to confirm it. It is fixed here, before the analytic table exists; any later change is an amendment (amendements/NNN-*.md) and is listed at the end of results.md as a deviation.

Nothing here can show insider trading. A burst is a timing pattern. A public news shock, a shared signal channel or a bot produce the same picture. No wallet is named as suspect by this study.

Earlier result to respect: `maduro-iran` phase 8 tested S_CONV (at least 2 other large buyers of the token within 30 minutes, size at or above the 90th percentile) and found it follows momentum. This study differs on four fixed points: six tight windows, entrants only (first trade of the wallet in that market), low prices only, and comparisons at the same price and the same crowd, with a null that destroys only the alignment between wallets. S_CONV's negative result stands whatever happens here.

## Data

- Source: the archive of phase 8, `~/Documents/Crypto/enquete_maduro_iran/donnees/brut_p8_p9/p8/`: `universe.json` (2,097 markets, Gamma) and `trades/{conditionId}.json` (taker rows of data-api `/trades`, at least $100, read on 2026-09-30). No new collection. The route has since been retired (HTTP 410), so the archive cannot be re-read from the source: its files are hashed in `derived/input_hashes.json`.
- Accounting, written by `code/ana_00_freeze.py` into `derived/freeze_counts.json`: markets read, files flagged `maybe_truncated`, files whose row count is an exact multiple of the 500-row page, the gap between a file's oldest row and the market's start, rows read, first rows rejected by each reason, tokens, entrants. An unreadable file stops this run. The archive's own collector could stop on an HTTP error mid-pagination and keep what it had, and such a file stays unflagged below 3,000 rows: this cannot be excluded for every file, and the page-multiple rule only catches part of it. Rows run from newest to oldest, so a cut loses the oldest, and in such a file an entrant is not a true first row.
- Traps checked: rows are taker rows only, so a maker's fill never enters and a resting order is not read as a decision taken at its fill time. The size filter of $100 hides smaller entries, so entrant status means "first row at or above $100 in this market". Sizes and prices are read as floats, for selection and for the difference, never for money reporting. Rows after `closedTime` are excluded.

## Unit of analysis and effective n

- Unit of H1: a burst event (market, token, window, trigger time), compared with entrant buys outside any burst of that window.
- Clusters: the Gamma event of each market, read once by `code/col_20_events.py` and written to `derived/events.json`, because the archive never kept it. Sibling outcomes of one event are not independent. A market with no event found falls back to its own slug, and these are counted. All inference is a cluster bootstrap on events.
- Effective n: number of events, written beside every nominal n.

## Population

- Conditioning: phase 8's universe, closed markets of at least $250,000 volume, end date from 2025-10-01 to 2026-09-15, sports, crypto price, tweet counts and weather excluded. It was defined without any suspicion criterion and holds winners and losers of both sides. Catalogue markets enter only if the universe already holds them.
- Excluded and counted: markets whose outcome prices are not exactly 1 and 0 (unresolved or disputed), tokens with no eligible row. Files flagged `maybe_truncated` or whose row count is a multiple of the page size stay out of H1 and H2, and a sensitivity run brings them back: an entrant in those files is only the first row among the rows kept.
- Survivorship: only closed markets exist in the archive. Limit stated.

## Labels

- `win`: 1 if the token's final price in `outcomePrices` is 1, 0 if it is 0, read from the archive. Never used to define a burst.
- Reference price: for a burst, the volume-weighted price paid by its wallets up to and including the trigger row. For an entrant, the price it paid. Both are prices actually paid.
- Excess: `win - price`. Zero in expectation for a calibrated market at that price.

## Features and point-in-time rule

t0 is the row's timestamp. Each row is read in time order, and a feature only uses rows with a strictly earlier order in the same market, or the universe-wide first-seen time of a wallet.

- `entrant`: a BUY row of a token, price from 0.01 to 0.35, at least $100, whose wallet has no earlier row of any side in that market.
- `burst(w)`, for w in 5, 30, 90, 300, 900, 3600 seconds: an entrant row at time T such that at least 3 distinct entrant wallets bought this token in (T - w, T]. After a trigger, the same token and window cannot trigger again for 21,600 seconds. The event is dated at its trigger.
- `fresh`: the wallet's first row anywhere in the universe is at most 7 days before its entrant row. A proxy for age: the universe is partial.
- `shock`: the last traded price of the token moved at least 0.05 in the 900 seconds before the first row of the burst, read from rows of that token only. Unknown, and left as null, when no row exists before that span. A rough marker of a move already visible.
- Similarity of sizes: coefficient of variation of the wallets' dollar amounts.

No feature uses a later row, the label, a list of names, or any report of suspicion.

## Splits

By end date, as in phase 8: TRAIN before 2026-03-01, VALID 2026-03-01 to 2026-05-31, TEST 2026-06-01 to 2026-09-15. No threshold is tuned on any of them: every threshold is fixed above. They serve as a stability check: a window can pass only if the sign holds in VALID and in TEST. The same wallet can appear in several splits, stated as a limit.

## Tests

- H1, primary, one per window, 6 tests, two-sided: difference between the mean excess of burst events and the mean excess of non-burst entrant buys in the same cell, weighted by bursts. A cell is a price band (0.01-0.10, 0.10-0.20, 0.20-0.35), crossed with a crowd bucket, the number of entrants of that token in the 24 hours up to the row, from earlier rows only, cut at 2, 5, 10 and 30, crossed with a total bucket, the number of entrants of that token over its whole life, cut at 5, 15, 50 and 150. The total looks ahead: it serves matching only, and this test is therefore an association, not a detector. A burst with no comparable entrant is left out, and the share kept is reported. So bursts are compared with entries at the same price, on an equally crowded day, on an equally crowded token: if bursts only mark those, the difference vanishes. Cluster bootstrap on events, 4,000 draws, seed 20261102. Correction: Bonferroni on the 6 windows, threshold 0.05/6 = 0.00833, fixed in the verdict. The full number of comparisons from the register, strata and placebo included, is written beside it, with what the result would be at that stricter threshold.
- H2, required for a pass, one per window: are bursts more frequent than the local intensity allows? Each entrant row moves by its own uniform offset within plus or minus 10 times the window, so a crowded hour or a news shock stays, and only alignment finer than that goes. An entrant is one wallet's first row in a market, so for bursts inside a market this moves that wallet as a block. Number of triggers, 499 draws, seed 20261102. p = (1 + draws at or above observed) / 500. A window where alignment is no more than the local crowd has no burst to speak of, whatever H1 says. A pass here says wallets align more than the crowd alone explains. A shared channel or a very fast reaction to public news produces that too: H2 says nothing of private information.
- Strata reported, never used to choose: no shock before the burst, shock not shown, at least half fresh entrants, each split, each price band, partial files brought back.
- Sizes similarity and shock share: read from the table, descriptive, not tested.
- Catalogue, exploratory: for each publicly reported market already in the universe (`catalog_markets.json`, fixed here), the token's largest number of entrants inside each window during the 8 days before the public event time, against the same measure on every other token of the universe, 8 days before close, in the same volume decile. A percentile rank, Benjamini-Hochberg over all ranks. This is selected on suspicion and on outcome, so it can only say "ordinary or not", never "insider".

Every run, including placebo and sensitivity, goes through the register.

## Negative and positive controls

- Placebo, H1P: the same H1 where each burst takes the outcome of a random entrant of the same cell and split, 4,000 draws. No information can remain, so a positive pass means the pipeline manufactures signal.
- Positive controls on synthetic tables, in `controles/`, at windows of 5, 30, 300 and 3600 seconds: groups planted with no information, burst outcomes at price plus 0.10 (medium), price plus 0.25 (strong), three seeds each, through the same functions and the same verdict. The nulls must stay silent. Power written there.
- Negative control of timing: synthetic independent wallets dense enough to burst by chance must not pass H2, and synthetic coordinated wallets must be caught by H2.
- Four synthetic traps. Two with no alignment: tokens that attract many entrants also win more, and entrants pile onto one news day of a token that wins. Two combined, adding groups that align and carry no information, as bots do on real news days: there H2 passes for a true reason, so only the matching can stop a false pass. The verdict must fail all four.

## Verdict, fixed before any result

For each window:
- `NOT_SUPPORTED`: the corrected test does not pass, or the difference is negative, or the sign differs between VALID and TEST.
- `PREDICTIVE_TIMING_PATTERN`: bootstrap p below the threshold, positive difference, same sign in VALID and TEST, H2 p below the threshold, and H1P does not pass with a positive difference.

Global: `NOT_SUPPORTED` if no window passes. Otherwise the passing windows are listed. A passing window says that a timing pattern carried information beyond the price paid. It says nothing about who knew what, nothing about legality, and it says nothing about what a follower could capture: execution is not measured.

## Limits stated now

Taker rows above $100 only. Closed markets only. Rows moved in H2 are moved independently across markets, because the table holds no wallet: wallets entering several markets together make those p-values too small, by reasoning, not measured. Splits follow `endDate`, as in phase 8: 227 of 2,097 markets would change split on `closedTime`, and 32 TEST markets closed in TRAIN, so the VALID and TEST sign check is not fully chronological. Entrants are defined by rows, not by the wallet's full history. Resolutions can be disputed: excluded when prices are not exactly 1 and 0. Effective n is events, and large news days weigh on a few events. Public information cannot be separated from private information with this data. The auditor is an instance of the same model family.

## Note written before the freeze

The table was first built before this plan's final text, and built again after the review below. Its builds printed only counts (rows, entrants, bursts per window, exclusions). No rate, no win share and no shift was computed or read by the author.

Synthetic controls changed this plan before any real rate existed. A shift of plus or minus 24 hours flagged independent wallets merely active in the same hour. A shift of 7 to 14 days removed every burst, crowded tokens included. A jitter of 10 windows as a null for H1 kept informed groups together, so the null reproduced a true effect and the test had no power. A uniform time across a token's whole life, tried next, flattened activity so far that a handful of tokens carried the null.

A resampling null for H1, in any of those forms, stayed either powerless or blind to one trap, because it rests on the few chance bursts of each draw. On 400 synthetic markets a strong planted effect passed once in 8 window and seed pairs, and the news-day trap passed once. H1 therefore moved to a direct comparison at the same price, the same crowd of the previous 24 hours and the same token size, and H2 became required. Matching on the crowd alone left a positive difference in the traps, with only H2 stopping them, so the total bucket and the combined traps were added. This changed the test before any real rate was computed.

A pre-freeze review by a separate agent (`silent-failure-hunter`) found the cluster key was silently the market and not the event (2,097 markets, 648 events), truncated files sat in the primary test, the volume field was always zero, and controls covered one window of six. All were fixed here. It worked on the table with `win` removed, read no outcome, and gave the author analytic expected null-trigger counts per window, from entrant counts and durations. Those counts hold no outcome information.
