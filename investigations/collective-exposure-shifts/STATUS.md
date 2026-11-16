---
id: collective-exposure-shifts
title: Collective exposure shifts on Polymarket, tested out of sample
state: IN_PROGRESS
updated_utc: 2026-11-16T21:55:00Z
origin: /Volumes/VERBATIM HD/phi-x (working machine, collected tapes)
version: investigation/collective-exposure-shifts, first commit
---

## Objective

Test whether several wallets raising their net exposure to the same outcome inside one hour predicts that outcome
better than the price, and whether any such edge survives execution. The Iran / 28 February 2026 cohort only suggests
the hypothesis and is excluded from every rate.

## Actual state

The primary sample is complete: 763 markets (688 events) sampled by hash of the condition id, 1,518,240 executed fills,
762 scored, 816 primary alerts (129 S4 collective shifts in 97 events, 392 naive-consensus, 166 single-wallet, 8,132
matched placebo points). Every declared test is null; the gross result per share is negative at zero slippage.

The pre-declared replication (amendment 002, `hash mod 1000 < 50`, 1,579 markets) was launched and is
**partially collected** at the time of this commit; it is the only open item, and its state is recorded in
`results/replication_state.json`. It cannot change the primary readings, only the power of the TEST split.

Also fixed here: the archived Iran tape is the newest 84 of 203 pages. On the complete tape the archived contrast
becomes 35/36 cohort and 27/733 comparators (band) / 28/733 (full history), instead of 20/36 and 16/733.

## Conclusions

- No excess over the price for collective exposure shifts: −0.23 point on 129 alerts (p = 0.567), −0.21 point in TEST
  (16 alerts, p = 0.625).
- No advantage over naive buy consensus (−0.56 pt, p = 1.000), over a single wallet's shift (+3.08 pt, CI −2.5…+8.9),
  or over the matched placebo (−2.69 pt).
- Not executable: −0.0023 per share at zero cost, −0.0123 at 1 % slippage, negative in all three splits, and no
  break-even slippage. The historical order book is not archived, so this is a gross reading, not a fillable one.
- The verified 28 February figure (20/36) reproduces, but rests on a censored tape.
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
