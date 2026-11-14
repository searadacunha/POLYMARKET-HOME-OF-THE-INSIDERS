# Live detection: what works, what it costs, where it stops

The monitor is in [monitoring](monitoring/README.md). This page says what was measured about the public interfaces on
13 November 2026, how fast an alert can be, and what has not been shown. Measurement files:
[latency_run1.json](research_notes/early-detection-2026-11-13/data/latency_run1.json),
[latency_run2.json](research_notes/early-detection-2026-11-13/data/latency_run2.json),
[rest_probe.json](research_notes/early-detection-2026-11-13/data/rest_probe.json),
[ws_reconnect.json](research_notes/early-detection-2026-11-13/data/ws_reconnect.json).

## Which channel sees what, and how late

Two windows of ten minutes each. The reference is the chain: every `OrderFilled` log of the two exchange contracts
(21,612 fills in the first window, 26,979 in the second). Lateness is measured against the block timestamp. The second
window was recorded on a machine under heavy load.

| Channel | Shows the wallet | Share of fills seen | Median lateness | 90th percentile |
|---|---|---:|---:|---:|
| Polygon `eth_getLogs` every 4 s | yes | 100 % and 100 % | 2.5 s and 7.8 to 9.9 s | 6.1 s and 25 to 27 s |
| Data API `v2/trades`, polled plainly | yes | 15.7 % and 18.5 % | 23.0 s and 21.3 s | 42 s and 45 s |
| Data API with a changing extra parameter | yes | 100 % and 97.2 % | 3.6 s and 6.4 s | 5.6 s and 24.9 s |
| Data API filtered at 1,000 USD and more | yes | all trades of that size | 118.8 s and 3.9 s | 258 s and 12 s |
| Live-data WebSocket, `activity` | yes | 47.0 % and 37.6 % | about 0 s | 0.5 s and 3.9 s |
| Market WebSocket, `last_trade_price` | **no** | 75 % and 100 % of the subscribed tokens | 2 s **before** the block | |

What these lines mean in practice:

- **The data API answers from a cache.** Its responses carry `Cache-Control: public, max-age=300`, and 258 of 278 plain
  polls returned a body already served. Polled every two seconds, the global feed showed one fill in six. The
  size-filtered feed does show every large trade, but up to five minutes late in the first window; the second window
  was much faster and the difference is not explained. A collector built on plain polling of that feed is blind most
  of the time and does not know it.
- **A changing extra parameter gets around the cache.** It works and it is complete, but it defeats a protection the
  operator chose. The monitor uses it only for the first page of one market under examination.
- **The chain is complete and a few seconds late.** It also needs no trust in an intermediary: one log is one order
  being filled, and it equals one row of the data API on every transaction compared (114 of 114, then 66 of 66 in the
  `doctor` command).
- **The live-data WebSocket is fast and incomplete.** It showed fewer than half of the fills. In 991 of 12,998 messages
  the market identifier was empty. Its messages carry profile fields (`name`, `pseudonym`, `bio`, `profileImage`),
  which this repository never stores. The monitor does not use it.
- **The market WebSocket carries no wallet.** It is the public channel for prices and sizes, and it shows a trade about
  two seconds before its block. The authenticated user channel shows one's own orders only; it is not a feed of
  everybody's trades and is not used.

So the monitor watches the chain, and asks the data API, Gamma and the price history only for the few markets where
something happened.

## How fast an alert can be

The delay of an alert comes from the rule, not from the data. The rule waits for the 10-minute price point that shows
the move, and for fifteen minutes of trading after the first buy, so that "one wallet did most of the buying" means
something. In the replay of the Nobel night the first buy is at 22:42:57 UTC and the alert at 23:00:15 UTC: 17 minutes
later, and ten hours before the announcement. A few seconds of data lateness do not matter at that scale.

A cluster takes longer, because it needs a second account to be funded and to trade: 00:50 UTC in the same replay.

## What it costs to run

- One `eth_getLogs` call every eight seconds or so, about 450 an hour, plus one call for the head of the chain.
- For each market that passes the first filter: two or three Gamma calls, one price history, and the trade pages of
  that market only.
- For each alert: three calls for the history of the leading account, then its funding from Polygon logs (about 70
  calls for the Nobel alert, most of them to locate blocks by time).
- No key, no paid service, one SQLite file. Everything fits the free limits met during these tests: no HTTP 429 in
  34,413 price-history requests at about 20 per second, nor in the test runs of the monitor.

## What the public endpoints allow

| Endpoint | Finding |
|---|---|
| Data API v1 (`/trades`, `/activity`) | Retired: HTTP 410 |
| Data API `v2/trades?condition=` | Newest first, cursor pagination, time filters ignored: one reads back from the latest trade |
| Data API `v2/activity?user=` | `start`, `end` and `type` are honoured; the monitor checks `end` on every answer |
| Gamma `events` with a page above 50 | HTTP 406 unless `Accept-Encoding: gzip` is sent; listing is by cursor (`events/keyset`) |
| Gamma `markets?clob_token_ids=` | Closed markets need `closed=true` |
| CLOB `prices-history` | One-minute points available; at most about 14 days per request; `interval=max` returns nothing for a closed market |
| CLOB `book`, `midpoint`, `spread`, `price` | Answer without authentication; no historical order book |
| Polygon logs for old blocks | Of four public nodes, one accepted wide block ranges; the others answered 50 blocks at most or had no archive |
| Relay request records | Retired on 24 November 2026; not used |

## Robustness that exists and is tested

Position in the chain and every page read are checkpointed in the same transaction as their rows; fills are keyed by
transaction and log index, so reading a block twice stores nothing twice; an outage longer than about an hour is
written to the journal as a gap; a tape that is not newest-first, or an HTTP error, raises instead of becoming an empty
result; the WebSocket client reconnects with a growing delay (handshake measured at 0.2 to 0.5 s). The offline tests
cover each of these. Alerts and gaps go to an append-only journal in which each entry commits to the previous one.

## The live run

One run of 16 minutes, from 23:49 UTC on 13 November 2026, with its store on a slow external disk that was busy with
other work ([live_run_20261113.json](research_notes/early-detection-2026-11-13/data/live_run_20261113.json)):

- 593 blocks read without a gap and without a source error: 29,518 fills, 2,181 tokens, 4,175 wallets, 1.16 million USD.
- 256 tokens passed the cheap first filter. 71 were dropped at once because their market is of an excluded kind
  (mostly sports matches); 21 markets were resolved and their price history read; 164 were still waiting when the run
  was stopped. No alert.
- The monitor fell behind: a fill was stored 31 seconds after its block at the median and more than six minutes after
  it at the 90th percentile. The sources were not the cause. Each pass got slower as the disk saturated, and the queue
  of first-time tokens grew faster than twenty per pass could clear.

Two lessons. The store belongs on a fast disk. And a monitor that starts with no history needs its first hour to work
through tokens it has never seen; the alert rule itself does not get less strict during that time.

**What was wrong, found the next day.** The disk was half of it. The store had no index on the wallet of a fill nor
on the receiver of a funding transfer, so every search for a funded group read the whole store, and read it again at
each step. A replay of 48 past alerts needed five and a half hours for the first 23, on the external disk, and sixteen minutes for the other 25 once
the two indexes existed. Both are now created with the store.

A second run on 14 November 2026, store on the internal disk, indexes in place, machine busy with other work
([live_run_20261114.json](research_notes/early-detection-2026-11-13/data/live_run_20261114.json)): 10 minutes 38
seconds before the session that ran it was cut off, 423 blocks, 18,871 fills, no source error, no alert. A fill was
stored 8.1 seconds after its block at the median and 11.9 seconds at the 90th percentile, the same at the end of the
run as at the start. Of 81 candidates, 71 were dismissed as excluded kinds and 10 were waiting. It kept up for ten
minutes; that is all this run shows.

**Price history.** The monitor used to read nine hours of prices for a market it had never seen. The rule compares a
price with the six hours before it and accepts a window that is half full, so the oldest points of a nine-hour
history were judged against a cut-off window. In one replay of 48 this produced an earlier move that no trade
confirmed, which closed the market before the real one
([replay_window_probe.json](research_notes/early-detection-2026-11-13/data/replay_window_probe.json)). The monitor
now reads 14 days once, as the study did, then only what is new. The second run above was made before that change.

## Not shown

- **No run of several days.** Whether public nodes stay available for weeks, and how many markets pass the first
  filter on a busy day once the store has history, is not measured.
- **The first hours are noisy.** With no stored history, many tokens pass the cheap filter once and are then dismissed
  by the price rule. This settles as the store fills.
- **The clock is local.** Lateness figures assume the Mac's clock; it was 0.12 s off the HTTP `Date` headers during the
  first window.
- **A Mac that sleeps collects nothing**, and says so in the journal when it wakes.
- **No alert has been raised live yet.** The pattern is rare; what the monitor would have said is known from replays
  ([BACKTEST_RESULTS.md](BACKTEST_RESULTS.md)).
