# Amendment 003 , 2026-11-16 , placebo drawn inside the alert's own market

**Status: adopted. Written after the replication control fired and before the corrected T2 values were computed.**

## What the control reported

`scripts/score.py` refuses a matched placebo whose win rate is more than 15 points from its mean price. On the
expanded replication sample it reported placebo win rate 0.802 against mean price 0.638.

## Diagnosis

The placebo pool was built across markets: every 10-minute bucket of every sampled market was one entry, so markets
with a long life and heavy trading contributed thousands of entries and short markets almost none. Long-lived markets
drift: a bucket drawn uniformly in their life is early, priced low, and still wins when the market later resolves the
same way. The pool therefore over-samples low prices that resolved favourably, which inflates the placebo win rate
without any error in the label join. The primary sample (763 markets) passed the control by luck of composition.

The defect is in the comparator's sampling, not in the alerts and not in the outcome join.

## What changed

- The placebo point for an alert is now drawn **inside the alert's own market**: same side, price within the same
  ±0.05 band, at a uniformly random 10-minute bucket at least 6 hours away from the alert. The seed stays 20261116.
- This measures the intended thing: at the same market and at the same price, does the shift pick a better moment than
  a random moment? It removes market composition entirely.
- T2 is recomputed on both the primary sample and the replication.

## What did not change

Signals, thresholds, sample, splits, the other tests, the decision rule and the verdict logic. T2 remains one of the 10
declared comparisons and is still corrected with Bonferroni and Benjamini-Hochberg.

## Effect on the verdict

None. T2 was null on the primary sample under the cross-market pool (−2.69 pt, p = 1.000) and the corrected comparator
is the stricter one. The verdict is decided by T7 (calibration in TEST), which this amendment does not touch.
