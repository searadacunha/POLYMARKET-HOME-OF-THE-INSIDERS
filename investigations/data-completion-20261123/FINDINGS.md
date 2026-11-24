## F-001 | CONFIRMED | An independent log-based replay reproduces every per-market result of PR 111 except two markets resolved after its cut-off
- Sources: results/regression_pr111.json ; scripts/regression_pr111.py ; scripts/ledger_build.py
- Method: Collect the four PR 111 wallets' logs by account filters (not PR 111's receipts), rebuild their ledgers with this folder's engine and compare every row of PR 111's positions_after_funding.csv on (wallet, condition) within one native unit.
- Limits: The four wallets are PR 111's selection, not a random sample. The two differences are markets PR 111 listed as OPEN that resolved and were redeemed after its cut-off.
- Links: none

## F-002 | CONFIRMED | Every input that PR 110 records by hash is present in Git and hash-identical; its empty data manifest is a documentation gap, not missing data
- Sources: results/data_gap_matrix.csv ; scripts/data_gap_matrix.py
- Method: Read inputs_sha256 of PR 110's results/weekly_funding.json at 8b633048 and hash each Git blob it names.
- Limits: This checks recorded inputs, not the completeness of the sources PR 110 chose.
- Links: none

## F-003 | CONFIRMED | The archived f2020 total of -$21,722 counts five shared trading addresses twice; over distinct addresses it is -$21,321
- Sources: results/REPORT.md ; scripts/report.py
- Method: Group the archived pm_pnl2.csv rows by lowercased account; five accounts appear in two bettor records whose trading fields (buy, sell, PnL, events) are identical, while the records differ in account type and ChangeNOW amount.
- Limits: Both figures come from the archived Data API file (rounded to the dollar, 16 records capped at 5,500 events). The on-chain replay of this folder is a separate measurement over a longer window.
- Links: none

## F-004 | CONFIRMED | PR 110's Ethereum log streams are recoverable for the 23 missing weeks; its native Ethereum stream was not recovered keyless in this session
- Sources: results/eth_weeks_coverage.csv ; results/REPORT.md ; results/eth_downstream_linking.json
- Method: Run PR 110's own collect_week (pinned 8b633048, unchanged) on a public Ethereum archive RPC for 2026-W16 to W38; control the native stream with each address's transaction count per week.
- Limits: The native stream stays PARTIAL for 17 of the 23 weeks because the keyless explorer answered HTTP 429 and Etherscan needs a key; it may be recoverable later or with a key. These packs are not inputs of PR 110's frozen study; adding them needs a dated amendment by the owner. Downstream linking was tried on a deterministic sample of 20 recipients only: Across deposits match their Polygon fills exactly, no bettor attribution was established, and that is a sampled zero, not a platform-wide one.
- Links: none

## F-005 | SUPPORTED | Within PR 110's sources and weeks, no wallet reaches a verified service-funding level; distinct possible wallets must be counted as a set union
- Sources: results/weekly_service_funding.csv ; results/weekly_service_funding_union.json ; results/REPORT.md
- Method: Reshape PR 110's frozen weekly address sets per evidence level and take unions across weeks.
- Limits: Scoped to PR 110's source registry, covered weeks and sampled frame; a platform-wide rate remains unknown. PR 110's Ethereum ChangeNOW source is UNKNOWN in 23 of its 31 weeks (W16 to W38); the streams recovered here are not inputs of PR 110, so the zero verified count in those weeks is not a measured zero. POSSIBLE means a commingled route, not service-to-bettor attribution.
- Links: none

## F-006 | CONFIRMED | The three Arbitrum passages of PR 109 hold on independent providers as pass-throughs at a shared intermediary, without establishing a common owner
- Sources: results/cross_chain_routes.csv ; results/cross_chain_provider_comparison.json ; results/cross_chain_passages.json
- Method: Re-collect the six receipts, headers and intermediary transfer windows on three or four public providers; rebuild the intermediaries' full USDC history; read the Relay request identifiers of each leg.
- Limits: Within each order the legs share a request identifier; between the two orders the link rests on the same address, identical amount, zero balance before and after and no other USDC movement. Ownership is unresolved.
- Links: none

## F-007 | CONFIRMED | Several public historical sources are gone or keyed, and of the four keyless Polygon RPC providers probed only one served historical log ranges at a practical span
- Sources: results/source_probes.json ; results/recovery_attempts.jsonl
- Method: Probe each endpoint with a generic client and record status, limits and response hashes: Polymarket subgraphs (paused), Data API v1 (retired), Goldsky Edge (paid), HyperSync and Relay v3 (keyed); for Polygon logs, publicnode refused archive ranges, dRPC answered spans of at most 100 blocks and 1rpc of at most 50 blocks with rate limits.
- Limits: Measured on 2026-11-23 on the probed set only; endpoints change. dRPC served archive receipts and was used as the second provider for a sample.
- Links: none

## F-008 | SUPPORTED | Order-book depth at alert time cannot be recovered afterwards, and the PR 109 evaluator keeps residual leakage paths; the verdict stays NO_EDGE_VALIDATED
- Sources: results/prospective_data_quality.csv ; results/leakage_and_comparison.json
- Method: Measure the availability of each prospective input; read the evaluator code of main and PR 109; run the PR 109 evaluator in memory on the live alerts.
- Limits: No holdout evidence was added. Residual paths are listed with their status, not quantified.
- Links: none

## F-009 | CONFIRMED | Every accepted range of the cohort's seven log filters is complete on the primary provider over the whole exchange history, and every cohort address's collateral reconciles exactly with its on-chain balances
- Sources: results/ledger_results.json ; results/wallet_summary.csv ; results/provider_sample.json ; results/REPORT.md
- Method: Seven log filters per account chunk over contiguous accepted ranges from the first V1 exchange block to a recorded finalized block; collateral transfers summed per token and compared with balanceOf at both ends for every account; a deterministic sample of ERC-1155 balances; every redemption against the official payout value; every trade against the verified fee rules; a second provider on a deterministic sample of collected receipts; the Data API as an independent count of trade transactions.
- Limits: Historical logs come from one keyless provider. The second-provider sample re-reads collected transactions, so it detects altered logs, not omitted ones; the collateral reconciliation detects net omissions of collateral transfers, not offsetting ones, and position transfers are checked on a sample only. Ten logs matched a filter without a known event (ERC-721 and other token transfers). Ten cohort addresses never owned a filled order. Seven ExchangeV3 positions and the tokens Gamma does not know stay unmapped.
- Links: changenow-polymarket:F-001

## F-010 | CONFIRMED | On chain, the cohort's trading loss is about twice the archived figure; the archive's capped records saw only a minority of their purchases
- Sources: results/archived_vs_chain.json ; results/REPORT.md ; results/wallet_summary.csv ; results/wallet_position_summary.csv.gz
- Method: Sum trading PnL (realized plus unrealized at average cost, shares sent away at cost) per account; compare with the archived pm_pnl2.csv by account over the archived window, separately for the records the archive marks incomplete, and compare purchase volumes.
- Limits: For uncapped records, 104 of 137 accounts agree within one dollar over the archived window. That the cap explains the gap is supported by the purchase volumes, not measured directly. Profit and loss say nothing about information: no finding here concerns insider trading, and deposits, withdrawals and funding are excluded.
- Links: changenow-polymarket:F-001

## F-011 | UNRESOLVED | PR 110's Ethereum-to-Polygon Relay screen cannot be completed before the announced v2 Sunset, and the histories read to the end contain no order created in the screened weeks
- Sources: results/relay_v2_screen.json ; results/relay_v2_screen.csv ; results/relay_v2_orders.csv
- Method: Re-read each recipient's GET /requests/v2 history (user, chain 1 to 137), one call at a time, every exchange recorded; a page counts only with a requests list; the Ethereum-origin query returned orders for some accounts, and a known Arbitrum-to-Polygon order of PR 109 was returned by the same endpoint and user parameter.
- Limits: The collector was stopped after its exchange of 2026-11-23T22:39:48Z, before the Sunset announced by the endpoint (2026-11-24T00:00:00Z), and was not restarted; the screen classifies all 117 exchanges of its append-only page log: 107 histories read to the end, 19 already complete in PR 110, 115 not reached. v3 needs a key. Histories not reached are unknown, not empty. Orders found outside the screened weeks are listed but are not funding paths of those weeks.
- Links: none

## Contradictions
- changenow-polymarket:F-001 sums 158 bettor records; five trading addresses appear in two records each, so the total counts them twice (see F-003).

## Missing to conclude
- A Relay requests v3 key, or another keyless index, to finish the Ethereum-to-Polygon histories after the v2 Sunset.
- A keyless explorer transaction list for the native ChangeNOW Ethereum stream of 2026-W16 to W32.
- Timestamped executable prices for open positions, and order-book depth captured at alert time.
- Platform-wide denominators for weekly funding.
