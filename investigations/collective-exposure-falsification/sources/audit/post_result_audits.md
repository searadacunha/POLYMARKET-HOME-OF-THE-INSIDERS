# Post-result independent audits (2026-11-17, after TEST was read)

Two independent agents, read-only, with their own scripts in temporary directories. Neither modified the study.

## 1. Statistical verification (stats-auditor): PASS on every computation, FAIL on wording (fixed)

| Item | Result | Independent values |
|---|---|---|
| T1 point value, bootstraps | PASS | ΔLL −0.004973733 (724 units, 357 events); event p 0.9496, wallet-cluster p 0.9795 (reported 0.9490 / 0.9802, within Monte-Carlo error) |
| Holm over 7 | PASS | only T4 below 1 (0.554); no rejection |
| Null gate | PASS | same 43 skipped markets in every seed; observed −0.0050759 on 689 units; 14 of 19 seeds ≥ observed; p = 0.75 |
| Verdict rule | PASS | H1 = UNDERPOWERED (T1 corrected bound 0.00101 < 0.002 but T4 bound 0.0529 ≥ 0.03); T2 NEGATIVE_PRECISE by the rule, not after bias correction (0.00267) |
| Report numbers | FAIL → fixed | no wrong number; wording issues listed below |

Wording issues raised and how `FALSIFICATION_REPORT.md` was corrected:

1. "Taken alone, T1 is a precise negative" read as proof of absence. Rewritten: the bound is fragile. With the
   pigeonhole two-way bootstrap the corrected bound is 0.0026 > 0.002, and the bias SE is 0.0005.
2. Contradiction on the MEDIUM effect. Aligned with the reading fixed before the freeze: MEDIUM is not excluded.
3. T4 interval from the COL-event bootstrap only. Replaced by the interval of the bootstrap that sets the p, with an
   explanation.
4. 3,357 control slots not in any output file. Recomputed by the auditor (exact match); stated as such.
5. Hyperactive-wallet threshold borderline (one wallet in 49 TEST events and 55 COL units; Kish n 68 wallet
   clusters vs 254 event clusters). Stated; the "without hyperactive wallets" variant is flagged as identical.
6. "detected in 4 of 5 seeds" wrong. Detection ≥ 98.8 % in all 5 seeds; T1 rejected in 4 of 5.
7. Mission 6 figures not in this study's files. Flagged as coming from PR #82 and not re-checked.
8. Plan vs code on clusters for units without a wallet. Added to the deviations: no status change (T3 p 0.705 vs
   0.702, T7 0.398 vs 0.396).
9. Null panels hold fewer COL units (346–406 vs 689). Stated: the null gate is a weak comparison.
10. T1 upper bound +0.00003 below its Monte-Carlo SE (≈ 0.00008). Reported as ≈ 0.

Real comparisons in the registry: 33 lines (31 with a p); Bonferroni 0.05/33 = 0.0015; smallest real p 0.0026.

## 2. Temporal leakage audit (leakage-auditor): no leak found

| Item | Status | Evidence |
|---|---|---|
| Features use fills ≤ t | OK | truncation test on 10 hold-out TEST markets (2,000–60,000 fills), 3 cuts each: 1,197 extras rows, 835 candidates and 104 PV/IND flags identical with and without the data after the cut |
| Phase-B features (F3–F7) | OK | F3, F4 rebuilt from tapes cut at t for 40 TEST COL units (81 wallets): 0 difference; F5/F7 checked in code |
| Unit selection, `closed_ts`, `endDate` | OK / declared limit | 0 units outside their split window or after close; R draws lost at the grid end: 0 in band in TEST; `endDate` shows no sign of after-the-fact edits in TEST |
| Splits and purge | OK | 0 shared events TRAIN–VALID, TRAIN–TEST, history–TEST; 310 VALID units of the 27 VALID/TEST events purged from the refit; labels only in `ana_50` (and TRAIN-only in `ctl_40`) |
| Hub status from the whole funding window | declared limit | recomputed as of t − W: F6b changes for 1 of 4,218 COL units (VALID), none in TEST |
| Amendment 001 | OK | TEST labels only; verdict reads the null gate only if T1 is rejected |

Minor, no impact: a transaction whose rows carry different timestamps marks its earlier rows UNKNOWN (2 groups
in the hold-out tapes, outside the TEST window). The selection by close date does not drive T4: dropping the
markets that closed before their `endDate` raises T4 slightly (+0.027 without them). The auditor also read TEST
and TRAIN labels for these exploratory splits; nothing was written to the registry.

Not checked by either audit: T4's three bootstraps (statistic and matching re-run only), calibration recomputed
independently, VALID recomputation, sensitivity refits, F5/F7 recomputation, tag edits after resolution, the
60 s publication latency, truncation on markets above 60,000 fills.
