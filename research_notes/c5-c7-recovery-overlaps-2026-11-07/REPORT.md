# C5/C7 historical recovery: exact proxy roster, independent detector overlaps, and financial test gates

**Date:** 2026-11-07. **Scope:** historical source recovery and reproducible cross-reference, not a new RPC trace. **Status:** documentary mapping / candidate leads. **Publication:** this independent note only; do not alter the root README, earlier investigations, evidence snapshots, or the publication baseline. Nothing here establishes shared beneficial ownership, access to non-public information, or criminal conduct.

> **Update — 8 November 2026:** The subsequent [C1/C7 primary-anchors note](../c1-c7-primary-anchors-2026-11-07/REPORT.md) records a full proxy mapping for the `6741` profile at documentary level. The other outstanding Nobel account mapping and the alleged common funder remain unverified. The chronological status descriptions below reflect the original 7 November research snapshot.

## Provenance and evidence boundary

This note reconciles (a) the user-supplied `POLYMARKET-RECUPERATION-COMPLETE-2026-11-07.txt` **consolidated digest** (recovery stages 1–2, `addresses_claims.csv`, gap matrix), (b) existing GitHub files and pending PRs, and (c) independently located public source pages. The digest lists hashes for separate archives, images, Gamma responses and raw X objects; **their bytes were not supplied in this task and those hashes have not been independently verified here**. A mapping reported as recovered from Gamma is not a fresh Gamma API query by this pass. Do not report those archives as committed evidence.

Source register:
- Original third-party C5 graph and X entity URLs: https://x.com/bubblemaps/status/2029603088420704535 ; https://x.com/bubblemaps/status/2041788771184877667 (the digest reports the complete address URLs in X object `2041788771184877667`).
- **Additional six-address roster** relaying a PolyBeats post, article ID 338288 (data timestamp: 2026-03-26 21:39:03): https://www.theblockbeats.info/flash/338288 . This is **third-party reported**, not chain-verified, and overlaps the Bubblemaps roster.
- Existing historical detector journal: `investigations/maduro-iran/sources/phase10/maduro_iran_timeline.csv`.
- Existing exact-address watchlist: `investigations/maduro-iran/sources/phase13/wallet_watchlist.csv`; further appearance in `investigations/edge-polymarket/sources/funding/data/echantillon.json`.
- Existing PolySentinel journal: `investigations/polysentinel/sources/evidence/signal_engine_v1/journal.jsonl`.
- **Unmerged PR #29**, `research/inca-crosscheck-20261106`: `research_notes/inca-crosscheck-2026-11-06/REPORT.md` and `data/population.json`. The complete address `0xfe6eee00d36717359578ddb4d6e091d56bc9074e` is present in its **control population**, while the report calls a matching 8-hex prefix `Kingyossi`. Exact address overlap with the control population is documented; a historical handle linkage remains a third-party mapping, not independent proof of account control.
- Original Nobel posts: https://x.com/PolymarketMoney/status/1976499384373121488 ; https://x.com/jconorgrogan/status/1977076806718308494 . Current public profile of the unresolved handle `6741`: https://polymarket.com/profile/@6741?tab=positions .
- Source review already on `main`: `research_notes/external-polymarket-cases-2026-11-07/REPORT.md` and `REPLAY_PROTOCOL.md`.
- Pending financial replay PR #44: https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/44 ; PR #32 (distinct, stacked draft): https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/32 .

## C5 — Iran strike / ceasefire: seven public proxy candidates, **not** seven proven coordinated owners

The recovery digest supplies **four** complete Polygon proxies through three X-entity links and a reported one-profile Gamma lookup:
- `nothingeverhappens911` (later renamed): `0xa4eb52229991c074bc560f825bf2776d77acd010`
- `MAGAMESSI` (later renamed): `0x1fa1be3eab546e06e4290839bf4c1d7abfbf1fa9`
- `Skoobidoobnj`: `0xfe6eee00d36717359578ddb4d6e091d56bc9074e`
- `Katzhgvhjbvccxd`: `0xb01a466c430119c47b02052d99c859d7bf63f311`

The March 26 PolyBeats roster includes the **first three** plus `0xde7be6d489bce070a959e0cb813128ae659b5f4b`, `0x88c4919de76e526d55a32c1f8afb439dd1f1129a`, and `0x0a854897a06d4999e5b2dde5693609f1428ffe9d`. These **three are extra candidate addresses relative to the recovered four**, not a new proven cluster. No exact account handle is assigned to them by the cited source. The union is seven unique addresses. See [data/candidates.csv](data/candidates.csv).

### A stronger cross-check already in the repository

The three original proxies appear as **eight-hex prefixes** in the earlier, separately produced P9 detector timeline:

| Exact proxy prefix | Replay alert UTC | Type | YES trade described by detector |
|---|---|---|---|
| `0x1fa1be3e` | 2026-02-27 13:54:09 | SIG_CTX | $488 at $0.230 |
| `0xfe6eee00` | 2026-02-27 21:23:31 | SIG_CTX | $417 at $0.170 |
| `0xa4eb5222` | 2026-02-28 00:55:43 | SIG_CONV | $4,087 at $0.190 |

These are **pre-existing detector observations**, not three transactions replayed anew in this pass. The identifier match is only at eight hexadecimal digits; it should be resolved against full proxy fields and transaction hashes before representing any trade as independently verified. The match is reproducible via [data/alert_crosswalk.csv](data/alert_crosswalk.csv) and `verify.py`, which validates the recorded journal rows, not their chain truth.

Two of the other extra addresses also occur in prior research:
- `0xde7be6...` appears at **full 40-hex length** in the phase-13 watchlist (`KNOWN_HIGH_LEAD`) and in later research. That label reflects an earlier detector's rule, not a verified insider attribution.
- `0x88c4919d...` appears at **full 40-hex length** in a PolySentinel signal-engine journal. Journal presence is not a proven C5 finance edge.
- `0x0a854897...` was **not returned by GitHub code search on `main`** in this pass; a zero code-search hit is not definitive absence.

In addition, PR #29's `data/population.json` contains the **full, exact** Skoobidoobnj proxy as a control, sharpening the digest's earlier eight-hex-only cross-reference. This does not make it an Inca five-account member, or make the C5 claims new.

### The missing, discriminating cash-flow evidence

A Bubblemaps diagram reproduced in the recovery digest only shows **short prefixes**: `0xeA2b...` (claimed Binance deposit), `0x7828...` (Relay recipient), `0xD0Dc...`, `0xbC8c...` (claimed auth signer for `0xb01a...`) and `0x8aCC...`. Amounts on the image were rounded by the third party. **Do not fill in these prefixes, equate same-amount transfers with a cross-chain hop, or mark the claimed signer as verified.**

Financial tests, in order:
1. Freeze the seven-account inclusion criteria, relevant Iran market condition IDs, historical time windows, USDC/native USDC.e contracts, and a comparable population of losing and ordinary bettors *before reading exits*.
2. For **each of seven proxies**, replay Polygon `Transfer` logs (tx hash, log index, token address, precise atomic quantity, UTC) and Polymarket fills and account/deposit-wallet distinctions. Reconcile withdrawals, bridge order identifiers, CCTP and swaps through complete receipts, not coincident amounts.
3. For `0xb01a...`, identify contract type at the **historical block** and recover the authorization/signer relation (Safe owners/modules or appropriate proxy factory and creation records). Resolve the `0xbC8c...` prefix only against a uniquely documented address. This is potentially more discriminating than a Binance deposit.
4. Search the recovered exit paths for `0xeA2b...` and all shared destinations, then count *all* distinct depositors and unrelated exchange users over the same observation window. An address with high fan-in is a service/customer-deposit edge at most, not shared control.
5. Compare exact address sets and on-chain counterparties to the separate 9-account Bitquery group, 38-account February cohort, 8-account Maduro/Iran group, and PR #27/#29 controls. Register each comparison and negative control; **do not combine PnL totals** without accounting for overlapping proxies and market snapshots.

Accept **CONFIRMED** only for independently replayed transaction-level legs. A direct authorization edge may support a control relationship with an alternative hypothesis recorded; shared exchange deposits alone never establish an individual owner.

## C7 — 2025 Nobel: four mapped proxies, two unresolved handles, and a missing distributor

Reported one-profile Gamma matches in the supplied digest (**not re-queried here**):
- `dirtycup`: `0x234cc49e43dff8b3207bbd3a8a2579f339cb9867`
- `madurowilllose`: `0x8507124d416dd181ea552e01a0dfed19ab0b1086`
- `fmaduro`: `0x1973177faa69b94b4afab818e612a7c05b3c01a9`
- `trumpdeservesit`: `0x03f8aae7ae1687ef7e2d55e4429e72e9a95d8541`

`6741` and `aenews0` remain **without a verified full proxy**. The public `@6741` profile is accessible but does not, in the inspected public page text, furnish an exact proxy mapping. Its displayed **$71.6k biggest win** and **+$47.1k total PnL** are different metrics; neither is a reconstructed October 2025 net profit or an account-level on-chain accounting result. Do not conflate the two or treat contemporaneous third-party profit figures as current PnL.

The posted assertion that one wallet funded six accounts for about $250k still lacks the wallet address and transfers in the supplied evidence. The `changenow-polymarket:F-005` note (8 buyers, $212,874) is a **different, unreplayed universe**, not six confirmed funding links. A useful next test is to resolve the two handles from stable historical profile keys and perform six independent Polygon inbound token-log histories **before 2025-10-10 09:00 UTC**. Link only direct, non-service transfers with transaction receipts; calculate sender fan-out to an appropriately matched market-wide control population, and distinguish early maker fills from order creation.

## Other recovery gates and no-duplicate rule

| Rank | Work | State as of this note | Acceptance |
|---|---|---|---|
| 1 | C5, 7 proxy candidate ledger + signer and claimed Binance graph | No chain receipts replayed in this note | Full tx/log evidence and deposit fan-in controls |
| 2 | C7, six Nobel handles and the alleged distributor | Four documentary proxy mappings; 2 missing | 6 exact mappings, funding receipts, pre-announcement chronology, control sample |
| 3 | PR #44 unfinished: 25 of 37 Iran deposit sides, 17 KPMG funding-wallet Relay pages, 22 non-Relay child destinations | PR open; not re-run here | Resume existing collectors on their branch; no parallel rewrite |
| 4 | C1 Burdensome-Mix versus Maduro 8 and Railgun 71 | Alleged account in official filings; proxy still unknown here | Exact proxy then first-funding and payout comparisons |
| 5 | C2 AlphaRaccoon / renamed `0xafEe` | Full proxy unresolved; one archived 39-hex string is invalid | Resolve via official account reference; reconcile 23+ market positions |
| 6 | C8 Israel October 2026 election | No unbiased entire-market wallet census | Freeze the full market population and independent control groups |

For C2, the CFTC civil pleading uses **`Wallet-0xAf6` as a litigation label for a funding wallet** and says it funded AlphaRaccoon in Oct/Nov 2025 (paragraphs 38–40); do **not** equate that identifier with the renamed public account `0xafEe`, nor assume `0xAf6` is a complete or unique EVM prefix. Source: https://www.cftc.gov/media/14046/ENF_SpagnuoloComplaint052726/download . Its fraud allegations are **not** adjudicated facts.

For C1, the two DOJ press pages give inconsistent end dates for the 13 bets (Jan 2 vs Jan 26, 2026). Keep the SDNY and indictment chronology explicit, as the existing intake already does. Do not link Burdensome-Mix to the 71-account Railgun distribution just because its reported account creation fell on Dec 26. The PR #44 sample is strongly selected: **66 of 71 accounts lost**; only five hit the Jan 31 outcome and their reported positions were not redeemed as of the PR snapshot. This pattern is not evidence that all 71 knew the military operation's date.

**Priority is cash-flow discrimination, not additional social-media search.** No new personal identification or claim of trading misconduct should be published on the basis of this registry.

## Local verification

Run from the repository root:

```bash
python3 research_notes/c5-c7-recovery-overlaps-2026-11-07/verify.py
```

The check validates address syntax, account uniqueness, missing-proxy statuses, the **three exact historical detector rows**, and existing exact-address overlap where locally available. It does **not** connect to RPC, establish a financial link, authenticate external media or verify the user's unprovided raw archives.
