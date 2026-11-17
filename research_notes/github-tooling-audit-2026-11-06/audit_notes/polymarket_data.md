# Polymarket data tooling audit (code-level, read-only), 2026-11-06

Method: shallow clones under `../clones/` (all < 50 MB), docs fetched with curl (saved beside this file: `llms.txt`, `v2openapi.json` extracted from `v2docs.out`, `contracts.md`, `blockchain-data.md`, `mig.md`). No third-party code executed. I computed event topic0 hashes with my own 40-line Keccak (self-checked against keccak("")), not with repo code. Test files are counted, not run.
"Not verified" = not observed in a source I read.

## 0. Documentation facts (docs.polymarket.com, data-api.polymarket.com/v2/docs, fetched 2026-11-06)

Data API v2 OpenAPI info block (`v2openapi.json`, info.description):
- Pagination is cursor-only: follow `pagination.next_cursor` until null; `has_more` exact; **no `offset` parameter, sending one is HTTP 400**. v1 offset capped at 10,000 and **Data API v1 retired 2026-11-02** (`mig.md` lines 17-28, 40-43).
- `/v2/activity` and `/v2/trades` are keyset walks `(block_timestamp, sequence_id)`, stable under concurrent writes. Cursor carries only seek anchor + page size (+ sort direction on activity). **Re-send identical filters on every page; changing one mid-walk re-anchors silently.**
- `limit`: default 100, max 1000, past-cap rejected (activity). Trades: limit is first-page size only, cursor's size wins.
- Window on `/v2/trades?user=` and `/v2/activity`: omitted or `0` `start` floors to **three years back**; `start=1` = full history; omitted/`0` `end` = now + 1 day. `/v2/trades` by `condition`/`event_id`: fixed 3-year window, start/end ignored; bare feed: rolling current + previous month.
- `/v2/activity` params: `user` (required), `limit`, `cursor`, `type` (CSV), `condition` (<=20), `event_id` (<=20, exclusive with condition), `side`, `start`, `end`, `sort_by`(TIMESTAMP only), `sort_direction` ASC|DESC (value sorts CASH/TOKENS rejected 400), `exclude_deposits_withdrawals`.
- **`exclude_deposits_withdrawals` defaults to true: DEPOSIT and WITHDRAWAL rows are dropped even when named in `type`.** Pass `false`. (openapi param description.)
- `type` accepted: TRADE, SPLIT, MERGE, REDEEM (auto-redemptions included), CONVERSION, MIGRATION, REWARD, YIELD, MAKER_REBATE, TAKER_REBATE, REFERRAL_REWARD, DEPOSIT, WITHDRAWAL, DIRECTIONAL_SPLIT, DIRECTIONAL_MERGE, THRESHOLD_COMPOSE, THRESHOLD_DECOMPOSE, TIP. **TIP (user-to-user pUSD transfer that is not a trade-settlement leg) is opt-in, never in the default set**; omitted `type` returns everything except TIP. Direct candidate for "pUSD movements the default activity omits".
- Activity row fields (schema `Activity`): proxy_wallet, condition_id, token_id, side, size, usdc_size, price, timestamp, type, transaction_hash, title, slug, outcome, outcome_index, plus profile fields. No log index / sequence_id in the row schema (the cursor holds it, opaque).
- `/v2/trades`: `taker_only` defaults true (each fill once on taker side); false adds maker rows; `filter_amount` default 0.01 (**small fills below 0.01 are filtered by default**; 0 means the same, so cannot be lowered to see them; TOKENS shares unless filter_type=CASH).
- `/v2/positions`: cursor binds status/sort/direction; bare `cursor` without `user` anchor = 400; re-send `title`, `condition`, start/end each page; old residual-sort cursors 400 "restart pagination without cursor".
- Other wallet endpoints: `/v2/value`, `/v2/user-pnl` (cumulative native-PnL atoms), `/v2/user-stats`, `/v2/user-volume`, `/v2/holders` (offset walk behind the opaque token; can skip/repeat across a refresh), `/v2/approvals?user=` (Polygon token/operator approvals of the proxy wallet), `/v2/activity/combos`, `/v2/positions/combos`.
- Errors: 429 + Retry-After; 503 request_timeout (not a 429). Every response has `x-trace-id`.
- **Proxy/deposit wallet to owner/signer: no documented endpoint.** The words owner/signer/deposit wallet appear 0 times in the OpenAPI. Only the opposite direction exists (signer to wallet, via CREATE2 derivation, see py-sdk below). Contracts page lists Deposit Wallet Factory `0x00000000000Fb5C9ADea0298D729A0CB3823Cc07`, Deposit Wallet Beacon `0x7A18...fc3a`, Polymarket Proxy Factory `0xaB45c5A4...4052`, Gnosis Safe Factory `0xaacfeea0...541b` (contracts.md). Reverse resolution would need factory/wallet events or `owner()` reads: not verified.

Contracts page (contracts.md), current as of today, Polygon 137:
- "CTF Exchange" `0xE111180000d2663C0091e4f400237545B87B996B`, "Neg Risk CTF Exchange" `0xe2222d279d744050d28e00520010520000310F59` (these are the CTF Exchange **V2** contracts; docs link `Polymarket/ctf-exchange-v2`); Conditional Tokens `0x4D97DCd97eC945f40cF65F87097ACe5EA0476045`; Neg Risk Adapter `0xd91E80cF2E7be2e162c6513ceD06f1dD0dA35296`.
- New "Polymarket Protocol V2" stack (separate from CTF Exchange V2): PositionManager `0x006F54F7f9A22e0000CC2AB60031000000ae9fEF` (owns ERC-1155 balances), ExchangeV3 `0xe3333700cA9d93003F00f0F71f8515005F6c00Aa` (EIP-712 domain version "3"), Router, Binary/NegRisk/Combinatorial modules, AutoRedeemer `0xa1200000d0002264C9a1698e001292D00E1b00af`.
- pUSD `0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB`, CollateralOnramp `0x93070a84...B8ee`, Offramp `0x2957922E...5854`, CtfCollateralAdapter `0xAdA100Db00Ca00073811820692005400218FcE1f`, NegRiskCtfCollateralAdapter `0xadA2005600Dec949baf300f4C6120000bDB6eAab`.
- `onchain-position-data.md`: two position systems selected by Gamma `version` ("v1" = CTF, tokenId, exchange domain "2"; "v2" = PositionManager, positionId, domain "3"). **Token-id spaces differ** (V2 position id packs module/baseHash/arity/condition/outcome). Migration CTF to PositionManager emits `PositionMigrated`, `MigrationConditionRegistered`. Docs warn: "Third-party schemas can lag contract upgrades. Check the indexed contract addresses against the current Contracts page."
- blockchain-data.md names Goldsky, Dune, Allium, CryptoHouse as official on-chain data routes.

## 1. Polymarket/py-sdk

- Pin now: `ddee30cebb6322d41119e10b20ea6a875a7f1c9c`, 2026-11-05, release 0.17.0 (pyproject.toml:7). Earlier pin `aa94ec43...` (2026-11-02).
- License: `LICENSE` = MIT, "Copyright (c) 2026 Polymarket"; pyproject.toml:11 `license = { text = "MIT" }`. No disagreement.
- Changes since aa94ec4 (7 commits, `git log aa94ec4..HEAD`, 19 files, +246/-13): feat(data) range-event activity types DIRECTIONAL_SPLIT/MERGE, THRESHOLD_COMPOSE/DECOMPOSE (f517647; models in `src/polymarket/models/data/activity.py`); fix threshold rows report `shares` not USDC (d5b2d88); UnknownActivity reduced to shared account fields (150822f); Binance price provider in streams (f4bce02); docs; release 0.17.0. **No change to pagination, windows, or wallet code.**
- Data API v2 endpoints wrapped (`src/polymarket/_internal/actions/data.py`): /v2/trades :92, /v2/activity :139, /v2/activity/combos :169, /v2/positions :226, /v2/positions/combos :279, /v2/value :308, /v2/user-stats :323, /v2/user-pnl :342, /v2/user-volume :361, /v2/holders :382, /v2/tokens :426, /v2/oi :461, /v2/live-volume :478, /v2/prices-history :517, /v2/resolutions :552, /v2/leaderboard :572/:597, /v2/biggest-winners :615, builders :631/:651; /v2/approvals in `actions/relayer/approvals.py:40`.
- Pagination: `KeysetPaginatedSpec` with `cursor_param="cursor"`, `max_page_size=1000` (data.py ~:150, ~:118). Envelope validator `_internal/data_envelope.py:26-38` raises `UnexpectedResponseError` on missing/invalid pagination, and when `has_more != (next_cursor is not None)`. That is a genuine truncation check on the envelope, not a completeness proof.
- Windows: `build_time_window` (data.py:704-711): `full_history=True` sends `start=1, end=None`; cannot be combined with start/end. Default (no start) lets the server floor to 3 years: **the SDK does not warn about the 3-year floor.** Offset caps: the `PaginationLimitError`/`limit_reached` machinery (`request.py:36`, `dispatch.py:87`, docstrings in clients/public.py:1135-1200) is for Gamma comments (offset 200), not Data API.
- Activity includes DEPOSIT/WITHDRAWAL: `list_activity_spec` hard-codes `"exclude_deposits_withdrawals": False` (data.py ~:150). Good. TIP is only returned if named in `activity_types`.
- Raw responses: models subclass a base with `extra="ignore"` (`models/base.py:15`), so unknown fields are dropped; only `UnknownActivity` keeps `raw` (activity.py:558, `{**data, "type": raw_type, "raw": dict(data)}`). Row-level `sequence_id`/log index not exposed. Raw cursor strings are exposed via the paginator.
- Proxy to owner: none. Wallet code `_internal/wallet.py`: owner to wallet only, `derive_proxy_wallet_address(signer, config)` :72, `derive_safe_wallet_address` :84, `derive_uups_deposit_wallet_address` :90, `derive_beacon_deposit_wallet_address` :97, `derive_current_deposit_wallet_address` :119 (RPC read of factory beacon). CREATE2 forward derivation lets us **test a candidate signer against a known proxy** (hash match) but cannot enumerate owners from a proxy.
- Tests: 183 test files, ~2,490 `def test_` (not run). Integration tests exist (`tests/integration/test_data*.py`; they hit the live API).
- Deps: eth-abi, eth-account, eth-utils, pydantic etc. (pyproject.toml:30+). No paid service.
- Risks: dropping fields (`extra=ignore`), silent 3-year floor, Decimal/validation errors on schema drift (reject rather than pass-through).
- Advantage over ours: reference for correct v2 param grammar and envelope validation; CREATE2 derivation. No new data.
- **Decision: REFERENCE** (use its param grammar; do not depend on it for evidence because it discards raw rows).

## 2. enviodev/polymarket-v2-indexer

- Pin: `0da9e5c3b2af40a192204461fafb463acf123c6a`, 2026-08-11 ("bump HyperIndex to envio@3.6.1"); clone is depth 1 so history count unknown.
- License: **no LICENSE file**; package.json has no license field; README silent. Unlicensed = all rights reserved; no reuse right. (GitHub metadata not checked, no API call needed for this.)
- Events indexed (config.yaml:12-48), start block `84902320` "PolyUSD deployment" (config.yaml chains block). Calendar date not stated in repo; test data block 85050371 has timestamp 1775220779 = 2026-04-03 (test/CTFExchangeV2.test.ts:75,88), so the start block is about end of March 2026 (inference). Kowalskk README says V2 contracts "deployed 2026-03-31" and "migration from v1 occurred on 2026-04-28" (update_chain.py:39-40; not independently verified).
  - CTFExchangeV2 at 3 addresses: `0xe111180000d2663c0091e4f400237545b87b996b`, `0xe2222d279d744050d28e00520010520000310f59`, `0xe2222d002000ba0053cef3375333610f64600036`. Events: OrderFilled(bytes32 indexed orderHash, address indexed maker, address indexed taker, uint8 side, uint256 tokenId, uint256 makerAmountFilled, uint256 takerAmountFilled, uint256 fee, bytes32 builder, bytes32 metadata), OrdersMatched, FeeCharged, pause/admin events.
  - PolyUSD `0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb`: Transfer, Wrapped, Unwrapped.
  - CtfCollateralAdapter `0xada100874d00e3331d00f2007a9c336a65009718`: PositionSplit, PositionsMerge, PayoutRedemption. NegRiskCtfCollateralAdapter `0xada200001000ef00d07553cee7006808f895c6f1`: Wrapped/Unwrapped only. Rewards `0xdd8db71c...` (DistributedRewards etc.).
- **Address drift:** both adapter addresses differ from today's contracts page (docs: `0xAdA100Db00Ca00073811820692005400218FcE1f`, `0xadA2005600Dec949baf300f4C6120000bDB6eAab`), and the third exchange `0xe2222d0020...0036` is not on the docs page. **The indexer predates (or misses) the current adapters, ExchangeV3, PositionManager, AutoRedeemer, Router and modules entirely.** Whether the old adapters still receive flows: not verified.
- V1 coverage: **none.** Only V2 exchange contracts, from the pUSD era. No CTF Exchange V1 / NegRisk V1 (pre-2026-04-28), no USDC.e Transfer, no ConditionalTokens TransferSingle/Batch. It cannot cover the V1 to V2 migration.
- Keying: id = `${chainId}_${blockNumber}_${logIndex}` (CTFExchangeV2.ts:6-7, PolyUSD.ts:3-4, CtfCollateralAdapter.ts:5-8); tx hash stored as a field (`event.transaction.hash`, field_selection hash+from). Block+logIndex is unique per chain; fine for dedupe, though no reorg note.
- V1/V2 token-id: handlers key `Market` by decimal `tokenId` and resolve via Gamma `markets/keyset?clob_token_ids=` (marketMetadata.ts); it assumes the exchange `tokenId` is a CLOB token id. It does not decode PositionManager position ids; fills on ExchangeV3 are not indexed at all. Metadata fetch failures leave `market_id` attributed by tokenId only (CTFExchangeV2.ts:51-57 comment).
- PolyUSD Transfer handler (PolyUSD.ts:17-60) stores every pUSD Transfer (from, to, amount, block, tx hash) and per-account balances. **This is the usable idea:** per-wallet pUSD in/out from chain, independent of the Data API.
- Needs HyperSync token: yes (`.env.example`: ENVIO_API_TOKEN; README:42). Free tier exists per Kowalskk README (rate-limited), paid faster; indexer also needs Docker, Postgres, Node 22, pnpm; ClickHouse optional; calls Gamma (140 calls/10 s). Cost: free tier plausible, not quantified.
- Tests: 15 `it(`/`test(` cases in 4 files (test/*.ts), simulated + HyperSync-sourced data (README). Not run.
- Risks: unlicensed; stale addresses; no V1; Gamma-dependent; whole tool is heavy for our need.
- **Decision: REFERENCE** (config.yaml topic/ABI list is a clean spec; do not adopt the tool).

## 3. Kowalskk/polyMARKET_data

- Pin: `cab11bd5a2fc41a67c4c643835a4766907208b55`, 2026-06-29 ("Update readme"). It is a **fork/copy of warproxxx/poly_data v2** (README badges point to warproxxx).
- License disagreement: `LICENSE` = GNU GPL v3 (README says GPL-3.0); `pyproject.toml:7` says `license = { text = "MIT" }`. The LICENSE file wins; GPL-3 is copyleft. Also vendors `backtrader_plotting/` (unrelated plotting package).
- Data: `OrderFilled` logs from **only one contract**, CTF Exchange V2 `0xe111180000d2663c0091e4f400237545b87b996b` (update_chain.py:41), from block `V2_GENESIS_BLOCK = 84_902_353` (:42), via Envio HyperSync (token `HYPERSYNC_API`, update_chain.py error text; free tier slow, "several hours to a few days"), topic0 computed at :45-50 from the 10-arg signature. CLOB `/markets` for metadata (update_markets.py).
- Schema (README, `data/orderFilled.csv`): timestamp, maker, makerAssetId, makerAmountFilled, taker, takerAssetId, takerAmountFilled, transactionHash (update_chain.py:~123-160). **Drops logIndex, orderHash, fee, builder, metadata and the exchange address** (decoded at :131 as `_fee, _builder, _metadata`, discarded). Without logIndex rows in one tx cannot be uniquely keyed.
- Completeness: only a resume cursor and 20-block reorg buffer (`CONFIRMATIONS = 20`, :54-ish); no reconciliation, no count checks. **Misses the Neg Risk exchange `0xe2222d...0f59`** (no address in query :161-178), so all neg-risk markets are absent. Maker-centric mapping: README itself says filter on `maker`, the contract can appear as taker.
- V1 coverage: none (README: v1 preserved only at warproxxx tag `v1-final`).
- Tests: 50 `def test_` in 4 files (not run), offline pure-function.
- **Decision: REJECT** for forensics (single exchange, lossy schema, GPL/MIT conflict). Idea already covered by the indexer config.

## 4. Polymarket/real-time-data-client

- Pin: `418cce9a05bdd7b74b1cef7af18727cfff5b4b8b`, 2026-10-09. License MIT (LICENSE and package.json:23 agree). **README header: package deprecated**, migrate to unified SDK; RTDS price topics move to PolyBolt `wss://ws-live-v2.polymarket.com/ws` (docs migrate/rtds-to-polybolt.md).
- Protocol: WebSocket `wss://ws-live-data.polymarket.com` (src/client.ts:4), text PING every 5 s (:5), subscribe `{subscriptions:[{topic,type,filters,clob_auth?,gamma_auth?}]}` (src/model.ts), message `{topic,type,timestamp,payload}` with `payload: object` (**no schema validation in code**; types are README-only).
- Topics (README table): `activity` types `trades`, `orders_matched` (filters event_slug or market_slug); `comments`; `crypto_prices`, `crypto_prices_chainlink`, `equity_prices`; `clob_user` (CLOB API creds).
- conditionId/transactionHash: README "Trade" schema lists `conditionId` ("also the CTF condition ID"), `transactionHash`, `proxyWallet`, `asset`, `side`, `size`, `price`. That is documentation only; the client passes the raw payload through and enforces nothing, so **our 890 messages without conditionId are neither explained nor contradicted by this repo**; plausible causes (not verified): different type (`orders_matched` shares the same documented schema), non-trade topics, or server-side change. Since the package is deprecated, do not build on it.
- Tests: none in repo (no test files; Makefile/eslint only).
- Advantage: none. **Decision: REJECT** (deprecated, no tests, no completeness semantics).

## 5. sfrbuilds/polymarket-wallet-analyzer

- Pin: `5c249247e22608592a8f801fba84b9af45a8a829`, 2026-06-04. Single file `wallet_analyzer.py` (README + script only).
- License: **no LICENSE file**; README line 235 says "MIT. No API key, no rate limits". Unlicensed in practice.
- Pagination: `_paginate` (wallet_analyzer.py:127-190) uses **v1 offset** `limit=500, offset` and stops on a short page or `data is None` (:148 `break` on failure = silent truncation). `since_ts` early stop assumes descending order. Endpoints: `/trades`, `/activity`, `/positions`, `/closed-positions`, `/value` (:487-525) with `DATA = https://data-api.polymarket.com` (:79) and `/v1/leaderboard` (:82). **All of these are retired (v1 off since 2026-11-02) and v2 returns 400 on `offset`**: the tool no longer works.
- Trade reconstruction: none; it normalises Data API rows (`_norm_trade` :227, `_norm_activity` :255).
- PnL definition (`_summarise`, :300-340): `total_pnl = sum(p["pnl"] for closed positions)` where pnl = `cashPnl or pnl or realizedPnl` from the API's `/closed-positions` rows (`_norm_position` :250). So it is the server's per-position realized PnL, summed, labelled "Total realised P&L"; win rate = share of positive rows. No handling of redemptions, merges, rewards, fees, or open positions in the total; it is not a cash flow. Ours (redemptions + sells - buys per market from activity) is strictly more transparent and testable.
- Tests: none. **Decision: REJECT.**

## 6. Answer to the key question: can any of this find proxy USDC.e/pUSD movements the Data API activity omits, or reconstruct fills/redemptions across V1 to V2?

Honest result: **no repo delivers it as a tool.** What exists:

A. Omissions inside the Data API itself (cheap, check first, per docs above):
 1. `exclude_deposits_withdrawals` default true drops DEPOSIT/WITHDRAWAL; we already use them, confirm the parameter is explicitly false.
 2. `type=TIP` pUSD user-to-user transfers are never returned unless requested.
 3. 3-year floor unless `start=1`; `/v2/trades` `filter_amount` default 0.01 and `taker_only` default true.
 4. Filters are not in the cursor: a changed filter mid-walk silently re-anchors.
 5. Rows with REWARD, YIELD, MAKER_REBATE, TAKER_REBATE, REFERRAL_REWARD are pUSD credits that a "redemptions+sells-buys" cash PnL ignores.

B. On-chain completeness check, the concrete method (from the indexer config; independent of the Data API; needs a HyperSync or RPC log source, I did not call any):
 - pUSD movements of a proxy wallet W: logs of `0xC011a7E12a19f7B1f670d46F03B03f3342E82DFB` with topic0 `0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef` (Transfer(address,address,uint256)), topic1 = W (outflows) OR topic2 = W (inflows), from block **84902320** (indexer start; about 2026-03-30/31). Wraps: `Wrapped(address,address,address,uint256)` `0xc00a5c84859ae82a7f5e6a2773283fb525335d5b3195f61174aa1ecc7e15dd84`, `Unwrapped` `0x18b42b684d0b621cc609f4d888916e5ed9e934a476259ec1c11ec116f2b9aa7f` (wallet in indexed `to`/`caller`).
 - Pre-pUSD: ERC-20 Transfer on USDC.e (address NOT in the audited sources; from memory `0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174`, verify before use) with the same topic0, topic1/2 = W. Same method; this is what our receipt decoding already does, now keyed by address instead of by known tx.
 - V2 exchange fills: OrderFilled (10-arg) topic0 `0xd543adfd945773f1a62f74f0ee55a5e3b9b1a28262980ba90b1a89f2ea84d8ee`, topic2 = maker, topic3 = taker, on `0xe111180000d2663c0091e4f400237545b87b996b` and `0xe2222d279d744050d28e00520010520000310f59` (docs addresses), from block 84902320 (or 84902353, Kowalskk genesis). Also index ExchangeV3 `0xe3333700cA9d93003F00f0F71f8515005F6c00Aa` (docs; not in any audited repo).
 - V1 exchange fills (pre-migration): old OrderFilled 8-arg topic0 `0xd0a08e8c493f9c94f29311604c9de1b4e8c8d4c06bd0c789af57f2d65bfec0f6` (computed by me; this signature matches the well-known v1 event). V1 exchange addresses are **not on the current docs page and not in these repos**; from memory CTF Exchange `0x4bFb41d5B3570DeFd03C39a9A4D8dE6Bd8B8982E` and NegRisk `0xC5d563A36AE78145C45a50134d48A1215220f80a`: unverified, check against the older audit's receipts.
 - Redemptions: CTF `PayoutRedemption(address,address,bytes32,bytes32,uint256[],uint256)` topic0 `0x2682012a4a4f1973119f1c9b90745d1bd91fa2bab387344f044cb3586864d18d` on Conditional Tokens `0x4D97DCd97eC945f40cF65F87097ACe5EA0476045` (redeemer = topic1); split `0x2e6bb91f8cbcda0c93623c54d0403a43514fabc40084ec96b6d5379a74786298`, merge `0x6f13ca62553fcc2bcd2372180a43949c1e4cebba603901ede2f4e14f36b282ca`. Adapter-wrapped variants on today's adapters (docs addresses) emit the same ABI per the indexer config, but the indexer watches old adapter addresses.
 - Balances/migration: ERC-1155 TransferSingle `0xc3d58168c5ae7397731d063d5bbf3d657854427343f4c083240f7aacaa2d0f62` / TransferBatch `0x4a39dc06d4c0dbc64b70af90fd698a233a518aa5d07e595d983b8c0526c8f7fb` on CTF and on PositionManager `0x006F54F7...9fEF`; docs say these are canonical, lifecycle events are context only (do not double count).
 - Redemption by AutoRedeemer / PositionManager events (PositionRedeemed, PositionMigrated): event names from docs only; ABI signatures not verified.
 - Rule from the docs, important for completeness: redemptions and merges may be auto/relayed, so the proxy appears in ERC-1155 Transfer and pUSD Transfer logs even when it is not the tx sender; always key on the wallet in topics, never on tx.from.

C. Proxy to owner: nothing in Data API, py-sdk, or indexers. The `txFrom` captured by the indexer is the relayer/sender, not the owner. Candidate methods (not verified, none tested): forward CREATE2 check from a candidate signer (py-sdk wallet.py), factory creation events, `owner()`/signer read on the EIP-7702 delegate.

## 7. Offline tests we could run (no network, on archived data)

1. Activity-vs-receipt reconciliation: for every archived tx hash in activity, decode the receipt (already done) and assert the sum of pUSD/USDC.e Transfer logs touching W equals signed sums of DEPOSIT/WITHDRAWAL/TRADE/REDEEM usdc_size within fee tolerance; residuals list transfers to/from W with no matching activity row. Needs only archived receipts.
2. Topic0 dictionary test: scan archived receipts for topic0 values above, count events by contract, flag logs from contracts not on today's contracts list (finds ExchangeV3/adapter drift).
3. Archive audit of our own fetch parameters: check whether archived pulls used `exclude_deposits_withdrawals=false`, `start=1`, and constant filters across cursor pages (cursor chain consistency).

## 8. Summary table

| Repo | SHA | Date | License | Decision |
|---|---|---|---|---|
| Polymarket/py-sdk | ddee30c | 2026-11-05 | MIT (file = manifest) | REFERENCE |
| enviodev/polymarket-v2-indexer | 0da9e5c | 2026-08-11 | none | REFERENCE |
| Kowalskk/polyMARKET_data | cab11bd | 2026-06-29 | GPL-3 file vs MIT manifest | REJECT |
| Polymarket/real-time-data-client | 418cce9 | 2026-10-09 | MIT | REJECT (deprecated) |
| sfrbuilds/polymarket-wallet-analyzer | 5c24924 | 2026-06-04 | none (README says MIT) | REJECT |

No ADOPT-CANDIDATE: the only workable method is our own log queries (section 6B) using the contract/topic list.

Limits: no log source was queried; block 84902320 date inferred from a test fixture; V1 addresses and USDC.e address are from memory; docs pages fetched once today and may change.
