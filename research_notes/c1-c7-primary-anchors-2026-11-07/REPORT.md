# Primary transaction anchors: Burdensome-Mix (C1) and 6741 (C7)

**Date:** 7 November 2026. This is an add-only research follow-up to the [external-case intake](../external-polymarket-cases-2026-11-07/REPORT.md) and open [C5/C7 PR #45](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/45). It documents two account-to-proxy mappings and two testable Polygon transaction anchors. **It does not establish any new financial connection between traders.**

> **Later evidence — 13 November 2026:** [Follow-up case C7](../../investigations/followup-20261113/FINDINGS.md) adds a verified common Polygon USDC funder for eight Nobel-related Polymarket accounts, the `aenews0` proxy mapping and 16 Relay withdrawal destinations. The statement above that this 7 November note finds no new trader-to-trader financial connection applies to the original snapshot, not the later C7 investigation. Common funding alone does not identify one operator or establish insider trading.

## Evidence boundary and statuses

- **DOCUMENTARY_CORROBORATED:** an early public article links a historical handle to a full 40-hex address; a Polymarket profile and chain trace corroborate the address, not the identity of a person.
- **PLATFORM_PROFILE_CORROBORATED:** Polymarket currently displays the handle for an exact address. Handles can change.
- **EXPLORER_RENDERED_NOT_RPC_REPLAYED:** direct Polygonscan transaction view, without independently downloaded raw receipt or internal trace.
- **EXPLORER_SEARCH_INDEX_NOT_RPC_REPLAYED:** transaction and transfer described by the search-indexed Polygonscan event view; raw JSON receipt and block still need verification.
- **NOT_ESTABLISHED:** no direct funding, control, non-public information, personal identity or criminal conduct established.

The source recovery digest describes 327 distinct X posts and separate original media / hash manifests. Their full original bytes are not attached here; we have not replayed those originals or certified their hashes.

## C1 — Burdensome-Mix: exact proxy and deployment anchor

Historical account **Burdensome-Mix** maps to Polygon proxy **0x31a56e9e690c621ed21de08cb559e9524cdb8ed9** via [Bored Ape Gazette's historical coverage](https://www.theboredapegazette.com/post/beginner-s-luck-or-a-burdensome-mix-of-insider-information-a-polymarket-bettor-turned-30k-into), which directly links that handle to the address. The [Polymarket address profile](https://polymarket.com/profile/0x31a56e9e690c621ed21de08cb559e9524cdb8ed9) describes a renamed account joined in December 2025 with four predictions.

**Polygon chain ID 137:** [transaction 0x6f1cca…](https://polygonscan.com/tx/0x6f1cca0092975d28d9dc37a4551b069c8d660f4d76d2cd2465cbd5d78d588eda), block **80805767**, **2025-12-26 06:32:57 UTC**, success. Polygonscan identifies a Polymarket Proxy Wallet Factory CREATE2 deployment producing the proxy. The outer transaction sender **0x64131b60502c01362639cc5cfe1a1efb6be1165a** interacts with the relay hub: **a relayer is not proof of beneficial ownership**. The explorer renders standard token-approval logs, not a verified first funding transfer.

**Open:** independently retrieve raw receipt and internal trace / factory creation event, then test the exact first funding and eventual cash-outs against the existing eight-account Maduro/Iran group and the separate 71-account Railgun tree in [PR #44](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/44). The shared 26 December creation window is timing only, not proof of common operation. Any official allegations in the older C1 case report remain allegations.

## C7 — Nobel 2025: 6741 exact proxy and a market-transfer anchor

The [Polymarket account page](https://polymarket.com/profile/0xa430506774f9efaf39903ee7e0db1351f66891ca) displays **6741** at full Polygon proxy **0xa430506774f9efaf39903ee7e0db1351f66891ca**. An [independent public wallet discussion](https://www.reddit.com/r/PredictionSignal/comments/1x40aeb/i_built_a_model_that_scores_polymarket_wallets/) prints the same full address. The current biggest-win display, account lifetime PnL and Nobel-only PnL are **different metrics** and are not reconciled here.

**Polygon chain ID 137:** [transaction 0x721c97…](https://polygonscan.com/tx/0x721c97a2a999fd600beec7ba1350d722b8c6bdbaa2abd08ec0eec6746e968649), block **77475875**, **2025-10-10 00:31:55 UTC**, success according to Polygonscan's indexed event view. Its event **107** is shown as a USDC.e ERC-20 Transfer of **2,500,000 atomic units = 2.5 USDC.e** from 6741's proxy to the **Polymarket Neg Risk CTF Exchange** (token 0x2791bca1f2de4661ed88a30c99a7a9449aa84174; exchange 0xc5d563a36ae78145c45a50134d48a1215220f80a). The indexed transaction also shows matched orders. **Order-book counterparties are not account funders**. The event's specific Nobel candidate/conditional token has not been independently identified, so the transaction must not be described as a confirmed Machado YES trade.

The timestamp precedes the reported Nobel announcement at approximately **09:00 UTC on 10 October 2025**. Timing alone does not establish access to confidential information. The six-handle roster described in [PR #45](https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/45) now has a fifth documentary full proxy if this mapping is adopted; **aenews0** and the alleged **~$250k common distributor** remain unresolved. No transfer to a common financier has been verified.

## Reproduction

Exact source URLs and evidence tiers are in [accounts.csv](data/accounts.csv) and [onchain_anchors.csv](data/onchain_anchors.csv). Run the local [verify.py](verify.py) to check address/transaction syntax, source consistency, atomic amounts and fail-closed statuses. The optional receipt replay requires the real JSON responses of Polygon eth_getTransactionReceipt and eth_getBlockByNumber for C7: these are **not included and were not fetched in this pass**. Its synthetic self-test uses one passing example and six deliberate failures.

Next steps: (1) trace C1 first funding and exits with complete receipts; (2) replay the C7 indexed ERC-20 log and match the condition/token ID; (3) reconstruct C7 six-account funding and negative controls, using existing collectors; (4) continue C5 and the 25 Iran / 17 KPMG unfinished legs only in their existing owned PRs. No README, archives, shared tools or publication baseline have been modified.
