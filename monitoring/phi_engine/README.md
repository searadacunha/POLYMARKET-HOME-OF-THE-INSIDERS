# phi_engine

Live surveillance of large purchases on Polymarket, from public data only. It follows each purchase through the steps
that can be observed: the funding of the wallet, the accumulation, the wallets paid by the same key, and it writes an
alert when a step fixed in advance is met.

It holds no key and no account, signs nothing and sends no order. It needs Python 3.10 or later and nothing else.

An alert is a reason to look. It describes trades and transfers. It never says who a trader is, and it never says that
a trader knew anything. What each kind of alert was worth on two years of markets is measured in
[the study of 14 November 2026](../../research_notes/realtime-intelligence-2026-11-14/RESULTS.md), and every alert
carries that result.

## Run it

```sh
cd monitoring
python3 -m phi_engine doctor                             # sources, decoder, and that no unknown exchange is trading
python3 -m phi_engine run --db ~/phi_engine.sqlite       # runs until stopped (Ctrl-C); safe to restart
python3 -m phi_engine status --db ~/phi_engine.sqlite
python3 -m phi_engine alerts --db ~/phi_engine.sqlite    # --json, --class NAME, --last N
python3 -m phi_engine journal --db ~/phi_engine.sqlite   # lags, unknown exchanges, entries left without an answer
python3 -m phi_engine replay --db ~/phi_engine.sqlite    # every alert again, from the rows kept with it
python3 -m unittest discover -s tests -v                 # offline tests
```

Everything is in the one SQLite file given by `--db`. Alerts are also appended to `<db>.alerts.jsonl`, one JSON object
a line, each line carrying the hash of the previous one. A second `run` on the same file is refused by a lock.

## What it does

| Step | Source | What is kept |
|---|---|---|
| Fills | Polygon `eth_getLogs`, `OrderFilled`, on the three exchanges | every fill: wallet, counterparty, token, side, shares, cash, fee, price, block, transaction |
| Entry | the fills just stored | the first BUY fill of 1,000 USD or more, at 0.90 or less, of a wallet on a side of a market, before the scheduled end, on a market whose outcome is not produced in public view |
| Market | Gamma `markets?clob_token_ids=` and `events/slug/` | question, outcomes, tags, family, scheduled end |
| History | data API `v2/activity` with deposits | the wallet's newest 1,000 rows, slim, with no profile field |
| Funding | Polygon receipt of each deposit of the 24 hours before; logs of the collateral tokens when the payer is a contract | the apparent payer, what the wallet received in the 10,000 blocks before, and one hop behind a pass-through key |
| Links | the store | the plain keys behind the deposits of each wallet, with the transaction |
| Alert | the store | one record per class met, with its evidence and with what the class was worth out of sample |

An entry is watched for 24 hours: some classes are met only when the wallet keeps buying. The history is read again
when the wallet buys more of the same side.

## Classes

The definitions are those of the frozen study, and the same file computes them here and there (`asof.py`).

| Class | Met when |
|---|---|
| `C1_FRESH_FUNDED_BET` | a wallet with almost no history (at most 2 other markets, 50 trades, fewer than 1,000 rows) got a deposit in the 24 hours before, and its net buying of the side reaches half of its deposits of the last 7 days |
| `C2_DORMANT_REACTIVATION` | the same, for a wallet whose last trade on another market is 60 days old or more |
| `C3_OUT_OF_CHARACTER` | the fill is 10 times the median of at least 20 earlier trades, and larger than all of them |
| `C4_COFUNDED_GROUP` | a plain key behind a deposit of the wallet is behind a deposit of another wallet that entered the same event in the 7 days before |
| `C5_RECURRENT_FUNDER` | a plain key behind a deposit of the wallet was behind a deposit of a wallet that entered a different event at least 7 days earlier |
| `C6_QUIET_FRESH_LOW` | `C1`, nobody else traded 1,000 USD on the market in the 6 hours before, and the price is 0.50 or less |
| `R1_S_FRESH_REPLICATION` | first deposit 48 hours old or less and at most two earlier large fills |
| `M1_RARITY_TOP1` | the rarity score is in the top 1 % of the reference population (against `reference/rarity_discovery.json.gz`, the discovery population of the study) |

A plain key has no code, no public name tag, fewer than 1,000 transactions, and has paid at most 10 wallets known to
the store. A contract, a tagged address or a busy key is a service used by many people and never links two wallets.
When the tags cannot be read, the address is kept out: unknown is never a link.

## An alert

Five parts, always.

- **MARKET**: question, side, price paid at the alert, family, scheduled end, identifiers.
- **WALLETS**: the wallet, what it bought, its deposits with their apparent payer and what kind of address that is,
  the plain keys behind them, and the linked wallet for the group classes.
- **ANOMALY**: what is unusual, in a sentence, then separate readings: the wallet against its own past, its funding,
  the wallet against the other traders of the market, the timing, and the rarity score with its parts. Then other
  explanations to rule out. There is no single score and no probability.
- **EVIDENCE**: the fills with transaction, log index and block; the receipts of the deposits with a hash of what was
  read; what the data cannot say (history capped, tags and transaction counts read at the time of the alert).
- **VALIDATION**: the verdict of the frozen study for this class, with its numbers, or `EXPLORATORY`.

## What it refuses to conclude

- A wallet whose history does not show the entry yet is not "a wallet without history". The data API is a few minutes
  behind the chain: the entry waits and is read again, up to about an hour, then is journaled as left without an answer.
- A receipt that a node does not serve is not "no payer". The entry waits.
- A token the catalogue does not know yet is asked again later, and never holds back the fills behind it.
- A combinatorial position of Protocol V2 (several outcomes in one token) is not a side of a market: counted apart.
- A fill on a contract outside the registry cannot be read at all: a periodic query without any contract name finds
  such a contract and journals it as `unknown_exchange`.
- After an outage nothing is skipped: the blocks are read, 600 a pass, and the lag is journaled while it lasts.

## With the order-book collector

The engine sees who trades and not the books; `monitoring/livecollect` sees the books of a list of markets and not who
trades. `python3 -m phi_engine priority --db FILE --out markets.json` writes the markets where entries were opened in
the last hours, in the format the collector takes as `--markets`. A second collector started on that file, in its own
folder, follows the books where something is happening. Nothing starts it automatically.

## Limits

- Fills under 1,000 USD open no entry. A purchase split into small fills is seen only through the wallet's history,
  once a larger fill has opened an entry.
- The history of a wallet is its newest 1,000 rows. Above that, the wallet cannot be "thin", and "larger than every
  earlier trade" means every trade among those rows.
- Tags and transaction counts of a payer are read when the alert is built, not as of the trade.
- Funding is followed on Polygon. Money that arrives through a bridge or an exchange stops there.
- The engine only sees what happens while it runs or what it catches up afterwards. A Mac that sleeps is behind, and
  says so in the journal when it wakes.
- There is no list of informed accounts anywhere. No precision or recall "on insiders" exists, and none is claimed.
