# Inca Digital's three other Iran accounts: bridged exits traced, and two more accounts on ricosuave666's wallets

Date: 6 November 2026. Branch `research/inca-bridges-pulser-20261106`, built on PR 29's head `c69ce98` (which is built on PR 27). Nothing in PR 27, PR 29 or PR 30 is modified. Every figure below is recomputed offline by `python3 -I verify.py` from `evidence/` (gzip copies of the raw responses; their SHA-256 are in `SHA256SUMS.txt`). Each money leg is in `EVIDENCE_INDEX.csv` with its full hash or signature, chain, time (UTC), parties, amount and evidence level.

Evidence levels used here:
- **Confirmed**: the link is in the transaction itself (same hash on both sides, an order identifier carried from the source chain to the fill, a transfer signed by the sending wallet).
- **Supported**: the link rests on behaviour (a deposit address recognised by its forward pattern, a customer deposit address shared by two senders, gas paid by one wallet for another).
- **Hypothesis**: an interpretation that the chain cannot prove (common ownership, the identity behind an account).

No person is identified. Insider trading is not established by anything below.

## Summary

1. **ricosuave666's bridged exits converge on one Solana wallet, and come back to its exit wallet (confirmed).** PR 29 left the Mayan, LI.FI and deBridge exits of ricosuave666's exit wallet `0xf09366c69108ddad2305ee1764a60efe92b48477` untraced. All four Solana-bound orders (13, 15 and 24 June 2025, 14 September 2025) name the same receiver, `J4t48znSuoXVyfytFMBCu7Y5Y4RtmCvK985EkUAZKxVe`, already seen as the receiver of ricosuave666's Relay order of 6 January 2026. Each fill is found on Solana and tied to its order (deBridge order id in the fill; Mayan Swift order state account in the fill). On 16 July 2025, `J4t48znS…` burns 60,077.603926 USDC through Circle CCTP with the exit wallet as recipient on Ethereum.
2. **Two more Polymarket accounts use ricosuave666's personal wallets in both directions (transactions confirmed; common control supported, not proven).**
   - **AugsburgFClover** (`0x509cd9d117e06a082df649a06e317195f048240a`): four of its withdrawals of June 2025 credit the exit wallet under the same hash; its June 2025 deposits are paid from the exit wallet through two deposit addresses; it withdraws to the exit wallet again through Relay in September 2025 (Polygon) and April 2026 (Arbitrum); it is funded from `J4t48znS…` through the intermediate Solana wallet `6pJEdTi1…`. Every Polymarket-withdrawal credit ever received by the exit wallet on Polygon comes from ricosuave666 or AugsburgFClover, and from no other account.
   - On **6 January 2026**, 2 hours after ricosuave666 had bought "Israel strikes Iran by January 31 / March 31, 2026?", it withdrew 25,000 USDC.e; the money went through `J4t48znS…` and `6pJEdTi1…` into AugsburgFClover, which bought the same two markets between 12:27 and 12:56 UTC. ricosuave666 sold its own positions the next morning.
   - **metushelah** (`0x4e74acf9447df43029fedc1fe592775110de6a9f`), active only on 15 and 16 September 2025: funded twice from `J4t48znS…` through the intermediate Solana wallet `3cCK8epV…` and Relay, it bet on "Israel strike on Yemen by September 19?" and "Will Israel strike Yemen on September 16 ET?" (+404.32 USDC on 5,357 staked), then withdrew everything to `J4t48znS…`.
3. **The 74,680.134173 USDC wallet funds a third account and shares a Binance deposit address with the exit wallet.** `0xe559eb45d13e9a2e0e5d69c181de790f38e4b9a0` (first funded with 74,680.134173 USDC by the exit wallet on 26 June 2025, PR 29) pays the deposits of the Polymarket account **meeeeeeeeeeeeeeee** (`0x03727dd8df63b9aaedebb30db24a7f07522fa86b`; confirmed for the Relay leg, supported for the deposit-address leg), which bet on Israel–Yemen markets from July to September 2025 and on Iran in January 2026. The same wallet sends 3,000 USDC to the Binance deposit address `0xaa00faedb1146785792f00e2feac69adbdaba42b` on Polygon, and the exit wallet sends 20.627 ETH to that same address on Ethereum (supported: one Binance customer account credited by both). It moves 65,649.069103 USDT to Ethereum and sends 65,362 USDT to the unlabeled `0x43d44a06325db643f8eb5ac998b5355978069bfc`.
4. **Published indictment figures and these accounts.** Four amounts quoted from the Israeli indictment in March 2026 match ricosuave666 to the dollar: 162,663 (redemption), 6,195 and 17,704 (two later markets) and 74,680 (the crypto transfer, here 74,680.134173 USDC on 26 June 2025). The 400-dollar profit on the Yemen markets "by 19 September" and "on 16 September" matches metushelah's +404.32 on exactly those two markets, and the 24,000 dollars on three named markets matches ricosuave666's +23,900.23 on two of them. The indictment summaries state that the civilian defendant bet "through several accounts". No article names an account. This is compatibility of figures, not an attribution.
5. **truthlord and PorcoRosso: bridged exits resolved, no convergence (confirmed).** truthlord's three deBridge orders (49,985.57 USDC, June and August 2025) all pay `HfGp55mpjgQpZS7sgn5cwggdSHFyVY3qeevxHNekwN9x` on Solana; its 2026 orders pay itself on BSC. PorcoRosso's deBridge order of 13 June 2025 pays 43.381968520308833448 ETH to its own address on Ethereum (order id confirmed in the fill), and its LI.FI Mayan-CCTP order of 22 June pays 63,072.68 USDC to `HdxkiXqe…`, a Solana address with tens of thousands of transactions a month (service-like). The three Solana destinations are distinct from each other and from PR 27's Solana addresses.
6. **Pulser (PR 30).** All 27 transfers of PR 30 are re-read from Etherscan receipts (independent of PR 29's node): 27 of 27 match. New: Pulser paid the **first deposit** of `0x0bb95597b85b89f83f66929be66edcf4ae7f9725`, the second wallet of group F (200 USDC.e on 4 December 2025, same hash on both sides), and received 140.3568 USDC.e back 7 minutes later. This link is not exclusive: Pulser paid the first deposit of 7 of the 16 Polymarket accounts it transacts with directly, and the five accounts of PR 29's control group with the most direct partners (15 to 19 each, against a control median of 0) include Pulser, cashy and Car. Groups F and E remain separate: no transfer between them was found.

## 1. ricosuave666: from the exit wallet to Solana and back

### 1.1 The four Solana-bound orders (confirmed at order level)

| Order (Polygon) | Time UTC | Bridge | Sent | Receiver read from the order | Fill on Solana | Received by `J4t48znS…` |
|---|---|---|---|---|---|---|
| `0x5da2a61dd3c01df76dece631bd66f0c0d1c35fe44e9213171f96616987c2789d` | 13 Jun 2025 01:00:11 | LI.FI (Phantom) to Mayan Swift, key `0x51466fd7…` | 2,290.551883 USDC | `J4t48znS…` (LI.FI non-EVM receiver event) | `57dpdLhiLDuD5QmT…` 01:01:17 | 15.611415587 SOL |
| `0xad096e3d5351bde74ea50dab8e1e4bd1837525d0d8013b00dfa778280173de65` | 15 Jun 2025 21:08:29 | Mayan Swift, gasless order, key `0xa17cf61a…` | 98,419.998631 USDC | `J4t48znS…` (`destAddr` in the signed order, Wormhole chain 1) | `3VqNtzFxyV1QomvN…` 21:09:38 | 98,378.852846 USDC |
| `0x2869df2eb42836b094cb59d36123a32e7dda3636e1b0854d92a79840e24633c5` | 24 Jun 2025 21:09:01 | LI.FI (Phantom) to Mayan Swift, key `0xf42e5919…` | 9,403 USDC | `J4t48znS…` | `Vv5p238nDpF2u813…` 21:09:38 | 64.309615064 SOL |
| `0x7711afb050503b2349b664567776284583589f901d2b6e1b2ce804a21e552622` | 14 Sep 2025 11:56:44 | deBridge DLN, order `0xc2c2f654a3666411a7df472002245475af17094929b9cedd4de7a7df1437cdbe` | 317.271572 USDC | `J4t48znS…` (`receiverDst` of `CreatedOrder`) | `5SQUJEfVXmFMh64n…` 11:56:46 | 1.259690717 SOL, the exact take amount |

How each fill is tied to its order:
- deBridge: the 32-byte order id of the source `CreatedOrder` event is in the instruction data of the Solana fill, signed by the DLN taker `2snHHreX…` through the DLN destination program `dst5MGcFPo…`.
- Mayan Swift: Mayan's public index (`explorer-api.mayan.finance/v3/swap/order-id/SWIFT_<key>`) gives for each key the fill signature and the order state account; the state account is present in that fill on chain, the fill runs the Mayan Swift program `BLZRi6frs4…`, and the amount received is the amount the index reports. The order key itself is read from the `OrderCreated` event on Polygon.
- Full signatures are in `EVIDENCE_INDEX.csv` (rows L01 to L08).

`J4t48znS…` is an older personal wallet (first transaction November 2023, 3,155 signatures). After the June fills it swaps USDC and SOL in transactions co-signed by a counterparty (program `61DFfeTK…`), and on 16 July 2025 at 21:58:13 it burns 60,077.603926 USDC through CCTP (`DepositForBurn`, destination domain 0 = Ethereum, mint recipient `0xf09366c6…`), minted to the exit wallet on Ethereum at 21:58:35 (tx `0xac53eccf6a3105855c47d207361184c2a1b616d90e1bf0567497f64aec4b4ea9`). Four minutes later the exit wallet swaps it on Uniswap; on 29 July 2025 it sends 20.627325794318736 ETH to a Binance deposit address (section 3.2).

### 1.2 What PR 29 left open, now closed

| PR 29, section 5 and 9 | Now |
|---|---|
| "Mayan Swift 98,420 (15 June)", "Mayan order not read" | Read: to `J4t48znS…`, filled 69 s later |
| "LI.FI 11,693.55" | Two LI.FI orders (2,290.55 and 9,403), both to `J4t48znS…` through Mayan Swift |
| "Solana `J4t48znS…`" (Relay, January 2026) | The same receiver as every bridged exit of the exit wallet; it returns 60,077.60 USDC to the exit wallet on Ethereum |
| "`0xe559eb45…` (USDT0 bridged to Ethereum on 14 July 2025)" | Polygon PoS exit of 65,649.069103 USDT at 17:36:35, then 65,362 USDT to `0x43d44a06…` (section 3) |
| A Yemen bet in the press "cannot be checked" on ricosuave666 | Found on metushelah, an account funded and cashed out through `J4t48znS…` (section 2.2) |

## 2. Two more accounts on ricosuave666's wallets

### 2.1 AugsburgFClover (`0x509cd9d117e06a082df649a06e317195f048240a`, pseudonym Celebrated-Shack)

Money between AugsburgFClover and ricosuave666's wallets, in both directions:

| Date UTC | Direction | Amount | How the link is read | Level |
|---|---|---|---|---|
| 11 Jun 2025 19:06:44 | exit wallet → deposit address `0xc0809d7e28dd52a35887bbd822635e13f3c6d7a4` → AugsburgFClover (19:25:10) | 998.818736 USDC sent, 998.249067 USDC.e credited | address forwards in 8 s; its only USDC in and out | supported |
| 13 Jun 2025 00:58:53 | AugsburgFClover → exit wallet | 2,289.770368 USDC.e out, 2,289.541657 USDC in | same hash `0x287aabc7…` | confirmed |
| 16 Jun 2025 10:05:21 | exit wallet → deposit address `0x5b9a5de307d566cac0cc02c32416c91998ff7e19` → AugsburgFClover (10:05:39) | 1,001.898091 sent, 1,000.454555 credited | forward in 8 s, credit 18 s after | supported |
| 23 Jun 2025 18:41:55 | AugsburgFClover → exit wallet | 700.302978 USDC | same hash `0xcbd92845…` | confirmed |
| 24 Jun 2025 15:08:35 and 18:48:25 | AugsburgFClover → exit wallet | 377.750882 and 8.642476 USDC | same hashes `0x3282d81f…`, `0xeda99492…` | confirmed |
| 11 Sep 2025 17:11:10 | `J4t48znS…` → `6pJEdTi1YST6irUvRy1BxW5iXzFASryLSMBepbMSNFoA` | 1.1 SOL | signed by `J4t48znS…` | confirmed |
| 11 Sep 2025 17:12:34 | `6pJEdTi1…` → AugsburgFClover (Relay `0xb16b9f4b…`) | 1.09910912 SOL in, 244.659317 USDC.e out | Relay order | confirmed |
| 14 Sep 2025 11:38:37 | AugsburgFClover → exit wallet (Relay `0x30923e8a…`, Polygon to Polygon) | 527.694203 USDC.e in, 527.271472 USDC out | Relay order; 18 minutes later the exit wallet sends 317.27 USDC to `J4t48znS…` by deBridge | confirmed |
| 6 Jan 2026 12:25:56 | `J4t48znS…` → `6pJEdTi1…` | 24,987.099103 USDC | signed by `J4t48znS…` | confirmed |
| 6 Jan 2026 12:26:40 | `6pJEdTi1…` → AugsburgFClover (Relay `0x46d3370a…`) | 24,987.099103 USDC in, 24,977.074454 USDC.e out | Relay order | confirmed |
| 28 Apr 2026 07:54:45 | AugsburgFClover → exit wallet on Arbitrum (Relay `0xd2efe205…`) | 20,873.019696 USDC.e in, 20,858.405667 USDC out | Relay order | confirmed |

All Polymarket-withdrawal credits of the exit wallet on Polygon (paid by the Uniswap pool `0xd36ec33c…` that serves withdrawals) were matched to their account by hash: 6 from ricosuave666 (251,518.135131 USDC) and 4 from AugsburgFClover (3,376.237993 USDC), none from any other account. The exit wallet's other Polygon credits are AugsburgFClover's Relay order above and one USDT0 bridge-in (1,496.08 on 16 October 2025).

**The 6 January 2026 sequence.**

| Time UTC | Event |
|---|---|
| 08:15:37 | ricosuave666 deposits 38,666.20 USDC.e |
| 08:18:51 to 11:40:41 | ricosuave666 buys "Israel strikes Iran by January 31, 2026?" (6,197.59) and "… by March 31, 2026?" (2,000) |
| 11:54:51 | ricosuave666 withdraws 25,000 USDC.e (Relay `0x4a21fc7f…`), 24,982.496121 USDC credited to `J4t48znS…` at 11:55:01 |
| 12:25:56 | `J4t48znS…` sends 24,987.099103 USDC to `6pJEdTi1…` |
| 12:26:40 to 12:26:45 | `6pJEdTi1…` bridges it to AugsburgFClover through Relay (24,977.074454 USDC.e) |
| 12:27:43 to 12:56:45 | AugsburgFClover buys "by January 31, 2026?" (7,000 in five orders) and "by March 31, 2026?" (2,000) |
| 7 Jan, 05:41:19 to 05:42:53 | ricosuave666 sells both positions (9,319.59 and 2,533.44), then withdraws 17,321.64 to its exit wallet on Arbitrum (PR 29) |

A post on X by Lookonchain about ricosuave666's two January bets is dated 7 January 2026, 02:12 UTC (press review). AugsburgFClover kept its positions: the January one lost, the March one redeemed 4,895.95 on 28 April 2026, withdrawn the same minute to the exit wallet on Arbitrum.

AugsburgFClover's earlier bets: "Israel military action against Iran before July?" (998.24 bought on 11 June 2025, 19:25, +1,291.52), "Israel announces end of military operations against Iran before July?" (+286.42), "Khamenei out as Supreme Leader of Iran by Friday?" (−200), "Israel strike on Yemen by September 5?" (−60), two football and boxing markets.

### 2.2 metushelah (`0x4e74acf9447df43029fedc1fe592775110de6a9f`, pseudonym Distorted-Gaiters)

| Time UTC | Leg | Amount | Level |
|---|---|---|---|
| 15 Sep 2025 21:06:26 | `J4t48znS…` → `3cCK8epVbySrZMoecevF6keiVKLmDs11oCMTCTgxYJd8` | 6.0 SOL (signed by `J4t48znS…`) | confirmed |
| 15 Sep 2025 21:06:50 | `3cCK8epV…` → metushelah, Relay `0x6d67609a…` (credited 21:06:58) | 5.99911912 SOL → 1,385.776073 USDC.e | confirmed (the Relay id is the last 32 bytes of the Polygon calldata) |
| 16 Sep 2025 10:05:12 | `J4t48znS…` → `3cCK8epV…` | 20.0 SOL | confirmed |
| 16 Sep 2025 10:06:35 | `3cCK8epV…` → metushelah, Relay `0xea7fdcb6…` (credited 10:06:40) | 20.000012022 SOL → 4,651.101731 USDC.e | confirmed |
| 16 Sep 2025 18:00:52 | metushelah → `J4t48znS…`, Relay `0x2c1dd890…` | 6,441.204432 USDC.e → 6,436.688402 USDC | confirmed (fill `AzViX9FP…` credits exactly the order output) |

Its only markets: "Israel strike on Yemen by September 19?" (2,059 bought, 2,168.45 redeemed, +109.45) and "Will Israel strike Yemen on September 16 ET?" (3,298 bought, 3,592.87 redeemed, +294.87). Four minutes after the cash-out, `J4t48znS…` swaps 6,250 USDC for 26.19 SOL.

### 2.3 What links these accounts, and what does not

- **Confirmed:** money moves between ricosuave666, AugsburgFClover and metushelah through two wallets that sign their own transactions, the exit wallet `0xf09366c6…` and `J4t48znS…`, in both directions and over ten months (June 2025 to April 2026).
- **Supported:** the simplest reading is that the same key holder chooses the deposit and withdrawal destinations of the three accounts. Alternatives exist (a person paying or being paid by another person's accounts) but would have to explain withdrawals in both directions and the intermediate wallets used once each (`6pJEdTi1…`, `3cCK8epV…`).
- **Not established:** who controls them.

## 3. The 74,680.134173 USDC wallet `0xe559eb45…`

### 3.1 Its outflows (in USDC unless stated)

| Time UTC | To | Amount | Then | Level |
|---|---|---|---|---|
| 26 Jun 2025 14:07:14 | (in) from the exit wallet | 74,680.134173 | PR 29: first transaction of `0xe559eb45…`, gas from the exit wallet | confirmed |
| 26 Jun 14:12:32 | `0x31c88bbb26203b52fd34fc44cde7843557b8b518` | 1,000 | forwarded 22 s later; **meeeeeeeeeeeeeeee** credited 999.612718 USDC.e at 14:13:00, its first deposit | supported |
| 26 Jun 14:31:06 | `0xaa00faedb1146785792f00e2feac69adbdaba42b` | 3,000 | swept to Binance 48 at 14:42:50 | supported (Binance deposit) |
| 14 Jul 15:28:29 to 7 Sep 2025 | `0x83324381d25f3cb09318fe85773365e93fdab7be` | 8,500 in 5 transfers | each forwarded within 6 minutes to MEXC 8 or MEXC 11 (Blockscout labels): a MEXC customer deposit address; MEXC 8 pays 4,999.9936 back to `0xe559eb45…` at 16:08:06 on 14 July | supported |
| 14 Jul 15:33:31 | Uniswap | 65,680.14 USDC swapped to 65,659.07 USDT0 | 16:17:06: 65,649.069103 USDT0 burned to the Polygon PoS bridge | confirmed |
| 14 Jul 17:36:35 (Ethereum) | (in) PoS bridge exit | 65,649.069103 USDT | 17:38:59 and 17:40:35: 10 and 65,352 USDT to `0x43d44a06…` | confirmed |
| 14 Sep 2025 20:14:22 | meeeeeeeeeeeeeeee, Relay `0x670d47d3…` | 1,498.640759 USDC → 1,498.042354 USDC.e | | confirmed (Relay id in the calldata) |

`0x43d44a06…` (Ethereum, no label) received its first funds the same day, 3 USDT at 16:27:23 from `0x1e5e118e098463380418f94f424217022159fe6e`. That wallet (nonce 0 to 9 over a year, a personal wallet) also paid the Ethereum gas of `0xe559eb45…` at 16:32:11 and of `0x43d44a06…` at 09:20 on 15 July, one minute before its first outgoing transfer, after receiving 10 USDT0 and 2 POL from `0xe559eb45…` on Polygon (supported: one operator priming the three wallets). `0x43d44a06…` sends 38,348 USDT on 15 July to `0x2b37b97628c9397f7e58f04a20056ecac85609aa`, an aggregator with more than 10,000 transfers and 553 senders, among them Bybit and Binance hot wallets: the trace stops there (service frontier).

meeeeeeeeeeeeeeee (`0x03727dd8…`, pseudonym Old-Friend) bet 100 to 732 USDC on "Another Houthi strike on Israel before July?", "Israel strikes Yemen by Friday?" (16 July 2025), "by August 31?", "Will Israel strike Yemen on September 15 ET?", "Israel strikes 3 different countries by September 30?", and on 8 January 2026 on "Israel strikes Iran by January 16 / January 31, 2026?". None of its figures appears in the press.

### 3.2 One Binance account credited by both wallets (supported)

`0xaa00faedb1146785792f00e2feac69adbdaba42b` is tagged "Binance Deposit" by Blockscout and behaves as one: on Ethereum each of its six ETH credits since October 2023 is swept to Binance 14 within an hour; on Polygon its USDC credit is swept to Binance 48. It is credited by `0xe559eb45…` (3,000 USDC, Polygon, 26 June 2025) and by ricosuave666's exit wallet (20.627325794318736 ETH, Ethereum, 29 July 2025). A Binance deposit address credits one customer account: the same Binance account received money from the wallet that got the 74,680.134173 USDC and from the exit wallet. Who holds that account is not visible on chain.

## 4. Published indictment figures against these accounts

Sources (press review of 6 November 2026; the indictment itself and its case number were not found): Bizportal/Takdin 27 and 31 March 2026 (`bizportal.co.il/takdin/news/article/20029617`, `…/20029842`, near-verbatim summaries of the indictment, Hebrew), Maariv 26 March 2026 (`maariv.co.il/news/law/article-1301703`), Kan (`kan.org.il/content/kan-news/defense/1019056/`), Walla (`news.walla.co.il/item/3826657`), The Guardian 30 January 2026.

| Published (quoted) | Source | On chain | Match |
|---|---|---|---|
| winnings of 162,663 dollars | Kan, Walla, 13tv | ricosuave666 redeemed 162,663.94 on "Israel military action against Iran by Friday?" (13 June 2025) | to the dollar |
| profit of 128,400 / 128,432 dollars | Takdin / Maariv | ricosuave666 cash on that market 128,735.29 | within 0.3 % |
| further profits of 6,195 and 17,704 dollars | Maariv, JNS | ricosuave666: +6,195.35 "Israel announces end of military operations against Iran before July?"; **+17,704.88 "Israel strike on Iran on June 24?"** | to the dollar |
| bets on the end of the operation by July, US action by Saturday and a strike on 24 June, 24,000 dollars | Takdin | ricosuave666 traded exactly these three markets: +6,195.35, −2,971.16, +17,704.88 | the two gains sum to 23,900.23 |
| the second defendant transferred to the officer 74,680 dollars in crypto, converted to 200,000 shekels | Takdin | exit wallet → `0xe559eb45…` 74,680.134173 USDC, 26 June 2025, two days after the ceasefire | to the dollar |
| Yes bets on Israel striking Yemen by 19 September and on 16 September; profit 400 dollars | Takdin | metushelah: those two markets only, +109.45 and +294.87 = **+404.32** | within 1.1 % |
| about 5,000 dollars won on a September Yemen bet | Walla | metushelah staked 5,357 and redeemed 5,761.32 | depends on what "won" counts |
| the second defendant bet through several accounts | Takdin; "several profiles", Maariv | ricosuave666, AugsburgFClover and metushelah share the exit wallet and `J4t48znS…` | consistent |
| bets by end of January and end of March 2026, some cancelled; username changed | Maariv, Takdin | ricosuave666 bought and sold both on 6 and 7 January 2026; served today as `Rundeep` (PR 29) | consistent |
| the user "recently transferred their bets to two other accounts" | The Guardian | 6 January 2026: 25,000 from ricosuave666 to AugsburgFClover, which bought the same two markets | consistent |

Reading: the published figures and the accounts' records agree to the dollar on four amounts and within 1.1 % on the Yemen profit, and the two accounts found here explain the details that PR 29 could not match on ricosuave666 alone (the Yemen bets). This makes it very likely that the indictment describes the money of these accounts. It does not identify anyone: no source names an account, and no wallet here is attributed to a person.

## 5. truthlord and PorcoRosso

| Account | Order (Polygon) | Time UTC | Sent | Receiver | Level |
|---|---|---|---|---|---|
| truthlord, exit wallet `0x4d1489edf5236653ae36db319f5267e1a921a6de` | deBridge `0x46096f6e…` (tx `0x8210149c…`) | 16 Jun 2025 07:40:43 | 19,998.047682 USDC (take 19,979.024709 USDC on Solana) | `HfGp55mpjgQpZS7sgn5cwggdSHFyVY3qeevxHNekwN9x` | confirmed (order) |
| | deBridge `0x8b4630b0…` and `0xe16cfb90…` | 20 Aug 2025 20:04:55 and 20:05:29 | 1,001.777096 and 28,985.749932 USDC | `HfGp55mp…` | confirmed (order) |
| | deBridge `0x90b04bf4…`, `0x258c6c0c…`, `0x29731aa2…` | 18 to 21 Apr 2026 | 200.99, 200.80 and 471.29 USDT0 | itself on BSC (USDT) | confirmed (order) |
| PorcoRosso, exit wallet `0xfefea9427bef554cc572bc4e887a0b9642fd8f4e` | deBridge `0x89fcc5557ea9140a42c7490de394b3581ed3d75050a565788587746ca69604a8` (tx `0x641e71f9…`) | 13 Jun 2025 00:53:45 | 110,083.989739 USDC | itself on Ethereum: 43.381968520308833448 ETH at 00:54:59 (`FulfilledOrder` with the same id) | confirmed (order id at both ends) |
| | LI.FI (Jumper) Mayan CCTP, tx `0xfb2996b7…` | 22 Jun 2025 00:52:29 | 63,072.677418 USDC | `HdxkiXqeN6qpK2YbG51W23QSWj3Yygc1eEk2zwmKJExp` | confirmed (order) |

### 5.1 truthlord on Solana: one loop, one fresh wallet

- **Fills (confirmed at order level).** The three deBridge orders are filled into `HfGp55mp…`'s USDC account `CDYN5tLW3QXYbLBSCsvSZH3D3QLvc3A3toVGNByah3An` at 07:41:35 on 16 June 2025 (`5VXqchPm55rd1WHk…`, +19,979.024709 USDC) and at 20:04:55 and 20:06:16 on 20 August 2025 (`nPAWmgFM4bseAXXx…` +999.20016, `8ZF5HDCfEL4yMjKm…` +28,957.860335); each fill carries its order id in the instruction data.
- **A loop within truthlord's own wallets (confirmed).** `HfGp55mp…` (first active 15 May 2025, 2,287 signatures) sends 3,000 USDC on 9 June and 7,697.512264 USDC on 12 June 2025 to `GeuDFmsBhiSndUUf8sie2wpnQHLhi55Be2yXACA6aDat`, the Solana wallet that funds truthlord through three Relay orders (October 2025 and January 2026, 20,981.19 USDC.e in all, PR 29). Money leaves truthlord, crosses to Solana and comes back to it.
- **A fresh wallet (confirmed transfer).** Fifteen minutes after the June fill, at 07:55:50, `HfGp55mp…` sends 19,979.024710 USDC to `ERgKoqmGtmeTy7iUXF8r3nGnd5N5FDA8aU4fBZ79AA6i`, whose first transaction this is (118 signatures in all, June 2025 to August 2026). Its next real transfer sends 5,000 USDC to `HeqfEokQgMYiXU75ijYijNvvJu3oPnLTC6ReFYQUH3ZS` the same day; most of its other early transactions are address-poisoning spam. Eight minutes after the August fills, `HfGp55mp…` swaps 14,978.530248 USDC for a token (mint `C29ebr…`) through Jupiter and puts the same amount in a Jupiter DCA order.
- None of `HfGp55mp…`, `GeuDFmsB…`, `ERgKoqmG…` or `HeqfEokQ…` appears in ricosuave666's or PorcoRosso's transactions read here, nor in PR 27's network files.
- PorcoRosso's Ethereum address has more than 10,000 transactions (an active trading wallet since April 2023). `HdxkiXqe…` has more than 29,000 signatures between 5 October and 5 November 2026 alone: a service-like address, not followed.
- No receiver of these orders is a receiver of ricosuave666's, of the network or of the two other Inca accounts. A link through what these wallets did next is not excluded (section 7).

## 6. Pulser and group F (PR 30)

### 6.1 Independent check of PR 30 (confirmed)

The 27 transactions of `DIRECT_TRANSFERS.csv` (PR 30, copied here as `data/pr30_direct_transfers.csv`) were re-read from Etherscan's v2 proxy (receipts and transactions, chain 137), independently of the drpc node used by PR 29. 27 of 27 have status success, a USDC.e transfer from the stated sender to the stated receiver for the stated amount (to 0.000002), and logs identical to the drpc copy. All 27 are calls to the same contract, `0xd216153c06e857cd7f72665e0af1d7d82172f494`, the one that carries Polymarket's proxy withdrawals in this sample.

### 6.2 Pulser and `0x0bb95597…` (group F)

| Time UTC | Leg | Hash | Level |
|---|---|---|---|
| 4 Dec 2025 19:05:33 | Pulser → `0x0bb95597…` 200.0 USDC.e, the **first deposit** of `0x0bb95597…` (profile created 18 November 2025) | `0x5d68fa366a958f8457bac7106d0a2106711d4055cb885fe6d5247df3c8b8f2c7` | confirmed (same hash, WITHDRAWAL and DEPOSIT) |
| 4 Dec 2025 19:12:43 | `0x0bb95597…` → Pulser 140.3568 USDC.e | `0x80ccdfee56f397eb184c9d486d1fb60eb77550b37c6a59ca087255b42c633499` | confirmed |
| 9 Dec 2025 16:15:20 | `0x0bb95597…` → `0xbbcab5377bbca9cccbc48d0a7afbeaf78c741f90` 250 USDC.e | `0xaf0bc26973cff40ad0748e796090a47cd12169358a476e0900ed04aa91a0825d` | confirmed (transfer) |

PR 27 had grouped Pulser and `0x0bb95597…` by two shared Relay recipients; phase 3 of `investigations/maduro-iran` mentions a direct link without a hash. These two hashes are that direct link. On the February 2026 market, `0x0bb95597…` bought 1,150 USDC of Yes at 0.23 at 05:55:05 on 28 February and Pulser 220 at 0.22 at 05:58:47 (phase 2, `TABLE5_population_iran.csv`); Pulser had bought 2,000 at 0.10 on 26 February (check J5).

### 6.3 How specific are these direct links? (controls)

- **Direct partners.** For each of PR 29's 60 analysed early Yes buyers, the number of distinct counterparties whose code is Polymarket's proxy (EIP-1167 clone of `0x44e999d5…`): control median 0, 37 of 54 controls have none. The five highest are controls: cashy 19, `0x8f7a4b41…` 18, Pulser 16, Car 16, `0xdd225a03…` 15. Pulser, cashy and Car are among the most connected ordinary buyers, not outliers of the Iran network.
- **First deposits.** Pulser paid the first deposit of 7 of its 16 direct Polymarket partners (`0x0484ced2…`, `0x0bb95597…`, `0x1e179ce5…`, DorShw, SignalX1, NGRGlobal, xyz11235). Funding a new account is a habit of Pulser, so the group F link does not single out `0x0bb95597…`.
- **A resolver community.** `0xbbcab537…`, paid by `0x0bb95597…`, proposes and disputes prices on UMA's optimistic oracles on Polygon (40 calls to UMA's oracle contracts, with 750 USDC.e bonds; check J4). Car withdrew 10,700 USDC.e to it and received 250 from it, and Car's counterparty `0x3e8379fa…` is another UMA proposer (168 oracle calls). Direct payments among these heavy users (bonds, loans, peer-to-peer) are a plausible ordinary explanation.
- **Groups F and E stay separate.** No transfer between Pulser, cashy, Car or `0x0bb95597…` and the 19 network accounts or their customer deposit addresses (PR 29's M1 = 0 for the controls; the new partners checked here are not in the network either).

## 7. Accounting (no double counting)

Transfers, positions and profits are kept apart.
- **Profits** are cash on each market (sells plus redemptions minus buys), per account: ricosuave666 in section 4 and PR 29; metushelah +404.32 (check E4); AugsburgFClover −2,498.46 over all its markets, the 7,000 lost on "by January 31, 2026?" included (check G3).
- **Transfers** are counted once per leg in `EVIDENCE_INDEX.csv`. A bridge order and its fill are two rows of one transfer (sent and received); the received amount is net of fees.
- **Positions** (amounts bought) are not money flows and are not summed with transfers.

## 8. Limits and work left

- **Mayan Swift fills** are tied to their orders through Mayan's index (state account present in the fill), not by deriving the state account from the order hash.
- **Solana coverage.** The Solana histories were read with the public RPC (both Helius keys of the pool were exhausted): `J4t48znS…` for June, July and September 2025 and January 2026, plus every signature of its USDC account; `HfGp55mp…` for June and August 2025 plus its USDC account on the fill days; the first 15 transactions of `ERgKoqmG…`. Months outside these windows were not read.
- **Labels** come from Blockscout's metadata service only; every classification that matters also rests on behaviour.
- **Frontiers.** The trace stops at exchanges (Binance, MEXC), at the aggregator `0x2b37b976…`, at `HdxkiXqe…`, and at the request-for-quote swaps of `J4t48znS…`.
- **Not done:** the flows of `HfGp55mp…` outside June and August 2025 and of `ERgKoqmG…` after its first 15 transactions; the BSC side of truthlord's 2026 orders; the 8 pUSD recipients of `0x0bb95597…` in May 2026 (EIP-7702 accounts with one delegate, `0xe6cae83b…`); a control test of "two accounts sharing a personal exit wallet" on comparable buyers (the population's exit wallets were not collected).
- **Press.** The indictment text was not found; the comparison relies on press summaries.

## 9. Reproduction

- `scripts/collect_sol.py` (adapted from PR 27's collector: public Solana RPC, Helius, Etherscan v2 including its proxy module, Relay, plain HTTP) and PR 29's `scripts/collect.py` (Polymarket, Relay, Etherscan Polygon, receipts, code, labels). At most two collectors ran at once. Raw data outside git: `~/Projects/Polymarket-inca-bridges-raw-20261106/raw/` (new) and `~/Projects/Polymarket-inca-raw-20261106/raw/` (PR 29, plus the new receipts).
- `scripts/abi.py`: stdlib decoders (deBridge `CreatedOrder` and `FulfilledOrder`, LI.FI `LiFiTransferStarted`, base58), with `scripts/keccak.py` from PR 28.
- `scripts/test_decoders.py`: synthetic positive and negative tests of the decoders.
- `scripts/package.py`: copies exactly the raw files that `verify.py --raw` reads into `evidence/` and writes `SHA256SUMS.txt`.
- `scripts/build_index.py`: writes `EVIDENCE_INDEX.csv` from the same files.
- `verify.py`: `python3 -I verify.py` recomputes every check from `evidence/`; result in `verification.json`.
