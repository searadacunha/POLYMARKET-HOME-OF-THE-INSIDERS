# Historical Polymarket X corpus — reconciliation against merged on-chain findings

**Intake date:** 2026-11-06. **Source:** [user-supplied historical corpus summary](sources/rapport-corpus.txt), provided after the first and second historical-X dossiers. **Source cutoff:** exclusive `2026-11-06T00:00:00Z` (the source intentionally excludes X posts made on November 6). **Status:** historical documentary material, **not a new blockchain analysis**.

**Priority of evidence:** [on-chain verification already merged via PR #36](../x-history-2026-11-06/verification/REPORT.md) and [its lead status register](../x-history-2026-11-06/verification/LEADS_STATUS.csv) take precedence for chain-derived balances, fills, attribution types and losses/profits. The supplied corpus is an important secondary archive of historical X content and counterclaims. It is **not an independent corroboration of the first two reports**: the three dossiers overlap and reuse many identical posts. Its primary X response wrappers, screenshots and 244 purportedly byte-preserved source files were **not attached with the summary**; the source's claimed full-corpus SHA256/replay cannot be independently validated here. This PR archives the summary, not those 244 files.

## 1. Recorded corpus coverage (reported, not independently recounted)

| Metric | Source report |
| --- | ---: |
| Original historical response wrappers | 79 |
| Occurrences from original historical responses | 1,416 |
| Targeted supplemental X calls | 18 |
| Supplemental occurrences, including 179 data and 124 reference occurrences | 303 |
| Combined occurrences | **1,719** |
| Unique X IDs in combined corpus | **1,301** |
| Unique serialized representations | 1,368 |
| Newly archived IDs relative to original 79 responses | 191 |
| Author objects / relation edges | 519 / 753 |
| Literal mentions / documentary observations | 2,299 / 36 |
| Files the original corpus preparer says were preserved byte-for-byte | 244 — *not supplied here* |

These counts are internally coherent at their stated aggregation levels; they do **not** represent independent confirmations or 191 new investigative findings. The 79 base wrappers, 18 extra calls, 986 IDs in the union of the first two exports, and the larger 1,301-ID combined raw corpus use different inclusion rules. No attempt to equate these denominators is justified.

## 2. Temporal audit: avoid the erroneous Snowflake offset

The source report challenges an independent audit that shifted X timestamps by ~317 seconds. For the standard X Snowflake encoding,

`timestamp_ms = (BigInt(post_id) >> 22n) + 1288834974657n`.

The source reports `created_at` agreeing with this standard to within one second for the 1,416 historical occurrences and 1,033 export rows. It attributes the audit discrepancy to an *implicitly used* alternative epoch of `1288834657000` milliseconds (317,657 ms difference). The original auditor's actual code was not provided, so no claim is made about intent or a proven implementation bug.

The local, deterministic [timestamp check](tools/check_intake.py) recomputes **selected exact X IDs** from this report, not all 1,301 ID objects; it tests only their encoded date and never establishes post text, edit history, media authenticity or authorship. A single `edit_history_tweet_ids` item cannot establish the absence of prior edits unless the API/provider's semantics support that inference independently.

## 3. Reconcile each historical observation with findings already on main

| Dossier | Source report's contribution | Current verification on main | What remains open |
| --- | --- | --- | --- |
| **D1 — Snoorrason, Oct 14** | Supplied `note_tweet.text` **purports to list all five names in order** at 08:23:34 UTC; the screenshot reflects Thin's positions | Oct 14 publication time and Thin's **66,799.56 Mbappé-over-Yamal** / **3,916.35 Rodri-over-Messi** shares are independently matched. The separately retrieved public embed was truncated; **complete five-name note text stays UNRESOLVED by independent primary retrieval** | Fetch the original long `note_tweet` body and edit provenance, store returned object, compare full and truncated renders, and perform blind prediction-from-positions analysis |
| **D2 — four alleged Railgun-funded Maduro wallets** | Four exact candidate addresses and annotated deposits on Dec 26 2025, spread over **51m50s** at ~774–818 USDC.e | **Not yet checked on-chain in the merged verification** | Resolve 4 proxy/wallet relationships, Polygon receipts, bridge orders, matched privacy-service controls; do not attribute private pool users |
| **D3 — Iran Jan 14 YES/NO** | Portuguese contemporaneous commentary proposes a >$40k YES stimulus with another account accumulating NO | **Untested** and no two account addresses established | Decode exact market's fills, order-book effects, counterparties and full net PnL; test market-making and unrelated trading alternatives |
| **D4 — thesecondhighlander** | Screenshots identify the account, claimed snapshot -$160,272.60 | On-chain report resolves proxy and reports **-$174,453.49** in the fuller ledger, a negative-control case | Preserve the snapshot-vs-ledger distinction; no new wallet identification required |
| **D5 — flydartball** | Original @Polymarket promotional posts and a subsequent *reported* June sale-at-loss | Verification **refutes the claim that the June market ended in a realized loss**: **+$256,137.07** in that market, **+$841,375.23** total with 12 losing Iran markets | Examine timing of partial sells vs later redemptions; historical promotional selection bias; no inference of privileged information |
| **D6 — alleged 38 + March 18 extension** | X entities contain **38 documentary links**, reported as 12 addressed URLs + 26 pseudonym URLs; one source section says 22 when 26 URLs are displayed | Verification separately resolves **38/38 profiles** and their payouts to Coinbase deposit `0xc5bb1be0…`, with **1,576,522.86 USDC** result (not claimed $2.14M); March 18 extra account **+$364,518.12**, with no established join | Preserve source's 22-vs-26 link discrepancy; complete unread Base/Arbitrum legs and prestrike comparator tests; do not infer person or secret information |
| **D7 — SBet365 / Jan 2026** | @lookonchain's Khamenei bet is a specific dated research clue; narratives about a jailed trader are not evidenced | Verification finds Khamenei by Jan 31 **-4,000 USDC**, without any proven judicial link | No arrest attribution; source-to-wallet narrative dependence |
| **D8 — Chiwawas** | Jan 3 sell/redeem conflict in screenshots; **$82,070.14 gross proceeds** conflated with profit | Prior main investigation already reports scoped net **+$34,351.19** | Decode order fills vs CTF redemption receipts at 15:07, reconcile December losses and fees |
| **D9 — Jydyjyd / irboz** | Sept Yamal stance, Oct 21 text on observing suspected insiders, Oct 27 claim of exits, irboz dissent | Ledger: Mbappé-over-Yamal from **16 minutes before Cypya's post**, sales on Oct 25, no exact-place bet; copying a person is not verified | Separate public-information influence from independent market strategies; don't claim the post explicitly says “I copied” |

The latest verification already establishes an additional **three-account Coinbase payout convergence**: JamWil23, bravonoll and Frogensky paid into `0xd1262395…`. This result comes from receipts in main, **not** from the newly supplied corpus. The absence of common ownership evidence is not a denial of the confirmed shared destination.

### Four Maduro accounts in D2, exact candidate proxies (source assertions only)

- FrostyFox: `0x2577c59314e3efd45f9dd31067ea329d5a4ea5ec`
- ThunderStrike99: `0xdbddb8bc3d3dca058a8b19c539effab1363c7417`
- W3tLdR9s: `0xdcdd69a814ca1b2c8f0611fd4e10c9376fa61e87`
- speedrinking: `0x86f2c4c9f2f81950d337647e188f77c4aea3c7a8`

Source publication: https://x.com/ec_unoxx/status/2008147229325013019 (Jan 5, 2026, 12:03:03 UTC). Source screenshot annotations (GMT+8 translated to UTC): Dec 26 at **07:39:29, 08:04:53, 08:15:11, 08:31:19**. These are not yet verified block timestamps. Do not trace through privacy pools to infer identities.

## 4. Two targeted additions from this source report

**C1 — explicit rejection of a weak Coinbase/ENS matching argument.** @ec_unoxx's Jan 5 replies https://x.com/ec_unoxx/status/2008186913170333953 and https://x.com/ec_unoxx/status/2008214606381281439 criticize a purported STVLU.SOL → sender connection and a ~23-hour timing coincidence as insufficient proof. This is **historical criticism of an inference**, not new chain evidence. It applies to that specific proposed edge; do not discard unrelated evidence without examining it. Do not infer a real-world identity from ENS plus amounts near a CEX.

**C2 — DimBull's alleged March 7 losing bet.** @qkl2058's Mar 19 post https://x.com/qkl2058/status/2034669367888318477 names DimBull and reports **2,000 YES shares at 0.24**, allegedly settling at zero (**-480 USD**) on a *different Iran deadline* from the February 27–28 cohort. Existing merged verification already resolves DimBull as `0xc0292a841a0c9a7320aa39075cffcf1b8f64f705` and reports **+74,315.08 USDC** across its broader ledger. **No inconsistency is established** until the exact conditionId/tokenId and Mar 7 leg are identified, including fees, sells and redemptions. This is not a new owner-link proof and an affiliate/copy-trading link is not evidence.

## 5. Highest-value next tests, ordered for an isolated agent

1. **Authenticate Snoorrason full long-form X body.** The user-supplied text includes the full five-name ranking while the independently fetched embed is truncated. Retain both as separate source representations; get X `note_tweet` from a documented primary API, original `created_at`, edit history and media ID; no guess from the final Ballon d'Or result.
2. **Validate the four December-26 privacy-route candidates** with primary receipts and comparison to at least a preregistered cohort of similar users. First test whether they are even correctly resolved Polymarket accounts and whether the actual upstream hop touches Railgun.
3. **Reconstruct January-14 Iran YES/NO episode** using frozen tokens, actual prices, order fills and independent news timestamps. An anonymous theory is not a confirmed coordinated manipulation.
4. **Close the DimBull and Chiwawas accounting discrepancies** with full token-level sales/redemptions and net PnL (don't equate gross recoveries to profits).
5. **Finish missing Base/Arbitrum portions and 38-group matched baselines** and independently explain any retained link to the March 18 extra account. Never join groups merely via a CEX.

### Publication protocol

Add new chain evidence only in a follow-on isolated branch with hashes, `chainId`, `contract`, `tokenId`, `txHash`, `logIndex`, exact amounts and snapshot provenance. Maintain separate **X quotation/citation graph** and **on-chain value-flow graph**. Mark partial coverage and negative controls. Do not modify the root README, frozen investigation reports, existing evidence or another agent's branch in this intake. No scheduled searches or automatic public posts.

## 6. Scope and limitations

The supplied summary says 244 corpus files were copied and SHA256-checked, 1,301 unique IDs compiled, 51 IDs having more than one rendered representation and 19 references unavailable. The original 244 raw files, primary X API bodies, captures, manifests and actual replay scripts were **not available as attachments in this conversation**. Only the user-provided text summary is archived here. Reproducing the *assertion that a checksum test passed* is not independent execution of that checksum test. The current PR does not rerun on-chain RPC or alter earlier reports. See [adjudication register](ADJUDICATION.csv) for explicit status at the intake boundary.
