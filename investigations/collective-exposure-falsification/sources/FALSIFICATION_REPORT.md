# Falsification and out-of-sample validation of collective exposure shifts (mission 5/7)

Date: 2026-11-17. Agent: Claude Code (Opus 5.5). Study directory:
`~/Projects/Polymarket-collective-falsification-20261117/`, raw tapes in
`~/Projects/Polymarket-collective-falsification-raw-20261117/` (backup state: section 14). Protocol frozen 2026-11-17 14:01:31 UTC, `PROTOCOL.lock` sha256
`fb2d486a7ac7dd3c9035a2ccc0c928c3a8318f66414a3899ca980567d477d7ee` (40 files). No economic edge is claimed here;
net profitability is mission 6.

## 1. Verdict

**H1, "a collective exposure shift carries information beyond the price and public market information":
`UNDERPOWERED`** (rule applied by code, `out/models/verdict.json`, sha256 `94f1c838…`).

**No advantage is demonstrated. Absence of an advantage is not proven either.** The positive-control gate failed
on power (G1: with the STRONG injection, detected in ≥ 98.8 % of injected markets, T1 rejected at the Holm threshold
in only 4 of 5 seeds) and the matched-excess
bound is too wide, so this study cannot rule out an effect of moderate size.

- The primary test does not reject. On the fresh TEST hold-out (724 collective units in 357 events), adding the
  collective features to price and public information made the forecast **worse**, not better:
  ΔLL(M1 → M3) = −0.0050 nats per unit, 95 % interval [−0.0110, +0.0008], one-sided p = 0.98.
- Corrected for the overfitting bias measured under the synthetic NULL controls (−0.0010), the one-sided upper
  bound of that improvement is +0.0010 nats, below the smallest effect of interest (0.002) under the declared
  max(event, wallet-cluster) rule. This bound is fragile. With the pigeonhole two-way bootstrap (event and wallet
  dependence together) the corrected bound is +0.0026 > 0.002. The bias estimate carries its own uncertainty
  (SE 0.0005 over 10 NULL seeds). Wallet dependence is strong (Kish effective n 68 wallet clusters vs 254 event
  clusters). So T1 alone is not read as proof that the effect is absent.
- The matched excess (T4) is **not** precise: collective units won 2.4 points more than matched non-collective
  units at the same price (p = 0.079 with the declared rule; 95 % interval −1.0 to +5.8 points from the same
  bootstrap; one-sided upper bound +5.3 points > 3). A narrower interval (+0.1 to +4.7) that seems to exclude zero
  comes from the COL-event bootstrap alone, which ignores the dependence created by reused controls; see section 4,
  "Why the T4 interval and p disagree". Residual imbalance on activity after matching (below) means this gap is not
  evidence of information either.
- Because the declared verdict requires both bounds, the overall status is `UNDERPOWERED`, not a precise
  negative. The control gate failed on power (G1), so `SUPPORTED` was unreachable by construction.
- M4 (collective shifts with financial relations observed at T): **IMPOSSIBLE**. Only 8 TEST collective units
  (11 in VALID) contained a pair of wallets linked by a direct USDC transfer or a common non-hub funder before the
  window; the declared minimum was 30. Funding coverage was complete (6,893 wallets, 0 errors). The FUNDLINK
  control shows the test would have detected such a link had it been frequent and informative (5/5 seeds).

What this does **not** show: that collective shifts never carry information. It shows that on 1,234 fresh TEST
markets with volume < 1 M USD the declared collective features did not improve on price plus public information,
and that an improvement of the size of the STRONG control (+0.036 nats) is excluded. As fixed before the freeze
(plan, pre-freeze change 6(ii)), the hold-out cannot exclude an effect of the MEDIUM size (+0.007): the controls
never detected it (0 of 5 seeds), so a non-rejection says nothing about it, whatever the T1 point estimate.

## 2. Population and selection (not built from winners)

| Set | Markets | Events | Role |
|---|---:|---:|---|
| TRAIN (h < 350, closed 2025) | 4,232 | 1,631 with units | fit, λ by event-grouped CV |
| VALID (h in [50, 350), closed H1 2026, events never read) | 2,572 | 1,418 | read once with TRAIN models |
| TEST (same, closed Jul–Oct 2026) | 1,234 | 725 | read once with TRAIN+VALID models |
| History only | 2,936 | | wallet history, never evaluated |

Source population: the 34,413-market universe frozen on 13 Nov 2026 (outcome-free rules). The hash band h < 50
read by the 16-Nov study (its TEST already seen) is never hold-out; every event holding an already-read market is
excluded from VALID/TEST; TRAIN events shared with the hold-out are purged; the Iran 28-February family (76 markets)
is excluded everywhere and the 36 cohort wallets never contribute. Coverage: every requested tape `ok` (no
`too_deep`, no error after one retry pass), 18.5 M new fills plus 3.2 M existing; Gamma metadata 10,973/10,974;
`endDate` known for 42,557 of 43,471 panel units.

Units (outcome-blind): R = random open grid times (Bernoulli 1/384 per 900 s grid time), PV = first price/volume
alert, IND = first single-wallet shift ≥ 3,000 USD, COL = first collective alert (mission 4 families F1–F5, F7, F8),
each per market, side and split window.

| Units | R | PV | IND | COL | total |
|---|---:|---:|---:|---:|---:|
| TRAIN | 14,027 | 4,682 | 996 | 2,594 | 22,139 |
| VALID | 8,976 | 2,991 | 383 | 1,622 | 13,881 |
| TEST | 4,967 | 1,605 | 194 | 724 | 7,451 |

## 3. Models compared (exactly M0–M4)

Nested L2 logistic regressions of the side's outcome; λ = 10 chosen by 5-fold event-grouped CV for every model.
M0 price (side-aware recalibration) · M1 + volume, volume ratio, price move, active wallets, fills, last-15-min
share, market age, hours to scheduled end, PV flag · M2 + largest single-wallet shift each side · M3 + collective
features (contributors, USD, concentration, habit surprise F3, young share F4, repeated pairs F5, repeated
lead/follow F7, flow-vs-price z F8) · M4 + direct link F6a, common funder F6b, funding coverage.

## 4. Results

Confirmatory family on TEST (Holm over 7). p = max(event-cluster, wallet-cluster bootstrap), 20,000 draws each.

| Test | Units (events) | Statistic | 95 % CI (event; T4: all events) | one-sided upper | p | Holm | Status |
|---|---|---:|---|---:|---:|---:|---|
| T1 ΔLL M1→M3, COL | 724 (357) | −0.00497 | [−0.0110, +0.0008] | ≈ 0 (+0.00003, MC SE 0.00008) | 0.980 | 1.00 | not rejected |
| T2 ΔLL M2→M3, COL | 724 (357) | −0.00278 | [−0.0081, +0.0024] | +0.0017 | 0.934 | 1.00 | NEGATIVE_PRECISE by the declared rule (see note) |
| T3 ΔLL M0→M3, all | 7,451 (591) | −0.00033 | [−0.0017, +0.0010] | +0.0008 | 0.702 | 1.00 | not rejected |
| T4 matched excess, COL | 693 matched (350) | +0.0242 | [−0.0103, +0.0583] (all events) | +0.0529 | 0.079 | 0.55 | not rejected |
| T5 ΔLL M3→M4, COL | 724 (357) | — | — | — | — | — | IMPOSSIBLE (8 linked units < 30) |
| T6 ΔLL M1→M2, IND | 194 (143) | −0.00239 | [−0.0097, +0.0048] | +0.0038 | 0.750 | 1.00 | UNDERPOWERED |
| T7 ΔLL M0→M1, PV | 1,605 (577) | +0.00037 | [−0.0021, +0.0028] | +0.0027 | 0.396 | 1.00 | UNDERPOWERED |

Tests rejected after Holm: **none** (0 of 7). BH: none. False positives cannot be counted on real data (no ground
truth); on synthetic data the NULL control rejected T1 in 0 of 10 seeds at p ≤ 0.05.

VALID (TRAIN-fitted models, reported, not part of the verdict except the sign condition): T1 +0.0007 [−0.0033,
+0.0045], p = 0.38; T3 +0.0014, p = 0.0026 (Holm 0.019); T7 +0.0021, p = 0.010 (Holm 0.062); T4 +1.23 points,
p = 0.13; T5 IMPOSSIBLE (11 linked units). The only VALID signal is public information (T3, T7), and it does not
replicate in TEST.

Wallet dependence: TEST T1 involves 911 distinct contributor wallets; no TEST unit holds a wallet active in ≥ 50
TEST events (4.0 % of VALID units do). The threshold is borderline: one wallet is active in 49 TEST events and sits in 55
of the 724 COL units (post-result audit), and the Kish effective n is 68 over wallet clusters against 254 over
event clusters. The sensitivity "without hyperactive wallets" therefore removes nothing in TEST. Event-only p for T1
0.949, wallet-cluster 0.980, pigeonhole two-way 0.898.

**Why the T4 interval and p disagree.** T4 has three bootstraps, and the plan reports the largest p and the largest
upper bound:

| Bootstrap | Resamples | one-sided p | 95 % interval | one-sided upper |
|---|---|---:|---|---:|
| (a) COL events | events of the COL units only | 0.018 | [+0.0010, +0.0466] | not stored separately |
| (b) all events involved | Poisson weights on the COL unit's event and every control's event | **0.079** | [−0.0103, +0.0583] | **+0.0529** |
| (c) wallet clusters | COL units grouped by their most recurrent wallet | 0.049 | [−0.0052, +0.0528] | +0.0490 |

(a) treats each control's outcome as fixed. Yet 2,209 of 3,357 control slots (3,357 is not stored in an output
file; it was recomputed independently by the post-result audit, which matched all stored T4 values) reuse a control, and each control
belongs to an event whose units share an outcome. (b) lets those control events vary, so it is wider. An earlier
draft printed the interval of (a) next to the p of (b): the interval seemed to exclude zero while p = 0.079. The
two now come from the same bootstrap. Interval (b) contains zero, as p > 0.05 implies. Neither changes the verdict:
the one-sided upper bounds of (b) and (c), +0.053 and +0.049, both exceed the +0.03 threshold.

The other confirmatory rows show the event-cluster interval. Their p is the larger of the event and wallet-cluster
p. For T1 the wallet-cluster bound (−0.0009) is lower than the event bound (≈ 0), so the reported bound is
the event one.

**T4 detail.** COL excess (win − price) +1.47 points, matched controls −0.95 points; 31 COL units unmatched; 2,209
of 3,357 control slots reuse a control. Balance after matching remains imperfect on activity: standardised mean
difference 0.53 for window volume and 0.40 for active wallets (2.89 and 2.47 before), 0.25 for cumulative volume,
0.23 for the 1 h price jump. The p components: COL-event 0.018, all-events 0.079, wallet-cluster 0.049.

**Calibration (TEST, all units).** The raw price is miscalibrated in this period: slope 0.744, intercept +0.068,
ECE 0.045, log loss 0.586 (VALID: slope 1.021, ECE 0.011). No model repairs it (M0–M4 slopes 0.746–0.750).
On COL units the M3 calibration slope is 0.878 versus 0.960 for M1: the collective features make the forecast
over-confident.

Note on T2: the declared rule compares the raw upper bound (+0.0017) with 0.002. Unlike H1, it does not subtract
the overfitting bias measured under NULL (−0.0010); with that correction the bound is +0.0027 > 0.002. T2 should
therefore be read as "no gain from collective over individual features, not precisely bounded".

**Activity-preserving null gate** (19 day-shift seeds on TEST, amendment 001, exploratory): T1 on the same
markets −0.00508; null T1 from −0.0083 to +0.0068 (mean −0.0018); 14 of 19 null seeds at or above the observed
value, p = 0.75 (`out/models/nullgate.json`, sha256 `66ef1b1f…`). The observed collective units forecast no better
than units built from wallets whose activity was shifted by whole days. The frozen `nullgate` stage refused 9
null-panel units whose TEST market had no observed unit (label lookup too narrow). Amendment 001
(`amendements/001-2026-11-17-nullgate-label-scope/`) widened only that lookup to the 1,234 TEST markets. It was
decided after TEST was read and cannot change the verdict, because `SUPPORTED` was already out of reach.

## 5. Controls and power (synthetic injections into real TRAIN tapes, before the freeze)

| Scenario | Seeds | T1 rejects at 0.05/7 | T1 p ≤ 0.05 | mean T1 ΔLL | detection | T5 rejects |
|---|---:|---:|---:|---:|---|---:|
| STRONG (s* = winner) | 5 | 4 | 5 | +0.0359 | 0.99 | — |
| MEDIUM (0.75) | 5 | 0 | 1 | +0.0067 | 0.99 | — |
| OLD (0.75, real old wallets) | 5 | 0 | 1 | +0.0086 | 0.98–0.99 | — |
| WEAK (0.60) | 5 | 0 | 0 | −0.0013 | 0.99–1.00 | — |
| NULL (0.50) | 10 | 0 | 0 | −0.0010 | 0.99–1.00 | — |
| FUNDLINK (link only when s* wins) | 5 | 0 | 0 | −0.0006 | 0.99–1.00 | 5 |
| PERMUTED labels | 1 | 0 | 0 | −0.0017 | — | — |

Gate: G1 (STRONG rejects in every seed) **failed** (4/5, STRONG_3 p = 0.0094); G2 detection, G3 NULL silence, G4
permuted silence passed. Benjamin decided, before any VALID/TEST label was read, to freeze and evaluate anyway.

## 6. Sensitivity of T1 (TEST, event bootstrap 5,000, reported only, 18 registry lines)

All variants keep a negative or near-zero estimate: F1 only −0.0011 (173 units), F2 only −0.0107 (43), score ≥ 2
−0.0070 (514), score ≥ 3 +0.0035 (181, p = 0.27), price 0.10–0.80 −0.0065 (474), ≥ 24 h before end −0.0074 (593),
closed on schedule −0.0033 (307), without hyperactive wallets −0.0050 (no wallet reaches 50 TEST events, so this
variant is identical to the main estimate), λ 0.1 / 1 / 10 / 100: −0.0053 / −0.0053 /
−0.0050 / −0.0036, leave-one-group-out: F3 −0.0026, F4 −0.0048, F5 −0.0050, F7 −0.0043, F8 −0.0047, size
features −0.0023. No variant has p < 0.27.

## 7. Multiple testing and registry

`registre/tests.jsonl`: 33 lines on real data, all after the freeze: 7 VALID, 7 TEST confirmatory, 18 TEST
sensitivity lines (exploratory by declaration), and 1 null gate (exploratory, outside the frozen code). There are
151 synthetic control lines, counted apart. Bonferroni over all 33 real comparisons: 0.05/33 = 0.0015. No real p
is below 0.0026 (VALID T3), so nothing survives that correction either. Confirmatory family: 7 tests (Holm). Registry chain verified intact; every VALID and TEST line is
after the freeze, VALID (14:02:14) before TEST (14:02:39), each test once.

## 8. Independent checks

- Blind pre-freeze audit (43 agents, `audit/pre_freeze_audit.md`): 50 findings; every blocking and major finding
  fixed or declared before the freeze.
- Post-result recomputation by two independent agents (workflow `wf_8472e3a6-627`) from the frozen inputs with their
  own code: T1, T2, T3, T6, T7, T4, unit and event counts and the raw-price log loss all match to < 1e-16.
- Integrity agent: `gel.py verifier` intact, registry chain intact, order and single reading of VALID/TEST
  confirmed.
- Two post-result audits (`audit/post_result_audits.md`):
  - **Statistics:** every computation passed; ten wording issues were corrected in this report.
  - **Temporal leakage:** no leak found. Truncation tests on 10 hold-out TEST markets and F3/F4 rebuilt at t
    show 0 differences. The selection by close date does not drive T4.

## 9. Deviations and data notes

1. Pre-freeze changes and their reasons are listed in `analysis_plan.md` ("Pre-freeze changes" 1–6), including a
   change of the decision p (pigeonhole two-way → wallet-cluster) made after seeing synthetic controls, and the
   failed gate G1 with Benjamin's decision.
2. Plan wording vs code, found by the recomputation agents: "log hours since first fill" and "log market age" are
   `log1p` in the code (using `log` changes T1 in the 6th digit and T4 from +0.02417 to +0.02408); the order of M3
   features and the handling of a zero volume ratio and of a negative time-to-end (clipped at 0) are fixed by the
   code, not by the plan text.
3. `sensitivity_test.json` shows `p_twoway: null` in the line `event_only_vs_twoway_T1`: it reads a key renamed by
   pre-freeze change 5. The value is in `results_test.json` (`tests.T1.twoway_pigeonhole.p` = 0.898).
4. VALID units of 27 events that also hold TEST markets: 310 units purged from the refit.
5. `ctl_40_inject.py` reads TRAIN labels (synthetic controls only).
6. Amendment 001 (null gate label lookup, after TEST was read, exploratory): see section 4.
   The null panels hold fewer COL units (346–406) than the observed TEST panel (689 on the same markets), so the
   null spread includes extra sampling noise and p = 0.75 is a weak comparison.
7. Plan wording vs code (post-result audit): the plan says "a unit without a wallet is its own cluster"; the code
   puts such units in an event-level cluster (`e:<event_id>`). No effect on T1/T2/T4 (every COL unit has a wallet).
   For T3 and T7 the plan's reading gives p 0.705 and 0.398 instead of 0.702 and 0.396; no status changes.
8. The null seeds 18 and 19 were interrupted when a session ended (`out/null_18/` empty, no `stats.json`). They
   were re-run alone with the frozen command. Seeds 1–17 were kept: each `stats.json` records the frozen
   `feat_30_detect.py` sha256 (`076ff73c…`), the frozen parameters (`37677ff8…`), its seed and the split TEST.

## 10. Limits

Fills only (no splits, merges, conversions); closed markets only, with early-YES over-representation in the close
windows; `endDate` as fetched in November 2026; wallet history limited to the collected band; no order book; markets
≥ 1 M USD excluded; funding window = first 100 ERC-20 transfers per wallet; controls on a TRAIN-only pool; the
day-shift null also scrambles the price path. Power: only an effect of the STRONG size is reliably detectable.

## 11. Reproduce

    cd ~/Projects/Polymarket-collective-falsification-20261117
    sh code/run_all.sh check        # tapes outside the study match derived/tapes_sha256.txt
    sh code/run_all.sh base         # detector + panel (≈ 6 min)
    sh code/run_all.sh funding      # Etherscan, cached
    sh code/run_all.sh controls; sh code/run_all.sh ctlsummary
    sh code/run_all.sh train; sh code/run_all.sh valid; sh code/run_all.sh test   # one-shot guards
    sh code/run_all.sh nulls
    python3 -I amendements/001-2026-11-17-nullgate-label-scope/nullgate_label_scope.py nullgate \
        --panel out/base/panel.jsonl.gz --labels data/labels.jsonl.gz --holdout derived/holdout_markets.jsonl \
        --out out/models --null-panel out/null_1/panel.jsonl.gz ... --null-panel out/null_19/panel.jsonl.gz
    sh code/run_all.sh verdict; sh code/run_all.sh assemble

Raw tapes: `~/Projects/Polymarket-collective-falsification-raw-20261117/` (8.3 GB, hashes in
`derived/tapes_sha256.txt`). Results: `STATISTICAL_RESULTS.json` (assembled, with the sha256 of every source file).

## 12. Power: what this study can and cannot say

- **G1 failed.** In the synthetic controls, an injection where the collective shift is always on the winning side
  (STRONG, mean mock-test ΔLL +0.036) rejected at the first Holm threshold in 4 of 5 seeds (all 5 at p ≤ 0.05).
  MEDIUM (+0.007), OLD (+0.009) and WEAK rejected in 0 of 5. The NULL control was silent (0 of 10 at p ≤ 0.05),
  and so were the permuted labels (p = 0.88). The test is valid but has little power below the STRONG size.
- **What the data exclude.** On TEST, the one-sided 95 % upper bound of T1 is ≈ 0 nats (+0.0010 after the
  overfitting correction), more than 30 times below the STRONG effect. A gain of the size the controls can detect is
  ruled out for these markets.
- **What the data do not exclude.** A MEDIUM-size effect (+0.007 nats) lies above the T1 bound but was never
  detected in the controls. The matched comparison (T4, +2.4 points, upper bound +5.3) leaves room for a few points
  of excess. **No advantage is demonstrated. This is not a proof that collective shifts carry no information.**
- **Out of reach here.** Funding relations (M4/T5: 8 linked units, 30 needed); markets of ≥ 1 M USD volume; any
  execution claim.

## 13. Economic conclusion

**No tradeable edge is demonstrated.** Mission 5 finds no out-of-sample predictive gain from collective features
over price and public information. The only positive sign (T4, +2.4 points over matched controls) is not
significant (p = 0.079 after the declared rule, Holm 0.55). It is not robust either: activity was still
imbalanced after matching (window-volume SMD 0.53), and on T1 the null gate shows no excess over shuffled alignment.
The figures of this paragraph do not come from this study's files and were not re-checked by its audits.
Mission 6 (`investigations/collective-exposure-shifts/execution/out/EXECUTION_RESULTS.json` on branch
`investigation/collective-exposure-shifts`, PR #82) simulated the 16-Nov detector's alerts from executed trades.
It found −0.8 % per USD in TEST (95 % interval −21.8 % to +19.3 %, 48 alerts, 22 events), with the historical
execution `UNVERIFIABLE` (no archived order book) and a verdict of `NO_DEMONSTRATED_EDGE`. A gap of 2–5 points
would also have to survive taker fees (0.04 on politics since 30/03/2026, 0.05 on culture) and the visible depth
(median ~80 USD in TEST). Nothing here supports trading on collective exposure shifts.

## 14. Backup state (2026-11-17, checked 14:50–15:10 UTC)

- The continuous backup `phi-backup` does **not** yet hold this study. Its `BACKUP_STATUS.md` (14:28 UTC) lists
  `Polymarket-collective-falsification-20261117` with 22,229 of 22,232 files waiting and
  `Polymarket-collective-falsification-raw-20261117` with 0 of 5,982 packed. Every `backup` pass since at least
  12:52 UTC has failed with `KeyError: 'Polymarket-early-detection-raw-20261113'` (728 `pass_failed` events in
  `~/.local/state/phi-backup/events.jsonl`). The phi-backup tool was not modified by this mission.
- A direct copy was made instead and checked file by file with SHA-256 (`BACKUP_VERBATIM.md`): 7,030 of 7,030 raw
  files and 22,337 of 22,337 study files verified, after one failed archive was rebuilt. There is still no off-site
  copy.
- The folder `/Volumes/VERBATIM HD/phi-x/investigations/collective-exposure-shifts/falsification/` holds only the
  first, pre-audit scripts and population files written before macOS revoked access to the disk (12:05–12:13 UTC).
  It is **not** a copy of this study, contrary to what earlier drafts said.

