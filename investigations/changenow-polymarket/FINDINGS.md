# Findings: changenow-polymarket

## F-001 | CONFIRMED | 158 bettors, total PnL of -$21,722 on $626,466 staked, 28 winners, 103 losers, 27 flat, median of -$6
- Sources: results/recompute_pm_pnl2.json ; sources/state/pm_pnl2.csv
- Method: scripts/recompute_pm_pnl2.py on the CSV of the full rerun of September 25
- Limits: 16 incomplete accounts, so bounds. Covers the f2020 hub only
- Links: none

## F-002 | SUPPORTED | The link from ChangeNOW to Polymarket is real but tiny: $46,533 of the $8,351,690 paid by f2020, largest position about $3,527, no visible insider pipeline
- Sources: sources/case_05_proxy_resolved.md
- Method: Sweep of the 3,408 payees, EOA and deposit wallet, residual audit
- Limits: No signal in this sample is no proof of absence elsewhere
- Links: none

## F-003 | UNRESOLVED | "Funded through ChangeNOW" is not established: 66% of bettors received their payment before their first trade, and the flow to the deposit was never traced transaction by transaction
- Sources: sources/case_05_proxy_resolved.md ; results/history_of_figures.md
- Method: Comparison of dates
- Limits: Timing compatibility only
- Links: none

## F-004 | REFUTED | The earlier figures of -$45,970 and $2.05M staked are false: they do not survive the full rerun
- Sources: results/history_of_figures.md ; results/recompute_pm_pnl2.json
- Method: pm_pnl2.py rerun against the public API on September 25
- Limits: A false value stayed in notes for a month: replay a figure before citing it
- Links: none

## F-005 | UNRESOLVED | Note only: on the Machado market, 8 YES buyers before the announcement would be funded by one disposable distributor, with cumulative stakes of $212,874
- Sources: results/history_of_figures.md
- Method: Hop-by-hop walk described in the note
- Limits: Scripts and data were lost with the scratchpad, figures cannot be replayed
- Links: none

## Contradictions

- `case_05` gives 66% of bettors paid before their first trade; the note gives 64% after deduplication into 153 accounts. The note's calculation no longer exists.

## Missing to conclude

- The flow from ChangeNOW to the Polymarket deposit, transaction by transaction.
