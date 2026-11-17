# Findings, followup-20261113 investigation

Data read on 12 November 2026 from public, keyless sources. An address is not a person. Detail and every transaction:
`sources/reports/FOLLOWUP_REPORT.md`.

## F-001 | CONFIRMED | The owner key of the 6741 Safe sent 372,521.54 USDC to eight Polymarket accounts between 2025-10-09 22:40:19 and 2025-10-10 03:30:43 UTC
- Sources: sources/reports/FOLLOWUP_REPORT.md ; sources/data/nobel_funding_transfers.csv ; sources/data/nobel_accounts.csv ; sources/data/funder_polygon_flows.csv ; first transfer tx 0xe4dd2102d6dd649611557415aa28457e792c5abaac963e5a6fbb7a3b6f3e2516 (Polygon, 2025-10-09 22:40:19 UTC) ; last transfer tx 0x837bb79029d2749c2d3085da352c668ab6fca5f9a454a0d6a6dd0e5ad8c6d9fb (Polygon, 2025-10-10 03:30:43 UTC)
- Method: sources/tools/pm_nobel_c7.py and sources/tools/pm_nobel_financeur.py (Blockscout Polygon, official native USDC only) ; all 14 receipts replayed by public JSON-RPC ; Safe getOwners() of 0xa430506774f9efaf39903ee7e0db1351f66891ca read at the current block and at block 77,472,527
- Limits: shows a common funder and the ownership of one Safe (6741). The seven other Safes have distinct owner keys; a group with a common treasurer gives the same picture
- Links: none

## F-002 | CONFIRMED | All 16 Relay withdrawals of the eight accounts went to that key (15 requests, 523,060.18 USDC) or to the 6741 proxy (1 request)
- Sources: sources/reports/FOLLOWUP_REPORT.md ; sources/data/nobel_relay_withdrawals.csv ; sources/data/funder_polygon_flows.csv
- Method: Relay requests API v2 for each account ; each delivery replayed by JSON-RPC receipt ; the funder's Polygon USDC inflows equal its outflows, its remaining balance being the 0.00001 USDC difference
- Limits: the recipient field comes from the Relay order record and matches the on-chain delivery; that the recipient is set by the owner signature was checked on one request only
- Links: none

## F-003 | SUPPORTED | The public Polymarket profile named aenews0 is the proxy 0x4bac00c61a02275d681f3857cdc5ae315f1f7075
- Sources: sources/reports/FOLLOWUP_REPORT.md ; sources/data/nobel_accounts.csv
- Method: Polymarket gamma public-profile lookup of every proxy funded by the key of F-001
- Limits: a profile name is chosen by its user; no second source
- Links: none

## F-004 | SUPPORTED | Each of the eight profiles was created between 45 seconds and 6 minutes before its first funding, except 6741 (74 minutes)
- Sources: sources/reports/FOLLOWUP_REPORT.md ; sources/data/nobel_accounts.csv ; sources/data/nobel_funding_transfers.csv
- Method: profile creation time from the gamma public profile against the time of the first transfer of F-001
- Limits: the creation time is a platform database timestamp, not the on-chain deployment of the Safe
- Links: none

## F-005 | CONFIRMED | The capital is 57.333146 ETH sent at 2025-10-09 22:18:23 UTC by 0x3e2c6d068fc6958684e836998285e3a836dbd96f, swapped to 249,677.38 USDC and bridged to Polygon through Across deposit 3253263
- Sources: sources/reports/FOLLOWUP_REPORT.md ; sources/data/funder_and_source_ethereum_flows.csv ; sources/data/funder_upstream_downstream.json ; tx 0x2b2dc98b5322e96a486a325c7c14c2623287709f2b711008b146ca9a67d8c27a (Ethereum, 2025-10-09 22:18:23 UTC) ; Across fill tx 0x609bb6181c0f916bd27e934b24c72bedddbc3e1c5f7c3013028b827a4b139ba7 (Polygon, 2025-10-09 22:39:09 UTC)
- Method: Ethereum transactions and token transfers of the funder and of its source (Blockscout), replayed by JSON-RPC ; Across deposit status API
- Limits: the source sold 6.2178 stETH itself and handed 1.8368 WBTC to a UniswapX solver; the WBTC sale is inferred from its ETH balance. The first POL of the funder comes from an address tagged FixedFloat by Blockscout alone
- Links: none

## F-006 | CONFIRMED | Seven of the eight accounts made their first Machado purchase after the public repricing from 0.037 at 22:30 to 0.390 at 23:00 UTC; 6741 first bought at 22:42:57 at 0.048
- Sources: sources/reports/FOLLOWUP_REPORT.md ; sources/data/machado_yes_price_history.json ; sources/data/nobel_accounts.csv
- Method: Polymarket CLOB price history of the Machado Yes token (5-minute points) against the first purchase of each account (data-api v2 trades)
- Limits: no calibrated base rate; the other large buyers of the same window are not enumerated completely. Inside information is not shown for any account, and the purchases of 6741 may be part of the cause of the move
- Links: none

## F-007 | UNRESOLVED | One person controls the eight accounts
- Sources: sources/reports/FOLLOWUP_REPORT.md ; sources/data/owner_keys_activity.csv ; sources/data/nobel_accounts.csv
- Method: Safe owners of the eight proxies and on-chain activity of the seven owner keys other than the funder
- Limits: the seven owner keys never transacted on Polygon or Ethereum. Against independence: creation seconds or minutes before each funding, handles on the same theme, every withdrawal back to the funder. For: distinct signing keys
- Links: none

## F-008 | REFUTED | A direct transfer or a shared counterparty links two of the eleven Ballon d'Or case files on Base, Arbitrum or Optimism
- Sources: sources/reports/FOLLOWUP_REPORT.md ; sources/data/ballon_l2_summary.json ; sources/data/ballon_l2_coverage.csv ; sources/data/ballon_l2_edges.csv
- Method: sources/tools/pm_ballon_l2.py on the 40 EVM addresses of the case files, complete pagination of transactions, token transfers and internal transactions, official tokens only
- Limits: BSC is still unread (no free history); Blockscout indexing only
- Links: ballon-dor-flow-trace:F-003 ; ballon-dor-flow-trace:F-004

## F-009 | SUPPORTED | The 0.0076965 ETH ChangeNOW payout to 0x3eaef6d5e91ecf7b7623eb19978e145ebd417013 on 2024-12-17 is the output of an order paid by that address on Base
- Sources: sources/reports/FOLLOWUP_REPORT.md ; sources/data/ballon_changenow_roundtrip.csv ; tx 0x92d8fce2c7835a2eb13f936419520874a1b2bfed6ddd93360ba9e7ca01bed9af (Base, 2024-12-17 02:10:49 UTC) ; tx 0xee338bdbba66bad7c6e36b75a5841e1294b418396c400b11bb4395bfda95b28b (Base, 2024-12-17 02:14:11 UTC)
- Method: Base history of the address and of the single-use deposit address (Blockscout), against row 49 of investigations/ballon-dor-flow-trace/sources/data/walk_edges.csv
- Limits: the ChangeNOW order is not public; the hot-wallet tag of 0x1b1d2149d656f8ca33fb633e6f642b5a2426b53d has a single source. Nothing changes for the brace227 key, whose link with the service stays indirect
- Links: changenow-proof:F-013

## F-010 | UNRESOLVED | The 1% service 0x3ab2206b98b01ba256dbdd4c50208bf17ab27d50 manages the WenZhuanBuPei receiving key 0xe820ecb3c6f48a420a5538046cab73d2f40987cd
- Sources: sources/reports/FOLLOWUP_REPORT.md ; sources/data/ballon_l2_edges.csv
- Method: Arbitrum transactions around the 27,724.00 USDC transfer of 2026-10-27
- Limits: the service advances 0.00001 ETH of gas two seconds before the transfer and receives 0.000008 ETH back in the same second, which fits a managed deposit address; the round amount, leaving 0.79 USDC, fits a user choice
- Links: ballon-dor-flow-trace:F-012

## Contradictions

- `research_notes/c5-c7-recovery-overlaps-2026-11-07/REPORT.md` and `research_notes/c1-c7-primary-anchors-2026-11-07/REPORT.md` say that the alleged distributor of about $250k has no address and that aenews0 has no proxy. The public branch `research/global-insider-forensics-20261102` (commit `34ff284`) already holds the funder of F-001 as the owner key of 6741 in machine-generated tables. See F-001 to F-003.
- Row 49 of `investigations/ballon-dor-flow-trace/sources/data/walk_edges.csv` records a self round-trip through ChangeNOW as funding. See F-009.
- `investigations/ballon-dor-flow-trace/STATUS.md` says Base has no free history; the Base API of Blockscout answered on 12 November 2026. See F-008.

## Missing to conclude

- BSC histories of the Ballon d'Or keys.
- The cause of the 22:30-23:00 UTC repricing of the Machado Yes token on 2025-10-09, and a complete list of the other large buyers of that window.
- Where the treasury of the Nobel funder sent the 330,020.96 USDC moved to the Relay depository on 2026-04-15.
