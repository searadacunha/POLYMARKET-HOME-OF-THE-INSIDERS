# Positive controls before the freeze

Run on synthetic tables only; no real market data is read. Every check exercises the functions of `code/ana_edge.py` that the study will use, so the controls test the frozen code itself.

| # | Control | Result |
|---|---|---|
| 1 | C1_flat_market_loses_spread_and_fees | PASS — net=-0.031998 per share |
| 2 | C2_strong_rise_positive_gross | PASS — net=0.285000 per share (optimistic) |
| 3 | C2b_rise_survives_politics_costs | PASS — net=0.264845 per share (politics) |
| 4 | C3_latency_moves_entry_price | PASS — ask@1s=0.3250 ask@31s=0.4050 |
| 5 | C4a_missing_exit_refused | PASS — after() returns None past the last quote |
| 6 | C4b_stale_quote_refused | PASS — before() refuses a quote older than 5 s |
| 7 | C4c_depth_at_quoted_price | PASS — supports 100 shares at the quoted ask |
| 8 | C4c2_depth_mismatch_refused | PASS — wrong level price -> None |
| 9 | C4c3_stale_depth_refused | PASS — depth older than 2 s -> None |
| 10 | C5_fees_on_losing_trades | PASS — gross=-0.1000 net=-0.1218 |
| 11 | C6a_summarize_metrics | PASS — n=7 dd=0.8190 expected=0.8190 |
| 12 | C6b_depth_supported_counts | PASS — depth_supported=7 |
| 13 | C6c_empty_rows_reported | PASS — empty cell reports n=0, no fabricated numbers |

Registered in the registry as synthetic data. Failures would block the freeze.
