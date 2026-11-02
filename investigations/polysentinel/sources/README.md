# PolySentinel

Local, read-only surveillance of public Polymarket activity. It collects trades and market metadata, flags unusual behaviour, seals its decisions in a hash chain, and produces investigation files an analyst can verify on-chain.

It holds no key and no account, sends no orders, and calls no paid service. An alert is a reason to look, never a finding of wrongdoing: a score or a category says nothing about a person's identity or about private information.

## What it does

- **Collection.** Market catalogue, a global trade feed filtered by size, and a rotating set of followed markets. Raw responses are kept compressed with their request parameters, and gaps are recorded instead of being hidden.
- **Frozen rules.** The first detector (`polysentinel/signals.py`) stays unchanged so that every later comparison has a fixed reference.
- **Prospective registry.** Decisions are sealed in an append-only, hash-chained journal before they enter the database, with the exact inputs needed to replay them.
- **Signal engine (shadow mode).** A separate engine (`signal_engine/`) combines market information risk, wallet behaviour, position context, collective behaviour and verified funding links. It compares each measurement with an empirical control group. See [docs/SIGNAL_ENGINE.md](docs/SIGNAL_ENGINE.md).
- **Fund flows (shadow mode).** `signal_engine/fund_flow/` follows a wallet's collateral in both directions with a stated level of proof for each relation, and stops where public data stops. It changes no category or score. See [Fund flows](docs/FUND_FLOWS.md).
- **Dashboard.** A local page at `http://127.0.0.1:8767/`, with the shadow queue at `/reports/signal-engine-queue.html` and the state of each component at `/reports/etat-polysentinel.html`.

## Quick start

Python 3.12 is required. On macOS the service runs under launchd.

```sh
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.lock
.venv/bin/python -m polysentinel doctor
.venv/bin/python -m polysentinel start
.venv/bin/python -m polysentinel status
```

| Command | Purpose |
|---|---|
| `python -m polysentinel doctor` | Check the environment |
| `python -m polysentinel start`, `stop`, `restart` | Control the background service |
| `python -m polysentinel status`, `logs`, `dashboard` | Inspect it |
| `python -m polysentinel investigate ADDRESS_OR_EVENT` | Queue a bounded investigation |
| `python -m polysentinel replay --as-of 2026-10-27T17:00:00Z` | Rebuild decisions from known observations, without network or alerts |
| `python -m signal_engine.service once` | One bounded run of the shadow engine |

Configuration lives in `config.json` and `config/`. The storage quota, free-disk floor and request budgets are explicit, and nothing is deleted automatically.

## How to read the output

| Term | Meaning |
|---|---|
| Market information risk | Who decides the outcome and who could know it early. A structural prior, not evidence about a trader. |
| `ANOMALOUS` | Unusual against an empirical comparison group. |
| `CORROBORATED_BEHAVIOR` | The same, supported by another wallet or by observed funds. |
| `INSUFFICIENT_EVIDENCE`, `BASELINE_INSUFFICIENT` | Not enough data to say anything. |

Every file lists competing explanations and missing data, and its conclusion is limited to its evidence.

## Limits

- There is no ground truth. Publicly named accounts are allegations, so precision, recall and false positive rates are not available and are not claimed.
- Coverage is partial: taker-side rows, a size filter on the global feed, and a rotating sample of small trades.
- First seen by the collector is not account creation. Concentration can be overstated for wallets active elsewhere.
- Public information is only partly covered: the absence of an article proves nothing.
- A local clock orders events; it is not an independent timestamp.
- A Mac asleep or offline collects nothing; such periods are recorded as gaps.

## Tests

```sh
.venv/bin/python -m unittest discover -s tests
```

Fixtures are synthetic except `tests/fixtures/chain_receipts_sample.json`, which holds decoded public on-chain fills used to test position reconstruction. Passing tests prove mechanics, not an ability to detect private information.

## Documentation

[Signal engine](docs/SIGNAL_ENGINE.md), [Historical case protocol](docs/HISTORICAL_CASE_PROTOCOL.md), [Rules](docs/REGLES.md), [Collection](docs/COLLECTE.md), [Sources](docs/SOURCES.md), [Storage](docs/STOCKAGE.md), [Third-party notices](THIRD_PARTY_NOTICES.md).
