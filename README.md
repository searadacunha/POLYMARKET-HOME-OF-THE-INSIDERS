# Polymarket, Home of the Insiders

<p align="center"><img src="assets/readme-hero-photo.jpg" width="100%" alt="POLYMARKET-HOME-OF-THE-INSIDERS project illustration" /></p>

On Polymarket, people bet on real-world events.

A president losing power. A military strike. A football award.

Behind those bets are blockchain wallets. They receive funds, enter positions, collect payouts and move money across networks.

Some accounts attracted attention because of the size and timing of their bets.

I wanted to know **who was funding them, whether apparently unrelated traders were connected, and where the money went after the bets settled.**

This investigation covers three events:

- **Nicolás Maduro:** bets on whether he would leave power by January 31, 2026.
- **Iran:** bets on U.S. military strikes by February 28, 2026.
- **Ballon d'Or 2026:** bets on the winner, the final ranking and individual player matchups.

I reconstructed their trading histories, funding networks and withdrawals.

Here's what I found.

---

# 1. Maduro & Iran: Follow the Money

## Iran-market transaction paths and trading patterns

The archived investigation maps **38 distinct Polymarket trading proxies** in the February 2026 Iran markets. **Thirty-six were created between February 22 and 25**, often minutes apart. They first bought NO on Iran-strike deadlines, then bought YES between **20:49 and 23:35 UTC on February 27**, before the following morning's market repricing. The significance of that pattern has not been measured against an unbiased control population.

| Recorded observation | Result |
|---|---:|
| Distinct trading proxies | **38** |
| Newly created accounts following the NO-to-YES sequence | **36** |
| Direct Polygon proxy senders to the same recipient address | **32** |
| Additional Polygon routes via Relay | **3 accounts, 12 individually matched USDC credits** |
| Arbitrum route with a matching receipt | **1 account; onward attribution not established** |
| Base routes documented by Relay | **2 accounts; later RPC check recorded in summaries, raw receipts not archived** |
| Combined recorded trading result, with eight accounts still holding shares | **+$1,576,522.86 USDC** |

The common EVM recipient is:

`0xc5bb1be0407db7312911ec765d399d02461e411a`

On Polygon, it received and swept **1,984,038.17 USDC/USDC.e** in the archived period. Gas funders and payout destinations carry Coinbase labels, and the address behaves like an exchange deposit wallet. Those labels and sweeps **do not establish that all 38 routes were credited to one verified Coinbase customer account**, let alone identify the controller. The Polygon Relay transfers are independently matched by exact amounts; the two Base routes rest on Relay records and a later RPC check recorded in summaries, without archived raw receipts for independent replay.

A separate, more specific financial connection involves `flipfloppity`: **9,990.03 USDC** passed through Relay to an intermediary wallet that then funded a trading proxy provisionally labelled `Anon`. That displayed label is inferred from historical account results, not corroborated by a served public profile.

These records show payment paths and a recurring trading pattern. They do **not** establish common beneficial ownership or access to non-public information.

[Strict proof-tier audit and offline verifier](research_notes/g38-proof-tier-audit-2026-11-08/REPORT.md) · [Later RPC observations and their replay limits](research_notes/independent-forensic-audit-2026-11-08/REPORT.md) · [Original transaction reconstruction](research_notes/x-history-2026-11-06/verification/REPORT.md) · [Per-account ledger](research_notes/x-history-2026-11-06/verification/data/g38_accounts.csv)

## Eight accounts connected across three blockchains

A separate investigation began with accounts trading on Maduro's removal from power and U.S. strikes on Iran.

Some entered positions before sharp changes in market prices.

I traced their deposits and withdrawals across **Polygon, Ethereum and TRON**.

The result was a network of **eight financially connected Polymarket accounts**.

Documented relationships include:

- `chileno777` → `TacticalInsiderNews`
- `Mrs.Joker` → `Planktonbets`
- `X34` → intermediate Ethereum address → `Mrs.Joker`

These are funding relationships reconstructed from blockchain transactions.

Other addresses received withdrawals from multiple accounts and later funded accounts within the same network.

What initially appeared to be separate trading accounts had identifiable financial connections.

[Explore the transaction-level network](investigations/maduro-iran/sources/phase2/RAPPORT_PHASE2_2026-09-29.md)

## The eight-account numbers

I reconstructed the published trading histories of all eight accounts, including their activity outside the two headline events.

| Metric | Result |
|---|---:|
| Connected Polymarket accounts | **8** |
| Aggregate trading PnL, including remaining position value | **+$509,993.24** |
| External capital entering the network | $151,084.40 |
| External outflows | $660,708.94 |
| Net external cash flow | **+$509,624.54** |

These figures are based on the September 29, 2026 accounting snapshot, with a full-precision arithmetic audit performed on November 4.

The trading PnL covers the accounts' recorded trading histories, not exclusively their Maduro and Iran positions. This eight-account network is distinct from the 38-account cohort above; the figures are not combined.

The results establish a financially connected network of high-value Polymarket accounts, with reconstructable funding and withdrawal paths.

[Accounting audit](investigations/maduro-iran/results/accounting_audit_2026-11-04.json) · [Full investigation](investigations/maduro-iran/FINDINGS.md)

## A shared withdrawal destination across Venezuela and Iran

Three accounts active in different geopolitical markets routed their Polymarket payouts through Relay to the **same Ethereum deposit address**:

| Account | Markets | Recorded payouts to this destination |
|---|---|---:|
| `Frogensky` | Venezuela | **101.64 USDC** |
| `JamWil23` | Maduro and Venezuela | **9,962.37 USDC** |
| `bravonoll` | Iran | **42,858.47 USDC** |

The destination, `0xd12623958b81d71e8be3fa936aed6d8c2528e992`, received gas from Coinbase Hot Wallet 10 and swept its USDC balances to that wallet within minutes of deposits.

This documents a shared cash-out destination across Venezuela and Iran positions, without establishing beneficial ownership of the accounts.

[Cross-market withdrawal evidence](research_notes/x-history-2026-11-06/verification/REPORT.md)

## A trader positioned across two Iran episodes

The account `flydartball` traded Iran-related markets in **June 2025** and **February 2026**. Before the February 28 repricing, its ledger shows **359,679.08 YES shares** on the strike-by-February-28 market. Across its recorded account history, the reconstructed trading result was **+$841,375.23**.

This is evidence of repeated market exposure and an auditable trading history, not evidence of how the trader obtained information.

[Position history and financial reconstruction](research_notes/x-history-2026-11-06/verification/REPORT.md)

---

# 2. Ballon d'Or: The Ranking Before the Announcement

## Five names. Five correct positions.

On October 23, 2026, three days before the Ballon d'Or ceremony, [Upside reported](https://www.upside24.com/articles/ballon-d-or-2024-264-000-mises-sur-polymarket-suggerent-une-fuite-du-top-5-avant-596165) that Polymarket accounts were backing a specific top-five ranking:

| Position | Player |
|---|---|
| 1 | Harry Kane |
| 2 | Kylian Mbappé |
| 3 | Lamine Yamal |
| 4 | Rodri |
| 5 | Lionel Messi |

On October 26, [UEFA published the official result](https://www.uefa.com/uefachampionsleague/news/02aa-21ec47378e70-b29defb43769-1000--harry-kane-wins-2026-mens-ballon-d-or/).

**The ranking matched. All five positions.**

On October 16, before the exact-place markets opened, an archived public post by `@Cypya_Poly` already listed those five names in order.

The Polymarket profile that declares the same X username had positions corresponding to **all seven ranking facts with an available market** before publishing the post.

This provides a dated public-information reference alongside the on-chain betting history. It does not establish the original source of that forecast.

Two days earlier, a public post highlighted a large position held by `Thin-Disclaimer-Life`. At that time, the account held **66,799.56 shares on Mbappé above Yamal** and **3,916.35 shares on Rodri above Messi**. Both amounts were reconciled to the historical trading record. Those positions preceded the October 16 post.

[Historical posts and trading verification](research_notes/x-history-2026-11-06/verification/REPORT.md)

I wanted to trace the money behind the accounts attracting attention.

## Eleven accounts identified

Starting from the publicly reported positions, I reconstructed the underlying Polymarket activity.

The original screenshot contained fifteen displayed positions.

**All fifteen matched the recorded trading data**, in the same order, within half a share.

The investigation identified eleven accounts associated with the public reporting.

All eleven held positions favouring Mbappé over Yamal, alongside other individual bets.

I mapped the account labels to blockchain wallets and started tracing their funding.

[Wallet inventory and reconstructed positions](investigations/ballon-dor-wallets/sources/reports/inventaire_adresses.md)

## A financial connection beyond the original accounts

The investigation uncovered transactions involving `brace227`, an account within the original group.

**October 4, 2026**

An address associated with `brace227` transferred **0.002048944 ETH** to an address associated with `kraben006`, another investigated account.

**October 9–10, 2026**

The same address transferred **5,170 USDC** in two transactions to an address associated with another Polymarket account.

That additional account was **not among the original eleven**.

Its recorded betting activity was concentrated on Harry Kane winning the Ballon d'Or.

| Additional Kane account | Recorded result |
|---|---:|
| Purchases | 16 |
| Total purchase cost | $5,164.99 |
| Withdrawals, including returned capital | **$8,061.90** |

This expanded the investigation beyond the accounts originally identified in the press.

The transfers establish a direct financial relationship between the investigated addresses, while the additional account provides another traceable set of Kane-related positions.

[Funding paths and transaction evidence](investigations/ballon-dor-flow-trace/sources/reports/COMMON_FUNDERS.md)

## Reconstructing the cash flows

Across the original eleven accounts, the November 2 reconciliation identified:

| Metric | Result |
|---|---:|
| Deposits | **$304,137.63** |
| Deposit transactions | 46 |
| Withdrawals | **$493,094.76** |
| Withdrawal transactions | 25 |
| Net external cash flow | **+$188,957.12** |
| Net cash flow across seven settled accounts | **+$129,367.79** |

The seven settled accounts are a subset of the eleven.

These figures measure observed wallet-level cash flows, not necessarily net trading profit. The totals were calculated from full-precision transaction amounts before rounding.

The additional Kane account is excluded from these eleven-account totals.

[Full transaction reconciliation](investigations/ballon-dor-wallets/sources/evidence/contre_verification_20261102/reconciliation_montants.json)

---

# 3. Beyond Polymarket: Ethereum to Monad

## The money trail continued.

The owner address associated with the additional Kane account appeared in another transaction on October 29, 2026.

It transferred **2,969.568353 mUSD** through Relay, a cross-chain routing service.

The route:

**Ethereum → Relay → Monad → Vault**

I reconstructed the transaction using archived Relay responses and receipts from both blockchains.

The evidence connects the originating transaction to the destination transaction.

Both succeeded, **29 seconds apart**.

On Monad, the destination transaction credited **2,904.308540 vmUSD vault shares** to:

`0xea1a3f324c5ee313bb04d9e642c39c8b29e7454b`

mUSD and vmUSD are different units, so the numerical difference is not a transaction-loss calculation.

The archived request and destination logs establish the route and the recipient of the vault shares.

The entire route can be independently checked using the published transaction hashes and offline verifier.

This establishes a later cross-chain payment by an address linked to the additional Kane account. Attribution of that payment specifically to its Polymarket winnings requires reconciliation of intermediary funds and conversions.

[Complete cross-chain investigation and verifier](research_notes/relay-followup-2026-11-04/REPORT.md)

---

# 4. How I Investigate

My approach is based on reconstructing financial activity directly from blockchain data.

**Follow the funding. Reconstruct the trades. Trace the exits. Connect the evidence.**

The research combines:

- **On-chain forensics:** Polygon, Ethereum, TRON and Monad transaction tracing.
- **Wallet analysis:** funding paths, financial relationships, intermediaries and cross-chain transfers.
- **Prediction-market analysis:** trade reconstruction, position sizes, timing, entry prices and realized outcomes.
- **Financial accounting:** deposits, withdrawals, remaining positions and trading PnL.
- **Network analysis:** relationships between accounts, addresses and funding sources.
- **Statistical analysis:** comparisons against wider market activity.
- **Python tooling:** blockchain data collection, transaction reconciliation, evidence validation and reproducible analysis.

Each documented finding is linked to its underlying evidence.

Financial connections, account ownership and access to non-public information are separate questions. The investigation establishes the first where transactions support it; it does not assume the other two.

---

# 5. Reproduce the Evidence

Verify the reconstructed Ethereum-to-Monad route using the archived data:

```bash
python3 research_notes/relay-followup-2026-11-04/verify.py
```

Run the repository's publication and evidence checks:

```bash
python3 scripts/test_publication.py
python3 scripts/test_phi.py
python3 scripts/test_integrity_regressions.py
python3 scripts/test_parallel_publication.py
python3 scripts/validate_evidence.py
python3 scripts/build_master_report.py --check
```

Verify the archived historical trading evidence and the X-source intake without live RPC calls:

```bash
python3 research_notes/x-history-2026-11-06/verification/verify.py
python3 research_notes/x-corpus-reconciliation-2026-11-06/tools/check_intake.py
```

The chain verifier checks the packaged evidence and reports raw-archive-dependent tests as skipped if their local caches are absent.

These scripts validate the corresponding published evidence and repository artefacts. Some investigations require additional raw data or blockchain RPC access for complete analytical reproduction.

---

# 6. Explore the Research

| Research | Files |
|---|---|
| **Maduro / Iran** | [Investigation](investigations/maduro-iran/README.md) · [Findings](investigations/maduro-iran/FINDINGS.md) |
| **Ballon d'Or** | [Wallets](investigations/ballon-dor-wallets/README.md) · [Independent audit](investigations/ballon-dor-audit/README.md) |
| **Funding and withdrawals** | [Tracing](investigations/ballon-dor-flow-trace/README.md) · [Market census](investigations/ballon-dor-census/README.md) |
| **ChangeNOW** | [Account links](investigations/changenow-proof/README.md) · [Outflows](investigations/changenow-outflows/README.md) · [Polymarket](investigations/changenow-polymarket/README.md) |
| **PolySentinel** | [Monitoring and research](investigations/polysentinel/README.md) |
| **Verified financial findings** | [Evidence-led overview](VERIFIED_FINANCIAL_FINDINGS.md) · [Cross-market verification](research_notes/x-history-2026-11-06/verification/REPORT.md) |
| **Scientific and integrity audits** | [8 November repository audit](AUDIT_2026-11-08.md) · [G38 proof-tier replay](research_notes/g38-proof-tier-audit-2026-11-08/REPORT.md) |
| **Historical X evidence** | [Corpus reconciliation](research_notes/x-corpus-reconciliation-2026-11-06/REPORT.md) · [Account and trade verification](research_notes/x-history-2026-11-06/verification/REPORT.md) |
| **Additional investigations** | [Security incidents](investigations/hacks-parallel/README.md) · [Trading research](investigations/edge-polymarket/README.md) · [Historical corpus](investigations/corpus-historique/README.md) |

The [Master Report](MASTER_REPORT.md) consolidates the published findings and supporting evidence.

[METHODOLOGY.md](METHODOLOGY.md) describes the research methodology.
