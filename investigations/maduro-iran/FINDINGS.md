# Findings: maduro-iran

## F-001 | CONFIRMED | Eight Polymarket accounts are linked by transfers of funds through 0x44b6f8de91e20953eb2c632062860338154ebe4e, 0xe9a7230f874930827b87970a4fbb33a262f02442 and TRON addresses
- Sources: sources/RAPPORT_2026-09-29.md ; sources/phase3/RAPPORT_PHASE3_2026-09-29.md
- Method: Each edge carries a hash, section 3 of the report; expansion to depth 2 finds no new account
- Limits: Found from large winners: the network is unusual only in size. A link of funds does not say who controls
- Links: none

## F-002 | CONFIRMED | Balance of the network: external capital of $151,084.40, external outflows of $660,708.94, PnL of $509,993.24
- Sources: sources/phase3/RAPPORT_PHASE3_2026-09-29.md ; sources/phase2/pnl_table.json ; results/accounting_audit_2026-11-04.json
- Method: SELL + REDEEM + MERGE + value - BUY - SPLIT, aggregated across the eight accounts before rounding to cents. The November 4 arithmetic audit corrects the one-cent rounding-order difference in the original report; source files are preserved.
- Limits: These 8 accounts only. Recalculation of the published tables, not a new RPC collection. External net cash flow and trading PnL are different measures.
- Links: none

## F-003 | HYPOTHESIS | These 8 accounts may be controlled by one person or a small group sharing wallets
- Sources: sources/RAPPORT_2026-09-29.md
- Method: Inferred from funds between accounts and shared personal deposits
- Limits: Labeled INFERRED by the report. No owner identified
- Links: none

## F-004 | HYPOTHESIS | The timing of the bets may be compatible with prior information on two US military operations
- Sources: sources/RAPPORT_2026-09-29.md ; sources/phase2/RAPPORT_PHASE2_2026-09-29.md
- Method: Comparison of buys with the minute CLOB price
- Limits: Compatible only. Phase 2 shows 128 YES buyers in the Iran window: the network is far from alone
- Links: none

## F-005 | SUPPORTED | The service paying the network is identified as MoonPay: outcome B, a strong but unproven identification, customers unknown
- Sources: sources/phase6/RAPPORT_PHASE6.md ; sources/phase7/RAPPORT_PHASE7.md
- Method: Falsification tests, links between wallets, external sources
- Limits: The name comes from labels and outside documents. A payment says nothing of the customer. Only a legal request would prove it
- Links: none

## F-006 | REFUTED | None of the 8 preregistered signals is exploitable out of sample, across 288 comparisons
- Sources: sources/phase8/RAPPORT_PHASE8.md ; sources/phase8/PROTOCOLE_PREENREGISTRE.md
- Method: Preregistered protocol, TRAIN, VALID and TEST split
- Limits: MoonPay funding is too rare to test
- Links: none

## F-007 | SUPPORTED | The SIG_HIST signal precedes moves: LEAD60 of 30% against 10 to 13% for matched buys, a gap reproduced in VALID and TEST
- Sources: sources/phase9/RAPPORT_PHASE9.md ; sources/phase9/frozen_spec.json
- Method: Thresholds frozen on TRAIN, matched controls
- Limits: Cause unknown, this says nothing about insiders. The target is dominated by context
- Links: none

## F-008 | UNRESOLVED | Capturing the lead across all alerts is neither demonstrated nor refuted: the achievable return stays UNKNOWN with public data
- Sources: sources/phase10/RAPPORT_PHASE10.md
- Method: Preregistered strategy, 10 criteria
- Limits: Depth is visible only through consumed makers
- Links: none

## F-009 | REFUTED | The second buy of a SIG_HIST wallet offers no executable window: -0.7% net in TEST, outcome B of the protocol
- Sources: sources/phase14/RAPPORT_PHASE14.md
- Method: Preregistered tree, blocking control of the definition
- Limits: Stays predictive without being executable. Wide interval: -7.7 to +7.1
- Links: none

## F-010 | CONFIRMED | INFRASTRUCTURE NOT VALIDATED: live audit against the chain on 151,313 trades, 4 defects shown, including the false market created by RTDS
- Sources: sources/phase15/RAPPORT_PHASE15.md
- Method: Independent recorder p15_audit.py, chain as truth
- Limits: Audit of 2 h 26. Fixes proposed, not applied
- Links: none

## F-011 | REFUTED | 0x73e237f9 did not win on Maduro, against the conclusions of July 30: no activity before April 30, 2026
- Sources: sources/RAPPORT_2026-09-29.md
- Method: data-api /activity, independent check on pUSD flows
- Limits: The figures belonged to 0x6baf05d1, a cache contamination
- Links: none

## Contradictions

- F-007 shows a predictive signal, F-008 and F-009 show it cannot be captured. Neither identifies an insider.

## Missing to conclude

- KYC registers of the service for the 16 payments into the network, the n.exchange order, the MEXC deposit: legal requests, out of reach of a public investigation.
- Customer identities: unknown.

## Prospective monitoring

- Streaming detector `sources/scripts/p9_detector.py`, research only, frozen on TRAIN.
- Before any live restart: apply the fixes listed at the end of `sources/phase15/RAPPORT_PHASE15.md`, or the infrastructure stays unvalidated.
- A wallet is known about 2 seconds after its trade, and the exploitable move is inside the trade itself (phase 13).
