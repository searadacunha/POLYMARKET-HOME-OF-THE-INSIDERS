# Polymarket, Home of the Insiders

## Tracing the funding, trading and exits behind high-stakes prediction-market bets

A series of bets on military operations, a president's removal and a football award prompted the same question: **are apparently independent Polymarket accounts financially connected, and where do their funds go?**

I investigate that question by reconstructing trades, following transaction-level funding routes and withdrawals across chains, and testing apparent wallet links against ordinary market activity.

**Selected findings:**

- **At least 19 Polymarket accounts** in an Iran-market network, reached by following bettors' money and linked by direct payments or by shared withdrawal destinations classified as customer deposit addresses.
- **Two exact wallet overlaps with [Inca Digital's independent Iran-market research](https://drive.google.com/file/d/1tesSlK0kHOU9vm6VtMf1QRS8VO2ah-Yz/view):** the accounts Inca called `9TungSahur` and `DonkeyDonkey999` appear in that 19-account network.
- **Two more Polymarket accounts on the wallets of `ricosuave666`, one of the accounts Inca flagged:** `AugsburgFClover` and `metushelah` are funded from and withdraw to the same two personal wallets (Polygon and Solana). Four amounts published from the Israeli indictment match these records to the dollar. No account is named in the press, so this is compatibility, not attribution.
- **65,992.25 USDC** sent by three network accounts to the same deposit address classified as a Bybit customer deposit, between 01:42 and 02:27 UTC on 13 June 2025, starting about 1 h 42 min after the June 2025 market first traded Yes at 0.90 or more (00:00:21 UTC).
- **70,065.262869 USDC.e** traced through 11 Relay orders from four accounts into **856.840698827 SOL**, followed by **842.687802663 SOL** transferred to a destination classified as a Bybit deposit.
- Separately, an **eight-account Maduro/Iran network** with **$509,993.24** in aggregate recorded trading PnL, and an investigation of the **2026 Ballon d'Or** betting positions.

The links below lead to evidence files, transaction hashes, chronological reconstructions and offline verification scripts. Financial connections are not, on their own, proof of common ownership or access to non-public information.

---

# 1. Iran: From Individual Bets to a 19-Account Financial Network

## Two market periods, accounts connected by transactions

The research includes bets on **Israeli military action against Iran in June 2025** and **U.S. strikes on Iran by 28 February 2026**. Instead of treating winning trades as evidence of insider knowledge, I traced deposits, withdrawals and cross-chain transfers to identify relationships that can be checked directly on public ledgers.

The February 2026 investigation expanded from a smaller group to **19 financially linked Polymarket accounts**. Documented examples include:

| Source account | Recipient account | Financial evidence |
|---|---|---|
| `TBFMM` | `BlueElephant666` | Three payments totalling **1,523 USDC.e**, appearing as withdrawals and the recipient's first deposits |
| `TBFMM` and `ILOVEYOUBABYZZ` | `DonkeyDonkey999` | Direct transfers with matching hashes in both accounts' activity |
| `TBFMM` | `oveiStheair` | **4,950.47 USDC.e** sent via the receiver's BSC deposit route |
| `ILOVEYOUBABYZZ` | `ALLOWMETOSHOWU1` | **5,000 USDC.e** routed into the recipient's first deposit, shortly after account creation |

Other routes converge on addresses classified by their behavior and third-party labels as customer deposits at Binance, Bybit and Crypto.com. A common exchange deposit address indicates that funds reached the same credited destination, **not who controls the sending wallets**.

[Full 19-account network report](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/blob/dd9df29cc577cc408a2031ebfa1e0b659af5c90f/research_notes/iran-cluster-e-network-2026-11-05/REPORT.md) · [Transaction evidence and verifier](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/tree/dd9df29cc577cc408a2031ebfa1e0b659af5c90f/research_notes/iran-cluster-e-network-2026-11-05)

## The independent overlap with Inca Digital

Inca Digital examined the June 2025 **"Israel military action against Iran by Friday?"** market and highlighted five accounts using trading-behavior heuristics. Comparing the wallet addresses listed in Inca's report with this investigation produced **two exact matches**:

| Inca Digital's name | Name in the financial network | Exact wallet address |
|---|---|---|
| `9TungSahur` | `TheOneWhoKnocks1312` | `0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a` |
| `DonkeyDonkey999` | `DonkeyDonkey999` | `0xcb18ea2923d957bd9cf049cce60a87638722f867` |

A separate reconstruction of the five accounts' June 2025 trading cash flows matched the realized profits reported by Inca within **1.50 USDC** for each account.

The on-chain trace goes further: on **11 June 2025**, three withdrawals from `DonkeyDonkey999` (1,162.81 USDC) went to an address that behaves as `9TungSahur`'s deposit address; about 19 minutes after each, `9TungSahur` received 98.8 % of that leg. These were its first three deposits, the day before its bets (classification by behaviour). On **13 June 2025**, these two accounts and `ILOVEYOUBABYZZ` transferred **65,992.25 USDC** to the same address classified as a Bybit customer deposit between **01:42 and 02:27 UTC**.

Inca's other three accounts showed no money link to these two or to the network in that first pass, and some comparable control buyers also showed such links (4 and 5 of 54). These are traceable **financial relationships between accounts selected for investigation using different methods**. Inca's behavioral classification is not treated as proof of insider trading; neither are these financial links.

[Inca cross-check, exact hashes and controls](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/blob/c69ce98cea602ba01c434e4c68c2f5b8647a8463/research_notes/inca-crosscheck-2026-11-06/REPORT.md) · [Original Inca report](https://drive.google.com/file/d/1tesSlK0kHOU9vm6VtMf1QRS8VO2ah-Yz/view)

## Following Inca's three other accounts across chains

Inca's other three accounts (`ricosuave666`, `truthlord`, `PorcoRosso`) left Polymarket through deBridge, Mayan, LI.FI and Relay. Reading each bridge order on the source chain and its fill on the destination chain gives:

| Account | Where its bridged exits go | Evidence |
|---|---|---|
| `ricosuave666` | All four Solana-bound orders (June and September 2025, 110,430.82 USDC sent) pay one Solana wallet, `J4t48znS…`, which sends 60,077.60 USDC back to the account's exit wallet on Ethereum by Circle CCTP | order ids and Mayan order state in each fill |
| `AugsburgFClover` (not flagged by Inca) | Withdraws to `ricosuave666`'s exit wallet (same transaction hashes, June 2025; Relay, September 2025 and April 2026) and is funded from it and from `J4t48znS…`. On **6 January 2026**, 25,000 USDC withdrawn by `ricosuave666` reached it in 32 minutes, and it bought the same two Iran markets `ricosuave666` had just bought | transaction hashes, Relay orders |
| `metushelah` (not flagged by Inca) | Funded from `J4t48znS…` and fully withdrawn to it, 15 and 16 September 2025; its only bets are two Israel–Yemen markets, +404.32 USDC | Solana transfers, Relay orders |
| `truthlord` | Three deBridge orders to `HfGp55mp…`, which pays back truthlord's own funding wallet and a fresh wallet | order ids in each fill |
| `PorcoRosso` | Its own address on Ethereum (43.38 ETH) and a service-like Solana address | order id at both ends |

The wallet that received **74,680.134173 USDC** from `ricosuave666`'s exit wallet on 26 June 2025 funds a third account and credits the same Binance deposit address as that exit wallet. Press summaries of the March 2026 Israeli indictment quote 162,663, 6,195, 17,704 and 74,680 dollars, and a 400-dollar profit on Yemen markets "by 19 September" and "on 16 September"; the first four match `ricosuave666`'s record to the dollar, the fifth matches `metushelah`. The press names no account; nothing here identifies a person or proves common ownership.

[Report, 39 indexed money legs and verifier](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/blob/c5052d54f2444067aa1f5afb7a6ae76ca5cded40/research_notes/inca-bridged-exits-2026-11-06/REPORT.md) · [Evidence and scripts](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/tree/c5052d54f2444067aa1f5afb7a6ae76ca5cded40/research_notes/inca-bridged-exits-2026-11-06)

## Tracing the exits through Relay, Solana and Privacy Cash

In the February 2026 group, **11 Relay orders from four Polymarket accounts** have matching Polygon deposit events and Solana fill records:

| Trace | Reconstructed amount |
|---|---:|
| USDC.e sent into 11 Relay orders | **70,065.262869** |
| SOL delivered to the shared Solana beneficiary | **856.840698827 SOL** |
| SOL subsequently forwarded to an address identified as a Bybit deposit | **842.687802663 SOL** |
| Deposited by the beneficiary into Privacy Cash in two transactions, before the Bybit transfers | **12.447822100 SOL** |

These 11 bridge matches can be reproduced from **on-chain identifiers without relying on Relay's requests API**. A Privacy Cash withdrawal to the Bybit deposit address was also observed shortly after a deposit from the beneficiary. The zero-knowledge proof does not identify which deposited funds were withdrawn, so **that deposit and withdrawal are not asserted to be the same funds**.

[Cross-chain tracing, transaction hashes and verifier](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/blob/dd9df29cc577cc408a2031ebfa1e0b659af5c90f/research_notes/iran-solana-beneficiary-2026-11-05/REPORT.md) · [Chain-only Relay and Privacy Cash decoding methods](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/blob/483b0780ae073905493246d18b244ca3695703aa/research_notes/github-tooling-audit-2026-11-06/REPORT.md)

## Another cross-market financial link: Pulser

A separately documented set of **25 same-transaction-hash payments** connects `Pulser` (`0x6a8328b1…4c59`) with another June 2025 early-YES buyer (`0x8f42ae0a…b88f`), for a total of **13,449.999999 USDC** in payments in both directions. The second wallet also paid **250 USDC** directly to a third early buyer.

Both wallets were among the 54 ordinary comparison buyers (controls) of the Inca cross-check, where they show that direct transfers also occur among ordinary buyers. Their payments run from December 2024 to February 2026, spanning both Iran markets. The same `Pulser` address belongs to a **separate February 2026 Iran-market pair** (group F) of the earlier investigation; these transactions are **not a link to the 19-account network above** and not evidence of informed trading. A later check re-read all 27 transfers from Etherscan receipts (27 of 27 match) and found that `Pulser` paid the first deposit of the other wallet of group F; it did the same for 7 of the 16 Polymarket accounts it pays directly, so the link is real but not exclusive ([PR 32](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/32)).

[Cross-market account graph, 27 transaction hashes and verifier](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/blob/644eb867075d3b3c861426d672c4851c06724d6d/research_notes/iran-pulser-cashy-crossmarket-2026-11-06/REPORT.md)

---

# 2. Maduro & Iran: Follow the Money

## Eight accounts connected across three blockchains

The same Maduro/Iran investigation first identified the eight-account network below. The 19-account network of section 1 grew out of a different group of that investigation (cluster E), for which no financial link to these eight accounts was found.

Some entered positions before sharp changes in market prices.

I traced their deposits and withdrawals across **Polygon, Ethereum and TRON**.

The result was a separate network of **eight financially connected Polymarket accounts**.

Documented relationships include:

- `chileno777` → `TacticalInsiderNews`
- `Mrs.Joker` → `Planktonbets`
- `X34` → intermediate Ethereum address → `Mrs.Joker`

These are funding relationships reconstructed from blockchain transactions.

Other addresses received withdrawals from multiple accounts and later funded accounts within the same network.

What initially appeared to be separate trading accounts had identifiable financial connections.

[Explore the transaction-level network](investigations/maduro-iran/sources/phase2/RAPPORT_PHASE2_2026-09-29.md)

## The numbers

I reconstructed the published trading histories of all eight accounts, including their activity outside the two headline events.

| Metric | Result |
|---|---:|
| Connected Polymarket accounts | **8** |
| Aggregate trading PnL, including remaining position value | **+$509,993.24** |
| External capital entering the network | $151,084.40 |
| External outflows | $660,708.94 |
| Net external cash flow | **+$509,624.54** |

These figures are based on the September 29, 2026 accounting snapshot, with a full-precision arithmetic audit performed on November 4.

The trading PnL covers the accounts' recorded trading histories, not exclusively their Maduro and Iran positions.

The results establish a financially connected network of high-value Polymarket accounts, with reconstructable funding and withdrawal paths.

[Accounting audit](investigations/maduro-iran/results/accounting_audit_2026-11-04.json) · [Full investigation](investigations/maduro-iran/FINDINGS.md)

---

# 3. Ballon d'Or: The Ranking Before the Announcement

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

# 4. Beyond Polymarket: Ethereum to Monad

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

# 5. How I Investigate

My approach is based on reconstructing financial activity directly from blockchain data.

**Follow the funding. Reconstruct the trades. Trace the exits. Connect the evidence.**

The research combines:

- **On-chain forensics:** Polygon, Ethereum, BNB Smart Chain, Solana, Arbitrum, TRON and Monad transaction tracing, including bridge orders (Relay, deBridge, Mayan, LI.FI, Circle CCTP).
- **Wallet analysis:** funding paths, financial relationships, intermediaries and cross-chain transfers.
- **Prediction-market analysis:** trade reconstruction, position sizes, timing, entry prices and realized outcomes.
- **Financial accounting:** deposits, withdrawals, remaining positions and trading PnL.
- **Network analysis:** relationships between accounts, addresses and funding sources.
- **Statistical analysis:** comparisons against wider market activity.
- **Python tooling:** blockchain data collection, transaction reconciliation, evidence validation and reproducible analysis.

Each documented finding is linked to its underlying evidence.

Financial connections, account ownership and access to non-public information are separate questions. The investigation establishes the first where transactions support it; it does not assume the other two.

---

# 6. Reproduce the Evidence

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

These scripts validate the corresponding published evidence and repository artefacts. Some investigations require additional raw data or blockchain RPC access for complete analytical reproduction.

---

# 7. Explore the Research

| Research | Files |
|---|---|
| **Iran, 19-account network and Inca cross-check** | [Network evidence](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/27) · [Inca cross-check](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/29) · [Cross-market transfers](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/30) · [Chain-only bridge matching](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/28) · [Bridged exits of the other Inca accounts](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/32) |
| **Maduro / Iran** | [Investigation](investigations/maduro-iran/README.md) · [Findings](investigations/maduro-iran/FINDINGS.md) |
| **Ballon d'Or** | [Wallets](investigations/ballon-dor-wallets/README.md) · [Independent audit](investigations/ballon-dor-audit/README.md) |
| **Funding and withdrawals** | [Tracing](investigations/ballon-dor-flow-trace/README.md) · [Market census](investigations/ballon-dor-census/README.md) |
| **ChangeNOW** | [Account links](investigations/changenow-proof/README.md) · [Outflows](investigations/changenow-outflows/README.md) · [Polymarket](investigations/changenow-polymarket/README.md) |
| **PolySentinel** | [Monitoring and research](investigations/polysentinel/README.md) |
| **Additional investigations** | [Security incidents](investigations/hacks-parallel/README.md) · [Trading research](investigations/edge-polymarket/README.md) · [Historical corpus](investigations/corpus-historique/README.md) |

The [Master Report](MASTER_REPORT.md) consolidates the published findings and supporting evidence.

[METHODOLOGY.md](METHODOLOGY.md) describes the research methodology.
