# Findings: changenow-proof

## F-001 | CONFIRMED | The key of kraben006 receives 834.848793 USDC in two payments on February 23, 2026 from 0xdd3d72c53ff982ff59853da71158bf1538b3ceee
- Sources: sources/reports/CHANGENOW_PROOF_FINAL.md ; sources/data/verified_transfers.csv ; tx 0x5e8b57210b722dbf0f7395cbe20c57a3e578d2897bb4ff8d4c5e853387789219 ; tx 0x472c85a3cd9df3bbdf9b5fac9ee812326646b1b40c832278fb42107554c0cd80
- Method: Transactions, receipts and blocks reread on a public node
- Limits: Shows the transfer. Attribution of the sender is F-002
- Links: ballon-dor-flow-trace:F-014

## F-002 | SUPPORTED | 0xdd3d72c53ff982ff59853da71158bf1538b3ceee and 0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b are service wallets attributed to ChangeNOW by labels and behaviour
- Sources: sources/reports/CHANGENOW_PROOF_FINAL.md ; sources/reports/ATTRIBUTION_EVIDENCE.md
- Method: Labels from several lineages, on-chain links, sweep fingerprint
- Limits: No confirmation from ChangeNOW, a white label stays possible. A label identifies no customer. For the second address, the level assumes the hildobby compilation does not derive from Etherscan, which is unchecked. The Arkham and AMLBot readings are second-hand copies
- Links: none

## F-003 | UNRESOLVED | No documented path links these 834.85 USDC to the bets: they leave to a platform deposit address 220 days before the account's first Polymarket deposit
- Sources: sources/reports/CHANGENOW_PROOF_FINAL.md
- Method: Following the outputs of the key
- Limits: A return through this account, a service or an unread chain is neither observed nor excluded
- Links: none

## F-004 | HYPOTHESIS | The 0.00247406 ETH sent on October 4 to a single-use address may be a deposit at ChangeNOW
- Sources: sources/reports/CHANGENOW_PROOF_FINAL.md ; tx 0x1a39308b89cc7d9de6e38fbf0c62aa5d0bdd777863079cd151fe12a6b135dd71
- Method: Sweep fingerprint compared with labeled addresses
- Limits: Fingerprint defined after reading, without a freeze. 12 of 13 addresses with the tag show it and 0 of 12 comparable addresses elsewhere do, upper bound 22 % at 95 %: a weak test, and circular on the attribution because the 13 share the tag family of the wallet tested. The documentation also describes a private-transfer route
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

## F-009 | CONFIRMED | 0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b is not the deposit address of one order: its first 1000 rows hold 599 inflows and 379 outflows
- Sources: sources/reports/ATTRIBUTION_EVIDENCE.md ; sources/state/p9.json
- Method: Three transaction windows read on Etherscan: August 10, October 4 and November 2
- Limits: Windows only, never the full history. Its generic DEPOSIT ADDRESS tag is misleading
- Links: ballon-dor-flow-trace:F-014

## F-010 | CONFIRMED | The Etherscan page read on November 2 shows no public name tag on 0xdd3d72c53ff982ff59853da71158bf1538b3ceee, unlike 0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b and 0xeba88149813bec1cccccfdb0dacefaaa5de94cb1
- Sources: sources/reports/ATTRIBUTION_EVIDENCE.md
- Method: Address pages archived with their SHA-256, not redistributed: see data_manifest.json
- Limits: One reading. The reason is unknown: tag removed, a source of Blockscout's own, or how the page renders
- Links: none

## F-011 | SUPPORTED | Movements tie 0xdd3d72c53ff982ff59853da71158bf1538b3ceee to other addresses labeled ChangeNOW: 432 rows over 426 tokens from ChangeNOW 17 and 343,181.853425 USDT from Hot Wallet 4
- Sources: sources/reports/ATTRIBUTION_EVIDENCE.md ; sources/data/attribution_links.csv
- Method: Last 1000 rows of each labeled address, read from its side, then one transaction per link reread on a node
- Limits: Independent of the tag tested, not of every label: several references carry the note "tagged based on hildobby compilation", whose origin is unchecked
- Links: none

## F-012 | SUPPORTED | After the two payments, 955 USDC then 40 USDC leave the key of kraben006 for 0x66d582e5e0670bd99153199f179733c6ee5d19be, a platform deposit address by behaviour, HTX by where it sweeps
- Sources: sources/reports/PAYOUT_MATCHES.md ; sources/data/verified_transfers.csv ; sources/state/figures.json
- Method: Transfers reread on a node. All 44 stablecoin outflows of this address go to 0xa03400e098f4421b34a3a44a1b4e571419517687, tagged HTX: Hot Wallet
- Limits: No label on the address itself. It has 26 stablecoin senders: anyone can pay a deposit address, and its holder is unknown
- Links: none

## F-013 | UNRESOLVED | The key of brace227 receives 291.317423 USDT from 0x3eaef6d5e91ecf7b7623eb19978e145ebd417013, which 0xdd3d72c53ff982ff59853da71158bf1538b3ceee paid 510.494311 USDT in all: the link between that key and the service stays indirect
- Sources: sources/reports/PAYOUT_MATCHES.md ; sources/data/verified_transfers.csv
- Method: Transfers reread on a node, USDT balance of the key recomputed, which reaches 0 on April 28, 2025
- Limits: The intermediary pays 9 different recipients and its owner is unknown. The 285 USDT are followed for one hop, and BSC is unread
- Links: none

## F-014 | REFUTED | Fast forwarding and twin payouts do not set kraben006 apart: 18 of 57 recipients in the same window forward within 5 minutes, and 9 of 57 receive two payments within 10 minutes
- Sources: sources/reports/FALSE_POSITIVES.md ; sources/state/p10.json
- Method: Same reading on every USDC recipient of the hot wallet in the window of the two payments
- Limits: One window of 2.13 hours, exploratory. The 57 include kraben006. Refutes the trait as distinctive, says nothing about intent
- Links: none

## F-015 | REFUTED | A match on amount and date proves nothing here: 10 of 530 outflows of 0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b fall within 10 % of the swept amount in 10 hours
- Sources: sources/reports/FALSE_POSITIVES.md ; sources/state/p10.json
- Method: Count of native outflows around the sweep, on one wallet and one asset
- Limits: One window. With other wallets and assets, chance matches only grow
- Links: none

## F-016 | UNRESOLVED | A ChangeNOW contact is not shown to be a trait of the named accounts: 1 of 11 keys against 0 of 54 comparators, p = 0.17
- Sources: sources/reports/FALSE_POSITIVES.md ; sources/state/p16.json
- Method: Same raw first-hop reading on both groups, tags read in batches, two-sided Fisher test
- Limits: Exploratory, uncorrected, very low power. Only 14 comparators and 6 named keys have any history. Comparators were chosen after the dossiers were read
- Links: none

## Contradictions

- `ballon-dor-flow-trace` gives `0x3f3ee0a9…` the profile of a deposit address: here `0x7e67df45…` has that profile, and `0x3f3ee0a9…` is a service wallet.
- Amendment A5 of `ballon-dor-wallets` speaks of a single uncorroborated source: the service is corroborated here, the order stays unknown.
- `ballon-dor-flow-trace:F-014` reads the October 4 send as gas resold: between 19.8 % and 82.8 % of it can come from brace227 depending on the convention, and the payout is unknown. Stays a hypothesis.

## Missing to conclude

- The orders behind the cited hashes, through a legal request or from the customer. Nothing was sent.
- The holder of deposit address `0x66d582e5…`: a matter for an authority.
- The origin of the hildobby compilation, and whether it derives from Etherscan.
- A direct reading of Arkham and AMLBot, which were only read through copies in third-party repositories.
- A history for BSC and Base, and label sources for Solana and Tron.
- A base rate for how often the recipients of a key also receive from this service: 4 of 8 here, not compared with anything.
