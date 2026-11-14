# Early detection, 13 November 2026

Evidence, scripts and checks behind the five reports at the root of the repository:
[AUDIT_20261113.md](../../AUDIT_20261113.md), [NEW_LEADS.md](../../NEW_LEADS.md),
[PATTERN_RESEARCH.md](../../PATTERN_RESEARCH.md), [LIVE_DETECTION.md](../../LIVE_DETECTION.md) and
[BACKTEST_RESULTS.md](../../BACKTEST_RESULTS.md). The monitor itself is in [monitoring](../../monitoring/README.md).

Everything here comes from public, keyless sources read on 13 November 2026: the Polymarket data API, Gamma and CLOB
endpoints, and Polygon JSON-RPC. No profile text is stored. An address is not a person.

## Check it

```sh
python3 -I research_notes/early-detection-2026-11-13/verify.py     # offline, reads only
(cd monitoring && python3 -m unittest discover -s tests -v)       # offline
```

`verify.py` recomputes the figures of the reports from the files below, and refuses any address or transaction hash
printed in a report that is not found in an evidence file.

## Files

| File | What it holds | How it was made |
|---|---|---|
| `data/machado_tape_20251009T2000_20251010T0900.csv` | Every maker and taker row of the Machado market from 20:00 UTC on 9 October to 09:00 UTC on 10 October 2025 | `scripts/tape.py` (data API, cursor to the end: 15,598 rows for the whole market) |
| `data/machado_top45_accumulators.csv` | The 45 largest net buyers before the announcement, with their history as of their first buy | `scripts/nobel_census.py`, `scripts/baseline.py`, `scripts/nobel_enrich.py` |
| `data/c7_funder_ledger.csv`, `c7_funder_ledger_summary.json` | Every native USDC transfer of the C7 funder key, with running balance | `scripts/c7_*.py`, Polygon logs by JSON-RPC, no explorer |
| `data/c7_withdrawals_onchain.csv`, `c7_safe_owners.csv` | The 16 withdrawals and the owners of the 8 Safes, read on chain | same |
| `data/c7_buy_cost_comparison.json` | Purchases stated in `followup-20261113` against the complete tape | from the two files above |
| `data/second_group_circuit_transfers.csv` | The 61 transfers between the addresses of the second group | `scripts/second_group.py`, step `circuit` |
| `data/payer_36626_flows.json`, `nobel_owner_keys_upstream.json`, `nobel_new_accounts_funding.json`, `second_cluster_accounts.json` | The hub key, the two owner keys and the three accounts | `scripts/second_group.py` |
| `data/nobel_top_buyers_direct_graph.json`, `nobel_direct_account_links.json` | Direct transfers between the largest buyers | `scripts/second_group.py`, step `graph` |
| `data/bt_nobel_result.json` | Replay of the night by the monitor, with the cluster timeline | `python3 -m phi_monitor backtest`, see [monitoring](../../monitoring/README.md) |
| `data/latency_run1.json`, `latency_run2.json`, `rest_probe.json`, `ws_reconnect.json` | Two ten-minute measurements of every public channel, and probes of the REST endpoints | measurement scripts of a sub-agent, not archived here; figures in LIVE_DETECTION.md |
| `audit/maduro-iran/` | Claim register, recomputations, 134 receipts and notes on the Maduro and Iran files | a sub-agent; two points re-checked, see AUDIT_20261113.md |
| `audit/ballon-c1c7/` | Recomputations, receipts and case registry for Ballon d'Or and C1 to C7 | a sub-agent stopped before writing notes |
| `study/` | The frozen study: plan, code, lock, controls, table, registry, results | see PATTERN_RESEARCH.md |

## How the pieces were produced, honestly

- The Nobel tape, the census, the second group and the monitor replay were run by the lead session. The steps of the
  second group were run one by one and then gathered into `scripts/second_group.py`; that file was checked offline but
  not re-run from start to end.
- The chain replay of the C7 funder and the two audits were run by sub-agents. Their sessions were cut off three times
  by a usage limit; what is archived is what they had written to disk. Their scripts are kept as run, with their
  original paths.
- Addresses in the scripts are resolved from data by prefix with a uniqueness check, or come out of a previous step.

## Limits

- One market was examined in depth. The other files of the repository were audited from their evidence, not re-traced.
- Bridge credits are not followed to their origin chain: the Relay record API is retired on 24 November 2026 and was
  not used here.
- Positions are measured at 09:00:00 UTC on 10 October 2025; later purchases are outside the tables.
- A transfer between two accounts shows a financial relationship. Who decides for each account is not visible on chain.

## Added on 14 November 2026

| File | Content |
|---|---|
| `study/audit/BLIND_AUDIT.md` | Blind audit of the frozen study by four auditors, each major finding given to a refuter; reproduction from fresh copies |
| `scripts/cluster_base_rate.py`, `data/cluster_base_rate.json` | Exploratory, after the verdict: the 48 alerts of the tested class replayed by the monitor, and how many come with a funded group |
| `data/replay_window_probe.json` | Why nine hours of price history lost one alert of 48, and 14 days do not |
| `data/live_run_20261114.json` | Second live run of the monitor, store on the internal disk |
