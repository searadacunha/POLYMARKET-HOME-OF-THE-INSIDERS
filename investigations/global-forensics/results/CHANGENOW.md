# ChangeNOW and Polymarket, both directions

Read on 2026-11-03. All data here is archived or computed offline. **None of it has been re-read from a node in this file.** A label says what a source wrote: the service has not confirmed any address. No individual order can be identified from public data: `OFFCHAIN_RECORD_REQUIRED`. Nothing here shows a passage through Monero, in either direction.

## From ChangeNOW to Polymarket

Method: `engine/tools/cn_polymarket_join.py`. Input: the 431,444 recipients of attributed payout addresses over 90 days, from 2026-08-04 to 2026-11-02, in `~/Projects/PolySentinel-ChangeNOW-outflows/state/recipients.csv`, collected by another session on 2026-11-02. Each recipient was tested as itself and through three wallet forms computed from a key. Known wallets: 309,565, from taker rows of 2,097 large markets to 2026-09-15, the Ballon d'Or family to late October, and the catalogue tapes.

| Item | Value |
|---|---|
| Recipients tested | 431,444 |
| Correspondences | 32 rows, 26 recipients, 26 wallets |
| Total received by those recipients from those addresses | $52,666.12, largest $25,604.06 |
| Rows with at least $100 received | 15 |
| Payment before the wallet's first known trade | 21 rows |
| Positive control: keys of the 11 named accounts must reach their wallets | 11 of 11 |
| Negative control: random addresses | 0 hits on 20,000 |

Ballon d'Or family, from the census tape: 9 of these wallets bought after their payment and before the Upside post of 2026-10-23 15:17:49 UTC, for $202.30 in total. The two largest payments that reach the family, $6,890 and $5,556, are followed by a first trade on October 26 and October 25, after that post.

**Reading.** Across this window and this universe, a direct payment from these addresses to the key of a known trading wallet is rare and small. This extends `changenow-polymarket`, which found a real and tiny link on one hub.

**What this does not say.** A payment is not a funding of a bet: no flow from the payment to the deposit was traced here. A recipient who forwards to a second address before funding is invisible, so this is a lower bound. Safe wallets are not tested. A wallet is known only if it took at least one taker trade of $100 in one of the large markets before mid-September, or traded in the Ballon d'Or family. Solana, Tron, Base, BSC and Bitcoin payouts are not in the input. No comparison with another service was made, so "rare" had no base rate at this point: see below.

## A base rate from other swap services

Read on 2026-11-03 by `engine/tools/cn_comparator.py`, output `results/changenow/comparators.json`. The same test, same 90-day block window, same 309,565 known wallets, same wallet forms, on recipients of other addresses that public lists or the September archive give to swap services. Outgoing listed transfers of value, native or listed tokens.

| Service, chain | Recipients | Reaching a known wallet | Rate | 95% interval | State of the read |
|---|---:|---:|---:|---|---|
| ChangeNOW attributed addresses, Ethereum | 417,279 | 18 | 0.004% | 0.003% to 0.007% | collected by another session |
| ChangeNOW attributed addresses, Polygon | 14,164 | 9 | 0.064% | 0.033% to 0.121% | collected by another session |
| Bridgers, Ethereum | 2,651 | 3 | 0.113% | 0.038% to 0.332% | COMPLETE |
| SwftSwap, Ethereum | 32,005 | 11 | 0.034% | 0.019% to 0.062% | INCOMPLETE: page cap 150 |
| Bridgers, Polygon | 1,044 | 5 | 0.479% | 0.205% to 1.116% | COMPLETE |

**Reading.** A payout address reaching a known trading wallet is no rarer on the other services read than on ChangeNOW, and on these reads it is more common. The 26 are not an excess against this base rate. FixedFloat's listed hot wallet shows no outgoing row in this window on Ethereum, so it gives no rate.

**Limits.** Addresses read differ in size and in what they serve: one contract or one list entry against 431,444 ChangeNOW recipients spread over many attributed addresses, and those include a tier of mere candidates. The SwftSwap read stopped at its page cap, so its rate covers part of the window. Rows differ in kind: the comparators count only listed tokens and native value, and the ChangeNOW file came from another collector. A label is a public list's word. A rate of reaching a known wallet is no rate of funding a bet.

## From Polymarket to ChangeNOW

Established earlier, on the 11 Ballon d'Or files only: `changenow-proof` found one corroborated direct contact, the kraben006 key, and refuted amount-and-date matching as proof. Traces of this investigation carry the same attribution table: any withdrawal path reaching a labelled ChangeNOW address stops there as a service. The traces of the catalogue and discovery lists are unfinished at this date, so no count is given.

## Rows

| Recipient | Form | Wallet | Chain | Tier | First source | First payment | USD received | Wallet first trade | Payment first | Family buys, USD | First family trade | Known from |
|---|---|---|---|---|---|---|---:|---|---|---:|---|---|
| `0x2212c2fb5ebbfcc8aa9c6cb2fcc1fe51238ec694` | deposit_legacy | `0xe0bf7ab5b11dcbdbb169638cacf43edaa540d7fe` | 1 | CANDIDAT | `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 2026-09-18 14:36 | 25,604.06 | 2026-05-19 02:53 | no | 0.00 |  | p8 |
| `0xaf0f3a3f50fe55a9f963a2e88d3ecfca7fe73f10` | itself | `0xaf0f3a3f50fe55a9f963a2e88d3ecfca7fe73f10` | 1 | CANDIDAT | `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 2026-08-24 17:59 | 7,930.63 | 2026-05-30 15:44 | no | 0.00 |  | p8 |
| `0x5db992c164b934b3ba58586e36cf0d5264e07110` | deposit_beacon | `0x55bb88498ecee0369bf77e45e04ca37eaf4270d3` | 1 | ETIQUETEE | `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 2026-09-19 22:27 | 6,889.95 | 2026-10-26 01:26 | yes | 4,558.07 | 2026-10-26 01:26 | census |
| `0x78a26f3b5808f73d8a03cc2a46eaf2ff002e7db8` | deposit_beacon | `0x14d03db8fb71d0811dedf16dd8a5ca20ec4a930c` | 1 | CANDIDAT | `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 2026-10-07 08:30 | 5,556.17 | 2026-10-25 16:45 | yes | 1,143.91 | 2026-10-25 16:45 | census |
| `0xc7fc68493da6d237584b3b416e2bea38a9428e68` | deposit_legacy | `0xf0b29b5cf68c19ffaaa0c961326d5409b0a7b501` | 1 | CANDIDAT | `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 2026-09-12 15:51 | 2,513.19 | 2026-07-19 22:18 | no | 0.00 |  | p8 |
| `0x9c39c3f4636eacbe09a4ccda2576c51b1c39a8b7` | deposit_beacon | `0x6e793da3489cb6f9e0174f8c4e2366b37273dc1f` | 1 | ETIQUETEE | `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 2026-08-19 05:33 | 1,927.48 | 2026-10-26 11:35 | yes | 3.00 | 2026-10-26 11:35 | census |
| `0xd8c603cecd534ee4ebb972b98ff6793a677da2c4` | deposit_beacon | `0xd7e584155367f9e3082b17c6e02aab5b6cea01a6` | 1 | CANDIDAT | `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 2026-08-18 02:40 | 400.73 | 2026-08-18 05:53 | yes | 0.00 |  | p8 |
| `0xc924cd3e375803f937ffbbc147528d92d5d87b6c` | deposit_legacy | `0xd18ef9f072479d988a70bcbaad93f33781a2a378` | 137 | CANDIDAT | `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 2026-08-19 08:57 | 330.11 | 2026-08-26 13:21 | yes | 40.22 | 2026-08-26 13:21 | census |
| `0x770c32fd0f64255b6abb564a7ca2b6a091a88f83` | deposit_beacon | `0x4a4f1fbc70c61f9a2daee0d8d1974fbe37bc32e0` | 137 | CANDIDAT | `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 2026-08-06 09:28 | 245.35 | 2026-08-02 10:40 | no | 0.00 |  | p8 |
| `0x371ac9a3c2c208cc75d4e2fd0e7172de5960d4e8` | deposit_beacon | `0x09b831e67e64c464dc31c4ead793727646e0e5fe` | 1 | ETIQUETEE | `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 2026-08-31 19:09 | 197.38 | 2026-10-26 04:28 | yes | 1.05 | 2026-10-26 04:28 | census |
| `0xadd9ab62b2c22151c661b99821cbb7433df98df9` | itself | `0xadd9ab62b2c22151c661b99821cbb7433df98df9` | 137 | CANDIDAT | `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 2026-08-18 17:59 | 189.35 | 2026-10-16 23:54 | yes | 14.00 | 2026-10-16 23:54 | census |
| `0x171928732a666978713c13f03e0e9ea30f8c1065` | deposit_beacon | `0x19bb95ea829511f4c0056a9b7024ddef1e272ff0` | 1 | ETIQUETEE | `0xeba88149813bec1cccccfdb0dacefaaa5de94cb1` | 2026-08-07 11:12 | 164.76 | 2026-10-01 10:21 | yes | 47.08 | 2026-10-01 10:21 | census |
| `0xeaba99109fea652233c70b00207328839315b993` | deposit_beacon | `0xdec4c188314de225a81c7ada6cadb26daefd2402` | 1 | CANDIDAT | `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 2026-10-25 00:01 | 143.93 | 2026-10-25 14:02 | yes | 106.32 | 2026-10-25 14:02 | census |
| `0x171928732a666978713c13f03e0e9ea30f8c1065` | deposit_beacon | `0x19bb95ea829511f4c0056a9b7024ddef1e272ff0` | 1 | CANDIDAT | `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 2026-08-18 14:15 | 143.21 | 2026-10-01 10:21 | yes | 47.08 | 2026-10-01 10:21 | census |
| `0x64e05558bcac6f406466081ae9d2a964835c4d33` | deposit_beacon | `0x3067fecf27edd852bd6f6beae4db025dae5ad85b` | 137 | CANDIDAT | `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 2026-10-20 08:40 | 125.05 | 2026-10-26 19:37 | yes | 3.50 | 2026-10-26 19:37 | census |
| `0x914885b1de5bb84a18bec6124995cbb1b432d4aa` | deposit_legacy | `0x3591ac128a1e7a19de48d68f10599d4dbf657bd7` | 1 | CANDIDAT | `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 2026-08-12 01:20 | 88.32 | 2026-05-31 13:03 | no | 0.00 |  | p8 |
| `0xeaba99109fea652233c70b00207328839315b993` | deposit_beacon | `0xdec4c188314de225a81c7ada6cadb26daefd2402` | 1 | ETIQUETEE | `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 2026-10-25 00:10 | 51.37 | 2026-10-25 14:02 | yes | 106.32 | 2026-10-25 14:02 | census |
| `0x0796a571510940163e21d631f88360ff2e2437ac` | deposit_beacon | `0x227ce6a5296462b67dff30d2ac309149e62d7366` | 1 | CANDIDAT | `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 2026-09-15 11:19 | 48.60 | 2026-09-16 06:09 | yes | 46.71 | 2026-09-16 06:09 | census |
| `0x1de9873b76a4277ed1526ff23c6acbe6f9d2c96b` | deposit_beacon | `0x814fd935380361956828ec5e176ee9e7ea19a031` | 1 | CANDIDAT | `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 2026-08-11 18:41 | 30.72 | 2026-08-11 18:55 | yes | 28.97 | 2026-08-11 18:55 | census |
| `0x1d5e692b160eda0add2c72c88d734f43997d4f5f` | deposit_beacon | `0x391112d827116d2b9cc6a079443ea9b3fea51bd7` | 137 | CANDIDAT | `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 2026-08-19 21:02 | 29.43 | 2026-10-26 21:59 | yes | 2.04 | 2026-10-26 21:59 | census |
| `0x1af772188fcb222920ae15c6f96ca33260ce38a2` | deposit_beacon | `0xd55776adc38f23659a0e8853ea73f4e7f2d756d6` | 1 | ETIQUETEE | `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 2026-09-27 23:45 | 18.56 | 2026-10-26 22:25 | yes | 476.02 | 2026-10-26 22:25 | census |
| `0xa254d507504180214898d9b9688455c43514b58a` | deposit_beacon | `0xd55dad050daeedcf9ca1236ab50b649f6ad1612e` | 1 | CANDIDAT | `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 2026-08-11 18:39 | 13.37 | 2026-08-15 20:03 | yes | 12.00 | 2026-08-15 20:03 | census |
| `0x265614b2e438183666a6e588f728824230c2e777` | deposit_beacon | `0xc31ed9f0f0e1cda74713a0fc51625f530a53a4db` | 1 | CANDIDAT | `0x64cdaa89629fe003eaa31b480d8b63372d109a53` | 2026-09-10 09:05 | 4.76 | 2026-10-13 16:40 | yes | 2.00 | 2026-10-13 16:40 | census |
| `0x0782a01b476851a438e1fe179b9542a10027790b` | deposit_beacon | `0x5c1aad95490e09b90485903b846940475803346b` | 137 | CANDIDAT | `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 2026-08-05 13:27 | 4.31 | 2026-08-02 21:33 | no | 0.00 |  | p8 |
| `0x89fa968f4161b8a90eee1b5646f7a04c3cdfd64f` | deposit_beacon | `0xd67b91b9ce4cb290e5d6ae27e783070a56287a5d` | 1 | ETIQUETEE | `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 2026-08-22 17:00 | 3.76 | 2026-07-24 07:20 | no | 0.00 | 2026-08-16 10:24 | census+p8 |
| `0x100f954b0efb9ab88d6a17de68e9c742b7cbd108` | deposit_beacon | `0xa8566ea1e940c1237b844f77e14fc1cb1b2f2278` | 137 | CANDIDAT | `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 2026-10-30 18:39 | 3.35 | 2026-10-24 15:24 | no | 5.00 | 2026-10-24 15:24 | census |
| `0x265614b2e438183666a6e588f728824230c2e777` | deposit_beacon | `0xc31ed9f0f0e1cda74713a0fc51625f530a53a4db` | 1 | ETIQUETEE | `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 2026-09-18 11:59 | 2.20 | 2026-10-13 16:40 | yes | 2.00 | 2026-10-13 16:40 | census |
| `0xd8c603cecd534ee4ebb972b98ff6793a677da2c4` | deposit_beacon | `0xd7e584155367f9e3082b17c6e02aab5b6cea01a6` | 1 | ETIQUETEE | `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 2026-08-18 05:25 | 2.18 | 2026-08-18 05:53 | yes | 0.00 |  | p8 |
| `0x12852f9976636427bcfcfd3e6309f5d9fcc7539e` | itself | `0x12852f9976636427bcfcfd3e6309f5d9fcc7539e` | 137 | CANDIDAT | `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 2026-09-09 11:53 | 1.80 | 2026-02-25 07:58 | no | 0.00 |  | tape |
| `0x1d5e692b160eda0add2c72c88d734f43997d4f5f` | deposit_beacon | `0x391112d827116d2b9cc6a079443ea9b3fea51bd7` | 1 | ETIQUETEE | `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 2026-10-26 20:15 | 1.00 | 2026-10-26 21:59 | yes | 2.04 | 2026-10-26 21:59 | census |
| `0x2212c2fb5ebbfcc8aa9c6cb2fcc1fe51238ec694` | deposit_legacy | `0xe0bf7ab5b11dcbdbb169638cacf43edaa540d7fe` | 1 | ETIQUETEE | `0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b` | 2026-09-18 15:50 | 0.84 | 2026-05-19 02:53 | no | 0.00 |  | p8 |
| `0x7678aa83a333f333356c04d4faa929d81b2322a3` | itself | `0x7678aa83a333f333356c04d4faa929d81b2322a3` | 137 | CANDIDAT | `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423` | 2026-10-28 15:39 | 0.20 | 2026-07-29 19:25 | no | 23,871.51 | 2026-10-26 02:04 | census+p8 |
