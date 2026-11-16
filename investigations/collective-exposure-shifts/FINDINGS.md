# Findings, collective exposure shifts

Levels: `CONFIRMED`, `SUPPORTED`, `HYPOTHESIS`, `REFUTED`, `UNRESOLVED` (METHODOLOGY.md).

## F-001 | CONFIRMED | The archived Iran contrast reproduces exactly from the archived tape, hash included
- Sources: `results/feb28_recheck.json` ; `scripts/reproduce_feb28.py`
- Method: the archived 42,000-row tape is re-read with the archive's own definition (earliest BUY of No strictly before earliest BUY of Yes, this market, this band) and its SHA-256 is compared with the one published in the 8 November audit.
- Limits: this reproduces the arithmetic of a cohort selected after its outcome. It is descriptive and carries no p-value, exactly as the archive says.
- Links: independent-forensic-audit-2026-11-08:REPORT.md, section A and B1.

## F-002 | CONFIRMED | The archived Iran tape is the newest 84 pages of a longer stream, and the published counts change on the complete tape
- Sources: `results/feb28_recheck.json`
- Method: the market is re-collected in full from data-api v2 (`condition=`, 1000 rows/page, cursor pagination, `has_more` honoured); the archived rows are matched against it row by row by (wallet, timestamp, outcome, side); the same classifier is then applied to the band, and to the full history.
- Limits: the complete tape is a snapshot of 16 November 2026. Fills near the resolution are settlement-driven and mix both outcomes. This corrects a descriptive figure; it does not create a test, and the cohort stays excluded from every rate in this study.
- Links: collective-exposure-methods-2026-11-16:CASE_CROSSCHECK.md (which flagged a possible truncation and could not measure it).

## F-003 | REFUTED | Collective exposure shifts do not beat the price at the alert
- Sources: `results/tests.json` ; `results/scored.jsonl`
- Method: 763 markets sampled by hash of the condition id only (1,579 in the replication, F-009); positions rebuilt from executed fills; S4 alert = at least three wallets each adding 500 USD of net exposure to one side inside an hour, 3,000 USD in total, no wallet above 60 % of it, price between 0.05 and 0.90; outcome joined last; excess tested against the alert price with an event-clustered bootstrap and 10,000 draws.
- Limits: 129 alerts in 97 events, 16 of them in TEST, so a small edge is not excluded. Price at the alert is the last executed fill, not a quote.
- Links: none.

## F-004 | REFUTED | Collective exposure is not better than naive buy consensus or a single wallet's shift
- Sources: `results/tests.json`
- Method: same alerts and windows, four declared comparators (matched placebo in the same price band, naive buy consensus, single-wallet shift, and the variant that keeps two-sided wallets), excess compared with the same event-clustered bootstrap; Bonferroni 0.05/10 and Benjamini–Hochberg applied over the declared family of 10 comparisons.
- Limits: the comparators are not matched on liquidity or on wallet age; the group that keeps two-sided wallets is nearly identical to the primary one, so that test has almost no power.
- Links: F-003.

## F-005 | REFUTED | The alert is not executable: the gross result is negative before any cost
- Sources: `results/tables.json` ; `results/tests.json`
- Method: result per share bought at the last executed price, over a declared slippage grid from 0 to 5 %; the historical order book is not archived, so no ask, depth or spread is invented.
- Limits: a real trader could in principle do better than the last executed price on a thin book, or worse; without book history neither direction can be quantified. Taker fees and gas are not included either, which makes the reported result optimistic.
- Links: F-008.

## F-006 | UNRESOLVED | Collective shifts by financially linked wallets were not measured at population scale
- Sources: `analysis_plan.md` ; `results/tests.json` (S5 arm absent)
- Method: declared untestable in the plan before the run. The only verified financial graph in this repository is the 38-account Iran network, which is part of the excluded cohort, so it cannot enter a rate.
- Limits: this is an absence of measurement, not a refutation. Recording funding links for every wallet of 763 markets would need an on-chain pass (Relay credits, direct Polygon transfers) that was out of scope here.
- Links: research_notes/x-history-2026-11-06/verification/REPORT.md.

## F-007 | CONFIRMED | No cross-deadline interval position drives the alerts in this sample
- Sources: `results/interval_reading.json`
- Method: for events holding two or more deadlines, each wallet's closing position is read per market, ordered by closing time and classified by the sign of its YES-equivalent exposure above 500 USD.
- Limits: only 60 events qualify with wallets large enough on two deadlines, so the absence is weakly powered. Positions built by splits or merges are invisible.
- Links: F-003.

## F-008 | CONFIRMED | Execution at the alert is not verifiable from archived data
- Sources: `results/tables.json` ; `analysis_plan.md`
- Method: the data-api serves executed fills, not the book. No snapshot of bids, asks or depth at the alert second exists in the repository for these markets.
- Limits: this is a data limitation of the repository, not of Polymarket. A prospective recorder (the repository's own live collector) could remove it.
- Links: F-005, monitoring/livecollect.

## F-009 | REFUTED | On the pre-declared replication, the alerted side wins less often than its own price implies
- Sources: `results/replication_tests.json` ; `results/replication_tables.json` ; `results/replication_scored.jsonl`
- Method: same rule, code, thresholds, splits, seed and decision rule as the primary run, on the same population with the hash threshold moved from 25 to 50 per thousand (1,579 markets, 266 alerts in 197 events, 48 in TEST, which meets the declared 30-alert threshold). Excess over the alert price, event-clustered bootstrap, Bonferroni and Benjamini-Hochberg over the declared family.
- Limits: one population, one rule. The period split moves the sign (positive in TRAIN, negative in VALID and TEST), which is reported rather than smoothed. Thresholds were never fitted, so no period is a training period in the model-fitting sense, only a chronological block.
- Links: F-003, F-004, F-005.

## Contradictions

- The archived figure of 20 of 36 accounts and 16 of 733 comparators is reproducible but computed on a censored tape. On the complete tape the same rule gives 35 of 36 and 27 of 733 (F-002). Any text that quotes the archived figures as if they were the whole market history overstates the rarity of the comparator pattern and understates how uniform the cohort was.
- The 16 November method note assumed the 42,000-row band "may omit some prior trade history". It does: 59,163 fills in the same window, and 175,997 in the market. The note's own statement that the full tape had not been reproduced is now resolved.

## Missing to conclude

- A TEST split large enough for the declared 30-alert threshold. The pre-declared replication (amendment 002) targets the same population with `hash mod 1000 < 50`; it is the only open item.
- An independent funding graph for the sampled wallets, to move F-006 from UNRESOLVED to measurable.
- A book recorder, to turn F-008 into an execution estimate rather than a gross one.

## Prospective monitoring

The rule is cheap to run live: it reads only fills, needs one hour of history per market and fires about once per six
markets. Recorded prospectively with the book, it would settle the two open items (financing links, executable price)
without any ex-post reconstruction.
