# Forensic Casebook — Evidence, Counterarguments, Reproduction

**Snapshot:** 18 November 2026 · **Companion:** [Industry Research Portfolio](INDUSTRY_RESEARCH_PORTFOLIO.md)

This is a reviewer-oriented index of work **already published in the main repository**, not a directory of accused individuals. It does not combine different accounting populations, promote press allegations to chain evidence, or substitute successful predictions for proof of non-public information.

## How to read an investigative finding

| Evidence class | Accepted meaning | Rejected inference |
|---|---|---|
| Exact on-chain transfer | Identifiable sender, recipient, contract, amount, time, block and transaction evidence | The parties are the same human or entity |
| Service-mediated route | Provider order or protocol identifier matches the receiving leg; available receipts reconcile | Identical tokens moved end-to-end, or the exchange credited one known customer |
| Shared cash-out endpoint | Accounts paid a specific common on-chain address | One controller without exchange/internal account evidence |
| Trade clustering | Observed entries/positions have temporal or financial characteristics | Insider trading without an unbiased reference population |
| Statistical price-relative excess | An event-time, price-adjusted estimate in a declared population | Tradable profit without contemporaneous asks, depth, fees and actual alert latency |
| Public reporting / official proceedings | Dated external statements or filed allegations, with original attribution | Final adjudication, civil identity of an on-chain wallet, or independent replication |

Every material edge must have a typed proof tier. The repository-wide evidence rules are in [METHODOLOGY.md](METHODOLOGY.md).

## 01 · Iran February 2026 — 38-proxy trading and cash-out routes

**Observed:** 38 distinct trading proxies; 36 opened over 22–25 February. The archived cohort traded NO before YES ahead of the final February repricing. Thirty-two proxy addresses transferred Polygon USDC/USDC.e directly to one recipient. Three more Polygon proxies generated 12 individually matched Relay provider orders and ERC-20 credits. Separate Arbitrum and Base legs have weaker or incomplete replay support.

**Accounting:** +1,576,522.86 USDC aggregate recorded trading result, including valuations of remaining shares for eight accounts. The recipient's gross observed Polygon transfers reconcile to 1,984,038.168550 in and the same amount out over the defined archive window; the two sides are **not** additive profit.

**Verification links:** [G38 strict proof-tier report](research_notes/g38-proof-tier-audit-2026-11-08/REPORT.md); [independent RPC caveats](research_notes/independent-forensic-audit-2026-11-08/REPORT.md); [wallet-level ledger](research_notes/x-history-2026-11-06/verification/data/g38_accounts.csv).

**Critical counterarguments:** exchange-like deposit wallets can be shared or internally multiplexed; selected wallets are not a random population; Relay may fund destination receipts from solver inventory; Base raw receipts are not archived for independent replay; identical later exits do not prove coordination before entry.

**Admissible conclusion:** strong transfer and timing evidence; one customer account, operator identity, synchronized-trading significance, and information access **UNRESOLVED**.

## 02 · Maduro / Iran — eight-account cross-chain funding network

**Observed:** transaction paths connect eight accounts through Polygon, Ethereum and TRON, including direct account-to-account payments and intermediate keys.

**Accounting:** +509,993.24 reconstructed trading PnL includes remaining position value across the accounts' recorded histories. External inflows 151,084.40, external outflows 660,708.94, net external flow +509,624.54. These are different measures with separate boundaries.

**Verification links:** [Investigation findings](investigations/maduro-iran/FINDINGS.md); [phase-two financial graph](investigations/maduro-iran/sources/phase2/RAPPORT_PHASE2_2026-09-29.md); [full-precision audit](investigations/maduro-iran/results/accounting_audit_2026-11-04.json).

**Critical counterarguments:** transfer paths may reflect treasury management or counterparties rather than common control; partially common market narratives can select connected winners; transaction accounting cannot reveal a private source of knowledge.

**Admissible conclusion:** a financially connected network and reconstructable amounts, not a confirmed insider conspiracy.

## 03 · Nobel Peace Prize 2025 — owner-key funding and historical warning

**Observed:** one owner key of the 6741 Safe sent 372,521.54 USDC to eight Polymarket accounts during the documented October 9–10 window. The investigation also reconstructs 16 Relay withdrawals and further related financial paths.

**Detection replay:** the retrospective LONELY_THIN alert for the Nobel case fires at 23:00:15 UTC on October 9, ahead of the following day's public announcement. However, the case **inspired the rule** and is not independent validation of the detector.

**Verification links:** [Follow-up findings](investigations/followup-20261113/FINDINGS.md); [dated historical monitoring replay](BACKTEST_RESULTS.md); [monitor implementation](monitoring/README.md).

**Critical counterarguments:** a treasury can fund different wallet controllers; a rule fit after studying this case can rediscover it by construction; a correct forecast may have relied on public clues or a speculative purchase.

**Admissible conclusion:** auditable common funding and a historically reconstructable alert, not a measured pre-event insider-identification rate.

## 04 · Ballon d'Or 2026 — account flows and a further Kane account

**Observed:** 15 public screenshot positions matched historical fills within half a share, and 11 accounts were mapped to their underlying trading wallets. The key related to brace227 paid 5,170 USDC to a key associated with an additional Kane-focused account (16 purchases). A separate tiny ETH transfer links brace227 and kraben006 keys.

**Accounting:** 304,137.63 USD deposits and 493,094.76 USD withdrawals across the 11 original accounts; +129,367.79 USD applies **only** to seven settled accounts. The additional Kane account is excluded.

**Historical-source caution:** the October 16 public ranking is explicitly present in its archived response; the shorter rechecked October 14 response does not independently establish the full earlier five-name ranking. Published predictions are not automatically evidence of secret information.

**Verification links:** [Wallet report](investigations/ballon-dor-wallets/FINDINGS.md); [flow-trace proof](investigations/ballon-dor-flow-trace/FINDINGS.md); [independent audit](investigations/ballon-dor-audit/README.md).

**Admissible conclusion:** several direct value relationships and reconstructed positions; common control and informed trading remain unproved.

## 05 · KPMG-related earnings markets — matched transfer handoffs

**Observed:** 14 recorded account-to-account value handoffs via Relay and chain legs, each with archived transaction anchors and matching intermediary credit/debit amounts. The recorded L1-to-L2 delays are 18–50 seconds. The expanded study resolves 22 proxies.

**Known statistical correction:** the 19-account and 22-account cohorts were previously conflated, and the original success-probability computation used a reference price for an event with a different success definition. Public SEC filing acceptance timestamps are not necessarily the first public earnings announcement.

**Verification links:** [Archive and transaction tables](research_notes/financial-links-replay-2026-11-07/REPORT.md); [statistical correction](research_notes/kpmg-statistical-correction-2026-11-10/REPORT.md); [archive-level independent recalculation](research_notes/financial-cycle-negative-control-20261118/REPORT.md).

**Admissible conclusion:** specific recorded transfer handoffs, not a calibrated probability of inside information.

## 06 · Railgun-funded Venezuela network — negative-control case

**Observed:** 22,044.16 USDC unshielded into six distributor addresses; 384 child wallets; 71 child deposits credited 71 distinct Polymarket accounts. All 71 placed one recorded bet. Five won, 66 lost; every winner traded the same Venezuela market.

**Recomputed controls:** recorded purchase cost 21,965.645223 USDC; unweighted mean entry price 0.055063; potential payout if redeemed 53,113.161821 USDC. A potential redemption payout is **not proof of realized profit**.

**Verification links:** [Source investigation](research_notes/financial-links-replay-2026-11-07/REPORT.md); [read-only replay and rejection controls](research_notes/financial-cycle-negative-control-20261118/REPORT.md).

**Admissible conclusion:** a distinctive funding fingerprint can coexist with mostly losing bets. Selecting only its five winners manufactures a misleading headline. The market outcome is shared: do not count 71 wallets as 71 independent events.

## 07 · Cross-market wallet transfers — Pulser, cashy, Car

**Observed:** 25 direct same-hash transfers between Pulser and cashy, a 250 USDC payment to Car, and a separate 1,000 USDC comparison transfer: 27 indexed payments and 14,699.999999 USDC directional transfer volume. The verifier rederives those edges from 7,596 archived activity rows.

**Verification links:** [Transaction graph and control data](research_notes/iran-pulser-cashy-crossmarket-2026-11-06/REPORT.md); [independent Inca overlap assessment](research_notes/inca-crosscheck-2026-11-06/REPORT.md).

**Admissible conclusion:** direct financial relations, not a unique account controller; transfer volume is not PnL.

## 08 · Ethereum → Monad — completed Relay/vault trace

**Observed:** a key associated with the additional Kane account sent 2,969.568353 mUSD in an Ethereum-to-Monad Relay/vault operation. A destination transaction credited 2,904.308540 vmUSD vault shares 29 seconds after the originating transaction.

**Critical unit distinction:** mUSD and vmUSD represent different instruments. Their numerical difference is not automatically a trading loss or fee.

**Verification links:** [Receipt-backed reconstruction and verifier](research_notes/relay-followup-2026-11-04/REPORT.md).

**Admissible conclusion:** the cross-chain path is evidenced. Attribution of the payment to specific Polymarket winnings is not established without a full intermediate-balance reconciliation.

---

## Scientific counter-tests that constrain interpretation

| Study | Why it matters | Primary record |
|---|---|---|
| **LONELY_THIN** | A memorable early historical alert was not enough: 45 validation alerts, 13 winners, +3.5 pp versus a 25.4% mean price, p=0.33. | [Pattern research](PATTERN_RESEARCH.md) |
| **Collective exposure** | A 6-hour largest-alert selection produced noncausal timestamps; the first-causal-firing check changes sign but does not validate an edge. | [Final audit](investigations/collective-exposure-shifts/AUDIT.md) |
| **Quote/execution diagnostics** | 15,555 paired YES+NO quotes yielded no gross basket violation; taker execution costs matter even in flat markets. | [Execution results](edge_research/results.md) |
| **Funding-tree negative control** | 71 linked bets gave only five wins on one market; selected successes are not a denominator. | [Financial-cycle replay](research_notes/financial-cycle-negative-control-20261118/REPORT.md) |

## Practical independent-review route

**Evidence first:** [VERIFIED_FINANCIAL_FINDINGS.md](VERIFIED_FINANCIAL_FINDINGS.md) → the cited report → archived receipts/CSV → corresponding offline verifier.  
**Scientific claims:** [METHODOLOGY.md](METHODOLOGY.md) → frozen plan and its lock → result registry → audit and false-positive/censoring checks.  
**Execution:** [EDGE_VERDICT.md](EDGE_VERDICT.md) and [monitoring documentation](monitoring/README.md).  
**External research:** [76-source bibliography](research_notes/external-market-abuse-corpus-20261117/README.md); original authors retain attribution.

The [master report](MASTER_REPORT.md) lists the formal investigation status and [the inventory](INVENTORY.md) identifies raw datasets that remain local-only. Offline replay verifies the archived objects it actually contains, not necessarily the complete acquisition history.

**Bottom line:** Financial relationships and archive arithmetic can be demonstrated at transaction level; **an operational, low-false-positive, net-profitable detector of informed trades has not yet been validated**.
