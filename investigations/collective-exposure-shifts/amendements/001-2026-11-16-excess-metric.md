# Amendment 001 — 2026-11-16 — group comparisons on excess, bootstrap p-values

**Status: adopted. Written before any replication sample was collected and before any verdict was published.**

## What was observed first

The primary sample (763 markets) was run once with the frozen plan. Two defects appeared in the *outputs*, not in the
data:

1. The label join compared `"YES"` to `"Yes"` and scored every alert as a loss, including the matched placebo. The
   placebo control caught it (0 % win rate against a 63 % mean price). Fixed in `scripts/score.py`, with a control
   that now refuses a placebo whose win rate is more than 15 points from its mean price.
2. Tests T2, T3, T4 and T6 compared **raw win rates** between signal families. Those families do not trade at the same
   prices: S2 (naive buy consensus) fires at a mean price of about 0.60 while S4 fires at about 0.72. A raw-rate
   difference therefore measures price composition, not edge. In the S4-versus-S2 case this produced an apparent
   p = 2.2e-05 in the *wrong* direction, from a comparison that cannot answer the question.

## What changed

- T2, T3, T4, T6 now compare **excess** (`win − price at the alert`), which is the edge over the market's own price.
  Raw rates are still written to the results for the record (`raw_rate_diff`).
- Their p-values now come from the **event-clustered bootstrap** (one-sided, share of resampled differences ≤ 0)
  instead of a binomial on raw rates. T1 and T7 (calibration against the price) are unchanged.
- T5 (net payoff) is now computed on the same event-clustered resampling.

## What did not change

Thresholds (500 USD per wallet, 3,000 USD total, 3 wallets, 60-minute window, price band 0.05–0.90, 60 % maximum
share), the sample rule, the population, the chronological splits, the slippage grid, the seed, the decision rule and
the exclusion of the Iran cohort. No alert was added, removed or re-timed.

## Effect on the verdict

None. Under v1 the calibration tests T1 and T7 were already null, and they are the ones that decide the verdict.
Under v2 the group tests also come out null. The correction removes a spurious positive, it does not create one.
