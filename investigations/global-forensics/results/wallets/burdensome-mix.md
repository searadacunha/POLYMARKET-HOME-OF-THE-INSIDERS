# Account file: `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9`

Group `federal-case`. Read 2026-11-02 22:57:06 UTC. Mode: full. An address is not a person. Ownership not established. This file is no finding of wrongdoing.

## Activity

- API history complete: True, 31 rows, types {"DEPOSIT": 10, "TRADE": 15, "REDEEM": 2, "WITHDRAWAL": 4}
- First activity 2025-12-26 21:13:09, last 2026-01-14 22:49:34
- First trade: 2025-12-27 05:05:41 US forces in Venezuela by January 31, 2026?
- Deposits and withdrawals listed None, not read here 0, unreadable 0

## Control

- control_latest: form CLONE_OR_OTHER, owners [], SIGNER_UNKNOWN, read at block latest
- control_at_first_money: form CLONE_OR_OTHER, owners [], SIGNER_UNKNOWN, read at block 80832173
- A relayer submitting a transaction is not its owner, and an owner key is not a person.

## Funding paths, branch by branch

Tokens are fungible: a path shows flows in sequence, never the same units.

- `0xf70da97812…` (31,599.81 USDC.e, bridge_payout) **stops: no further flow read**
- `0x7f4f8ab780…` (1,238.07 USDC.e, deposit_path) **stops: SERVICE_OR_SHARED:CONTRACT**
- `0xa67d7eb4dc…` (914.48 USDC.e, bridge_payout) **stops: no further flow read**
- `0x56c262027e…` (96.28 USDC.e, bridge_payout) **stops: no further flow read**
- `0xc4d5f64b74…` (1.00 USDC.e, deposit_path) **stops: SERVICE_OR_SHARED:CONTRACT**
- `0xb12a3f0fed…` (0.77 USDC.e, deposit_path) **stops: SERVICE_OR_SHARED:CONTRACT**
- `0x2501e39763…` (0.44 USDC.e, deposit_path) **stops: SERVICE_OR_SHARED:CONTRACT**
- `0x815770b0f7…` (0.21 USDC.e, deposit_path) **stops: SERVICE_OR_SHARED:CONTRACT**
- `0x82aed30e16…` (0.10 USDC.e, deposit_path) **stops: SERVICE_OR_SHARED:CONTRACT**

## Exit paths

- `0xf70da97812…` (437,858.69 USDC.e, bridge_deposit) **stops: no further flow read**
- `0xf70da97812…` (5,857.90 USDC.e, bridge_deposit) **stops: no further flow read**
- `0xf70da97812…` (100.00 USDC.e, bridge_deposit) **stops: no further flow read**
- `0xf70da97812…` (1.00 USDC.e, bridge_deposit) **stops: no further flow read**

## Markets and positions

| Market | Trades | First | Capital engaged | Cash result | Shares left, API |
|---|---:|---|---:|---:|---:|
| Maduro out by January 31, 2026? | 7 | 2025-12-31 00:20:15 | 32,538.34 | 404,221.27 | 0.00 |
| Trump invokes War Powers against Venezuela by January 31? | 4 | 2026-01-01 23:56:53 | 250.00 | 2,464.64 | 0.01 |
| Will the U.S. invade Venezuela by January 31, 2026? | 2 | 2026-01-01 23:55:11 | 1,000.00 | 2,143.26 | 0.01 |
| US forces in Venezuela by January 31, 2026? | 2 | 2025-12-27 05:05:41 | 146.00 | 1,051.77 | 0.00 |

## Accounting

- Cash by type: {"deposit": "33937.078776", "buy": "33934.339992", "redeem": "437957.388901", "withdrawal": "443817.589766", "sell": "5857.90208", "merge": "0", "reward": "0", "maker_rebate": "0", "taker_rebate": "0", "referral_reward": "0", "yield": "0", "split": "0"}
- Unknown types: {}
- Trading cash over the rows read: 409,880.95. Balance computed from the rows: 0.44.
- Held today: null
- Withdrawals minus deposits is not a profit. An unredeemed position counts for nothing in cash.

## Coverage

| Address | Chain | Status | Rows | Source |
|---|---|---|---:|---|

## Where reading stopped

- BRIDGE_HOP_NOT_PROVEN: 7
- SERVICE_OR_SHARED:CONTRACT: 6
- AMBIGUOUS_PATH: 1
- Token rows outside the value list, not followed: 0 rows on 0 contracts

## Moves with their proof

| UTC | Chain | Role | Amount | From | To | Other side | Level / data | Transaction | Log |
|---|---|---|---:|---|---|---|---|---|---:|
| 2025-12-26 21:13:09 | polygon | bridge_payout | 96.276261 USDC.e | `0x56c262027e0de4aea31d2489529cb25d23e58a8b` | `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9` | Relay solver | REVERIFIED / fresh | `0xf064dbbbcab20e018de5f9207f23e6a78d009e150d8a08b8df6eb4908dc13152` | 151 |
| 2025-12-31 00:16:49 | polygon | deposit_path | 1,238.066040 USDC.e | `0x7f4f8ab7809c9b1e6ce14742608cf0f2b50ac473` | `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9` | CONTRACT | REVERIFIED / fresh | `0x795383b99c7f8654c70504afa563bcc0a53c5bf5495f940f7bad4adb87be0e4a` | 155 |
| 2026-01-01 23:54:09 | polygon | bridge_payout | 31,599.806914 USDC.e | `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9` | Relay EVM solver | REVERIFIED / fresh | `0x36bb7480367665f2ede304de84a0e38f1baefe81ff7e14f2c6d3e11bcb842f8c` | 353 |
| 2026-01-03 01:40:21 | polygon | bridge_payout | 914.483597 USDC.e | `0xa67d7eb4dc68fa6ce8e34ef8cadaf075b9893fbb` | `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9` | Relay solver | REVERIFIED / fresh | `0xdf77bb3edd4d1378369a56fe3d3c053d8872401d35bedc31696470f83ffaa8cc` | 1170 |
| 2026-01-03 15:41:33 | polygon | deposit_path | 0.770000 USDC.e | `0xb12a3f0fed5928c2eda8a16ed9e2d44d2c8dcb82` | `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9` | CONTRACT | REVERIFIED / fresh | `0x4513ad3ca76a48b579279ebd381ff9f64e83de34e6160ed4e1b6261c54c54cdc` | 651 |
| 2026-01-03 15:50:27 | polygon | deposit_path | 0.100000 USDC.e | `0x82aed30e16478ce30d1e60b2474c5bfb4ca34325` | `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9` | CONTRACT | REVERIFIED / fresh | `0x0498f455ae267187409a4cb56b04463f2f16a0967478b3fe575c24056ec1f1ad` | 408 |
| 2026-01-03 16:33:27 | polygon | deposit_path | 0.210000 USDC.e | `0x815770b0f7be31a2a6587dd336d1077502196cc6` | `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9` | CONTRACT | REVERIFIED / fresh | `0x12d71fb5c07b4d6721c68850559931f797eef1b6daa4baa13a65ba7d7dfa2035` | 994 |
| 2026-01-03 23:50:17 | polygon | bridge_deposit | 100.000000 USDC.e | `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9` | `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | Relay EVM solver | REVERIFIED / fresh | `0x55c09ad76bfcba05460c139fe383f2a9f9699ce3b15d92642f56727daeb9ca5a` | 1322 |
| 2026-01-03 23:54:35 | polygon | bridge_deposit | 437,858.687687 USDC.e | `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9` | `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | Relay EVM solver | REVERIFIED / fresh | `0xbb15de695f711b191732056cb8c170166373a98f889e2e5ea9d40c525917be96` | 841 |
| 2026-01-04 00:06:17 | polygon | bridge_deposit | 5,857.902080 USDC.e | `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9` | `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | Relay EVM solver | REVERIFIED / fresh | `0x6b871b2e1ea68e50c46ae0fcffafca299fe67db710abad46542cd5b6c6c64ca9` | 1087 |
| 2026-01-06 04:51:21 | polygon | deposit_path | 1.000000 USDC.e | `0xc4d5f64b741d55464250ff1bae7b23742b208814` | `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9` | CONTRACT | REVERIFIED / fresh | `0x1374937e9ef8bf14ed4b0d877bedce740655caf60dd10d76dfc6914f64a8d71c` | 765 |
| 2026-01-06 16:57:51 | polygon | bridge_deposit | 1.000000 USDC.e | `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9` | `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | Relay EVM solver | REVERIFIED / fresh | `0x5582e70a2ac9c1df06d98c2ac102d5f5004dc58bb0d214e7acc9f8991d597197` | 510 |
| 2026-01-14 22:49:34 | polygon | deposit_path | 0.440000 USDC.e | `0x2501e39763fd3c90cbcfdb212cb9640159d49a5b` | `0x31a56e9e690c621ed21de08cb559e9524cdb8ed9` | CONTRACT | REVERIFIED / fresh | `0xe13b3aecddb001bb6ebd7fff0cd5990701d3672da8520e31eb0f2401af2b06b9` | 906 |

## Other explanations

- Money between two addresses says nothing of who holds them: a payment, a gift, a loan, a service or a resale give the same picture.
- A service or an exchange pays thousands of people. A shared one proves no link.
- An early, large or lucky bet can follow public signals, private analysis or chance.
- Access to private information is not something on-chain data can show.
