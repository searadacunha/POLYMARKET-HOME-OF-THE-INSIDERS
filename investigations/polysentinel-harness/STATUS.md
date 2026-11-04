---
id: polysentinel-harness
title: Recovery harness for PolySentinel
state: PAUSED
updated_utc: 2026-11-04T18:59:47Z
origin: ~/Projects/PolySentinel-harness
version: git 4f9c66f, branch harness/autonomy, baseline 86109b9; full history in results/harness_history.bundle
---

## Objective

Keep an investigation going across crashes and restarts, and admit a result only after an independent process has recomputed it from raw rows.

## Actual state

Not installed. Its author's verdict: do not install it before the reduced mode is resolved, a supervised run on real data has happened and a retention policy exists.

## Conclusions

Recovery is shown on synthetic data and a demo launchd job, never end to end on real data.

## Limits

No real restart of the Mac, no multi-day run. No ground truth: synthetic results show mechanics, not detection.

## Links

Depends on the code of `polysentinel`: identical files point there through `duplicate` entries in the manifest.
