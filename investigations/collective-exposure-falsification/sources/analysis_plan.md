# Analysis plan, mission 5/7: falsification and out-of-sample validation of collective exposure shifts

Study id: `collective-exposure-falsification`. Plan version 1 (final pre-freeze text), written 2026-11-17 by Claude
Code (Opus 5.5), **before any VALID or TEST label of the hold-out was read and before any model was scored on
VALID or TEST.** Every later change is a dated amendment in `amendements/`; anything decided after results is
exploratory. Changes made before the freeze, and why, are listed at the end ("Pre-freeze changes").

## Question

Does a **collective** change of real economic exposure (several wallets moving their net exposure toward the same
outcome in the same window: mission 4 detector on the mission 3 point-in-time ledger) carry information about the
outcome **beyond the price and beyond public market information** (volume, price move, market-level activity,
scheduled deadline), and beyond **individual** shifts?

The plan tries to destroy that hypothesis. A null result is classified as a precise negative, insufficient power,
or an impossible test. No economic edge is claimed: net profitability belongs to mission 6.

## What already happened (why a new hold-out is needed)

- The 16-Nov study (`investigation/collective-exposure-shifts`, tip `b4b9c8e`) evaluated its S4 rule on the markets
  with `h = int(sha256(condition_id)[:8],16) % 1000 < 50`, VALID and TEST included. Verdict `NOT_SUPPORTED`. Those
  VALID/TEST markets have been seen: they are **never** used as hold-out here (history only).
- Mission 4 (`exposure-signals/`, TRAIN only, h < 50) set the detector rules on TRAIN; its preliminary TRAIN table
  showed no family above the price. TRAIN results are known to the author of this plan; hold-out results are not.

## Data

- Population: `research_notes/early-detection-2026-11-13/study/derived/universe_markets.jsonl.gz` (origin/main
  `0d79ba6`, 34,413 markets, inclusion rules frozen on 13 Nov 2026). Labels: `labels.jsonl.gz` of the same study
  (`data/labels.jsonl.gz`, sha256 `97d4ea90…`, `winner` ∈ {YES, NO}; any other value stops the run).
- Market sets (`code/col_10/11/12_*.py`, run before any tape of these markets existed):
  - **TRAIN** = h < 50 TRAIN markets (623) + h in [50, 350) TRAIN markets (`train_ext`, 3,609; events shared with
    the hold-out purged).
  - **VALID** (2,572 markets, 1,418 events) and **TEST** (1,234 markets, 725 events) = h in [50, 350), volume
    < 1 M USD, closed in the frozen windows, **no event holding any already-read market**.
  - **HISTORY** = HISTORY_ONLY (1,980; h in [50, 350), closed in VALID/TEST windows, events already read) and the
    956 h < 50 VALID/TEST markets: wallet history only, never evaluated, labels never joined.
  - Iran: every market of an event whose slug starts with `us-strikes-iran` and the 28-Feb condition `0x3488f31e…`
    are excluded from every set (76 markets). The 36 cohort wallets (mission 3 `iran_cohort_wallets.json`) are added
    to the infra set: they never contribute and never count as counterparties, in any split.
- Tapes: data-api `v2/trades?condition=…&taker_only=false`, frozen collector of the 16-Nov study
  (`frozen_deps/collect_tapes.py`, sha256 `ee7f6d75…`, checked at run time), 300-page cap. h < 50: `phi-x/
  tapes_all.sqlite` (copied to `data/`, sha256 `49a99594…`, 1,579 markets `ok`, 3,206,979 fills, the union of the
  16-Nov `tapes.sqlite` and `tapes2.sqlite`; its request / too_deep / error accounting is not available). New tapes
  fetched on 2026-11-17 by `code/col_20_tapes.py`: train_ext 3,609/3,609 `ok` (6,699,376 fills), hold-out
  3,806/3,806 `ok` (7,407,906), history 1,980/1,980 `ok` (4,440,226); no `too_deep`, no error left after the retry
  pass; row counts equal the status table. Their sha256 are in `derived/tapes_sha256.txt` and are checked by
  `run_all.sh check` before the detector runs; the detector refuses to run if any market lacks a final status.
- Gamma metadata (mission 3 `fetch_meta.py`, fetched 2026-11-17, `derived/meta.jsonl`): `endDate`, `createdAt`,
  `startDate`. No outcome field. 10,973 of 10,974 returned.
- Funding (M4, `code/col_30_funding.py`): for every wallet contributing to a candidate at any panel unit (either
  side, all splits, collected without labels), its **first 100 ERC-20 transfers** on Polygon (Etherscan v2
  `tokentx`, ascending, one call). Status `complete` (< 100 transfers, whole history), `early` (first 100 only),
  `error` (downstream UNKNOWN). Kept: USDC.e and native USDC rows. Direct pair link: a USDC transfer between two
  collected wallets whose transaction `to` is not a Polymarket contract of mission 4 `params.json["infra"]`
  (checked by `eth_getTransactionByHash`; unchecked pairs are `unresolved` → UNKNOWN). Common funder: a non-hub
  sender of USDC to both wallets; a hub sent USDC to ≥ 10 distinct collected wallets, or is an infra contract or
  the zero address. All links count only if dated strictly before `t − W`.
  Collected 2026-11-17: 6,893 wallets, 823 `complete`, 6,070 `early`, 0 `error`; 750 candidate direct edges, 227
  direct pairs kept, 0 unresolved; 68 hubs; 6,619 wallets with an inbound USDC transfer in the window.

## Splits and point-in-time rule

- A unit is eligible for split S only if its market is in S **and** its time `t` lies inside S's window (mission 3
  observation-time rule). No model is fitted on labels that resolve after the unit it scores.
- Every feature at `t` uses fills with `ts ≤ t`, the last **executed** price at or before `t` (never a midpoint),
  history strictly before `t − W` where mission 4 says so, metadata existing before resolution (as fetched in
  November 2026: see Limits), and funding transfers strictly before `t − W`. `closed_ts` is never a feature.
- TRAIN may be read freely. VALID is read once, with the TRAIN-fitted models (`valid` refuses a second run). Models
  are then refitted on TRAIN + VALID (same λ and specification; VALID units of the 27 events that also hold TEST
  markets are purged from the refit). TEST is read once (`test` refuses a second run).

## Detector (inherited, not tuned)

Mission 4 `signals.py` (sha256 `914f59c8…`) on the mission 3 ledger **final version** `ledger.py` (sha256
`9e6fee08…`), parameters `params.json` (sha256 `37677ff8…`). Mission 4's own TRAIN outputs were computed on an
earlier ledger (`3a905ec3…`, its manifest); the final ledger is used here, so contributors, candidates and alerts
can differ from mission 4's recorded TRAIN outputs. `code/feat_30_detect.py` copies `market_pass` line for line
(additions marked `# m5`) and imports `enrich_and_fire` unchanged; `tests/test_feat.py` checks on real tapes that
candidates, PV rows and wallet history equal `signals.market_pass` (with and without a null seed), that every
recorded feature is invariant to cutting the tape after `t`, and that the compact wallet index equals
`signals.build_index`. Grid 900 s, W = 3600 s, warm-up 3600 s, contribution = real change of X = q(YES) − q(NO) ≥ 500
shares classified as a real change, price band [0.05, 0.90]. One global time-ordered pool (all tapes above).

## Units (evaluation points), all outcome-blind

For each market and side `s`, eligible grid times `t`, price of `s` in [0.05, 0.90]:

- **R**: each grid time is drawn with probability 1/384 by `sha256(cid|t|R)` (about one per 4 days of open market),
  side drawn by hash. The chance that an open time becomes a unit does not depend on the market's future length.
- **PV**: first grid time per (market, side, split window) where mission 4's price/volume rule fires.
- **IND**: first grid time per (market, side, split window) with exactly one contributing wallet whose change
  ≥ 3,000 USD.
- **COL**: first mission 4 alert per (market, side, split window) with ≥ 1 family among F1, F2, F3, F4, F5, F7, F8.
- Panel = union of all units; identical (market, side, t) are merged with their type flags.

## Models (exactly these, nested)

Logistic regressions of `win_s`, features standardised with the moments of the fitting set, L2 penalty
λ ∈ {0.1, 1, 10, 100} chosen per model by 5-fold **event-grouped** cross-validation on TRAIN (mean log loss; a
fold that cannot be fitted stops the run), IRLS with a convergence flag stored with the model.

- **M0, price alone**: `logit(p_s(t))` (clipped to [0.01, 0.99]), a side indicator (YES = 1) and their product, a
  side-specific recalibration of the price. `M0raw` = `p_s(t)` itself, reported in the calibration tables.
- **M1, price + public market information**: M0 + log1p window volume USD, log ratio of window volume to the
  median of prior non-zero windows and an indicator that this ratio is undefined, side price move over W, log1p
  distinct wallets trading in the window, log1p fills in the window, share of the window's volume in its last
  900 s, log hours since the market's first fill, log1p hours to the scheduled `endDate` and an indicator that it
  is unknown, PV flag.
- **M2, individual shifts**: M1 + log1p largest single-wallet real change toward `s` (USD), same toward the other
  side, IND flag for `s` and for the other side.
- **M3, collective shifts**: M2 + for `s` and the other side: log1p contributors, log1p total USD change, top share;
  for `s`: F3 mean surprise, F4 young share, F5 repeated pair (0/1), F7 repeated lead (0/1), F8 z (clipped to
  [−5, 5]), number of COL families fired, COL flag. Features of an absent candidate are 0.
- **M4, collective shifts with independently observed financial relations at T**: M3 + F6a (direct pair link
  before `t − W`), F6b (common non-hub funder before `t − W`), share of contributors without a known funding
  window, and F6-unknown (no link found while a window is missing or a pair is unresolved).

## Tests

ΔLL = mean log loss of the smaller model minus that of the larger (positive = larger model better), per unit.

Confirmatory family on TEST (models refitted on TRAIN+VALID), Holm at α = 0.05 over **7** tests (an IMPOSSIBLE
test enters Holm with p = 1 and is registered without a p):

- **T1 (primary)**: ΔLL(M1 → M3) on COL units.
- **T2**: ΔLL(M2 → M3) on COL units.
- **T3**: ΔLL(M0 → M3) on all panel units (also credits public, non-collective information; not specific).
- **T4**: matched excess of COL units over controls (below).
- **T5**: ΔLL(M3 → M4) on COL units.
- **T6**: ΔLL(M1 → M2) on IND units.
- **T7**: ΔLL(M0 → M1) on PV units.

Inference, H0: θ ≤ 0. (a) Event-cluster bootstrap: 20,000 resamples of events. (b) Wallet-cluster bootstrap:
20,000 resamples of wallet clusters, each unit assigned to its wallet (COL contributors on `s` and the IND wallet)
that holds the most units of the split, so units sharing a recurrent wallet move together; a unit without a wallet
is its own cluster. For each: p = (1 + #{θ*_b − θ̂ ≥ θ̂}) / (B + 1), one-sided 95 % upper bound
θ̂ − q_{0.05}(θ*_b − θ̂). **The reported p is the larger of (a) and (b), the reported upper bound the larger of the
two bounds.** A two-way pigeonhole bootstrap (Poisson weights on events × mean Poisson weight of the unit's
wallets) is reported as robustness only (see pre-freeze change 5). Models are fixed during the bootstrap. BH at q = 0.05 is reported alongside.
Each test also reports units, events, distinct wallets and the share of units holding a wallet active in ≥ 50
events of the split. VALID gets the same 7 tests with the TRAIN-fitted models.

**T4, matched controls.** Each COL unit is matched to up to 5 non-COL units with no candidate on `s`, from other
events of the same split, exact on side, category group (politics, sports, crypto, culture, economy, world,
science, other: first matching tag in that order) and `endDate` known/unknown; nearest neighbours with replacement
on standardised `logit p`, log1p hours to `endDate`, log1p cumulative market volume up to `t`, log1p window volume,
log1p active wallets in the window, log market age at `t`, |dp| over W and over 4 h (price jumps as a proxy for
public news), and day of `t`; caliper 1.0 (mean absolute standardised distance). Statistic: mean over matched COL
units of `(win − p) − mean over its controls (win − p)`. p and bound = the largest of (a) the COL-event bootstrap,
(b) a bootstrap with Poisson weights on every event involved (the COL unit's and each control's, so reused controls
move together) and (c) the wallet-cluster bootstrap of the COL units. Balance (standardised mean differences before and after) and the number of reused controls are
reported. Fewer than 100 matched COL units → IMPOSSIBLE.

**Activity-preserving null gate (not in the Holm family).** Mission 4's day-shift null (each wallet's fills in a
market shifted circularly by whole days, keeping its sizes, sides, activity and hour of day) applied to every TEST
market, K = 19 seeds, whole pipeline re-run, frozen TEST models; markets the null skips (life < 3 days) are removed
from the observed statistic too. A seed without any COL unit counts as a null at least as large as the observed.
Gate p = (1 + hits) / 20 (smallest possible 0.05). The shift also moves each fill's price, so the null scores the
models under a scrambled price path: it tests alignment, not information.

**Calibration** (M0raw, M0–M4 on VALID and TEST, all units and COL units): intercept and slope of the logistic
recalibration, ECE (10 equal-count bins), reliability table, Brier, log loss.

**Sensitivity** of T1 on TEST (reported, never used to choose; one registry line each, event bootstrap 5,000):
COL restricted to F1, to F2, score ≥ 2, score ≥ 3; price band [0.10, 0.80]; units ≥ 24 h before `endDate`; markets
closed within 1 day of their `endDate`; COL units without any wallet active in ≥ 50 TEST events; λ fixed at each
grid value (M1 and M3 refitted on TRAIN+VALID); leave one M3 group out (F3, F4, F5, F7, F8, size features);
event-only vs two-way p.

## Minimum sizes and smallest effect of interest

- T1, T2, T4, T5: ≥ 100 COL units in ≥ 50 events in TEST; T5 also ≥ 30 COL units with F6a or F6b = 1 and a known
  funding window for ≥ 70 % of the contributor wallets. T6, T7: ≥ 100 units in ≥ 50 events. Otherwise IMPOSSIBLE.
- SESOI: ΔLL 0.002 nats per unit (about a 3-point excess at p ≈ 0.45) for T1/T2/T3/T5/T6/T7; +0.03 for T4.

## Verdict, applied by `ana_50_models.py verdict` (no hand assembly)

For H1 (collective information beyond price and public information):
- `SUPPORTED`: T1 passes Holm, the VALID T1 estimate is > 0, the null gate p ≤ 0.05, and the control gate passed.
- `INCONSISTENT`: T1 passes Holm but one of those three conditions fails (the failing ones are reported).
- `NEGATIVE_PRECISE`: T1 does not pass, the T1 upper bound corrected for the overfitting bias measured under the
  NULL controls (`upper − min(0, mean NULL T1)`) is < 0.002, **and** the T4 upper bound is < +0.03.
- `UNDERPOWERED`: T1 does not pass and the negative is not precise.
- `IMPOSSIBLE`: minimum sizes not met, or data unavailable.
T2, T5, T6, T7 get `REJECTS_H0_AFTER_HOLM`, `NEGATIVE_PRECISE` (upper bound < 0.002), `UNDERPOWERED` or `IMPOSSIBLE`.
A failure to reject is never written as "no edge exists".

## Positive and negative controls (before freezing, TRAIN only)

`code/ctl_40_inject.py` injects synthetic collective shifts into real TRAIN tapes: in a hash-chosen 25 % of TRAIN
markets, 3 wallets each buy 1,500 shares of side `s*` at the last executed price, at t0 + 60, 300, 600 s, t0 a
hash-chosen grid time with p(s*) in [0.2, 0.7]; each buy is minted against one synthetic counterparty buying the
other side. Detector runs on a TRAIN-only pool. `ana_50_models.py controls`: mock split of TRAIN events (70 / 30 by
event hash), λ by CV on mock-train, T1 and T4 (and T5 with funding) on mock-test with the same p rule as the real
tests (two-way included).

| Scenario | P(s* = winner) | Wallets | Seeds | Role |
|---|---|---|---:|---|
| STRONG | 1.00 | fresh | 5 | positive control |
| MEDIUM | 0.75 | fresh | 5 | power |
| WEAK | 0.60 | fresh | 5 | power |
| NULL | 0.50 | fresh | 10 | negative control; its mean T1 is the overfitting bias used by the verdict |
| OLD | 0.75 | real TRAIN wallets first seen ≥ 30 days before t0, absent from the market | 5 | power without the "young wallet" give-away |
| FUNDLINK | 0.50, plus a synthetic common funder and direct link only when s* wins | fresh | 5 | power of T5 (M4), invisible to M3 |
| PERMUTED | labels permuted within (category, month of first unit) strata, one label per market | — | 1 | negative control |

Freeze gate (`code/ctl_45_summary.py`, written to `controles/positive_controls.md`): G1 STRONG rejects T1 at
p ≤ 0.05/7 in every seed; G2 STRONG detection rate ≥ 0.90 of injected markets (an alert on the injected side within
2 h after t0 holding ≥ 2 injected wallets) in every seed; G3 NULL has T1 p ≤ 0.05 in at most 2 of 10 seeds; G4
PERMUTED T1 p > 0.05. MEDIUM, WEAK, OLD and FUNDLINK give the power table (not gating). Synthetic registry lines are
marked `donnees="synthetiques"`. The counterparty of each synthetic buy is itself a single-wallet shift toward the
other side and can light M2's IND features, so T2 is not a clean power estimate under injection.

## Limits declared now

- Fills only (no splits, merges, conversions, redemptions): exposure is the ledger's observable part.
- Inclusion depends on end-of-life quantities (final volume < 1 M USD, tape under 300 pages, close inside the
  window); for "by date" markets an early YES closes early, so the windows over-represent early YES. All models
  are compared on the same units; the "closed on schedule" sensitivity bounds the effect for T1 only.
- `endDate` was read from Gamma in November 2026; a deadline edited after `t` would leak into M1 and T4 matching.
- Wallet history is limited to the collected band (h < 350, volume < 1 M USD): a lower bound of real history.
- Tapes fetched in November 2026; publication latency of each fill is assumed (60 s), not measured. No order book.
- Markets of ≥ 1 M USD volume are excluded, where large coordinated positions may sit.
- Funding: only each wallet's first 100 ERC-20 transfers are read, so a direct transfer made later between two
  active wallets is not seen; hub status uses the whole collected window, not the history as of `t` (it can only
  remove funders, biasing F6b toward zero, not toward the outcome).
- Effective n is bounded by events, and below that by wallets recurring across events; the two-way bootstrap with
  mean wallet weights only partly captures a wallet present in many events (sensitivity without such wallets).
- The day-shift null scrambles prices together with wallet activity (above).
- Controls run on a TRAIN-only pool (less history than the real runs); their power applies to injected patterns,
  not to every real form of coordination.

## Pre-freeze changes (all before any VALID/TEST label was read)

1. 12:29 UTC: M0 made side-aware after a smoke run on TRAIN with permuted labels (registry lines
   `SMOKE_PERMUTED_*`): a side-blind M0 was beaten by any side-correlated feature.
2. After the blind audit (workflow `wf_2c94ab5c-b5d`, 43 agents, `audit/pre_freeze_audit.md`): R units drawn per
   grid time instead of a fixed number per market (look-ahead on market length); verdict computed by code; T4
   two-way bootstrap over all involved events; two-way bootstrap weights via `bincount` (the `reduceat` version
   dropped a wallet) and B = 20,000; labels other than YES/NO refused; CV and single-class fits refused instead of
   silently scored; tapes hashed and completeness enforced; phase-A cache keyed by code, parameters, ledger,
   detector and Iran list; VALID and TEST one-shot guards; refit purge of VALID events shared with TEST; IMPOSSIBLE
   tests registered without a p; one registry line per sensitivity variant, missing variants added; funding
   UNKNOWN handled; null gate on the same market subset; permutation control made a bijection per market; ledger
   version difference declared.
3. Controls redesigned (after 5 runs of the first design were seen, synthetic data only: STRONG rejected T1 in 2/2
   seeds, MEDIUM in 1/2, WEAK in 0/1, registry lines `CTL_*` of the first design): more seeds, OLD and FUNDLINK
   scenarios, two-way p in controls, detection rate computed, gate written in code. The first design's rule
   ("MEDIUM rejects in every seed") was replaced by G1–G4 because MEDIUM is below the detectable size; MEDIUM is
   reported as power.
5. Decision p changed from max(event, pigeonhole two-way) to max(event, wallet-cluster), **after seeing the
   redesigned controls** (synthetic, 21 runs): under STRONG the event p was ≤ 0.0024 in 5/5 seeds but the pigeonhole
   p reached 0.015 (3/5 below 0.05/7), while under NULL the two agreed. With wallets that appear in a single unit
   (injected wallets, and most real wallets), the pigeonhole product of weights adds unit-level noise unrelated to
   any dependence and is conservative by construction. The wallet-cluster bootstrap keeps units of a recurrent
   wallet together without that extra noise. All controls are re-scored with the new rule (`run_all.sh rescore`);
   the gate G1–G4 is unchanged. Registry lines of the first scoring stay in the registry.
6. **Freeze gate result: FAILED on G1 only** (`controles/positive_controls.md`, 13:32 UTC): STRONG rejects T1 at
   p ≤ 0.05/7 in 4 of 5 seeds (STRONG_3: p = 0.0094; all 5 at p ≤ 0.05); G2 (detection ≥ 0.98 in every seed), G3
   (NULL: 0 of 10 seeds at p ≤ 0.05) and G4 (PERMUTED p = 0.88) pass. Power table: MEDIUM 0/5, OLD 0/5, WEAK 0/5
   at the Holm threshold; FUNDLINK: T5 rejects in 5/5 seeds while T1 stays silent (0/5). **Decision by Benjamin, 2026-11-17 ~13:36 UTC, asked before any VALID/TEST label was
   read: freeze and evaluate anyway**, the failure being recorded here. Consequences fixed now: (i) the verdict
   rule is unchanged, so `SUPPORTED` cannot be reached (the control gate did not pass) and a T1 rejection would
   read `INCONSISTENT`; (ii) the power reading of a null result is the table above: the hold-out can exclude an
   effect of the STRONG size (mean mock-test T1 ΔLL +0.036), not of the MEDIUM size (+0.007).
4. M4 funding window reduced to each wallet's first 100 ERC-20 transfers: full histories of active wallets need
   up to 10 Etherscan pages each (24 % of the first 117 wallets hit the 10,000-row cap), about 19 h for 7,010
   wallets.
