# Real-time intelligence: audit, a study of large purchases, and a live engine

14 November 2026. This note answers one question: can unusual trading on Polymarket be noticed while it happens, and
is what gets noticed worth anything?

It contains an audit of what was running, a register of everything already tried, a study frozen before any rate was
computed, and an engine that applies the study's definitions to the live chain.

| Page | What it holds |
|---|---|
| [SYSTEM_AUDIT.md](SYSTEM_AUDIT.md) | the two collectors and the data they really hold, the defects found, what this pull request fixes |
| [SIGNALS_REGISTER.md](SIGNALS_REGISTER.md) | 66 signals examined before this note, with their status, and the experiments that must not be rerun |
| [HYPOTHESES.md](HYPOTHESES.md) | what is tested here and why it is not the earlier tests |
| [RESULTS.md](RESULTS.md) | the frozen study: population, classes, tests, verdicts, limits |
| [FINANCIAL_LINKS.md](FINANCIAL_LINKS.md) | how the payer of a deposit has to be read, and the groups of wallets paid by one key |
| [LIVE_RUN.md](LIVE_RUN.md) | the engine on the live chain: lateness, coverage, alerts raised |
| [SOURCES_AND_TOOLS.md](SOURCES_AND_TOOLS.md) | public sources and open-source tools, re-evaluated |
| [../../monitoring/phi_engine/README.md](../../monitoring/phi_engine/README.md) | the engine itself |

An address is not a person. "Linked" means that a transfer was read on chain. A class of trades that wins more than
its price says is a class that was profitable over a period: it says nothing about one account, and nothing here is a
finding of insider trading.

## Reproduce

```sh
python3 -I research_notes/realtime-intelligence-2026-11-14/verify.py     # recomputes the results from the published tables
(cd monitoring && python3 -W error -m unittest discover -s tests -v)      # monitor and engine, offline
(cd monitoring && python3 -m phi_engine doctor)                           # live sources and exchange registry (network)
```

`study/` is the frozen study as it was computed: plan, code, lock, amendment, positive controls, registry of every
test, results, the reports of the pre-freeze audits, and which code produced which data (`study/code/PROVENANCE.md`). `data/study_export/` holds the alert and control tables, without any wallet address, and the funding links of
the two keys that paid two wallets or more (`financial_links.csv`, which names those keys and wallets). The raw collections
(2.85 million fills, 40,558 wallet histories, 28,600 deposit receipts, 19,000 windows of transfers read on chain) stay on the machine that collected them; the collectors
in `study/code/` read them again from the public sources.
