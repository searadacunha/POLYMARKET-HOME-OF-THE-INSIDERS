# Positive controls (synthetic tables, before the freeze)

Each cell: 60 synthetic tables of 1500 ignitions, entry prices drawn from Beta(2,3) clipped to [0.03, 0.90]; T1 exact, T2 with 4000 permutations, verdict rule of `code/stats.py` at the corrected threshold 0.0025.
`delta_class` is the planted excess win probability of the flagged class; `delta_all` is an excess shared by every ignition (a general under-reaction of the market), which must NOT produce a SUPPORTED verdict by itself.

| flagged rows | delta_class | delta_all | SUPPORTED | NOT_SUPPORTED | INCONCLUSIVE |
|---:|---:|---:|---:|---:|---:|
| 8 | 0.00 | 0.00 | 0/60 | 0/60 | 60/60 |
| 8 | 0.00 | 0.10 | 0/60 | 0/60 | 60/60 |
| 8 | 0.15 | 0.00 | 0/60 | 0/60 | 60/60 |
| 8 | 0.30 | 0.00 | 0/60 | 0/60 | 60/60 |
| 8 | 0.50 | 0.00 | 0/60 | 0/60 | 60/60 |
| 8 | 0.30 | 0.10 | 0/60 | 0/60 | 60/60 |
| 12 | 0.00 | 0.00 | 0/60 | 60/60 | 0/60 |
| 12 | 0.00 | 0.10 | 0/60 | 60/60 | 0/60 |
| 12 | 0.15 | 0.00 | 0/60 | 60/60 | 0/60 |
| 12 | 0.30 | 0.00 | 17/60 | 43/60 | 0/60 |
| 12 | 0.50 | 0.00 | 47/60 | 13/60 | 0/60 |
| 12 | 0.30 | 0.10 | 14/60 | 46/60 | 0/60 |
| 20 | 0.00 | 0.00 | 0/60 | 60/60 | 0/60 |
| 20 | 0.00 | 0.10 | 0/60 | 60/60 | 0/60 |
| 20 | 0.15 | 0.00 | 8/60 | 52/60 | 0/60 |
| 20 | 0.30 | 0.00 | 28/60 | 32/60 | 0/60 |
| 20 | 0.50 | 0.00 | 59/60 | 1/60 | 0/60 |
| 20 | 0.30 | 0.10 | 32/60 | 28/60 | 0/60 |
| 40 | 0.00 | 0.00 | 1/60 | 59/60 | 0/60 |
| 40 | 0.00 | 0.10 | 1/60 | 59/60 | 0/60 |
| 40 | 0.15 | 0.00 | 13/60 | 47/60 | 0/60 |
| 40 | 0.30 | 0.00 | 48/60 | 12/60 | 0/60 |
| 40 | 0.50 | 0.00 | 60/60 | 0/60 | 0/60 |
| 40 | 0.30 | 0.10 | 45/60 | 15/60 | 0/60 |
| 80 | 0.00 | 0.00 | 0/60 | 60/60 | 0/60 |
| 80 | 0.00 | 0.10 | 0/60 | 60/60 | 0/60 |
| 80 | 0.15 | 0.00 | 30/60 | 30/60 | 0/60 |
| 80 | 0.30 | 0.00 | 60/60 | 0/60 | 0/60 |
| 80 | 0.50 | 0.00 | 60/60 | 0/60 | 0/60 |
| 80 | 0.30 | 0.10 | 60/60 | 0/60 | 0/60 |

Null rows (delta_class = 0, with or without a shared excess): 2 SUPPORTED out of 600 tables.
Fewer than 10 flagged rows always give INCONCLUSIVE by rule.
