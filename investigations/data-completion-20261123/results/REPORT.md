# Data completion and forensic reconstruction: results

Generated from the files of `results/` only. Window: blocks 33605403 to 97836049 (finalized, 2026-11-23T18:45:43+00:00), provider https://gateway.tenderly.co/public/polygon.

## 1. Units of the f2020 cohort

| Unit | Count | Source |
|---|---|---|
| Archived f2020 payees | 3408 | PR 110 results/weekly_funding.json |
| Bettor records (pm_traders.csv rows) | 158 | same |
| Distinct lowercased trading addresses | 153 | same |
| Addresses in this ledger's cohort | 153 | results/ledger_results.json |
| Addresses with at least one log | 153 | same |
| Addresses with at least one OrderFilled as order owner | 143 | same |

These are different units. Payees are not traders, and five trading addresses are shared by two bettor records each.

## 2. Collection coverage

Every accepted range of every stream is complete on the primary provider; the second-provider sample below re-reads collected transactions, so it can detect altered or wrong logs but not omitted ones. Omissions of collateral transfers would break the balance reconciliation of section 3; omissions of position transfers are checked only on the sampled balances.

| Stream | Logs | Ranges | Complete |
|---|---|---|---|
| adapter_events/c0 | 18182 | 16 | True |
| adapter_events/c1 | 7574 | 11 | True |
| ctf_events/c0 | 23105 | 18 | True |
| ctf_events/c1 | 72365 | 28 | True |
| erc1155_from/c0 | 62994 | 29 | True |
| erc1155_from/c1 | 76238 | 27 | True |
| erc1155_to/c0 | 101079 | 33 | True |
| erc1155_to/c1 | 143255 | 47 | True |
| erc20_from/c0 | 97830 | 31 | True |
| erc20_from/c1 | 113725 | 36 | True |
| erc20_to/c0 | 61085 | 29 | True |
| erc20_to/c1 | 70674 | 25 | True |
| fills/c0 | 96630 | 32 | True |
| fills/c1 | 116183 | 36 | True |

Unique logs after de-duplication: 1060865. Load problems (hash mismatch, duplicate that differs, block-hash conflict, removed log): 0. Account-transactions: 344630. Fills owned by cohort accounts: 212813 (v1 79087, v2 133714, v3 12).

Second-provider control (https://polygon.drpc.org): 200 transactions sampled by rule (200 smallest sha256(tx hash) among all collected cohort transactions); collected logs that agree field by field: 575, that differ: 0, receipts missing: 0.

Transaction kinds (one transaction can carry several):

| Kind | Account-transactions |
|---|---|
| TRADE | 209011 |
| REDEEM | 86229 |
| CASH_ONLY | 18458 |
| BURN_FOR_COLLATERAL | 11433 |
| SPLIT | 8673 |
| NO_NET_CHANGE | 4953 |
| MINT_FOR_COLLATERAL | 3299 |
| MERGE | 2525 |
| SHARE_TRANSFER | 47 |
| CONVERT | 1 |
| SHARE_AND_CASH_UNEXPLAINED | 1 |

## 3. Positions and profit

| Measure | Value |
|---|---|
| Account-market positions | 103342 |
| Distinct markets | 77835 |
| Markets resolved on chain (official payout vector) | 77668 |
| Positions RESOLVED / OPEN_OR_UNRESOLVED / UNKNOWN_MARKET | 103149 / 127 / 66 |
| Positions with an unknown inventory value | 15 |
| Arithmetic identity (self-check, not an independent control) PASS / FAIL / NOT_EVALUATED | 103327 / 0 / 15 |
| Accounts whose collateral reconciles with balanceOf (all tokens) | 153 of 153 (failed 0) |
| Position-token balance sample PASS / FAIL | 600 / 0 |
| Gamma outcome prices that disagree with the chain payout | 0 |
| Redeem or burn account-transactions whose collateral equals the official payout value of the burned shares (PASS / FAIL / some payout unknown) | 61734 / 0 / 23 |
| Trades whose collateral matches the fill fee rules (zero / above / below, by version) | v1:above 11227; v1:zero 67051; v2:above 16; v2:zero 130705; v3:zero 12 |
| Positions with no remaining inventory, of all positions | 92873 of 103342 |
| Positions with inventory valued by official payout / by a CLOB mark / unknown | 10368 / 86 / 15 (of 10469) |
| Collateral paid for buys (fees included) | 1,356,784.32 |
| Fees paid on 2026 and V3 exchanges (pUSD) | 9,512.27 |
| Trading PnL, positions with a known value (shares sent to other wallets leave at cost) | -43650.447579 |
| Net position PnL, same positions (cash plus inventory; shares sent away count as outflows) | -43961.575072 |

Of the 143 accounts with at least one fill, 141 have a complete trading PnL (winners 28, losers 113, flat 0; median -9.911603) and 2 hold at least one position of unknown value. 10 accounts of the cohort never owned a filled order. Sum of the known parts over all 153 accounts: -43650.447579.

Flags on positions (count of positions carrying each):

| Flag | Positions |
|---|---|
| BURN_WITHOUT_USER_EVENT | 11433 |
| TRADE_CASH_RESIDUAL | 8493 |
| MINT_WITHOUT_USER_EVENT | 3295 |
| MULTI_CONDITION_PRO_RATA | 108 |
| CONVERSION | 60 |
| BURN_PARTLY_UNKNOWN_PAYOUT | 46 |
| BURN_CASH_NOT_PAYOUT | 1 |

### Independent count from the Data API

| Measure | Value |
|---|---|
| Accounts whose /v2/activity history was read to the end | 153 |
| API TRADE transactions / on-chain fill transactions | 209007 / 209011 |
| API TRADE transactions missing on chain | 0 |
| On-chain fill transactions missing in the API | 4 |

### Archived figure

The archived file `pm_pnl2.csv` (Data API, rounded to the dollar, 16 records capped at 5,500 events) sums to -21722 over 158 records. Five trading addresses appear in two records, so that sum counts them twice; over the 153 distinct addresses it is -21321. This ledger replaces neither: it is an independent on-chain replay over a longer window.

| Archived records | Accounts | Archived PnL | Chain PnL, archived window | Chain PnL, lifetime | Archived buys | Chain buys | Within 1 USD |
|---|---|---|---|---|---|---|---|
| capped | 16 | -7225 | -29271.893251 | -29685.548124 | 316689 | 1173001.818144 | 0 |
| uncapped | 137 | -14096 | -14589.201914 | -13964.899455 | 178534 | 183782.506332 | 104 |

Capped records are those the archive marks incomplete (5,500 events). archived values are whole dollars from the Data API; the chain values are exact. The window match uses each account's archived last_trade, an approximation of the archive's observation time.

## 4. Regression against PR 111

| Comparison | Count |
|---|---|
| EXACT | 2546 |
| EXPLAINED_LATER_RESOLUTION | 2 |
| MISSING | 0 |
| UNEXPLAINED | 0 |

| Wallet | PR 111 focus net | Ledger | Exact |
|---|---|---|---|
| W1 | 2.824012 | 2.824012 | True |
| W2 | 0.560130 | 0.560130 | True |
| W3 | -2.407870 | -2.407870 | True |
| W4 | -0.149839 | -0.149839 | True |

Focus-market sum in this ledger: 0.826433. PR 111 cut-off: 2026-11-22T10:14:28Z. Each difference is listed in `regression_pr111.json`.

## 5. Weekly funding (PR 110 sets, unchanged)

| Service | Evidence | Sum of weekly verified | Sum of weekly possible | All-period distinct (union) | Transactions | USD |
|---|---|---|---|---|---|---|
| ChangeNOW | CONFIRMED_DIRECT | 0 | 0 | 0 | 0 | 0.00 |
| ChangeNOW | POSSIBLE | 0 | 331 | 162 | 533 | 58,975.45 |
| ChangeNOW | SUPPORTED_INDIRECT | 0 | 0 | 0 | 0 | 0.00 |
| Tornado Cash | CONFIRMED_DIRECT | 0 | 0 | 0 | 0 | 0.00 |
| Tornado Cash | POSSIBLE | 0 | 0 | 0 | 0 | 0.00 |
| Tornado Cash | SUPPORTED_INDIRECT | 0 | 0 | 0 | 0 | 0.00 |

Weekly distinct counts are not additive: the all-period column is a set union of the weekly address sets.

## 6. Ethereum weeks W16 to W38 (recovered source streams)

| Stream | Weeks | Events | Status |
|---|---|---|---|
| 1/changenow | 23 | 347025 | {'COMPLETE': 23} |
| 1/changenow_native | 23 | 121116 | {'PARTIAL': 17, 'COMPLETE': 6} |
| 1/tornado | 23 | 36819 | {'COMPLETE': 23} |

## 7. Relay v2 history screen (Ethereum to Polygon)

| Measure | Value |
|---|---|
| Accounts | 241 |
| PR 110 status | {"EXHAUSTED": 19, "PARTIAL": 222} |
| Status now | {"EXHAUSTED": 52, "EXHAUSTED_IN_PR110_NOT_REREAD": 19, "NOT_REACHED": 170} |
| Transitions from PR 110's status | {"EXHAUSTED->EXHAUSTED_IN_PR110_NOT_REREAD": 19, "PARTIAL->EXHAUSTED": 52, "PARTIAL->NOT_REACHED": 170} |
| Relay requests found / accounts with any / histories read to the end | 48 / 2 / 52 |
| Requests created in PR 110's screened weeks (W39 to W46) | 0 |
| Positive control: known Arbitrum-to-Polygon order of PR 109 returned by the same endpoint and user parameter (originChainId=42161) | True |
| HTTP calls / HTTP 429 | 62 / 10 |
| Calls between | 2026-11-23T18:16:49.230641+00:00 and 2026-11-23T20:22:04.055760+00:00 |

EXHAUSTED histories are complete for originChainId=1 to destinationChainId=137; histories PR 110 had exhausted and that were not re-read keep that status; every other status is an unknown, not a zero. The collector keeps reading until one minute before the announced Sunset; this file is the classification of the first http_calls exchanges of the append-only page log. The Ethereum-origin filter itself returned orders for the accounts listed in relay_v2_orders.csv.

## 8. Cross-chain passages of PR 109

| Route | Leg | Origin tx | Destination tx | Verdict | Proof level |
|---|---|---|---|---|---|
| R0 | 1_upstream | 0x4b8a2ff24929… | 0xbc5c7257ce78… | CONFIRMED | CONFIRMED_DIRECT |
| R0 | 2_downstream | 0xb4f4235592ce… | 0xbf91190db32f… | CONFIRMED | CONFIRMED_DIRECT |
| R1 | 1_upstream | 0x05bef803a506… | 0x6d242e5c9dbc… | CONFIRMED | CONFIRMED_DIRECT |
| R1 | 2_downstream | 0x01f08bf49673… | 0xe648501d1ac0… | CONFIRMED | CONFIRMED_DIRECT |
| R2 | 1_upstream | 0x4cb3933e1dc5… | 0xb8cbf4f99bf0… | CONFIRMED | CONFIRMED_DIRECT |
| R2 | 2_downstream | 0x9adac51c60e0… | 0x2f08bf6101a0… | CONFIRMED | CONFIRMED_DIRECT |

A passage is a transaction-level fact at one shared intermediary. It does not establish a common owner.

## 9. Prospective data and leakage

| Item | Availability | Priority |
|---|---|---|
| bid/ask history (historical, any market) | PARTIAL | P0 |
| bid/ask history (local live capture) | PARTIAL | P0 |
| order-book depth at alert time | UNAVAILABLE | P0 |
| fee schedule at alert time | PARTIAL | P1 |
| realized fees per fill | AVAILABLE | P2 |
| order-book sequence gaps | PARTIAL | P1 |
| collector latency (websocket) | PARTIAL | P1 |
| collector latency (engine fills -> alert) | AVAILABLE | P1 |
| trade-tape poll latency | PARTIAL | P2 |
| public news first-observed timestamps | PARTIAL | P0 |
| independently verifiable event chronology | PARTIAL | P1 |
| historical account state at alert time (on chain) | AVAILABLE | P1 |
| historical account state at alert time (platform) | PARTIAL | P1 |
| midpoint / spread at alert time | UNAVAILABLE | P0 |

Scientific verdict: NO_EDGE_VALIDATED (unchanged). Prospective evidence measured here: 26 radar-live alerts = 17 distinct wallet/market/outcome entries; PR #109 evaluator run in memory gives 2 FINAL (one entry, two classes) and 24 PARTIAL. No holdout result.

## 10. Data gap matrix

| Status | Datasets |
|---|---|
| COMPLETE | 25 |
| CORRUPT | 1 |
| LOCAL_ONLY | 4 |
| PARTIAL | 23 |
| UNAVAILABLE | 8 |

File-level inventory: 167580 evidence rows; COMPLETE 3287, CORRUPT 5, LOCAL_ONLY 75491, PARTIAL 0, UNAVAILABLE 88786, UNKNOWN 0, UNVERIFIED 11.

## 11. Tests run

| Suite | Result |
|---|---|
| investigation unit tests (python3 -m unittest discover -s tests) | 24 tests, OK (synthetic fixtures, no network) |
| verify.py with the local raw data | 14 passed, 0 failed, 0 skipped |
| verify.py without raw data (CI mode) | 2 passed, 0 failed, 7 SKIPPED_MISSING_INPUT (raw logs are local_only) |
| PR 110 verify.py at 8b633048 (read-only wrapper, no bytecode written) | OK: Verified 129 inputs, weekly tables, wallet receipts, report and chart offline |
| PR 110 unit tests at 8b633048 | 21 tests, OK |
| PR 111 verify.py at 58c964b5 | 0 failure(s) |
| PR 111 unit tests at 58c964b5 | 12 tests, OK |
| scripts/run_all_checks.py --keep-going (working tree, before this folder was complete) | 33 of 34 steps OK; the failing step was this folder's then-missing FINDINGS.md and data_manifest.json |
| independent code review (2 agents, read-only) | 2 MAJOR and 8 MINOR silent-failure findings, 2 MAJOR and 6 MINOR accounting findings; all fixed or documented in this folder |
| recorded_utc | 2026-11-23T20:24:51Z |
| independent claims audit (1 agent, read-only) | FAIL on wording and denominators (all recomputed numbers matched exactly); every listed problem fixed in this commit |

