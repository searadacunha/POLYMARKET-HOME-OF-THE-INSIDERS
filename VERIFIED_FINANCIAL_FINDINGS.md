# Verified Financial Findings

A direct index to the strongest reconstructed cash flows and trading histories in **Polymarket, Home of the Insiders**. All figures are scoped to their underlying ledgers; they are not a claim of inside information or beneficial ownership.

The core results are documented in the [November 6 historical-wallet verification](research_notes/x-history-2026-11-06/verification/REPORT.md), [Maduro/Iran transaction accounting](investigations/maduro-iran/sources/phase2/RAPPORT_PHASE2_2026-09-29.md) and the [Ballon d'Or cash-flow reconstruction](investigations/ballon-dor-wallets/sources/reports/rapport_final.md). **The eight-account Maduro/Iran network and the separate 38-account Iran cohort have different defined populations; do not sum their results into a unique population-wide PnL without a reconciliation of scope and overlap.**

## 1. The 38-account Iran payout network

The historical verification resolves 38 accounts (including four already examined in an earlier group G investigation). Their recorded ledger outcomes total **+$1,576,522.86 USDC**.

| Observation | Reconstruction |
|---|---|
| Accounts | **38** |
| Created between February 22 and 25, 2026 | **36** |
| Sequence for those 36 | NO positions on Iran strike deadlines, followed by YES purchases |
| YES purchases by that 36-account subset | February 27, **20:49–23:35 UTC** |
| Identified common destination | `0xc5bb1be0407db7312911ec765d399d02461e411a` |
| Combined recorded account results | **+$1,576,522.86 USDC** |

All 38 account payouts were reconstructed as reaching this **Coinbase-style customer deposit address** directly or through documented Relay delivery routes. On Polygon, the address received and swept **1,984,038.17 USDC/USDC.e** between January 5 and March 9. That figure is a **gross flow**, not profit.

A second, transaction-specific connection was documented: `flipfloppity` withdrew **9,990.03 USDC** via Relay to `0x12d5b13fc89bcae0e68557a42d6bf9ec319b7944`, which routed the same amount toward the account labelled `Anon`, with **9,987.65** credited after the protocol route. This is a **value path**, not an inference from matching prices or use of a common exchange.

The entry side is now read for all 38 accounts: 86 Relay deposits from **39 separate funding wallets**, none shared by two accounts. Where the funding wallets were read one hop further (Polygon and Ethereum), they were fed by Robinhood or Coinbase hot wallets ([deposit origins](research_notes/financial-links-replay-2026-11-07/data/g38_deposit_origins.csv)).

**Status:** cash-out convergence and the particular inter-account funding path are supported by receipts/Relay records. The destination is consistent with a customer deposit for one exchange account; the natural person, organisation or group behind it remains unknown. Incomplete Base/Arbitrum and inbound funding histories preclude broader owner attribution.

**Evidence:** [38-account reconstruction](research_notes/x-history-2026-11-06/verification/REPORT.md), [per-account data](research_notes/x-history-2026-11-06/verification/data/g38_accounts.csv), [verification script](research_notes/x-history-2026-11-06/verification/verify.py).

## 2. An eight-account Maduro/Iran funding network

- **Eight financially connected Polymarket accounts**, with verified value-transfer paths on Polygon, Ethereum and TRON.
- **+$509,993.24** aggregate recorded trading PnL, including remaining position value across the accounts' published trading histories, **not only the two headline markets**.
- **$151,084.40** external inflows and **$660,708.94** external outflows; **+$509,624.54** net external flow over the reported accounting window.
- Individual examples of funding relationships: `chileno777` to `TacticalInsiderNews`, `Mrs.Joker` to `Planktonbets`, and `X34` through an intermediate Ethereum address to `Mrs.Joker`.

**Evidence:** [phase-2 transaction graph and accounting](investigations/maduro-iran/sources/phase2/RAPPORT_PHASE2_2026-09-29.md) and [full precision audit](investigations/maduro-iran/results/accounting_audit_2026-11-04.json).

## 3. A cash-out destination joining Venezuela and Iran betting histories

Three additional accounts paid the same Ethereum address, `0xd12623958b81d71e8be3fa936aed6d8c2528e992`, through recorded Relay withdrawal routes:

| Account | Market family | USDC withdrawals to that address |
|---|---|---:|
| `Frogensky` | Venezuela | **101.64** |
| `JamWil23` | Maduro / Venezuela | **9,962.37** |
| `bravonoll` | Iran strikes | **42,858.47** |

The receiving address had gas deposits from a Coinbase hot wallet and transferred its balances to Coinbase Hot Wallet 10 shortly after receiving them. The common destination is independently meaningful; use of this address **does not alone prove** a common trader, account controller, or access to non-public information.

**Evidence:** [wallet histories and Coinbase sweeps](research_notes/x-history-2026-11-06/verification/REPORT.md), section 3.1.

## 4. A recurring Iran trader: `flydartball`

The reconstructed account ledger covers multiple Iran markets from June 2025 to February 2026:

- Before the February 28, 2026 repricing, **359,679.08 YES shares** were held on the strike-by-February-28 market.
- On the earlier June 2025 Iran market, final settlement and sales produce **+$256,137.07**.
- Across the recorded trading history, the account result is **+$841,375.23**, including both profitable and losing Iran markets.

This is an unusually large trading history that can be examined without relying on X narratives. It does not by itself reveal the trader's source of information.

**Evidence:** [account ledger and receipt-based checks](research_notes/x-history-2026-11-06/verification/REPORT.md), section 5.

## 5. Ballon d'Or 2026: positions, published forecasts, and financial connections

- Before an October 14 public discussion, `Thin-Disclaimer-Life` held **66,799.56 shares** on Mbappé above Yamal and **3,916.35 shares** on Rodri above Messi. Those share totals agree with the archived public screenshot and ledger.
- On October 16, @Cypya_Poly publicly published the final five names in correct order. A Polymarket account declaring that X username held positions aligned with **seven ranking facts** in markets already available before publication.
- Eleven accounts associated with news coverage had **$304,137.63** of observed deposits and **$493,094.76** of withdrawals. The **+$129,367.79** subset total applies to **seven settled accounts** and is not a universal net-profit claim for eleven accounts.
- A key associated with `brace227` transferred approximately **0.002048944 ETH** to a key associated with `kraben006`, and **5,170 USDC** to the key of an additional Kane-betting Polymarket account. These are on-chain value transfers, distinct from same-market buys or service co-usage.

- 57 hours before Cypya, on October 14 at 08:23:34 UTC, @SnoorrasonPoly's long-form post already listed "1)kane 2)mbappe 3)yamal 4)rodri 5)messi". The text was recovered identically from two mirrors of X; the post was never edited. The author infers that order from Polymarket prices.

**Evidence:** [October 2026 chronology and account verification](research_notes/x-history-2026-11-06/verification/REPORT.md), [Ballon d'Or findings](investigations/ballon-dor-wallets/FINDINGS.md), [transactional report](investigations/ballon-dor-wallets/sources/reports/rapport_final.md) and [recovered long-form text](research_notes/financial-links-replay-2026-11-07/REPORT.md#7-snoorrason-14-oct-2026-082334-utc-2110285369748963671).

## 6. KPMG-client earnings bets: fourteen account-to-account handoffs

Bitquery reported a network of 22 accounts that bet on companies audited by KPMG. Replayed from primary chain data:

| Observation | Reconstruction |
|---|---|
| Accounts resolved to Polymarket proxies | **22 of 22** |
| Withdrawal of one account becoming the deposit of another, matched by Relay keys on Polygon and Solana | **14** (the 11 published, plus 3) |
| Time from withdrawal to credit | **18–50 seconds** |
| Withdrawal destinations shared by several accounts, all exchange-style customer deposit addresses | **7**, paid by no account outside the group |
| Record on the 21 KPMG-audited markets held at the SEC results filing | **20 won** on the biggest-stake rule (p = 0.00116); **18 won** if any account's losing side counts (p = 0.040) |

The first account, `Youaregu`, sent its payouts to three Solana deposit addresses that `KARLSON1970`, `kundragame` and `pops4532` also paid. Those payouts were therefore credited to the same exchange customer accounts. Each handoff is an account-to-account value path; the probabilities are conditional on a group chosen for its record, and describe no information source.

**Evidence:** [chain replay and tables](research_notes/financial-links-replay-2026-11-07/REPORT.md), [verified handoffs](research_notes/financial-links-replay-2026-11-07/data/kpmg_handoffs_verified.csv), [shared deposit addresses](research_notes/financial-links-replay-2026-11-07/data/kpmg_shared_deposit_addresses.csv).

## 7. A Railgun-funded tree of 71 single-bet Venezuela accounts

| Observation | Reconstruction |
|---|---|
| Railgun Unshield events on December 16, 2025, to six fresh distributor wallets | **22,044.16 USDC** |
| Child wallets funded by those distributors | **384** |
| Relay deposits from the children, each crediting a new Polymarket account | **71**, all resolved by chain data |
| Unshielded USDC accounted for | **21,977.51** to the 71 deposits, **66.65** left in children: the tree is closed |
| Bets | **one per account**, December 19 to January 2, on Venezuela regime-change long shots |
| Results | **66 lost** (deadlines in 2025); **5 won** on "Maduro out by January 31, 2026?" |
| Winning shares never redeemed (November 7, 2026) | **53,113.16** |

The four accounts published on X as "Railgun-funded Maduro insiders" are four of the five winners of this tree. The 66 losing accounts from the same source show a spray of cheap bets across adjacent deadlines, not a precise date. The common funding tree is a verified fact; who operated it, and why, remains unknown. None of the 71 accounts appears in the eight-account network (section 2).

**Evidence:** [tree reconstruction](research_notes/financial-links-replay-2026-11-07/REPORT.md#2-maduro-railgun-lead-one-distribution-tree-71-single-bet-accounts-66-losers), [accounts and bets](research_notes/financial-links-replay-2026-11-07/data/railgun_tree_accounts.csv), [edges](research_notes/financial-links-replay-2026-11-07/data/railgun_maduro_edges.csv).

## 8. Biden-pardon market accounts: one deposit address

Withdrawals of the two trading proxies `0xd9be4e8f…` (**337,487.34 USDC**, 16 withdrawals) and `0xa416a5c0…` (**146,504.52 USDC**, 9 withdrawals) reach the same Polygon address, `0x0a65fdd872da9fc9a16a37a9c10be8e8362d8d7e`. The **25 traced cashouts total 483,991.868223 USDC**; those funds are swept to `0x4b6f17856215eab57c29ebfa18b0a0f74a3627bb`.

The address is **not exclusive** to these accounts. An additional **453.947234 USDC** arrived from `0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222` on November 15, 2025, and was swept to a different destination, `0x0853ea40b121f9135d7e0c07fae35d59aedb4d0b`. The overall USDC flow is **484,445.815457**, but this extra transfer cannot be attributed to either trading proxy. The shared payout path is confirmed by receipts; no exclusive ownership, shared natural-person identity or named exchange is established.

**Evidence:** [withdrawal receipts](research_notes/financial-links-replay-2026-11-07/data/biden_pardon_shared_deposit.csv), [report section 3](research_notes/financial-links-replay-2026-11-07/REPORT.md#3-iran-cohorts-and-the-pardon-accounts).

## 9. XFM paired wallets: 37 numbered accounts consolidated into two wallets

On a market about Anthropic's public ticker, accounts named `xfm-<series>-<n>` bought YES and NO against each other in two-party matches: nine published receipts, 1,779.93 shares on each side, a fee paid each time and no price edge. On **October 15, 2026**, 37 accounts of series 5–8 withdrew to two Polygon wallets in numeric order, within 46 minutes:

| Collector wallet | Accounts | Window (UTC) |
|---|---:|---|
| `0x91243b658072dc08218b9868cc55e7cdc2cbfadc` | 20 (series 5 and 6) | 14:34–14:57 |
| `0x75a4aeb14de48105037fefc03e33512f1a0c1173` | 17 (series 7 and 8) | 15:10–15:20 |

The first collector had also paid for `xfm-6-1`'s first deposit in January. The matched trades are therefore between accounts whose balances end in the same wallet. This is consistent with volume or incentive farming; it is not evidence about information.

**Evidence:** [decoded receipts](research_notes/financial-links-replay-2026-11-07/data/xfm_nine_receipts_decoded.csv), [collector credits](research_notes/financial-links-replay-2026-11-07/data/xfm_collectors.csv), [report section 4](research_notes/financial-links-replay-2026-11-07/REPORT.md#4-xfm-paired-wallets-nine-mint-matches-two-collector-wallets-for-37-numbered-accounts).

## 10. Iran cluster E: order-linked Polygon to Solana payments

A separate February 2026 Iran investigation recovered **11 Relay orders from four Polymarket accounts**, depositing **70,065.262869 USDC.e** on Polygon and delivering **856.840698827 SOL** to the same Solana beneficiary. That wallet subsequently transferred **842.687802663 SOL** to a destination classified as a Bybit customer deposit address. The Polygon order identifiers and Solana fills establish the recorded cross-chain routes; an exchange deposit address does not disclose the credited customer's identity.

The broader **19-account cluster E** includes independently archived account-to-account payment paths as well as shared exchange deposit destinations. It must **not** be conflated with the separate 38-account Iran payout cohort (section 1), or with the eight-account Maduro/Iran investigation (section 2). The later erratum clarifies that some exchange-service classifications rely on Blockscout labels as well as observed sweep behaviour. A Privacy Cash withdrawal shortly after a deposit is **not** cryptographically attributed to those deposited coins.

**Evidence:** [cross-chain receipt/order replay](research_notes/iran-solana-beneficiary-2026-11-05/REPORT.md), [19-account network and verifier](research_notes/iran-cluster-e-network-2026-11-05/REPORT.md), [classification erratum](research_notes/iran-cluster-e-erratum-2026-11-06/REPORT.md), [Privacy Cash sequence and limits](research_notes/iran-privacy-cash-sequence-2026-11-06/REPORT.md).

## 11. Independent Inca overlap and further Iran exits

Comparing the **five wallets** singled out by Inca Digital's June 2025 Iran-market behavioural analysis with the independently developed February 2026 network found **two exact address intersections**: `9TungSahur` (later `TheOneWhoKnocks1312`) and `DonkeyDonkey999`. Matching account addresses is not identifying the natural persons. Reconstructed payments include DonkeyDonkey999's three withdrawals followed by credits to 9TungSahur's first-deposit route, and **65,992.25 USDC** paid by three network accounts into the same Bybit-classified deposit address on **13 June 2025, 01:42–02:27 UTC**. Such convergence is a financial relationship at a credited destination, not proof of common ownership.

A separate follow-up traced `ricosuave666`'s four Solana-bound bridge exits to one beneficiary and documented money routes involving `AugsburgFClover` and `metushelah`. Matching amounts in public reporting on an indictment do **not** identify a defendant, establish guilt or prove that someone traded on non-public information. Some classifications remain behavioural rather than transaction-exclusive.

**Evidence:** [independent cross-check, 54-buyer control population and archived receipts](research_notes/inca-crosscheck-2026-11-06/REPORT.md), [bridge exits, 39 indexed money legs and verifier](research_notes/inca-bridged-exits-2026-11-06/REPORT.md).

## 12. Pulser, cashy and Car: same-transaction cash flows in the control population

A fixed June 2025 Iran-market comparison cohort contains **25 distinct matched-hash withdrawal/deposit payments between `Pulser` and `cashy`**, with a combined directional transfer volume of **13,449.999999 USDC**. A further **250 USDC** payment from `cashy` to `Car`, and an unrelated **1,000 USDC** comparator transfer, bring the archived index to **27 transactions / 14,699.999999 USDC**. Each indexed payment has the same transaction hash in two different account activity records, reciprocal counterparties and matching amounts. The verifier rederives the index from **7,596 frozen activity rows**.

Pulser also appears in the separate February 2026 Iran early-buyer population. This is a wallet-level, cross-period observation. **Transfer volume is neither net investment nor realised profit; these accounts are not shown to belong to cluster E or to one operator.** The matched high-activity controls are useful specifically because repeated direct payments alone do not demonstrate inside information.

**Evidence:** [Pulser–cashy–Car graph and 27-hash index](research_notes/iran-pulser-cashy-crossmarket-2026-11-06/REPORT.md), [source cohort and receipt cross-check](research_notes/inca-crosscheck-2026-11-06/REPORT.md).

## Scope and reproducibility

The on-chain cases above have different evidence classes: confirmed transfers, reconstructed market positions, supported deposit-route convergence and historical source attribution. None proves insider trading or a common beneficial owner merely from the appearance of synchronised bets.

For raw source indexes, exact token/contract types, transaction hashes, receipt checks, account windows, token prices, fees and unresolved legs, use the linked technical reports. [METHODOLOGY.md](METHODOLOGY.md) documents the separation of an exchange customer's deposit address, a transaction relationship and personal control. [MASTER_REPORT.md](MASTER_REPORT.md) and [INVENTORY.md](INVENTORY.md) are generated from the 14 tracked `investigations/` folders; they are not hand-edited to fold separate `research_notes/` into formal investigations.
