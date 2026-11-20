# radar

A layer over [phi_engine](../phi_engine/README.md): each alert of the engine is sealed once, with what a reviewer needs to
judge it, into an append-only file whose lines are chained by SHA-256; later, a separate file records what happened
after it. A local page shows both. The engine decides what is an alert; the radar only describes, seals and evaluates.

It holds no key and no account, signs nothing and sends no order. It needs Python 3.10 or later and nothing else.

## Run it

```sh
cd monitoring
python3 -m phi_engine run --db ~/radar/phi_engine.sqlite &                  # the detector, unchanged
python3 -m radar watch --engine-db ~/radar/phi_engine.sqlite --out ~/radar   # seals new engine alerts every 30 s
python3 -m radar verify --engine-db ~/radar/phi_engine.sqlite --out ~/radar  # both chains, every record against its engine line
python3 -m radar evaluate --out ~/radar --fee 0.0                            # later, from public prices and resolutions
python3 -m radar dashboard --out ~/radar --html ~/radar/index.html           # open the file in a browser
python3 -m radar anchor --out ~/radar                                        # head hash, to publish wherever a date is proven
python3 -m unittest tests.test_radar -v                                      # offline tests, on alerts made by phi_engine itself
```

## A sealed record

| Field | What it says |
|---|---|
| `id`, `engine_alert_id`, `engine_line_sha256` | the record, the engine alert, and the exact line of `<db>.alerts.jsonl` it was built from |
| `trigger_utc`, `emitted_at_utc`, `sealed_at_utc` | the fill that met the class, when the engine wrote the alert, when the radar sealed it |
| `market` | question, outcome, condition id, event, family, protocol version, scheduled end |
| `wallets`, `cluster` | the wallet, and for the group classes the other wallet and the plain key behind both deposits |
| `transactions`, `sources` | fills (transaction, log index, block), deposits and their receipts, the public sources read |
| `information_at_trigger` | the state of each input: `OK`, `CAPPED_AT_1000_ROWS`, `UNRESOLVED`, `READ_AT_ALERT_TIME`, or `DATA_UNAVAILABLE` (order book, first public information); the engine's readings |
| `risk` | the class, its rule, and the rarity score when there is one; there is no single score and no probability |
| `controls`, `uncertainty` | the class's verdict on the validation events of the frozen study, its excess over the price with its 95 % interval, and how many alerts of the same class the engine raised in the 24 hours before |
| `data_latency` | seconds from the fill to the alert |
| `detector` | SHA-256 of the engine's code and reference data, and of the radar's code |
| `price_and_depth` | price at the alert and one hour before; depth is `DATA_UNAVAILABLE` unless a book snapshot is given |
| `evidence_status` | each statement the alert could be read as making, with `CONFIRMED`, `SUPPORTED`, `HYPOTHESIS`, `REFUTED` or `UNRESOLVED` |

`kind` is always `ANOMALY`. A suspicion needs a person's review of more evidence; a proof is never produced here. "The
trader acted on private information" is always a `HYPOTHESIS`, and "the linked wallets have one controller" is one too.

## What cannot change, and what proves it

- A record is written once, under one lock for the whole sealing pass, so two sealers never seal a line twice.
- `verify` recomputes the chain: an edited, removed or reordered line before the last one breaks it. The last lines
  can be checked only against a head known earlier: `anchor` records the current head and line count in
  `radar.alerts.jsonl.anchors.jsonl`, and `verify` fails if any line up to an anchor changed or if the file is shorter
  than an anchor says. Publishing an anchor somewhere dated proves that the records before it existed at that time.
- With the engine file, `verify` also fails on a record sealed twice, on a record whose engine line does not exist, and
  on a record whose class, market, trigger time or fills differ from its engine line; it counts engine lines not sealed.
- Sealing refuses an engine file whose own chain is broken. An engine line still being written (no newline yet) is
  left for the next pass, and `watch` keeps running after a failed pass.
- A record holds nothing that depends on the outcome. Evaluations go to `radar.evaluations.jsonl`, their own chain, and
  a new line is written only when an evaluation changes.

## Evaluation

The shadow purchase is made at the first price printed at or after the alert was emitted (the trigger fill's time plus
the engine's delay), never at the alerted wallet's own fill, which nobody could get after being alerted; the 1, 6 and
24 hour prices count from the emission too. The trigger fill's price is kept only as an upper bound. Without a book of
that moment the entry is `PRINTED_PRICE_DEPTH_UNKNOWN`: optimistic, and no slippage is invented. The fee convention is
all-in (one USD spent, the fee included). An evaluation is `FINAL` only when every horizon has a price and the market is
settled: the UMA status says resolved, or, when Gamma gives no status, the closed market's prices are 0 and 1. The market
must carry the record's condition id: an answer about another market is `DATA_UNAVAILABLE`.

## Notifications

Off unless `RADAR_WEBHOOK_URL` (https only), or `RADAR_TELEGRAM_TOKEN` and `RADAR_TELEGRAM_CHAT`, are set. Only records
sealed within an hour of their trigger are sent, so a first run over an old engine file sends nothing. The message names
the class and its out-of-sample result, never a person. A failed notification is reported, not retried, and never blocks
sealing.

## Limits

- The radar sees what the engine sees: Polygon fills of 1,000 USD or more on the exchanges of protocol V2, finalized
  blocks, one hop of funding. A replay of 2025 needs the data API path of `phi_monitor` or a research note, not this.
- Every class of the engine is `EXPLORATORY` or not supported out of sample (see `controls`). An alert is a reason to
  look.
- A shadow return of one alert says nothing about a class. A class is judged only on a set of alerts fixed in advance.
- The evaluation reads Gamma and the CLOB today: a market renamed or delisted is `DATA_UNAVAILABLE`, and a market of
  protocol V2 that lists `positionIds` instead of `clobTokenIds` is not evaluated yet.
- `phi_engine` writes `<db>.alerts.jsonl` without a lock or `fsync` (`store.append_alert_file`): if it dies in the middle
  of a line and later appends again, its own file is broken and sealing stops until it is repaired. Not changed here.
