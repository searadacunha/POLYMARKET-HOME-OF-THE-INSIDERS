# Which study next? Three candidates compared

Written 18 November 2026 from the findings already in this repository. **No collection was run and no signal is claimed.**
The only external contact was a feasibility probe: two listing calls to the public Gamma API and one `prices-history` call
for one closed basketball market. Nothing from them is stored here.

## The three candidates

| Code | Question | Where it comes from |
|---|---|---|
| **B** | Does the win rate of sports game outcomes exceed their price at T-7d in the 0.55 to 0.60 bucket, as an external study claims (+25.8 points, "n=120/2,025" in the external write-up)? | `EDGE_VERDICT.md`, "Next most informative test"; the claim is the external `sturzael/polymarket-edge-research`, read as data and not executed |
| **C** | Do collective exposure shifts beat the price when the wallets involved are financially linked? | `collective-exposure-shifts` STATUS: "financially linked collective shifts are UNRESOLVED, no funding graph was built at this scale" |
| **A** | Can the `SIG_HIST` lead be captured at an executable price, using archived order books? | `maduro-iran:F-008` (UNRESOLVED) and `F-009` (REFUTED for the second-buy route) |

## Comparison

| Criterion | B: sports calibration at T-7d | C: financially linked shifts | A: capture of the `SIG_HIST` lead |
|---|---|---|---|
| Probability of an interpretable result | **High.** Binary outcomes, one fixed cell, one benchmark (the price). About 530 games in the cell detect a 6-point excess with 80 % power (one cell, no clustering, normal approximation); the external 25.8 points needs far fewer. Open: how many games were listed 7 or more days ahead (the probed game was listed 6.9 days before it) | **Low to medium.** The whole signal is null (-1.6 points on 266 alerts, 48 in TEST). A linked subgroup of unknown share is smaller: at 10 % it would be about 27 alerts, whose standard error is about 9.6 points | **Low.** Depth was observable within 2 s for 5 to 8 % of alerts (phase 10); the next buyer arrives in 2 to 4 s; the live infrastructure was not validated (`F-010`) |
| Cost in data and quota | **Low.** Free public endpoints, hourly price history (median gap 3,600 s in the probe), about one call per market, a few thousand calls; tens of MB; a script, not agents | **Medium to high.** A funding graph for the wallets of about 2,000 shifts: on-chain calls, rate-limited public RPC, earlier keys were exhausted | **Highest.** A local collector of 20 markets wrote about 0.9 GB a day; covering the markets where alerts occur is out of reach, and months are needed |
| Can it refute a hypothesis? | **Yes, the best case.** A cell fixed before any rate, tested on data the claim never saw; a miss refutes it. The neighbouring buckets are the control | **Weakly.** An underpowered null excludes only large effects | **Partly.** Two routes are already refuted (`F-009`, phase 10); more data would only close the rest |
| Out-of-sample backtest | **Yes.** The external discovery sample is not ours; chronological halves inside ours | **Yes.** TRAIN, VALID and TEST exist | **Forward only.** No historical order books |
| Improvement over the market price alone | **The test is that comparison** (win rate against price). An executable edge also needs the ask and the fees, which the history does not hold: a second, forward stage | Compared with the price at the alert, as in T1 of the study | The lead is real against matched controls (+17.6 to +20.7 points of LEAD60), but the price moves within seconds and the copy return was -3.7 % in TEST (phase 9) |
| **Rank** | **1** | **2** | **3** |

## Why B first, and its cautions

- It is the only candidate whose answer can be obtained cheaply and whose failure would be informative. The repository's standing
  result is that nothing tested has a net edge (`EDGE_VERDICT.md`); B tests the one external claim large enough to matter.
- The claim deserves suspicion before any test. Its authors narrowed the effect to one cell after a six-way stratification of the
  same data (MLB, NBA, NFL, NHL; game outcome; T-7d; 0.55 to 0.60; lifespan up to 14 days; volume above 5,000 USD): a classic path
  for a false positive. They also report that their earlier estimates were "systematically 3 to 10 times too high". Treat the
  cell as a hypothesis, fix it in the plan, and count every neighbouring cell in the register (`hypothesis_tests`).
- Traps seen in the probe: a game listed 6.9 days ahead has no T-7d price, so the population must be defined by listing time;
  `endDate` of a market can precede the game, so T must be the game start; the first price after listing may be a stale or
  initial quote; many markets share one event, so errors must be clustered by event.

## Shape of the study, if the owner chooses it (not frozen, not started)

1. **Stage 1, free, no execution claim.** Population: resolved two-outcome game-outcome markets of the four leagues, listed at least
   7 days before the game start. Price: the last hourly point at or before T-7d. Primary test: win rate minus mean price in the
   0.55 to 0.60 cell, bootstrap by event. Declared comparisons: the other price buckets and the other horizons, all in the
   register. Chronological halves; verdict `SUPPORTED` only if the excess is positive in both halves and its interval excludes 0
   after correction for the declared comparisons, otherwise `NOT_SUPPORTED`. A positive control first: the test must find a
   planted bias.
2. **Stage 2, only if stage 1 is `SUPPORTED`.** A forward paper test against live best asks with the sports fees in force, no
   money. Until it passes, no advantage over the price is claimed.

Whatever is started needs the frozen-plan discipline of `METHODOLOGY.md`: a plan locked by hash before any rate, a register of
every test, positive controls, blind audits before the results are read.
