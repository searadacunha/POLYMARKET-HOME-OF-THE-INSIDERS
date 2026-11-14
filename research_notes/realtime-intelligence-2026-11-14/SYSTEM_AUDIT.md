# Audit of the collectors and of the data, 14 November 2026

What runs, what it really collected, what was wrong, and what this pull request changes. Every finding below was read on
copies. The running service was not stopped, replaced or modified.

Method. Each collector was audited by one reader on a copy; every finding rated blocking or major was then re-derived by
a second reader with its own scripts, whose task was to refute it. Both readers are language-model agents; their
findings, and the verdict of the second reader for each, are in
[data/collector_audit_findings.json](data/collector_audit_findings.json). The live probes of the exchanges were made
separately and are in [data/exchange_probe_20261114.json](data/exchange_probe_20261114.json).

## State found

- `main` held pull requests 69, 70 and 71 (head `2fafe7c` when the audit started).
- The prospective collector (`monitoring/livecollect`) runs on the Mac under launchd, restarted every hour by its
  supervisor, and writes to a local folder. Its code was version `livecollect-4`, identical byte for byte to commit
  `c218469` of the branch `cursor/forensic-engine-8e30`, which was **newer than `main`**. Replacing the deployed copy
  by `main` would have been a regression: no more books for the NO tokens, no more reference books, and a dedup of
  messages switched back on. This pull request merges that commit, so `main` and the service hold the same collector.
- The chain monitor (`monitoring/phi_monitor`) is not a service. It runs when started by hand.
- Two older collectors of the same machine also hold prospective data and are described at the end.

## The prospective collector

| | |
|---|---|
| Markets | 20, all still open, all ending in 2027 or 2028: nothing in this collection can be scored against an outcome before 2027 |
| Started | 13 November 2026, 18:04:53 UTC |
| Usable from | 13 November, 23:10:09 UTC. The first 5 h 05 min (114,325 price changes, 169 books) were stored without asset, price, side or size and cannot be repaired |
| List frames | From 23:10 to 09:25:35 UTC on 14 November the code then running kept only the last element of a websocket frame that was a list: the opening snapshot of 20 books became one book at each connection. About 285 snapshots lost (15 connections), not recoverable. Fixed in `livecollect-4` |
| Books that can be rebuilt | 24.6 % of the token-seconds of the decoded window are confirmed by replaying price changes between two snapshots. 62.2 % lie before any snapshot of their token (all NO tokens until 09:25). 11.4 % sit between snapshots that do not replay, 8 of 40 pairs that span a reconnection |
| Replay when nothing breaks | 41 of 41 pairs of snapshots without a reconnection replay exactly |
| Trades | 4,129 rows, of which 133 are after the start; the others are history returned by the first polls. 4,045 rows lack size, price and asset. All 118 trades of the window found by a fresh read of the public tape are present |
| Receipts | 134 transactions decoded: 84 attributed to the trade row, 50 ambiguous because the trade row was thin. 332 fills, all on the two CTF exchanges, none on the earlier contracts |
| Heartbeats | 100 % with a largest gap of 12.4 s, but they prove that the process is alive, not that the websocket is. The real evidence is the largest silence between two market rows: 8.4 s |
| Disconnections | 4 in 15 hours, each followed by a new snapshot about 2 s later |
| Storage | 16.6 MB an hour, 0.40 GB a day, about 12 GB in 30 days. The state file (840 KB) is rewritten every 10 s. The `status` command reads the whole market file twice and uses 2.35 times its size in memory |

Failures that are stored as measurements, all reproduced on a copy by the second reader:

- a receipt answered `null`, an error object, or a reverted transaction becomes "not found" and is acknowledged;
- an exception other than a network error ends a loop without any error row, while the heartbeats go on;
- one truncated line in the trades file stops the collector at start-up, and the supervisor restarts it every 2 s;
- a corrupt line is skipped silently by the readers, and `status` counts it as absent.

These are not fixed here, because fixing them means replacing the running service. They are the first things to do on
the collector, with the size of its files.

## The chain monitor

22 of 22 offline tests passed before any change. The decoder equals the public data API on 942 of 942 rows and the
receipts on 30 of 30 logs. A 10-minute live run read 404 blocks without a hole: 20,100 fills, stored 8.4 s after
their block at the median and 12.0 s at the 90th percentile, no HTTP error, no alert.

| Finding | Second reader | In this pull request |
|---|---|---|
| The same fill read from the chain and from the data API was stored twice and summed: 600 USD could count as 1,200 and cross a floor | Confirmed, with a smaller reach: the candidate path does not mix the two sources, the follow-up path does | Fixed: a row held by two sources counts once (`store.tape`), and the follow-up reads that tape. Test added |
| ExchangeV3 emits the same `OrderFilled` event and was not read: 1.19 % of the fills in 1,001 blocks | Confirmed | Fixed: third address in the registry |
| Any exception other than a source error stopped the monitor; a log that cannot be decoded stopped it again at every restart | Confirmed | Fixed: such a log is journaled and passed; an unexpected exception is journaled and the loop goes on; a body that is not JSON is a failed source |
| An outage of more than 1,800 blocks made the monitor skip the whole outage. 1,800 blocks are 45 minutes at 1.5 s a block, not "about an hour" | Confirmed | Fixed: the outage is read, 600 blocks a pass, and the lag is journaled while it lasts. Test added |
| Excluded kinds of markets were excluded only the first time their token was seen | Confirmed | Fixed. Test added |
| An empty answer of the data API was read as a wallet without history, the strongest alert level | Confirmed | Fixed: it is a failed source. Test added |
| One price-history request per waiting candidate at every pass (435 calls in 10 minutes) | Confirmed | Fixed: the series is asked again when a new 10-minute point can exist |
| The 20 oldest waiting candidates could keep a new one unexamined for two hours | Shown by the second reader on a copy | Fixed: half of each pass goes to the newest. |
| A token unknown to the catalogue at first sight was excluded for good | Confirmed | Not fixed in the monitor. The new engine asks again |
| The journal chain did not cover the time of an entry, and deleting the last entries went unseen | Confirmed | Not changed in the monitor, to keep existing journals readable. The new engine chains time and sequence number |
| Fills ignore the taker fee: the cash of a fill is before fee (the fee word is not zero on 36.7 % of logs) | Confirmed | Not changed in the monitor. The new engine stores the fee |

## Contracts

Three contracts emit `OrderFilled` with the same signature today: the CTF Exchange, the Neg Risk CTF Exchange, and
**ExchangeV3 of Polymarket Protocol V2** (`0xe3333700ca9d93003f00f0f71f8515005f6c00aa`). A query by event signature
alone, without naming a contract, finds these three and no other. The two earlier exchange contracts emit no fill any
more.

On 14 November 2026 every fill of ExchangeV3 was a combinatorial position (117 of 117 in the 150 blocks of the probe,
1.5 % of all fills, and 210 of 210 in a 15-minute run of the engine: the top byte of the position identifier is 3),
that is several outcomes in one token. The catalogue does not list them as markets, and
they are not a side of one market. The official rollout page says that new single markets start trading on Protocol V2
from 23 November 2026, by phases. A reader that lists two contracts goes blind to them without any error.

The new engine therefore reads the three contracts, counts combinatorial positions apart, and at regular intervals asks
the chain for `OrderFilled` without naming a contract: an emitter outside its registry is journaled as
`unknown_exchange`.

## Other facts about the sources, measured on 14 November 2026

- The global trade feed of the data API, filtered by size, stops at 1 October 2026 00:00 UTC. The same filter applied
  to one market returns that market's whole history (354 fills of 1,000 USD or more for a market of October 2025, in
  one request). History has to be read market by market.
- A deposit shown in a wallet's activity is often not the transfer that funded it. Money that arrives as native USDC is
  swapped into the collateral token by a pool in a second transaction, and that second transaction is the one the
  activity shows. The payer read in it is the pool. The key that funded the documented Nobel 2025 account appears 39
  blocks before its deposit, in another transaction.
- A public node can answer `null` for a receipt it does not hold, and a moment later serve it. A `null` is not "no such
  transaction".
- Of five public nodes, one accepts ranges of more than 10,000 blocks on old logs; a second accepts exactly 10,000.
- The public subgraphs of the exchange are closed (deprecated endpoints); their replacement is paid.

## Other prospective data on the same machine

| Collection | Since | Content | How it was selected |
|---|---|---|---|
| Prospective collector (this audit) | 13 November 2026 | books and price changes of 20 open markets, their trades | a fixed list, not chosen on outcomes; no outcome before 2027 |
| TriAgent collector | 7 November 2026 | every trade of 5,000 USDC or more (21,983 rows on 14 November), and every account created (105,662), with the payer of the first deposit for 2.76 % of them | by size only; the payer is read at most four times in 24 hours and only for a budget of accounts |
| PolySentinel | 27 October 2026 | 555,763 trades, 51,507 wallets | a size floor plus a rotating sample of markets: not a census, sampling probability not recorded |
| Maduro and Iran file, phase 11 | 1 to 9 October 2026 | full-depth books of 650 markets and every trade of the platform (about 10.8 GB compressed) | books by wallet history and controls, trades platform-wide; rows not counted, completeness not verified |

None of these is both complete and unselected. The study of this note therefore built its own population from the
public tape, market by market ([RESULTS.md](RESULTS.md)).

## How the pieces fit together

| | Chain feed (`phi_monitor`, `phi_engine`) | Order-book collector (`livecollect`) |
|---|---|---|
| Sees | every fill of every market, with both wallets, a few seconds after its block | every price change and book of the markets it is given, 50 ms after the message, with no wallet |
| Does not see | orders that are not filled, books | who trades, and anything outside its list |
| Key of a fill | transaction hash and log index | transaction hash, wallet and side, as the data API serves them |
| Cost | one request every few seconds, whatever the number of markets | grows with the number of markets followed |

They do not overlap: the chain feed is the only writer of fills, the collector the only writer of books, and a trade of
the collector joins a fill by its transaction hash. The engine closes the loop with one command, `priority`, which
writes the markets where entries were opened in the last hours in the format the collector takes as its list. A second
collector started on that file follows the books where something is happening. It is not started automatically: one
writer per folder, and nothing replaces the running service without a check.

## Not checked

- No run of several days of any component. What a public node does over weeks is unknown.
- Whether negative-risk conversions, which emit no `OrderFilled`, are visible in these feeds.
- The local clock against a time server (the skew of 50 to 110 ms is inferred from message timestamps).
- The completeness of the October 2026 platform-wide trade archive, and why that collection stopped on 9 October.
- The external volume that holds older Iran archives was not mounted.
