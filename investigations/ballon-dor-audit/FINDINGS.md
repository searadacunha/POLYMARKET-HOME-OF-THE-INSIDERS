# Findings: ballon-dor-audit

## F-001 | CONFIRMED | Accounting verified: 25 pUSD burns equal to the API, total $493,094.76; 46 mints, total $304,137.63; $129,367.79 is the exact sum of the 7 settled accounts
- Sources: sources/RAPPORT_AUDIT.md ; sources/out/a2_chain.txt
- Method: Recomputed from evidence files, chain reread without the investigation's cache
- Limits: $129,367.79 remains a partial scope
- Links: ballon-dor-wallets:F-001

## F-002 | REFUTED | "0 direct transfer, 0 discriminating link across 55 pairs" is false for one pair: the key of brace227 sent ETH to the key of kraben006
- Sources: sources/RAPPORT_AUDIT.md
- Method: Reading of native transfers and key histories
- Limits: One pair, nothing on control
- Links: ballon-dor-wallets:F-005

## F-003 | REFUTED | The base rate table is not valid as published: 20 of 50 comparator reads are invalid
- Sources: sources/RAPPORT_AUDIT.md
- Method: Reread of the comparators
- Limits: This audit's own figure of 53 of 83 was later corrected to 48 of 78
- Links: ballon-dor-wallets:F-009

## F-004 | UNRESOLVED | Several "weakened" verdicts confuse absence of proof with proof of absence: H3, H4 and H9 have no positive control
- Sources: sources/RAPPORT_AUDIT.md
- Method: Review of hypotheses
- Limits: Neither demonstrated nor excluded
- Links: none

## F-005 | UNRESOLVED | Insider trading stays not demonstrated: nothing in the data answers it
- Sources: sources/RAPPORT_AUDIT.md
- Method: Review of levels of proof
- Limits: Limit of public data
- Links: ballon-dor-wallets:F-013
