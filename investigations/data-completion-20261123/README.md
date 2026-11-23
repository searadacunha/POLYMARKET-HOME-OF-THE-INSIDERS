# Data completion and forensic reconstruction (2026-11-23)

## Objective

Make the repository's Polymarket evidence more complete and independently reproducible: measure what data exists and what is missing, recover what public sources still allow, rebuild the f2020 cohort's trades and positions from chain logs in exact integer units, and reconcile the money. This investigation builds on three open pull requests without changing them: [PR 109](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/109) (radar and benchmark), [PR 110](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/110) (weekly funding) and [PR 111](https://github.com/searadacunha/POLYMARKET-HOME-OF-THE-INSIDERS/pull/111) (four reconstructed bets). The competitor benchmark of PR 109 is not repeated.

## Baseline

| Reference | Commit |
|---|---|
| `main` | `3faf43ae4b7bf8859afe2ab3c1543aa01169608a` |
| PR 109 `research/radar-asof-benchmark-20261121` | `f34a8bff95eaa297f7bb7e8f42093edd23a9725d` |
| PR 110 `investigation/weekly-funding-intelligence` | `8b633048290e7174945bc811b16cf0b11b4d8ceb` |
| PR 111 `research/f2020-bet-reconstruction-20261122` | `58c964b5aa5063d90e4dd7d72dab50d916a81bd7` |

The three PR heads were read as pinned Git objects (`git show <sha>:<path>`). Their own verifiers and tests were run read-only in existing clones at those exact heads.

## Method

1. **Inventory.** `scripts/audit_data_coverage.py` expands every `investigations/*/data_manifest.json` into file-level rows, re-hashes imported files, looks up local-only files at their recorded origin and joins every recorded SHA-256 with the local encrypted backup index. `scripts/data_gap_matrix.py` turns this and every dataset of this session into `results/data_gap_matrix.csv`, with explicit statuses (`COMPLETE`, `PARTIAL`, `UNAVAILABLE`, `LOCAL_ONLY`, `CORRUPT`, `UNVERIFIED`, `UNKNOWN`). A row without a measurable denominator keeps `UNKNOWN`.
2. **Contract semantics.** Exchange deployment and first-fill blocks, event signatures (topic0 recomputed), fee rules per contract generation, taker semantics, position contracts and collateral were established on receipts and are recorded in `results/contract_semantics.json`. Public data sources were probed for their real limits (`results/source_probes.json`).
3. **Cohort logs.** `scripts/ledger_collect.py` reads, for the 153 distinct trading addresses of the archived f2020 cohort (158 bettor records), every finalized Polygon log that moves value for them: OrderFilled on the five exchanges (order owner = maker), Conditional Tokens and Neg Risk Adapter split, merge, redeem and convert events, the 2026 collateral adapters' events, and ERC-1155 and ERC-20 transfers from or to each account. The window runs from the first block with V1 exchange code to a finalized block recorded in the plan. A range is accepted only when answered in full and below half the provider's result cap; a refusal is never an empty range. Every accepted range is stored with its SHA-256 in a checkpoint, so collection resumes.
4. **Ledger.** `scripts/ledger_build.py` and `scripts/ledger_report.py` rebuild, per account and transaction (in chain order), the net collateral and position deltas from the actual transfers, classify the transaction from its events, attribute it to a market (condition) and book every outcome token at average cost with exact fractions. Fees are therefore inside the cash flows and never subtracted twice; V1 fee refunds are included. Deposits, withdrawals and wraps never enter trading PnL. A burn's collateral goes to each burned token at its official payout value; only a remainder is spread over tokens whose payout is unknown, and that is flagged. Shares sent to another wallet leave at cost (`trading_pnl` = realized + unrealized; `net_position_pnl` = cash + inventory value keeps them as an outflow). Settled inventory is valued with the official on-chain payout vector (`ConditionResolution`); open inventory is marked with the last CLOB price point at or before the valuation time, or stays `UNKNOWN`. `realized + unrealized - transfer_out_cost = cash_pnl + inventory_value` is an arithmetic self-check only. The independent checks are: collateral reconciled against `balanceOf` at the window's two ends for every account and token; a deterministic sample of position tokens against ERC-1155 `balanceOf` at the end block; the collateral of every redemption against the official payout value of the redeemed shares; the collateral of every trade against the verified fee rules of its fills; Gamma outcome prices against on-chain payouts; and the Data API as an independent count of trades.
5. **Regression.** The same code, run on PR 111's four wallets, is compared market by market with PR 111's published results (`scripts/regression_pr111.py`).
6. **Funding.** `scripts/weekly_table.py` reshapes PR 110's frozen weekly sets into the requested columns, with all-period counts as set unions. PR 110's Ethereum log streams were recovered for the 23 weeks W16 to W38 with PR 110's own collector, unchanged; this does not modify PR 110's frozen inputs. `scripts/relay_v2_history.py` resumed PR 110's Ethereum-to-Polygon Relay history screen on the v2 endpoint before its announced Sunset, and `scripts/relay_screen.py` classifies every history without ever reading a rate-limited history as empty; a page counts only when it carries a list of requests.
7. **Cross-chain and prospective data.** The three Arbitrum passages of PR 109 were re-collected on three or four public providers (`results/cross_chain_routes.csv`). Prospective data availability and residual leakage paths of the PR 109 evaluator were audited without code changes (`results/prospective_data_quality.csv`, `results/leakage_and_comparison.json`).

## Reproduce

From a full clone of the repository on this branch:

```bash
I=investigations/data-completion-20261123
python3 -m unittest discover -s $I/tests                      # synthetic fixtures, no network
python3 $I/verify.py                                          # offline replay; SKIPPED_MISSING_INPUT without the raw logs
# full collection (public keyless endpoints; resumable)
python3 $I/scripts/ledger_collect.py --out RAW/ledger
python3 $I/scripts/ledger_sources.py --raw RAW/ledger --out RAW/sources
python3 $I/scripts/ledger_report.py --raw RAW/ledger --sources RAW/sources --results $I/results
python3 $I/scripts/regression_pr111.py --repo . --summary RAW/results_pr111/wallet_position_summary.csv --out $I/results/regression_pr111.json
python3 $I/scripts/weekly_table.py --repo . --eth-csv $I/results/eth_weeks_coverage.csv --results $I/results
python3 $I/scripts/data_gap_matrix.py --repo . --results $I/results
```

Raw logs, caches and agent working files stay local (`data_manifest.json` lists their sizes and SHA-256). The Relay v2 endpoint announced a Sunset of 2026-11-24T00:00:00Z (HTTP `Sunset` header) and v3 needs a key, so the Relay screen will not be re-collectable after that time; its page log is append-only and the published screen states how many exchanges it classifies.

## Licences

All code here is original. Contract semantics come from on-chain receipts and published interfaces. The reviewed public indexers were read for their published interfaces only: `Polymarket/polymarket-subgraph` (LGPL-3.0), `psyberck/polymarket-subgraph-v2` (MIT), `enviodev/polymarket-v2-indexer` (no licence published) and `wietrade/poly_data` (GPL-3.0). No code was copied from them.
