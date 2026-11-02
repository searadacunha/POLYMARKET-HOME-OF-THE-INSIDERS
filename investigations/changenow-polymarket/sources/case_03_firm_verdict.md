# DECISION REQUEST — give a FIRM, defensible verdict (no fence-sitting)

You previously designed the methodology. I executed it on live Polygon data. The operator now
demands a FIRM answer to ONE question, not more hedging:

  **"Are the identified Polymarket wallets actually funded via ChangeNOW (CN) — yes or no?"**

A "firm" answer does NOT mean false certainty. It means: commit to the most defensible verdict
the evidence supports, state it plainly, give the per-wallet confidence band you will stand
behind, and name the SINGLE most decisive additional on-chain test that would move a QUALIFIED
verdict to a FIRM-YES (so I can run it). Weigh ALL evidence below adversarially.

## THE ATTRIBUTION CHAIN
wallet_PM  ⟵ (ERC-20 stablecoin payout)  f2020  ⟵ (funding)  {ChangeNOW + other sources}
The certain link is wallet⟵f2020. The contested link is f2020 = ChangeNOW.

## MEASURED EVIDENCE (all on-chain / verified this run)

### About f2020 (0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423)
- OUTBOUND (payouts): 11,185 stablecoin transfers to **3,408 distinct recipients**, full life
  2026-04-14 → 2026-06-22, median payout ~$27 (retail fan-out = swap-payout signature).
- INBOUND (funding): **$8.38M from 7,006 distinct funders**. Breakdown:
  - **25.0% from labeled "ChangeNOW 22"** (0x4958…bd0a, PolygonScan name tag).
  - **42% ($3.55M) from 0x254aa3a8** = a CONTRACT with diverse unlabeled counterparties
    (settlement/router-like, NOT CN-labeled, no CN counterparties in its top flows).
  - remaining ~33% spread across a long tail of thousands of small funders.
- f2020 is NOT publicly labeled ChangeNOW (only a weak OSINT post says "Changenow most likely").

### Ground-truth anchor (strongest single piece)
- The operator (Benjamin) previously did a CONTROLLED ChangeNOW test swap. Its payout to his
  Polygon deposit wallet came **FROM f2020** (verified on-chain: f2020 → $8.83 on 06/04 +
  $8.12 on 06/10), funded two levels up by 0x4958 = labeled "ChangeNOW 22". So a KNOWN CN swap
  was demonstrably paid out of f2020. (That same prior analysis flagged attribution as
  "plausible, ceiling" because f2020 is commingled.)

### Labeled CN addresses behavior
- The 6 PolygonScan-labeled CN addresses (Hot Wallet 1/2, CN6, CN16, CN18, CN22) have ~ZERO
  retail stablecoin fan-out on Polygon EXCEPT CN22 (which is internal consolidation, only ~4
  recipients). So ChangeNOW does NOT pay end-users directly from its labeled wallets on
  Polygon — payouts are routed through unlabeled hot-wallets like f2020.

### Batch result (this run)
- Of f2020's 3,408 recipients, those with verified Polymarket activity (data-api /activity):
  **~88 so far (batch ~55% done, projecting ~150-180 final) PM bettor wallets** (out of 1712 checked), total
  CN→ those wallets ≈ $(finalizing). Most are retail-sized; categories skew crypto
  Up/Down + sports + misc (consistent with general CN users, not a coordinated insider fleet).

## THE TWO COMPETING HYPOTHESES (decide between them)
- **H1 — f2020 is a ChangeNOW-dedicated payout hot-wallet.** Then every retail payout f2020→user
  IS a CN payout, and these wallets ARE CN-funded. The mixed INBOUND is just CN refilling its
  hot wallet via treasury/bridging/market-making (need not be labeled). Supported by: test-swap
  ground truth, CN22 coupling, payout signature, labeled-wallets-don't-pay-retail.
- **H2 — f2020 is a multi-tenant settlement hub** serving several services. Then only SOME
  f2020→user payouts are CN; "CN-funded" is base-rate, not specific. Supported by: 7,006
  funders, 42% from a non-CN settlement contract, not CN-labeled, "shared infra" prior.

## WHAT I CANNOT DO (state honestly in the verdict)
- Per-dollar provenance tracing through f2020 is impossible (commingling). So I can argue about
  f2020's ROLE, not trace a specific deposit to a specific payout.

## DELIVERABLE
1. FIRM VERDICT: H1 or H2 (or a precise mixture, e.g. "H1 with an estimated X% non-CN false-
   positive rate"). One paragraph, committed.
2. The per-wallet confidence band you will stand behind for "this wallet is CN-funded" on the
   direct-Polygon/f2020 rail, with the reasoning.
3. THE decisive next on-chain test (single most informative) to move QUALIFIED → FIRM-YES, that
   I can run with: Etherscan V2 (txlist/tokentx/internal/receipt logs), Polygon RPC, Helius
   (Solana), Polymarket data-api. Be specific enough to implement.
4. Any false-positive filter I should apply to the wallet list NOW to make the verdict tighter.
Be decisive. The operator is tired of "it depends."
