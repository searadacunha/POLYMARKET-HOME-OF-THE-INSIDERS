# Reproducible follow-up protocol: external cases, historical-only (2026-11-07)

This is a **task specification**, not a finding. Historical X input cutoff: exclusive 2026-11-06T00:00:00Z. Civil/criminal filing documents can be read through November 7 for case-status checking. The 93-line user's source report references \`cases.json\`, raw X files and \`SHA256SUMS.txt\`; those **actual bytes have not been supplied**. Do not manufacture an archive or claim those hashes were verified.

## First: freeze documentary provenance

For each case store a source register with \`source_type, original_publication_utc, accessed_utc, url, preserved_sha256, source_role, exact_quote_or_paraphrase, legal_status_as_of\`. Capture DOJ/CFTC press releases as **filing reports**, not judicial convictions. In C1 distinguish the DOJ SDNY Jan 2 window from a different OPA webpage's internally impossible Jan 26 phrase. In C2 distinguish **amount wagered/at risk**, **gross received**, **realized result** and **cash out**. Cite the actual filing and pleadings, not just translated media.

Keep a record of *non-independence*: 60 Minutes' nine-account conclusions are attributed to Bubblemaps; many X posts merely reproduce the same graph. Bitquery independently reworked the chain, but until a local reproducible run is performed its calculations remain \`INDEPENDENT_THIRD_PARTY_LEDGER\`, not \`CONFIRMED_IN_THIS_REPO\`.

## Case-specific preregistered checks

### C4: nine Iran accounts versus 38 in current main

1. Use \`EXTERNAL_WALLETS.csv\` to freeze nine externally published Polygon proxies. Run \`python3 research_notes/external-polymarket-cases-2026-11-07/tools/check_external_cohort.py\`; it must return **0 / 9 direct address overlap** with the 38 committed proxies. This does **not** exclude indirect funding/exits.
2. Obtain their historical Polymarket profiles, Gamma conditionIds/tokenIds, every buy/sell/split/merge/redeem, current and expired collateral, receipts/logIndex, rewards, and complete pagination. Validate Bitquery's **$2,476,951** per-account sums independently, distinguishing a Sep 22 snapshot from later activity.
3. Confirm the **86 / 101 position-wins (~85.15%)** and the distinct **98.2% money-weighted successful share** before citing any win rate. Show null models conditional on quoted entry prices, market selection, event-time public information and account ages. **Five opened Feb 13–16; four in March.** Do not describe all nine as early buyers before Feb 28.
4. Classify all shared Binance deposits by real on-chain gas funding, sweeps, CEX tags **with provenance**, fan-in distribution and matched ordinary service users. Bitquery reports many unrelated senders on those deposits; that observation weakens inference of one customer.
5. Check any graph edge between the nine, the existing 38, the independent eight-account Maduro/Iran group and the 19-account Iran research in unmerged PR #27. Use exact proxy IDs, direct value transfers and discriminant service-controlled edges. The **0/9 address overlap** cannot prove absence of non-proxy links.

### C6: Biden pardons, two betting proxies plus one Kraken-style cashout destination

- Freeze \`0xd9be4e8f031a5beaa1f0d29ceff2826e3cc91d98\` and \`0xa416a5c03381c90b94e4c1881b0494281e3e025e\` as two **trading proxies**; \`0x0a65fdd872da9fc9a16a37a9c10be8e8362d8d7e\` as an **exchange deposit destination**. Do not count the latter as a third betting account.
- Resolve pre-inauguration January 2025 questionIDs and conditionIds directly from old CTF contracts and settlement events; a 2026-era data API may not cover 2025 history completely.
- Reconstruct PnL from exact fills including the earlier Hunter Biden market and the separate small losing bets. Compare Bitquery **$316,343** with Bubblemaps/NPR **$316,346**, not treating a $3 difference as different accounts. Reconcile NPR's ~$64k vs Bitquery's ~$50k January staking bases with the same date/market scope.
- Trace both withdrawals to the exact Kraken-style deposit via chain receipts and check whether this address received unrelated client funds or was reused, before inferring a shared credited account.
- Bitquery reports that \`a416\` later **lost $11,379 in 23 Iran markets** and once met \`fuego66\` in a **routine $2,000 order-book fill**. Treat these as controls for "market overlap ≠ wallet ownership".

### C1, C2, C3: legal-source cases and exact chain mapping

- C1: resolve the Burdensome-Mix proxy with contemporaneous archived Polymarket aliases or official records, freeze market IDs and YES positions, then compare exact funding and payout edges to all existing Maduro cases. Do not assume an accused person operated any address other than the one documented in an official record.
- C2: resolve AlphaRaccoon **full Polymarket account contract/proxy** from documented public attribution; compare >23 Google Year in Search condition IDs, sale/redemption fees and $2,754,092 amount at risk. Do not mistake the alleged ~$1.2m profits for independently rerun net PnL.
- C3: do not publish a real name or equate a public wallet handle with the two unnamed defendants in the Israeli court reports. Treat open PR #32 as a separate draft, read its evidence before opening a dependent investigation, and avoid re-writing any parent/child PR.

### C5, C7, C8: other distinct markets

- C5: recover the original Bubblemaps X entity URLs and exact 4 profiles, verify reported shared Binance deposit receipts, then check overlap with nine and 38 separately. No ownership or standalone PnL claim until verified.
- C7: compare Nobel 2025 account set to existing \`changenow-polymarket:F-005\`, freeze the correct market, obtain the actual date/transactions for dirtycup/madurowilllose, test the alleged distributor-to-six edges.
- C8: Israel 27 Oct 2026 elections: make a market-family census of **all** accounts that traded the same outcomes, not only new winners. Distinguish Bloomberg's "600+ newly created wallets" from Bubblemaps' "101 first funded on election day". Choose matching mature and contrarian accounts, fix cutoffs at verified public exit-poll times, calculate trade time versus public update/repricing, and evaluate maker order placement as unknown if only a fill time is visible.

## Chain and statistical discipline

- Always use official token **contract addresses**, chainId, logIndex, transactionHash, event/conditionId/tokenId, exact Decimal units, market resolution, split/merge/redeem paths, and all visible transaction fees.
- Propagate uncertainty due to missing Base/BSC/Solana/Arbitrum histories; any unknown leg is \`UNKNOWN\`, never \`DISPROVEN\`.
- Keep independent provenance categories: actual direct wallet-to-wallet transfer, service exposure, CEX deposit convergence, routine maker/taker fill, price coincidence and media allegation.
- Fix control-population filters and time windows before examining profits; pre-register missing-data rates and keep negative-control losing accounts.
- Do not infer private identities from deposit labels, ENS overlap, equal-sized flows or the jurisdiction of an official indictment.

## Git and publication guard

Use a new dedicated worktree rooted at current \`main\`, and publish primary chain results under an append-only subfolder with a verifiable SHA-256 manifest. Do not edit the accepted root README, existing investigations, imported source snapshots, archived Relay, generated central reports, publication-baseline anchor or other open drafts in this intake.

A claim can move from reported to confirmed **only** after primary receipts plus a deterministic replay. Any later evidence-backed promotional README change requires its own isolated review and exact protected-baseline process. Keep this historical project **one-off**, no recurring X searches or alerts.