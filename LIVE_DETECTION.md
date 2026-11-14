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

## Not shown

- **No run of several days.** The longest live run is described below. Whether public nodes stay available for weeks,
  and how many markets pass the first filter on a busy day, is not measured.
- **The first hours are noisy.** With no stored history, many tokens pass the cheap filter once and are then dismissed
  by the price rule. This settles as the store fills.
- **The clock is local.** Lateness figures assume the Mac's clock; it was 0.12 s off the HTTP `Date` headers during the
  first window.
- **A Mac that sleeps collects nothing**, and says so in the journal when it wakes.
- **No alert has been raised live yet.** The pattern is rare; what the monitor would have said is known from replays
  ([BACKTEST_RESULTS.md](BACKTEST_RESULTS.md)).
