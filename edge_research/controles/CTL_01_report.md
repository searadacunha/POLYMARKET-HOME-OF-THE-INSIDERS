# Positive controls for the historical recount script

Run on synthetic labelled rows only; no real data is read.

| # | Control | Result |
|---|---|---|
| 1 | S1_excess_definition | PASS — win rate 0.5, mean price 0.5 → excess 0 |
| 2 | S2_planted_positive | PASS — win rate 0.5, price 0.4 → +0.1 found |
| 3 | S3_planted_negative | PASS — win rate 0.5, price 0.6 → −0.1 found |
| 4 | S4_validation_filter_only | PASS — discovery_info row excluded from the declared comparison |
