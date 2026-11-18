# Which code produced which data

Written on 14 November 2026, before the freeze, after the protocol audit found that several scripts had been changed
after some of their outputs were written (audit/protocole_avant_gel_20261114.txt, B1). The study folder is not a git
repository, so the changes are stated here with the check that shows whether an output is still what the frozen code
would produce. Times are UTC, from the file times and logs/chain.log. No outcome had been read at any of these steps.

| Output | Produced by | Code changed since? | Check |
|---|---|---|---|
| `data/catalogue.jsonl` | `col_05_catalogue.py`, 09:45 | no | |
| `derived/universe_markets.jsonl`, `derived/labels.jsonl`, `derived/sets.json` | `feat_10_universe.py`, rerun 15:14:20 | no (changed 15:14:09: documented cases are only those listed, the event end is taken over its markets whatever their resolution) | universe and labels identical to the 09:46 run (sha256 e26e7225…, 02be902a…); one event moved, `nobel-peace-prize-winner-2026-139`, DISCOVERY to VALIDATION; the earlier split is kept in `derived/sets.before_audit_fixes.json` |
| `data/fills_all.sqlite` | `col_20_fills.py`: 32,536 markets by the version before 12:24:59, the 16 others at 12:25 by the current one | the 12:24:59 change keeps and counts rows served a little under 1,000 USD, which the earlier version rejected by failing the market | the 32,536 markets read before succeeded, so they held no such row: the current code returns the same rows for them |
| `derived/entries.sqlite` | `feat_20_entries.py`, rerun 15:15:47 | no (changed 14:18:55: fills of one second ordered by rowid; 15:14:44: the day after a scheduled end only for ends at 00:00 UTC, atomic write) | the rowid order alone reproduced the 13:07 table byte for byte (sha256 of all rows, 675,747 entries); the 15:15 table has the same ids and the same features (sha256 f6394e17… of the key columns, both versions), only `eligible` and `tier1` differ (210,021 and 77,191 instead of 213,689 and 78,432) |
| `data/activity.sqlite` | `col_30_activity.py` (code of 09:56) and `col_31_asof.py` (code of 12:30), last runs 12:27 and 12:41 | no | |
| `derived/inflow_todo.jsonl` | `feat_30_wallet.py` pass 1, 15:19:45 | see below | 18,780 windows; every window already stored covers the one needed now, for the same wallet and time (0 mismatch) |
| `data/inflows_chain.sqlite`, table `items` | `col_41_inflows.py`, log reading started 14:17:33 on the list of that time (19,104 windows, of which the 18,780 of the current list) | yes, 14:48 and 15:15: the block range is capped at the head of the chain, a missing end header raises, an item is done only when its stored window covers the needed one, and the phases for pUSD mints and senders were added | the log-reading part (`transfers_in`, the time filter) is unchanged; every entry ends before 1 November 2026, far below the head, so the cap never applies; the window check is enforced again in `feat_30` (a read that does not cover its window is `missing`). At 16:22 UTC the first process was stopped with 13,000 windows stored (the endpoint had slowed to 6 to 11 s a call) and the current version resumed the 6,009 left, with three calls in flight under one shared pace of one call a second; the reading of each window is the same |
| `data/inflows_chain.sqlite`, table `mints`; senders in `data/funding.sqlite` | `col_41_inflows.py`, chain 4 | no | |
| `derived/wallet_features.sqlite`, `derived/funding_todo.jsonl` | `feat_30_wallet.py` pass 2, chain 4 | no | |
| `data/funding.sqlite` | `col_40_funding.py`: receipts and inflows up to 13:33 by earlier versions, chain 4 by the current one | yes: block time kept in the log rows, a null receipt believed only when every endpoint says null (0 `no_receipt` were stored before), every payment of a pass-through key read | receipts are stored as read (sha256 per receipt); `feat_40` uses only the deposits of the current `funding_todo.jsonl` |
| `derived/groups.sqlite` | `feat_40_groups.py`, chain 4 | no | |
| `controles/positive_controls.*` | `ctrl_10_positive_controls.py`, run 4 | no | earlier runs kept in `controles/run1_before_class_rewrite/`, `run2_before_audit_fixes/`, `run3_before_second_audit/` |

The chains of steps are `run_10_chain.sh`, `run_20_chain.sh`, `run_30_chain.sh` (stopped while waiting, no step run) and
`run_40_chain.sh`; the steps run by hand are listed at the top of `run_40_chain.sh`.
