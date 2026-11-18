# EDGE_VERDICT

Date: 16 November 2026. Scope: this file states the results of the `edge_research/` study
(`analysis_plan.md`, frozen before any rate was computed, lock `b51b510f0c22ca95…`) together with
the standing negative results of this repository. It replaces no historical report and changes no
published claim.

## Overall verdict: `NO_EDGE_VALIDATED`

No pattern tested here, and no pattern previously tested in this repository, shows a net positive
expectancy out of sample after real execution costs. The frozen detection study of 13 November 2026
measured the `LONELY_THIN` class at +3.5 points over the price (p = 0.33, n = 45) — no advantage.
The present study measured four execution-side families on live order-book quotes and one
arbitrage gate; all are negative or empty. The honest statement of this repository is that it
detects one kind of early trading, not an exploitable advantage.

## Comparative table, ranked by validated net edge

| # | Family (mission code) | What was tested | Evidence level | Net result after costs | Verdict |
|---|---|---|---|---|---|
| 1 | E. Arbitrage / baskets | 15,555 paired YES+NO top-of-book quotes, 3 splits, ≤ 2 s quote ages | Measured here, 2.5 d | 0 gross violations; basket always ≥ 0.1 c over 1 USD | `NO_EDGE_VALIDATED` for this universe |
| 2 | C. Microstructure: taker taker | 12,224 control entries, 5 horizons, 3 cost scenarios | Measured here, 2.5 d | −1.1 c to −1.9 c per share (fees make it worse) | `NON_EXPLOITABLE` as tested |
| 3 | D3 order-book imbalance | 630 signals vs matched controls | Measured here, 2.5 d | matched difference −0.0011…+0.0002/share; depth proof for 0 rows | `NON_EXPLOITABLE` |
| 4 | B1 copy-large public trades | 3 trades ≥ 1,000 USD in 2.5 d | Measured here | n=3, cells negative | `DONNEES_INSUFFISANTES` |
| 5 | D1/D2 momentum/reversal ±0.005/5 min | 73,200 minute-token observations | Measured here | 0 signals: universe too quiet at this threshold | `DONNEES_INSUFFISANTES` |
| 6 | A. Alert-following (smart money) | 45 alerts of the frozen study; 6,645 labelled alerts of a previous local study (descriptive recount) | Frozen study 13 Nov + recount | +3.5 points, p = 0.33; recount excess −2.65 points (n = 2,885) | `NO_EDGE_VALIDATED` |
| 7 | B. ChangeNOW → Polymarket | Repo investigations `changenow-proof`, `changenow-polymarket`, `followup-20261113` | Repo evidence | Losing retail; no shared owner demonstrated; one corroborated contact, no path to bets | `NO_EDGE_VALIDATED` |
| 8 | External lead: FLB on sports favorites (sturzael e23) | Not tested here: match-level sports are outside this repository's universe | External claim only | external claim +25.8 pp at T-7d, 0.55–0.60 bucket | `PROMISING_NOT_VALIDATED` — see "next test" |

## The one operational fact worth money

On the markets measured, **the toll is the trade**: buying at the ask and exiting at the bid costs
0.1–1.9 cents per share per round trip before any edge, and the displayed top-of-book rarely proves
even 10 shares of depth within 2 s. Any strategy must beat a guaranteed negative baseline; nothing
tested here does. This reproduces, on live Polymarket quotes, what an external 478,155-entry shadow
evaluation found (junegun/polymarket-strategy-lab: −2.1 % per entry, every family losing).

## Next most informative test

The single external lead that survives triage is the favorite-longshot bias on **sports game
outcomes** at T-7d in the 0.55–0.60 bucket (sturzael/polymarket-edge-research, e23 synthesis,
+25.8 pp claimed, stable across 3 years, not our data). It is the only candidate whose claimed
magnitude survives its own stratification. The most informative next test is therefore a frozen
replication on our own sports-market population (Gamma match-outcome markets, resolution-labelled,
entry price = real ask at T-7d, fees per the plan's scenarios, chronological splits) — it is cheap,
uses only public endpoints, and either destroys the external claim or produces the first candidate
for a paper-traded live test. Everything else tested to date is either negative, empty, or a
single-case anecdote.

## Provenance and licences

External repositories were read (never executed) through `edge_research/data/github/` with per-file
sha256 (`data/github/followup.json`). Their files are fetched locally for reading only and are NOT
redistributed in this branch (several carry no licence or a custom one); the published commit keeps
only `index.json` and `followup.json` (metadata, provenance, sha256). Cited findings: outcometick
(polymarket-backtest, MIT), SII-WANGZJ (Polymarket_data, MIT), G0BLINDEV (MIT), hugompt (MIT),
vsbtc (MIT), junegun (NOASSERTION — findings cited only), tlafargue (NOASSERTION — its calibration
parquet files motivated the thresholds; nothing redistributed), darrnhard, bradca0, sturzael,
Fierdimo. All analysis code in `edge_research/code/` is original to this study.
