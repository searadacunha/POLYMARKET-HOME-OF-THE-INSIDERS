# Positive controls, run before the freeze

Synthetic tables: 1500 discovery events and 2000 validation events, entries of one market side share one outcome.
Threshold used: 0.05 / 63 = 0.000794. Bootstrap draws in the controls: 2000 then 10000.
`flag` is the planted class stored as a flag (alert at the entry), `moment` the same entries stored as a class with its own
alert moment and price, `edge` the top 5 % of the logistic model fitted on the synthetic discovery set.

| Configuration | Alert events aimed at | Runs | Mean alert events | Mean excess (flag) | SUPPORTED: flag | SUPPORTED: moment | SUPPORTED: edge | T1 under threshold (flag) | T2 under threshold (flag) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| effect_0.03 | 150 | 6 | 124 | +0.041 | 0 | 0 | 0 | 0 | 0 |
| effect_0.03 | 500 | 6 | 392 | +0.049 | 1 | 0 | 0 | 1 | 1 |
| effect_0.03 | 1500 | 6 | 1105 | +0.018 | 0 | 0 | 0 | 1 | 0 |
| effect_0.05 | 150 | 6 | 124 | +0.059 | 0 | 0 | 0 | 0 | 0 |
| effect_0.05 | 500 | 6 | 392 | +0.067 | 3 | 2 | 2 | 3 | 3 |
| effect_0.05 | 1500 | 6 | 1105 | +0.032 | 1 | 0 | 0 | 2 | 2 |
| effect_0.10 | 150 | 6 | 124 | +0.109 | 3 | 0 | 0 | 3 | 3 |
| effect_0.10 | 500 | 6 | 392 | +0.107 | 6 | 4 | 3 | 6 | 6 |
| effect_0.10 | 1500 | 6 | 1105 | +0.065 | 4 | 3 | 2 | 6 | 5 |
| effect_0.15 | 150 | 6 | 124 | +0.162 | 5 | 5 | 0 | 6 | 5 |
| effect_0.15 | 500 | 6 | 392 | +0.145 | 6 | 6 | 3 | 6 | 6 |
| effect_0.15 | 1500 | 6 | 1105 | +0.102 | 6 | 6 | 6 | 6 | 6 |
| null | 150 | 20 | 124 | -0.007 | 0 | 0 | 0 | 0 | 0 |
| null | 500 | 20 | 391 | -0.002 | 0 | 0 | 0 | 0 | 0 |
| null | 1500 | 20 | 1094 | +0.005 | 0 | 0 | 0 | 0 | 0 |
| shift_all_0.05 | 500 | 8 | 415 | +0.036 | 0 | 0 | 0 | 1 | 0 |
| weeks_sigma_0.8 | 500 | 20 | 410 | +0.002 | 0 | 0 | 0 | 0 | 0 |

False positives with nothing planted: 0 verdicts SUPPORTED in 180 class runs.
Population that beats its price everywhere: 0 verdicts SUPPORTED (T1 fires there, T2 is what must hold the verdict back).
The `weeks` rows give the rate at which correlated outcomes alone produce a SUPPORTED verdict.

How to read the power rows. The column to read is the mean excess actually present in the tables, not the size planted:
at the highest share of flagged entries, flagged entries sit on both sides of many markets and the planted lift partly
cancels (10 points planted leave about 6.5 at 1,100 alert events). With about 400 alert events, a real excess of 10 points
was found in 6 tables of 6 and one of 5 to 7 points in 3 of 6; with about 125 alert events, 10 points in 3 of 6 and 15
points in 5 of 6. A verdict also needs an excess of 5 points or more, so an excess under 5 points cannot be SUPPORTED
whatever the sample. The collection and feature code is not exercised by these tables: it is checked by self-tests
and on documented accounts of the discovery set.
