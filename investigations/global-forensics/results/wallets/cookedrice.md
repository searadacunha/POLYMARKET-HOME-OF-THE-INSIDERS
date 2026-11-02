# Account file: `0x4060509c8c70cece529be4a089d6d66ad865b4d0`

Group `ballon-dor-named`. Read 2026-11-02 23:24:18 UTC. Mode: full. An address is not a person. Ownership not established. This file is no finding of wrongdoing.

## Activity

- API history complete: True, 31 rows, types {"DEPOSIT": 1, "TRADE": 21, "TAKER_REBATE": 4, "MAKER_REBATE": 2, "REDEEM": 2, "WITHDRAWAL": 1}
- First activity 2026-10-14 19:58:36, last 2026-10-28 18:04:55
- First trade: 2026-10-14 20:01:01 Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher?
- Deposits and withdrawals listed None, not read here 0, unreadable 0

## Control

- control_latest: form DEPOSIT_WALLET_OR_OWNABLE, owners ['0x6ec290051ea167cf564a4282c153351ab3fd876f'], OWNERS_READ_ONCHAIN, read at block latest
- control_at_first_money: form DEPOSIT_WALLET_OR_OWNABLE, owners ['0x6ec290051ea167cf564a4282c153351ab3fd876f'], OWNERS_READ_ONCHAIN, read at block 95535061
- A relayer submitting a transaction is not its owner, and an owner key is not a person.

## Funding paths, branch by branch

Tokens are fungible: a path shows flows in sequence, never the same units.

- `0xd628c33301…` (21,873.74 pUSD, deposit_path) <- `0xf70da97812…` (21,873.74 USDC.e, bridge_payout) **stops: no further flow read**
- `0xf70da97812…` (21,873.74 USDC.e, bridge_payout) **stops: no further flow read**

## Exit paths

- `0x4cd00e3876…` (39,158.78 USDC.e, bridge_deposit) **stops: no further flow read**

## Markets and positions

| Market | Trades | First | Capital engaged | Cash result | Shares left, API |
|---|---:|---|---:|---:|---:|
| Ballon d'Or 2026: Kylian Mbappé or Lamine Yamal to finish higher? | 18 | 2026-10-14 20:01:01 | 16,996.75 | 15,005.16 | 0.00 |
| Ballon d'Or 2026: Rodri or Lionel Messi to finish higher? | 3 | 2026-10-15 21:26:38 | 4,895.19 | 2,255.37 | 0.00 |

## Accounting

- Cash by type: {"deposit": "21873.73561", "buy": "21891.936856", "taker_rebate": "18.8217", "maker_rebate": "5.6890", "redeem": "39152.473416", "withdrawal": "39158.78287", "sell": "0", "merge": "0", "reward": "0", "referral_reward": "0", "yield": "0", "split": "0"}
- Unknown types: {}
- Trading cash over the rows read: 17,285.05. Balance computed from the rows: 0.00.
- Held today: null
- Withdrawals minus deposits is not a profit. An unredeemed position counts for nothing in cash.

## Coverage

| Address | Chain | Status | Rows | Source |
|---|---|---|---:|---|
| `0x6ec290051ea167cf564a4282c153351ab3fd876f` | ethereum | COMPLETE | 0 | etherscan-v2 |
| `0x6ec290051ea167cf564a4282c153351ab3fd876f` | polygon | COMPLETE | 0 | etherscan-v2 |
| `0x6ec290051ea167cf564a4282c153351ab3fd876f` | arbitrum | COMPLETE | 0 | etherscan-v2 |
| `0x6ec290051ea167cf564a4282c153351ab3fd876f` | optimism | COMPLETE | 0 | blockscout |
| `0x6ec290051ea167cf564a4282c153351ab3fd876f` | base | NO_SPEND_NOTHING_HELD |  | node presence |
| `0x6ec290051ea167cf564a4282c153351ab3fd876f` | bsc | NO_SPEND_NOTHING_HELD |  | node presence |
| `0xd628c333015848b9c4e8c519f51a22642a555c58` | ethereum | COMPLETE | 0 | etherscan-v2 |
| `0xd628c333015848b9c4e8c519f51a22642a555c58` | polygon | COMPLETE | 2 | etherscan-v2 |
| `0xd628c333015848b9c4e8c519f51a22642a555c58` | arbitrum | COMPLETE | 0 | etherscan-v2 |
| `0xd628c333015848b9c4e8c519f51a22642a555c58` | optimism | COMPLETE | 0 | blockscout |
| `0xd628c333015848b9c4e8c519f51a22642a555c58` | base | NO_SPEND_NOTHING_HELD |  | node presence |
| `0xd628c333015848b9c4e8c519f51a22642a555c58` | bsc | NO_SPEND_NOTHING_HELD |  | node presence |

## Where reading stopped

- NO_FLOW_IN_WINDOW: 11
- NO_LATER_OUTFLOW: 6
- BRIDGE_HOP_NOT_PROVEN: 2
- Token rows outside the value list, not followed: 0 rows on 0 contracts

## Moves with their proof

| UTC | Chain | Role | Amount | From | To | Other side | Level / data | Transaction | Log |
|---|---|---|---:|---|---|---|---|---|---:|
| 2026-10-14 19:58:24 | polygon | bridge_payout | 21,873.735610 USDC.e | `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | `0xd628c333015848b9c4e8c519f51a22642a555c58` | Relay EVM solver | LISTED / archived | `0xd46b453237a6a3eb2e9df3dceb61519f6aab9b7d37a05d901117d722eead92c2` |  |
| 2026-10-14 19:58:36 | polygon | deposit_path | 21,873.735610 pUSD | `0xd628c333015848b9c4e8c519f51a22642a555c58` | `0x4060509c8c70cece529be4a089d6d66ad865b4d0` | PERSONAL_SIZED | REVERIFIED / fresh | `0x9e1a809440c983f23ae834f92a6214198cfd15b65b4001e5739add05ea733012` | 677 |
| 2026-10-28 18:04:55 | polygon | bridge_deposit | 39,158.782870 USDC.e | `0x4060509c8c70cece529be4a089d6d66ad865b4d0` | `0x4cd00e387622c35bddb9b4c962c136462338bc31` | Relay Depository | REVERIFIED / fresh | `0x32c1285b13708b90937e6af48e956c07148630916649d021f9047af08767f1ae` | 91 |

## Other explanations

- Money between two addresses says nothing of who holds them: a payment, a gift, a loan, a service or a resale give the same picture.
- A service or an exchange pays thousands of people. A shared one proves no link.
- An early, large or lucky bet can follow public signals, private analysis or chance.
- Access to private information is not something on-chain data can show.
