# Amendment 001 — collection-date horizon

**Written:** 19 November 2026, after the frozen reference positive control reproduced PR 27 (37 censored wallets, S1 = 17, groups 9, 4, 2, 2) and after comparator trade tapes were collected, **before any comparator exit statistic, class, or p-value was computed**.

## Why this amendment exists

The frozen plan allows collection until 22 November 2026 23:59 UTC. This execution is inside that window, on 19 November 2026. Reference Relay pages stay the archive fetched on 5 November 2026. Comparator pages are read live on 19 November 2026. A comparator can therefore show withdrawals that did not exist when the reference pages were archived. That asymmetry was not a free parameter of the original plan; it is a consequence of running the collectors later than 6 November.

## What does not change

`analysis_plan.md`, `PROTOCOL.lock`, and every file named in that lock stay byte-for-byte identical. `code/ana_50_stats.py` remains the only primary analysis. Its verdict is the pre-registered classification. This amendment does not retune M, the permutation count, the service threshold, the population rule, or the verdict cut points.

## Sensitivity `S_INDEX_HORIZON` (exploratory)

Recompute each comparator wallet's recipient set from the reduced orders already stored by `col_30_relay.py`, keeping an order only when its `created` timestamp is less than or equal to **2026-11-05T23:59:59Z** (the reference archive day).

- Classes are **not** recomputed. A 5 November popularity index cannot be reconstructed from the 19 November Relay responses. Recipients use the classes of the primary `data/classes.json`.
- The same degree-preserving test, power rule, and verdict function are called on comparators. The seed key is `condition + "|index_horizon"`.
- The reference archive is not re-permuted. After checking that every archived reference order is already on or before the cutoff, the sensitivity reuses the primary reference result. A new seed on an unchanged reference graph would move p only by Monte Carlo noise.
- A population that the primary analysis marks exit-incomplete stays incomplete. Truncation at 100 Relay pages is not repaired.
- The sensitivity cannot replace the primary verdict. If the two classifications differ, both are reported and the difference is an unresolved robustness limit.
- Because the executing script is not in `PROTOCOL.lock`, the study registry forces the line to `declare_dans_plan: false`. That is the conservative label, even though this text was written before the comparator exits were scored.

## Explicit non-claims

This sensitivity is not a point-in-time trading alert, not a test of non-public information, and not a claim of common ownership. Lifetime Relay withdrawals, even when cut at 5 November 2026, are still not features that were required to be observable at each market's shock time T.
