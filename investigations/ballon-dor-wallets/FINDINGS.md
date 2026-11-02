# Findings: ballon-dor-wallets

## F-001 | CONFIRMED | The 11 accounts total $304,137.63 of deposits and $493,094.76 of withdrawals: a gross flow, not a gain. The net of $129,367.79 covers only the 7 settled accounts
- Sources: sources/reports/rapport_final.md
- Method: Polymarket API checked on chain against pUSD burns and mints
- Limits: Says nothing of gas, fees outside the wallet or other accounts of one person. 4 accounts keep a residue or positions
- Links: ballon-dor-audit:F-001

## F-002 | CONFIRMED | The key of brace227 sends 0.002048944 ETH, about $5.53, to the key of kraben006
- Sources: sources/reports/liens_entre_wallets.md ; sources/reports/rapport_final.md ; tx 0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98 (Ethereum, block 26119420)
- Method: Read on 2 nodes, plain transfer without data
- Limits: Negligible amount, 0.055% of the deposits of brace227. Says nothing of who controls the keys, or why
- Links: ballon-dor-audit:F-002 ; ballon-dor-flow-trace:F-003

## F-003 | CONFIRMED | The key of brace227 sends 2,210 then 2,960 USDC to 0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d, owner of the wallet 0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5, which the press does not name
- Sources: sources/reports/liens_entre_wallets.md ; tx 0x7e3aecb9b41e6d3f92f25b8760228f15e9b55e798cd27977eb7170445cf64349 ; tx 0xb07c3c53a713d98aea1d1bd5d6facf849b6edc675c0fe2cfd3df5b791db20add
- Method: owner() read on Polygon, transfers read on chain
- Limits: Funding an account is not controlling it. Outside the 11 accounts named by the press
- Links: ballon-dor-flow-trace:F-001

## F-004 | HYPOTHESIS | brace227 and the unnamed wallet 0xa8e64a3c… may be operated together: same source of funds on October 9 and 10, first buys 13 minutes apart, Kane in common
- Sources: sources/reports/rapport_final.md
- Method: Comparison of timelines
- Limits: No positive control of common ownership. Close buys can follow one public signal
- Links: ballon-dor-flow-trace:F-002

## F-005 | REFUTED | "0 direct transfer, 0 discriminating link across 55 pairs", written in version 1, is false for one pair
- Sources: sources/reports/AMENDEMENT_AUDIT_2026-11-02.md
- Method: Audit, then reading on chain
- Limits: Holds for the other pairs on the scope read, which is not exhaustive
- Links: ballon-dor-audit:F-002

## F-006 | REFUTED | Funding less than one hour before the first buy does not set the named accounts apart: 9/11 against 32/39 fresh accounts, p = 0.69
- Sources: sources/reports/rapport_final.md
- Method: Exploratory reread by flow-trace, p values recomputed
- Limits: Traits of the controls chosen after the fact
- Links: ballon-dor-flow-trace:F-010

## F-007 | REFUTED | The simultaneous redemption of 0x86544e4dfde and walletwallet8424 is no link: a batch of 2,711 accounts in 136 transactions
- Sources: sources/reports/CONTRE_VERIFICATION.md ; sources/reports/rapport_final.md
- Method: Reading of the resolution timeline of the Kane market
- Limits: Trigger of the batch not read
- Links: none

## F-008 | REFUTED | The close withdrawals of brace227 and kraben006 are no signal: 10 of 20 comparable sellers also withdraw within 5 minutes, p = 0.29
- Sources: sources/reports/AMENDEMENT_AUDIT_2026-11-02.md ; sources/reports/CONTRE_VERIFICATION.md
- Method: Post hoc comparison with sellers of Kane at 0.99
- Limits: Exploratory
- Links: none

## F-009 | UNRESOLVED | The base rate of version 1 is invalid, 48 of 78 wallets are unusable, and the KuCoin gap is neither supported nor refuted
- Sources: sources/reports/CONTRE_VERIFICATION.md ; sources/reports/rapport_final.md
- Method: Recount, cross-check with flow-trace
- Limits: The real rate stays unknown
- Links: ballon-dor-audit:F-003

## F-010 | UNRESOLVED | Common control of wallets is neither demonstrated nor excluded, including for pairs linked by funds
- Sources: sources/reports/rapport_final.md
- Method: Review of direct links and shared services
- Limits: The method has no positive control of common ownership
- Links: ballon-dor-flow-trace:F-004

## F-011 | UNRESOLVED | Coordination of bets is not demonstrated: 0 discriminating shared address across 55 pairs, but 19 of 55 pairs never tested by E4
- Sources: sources/reports/rapport_final.md
- Method: Synchrony tests, shared addresses, frozen plan
- Limits: Scope not exhaustive, exchange accounts invisible
- Links: none

## F-012 | SUPPORTED | Frozen verdict of part A: VISIBLE_NON_SPECIFIQUE on October 13 at 18:51 UTC and on October 23 at 15:17:49 UTC
- Sources: sources/collective/results.md ; sources/collective/PROTOCOL.lock
- Method: Frozen plan, positive controls, register of 140,114 real comparisons
- Limits: Effective n is 1, the author knew the affair. No independent review of phases 5 and 8
- Links: polysentinel:F-002

## F-013 | UNRESOLVED | Insider trading is not demonstrated: no evidence of access to information
- Sources: sources/reports/rapport_final.md
- Method: Review of what the data can establish
- Limits: Winning a bet, even early, does not prove its source. Public timelines of October 8 to 13 are incomplete
- Links: ballon-dor-flow-trace:F-015

## Contradictions

- `sources/collective/results.md` and the freeze were not changed: they still carry the earlier readings, flagged in the amendment.
- The audit and version 2 wrote 53 unusable comparators of 83: the recount gives 48 of 78 distinct wallets.

## Missing to conclude

- Open decisions listed in the amendment: XMR status, a file on `0xa8e64a3c…`, protocol amendments, closing `collective/`, publication.
- BSC and Base histories, exchange accounts: private registers.
