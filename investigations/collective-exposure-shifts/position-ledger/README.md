# Position ledger (mission 3 of 7, collective-exposure-shifts)

Point-in-time reconstruction of each wallet's economic exposure, per market, outcome and instant, from the archived
fill tapes. Built 2026-11-17. It adds a folder; it changes nothing in the frozen study one level up, in the tapes or
in the repository README. No outcome field is read or stored here: `data/gamma_meta.jsonl` and the Iran event
cache were stripped of Gamma's outcome prices and resolution status.

| File | What it is |
|---|---|
| `POSITION_SCHEMA.md` | event, snapshot, bounds, families, classes A/B/C/D, partitions, output files |
| `DATA_GAPS.md` | what the data cannot show, what that does to each reading, measured where possible |
| `EXAMPLE_PORTFOLIO.md` | two worked, checkable examples with transactions and timestamps |
| `REVIEW_LOG.md` | the two reviews: each defect, its fix and its test; rejected findings |
| `PARTITIONS.json` | TRAIN / VALID / TEST, defined before any signal work; Iran cohort exploratory only (never in TRAIN, VALID or TEST) |
| `scripts/ledger.py` | the engine |
| `scripts/run_ledger.py` | resumable run over the tapes, one event at a time, with checkpoints |
| `scripts/summarize.py` | per-partition summary of a run, writes `PARTITIONS.json` |
| `scripts/verify_with_activity.py` | re-reads episodes with each wallet's public activity feed (splits, merges) |
| `scripts/example_portfolio.py`, `scripts/example_ladder_iran.py` | the two examples |
| `scripts/fetch_meta.py` | Gamma metadata (rules text, contract version, fee and neg-risk flags) |
| `tests/test_ledger.py` | synthetic cases and edge cases (`python3 -I tests/test_ledger.py`) |
| `data/` | Gamma metadata, Iran cohort list, cached activity feeds (all with fetch times) |
| `out/full/` | the run: ledger files, `units.jsonl`, `episodes.jsonl`, `checkpoint.jsonl`, `SUMMARY.json` |
| `out/*_superseded/` | earlier runs, before the review fixes; kept, not used |

Reproduce (from this folder, tapes in `../../../`):

```
python3 -I tests/test_ledger.py
python3 -I scripts/run_ledger.py --tapes ../../../tapes.sqlite --tapes ../../../tapes2.sqlite \
  --markets ../../../sample_markets.jsonl --markets ../../../sample_expanded.jsonl \
  --meta data/gamma_meta.jsonl --iran-cohort data/iran_cohort_wallets.json --out out/full
python3 -I scripts/summarize.py --run out/full --frozen-splits ../../../splits.json \
  --frozen-splits ../../../splits_expanded.json --out-summary out/full/SUMMARY.json --out-partitions PARTITIONS.json
```

The engine and the deliverables were reviewed adversarially before the final run; every finding was reproduced by
an executed counterexample. Defects, fixes, tests and rejected findings are listed in `REVIEW_LOG.md` (three runner
fixes have no unit test, which the log says).
