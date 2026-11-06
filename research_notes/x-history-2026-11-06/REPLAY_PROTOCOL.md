# Historical-intelligence replay protocol (frozen input, no outcome-based cohort selection)

## Inputs / authority

1. Source dossier: user-provided `rapport-polymarket.txt` dated 6 Nov 2026. This PR imports its **reported** X observations, not an independently fetched X response corpus.
2. Primary X objects: archived author ID, post ID, created_at, edit_history_tweet_ids, full text, entities, quoted/replied post IDs, media hashes, URL and original timezone. Preserve all fetched pages (including zero-result queries), pagination and rate-limit logs. Do not replace failed lookups with negative evidence.
3. Existing on-chain baseline: main commit `17acd3409382201dfb6fc0d43a30d4208952eb02`, plus PR27–32 only when their actual head commits are explicitly recorded. Read README, MASTER_REPORT, METHODOLOGY, both Ballon d'Or findings/reports, maduro-iran phase2 and relevant PR reports. Never silently treat unmerged PR data as main.
4. Independent public result: UEFA's 26 Oct 2026 top five (linked in REPORT.md). Keep date of publication separate from event date.

## Fixed questions and stop conditions

**Q1 — Ballon d'Or public diffusion, two public cutoffs.** Does the full top-five text occur in the Oct 14 @SnoorrasonPoly post (X ID 2110285369748963671, 08:23:34Z) and/or Oct 16 @Cypya_Poly post (X ID 2111149784858042762, 17:38:26Z)? Validate each original API note_tweet.text, edit history, URL/media and author; a Snowflake ID alone does not validate post content. Treat the Oct 14 date as **the earliest located in the bounded X sample**, not the earliest all-X source. If the text was edited after the relevant time, do not assign it earlier. The Oct 14 forecast reportedly interprets pre-existing Thin positions rather than documenting the source of privileged information.

**Q1b — Thin screenshot vs existing on-chain snapshot.** Audit the case `0x8d3319c51520518ad01f6744486ceea29f376f5b` and both matchup outcomes before Oct 14 08:23:34Z. The published 73-row case's pre-cutoff BUY ledger totals **66,799.56 Mbappé and 3,916.35 Rodri shares** (49 matchup BUY rows; see `tools/check_thin_before_snoorrason.py`). Verify these figures from primary Polygon receipts/logIndex and public API snapshots, separate screenshot capture time from block time, and challenge whether a top-five ranking can be inferred without the final result. A viewer of positions must not be equated to the wallet controller.

**Q2 — Before-vs-after fills.** Among all eligible market participants (not just winners), which outcomes and positions were available/traded before Oct 16 17:38:26 UTC, between Oct 14 and Oct 16, from Oct 16 to market launches, and afterward? Freeze exact outcome tokens and market IDs from Gamma, not from the winning final rank. Compare pre-/post-signals and identical-shift placebo cutoffs, controlling for liquidity, market price and participant activity.

**Q3 — Copies and independent traders.** Does the account described by @Jydyjyd follow the observed leaders, or does any alleged follower systematically predate them? No X-to-wallet assumption without an explicit, dated mapping; the Cypya/Jydyjyd profile addresses are **candidates only**. If mapping fails, stop person-level inference, retain market-wide diffusion tests.

**Q4 — Maduro/Iran candidates.** For PURE698 and JamWil23, verify account identity and complete Polygon fills, deposits, withdrawals and settlements from 2025-03-01 to 2026-02-28. Check Israel–Iran June 2025 against each other Iran/Maduro market by exact conditionId/tokenId; include losing/missing expiries. Refute the alleged cross-event continuity if no earlier Iran exposure exists for the same verified address.

**Q5 — Group G and alleged 38 accounts.** Extract source-linked unique proxies and check all claimed payments to `0xc5bB1Be0407db7312911ec765D399D02461e411a`. Compute intersection and differences versus G (4), E, and the Maduro/Iran eight-account group. Test pooled deposit-service hypotheses with fan-in/fan-out and matched service recipients. Do **not** claim 38 controlled wallets until 38 distinct addresses plus discriminating links and an alternative-service test exist.

**Q6 — cashy, flydartball and negative controls.** Link tweets to receipts via calibrated bot lag; measure actual fill time, fill type (maker/taker), inventory and realized + remaining value. Include every failed expiry, negative-control alerts and all periods. Do not treat volume or withdrawn cash as profit.

**Q7 — Media census discrepancy.** Reconcile press claims of 12 accounts versus the existing 11-account audited cohort by explicit profile and wallet mappings. The numerical difference alone is not evidence of an omitted account.

**Q8 — Privacy-routed Maduro quartet.** Verify four addresses from @ec_unoxx (see SECOND_PASS.md) and the alleged funding on 2025-12-26 at 07:39:29, 08:04:53, 08:15:11 and 08:31:19 UTC. These timestamps and $774–818 amounts are **annotations from social media screenshots**, not verified chain receipts. Test the Railgun/Relay routing claim using actual on-chain routes and matched service controls; never infer common ownership or de-anonymize private-pool clients.

**Q9 — January Iran YES/NO, SBet365 and losing controls.** Resolve US strikes Iran Jan 14 vs Khamenei out Jan 31 vs Iran Feb 9 as **different market IDs**. Test the alleged $40k YES-led price swing with full makers/takers, liquidity and net PnL; verify SBet365's claimed Jan 13 order without drawing any arrest implication. Use thesecondhighlander as a potential losing control after resolving the address and PnL.

**Q10 — Cohort 38 / candidate 39 / gross-vs-net.** Collect source entity URLs to resolve all 38 independently of aliases; the supplied second X report's CSV exports were **not available**. Keep a claimed `0x1caA6a7ad0c6916aeF7b67946De2e57Ad24846a0` / $500k account separate because the cited Coinbase deposit differs from group G's. Independently reconcile Chiwawas's Jan 3 SELL vs REDEEM and gross $82k exit vs historical net PnL. Confirm each assertion from on-chain receipts.

## Chain reconstruction

- Resolve Gamma event -> market -> conditionId -> clobTokenIds; record the response snapshot, resolution criteria, market opening metadata and the **first verified trade** (metadata startDate need not equal first executable trade).
- Fetch Polymarket Data API positions/trades with complete pagination and coverage diagnostics. Cross-validate decisive fills with Polygon (chainId 137) OrderFilled receipts/logs and block timestamps from two independent RPC endpoints. For proxy and EOA ownership validate contract method and time, not username similarity.
- Normalize decimal scaling for USDC/pUSD/conditional token positions; use integers/Decimal, not float for money. Include splits, merges, sales, redemptions, fees, position carry and incomplete-state bounds.
- Cross-chain transit: only follow Ethereum/Base/Arbitrum/Solana/TRON on a specific verified bridge order and its on-chain payout, **not** time/amount resemblance or Relay's HTTP request ID. Log chainId, transaction hash/signature, logIndex or instruction index, contract, token, exact units and ordering.
- Every asserted edge must be typed: DIRECT_VALUE, CONTRACT_INTERACTION, SAME_SERVICE, CORRELATED_TIMING, BRIDGE_ORDER_MATCH or UNKNOWN. Evidence confidence is separate from interpretation of wallet control.
- Controls must be matched for account age, market participation, notional, available markets, event timing and service exposure. Keep holdout period and control selection independent of observed profit.
- Outputs: immutable CSV/JSONL ledger, byte hashes of raw RPC/API/X records, completeness and pagination report, candidate identity ledger with dated provenance, before/after chart, test notebook/script, all p-values labelled exploratory when appropriate, and limitations.

## Reproducibility and integration gate

- Work in a **new isolated worktree/branch**. Preserve branch base SHA, freeze inputs, avoid modifying root README, MASTER_REPORT, METHODOLOGY, existing investigations' reports, evidence snapshots or other agents' branches.
- Prefer adding validated records under this directory (new evidence subdirectory). For candidate IDs, report DISPROVEN, UNRESOLVED, SUPPORTED, or CONFIRMED and exactly which test justifies each label.
- No synthetic transactions, guessed recipients, invented profit, fabricated RPC success, inferred owner or blanket “insider” accusation.
- Before publishing to main: deterministic replay with fresh cache, scripts/tests relevant to the changed files, diff inspection, secret scan, no changes to protected evidence. Open/update a reviewable PR; resolve conflicts without overwriting concurrent work.
- Technical uncertainty belongs in the research evidence and conclusions. Root promotional README changes are out of scope; if a future verified finding warrants them, create a **separate** scoped PR after review.
