# Counts

Written by `engine/tools/counters.py` from `wallets/*/trace.json`, by the rules of `engine/gf/state.py`.

- **Accounting reconciled:** on a complete activity list, the money rows close within 1 USD against the balance read on chain. It says nothing about who paid or who was paid, so it can overlap with every state below.
- **Traced to public frontiers:** every deposit and withdrawal row has its path, the books close, and every branch ended on a complete history, at a named service or verified contract, or at a hub measured in the file. A branch stopped by a budget never counts.
- **Work left:** a read, a budget, a branch or a check is open.
- **Blocked by data:** nothing left to read here, and what is needed is not public. The motives are below.

The last four columns add up to the accounts listed once the same-wallet column is taken out. No state asks for a civil identity or a platform's internal records.

| Group | Listed | Same wallet as a named file | Accounting reconciled | Traced to public frontiers | Work left | Blocked by data | Not yet processed |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ballon d'Or | 12 | 0 | 12 | 0 | 12 | 0 | 0 |
| Documented accounts | 15 | 0 | 14 | 0 | 15 | 0 | 0 |
| ChangeNOW | 26 | 0 | 4 | 0 | 26 | 0 | 0 |
| Discovery | 345 | 12 | 32 | 0 | 59 | 0 | 274 |

## State by group

| Group | Polymarket history | Funding | Exits | Branches at a frontier, in files | With the wallet's own history | Blocked by |
|---|---|---|---|---|---:|---|
| Ballon d'Or | COMPLETE 12 | WORK_LEFT 8, REBUILT 4 | REBUILT 10, WORK_LEFT 2 | named 238, measured_hub 39 | 0 | none |
| Documented accounts | COMPLETE 15 | REBUILT 8, WORK_LEFT 7 | WORK_LEFT 8, REBUILT 7 | measured_hub 215, named 130 | 7 | BRIDGE_ID_ABSENT_ON_BOTH_CHAINS 3 |
| ChangeNOW | COMPLETE 22, INCOMPLETE 4 | WORK_LEFT 19, REBUILT 4, NONE_FOUND 3 | WORK_LEFT 20, NONE_OBSERVED 3, REBUILT 3 | named 268, measured_hub 93 | 2 | NO_FUNDER_OBSERVED 3 |
| Discovery | COMPLETE 30, INCOMPLETE 29 | WORK_LEFT 51, REBUILT 8 | WORK_LEFT 42, REBUILT 14, NONE_OBSERVED 3 | named 718, measured_hub 240 | 1 | none |

## Work left

Number of files holding each reason.

| Group | Reasons |
|---|---|
| Ballon d'Or | TRADING_WALLET_HISTORY_NOT_READ 12, WINDOW_SCAN_NEEDED 8, CONTRACT_NOT_IDENTIFIED 4, DEPTH_BUDGET 3, BRIDGE_FAR_SIDE_NOT_READ 1 |
| Documented accounts | CONTRACT_NOT_IDENTIFIED 9, TRADING_WALLET_HISTORY_NOT_READ 8, BRIDGE_FAR_SIDE_NOT_READ 7, AMBIGUOUS_PATH 4, DEPOSIT_ROW_NOT_TRACED 4, WINDOW_SCAN_NEEDED 2, NODE_BUDGET 1, ACCOUNTING_NOT_RECONCILED 1 |
| ChangeNOW | LIGHT_MODE 26, TRADING_WALLET_HISTORY_NOT_READ 24, NODE_BUDGET 20, ACCOUNTING_NOT_RECONCILED 18, CONTRACT_NOT_IDENTIFIED 17, WINDOW_SCAN_NEEDED 13, LIGHT_FLOW_CAP 10, ACTIVITY_LIST_INCOMPLETE 4, BRIDGE_FAR_SIDE_NOT_READ 3, DEPTH_BUDGET 3 |
| Discovery | LIGHT_MODE 59, TRADING_WALLET_HISTORY_NOT_READ 58, CONTRACT_NOT_IDENTIFIED 43, DEPOSIT_ROW_NOT_TRACED 39, AMBIGUOUS_PATH 34, LIGHT_FLOW_CAP 29, NODE_BUDGET 23, MONEY_ROWS_NOT_READ 19, ACTIVITY_LIST_INCOMPLETE 18, WITHDRAWAL_ROW_NOT_TRACED 18, ACCOUNTING_NOT_RECONCILED 9, BRIDGE_FAR_SIDE_NOT_READ 6, DEPTH_BUDGET 5, WINDOW_SCAN_NEEDED 2, HISTORY_INCOMPLETE 1, DUST_SUM_NOT_FOLLOWED 1 |

## Discovery queue

From `results/discovery/queue.json`, 124 of 345 wallets read for the pass and 221 not read. A priority is a reading order, no finding, and every wallet stays in the queue.

| Tier | Why | Listed | File written | Left |
|---:|---|---:|---:|---:|
| 1 | same owner key, shared private funder, direct move with a listed address, or money already seen in a traced file | 18 | 7 | 11 |
| 2 | shared private destination, or several markets | 5 | 1 | 4 |
| 3 | no hint in this pass, largest entry first | 322 | 56 | 266 |
