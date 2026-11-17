# Historical order book and fees: sources read on 17/11/2026

Web research by two sub-agents (public pages only, no account). Full answers, details and the list of what could not be verified are in `book_and_fees_research.json`.

## Historical order book: PARTIAL

Polymarket itself publishes no historical order book. Its /book and /books endpoints return only the current resting book, keyed by token_id alone, with no time parameter. /prices-history returns a single price series ({t, p}); the docs call it an "observed price" and never say whether it is the midpoint or the last trade. The orderbook subgraph stores only fills (OrderFilled and OrdersMatched events), never resting orders. Historical L2 depth exists only in archives that third parties recorded live, and the earliest dates found are Oct 11, 2025 (Telonex, paid), Oct 14, 2025 (Dome), Nov 2025 (PredictionData, paid), Feb 2026 (TickFoundry, paid, and the free PMXT archive, whose downloader starts at 2026-02-21T16:00Z) and Mar 2026 (Marketlens, paid). One vendor, PolymarketData, claims full-ladder 1-minute history "from each market's creation date", but gives no start date and no collection method, so the claim is unverified. Under this task's rules (public sources only: no login, no account, no paid API), the best ask and depth at an arbitrary past second cannot be rebuilt for markets that closed between 2025-01-01 and about 2025-10-10. For later markets they exist only in paid archives. The one free route is PMXT for hours from 2026-02-21 onward, and its host refused or timed out from this machine. The verdict for historical execution in the window 2025-01-01 to 2026-10-31 should therefore be UNVERIFIABLE, except for markets PMXT actually covers once access is confirmed.

**Not verified:** - archive.pmxt.dev and its docs page were unreachable from here (both WebFetch and curl got connection refused or timed out). PMXT's start date, its free status and its event and snapshot schema therefore come from secondary pages (evan-kolberg.github.io and polymart.app), not from PMXT's own docs. No PMXT file was downloaded or inspected.
- All vendor coverage claims are the vendors' own marketing and were not tested. That covers PolymarketData's "from creation" claim, Telonex, Dome, PredictionData, TickFoundry, Marketlens, PolyOrderbooks and Allium. No account or paid API was used.
- No live call to /prices-history was made. What p means (midpoint or last trade) and how much 1-minute data survives for markets resolved in 2025 were not checked empirically.
- Dune was not checked for any order-book table; only the subgraph schema was read.
- No Kaggle, Hugging Face or Zenodo listing was opened directly. The Zenodo dataset is described only on the PolyOrderbooks page.
- Allium's market-orderbook start date and access terms are unknown.
- Read times are given as a date only (2026-11-17); exact UTC times were not recorded.

### Sources

- <https://docs.polymarket.com/api-spec/clob-openapi.yaml>: "/book: Retrieves the order book summary for a specific token ID. Includes bids, asks, market details, and last trade price. (only parameter: token_id)"
- <https://docs.polymarket.com/api-spec/clob-openapi.yaml>: "/prices-history: Retrieve historical price data for a market. ... fidelity: Accuracy of the data expressed in minutes. Default is 1 minute."
- <https://docs.polymarket.com/market-data/prices-order-books.md>: "Retrieve the resting bids and asks for one outcome."
- <https://docs.polymarket.com/market-data/prices-order-books.md>: "Observed price, normalized to a decimal string. ... One-minute data lasts at least 7 days, five-minute at least 60 days ... Explicit start/end ranges span at most 15 days."
- <https://docs.polymarket.com/concepts/prices-orderbook.md>: "The displayed price is the midpoint of the bid-ask spread. If the spread is wider than $0.10, the last traded price is shown instead."
- <https://docs.polymarket.com/market-data/realtime-data.md>: "a later subscribe frame always sends a book snapshot for each outcome ID it adds (events: book, price_change, last_trade_price, tick_size_change)"
- <https://github.com/Polymarket/polymarket-subgraph/blob/main/orderbook-subgraph/schema.graphql>: "# Exchange OrderFilled event stored directly / type OrderFilledEvent ... # Exchange OrdersMatched event stored directly ... type Orderbook: Number of trades of any kind against this order book"
- <https://evan-kolberg.github.io/prediction-market-backtesting/data-vendors/>: "PMXT is the hourly raw archive path for Polymarket L2 order-book data ... from 2026-02-21T16:00:00Z through the current floored UTC hour ... book_snapshot as a fresh full book snapshot ... price_change as an incremental price-level update"
- <https://polymart.app/pmxt>: "a free public archive containing historical data and hourly order book snapshots in Parquet format"
- <https://telonex.io/data/polymarket>: "Trades, quotes, order books ... From Oct 11, 2025 ... onchain_fills: From market inception (Nov 2022)"
- <https://docs.domeapi.io/api-reference/endpoint/get-orderbook-history.md>: "snapshots of the order book including bids, asks, and market metadata ... starting from October 14th, 2025"
- <https://predictiondata-dev.pages.dev/faq>: "We began capturing websocket data (trades and order books) in November 2025."
- <https://github.com/tickfoundry/polymarket-historical-data>: "Order book history: L1 top of book on every change and 25-level L2 depth, back to February 2026."
- <https://marketlens.trade/polymarket-historical-data>: "Order book capture started in March 2026 and the archive is complete from there ... Paid plans start at $39/mo."
- <https://polyorderbooks.com/polymarket-order-book-data>: "There is no historical equivalent, no date parameter, and nothing behind it storing yesterday's state."
- <https://www.polymarketdata.co/polymarket-order-book-data>: "Order book history is available from each market's creation date at 1-minute resolution. ... Full ladder. Every resting bid and ask at each snapshot is included."
- <https://docs.allium.so/historical-data/supported-blockchains/evm/polygon/predictions/market-orderbook>: "provides orderbook snapshots for Polymarket prediction markets ... Multiple rows per market and timestamp represent different price levels (status: Beta)"

## Historical fees: PARTIAL

2025-01-01 to 2026-03-29: Polymarket charged no trading fees on politics, geopolitics, culture or business markets. The only fees in early 2026 were taker fees on crypto markets (15-minute markets from 2026-01-05, then all crypto timeframes for markets created after 2026-03-06) and on NCAAB and Serie A sports markets (from 2026-02-18).

From 2026-03-30 ("Fee Structure V2"), taker-only fees apply to Politics, Finance, Tech and Mentions (taker rate 0.04), to Economics, Culture, Weather and Other/General (0.05 after the correction below), and to Crypto (0.072, later 0.07) and Sports. Geopolitics and world-events markets stayed fee-free (rate 0) for the whole period. Makers are never charged. Maker rebates are 25% of taker fees for the non-sports, non-crypto categories, 20% for Crypto, and 15% for Sports from 2026-07-10.

The formula changed once:
- 2026-03-30: `fee = C*p*feeRate*(p*(1-p))^exponent`, where C is the number of shares and p the price. Politics used exponent 1, for a 1.00% peak.
- From 2026-03-31/04-01 (by 2026-04-01 at the latest): `fee = C*feeRate*p*(1-p)`, the exponent field is effectively 1, and fees are charged in shares on buys and in USDC on sells. For politics this means $1.00 per 100 shares at 50c, which is 2% of notional.

Scope over time:
- Docs from 2026-03-30 to 2026-04-14: "Fees apply only to markets deployed on or after the activation date. Pre-existing markets are unaffected."
- By 2026-04-22 that sentence had been replaced with "Fees are determined per-market at match time." The CLOB V2 cutover was 2026-04-28.
- Today, July-2025 politics markets show feesEnabled=true. The date they became fee-bearing could not be verified.

Gas: trades are settled on-chain by Polymarket's operator, and wallet operations through the Relayer are gasless for the user.

Per-fill fee on record:
- Yes, on-chain. CTF Exchange v1 and v2 `OrderFilled` has a `uint256 fee` field, and v2 also emits `FeeCharged(receiver, amount)`.
- No, in the public Data API v2 `Trade` schema (no fee field). Positions have had `entryFeesUsdc` since 2026-08-10.
- The authenticated CLOB get-trades carries `fee_rate_bps`.
- The per-market fee parameters are the Gamma fields `feesEnabled` and `feeSchedule {rate, exponent, takerOnly, rebateRate}`. The legacy `maker_base_fee`/`taker_base_fee` (`makerBaseFee`/`takerBaseFee`) are not the charged fee: politics markets currently show makerBaseFee=1000 although makers are never charged.

**Not verified:** - The exact date (and whether it was retroactive or progressive) when markets created before 2026-03-30 became fee-bearing. The Gamma API now shows feesEnabled=true on July-2025 politics markets, but the docs only show the "pre-existing unaffected" sentence disappearing between 2026-04-14 and 2026-04-22. A link to the 2026-04-28 V2 cutover is plausible but unverified. Settling it needs on-chain `FeeCharged`/`OrderFilled.fee` checks on old markets, which I did not do.
- The exact time on 2026-03-30 when fees went live, and the exact time the formula was corrected (official changelog date 2026-03-31, docs snapshot 2026-04-01). The account of the bug comes from secondary press citing Discord, not from a page I read on Polymarket's own site.
- Whether the Gamma `feesEnabled`/`feeSchedule` fields are versioned over time. They are current snapshots, not history.
- The meaning of the legacy makerBaseFee/takerBaseFee=1000.
- Whether gas was ever charged to proxy-wallet users for trades in 2025. The docs say Relayer operations are gasless and the operator submits trades, but I found no explicit statement covering 2025.
- The start date of the taker rebate program and the exact boundaries of the "Geopolitics" category (which markets carry it).
- Wayback snapshots between 2026-04-22 and 2026-11-12 were only checked for the politics rate, the formula and the "pre-existing" sentence, not read in full.
- I did not use the 0xinsider, predictionhunt or medium pages.

### Sources

- <https://web.archive.org/web/20250615120451/https://docs.polymarket.com/polymarket-learn/trading/fees>: "Polymarket does not charge any type of fee. ... There are no fees to trade shares in any market."
- <https://web.archive.org/web/20260122070830/https://docs.polymarket.com/polymarket-learn/trading/fees>: "The vast majority of Polymarket markets have no trading fees ... 15-minute crypto markets have taker fees enabled to fund the Maker Rebates Program"
- <https://docs.polymarket.com/changelog/changelog.md>: "Jan 5, 2026 Taker Fees & Maker Rebates: Enabled on 15-minute crypto markets. Fees vary by price and peak at 1.56% at 50% probability."
- <https://docs.polymarket.com/changelog/changelog.md>: "Taker fees to be enabled on NCAAB (college basketball) and Serie A markets on February 18, 2026."
- <https://docs.polymarket.com/changelog/changelog.md>: "Starting March 6, 2026, taker fees and maker rebates extend to all crypto markets including 1H, 4H, daily, and weekly. ... Only new markets created after March 6 are affected."
- <https://docs.polymarket.com/changelog/changelog.md>: "Mar 30, 2026 Fee Structure V2: Fees now apply to Crypto, Sports, Finance, Politics, Economics, Culture, Weather, Tech, Mentions, and Other / General markets with updated rates per category. Geopolitical and world events markets remain fee-free."
- <https://docs.polymarket.com/changelog/changelog.md>: "Mar 31, 2026 REST API Fee Fields Update: Fees should now be calculated using the `feeSchedule` object within a market."
- <https://docs.polymarket.com/changelog/changelog.md>: "Fees are now set at match time — no more `feeRateBps` on orders ... As of April 28, V2 runs on `https://clob.polymarket.com`."
- <https://docs.polymarket.com/changelog/changelog.md>: "The sports taker fee rate increases from `0.03` to `0.05` at midnight UTC. ... The sports maker rebate decreases from 25% to 15% of collected taker fees."
- <https://web.archive.org/web/20260330095359/https://docs.polymarket.com/trading/fees>: "Fees apply only to markets deployed on or after the activation date. Pre-existing markets are unaffected. ... fee = C × p × feeRate × (p × (1 - p))^exponent ... Politics 0.04 1 25% 1.00% ... Geopolitics 0 — — 0%"
- <https://web.archive.org/web/20260414223031/https://docs.polymarket.com/trading/fees>: "fee = C × feeRate × p × (1 - p) ... Makers are never charged fees. Only takers pay fees. ... Politics 0.04 0 25% ... fees are collected in shares on buy orders and USDC on sell orders."
- <https://web.archive.org/web/20260422232554/https://docs.polymarket.com/trading/fees>: "Fees are determined per-market at match time. Markets with fees enabled have feesEnabled set to true on the market object. Query fee parameters for any market with getClobMarketInfo(conditionID)."
- <https://docs.polymarket.com/trading/fees>: "Geopolitical and world events markets are fee-free. ... fee = C × feeRate × p × (1 - p) ... Politics 0.04 0 25% ... Culture 0.05 0 25% ... Combos 0.05 0 0%"
- <https://docs.polymarket.com/market-data/market-details>: "feeSchedule.exponent: Exponent applied to the price component of the fee curve. ... takerOnly: When true, fees are charged to the taker side only, and makers pay no fee."
- <https://www.kucoin.com/news/flash/polymarket-addresses-high-fee-controversy-confirms-calculation-error-and-fixes>: "dollars-denominated taker volume was incorrectly used ... This has now been corrected to use "number of shares" (secondary report of a Polymarket Discord post, 2026/04/01; weather and economics markets affected)"
- <https://pineanalytics.substack.com/p/polymarket-fee-rollout>: "fee = C x p x feeRate x (p x (1 - p))^exponent (third-party; matches the 2026-03-30 docs snapshot, superseded by 2026-04-01)"
- <https://github.com/Polymarket/ctf-exchange/blob/main/src/exchange/interfaces/ITrading.sol>: "event OrderFilled(bytes32 indexed orderHash, address indexed maker, address indexed taker, uint256 makerAssetId, uint256 takerAssetId, uint256 makerAmountFilled, uint256 takerAmountFilled, uint256 fee"
- <https://github.com/Polymarket/ctf-exchange-v2/blob/main/src/exchange/interfaces/IFees.sol>: "/// @notice Emitted when a fee is charged event FeeCharged(address indexed receiver, uint256 amount);"
- <https://docs.polymarket.com/resources/onchain-position-data.md>: "The CTF exchanges emit `OrderFilled`, `OrdersMatched`, and `FeeCharged`."
- <https://data-api.polymarket.com/v2/openapi.json>: "Trade properties: bio, condition_id, event_slug, icon, name, outcome, outcome_index, price, profile_image, profile_image_optimized, proxy_wallet, pseudonym, side, size, slug, timestamp, title, token_id, transaction_hash (no fee field)"
- <https://docs.polymarket.com/changelog/changelog.md>: "Aug 10, 2026 ... `GET /positions` entries can include `grossInitialValue`, the remaining entry basis including attributed buy fees, and `entryFeesUsdc`, that fee component."
- <https://docs.polymarket.com/api-reference/trade/get-trades.md>: "fee_rate_bps: description: Fee rate in basis points (authenticated CLOB endpoint: Requires readonly or level 2 API key authentication)"
- <https://gamma-api.polymarket.com/markets?limit=3&closed=false&tag_slug=politics>: "'Xi Jinping out before 2027?', 'createdAt': '2025-07-03T20:25:56Z', 'feesEnabled': True, 'feeSchedule': {'exponent': 1, 'rate': 0.04, 'takerOnly': True, 'rebateRate': 0.25}, 'makerBaseFee': 1000, 'takerBaseFee': 1000"
- <https://docs.polymarket.com/trading/wallets-auth.md>: "Execute Gasless Transactions: Approve token spending, transfer funds, and manage positions from the account wallet without paying gas."
- <https://docs.polymarket.com/concepts/order-lifecycle.md>: "When orders match, the operator submits the trade to the blockchain."
