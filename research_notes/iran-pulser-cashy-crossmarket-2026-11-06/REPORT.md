# A cross-market financial link: Pulser, cashy and Car

**Research note — 6 November 2026**  
**Scope:** Polymarket on Polygon; June 2025 Israel–Iran early-YES control cohort, cross-checked against the February 2026 Iran investigation.  
**Finding:** a pre-existing February 2026 Iran cohort member has a long, repeated, **direct on-chain payment relationship** with another June 2025 early-YES buyer. A third prolific bettor received a direct transfer. This is a financial network, **not evidence of insider trading**.

## Executive finding

The independent control population in [PR #29](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/29) included 54 wallets, defined by buying at least 1,000 USDC of YES at prices no higher than 0.50 before the June 2025 Israel–Iran market first traded at 0.90. Its archived transfers reveal the following cross-account history.

| From | To | Direct transaction hashes | USDC-denominated value | Period |
|---|---|---:|---:|---|
| **cashy** `0x8f42ae0a…b88f` | **Pulser** `0x6a8328b1…4c59` | **11** | **10,758.00** (10,757.999999 exact) | 13 Dec 2024–7 Dec 2025 |
| **Pulser** | **cashy** | **14** | **2,692.00** | 14 Jun 2025–23 Feb 2026 |
| **cashy** | **Car** `0x7c3db723…5c6b` | **1** | **250.00** | 10 Dec 2025 |
| **Separate control pair** `0x5e9c76f3…` | `0x8f7a4b41…` | **1** | **1,000.00** | 23 Jun 2025 |

**Totals:** 25 transfer hashes / 13,449.999999 USDC between cashy and Pulser, **26 / 13,699.999999 USDC** in the three-wallet chain, and **27 / 14,699.999999 USDC** across all exact same-hash control-to-control transfers recovered from the 59-wallet dataset (54 controls plus five Inca accounts). Each hash is listed in [DIRECT_TRANSFERS.csv](DIRECT_TRANSFERS.csv). The directional sum is transfer volume, **not profit, capital invested or net new money**: funds can circulate.

The 27 transactions were **not inferred from matching amounts or timings**. Every row is a transaction that appears *with the same hash*, as a Polymarket **WITHDRAWAL** from one proxy and a **DEPOSIT** into a different proxy. Their recorded amounts agree to micro-USDC precision and their observed timestamps coincide. The source includes the receipts-derived counterparties for each leg. The transaction links are on Polygon.

## Why this matters: the same Pulser wallet appears in both Iran studies

**Wallet identity is exact.** Pulser is `0x6a8328b1ae11569f7b27600073558879885e4c59` in the pre-existing September 2026 [phase-3 investigation](../../investigations/maduro-iran/sources/phase3/RAPPORT_PHASE3_2026-09-29.md) and its [archived Relay table](../../investigations/maduro-iran/sources/phase3/ext_relay.json). It is also the Pulser account in the [February 2026 Iran early-buyer population](../../investigations/maduro-iran/sources/phase2/TABLE5_population_iranA.csv), with a recorded 2,000 USDC YES buy on **26 February 2026 at 21:45:20 UTC**, at 0.10. The separate [PR #27 network note](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/blob/dd9df29cc577cc408a2031ebfa1e0b659af5c90f/research_notes/iran-cluster-e-network-2026-11-05/REPORT.md) places Pulser and `0x0bb95597b85b89f83f66929be66edcf4ae7f9725` in its separately classified **pair F**, based on a shared withdrawal recipient. The phase-3 report describes an additional Pulser-to-deposit relationship with that wallet; that leg is *previously reported, not independently re-executed here*.

The independent June 2025 control archive also contains Pulser: **1,334.914600 USDC** of pre-jump YES purchases. In that same June cohort, cashy (`0x8f42ae0a01c0383c7ca8bd060b86a645ee74b88f`) bought **1,541.721000 USDC**, while Car (`0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b`) bought **4,515.502900 USDC**. These are **market-specific purchase amounts**, not lifetime exposure.

Thus the new graph joins **a pre-existing February 2026 pair-F wallet (Pulser)** to **two June 2025 comparator wallets (cashy and Car)** through direct payments. There is *no demonstrated transfer from this chain to Iran cluster E's 19 accounts*. Pair F and cluster E should remain separate. The shared use of a high-degree Relay service cannot join them.

## Independent wallet-name cross-checks

Names are **public labels for addresses**, not identities or assertions about who owns the wallets:

- **Pulser** `0x6a8328b1…4c59`: original [phase-3 Relay file](../../investigations/maduro-iran/sources/phase3/ext_relay.json); [third-party Polydata profile](https://polydata.pro/traders/Pulser).
- **cashy** `0x8f42ae0a…b88f`: [PolymarketScan profile, exact address](https://polymarketscan.org/address/0x8f42ae0a01c0383c7ca8bd060b86a645ee74b88f) and [Oxygen Delta profile](https://oxygendelta.com/traders/cashy/).
- **Car** `0x7c3db723…5c6b`: [Struct trader profile, exact address](https://explorer.struct.to/traders/0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b) and [Oxygen Delta](https://oxygendelta.com/traders/car/).

Both cashy and Car have extensive public trading histories outside the two studied events. This makes the trio a useful **negative-control stress test**, not automatically a cohort of insiders. Third-party statistics can vary by snapshot and must not replace on-chain accounting.

## Secondary edges, lower confidence

PR #29's fixed M2 extraction also lists **two common withdrawal recipients** for cashy and Pulser: EVM-format `0xd46b0f3f3acda6b943b18d05c208e7fb844c9288` and `TQtL4Z1j6AXTcTVMuSbzNeZVSegyV1HAfK` (a TRON-format identifier). The classification and destination chains of these endpoints were not revalidated in this note. They are **not counted** among the 26 direct transfers.

Car and a fourth control `0xdd225a03cd7ed89e3931906c67c75ab31cf89ef1` share `0x4c707bf3c3a79e465e90e37788a2247372ad1bcf` in the PR #29 M2 output, but **no direct transfer** between them is established. This is a weak shared-recipient observation, not a fourth member of the direct-payment chain.

The 1,000-USDC same-hash payment between two other controls is reported separately; neither is joined to Pulser, cashy or Car by this transaction.

## Provenance and reproducibility

All 27 direct hashes were **recomputed**, not manually selected, from the archived **7,596 DEPOSIT/WITHDRAWAL rows** in PR #29 at immutable commit `c69ce98cea602ba01c434e4c68c2f5b8647a8463`:

- [Source activity and counterparties — data/flows.csv](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/blob/c69ce98cea602ba01c434e4c68c2f5b8647a8463/research_notes/inca-crosscheck-2026-11-06/data/flows.csv).
- [Fixed cohort population — data/population.json](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/blob/c69ce98cea602ba01c434e4c68c2f5b8647a8463/research_notes/inca-crosscheck-2026-11-06/data/population.json).
- [Original measures, M2/M3 — data/results.json](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/blob/c69ce98cea602ba01c434e4c68c2f5b8647a8463/research_notes/inca-crosscheck-2026-11-06/data/results.json).
- [Primary receipt collection and its SHA-256 index](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/tree/c69ce98cea602ba01c434e4c68c2f5b8647a8463/research_notes/inca-crosscheck-2026-11-06).
- [CSV of individual transaction hashes](DIRECT_TRANSFERS.csv). Each hash can be checked on a Polygon explorer.

Reproduction rule: group each archived row by its transaction hash. Accept an edge only if **two different wallets** each have the **same hash**, one `WITHDRAWAL` and the other `DEPOSIT`, **reciprocal counterparties**, timestamps equal within one second, and USDC-denominated amounts matching within 0.000002. Count each transaction **once**. The [standalone verifier](verify.py) checks the exported index offline; `--source-github` optionally downloads the exact pinned source to rederive all edges and verify wallet inclusion in the control population.

This is a **retrospective descriptive follow-up** triggered by inspecting the PR #29 control group. No prespecified p-value, enrichment or insider-trading probability is claimed.

## What is established — and what remains open

**Established from the archived matched records:** 25 direct payment transactions between Pulser and cashy; one payment from cashy to Car; repeated exposure of Pulser to the June 2025 and February 2026 Iran market populations. The first pair-F relationship is an earlier, separately documented finding.

**Not established:** one owner of these wallets; access to confidential information; a financial connection between this trio and cluster E's 19 accounts; or the ownership of any external recipient, exchange or service.

**Useful next tests:** (1) primary receipt replay of all 27 hashes on an independent RPC, (2) cashy/Pulser/Car trade-overlap and lead–lag analysis versus matched high-volume traders, (3) check the pair-F receiving deposit address and its onward withdrawals across BSC/Relay, (4) stratify comparator baselines by account tenure and lifetime activity so established high-volume traders do not dominate comparisons with fresh single-purpose accounts.

No existing investigation or README was modified.