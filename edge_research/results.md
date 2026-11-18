# Results — quote diagnostics, execution costs, pair gate, historical recount

Study: `analysis_plan.md` (frozen 16 November 2026, lock `b51b510f0c22ca95…`). Inputs: fixed sha256
prefix of `~/phi-live/market.jsonl` (`42f8508d2da53bb7…dc29b`, 2,406,972,265 bytes, verified by
re-reading the prefix), receive-time window 2026-11-14 00:00 → 2026-11-16 13:00 UTC; universe 20
pre-existing YES tokens (19 Democratic nomination event, 1 Xi event; 2 independent event families).
Code frozen before any rate was computed. Positive controls: 13/13 PASS
(`controles/CTL_00_report.md`). All rates below are in the registry (`registre/tests.jsonl`).

## 1. The five signal families on live quotes (675 cells)

5 groups × 5 horizons × 3 latencies × 3 cost scenarios × 3 chronological splits. Entry at the ask
received at decision+latency, exit at the bid at horizon; missing inputs excluded AND counted; no
split crossing; fees charged on both legs regardless of profit (scenario rates: optimistic 0/0,
politics 0.04/0.001, stress 0.07/0.002).

| Signal | Unique signals (2.5 d) | Non-empty cells | Net per share (politics, 1 h, 5 s latency) | Verdict |
|---|---:|---:|---|---|
| Control (flat minutes) | 12,224 | 108 | **−0.0111** | NON_EXPLOITABLE: the taker toll |
| D1 momentum (≥ +0.005 / 5 min) | **0** | 0 | — | DONNEES_INSUFFISANTES |
| D2 reversal (≤ −0.005 / 5 min) | **0** | 0 | — | DONNEES_INSUFFISANTES |
| D3 imbalance (top-3 bid share ≥ 0.8) | 630 | 63 | −0.0138 | NON_EXPLOITABLE (all cells negative) |
| B1 copy-large (≥ 1,000 USD BUY) | **3** | 42 | — | DONNEES_INSUFFISANTES (n=3) |

- **The baseline is the finding.** Buying at the ask and exiting at the bid one hour later on a
  market that did not move loses 0.11 c (spread, optimistic) to 1.9 c (stress) per share. With the
  politics fee scenario every control cell is negative (−0.0107 to −0.0123). There is no fee-free
  directional trade on these markets: the toll is paid first.
- **D1/D2 never fire.** Of 73,200 minute-token observations, no 5-minute midpoint move reached
  ±0.005. These long-horizon nomination markets are too quiet for a threshold calibrated on faster
  markets; the threshold was fixed before the freeze and is not retuned (that would be exploratory).
- **D3 imbalance never beats the control.** 630 signals across the three splits; matched
  differences against same-token/hour/price-bin controls lie between −0.0011 and +0.0002 per share.
  Displayed top-of-book depth supported 10 shares for **0** executed rows (full book frames are
  sparse: 7,267 books for ~70k decision events; the 2 s age rule and the exact-BBO match are the
  plan's own strictness, not a bug).
- **B1 copy-large.** Only 3 trades of ≥ 1,000 USD BUY on the 20 YES tokens in 2.5 days (4,909
  recorded trade rows); median lag chain→received 76 s. n=3 says nothing; its cells are negative.

## 2. Pair gate E — YES+NO baskets (3 comparisons)

15,555 minute pairs with both quotes ≤ 2 s old and quote clocks ≤ 2 s apart:

| Split | Paired quotes | Gross violations (sum of asks < 1) | Max gross edge per pair |
|---|---:|---:|---:|
| TRAIN | 6,709 | **0** | −0.001 |
| VALIDATION | 5,436 | **0** | −0.001 |
| TEST | 3,410 | **0** | −0.001 |

Even before any fee, a YES+NO basket always costs at least 0.1 cent more than 1 USD. The market is
internally consistent at the displayed top of book on this universe: nothing to capture.

## 3. Historical diagnostic recount (1 declared comparison)

On the frozen copy of the labelled alerts of a previous local study (origin volume not mounted;
descriptive reuse only, not independent validation): pooled win rate minus mean price at the alert
across the two validation populations, all 12 classes pooled — **n = 2,885, excess −2.65 points**
(win rate 57.5 % against a mean price of 60.2 %). The per-class recount (32 cells, exploratory,
registered as such) shows no class with a convincing positive excess; C3_OUT_OF_CHARACTER (the
largest, n=1,180) sits at +2.9 points with a mean price of 66 % — well inside noise for one
unverified population.

## 4. What this study does not show

- Two independent event families and 2.5 days: the bootstrap intervals are descriptive; no power
  for generalization. No p-value is claimed anywhere in this study.
- Quote-to-quote outcomes are conditional on received quotes; unknown cancellations, message loss
  and clock skew prevent certified fills. Depth is display depth at frame time only.
- The 24 h horizon is censored by the daily splits and stays missing by design.
- D1/D2 verdicts are about this universe at this threshold, not about momentum in general.
