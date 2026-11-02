# Findings: changenow-proof

## F-001 | CONFIRMED | The key of kraben006 receives 834.848793 USDC in two payments on February 23, 2026 from 0xdd3d72c53ff982ff59853da71158bf1538b3ceee
- Sources: sources/reports/CHANGENOW_PROOF_FINAL.md ; sources/data/verified_transfers.csv ; tx 0x5e8b57210b722dbf0f7395cbe20c57a3e578d2897bb4ff8d4c5e853387789219 ; tx 0x472c85a3cd9df3bbdf9b5fac9ee812326646b1b40c832278fb42107554c0cd80
- Method: Transactions, receipts and blocks reread on a public node
- Limits: Shows the transfer. Attribution of the sender is F-002
- Links: ballon-dor-flow-trace:F-014

## F-002 | SUPPORTED | 0xdd3d72c53ff982ff59853da71158bf1538b3ceee and 0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b are service wallets attributed to ChangeNOW by labels and behaviour
- Sources: sources/reports/CHANGENOW_PROOF_FINAL.md ; sources/reports/ATTRIBUTION_EVIDENCE.md
- Method: Labels from several lineages, on-chain links, sweep fingerprint
- Limits: No confirmation from ChangeNOW, a white label stays possible. A label identifies no customer
- Links: none

## F-003 | UNRESOLVED | No documented path links these 834.85 USDC to the bets: they leave to a platform deposit address 220 days before the account's first Polymarket deposit
- Sources: sources/reports/CHANGENOW_PROOF_FINAL.md
- Method: Following the outputs of the key
- Limits: A return through this account, a service or an unread chain is neither observed nor excluded
- Links: none

## F-004 | HYPOTHESIS | The 0.00247406 ETH sent on October 4 to a single-use address may be a deposit at ChangeNOW
- Sources: sources/reports/CHANGENOW_PROOF_FINAL.md ; tx 0x1a39308b89cc7d9de6e38fbf0c62aa5d0bdd777863079cd151fe12a6b135dd71
- Method: Sweep fingerprint compared with labeled addresses
- Limits: Fingerprint defined after reading, without a freeze, and a weak test. The documentation also describes a private-transfer route
- Links: ballon-dor-flow-trace:F-014

## F-005 | UNRESOLVED | No individual ChangeNOW order can be found with public data, nor its payout destination
- Sources: sources/reports/CHANGENOW_PROOF_FINAL.md
- Method: Reading of the official documentation and collection, 49 transactions reread
- Limits: The API needs a partner key and only gives that partner's orders. No route was called
- Links: none

## F-006 | UNRESOLVED | Monero: 0 confirmed case, 3 paths remain possible in the strict sense, with nothing specific to XMR
- Sources: sources/reports/CHANGENOW_PROOF_FINAL.md ; sources/reports/XMR_VISIBILITY.md
- Method: Classification into confirmed, possible, not established
- Limits: An XMR origin is invisible by construction
- Links: ballon-dor-flow-trace:F-007

## F-007 | REFUTED | ouldlm3alem and wen are not linked to ChangeNOW: Binance Hot Wallet 34 sends 10,000 USDC to ChangeNOW 22, a flow between two services
- Sources: sources/reports/CHANGENOW_PROOF_FINAL.md ; sources/reports/FALSE_POSITIVES.md
- Method: Reading of the transfer and the labels
- Limits: A naive rule would have linked them
- Links: none

## F-008 | REFUTED | Touching the same ChangeNOW wallet is no link: 0xdd3d72c5… has 1,656,021 transactions, and no private intermediary is shared on this path
- Sources: sources/reports/CHANGENOW_PROOF_FINAL.md
- Method: Comparison of counterparties
- Limits: Partial windows
- Links: none

## Contradictions

- `ballon-dor-flow-trace` gives `0x3f3ee0a9…` the profile of a deposit address: here `0x7e67df45…` has that profile, and `0x3f3ee0a9…` is a service wallet.
- Amendment A5 of `ballon-dor-wallets` speaks of a single uncorroborated source: the service is corroborated here, the order stays unknown.

## Missing to conclude

- The orders behind the cited hashes, through a legal request or from the customer. Nothing was sent.
- The holder of deposit address `0x66d582e5…`: a matter for an authority.
