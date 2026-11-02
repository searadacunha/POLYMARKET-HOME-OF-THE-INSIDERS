# Account file: `0x56efadc9defe5b7a21af751e0d026f2cf54136db`

Group `maduro-iran-network`. Read 2026-11-02 23:16:50 UTC. Mode: full. An address is not a person. Ownership not established. This file is no finding of wrongdoing.

## Activity

- API history complete: True, 4 rows, types {"DEPOSIT": 1, "TRADE": 1, "REDEEM": 1, "WITHDRAWAL": 1}
- First activity 2026-02-26 22:52:30, last 2026-02-28 10:18:21
- First trade: 2026-02-26 22:53:50 US strikes Iran by February 28, 2026?
- Deposits and withdrawals listed None, not read here 0, unreadable 0

## Control

- control_latest: form CLONE_OR_OTHER, owners [], SIGNER_UNKNOWN, read at block latest
- control_at_first_money: form CLONE_OR_OTHER, owners [], SIGNER_UNKNOWN, read at block 83513161
- A relayer submitting a transaction is not its owner, and an owner key is not a person.

## Funding paths, branch by branch

Tokens are fungible: a path shows flows in sequence, never the same units.

- `0xf70da97812…` (9,883.75 USDC.e, bridge_payout) **stops: no further flow read**

## Exit paths

- `0xb685760ebd…` (98,679.34 USDT, transfer) **stops: SERVICE_OR_SHARED:CONTRACT**
- `0xa347472cec…` (0.02 ETH, transfer) **stops: NO_LATER_OUTFLOW**
- `0x4cd00e3876…` (98,837.50 USDC.e, bridge_deposit) **stops: no further flow read**

## Markets and positions

| Market | Trades | First | Capital engaged | Cash result | Shares left, API |
|---|---:|---|---:|---:|---:|
| US strikes Iran by February 28, 2026? | 1 | 2026-02-26 22:53:50 | 9,883.75 | 88,953.75 | 0.00 |

## Accounting

- Cash by type: {"deposit": "9883.752425", "buy": "9883.75", "redeem": "98837.5", "withdrawal": "98837.502425", "sell": "0", "merge": "0", "reward": "0", "maker_rebate": "0", "taker_rebate": "0", "referral_reward": "0", "yield": "0", "split": "0"}
- Unknown types: {}
- Trading cash over the rows read: 88,953.75. Balance computed from the rows: 0.00.
- Held today: null
- Withdrawals minus deposits is not a profit. An unredeemed position counts for nothing in cash.

## Coverage

| Address | Chain | Status | Rows | Source |
|---|---|---|---:|---|
| `0x4e062726688d02cffff7c39918bfb3d4470614eb` | ethereum | COMPLETE | 10 | etherscan-v2 |
| `0xa347472cec447d17e80ea4a16784c1490f4c2185` | ethereum | COMPLETE | 62 | etherscan-v2 |
| `0xa347472cec447d17e80ea4a16784c1490f4c2185` | polygon | COMPLETE | 17 | etherscan-v2 |
| `0xa347472cec447d17e80ea4a16784c1490f4c2185` | arbitrum | COMPLETE | 0 | etherscan-v2 |
| `0xa347472cec447d17e80ea4a16784c1490f4c2185` | optimism | COMPLETE | 3 | blockscout |
| `0xa347472cec447d17e80ea4a16784c1490f4c2185` | base | NO_SPEND_NOTHING_HELD |  | node presence |
| `0xa347472cec447d17e80ea4a16784c1490f4c2185` | bsc | NO_SPEND_NOTHING_HELD |  | node presence |

## Where reading stopped

- NO_LATER_OUTFLOW: 6
- BRIDGE_HOP_NOT_PROVEN: 1
- SERVICE_OR_SHARED:CONTRACT: 1
- Token rows outside the value list, not followed: 34 rows on 22 contracts

## Moves with their proof

| UTC | Chain | Role | Amount | From | To | Other side | Level / data | Transaction | Log |
|---|---|---|---:|---|---|---|---|---|---:|
| 2026-02-26 22:52:30 | polygon | bridge_payout | 9,883.752425 USDC.e | `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | `0x56efadc9defe5b7a21af751e0d026f2cf54136db` | Relay EVM solver | REVERIFIED / fresh | `0xaf44ea53f3c24c292435f88ba2df12c8b60344e75ac87286da6668ad6d84407b` | 666 |
| 2026-02-28 10:18:21 | polygon | bridge_deposit | 98,837.502425 USDC.e | `0x56efadc9defe5b7a21af751e0d026f2cf54136db` | `0x4cd00e387622c35bddb9b4c962c136462338bc31` | Relay Depository | REVERIFIED / fresh | `0x6182e18523991bed04b1112b8c28316bb7024bbae104862cfcc2e3bad2dd282a` | 3462 |
| 2026-02-28 10:21:59 | ethereum | transfer | 98,679.335887 USDT | `0x4e062726688d02cffff7c39918bfb3d4470614eb` | `0xb685760ebd368a891f27ae547391f4e2a289895b` | CONTRACT | LISTED / fresh | `0xf6f4ae986acd03e0f6a41dc0d4e064d228fc5c04f88241d9d2f2ce985d9a2172` |  |
| 2026-10-14 20:53:47 | ethereum | transfer | 0.016753 ETH | `0x4e062726688d02cffff7c39918bfb3d4470614eb` | `0xa347472cec447d17e80ea4a16784c1490f4c2185` | PERSONAL_SIZED | LISTED / fresh | `0x798500f434aacd93c09890f836db5b93e5fb50c21545060fac33db71792c8c6a` |  |

## Other explanations

- Money between two addresses says nothing of who holds them: a payment, a gift, a loan, a service or a resale give the same picture.
- A service or an exchange pays thousands of people. A shared one proves no link.
- An early, large or lucky bet can follow public signals, private analysis or chance.
- Access to private information is not something on-chain data can show.
