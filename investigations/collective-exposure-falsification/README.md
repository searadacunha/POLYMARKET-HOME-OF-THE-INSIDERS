# Falsification of collective exposure shifts (mission 5 of 7)

Out-of-sample test of whether several wallets moving their real net exposure toward the same outcome in the same
hour (the collective-exposure detector of `investigation/collective-exposure-shifts`, PR #82) carries information
about the outcome beyond the price, public market information and single-wallet shifts.

**Verdict: `UNDERPOWERED`. No advantage is demonstrated, and its absence is not proven either.** On 1,234 fresh
TEST markets (724 collective units in 357 events), the collective features did not improve the forecast:
ΔLL(M1 → M3) = −0.0050 nats per unit, 95 % interval [−0.0110, +0.0008], one-sided p = 0.98. The matched
excess over non-collective units was +2.4 points, 95 % interval −1.0 to +5.8, p = 0.079. No test passes Holm.
The positive-control gate failed on power (G1), so only an effect of the strongest injected size is excluded.

The study was frozen before any hold-out label was read (`sources/PROTOCOL.lock`, 2026-11-17 14:01:31 UTC). It
does not modify PR #82 or any other frozen study.

## Contents

Snapshot of 2026-11-17. `sources/` is a copy of the study folder:
- `sources/FALSIFICATION_REPORT.md`: the full report, including power, the economic conclusion and deviations;
- `sources/STATISTICAL_RESULTS.json`: every number, with the sha256 of its source file;
- `sources/analysis_plan.md`, `sources/PROTOCOL.lock`, `sources/registre/`, `sources/amendements/`;
- `sources/controles/positive_controls.md` and `sources/audit/`.

Raw tapes (8.3 GB), panels and caches are not published. `data_manifest.json` lists every original file and
why it stays out; `local_only_hashes.sha256.gz` holds their hashes.

- [Status](STATUS.md)
- [Classified findings](FINDINGS.md)
- [Evidence and hashes](EVIDENCE.md)
