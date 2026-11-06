# Independent cross-check of Inca Digital's Iran accounts against PR 27

Date: 6 November 2026. Branch `research/inca-crosscheck-20261106`, built on PR 27's head `dd9df29`. Nothing in PR 27's notes is modified. Every figure below is recomputed offline by `python3 -I verify.py` from `evidence/` (and PR 27's `accounts.csv` and Relay pages, which are in git). Raw responses are kept outside git; each evidence file lists the URL and SHA-256 of the raw responses it was made from.

## Summary

- **The two intersections are exact.** Inca's 9TungSahur (`0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a`, now TheOneWhoKnocks1312) and DonkeyDonkey999 (`0xcb18ea2923d957bd9cf049cce60a87638722f867`) are two of PR 27's 19 network accounts. For all five Inca accounts, the cash recomputed from Polymarket's activity equals Inca's realized profit within 1.50 USDC.
- **New money relations between the two, June 2025** (every leg in `EVIDENCE_INDEX.csv`):
  - R1, level L2: on 11 June 2025, DonkeyDonkey999's three withdrawals (1,162.81 USDC) pay `0xa26792e2…`, which behaves as 9TungSahur's deposit address; 9TungSahur is credited 98.8 % of each leg about 19 minutes later. These are its first deposits, the day before its bets.
  - R2, level L3: on 13 June 2025, between 01:42 and 02:27 UTC, 9TungSahur, DonkeyDonkey999 and ILOVEYOUBABYZZ (PR 27) credit the same Bybit deposit address `0x93b7e169…` with 65,992.25 USDC. PR 27 had missed these payments (they come from the Uniswap pool, not from the proxies).
- **Later relations:**
  - R6, level L3: the Stake.com deposit address `0xbfaa1d49…` is credited by DonkeyDonkey999 (October 2024), TBFMM (January 2026) and `0x283ad350…`, a Polymarket account with no trade (February 2026).
  - R3, level L3u: 9TungSahur, rrrrgggbbbclat and Bigboyslatvian pay the wallet `0x529c2eef…`, of the same unidentified service as PR 27's `0xa6c22144…`. So does, two hops away, one ordinary control: customer-specific is not established.
  - R4, level L4: Bybit hot-wallet payouts line up with these addresses. This is timing only.
- **The three other Inca accounts (PorcoRosso, ricosuave666, truthlord):** no direct transfer, no shared non-service funder and no shared beneficiary with the two others or the network, in every hop read. Their shared funders are services (Fun.xyz, Relay, `0xf0fc40a6…`). In the control test fixed before the data (54 comparable early Yes buyers), they score 0 of 3 on all three measures, against 0 %, 7.4 % and 9.3 % of controls; p = 1. Their bridged outflows are not traced.
- **ricosuave666 and the Israeli indictment:** the winnings quoted in the press ($162,663) equal ricosuave666's redemption of 162,663.94 USDC, and the other published details are consistent with its record: about $128,000 of profit, a winning bet on the end of the operation, January and March bets partly cancelled, a changed username, and a fresh wallet funded with 74,680.13 USDC two days after the fighting. Two details do not match (section 5.1). No article names an account; this is compatibility, not attribution.
- **Rarity pipeline:** freeze intact in git (129 of 129 files, lock hash equal to the freeze index). The live collection on the external disk cannot be checked: the disk is not mounted and no process is running.
- **Not shown:** that one person controls these accounts, or that anyone traded on inside information. A shared deposit address means the same exchange or service account was credited.


## 1. The external source

- **Report.** Inca Digital, *Insider Detection on Polymarket*, PDF of 30 pages, title metadata "Copy of Polymarket Insiders Report Draft", created 26 November 2025, modified 25 June 2026. Downloaded on 6 November 2026 from `https://drive.google.com/file/d/1tesSlK0kHOU9vm6VtMf1QRS8VO2ah-Yz/view`, SHA-256 `2b14e2874ff26712db5e85a3fcbb5c1c3c425c91671245bc9b34be892141d38b`. The PDF is third-party content and is not in the repository.
- **What it claims.** Section 3.1 (pages 9 to 12) lists five accounts on "Israel military action against Iran by Friday?" as "high-likelihood insiders", with a realized profit for each. The method (section 1) is a set of trading heuristics: profit concentration, timing before resolution, entry price, post-entry price move, loss share, "decision centralization". Inca reads no deposit or withdrawal. Its label is a third-party judgement and is used here only to name the accounts.

| Inca name | Address | Inca realized profit |
|---|---|---|
| 9TungSahur | `0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a` | 36,790.56 |
| PorcoRosso | `0xd5de5cad9ef22b16317fe30a4234c72ece3eac1a` | 85,120.83 |
| ricosuave666 | `0x0afc7ce56285bde1fbe3a75efaffdfc86d6530b2` | 128,736.79 |
| DonkeyDonkey999 | `0xcb18ea2923d957bd9cf049cce60a87638722f867` | 34,996.87 |
| truthlord | `0xa3a6fa49a39a4bf84cf510b7c8a2ab8be8508c44` | 52,329.69 |

## 2. The two intersections are exact

- `0x6c2c072a…` and `0xcb18ea29…` are, character for character, two of the 19 network accounts of PR 27 (`../iran-cluster-e-network-2026-11-05/accounts.csv`). The other three Inca addresses are not in any PR 27 file (section 7 for the rest of the repository).
- **Same accounts, not look-alikes.** The cash flow of each account on that market, recomputed from its full Polymarket activity (sells and redemptions minus buys), equals Inca's realized profit within 1.50 USDC for all five accounts (table in section 3). An address shared by chance would not reproduce five profits to the dollar.
- **Usernames.** Polymarket serves today `TheOneWhoKnocks1312` for `0x6c2c072a…` (Inca: 9TungSahur), `RemiIio` for PorcoRosso's address and `Rundeep` for ricosuave666's. DonkeyDonkey999 and truthlord are unchanged. The renames are inferred from Inca's table; their dates are not known.

## 3. June 2025: the trades and the money of the two network accounts

Cash flow on "Israel military action against Iran by Friday?" (condition `0x7f39808829da93cfd189807f13f6d86a0e604835e6f9482d8094fac46b3abaac`), from each account's full activity. The market opened on 11 June 2025 at 20:10:25 UTC and the first Yes trade at 0.90 or more is at 00:00:21 UTC on 13 June.

| Account | Yes bought (USDC) | Average price | First and last buy (UTC, 12 June) | Exit | Cash on the market | Inca |
|---|---|---|---|---|---|---|
| 9TungSahur | 6,332.74 | 0.146 | 06:15:43 to 21:22:47 | sold at 0.997 from 00:27 on 13 June | 36,790.37 | 36,790.56 |
| PorcoRosso | 25,002.03 | 0.216 | 12:19:21 to 20:31:19 | sold from 00:13 on 13 June | 85,120.76 | 85,120.83 |
| ricosuave666 | 33,928.65 | 0.209 | 07:00:01 to 21:23:15 | redeemed 162,663.94 at 11:57 on 13 June | 128,735.29 | 128,736.79 |
| DonkeyDonkey999 | 6,125.08 | 0.128 | 08:28:17 to 11:24:41 | sold at 0.995 or more on 13 June | 34,996.81 | 34,996.87 |
| truthlord | 13,045.09 | 0.157 | 18:45:29 to 23:36:57 | sold, partly from 21:16 on 12 June | 52,329.44 | 52,329.69 |

### 3.1 DonkeyDonkey999 funds 9TungSahur the day before the bets (relation R1)

On 11 June 2025, DonkeyDonkey999 withdraws 10, 15 and 1,138 USDC.e (17:39:42, 17:51:28 and 18:11:36 UTC). Through the Uniswap pool used by Polymarket withdrawals, `0xa26792e288079f9ee81d09e81058a5edbca522e4` receives 9.998332, 14.997512 and 1,137.811752 USDC. About 19 minutes after each leg (1,128, 1,142 and 1,138 seconds), 9TungSahur receives a deposit of 9.876636, 14.81913 and 1,124.774109 USDC.e, that is 98.8 % of each leg, from `0x3f77a673a29e8cea345f0ed1f4f40a914156fc32`. These are 9TungSahur's first three deposits ever, 12 hours before its first bet.

What `0xa26792e2…` is, from its own history:
- it forwards each inflow within 16 to 26 seconds, each time to a different address, and each forward is preceded by a gas top-up from `0x3f77a673…` or `0xefce5b1cd37a24b752308c93e51fb7da69e220da`, two wallets with tens of thousands of transactions (nonce 35,812 and 44,285 at the time);
- `0x3f77a673…` is the wallet that then pays 9TungSahur. The repository's Maduro investigation (`investigations/maduro-iran/sources/phase2/TABLE1_graph.csv`) shows it paying the gas of other Polymarket deposit addresses;
- its fourth and last real inflow is 1.999965 WETH from Crypto.com 6 (`0xfa0b641678f5115ad8a8de5752016bd1359681b9`, Blockscout label) at 21:07:35 on 12 June. Forty seconds later, 9TungSahur receives its fourth and last deposit, 5,183.27 USDC.e, through the Fun.xyz CheckoutPool;
- every other token it received is spam (fake "UЅDС" from look-alike addresses).

So each of the four inflows of `0xa26792e2…` is followed by one of 9TungSahur's four deposits, and each of these deposits follows an inflow. `0xa26792e2…` behaves as a deposit address credited to 9TungSahur, like `0x20bd758d…` for ALLOWMETOSHOWU1 in PR 27. Polymarket's bridge status endpoint returns no record for it (it returns six deposits for `0x20bd758d…` back to September 2025); the classification therefore rests on behaviour, not on Polymarket's records. Level L2.

### 3.2 The exits of 13 to 19 June 2025 (relation R2)

| Time (UTC) | Account | Recipient | USDC received | Status |
|---|---|---|---|---|
| 13 June, 00:53 to 01:17 | 9TungSahur | Crypto.com customer deposit `0x9063493a…` | 35,121.39 in 6 withdrawals | in PR 27 |
| 13 June, 01:12 | 9TungSahur | `0x93a2eb921ae9c45e57709406b29749c449f04fff` | 999.90 | not classified |
| 13 June, 01:24 to 01:31 | 9TungSahur | customer wallet `0x529c2eef…` (section 4.1) | 4,999.44 in 3 | **new** |
| 13 June, 01:42 and 01:44 | 9TungSahur | Bybit customer deposit `0x93b7e169…` | 1,999.88 in 2 | **new** |
| 13 June, 01:53 and 01:55 | DonkeyDonkey999 | Bybit customer deposit `0x93b7e169…` | 19,997.72 in 2 | **new** |
| 13 June, 02:01 and 02:02 | DonkeyDonkey999 | Binance customer deposit `0x519fa16e…` | 20,011.85 in 2 | in PR 27 |
| 17, 18 and 19 June | DonkeyDonkey999 | Bybit customer deposit `0x93b7e169…` | 20,216.10 in 3 | **new** |

The two accounts paid the **same Bybit deposit address** nine minutes apart. A Bybit deposit address credits one Bybit account (PR 27, section 2: gas from Bybit: Deposit Funder 2, sweeps to Bybit). PR 27 lists four payers of `0x93b7e169…` (ALLOWMETOSHOWU1, rrrrgggbbbclat, DonkeyDonkey999 in January 2026, Bigboyslatvian) and misses these seven withdrawals: in the address's token history they come from the Uniswap pool, not from the proxies. Level L3, a shared customer-specific address: the same Bybit account was credited by both accounts. It does not show that one person controls both.

## 4. Later financial relations

### 4.1 Wallet `0x529c2eef…`: 9TungSahur, two network accounts and one control (relation R3)

`0x529c2eef349edaf657cb23c2493bfd4369eb09bf` is, like PR 27's `0xa6c22144…`, an EOA delegated through EIP-7702 to `0x0000fb7702036ff9f76044a501ac1aa74cbab16b` (same code at `latest`, `0xef0100` followed by that delegate). Its only gas came from relayer `0x80e54311d48127cb66df9d65bf430796c8cf42be` (2 POL at 01:25:39 on 13 June 2025, 40 s after 9TungSahur's first payment into it), the relayer of `0xa6c22144…`'s `execute` calls in PR 27. Every one of its real outflows (USDC and USDT0) goes to `0x852dc1c875f0117ea0808610010893e4c576b6a9`, the address where `0xa6c22144…` also sends everything. It is therefore a wallet of the same unidentified service.

Its payers:

| Date (UTC) | Payer | Amount | Path |
|---|---|---|---|
| 13 June 2025, 01:24 to 01:31 | 9TungSahur | 4,999.44 USDC | 3 Polymarket withdrawals |
| 14 June 2025, 11:33 | `0x0bc0369198d851db9dfc865f088661c50dd901dd`, own wallet of the control **`0x4d209741…`** (below) | 300 | direct |
| 14 to 22 June 2025 | Bybit 5 (Bybit hot wallet) | 7,537 in 4 | Bybit withdrawals (section 4.2) |
| 13 and 14 April 2026 | rrrrgggbbbclat (PR 27 network) | 299.76 and 299.76 | Relay, Polygon to Polygon |
| 11 May 2026 | `0x6c3cd5d25cac386a9c77dc6248067345aa5f8d00` (not a Polymarket account, unknown) | 200 | Relay |
| 12 June 2026 | Bigboyslatvian (PR 27 network) | 171.36 | Relay |
| 12 June 2026 | Bybit: Wallet 131 | 150 USDT0 | Bybit withdrawal |

The control `0x4d209741d0e8ae2758685bcb6d44f0704ac616dd` bought 6,038 USDC of Yes on the same market and is one of the 54 controls of section 6. On 13 June 2025 at 01:01 to 01:08 UTC it withdrew 29,949.95 USDC.e in three legs to `0x0bc03691…`, a wallet whose first transaction is that day and whose only gas came from Bybit 5. It is in no PR 27 file and not in Inca's report. This was found while classifying the payers of `0x529c2eef…`, outside the plan's measures: exploratory.

Reading: a single customer would explain 9TungSahur, rrrrgggbbbclat and Bigboyslatvian, but then the control's wallet and the unknown `0x6c3cd5d2…` would belong to the same customer; a merchant, a peer-to-peer desk or a card top-up address shared by several people would explain all payers. **Customer-specific is not established** (level L3u). It is a shared destination of an unidentified service, not proof of a common owner.

### 4.2 After the Bybit deposits of 13 June: Bybit 5 pays 0x09133414 and 0x529c2eef (relation R4)

Between 01:42 and 01:55 UTC on 13 June 2025, 9TungSahur and DonkeyDonkey999 credit 21,997.61 USDC to the Bybit deposit address `0x93b7e169…`. The same day at 10:27:14, Bybit 5 (`0xf89d7b9c864f589bbf53a82105107622b35eaa40`, Blockscout label "Bybit: Hot Wallet") pays 11,991 USDC to `0x09133414aa940fbe81a81d9c936275685c2aea88`, swept to Binance 48 six minutes later; then from 14 to 22 June it pays `0x529c2eef…` four times, 7,537 USDC. `0x09133414…` is the Binance customer deposit address to which DonkeyDonkey999 sent its October 2024 withdrawals (section 4.3). These are the timing and the destinations of a Bybit customer who moves money to the two places the accounts used. Bybit pays every customer from the same hot wallets: the customer is not provable from the chain (level L4, like PR 27's section 5).

### 4.3 DonkeyDonkey999 before June 2025, and a Stake.com deposit address shared with TBFMM (relations R5, R6)

- **October 2024, Binance.** DonkeyDonkey999's six withdrawals of 25 and 26 October 2024 (13,134.10 USDC) go to `0x09133414…`, which sweeps every inflow to Binance 48 (`0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245`, "Binance: Hot Wallet") within minutes, amounts equal: a Binance customer deposit address. The same address receives Bybit 5's 11,991 USDC on 13 June 2025 (section 4.2).
- **Stake.com deposit `0xbfaa1d49144c84dac4163704e5ba3e876a7c345a`.** DonkeyDonkey999 withdrew 282.883254 USDC to it on 28 October 2024. On 6 November 2024 it received gas from Stake.com 9 (`0x019d0706d65c4768ec8081ed7ce41f59eef9b86c`, nonce 606,556) and sent the 282.883254 USDC to Stake.com 9 94 s later: a Stake.com customer deposit address. Its Relay pages (archived by PR 27 too, never cited there) show two more payers, on BSC: **TBFMM** (300 USDC.e on 19 January 2026, 17:29 UTC) and **`0x283ad35049970a1d0ca4c766acfefa4f44f91298`** (431.67 on 13 February 2026). The same Stake.com account was credited by DonkeyDonkey999 and TBFMM, which already have a direct transfer between them (PR 27). Level L3; the BSC side is read from the Relay orders only.
- `0x283ad350…` is a Polymarket account without username and **without a single trade**: three deposits (22 and 23 January 2026, one bridged from BSC by `0x9e85dd02ee0f5af51dc503a13aa8f46effae8db9`) and three withdrawals to BSC (12 and 13 February 2026, to `0xe9e133684997cd3e8364b50d63205842ea1e879b` and to the Stake.com address). It uses Polymarket as a wallet. New to the repository.

### 4.4 A third network account on the same Bybit deposit address, 13 June 2025

The two unidentified pool payments into the Bybit deposit address `0x93b7e169…` that night (199.98 at 02:25:39 and 43,794.66 at 02:26:59 UTC), and a third of 2.00 on 10 July 2025, are withdrawals of **ILOVEYOUBABYZZ** (PR 27 network), read from their receipts. Between 01:42 and 02:27 UTC on 13 June 2025, 9TungSahur, DonkeyDonkey999 and ILOVEYOUBABYZZ credited the same Bybit account with 65,992.25 USDC. In the same minutes ILOVEYOUBABYZZ sent 43,794.84 to the Binance deposit address of PR 27 (known). New relative to PR 27, level L3.

### 4.5 Confirmed from PR 27 (relation R7)

On 13 January 2026, TBFMM sends 32 USDC.e and ILOVEYOUBABYZZ 2,073 USDC.e to DonkeyDonkey999 (same hash as their withdrawals); five minutes later DonkeyDonkey999 sends 2,073.61 through Relay to the Bybit deposit address on BSC. Recomputed from the receipts, unchanged.



## 5. The three other Inca accounts

Read for each account: every deposit and withdrawal with its receipt, every Relay order, and the full Polygon token history of the wallet each one withdraws to.

| Account | Funded by | Withdraws to | Then |
|---|---|---|---|
| PorcoRosso | Polygon service `0xf0fc40a6…` (June 2025), Relay orders from `0xfefea9427bef554cc572bc4e887a0b9642fd8f4e` on Ethereum, Base, Arbitrum, BSC and Monad (July and August 2026) | `0xfefea942…` only (110,089.87 on 13 June 2025, 63,066.80 on 22 June; Relay in 2026) | Relay and deBridge (110,089.87 and 110,084.02), `0x63071190…` |
| ricosuave666 | `0xf0fc40a6…` and the Fun.xyz CheckoutPool through its own deposit address `0xd58af4d241315b1778cb9e245605f447201f12ec` (each of 8 payments from `0xf09366c6…`, 67,000 USDC in all, is credited 28 to 52 s later); Relay from Arbitrum in January 2026 | `0xf09366c69108ddad2305ee1764a60efe92b48477` (2 × 499.91 on 11 June 2025, 162,636.60 on 13 June, 6,017.76, 72,680.33 and 9,183.62 on 23 and 24 June; in January 2026, 17,321.64 through Relay to the same address on Arbitrum and 25,000 to Solana `J4t48znSuoXVyfytFMBCu7Y5Y4RtmCvK985EkUAZKxVe`) | Mayan Swift 98,420 (15 June), `0xe559eb45…` 74,680.13 (26 June, section 5.1), LI.FI 11,693.55 |
| truthlord | `0xf0fc40a6…`, the Fun.xyz CheckoutPool, Relay from Solana `GeuDFmsBhiSndUUf8sie2wpnQHLhi55Be2yXACA6aDat` | `0x4d1489edf5236653ae36db319f5267e1a921a6de` (86,991.09 in 5 withdrawals, June and July 2025; Relay in 2026) | deBridge 49,985.57, `0x3c6db606…` 19,997.58, `0x169ec37a…` 11,557.24 |

Result:
- **No direct transfer** between any of these three accounts and the two others or the 19 network accounts (no shared hash, no matched pair, section 6).
- **No shared non-service funder.** The funders they share with each other and with 9TungSahur and DonkeyDonkey999 are services: the Fun.xyz CheckoutPool (operator nonce 551,866 to 1,055,337), the contract `0xf0fc40a6…` (called by at least three operators, nonces 12,694 to 25,040; it pays 3,110 recipients in the repository's Ballon d'Or sample), the Relay solver and depository.
- **No shared beneficiary.** None of their funders or recipients, nor any counterparty of their three exit wallets on Polygon, is a network account, a customer-specific address of PR 27 or one of the other Inca accounts (`verify.py`). Their exit wallets share only contracts and exchanges (Uniswap, deBridge, Relay, Binance 48, token contracts).
- **Not traced**: what leaves through deBridge, Relay, Mayan and LI.FI on the other chains, the Solana side of ricosuave666's and truthlord's Relay orders, and the unlabeled recipients in the last column. A link there is not excluded. WORK_LEFT.

### 5.1 ricosuave666 and the Israeli indictment

Israeli media reported in February and March 2026 an indictment, filed in the Tel Aviv District Court, of an Air Force reserve major and a civilian for betting on Polymarket with classified information about the June 2025 strike. No article names an account or a wallet. The defendants are not named. The figures quoted verbatim in the articles read on 6 November 2026, set against ricosuave666's on-chain record:

| Published | Source | ricosuave666 |
|---|---|---|
| "the bet yielded winnings of $162,663" | Jerusalem Post, 27 March 2026; Times of Israel, 27 March 2026; Ynet | redemption of 162,663.94 USDC on 13 June 2025, 11:57 UTC |
| "approximately $128,000 in profit" | Israel National News, 26 March 2026 | cash on the market 128,735.29 |
| "also allegedly bet on the timing of the operation's end and won again" | Jerusalem Post | "Israel announces end of military operations against Iran before July?", +6,195.35, June 16 to 24 |
| "bets on two scenarios, one predicting an attack by the end of January and another by the end of March"; "cancel some wagers" | Jerusalem Post | bought both "Israel strikes Iran by January 31, 2026?" and "… by March 31, 2026?" on 6 January 2026, sold both on 7 January |
| "change his username on the betting platform" | Jerusalem Post, Ynet | the account is now served as `Rundeep` |
| "Two days after the fighting ended … a digital wallet was allegedly opened for the officer, into which cryptocurrency was transferred" | Jerusalem Post | 26 June 2025, 14:07:14 UTC, two days after the 24 June ceasefire: 74,680.134173 USDC from the exit wallet to `0xe559eb45d13e9a2e0e5d69c181de790f38e4b9a0`, a wallet with no earlier transaction, plus 10 POL of gas from the same exit wallet 20 s later |

Three published details do **not** match or cannot be checked: the bet is described as "the strike would occur before July" (ricosuave666 made only +897.02 on "Israel military action against Iran before July?" and its winnings are on the Friday market); a September 2025 bet on Yemen "worth about $5,000" (ricosuave666 has no activity between 24 June 2025 and 6 January 2026); and the officer's "about NIS 200,000", which cannot be read on chain. The match of the published figures is compatible with ricosuave666 being the civilian's account. It is not an attribution: the articles name no account, and nothing here identifies a person. The other four Inca accounts show no figure from these articles.

## 6. Controls: are these money links rarer among comparable buyers?

`PLAN_CONTROLS.md` was committed (`f43270b`, 11:52:23 UTC) before any control data was collected and before the funders and recipients of the three other Inca accounts were read. Two amendments were made before any control flow was read: A1 (12:01:51 UTC) reads deposits and withdrawals with the `type` filter because one control has more than 100,000 activity rows (checked equal to full reads on 16 wallets), and A2 (12:07:32 UTC) raises the receipt cap from 4,000 to 5,000 instead of dropping the most active wallets. Both are deviations from the plan as first written, for the repository owner to review.

- **Population.** The market's whole trade tape (7,518 rows; every one of the 121 trades of the five Inca accounts on this market is in it). T, the first Yes trade at 0.90 or more, is 13 June 2025 00:00:21 UTC. 60 wallets bought at least 1,000 USDC of Yes at 0.50 or less between the market's opening and T: the five Inca accounts, ILOVEYOUBABYZZ (PR 27) and 54 controls, all analysed (fewer than the cap of 150, no sampling). Three controls are accounts that Inca flags for other Iran markets (`0x53af93e7…` Lol123555, `0xc0a00575…`, `0xfe6eee00…` Kingyossi); the plan does not exclude them.
- **Coverage.** 4,157 deposit and withdrawal rows of controls with their receipts, 795 Relay orders; 549 rows (13.2 %) have no counterparty in their own receipt (pUSD deposits through Relay, swap-only rows), against 17 of 118 (14.4 %) for the five Inca accounts. 469 recipients classified, 195 excluded as services (contract code or a Blockscout tag).

| Measure | Controls (54) | Inca three | Inca two (in PR 27) | One-sided Fisher p, Inca three vs controls (Holm) |
|---|---|---|---|---|
| M1 funder or recipient in PR 27's network set N27 | 0 (0 %, Wilson 0 to 6.6 %) | 0 of 3 | 2 of 2, by construction | 1.0 (1.0) |
| M2 non-service withdrawal recipient shared with another analysed wallet | 4 (7.4 %, 2.9 to 17.6 %) | 0 of 3 | 2 of 2: the Bybit deposit `0x93b7e169…` | 1.0 (1.0) |
| M3 transfer between two analysed wallets (same hash, or two or more matched legs) | 5 (9.3 %, 4.0 to 19.9 %) | 0 of 3 | 2 of 2: the three matched legs of 11 June 2025 (R1) | 1.0 (1.0) |

Reading:
- **The confirmatory test finds nothing for the three other Inca accounts.** They show none of the three money links, while a few controls do. Inca's trading heuristics grouped five accounts; the money links found concern only the two that PR 27 had already reached through their exits.
- **R1 is found by the fixed rule.** M3, written before the data, pairs DonkeyDonkey999's three withdrawals of 11 June 2025 with 9TungSahur's three deposits without being told where to look.
- **Links exist among ordinary buyers too.** Four controls (`0x6a8328b1…`, `0x8f42ae0a…`, `0x7c3db723…`, `0xdd225a03…`) form one group through three shared recipients and five direct transfers, and two others (`0x5e9c76f3…`, `0x8f7a4b41…`) share a direct transfer. Like group G in PR 27, they show that shared exits and transfers between accounts are not, by themselves, specific to the Iran network. They were not investigated further.
- **Power.** With three accounts, the test can only reject when the control rate is low. It was low for M1 (0 of 54), and none of the three had M1 either.
- Excluding the three Inca-flagged controls changes nothing: none of them has M1, M2 or M3.
- The plan's service rule (contract code at `latest`) classes EIP-7702 delegated EOAs such as `0x529c2eef…` as services. No effect here: within the analysed set only 9TungSahur pays `0x529c2eef…` directly.


## 7. Against PR 27 and the other studies

| Point | Source | What this check finds |
|---|---|---|
| TheOneWhoKnocks1312 and DonkeyDonkey999 in the network | PR 27 | Confirmed. Exact addresses, and the same accounts as Inca's 9TungSahur and DonkeyDonkey999 (profits to the dollar) |
| Their withdrawals of 13 June 2025 to the Crypto.com and Binance deposit addresses | PR 27 | Confirmed from the receipts |
| June 2025 trading "not compared" | PR 27 section 6 | Inca's report is that comparison, from trading heuristics; this note adds money relations: R1, R2, R3 |
| Payers of the Bybit deposit `0x93b7e169…` | PR 27 section 3.4 (4 accounts) | **Incomplete**: 9TungSahur and DonkeyDonkey999 paid it seven times in June 2025, through the Uniswap pool. Two other pool payments of 13 June (02:25 and 02:26 UTC) are ILOVEYOUBABYZZ's (section 4.4) |
| Relay pages of `0xbfaa1d49…` | PR 27 archives, not used | A Stake.com deposit shared by DonkeyDonkey999 and TBFMM (R6) |
| `0x852dc1c8…`, sink of `0xa6c22144…` | PR 27, "unlabeled service-like" | Also the sink of `0x529c2eef…`; still unidentified |
| Inca's five "high-likelihood insiders" | Inca, trading heuristics only | Three of the five have no money link to the other two or to the network in the first hops read. Inca's grouping by market does not imply a common owner; the money links found concern the two accounts already in PR 27 |
| One bettor indicted in Israel | Press, February and March 2026 | Published figures match ricosuave666 (section 5.1); no account is named |
| `0x3f77a673…` | `investigations/maduro-iran` phase 2 | Same role: hot wallet paying the gas of Polymarket deposit addresses |
| PorcoRosso, ricosuave666, truthlord elsewhere in the repository | `investigations/edge-polymarket` (`p8_wallets.csv`), `investigations/maduro-iran` phases 9 and 13 | Only as rows of mechanical universes of 2026 trades: in phase 13, PorcoRosso and ricosuave666 are "new wallets" not qualified and without alert; in phase 9, PorcoRosso has one `SIG_CTX` signal on 23 July 2026 (TEST split, score 0.21). No study of the repository analyses these accounts or their June 2025 trades |
| Shared funders `0x1929347e…`, `0xf0fc40a6…` | `investigations/ballon-dor-wallets` (3,077 and 3,110 recipients) | Services, as there |

## 8. Classification of the addresses used

| Address | Classification | Evidence |
|---|---|---|
| `0xa26792e2…` | deposit address credited to 9TungSahur | 4 inflows, each forwarded in 16 to 26 s after a gas top-up by a service hot wallet; each followed by one of 9TungSahur's 4 deposits (behaviour; Polymarket bridge has no record) |
| `0x3f77a673…`, `0xefce5b1c…` | hot wallets of a deposit service | nonces 35,812 and 44,285 in June 2025; gas for deposit addresses |
| `0x93b7e169…` | Bybit customer deposit | PR 27 (gas from Bybit: Deposit Funder 2, sweeps to Bybit) |
| `0x9063493a…`, `0x519fa16e…` | Crypto.com and Binance customer deposits | PR 27 |
| `0x09133414…` | Binance customer deposit | every USDC inflow swept to Binance 48 within 10 minutes, amounts equal |
| `0xbfaa1d49…` | Stake.com customer deposit | gas from Stake.com 9, full sweep to Stake.com 9 94 s later |
| `0x529c2eef…` | wallet of the unidentified service of `0xa6c22144…`; customer-specific not established | single gas funder = PR 27's relayer, all outflows to `0x852dc1c8…`; payers of several origins |
| `0x0bc03691…`, `0xf09366c6…`, `0x4d1489ed…`, `0xfefea942…` | personal exit wallets of the control `0x4d209741…`, ricosuave666, truthlord, PorcoRosso (no label; first activity and gas consistent; `0xfefea942…` tagged Farcaster) | token and transaction histories |
| `0xd58af4d2…` | ricosuave666's deposit address | 8 payments from its exit wallet credited 28 to 52 s later |
| `0xe559eb45…` | wallet first funded on 26 June 2025 by ricosuave666's exit wallet | nonce 0 at 14:12:32 that day, gas from the same wallet |
| Bybit 5, Bybit: Wallet 131, Crypto.com 6, Stake.com 9, Binance 48 | exchange hot wallets | Blockscout labels (single source) and behaviour |
| Fun.xyz CheckoutPool, `0xf0fc40a6…`, Relay solver and depository, RelayRouter, Mayan Swift, LI.FI, deBridge DlnSource | services and bridges | labels, operator nonces, recipient counts |

Labels come from the Blockscout metadata service, one source; the classifications above that matter rest on behaviour checked by `verify.py`.

## 9. Status, limits and work left

Status of the five accounts, in the four categories used in the repository:

| Account | ACCOUNTING_RECONCILED | TRACE_COMPLETE_TO_PUBLIC_FRONTIERS | WORK_LEFT | BLOCKED_BY_DATA |
|---|---|---|---|---|
| 9TungSahur | yes: 4 deposits and 12 withdrawals, each with its counterparty | yes for every withdrawal (exchange deposits, `0x529c2eef…`), except `0x93a2eb92…` (999.90, not classified) | `0x93a2eb92…` | no |
| DonkeyDonkey999 | yes: 19 deposits and 19 withdrawals. Five rows of October 2024 have no counterparty in their own receipt (USDC already on the proxy is swapped); the token history resolves them: Kraken 72 twice (283.0566 and 283.0), Binance 48 once (987.970091), and one withdrawal to itself re-deposited 30 s later | to exchange deposits and `0xa26792e2…` | its 2025 deposits through the Fun.xyz CheckoutPool and `0xf0fc40a6…` come from services whose customer is not public | origin of the Fun.xyz checkouts |
| PorcoRosso | yes | no: deBridge and Relay outflows of `0xfefea942…` not followed | other chains | no |
| ricosuave666 | yes | no: Mayan, LI.FI, `0xe559eb45…` (USDT0 bridged to Ethereum on 14 July 2025), Solana `J4t48znS…` | other chains | Mayan order not read |
| truthlord | yes | no: deBridge and unlabeled recipients of `0x4d1489ed…` | other chains, Solana funder `GeuDFmsB…` | no |

Limits:
- **Selection.** The five accounts were chosen by Inca; two of them were already in PR 27 through their exits. The comparison of section 6 is confirmatory only for the other three.
- **Behavioural classifications.** Deposit addresses are identified by gas and sweep behaviour, as in PR 27. A shared deposit address means the same exchange or service account was credited, not the same person.
- **Hot wallets.** Bybit, Binance and Crypto.com pay all customers from the same wallets; relation R4 is timing only.
- **Press.** The indictment itself was not read; only articles. Their figures disagree on the market and on totals, and the JNS text could not be read verbatim (its figures are not used).
- **Labels.** One source (Blockscout metadata).
- **Not traced** (WORK_LEFT): bridged outflows of the three other accounts, the BSC side of the Stake.com address, the other recipients of the control `0x4d209741…`.

## 10. Local rarity pipeline (PR 27, `iran-exit-rarity-2026-11-06`)

Checked on 6 November 2026 between 11:20 and 12:40 UTC, without changing anything:
- **Freeze intact in git.** At PR 27's head `dd9df29`, the 129 files listed in `PROTOCOL.lock` all have their recorded SHA-256, and `PROTOCOL.lock` itself has the SHA-256 `734f3be9fc19d55d007146aabd964d4b72db6daf80077f31e28d54f7807a16c1` registered in the freeze index (frozen 06:47:39 UTC, no later re-freeze in the index history).
- **Live run not verifiable.** The collection was relaunched at 08:17 UTC from the external disk `TravailExterne` (journal). That disk is not mounted on this Mac today; no `col_30`, `col_40` or `ana_50` process is running. Whether the comparator collection finished and whether `ana_50` ran cannot be checked from here. `gel.py liste` reports "LOCK DISPARU" for the study's path on that disk, which means the disk is absent, not that the lock changed.
- No result of that study is used in this note.

## 11. Reproduction

- `scripts/collect.py`: sequential collector; at most two run at once. Polymarket data-api and gamma, Relay `requests/v2?user=`, Etherscan v2 (Polygon), public Polygon RPC (receipts, `eth_getCode`), Blockscout metadata, Polymarket bridge status. Raw responses outside git under `~/Projects/Polymarket-inca-raw-20261106/raw/`.
- `PLAN_CONTROLS.md`: fixed before the control data (commit `f43270b`), amendments A1 and A2 and a time erratum after it.
- `scripts/rules.py`, `scripts/test_rules.py` (positive and negative controls), `scripts/build.py` (measures), `scripts/package.py` (evidence), `scripts/relations.py` (index).
- `verify.py`: recomputes everything from `evidence/` with its own code; `python3 -I verify.py`.


