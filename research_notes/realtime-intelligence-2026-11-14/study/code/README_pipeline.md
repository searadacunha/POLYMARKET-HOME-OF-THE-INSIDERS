# Order of the pipeline

Collection and features read no outcome. The outcome meets a row in `ana_00_freeze.py` only.

| Step | Script | Reads | Writes |
|---|---|---|---|
| 1 | `col_05_catalogue.py` | Gamma event listings | `data/catalogue.jsonl` |
| 2 | `feat_10_universe.py` | the catalogue | `derived/universe_markets.jsonl`, `derived/sets.json`, and apart, `derived/labels.jsonl` |
| 3 | `col_20_fills.py all` | data API, one market at a time | `data/fills_all.sqlite` |
| 4 | `feat_20_entries.py` | the fills | `derived/entries.sqlite`, `derived/tier1_wallets.txt` |
| 5 | `col_30_activity.py`, `col_31_asof.py` | data API, one wallet at a time | `data/activity.sqlite` |
| 6 | `feat_30_wallet.py` (pass 1) | entries and histories | `derived/inflow_todo.jsonl` (decided from activity rows alone) |
| 6b | `col_41_inflows.py` | Polygon Transfer logs to the wallet, block headers | `data/inflows_chain.sqlite` |
| 6c | `feat_30_wallet.py` (pass 2) | entries, histories, chain inflows | `derived/wallet_features.sqlite`, `derived/funding_todo.jsonl` |
| 7 | `col_40_funding.py` | Polygon receipts and logs, public name tags | `data/funding.sqlite` |
| 8 | `feat_40_groups.py` | entries and funding | `derived/groups.sqlite` |
| 9 | `ctrl_10_positive_controls.py` | nothing real | `controles/positive_controls.md` |
| 10 | `ana_00_freeze.py` | every derived table, then the labels | `derived/analytic_table.jsonl` (frozen) |
| 11 | `run_50_analysis.sh` | the frozen table | results, verdicts, exports |

`col_10_bigtrades.py` reads the venue-wide feed, which stops at 1 October 2026; it is kept for description and enters no
test. `run_10_chain.sh`, `run_20_chain.sh` and `run_30_chain.sh` are the three chains of steps as they were really run on 14 November 2026,
retries included. Steps 3, 5, 6b and 7 are resumable: run them again after an interruption.
