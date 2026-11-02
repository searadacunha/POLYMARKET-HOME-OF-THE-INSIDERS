# History of the figures

Written on November 2, 2026 from an internal agent note, which stays unpublished. Figures from the note alone cannot be replayed: their scripts sat in a session scratchpad that no longer exists.

## Corrected totals

| | Earlier note (false) | Full rerun of September 25, 2026 |
|---|---|---|
| Total PnL | -$45,970 for the losers, about -$45,000 overall | -$21,722 |
| Staked | $2.05M | $626,466 |
| Winners, losers, flat | 26 winners | 28, 103, 27 |

`pm_pnl2.py` was rerun end to end against the public API on September 25, and the result stayed within 3% of the stored CSV. The false values survived for almost a month because they were written in a note and nobody replayed them. `recompute_pm_pnl2.json` recomputes the current figures from the CSV.

## Claims in the note that can no longer be checked

- 153 unique trading accounts after deduplication, and 64% with a ChangeNOW payment before the first trade. `case_05` gives 66% on 158 accounts.
- The flow from ChangeNOW to a Polymarket deposit was never traced transaction by transaction.
- Machado market: a disposable distributor funds at least 8 YES buyers before the announcement, with cumulative stakes of $212,874 and cumulative redemptions of $350,495. The note traces its funds back through Relay to a treasury active since 2021. It says nothing about who controls these wallets.
