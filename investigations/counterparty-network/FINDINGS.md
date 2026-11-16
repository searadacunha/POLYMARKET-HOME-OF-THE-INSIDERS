# Findings: counterparty-network

## F-001 | CONFIRMED | Four archived C7 transactions reconcile to 53355.91 shares and 30514.17 USDC among one seller and two buyers
- Sources: results/c7_reconciled.json ; scripts/reconcile_c7.py
- Method: Read the previously published C7 CSV, validate unique transaction identifiers and share-price approximations, sum atomic decimal amounts by buyer, then compare with the committed JSON
- Limits: Confirmation applies to archival arithmetic only. The source CSV was curated by an earlier investigation and the four original Polygon receipts were not independently reread during this addition
- Links: none

## F-002 | SUPPORTED | Executed V2 maker-taker logs can establish transaction-level counterparty edges, but not control or share ownership
- Sources: results/source_review.md ; scripts/counterparty_graph.py
- Method: Compare the first-party V2 event semantics to the local chain decoder, omit exchange-address taker events and distinguish raw execution edges from buyer-seller position transfers
- Limits: No claim that the prototype has reconstructed the full exchange history, handled all matching regimes, or separated professional liquidity provision from coordinated accounts
- Links: none

## F-003 | UNRESOLVED | No predictive advantage from recurring counterparties has been measured
- Sources: results/analysis_plan.md ; results/source_review.md
- Method: Set out a prospective design comparing point-in-time network signals with observable prices, matched controls and executable post-alert returns
- Limits: No frozen thresholds, unbiased event-wide backtest, live execution simulation or outside-sample replication was completed
- Links: none

## Prospective monitoring

- Obtain complete V2 transaction receipts and link maker/taker rows to individual matching calls where needed
- Check counterparties and market-making background rates in markets selected without reference to eventual winners
- Test incremental prediction versus the quoted price after fees, spreads, latency and real liquidity
