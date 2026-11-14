# The engine on the live chain

`monitoring/phi_engine` was run against Polygon on 14 November 2026, on this machine, next to the deployed collector
(`~/phi-livecollect`, untouched). Two runs are reported; four shorter runs before them found the defects listed at the
end. Every number below is in `data/live_run_20261114_run5.json` and `data/live_run_20261114_run6.json`, written by
`scripts/summarize_live_run.py` from the engine's own database. The alert journals stay next to those databases: they
name wallets.

| | Run 5 | Run 6 |
|---|---:|---:|
| Engine version | definitions of the study before its second pre-freeze audit | final definitions (money received on chain, R1 age, exclusions) |
| Start, end (UTC) | 13:16:21, 14:36:23 | 15:22:59, 16:16:13 |
| Minutes | 80.0 | 53.2 |
| Blocks read | 3,202 | 2,130 |
| Passes behind the head of the chain | 0 of 570 | 0 of 376 |
| Source errors, other errors | 0, 0 | 0, 0 |
| Fills seen, three exchanges | 234,249 | 163,885 |
| of which ExchangeV3 (Polymarket protocol V2) | 2,825 (1.2 %) | 2,372 (1.4 %) |
| Fills of 1,000 USD or more | 1,106 | 925 |
| Rows kept (large fills and fills of watched wallets) | 1,173 | 1,025 |
| Seconds from block to storage, median / p90 / max | 8.0 / 11.2 / 13.3 | 8.2 / 11.3 / 13.6 |
| Markets met, by family: excluded kinds / INFO / PUBLIC_PROCESS | 134 / 16 / 1 | 142 / 16 / 0 |
| Entries evaluated (first large purchase of a side) | 24 | 18 |
| Alerts | 4 | 2 |
| Seconds from the trade to the alert, median / max | 6 / 7 | 5 / 9 |
| Database size | 1.1 MB | 0.9 MB |

Run 5 was stopped after 80 minutes because the only public endpoint that serves old log ranges (tenderly) was needed
by the study's collector; run 6 was stopped after 53 minutes for the same reason. Neither stop lost data: the engine
stores each block range before it moves on and resumes from its checkpoint.

## What the runs show

- **An alert is ready a few seconds after the trade**, about one block after it is stored: the engine reads the logs
  of the three exchanges directly, so it does not wait for the data API, whose plain listing is cached for 300 s (the
  latency agent of 13 November measured 15.7 % of trades seen without its cache-busting parameter).
- **ExchangeV3 is already live**: 1.2 % to 1.4 % of fills, all of them in combinatorial markets in the probe of
  `data/exchange_probe_20261114.json`. A monitor that reads only the two older exchanges misses them, and the
  documentation announces that new markets move to protocol V2 from 23 November 2026.
- **Most large fills are on markets the study excludes** (sports, crypto prices, weather and the like): 134 and 142
  markets of excluded kinds against 16 INFO markets. The light filter of the engine (one fill of 1,000 USD or more on an
  INFO or PUBLIC_PROCESS market) is what keeps the expensive reads (wallet history, receipts, logs) rare.
- **The alerts are exploratory.** Each one carries `VALIDATION: EXPLORATORY` unless its class is SUPPORTED by the frozen
  study (RESULTS.md). The six alerts of these two runs were on three markets: two Taipei mayoral markets and one token
  launch market (PUBLIC_PROCESS). They are what the definitions select, not findings.

## Defects found by the live runs, fixed with tests

| Run | Defect | Fix |
|---|---|---|
| 1 | a token of ExchangeV3 unknown to the catalogue blocked the queue of entries | unknown tokens are resolved or set aside, counted |
| 1 | keeping every fill would cost about 2 GB a day | only fills of 1,000 USD or more and fills of watched wallets are kept; the others are counted |
| 4 | the public tag service answers with checksummed addresses: a tagged relay was read as untagged | keys compared in lower case, test added |
| 4 | an alert written by an earlier version could not be displayed | the report reads old field names |
| 5 | the study's second pre-freeze audit changed the definitions (money received on chain, R1 age) | engine aligned with the study code (`asof.py`, `chainfund.py` identical), the day of transfers read in slices of 9,000 blocks from an endpoint capped at 10,000, the 30 days of R1 in one call from the endpoint that accepts it |

## Limits

- Two runs of 53 and 80 minutes on one afternoon: lateness and coverage are measured, the rate of alerts per
  market-day is not.
- Old log ranges come from one public endpoint. At 16:20 UTC it answered in 6 to 11 s a call; the engine waits and
  retries, an entry is never concluded on a missing answer.
- A wallet with more than 1,000 activity rows is not evaluated for R1 by the engine (its first row is not read).
- The engine reads no news, posts or broadcasts: an alert after a public report is not told apart from one before it.
