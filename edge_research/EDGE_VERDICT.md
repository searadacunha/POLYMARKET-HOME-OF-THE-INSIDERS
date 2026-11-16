# Executable-edge verdict — 16 November 2026

**Verdict: NO_EDGE_VALIDATED.** This new file is a post-hoc execution-sensitivity audit, **not a new independent holdout** or a profitable-trading claim. Existing frozen protocols, evidence, baseline and root README are untouched.

## Frozen cohort — source-backed arithmetic

Source: [published analytic table](../research_notes/early-detection-2026-11-13/study/derived/analytic_table.jsonl) and [frozen verdict](../research_notes/early-detection-2026-11-13/study/derived/verdict.json). The original rule **LONELY_THIN** on the original VALIDATION subset: 45 observations from 44 events, 13 winning sides, mean last-buy price 0.2538753. Mean (outcome minus observed price) = **+0.0350136 USDC per share**, with a frozen exact-test p-value **0.3346** and reported event-bootstrap 95% interval **[-0.0981, +0.1795]**. The interval includes zero.

This branch's new read-only module, [cost_gate.py](cost_gate.py), applies *hypothetical* fixed per-share adverse-entry markups to the very same 45 rows. Each row assumes buying **one share at the already recorded historical price** and holding to settlement at 0 or 1, with perfect fills, no market impact and no other cost. These optimistic conditions are not real orders.

| Additional per-share entry cost | Mean hypothetical settlement PnL per share |
| ---: | ---: |
| 0.000 USDC | +0.0350 USDC |
| 0.005 USDC | +0.0300 USDC |
| 0.010 USDC | +0.0250 USDC |
| 0.020 USDC | +0.0150 USDC |
| 0.030 USDC | +0.0050 USDC |
| 0.050 USDC | -0.0150 USDC |

The initial print was often **consumed by the wallet being detected**. It is not an executable bid/ask quote and may precede alert delivery. Thus, even the no-cost calculation is not an observed tradeable profit. The historical platform fee, fill probability, latency, slippage, position size, settlement lock, adverse selection and rebate entitlement are not known for these 45 entries. This grid was examined *after* the signal's validation, so it must not be used to select an ex-post profitable parameter.

## Family-by-family gate

| Family | Current evidence | Missing for verified positive net expectancy |
| --- | --- | --- |
| A. Wallet-following / smart money | Original LONELY_THIN 13/45 wins vs price-implied 25.4%, p=0.33. External skill-following backtest reports a negative result in its own sample. **Not validated.** | As-of track record and complete positions, new time holdout, live detection/queue/fees |
| B. ChangeNOW cohort | [Case audit](../investigations/changenow-polymarket/FINDINGS.md) records 158 bettors, total PnL -$21,722 on $626,466 staked, with 16 incomplete histories; **not evidence for edge**. | Exact funding path to deposit, comparable matched controls, future entry quotes |
| C. Maker / microstructure | Prior engine's three short-horizon hypotheses produced **zero validation passes**, small sample; modeled maker advantages are unresolved. | Order-by-order queue/fill evidence, spread vs adverse selection, rebates and external holdout |
| D. Linked-market arbitrage | Mathematical inconsistency alone **not executable**. | All-leg simultaneous depth, negative-risk conversion treatment, timing, fees, capital |
| E. Structural probability bias | [Historic local study](../investigations/edge-polymarket/FINDINGS.md): 16 calibration strategies, none survived TRAIN. External favorite-longshot evidence depends on event-level aggregation. | Predeclared category/horizon rule, genuinely later events, executable bid and ask |

Every family remains at **NO_EDGE_VALIDATED** under the requested positive **out-of-sample, after-cost, executable** standard. No signal scanner or trading API was enabled.

## One decisive next experiment — pre-register before seeing new outcomes

Test a single maker-spread hypothesis on a narrowly defined new market cohort. Record both tokens' true L2 book and prints, event time and local receive time, historical category fees/rebates, and final resolution. Enter only when a predeclared spread condition holds; place a small limit order *behind the visible queue* with a specified placement/cancel delay. Credit fills only when a conservative queue model says volume actually reached the order. Measure 1- and 5-minute markouts and settlement PnL, compare against no-quote and aggressive-crossing baselines, debit capital lock and adverse selection, and split by future time and parent event. If enough contemporaneous book data are missing, return NOT_TESTABLE rather than imputing profitable fills.

A small free crypto L2 sample from [outcometick](https://github.com/outcometick/polymarket-backtest) or [PMData](https://github.com/mileswangs/polymarket-historical-data) is suitable for **software validation**, not for claiming our historical political/geopolitical signals were tradeable.

## What was actually checked

- GitHub main tree and high-value reports, datasets and code paths inspected; no claim that 8,912 blobs were all reviewed or local Mac files accessed.
- The published 587-row analytic table was parsed and the original 45-row frozen cohort's outcomes/mean prices/cost sensitivities recalculated from GitHub source.
- Six independent local Python unit tests for the **new** read-only module passed.
- **Not performed:** full-repository publication integrity tests on a real cloned worktree, an independent future holdout, or any maker/order execution experiment using historical true order books. This research PR should remain **draft** until the existing AGENTS.md release checklist is executed on a complete clone.
