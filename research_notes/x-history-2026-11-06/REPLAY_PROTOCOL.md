# Historical-intelligence replay protocol (frozen input, no outcome-based cohort selection)

## Inputs / authority

1. Source dossier: user-provided `rapport-polymarket.txt` dated 6 Nov 2026. This PR imports its **reported** X observations, not an independently fetched X response corpus.
2. Primary X objects: archived author ID, post ID, created_at, edit_history_tweet_ids, full text, entities, quoted/replied post IDs, media hashes, URL and original timezone. Preserve all fetched pages (including zero-result queries), pagination and rate-limit logs. Do not replace failed lookups with negative evidence.
3. Existing on-chain baseline: main commit `17acd3409382201dfb6fc0d43a30d4208952eb02`, plus PR27–32 only when their actual head commits are explicitly recorded. Read README, MASTER_REPORT, METHODOLOGY, both Ballon d'Or findings/reports, maduro-iran phase2 and relevant PR reports. Never silently treat unmerged PR data as main.
4. Independent public result: UEFA's 26 Oct 2026 top five (linked in REPORT.md). Keep date of publication separate from event date.

## Fixed questions and stop conditions

**Q1 — Ballon d'Or public diffusion.** Does the full top-five text occur in the original Oct 16 Cypya post (or an edit prior to market openings)? Falsify the claim if the archived original does not say all five in that order, or if edits postdate the relevant market openings. Require full API text plus edit provenance; a valid X ID alone proves neither.

**Q2 — Before-vs-after fills.** Among all eligible market participants (not just winners), which outcomes and positions were available/traded before Oct 16 17:38:26 UTC, between that event and market launches, and afterward? Freeze exact outcome tokens and market IDs from Gamma, not from the winning final rank. Compare pre-/post-signals and identical-shift placebo cutoffs, controlling for liquidity, market price and participant activity.

**Q3 — Copies and independent traders.** Does the account described by @Jydyjyd follow the observed leaders, or does any alleged follower systematically predate them? No X-to-wallet assumption without an explicit, dated mapping; the Cypya/Jydyjyd profile addresses are **candidates only**. If mapping fails, stop person-level inference, retain market-wide diffusion tests.

**Q4 — Maduro/Iran candidates.** For PURE698 and JamWil23, verify account identity and complete Polygon fills, deposits, withdrawals and settlements from 2025-03-01 to 2026-02-28. Check Israel–Iran June 2025 against each other Iran/Maduro market by exact conditionId/tokenId; include losing/missing expiries. Refute the alleged cross-event continuity if no earlier Iran exposure exists for the same verified address.

**Q5 — Group G and alleged 38 accounts.** Extract source-linked unique proxies and check all claimed payments to `0xc5bB1Be0407db7312911ec765D399D02461e411a`. Compute intersection and differences versus G (4), E, and the Maduro/Iran eight-account group. Test pooled deposit-service hypotheses with fan-in/fan-out and matched service recipients. Do **not** claim 38 controlled wallets until 38 distinct addresses plus discriminating links and an alternative-service test exist.

**Q6 — cashy, flydartball and negative controls.** Link tweets to receipts via calibrated bot lag; measure actual fill time, fill type (maker/taker), inventory and realized + remaining value. Include every failed expiry, negative-control alerts and all periods. Do not treat volume or withdrawn cash as profit.

**Q7 — Media census discrepancy.** Reconcile press claims of 12 accounts versus the existing 11-account audited cohort by explicit profile and wallet mappings. The numerical difference alone is not evidence of an omitted account.

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
