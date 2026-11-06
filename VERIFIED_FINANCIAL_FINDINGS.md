# Verified Financial Findings

A direct index to the strongest reconstructed cash flows and trading histories in **Polymarket, Home of the Insiders**. All figures are scoped to their underlying ledgers; they are not a claim of inside information or beneficial ownership.

The core results are documented in [Maduro/Iran transaction accounting](investigations/maduro-iran/sources/phase2/RAPPORT_PHASE2_2026-09-29.md), the [November 6 historical-wallet verification](research_notes/x-history-2026-11-06/verification/REPORT.md) and the [Ballon d'Or cash-flow reconstruction](investigations/ballon-dor-wallets/sources/reports/rapport_final.md). **The eight-account Maduro/Iran network and the separate 38-account Iran cohort have different defined populations; do not sum their results into a unique population-wide PnL without a reconciliation of scope and overlap.**

## 1. An eight-account Maduro/Iran funding network

- **Eight financially connected Polymarket accounts**, with verified value-transfer paths on Polygon, Ethereum and TRON.
- **+$509,993.24** aggregate recorded trading PnL, including remaining position value across the accounts' published trading histories, **not only the two headline markets**.
- **$151,084.40** external inflows and **$660,708.94** external outflows; **+$509,624.54** net external flow over the reported accounting window.
- Individual examples of funding relationships: `chileno777` to `TacticalInsiderNews`, `Mrs.Joker` to `Planktonbets`, and `X34` through an intermediate Ethereum address to `Mrs.Joker`.

**Evidence:** [phase-2 transaction graph and accounting](investigations/maduro-iran/sources/phase2/RAPPORT_PHASE2_2026-09-29.md) and [full precision audit](investigations/maduro-iran/results/accounting_audit_2026-11-04.json).

## 2. A second Iran cohort: 38 accounts and common cash-out infrastructure

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

**Status:** cash-out convergence and the particular inter-account funding path are supported by receipts/Relay records. The destination is consistent with a customer deposit for one exchange account; the natural person, organisation or group behind it remains unknown. Incomplete Base/Arbitrum and inbound funding histories preclude broader owner attribution.

**Evidence:** [38-account reconstruction](research_notes/x-history-2026-11-06/verification/REPORT.md), [per-account data](research_notes/x-history-2026-11-06/verification/data/g38_accounts.csv), [verification script](research_notes/x-history-2026-11-06/verification/verify.py).

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

**Evidence:** [October 2026 chronology and account verification](research_notes/x-history-2026-11-06/verification/REPORT.md), [Ballon d'Or findings](investigations/ballon-dor-wallets/FINDINGS.md) and [transactional report](investigations/ballon-dor-wallets/sources/reports/rapport_final.md).

## Scope and reproducibility

The on-chain cases above have different evidence classes: confirmed transfers, reconstructed market positions, supported deposit-route convergence and historical source attribution. None proves insider trading or a common beneficial owner merely from the appearance of synchronised bets.

For raw source indexes, exact token/contract types, transaction hashes, receipt checks, account windows, token prices, fees and unresolved legs, use the linked technical reports. [METHODOLOGY.md](METHODOLOGY.md) documents the separation of an exchange customer's deposit address, a transaction relationship and personal control. [MASTER_REPORT.md](MASTER_REPORT.md) and [INVENTORY.md](INVENTORY.md) are generated from the 14 tracked `investigations/` folders; they are not hand-edited to fold separate `research_notes/` into formal investigations.
