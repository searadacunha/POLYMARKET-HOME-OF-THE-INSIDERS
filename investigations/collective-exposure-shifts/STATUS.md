---
id: collective-exposure-shifts
title: Collective exposure shifts on Polymarket, tested out of sample
state: DONE
updated_utc: 2026-11-17T12:30:00Z
origin: /Volumes/VERBATIM HD/phi-x (working machine, collected tapes)
version: investigation/collective-exposure-shifts, after the replication run
---

## Objective

Test whether several wallets raising their net exposure to the same outcome inside one hour predicts that outcome
better than the price, and whether any such edge survives execution. The Iran / 28 February 2026 cohort only suggests
the hypothesis and is excluded from every rate.

## Actual state

Complete. Two runs of the same frozen rule on the same outcome-blind population:

- **Primary:** 763 markets (688 events), 1,518,240 fills, 129 collective alerts in 97 events, 16 of them in TEST.
  Every declared comparison null; verdict `INCONCLUSIVE` under the declared 30-alert rule.
- **Pre-declared replication (amendment 002):** 1,579 markets, 3,206,979 fills, 266 collective alerts in 197 events,
  **48 in TEST**. Verdict `NOT_SUPPORTED`: in TEST the alerted side won less often than its own price implied
  (−4.3 points), and the net result at 1 % slippage is negative in VALID and TEST (+1.7 / −4.5 / −5.3 points across
  TRAIN, VALID, TEST).

Also corrected here: the archived Iran tape is the newest 84 of 203 pages, so the published 20/36 and 16/733 become
35/36 and 27/733 (band) or 28/733 (full history) on the complete tape.

Three dated amendments document what changed and why: the excess-based group tests (001), the pre-declared
replication (002), and the within-market placebo after the calibration control fired (003).

## Final audit (2026-11-17)

`AUDIT.md`, `results/audit/final_audit.json`. All published numbers reproduce exactly from the tapes, labels and
population: the sample, the splits, the 0-mismatch label join, 395 alert prices, 1,963 wallet shifts, T1, T5, T7 and
both verdicts. A time-honest re-run (first firing instead of the largest candidate of a 6-hour block) moves the
replication excess from −1.6 to +0.7 points, and TEST from −4.3 to +1.2 points (CI −6.8 … +9.3). The verdict stays
`NOT_SUPPORTED`. Corrected claims are listed as A-01 to A-08 in that file: lookahead in alert timing, coexistence not
implemented, plan edited after the first results, T2 placebo not matched to S4, stale tapes2 manifest entry,
documented-case list not implemented, file times contradicting two amendment claims, and duplicate fill rows.

The follow-up steps of 17 November 2026 are included and checked in `AUDIT.md`: 1 (baseline audit), 2 (external
methods), 3 (position ledger), 4 (exposure signals, TRAIN only) and 6 (execution replay, hypothetical, no historical
book). Step 5 (falsification) was still collecting data and is neither included nor audited.

## Conclusions

- No excess over the price for collective exposure shifts: −0.23 point on the primary sample (p = 0.567) and
  −1.58 points on the replication (p = 0.745); TEST is negative in both (−0.2 and −4.3 points).
- No advantage over naive buy consensus, a single wallet's shift, a within-market placebo at the same price, or the
  variant that keeps two-sided wallets.
- Not executable: −0.0023 per share at zero cost on the primary sample and −0.0158 on the replication, with no
  break-even slippage in either. The historical order book is not archived, so these are gross readings.
- The verified 28 February figure (20/36) reproduces exactly, but rests on a censored tape.
- Financially linked collective shifts are UNRESOLVED, not refuted: no funding graph was built at this scale.

## Limits

- 129 alerts in 97 events, 16 in TEST: a small edge (under about 5 points) is not excluded.
- Fills only: splits, merges, redemptions and conversions are invisible, so exposure is an upper bound on inventory.
- No archived order book: entry price is the last executed price plus a declared slippage grid; fees and gas excluded,
  which makes the negative result optimistic.
- Markets of 1 M USD volume and above are excluded by the sample rule; that tail is where large coordinated positions
  would sit.
- The population inherits the 13 November 2026 exclusions without re-auditing them.

## Links

- README.md, analysis_plan.md, FINDINGS.md, amendements/001, amendements/002
- results/tests.json, results/tables.json, results/feb28_recheck.json, results/interval_reading.json
- research_notes/independent-forensic-audit-2026-11-08 (archived tape and audit)
- research_notes/early-detection-2026-11-13 (population and labels)
