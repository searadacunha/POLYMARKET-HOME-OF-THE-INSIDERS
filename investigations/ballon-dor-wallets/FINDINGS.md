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

## F-008 | REFUTED | The close withdrawals of brace227 and kraben006 show no measurable signal: 10 of 20 comparable sellers also withdraw within 5 minutes, p = 0.29
- Sources: sources/reports/AMENDEMENT_AUDIT_2026-11-02.md ; sources/reports/CONTRE_VERIFICATION.md
- Method: Post hoc comparison with sellers of Kane at 0.99
- Limits: Exploratory. Tests the speed of withdrawal. Their sales are 78 seconds apart, against a median gap of 45 seconds between consecutive sales of these 22 sellers. Their withdrawals are 166 seconds apart, as close as 8 of 105 pairs, with no correction for the choice of this pair
- Links: none

## F-009 | UNRESOLVED | The base rate of version 1 is invalid, 48 of 78 wallets are unusable, and the KuCoin gap is neither supported nor refuted
- Sources: sources/reports/CONTRE_VERIFICATION.md ; sources/reports/rapport_final.md
- Method: Recount, cross-check with flow-trace
- Limits: Flow-trace rereads 77 controls: Solana origin 3/11 against 6/68, p = 0.11; KuCoin 3/3 against 1/6 on 9 wallets; no trait passes the corrected threshold of 0.0056. The real rate beyond this exploratory reread stays unknown
- Links: ballon-dor-audit:F-003 ; ballon-dor-flow-trace:F-010

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

## F-014 | CONFIRMED | The ETH sent to the key of kraben006 follows a Relay order paid from the Solana address 7XUJsJBNp7WykVXG4y76ntsSn3H7tFdLVcmehAgJfrZc: same identifier on both chains, and at least 81.4% of the amount must come from that payment
- Sources: sources/evidence/contre_verification_20261102/identifiant_relay_7xujs.json ; sources/evidence/contre_verification_20261102/circuit_7xujs_brace_kraben.json ; sources/reports/rapport_final.md ; tx 0xb17e1c4627ad8914f98f48a4fa7f5916953d3286e60cf3d80c6508257f46ce3c (Ethereum, block 26119411)
- Method: Identifier read in the Solana instruction and in the payment calldata, balances in wei cross-checked at those blocks on an archive node (sources/tools/cv_14_identifiant_relay.py, sources/tools/cv_17_circuit.py)
- Limits: The solver pays from its own stock: same order, equal value, not the same coins. The next hop, to 0x7e67…, is simple succession: only 22.7% of what was received is forced by accounting. Says nothing of who holds the Solana address
- Links: ballon-dor-flow-trace:F-003

## F-015 | CONFIRMED | That transfer sends 98.85% of the ETH balance of the key of brace227, which stays in use and holds 22,024.57 USDC on November 2: neither abandoned nor drained
- Sources: sources/reports/rapport_final.md ; sources/evidence/contre_verification_20261102/circuit_7xujs_brace_kraben.json
- Method: Balances in wei before and after the transfer, later activity of the key
- Limits: ETH only, about $5.53. A send-max reading is an inference. Motive unknown, see the hypotheses in section 4 of the report. The gas-gift reading of the audit is weakly supported
- Links: ballon-dor-audit:F-002

## F-016 | UNRESOLVED | 0x86544e4dfde and walletwallet8424 withdraw 96 and 189 seconds after their Kane redemption, against 1 of 175 comparable accounts within 5 minutes: atypical raw, not significant after correction in the closest strata
- Sources: sources/reports/CONTRE_VERIFICATION.md ; sources/evidence/contre_verification_20261102/stats_retraits_kane.json ; sources/evidence/contre_verification_20261102/tests_exploratoires.jsonl
- Method: Post hoc Fisher test across 13 strata of 24-hour activity windows (sources/tools/cv_15_stats_retraits.py)
- Limits: Written after seeing the data, one event, two accounts, selected by the press. Raw p from 0.0002 to 0.0069, corrected for 55 pairs from 0.010 to 0.38. Notifications, wallet software and time zone not measured. The 93 seconds between them add nothing once both are fast. Proves no link
- Links: none

## F-017 | UNRESOLVED | brace227 and kraben006 are the two largest taker buyers of Kane between 14:00 and 17:00 UTC on October 24, the day after the article: 45% of purchases and 8 close buys, with no finer synchrony, p = 0.40
- Sources: sources/reports/rapport_final.md ; sources/evidence/contre_verification_20261102/derniers_controles.json ; sources/evidence/contre_verification_20261102/stats_retraits_kane.json
- Method: Shift test inside the window, comparison with the 14 other taker buyers of $100 or more
- Limits: Exploratory, window chosen after the fact. The p = 0.0012 of the audit shifts by days and mostly measures two accounts active the same afternoon. Of the 9 close buys over their whole activity, 0 predate October 13
- Links: none

## F-018 | REFUTED | Transactions shared between dossiers are no link: of 14, 8 are batches and 5 are joint makers against a third party; the only direct execution is ordinary on an order book
- Sources: sources/reports/rapport_final.md ; sources/evidence/contre_verification_20261102/transactions_communes.json
- Method: Receipts read, OrderFilled logs decoded, over the complete activity of the 11 wallets
- Limits: Covers these 11 wallets only
- Links: none

## F-019 | REFUTED | The candidate of 59.09 POL from 0xc590175e458b83680867afd273527ff58f74c02b to 0x408ce42ac7538e5a6f53324585075470d1b3c5b3 is not a transfer between dossiers: the recipient itself pays 5.62 USDC through a shared contract
- Sources: sources/reports/rapport_final.md ; sources/evidence/contre_verification_20261102/faux_signaux.json ; tx 0x4b89cf4f04f9ce694b9dc26bc870fd873a5e00aa71ce1d3e99fd556a75005ac8 (Polygon)
- Method: Receipt read, native and token moves listed
- Limits: The contract also served the deposit of walletwallet8424: it is shared, not a link
- Links: none

## F-020 | REFUTED | The matching exit of VidenteRibeira and cookedrice comes from the service GxjcMTWWDcKx5sxnHkNfPtuTSfV9cLgVkw3G7KvMnvBW, which cosigns and pays the fees 4 and 2 seconds after receipt
- Sources: sources/reports/rapport_final.md ; sources/evidence/contre_verification_20261102/faux_signaux.json ; sources/evidence/hub_ee7a_gxjc.json
- Method: Solana transactions read, signers and fee payer compared. One second after each sweep, the service sends exactly 1.00% to the same address 2zEAZhgyiAyr5UWFp77gypzPuFz3oEfEpjdyGLVQkmhv: 391.58 of 39,158 and 514.89 of 51,489
- Limits: The shared choice of this service stays unexplained, with no link value shown. That these are deposit addresses of the service, and that the 1.00% is a fee, is probable, not proven
- Links: none

## F-021 | SUPPORTED | Two addresses labelled ChangeNOW by Blockscout touch the key of kraben006: 834.85 USDC received in February 2026 and 0.00241406 ETH reaching a deposit address on October 4. No XMR exchange is observed
- Sources: sources/reports/rapport_final.md ; sources/evidence/contre_verification_20261102/etiquettes_blockscout.json
- Method: Labels in the from and to objects of the saved Blockscout transactions, which the address page returned empty
- Limits: Single label source. A label does not prove that an exchange took place, nor what it returned. Nothing ties these funds to a bet. Version 1 wrote that no such label existed
- Links: changenow-proof:F-001 ; changenow-proof:F-004 ; ballon-dor-flow-trace:F-014

## F-022 | CONFIRMED | The 17 cut comparator histories of the base rate all stop before the first family buy, 17 of 17, while all 11 named histories are complete, so the accounting stands
- Sources: sources/reports/CONTRE_VERIFICATION.md ; sources/evidence/contre_verification_20261102/coupure_par_comparateur.json
- Method: The 12 pages replayed from the HTTP cache, no network (sources/tools/cv_05_coupure.py)
- Limits: The raw cache is not published: only the result file is. Replay needs the original machine
- Links: ballon-dor-audit:F-003

## F-023 | CONFIRMED | E4 v2 is reproducible, 6 of 6 outputs identical under another hash seed, but 19 of 55 named pairs are never tested on October 23 and 45 of 55 on October 13
- Sources: sources/evidence/contre_verification_20261102/e4_reproduction.json ; sources/reports/rapport_final.md
- Method: Frozen code rerun on three seeds and two dates, nothing written in the study (sources/tools/cv_12_e4.py)
- Limits: Of the 45, 40 come from accounts with no buy at that date and 5 from a filter absent from the frozen plan. The threshold only sees an extreme
- Links: ballon-dor-audit:F-004

## Contradictions

- The audit calls the fast withdrawals of 0x86544e4dfde and walletwallet8424 a false positive: the calendar explains the redemption, not the withdrawal (F-016).
- `ballon-dor-flow-trace` writes that the 1% service attributed to `GxjcMTWW…` was not found because the sweeps take nothing. Both readings hold on their own scope: the sweep takes nothing, and the next transaction, one second later, sends exactly 1.00% to 2zEAZhgyiA… in both cases (`sources/evidence/hub_ee7a_gxjc.json`).
- The date D2 of the frozen plan, October 13 at 18:51:00 UTC, falls 60 seconds after a buy by Thin. The plan does not justify it. Part A does not depend on it: the rank alone decides the verdict.
- `sources/collective/results.md` and the freeze were not changed: they still carry the earlier readings, flagged in the amendment.
- The audit and version 2 wrote 53 unusable comparators of 83: the recount gives 48 of 78 distinct wallets.

## Missing to conclude

- Open decisions listed in the amendment: XMR status, a file on `0xa8e64a3c…`, protocol amendments, closing `collective/`, publication.
- BSC and Base histories, exchange accounts: private registers.
- Older Safe and Magic proxies were not tested in the search for other wallets (flow-trace).
