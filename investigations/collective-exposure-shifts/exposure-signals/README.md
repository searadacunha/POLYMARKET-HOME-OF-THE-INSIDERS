# Collective exposure signals (mission 4/7)

Date: 2026-11-17. Agent: Claude Code (Opus 5.5). TRAIN only. **No VALID or TEST market was run or labelled.**
Status: **EXPLORATORY**. Nothing here is evidence of predictability, and the best TRAIN family must not be read as
one.

## What it is

A deterministic detector built on the point-in-time position ledger of mission 3
(`../position-ledger/scripts/ledger.py`, imported, not copied; only its public API: `Ledger`, `snapshot`,
`classify`, `family_binary`, `partition_of`, `make_event`). Every 900 s grid time `t`, window `(t-3600, t]`, per market and per side:

- a wallet **contributes** to side `s` when its directional exposure `X = q(YES) - q(NO)`, read from the ledger at
  `t` and `t-W`, moved toward `s` by >= 500 shares (payout USD) **and** the ledger classifies the window as a real
  change (`DIRECTIONAL_ADD`, `A_TRUE_INVERSION`, `D_*`). Excluded: `C_TECHNICAL`, `C_MARKET_MAKING`,
  `C_COMPLETE_SET`, `C_HEDGE_REBALANCE`, `NONE`, `UNKNOWN`, and the six Polymarket contracts listed in `params.json`;
- a **candidate** is >= 2 contributors on one side, price of that side in [0.05, 0.90], `t` at least 60 min after the
  market's first fill and not after its close.

Eight families, each with its own fixed rule (`params.json`, declared before any label was read):

| Family | Feature | Fires when | Information used |
|---|---|---|---|
| F1 | wallets whose net exposure really changed | >= 3 | ledger at t, t-W |
| F2 | marked change (USD) and concentration (top share, HHI) | >= 3,000 USD and top share <= 0.6 | ledger, last price <= t |
| F3 | synchronisation vs each wallet's habit: mean of `-ln((h+1)/(H+2))`, h = active hours, H = hours observed, all **before t-W** | mean >= 3.0 (each wallet active in under ~5 % of its hours) | TRAIN tapes before t-W |
| F4 | first-seen age and prior markets at t | >= 50 % of contributors first seen < 7 days | TRAIN tapes <= t |
| F5 | contributor pairs already together on one side in **another event** | >= 1 pair | candidates with t' < t |
| F6 | direct funding link between contributors | >= 1 pair paid **before t-W** | funding edges (not collected, see Limits) |
| F7 | lead/follow (follower's first window fill <= 600 s after the leader's) repeated from another event; counterparty concentration and share traded among contributors | >= 1 repeated ordered pair and internal share < 0.5 | window fills, candidates with t' < t |
| F8 | contributors' flow not explained by the price move: z of the residual of `flow ~ k * dp`, fitted on the market's **prior** grid points | z >= 2 with >= 8 prior points | market's own prior windows |

`score` = number of families fired; `reasons` gives each fired rule with its values. Statistical units are the first
firing per (market, side, family) (`primary_for`); repeats are kept but never counted twice.

Relations built only through an exchange, bridge, hot wallet or technical event are excluded:
- Polymarket contracts are never contributors or counterparties.
- Counterparties come from opposite exposure moves in the same transaction.
- The funding loader keeps only `kind == "direct_transfer"` with a tx hash, and drops exchange, bridge and technical rows.
- A payment after `t - W` never links a group.

## Each alert keeps

`alert_id`, `event_id`, `event_slug`, `condition_id`, `token_id`, `side`, `t`, `window`, `available_ts`
(`t + 60 s`, a declared indexing latency, **not measured**), `price_side`, `price_side_prev`, `contributors[]`
(wallet, signed net change in shares and USD, ledger class, `x_status`, reasons, first window fill, transactions,
habit and age features), `source_txs`, every family's features, `families_fired`, `score`, `reasons`,
`primary_for`, `params_sha256`, `known_at_t` (what each feature was allowed to see).

## Files

| Path | Content |
|---|---|
| `params.json` | every threshold, declared before labels (sha256 `37677ff8…e5a9`) |
| `scripts/signals.py` | detector: phase A per market, phase B global in time order |
| `scripts/run_signals.py` | runner, TRAIN guard, observed or null seed, JSONL + Parquet |
| `scripts/check_truncation_real.py` | anti-lookahead check on real tapes |
| `scripts/run_nulls.sh`, `scripts/compare_nulls.py` | 19 day-shift null runs and the comparison |
| `scripts/evaluate_train.py` | preliminary TRAIN comparison (labels joined last, TRAIN ids only) |
| `tests/test_signals.py` | 11 tests (positive control, truncation invariance of the whole pipeline, group repetition only from earlier events, payments after the window ignored, technical relations dropped, infra never contributes, null keeps hour of day, detector code never reads labels, partition guard) |
| `PRE_LABELS.sha256` | hashes of code, params and observed outputs taken before labels were read, plus a dated correction |
| `out/observed/` | `alerts.jsonl`, `alerts.parquet`, `alert_contributors.parquet`, `pv_baseline.jsonl`, `grid_prices.jsonl.gz`, `market_stats.jsonl`, `manifest.json` |
| `out/null/seed_k/manifest.json` | null counts and feature quantiles |
| `out/eval/` | `labels_train.jsonl` (623 TRAIN ids only), `comparison_train.json`, `truncation_real.json`, `nulls_vs_observed.json` |
| `out/observed_ledger_v1_superseded/` | first run, on ledger v1 (superseded at 09:42 UTC by mission 3); kept, not used |

Reproduce (Python 3.13 of `/Library/Frameworks`, which has pyarrow; inputs read-only on VERBATIM):

    X=../../..; PY=/Library/Frameworks/Python.framework/Versions/3.13/bin/python3
    $PY -m pytest -q -p no:cacheprovider tests
    $PY -I scripts/run_signals.py --tapes $X/tapes.sqlite --tapes $X/tapes2.sqlite \
        --markets $X/sample_markets.jsonl --markets $X/sample_expanded.jsonl --params params.json --out out/observed

## Run (TRAIN)

623 TRAIN markets (closed in 2025, Iran excluded), 510 events, 1,235,327 fills, 2,611,844 grid points, 0 quarantined
rows, 30 unbalanced transactions (their wallets read `UNKNOWN` and are excluded). The runner refused 666 VALID and
290 TEST markets before reading any of their fills. 6,434 candidates, 6,353 alerts. Contributor classes in alerts:
17,261 `DIRECTIONAL_ADD`, 737 `D_UNVERIFIED_NO_RETENTION`, 295 `A_TRUE_INVERSION`.

Anti-lookahead: 11/11 tests pass. On 5 hash-drawn real TRAIN markets (38,840 fills), alerts before each of three cuts
are byte-identical with and without the data after the cut (0, 5 and 43 alerts before the cuts).

## Null model (activity and habits kept)

How the null works:
- Each wallet's fills in a market are shifted circularly by a whole number of days, drawn by hash of seed, wallet and market.
- This keeps every wallet's sizes, sides, activity and hour of day, and the market's prices.
- It breaks the alignment between wallets.
- 19 seeds were run on the 586 markets that can be shifted (life >= 3 days); 37 short markets were skipped by every seed.
- The observed counts below are restricted to the same 586 markets.
- One-sided p = (1 + #null >= observed) / 20, so **0.05 is the smallest value 19 seeds can give**.

| Family | Observed units | Null mean [min, max] | p | Observed firings | Null firings mean |
|---|---:|---|---:|---:|---:|
| F1 | 215 | 87.9 [80, 96] | 0.05 | 2,128 | 673.4 |
| F2 | 88 | 43.0 [34, 56] | 0.05 | 520 | 156.3 |
| F3 | 290 | 212.6 [197, 225] | 0.05 | 2,767 | 1,623.8 |
| F4 | 239 | 192.9 [178, 206] | 0.05 | 2,557 | 2,073.8 |
| F5 | 93 | 15.8 [11, 19] | 0.05 | 715 | 67.9 |
| F6 | 0 | 0 | not measured | 0 | 0 |
| F7 | 14 | 5.7 [1, 8] | 0.05 | 43 | 13.3 |
| F8 | 367 | 245.8 [236, 260] | 0.05 | 4,723 | 1,736.6 |

Reading:
- Wallets change their net exposure together, on the same side, more often than their own habits produce. That holds for every family the data can measure: about 2.4 times for F1, and about 6 times for F5 (pairs that come back together).
- This is a statement about **timing**, not about coordination or information. Shifting by whole days also breaks the shared reaction to public news, so a crowd reacting to the same headline is enough to produce this excess.
- Repeated pairs (F5) are less exposed to that reading, but they can still be active traders of the same market type.
- The excess is not accompanied by any excess over the price (table below).

## Preliminary comparison with price and price/volume alone (TRAIN, exploratory)

Excess = win - price of the side at `t` (last executed). Event-clustered bootstrap, 2,000 draws, 95 % interval.
"Next grid" re-prices at the next 900 s grid point (a crude proxy for executing after the alert). Placebo:
same market, same side, >= 6 h away, price within 0.05.

| Group | Units | Events | Mean price | Win rate | Excess vs price at t | Excess vs next grid price | Net at 1 % slippage | Minus within-market placebo |
|---|---:|---:|---:|---:|---|---|---|---|
| F1 | 229 | 147 | 0.427 | 0.419 | -0.008 [-0.033, +0.016] | +0.001 [-0.024, +0.026] | -0.018 [-0.043, +0.006] | -0.000 [-0.003, +0.002] |
| F2 | 95 | 68 | 0.665 | 0.674 | +0.009 [-0.037, +0.055] | +0.012 [-0.035, +0.060] | -0.001 [-0.047, +0.045] | -0.002 [-0.007, +0.002] |
| F3 | 305 | 198 | 0.439 | 0.439 | +0.001 [-0.025, +0.025] | +0.003 [-0.018, +0.026] | -0.009 [-0.035, +0.015] | +0.001 [-0.001, +0.004] |
| F4 | 255 | 167 | 0.408 | 0.380 | -0.028 [-0.052, -0.005] | -0.027 [-0.049, -0.004] | -0.038 [-0.062, -0.015] | -0.001 [-0.004, +0.002] |
| F5 | 95 | 78 | 0.532 | 0.495 | -0.037 [-0.100, +0.023] | -0.032 [-0.092, +0.022] | -0.047 [-0.110, +0.013] | +0.003 [-0.001, +0.008] |
| F6 | 0 | | | | not collected | | | |
| F7 | 15 | 14 | 0.598 | 0.733 | +0.135 [-0.017, +0.278] | +0.119 [-0.031, +0.259] | +0.125 [-0.027, +0.268] | +0.012 [-0.002, +0.025] |
| F8 | 388 | 232 | 0.432 | 0.425 | -0.007 [-0.024, +0.011] | -0.010 [-0.027, +0.006] | -0.017 [-0.034, +0.001] | -0.001 [-0.003, +0.001] |
| Any family, first firing | 404 | 241 | 0.439 | 0.436 | -0.004 [-0.021, +0.013] | -0.004 [-0.021, +0.012] | -0.014 [-0.031, +0.003] | -0.001 [-0.003, +0.001] |
| Score >= 2, first | 376 | 230 | 0.431 | 0.418 | -0.014 [-0.033, +0.005] | -0.015 [-0.034, +0.004] | -0.024 [-0.043, -0.005] | -0.001 [-0.003, +0.001] |
| Score >= 3, first | 245 | 156 | 0.442 | 0.420 | -0.021 [-0.044, +0.000] | -0.011 [-0.035, +0.010] | -0.031 [-0.054, -0.010] | +0.001 [-0.001, +0.004] |
| **Price alone**, random grid time per market side | 939 | 442 | 0.448 | 0.461 | +0.013 [+0.005, +0.022] | +0.016 [+0.007, +0.025] | +0.003 [-0.005, +0.012] | |
| **Price/volume alone** (hour volume >= 3x prior median, price of the side up >= 0.02) | 725 | 378 | 0.458 | 0.441 | -0.017 [-0.025, -0.009] | -0.014 [-0.022, -0.007] | -0.027 [-0.035, -0.019] | |

Reading, TRAIN only:
- No family beats the price at the alert.
- Combining families (score >= 2, >= 3) does worse, not better.
- The price/volume rule is below the price. The price alone at a random time is slightly above it, which is the usual calibration bias of the price, not a signal.
- F4 is below the price, but its feature is biased (see Limits).
- F7 is the highest, at +0.135, but on 15 units in 14 events, with an interval that includes 0. It is one of 12 groups compared without any correction, and its value moved from +0.046 to +0.135 between ledger v1 and v2. **That is noise until a frozen out-of-sample test says otherwise, and it must not be quoted as a result.**

The within-market placebo column is near 0 by construction. Same market and same side means the same outcome, so it only measures whether the alert's moment gets a better price than other moments at a similar price. It does not.

## Limits

- **F6 not measured.** No funding edges were collected (internal disk 0.3 GB free; no collection allowed). The
  loader, the "before t-W" rule and the exclusion of technical relations are implemented and tested on fixtures
  only. In every alert, `F6.status = NOT_COLLECTED`.
- **F4 is biased young.** "First seen" is the first fill inside the 2.2 % sample of TRAIN tapes, not the account's
  creation, so most contributors look new: F4 fired in 2,647 of 6,353 alerts. Gamma `createdAt` is not available
  offline.
- **Wallet history** (F3, F4, F5, F7) is limited to the TRAIN sample tapes. It is a lower bound of the real history.
- **Fills only**: splits, merges, conversions and redemptions are invisible, as the ledger states for each snapshot.
  Neg-risk markets are read as single binaries; no event-level family.
- **Availability**: tapes were fetched in November 2026. Whether each fill was visible within 60 s of its block in
  2025 is not verified.
- **Execution**: last executed price, no order book. The 1 % slippage is a flat assumption.
- **Ledger dependency**: mission 3 rewrote the engine once during this run (v1 to v2). Outputs record the ledger
  sha256 (`3a905ec3…01d1`). Null runs refuse to compare against an observed run on another ledger.
