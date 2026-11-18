# Data inventory for an executable-edge test (16 November 2026)

Scope: public GitHub main tree, **not** the owner's unpublished Mac. A recursive API tree at the audit snapshot showed **8,912 file blobs** and was not truncated. Listing them does not mean each blob was separately read or validated.

| Data family | Published evidence | Critical gap for executable PnL |
| --- | --- | --- |
| Frozen alert labels | [analytic_table.jsonl](../research_notes/early-detection-2026-11-13/study/derived/analytic_table.jsonl): 587 rows (570 validation, 17 discovery); [test results](../research_notes/early-detection-2026-11-13/study/derived/results_tests.json) | Alert's last-trade price is not the contemporaneous ask; the price grid covers limited windows |
| Wallet trades/positions | Case-specific source files and some PnL reconstructions in investigations | Full point-in-time trading histories, split/merge/conversion accounting, controls |
| ChangeNOW funding/redeeming | investigations/changenow-proof, changenow-outflows, changenow-polymarket | A shared service address is not common control; the exact path to a deposit often remains missing |
| Financial network graphs | Transfer and funding files in investigations and research_notes | Exclude shared relays/exchanges and direct-ownership overclaims |
| Price vs announcements | PATTERN_RESEARCH.md, BACKTEST_RESULTS.md, case timelines | Official first-public-news timestamps are only documented for selected cases |
| Historical PnL | investigations/changenow-polymarket/sources/state/pm_pnl2.csv | 16 incomplete accounts in the 158-account study; no guaranteed future skill |
| Tick-level books and fills | integrations/quantitative_engine and research_notes/forensic-engine-2026-11-13 | Some Parquet files referenced by those analyses are **not archived in Git**; insufficient diverse book/queue coverage |
| Live observations | monitoring/phi_monitor and LIVE_DETECTION.md | No verified multi-day executed paper returns; live channels differ in completeness and latency |
| Missing local archives | INVENTORY.md, BACKUP_STATUS.md and local-only manifests | Not retrievable by examining GitHub; do not imply that Mac-only files were audited |

The published frozen study began with 34,413 eligible markets and yielded 570 trade-confirmed unselected price ignitions. The original LONELY_THIN class had **45 validation alerts in 44 events**; see [PATTERN_RESEARCH.md](../PATTERN_RESEARCH.md). These numbers describe the published study, not independent market re-collection.

**Minimum additional dataset, conditional on a frozen hypothesis:** one narrowly scoped set of contemporaneous bid/ask depth on *both* tokens, actual trade prints, event and receipt timestamps, historical fees/rebates, resolution evidence and enough later observations to measure fill probability and adverse selection. Collect only the columns and dates essential to that test. Avoid large downloads on a machine with limited disk space.

All original evidence and the repository README remain unchanged.
