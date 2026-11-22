# changenow_weekly

Reads public chains for one ISO week and lists the Polymarket trading wallets that received funds from, or sent funds to, an address attributed to ChangeNOW, with every hop of each path. It holds no private key, sends no transaction and needs Python 3.10 or later and nothing else.

Output: [`reports/changenow/`](../../reports/changenow/WEEKLY_LEADERBOARD.md). Method and limits: [`METHODOLOGY.md`](../../reports/changenow/METHODOLOGY.md).

A flow from a ChangeNOW address shows that the service's infrastructure paid or was paid. It never shows an individual exchange order, an identity, or an offence.

## Run it

```sh
cd monitoring
python3 -m unittest tests.test_changenow_weekly -v                     # offline tests
export ETHERSCAN_API_KEY=...                                           # optional, free plan
python3 -m changenow_weekly run --raw ~/changenow-raw --week 2026-W46  # read, analyse, write the report
python3 -m changenow_weekly update --raw ~/changenow-raw               # current week, and last week until it is frozen
python3 -m changenow_weekly report --raw ~/changenow-raw --week 2026-W46   # rebuild the files from the analysis, offline
python3 -m changenow_weekly verify                                     # SHA-256 of every frozen week, offline
python3 -m changenow_weekly reconcile --week 2026-W46                  # read every published transaction again, by hash
python3 -m changenow_weekly registry --raw ~/changenow-raw             # read today's public tags, then rebuild registry.csv
```

`--raw` is a folder outside the repository. It holds the raw transfers by block range, which are the checkpoints: a run that stops loses at most one file, and the next run reads only blocks after the last range on disk.

Without `ETHERSCAN_API_KEY`, native transfers on Ethereum are not read and `COVERAGE.md` says so. The key is read from the environment only and is never written anywhere.

## Every six hours

- GitHub: no scheduled workflow is installed in this repository. The six-hourly job written with this module (read, test, verify, push `reports/changenow` to a data branch and open a pull request, never to `main`) was left out when the module was first published with the withdrawal census of [`research_notes/changenow-withdrawals-2026-11-22`](../../research_notes/changenow-withdrawals-2026-11-22/); adding it is a separate decision.
- Locally on macOS: `local/update.sh` does the same from a checkout and pushes nothing. `sh local/install_launchd.sh [env file]` registers it every six hours; run that installer yourself.

## Files

| File | Role |
|---|---|
| `chainio.py` | Block-window reads over public JSON-RPC, Multicall3, Etherscan lists with their two guards |
| `registry.py`, `registry.csv`, `registry_evidence.json`, `registry_labels_refresh.json` | Addresses associated with ChangeNOW, their tier and its basis, the role rules, the last reading of public tags |
| `collect.py` | Resumable streams of raw transfers |
| `pipeline.py` | Recognised tokens, measured roles, deposit addresses, payouts and customer deposits |
| `polymarket.py` | Wallet types, key ownership read on-chain, public profile and activity |
| `trace.py` | The backward walker, the Relay order match, the lower bound for mixed funds |
| `analyse.py` | One week end to end, written to one analysis file |
| `prices.py` | USD value at transaction time |
| `reconcile.py` | Second reading of every published transaction, by hash, before a week is sealed |
| `report.py` | Every published file, the freeze and its check |

The wallet classifier, the contract names and the Keccak and Deposit Wallet formulas are imported from the archived investigations of this repository (`investigations/polysentinel`, `investigations/changenow-outflows`), which are not modified.
