# phi_monitor

Read-only surveillance of public Polymarket activity. It watches every fill of the exchanges on Polygon, notices when a
quiet, low-priced outcome is suddenly bought up, works out who did the buying, and writes an alert that states its reasons.

It holds no key and no account, signs nothing and sends no order. It needs Python 3.10 or later and nothing else.

An alert is a reason to look. It describes a pattern of trades in public data. It never says who a trader is, and it never
says that a trader knew anything.

## Run it

```sh
cd monitoring
python3 -m phi_monitor doctor                                   # checks each source and the on-chain decoder
python3 -m phi_monitor run --db ~/phi_monitor.sqlite            # runs until stopped (Ctrl-C); safe to restart
python3 -m phi_monitor status --db ~/phi_monitor.sqlite
python3 -m phi_monitor alerts --db ~/phi_monitor.sqlite
python3 -m unittest discover -s tests -v                        # offline tests
```

`run --minutes 30` stops by itself; `run --once` does a single pass. Everything is kept in the one SQLite file given by
`--db`. Stopping and restarting loses nothing: the position in the chain and every page already read are checkpointed
with the rows they produced. After an outage the missing blocks are read, 600 at a pass, and the lag is written to the
journal while it lasts. (Until 14 November 2026 an outage of more than 45 minutes was skipped whole.)

To replay a past market in the order things happened:

```sh
python3 -m phi_monitor backtest --db /tmp/nobel.sqlite \
    --token 75406677405586796507165996816755205915219135539748390183994296030461533919844 \
    --start "2025-10-09 12:00" --end "2025-10-10 09:00"
python3 -m phi_monitor replay --db /tmp/nobel.sqlite            # same result again, from stored rows, no network
```

## What it does, step by step

| Step | Source | What is kept |
|---|---|---|
| Watch | Polygon `eth_getLogs` on the three exchange contracts, `OrderFilled` | every fill: wallet, token, side, shares, cash, price, block, transaction |
| Trigger | the fills just stored | a candidate when a buy of 100 USD or more prints at three times a low reference price |
| Resolve | Gamma `markets?clob_token_ids=` and `events/slug/` | the market, its two tokens, its tags (sports matches, price ladders and similar are dropped) |
| Confirm | CLOB `prices-history`, 10-minute points | the official rule: 6-hour median at 0.15 or less, then three times that and at least 0.10 more |
| Tape | data API `v2/trades?condition=...&taker_only=false` | every buy and sell of that market since just before the move |
| History | data API `v2/activity?user=...&end=...` | what the leading buyer had done strictly before its first buy |
| Funding | Polygon logs of USDC, USDC.e and pUSD received by that wallet | who paid it in the 72 hours before, described by behaviour only |
| Alert | the local store | one record with reasons, transaction hashes and the other explanations to rule out; one journal entry |

The decision itself (`detect.evaluate`) reads only the local store, and only rows dated at or before the time it is asked
about. Run it again on the same store and it gives the same answer; `replay` does exactly that.

## Alert levels

| Level | Meaning |
|---|---|
| `LONELY_THIN` | one wallet supplied at least half of the buying in the first 15 minutes of the move, and that wallet had traded two markets or fewer before |
| `LONELY` | the same concentration, by a wallet with a trading history |
| `THIN` | a wallet with almost no history led the buying, but supplied less than half of it |

A move bought by many established wallets raises nothing: that is what public news looks like on the tape.

When a second wallet of the same event was paid by the same plain key, the alert lists it under `cluster`. Only a direct
transfer from a key with few transactions counts. A bridge, a contract, an exchange hot wallet or any key with a
thousand transactions or more is a service used by many people and is never treated as a link between two accounts.

How often each level was followed by a win, and how that compares with the price at the time of the alert, is measured
in [BACKTEST_RESULTS.md](../BACKTEST_RESULTS.md) and [PATTERN_RESEARCH.md](../PATTERN_RESEARCH.md). Those rates describe a
class of trades over a past period. They are not the probability that a given account is informed.

## What was measured about the sources

Measured on 13 November 2026; details and limits in [LIVE_DETECTION.md](../LIVE_DETECTION.md).

- One `OrderFilled` log is one row of the data API (`taker_only=false`): identical wallet, token, side, size and price on
  every transaction compared. The `doctor` command repeats that comparison.
- Reading the chain every few seconds sees every fill, about 2.5 seconds after its block.
- The data API answers from a 5-minute cache. Polled plainly, its global trade feed showed about one fill in six.
- The public market WebSocket carries prices and sizes but no wallet. The authenticated user channel shows only one's own
  orders and is not used here.

## Limits

- The validated pattern covers Yes/No markets whose outcome is not produced in public view. Match-level sports, price
  ladders, weather and counting markets are excluded on purpose.
- A market is examined when a buy prints far above its recent prices. A slow accumulation that never moves the price
  raises nothing.
- Wallet history comes from the data API and is capped at the last 500 rows before the buy.
- Funding is read one hop back, on Polygon. Money that arrives through a bridge or an exchange is marked as such and its
  origin is left unknown.
- There is no ground truth about private information. No precision or recall "on insiders" exists, and none is claimed.
- The monitor only sees what happens while it runs. A Mac that is asleep collects nothing.
- Public RPC endpoints can fail or throttle. Calls fall back across several endpoints; a failed pass leaves the checkpoint
  where it was and is retried.
- The cash of a fill is before the taker fee.
- The monitor follows one mechanism, a quiet price lifted by one wallet. Large purchases that do not move the price,
  funding links and bets out of a wallet's character are followed by [phi_engine](phi_engine/README.md), which reads
  the same chain feed.

## Changes of 14 November 2026

Found by an audit on a copy, each re-derived by a second reader
([findings](../research_notes/realtime-intelligence-2026-11-14/SYSTEM_AUDIT.md)), each with a test:

- the third exchange (ExchangeV3 of Polymarket Protocol V2) is read;
- a fill held both from the chain and from the data API counts once;
- an outage is caught up instead of being skipped;
- an excluded kind of market stays excluded after its token is known;
- an empty answer about a wallet that has just traded is a failed source, not a wallet without history;
- a log that cannot be decoded, or an unexpected error, is journaled and no longer stops the monitor;
- prices are asked again only when a new 10-minute point can exist, and new candidates are no longer kept waiting by
  old ones.
