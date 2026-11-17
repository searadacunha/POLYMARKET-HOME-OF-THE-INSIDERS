# Second pass — historical X counter-investigation (2026-11-06)

**Evidence class:** historical source dossier / on-chain hypothesis generation. **This phase itself produced no fresh RPC receipts.** Subsequent [verification in PR #36](verification/REPORT.md) provides newer primary-chain evidence and takes precedence where claims conflict. The report's Oct 14 *complete-ranking* claim is still **UNRESOLVED**: the independently retrieved Snoorrason embed confirms discussion of Thin's positions but truncates the long-form text; it does not independently show the five names. The Oct 16 Cypya complete ranking is verified. Preserve this second-pass dossier as a record of what its source reported, not a second independent confirmation.

## Source / research coverage

Source supplied by the user: **"Polymarket — contre-enquête historique approfondie"**, 1,383 lines, date cutoff 2026-11-06 (Europe/Lisbon), generated after the earlier historical-X report referenced in [REPORT.md](REPORT.md). It reports 39 successful X calls + 1 failed, 35 searches + 4 lookups, 472 unique data posts (642 IDs including references) and 11 downloaded images for the second pass. Together both passes report 80 calls, 986 distinct IDs including references, with incomplete pagination. These figures are **source-reported**, not locally recounted from its unavailable `raw/`, `posts.json`, `wallets.csv`, `cohort38.csv` and `queries.json` exports.

The second report states **7 PARTIAL, 2 UNVERIFIED and 0 globally certified NEW** (its classifications, not an independent audit). Source posts may be older than the observations they describe. A single returned edit-history ID does **not** independently guarantee that the text was never edited.

## D1 — Snoorrason discusses Thin's positions on October 14; full ranking text disputed

- Primary X object reported: https://x.com/SnoorrasonPoly/status/2110285369748963671
- `created_at` reported: **2026-10-14T08:23:34Z** (09:23:34 Europe/Lisbon); X snowflake timestamp independently checkable offline. This is **57h14m52s before** @Cypya_Poly's Oct 16 17:38:26Z post. The claim of a complete prediction in the post is from the supplied X archive; the X API text/edit history has not been independently fetched in this PR.
- The reported text lists **Kane, Mbappé, Yamal, Rodri, Messi in that order** and says this appears inferable from large Polymarket positions, rather than citing a private source.
- Reported screenshot attributes positions to prefix `0x8d3319C51520518a`. The already-published [Thin-Disclaimer-Life case](../../investigations/ballon-dor-wallets/sources/cases/thin.md) gives proxy `0x8d3319c51520518ad01f6744486ceea29f376f5b`.
- **Recomputed from the existing case's 73-row historical Markdown ledger**: before 2026-10-14T08:23:34Z, 49 logged BUY rows across these two outcomes sum to **66,799.56 Mbappé-over-Yamal shares** and **3,916.35 Rodri-over-Messi shares**, consistent with the reported screenshot values (66,799.6 and 3,916.4, rounded). This is an **independent arithmetic consistency check of existing repository data**, **not** a fresh RPC validation, a dated screenshot authentication, or an X account↔Thin key association.
- Distinction: available outcome markets at that point include matchups, **not the later exact-place markets** (2nd/3rd Oct 19; 4th/5th Oct 20 per existing Gamma snapshots). The top five is a forecast deduced from positions; no one could trade all exact-place tokens before those tokens were available.
- Test: independently recover the X API note_tweet text + media + edit history; replay Thin pre-/post-14th fills from receipts (and their metadata), then test whether the complete ranking can be inferred *blindly* from the position snapshot without knowledge of the eventual winners.
- **Do not claim an independently verified full top-five forecast on Oct 14:** the Grok report's long-form text requires authentication beyond the truncated independent embed. Its date and Thin-position correspondence are supported; Cypya's Oct 16 exact post is confirmed in the later verification.

**Additional public candidate, NOT X-to-wallet identity proof:** [Polymarket Snoorrason profile](https://polymarket.com/profile/0x805a922574d7d6b158b7bbb49a6fa8925eb60635), address `0x805a922574d7d6b158b7bbb49a6fa8925eb60635`. A third-party [PolyPnL page](https://polypnl.kaeose.me/profile/0x805a922574d7d6b158b7bbb49a6fa8925eb60635) labels this profile `@SnoorrasonPoly`; mapping and trading period require validation. It must **not** be equated to Thin or used as evidence of common ownership.

## D2 — Four alleged small Maduro accounts sharing a privacy route

Source X: https://x.com/ec_unoxx/status/2008147229325013019 (2026-01-05T12:03:03Z).

| X label | Proxy candidate (not independently revalidated) |
| --- | --- |
| FrostyFox | `0x2577c59314e3efd45f9dd31067ea329d5a4ea5ec` |
| ThunderStrike99 | `0xdbddb8bc3d3dca058a8b19c539effab1363c7417` |
| W3tLdR9s | `0xdcdd69a814ca1b2c8f0611fd4e10c9376fa61e87` |
| speedrinking | `0x86f2c4c9f2f81950d337647e188f77c4aea3c7a8` |

X media reportedly shows four receipts around **2025-12-26T07:39:29Z, 08:04:53Z, 08:15:11Z, 08:31:19Z**, each roughly **$774–818 USDC.e** (image annotations converted from GMT+8, **not blockchain timestamps**). The X author labels the financing upstream as Railgun and hypothesizes common control. **Neither the private-pool relation, the incoming sums, the transaction hashes nor the owner hypothesis is independently proven here.** Similar service routes, repeated fees and fixed sizes require service-exposed negative controls. Halt wallet trace at the privacy pool; do not attempt attribution through private users. These addresses were not in the reviewed summaries, but full-repository novelty is **UNVERIFIED**.

## D3 — Alleged YES pump / NO accumulation, Iran Jan 14

Sources https://x.com/LordWottonBR/status/2011836680756470064 and https://x.com/MariaOsint/status/2011825433998676026 (posts on Jan 15). A $40k+ YES and concurrent NO buying are alleged, **without full wallet IDs or receipts**. Could represent independent speculative trading, market making or arbitrage, not market manipulation. Resolve the exact Jan-14 US-strike-Iran market, all participants and liquidity; simulate both sides' costs/slippage. Do not link to X34 or existing groups by narrative alone.

## D4 — Negative-control identity: thesecondhighlander

Source https://x.com/PredictFolio/status/2020936742937952644 ; correction https://x.com/CarOnPolymarket/status/2021095225393873035. The source screenshot reportedly names **thesecondhighlander**, an account dormant since an earlier join (Nov 2024), **not necessarily a newly created wallet**. Reported -$160,272.60 total account PnL does not equal the naive sum of displayed position losses (-$97,265.50 Iran Feb 9 YES and -$74,997.91 Trump 2024 NO); no receipt-based accounting here. Resolve profile and historic immutable proxy before classifying.

## D5 — Platform amplification of flydartball before later loss reports

@Polymarket posted https://x.com/Polymarket/status/1935081943001088030 (Jun 17 2025) and https://x.com/Polymarket/status/1935448595378909355 (Jun 18), promoting the trader's purported >$200k then >$500k stake. Source https://x.com/yc989/status/1935769781669437727 (Jun 19) says the trader sold at a ~$216k loss. Distinguish promotion from verification and sale loss from eventual settlement. The recurring 2026 username must be mapped to the actual same address before making any cumulative PnL claim.

## D6 — Details and extra candidate in alleged G→38 cohort

@Andrey_10gwei's March 17 thread claims: **2 initial + 10 Feb 22 + 22 Feb 24 + 4 Feb 25–27 = 38**. The second report collected **10 fully exposed profile addresses, 26 more pseudonyms**, nine EVM funding addresses, one Solana funding address; the reported `cohort38.csv` / `wallets.csv` exports were **not attached**. Do **not** pretend all 38 are resolved or transfer-confirmed.

- Candidate account 1: `0x8a480B60Cb78213fDf34842160dc956a831a2558`.
- Previously known group G destination: `0xc5bB1Be0407db7312911ec765D399D02461e411a`; PR27 already discusses four G accounts.
- Extra claimed associated account from March 18 post https://x.com/Andrey_10gwei/status/2034374844746526837: `0x1caA6a7ad0c6916aeF7b67946De2e57Ad24846a0`, purported +$500k. Its cited Coinbase destination `0xD85b82C258be0Fa3EF52fF7242c213765daAffe6` **differs** from G's sink; timing and exchange overlap alone do not establish any edge.
- Claimed 46 consecutive wins were reportedly on 89–99¢ outcomes; compare to risk-calibrated benchmarks and selection effects, not a naive 50/50 null.
- Stop at the 38 distinct profiles claim until source entities and blockchain receipts resolve them.

## D7 — SBet365: Iran market Jan 2026 vs false arrest association

Source https://x.com/lookonchain/status/2011736650054062085 (Jan 15) says SBet365 allegedly bet on **Khamenei out by Jan 31** around Jan 13. The same post juxtaposes a statement about an imprisoned Venezuelan leaker and inactivity of other wallets. **There is no evidence here that SBet365, or any named trader in this case, was arrested.** SBet365 and Ethereum deposit `0x72bf08860e18a46ee020e3a475f8491461903f48` are already in main; verify token, bet, exit and outcome without re-labelling known addresses NEW.

## D8 — Chiwawas: audit SELL vs REDEEM and gross receipts vs profit

Source https://x.com/alexin091/status/2008444605922984343 (Jan 6). Chiwawas `0x168b100d7a6620a2f49a455344c2c006eaf1714b` already in main. The post/capture refers to two Jan 3 purchases (05:35/05:46 UTC) and around $82,070 gross proceeds at 15:07, while the main dossier reportedly calculates +$34,351.19 over its scoped accounting. A screenshot labels the later action REDEEM while a table calls it SELL; require Exchange OrderFilled vs CTF payout Redemption receipts, and reconcile all Dec 2025 losses, Jan 2026 trades and costs. **No person-level identification from ENS and CEX amount proximity**.

## D9 — Public copy narrative and exits, Ballon d'Or

@Jydyjyd described looking at presumed informed traders' positions on Oct 21; independently checked text does not explicitly say they copied, and one relevant fill predated Cypya. New source https://x.com/Jydyjyd/status/2115072247618531466 (Oct 27) says they closed positions before the end; https://x.com/irboz/status/2114756749353779546 (Oct 26) voices contrary skepticism about large recent wallets. These opinions are not audit findings and cannot be attributed to a specific Polymarket wallet without a dated X↔wallet mapping. Compare the observable before/after tape to both the Oct 14 Snoorrason and Oct 16 Cypya boundary.

## Next steps

Prioritize: (1) authenticate Snoorrason original/edit history and revalidate Thin ledger on-chain; (2) test four privacy-routed addresses with matched service controls; (3) resolve and reconcile the 38 cohort with PR27; (4) challenge the $500k extra account link; (5) use losing alerts and Jan 14 YES/NO episode to quantify selection effects.

All evidence should preserve `chainId, tokenId, txhash, logIndex, timestamp, source_ID, source_role, result_status`, and must distinguish **X narrative graph** from **blockchain transaction graph**. The source excerpt and prior PR36 should **not** be counted as two independent witnesses. Missing raw exports or absent results must not be silently treated as negatives.

**Publication guard:** no changes to root README, MASTER_REPORT, frozen investigations or archived Relay evidence; do not merge while the existing publication-baseline CI issue remains unresolved. See PR36's CI diagnosis comment.
