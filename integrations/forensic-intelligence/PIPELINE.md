# Forensic workflow map

Generated from `pipeline.json` by `pipeline_manifest.py`; edit the JSON, not this file.

Map of the modules that already exist for each stage. Nothing here is merged or rewritten. Paths are relative to the repository root. 'checked' lists only commands run offline when this map was written (2026-11-20); everything else is described from the code, not from a run.

## 1. Polymarket and chain data

| Module | Functions |
| --- | --- |
| `monitoring/phi_monitor/collect.py` | `watch_chain`, `fetch_tape`, `fetch_prices`, `baseline`, `funding` |
| `monitoring/phi_monitor/chain.py` | `fills`, `transfers_to`, `account_kind` |
| `monitoring/phi_engine/feed.py` | `watch`, `open_entries` |
| `monitoring/phi_engine/enrich.py` | `history`, `chain_inflows` |
| `monitoring/livecollect/__main__.py` | `collect`, `status` |

Entry points:

- `cd monitoring && python3 -m phi_monitor run --db X`
- `cd monitoring && python3 -m phi_engine run --db X`
- `python3 -m monitoring.livecollect collect --markets markets.json --out DIR`

Input: Polygon eth_getLogs (OrderFilled, ERC-20 Transfer), Polymarket data API, Gamma and CLOB websocket

Output: three separate stores: phi_monitor SQLite (fills, prices, baselines, funding, alerts), phi_engine SQLite (fills of 1,000 USD or more and watched wallets, entries, deposits, links, alerts), livecollect files

Tests:

- `monitoring/tests/test_engine.py`
- `monitoring/tests/test_units.py`
- `integrations/quantitative_engine/tests/test_engine.py`

Checked offline when this map was written:

- cd monitoring && python3 -B -W error -m unittest discover -s tests: 93 tests OK (fake network and committed fixtures only)

Known gap: No single collector: three collectors pull overlapping fills, tape and prices into three stores that are not interchangeable. Live collection was not run here. livecollect has no test under monitoring/tests except the decoder conformance test.

## 2. Normalisation

| Module | Functions |
| --- | --- |
| `monitoring/phi_monitor/chain.py` | `decode_fill` |
| `monitoring/phi_engine/feed.py` | `decode` |
| `monitoring/livecollect/decode.py` | `decode_logs` |
| `monitoring/phi_monitor/store.py` | `tape` |
| `integrations/quantitative_engine/executions.py` | `economic_executions` |
| `integrations/forensic-intelligence/ledger.py` | `validate_edge`, `canonical_edges` |
| `integrations/forensic-intelligence/monitor_bridge.py` | `funding_to_edges`, `normalise_alert` |

Entry points:

- `library functions only`

Input: raw OrderFilled logs; monitoring funding rows; alert bodies

Output: fill dicts (floats in chain and feed, raw integer strings in livecollect); evidence edges; flat alert records

Tests:

- `monitoring/tests/test_decoder_conformance.py`
- `monitoring/tests/test_engine.py`
- `monitoring/tests/test_units.py`
- `integrations/forensic-intelligence/tests/test_monitor_bridge.py`
- `integrations/forensic-intelligence/tests/test_integration.py`

Checked offline when this map was written:

- test_decoder_conformance: the three decoders agree on log index, exchange, maker or wallet, taker or counterparty, token id, side and amounts for the 14 logs of monitoring/fixtures/orderfilled_20261113.json
- cd integrations/forensic-intelligence && python3 -B -m unittest discover -s tests: 51 tests OK

Known gap: Three OrderFilled v2 decoders plus a v1 one remain, with different units, fee handling, removed-log handling and fields (livecollect fills hold no transaction hash). Three tape row shapes: phi_monitor store.tape drops tx and outcome_index, which the position ledger needs. No shared schema document for fills or tape.

## 3. Position reconstruction

| Module | Functions |
| --- | --- |
| `investigations/collective-exposure-shifts/position-ledger/scripts/ledger.py` | `make_event`, `events_from_tape_rows`, `reconcile_tx`, `payoff_vector`, `classify` |
| `monitoring/phi_engine/asof.py` | `view`, `watch`, `classes` |
| `monitoring/phi_monitor/collect.py` | `baseline` |

Entry points:

- `python3 investigations/collective-exposure-shifts/position-ledger/scripts/verify_with_activity.py (seven required arguments)`
- `library calls from phi_engine.enrich.evaluate`

Input: tape rows (rowid, cid, ts, wallet, side, outcome, outcome_index, size, price, tx) from its own tape SQLite; activity rows for asof

Output: position events, payoff vectors and classes; wallet history as of a time

Tests:

- `investigations/collective-exposure-shifts/position-ledger/tests/test_ledger.py`
- `monitoring/tests/test_engine.py`

Checked offline when this map was written:

- nothing

Known gap: Not run here: test_ledger.py is pytest-style, pytest is not a dependency and unittest discovery finds 0 tests. Nothing feeds the position ledger from the monitoring stores. Five different modules are named ledger.py with five meanings.

## 4. Funding graphs

| Module | Functions |
| --- | --- |
| `monitoring/phi_monitor/detect.py` | `clusters` |
| `monitoring/phi_engine/chainfund.py` | `payer_of_deposit` |
| `monitoring/phi_engine/enrich.py` | `trace_funding`, `group_classes` |
| `integrations/forensic-intelligence/ledger.py` | `financial_graph`, `pair_links`, `save_exports` |
| `integrations/forensic-intelligence/monitor_bridge.py` | `funding_to_edges` |

Entry points:

- `cd monitoring && python3 -m phi_monitor run --db X (fills the funding table)`
- `ledger.save_exports(edges, new_empty_dir)`

Input: phi_monitor funding rows (tx, log_index, block, ts, proxy, payer, token, amount, payer_kind, payer_nonce); phi_engine deposits and links

Output: clusters of wallets sharing a plain-key payer; evidence edges, financial graph, CSV, JSON and GraphML exports

Tests:

- `monitoring/tests/test_replay.py`
- `monitoring/tests/test_engine.py`
- `integrations/forensic-intelligence/tests/test_integration.py`
- `integrations/forensic-intelligence/tests/test_monitor_bridge.py`

Checked offline when this map was written:

- test_monitor_bridge: the 2 funding rows of monitoring/fixtures/nobel_machado_20251009.json become 2 valid edges and 2 financial-graph edges; rows with a missing field are refused

Known gap: funding_to_edges reads phi_monitor funding rows only. phi_engine deposits rows carry no log index and no token and are refused, so phi_engine funding cannot reach the evidence ledger without new data. No command runs the bridge on a live store. Label and role tables (account_kind, chainfund.INFRA, pair_links node_roles) are separate.

## 5. Anomaly detection

| Module | Functions |
| --- | --- |
| `monitoring/phi_monitor/detect.py` | `evaluate`, `scan`, `replay`, `record` |
| `monitoring/phi_monitor/ignition.py` | `first_ignition` |
| `monitoring/phi_monitor/tapefeat.py` | `alert_features`, `classify` |
| `monitoring/phi_engine/enrich.py` | `evaluate`, `work` |
| `monitoring/phi_engine/models.py` | `rarity_fit`, `iforest_fit`, `edge_fit` |
| `integrations/forensic-intelligence/temporal.py` | `synchronized_pairs`, `circular_shift_null` |

Entry points:

- `cd monitoring && python3 -m phi_monitor replay --db X`
- `cd monitoring && python3 -m phi_engine replay --db X`

Input: the stores of stage 1

Output: phi_monitor alert bodies (level LONELY_THIN, LONELY, THIN; market-centric) and phi_engine alert bodies (class C1 to C7, R1, M1; wallet-centric); normalise_alert maps both to one flat record

Tests:

- `monitoring/tests/test_replay.py`
- `monitoring/tests/test_engine.py`
- `integrations/forensic-intelligence/tests/test_monitor_bridge.py`

Checked offline when this map was written:

- test_replay (in the 93 monitoring tests): the stored Machado evening raises 1 LONELY_THIN alert
- test_monitor_bridge: normalise_alert maps that alert and the C1_FRESH_FUNDED_BET alert of test_engine

Known gap: Two detectors with two alert schemas and two journals. normalise_alert gives one record shape, but nothing downstream reads it yet: no validation, registry or report consumes monitoring alerts.

## 6. Statistical validation

| Module | Functions |
| --- | --- |
| `integrations/quantitative_engine/validation.py` | `fisher_greater`, `permutation_p`, `evaluate` |
| `edge_research/cost_gate.py` | `cluster_ci`, `analyse` |
| `research_notes/early-detection-2026-11-13/study/code/stats.py` | `t1_exact`, `t2_permutation`, `cluster_ci` |

Entry points:

- `python3 -m edge_research.cost_gate --output DIR`
- `python3 research_notes/early-detection-2026-11-13/verify.py`

Input: scored rows of each tool or frozen study tables

Output: p-values, confidence intervals, verdicts per study

Tests:

- `integrations/quantitative_engine/tests/test_engine.py`
- `edge_research/tests/test_cost_gate.py`

Checked offline when this map was written:

- cd integrations/quantitative_engine && python3 -B -m unittest discover -s tests: 35 tests OK
- python3 -B -m unittest discover -s edge_research/tests: 6 tests OK

Known gap: No reusable function takes an alert set and returns a validated verdict; study statistics are per study and frozen. The multiple-testing count is per tool, not global. The study verify scripts were not run here.

## 7. Financial evidence

| Module | Functions |
| --- | --- |
| `integrations/forensic-intelligence/ledger.py` | `validate_edge`, `financial_graph`, `save_exports` |
| `scripts/validate_evidence.py` | `check_investigation`, `main` |
| `scripts/phi_lib.py` | `sha256_file`, `parse_findings` |

Entry points:

- `python3 scripts/validate_evidence.py`
- `python3 research_notes/<note>/verify.py`

Input: evidence edges; investigation folders (README, STATUS, FINDINGS, EVIDENCE, data manifests)

Output: validated edges and exports; evidence check report

Tests:

- `integrations/forensic-intelligence/tests/test_integration.py`
- `scripts/test_evidence_paths.py`
- `scripts/test_numeric_evidence.py`

Checked offline when this map was written:

- python3 -B scripts/validate_evidence.py: 0 errors

Known gap: Evidence for published findings is produced by hand-written per-note scripts. Only the forensic-intelligence edge schema is reusable, and no monitoring code writes it: funding_to_edges is a library function, not a step any collector calls.

## 8. Investigation reports

| Module | Functions |
| --- | --- |
| `monitoring/phi_engine/report.py` | `build`, `render` |
| `scripts/build_master_report.py` | `report`, `main` |
| `integrations/phi_registry/phi_registry.py` | `build`, `brief`, `check`, `verify` |

Entry points:

- `python3 scripts/build_master_report.py --check`
- `python3 integrations/phi_registry/phi_registry.py build --repo . --ref HEAD`
- `cd monitoring && python3 -m phi_engine alerts --json`

Input: phi_engine alert bodies; investigation STATUS and FINDINGS Markdown

Output: plain-text alert reports; master report; registry of findings and wallet mentions

Tests:

- `monitoring/tests/test_engine.py`
- `integrations/phi_registry/tests/test_registry.py`
- `scripts/test_publication.py`

Checked offline when this map was written:

- cd integrations/phi_registry && python3 -B -m unittest discover -s tests: 34 tests OK
- python3 -B scripts/build_master_report.py --check: reports up to date

Known gap: The registry parses Markdown only: alert ids, journal hashes and edge exports are not ingested, so an alert never becomes a finding or an open item. Alert reports and finding reports share no template or ids.
