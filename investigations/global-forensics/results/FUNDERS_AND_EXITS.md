# Who paid each account, and where its money went

Written by `engine/tools/money_report.py` from `wallets/*/trace.json`. An address is not a person, and money between two addresses does not show a common owner. Ownership is not established for any address here. No finding of wrongdoing.

A payer or destination is one hop from the account or its keys. A branch further out shows flows through an address, and tokens are fungible, so they are not shown to be the same units. USD at list rates: exact for dollar tokens, an estimate for the others.

Levels: `ONCHAIN_CONFIRMED` is a log read in a receipt. `LISTED` is an explorer row not yet confirmed by a receipt. A bridge hop is shown with its own proof in the file.

## Ballon d'Or

### 0x86544e4dfde

`0x3ed2c452f141c291adecb97ddfc72b1650acff3d`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 44,847.24, withdrawals 74,198.32, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 4, "WINDOW_SCAN_NEEDED": 2}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x3ed2c452f141c291adecb97ddfc72b1650acff3d` | 137 | read through a bridge | 74,198.32 USDC | 74,198.32 | 1 | 2026-10-27 01:59 | `0xf157abfd294420ba1d35bf08a5c8725bb74a87437454fea3ead8da50dbeabb05` | LISTED | Relay, same id on both chains |
| `0x0ce9bdf38714143043b1d36de9bd90f7335bf06d` | 137 | Circle SingleOwnerMSCA account of an unattributed custodial service | 42,390.54 USDC | 42,390.54 | 3 | 2026-10-09 15:40 | `0x76465038ac8cd628232731259c2544ff4d6b2c61af02619e1be0a97b33b2e13b` | LISTED | direct |
| `0x69837228fa0bcbac53713d981161c929523c0ded` | 137 | read through a bridge | 42,389.48 pUSD | 42,389.48 | 3 | 2026-10-09 18:06 | `0x40f84e77821ecf20773964ead4dba8868267f8efcb9f9d134d50c3a27dcc2f1e` | REVERIFIED | Relay, same id on both chains |
| `0x99a5baa3a0210b6eee0641f5976ad483fc5d22be` | 137 | PERSONAL_SIZED | 2,457.76 pUSD | 2,457.76 | 1 | 2026-10-17 21:09 | `0x8579f8fba65448840888623b49218adb9fbb0a39ef7821a997fb1ce6fd5243cf` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x69837228fa0bcbac53713d981161c929523c0ded` | 1 | read through a bridge | 74,198.32 USDC.e | 74,198.32 | 1 | 2026-10-27 01:59 | `0x592333616322f0718366c916984050edd5b23d8ce108c62f4aaecb62cfe03b83` | REVERIFIED | Relay, same id on both chains |
| `0x3ed2c452f141c291adecb97ddfc72b1650acff3d` | 137 | read through a bridge | 42,389.48 USDC | 42,389.48 | 3 | 2026-10-09 18:05 | `0xba5a0a5905f753ed509069527670eef0fb8b2bfdc3a27b569f3476ba4df8ab40` | LISTED | Relay, same id on both chains |

Funding branches stopped at: Circle SingleOwnerMSCA account of an unattributed custodial service (3 branches, 42,390.54 USD); Kraken: Hot Wallet (7 branches, 12,463.48 USD); Binance: Hot Wallet (7 branches, 11,082.85 USD); UniswapX: Dutch Order Reactor V2 (1 branches, 870.89 USD); Binance 16 (1 branches, 826.59 USD); Binance 17 (2 branches, 681.30 USD); Across Protocol: Ethereum Spoke Pool V2 (1 branches, 344.68 USD); NEAR Intents (1 branches, 319.99 USD); Uniswap V4: Pool Manager (3 branches, 28.58 USD); Relayer of MetaMask-delegated transactions (1 branches, 0.44 USD).

### 0xdd97e6

`0xdd97e6ad12ca4dd18a88804fb5ed7ed429849464`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 44,059.16, withdrawals 63,143.10, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1, "WINDOW_SCAN_NEEDED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x22cec127f5e203578d2b8b7e6eddf182a2342e76` | 137 | PERSONAL_SIZED | 44,059.16 pUSD | 44,059.16 | 2 | 2026-10-20 09:11 | `0xf9ae2a36fcd4d92b72231b4bad40cca7fdc3a48f9620eace4cf9479bbbfb6f05` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xca8b1f1a56a0fe8947d325baafa286f5bd4d6165` | 1 | read through a bridge | 63,143.10 USDC.e | 63,143.10 | 1 | 2026-10-27 00:49 | `0x16ae2a26a481e38097d3b0cbcec9a704dc07d98e7de3b9d58935e6dc93f4b208` | REVERIFIED | Relay, same id on both chains |

### brace227

`0x873848cd27784900e193611845fc3fd2c4716d03`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 10,032.98, withdrawals 22,036.76, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1, "WINDOW_SCAN_NEEDED": 4, "DEPTH_BUDGET": 1, "CONTRACT_NOT_IDENTIFIED": 48}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x873848cd27784900e193611845fc3fd2c4716d03` | 137 | read through a bridge | 22,036.76 USDC | 22,036.75 | 4 | 2026-10-11 13:25 | `0x1f3bb89154029ee54984e44d8650fe88b2dddd22051aeb97c942ca31525454bf` | LISTED | Relay, same id on both chains |
| `0xc1d13492285eb664951e201bf7c80c7c6318a1b5` | 1 | SwftSwap (SWFT Blockchain) | 15,096.29 USDC | 15,096.28 | 4 | 2026-10-09 20:03 | `0xead283d89c81ad82e63d7186d7b52a5d4279fe11bd3352fa0430d01b7f472f3f` | LISTED | direct |
| `0xc852b0938f5ad79b640d105ed11c14499454af26` | 1 | read through a bridge | 10,032.98 pUSD | 10,032.99 | 8 | 2026-10-09 20:49 | `0x2a89597ebf1d83b5b76ceccab02924c28ca0ad8f6d208b2c42801a0925280a2c` | REVERIFIED | Relay, same id on both chains |
| `0xcad621da75a66c7a8f4ff86d30a2bf981bfc8fdd` | 1 | KuCoin: Hot Wallet | 0.13 ETH | 296.39 | 2 | 2022-03-29 02:56 | `0x61feaa449019253831b9e38a62ea93457072d421df6253ce12edfce699bfa116` | LISTED | direct |
| `0x3eaef6d5e91ecf7b7623eb19978e145ebd417013` | 1 | PERSONAL_SIZED | 291.32 USDT | 291.32 | 1 | 2025-01-04 02:03 | `0xf64e9d194769bdcad0682063984db82e7add22c752e28bbc1f597cdc02a7b3ff` | LISTED | direct |
| `0x7ff8bbf9c8ab106db589e7863fb100525f61cce5` | 1 | BloFin: Hot Wallet 1 | 110.20 USDC | 110.20 | 1 | 2026-10-20 16:44 | `0xebbc699a370b7796c6e13e52da28cbea08541b03e79551b30ed70a8b0002edd3` | LISTED | direct |
| `0x4976a4a02f38326660d17bf34b431dc6e2eb2327` | 1 | Binance: Hot Wallet | 0.02 ETH | 54.87 | 1 | 2022-03-30 13:55 | `0x60a45586833962b48cc532f0adff732112709cd7f07e3782373f002abbc12d72` | LISTED | direct |
| `0xd37bbe5744d730a1d98d8dc97c42f0ca46ad7146` | 1 | THORChain: THORChain Router v4.1.1 | 6.71 USDT | 6.71 | 1 | 2026-10-12 18:45 | `0xfd1f2912b28873463db1c46178c684ea3018b20a24d0b8e923ea43f8eaa9ef89` | LISTED | direct |
| `0x2cff890f0378a11913b6129b2e97417a2c302680` | 1 | NEAR Intents | 0.00 ETH | 4.65 | 1 | 2026-10-16 19:21 | `0xb32fb0edcaf35315c87edb50ae9675e7a9e2ea76aa39c027acdf6f5e6b1c056d` | LISTED | direct |
| `7XUJsJBNp7WykVXG4y76ntsSn3H7tFdLVcmehAgJfrZc` | 792703809 | read through a bridge | 0.00 ETH | 3.89 | 1 | 2026-10-04 13:52 | `0xb17e1c4627ad8914f98f48a4fa7f5916953d3286e60cf3d80c6508257f46ce3c` | LISTED | Relay, same id on both chains |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xc852b0938f5ad79b640d105ed11c14499454af26` | 1 | read through a bridge | 22,036.76 USDC.e | 22,036.75 | 4 | 2026-10-11 13:25 | `0x93518e172a0daf71fa8610c411e0ec5b7e208773424a2898e889e39e0816c946` | REVERIFIED | Relay, same id on both chains |
| `0x873848cd27784900e193611845fc3fd2c4716d03` | 137 | read through a bridge | 10,032.98 USDC | 10,032.99 | 8 | 2026-10-09 20:48 | `0xdade897786d0929dcaf4c0c93513178069d81b0b946f17c375355a39079a9cf8` | LISTED | Relay, same id on both chains |
| `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d` | 1 | PERSONAL_SIZED | 5,170.00 USDC | 5,170.00 | 2 | 2026-10-09 20:28 | `0x7e3aecb9b41e6d3f92f25b8760228f15e9b55e798cd27977eb7170445cf64349` | LISTED | direct |
| `0xd37bbe5744d730a1d98d8dc97c42f0ca46ad7146` | 1 | THORChain: THORChain Router v4.1.1 | 7.00 USDC | 7.00 | 1 | 2026-10-12 18:45 | `0xac47d8f901b76bad8b1aa370945a8ac16039c3e57e538d48c7b72d5f10719951` | LISTED | direct |
| `0x2c791cb8eb86e23ca61a4a478d8d5caa4ff7118a` | 1 | PERSONAL_SIZED | 6.69 USDT | 6.69 | 1 | 2026-10-12 18:47 | `0xa6497b227fb39257f0107ad44d860182a585f9e860ca4e7725acc368da4867df` | LISTED | direct |
| `0xcde230988abac1e56f57e3ed4fcd85fe6cc6d1f1` | 1 | PERSONAL_SIZED | 5.00 USDC | 5.00 | 1 | 2026-10-16 19:20 | `0x1acaf51467d0686487dffacdb213edd1e4212105084fedce06ba9716ab953998` | LISTED | direct |
| `0x101b5f4dc0886c32e2b75972101aeaf9f338fb65` | 1 | PERSONAL_SIZED | 0.00 ETH | 4.71 | 1 | 2026-10-04 13:54 | `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98` | LISTED | direct |
| `0xe3478b0bb1a5084567c319096437924948be1964` | 1 | MetaMask: Gas Station Swap | 1.01 USDC | 1.01 | 1 | 2026-10-09 20:28 | `0x325baa1df3cfb3a87d664c7a1afb592abb7916276d7afd7e6538332769ba5ec6` | LISTED | direct |

Funding branches stopped at: SwftSwap (SWFT Blockchain) (4 branches, 15,096.28 USD); ChangeNOW: Hot Wallet 3 (4 branches, 450.78 USD); Measured hub, unnamed (11 branches, 332.69 USD); KuCoin: Hot Wallet (2 branches, 296.39 USD); BloFin: Hot Wallet 1 (1 branches, 110.20 USD); Binance: Hot Wallet (1 branches, 54.87 USD); ChangeNOW 16 (2 branches, 23.00 USD); THORChain: THORChain Router v4.1.1 (1 branches, 6.71 USD); NEAR Intents (1 branches, 4.65 USD); MetaMask: Gas Station (2 branches, 1.04 USD).

Exit branches stopped at: Polymarket pUSD — CollateralToken Poly v2 (4 branches, 23,215.73 USD); Polymarket Neg Risk CTF Exchange (58 branches, 11,298.13 USD); Polymarket CTF Exchange (25 branches, 3,705.05 USD); MetaMask: Swaps Spender (1 branches, 3,000.00 USD); Measured hub, unnamed (2 branches, 7.69 USD); THORChain: THORChain Router v4.1.1 (1 branches, 7.00 USD); ChangeNOW Dep: 0x3f3...07B (1 branches, 5.55 USD); NEAR Intents (1 branches, 5.00 USD); MetaMask: Gas Station Swap (1 branches, 1.01 USD).

### cookedrice

`0x4060509c8c70cece529be4a089d6d66ad865b4d0`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 21,873.74, withdrawals 39,158.78, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xd628c333015848b9c4e8c519f51a22642a555c58` | 137 | PERSONAL_SIZED | 21,873.74 pUSD | 21,873.74 | 1 | 2026-10-14 19:58 | `0x9e1a809440c983f23ae834f92a6214198cfd15b65b4001e5739add05ea733012` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `F7ew8r8X5YL3DPLtzg9Az3cPDKcVxXGjUpqgpskNh5Eh` | 792703809 | read through a bridge | 39,158.78 USDC.e | 39,158.78 | 1 | 2026-10-28 18:04 | `0x32c1285b13708b90937e6af48e956c07148630916649d021f9047af08767f1ae` | REVERIFIED | Relay, same id on both chains |

Funding branches stopped at: KuCoin Hot Wallet 2 (1 branches, 21,873.74 USD).

Exit branches stopped at: Unidentified Solana custodial service (cosigns sweeps of its deposit addresses) (1 branches, 39,158.00 USD).

### kraben006

`0x84212ee459d1edaf35983bbec342b0806282d8ec`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 5,689.47, withdrawals 15,593.54, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1, "WINDOW_SCAN_NEEDED": 3, "CONTRACT_NOT_IDENTIFIED": 9, "DEPTH_BUDGET": 2}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x84212ee459d1edaf35983bbec342b0806282d8ec` | 137 | read through a bridge | 15,593.15 USDC | 15,593.15 | 5 | 2026-10-07 00:33 | `0xb10a9439124aa29e783787d6a1399398cd1f2816b5d111c3c8cd60e19803d104` | LISTED | Relay, same id on both chains |
| `0x101b5f4dc0886c32e2b75972101aeaf9f338fb65` | 1 | read through a bridge | 5,689.47 pUSD | 5,689.47 | 14 | 2026-10-01 18:31 | `0x4431828712a924d5845de5f1779ad98eabf3563d55f299f46dde35700129a5a4` | REVERIFIED | Relay, same id on both chains |
| `0x7bef16275a88bd9c3004dbd0b85da65b08705c24` | 1 | Payout wallet of an unattributed custodial service | 1,943.61 USDC | 1,943.61 | 5 | 2026-10-07 00:18 | `0x66a3b700ba3d9653b2a24f6a54f92fb9d772e52b408f11169fe552dee4c59acd` | LISTED | direct |
| `0xbd1f44622d8a2480546e72afb90696ae4fc7eb3b` | 1 | Payout wallet of an unattributed custodial service | 1,752.46 USDC | 1,752.46 | 2 | 2026-10-01 21:48 | `0x4106c63f93fffc8fd0b31ceb039a22c5e9dbf10d92167b7b523325dd7345f719` | LISTED | direct |
| `0x58f298e3bf930886ab7639f4d71f892d5f1f0214` | 1 | Payout wallet of an unattributed custodial service | 1,046.82 USDC | 1,046.82 | 2 | 2026-10-01 18:37 | `0x8948ecd5edf1ab214c850641ca340fbbf7e6496f42b863c38f77f497417c6395` | LISTED | direct |
| `0xdd3d72c53ff982ff59853da71158bf1538b3ceee` | 1 | ChangeNOW: Hot Wallet 3 | 834.85 USDC | 834.85 | 2 | 2026-02-23 15:56 | `0x5e8b57210b722dbf0f7395cbe20c57a3e578d2897bb4ff8d4c5e853387789219` | LISTED | direct |
| `0x0c58909d3bbca91c4a5c3acbe0a72b57312d270d` | 1 | Payout wallet of an unattributed custodial service | 315.68 USDC | 315.68 | 1 | 2026-10-02 03:51 | `0x26103b96cae8b5403fdd784b462f462e2ab81c2f9d51bbb11b337ebb443966b5` | LISTED | direct |
| `0xb43c1981d57161dcb077ee4bcbb2d376b577a857` | 1 | Deblock: Wallet 1 | 244.80 USDC, 0.00 ETH | 252.99 | 3 | 2026-01-14 11:44 | `0x9e8097e8cb64501fa88c544198166bb820cd4659317ffa4ef8f003f8108ab4ac` | LISTED | direct |
| `0xc1d13492285eb664951e201bf7c80c7c6318a1b5` | 1 | SwftSwap (SWFT Blockchain) | 188.97 USDC | 188.97 | 1 | 2026-10-01 18:25 | `0x7ba5697f8278d0558d58e97250d086128e76f18b730637072a44d2de0db6530f` | LISTED | direct |
| `0xcad97616f91872c02ba3553db315db4015cbe850` | 1 | HUB_MEASURED | 49.18 USDC | 49.18 | 1 | 2026-02-23 17:06 | `0x4f7bf1ca04123f5d7c0c7ee4ed54dcc6618b160f6b407edd8dfbf2b57e821fa9` | LISTED | direct |
| `0xc852b0938f5ad79b640d105ed11c14499454af26` | 1 | PERSONAL_SIZED | 0.00 ETH | 4.71 | 1 | 2026-10-04 13:54 | `0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x101b5f4dc0886c32e2b75972101aeaf9f338fb65` | 1 | read through a bridge | 15,593.54 USDC.e | 15,593.54 | 5 | 2026-10-07 00:33 | `0x9e313ca47e181cfe4e0368653ed28a63826eded1ce4bbd50909db123ca99166e` | REVERIFIED | Relay, same id on both chains |
| `0x84212ee459d1edaf35983bbec342b0806282d8ec` | 137 | read through a bridge | 5,689.47 USDC | 5,689.47 | 14 | 2026-10-01 18:30 | `0x08ac0743492cf551079d0623e366090dc55ddd32b2dbd302dc6614b70e5fc214` | LISTED | Relay, same id on both chains |
| `0x7e67df45e0a0bab092cbb2ff045f8aa8dfab6e23` | 1 | PERSONAL_SIZED | 0.00 ETH | 5.69 | 1 | 2026-10-04 23:48 | `0x1a39308b89cc7d9de6e38fbf0c62aa5d0bdd777863079cd151fe12a6b135dd71` | LISTED | direct |

Funding branches stopped at: Payout wallet of an unattributed custodial service (10 branches, 5,058.57 USD); ChangeNOW: Hot Wallet 3 (6 branches, 1,285.63 USD); Measured hub, unnamed (11 branches, 381.74 USD); KuCoin: Hot Wallet (2 branches, 296.39 USD); Deblock: Wallet 1 (3 branches, 252.99 USD); SwftSwap (SWFT Blockchain) (1 branches, 188.97 USD); Binance: Hot Wallet (1 branches, 54.87 USD); ChangeNOW 16 (2 branches, 23.00 USD).

Exit branches stopped at: ChangeNOW Dep: 0x3f3...07B (1 branches, 5.55 USD).

### ouldlm3alem

`0x71ae923f12eb947c58365287691cf5a10bc3e5bf`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 56,167.11, withdrawals 77,250.77, residual 0.2. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1, "BRIDGE_FAR_SIDE_NOT_READ": 2, "CONTRACT_NOT_IDENTIFIED": 3, "WINDOW_SCAN_NEEDED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x71ae923f12eb947c58365287691cf5a10bc3e5bf` | 137 | read through a bridge | 839,893.73 POL | 83,989.37 | 1 | 2026-10-26 23:50 | `0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1` | LISTED | Relay, API record only |
| `0x555ce236c0220695b68341bc48c68d52210cc35b` | 42161 | HUB_MEASURED | 75,724.74 USDC | 75,724.74 | 1 | 2026-10-29 20:54 | `0x88a0d82f0453c76294e665fc884069773b486f4c57b9ba88a6dde84f40f466b7` | LISTED | direct |
| `0xb3afcdc711378d17ca1a1000770af5a0b78bb0ba` | 137 | PERSONAL_SIZED | 56,167.11 pUSD | 56,167.11 | 3 | 2026-10-22 18:39 | `0xaed3dd931c9bbc163818983c01b6ebc43cb3885f43dcb18359d3651e7f5fe4dd` | REVERIFIED | direct |
| `0xe7351fd770a37282b91d153ee690b63579d6dd7f` | 42161 | deBridge: DlnDestination | 0.03 ETH | 78.89 | 1 | 2026-10-29 22:11 | `0x1609361dc493ec13dc46cb99ab042e69b9a404c0d490e9b605fc66b498118739` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xdc264714f68d84cf29bc605589405e78bdbe7c9f` | 137 | CONTRACT | 839,000.00 POL | 83,900.00 | 1 | 2026-10-26 23:52 | `0x8c35829294c002aabcd2bd518e88f46f86e4c5a075c6e89938d4532cc62dd2c3` | LISTED | direct |
| `0x1b500b6c40a2ff0930e540e8f53c559a32e75f2c` | 137 | read through a bridge | 77,050.77 USDC.e | 77,050.77 | 1 | 2026-10-26 23:50 | `0x909d9602d5ad975b2f30c66d4a058592306e2468a002dd0a691170b61677a6f1` | REVERIFIED | Relay, API record only |
| `0x663dc15d3c1ac63ff12e45ab68fea3f0a883c251` | 137 | deBridge: Crosschain Forwarder Proxy | 75,946.74 USDT, 888.19 POL | 76,035.56 | 2 | 2026-10-29 20:54 | `0x70a1e0133b21f471c6e5bd556c54c5df982606ac8c45a47286edc0344c5d108f` | LISTED | direct |
| `0xa95d9c1f655341597c94393fddc30cf3c08e4fce` | 42161 | CONTRACT | 75,724.74 USDC | 75,724.74 | 1 | 2026-10-29 20:55 | `0x5c5e1650625c27fdc99cd69993a79132db223b899fef7b1b6b85911cf0fc223a` | LISTED | direct |
| `0xae232f7885946fda51b3f1dac7e10ffaae00c026` | 56 | read through a bridge | 200.00 USDC.e | 200.00 | 2 | 2026-10-26 21:40 | `0x8d84c3cf0d15c5e573b71b75c43182837a9d88b3d3ad1ed078c11ffef9c58a40` | REVERIFIED | Relay, same id on both chains |

Funding branches stopped at: Measured hub, unnamed (2 branches, 75,724.79 USD); deBridge: DlnDestination (1 branches, 78.89 USD).

Exit branches stopped at: deBridge: Crosschain Forwarder Proxy (3 branches, 76,035.61 USD).

### thin

`0x8d3319c51520518ad01f6744486ceea29f376f5b`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 45,679.23, withdrawals 80,037.93, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1, "WINDOW_SCAN_NEEDED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x8e43af995577339436e071990e524ebfe6c09865` | 137 | PERSONAL_SIZED | 45,679.23 pUSD | 45,679.23 | 3 | 2026-10-11 15:23 | `0x761f6058829482bc5fc66acd8b6d5bcc583e96a463ac75e52d666b31fd6f32d1` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `CXVYMP5qxBENTNnqqmBAgvQB5wRLkcUBYPBDLFTeGrfJ` | 792703809 | read through a bridge | 40,250.00 USDC.e | 40,250.00 | 2 | 2026-10-27 01:24 | `0x6373a98fb86f82e1562448ccddf261d537a06a7112180f1d414e3f0968d9be7c` | REVERIFIED | Relay, same id on both chains |
| `EnHRjTP4pKGkA4BC1yfoCNyUJcU3wapK1Gj8Us35PZ8B` | 792703809 | read through a bridge | 39,787.93 USDC.e | 39,787.93 | 2 | 2026-10-27 01:28 | `0xe35ea7f316355dc91347aa2f409aa030bb696035151a5ea5d8d72a69d11df989` | REVERIFIED | Relay, same id on both chains |

Funding branches stopped at: KuCoin Hot Wallet 2 (1 branches, 11,833.23 USD).

### vidente

`0x5f8b30fde56bd2d2f3853769602330aeb9f1866a`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 28,029.96, withdrawals 51,509.88, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x6d24d9452f900f3307cd5b791ffaf1d1a7476df8` | 137 | PERSONAL_SIZED | 28,029.96 pUSD | 28,029.96 | 2 | 2026-10-15 21:06 | `0xcb790208996b569b3671f4d5090acae8ca22eff2a3cec6029b8aeee2081aa2d1` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `DMmDPF9sFcNbq8dVKfxqZsKV4xKZBtsUZ4hXSwy1wt5T` | 792703809 | read through a bridge | 51,509.88 USDC.e | 51,509.88 | 1 | 2026-10-27 16:51 | `0x650d76f3ef10b8e0001baf61693372fa8634ae29a29ae11f86589c064cf52e16` | REVERIFIED | Relay, same id on both chains |

Funding branches stopped at: KuCoin Hot Wallet 2 (1 branches, 9,940.01 USD).

Exit branches stopped at: Unidentified Solana custodial service (cosigns sweeps of its deposit addresses) (1 branches, 51,489.00 USD).

### walletwallet8424

`0x1a1ef4c65583d5c71011d7fe51e9f544e2b1cc40`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 22,088.68, withdrawals 35,546.89, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1, "WINDOW_SCAN_NEEDED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x1a1ef4c65583d5c71011d7fe51e9f544e2b1cc40` | 137 | read through a bridge | 35,546.89 USDC | 35,546.89 | 1 | 2026-10-27 02:01 | `0x1eb9ec280314e1c8e81753c286d53d4aee7c0e7e1eac4149e4de1f9409213b76` | LISTED | Relay, same id on both chains |
| `0x82775eb82fe33acffdf1b91a28c0fc19b4b6a3a1` | 137 | read through a bridge | 22,088.68 pUSD | 22,088.68 | 3 | 2026-10-10 13:19 | `0x71250186b46bcded0deb878fae935386f67adeb43ed59c64a6d1614d291594f4` | REVERIFIED | Relay, same id on both chains |
| `0xcc0f311eb2c688f30bc9aadb42781e46899723f7` | 1 | PERSONAL_SIZED | 16,808.96 USDC | 16,808.96 | 1 | 2026-10-10 18:41 | `0x6afda18100e60991b4a7cd34c07616f14bb27c734e57391f14eb00f83bf00358` | LISTED | direct |
| `0x0ce9bdf38714143043b1d36de9bd90f7335bf06d` | 137 | Circle SingleOwnerMSCA account of an unattributed custodial service | 5,581.47 USDC | 5,581.46 | 2 | 2026-10-10 13:12 | `0x1e19e0ae34d250fac1b26db226a98a6c06d41859245ccdaa1ba2dbc8041c319d` | LISTED | direct |
| `0xc066ac5d385419b1a8c43a0e146fa439837a8b8c` | 1 | MetaMask: Gas Station | 0.00 ETH | 4.01 | 1 | 2026-10-10 19:13 | `0x02ed690756140466231f686e877f77179ec66f72b72964f017bc5bc06d8e4a4f` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x82775eb82fe33acffdf1b91a28c0fc19b4b6a3a1` | 1 | read through a bridge | 35,546.89 USDC.e | 35,546.89 | 1 | 2026-10-27 02:01 | `0x27db9e0ad79e75020c1fcff6d22940313ab26808a853a5139db35c8823321a91` | REVERIFIED | Relay, same id on both chains |
| `0x1a1ef4c65583d5c71011d7fe51e9f544e2b1cc40` | 137 | read through a bridge | 22,088.68 USDC | 22,088.68 | 3 | 2026-10-10 13:19 | `0xa63cf849db8399ff7d626dadcc460e013665907cf6ae6f4c81fab577f9c17c17` | LISTED | Relay, same id on both chains |
| `0x74de5d4fcbf63e00296fd95d33236b9794016631` | 1 | MetaMask: Swaps Spender | 16,808.96 USDC | 16,808.96 | 1 | 2026-10-10 19:13 | `0x42853b0ffc770d371eca4519e5eb44a7747335ad35ce0496d0a664adf21a1f8e` | LISTED | direct |
| `0xa0c68c638235ee32657e8f720a23cec1bfc77c77` | 1 | Polygon (Matic): Bridge | 6.63 ETH | 15,249.65 | 1 | 2026-10-10 19:15 | `0xf17a234a067c0739c15211f79866e1afab9337d60d58023b16dbaa16f47e32f2` | LISTED | direct |
| `0xc590175e458b83680867afd273527ff58f74c02b` | 137 | Swap contract used through MetaMask delegation | 6.63 WETH | 15,249.65 | 1 | 2026-10-10 19:32 | `0x0adf897130e4317e7cfc06fd08c4a6cb9b26b4810611fa8037f532930f9b261d` | LISTED | direct |

Funding branches stopped at: Circle SingleOwnerMSCA account of an unattributed custodial service (2 branches, 5,581.46 USD); MetaMask: Gas Station (1 branches, 4.01 USD); Measured hub, unnamed (1 branches, 0.00 USD).

Exit branches stopped at: MetaMask: Swaps Spender (1 branches, 16,808.96 USD); Polygon (Matic): Bridge (1 branches, 15,249.65 USD); Swap contract used through MetaMask delegation (1 branches, 15,249.65 USD).

### wen

`0x8832319d9c25df311e37511f0aa5b214abc16500`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 15,926.88, withdrawals 27,724.79, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x315ac6e73410faafd02edac1b1a46da7b90814c5` | 137 | PERSONAL_SIZED | 15,926.88 pUSD | 15,926.88 | 1 | 2026-10-18 20:14 | `0x45c27719b34b5490a620b319911db190d6570bc1b0e2da3782d5bbb8c4cc2da3` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xe820ecb3c6f48a420a5538046cab73d2f40987cd` | 42161 | read through a bridge | 27,724.79 USDC.e | 27,724.79 | 1 | 2026-10-27 22:58 | `0x094f60bf5bf3a015903748b150b621bfeb115dcccf5d81d35bd688d5cdbe9b91` | REVERIFIED | Relay, same id on both chains |

Funding branches stopped at: Binance: Hot Wallet 34 (1 branches, 15,926.88 USD).

Exit branches stopped at: Measured hub, unnamed (2 branches, 27,724.02 USD).

### zoomman17

`0x92a8eec13a691af81a1a196b7594c1eccfa0eebc`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 9,743.19, withdrawals 6,894.00, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xd90d00130519086d412d2b9ffac2bb01f71ef444` | 1 | read through a bridge | 9,743.19 pUSD | 9,743.19 | 5 | 2026-10-06 00:45 | `0xc401f99aae37edbab349f5130cdf1db71d4c23539a741594aa8aa91b4dbc092e` | REVERIFIED | Relay, same id on both chains |
| `0x92a8eec13a691af81a1a196b7594c1eccfa0eebc` | 137 | read through a bridge | 6,894.00 USDC | 6,894.00 | 3 | 2026-10-11 22:23 | `0xd65619db14590731fd8f81834bc692aa4ee22add918a8c70b898ba3e81c01899` | LISTED | Relay, same id on both chains |
| `0xf5e10380213880111522dd0efd3dbb45b9f62bcc` | 1 | Chainflip 1 | 5,439.33 USDC | 5,439.33 | 1 | 2026-10-09 20:03 | `0xa290b2af61506058dc65e362a1ef51896c86a6374f701d38b521f25044e975b7` | LISTED | direct |
| `0xb23360ccdd9ed1b15d45e5d3824bb409c8d7c460` | 1 | Revolut: Hot Wallet | 3,227.76 USDC | 3,227.75 | 7 | 2026-10-09 14:28 | `0x72a7ece2e2b99c4555d371704ff4a22d5ac890edbcb4129fd95b826444119d33` | LISTED | direct |
| `0x58f298e3bf930886ab7639f4d71f892d5f1f0214` | 1 | Payout wallet of an unattributed custodial service | 867.98 USDC | 867.98 | 1 | 2026-10-06 00:32 | `0xa3214c31f7b3b3494293abbea89a40f059f2bb42b20cb04434970d2a2361a120` | LISTED | direct |
| `0x09c30cdcdd971423cb3ba757a47d56c35d06d818` | 1 | Revolut 6 | 0.11 ETH | 260.27 | 1 | 2026-10-26 17:26 | `0x1373d64937774e481aecc3d805ca0ce22c682de09625c56e323a49112ceac11a` | LISTED | direct |
| `0x74de5d4fcbf63e00296fd95d33236b9794016631` | 1 | MetaMask: Swaps Spender | 0.00 ETH | 6.93 | 1 | 2026-10-09 19:43 | `0xba9821f67d9755dd46d8321fdb05a520d9d949a9e3865cabb8cc34fcec6d6b3c` | LISTED | direct |
| `0xc066ac5d385419b1a8c43a0e146fa439837a8b8c` | 1 | MetaMask: Gas Station | 0.00 ETH | 4.80 | 2 | 2026-10-09 19:42 | `0x57a3c486dd2bf675096ea2804cf714257c79311a5a4d2acba0c58109d9db2982` | LISTED | direct |
| `0xb01caea8c6c47bbf4f4b4c5080ca642043359c2e` | 1 | MetaMask: Gas Station 2 | 0.00 ETH | 3.17 | 2 | 2026-10-09 18:35 | `0x74340de8cbd957877bf9bf0f0bde398df3fa7dfe67d27f0aeaaa2d0a77ef97c6` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x92a8eec13a691af81a1a196b7594c1eccfa0eebc` | 137 | read through a bridge | 9,484.65 USDC, 0.11 ETH | 9,742.39 | 5 | 2026-10-06 00:44 | `0xc57e5170b950615d23938e5fc57bed952f29927f7d838443b5c0b8f22b258643` | LISTED | Relay, same id on both chains |
| `0xd90d00130519086d412d2b9ffac2bb01f71ef444` | 1 | read through a bridge | 6,894.00 USDC.e | 6,894.00 | 3 | 2026-10-11 22:23 | `0x1bb4cf39845d19c62166ed1cb3e2b0f4c37a0c0298ce7cba062ff5e2217c33f8` | REVERIFIED | Relay, same id on both chains |
| `0x8c5dc729fe1f5f31d6722301fc3fe8f83eb710fe` | 1 | PERSONAL_SIZED | 6,893.00 USDC | 6,893.00 | 4 | 2026-10-11 22:25 | `0x6e04aeb4c6c1a84ded7fa077c988edf2c5c95c00e8db7237a902e89d1863cf54` | LISTED | direct |
| `0x9a47f3289794e9bbc6a3c571f6d96ad4e7baed16` | 1 | MetaMask: MetaBridge V2 Spender | 23.00 USDC | 23.00 | 1 | 2026-10-09 19:58 | `0x8cea7e5fbd2407a70e514d45369b087c45b432dd11d9f2b636a203a89c0ffeb8` | LISTED | direct |
| `0x74de5d4fcbf63e00296fd95d33236b9794016631` | 1 | MetaMask: Swaps Spender | 21.91 USDC | 21.91 | 3 | 2026-10-09 18:35 | `0x3b31351409dbf79981d62d6c186f3563f23e11e6a8f3033ea0f891f1f001abec` | LISTED | direct |
| `0x881d40237659c251811cec9c364ef91dc08d300c` | 1 | Swap Router | 0.00 ETH | 9.63 | 1 | 2026-10-09 18:59 | `0x933d3772841f79fe4d9d737668b06737184972a2bb3ae5f883666d3fc01278e0` | LISTED | direct |
| `0x0439e60f02a8900a951603950d8d4527f400c3f1` | 1 | MetaMask: Meta Bridge | 0.00 ETH | 8.01 | 1 | 2026-10-09 19:50 | `0x2be67fb363ed1b0a480a840a598d76cfb4fd11ed3e749480771fea0051e42a7a` | LISTED | direct |
| `0xe3478b0bb1a5084567c319096437924948be1964` | 1 | MetaMask: Gas Station Swap | 6.52 USDC | 6.52 | 6 | 2026-10-06 00:43 | `0xdec6234631418a1722fb9bb478b2edc4dfa0ce2bec55cad200788e30d43433c9` | LISTED | direct |

Funding branches stopped at: Chainflip 1 (1 branches, 5,439.33 USD); Revolut: Hot Wallet (7 branches, 3,227.75 USD); Payout wallet of an unattributed custodial service (1 branches, 867.98 USD); Revolut 6 (1 branches, 260.27 USD); MetaMask: Gas Station (6 branches, 7.17 USD); MetaMask: Swaps Spender (1 branches, 6.93 USD); MetaMask: Gas Station 2 (3 branches, 3.70 USD); Relayer of MetaMask-delegated transactions (2 branches, 1.10 USD).

Exit branches stopped at: Revolut: Hot Wallet (1 branches, 6,893.00 USD); MetaMask: MetaBridge V2 Spender (1 branches, 23.00 USD); MetaMask: Swaps Spender (3 branches, 21.91 USD); Swap Router (1 branches, 9.63 USD); MetaMask: Meta Bridge (1 branches, 8.01 USD); MetaMask: Gas Station Swap (6 branches, 6.52 USD).

### unnamed-0xa8e64a3c

`0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 5,165.00, withdrawals 8,061.90, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1, "WINDOW_SCAN_NEEDED": 3, "DEPTH_BUDGET": 2}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5` | 137 | read through a bridge | 8,061.90 USDC | 8,061.90 | 1 | 2026-10-27 18:49 | `0xf48b2e12dd337fb02173debc38702f38da53d5104da3f1b54117b6c0cca78c91` | LISTED | Relay, same id on both chains |
| `0xc852b0938f5ad79b640d105ed11c14499454af26` | 1 | PERSONAL_SIZED | 5,170.00 USDC | 5,170.00 | 2 | 2026-10-09 20:28 | `0x7e3aecb9b41e6d3f92f25b8760228f15e9b55e798cd27977eb7170445cf64349` | LISTED | direct |
| `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d` | 1 | read through a bridge | 5,165.00 pUSD | 5,165.00 | 2 | 2026-10-09 20:36 | `0x3cd7757ad4fb02e4e30ffdd0ba75575a54c635ca6597bed2a9b6bc0be60cb53a` | REVERIFIED | Relay, same id on both chains |
| `0x6a2522df817c815e293b09c127edf98b6a8a7973` | 1 | PERSONAL_SIZED | 2,501.00 USDC | 2,501.00 | 2 | 2026-10-29 15:43 | `0x0e27a38207cfc2537f73ac1987cea70169d288578784074462017c51e4e6ac2d` | LISTED | direct |
| `0xb42f812a44c22cc6b861478900401ee759ebead6` | 1 | Relayer of MetaMask-delegated transactions | 0.00 ETH | 3.52 | 1 | 2026-10-29 16:33 | `0x11178f7bfeafeb0ddeedecdb4ea0f94397f41db55f1a464de60bd86b066cf3f6` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d` | 1 | read through a bridge | 8,061.90 USDC.e | 8,061.90 | 1 | 2026-10-27 18:49 | `0x09d05d707c4d804dfc86e829f4c1cac90627b7130c54315d16a4d125c207cd3a` | REVERIFIED | Relay, same id on both chains |
| `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5` | 137 | read through a bridge | 5,165.00 USDC | 5,165.00 | 2 | 2026-10-09 20:36 | `0x2e7684ba9eaf5d8632b2ab28e30f79849a00b0ac534917a8b3151b69e43ae209` | LISTED | Relay, same id on both chains |
| `0x74de5d4fcbf63e00296fd95d33236b9794016631` | 1 | MetaMask: Swaps Spender | 3,000.00 USDC | 3,000.00 | 1 | 2026-10-29 16:33 | `0xb53085f7d3391581de0971dfa3443a9fa46750cf18ade7b42413ee8ae9e3d008` | LISTED | direct |
| `0x6a2522df817c815e293b09c127edf98b6a8a7973` | 1 | PERSONAL_SIZED | 2,501.00 USDC | 2,501.00 | 2 | 2026-10-28 14:36 | `0x70217e2085291f617ea70dbdc088b35a9edc1b25471e57e76ad5a00694147a3b` | LISTED | direct |

Funding branches stopped at: SwftSwap (SWFT Blockchain) (3 branches, 10,347.25 USD); ChangeNOW: Hot Wallet 3 (4 branches, 450.78 USD); Measured hub, unnamed (10 branches, 332.56 USD); KuCoin: Hot Wallet (2 branches, 296.39 USD); Binance: Hot Wallet (1 branches, 54.87 USD); ChangeNOW 16 (2 branches, 23.00 USD); Relayer of MetaMask-delegated transactions (3 branches, 4.56 USD); MetaMask: Gas Station (4 branches, 2.11 USD); MetaMask: Gas Station 2 (2 branches, 1.11 USD); Revolut: Hot Wallet (1 branches, 0.05 USD).

Exit branches stopped at: MetaMask: Swaps Spender (1 branches, 3,000.00 USD).

## Documented accounts

### linkcs

`0x0e9310b9a1bf61ff13d5a31e8ca6188abc8ddb0c`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 25,872.60, withdrawals 429.46, residual 0.242847. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"BRIDGE_FAR_SIDE_NOT_READ": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x8db6758f477290b2530bfb6a5d5f11d3b39b822d` | 137 | PERSONAL_SIZED | 25,556.55 USDC.e, 145.47 pUSD | 25,702.02 | 7 | 2026-01-13 17:04 | `0xf295bd6667ef13875c57cf4d1332977741541fdfe754730e4b1e590774e7c4c2` | REVERIFIED | Relay, same id on both chains |
| `0x8db6758f477290b2530bfb6a5d5f11d3b39b822d` | 1 | read through a bridge | 109.47 USDC.e | 109.47 | 2 | 2026-01-13 16:56 | `0xe9dc7b6aa7246ed8c6b67716b0686b2520ce99ef6179b84e6b1d31bfd2c3ca1e` | REVERIFIED | Relay, same id on both chains |
| `bc1qmkfg69t47fh374lr0hudfyze3s9lzuv60psmq8` | 8253038 | read through a bridge | 61.10 USDC.e | 61.10 | 1 | 2026-03-30 10:36 | `0x1706f34505d55178a35433c1e82099f8b5582347faa186c7d41bbbe6288c3611` | REVERIFIED | Relay, API record only |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x13aad1943d6d5bf13cd9f212d3b5bee267988033` | 1 | read through a bridge | 221.51 USDC.e | 221.51 | 5 | 2026-03-23 15:28 | `0x8ae174e76d6779354ff080972f8cda31c3ac89885568deb3aa7a6d6da9c87709` | REVERIFIED | Relay, same id on both chains |
| `EkDy99Z6TeTozDvrEGAGhD7tnBvx4nNb13Toa4yX1ZQP` | 792703809 | read through a bridge | 207.95 USDC.e | 207.95 | 19 | 2026-03-24 09:47 | `0x4e7d499d155a24a818dd8dce56594f94c8abef8bfb74e502362e609676cc8214` | REVERIFIED | Relay, same id on both chains |

Funding branches stopped at: Polymarket Conditional Tokens (CTF) (2 branches, 170,709.79 USD); Coinbase 10 (2 branches, 25,100.00 USD); Measured hub, unnamed (2 branches, 0.13 USD).

Exit branches stopped at: Kraken: Hot Wallet 4 (4 branches, 216.37 USD); Measured hub, unnamed (19 branches, 207.74 USD).

### chiwawas

`0x168b100d7a6620a2f49a455344c2c006eaf1714b`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 47,718.95, withdrawals 82,070.14, residual 2e-06. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"CONTRACT_NOT_IDENTIFIED": 220, "WINDOW_SCAN_NEEDED": 1, "BRIDGE_FAR_SIDE_NOT_READ": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x572441fa356183130b0386de377222d17a7d66a5` | 1 | read through a bridge | 47,718.95 USDC.e | 47,718.94 | 8 | 2025-12-23 02:00 | `0x67fe66b0eae19e04362a1b97be4163ea9be315527b44a1f9e52cc728e506eb45` | REVERIFIED | Relay, same id on both chains |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x44b6f8de91e20953eb2c632062860338154ebe4e` | 1 | read through a bridge | 82,070.14 USDC.e | 82,070.14 | 1 | 2026-01-03 16:49 | `0x9813a40e1c98939cfb67d4a1ac0665a218ad2d89c7024481b330837f91a4e11d` | REVERIFIED | Relay, same id on both chains |

Funding branches stopped at: Measured hub, unnamed (2 branches, 1,011.48 USD).

Exit branches stopped at: Measured hub, unnamed (128 branches, 403,224.46 USD); Binance: Hot Wallet (3 branches, 17,591.11 USD); NEAR Intents (2 branches, 1,268.58 USD); Circle CCTP: Token Minter V2 (4 branches, 360.00 USD); 1inch Network : Aggregation Router V6 (10 branches, 348.91 USD); 0x: Allowance Holder (3 branches, 128.80 USD); Uniswap V3 Positions NFT-V1 (UNI-V3-POS) (5 branches, 14.83 USD).

### burdensome-mix

`0x31a56e9e690c621ed21de08cb559e9524cdb8ed9`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 33,937.08, withdrawals 443,817.59, residual 1e-06. Deposit rows with no path: 85.93 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"CONTRACT_NOT_IDENTIFIED": 6, "AMBIGUOUS_PATH": 1, "DEPOSIT_ROW_NOT_TRACED": 1}. Blocked by data: {"BRIDGE_ID_ABSENT_ON_BOTH_CHAINS": 3}.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `2i7HJJTs8Ht25H8fSjJJSsgGp2HE3umxMrcEa1Cq6hV3` | 792703809 | read through a bridge | 32,610.57 USDC.e | 32,610.57 | 3 | 2025-12-26 21:13 | `0xf064dbbbcab20e018de5f9207f23e6a78d009e150d8a08b8df6eb4908dc13152` | REVERIFIED | Relay, API record only |
| `0x7f4f8ab7809c9b1e6ce14742608cf0f2b50ac473` | 137 | CONTRACT | 1,238.07 USDC.e | 1,238.07 | 1 | 2025-12-31 00:16 | `0x795383b99c7f8654c70504afa563bcc0a53c5bf5495f940f7bad4adb87be0e4a` | REVERIFIED | direct |
| `0xc4d5f64b741d55464250ff1bae7b23742b208814` | 137 | CONTRACT | 1.00 USDC.e | 1.00 | 1 | 2026-01-06 04:51 | `0x1374937e9ef8bf14ed4b0d877bedce740655caf60dd10d76dfc6914f64a8d71c` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `ERKEtTTbZ2WaGUnBAAcTNDpFjukxZUKkrbdhB8Y2SkNN` | 792703809 | read through a bridge | 443,717.59 USDC.e | 443,717.59 | 3 | 2026-01-03 23:54 | `0xbb15de695f711b191732056cb8c170166373a98f889e2e5ea9d40c525917be96` | REVERIFIED | Relay, same id on both chains |
| `2Bk3rxnw8MNqBk5WsYHDwmfDqyqTwijPgQQEJMmFz9A8` | 792703809 | read through a bridge | 100.00 USDC.e | 100.00 | 1 | 2026-01-03 23:50 | `0x55c09ad76bfcba05460c139fe383f2a9f9699ce3b15d92642f56727daeb9ca5a` | REVERIFIED | Relay, same id on both chains |

Exit branches stopped at: Measured hub, unnamed (3 branches, 443,592.82 USD).

### planktonbets

`0x38745db27f7360a287f6ca3c9b6a6a9c76149801`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 26,840.84, withdrawals 200,747.08, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"BRIDGE_FAR_SIDE_NOT_READ": 3, "CONTRACT_NOT_IDENTIFIED": 12}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `TEfE77WkNAzm6DrKhkqd6S9kw53HnqHPS6` | 728126428 | read through a bridge | 17,573.18 USDC.e | 17,573.18 | 2 | 2026-02-18 04:45 | `0x6501eaa46bed63676d207c0e33c133f06bef03ed84ef43444c1c8e84d9674d68` | REVERIFIED | Relay, API record only |
| `0x75db067e953f776d24ba54b64217a168a13ab397` | 1 | read through a bridge | 9,267.66 USDC.e | 9,267.66 | 1 | 2026-02-18 16:00 | `0x1f89497e1d8573d8b7416c34da892d751b9ffb458b0b345229482468e164b030` | REVERIFIED | Relay, same id on both chains |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xe9a7230f874930827b87970a4fbb33a262f02442` | 1 | read through a bridge | 200,747.08 USDC.e | 200,747.08 | 1 | 2026-02-28 09:43 | `0x96774c8c2b6c6a303cf2f00916198a0891abfa6145b6506b7b11cbba6a2e7c98` | REVERIFIED | Relay, same id on both chains |

Funding branches stopped at: Polymarket Conditional Tokens (CTF) (5 branches, 335.16 USD); Measured hub, unnamed (2 branches, 0.03 USD).

### tacticalinsidernews

`0x5621116629c5d640c8186f577362478cc6605245`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 5,513.39, withdrawals 6,500.00, residual 2e-06. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"CONTRACT_NOT_IDENTIFIED": 8, "BRIDGE_FAR_SIDE_NOT_READ": 2}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x5b85645c81b2a768c9919ea54c736ba025b21ece` | 1 | read through a bridge | 5,513.39 USDC.e | 5,513.39 | 3 | 2026-01-03 05:18 | `0x30cfdc253b5f5d86a4ee0c4b4ad8a062798a062744d7d5d548d357399977ea17` | REVERIFIED | Relay, same id on both chains |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x44b6f8de91e20953eb2c632062860338154ebe4e` | 1 | read through a bridge | 6,500.00 USDC.e | 6,500.00 | 1 | 2026-01-14 20:18 | `0x2a1005f27053e974826a2004dd94c72bea541551e0f4dcbf40650a433c695623` | REVERIFIED | Relay, same id on both chains |

Funding branches stopped at: Measured hub, unnamed (1 branches, 0.01 USD).

Exit branches stopped at: Measured hub, unnamed (40 branches, 31,287.58 USD).

### neodbs

`0x56efadc9defe5b7a21af751e0d026f2cf54136db`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 9,883.75, withdrawals 98,837.50, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"BRIDGE_FAR_SIDE_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `TLREUZVRJ9jifQfKvnDMRyXxEhasiGYhP4` | 728126428 | read through a bridge | 9,883.75 USDC.e | 9,883.75 | 1 | 2026-02-26 22:52 | `0xaf44ea53f3c24c292435f88ba2df12c8b60344e75ac87286da6668ad6d84407b` | REVERIFIED | Relay, API record only |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x4e062726688d02cffff7c39918bfb3d4470614eb` | 1 | read through a bridge | 98,837.50 USDC.e | 98,837.50 | 1 | 2026-02-28 10:18 | `0x6182e18523991bed04b1112b8c28316bb7024bbae104862cfcc2e3bad2dd282a` | REVERIFIED | Relay, same id on both chains |

### x34

`0x60280beffdfeaf962de4e6397ab49ed05a1b99e1`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 39,572.24, withdrawals 69,986.11, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"CONTRACT_NOT_IDENTIFIED": 6, "BRIDGE_FAR_SIDE_NOT_READ": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xefaa882c1eb8253a65a3a194f08063693a13f565` | 1 | read through a bridge | 39,572.24 USDC.e | 39,572.24 | 1 | 2026-01-14 20:58 | `0x591af2b2fbe8bb27c3cee254324553a2d63f4f1ccc4b36bca7b24c743a5e2772` | REVERIFIED | Relay, same id on both chains |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xe9a7230f874930827b87970a4fbb33a262f02442` | 1 | read through a bridge | 69,986.11 USDC.e | 69,986.11 | 2 | 2026-01-15 20:51 | `0xd39eda387984257671a70cdb5164ae98a658a74362d5e883c720443e1aa19c13` | REVERIFIED | Relay, same id on both chains |

Funding branches stopped at: Measured hub, unnamed (1 branches, 0.04 USD).

### strong-0x6baf05d1

`0x6baf05d193692bb208d616709e27442c910a94c5`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 25,089.95, withdrawals 166,709.80, residual -3e-06. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1, "BRIDGE_FAR_SIDE_NOT_READ": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x72bf08860e18a46ee020e3a475f8491461903f48` | 1 | read through a bridge | 25,089.95 USDC.e | 25,089.95 | 2 | 2025-12-29 21:31 | `0xcb69aec9bc4c6d503dc2f048391acc874edd589ca60033bee5a2da1477f52fa8` | REVERIFIED | Relay, same id on both chains |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | 137 | Relay EVM solver | 141,709.80 USDC.e | 141,709.80 | 9 | 2026-01-13 16:55 | `0xdc3523d9fc1b0a9bbf13e0d4b31a648d97d15d6523a03806458748edd77d0f8e` | REVERIFIED | direct |
| `0x8db6758f477290b2530bfb6a5d5f11d3b39b822d` | 137 | read through a bridge | 25,000.00 USDC.e | 25,000.00 | 1 | 2026-01-13 17:04 | `0x0368e7cbbf147d8d632026364314f21389ce54e1e981d4fca38525d33969d47c` | REVERIFIED | Relay, API record only |

Funding branches stopped at: Coinbase 10 (1 branches, 100.00 USD); Measured hub, unnamed (1 branches, 0.03 USD).

Exit branches stopped at: Relay EVM solver (9 branches, 141,709.80 USD).

### chileno777

`0x834079f62fa9b4b0bdfad5b8b7a841e8267da024`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 4,994.03, withdrawals 4,161.83, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | 137 | Relay EVM solver | 4,933.37 USDC.e | 4,933.37 | 4 | 2025-12-22 23:43 | `0x39b97ede21077818a05efb52f0591e378434e3c39a527ff5d8ed8fa34ec8cc66` | REVERIFIED | direct |
| `0xa67d7eb4dc68fa6ce8e34ef8cadaf075b9893fbb` | 137 | Relay solver | 60.67 USDC.e | 60.67 | 1 | 2025-12-23 05:28 | `0x2b0b73c90f8ed2225f857489a54c8f5e1e86f43e1c6f3c836253b02454fcb71c` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | 137 | Relay EVM solver | 4,161.83 USDC.e | 4,161.83 | 2 | 2026-01-03 17:07 | `0x3cde2923a7c1fe98e44095ba7d0d4b02d9c27608e6600a73a8e07fab761fb18e` | REVERIFIED | direct |

Funding branches stopped at: Relay EVM solver (4 branches, 4,933.37 USD); Relay solver (1 branches, 60.67 USD).

Exit branches stopped at: Relay EVM solver (2 branches, 4,161.83 USD).

### strong-0xa72db174

`0xa72db1749e9ac2379d49a3c12708325ed17febd4`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 5,782.68, withdrawals 80,764.96, residual 0.0. Deposit rows with no path: 3,424.51 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1, "AMBIGUOUS_PATH": 1, "CONTRACT_NOT_IDENTIFIED": 1, "DEPOSIT_ROW_NOT_TRACED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | 137 | Relay EVM solver | 1,380.11 USDC.e | 1,380.11 | 1 | 2025-12-24 16:33 | `0xb81561a128ef02e9dc53cbe4b166d11145076c63f236d295b0c42ddcea45dd21` | REVERIFIED | direct |
| `0xa67d7eb4dc68fa6ce8e34ef8cadaf075b9893fbb` | 137 | Relay solver | 978.05 USDC.e | 978.05 | 1 | 2025-12-24 20:59 | `0x03210070d13059705067c3b41d2aa08979e9a91306a5d9229179cee2c70bebea` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222` | 137 | Relay v2 Router | 80,764.96 USDC.e | 80,764.96 | 2 | 2026-01-03 20:53 | `0xa4e98a602a8f86a59c44f85591a572cf683134063b7555ce99261347178da2f2` | REVERIFIED | direct |

Funding branches stopped at: Relay EVM solver (1 branches, 1,380.11 USD); Relay solver (1 branches, 978.05 USD).

Exit branches stopped at: Relay v2 Router (2 branches, 80,764.96 USD).

### x154x838hjd6

`0xbf32f7a77ccea8bba647fea63d438ce1778b1762`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 13,642.93, withdrawals 72,897.51, residual 2e-06. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xd4f7d8ac96ed3f467db31fd195faa10676775dab` | 1 | read through a bridge | 9,411.14 USDC.e | 9,411.14 | 2 | 2026-02-28 05:57 | `0x17039631eda3847bd0417a42e2603d42b3f90b682bf56e61092dbbe075e56a9a` | REVERIFIED | Relay, same id on both chains |
| `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | 137 | Relay EVM solver | 4,231.79 USDC.e | 4,231.78 | 2 | 2025-12-30 03:37 | `0x7d6642c83349f8124cfa567a12beed83053dd2f4b827efa1391e34571db8940d` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x44b6f8de91e20953eb2c632062860338154ebe4e` | 1 | read through a bridge | 38,758.52 USDC.e | 38,758.52 | 1 | 2026-02-28 09:36 | `0x6a3f37edfe84882a7191ad522e766f3d8321cbfc245078883f7647172b74a657` | REVERIFIED | Relay, same id on both chains |
| `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | 137 | Relay EVM solver | 34,138.99 USDC.e | 34,138.99 | 1 | 2026-01-03 18:17 | `0xa817144b739cbb15dd34a4ba9c386580cced7fadef3f9e37a78098a4ca315822` | REVERIFIED | direct |

Funding branches stopped at: Measured hub, unnamed (3 branches, 4,233.92 USD); Relay EVM solver (2 branches, 4,231.78 USD).

Exit branches stopped at: Relay EVM solver (1 branches, 34,138.99 USD).

### mrs-joker

`0xe9b80c387ba77a585423b13c850c2e126c3befd8`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 43,625.03, withdrawals 166,364.31, residual 7e-06. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | 137 | Relay EVM solver | 43,625.03 USDC.e | 43,625.03 | 4 | 2026-01-20 20:06 | `0x7c4eae0aec4174fd9715a69af7a12b21422bdd5f17a09eeb6e601bd5935d74a0` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 137 | Relay Depository | 157,086.31 USDC.e | 157,086.31 | 1 | 2026-02-28 09:53 | `0x4a60fcc6d89147cfd0f635fe9b2755575652ac885d3d1922296cb3d4ec26c2c1` | REVERIFIED | direct |
| `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | 137 | Relay EVM solver | 9,278.00 USDC.e | 9,278.00 | 1 | 2026-02-18 15:59 | `0x9388045944b6cf8d42d1fbbb3454f250102b0bd9881e22c0e59ed5492a3ebadb` | REVERIFIED | direct |

Funding branches stopped at: Relay EVM solver (4 branches, 43,625.03 USD).

Exit branches stopped at: Relay Depository (1 branches, 157,086.31 USD); Relay EVM solver (1 branches, 9,278.00 USD).

### nobel-dirtycup

`0x234cc49e43dff8b3207bbd3a8a2579f339cb9867`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 68,504.29, withdrawals 99,138.01, residual 1e-06. Deposit rows with no path: 68,504.29 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1, "AMBIGUOUS_PATH": 2, "DEPOSIT_ROW_NOT_TRACED": 2}. Blocked by data: nothing.

Who paid in, one hop out:

None read at this hop.

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222` | 137 | Relay v2 Router | 99,138.01 USDC.e | 99,138.01 | 1 | 2025-10-10 12:49 | `0xdee0408acc49b3523803b16dc7316424670e2f124991d59f08bc3229323d450c` | REVERIFIED | direct |

Exit branches stopped at: Relay v2 Router (1 branches, 99,138.01 USD).

### nobel-6741

`0xa430506774f9efaf39903ee7e0db1351f66891ca`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 121,086.86, withdrawals 168,236.53, residual -90000.0. Deposit rows with no path: 121,086.86 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1, "AMBIGUOUS_PATH": 4, "CONTRACT_NOT_IDENTIFIED": 61, "DEPOSIT_ROW_NOT_TRACED": 4, "WINDOW_SCAN_NEEDED": 6, "NODE_BUDGET": 689, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222` | 137 | Relay v2 Router | 523,060.18 USDC | 523,060.19 | 15 | 2025-10-10 00:28 | `0x9bed484b7108cd6a1453d8d776e8ad1f29f2b40565da8074fc77c527dffc6375` | LISTED | direct |
| `0x07ae8551be970cb1cca11dd7a11f47ae82e70e67` | 137 | HUB_MEASURED | 249,652.41 USDC | 249,652.41 | 1 | 2025-10-09 22:39 | `0x609bb6181c0f916bd27e934b24c72bedddbc3e1c5f7c3013028b827a4b139ba7` | LISTED | direct |
| `0x3e2c6d068fc6958684e836998285e3a836dbd96f` | 1 | PERSONAL_SIZED | 57.36 ETH | 131,918.98 | 2 | 2025-10-09 22:13 | `0x521010dcebdbb95468792aea68337c599cc5685aa974c1b12454509d6ce4e7b8` | LISTED | direct |
| `0xeff7337b37c8d217d01cb8223fe497abd75190d5` | 1 | HUB_MEASURED | 69,983.21 USDC | 69,983.21 | 1 | 2025-10-10 14:43 | `0x778dce975a92059454edf1e9f84fb319e18ead22a0f5c6b823d3b3fe074721c0` | LISTED | direct |
| `0x71d4249079684479f2651745fa2fcd79c9b45f53` | 137 | HUB_MEASURED | 183.95 POL | 18.40 | 1 | 2025-10-09 22:26 | `0x62278f19c6917f90ad9d384d7062218e9d378013dd48ad4ce4207737a1672106` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xb282b48ae713fa2201282e298f3393130c4f851d` | 137 | PERSONAL_SIZED | 330,191.06 USDC | 330,191.06 | 1 | 2025-10-10 15:29 | `0xa3b2afdee9ce0c39b9dce54f327760fb1c7c43822f94a8901a6262d94ad77463` | LISTED | direct |
| `0x5c7bcd6e7de5423a257d81b442095a1a6ced35c5` | 1 | Across Protocol: Ethereum Spoke Pool V2 | 249,677.38 USDC | 249,677.38 | 1 | 2025-10-09 22:23 | `0xde3c36d433640f1b2e693f7e4619ded6abbaa3f7ac228321b621f7b0b523d53b` | LISTED | direct |
| `0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222` | 137 | Relay v2 Router | 168,236.53 USDC.e | 168,236.52 | 4 | 2025-10-10 00:28 | `0x9bed484b7108cd6a1453d8d776e8ad1f29f2b40565da8074fc77c527dffc6375` | REVERIFIED | direct |
| `0x0000000000001ff3684f28c67538d4d072c22734` | 1 | 0x: Allowance Holder | 57.30 ETH | 131,790.00 | 1 | 2025-10-09 22:20 | `0xc49cede96c20fb850e967fa46a5c8b55fea552d135a820ffaeea48faa17d695b` | LISTED | direct |
| `0x9295ee1d8c5b022be115a2ad3c30c72e34e7f096` | 137 | CONTRACT | 70,000.00 USDC | 70,000.00 | 1 | 2025-10-10 14:42 | `0x708b58858b25ea4cad8987054c11981046071b7758d92244dd5a7c1898755b43` | LISTED | direct |
| `0x234cc49e43dff8b3207bbd3a8a2579f339cb9867` | 137 | CONTRACT | 68,521.54 USDC | 68,521.54 | 2 | 2025-10-10 03:26 | `0x1b6836d22eb515b8eba1f8a5cb9c7c0909ded9519d4b47f63a63d1a6dce12d9e` | LISTED | direct |
| `0x8507124d416dd181ea552e01a0dfed19ab0b1086` | 137 | CONTRACT | 60,000.00 USDC | 60,000.00 | 2 | 2025-10-10 01:46 | `0x36a7fc28b0ade3f6a56b48e716ddaf6a574ff671836919e1df6452875760b1d6` | LISTED | direct |
| `0xb282b48ae713fa2201282e298f3393130c4f851d` | 1 | PERSONAL_SIZED | 39,983.21 USDC, 6.95 ETH | 55,969.07 | 2 | 2025-10-10 15:26 | `0x93083ee195dc1c042549bb9b5c760d6c7afc2b05cfb11e7e4125d1151a592416` | LISTED | direct |
| `0x1973177faa69b94b4afab818e612a7c05b3c01a9` | 137 | CONTRACT | 44,000.00 USDC | 44,000.00 | 3 | 2025-10-10 00:43 | `0xfd981aca74f1b9ae6e9cdb9a726c82d7d3d3a65876ca34b8ae4290562209b838` | LISTED | direct |
| `0x225a38bc71102999dd13478bfabd7c4d53f2dc17` | 1 | Rizzolver: Uniswap X | 30,000.00 USDC | 30,000.00 | 1 | 2025-10-10 14:50 | `0x43cb1aea9db5480993fc80d0206a9513b6dcc574b757468984e8cd28c28b0abb` | LISTED | direct |
| `0x03f8aae7ae1687ef7e2d55e4429e72e9a95d8541` | 137 | CONTRACT | 30,000.00 USDC | 30,000.00 | 1 | 2025-10-10 01:04 | `0x8ccc80d84f4cb1002fd9af6a96da6403fbc718602ee8703e78ddd379068efe36` | LISTED | direct |
| `0x4bac00c61a02275d681f3857cdc5ae315f1f7075` | 137 | CONTRACT | 30,000.00 USDC | 30,000.00 | 1 | 2025-10-10 01:32 | `0xf3366b67b279de1cfea9927defe085b6a8a2706e164361a2c2af529163b12251` | LISTED | direct |

5 smaller addresses are in the JSON.

Funding branches stopped at: Measured hub, unnamed (5 branches, 636,193.02 USD); Relay v2 Router (15 branches, 523,060.19 USD); HitBTC 2 (1 branches, 51,989.52 USD); 1inch: Router 2 (2 branches, 17,485.15 USD); Binance 11 (1 branches, 5,845.80 USD); MetaMask: Swaps Spender (1 branches, 336.86 USD).

Exit branches stopped at: Relay Depository (6 branches, 331,161.35 USD); Across Protocol: Ethereum Spoke Pool V2 (1 branches, 249,677.38 USD); Relay v2 Router (4 branches, 168,236.52 USD); 0x: Allowance Holder (1 branches, 131,790.00 USD); MetaMask: Swaps Spender (4 branches, 40,520.26 USD); Rizzolver: Uniswap X (1 branches, 30,000.00 USD); Swap Router (1 branches, 15,973.60 USD); Uniswap V4: Pool Manager (3 branches, 13,817.65 USD); Chainflip 1 (1 branches, 2,882.51 USD); Measured hub, unnamed (8 branches, 1,745.19 USD).

### iran-0x1caa6a7a

`0x1caa6a7ad0c6916aef7b67946de2e57ad24846a0`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 210,622.44, withdrawals 575,023.74, residual 3e-06. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"TRADING_WALLET_HISTORY_NOT_READ": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | 137 | Relay EVM solver | 210,622.44 USDC.e | 210,622.44 | 10 | 2026-02-25 21:39 | `0x4125280ca43dd8bc87653e40725ad3b0f2233eb934440e40cc43a84188509d4d` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 137 | Relay Depository | 575,023.74 USDC.e | 575,023.74 | 3 | 2026-02-28 11:57 | `0x36eb4a8a59cd1eedb0e278f24a47b6b9cc2a7200a1a883e05cc2de5a6125fbbd` | REVERIFIED | direct |

Funding branches stopped at: Relay EVM solver (10 branches, 210,622.44 USD).

Exit branches stopped at: Relay Depository (3 branches, 575,023.74 USD).

## ChangeNOW

### cn-0x5c1aad9549

`0x5c1aad95490e09b90485903b846940475803346b`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 121.25, withdrawals 0.00, residual 247.659995. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 40, "WINDOW_SCAN_NEEDED": 2, "NODE_BUDGET": 6, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x6321f9f02d9d56261c8c79131ae74d7b427ccaf5` | 137 | HUB_MEASURED | 3,248.24 POL | 324.82 | 1 | 2026-08-02 18:52 | `0x12c7485f2a4712cee4630a1139d1686abb5f4aaea29668e219bda578b9d0a215` | LISTED | direct |
| `0x0782a01b476851a438e1fe179b9542a10027790b` | 137 | read through a bridge | 119.42 pUSD | 119.42 | 3 | 2026-08-05 13:42 | `0x830f346457e5e973f87d335f93b55d823c33040f6817bc2c99a4fb28f39e4be5` | REVERIFIED | Relay, same id on both chains |
| `0xc9aaa6ca0e05b87d53a3e51edbc44b406eeaf299` | 137 | Coinbase 37 | 116.11 USDC | 116.11 | 2 | 2026-08-05 16:49 | `0xbe1acc3a4ead405e6a80787c05668c6aeb3425f1aff4933e9954ca05b6a9cbd4` | LISTED | direct |
| `0xb87a436b93ffe9d75c5cfa7bacfff96430b09868` | 42161 | CONTRACT | 0.03 ETH | 68.08 | 34 | 2026-01-13 03:58 | `0x2ca8330a6c80dad64e088954c6899d9211e60efea62fcb592e5fbc458a59f4be` | LISTED | direct |
| `0xe68ee8a12c611fd043fb05d65e1548dc1383f2b9` | 42161 | Coinbase 3 | 50.00 USDC | 50.00 | 1 | 2026-01-23 02:45 | `0xf8bede1a88135670b6d37ca5335f028f07a43a6484a05843592d0d540eb9e3c0` | LISTED | direct |
| `0x724d8bcec1fb1f34e128e5befef3506fc4d0a2d8` | 137 | read through a bridge | 29.01 USDC | 29.01 | 2 | 2026-01-28 14:22 | `0x377665b8bfc2a51d2ed12f43ddcc92cfdeb06a6ea579e0bab4300e4ca207a069` | LISTED | Relay, same id on both chains |
| `0x5122e9aa635c13afd2fc31de3953e0896bac7ab4` | 10 | Coinbase 39 | 0.01 ETH | 26.50 | 2 | 2026-01-11 21:57 | `0x5dedf1dfba6a2c0018ef16ed3ed1bd2d7000e667697deafa2fe7a6b38db2b54b` | LISTED | direct |
| `0x3eb9845b9c8f835ad130456f8dab6aef79af5272` | 137 | HUB_MEASURED | 19.12 USDC | 19.12 | 1 | 2026-01-23 02:46 | `0x853d080a554adb452bc75abfdc32df780aa5cb4ff3c501f4b19ccfddaa3b6ad9` | LISTED | direct |
| `0xa9d1e08c7793af67e9d92fe308d5697fb81d3e43` | 1 | Coinbase 10 | 0.01 ETH | 18.38 | 3 | 2026-01-11 02:07 | `0x8fdd86a96305fbf6ced928b855089863c6e5b53a088f2ee1b37f66b16d535fff` | LISTED | direct |
| `0x563537412ad5d49faa7fa442b9193b8238d98c3c` | 42161 | Coinbase 4 | 14.63 USDC | 14.63 | 1 | 2026-01-12 06:53 | `0x3a2ebb6155be160b67fe0cae29d08d9f4781c78f6c20bacd0effac4a445f617f` | LISTED | direct |
| `0x19ab546e77d0cd3245b2aad46bd80dc4707d6307` | 137 | Coinbase 17 | 113.77 POL | 11.38 | 1 | 2026-01-24 21:47 | `0x784fb730238429f0f618a9eaca3120f93cc5e645ef4359ee781ffd9d048bf925` | LISTED | direct |
| `0xc8373edfad6d5c5f600b6b2507f78431c5271ff5` | 10 | Coinbase 19 | 9.51 USDC | 9.51 | 1 | 2026-01-24 22:23 | `0x2c258e2220c71657d2ffb7b71448b349384c2850954cfe277fce9072ad2c7471` | LISTED | direct |

10 smaller addresses are in the JSON.

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x0d500b1d8e8ef31e21c99d1db9a7444b2498d60f` | 137 | PERSONAL_SIZED | 3,200.00 POL | 320.00 | 1 | 2026-08-02 19:08 | `0xb749889cef5f3e3be221998b3474a7010d33983ef50e9805f29b64e40b2882c5` | LISTED | direct |
| `0x5c1aad95490e09b90485903b846940475803346b` | 137 | read through a bridge | 0.00 ETH, 119.42 USDC | 121.85 | 4 | 2026-08-05 13:32 | `0x818d31ecc4476c5e11d319e90545ab1b061c55daf0b38bb2d3d45fa323499902` | LISTED | Relay, same id on both chains |
| `0x0d500b1d8e8ef31e21c99d1db9a6444d3adf1270` | 137 | Polygon: WMATIC Token | 35.00 POL | 3.50 | 1 | 2026-08-02 19:25 | `0x0614009088328bbdfaa39252e1814535276d872caf3926d190d6307850c80756` | LISTED | direct |
| `0xcd353f79d9fade311fc3119b841e1f456b54e858` | 137 | CONTRACT | 35.00 WPOL | 3.50 | 1 | 2026-08-02 19:25 | `0x91286bb27363a66a76f74314e44b08285f7ff9701d0463cc5c3a8134a0ecf47d` | LISTED | direct |

Funding branches stopped at: Measured hub, unnamed (5 branches, 369.13 USD); Coinbase 37 (2 branches, 116.11 USD); Coinbase 3 (1 branches, 50.00 USD); Coinbase 39 (2 branches, 26.50 USD); Coinbase 10 (3 branches, 18.38 USD); Coinbase 4 (1 branches, 14.63 USD); Coinbase 17 (1 branches, 11.38 USD); Coinbase 19 (1 branches, 9.51 USD); Polymarket Conditional Tokens (CTF) (2 branches, 4.43 USD); ChangeNOW candidate, unconfirmed (1 branches, 4.31 USD).

Exit branches stopped at: Circle CCTP: Token Minter V2 (1 branches, 5.55 USD); Polygon: WMATIC Token (2 branches, 3.60 USD); Measured hub, unnamed (2 branches, 1.00 USD).

### cn-0x4a4f1fbc70

`0x4a4f1fbc70c61f9a2daee0d8d1974fbe37bc32e0`. Trace **WORK_LEFT**, books **NOT_CHECKED**: deposits 15,089.35, withdrawals 0.00, residual -10738.837283. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "ACTIVITY_LIST_INCOMPLETE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 61, "BRIDGE_FAR_SIDE_NOT_READ": 2, "NODE_BUDGET": 21}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xc417fd8e9661c0d2120b64a04bb3278c17e99db1` | 137 | CONTRACT | 19,497.55 USDC.e | 19,497.55 | 2 | 2026-08-06 12:26 | `0x0cc69817ec03c70a76d6fad35916f384ce075e05fc98393b1899bc6af0e72c39` | LISTED | direct |
| `0xe641cb25842d81fecb622795a9bf6abc1344e25c` | 1 | PERSONAL_SIZED | 7.59 ETH | 17,462.04 | 1 | 2026-08-03 07:10 | `0xa77d11154dc1f8b482feb323eaad2e579afb07367caf847725898a4d8509a31c` | LISTED | direct |
| `0x770c32fd0f64255b6abb564a7ca2b6a091a88f83` | 137 | PERSONAL_SIZED | 15,089.35 pUSD | 15,089.35 | 12 | 2026-08-03 04:45 | `0x3ebcc412df2ef53e361f27a6425dad13469bbb463e8a04955df0258e1c455e81` | REVERIFIED | direct |
| `0x04ecc5ba3258840725fd808be0fae3430b8346f2` | 137 | Midas Capital Exploiter 3 | 13,646.01 USDC | 13,646.01 | 1 | 2026-08-03 07:17 | `0x46a19ccfa3999a131e2ff37fc6a576e25db7ba6c4fea1e9e55d5059465d75c6d` | LISTED | direct |
| `0xca97f5464912ba0308bd40c095bea215980849f6` | 137 | read through a bridge | 8,000.00 USDC, 3,456.64 POL | 8,345.66 | 4 | 2026-08-01 06:16 | `0x5980214520a73d23650815369cf8068e68df0d868832bdf75d365645c4f02a4a` | LISTED | Relay, API record only, Relay, same id on both chains |
| `0x3a3bd7bb9528e159577f7c2e685cc81a765002e2` | 137 | CONTRACT | 1,787.15 USDC.e | 1,787.15 | 52 | 2026-08-01 17:50 | `0xa85743e890910bac2bcdd06a5a9eb1e756ae1664ca01caf6f4ff7f520bfc9e26` | LISTED | direct |
| `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 137 | ChangeNOW candidate, unconfirmed | 245.50 USDC.e | 245.50 | 1 | 2026-08-06 09:28 | `0xade3069a03f5a583cd452670b0fae68100105b4220e82af9ab4b8355de37deef` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb` | 137 | Polymarket pUSD — CollateralToken Poly v2 | 23,696.72 USDC.e | 23,696.72 | 32 | 2026-08-01 06:32 | `0x7bf4b0bf0d6fdc2846ccb86995cb37fcb686b9b04f93211de4630406fdbb1a73` | LISTED | direct |
| `0xd36ec33c8bed5a9f7b6630855f1533455b98a418` | 137 | CONTRACT | 21,646.01 USDC | 21,646.01 | 5 | 2026-08-01 06:29 | `0xfd06aec0056ec16c7bffab54de18ad4be31aea43225783b64a9c6df6c2db05d7` | LISTED | direct |
| `0x424c6c464f9470e90c2647993b8611d58bf454bf` | 137 | PERSONAL_SIZED | 19,477.54 USDC.e | 19,477.54 | 1 | 2026-08-06 12:30 | `0x26e54c542a2ac5af039556dfdb40157beff46e8ef761ffbc34e61a235b8f30f4` | LISTED | direct |
| `0xf09b7e4db41025d949c51e867b36486f5ec57ceb` | 1 | PERSONAL_SIZED | 7.59 ETH | 17,457.00 | 1 | 2026-08-03 07:15 | `0x501bcc6004cf69f10b078839f2e4ae4beb330350afd22131b61bf20c6e8c40c8` | LISTED | direct |
| `0x8bb64c9b388bc1e5ddb58a384707c20bb2473345` | 137 | PERSONAL_SIZED | 3,300.00 POL | 330.00 | 1 | 2026-08-06 09:26 | `0x2746dc69644a3f6797cbb9cb1ceab8943b3afd6f5321e7a6b457fd325179f96b` | LISTED | direct |

Funding branches stopped at: Midas Capital Exploiter 3 (1 branches, 13,646.01 USD); ChangeNOW candidate, unconfirmed (1 branches, 245.50 USD); Relay v3 Router (1 branches, 58.15 USD).

Exit branches stopped at: Polymarket pUSD — CollateralToken Poly v2 (40 branches, 120,918.22 USD); Relay v3 Router (5 branches, 88,302.10 USD); Measured hub, unnamed (1 branches, 17,457.04 USD).

### cn-0xadd9ab62b2

`0xadd9ab62b2c22151c661b99821cbb7433df98df9`. Trace **WORK_LEFT**, books **NOT_CHECKED**: deposits 0.00, withdrawals 0.00, residual 485.986798. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "ACTIVITY_LIST_INCOMPLETE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1}. Blocked by data: {"NO_FUNDER_OBSERVED": 1}.

Who paid in, one hop out:

None read at this hop.

Where it went, one hop out:

None read at this hop.

### cn-0xd18ef9f072

`0xd18ef9f072479d988a70bcbaad93f33781a2a378`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 1,034.88, withdrawals 0.00, residual -99.99936. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 8, "LIGHT_FLOW_CAP": 2, "WINDOW_SCAN_NEEDED": 3, "NODE_BUDGET": 26, "BRIDGE_FAR_SIDE_NOT_READ": 1, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xb81f4236fa866de7594646a0736db696810acadb` | 137 | HUB_MEASURED | 24,901.05 POL | 2,490.11 | 1 | 2026-08-19 21:25 | `0x7522ba2d2a44d73dbd4325245673eb76249ec1364ba7fd4a11a3084be17e6a8a` | LISTED | direct |
| `0x9c0d5847737d4642a1e38cef0ce2d33fef782c5e` | 137 | HUB_MEASURED | 13,979.00 POL | 1,397.90 | 2 | 2026-06-12 19:10 | `0x6057e7ddc805bfd8536afa2e190943506a525905b88ba0ebe89348ef7b93fda8` | LISTED | direct |
| `0x7150ea07d00d8e5a46bcc809f1c9fdf5cb5f8e81` | 137 | CONTRACT | 1,034.88 pUSD | 1,034.88 | 2 | 2026-06-13 15:32 | `0x180874216dffde5184b136eff147f07ea41c1d9b7ca1f34716075ccc0d28eb61` | REVERIFIED | direct |
| `0x51e3d44172868acc60d68ca99591ce4230bc75e0` | 137 | MEXC.com | 645.06 USDC | 645.06 | 1 | 2026-08-14 21:31 | `0x09620ed1dec49f72934b8b4de14466a916d66e0ced8cac23d0f17135081614cb` | LISTED | direct |
| `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 137 | ChangeNOW candidate, unconfirmed | 528.58 USDC | 528.58 | 2 | 2026-07-21 20:47 | `0x176498f0af2bca65d72a9ae5e0e9c6f99c11015a25394efc6c04730de76c06e7` | LISTED | direct |
| `0x83092f58e188df598f9b1f73d804b987f0c83d60` | 137 | PERSONAL_SIZED | 3,759.00 POL | 375.90 | 1 | 2026-06-10 08:09 | `0x0687d3c870ccada0617cabb4a7466f8d8a08cf9b9191049c88fd93447a9587e3` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x8b844f885672f333bc0042cb669255f93a4c1e6b` | 137 | CONTRACT | 16,973.63 POL | 1,697.36 | 3 | 2026-08-19 21:34 | `0x06ae586120086cd7d552b110477162637307ec0ab1d9ec3b12920a801d111a6e` | LISTED | direct |
| `0x32e9e1013f791d5866ad129044315d6c2d381543` | 137 | PERSONAL_SIZED | 1,369.00 USDC | 1,369.00 | 2 | 2026-08-23 19:17 | `0xe0d5f3b061d1d9f0acdef831ef039f7a467a0645e6ad6afcc87110262c0a0d7c` | LISTED | direct |
| `0xd18ef9f072479d988a70bcbaad93f33781a2a378` | 137 | read through a bridge | 13,176.75 POL | 1,317.67 | 1 | 2026-07-05 10:19 | `0xa9c04c42f2220162171a67001eea85520a6494fda469f0586a8fa03d1fa26bb1` | LISTED | Relay, API record only |
| `0x97ccdbea4632140639ad5ea9b944aa034eb15fd4` | 137 | CONTRACT | 855.75 USDC | 855.75 | 2 | 2026-08-14 21:32 | `0x03d5836248c3a7642629e03525486ecb7ec67e9b49f64d595b7d3841da7f9e3e` | LISTED | direct |
| `0x0a59eed84960d2a81fc027279652f6e24c16e33a` | 137 | PERSONAL_SIZED | 4,726.80 POL | 472.68 | 1 | 2026-06-12 19:10 | `0x5540a84c1657460e2637af860dbf1e7b3e7b424ba95f829b116e00fb08fa6712` | LISTED | direct |
| `0xe07681bf80db1f24d4a571bcb28eb80985655561` | 137 | PERSONAL_SIZED | 400.00 USDC | 400.00 | 2 | 2026-08-19 21:39 | `0xd60ca763bdb9e53b037ad3be63a8ec58488fb489620f7cf4b7ea0747d9de8870` | LISTED | direct |
| `0xfc90905645f5d9d1e9046cc90d03f6ee091049ec` | 137 | PERSONAL_SIZED | 3,000.00 POL | 300.00 | 1 | 2026-08-20 15:16 | `0x02ad94e761754046ea4163709cb5f94c3f23767bc55cf53da88c373384b1bfdd` | LISTED | direct |

Funding branches stopped at: Measured hub, unnamed (4 branches, 4,674.11 USD); MEXC.com (1 branches, 645.06 USD); ChangeNOW candidate, unconfirmed (2 branches, 528.58 USD).

Exit branches stopped at: ChangeNOW candidate, unconfirmed (1 branches, 472.68 USD).

### cn-0x391112d827

`0x391112d827116d2b9cc6a079443ea9b3fea51bd7`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 12.525134. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 11, "NODE_BUDGET": 4, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x233c5370ccfb3cd7409d9a3fb98ab94de94cb4cd` | 137 | CONTRACT | 62.23 USDT | 62.22 | 2 | 2026-10-27 01:20 | `0x6a42b51f2731a3065b87243bfa792ffb14acc4b2a3e1a9d31650a1ae9d31ed02` | LISTED | direct |
| `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 137 | ChangeNOW candidate, unconfirmed | 25.40 USDT, 4.08 USDC | 29.48 | 2 | 2026-08-19 21:02 | `0xd1bb7128d48d236cfd1dca1e73608f1711b119d620e80228d93bd006299f2827` | LISTED | direct |
| `0xa65f81eddcf5031e020679b933dc2287868fe59a` | 42161 | HUB_MEASURED | 4.01 USDC | 4.01 | 1 | 2026-08-19 20:51 | `0xa8a88b7d5f8b851ef27bbd404df67d4d254c6553f1ba47d1a3269b3682accb1c` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xfe5e470cd9ab460781c52d49e821523dd5f66dd5` | 137 | PERSONAL_SIZED | 67.33 USDT, 4.08 USDC | 71.41 | 8 | 2026-08-19 21:12 | `0xf86faf9ef6e54e33f938455247ece8d313a1388566e2cec2726c8586ce057a25` | LISTED | direct |
| `0x8ed8ea86a2a95923d25b6769e966c39bdd243492` | 137 | PERSONAL_SIZED | 20.00 USDT | 20.00 | 1 | 2026-11-01 00:25 | `0x1521e67cf3cd06805d9eaed97a4a8b80211d2a0a8e68c7eeeff706390b82d867` | LISTED | direct |

Funding branches stopped at: ChangeNOW candidate, unconfirmed (3 branches, 30.16 USD); Measured hub, unnamed (1 branches, 4.01 USD); ChangeNOW Dep: 0x3f3...07B (1 branches, 0.99 USD).

### cn-0x12852f9976

`0x12852f9976636427bcfcfd3e6309f5d9fcc7539e`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 6.070792. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "LIGHT_FLOW_CAP": 2, "CONTRACT_NOT_IDENTIFIED": 13, "WINDOW_SCAN_NEEDED": 2, "NODE_BUDGET": 38, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x6976d8025229db5f54bc899dd3dbc9285423896b` | 137 | ChangeNOW candidate, unconfirmed | 117.88 POL | 11.79 | 2 | 2026-10-14 13:43 | `0xc700db1cb0a57ec69b527eb633726621a47fa8c3b5084ccba93291e2afa82185` | LISTED | direct |
| `0xf83b85de9763ea8335bb6772b27ef9a0afad3c83` | 137 | CONTRACT | 9.48 USDC.e | 9.48 | 2 | 2026-04-24 11:14 | `0xf9be592e2c8d1b9356787ccfe6e8e7f5109a96959d6123fd5af008de11fac830` | LISTED | direct |
| `0x3a0d24d59af3a3444dc6ef12cdb0c6e38c985288` | 137 | ChangeNOW 6 | 67.21 POL | 6.72 | 2 | 2024-09-11 11:51 | `0x27bf13826e5a334c1cbc68f8a0bf9e75b98c2bf2aac5e385c67472e5bf6d719f` | LISTED | direct |
| `0x2cab3defed9cc52827ecf37536a131c7da6cd5aa` | 137 | HUB_MEASURED | 5.45 USDC.e | 5.45 | 1 | 2026-02-16 15:40 | `0xd8b7cb6e3456e1444464cd6ca008bf8b987ecd701c5c9a62d1e18f37a62b3a30` | LISTED | direct |
| `0xc417fd8e9661c0d2120b64a04bb3278c17e99db1` | 137 | CONTRACT | 5.22 USDC.e | 5.22 | 1 | 2026-05-20 07:21 | `0x0478060dfdc63976207af872b35cbb607440f71b3a4ae17d3082b91b302d2123` | LISTED | direct |
| `0xf3d619f7b10f5fd27545755439288edb8fc406ce` | 137 | PERSONAL_SIZED | 3.99 USDC.e | 3.99 | 1 | 2026-04-02 13:15 | `0x5ad08f12a22d2297c5f2e3570a695dc51f56f2910f5462143c70d1182c561840` | LISTED | direct |
| `0x69c9aab5fd89f75ae64301099e91b77151b63a1d` | 137 | PERSONAL_SIZED | 34.53 POL | 3.45 | 1 | 2024-09-12 15:29 | `0x28691e9d8c93e834a0df5214a55283557a4b829d52f8e4c231a6f28118749e61` | LISTED | direct |
| `0x80743cd0260f42a3cc59fa601a54c626ab5cf03f` | 137 | CONTRACT | 3.37 USDC.e | 3.37 | 1 | 2026-02-18 09:55 | `0x725d9d8dc08d488f55d1e92ec1f2feca70312adcc3d2ec53ca5bf2a6e90533b1` | LISTED | direct |
| `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 137 | ChangeNOW candidate, unconfirmed | 3.30 USDC | 3.30 | 1 | 2026-05-28 10:43 | `0x5bf6a3f79e10cdcc2088f9be38d4a76b670200c39d1fffaedd61ccae3b5aa7ff` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xf83b85de9763ea8335bb6772b27ef9a0afad3c83` | 137 | CONTRACT | 9.00 USDC.e | 9.00 | 3 | 2026-04-02 11:14 | `0xd610c934918a8f9b888c467f8ee0c4507f101fef04081bf57261516a3d38c031` | LISTED | direct |
| `0x97b7b27c4628e5ca7f3a72e5edee585e4d2f490e` | 137 | PERSONAL_SIZED | 73.00 POL | 7.30 | 1 | 2026-10-19 10:39 | `0x1e380a507cc8bfed393e82f997946e3c5b76798d32ae769b40dd992b9037239d` | LISTED | direct |
| `0x0990dbf3a3164e5f6623dd5ffb286f1ce15eef23` | 137 | PERSONAL_SIZED | 5.00 USDC.e | 5.00 | 1 | 2026-04-03 09:54 | `0xe21515c98d19f972a710df199cf7ad9f8ec8d69a1073283503cf46e763720a7e` | LISTED | direct |
| `0xb154b46f42eb3b241f50b190e7e0658eee2f3c12` | 137 | PERSONAL_SIZED | 4.90 USDC.e | 4.90 | 1 | 2026-06-01 07:37 | `0x85d971e31516d208a072690faa37cd5498bfde4ba10185c9dc6acc49995e2f5c` | LISTED | direct |
| `0xf248f452ff5f02e1457a0f5d195c1060c22c0f32` | 137 | PERSONAL_SIZED | 4.90 USDC.e | 4.90 | 1 | 2026-04-06 15:04 | `0xa26994ebef6ffcba7b63ccd66c2625530d129dcae7938d19d7d520530dd18c7e` | LISTED | direct |
| `0xa9e669fe13e8fd512a6fcc85a3ebaed871a04486` | 137 | CONTRACT | 3.17 USDC.e | 3.17 | 1 | 2026-06-02 12:32 | `0xd5bc2589dcdd8c609c83ad2cc2ede7aed8f6a0cc588343443af987102600c31b` | LISTED | direct |
| `0x24a339e647ae43f3964a2204a7acd5c35a8f9197` | 137 | PERSONAL_SIZED | 30.61 POL | 3.06 | 1 | 2026-09-18 14:18 | `0x79528fccb34d6664dd2155dca2d590a0bca340fe244e9b502f4a422a9f436fdc` | LISTED | direct |
| `0xc6cddbb19e7f4891a96cf35438ef3bf3e63a3cf1` | 137 | PERSONAL_SIZED | 3.00 USDC.e | 3.00 | 1 | 2026-04-27 08:55 | `0x13ed1579a692c1440df92947baa48dce64775d64516ea3fe2cb9183e7c1a4111` | LISTED | direct |
| `0x00e8aac7b02a2155ebd5ae225cd1303b53fdd88a` | 137 | CONTRACT | 3.00 USDC.e | 3.00 | 1 | 2026-05-06 08:25 | `0x5225d8083534a2aecc900464c114b73c8d7a67efc75dc30f5947ef5228fd6eca` | LISTED | direct |
| `0x511476b62e2190b26d0c740d208eeccecaf810f3` | 137 | CONTRACT | 2.01 USDC.e | 2.01 | 1 | 2026-05-20 08:02 | `0xfd00bf320fb09cce25369b7643ef5a66a95ee6954528699c91711cdf46213c99` | LISTED | direct |

Funding branches stopped at: ChangeNOW candidate, unconfirmed (3 branches, 15.09 USD); ChangeNOW 6 (3 branches, 10.17 USD); Measured hub, unnamed (1 branches, 5.45 USD).

Exit branches stopped at: ChangeNOW candidate, unconfirmed (1 branches, 7.30 USD); Measured hub, unnamed (1 branches, 5.00 USD).

### cn-0x3067fecf27

`0x3067fecf27edd852bd6f6beae4db025dae5ad85b`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 122.40, withdrawals 0.00, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "WINDOW_SCAN_NEEDED": 2, "LIGHT_FLOW_CAP": 1, "NODE_BUDGET": 28, "BRIDGE_FAR_SIDE_NOT_READ": 3, "CONTRACT_NOT_IDENTIFIED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 137 | ChangeNOW candidate, unconfirmed | 89.79 USDC.e, 35.29 USDC | 125.08 | 5 | 2026-10-20 08:40 | `0x4f8e01881f7c02555050b484093eda31a9372fd7ef3cfea4b0f9384fd513d6d7` | LISTED | direct |
| `0x64e05558bcac6f406466081ae9d2a964835c4d33` | 137 | PERSONAL_SIZED | 122.29 pUSD | 122.29 | 3 | 2026-10-20 10:59 | `0xcfe107931979bfdac414cd396efd6d09cfce90fcc5e96b0ddf4cbd4a35513482` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x3067fecf27edd852bd6f6beae4db025dae5ad85b` | 137 | read through a bridge | 122.29 USDC.e | 122.29 | 3 | 2026-10-20 10:59 | `0xcfe107931979bfdac414cd396efd6d09cfce90fcc5e96b0ddf4cbd4a35513482` | LISTED | Relay, API record only |
| `0xd36ec33c8bed5a9f7b6630855f1533455b98a418` | 137 | CONTRACT | 35.29 USDC | 35.29 | 1 | 2026-10-20 08:45 | `0x3b37b7b334e02b1f5e69c98d116a1c384f438c4706eb6e92f419aa67e0e26040` | LISTED | direct |

Funding branches stopped at: Binance 12 (1 branches, 1,089.56 USD); ChangeNOW candidate, unconfirmed (5 branches, 125.08 USD); Relay EVM solver (1 branches, 0.03 USD); Measured hub, unnamed (1 branches, 0.00 USD).

### cn-0x7678aa83a3

`0x7678aa83a333f333356c04d4faa929d81b2322a3`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 18931.28493. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "CONTRACT_NOT_IDENTIFIED": 2, "DEPTH_BUDGET": 2, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: {"NO_FUNDER_OBSERVED": 1}.

Who paid in, one hop out:

None read at this hop.

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb` | 137 | Polymarket pUSD — CollateralToken Poly v2 | 14,930.86 USDC.e | 14,930.86 | 7 | 2026-08-23 14:40 | `0x152d5490951a7ea9cc88e6abf388775508c6d7101e81c29c9e740490da9f369d` | LISTED | direct |
| `0x2cfd8f89c662d8f7998a338d87b19d02d0069f50` | 137 | PERSONAL_SIZED | 13,123.67 pUSD | 13,123.67 | 1 | 2026-10-30 18:44 | `0x0ff7aa651fc59bd9c465350ae60c4dffa2b42123b15045dcc0868a1a8d9fa233` | LISTED | direct |
| `0xfe0c8cabe3bd6479855fa874f2e6f927b90004b6` | 137 | CONTRACT | 3,300.00 pUSD | 3,300.00 | 1 | 2026-08-31 22:38 | `0xc7ef0a2995b36628f5ea6f800ac8853c14bf6f6b51dc932f02b76c7882829aef` | LISTED | direct |
| `0x8f42ae0a01c0383c7ca8bd060b86a645ee74b88f` | 137 | CONTRACT | 2.00 pUSD | 2.00 | 1 | 2026-08-31 22:36 | `0x3e27028c9f9face6eacdd5b17093b75117285696caeed941af0d146a71df149a` | LISTED | direct |

Exit branches stopped at: Polymarket pUSD — CollateralToken Poly v2 (8 branches, 28,054.53 USD).

### cn-0xa8566ea1e9

`0xa8566ea1e940c1237b844f77e14fc1cb1b2f2278`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 393.252565. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 2, "WINDOW_SCAN_NEEDED": 2, "NODE_BUDGET": 38, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x2df1c51e09aecf9cacb7bc98cb1742757f163df7` | 42161 | CONTRACT | 22.33 USDC | 22.33 | 1 | 2026-10-19 19:56 | `0xfb89d4752c9b057b049682bd5767c224249d88b14bfff59fd0f28f0aa4636357` | LISTED | direct |
| `0x5e90a0a9e20b039311eed7005ee812792ad697d3` | 42161 | PERSONAL_SIZED | 0.00 ETH | 9.71 | 1 | 2026-11-02 08:31 | `0x6690cb92fde16771b2d58728550ed1c8cf4b1de10dfd2708b7d6de8cf8dd9425` | LISTED | direct |
| `0x62dc3784c1c8bad8618665d72422b9b6591f6d91` | 42161 | HUB_MEASURED | 9.25 USDC.e | 9.25 | 1 | 2026-11-02 06:55 | `0x3b47807df4e6290a57b1f9865141d33ec2c7ff8c515702ae91e3a696181f383d` | LISTED | direct |
| `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 137 | ChangeNOW candidate, unconfirmed | 3.35 USDT | 3.35 | 1 | 2026-10-30 18:39 | `0x4b504a8f80a04016fc55e67180ad572255c2ab56428bfef5855866120aeaffdb` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x0daa3b27a76b8e0ff3832705832cf922491c595c` | 137 | PERSONAL_SIZED | 355.00 USDC.e | 355.00 | 2 | 2026-10-30 08:03 | `0xecdf22ea3733b16ea1d0267315aa02a46cf9351889c7d7d5e664d4f7a71cad0a` | LISTED | direct |
| `0x98c593cf775aaf1f54aadc9ef0e77213b6aa178e` | 137 | PERSONAL_SIZED | 33.83 USDC.e | 33.83 | 4 | 2026-10-25 20:14 | `0xda7a3b65db12aaa4ad04d8f5f130bddf2f60289deea6cea4106ee98a2ca15d85` | LISTED | direct |
| `0x39423f9f59200673bad8bef16c0ac16ebc124b4d` | 42161 | PERSONAL_SIZED | 22.33 USDC | 22.33 | 1 | 2026-11-02 07:28 | `0xf410843235fc7ea10ef2fd7f519bf659dc5c29ca2412453ed6c666083aa26f28` | LISTED | direct |
| `0x5e90a0a9e20b039311eed7005ee812792ad697d3` | 42161 | PERSONAL_SIZED | 9.25 USDC.e | 9.25 | 2 | 2026-11-02 07:55 | `0x47465f49ea9399cf79ac195ff0035f9be73004bae40fda1ef108a9e50b281ebd` | LISTED | direct |
| `0x19697cb626b4158559a2ba21c19285a672a1cad0` | 137 | PERSONAL_SIZED | 3.35 USDT | 3.35 | 1 | 2026-10-30 18:42 | `0x3c75c291f56fb4f0a4f894f4de2ff815fd3d7fe33dce6441c3f020f5ba961864` | LISTED | direct |

Funding branches stopped at: Measured hub, unnamed (2 branches, 10.24 USD); ChangeNOW candidate, unconfirmed (2 branches, 3.53 USD).

Exit branches stopped at: Measured hub, unnamed (1 branches, 345.00 USD); Polymarket pUSD — CollateralToken Poly v2 (2 branches, 36.60 USD).

### cn-0xd7e5841553

`0xd7e584155367f9e3082b17c6e02aab5b6cea01a6`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 250.672861. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 3, "WINDOW_SCAN_NEEDED": 2, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xd36ec33c8bed5a9f7b6630855f1533455b98a418` | 137 | CONTRACT | 4,896.93 USDC | 4,896.94 | 3 | 2024-11-13 23:07 | `0x9c45508c1c9de53165c0424aacbb1b9906f9b33fb04ea96df272b45eddbed613` | LISTED | direct |
| `0xdd3d72c53ff982ff59853da71158bf1538b3ceee` | 1 | ChangeNOW: Hot Wallet 3 | 1,702.91 USDC | 1,702.90 | 3 | 2024-10-24 22:02 | `0xeb7e8e86f31b8086068ae5dc7876c3d82020c2fe97490c21c8332601c9b7eeb4` | LISTED | direct |
| `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 1 | HUB_MEASURED | 400.87 USDC | 400.87 | 1 | 2026-08-18 02:40 | `0x8eae6ac448cc8aca2946c00db65e3193009beb0e5660c2c1f05e17686aee8d3a` | LISTED | direct |
| `0xeba88149813bec1cccccfdb0dacefaaa5de94cb1` | 1 | ChangeNOW 16 | 0.01 ETH | 29.00 | 1 | 2024-10-24 22:21 | `0x6c7055c2c45081474092f736a6217fd8a66de5f5bf71c73ef3768f72968f52e9` | LISTED | direct |
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 1 | ChangeNOW Dep: 0x3f3...07B | 0.00 ETH | 2.63 | 1 | 2026-08-18 05:25 | `0x0afbdaf0928dafa8613643f4ee92449b5dc8a8a56861c30753fdafac31d9b923` | LISTED | direct |
| `0x3a0d24d59af3a3444dc6ef12cdb0c6e38c985288` | 137 | ChangeNOW 6 | 24.86 POL | 2.49 | 1 | 2024-11-14 00:19 | `0x034e2158fe6c69b0525c111b76018863b59fb73afea9fa45d1b6ad23cd65353c` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 1 | Relay Depository | 251.00 USDC | 251.00 | 1 | 2026-08-18 05:27 | `0x6170a3fb30c059bebd165eb541b616a2425952ff0bc58099fb22819523f7d600` | LISTED | direct |
| `0xb1f443109ac4877c1cf7b648733a00e3ef353f9c` | 1 | PERSONAL_SIZED | 149.87 USDC | 149.87 | 1 | 2026-10-14 05:36 | `0x12906879b8cdb770c1f7a33c969391a1d402da4e577f42bcabb13da1e0d9074e` | LISTED | direct |

Funding branches stopped at: ChangeNOW: Hot Wallet 3 (3 branches, 1,702.90 USD); Measured hub, unnamed (1 branches, 400.87 USD); ChangeNOW 16 (1 branches, 29.00 USD); ChangeNOW Dep: 0x3f3...07B (1 branches, 2.63 USD); ChangeNOW 6 (1 branches, 2.49 USD).

Exit branches stopped at: Relay Depository (1 branches, 251.00 USD); Measured hub, unnamed (2 branches, 150.09 USD).

### cn-0x6e793da348

`0x6e793da3489cb6f9e0174f8c4e2366b37273dc1f`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 301.247996. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 1 | ChangeNOW Dep: 0x3f3...07B | 0.89 ETH | 2,043.11 | 2 | 2026-08-19 05:33 | `0x4caf23299fce6319d3a4ff215d793e9bcd74d43af88da7b787b970af81be2431` | LISTED | direct |

Where it went, one hop out:

None read at this hop.

Funding branches stopped at: ChangeNOW Dep: 0x3f3...07B (2 branches, 2,043.11 USD).

### cn-0xd67b91b9ce

`0xd67b91b9ce4cb290e5d6ae27e783070a56287a5d`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 430.585788. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "NODE_BUDGET": 22, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x8f54972f4ca40bd3ffc8b085f6ece1739c40c65f` | 1 | changenow | 0.22 ETH | 515.56 | 2 | 2021-01-15 12:13 | `0xc362f9b5877335bb6c72d94a556531da7f1d7f86891ac48f00c58c029184c01f` | LISTED | direct |
| `0x29a2dbc5fad0cb674550428a67143d7722c6c31f` | 10 | HUB_MEASURED | 48.86 USDT | 48.86 | 1 | 2026-07-05 12:05 | `0xfbdf72a99f345123fde9dacd7e3a4fe01057dc6c5129a5a42061886304b63a6b` | LISTED | direct |
| `0xe060e9567040027f805459d9c0d60f1610c70c2a` | 10 | HUB_MEASURED | 0.01 ETH | 29.04 | 1 | 2026-07-05 12:36 | `0x8fa9a9db15de692af8238a275d1cd136838543d563367f75168c1b3bad7ba339` | LISTED | direct |
| `0x077d360f11d220e4d5d831430c81c26c9be7c4a4` | 1 | changenow | 0.00 ETH | 7.53 | 1 | 2021-08-17 03:38 | `0xe14232a098738dfdd16dabb63b5af25ef40f16cdedd4a347f9c53ccc18e4c0c1` | LISTED | direct |
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 1 | ChangeNOW Dep: 0x3f3...07B | 0.00 ETH | 2.38 | 1 | 2026-09-28 11:00 | `0x4b50b183ff384bf3c2d633471d6c3d95494e80eecd1f557a9924741b0861fce2` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x85c7d719a123ebe05a37a0771f984a618e387e9c` | 137 | PERSONAL_SIZED | 350.12 USDC.e | 350.12 | 1 | 2026-08-22 16:55 | `0x0fbbd789f193a2c11cde9e6fb75cb2841214b779bb1d10e9833c8ac8b941c27c` | LISTED | direct |
| `0xda895d0ef80929117831203a627412a6fcc9f440` | 10 | PERSONAL_SIZED | 48.86 USDT | 48.86 | 1 | 2026-07-05 13:00 | `0x76453b8da233edbd1a994f90a8403bc22f6a2dc91fe13ef76593b9259015169c` | LISTED | direct |
| `0xfc2aa3c669b331552a36c004b157fde574016dc2` | 10 | PERSONAL_SIZED | 0.01 ETH | 28.88 | 1 | 2026-08-22 17:01 | `0xed2f7b2f79b707b085721af19f41089739d8f94625ee67e2dc3f2a1f49058802` | LISTED | direct |
| `0xab3ff76b7e5070dfc6fc9c300ef504d357d867b5` | 1 | PERSONAL_SIZED | 0.00 ETH | 3.03 | 1 | 2026-09-28 11:04 | `0x4bc1089fada5bf9c0851860cd843408e77988e77f6618e32e62ad49ba39aeb2f` | LISTED | direct |

Funding branches stopped at: changenow (3 branches, 523.09 USD); Measured hub, unnamed (2 branches, 77.90 USD); ChangeNOW Dep: 0x3f3...07B (2 branches, 3.34 USD); ChangeNOW candidate, unconfirmed (2 branches, 0.78 USD).

Exit branches stopped at: ChangeNOW candidate, unconfirmed (1 branches, 350.12 USD); ChangeNOW Dep: 0x3f3...07B (1 branches, 2.89 USD).

### cn-0x09b831e67e

`0x09b831e67e64c464dc31c4ead793727646e0e5fe`. Trace **WORK_LEFT**, books **NOT_CHECKED**: deposits 227.49, withdrawals 0.00, residual -61.718418. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "ACTIVITY_LIST_INCOMPLETE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "WINDOW_SCAN_NEEDED": 2, "CONTRACT_NOT_IDENTIFIED": 2, "LIGHT_FLOW_CAP": 2, "DEPTH_BUDGET": 9, "NODE_BUDGET": 4}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x371ac9a3c2c208cc75d4e2fd0e7172de5960d4e8` | 1 | read through a bridge | 222.40 pUSD | 222.39 | 12 | 2026-08-20 18:01 | `0x2323f4a7d7ca47d43bec3567b3d1b0fe49ccd544e59ce56f7e2d3a70b22f1cb9` | REVERIFIED | Relay, same id on both chains |
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 1 | ChangeNOW Dep: 0x3f3...07B | 0.08 ETH | 177.64 | 5 | 2026-08-31 19:09 | `0xb61c944b4fa85b0b83271ccd44141841b617ed8c2bc89887bb164fe83b4c00a1` | LISTED | direct |
| `0xeba88149813bec1cccccfdb0dacefaaa5de94cb1` | 1 | ChangeNOW 16 | 0.01 ETH | 33.43 | 2 | 2025-11-16 13:00 | `0x7b77c5e409a06be7db190a28dffeaea060340126b623263b8c9e70ea354c40df` | LISTED | direct |
| `0x43fc1d5bf29f4915c670b803a59d7f9d8bb79b7c` | 1 | HUB_MEASURED | 27.83 USDC | 27.83 | 1 | 2026-09-23 19:15 | `0x9b33284181b97e1461e95172784a1ddb88eef4df13da2deef9f4c4bb3ac53a92` | LISTED | direct |
| `0x53d111557bc0d48ec540fbdca14a1f148cabdb40` | 137 | PERSONAL_SIZED | 5.09 pUSD | 5.09 | 1 | 2026-09-12 00:18 | `0xb3adbceb71e4ef30f120bcc172b25c4688be33ec3f64e52d79764aca908f181c` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 1 | Relay Depository | 0.08 ETH, 28.24 USDC | 215.34 | 12 | 2026-08-20 18:01 | `0xa2ce4fd156eb81ab7334072131d5c031e5cee15b83dbe6b7014205702688fdbc` | LISTED | direct |

Funding branches stopped at: ChangeNOW Dep: 0x3f3...07B (5 branches, 177.64 USD); Measured hub, unnamed (3 branches, 137.83 USD); ChangeNOW 16 (2 branches, 33.43 USD).

Exit branches stopped at: Relay Depository (12 branches, 215.34 USD).

### cn-0xc31ed9f0f0

`0xc31ed9f0f0e1cda74713a0fc51625f530a53a4db`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 15.749762. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "LIGHT_FLOW_CAP": 3, "WINDOW_SCAN_NEEDED": 5, "NODE_BUDGET": 92, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xa6ede2decb8761cf42da78dc82098589372a4357` | 1 | PERSONAL_SIZED | 70.00 USDT | 70.00 | 2 | 2026-07-16 09:09 | `0xb07f72683238b6043a563f0d1e331fbea134ca39d0a3057d038ae33ba9d90aac` | LISTED | direct |
| `0xeba88149813bec1cccccfdb0dacefaaa5de94cb1` | 1 | ChangeNOW 16 | 0.01 ETH | 12.94 | 4 | 2026-02-03 10:12 | `0x8421a1b6226002f504527fd973696837d259282a90b45d7696c834ae919b5566` | LISTED | direct |
| `0x8907d3ad4f672b5f74bdf877071637052f94973d` | 1 | PERSONAL_SIZED | 7.33 USDT | 7.33 | 2 | 2025-11-06 12:15 | `0x5fb07a2cc28bb9c8df89f73ea3a7ca17223840984940e756b75467cfe270af13` | LISTED | direct |
| `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 1 | HUB_MEASURED | 4.01 USDT | 4.02 | 3 | 2026-09-10 09:05 | `0xffcfe3082564241433c02c98e2ae7116a8626e783e790f89e475dd40b1c9073d` | LISTED | direct |
| `0xafbe66947a21960b4d8a2c8f4534983c5dcbc56f` | 42161 | HUB_MEASURED | 0.00 ETH | 3.10 | 1 | 2025-12-02 14:14 | `0x53330486ea76ef6655e78bc62f533119e8cf6713c5929ed7761a60b60a8f390f` | LISTED | direct |
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 1 | ChangeNOW Dep: 0x3f3...07B | 0.00 ETH | 1.25 | 1 | 2026-10-16 13:49 | `0x841ac15fed848c6eebc22891dacdf3d7a347bc579fbd12e2fe23b9789a3889b2` | LISTED | direct |
| `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 137 | ChangeNOW candidate, unconfirmed | 1.12 USDC.e | 1.12 | 1 | 2026-07-10 12:38 | `0x3bb145e0b558d1b318391a7b02b7a3d34d5432e78557d1cde578cc2a495fb4cf` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xa51d4802f3a7f868f17a47f9cc14e99e2fc0a823` | 1 | PERSONAL_SIZED | 6.00 USDT | 6.00 | 1 | 2026-09-18 13:43 | `0x820f37d64f7c379f9254525693a6c6e71e4ea329c8b6a61465bddc819e680876` | LISTED | direct |
| `0xc10c299f26c5d053031ac676d94f4cc851f5d78b` | 1 | PERSONAL_SIZED | 5.00 USDT | 5.00 | 1 | 2026-07-31 09:58 | `0xe4f30b37f597178948e57ed29c773a413b7a4443aca9b1dbcb519ce77151da4a` | LISTED | direct |
| `0x6fa6a751a79194c3abe437d359d8960dc85d9ec7` | 1 | PERSONAL_SIZED | 5.00 USDT | 5.00 | 1 | 2026-09-14 08:48 | `0x8c59441be2b98493a1a992d422ac59ed86487ceea2e1a729646b78ed8117893a` | LISTED | direct |
| `0x57ab5bae2bfabf1a6be2f728782d35c7dda8b69e` | 1 | PERSONAL_SIZED | 4.00 USDT | 4.00 | 1 | 2026-09-25 10:14 | `0xa3934f6946d0a10274f13ecdfd8437cb313b6689c3784757da470928f10c36f9` | LISTED | direct |
| `0xb1c54624caf9b15899e5916ed64326107f537d64` | 1 | PERSONAL_SIZED | 2.50 USDT | 2.50 | 1 | 2026-09-28 14:02 | `0xde57a0608f77f1083c9a617ad849301862d2f75b97b3b857bbbfc5eca459c18a` | LISTED | direct |
| `0x7ad03c40cc336f6ff9c9ef6948354dfae73bc46c` | 1 | PERSONAL_SIZED | 2.21 USDT | 2.21 | 1 | 2026-10-05 10:58 | `0x2efd8699adb199c6856ef53aee70614d1301d6573669eef4410fe4388953f0c5` | LISTED | direct |
| `0x6fc3a50668297ba6522ca320048d21789fe0a6c4` | 137 | PERSONAL_SIZED | 2.12 USDC.e | 2.12 | 1 | 2026-07-10 12:46 | `0x8ecb812594e4d5e8cc19e748e52f9ede82c9412f6df5f4a905a490893fefe9ea` | LISTED | direct |
| `0x202a622bcb1b25c805e52c1b39ea56d6535de14c` | 1 | PERSONAL_SIZED | 2.00 USDT | 2.00 | 1 | 2026-09-01 10:49 | `0xbff6648e69a84749ede8252b26aa263051be3fb55cb6a46688a415d1dd9f3392` | LISTED | direct |
| `0x90e9590540ed13cd98edc9b74bb5830e2c3976bb` | 1 | PERSONAL_SIZED | 2.00 USDT | 2.00 | 1 | 2026-09-01 11:25 | `0xc1756e2dad1dc650bd265fadecc929608253b8914ccf766003f1f80bef6de13c` | LISTED | direct |
| `0xea91021e777550d79f14a59c4682a66f27fe8f0d` | 1 | PERSONAL_SIZED | 2.00 USDT | 2.00 | 1 | 2026-09-02 09:35 | `0x5e193ae3885398a1f9d46d4860881eb09540803b81cb45021f4fa410fb066837` | LISTED | direct |
| `0x32ceebb2916b8e4ece121dd2b44685f49f2c1167` | 1 | PERSONAL_SIZED | 2.00 USDT | 2.00 | 1 | 2026-09-02 13:25 | `0xcc59325e997330753a2f67ddb31e05d127ee581ab9c5325804ed8407d5e81ce9` | LISTED | direct |
| `0xf6fd3eb1b89b470db948f3457f07762d8a3d0e6a` | 1 | PERSONAL_SIZED | 2.00 USDT | 2.00 | 1 | 2026-09-02 14:55 | `0x2430bb11fbdb83f2508de0249448e3587d573a0e4eb1bee1f97090302e5da548` | LISTED | direct |

1 smaller addresses are in the JSON.

Funding branches stopped at: ChangeNOW: Hot Wallet 3 (4 branches, 38,912.31 USD); Measured hub, unnamed (5 branches, 37.89 USD); ChangeNOW 16 (5 branches, 13.29 USD); Poloniex 7 (1 branches, 7.33 USD); ChangeNOW candidate, unconfirmed (2 branches, 1.59 USD); ChangeNOW Dep: 0x3f3...07B (1 branches, 1.25 USD).

Exit branches stopped at: Measured hub, unnamed (3 branches, 8.10 USD); ChangeNOW: Hot Wallet 3 (1 branches, 5.00 USD); Relay Depository (1 branches, 2.00 USD).

### cn-0xe0bf7ab5b1

`0xe0bf7ab5b11dcbdbb169638cacf43edaa540d7fe`. Trace **WORK_LEFT**, books **NOT_CHECKED**: deposits 67,600.00, withdrawals 5,113.00, residual -50.635906. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "ACTIVITY_LIST_INCOMPLETE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 5, "WINDOW_SCAN_NEEDED": 3, "LIGHT_FLOW_CAP": 1, "DEPTH_BUDGET": 2, "NODE_BUDGET": 8}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x833ded6040a7887f55ed9c164c7099dde1996120` | 137 | PERSONAL_SIZED | 67,600.00 pUSD | 67,600.00 | 12 | 2026-05-19 01:52 | `0xba722038df50dee30ced2b5da12783ae4336b5999ed34ca263a8723c76138899` | REVERIFIED | direct |
| `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 1 | HUB_MEASURED | 25,612.43 USDC | 25,612.44 | 4 | 2026-09-18 14:36 | `0x5a58a99ed82dcf02bac8b0d4477fb1d1ece611f40197f6d1b8d175664e4d9c94` | LISTED | direct |
| `0xe0bf7ab5b11dcbdbb169638cacf43edaa540d7fe` | 137 | read through a bridge | 17,259.87 USDC | 17,259.87 | 1 | 2026-09-18 15:36 | `0xbc2969239d35246f3d62c7d3bce012ee47019f601078059debc6b15d2fc63621` | LISTED | Relay, same id on both chains |
| `0x4e5b2e1dc63f6b91cb6cd759936495434c7e972f` | 1 | HUB_MEASURED | 2,812.21 USDC | 2,812.21 | 1 | 2026-09-18 20:08 | `0xd35672c6467950729914ec13b2b8a8914bfc54f5ecd63cc44381e732ae21ffc4` | LISTED | direct |
| `0x1f8e735f424b7a49a885571a2fa104e8c13c26c7` | 1 | CONTRACT | 33.79 USDC | 33.79 | 1 | 2026-10-21 08:11 | `0xf4a0a3d3a744cb39b8298f9dd61eb4ff7edc48a77f09841a9b603cbf6d86eb4e` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xbd8d892efa790742d81f642b2d55096387411efe` | 1 | PERSONAL_SIZED | 45,684.51 USDC | 45,684.50 | 2 | 2026-09-18 16:02 | `0xc2eddcaa945a66344893800fe9d011f0ebedb4d885651f8ac2358667f2f9f51c` | LISTED | direct |
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 137 | Relay Depository | 5,113.00 USDC.e | 5,113.00 | 2 | 2026-08-22 13:47 | `0x02f3ca98cca53f10ade10874a8918e16136f58350e5ad56a3716cdf282385118` | REVERIFIED | direct |
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 1 | Relay Depository | 32.79 USDC | 32.79 | 1 | 2026-10-21 08:16 | `0x556aa376d1a23d5175175368e8859916ea677cd15484958f11fc786bb8bc503e` | LISTED | direct |

Funding branches stopped at: Compound: USDCv3 Token (4 branches, 986,486.83 USD); Aave: USDC V3 (2 branches, 381,923.06 USD); Compound: cUSDC Token (1 branches, 117,004.10 USD); Measured hub, unnamed (5 branches, 28,424.65 USD); ChangeNOW Dep: 0x3f3...07B (1 branches, 0.75 USD).

Exit branches stopped at: Compound: USDCv3 Token (6 branches, 109,833.50 USD); Relay Depository (3 branches, 5,145.79 USD); Measured hub, unnamed (1 branches, 662.49 USD).

### cn-0x55bb88498e

`0x55bb88498ecee0369bf77e45e04ca37eaf4270d3`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 4,989.94, withdrawals 894.18, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 1, "NODE_BUDGET": 4}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 1 | ChangeNOW Dep: 0x3f3...07B | 2.61 ETH | 6,007.00 | 1 | 2026-09-19 22:27 | `0x3956d68ecdd73716e57f2e72e597cbc54a699fc389af9520c00ba43b1c4e724f` | LISTED | direct |
| `0xfe04198b251d06e455d6cbb904811230d96eed12` | 137 | PERSONAL_SIZED | 4,989.94 pUSD | 4,989.94 | 1 | 2026-10-26 01:25 | `0x6f56f94acc9040042641954ffcc19025903b511e4d0be0ecc62761f65901eab7` | REVERIFIED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 137 | Relay Depository | 894.18 USDC.e | 894.18 | 1 | 2026-10-26 15:38 | `0x5d51232d1fc3ddbedf0fdd02c7c0b868b053766d15a68d94decd62cdfb615e87` | REVERIFIED | direct |

Funding branches stopped at: ChangeNOW Dep: 0x3f3...07B (1 branches, 6,007.00 USD); Relay EVM solver (1 branches, 4,989.94 USD).

Exit branches stopped at: Relay Depository (1 branches, 894.18 USD).

### cn-0xd55776adc3

`0xd55776adc38f23659a0e8853ea73f4e7f2d756d6`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 498.008616. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 5, "WINDOW_SCAN_NEEDED": 2, "LIGHT_FLOW_CAP": 1, "NODE_BUDGET": 34, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xfb19ffd1ff9316b7f5bba076ef4b78e4bbedf4e1` | 1 | HUB_MEASURED | 4.03 ETH | 9,269.08 | 1 | 2026-10-14 16:29 | `0x3980d366ef0f0ea6a38407e5cd1382c2ae30f62e82fba81afe8d0c0624944bcb` | LISTED | direct |
| `0x963737c550e70ffe4d59464542a28604edb2ef9a` | 1 | Union Chain | 2.33 ETH | 5,354.63 | 2 | 2026-10-19 23:11 | `0xf05426026004fbdbbd841fac82bf29845770dd25f58b11ce24de4e653af3edb6` | LISTED | direct |
| `0xbc1d9760bd6ca468ca9fb5ff2cfbeac35d86c973` | 1 | CONTRACT | 2.23 ETH | 5,126.00 | 1 | 2026-10-30 02:00 | `0x647d93d29d31ddd1f859b624fd750679ac24e6fac4eef866135b85b555751ed5` | LISTED | direct |
| `0x1231deb6f5749ef6ce6943a275a1d3e7486f4eae` | 1 | CONTRACT | 1.27 ETH | 2,916.00 | 1 | 2026-10-30 00:13 | `0x85bc0f3454d73c0be88cbc98c79039d8e1d4f535948b36e3ccae43aa6084a764` | LISTED | direct |
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 1 | ChangeNOW Dep: 0x3f3...07B | 0.01 ETH | 15.87 | 1 | 2026-09-27 23:45 | `0x876fd12490f55901845cf3203c6a3d7eca745e361b8de25d4b4239e459dc4aae` | LISTED | direct |
| `0x51dbd97fa14f4d78f8afc2e92a692a9e087efb5c` | 1 | HUB_MEASURED | 0.00 ETH | 8.26 | 1 | 2026-09-27 08:31 | `0x17fd728e2d09d11ee085eee6a3fb83b825a1b4767c0eded5cd65409c9bc8644e` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xa1a28d413d29ecd433b77493511a8744cc4014a1` | 1 | PERSONAL_SIZED | 0.47 ETH | 1,084.48 | 2 | 2026-10-23 13:39 | `0xca81f8a7f94fd2eed1a56fa8358ccab5536727604113635127d1aca0f68049f9` | LISTED | direct |
| `0xbc1d9760bd6ca468ca9fb5ff2cfbeac35d86c973` | 1 | CONTRACT | 0.21 ETH | 478.82 | 1 | 2026-10-23 20:58 | `0x3dfc9945fdcbe670f00a1cefca3593999b1e647cdbd8c3dd584e3e8d3effedcd` | LISTED | direct |
| `0xb92fe925dc43a0ecde6c8b1a2709c170ec4fff4f` | 1 | Relay v3 Router | 0.08 ETH | 191.53 | 1 | 2026-10-23 20:58 | `0x21121bdc3b258e872038bc6062516dfc66b13ad6ee1d9a705f9ab953e1c6cf49` | LISTED | direct |
| `0x5b8d2b4acbc8021f38f63ae67b6dd24b4dfca066` | 1 | HUB_MEASURED | 0.02 ETH | 50.14 | 3 | 2026-10-15 14:32 | `0x5e4417ad8d5e8ed50714f5c2f1c28d6fc20899aa45d0339081fab12b0d73b214` | LISTED | direct |
| `0xd9771273a4bfde3493f61e2c449a2b1a36aec9e9` | 1 | PERSONAL_SIZED | 0.01 ETH | 20.52 | 1 | 2026-10-30 04:38 | `0x5eb84a76e1267d05f01f30213d89aae4d0b69bba80f49a73d135f48052bed278` | LISTED | direct |
| `0x8742cfa8297dd2dde8bb4a91542c213c2097e8f4` | 1 | PERSONAL_SIZED | 0.01 ETH | 20.45 | 1 | 2026-11-02 17:54 | `0xccd32001dfd7d36e45f0bba7a63b810170ccb355c00cfd1cd64c1d3ade2ae530` | LISTED | direct |
| `0x20bf27fa150688f6e8126a256a304f48315d45b8` | 1 | PERSONAL_SIZED | 0.01 ETH | 20.38 | 1 | 2026-11-01 00:44 | `0x3602c426fb7bdcec6f9b95e9abd401fd66ad2ab8086b4a4dabc870add846dc9b` | LISTED | direct |
| `0xbace509bbdc41f76e0c3abeb412c2fdc0d4bf8fa` | 1 | PERSONAL_SIZED | 0.01 ETH | 20.36 | 1 | 2026-11-01 23:01 | `0x3eaae1e0114d6a4b409380bdf06dd20d3e0d8419fa76c080ad6a5f6c4616c673` | LISTED | direct |
| `0xbbc9787074b3416cc2715ae22c050539d1e83810` | 1 | PERSONAL_SIZED | 0.00 ETH | 10.19 | 1 | 2026-11-03 01:14 | `0x18a27aa55e013d9877b79d8edfdf017e05de80e4900cf05a9dd5cfd3fadc8f17` | LISTED | direct |

Funding branches stopped at: Measured hub, unnamed (2 branches, 9,277.34 USD); Union Chain (2 branches, 5,354.63 USD); ChangeNOW Dep: 0x3f3...07B (1 branches, 15.87 USD).

Exit branches stopped at: Relay v3 Router (1 branches, 191.53 USD); Measured hub, unnamed (3 branches, 50.14 USD); ChangeNOW Dep: 0x3f3...07B (1 branches, 20.38 USD).

### cn-0x19bb95ea82

`0x19bb95ea829511f4c0056a9b7024ddef1e272ff0`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 48.956119. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 1, "WINDOW_SCAN_NEEDED": 2, "NODE_BUDGET": 50, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xeba88149813bec1cccccfdb0dacefaaa5de94cb1` | 1 | ChangeNOW 16 | 0.06 ETH | 143.85 | 1 | 2026-08-07 11:12 | `0x8d62c85e499b28508245c9c6262b7294ff4eb6606ca067499423fcd97f7b5289` | LISTED | direct |
| `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 1 | HUB_MEASURED | 143.25 USDC | 143.26 | 4 | 2026-08-18 14:15 | `0x6034b4c226a6515fe2e6fe2b17659fdbf39716db9bac478d16bad946da4664e4` | LISTED | direct |
| `0x2df1c51e09aecf9cacb7bc98cb1742757f163df7` | 42161 | CONTRACT | 49.00 USDC | 49.00 | 1 | 2026-10-01 10:08 | `0xd80f2fd0539e457d93caf59666f7ab42ad5919ea55e6102e05a9ca00989811b1` | LISTED | direct |
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 1 | ChangeNOW Dep: 0x3f3...07B | 0.02 ETH | 40.82 | 2 | 2026-10-13 10:11 | `0x772f518018cbc0bb4d4e5a412eab399475fec051d5df69cb159177f2f0384829` | LISTED | direct |
| `0x77184e9136525a724b34efdbf9bf87b3c251f9f1` | 1 | PERSONAL_SIZED | 0.02 ETH | 40.20 | 1 | 2026-09-28 17:10 | `0x5d3cb019c32b23252415339c7d3e61cd36c7c9893ed8fcea852a8e4d7ffc0fa2` | LISTED | direct |
| `0x390aeb31f09e12b9212c9aeb7b5299da4bf34268` | 1 | PERSONAL_SIZED | 0.00 ETH | 8.46 | 1 | 2026-10-12 17:16 | `0xf1a74e0d90e74a3ca42489a8c3416ca863554b42d55b04721fa032bfddc268d1` | LISTED | direct |
| `0xe94667d85ae6050dbb41e63109bc303759876cba` | 42161 | HUB_MEASURED | 0.00 ETH | 3.89 | 1 | 2026-10-01 10:13 | `0x26b8206cb06044904ca0a0780f9a7133b2e2fba0e1a17ac3446d219895caefc0` | LISTED | direct |
| `0x6dce8cbcfe8b1e9ae5c61463e2878bd2acf75d96` | 1 | PERSONAL_SIZED | 0.00 ETH | 1.20 | 1 | 2026-08-18 16:09 | `0x792896c77778a5d46d670f83f42553d0f0a577508ad4cc27d863df13159a82b5` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 42161 | Relay Depository | 49.00 USDC | 49.00 | 1 | 2026-10-01 10:13 | `0x4c0ddd62a9e9b2f4ec7df1041b5a16aad4e0d84f42a94d94b0e970982f3756ac` | LISTED | direct |
| `0x3db2506edaf2ddc0364a145713bfb3649e54b750` | 1 | PERSONAL_SIZED | 41.95 USDC | 41.95 | 1 | 2026-10-13 10:09 | `0x130c1dd3a681dc037edc778098a6a4a1caf04e464eb80f1e028ed886cd3055ce` | LISTED | direct |
| `0xa11bacf5be1f7cd56f5c6d8abbb0bff2cc2c3eb5` | 1 | PERSONAL_SIZED | 0.02 ETH | 36.80 | 1 | 2026-10-01 10:07 | `0x0f21c94ee52bfc4a2dd5aa4a58e06710556f624125906bc6fd2ef86271a93382` | LISTED | direct |
| `0xe843841d72359dae1be9d81200d794a8d8d78b45` | 1 | PERSONAL_SIZED | 0.01 ETH | 14.72 | 1 | 2026-10-28 14:43 | `0x9c0ac229b2e52509ac7d87ca9dc616c73e99d3e2f787314f4e14ea889678e884` | LISTED | direct |
| `0x15e1ac645de291eda6853760b6f2d76785348163` | 1 | PERSONAL_SIZED | 0.00 ETH | 9.73 | 1 | 2026-10-30 13:57 | `0x3ad220bd18b49679d1ab9fbeeb46cde5b57f79f46be5a7248fb2a54437b0d4df` | LISTED | direct |
| `0x0314cd9acdbd7e4eda76c41e5e1b1e83318f910a` | 1 | PERSONAL_SIZED | 0.00 ETH | 7.89 | 1 | 2026-10-28 14:20 | `0x0787ae64907713b292c37b4c247ea9389403b6a23c496e5477f8c46943b58f0a` | LISTED | direct |
| `0x710754204b80ffb52cecbfafa84cf7d057d96462` | 1 | PERSONAL_SIZED | 0.00 ETH | 4.83 | 1 | 2026-10-28 10:21 | `0xfe53139f5c66a56978d4cf7b9e9cac47b7ee9c1e4f6d10ad92bc43693169fee7` | LISTED | direct |
| `0xd8d1444a7f908315162b1b1cb0658df65e300632` | 1 | PERSONAL_SIZED | 0.00 ETH | 4.22 | 1 | 2026-10-01 10:11 | `0x96c24767d9303b8dc2e5266304d17b4bf533a4ac7c6e94ed2d7a9dba1338aa8d` | LISTED | direct |
| `0x7a771893e430d1811a31a727c6f0f6cb9f24cc11` | 42161 | PERSONAL_SIZED | 0.00 ETH | 3.79 | 1 | 2026-10-13 10:33 | `0x9ff61ddf033a7bd3dc827261968c88c191fc036a57116299e7b9ecd27c8e6a18` | LISTED | direct |

Funding branches stopped at: Crypto.com 2 (3 branches, 2,854.85 USD); Measured hub, unnamed (7 branches, 155.84 USD); ChangeNOW 16 (1 branches, 143.85 USD); ChangeNOW Dep: 0x3f3...07B (2 branches, 40.82 USD); Revolut 6 (1 branches, 40.34 USD).

Exit branches stopped at: Relay Depository (1 branches, 49.00 USD); Measured hub, unnamed (2 branches, 42.17 USD); ChangeNOW Dep: 0x3f3...07B (1 branches, 36.66 USD).

### cn-0xdec4c18831

`0xdec4c188314de225a81c7ada6cadb26daefd2402`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 259.775641. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "WINDOW_SCAN_NEEDED": 2, "NODE_BUDGET": 22, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x75405ae639ac565720b1b3075d5c7cd5abcb9c06` | 1 | HUB_MEASURED | 0.64 ETH | 1,471.97 | 1 | 2020-06-19 07:07 | `0xde347c0011c857fbd79fbc8b8c209502b939d34569305aa1eab5567c315d77e8` | LISTED | direct |
| `0xaaa1daa59d0f89426430af3a48480dd34ef1bf56` | 1 | PERSONAL_SIZED | 0.29 ETH | 660.42 | 1 | 2020-05-10 01:56 | `0x024c60eb474a84823815a0c5551874fa25968c2c672c926e1896b98a30c1845b` | LISTED | direct |
| `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 1 | HUB_MEASURED | 143.56 USDC | 143.56 | 2 | 2026-10-25 14:46 | `0xd749ae422fb30d57bce1d98441bdae315362ac8b3d6b5337d01364f48fe0f7f9` | LISTED | direct |
| `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 1 | ChangeNOW Dep: 0x3f3...07B | 0.02 ETH | 50.64 | 3 | 2026-10-25 00:10 | `0xbddbcd841a66caa8af51c4b42147627216615d98b4468653a0e415b3a06ee844` | LISTED | direct |
| `0xde4cae36b13bb4e2f273c6cdeb60a0076553dc33` | 1 | HUB_MEASURED | 0.02 ETH | 41.37 | 1 | 2020-05-10 02:16 | `0x33e76ed3977d4b951332beed805c6d182e60dbb1f26de312039ea721f945fe35` | LISTED | direct |
| `0xdd3d72c53ff982ff59853da71158bf1538b3ceee` | 1 | ChangeNOW: Hot Wallet 3 | 10.81 USDT | 10.81 | 1 | 2026-07-13 07:44 | `0x2f4404de9f580104c2f4f38170a40b6cc95c606ebf92e9a62c30a0167a367d98` | LISTED | direct |
| `0x54ee244363c2ab17e801b7a089f794eae743213a` | 1 | PERSONAL_SIZED | 5.09 DAI | 5.09 | 1 | 2020-05-10 01:45 | `0xe32a16822515b2dd46ffa3a956526db9991234e40cf7cb2e11533319d1c269c2` | LISTED | direct |
| `0xeba88149813bec1cccccfdb0dacefaaa5de94cb1` | 1 | ChangeNOW 16 | 0.00 ETH | 1.11 | 1 | 2026-07-13 12:27 | `0xdade0bba0aa0cd544d78ad12e52f3717fa6e122f00f882be64a1309d26649ad8` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 1 | Relay Depository | 144.00 USDC, 10.80 USDT | 154.80 | 2 | 2026-07-13 12:38 | `0x736f1cb7ced46ea0b5ad25ac2eea19183bebdea951a633c532b89abfab6064b9` | LISTED | direct |
| `0x2e9f6b52537364283ccb572a524e8eeb06222577` | 1 | PERSONAL_SIZED | 0.02 ETH | 36.35 | 1 | 2026-10-25 10:51 | `0x85ac74e3f9dc1d0016d6f04f904333005a0eedff2d13154775fcd980386b7cc9` | LISTED | direct |

Funding branches stopped at: Measured hub, unnamed (4 branches, 1,656.90 USD); ChangeNOW Dep: 0x3f3...07B (3 branches, 50.64 USD); ChangeNOW: Hot Wallet 3 (1 branches, 10.81 USD); ChangeNOW 16 (1 branches, 1.11 USD).

Exit branches stopped at: Relay Depository (2 branches, 154.80 USD); ChangeNOW Dep: 0x3f3...07B (1 branches, 36.21 USD).

### cn-0xd55dad050d

`0xd55dad050daeedcf9ca1236ab50b649f6ad1612e`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 13.330123. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "NODE_BUDGET": 4, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x9696f59e4d72e237be84ffd425dcad154bf96976` | 1 | Binance: Hot Wallet | 0.01 ETH | 17.09 | 1 | 2026-08-11 18:36 | `0xedc5c2f53774a03547bfe519d593ab409cea80e43133df18bd092b6f63dfed12` | LISTED | direct |
| `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 1 | HUB_MEASURED | 13.38 USDT | 13.38 | 1 | 2026-08-11 18:39 | `0xfaf1aa580c8aa671af7bbc904fae3247345d249831562c40bf7915eb631b43f4` | LISTED | direct |
| `0x1de9873b76a4277ed1526ff23c6acbe6f9d2c96b` | 1 | PERSONAL_SIZED | 0.00 ETH | 3.44 | 1 | 2026-08-11 18:49 | `0x5a1a0bc31eed1a3ed2d09c65494194392976d592f73e53984f0f7544704d83da` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xb9d035c3c6a9e20f0a91f50e53209b8726adc8f7` | 1 | PERSONAL_SIZED | 0.01 ETH | 17.05 | 1 | 2026-08-11 18:37 | `0x9655e5a39d59abfb262a49ad1ecb14648be30843b9f86bd2fa55438c8262d9fe` | LISTED | direct |
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 1 | Relay Depository | 13.38 USDT | 13.38 | 1 | 2026-08-15 20:00 | `0xe7aef36b7b10982838e52ba357a919bab53b80931e174b9180e6f0f6e112aa64` | LISTED | direct |

Funding branches stopped at: Measured hub, unnamed (3 branches, 100.08 USD); Binance: Hot Wallet (3 branches, 92.15 USD); Binance 17 (1 branches, 38.80 USD).

Exit branches stopped at: ChangeNOW Dep: 0x3f3...07B (1 branches, 16.91 USD); Relay Depository (1 branches, 13.38 USD).

### cn-0x814fd93538

`0x814fd935380361956828ec5e176ee9e7ea19a031`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 30.681574. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 1, "NODE_BUDGET": 4, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x56eddb7aa87536c09ccc2793473599fd21a8b17f` | 1 | Binance 17 | 0.02 ETH | 38.80 | 1 | 2026-08-11 18:37 | `0x4375fa5405a7d47aa1b3ac07d06867ed9422898413d64651efd15cb3e0e2b0c6` | LISTED | direct |
| `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 1 | HUB_MEASURED | 30.75 USDT | 30.75 | 1 | 2026-08-11 18:41 | `0x725cda0cf000d13a23cee46fc696961c3b72403b5e2aaab921e9895198cad5eb` | LISTED | direct |
| `0x75a383c773f4ff6a0df73e93486b3d44c1e9bbff` | 1 | PERSONAL_SIZED | 0.00 ETH | 3.70 | 1 | 2026-08-11 18:48 | `0x5f050249c5f8125b00e02317b06c5bee2c05ea735ffa769f90f21bf89d87b75c` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x8e638da706bb3c0c93388eef69547b6c3ee1edc6` | 1 | PERSONAL_SIZED | 0.02 ETH | 38.75 | 1 | 2026-08-11 18:39 | `0xa911df838c3bdea82976f4059f94e41cb5a3b46f2066f6df744df553d59856af` | LISTED | direct |
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 1 | Relay Depository | 30.74 USDT | 30.74 | 1 | 2026-08-11 18:48 | `0x1fa89fed38950627ea4918a9250aaff4f89c66d069dec071b92117e3f28c6a25` | LISTED | direct |
| `0xa254d507504180214898d9b9688455c43514b58a` | 1 | PERSONAL_SIZED | 0.00 ETH | 3.44 | 1 | 2026-08-11 18:49 | `0x5a1a0bc31eed1a3ed2d09c65494194392976d592f73e53984f0f7544704d83da` | LISTED | direct |

Funding branches stopped at: Measured hub, unnamed (2 branches, 86.70 USD); Binance: Hot Wallet (2 branches, 75.06 USD); Binance 17 (1 branches, 38.80 USD).

Exit branches stopped at: Relay Depository (2 branches, 44.12 USD); ChangeNOW Dep: 0x3f3...07B (1 branches, 38.61 USD).

### cn-0x3591ac128a

`0x3591ac128a1e7a19de48d68f10599d4dbf657bd7`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 2,000.00, withdrawals 0.00, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "LIGHT_FLOW_CAP": 6, "CONTRACT_NOT_IDENTIFIED": 20, "WINDOW_SCAN_NEEDED": 3, "NODE_BUDGET": 20}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x2df1c51e09aecf9cacb7bc98cb1742757f163df7` | 42161 | CONTRACT | 32,740.39 USDC | 32,740.39 | 3 | 2026-05-27 02:27 | `0x4aa9f7ec4b7601175b18003310ecc615f94afc467151e07b12f3538cdd3da24f` | LISTED | direct |
| `0xfd03abcadaf3f930fa4e37eb2f6ea3a44a41b7f0` | 1 | CONTRACT | 30,788.31 USDC | 30,788.31 | 3 | 2026-05-31 12:50 | `0xda4b5564d935d2915fecd76874c7eca9d9bd95f79e3dcef9e4e26c37f9937b10` | LISTED | direct |
| `0x394311a6aaa0d8e3411d8b62de4578d41322d1bd` | 42161 | HUB_MEASURED | 12,998.03 USDC | 12,998.04 | 3 | 2026-06-22 11:04 | `0x81765ee9e9d1504f23f7ecc8cd7648e170191548f1dfee71e408ac7ea3797f11` | LISTED | direct |
| `0xfd03abcadaf3f930fa4e37eb2f6ea3a44a41b7f0` | 42161 | CONTRACT | 9,053.05 USDC | 9,053.06 | 2 | 2026-07-02 02:01 | `0xe52caa5266e4973045c136eee2de07550b81bcec918c16f47f3bbfe76961d890` | LISTED | direct |
| `0x65a01a7364f90dd9024efa0bc85d88a373b483d3` | 1 | PERSONAL_SIZED | 4,054.64 USDC | 4,054.64 | 1 | 2026-07-13 01:50 | `0x44279447e3d44d3177473c24aa800464ae67738ab880182c4b9bc6f0a8f226fa` | LISTED | direct |
| `0x6cd1b8cfcd2ca2bcdb46a2d96bd22b92e16ba427` | 1 | HUB_MEASURED | 2,526.56 USDC | 2,526.56 | 2 | 2026-08-11 02:56 | `0xf65826c09cea868b973b5bd729094a838b301e248b1712ef6ebd7621c672f630` | LISTED | direct |
| `0xb405ba0530966178cf1fc73327266db5a98aa202` | 42161 | CONTRACT | 2,499.75 USDC | 2,499.75 | 1 | 2026-07-04 01:21 | `0x4fe0bf5e4e78167e8a338b1f3de03dd7282197c7c771276c33ffad2118b7b32b` | LISTED | direct |
| `0x65a01a7364f90dd9024efa0bc85d88a373b483d3` | 42161 | PERSONAL_SIZED | 2,493.75 USDC | 2,493.75 | 1 | 2026-07-05 17:33 | `0x919df4c23bf1dd684eca2cce2fb91274eecb522795d9bfd4f1bfe21cc3483326` | LISTED | direct |
| `0x5ddff00e743f999e731b3567be2181e32cfd1e45` | 137 | PERSONAL_SIZED | 1,000.00 pUSD | 1,000.00 | 1 | 2026-05-31 13:01 | `0x8fc11fb9d3d95f9847787de2d13396237fbf364f0930c40a7761020937666591` | REVERIFIED | direct |
| `0x914885b1de5bb84a18bec6124995cbb1b432d4aa` | 42161 | read through a bridge | 1,000.00 pUSD | 1,000.00 | 1 | 2026-05-31 13:05 | `0xbfce03371dd4c4c139477b62f8bc7c44623985808bda84a8e41dbe34493eb439` | REVERIFIED | Relay, same id on both chains |
| `0x394311a6aaa0d8e3411d8b62de4578d41322d1bd` | 1 | HUB_MEASURED | 853.57 USDC | 853.57 | 2 | 2026-09-21 01:43 | `0x43f61573dcacd51aa8f19be9884ad857d3d895be09f768ea0b759e083f71151e` | LISTED | direct |
| `0xd98e6008c2be593049bcd18302965e3850ab0859` | 1 | HUB_MEASURED | 688.53 USDC | 688.53 | 1 | 2026-08-05 21:27 | `0xbb9527b3add81b96e06ef2423c4d53efe2780203f8891e081469b05e40f9d991` | LISTED | direct |

2 smaller addresses are in the JSON.

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xe35e9842fceaca96570b734083f4a58e8f7c5f2a` | 42161 | Across Protocol: Bridge | 31,819.97 USDC | 31,819.97 | 3 | 2026-06-09 23:19 | `0xf9be5553072cab6f9ce64060facb894a648188c669d19305464a9585ba123393` | LISTED | direct |
| `0xa95d9c1f655341597c94393fddc30cf3c08e4fce` | 42161 | CONTRACT | 29,049.35 USDC | 29,049.35 | 8 | 2026-06-22 11:05 | `0x1a5751a6f035d47bd8e195320cf946dc85a459207a602841cc6c5b5e28362dfb` | LISTED | direct |
| `0x5c7bcd6e7de5423a257d81b442095a1a6ced35c5` | 1 | Across Protocol: Ethereum Spoke Pool V2 | 28,321.69 USDC | 28,321.70 | 9 | 2026-06-22 11:03 | `0x37579b6308b5fafff2dcc60a16b3af19aeaa11b1b1adda29067cc93311e15d53` | LISTED | direct |
| `0x65a01a7364f90dd9024efa0bc85d88a373b483d3` | 1 | PERSONAL_SIZED | 8,332.29 USDC | 8,332.30 | 2 | 2026-08-11 02:57 | `0xa63d6a050c211926b31150c6c8102d1cf56e93267df921458c329fbb59dc3188` | LISTED | direct |
| `0xd98e6008c2be593049bcd18302965e3850ab0859` | 42161 | PERSONAL_SIZED | 3,449.80 USDC | 3,449.80 | 1 | 2026-09-11 01:49 | `0xc13ece30e2f97da70e685e262a24ed8f94cfe51a00b46777f13d783091ae6253` | LISTED | direct |

Funding branches stopped at: Binance: Hot Wallet (4 branches, 232,973.60 USD); Measured hub, unnamed (14 branches, 80,414.86 USD); NEAR Intents (2 branches, 16,715.06 USD); Across Protocol: Ethereum Spoke Pool V2 (1 branches, 11,103.45 USD).

Exit branches stopped at: Across Protocol: Bridge (3 branches, 31,819.97 USD); Across Protocol: Ethereum Spoke Pool V2 (10 branches, 29,306.97 USD); Stargate: Pool USDC (1 branches, 603.43 USD); Uniswap V4: Pool Manager (1 branches, 409.11 USD); Circle CCTP: Token Minter V2 (1 branches, 100.00 USD).

### cn-0xaf0f3a3f50

`0xaf0f3a3f50fe55a9f963a2e88d3ecfca7fe73f10`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 28072.173411. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: {"NO_FUNDER_OBSERVED": 1}.

Who paid in, one hop out:

None read at this hop.

Where it went, one hop out:

None read at this hop.

### cn-0xf0b29b5cf6

`0xf0b29b5cf68c19ffaaa0c961326d5409b0a7b501`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 15434.298611. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "LIGHT_FLOW_CAP": 1, "NODE_BUDGET": 16, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0xdd3d72c53ff982ff59853da71158bf1538b3ceee` | 1 | ChangeNOW: Hot Wallet 3 | 7,092.67 USDT | 7,092.67 | 6 | 2026-06-24 08:59 | `0x2f4256ecdbb787b38a6d82a95b0e90dfb2f09dedfa4cb506c7151461e7ae6c73` | LISTED | direct |
| `0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055` | 1 | Binance: Hot Wallet 34 | 5,848.80 USDC | 5,848.80 | 2 | 2026-10-26 13:03 | `0x99fa71e02323181314ed74c184c63338ee9f29085058db9f25879c5bf99cde6a` | LISTED | direct |
| `0x77300c71071eca35cb673a0b7571b2907deb77c7` | 1 | HUB_MEASURED | 1.73 ETH | 3,985.53 | 2 | 2026-07-02 01:59 | `0xefbfe2d5f9083fa9b49029842e121f8e827479a9fe2aa6504f252d69453e2154` | LISTED | direct |
| `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 1 | HUB_MEASURED | 2,513.67 USDT | 2,513.67 | 1 | 2026-09-12 15:51 | `0xd0e8030014b13913b0938872f10abbe59bdebff868b4b502a03c2a5a0c3048f6` | LISTED | direct |
| `0xeba88149813bec1cccccfdb0dacefaaa5de94cb1` | 1 | ChangeNOW 16 | 0.04 ETH | 84.86 | 1 | 2026-06-24 09:06 | `0x7a70e7621837727d99b860929eae37fd3240fe1c90f70128f90fe500d910d2b2` | LISTED | direct |
| `0x6976d8025229db5f54bc899dd3dbc9285423896b` | 137 | ChangeNOW candidate, unconfirmed | 91.72 POL | 9.17 | 1 | 2026-09-06 23:05 | `0xa84faee1e712defe3af53198d9ed7daf8db9dcafe12fa701493121e1851b3dbf` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 1 | Relay Depository | 5,845.00 USDC, 9,600.52 USDT | 15,445.52 | 9 | 2026-06-24 09:08 | `0x54f233bd45a247f9738e41acfe11c14f0192d8043cb54314125e20443267f937` | LISTED | direct |
| `0xb21ac14ecf3963307ac5c431b21519b2aeb6eb29` | 137 | PERSONAL_SIZED | 8,166.11 USDC.e | 8,166.11 | 1 | 2026-09-07 03:46 | `0x202545b9c3af8c1dfdc5e1923d218d46ec754a1a9884f7ed7f0f454157324847` | LISTED | direct |
| `0xd046768723a56cc63607ccfea9cf7504285a5d77` | 1 | PERSONAL_SIZED | 1.02 ETH | 2,336.54 | 1 | 2026-09-12 15:49 | `0x261244fbb52917b9092f1ce29632cc86c3ebe77f714713f37544864b8e2564a1` | LISTED | direct |
| `0xeb91fa4617ed5778525e4f51d74c329f79fadbbf` | 1 | PERSONAL_SIZED | 0.71 ETH | 1,632.15 | 1 | 2026-07-02 07:27 | `0x5d1115572de0a1a5b4e216ceaa92ca72268cc570ce91920818b9bb688930c13b` | LISTED | direct |
| `0x9a2f5c64380031d5ba764b947a2edc659b46062f` | 1 | PERSONAL_SIZED | 0.04 ETH | 82.32 | 1 | 2026-07-07 02:03 | `0x1d496210762faa8e60d71174126eae286f19bb4eed61462084de83b9ceba7a7b` | LISTED | direct |

Funding branches stopped at: ChangeNOW: Hot Wallet 3 (6 branches, 7,092.67 USD); Measured hub, unnamed (3 branches, 6,499.20 USD); Binance: Hot Wallet 34 (2 branches, 5,848.80 USD); ChangeNOW 16 (1 branches, 84.86 USD); ChangeNOW candidate, unconfirmed (1 branches, 9.17 USD).

Exit branches stopped at: Relay Depository (9 branches, 15,445.52 USD); ChangeNOW Dep: 0x3f3...07B (1 branches, 2,336.40 USD); ChangeNOW 16 (1 branches, 1,632.01 USD).

### cn-0x227ce6a529

`0x227ce6a5296462b67dff30d2ac309149e62d7366`. Trace **WORK_LEFT**, books **NOT_RECONCILED**: deposits 0.00, withdrawals 0.00, residual 48.551323. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "ACCOUNTING_NOT_RECONCILED": 1}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x9468bf7e238129b8e7f49ff8ebdee642880fa293` | 1 | PERSONAL_SIZED | 0.02 ETH | 52.38 | 1 | 2026-09-15 11:16 | `0x7fceb475563344122e0e53e2ff1426077a8c2e2baddb2193fffec7013ae9d57c` | LISTED | direct |
| `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 1 | HUB_MEASURED | 48.61 USDC | 48.61 | 1 | 2026-09-15 11:19 | `0xf6d2e2c1bb79aecd02b978ae96e0212637cbf7318f53b807e28f9edbb49f8473` | LISTED | direct |

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 1 | Relay Depository | 48.61 USDC | 48.61 | 1 | 2026-09-15 11:21 | `0x0572f22bf7e0fc5aa4534a760f238542d25e6c817d642442e6b0237b4c91bd05` | LISTED | direct |
| `0x6e51618e084f20b28001a0934cfa4d2389e4f3bf` | 1 | PERSONAL_SIZED | 0.02 ETH | 46.00 | 1 | 2026-09-15 11:18 | `0xd81ea1a9a7af2529897f7dfc26df5e3f862a3dbe252ca98fcb91abe1b1df682f` | LISTED | direct |

Funding branches stopped at: Revolut 6 (1 branches, 173.89 USD); Measured hub, unnamed (1 branches, 48.61 USD).

Exit branches stopped at: Relay Depository (1 branches, 48.61 USD); ChangeNOW Dep: 0x3f3...07B (1 branches, 45.86 USD).

### cn-0x14d03db8fb

`0x14d03db8fb71d0811dedf16dd8a5ca20ec4a930c`. Trace **WORK_LEFT**, books **ACCOUNTING_RECONCILED**: deposits 939.59, withdrawals 294.34, residual 0.0. Deposit rows with no path: 0.00 USD. Withdrawal rows with no path: 0.00 USD.

Still open: {"LIGHT_MODE": 1, "TRADING_WALLET_HISTORY_NOT_READ": 1, "CONTRACT_NOT_IDENTIFIED": 4, "LIGHT_FLOW_CAP": 1, "NODE_BUDGET": 62}. Blocked by data: nothing.

Who paid in, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x8f0d024e780b7e2fd633a4d6d43631a96e8cb059` | 42161 | HUB_MEASURED | 4,362.92 USDC | 4,362.92 | 1 | 2026-10-11 21:28 | `0x31ba0ba1735e28f1925c15718ae70028bf968d3143a9a471a36fdd208aa6686c` | LISTED | direct |
| `0x20896aba1b4652807e59ec89d022c90463f67fd9` | 137 | CONTRACT | 2,591.34 USDC | 2,591.34 | 1 | 2026-10-03 14:55 | `0xc4901956c4f5d11fcd972288c48dcf2e221089a0a96ed5530bdc36be55fef901` | LISTED | direct |
| `0x202ff18fe234761c73048c67b6877153496d0c66` | 42161 | PERSONAL_SIZED | 0.53 ETH | 1,210.42 | 2 | 2026-10-03 16:39 | `0xbb0f25118132d2765173af720163883c9d6ddf931a9a59b8f6702c6f7ecaa4f4` | LISTED | direct |
| `0x78a26f3b5808f73d8a03cc2a46eaf2ff002e7db8` | 1 | read through a bridge | 540.25 pUSD | 540.25 | 2 | 2026-10-26 10:19 | `0x9defe40689d8ef1035dee4f62d2dfba7735446ce0181ea2ce9d9fc9450560460` | REVERIFIED | Relay, same id on both chains |
| `0x8267e03cfed422821978e49b3c2acaa9d4dfd136` | 1 | PERSONAL_SIZED | 464.00 USDC | 464.00 | 1 | 2026-11-01 13:59 | `0x49f7ee559d03cd2e0a7e04474626b724430a3a5ea772518abf237e8d2b07d7ab` | LISTED | direct |
| `0xc1d13492285eb664951e201bf7c80c7c6318a1b5` | 1 | SwftSwap (SWFT Blockchain) | 452.02 USDC | 452.02 | 1 | 2026-11-03 01:15 | `0x503572b6bee3e5da1ed043270efa5362a7a4f5c039582d350b047995e32ad9fe` | LISTED | direct |
| `0x8f0d024e780b7e2fd633a4d6d43631a96e8cb059` | 1 | HUB_MEASURED | 399.00 USDT, 0.00 ETH | 406.28 | 2 | 2026-10-04 13:11 | `0x3a1d9c3999c855b916c283c85ac9431d4761580b0eab681e8f02a44b64ffb4e0` | LISTED | direct |
| `0xb9eec60dca89d0d46b9bcf5f23d77ad1badcd07b` | 137 | PERSONAL_SIZED | 399.34 pUSD | 399.34 | 1 | 2026-10-25 01:53 | `0xa125891985512b83d69bfafb6a217c6d942f0ae26b04043def6f61dcc88b9eba` | REVERIFIED | direct |
| `0x6649caac72ca7426802b281f081d99656a346aa6` | 1 | PERSONAL_SIZED | 317.53 USDC | 317.53 | 1 | 2026-10-04 12:12 | `0xa70a2cbfc7c08933d7e9e81ab7d13caa1367abfda1773a85c4b534b1705bc0b1` | LISTED | direct |
| `0x14d03db8fb71d0811dedf16dd8a5ca20ec4a930c` | 137 | read through a bridge | 294.20 USDT | 294.20 | 2 | 2026-10-25 19:59 | `0xa05025fd46453fbe8481ece702fee5903935be6ebb030d73e36ec59127d83fa3` | LISTED | Relay, same id on both chains |
| `0x46340b20830761efd32832a74d7169b29feb9758` | 1 | Crypto.com 2 | 194.69 USDC | 194.69 | 1 | 2026-10-04 20:36 | `0x372f6e65150c72cee81e61dcee790ca52914d11ff0e542232740c8f7c0c55412` | LISTED | direct |
| `0x5c7bcd6e7de5423a257d81b442095a1a6ced35c5` | 1 | Across Protocol: Ethereum Spoke Pool V2 | 0.00 ETH | 8.83 | 1 | 2026-10-25 02:19 | `0xb750a382f5ac9ed47bd274b26b273f33c02fded8a66e77ee5b6cbaf7a11339ec` | LISTED | direct |

1 smaller addresses are in the JSON.

Where it went, one hop out:

| Address | Chain | Label or class | Amount | USD | Tx | First, UTC | First transaction | Level | Through |
|---|---:|---|---|---:|---:|---|---|---|---|
| `0x69460570c93f9de5e2edbc3052bf10125f0ca22d` | 42161 | CONTRACT | 4,362.00 USDC, 0.01 ETH | 4,376.85 | 3 | 2026-10-04 18:59 | `0xa9ce8e70f99c0ca887a95a18809f455f4f0c34a5d72888a1383db15f7921e3b9` | LISTED | direct |
| `0xd7b9e5dc08e95002b45fd32e095643370a174daa` | 137 | PERSONAL_SIZED | 2,591.34 USDC | 2,591.34 | 1 | 2026-10-03 21:18 | `0x79f231eb5646b396aee204cc9934cf799e84457d704b0d4cfca554fe72c0cf33` | LISTED | direct |
| `0xd48fefe7e9ffd7c8f57b328ce77a61567753b775` | 1 | PERSONAL_SIZED | 1,428.24 USDC, 121.88 USDT | 1,550.12 | 4 | 2026-10-04 13:15 | `0x61aab53e9dd45f774eaa9b3ba55aab51a53225accc90679b357867dab27d99ec` | LISTED | direct |
| `0xd48fefe7e9ffd7c8f57b328ce77a61567753b775` | 42161 | PERSONAL_SIZED | 845.88 USDC | 845.88 | 1 | 2026-10-03 20:55 | `0xf0f9af0d542d61a9188d115ea94861621c7997e7a350b9787236c131721c03da` | LISTED | direct |
| `0x0000000000001ff3684f28c67538d4d072c22734` | 42161 | 0x: Allowance Holder | 0.32 ETH | 729.36 | 1 | 2026-10-03 20:54 | `0x37e915c545135db48e13eafce4539b2549b3e8dbaabf7e234175d637cea59a46` | LISTED | direct |
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 1 | Relay Depository | 541.23 USDT | 541.22 | 2 | 2026-10-26 10:19 | `0xe55058ec30f4cf6429949a0831846babbdbbbfc1e1360c07891ee02f825899cc` | LISTED | direct |
| `0xc1d13492285eb664951e201bf7c80c7c6318a1b5` | 42161 | SwftSwap (SWFT Blockchain) | 0.20 ETH | 466.13 | 1 | 2026-11-03 01:14 | `0xb0031377ac0eb0de17352e6ce6fe857ee65a049f689644a5dfe48cc5ff495478` | LISTED | direct |
| `0x4cd00e387622c35bddb9b4c962c136462338bc31` | 137 | Relay Depository | 294.34 USDC.e | 294.34 | 2 | 2026-10-25 19:59 | `0x94093d5541a242cdfa91dbdfe179564fc7c0c8744aff2e6337b436f4bad9418a` | REVERIFIED | direct |
| `0x0c2978ba7256d9b3889a098060e36a2a49a134a9` | 1 | PERSONAL_SIZED | 30.09 USDT | 30.09 | 1 | 2026-10-25 20:30 | `0x15c0fd6c97cd67ce24b46a5c3fc4b3e825f0dd1ded5f2399ccf3e075e06d7ba8` | LISTED | direct |
| `0x35097e9782f5d1ea45c43ecde8b22d1e7a263fd3` | 1 | PERSONAL_SIZED | 0.00 ETH | 9.94 | 1 | 2026-10-25 02:21 | `0x4a1ebc9a905742a8e37f7649ea431a5b83b6e41b2512f454a20daeeb8c7aa95d` | LISTED | direct |

Funding branches stopped at: Measured hub, unnamed (7 branches, 19,965.94 USD); Stake.com (6 branches, 16,995.04 USD); SwftSwap (SWFT Blockchain) (1 branches, 452.02 USD); Crypto.com 2 (1 branches, 194.69 USD); Across Protocol: Ethereum Spoke Pool V2 (1 branches, 8.83 USD).

Exit branches stopped at: Relay Depository (4 branches, 835.56 USD); 0x: Allowance Holder (1 branches, 729.36 USD); SwftSwap (SWFT Blockchain) (1 branches, 466.13 USD); Measured hub, unnamed (4 branches, 95.47 USD).
