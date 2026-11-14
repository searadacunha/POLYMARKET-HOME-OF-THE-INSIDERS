# The engine on the live chain

`monitoring/phi_engine` was run against Polygon on 14 November 2026, next to the deployed collector, which was left
untouched. Two runs are reported; four shorter runs before them found the defects in the first four rows of the table
at the end (its last row is the alignment with the study after the study's second audit, between runs 5 and 6). Every number below is in `data/live_run_20261114_run5.json` and `data/live_run_20261114_run6.json`, written by
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

- **An alert is ready 5 to 9 seconds after the trade** (6 alerts): the engine reads the logs of the three exchanges
  directly, so it does not wait for the data API, whose plain listing is cached: polled plainly, it showed 15.7 % and
  18.5 % of the 21,612 and 26,979 fills of two ten-minute windows ([LIVE_DETECTION.md](../../LIVE_DETECTION.md)).
- **ExchangeV3 is already live**: 1.2 % to 1.4 % of fills, and all 117 ExchangeV3 fills of the 150 blocks of the probe
  (`data/exchange_probe_20261114.json`) were combinatorial positions. A monitor that reads only the two older exchanges
  misses them, and the official rollout page, as read on 14 November 2026, says that new single markets start trading on
  Protocol V2 from 23 November 2026, by phases ([SYSTEM_AUDIT.md](SYSTEM_AUDIT.md)).
- **Most markets met are of the kinds the study excludes** (sports, crypto prices, weather and the like): 134 and 142
  markets of excluded kinds against 16 INFO markets. The light filter of the engine (one fill of 1,000 USD or more on an
  INFO or PUBLIC_PROCESS market) is what keeps the expensive reads (wallet history, receipts, logs) rare.
- **The alerts are exploratory.** Each one carries `VALIDATION: EXPLORATORY` unless its class is SUPPORTED by the frozen
  study (RESULTS.md). The six alerts of these two runs (four purchases; the four alerts of run 5 used the
  definitions before the study's second audit) were on three markets: two Taipei mayoral markets and one token launch
  market (PUBLIC_PROCESS). They are what the definitions select, not findings.

## Defects found by the live runs, fixed with tests

| Run | Defect | Fix |
|---|---|---|
| 1 | a token of ExchangeV3 unknown to the catalogue blocked the queue of entries | unknown tokens are resolved or set aside, counted |
| 1 | keeping every fill would cost about 2 GB a day | only fills of 1,000 USD or more and fills of watched wallets are kept; the others are counted |
| 4 | the public tag service answers with checksummed addresses: a tagged relay was read as untagged | keys compared in lower case, test added |
| 4 | an alert written by an earlier version could not be displayed | the report reads old field names |
| 5 | the study's second pre-freeze audit changed the definitions (money received on chain, R1 age) | engine aligned with the study code (`asof.py`, `chainfund.py` identical), the day of transfers read in slices of 9,000 blocks from an endpoint capped at 10,000, the 30 days of R1 in one call from the endpoint that accepts it |

## Audit of the engine, 14 November 2026, evening

A separate agent audited `monitoring/phi_engine` against the official contract source and the protocol V2 pages,
changed only the engine and its tests, and measured two runs against the public data API for 15 minutes
(18:31 to 18:46 UTC). Findings and measurements: `data/engine_audit_20261114.json`, `data/engine_race_20261114.json`,
`data/engine_reorg_probe_20261114.json`. The collector `monitoring/livecollect` was not touched. Tests: 51, all passing
(44 before); run against the earlier `feed.py`, 6 of the new tests fail or error (5 failures, 1 error).

| Point | Found | Now |
|---|---|---|
| Decoding | layout, sides and decimals match the ExchangeV3 source; 333 fills of 1,000 USD or more of the API in the window, 0 missing from the store, 0 size mismatch over 0.01 among 340 large fills | unchanged |
| Silent drops | logs marked `removed` were skipped without a count; a node behind the others (drpc, measured) answers a range past its own head with a list that stops at it, so the checkpoint could pass unread blocks; fills of an exchange outside the registry were never read (a sentinel sampled 4 blocks every 40 passes) | removed logs journaled; near the tip a chunk counts only up to the last block its answer shows; the log query names no contract, unknown emitters are counted by address and journaled hourly, never kept |
| Protocol V2 | ExchangeV3, pUSD, ramps and adapters already in the registry with the right event; the market lookup knew only `clobTokenIds`, which the V2 pages say can be null for a V2 market (its ids are in `positionIds`) | lookup by `position_ids` and field chosen by `version`, tested; today Gamma still fills both fields, and no binary or negative-risk V2 market has traded yet (every ExchangeV3 fill so far is combinatorial) |
| Reorganizations | blocks read up to head minus 3, no hash check | blocks read only up to Polygon's finalized block, 1 to 4 blocks behind the head (median 3, 107 reads); 485 blocks read again 60 s later on another node: 0 hash changed, 0 answer incomplete. No real reorganization occurred during the probe |
| Double counting | one row per (transaction, log index), counters committed with the checkpoint, one entry per wallet and side when a transaction holds several orders, chain and API never summed | tested, including a re-read range and a queue run twice; the `cash` counter adds both sides of a trade |
| Resumption | atomic checkpoint, outages read 600 blocks a pass, lock against a second run | a crash during a catch-up resumes and counts 200 fills once (test); an alert committed to the store before its line in `.alerts.jsonl` can leave the file one line short after a crash |
| Lateness | block to stored fill, 340 large fills | median 7.7 s, p90 11.1 s polling every 8 s; 4.1 s and 5.6 s every 2 s |

**Is the alert earlier than public broadcast?** Not earlier than the data API itself. The API's route of large
trades (`v2/trades`, the older `trades` now answers HTTP 410) showed a large fill a median 3.1 s after its block when
its cache was bypassed (p90 5.2 s); the engine was first on 16 of 340 fills polling every 8 s and 79 of 340 every 2 s.
The same listing read as a bot reads it is served from a cache: 897 of 900 polls were cache hits, and the engine
was first on all 340 fills, by a median 175 s (109 of them never appeared there before the window ended and are
counted as the engine's). Each run raised one alert, on the same trade (class C3), 4.5 and 5.4 s after it; the
uncached API had that trade 2.4 and 3.2 s before the alert. By construction an alert cannot precede the API: the
engine waits for the wallet's activity listing to show the entry. One window of 15 minutes, large fills only; posts
on social networks were not measured.

## Limits

- Two runs of 53 and 80 minutes on one afternoon, and two of 15 minutes in the evening: lateness and coverage are
  measured, the rate of alerts per market-day is not.
- Old log ranges come from one public endpoint. At 16:20 UTC it answered in 6 to 11 s a call; the engine waits and
  retries, an entry is never concluded on a missing answer.
- A wallet with more than 1,000 activity rows is not evaluated for R1 by the engine (its first row is not read).
- The engine reads no news, posts or broadcasts: an alert after a public report is not told apart from one before it.
