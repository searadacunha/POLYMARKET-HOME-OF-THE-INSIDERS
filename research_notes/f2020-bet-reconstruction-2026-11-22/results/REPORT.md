# Funded bets of four f2020 payees: positions, outcomes and profit

Follow-up of [PR 110](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/110). That PR lists four Polymarket trading addresses that bought shortly after a credit from the commingled `0xf2020c…c423` route, where ChangeNOW provenance is only `POSSIBLE`. This note reconstructs what each bet bought, at what price, how the position ended and what it earned after fees. It then rebuilds every later position of the same addresses. Captures ran from 2026-11-22T10:07:24Z to 2026-11-22T10:52:25Z. Chain reads stop at Polygon block 97,757,999 (2026-11-22T10:14:28Z). PR 110's files and conclusions are not modified.

## Results

| Wallet | Market | Exact position | Stake | Result | Net gain/loss | Delay after funding | Anomaly impression |
|---|---|---|---:|---|---:|---|---|
| W1 `0x9fed…1d1b` | [Bitcoin Up or Down - October 25, 11:10AM-11:15AM ET](https://polymarket.com/event/btc-updown-5m-1792941000) | BUY Down (outcome index 1), 6.461537 shares at 0.6500 as taker; then SELL 6.460000 Down at 0.67; BUY 7.017544 Down at 0.57; REDEEM 7.019081 Down | 4.302889 pUSD, fee 0.102890 included | WIN: bought Down, Down won; first lot sold early, re-bought, redeemed | +2.824012 on the market; first lot alone -0.073132 | 3 min 57 s | Medium (A medium, B medium, C low) |
| W2 `0xd74d…ccf3` | [Bitcoin Up or Down - October 1, 9:25PM-9:30PM ET](https://polymarket.com/event/btc-updown-5m-1790904300) | BUY Down (outcome index 1), 3.000000 shares at 0.4000 as taker; then SELL 3.000000 Down at 0.62 | 1.250400 pUSD, fee 0.050400 included | WIN: bought Down, Down won; closed before resolution | +0.560130 on the market; first lot alone +0.560130; 0.042330 more paid to a third party | 7 min 27 s | Low (A medium, B low, C low) |
| W3 `0x569c…741d` | [Bitcoin Up or Down - September 24, 5:55AM-6:00AM ET](https://polymarket.com/event/btc-updown-5m-1790243700) | BUY Down (outcome index 1), 6.969697 shares at 0.3300 as taker | 2.407870 pUSD, fee 0.107870 included | LOSS: bought Down, Up won | -2.407870 on the market; first lot alone -2.407870 | 28 min 57 s | Medium (A high, B low, C medium) |
| W4 `0xadd9…8df9` | [Will the highest temperature in Busan be 22°C on September 26?](https://polymarket.com/event/highest-temperature-in-busan-on-september-26-2026) | BUY No (outcome index 1), 0.184633 shares at 0.0300 as maker; then BUY 4.810000 No at 0.03; REDEEM 4.994633 No | 0.005539 pUSD, fee 0.000000 included | LOSS: bought No, Yes won | -0.149839 on the market; first lot alone -0.005539 | 1 h 6 min 28 s | Low (A high, B low, C low) |

Stake: the mission's transaction, price plus fee, in pUSD (Polymarket's USD collateral). Net: every cash flow of the address on that market, fees included, once it resolved. Result: whether the outcome bought in that transaction won. Delay: block time of the f2020 credit to block time of the first buy. The impression is the higher of B and C. The three scores are explained below. None of them is an accusation.

### Ranking, most to least noticeable

1. **W3** `0x569c…741d`: its only flag is statistical. After the funding its first buys won 803 of 1462 5-minute BTC markets, against 776.902 implied by the prices paid (z 1.414, p 0.1573). That is above all 15 of its own controls and at the 93% point of the 58 pooled controls, without being significant. It enters 99.9% of windows within 30 s of the open, so it buys before the window carries information. Net +18.06 on 4,161.92 engaged. The credit was its only new money in the window.
2. **W1** `0x9fed…1d1b`: its bet used 98.9% of its balance 3 min 57 s after a credit worth 92.7% of that balance, which ended a 21 d 0 h 55 min 58 s pause. Afterwards it bet at the same sizes as before (largest market 313.99 against 273.37 before). It was funded by 1,910.63 USDC from an unlabelled contract and 116.00 pUSD from a key. Net -269.20, z 0.257.
3. **W4** `0xadd9…8df9`: a key-signed account (nonce 18,006) that received 30 f2020 credits from W16 to W46. The studied order was a 0.03 resting bid on the outsider, which lost. Later its first buys did worse than their prices implied (z -0.53; first 30 days -1.832).
4. **W2** `0xd74d…ccf3`: stakes of about a dollar, 95 of 136 later positions closed before resolution, 373 small payments to a third party, net -46.51, z -0.087.

Not found for any of the four: a statistically supported edge, a run of long-shot wins, or a bet that preceded information the market did not already show.

## The four bets

### W1 · [0x9fed84d86211d077277426db9831d74756531d1b](https://polygonscan.com/address/0x9fed84d86211d077277426db9831d74756531d1b) · [Polymarket profile](https://polymarket.com/profile/0x9fed84d86211d077277426db9831d74756531d1b)

- **Account:** Safe proxy, owner `0x3345aa1c6b7bbbab7645065b585f7a32c0e3ba27`, nonce 1 at block 97,759,159.
- **Funding:** [tx](https://polygonscan.com/tx/0xf33adda7050db46a8db7cdb65e6ba5567a6db36d5723a1583fc418421875b884) at 2026-10-25T15:07:06Z: 4.030236 USDC from `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423`. The last activity before it was 21 d 0 h 55 min 58 s earlier. Balance just before the first trade: 4.349035 pUSD, 92.7% of it from the credit.
- **Market:** [Bitcoin Up or Down - October 25, 11:10AM-11:15AM ET](https://polymarket.com/event/btc-updown-5m-1792941000). Condition `0x90c2141b69cd6f19ca7151323b870a2c8a67ac2f459bd9311d4fc8a4d8459526` ([Gamma](https://gamma-api.polymarket.com/markets?closed=true&condition_ids=0x90c2141b69cd6f19ca7151323b870a2c8a67ac2f459bd9311d4fc8a4d8459526)).
- **Bought:** Down, token `52055281677910196584104409969759823766754424659408302592406772846187080616247`, in [tx](https://polygonscan.com/tx/0x3fa0acff0fc531091701c3fbea371c125b770e4c3a534dc9555f5addb4130aac) at 2026-10-25T15:11:03Z: 6.461537 shares at 0.6500, fee 0.102890, filled as taker. The token id was recomputed on chain from the condition and outcome slot. It equals Gamma's `clobTokenIds` entry for that outcome.
- **Resolution:** Down won. The payout vector was read from the Conditional Tokens contract. ConditionResolution [tx](https://polygonscan.com/tx/0x0a27b7a3fa7f43576af830d1c69bfac51c83ea8eb9eb6878fdeaec281a803b02) by oracle `0x58e1745bedda7312c4cddb72618923da1b90efde`. Its question id equals Gamma's.
- **Rule and prices:** Up if the Chainlink BTC/USD 60-second TWAP stream ends at or above its value at the window start. Published start 80605.31, final 80589.60, margin -15.71. Binance BTCUSDT 1-second candles, an independent spot proxy and not the resolution source, had moved -1.99 when the order filled 63 s into the window, and -12.00 at the end.
- **Same market:** 871 buying addresses, 66.6% of them with their larger side on the winner. 170 other addresses bought Down within 30 s of this order, at 0.400–0.750. By notional this address ranks 439 of 871 (median buyer 8.60).
- **Whole position:** 8.423289 pUSD engaged for 13.479081 shares, average 0.6249 with fees, fees 0.323270, sales 4.228220, redemptions 7.019081, still held 0.000000. Net +2.824012 pUSD. Every operation is in [focus_operations.csv](focus_operations.csv).
- The first lot was sold 84 s later at 0.67. After two fees it lost 0.073132. A new buy 123 s after the first was redeemed at 1.00 and carried the profit.

### W2 · [0xd74d2d3a4016079ff49743f831d1a31b668cccf3](https://polygonscan.com/address/0xd74d2d3a4016079ff49743f831d1a31b668cccf3) · [Polymarket profile](https://polymarket.com/profile/0xd74d2d3a4016079ff49743f831d1a31b668cccf3)

- **Account:** deposit wallet, owner `0x51309c0dcc257a86d5b0ac4bac9d3a85539dd5c3`, nonce 1 at block 97,759,159.
- **Funding:** [tx](https://polygonscan.com/tx/0xeb056655d1c4248f685bdc61e063f27f9c7fa415fcb1cb01c92f76eb897bfe10) at 2026-10-02T01:18:18Z: 3.567014 USDC.e from `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423`. The last activity before it was 15 min 39 s earlier. Balance just before the first trade: 9.887029 pUSD, 36.1% of it from the credit.
- **Market:** [Bitcoin Up or Down - October 1, 9:25PM-9:30PM ET](https://polymarket.com/event/btc-updown-5m-1790904300). Condition `0x21c38ba0761e1510ce74a7ad26c873cd3c742dd8f3bb1f2eee398c0176f2cd16` ([Gamma](https://gamma-api.polymarket.com/markets?closed=true&condition_ids=0x21c38ba0761e1510ce74a7ad26c873cd3c742dd8f3bb1f2eee398c0176f2cd16)).
- **Bought:** Down, token `68065464311831938095232827725787564666826453154674288246419598757013202676468`, in [tx](https://polygonscan.com/tx/0x3699f4fc60ad6d5d7cc2903deba6ec448cf5684777df5dd1e56b0d1d50f8a94c) at 2026-10-02T01:25:45Z: 3.000000 shares at 0.4000, fee 0.050400, filled as taker. The token id was recomputed on chain from the condition and outcome slot. It equals Gamma's `clobTokenIds` entry for that outcome.
- **Resolution:** Down won. The payout vector was read from the Conditional Tokens contract. ConditionResolution [tx](https://polygonscan.com/tx/0xb088d601ed9b1283f7299ddf9f93ec0260750cf015c875f2e6d0c6b428534606) by oracle `0x58e1745bedda7312c4cddb72618923da1b90efde`. Its question id equals Gamma's.
- **Rule and prices:** Up if the Chainlink BTC/USD 60-second TWAP stream ends at or above its value at the window start. Published start 84584.04, final 84575.19, margin -8.85. Binance BTCUSDT 1-second candles, an independent spot proxy and not the resolution source, had moved -7.82 when the order filled 45 s into the window, and -25.99 at the end.
- **Same market:** 915 buying addresses, 66.9% of them with their larger side on the winner. 142 other addresses bought Down within 30 s of this order, at 0.160–0.490. By notional this address ranks 796 of 915 (median buyer 6.83).
- **Whole position:** 1.250400 pUSD engaged for 3.000000 shares, average 0.4168 with fees, fees 0.099870, sales 1.810530, redemptions 0.000000, still held 0.000000. Net +0.560130 pUSD. Every operation is in [focus_operations.csv](focus_operations.csv).
- The direction was right. Holding the 3 shares would have paid 3.000000; the sale 36 s later returned 1.810530. Around the two orders, small transfers to `0xdc9c35bf585fba2a39bcd17bdfe343277b595cad` add 0.042330. That address is a key, not a Polymarket contract, and not this deposit wallet's owner.

### W3 · [0x569c5f3850c31bcb8590ef1926fb69e0f42f741d](https://polygonscan.com/address/0x569c5f3850c31bcb8590ef1926fb69e0f42f741d) · [Polymarket profile](https://polymarket.com/profile/0x569c5f3850c31bcb8590ef1926fb69e0f42f741d)

- **Account:** deposit wallet, owner `0xc8ad9c1accf3fa119347a29f0398fb7c4e1afeec`, nonce 1 at block 97,759,159.
- **Funding:** [tx](https://polygonscan.com/tx/0x5091f0f0243a6bb383c0d7e01a656fa1edfe63187d976f692dbfe028cb073f1f) at 2026-09-24T09:26:12Z: 22.079897 USDC from `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423`. The last activity before it was 15 h 46 min 04 s earlier. Balance just before the first trade: 22.364206 pUSD, 98.7% of it from the credit.
- **Market:** [Bitcoin Up or Down - September 24, 5:55AM-6:00AM ET](https://polymarket.com/event/btc-updown-5m-1790243700). Condition `0xaf10b9a2e7d992c1fd35cc11849c09d53ebaaaad092cdce899eb4a779e656449` ([Gamma](https://gamma-api.polymarket.com/markets?closed=true&condition_ids=0xaf10b9a2e7d992c1fd35cc11849c09d53ebaaaad092cdce899eb4a779e656449)).
- **Bought:** Down, token `54730462898423900631398302528999603045788997651755589734001105338707860030494`, in [tx](https://polygonscan.com/tx/0x56a320f48ad0ad9eafee8d76fe3b1087e7ce9501804e9a0c7110debce5163bad) at 2026-09-24T09:55:09Z: 6.969697 shares at 0.3300, fee 0.107870, filled as taker. The token id was recomputed on chain from the condition and outcome slot. It equals Gamma's `clobTokenIds` entry for that outcome.
- **Resolution:** Up won. The payout vector was read from the Conditional Tokens contract. ConditionResolution [tx](https://polygonscan.com/tx/0x242c0f2ebd553b0ea3eba52b0069c3a0beeffa63bcf445595fb39cdd2e9eb280) by oracle `0x58e1745bedda7312c4cddb72618923da1b90efde`. Its question id equals Gamma's.
- **Rule and prices:** Up if the Chainlink BTC/USD 60-second TWAP stream ends at or above its value at the window start. Published start 83208.24, final 83234.27, margin +26.03. Binance BTCUSDT 1-second candles, an independent spot proxy and not the resolution source, had moved +30.12 when the order filled 9 s into the window, and +18.06 at the end.
- **Same market:** 884 buying addresses, 58.9% of them with their larger side on the winner. 135 other addresses bought Down within 30 s of this order, at 0.310–0.500. By notional this address ranks 674 of 884 (median buyer 6.02).
- **Whole position:** 2.407870 pUSD engaged for 6.969697 shares, average 0.3455 with fees, fees 0.107870, sales 0.000000, redemptions 0.000000, still held 0.000000. Net -2.407870 pUSD. Every operation is in [focus_operations.csv](focus_operations.csv).

### W4 · [0xadd9ab62b2c22151c661b99821cbb7433df98df9](https://polygonscan.com/address/0xadd9ab62b2c22151c661b99821cbb7433df98df9) · [Polymarket profile](https://polymarket.com/profile/0xadd9ab62b2c22151c661b99821cbb7433df98df9)

- **Account:** key (no code), nonce 18,006 at block 97,759,159.
- **Funding:** [tx](https://polygonscan.com/tx/0x862e0947bd7c3e660fc76bd5705f0ffdc17c707a1a149f9705767732aaf8fb82) at 2026-09-26T04:54:32Z: 47.740725 USDC.e from `0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423`. The last activity before it was 9 min 36 s earlier. Balance just before the first trade: 115.171306 pUSD, 41.4% of it from the credit.
- **Market:** [Will the highest temperature in Busan be 22°C on September 26?](https://polymarket.com/event/highest-temperature-in-busan-on-september-26-2026). Condition `0x5ef8a6de47a93de0e2c467e5f2cb426502d65afa8bde273b7eb4f2c7ea07b905` ([Gamma](https://gamma-api.polymarket.com/markets?closed=true&condition_ids=0x5ef8a6de47a93de0e2c467e5f2cb426502d65afa8bde273b7eb4f2c7ea07b905)).
- **Bought:** No, token `2463336633153656247268945689795644816833160426782461675926114204755582678148`, in [tx](https://polygonscan.com/tx/0x2c4ff87943aadc7b36c96be229a8ce0aaaf86bc7c461c7a7e6fbef4a80962639) at 2026-09-26T06:01:00Z: 0.184633 shares at 0.0300, fee 0.000000, filled as maker. The token id was recomputed on chain from the condition and outcome slot. It equals Gamma's `clobTokenIds` entry for that outcome.
- **Resolution:** Yes won. The payout vector was read from the Conditional Tokens contract. ConditionResolution [tx](https://polygonscan.com/tx/0x9748408cb598c50bd233e9cfe38ab066be3904c660d5c9c403ef0ff4842d1db0) by oracle `0xd91e80cf2e7be2e162c6513ced06f1dd0da35296`. Its question id equals Gamma's.
- **Rule and readings:** the highest NOAA reading at Gimhae Intl Airport (RKPK) on the local day, in whole °C ([resolution source](https://www.weather.gov/wrh/timeseries?site=rkpk)). The Iowa Environmental Mesonet METAR archive has 27 reports for 2026-09-26 KST (UTC+9). The day's maximum, 22 °C, appears only in the 2026-09-26 00:00 KST report. Without it the maximum is 21 °C. When the order filled at 15:01 KST, the last report was 2026-09-26 15:00 KST 21.00 C. YES had traded at 0.940 or more in the previous 10 minutes. NO needed a later reading of at least one degree more than the maximum, or a resolution that left out the midnight report.
- **Same market:** 224 buying addresses. 2 other addresses bought NO within 30 s, at 0.030–0.030. This address had a resting bid that sellers hit. When the bid was placed is off chain and unknown.
- **Whole position:** 0.149839 pUSD engaged for 4.994633 shares, average 0.0300 with fees, fees 0.000000, sales 0.000000, redemptions 0.000000, still held 0.000000. Net -0.149839 pUSD. Every operation is in [focus_operations.csv](focus_operations.csv).
- The second fill came 260 s after the first, at the same price. The NO shares were redeemed for 0 11 h 39 min 02 s later.

## Every later position

A position is a market whose first buy came at or after the funding. Data run to the last activity captured. Rows come from the complete paginated Polymarket v2 activity. Outcomes come from payout vectors read on chain: W1 39 markets, W2 136 markets, W3 1462 markets, W4 903 markets are also resolved in Gamma, and every one agrees. Shares still held are valued with their on-chain balance.

| | W1 | W2 | W3 | W4 |
|---|---:|---:|---:|---:|
| Markets (trades) | 39 (70) | 136 (351) | 1462 (1540) | 911 (1517) |
| Still open at capture | 0 | 0 | 0 | 2 |
| First buy won / lost | 28 / 11 | 38 / 98 | 803 / 659 | 687 / 186 |
| Profitable / unprofitable markets | 26 / 13 | 39 / 97 | 798 / 664 | 628 / 245 |
| Closed before resolution | 23 | 95 | 78 | 213 |
| Capital engaged (buys + fees) | 2,494.85 | 296.30 | 4,161.92 | 6,903.78 |
| Polymarket fees | 56.42 | 10.07 | 129.77 | 29.52 |
| Net PnL of the positions | -269.20 | -46.51 | +18.06 | -264.81 |
| Rewards and rebates | 0.00 | 0.00 | +10.00 | +112.20 |
| Small payments to a third party | 0.00 | -12.77 | 0.00 | 0.00 |
| Return on capital | -10.8% | -15.7% | 0.4% | -3.8% |
| Largest gain / loss | +82.42 / -238.48 | +12.32 / -9.57 | +6.42 / -4.26 | +22.12 / -33.70 |
| Top-3 markets, share of gains | 48.7% | 37.2% | 1.0% | 6.7% |
| Main side at ≤ 0.20 (won) | 0 (0) | 55 (8) | 4 (0) | 22 (1) |
| Median / largest stake per market, before | 15.54 / 273.37 | 0.93 / 1.62 | 2.99 / 5.09 | 3.23 / 24.87 |
| Median / largest stake per market, after | 38.98 / 313.99 | 1.50 / 16.21 | 2.89 / 4.53 | 5.43 / 62.00 |
| Up/down entries: median s into window | 134 | 240 | 10 | 591 |
| Collateral at funding → peak → end | 4.35 → 310.60 → 1.55 | 9.89 → 82.04 → 0.00 | 22.37 → 134.27 → 0.34 | 115.29 → 367.24 → 174.47 |
| Other money in / out | 2026.63 / 1760.23 | 96.76 / 60.34 | 0.00 / 50.00 | 247.69 / 9.94 |

- W1: largest gain +82.42 on Bitcoin Up or Down - November 19, 2:10AM-2:15AM ET (`0x041f85e2c9d725508835af2294ced463cb175e696381668432ffac2ea89692c7`); largest loss -238.48 on Bitcoin Up or Down - November 19, 2:20AM-2:25AM ET (`0xb9a0ebaf2d51780ee95617b1792b4d16149c663d8755cc6fbb2f2846c7924f4d`).
- W2: largest gain +12.32 on Bitcoin Up or Down - October 15, 8:00AM-8:15AM ET (`0xc5eab2a7c1a1b48e71966377273c71342472747b3754585b7c0dfa3f0a00c786`); largest loss -9.57 on Bitcoin Up or Down - October 15, 7:00AM-7:15AM ET (`0x00c0cb42280253e9f828474fcfd87e99379971fc43f7b0b3f72ef8984296c9a4`).
- W3: largest gain +6.42 on Bitcoin Up or Down - September 24, 11:00AM-11:05AM ET (`0xc584434c3dc081b8b9e298935dfa9506233b0ea7e3f18028204386cdd14646ee`); largest loss -4.26 on Bitcoin Up or Down - October 3, 7:50AM-7:55AM ET (`0x870f5197bc936ce3145b92378c7ac4df9f5f7b94c414403aa82fb27fba9462d4`).
- W4: largest gain +22.12 on Will CF América vs. Deportivo Toluca FC end in a draw? (`0x2608d2ef3640343ae74061c26a5d521bdc1d9333902020bb9a539a1938797d6f`); largest loss -33.70 on Gold Up or Down - November 4, 3:30PM-3:45PM ET (`0x481bfe813ab1678fb152fbe8bf8da73ceeacd98e6128a95140fb729033d35d41`).

Net PnL adds sales, redemptions, merges and the payout value of shares still held, then subtracts buys and fees. Rewards, rebates and third-party payments are on their own lines. Every position is in [positions_after_funding.csv](positions_after_funding.csv).

## Does any of it look like anticipation?

The test uses one observation per market: the first buy, its price p and whether that outcome won. Brackets of one weather city-day count once. If the bettor knows nothing beyond the price, Σp is the expected number of wins and z = (wins − Σp) / √Σp(1−p). Later buys and sales do not enter, so averaging up after a move cannot inflate the score. Controls are 15 buyers per focus market with USD 0.5–20 there, taken in SHA-256 order of market and address without reading their results. Each gets the same test over the 30 days after the funding date.

| | n | wins | expected | z | two-sided p | percentile among its controls | among all controls | z before funding |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| W1, first 30 days | 39 | 28 | 27.307 | 0.257 | 0.7974 | 67% of 15 | 64% of 58 | -0.862 |
| W2, first 30 days | 136 | 38 | 38.418 | -0.087 | 0.9309 | 50% of 14 | 55% of 58 | -0.418 |
| W3, first 30 days | 1462 | 803 | 776.902 | 1.414 | 0.1573 | 100% of 15 | 93% of 58 | -1.014 |
| W4, first 30 days | 377 | 245 | 258.716 | -1.832 | 0.0669 | 0% of 14 | 9% of 58 | -1.985 |

Over the whole later period z is 0.257 (W1), -0.087 (W2), 1.414 (W3) and -0.53 (W4). The smallest first-30-day p among the four wallets is 0.0669, against 0.05/4 = 0.0125 after a correction for four tests. Control z values run from -2.651 to 2.548 (median -0.391), and 13.8% of controls have |z| ≥ 2. Ordinary small traders of the same markets therefore spread more widely than a normal curve.

Timing points the same way. W3 enters within 30 s of the window opening in 99.9% of its 1462 up/down markets, when the window has produced no information. On BTC 5-minute markets with a measurable Binance move at entry, W1 followed the move in 14 of 19 and W2 in 11 of 39. Base rate for the delay: PR 110 has 397 f2020 receipts followed by a buy. 10% were followed within 182 s and half within 4059 s. W1's delay sits at the 13% point.

## Three separate scores

| Wallet | A. Provenance opacity | B. Behavioural anomaly | C. Apparent informational advantage |
|---|---|---|---|
| W3 | High: one hop from the commingled rail, originator not visible on chain; 1 f2020 credit W16–W46; f2020 = 100.0% of new money in the window | Low: no flag | Medium: above 95pct of controls |
| W1 | Medium: one hop from the commingled rail, originator not visible on chain; 3 f2020 credits W16–W46; f2020 = 0.2% of new money in the window | Medium: focus stake majority of balance | Low: no flag |
| W4 | High: one hop from the commingled rail, originator not visible on chain; 30 f2020 credits W16–W46; f2020 = 16.2% of new money in the window | Low: no flag | Low: no flag |
| W2 | Medium: one hop from the commingled rail, originator not visible on chain; 1 f2020 credit W16–W46; f2020 = 3.6% of new money in the window | Low: no flag | Low: no flag |

**A** is High when the rail recurs (at least 10 credits) or brings at least half of the new money in the window. Otherwise it is Medium. Low would need an attributable originator, which f2020 never gives. **B** counts four flags: delay at or below the 10th percentile of the f2020 base rate; median stake after funding at least 3 times, or at most a third of, the median before; top three markets ≥ 50% of gains; focus stake ≥ 50% of the balance. **C** counts four: the focus bet won while buying against the visible move; first-30-day z ≥ 2; z ≥ 3; z above 95% of its own controls. 0 flags = Low, 1 = Medium, 2 or more = High. These rules were written in this session after the first descriptive numbers had been seen, not preregistered. One wallet's score says nothing about the other axes.

## Observations kept with their uncertainty

- The mission gives wallet 4 as `0xadd9ab62b2c22151c661b99821cbbafb9cc9361`, 39 hex digits, so not a valid address. Its first 29 hex digits are those of `0xadd9ab62…8df9`. Its last 10 are those of `0xe129d1e0…cc9361`, another f2020 payee in W39–W46 for which PR 110 observed no later trade. The mission's amount, time, block and bet transaction all belong to `0xadd9ab62b2c22151c661b99821cbb7433df98df9`, which is the address studied here.
- Chainlink's TWAP stream is off chain. The start and final values are Polymarket's published `eventMetadata`, not recomputed. Binance spot moved the same way in all three BTC markets, but it is only a proxy.
- The Busan readings come from the IEM METAR archive, not a capture of the NOAA page. The official outcome, YES at 22 °C, can only be reproduced if the 00:00 KST report counts in the local day.
- W1's later USDC arrives from `0xba4eee20f434bc3908a0b18da496348657133a7e`, an unlabelled contract. In [an earlier funding graph](../../investigations/edge-polymarket/sources/funding/data/graphe/0xf54dae096aaf3d18c417ecfb454512191902b546.json) of this repository it pays 49,987.45 USDT twice on 16 November 2024. W1's pUSD outflows go to 6 contracts with no Polymarket activity. Whether they are bridge deposit addresses, exchanges or something else is not established.
- W2's recipient `0xdc9c35bf…5cad` took 373 payments of at most 0.090000 (12.769546 in total) and 3 larger transfers (10.541049). It also sent W2 0.059656 once. Reading the small ones as an app or bot fee comes from their pattern only.
- Lifetime PnL rebuilt from the rows, compared with Polymarket's `user-pnl` point that PR 110 recorded at 2026-11-21T00:00:00Z: differences W1 +4.70, W2 -0.00, W3 -0.00, W4 +159.17. W4's difference is close to the 170.86 this method gives to pre-funding positions whose share count comes from the API. Before 28 April 2026, fees were taken in shares, so those counts are slightly too high. W1's +4.70 is not explained. After the funding no such gap exists: the API cash equals the on-chain transfers (see Method).
- 13 of the 60 control histories hit the 10,000-row capture cap. Their positions stop one day before the cap.
- First version of the test: it used each market's side with the larger buy and that side's average price. One control scored z = 22 that way by buying a side after it had moved, so the test was switched to the first buy. The first version gives, over the first 30 days, W1 0.261, W2 -0.425, W3 1.414, W4 -2.277. In neither version does any wallet reach z = +2.

## Method

1. **Activity:** `data-api.polymarket.com/v2/activity` returns every type in ascending order, read with its cursor until `has_more` is false. Profile fields are dropped on read. PR 110's sampled buys are all present: W1 48/48, W2 16/16, W3 16/16, W4 384/384.
2. **Receipts:** the funding and every transaction on the four focus markets are decoded from Polygon receipts (`OrderFilled`, ERC-1155 and ERC-20 transfers). Each running position equals `balanceOf` at the same block. Each API amount on those markets equals the decoded receipt.
3. **Outcomes:** `payoutNumerators` and `payoutDenominator` are read at block 97,758,236 for the 2,540 markets touched after the funding. Position ids are recomputed with `getCollectionId` and `getPositionId`.
4. **Ledger:** every USDC, USDC.e and pUSD transfer of each wallet, from 2,000 blocks before its funding to block 97,757,999. Opening balance plus replayed transfers equals the closing `balanceOf` for all four. In the transactions the API lists, on-chain cash equals API cash, with gaps of W1 0.000000, W2 0.000000, W3 0.000000, W4 0.000000.
5. **PnL:** per market, sales + redemptions + merges + payout value of shares still held − buys (fees included). A redemption zeroes the redeemed token, because `redeemPositions` burns the whole balance.
6. **Controls, base rate and scores:** as above.

Reproduce offline from the repository root: `python3 -I research_notes/f2020-bet-reconstruction-2026-11-22/verify.py`. It blocks network sockets, rebuilds every file in `results/` in a temporary folder and compares the bytes. To recapture, run `python3 -I scripts/collect.py <step>` from the note folder. That step uses the network.

## Limits

- Funding is traced one hop back. The ChangeNOW order, the depositor and the people behind the addresses are not identified.
- The test looks for a persistent edge. It cannot rule out one informed bet among many uninformed ones, and four wallets give little power.
- Order placement times are off chain. For a maker fill such as W4's, the moment of decision is unknown.
- Controls come from the same focus markets. They stand for small traders of those markets, not the whole platform.

PR 110 inputs, pinned at its head: [wallet_funding.csv](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/blob/8b633048290e7174945bc811b16cf0b11b4d8ceb/investigations/weekly-funding-intelligence/results/wallet_funding.csv) · [weekly_funding.csv](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/blob/8b633048290e7174945bc811b16cf0b11b4d8ceb/investigations/weekly-funding-intelligence/results/weekly_funding.csv) · [weekly_funding.json](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/blob/8b633048290e7174945bc811b16cf0b11b4d8ceb/investigations/weekly-funding-intelligence/results/weekly_funding.json) · [accounts snapshot](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/blob/8b633048290e7174945bc811b16cf0b11b4d8ceb/investigations/weekly-funding-intelligence/snapshot/accounts.json.gz)
