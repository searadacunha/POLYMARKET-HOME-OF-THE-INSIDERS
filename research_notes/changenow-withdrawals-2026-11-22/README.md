# Polymarket withdrawals to ChangeNOW

Which Polymarket trading wallets sent money to an address attributed to ChangeNOW, how much, by which route, and what they had won before. This note counts outflows only: money leaving a Polymarket wallet toward the service. Funding coming from ChangeNOW is measured elsewhere ([PR 110](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/110), [`investigations/changenow-polymarket`](../../investigations/changenow-polymarket/)) and is not mixed with it.

**State on 2026-11-22: code only.** The collectors, the classification, the accounting and their offline tests are here; the census itself is still being read from the chains, so `results/`, `data/`, `SHA256SUMS` and the replay by `verify.py` are not published yet and no figure is claimed. They will be added to this note when the weeks are read.

When they are, start with [`results/REPORT.md`](results/REPORT.md). Every transfer is in [`results/changenow_outflows.csv`](results/changenow_outflows.csv) with its transactions and explorer links, the wallets are ranked in [`results/wallet_rankings.csv`](results/wallet_rankings.csv), the weeks in [`results/weekly_outflows.csv`](results/weekly_outflows.csv), and the accounts worth a closer look are in [`results/interesting_wallets.md`](results/interesting_wallets.md).

Sending money to ChangeNOW is lawful and common. A withdrawal found here is a fact about wallets and transactions. It says nothing about a person, an exchange order or inside information.

## Reproduce

Offline, from the snapshot in `data/` (no network, a few seconds):

```sh
python3 -I research_notes/changenow-withdrawals-2026-11-22/tests/test_withdrawals.py
python3 -I research_notes/changenow-withdrawals-2026-11-22/verify.py
```

From public chains and APIs (hours; raw rows go to a folder outside the repository):

```sh
cd research_notes/changenow-withdrawals-2026-11-22
python3 scripts/census.py --raw ~/cnw-raw --chains 137 --week 2026-W46            # Polygon, one ISO week (repeat --week)
python3 scripts/census.py --raw ~/cnw-raw --chains 1 --env-file <file with ETHERSCAN_API_KEY=...> --week 2026-W46
python3 scripts/relay_api.py --raw ~/cnw-raw --from-census                        # Relay's record of unresolved fills (keyless v2, retired 2026-11-24)
python3 scripts/relay_api.py --raw ~/cnw-raw --check                              # read on chain the origins it names
python3 scripts/build.py --raw ~/cnw-raw --out /tmp/cnw-results                   # classes, values, tables
python3 scripts/bets.py --raw ~/cnw-raw --outflows /tmp/cnw-results/changenow_outflows.csv --controls 5
python3 scripts/build.py --raw ~/cnw-raw --out results                            # again, with the bets
python3 scripts/report.py                                                          # REPORT.md and interesting_wallets.md
python3 scripts/snapshot.py --raw ~/cnw-raw                                        # copy the evidence used into data/, write SHA256SUMS
```

## Files

| Path | Role |
|---|---|
| `scripts/census.py` | One ISO week, withdrawal direction only, on top of [`monitoring/changenow_weekly`](../../monitoring/changenow_weekly/) (collector, ChangeNOW register, deposit-address rules, Polymarket wallet classifier, backward walker) |
| `scripts/relay_api.py` | Relay's own record of the fills the chain did not tie to an origin, and the on-chain check of what it names |
| `scripts/build.py` | Evidence classes, deduplication, USD values, weekly table, rankings, bets before each withdrawal |
| `scripts/pnl.py` | Per-market accounting of a wallet's bets, copied from [PR 111](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/111) unchanged, plus the state of a wallet at a given time |
| `scripts/bets.py` | Activity feed, Gamma markets, balance before each debit, comparable traders |
| `scripts/report.py`, `scripts/snapshot.py` | The two Markdown reports; the evidence snapshot and its checksums |
| `data/` | Evidence used by the tables, with `SHA256SUMS` |
| `tests/`, `verify.py` | Offline tests and replay |
