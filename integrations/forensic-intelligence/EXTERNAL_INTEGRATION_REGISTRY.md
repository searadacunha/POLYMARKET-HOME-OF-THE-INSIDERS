# External integration registry

Generated from `external_registry.json` by `external_registry.py --write`. Do not edit by hand: `tests/test_external_registry.py` fails when this file and the data differ, or when a cited file is gone.

State of the repository read: commit `6171f7a`, 2026-11-20. Each entry sits in the lowest state its evidence fully supports. A document saying that something is integrated is not evidence; a file of ours, a check that passes and a recorded run are.

How far this registry was itself checked: for every S3 and S4 entry the cited files exist (enforced by the test) and the cited checks were run again on the commit above. S1 and S2 entries were classified by reading the documents of this repository; they were not re-verified one by one against the external projects.

## Counts

| State | Meaning | Entries |
|---|---|---|
| S4_INTEGRATED_VALIDATED | integrated, checked and run on real data | 19 |
| S3_METHOD_ADAPTED | method adapted or re-implemented here | 11 |
| S2_CODE_EXAMINED | code read at a pinned commit | 45 |
| S1_LISTED | listed or cited only | 143 |

## Integrated and validated (S4)

| Project | Kind | Licence | Our files | Check that passes | Evidence |
|---|---|---|---|---|---|
| Bitquery investigations (KPMG earnings cohort, Iran nine accounts, pardon accounts) | paper | third-party publication; no code taken | `research_notes/financial-links-replay-2026-11-07/tools/kpmg_markets.py`, `research_notes/financial-links-replay-2026-11-07/tools/verify_handoffs.py`, `research_notes/financial-links-replay-2026-11-07/verify.py` | python3 -B verify.py in research_notes/financial-links-replay-2026-11-07/ (scratch copy): 47/47 checks pass, exit 0 | VERIFIED: research_notes/financial-links-replay-2026-11-07/tools/verify_handoffs.py, kpmg_markets.py, build_tables.py re-derive the handoffs and statistics; verify.py checks A0-C4 and E1 pass (11 of 11 Bitquery handoffs plus 3, biggest-stake 20/21 p=0.00116; headline 19/21 not reproduced); data/kpmg_*.csv recorded. |
| Blockscout public name tags | service | public service | `monitoring/phi_engine/enrich.py`, `research_notes/realtime-intelligence-2026-11-14/study/code/col_40_funding.py` | python3 -I -B realtime verify.py: 338 passed, 0 failed | VERIFIED: realtime-intelligence study/code/col_40_funding.py and monitoring/phi_engine/enrich.py use it; REPORTED 3,705 addresses read; the recorded study is recomputed by verify.py (338 checks passed in my run). A tag that cannot be read never links two wallets. |
| circomlib / Poseidon reference parameters (generate_parameters_grain.sage) | library | not stated in our tree (provenance stated in the file header, licence of circomlib not recorded); nothing copied | `research_notes/github-tooling-audit-2026-11-06/scripts/poseidon.py` | python3 -I -B scripts/poseidon.py: vector OK; python3 -I -B verify.py in research_notes/github-tooling-audit-2026-11-06/ (scratch copy): 58/58 checks passed, exit 0 (poseidon_circomlib_vector, historical_roots_equal_full_rebuild_on_synthetic_tree) | VERIFIED: research_notes/github-tooling-audit-2026-11-06/scripts/poseidon.py regenerates circom BN254 constants by the reference Grain procedure and matches the circomlib vector poseidon([1,2]); used by privacy_cash_roots.py to recompute roots R(346,814) and R(346,816) proven by real transactions. |
| Etherscan API v2 (tokentx, token1155tx, txlist) | service | API terms; key read locally, never written | `research_notes/github-tooling-audit-2026-11-06/scripts/experiment_b.py`, `scripts/phi_lib.py` | python3 -I -B verify.py in research_notes/github-tooling-audit-2026-11-06/ (scratch copy): 58/58 checks passed, exit 0; scripts/test_integrity_regressions.py 27 tests OK | VERIFIED: research_notes/github-tooling-audit-2026-11-06/scripts/experiment_b.py collect/score; checks b_etherscan_pages_sha256 and b_recomputed_equals_kept_result pass; research_notes/financial-links-replay-2026-11-07/evidence/etherscan/ pages recorded. |
| Helius RPC (getTransactionsForAddress) | service | API terms; keys read from a local pool, never written | `research_notes/github-tooling-audit-2026-11-06/scripts/experiment_a_forward.py` | python3 -I -B verify.py in research_notes/github-tooling-audit-2026-11-06/ (scratch copy): 58/58 checks passed, exit 0 | VERIFIED: research_notes/github-tooling-audit-2026-11-06/scripts/experiment_a_forward.py pages the solver key; checks a_forward_11_recipients_recovered and a_forward_cost pass; evidence/forward_live/ holds the 16 matched transactions and the page hashes. |
| MSR XFM paired-wallet receipts (source cited as 'MSR' in the KPMG/XFM intake) | paper | third-party publication | `research_notes/financial-links-replay-2026-11-07/data/xfm_collectors.csv`, `research_notes/financial-links-replay-2026-11-07/tools/xfm_decode.py` | python3 -B verify.py in research_notes/financial-links-replay-2026-11-07/ (scratch copy): 47/47 checks pass, exit 0 | VERIFIED: research_notes/financial-links-replay-2026-11-07/tools/xfm_decode.py decodes the nine published transactions; verify.py H1-H3 pass (two-party mint matches, labels equal MSR's 9/9, 37 numbered accounts swept to two wallets); data/xfm_*.csv recorded. |
| Polygon public JSON-RPC nodes (eth_getTransactionReceipt, eth_getLogs) | service | public endpoints | `monitoring/phi_monitor/chain.py`, `research_notes/early-detection-2026-11-13/audit/maduro-iran/onchain_spotcheck.json` | integrations 35 OK; monitoring 51 OK | VERIFIED: monitoring/phi_monitor/chain.py and quantitative_engine tests test_order_filled_pair_is_confirmed pass; REPORTED 24,776 receipts and old-range log sweeps in realtime SOURCES_AND_TOOLS.md; early-detection audit/maduro-iran/onchain_spotcheck.json recorded. |
| Polymarket CLOB WebSocket market channel (wss://ws-subscriptions-clob.polymarket.com/ws/market) | service | terms of the venue | `monitoring/livecollect/__main__.py`, `monitoring/livecollect/decode.py` | integrations tests 35 OK (MarketDecodeTests, WebSocketFrameTests); monitoring 51 OK | VERIFIED: monitoring/livecollect/decode.py and __main__.py; MarketDecodeTests (real price_change rebuilds the book, batched frames, divergence classes) pass. REPORTED recorded live run: research_notes/forensic-engine-2026-11-13/PASSE5.md, early-detection data/live_run_20261114.json. |
| Polymarket Data API v2 (docs and OpenAPI) | service | public API | `integrations/quantitative_engine/trades_pull.py`, `monitoring/livecollect/trades.py`, `research_notes/github-tooling-audit-2026-11-06/scripts/collect_tip.py`, `research_notes/github-tooling-audit-2026-11-06/scripts/experiment_b.py` | python3 -I -B verify.py in research_notes/github-tooling-audit-2026-11-06/ (scratch copy): 58/58 checks passed, exit 0 | VERIFIED: research_notes/github-tooling-audit-2026-11-06/scripts/collect_tip.py (type=TIP, start=1, constant filters) and experiment_b.py; checks tip_counts, tip_none_for_note_accounts, b_totals pass; evidence/tip_summary/ and results/experiment_b_score.json recorded. |
| Polymarket Gamma API (public-search, profiles, markets) | service | public API | `monitoring/phi_engine/feed.py`, `research_notes/financial-links-replay-2026-11-07/tools/resolve_names.py`, `research_notes/realtime-intelligence-2026-11-14/study/code/col_05_catalogue.py` | python3 -B verify.py in research_notes/financial-links-replay-2026-11-07/ (scratch copy): 47/47 checks pass, exit 0 | VERIFIED: research_notes/financial-links-replay-2026-11-07/tools/resolve_names.py; verify.py A0 (22 accounts with distinct proxies), G1 and H1 use Gamma outcomes; research_notes/independent-forensic-audit-2026-11-08/evidence/feb22_25_traders_createdAt.csv recorded. |
| PostgreSQL 15 | library | PostgreSQL licence (permissive); not vendored | `integrations/phi_registry/supabase/migrations/20261118000300_rls_and_rpc.pg.sql`, `integrations/phi_registry/tests/test_postgres.py` | python3 -B -m unittest discover -s tests -v in integrations/phi_registry: Ran 34 OK (Postgres tests ran, not skipped) | VERIFIED: integrations/phi_registry/tests/test_postgres.py applies the 3 migrations to a throw-away local PostgreSQL 15 (brew, unix socket); 34 phi_registry tests incl. 10 Postgres tests pass in my run. Recorded: research_notes/registry-pilot-2026-11-18/results/bench.json, integrity.json (real registry data). |
| Privacy Cash relayer (api3.privacycash.org /merkle/root, /merkle/proofv2) | service | off-chain service, no terms recorded | `research_notes/github-tooling-audit-2026-11-06/scripts/privacy_cash_roots.py` | python3 -I -B verify.py in research_notes/github-tooling-audit-2026-11-06/ (scratch copy): 58/58 checks passed, exit 0 | VERIFIED: four archived responses in research_notes/github-tooling-audit-2026-11-06/evidence/privacy_cash_roots/; checks pc_api_root_is_the_chain_root and pc_four_current_paths_fold_to_the_chain_root pass (paths accepted only because they fold to the on-chain root). |
| Privacy-Cash/privacy-cash | repo | BSL 1.1, GPL-2.0+ from 2027-12-27 (REPORTED); GitHub metadata NOASSERTION (VERIFIED 2026-11-20). Layout as reference, no code copied | `research_notes/github-tooling-audit-2026-11-06/scripts/privacy_cash.py`, `research_notes/github-tooling-audit-2026-11-06/scripts/privacy_cash_roots.py` | python3 -I -B verify.py in research_notes/github-tooling-audit-2026-11-06/ (scratch copy): 58/58 checks passed, exit 0; privacy_cash_roots.py self-check OK | VERIFIED: research_notes/github-tooling-audit-2026-11-06/scripts/privacy_cash.py (decode_transact, byte-exact) and privacy_cash_roots.py; header cites anchor/programs/zkcash/src/lib.rs at f79b82f. 21 pc_* checks pass on 3 real transactions; evidence/privacy_cash_roots/ and evidence/solana_program/ recorded. |
| Public JSON-RPC endpoints (dRPC, Tenderly, Base, Arbitrum, Solana mainnet-beta) | service | public endpoints | `research_notes/github-tooling-audit-2026-11-06/scripts/experiment_a_live.py`, `scripts/check_polygon_rpc_coverage.py` | python3 -I -B verify.py in research_notes/github-tooling-audit-2026-11-06/ (scratch copy): 58/58 checks passed, exit 0; scripts/test_polygon_rpc_coverage.py 15 tests OK | VERIFIED: research_notes/github-tooling-audit-2026-11-06/scripts/experiment_a_live.py (evidence/polygon_live/) and scripts/check_polygon_rpc_coverage.py over research_notes/independent-forensic-audit-2026-11-08/evidence/polygon_logs_*.json; a_live_* checks and 15 coverage tests pass. |
| Relay API (api.relay.link requests/v2) | service | public API | `research_notes/financial-links-replay-2026-11-07/tools/relay_handoffs.py`, `research_notes/github-tooling-audit-2026-11-06/scripts/experiment_c.py` | python3 -I -B verify.py in research_notes/github-tooling-audit-2026-11-06/ (scratch copy): 58/58 checks passed, exit 0; python3 -B verify.py in research_notes/financial-links-replay-2026-11-07/ (scratch copy): 47/47 checks pass, exit 0 | VERIFIED: used as ground truth and record source in research_notes/github-tooling-audit-2026-11-06/scripts/experiment_c.py and research_notes/financial-links-replay-2026-11-07/tools/relay_handoffs.py, relay_by_hash.py; checks a_offline_all_api_fields_agree and c_s2_figures pass; archived records in fixtures and evidence. |
| relayprotocol/relay-settlement | repo | none (no licence at root, REPORTED; GitHub API licence null VERIFIED 2026-11-20). Interface facts only, no code copied | `research_notes/financial-links-replay-2026-11-07/tools/verify_handoffs.py`, `research_notes/github-tooling-audit-2026-11-06/scripts/experiment_a_forward.py`, `research_notes/github-tooling-audit-2026-11-06/scripts/experiment_c.py`, `research_notes/github-tooling-audit-2026-11-06/scripts/relay_onchain.py` | python3 -I -B verify.py in research_notes/github-tooling-audit-2026-11-06/ (scratch copy): 58/58 checks passed, exit 0; scripts/test_experiment_c.py 26/26; python3 -B verify.py in research_notes/financial-links-replay-2026-11-07/ (scratch copy): 47/47 checks pass, exit 0 | VERIFIED: research_notes/github-tooling-audit-2026-11-06/scripts/relay_onchain.py (decode_deposit_log, deposits_from_receipt, solana_fills, match, find_origin); header cites RelayDepository.sol at b2f3e0e. Same key used by research_notes/financial-links-replay-2026-11-07/tools/verify_handoffs.py. Recorded runs: results/experiment_a_{offline,live,forward}.json, experiment_c_score.json. |
| SEC EDGAR full-text search | service | public records | `research_notes/financial-links-replay-2026-11-07/tools/kpmg_markets.py`, `research_notes/financial-links-replay-2026-11-07/tools/sec_collect.py` | python3 -B verify.py in research_notes/financial-links-replay-2026-11-07/ (scratch copy): 47/47 checks pass, exit 0 | VERIFIED: research_notes/financial-links-replay-2026-11-07/tools/sec_collect.py and kpmg_markets.py (auditor from EX-23.1, results time from the 8-K Item 2.02 acceptance); verify.py C1-C4 pass; data/kpmg_earnings_markets.csv recorded. |
| X public mirrors (cdn.syndication.twimg.com, fxtwitter, vxtwitter) | service | public mirrors of X | `research_notes/financial-links-replay-2026-11-07/verify.py` | python3 -B verify.py in research_notes/financial-links-replay-2026-11-07/ (scratch copy): 47/47 checks pass, exit 0 | VERIFIED: research_notes/financial-links-replay-2026-11-07/verify.py F1 passes (two mirrors agree, text never edited); research_notes/independent-forensic-audit-2026-11-08/evidence/ballon_syndication_2026-11-08.json recorded. |
| X-sourced leads (Railgun-funded Maduro accounts, Iran 14 January whale, Snoorrason post) | paper | public posts | `research_notes/financial-links-replay-2026-11-07/tools/build_tables.py`, `research_notes/financial-links-replay-2026-11-07/verify.py` | python3 -B verify.py in research_notes/financial-links-replay-2026-11-07/ (scratch copy): 47/47 checks pass, exit 0 | VERIFIED: research_notes/financial-links-replay-2026-11-07/verify.py checks D1-D5, G1-G2, I1-I3 and F1 pass (six Railgun unshields 22,044.160154 USDC, 71 single-bet accounts with 5 winners, tree closed; mutualdelta funding path; two mirrors agree); data/railgun_*.csv, iran_jan14_episode.csv recorded. |

## Method adapted or re-implemented (S3)

| Project | Licence | Our files | Evidence |
|---|---|---|---|
| Bitquery Research investigations (Iran nine accounts, Biden pardons, KPMG cohort) | third-party publication, no code taken | `research_notes/external-polymarket-cases-2026-11-07/tools/check_external_cohort.py`, `research_notes/kpmg-election-integrity-2026-11-07/tools/check_intake.py` | VERIFIED: external-polymarket-cases tools/check_external_cohort.py recomputes the sum of published results (2,476,951 USD), 0/9 exact proxy overlap with the 38-account cohort; kpmg tools/check_intake.py PASS (11 handoffs, 9 XFM hashes). Both offline, write nothing. |
| DuckDB | MIT (not recorded in our tree) | `integrations/quantitative_engine/pendulum.py` | VERIFIED: imported only in integrations/quantitative_engine/pendulum.py; run recorded in forensic-engine data/results.json. No unit test imports it (README: tests need no dependency). |
| Ikey168/Noesis (src/kb/onchain_clustering.py) | MIT (REPORTED; GitHub API MIT VERIFIED 2026-11-20) | `research_notes/iran-exit-rarity-2026-11-06/code/common.py` | VERIFIED: research_notes/iran-exit-rarity-2026-11-06/code/common.py has curveball() (line 184); analysis_plan.md line 48 names the Noesis idea, MIT, e4ae131, and states no code is taken. Code facts at broad_discovery.md s.4 (:255, :361-410). |
| Inca Digital named cohort (Decision Centralization Index report, 39 flagged wallets) | third-party report, no code taken | `integrations/quantitative_engine/inca_full.py`, `integrations/quantitative_engine/inca_tape.py`, `research_notes/forensic-engine-2026-11-13/data/inca_prejump.json` | VERIFIED: integrations/quantitative_engine/inca_tape.py COHORT (addresses from inca-crosscheck REPORT) and inca_full.py score the named wallets; forensic-engine data/inca_prejump.json and inca_full.json hold the runs (7,271 deduped prints). Tape tests pass. Raw archives are local-only, runs not replayed by me. |
| Pendulum Flow Polymarket Orderbook Archive (archive.pendulumflow.com, V3.1 preview hours) | CC BY-NC 4.0 (PMXT mirror eras CC BY 4.0; AG6 none), stated in pendulum.py header, README, results.json | `integrations/quantitative_engine/pendulum.py`, `integrations/quantitative_engine/run_sample.py`, `research_notes/forensic-engine-2026-11-13/data/results.json` | VERIFIED: integrations/quantitative_engine/pendulum.py load_events() (DuckDB read of 6 parquet hours) feeds run_sample.py; forensic-engine-2026-11-13/data/results.json holds the run (353 prints, 9 candidates withheld, 0 alerts, sha256 of the 6 files). REPORTED: parquet not in Git, so I could not re-run. No test imports pendulum.py. |
| Polymarket official documentation: exchange contracts and Protocol V2 rollout pages | public documentation | `integrations/quantitative_engine/contracts.py`, `integrations/quantitative_engine/replay.py` | VERIFIED: integrations/quantitative_engine/contracts.py holds CTF_EXCHANGE_V2 0xe111..996b, neg-risk exchange, V1_UNTIL_UTC 2026-04-28 11:00 and PENDULUM_WINDOWS; executions.py and replay.py refuse claims outside them; tests pass; realtime SOURCES_AND_TOOLS.md says read 14 Nov 2026. No page URL or hash pinned in contracts.py. |
| prettydeath/TornadoCash-demixer | MIT (REPORTED; GitHub API MIT VERIFIED 2026-11-20) | `research_notes/github-tooling-audit-2026-11-06/results/demixer_eval.json`, `research_notes/github-tooling-audit-2026-11-06/scripts/demixer_eval.py` | VERIFIED: research_notes/github-tooling-audit-2026-11-06/scripts/demixer_eval.py is an own re-implementation of deposit_addresses.py:104-168 (header cites commit cc30ba7; MIT stated in audit_notes/demixer_evaluation.md). Recorded run on 10 real addresses: results/demixer_eval.json. Decision: rejected as a method. |
| SoweluAvanzo/intelliFi_anomaly_detection | none in upstream (all rights reserved); methods re-specified, no code copied (METHODS_REUSE.md) | `investigations/collective-exposure-shifts/exposure-signals/scripts/run_nulls.sh`, `investigations/collective-exposure-shifts/exposure-signals/scripts/signals.py` | REPORTED: investigations/collective-exposure-shifts/METHODS_REUSE.md pins a1707ad4b1d2, names coordination.py cotrade_pairs_with_null, backtest.py matched_control_events; decision ADAPT activity-preserving null (N2). VERIFIED: exposure-signals/scripts/signals.py day_shift() re-implements a circular day-shift null; 9 of 11 tests run by me pass; 19 null seeds recorded in out/null. |
| Supabase (hosted project, CLI, Data API) | SaaS terms; not applicable | `integrations/phi_registry/supabase/migrations/20261118000100_registry_core.sql` | VERIFIED: integrations/phi_registry/supabase/migrations/* follow the Supabase CLI layout with RLS and role grants; REPORT.md of registry-pilot cites 4 docs pages found by search, not fetched page by page. No project, no db push (CLI not installed). |
| warproxxx/poly_data | LICENSE file GPL-3.0 vs pyproject MIT; nothing copied (stated in quantitative_engine README) | `integrations/quantitative_engine/contracts.py`, `integrations/quantitative_engine/executions.py`, `integrations/quantitative_engine/replay.py` | VERIFIED docs: forensic-engine AUDIT_SOURCES.md pins 136e129735c73bce, describes update_chain.py (contract 0xe111..996b, block 84_902_353, columns kept/dropped). VERIFIED code: executions.inspect_poly_data_csv_row and contracts.poly_data_v2_claim encode those limits; 5 refusal tests pass; replay.py applies them to the real case windows. |
| websockets 15.0.1 (Python library) | BSD-3 (not recorded in our tree) | `monitoring/livecollect/__main__.py`, `monitoring/livecollect/requirements.txt` | VERIFIED: monitoring/livecollect/requirements.txt pins it; __main__.py uses websockets.connect (line 501). No test imports the library; frame decoding is tested separately. |

## Studied but not integrated: capabilities of high value

| Project | State | Licence | Capability we do not have |
|---|---|---|---|
| alphalab-research/wash-replication-2026 | S1_LISTED | not recorded in our documents | Replication of the Columbia wash study; unread. |
| Anti-Corruption Data Collective (ACDC) 544-wallet dataset | S1_LISTED | not recorded | The 544-wallet list itself, as an external labelled population to test our screens against. |
| Anti-Corruption Data Collective (ACDC) longshot and midterm pages (EXT-004, EXT-005, 2 Nov briefing) | S2_CODE_EXAMINED | author pages, no licence stated | Orca/Whale/Bot taxonomy, 78,496-wager longshot screen and follower-of-Orca test (RESEARCH_GAPS G1) are not replicated; wallet lists not matched to our 38-account cohort. |
| bradca0/polymarket-pnl | S2_CODE_EXAMINED | no licence in GitHub metadata, nothing copied | Its as-of shrinkage of wallet skill and the SPLIT/MERGE/REDEEM cash accounting were not ported; the repo's own PnL still needs point-in-time reconciliation. Result REPORTED, not rerun. |
| Columbia network-based wash-trading study (Gambling Harm PDF, EXT-022) | S1_LISTED | not recorded in our documents | Population-scale wash verdict absent from our repository (README research gap). |
| DOJ and CFTC filings: Spagnuolo (AlphaRaccoon) Google Year in Search case | S2_CODE_EXAMINED | public record | Full Google 2025 proxy and market mapping (recommended test 3) not done; no positive-control backtest. |
| DOJ and CFTC filings: Van Dyke (Burdensome-Mix) case | S2_CODE_EXAMINED | public record | Used as a positive control in no test: RESEARCH_GAPS proposes it, the exact Burdensome-Mix proxy is not mapped to our data. |
| Empirical Evaluation of Deadline-Resolved Information Leakage (SSRN 6687398) | S1_LISTED | not recorded in our documents | Deadline-resolved leakage is exactly the NO(D1)+YES(D2) ladder question; unread. |
| Envio HyperSync (hosted service) | S1_LISTED | token required; free tier rate-limited (REPORTED) | See enviodev/hypersync-client-python. |
| enviodev/hypersync-client-python | S1_LISTED | MPL-2.0 (GitHub metadata, REPORTED) | Bounded full-history log and trace retrieval with Parquet export: the log source needed for V1-era fills, BSC/Base histories and log-level experiment B. Never piloted; cost and token limits unmeasured. |
| enviodev/polymarket-v2-indexer | S2_CODE_EXAMINED | none (no LICENSE file REPORTED; GitHub API licence null VERIFIED 2026-11-20) | Per-wallet pUSD Transfer/Wrapped/Unwrapped reconciliation from raw logs, independent of the Data API (method written in s.6B, never run at log level: experiment B used Etherscan's index on 7 accounts); clean topic and ABI list for a contract registry. |
| From Iran to Taylor Swift: Informed Trading in Prediction Markets (SSRN 7259741, Harvard summary EXT-069) | S1_LISTED | not recorded in our documents | Its screen is a ready external replication target for our population; not attempted. |
| GDELT (DOC 2.0 API, GKG and Events 15-minute files) | S2_CODE_EXAMINED | not recorded | A reusable, archived 'first verifiable publication <= T' collector (GKG first batch + CDX earliest capture + primary-source timestamp, each labelled) feeding every insider-timing claim. |
| Hugging Face TimeSeventeen/Polymarket-v2 (daily on-chain fills with wallets, 55 GB, CC BY 4.0) | S1_LISTED | not recorded in our documents | Fills under 1,000 USD for 2026 (our study sees only larger fills); a possible independent tape for N1 reconciliation. |
| Inca Digital report on concentrated profitable Polymarket bettors (PDF, SHA-256 2b14e287...) | S2_CODE_EXAMINED | third-party report; PDF not committed | Inca's selection and scoring pipeline for profitable concentrated bettors (INDUSTRY_RESEARCH_PORTFOLIO.md line 61: no replication claimed); 25 non-Polygon legs of the exit index not replayed. |
| Information Leakage at Population Scale, Polymarket insider-relevant subpopulation 2020-2026 (arXiv 2605.00459) | S1_LISTED | not recorded in our documents | The nearest published population-scale comparator to our unselected-population design; methods and denominators unread. |
| Internet Archive Wayback CDX API | S2_CODE_EXAMINED | not recorded | Same collector as the GDELT entry: earliest-capture upper bounds archived with hashes per case. |
| l2beat/l2beat (interop plugins) | S2_CODE_EXAMINED | MIT (REPORTED; GitHub API MIT VERIFIED 2026-11-20) | Leg matching by protocol identifier for Mayan Swift, deBridge DLN, CCTP v1/v2 and Across, with test vectors; collector aborts on a repeated or empty cursor. Our identifier-level matching covers Relay only (REPORT.md s.7: other bridges untested). |
| moose-code/polymarket-indexer | S2_CODE_EXAMINED | none (no licence file REPORTED; GitHub API licence null VERIFIED 2026-11-20): blocked for copying | Separate V1 Exchange and V2 OrderFilled/OrdersMatched decoding with raw integer fills keyed by tx and log index, user positions: the V1-era fill reconstruction our scope lacks. Design never re-implemented. |
| orcalayer/polymarket-insider-score-backtest | S1_LISTED | not recorded in our documents | A published backtest of an insider score: the cleanest comparator for our as-of score test; unread beyond README. |
| outcometick/polymarket-backtest | S2_CODE_EXAMINED | MIT (GitHub metadata) | Named first choice for a controlled execution benchmark and the one decisive maker-spread experiment (EDGE_VERDICT); never run, no historical L2 for our cohort. Only its free crypto sample could test software. |
| Polymarket fee schedule (help article 13364478, July 2026) | S1_LISTED | not recorded in our documents | As-of fee table by trade date absent; edge_research uses hypothetical fixed markups only (cost_gate.py). |
| Polymarket/ctf-exchange-v2 | S1_LISTED | BSL 1.1, change date 2030-03-27 (REPORTED): ABI reference only | Authoritative CTF Exchange V2 event ABI (side, tokenId, builder, metadata) for a versioned contract registry (chain, address, deploy block, topic hashes). The registry is described as future work and does not exist in this scope. |
| Polymarket/polymarket-v2-external | S1_LISTED | BSL 1.1, change date 2030 (REPORTED) | Protocol V2 PositionManager position-id decoding and ExchangeV3 fills. No decoder in this scope; polymarket_data.md notes ExchangeV3 0xe3333700... is indexed by no audited repo. |
| ScrapingBee/polymarket-api | S2_CODE_EXAMINED | MIT | Semantic/monotonicity gate on deadline ladders (N4) before any NO(D1)+YES(D2) reading is not found as code; EXTERNAL_METHODS calls it the high-priority control. |
| shottah/tracer | S2_CODE_EXAMINED | MIT OR Apache-2.0 (both files, REPORTED); GitHub API Apache-2.0 (VERIFIED 2026-11-20) | Internal native transfers from a callTracer tree and exact prestate balance diffs: our Polygon decoder sees only ERC-20 Transfer logs, so internal POL value and delegated call structure are invisible. Blocked on a debug or archive RPC. |
| sturzael/polymarket-edge-research | S2_CODE_EXAMINED | no licence (GitHub metadata) | Frozen replication on our own sports-market population never run (sports excluded from universe). SYNTHESIS also says 109/120 bucket markets live 14 days or less, game_outcome only, and a 30-day forward collector is required; our verdict omits the age gate. |
| The Ghosts of Polymarket: Off-chain Matches and On-chain Reverts (arXiv 2606.16852) | S1_LISTED | not recorded in our documents | Reverted on-chain fills versus API tapes bear directly on tape completeness (N1); unread. |
| vsbtc/polymarket-insider-detection | S2_CODE_EXAMINED | MIT (index.json, root EDGE_VERDICT) | The REVIEW's falsification experiment (past-only score vs market price on a locked TEST, Brier/log-loss/calibration) is specified, not run; their validate.py never compared; no online reveal-jump detector built. |

## Where documents of this repository say more than the code supports

- integrations/forensic-intelligence/GITHUB_FORENSIC_DISCOVERY.md line 90 says README plus implementation, configuration and test files 'were actually opened' for every shortlisted repository, but its own second table (lines 141-152) lists only README, tree or licence for hypersync-client-python, relay-kit, chainmap, graphsense-tagpacks, ctf-exchange-v2 and polymarket-v2-external; graphsense-lib, evm-cctp-contracts, duckdb, polars and ruptures have no pinned commit. These are S1, not S2.
- integrations/forensic-intelligence/GITHUB_FORENSIC_DISCOVERY.md decisions 'ADAPT public read-only adapter' (py-sdk, line 94) and 'PILOT' (hypersync, PublicClient; also NEXT_INVESTIGATIONS.md line 22) read as work in progress; no adapter or pilot exists (grep polymarket_client|PublicClient over all *.py: 0 hits; 'hypersync' only in one BSC probe outside scope).
- integrations/forensic-intelligence/TOOLS_BENCHMARK.md lines 77-85 pin git blob SHAs as 'tested and uploaded bytes'; at 6171f7a five of seven differ (git hash-object: ledger.py b18bbb58, temporal.py 6163a682, source_ingest.py c6a64cb4, tests/test_integration.py 597dec7a, tests/test_source_ingest.py 915827e4). Only coverage.py, tests/test_coverage.py and the fixture match. The recorded benchmark no longer describes the committed code.
- integrations/forensic-intelligence/TOOLS_BENCHMARK.md line 53 states a NetworkX smoke test was 'actually executed'; no script, log or output of it is in the repository, so it cannot be checked (REPORTED only).
- integrations/forensic-intelligence/README.md, TOOLS_BENCHMARK.md and CAPABILITY_GAP_ANALYSIS.md give '35 discovered, 34 PASS, 1 SKIP'; my run at 6171f7a gives 44 tests, 44 OK, 0 skipped (stale, understated; the suite ran on an isolated Linux runtime, never recorded on the Mac).
- research_notes/github-tooling-audit-2026-11-06/REPORT.md line 5 says 'last run: 49 of 49 checks'; verification.json and my run give 58/58 (stale, understated).
- research_notes/github-tooling-audit-2026-11-06/REPORT.md line 17 says all repositories 'were read at the pinned commit' with detailed notes in audit_notes/; relay-kit (row 5) has no commit, and relay-settlement, privacy-cash, privacy-cash-sdk and relay-protocol-oracle have no note in audit_notes/ (their code facts exist only in the REPORT table and in script headers).
- research_notes/github-tooling-audit-2026-11-06/REPORT.md section 5 'Integrated' and the row labels 'Tested, integrated as a method' mean integrated inside research notes: relay_onchain.py and privacy_cash.py are duplicated per note and are absent from monitoring/, shared/ and scripts/. No shared, importable module exists.
- research_notes/github-tooling-audit-2026-11-06/REPORT.md section 6 says the rarity protocol is 'proposed, not run' and row 9 places the Noesis-style null in 'PR 27's frozen rarity study'; a frozen study with code and a registry exists at research_notes/iran-exit-rarity-2026-11-06 (PROTOCOL.lock, registre/tests.jsonl). The report was not updated; which PR holds it is UNKNOWN from this scope.
- research_notes/github-tooling-audit-2026-11-06/scripts/demixer_eval.py and results/demixer_eval.json are not covered by verify.py: the only S3 re-implementation of third-party logic in this note has no regression check (it reproduced when I ran it by hand).
- research_notes/independent-forensic-audit-2026-11-08/DECISIONS.csv is older than the decision table of REPORT.md: it still says the publication anchor is 'limite observee, non corrigee' and '1 984 038.168550 CONFIRMED : chaque cote' with no exhaustiveness caveat, and lacks the row 'Couverture du scan Polygon: NON ETABLIE' that REPORT.md lines 225 and 234 add.
- INDUSTRY_RESEARCH_PORTFOLIO.md line 43 ('Cross-chain analysis: Relay order identifiers, bridge outputs, Polygon/Ethereum/TRON/Solana/Monad paths') reads broader than what this scope tests: identifier-level matching exists for Relay only (other bridges untested, tooling REPORT s.7), and Monad, Bitcoin and Optimism appear as origins in Relay records (financial-links REPORT s.3), not as traced paths. TRON evidence is outside this scope: UNKNOWN.
- RAPPORT_FINAL.md line 14 and quantitative_engine/README.md line 20 present verify.py as recomputing the result. VERIFIED on this Mac (Python 3.9.6, 3.11.15, 3.12.16, 3.14.8): it exits 'evaluation does not match scored_prints.jsonl'; only fisher_one_sided differs by one ulp (H1 0.6250000000000003 vs saved 0.6250000000000001, H3 0.3333333333333329 vs ...315) under strict equality. The doc also says 13 unit tests, now 35 (historical note present).
- Root EDGE_VERDICT.md 'Provenance and licences' says 'Cited findings' for 11 repositories. VERIFIED by grep: only junegun, sturzael, bradca0 (and vsbtc in REVIEW.md) have a finding or file content described; outcometick, SII-WANGZJ, G0BLINDEV, hugompt, Fierdimo, tlafargue only appear in this licence line and in index.json. 'tlafargue parquet motivated the thresholds' traces to no threshold in analysis_plan.md or edge_research/code.
- Root EDGE_VERDICT.md next-test paragraph calls the sturzael FLB lead 'stable across 3 years' and the only survivor of its stratification. VERIFIED against the pinned SYNTHESIS.md: true, but the source itself says 109 of 120 bucket markets are 14 days old or less (age-gated, monotone dose-response), game_outcome only, MLB driven, and demands a 30-day forward collector. Our paragraph omits this.
- EXTERNAL_METHODS.md opens with 'observations from published documentation or code' but pins no commit and no file; the pins (a1707ad4, 6d530aa1, 5c9be8b7, 10e18702, b3839cf3) live only in investigations/collective-exposure-shifts/METHODS_REUSE.md. It recommends adopting the activity-preserving null; signals.py day_shift implements one but neither signals.py nor the exposure-signals README cites intelliFi, against METHODS_REUSE's own rule.
- edge_research/DATA_INVENTORY.md says trees are complete (truncated=false) for 11 repositories; index.json has no truncated field and tree.json files are not committed, so it cannot be checked from the repository (the fetch script asserts it, REPORTED). SOURCE_AUDIT.md gives licences for eliazonta, mileswangs, Epsilon-Fund with no pin, hash or fetch record in index.json (UNKNOWN).

## All entries

| Project | Kind | State | Value of integrating | Licence |
|---|---|---|---|---|
| 0xaaiden/smoldata | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| 0xinsider/research | repo | S1_LISTED | LOW | CC-BY (REPORTED) |
| 0xPolygon/polygon-edge | repo | S1_LISTED | LOW | Apache-2.0 (GitHub metadata as recorded 2026-11-02, REPORTED) |
| across-protocol/skills | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| adbar/htmldate | library | S2_CODE_EXAMINED | LOW | Apache-2.0 (REPORTED) |
| agentic-reserve/solana-forensic-intelligence | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| akamhy/waybackpy | library | S2_CODE_EXAMINED | NONE | MIT (REPORTED) |
| Akshat-cs/Polymarket-wash-trading-test | repo | S1_LISTED | MEDIUM | not recorded in our documents |
| Allium | indexer | S1_LISTED | LOW | not recorded |
| alphalab-research/wash-detector-v3 | repo | S2_CODE_EXAMINED | NONE | MIT (REPORTED) |
| alphalab-research/wash-replication-2026 | repo | S1_LISTED | HIGH | not recorded in our documents |
| Anatomy of a Decentralized Prediction Market (arXiv 2604.24366, 30 billion book events) | paper | S1_LISTED | MEDIUM | not recorded in our documents |
| andy1245-rgb/PolyCrawler | repo | S2_CODE_EXAMINED | LOW | Apache-2.0 (REPORTED) |
| Anti-Corruption Data Collective (ACDC) 544-wallet dataset | dataset | S1_LISTED | HIGH | not recorded |
| Anti-Corruption Data Collective (ACDC) longshot and midterm pages (EXT-004, EXT-005, 2 Nov briefing) | dataset | S2_CODE_EXAMINED | HIGH | author pages, no licence stated |
| ArbitrumFoundation/sybil-detection | repo | S1_LISTED | NONE | none (REPORTED) |
| arnaudknobloch/awesome-polymarket | repo | S1_LISTED | LOW | not recorded in our documents |
| bandrehc/polywash | repo | S1_LISTED | MEDIUM | not recorded in our documents |
| Benja-Pauls/polymarket-insider-detection | repo | S2_CODE_EXAMINED | LOW | not recorded |
| bensaru/polymarket-analyzer | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| berlinbra/polymarket-mcp | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Bitquery investigations (KPMG earnings cohort, Iran nine accounts, pardon accounts) | paper | S4_INTEGRATED_VALIDATED | HIGH | third-party publication; no code taken |
| Bitquery Research investigations (Iran nine accounts, Biden pardons, KPMG cohort) | paper | S3_METHOD_ADAPTED | HIGH | third-party publication, no code taken |
| blockchain-etl/awesome-blockchain-data | repo | S1_LISTED | LOW | , (GitHub metadata as recorded 2026-11-02, REPORTED) |
| blockchain-etl/ethereum-etl | library | S1_LISTED | LOW | MIT (GitHub metadata, REPORTED) |
| Blockscout (labels and API) | service | S2_CODE_EXAMINED | MEDIUM | public service |
| Blockscout public name tags | service | S4_INTEGRATED_VALIDATED | MEDIUM | public service |
| blockscout/blockscout | repo | S1_LISTED | LOW | NOASSERTION (GitHub metadata as recorded 2026-11-02, REPORTED) |
| bradca0/polymarket-pnl | repo | S2_CODE_EXAMINED | HIGH | no licence in GitHub metadata, nothing copied |
| BrainDAO/mcp-polymarket | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| brianleect/etherscan-labels | dataset | S1_LISTED | LOW | MIT (REPORTED) |
| Bubblemaps X threads and analyses (Iran 9 accounts, 4-wallet sequence, 7-account cluster, Axiom) | service | S1_LISTED | MEDIUM | not recorded in our documents |
| caiovicentino/polymarket-mcp-server | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Cardozo and Rivero-Wildemauwe, Favorite-Longshot Bias in Prediction Markets (arXiv 2609.12878) | paper | S1_LISTED | MEDIUM | not recorded in our documents |
| catmcgee/solana-mixer-circom | repo | S1_LISTED | NONE | not recorded |
| ChainPrimitives/eth-event-decoder | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| circlefin/evm-cctp-contracts | repo | S1_LISTED | MEDIUM | Apache-2.0 (GitHub metadata, REPORTED) |
| circomlib / Poseidon reference parameters (generate_parameters_grain.sage) | library | S4_INTEGRATED_VALIDATED | LOW | not stated in our tree (provenance stated in the file header, licence of circomlib not recorded); nothing copied |
| Clifford-Swartz/provenance | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Columbia network-based wash-trading study (Gambling Harm PDF, EXT-022) | paper | S1_LISTED | HIGH | not recorded in our documents |
| CRS Legal Sidebar: Prediction Markets and Insider Trading Law (EXT-076) | paper | S1_LISTED | LOW | not recorded in our documents |
| CryptoHouse | indexer | S1_LISTED | LOW | not recorded |
| darrnhard/polymarket-smart-money | repo | S2_CODE_EXAMINED | MEDIUM | none (README MIT badge only) |
| debridge-finance/solana-tx-parser-public | library | S2_CODE_EXAMINED | MEDIUM | LGPL-2.1 (REPORTED) |
| deepcharles/ruptures | library | S1_LISTED | LOW | BSD-2-Clause (GitHub metadata, REPORTED) |
| DineshKumar8399/polymarket-orderbook-dataset | repo | S1_LISTED | MEDIUM | not recorded in our documents |
| Do prediction markets price events or adjudication (ScienceDirect S0165176526003721) | paper | S1_LISTED | MEDIUM | not recorded in our documents |
| DOJ and CFTC filings: Spagnuolo (AlphaRaccoon) Google Year in Search case | paper | S2_CODE_EXAMINED | HIGH | public record |
| DOJ and CFTC filings: Van Dyke (Burdensome-Mix) case | paper | S2_CODE_EXAMINED | HIGH | public record |
| DuckDB | library | S3_METHOD_ADAPTED | LOW | MIT (not recorded in our tree) |
| duckdb/duckdb | library | S1_LISTED | LOW | MIT (GitHub metadata, REPORTED) |
| Dune | indexer | S1_LISTED | MEDIUM | not recorded |
| Dune, Allium, Bitquery SQL, Flipside, CryptoHouse | indexer | S1_LISTED | LOW | not recorded in our documents |
| duneanalytics/spellbook | repo | S1_LISTED | MEDIUM | NOASSERTION (GitHub metadata as recorded 2026-11-02, REPORTED) |
| eliazonta/pmarket_arb | repo | S1_LISTED | LOW | not recorded in our documents |
| Empirical Evaluation of Deadline-Resolved Information Leakage (SSRN 6687398) | paper | S1_LISTED | HIGH | not recorded in our documents |
| Envio HyperSync (hosted service) | service | S1_LISTED | HIGH | token required; free tier rate-limited (REPORTED) |
| enviodev/hypersync-client-python | library | S1_LISTED | HIGH | MPL-2.0 (GitHub metadata, REPORTED) |
| enviodev/polymarket-v2-indexer | indexer | S2_CODE_EXAMINED | HIGH | none (no LICENSE file REPORTED; GitHub API licence null VERIFIED 2026-11-20) |
| Epsilon-Fund/Epsilon-Quant-Research | repo | S1_LISTED | MEDIUM | not recorded in our documents |
| ESMA Trends, Risks and Vulnerabilities Report No.2 2026 (EXT-074) | paper | S1_LISTED | LOW | not recorded in our documents |
| ethereum/eth-abi | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| ethereum/eth-account | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| ethereum/web3.py | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Etherscan API v2 (tokentx, token1155tx, txlist) | service | S4_INTEGRATED_VALIDATED | MEDIUM | API terms; key read locally, never written |
| External research bibliography (76 sources, research_notes/external-market-abuse-corpus-20261117) | dataset | S1_LISTED | LOW | various |
| Fidonis resolution-integrity monitor and Bitquery 'Who decides Polymarket disputes' (EXT-029, EXT-030) | dataset | S1_LISTED | MEDIUM | not recorded in our documents |
| Fierdimo/polymarket-analysis | repo | S1_LISTED | LOW | none |
| Fill-Side Non-Retail Trading on Polymarket (SSRN 6751284) | paper | S1_LISTED | MEDIUM | not recorded in our documents |
| ForesightFlow/datasets | repo | S1_LISTED | MEDIUM | not recorded in our documents |
| ForesightFlow/datasets (ffic-inventory, ffic-v1.csv) | dataset | S2_CODE_EXAMINED | MEDIUM | CC-BY-4.0 (REPORTED) |
| forta-network/labelled-datasets | dataset | S1_LISTED | LOW | not recorded |
| From Iran to Taylor Swift: Informed Trading in Prediction Markets (SSRN 7259741, Harvard summary EXT-069) | paper | S1_LISTED | HIGH | not recorded in our documents |
| FuckFiat/polymarket-whale-tracker | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| G0BLINDEV/polymarket-backtester-realistic | repo | S1_LISTED | MEDIUM | MIT |
| GDELT (DOC 2.0 API, GKG and Events 15-minute files) | dataset | S2_CODE_EXAMINED | HIGH | not recorded |
| gl0bal01/chainmap | repo | S1_LISTED | LOW | MIT (GitHub metadata, REPORTED) |
| gnosis/conditional-tokens-contracts | repo | S1_LISTED | MEDIUM | LGPL-3.0 (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Goldsky | indexer | S1_LISTED | MEDIUM | not recorded |
| Goldsky public subgraphs (order book, activity, positions, profit, open interest) | service | S1_LISTED | NONE | not recorded in our documents |
| graphsense/graphsense-lib | library | S1_LISTED | LOW | MIT (GitHub metadata, REPORTED) |
| graphsense/graphsense-tagpacks | dataset | S1_LISTED | MEDIUM | MIT (GitHub metadata, REPORTED) |
| gregyoung14/openmarket (and arXiv 2607.26245) | dataset | S1_LISTED | MEDIUM | not recorded in our documents |
| Helius RPC (getTransactionsForAddress) | service | S4_INTEGRATED_VALIDATED | MEDIUM | API terms; keys read from a local pool, never written |
| helius-labs/helius-sdk | library | S2_CODE_EXAMINED | MEDIUM | MIT (REPORTED) |
| HemeraProtocol/hemera-indexer | repo | S1_LISTED | LOW | Apache-2.0 (GitHub metadata as recorded 2026-11-02, REPORTED) |
| hildobby labels / Polygonscan nametags | dataset | S1_LISTED | MEDIUM | not recorded |
| Hugging Face TimeSeventeen/Polymarket-v2 (daily on-chain fills with wallets, 55 GB, CC BY 4.0) | dataset | S1_LISTED | HIGH | not recorded in our documents |
| hugompt/polymarket-microstructure-lab | repo | S1_LISTED | MEDIUM | MIT |
| Ikey168/Noesis (src/kb/onchain_clustering.py) | repo | S3_METHOD_ADAPTED | MEDIUM | MIT (REPORTED; GitHub API MIT VERIFIED 2026-11-20) |
| Imig et al. 2025 (LayerZero sybil detection paper) | paper | S1_LISTED | NONE | not recorded |
| Inca Digital named cohort (Decision Centralization Index report, 39 flagged wallets) | paper | S3_METHOD_ADAPTED | HIGH | third-party report, no code taken |
| Inca Digital report on concentrated profitable Polymarket bettors (PDF, SHA-256 2b14e287...) | paper | S2_CODE_EXAMINED | HIGH | third-party report; PDF not committed |
| Information Leakage at Population Scale, Polymarket insider-relevant subpopulation 2020-2026 (arXiv 2605.00459) | paper | S1_LISTED | HIGH | not recorded in our documents |
| Internet Archive Wayback CDX API | service | S2_CODE_EXAMINED | HIGH | not recorded |
| IYKYK Markets 'Finding the Needle' (blind wallet detection) | paper | S2_CODE_EXAMINED | MEDIUM | not recorded |
| JakubReha/ProvCTDG | repo | S1_LISTED | NONE | not recorded |
| jayrabol/solana-holder-clusters | repo | S1_LISTED | LOW | MIT (REPORTED) |
| jsinyavsky/polymarket_anomaly_detection | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| junegun/polymarket-strategy-lab | repo | S2_CODE_EXAMINED | LOW | NOASSERTION (findings cited only) |
| kachence/prediction-almanac | repo | S1_LISTED | LOW | not recorded in our documents |
| Kowalskk/polyMARKET_data | repo | S2_CODE_EXAMINED | NONE | GPL-3.0 LICENSE vs MIT in pyproject (REPORTED) |
| l2beat/l2beat (interop plugins) | repo | S2_CODE_EXAMINED | HIGH | MIT (REPORTED; GitHub API MIT VERIFIED 2026-11-20) |
| Lightprotocol/instruction-decoder | repo | S1_LISTED | NONE | none (REPORTED) |
| linwoodc3/gdeltPyR | library | S2_CODE_EXAMINED | NONE | GPL-3.0 (REPORTED) |
| Market Attention and Information Quality (arXiv 2610.37669) | paper | S1_LISTED | LOW | not recorded in our documents |
| mayan-finance/swap-sdk | library | S1_LISTED | LOW | not recorded |
| metaver5o/Blockchain-Forensic-Toolkit | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| mikemarshall01/sybil-detect | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| mileswangs/polymarket-historical-data (PMData) | dataset | S1_LISTED | MEDIUM | not recorded in our documents |
| MNEMONIMO/onchain-sybil-detector | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| moose-code/polymarket-indexer | indexer | S2_CODE_EXAMINED | HIGH | none (no licence file REPORTED; GitHub API licence null VERIFIED 2026-11-20): blocked for copying |
| MSR XFM paired-wallet receipts (source cited as 'MSR' in the KPMG/XFM intake) | paper | S4_INTEGRATED_VALIDATED | MEDIUM | third-party publication |
| muzilicheng/polymarket-historical-market-data | repo | S1_LISTED | LOW | NOASSERTION (GitHub metadata as recorded 2026-11-02, REPORTED) |
| NachoCanabal/wallet-attribution | repo | S1_LISTED | LOW | NOASSERTION (GitHub metadata as recorded 2026-11-02, REPORTED) |
| neo4j/graph-data-science | repo | S1_LISTED | LOW | NOASSERTION (GitHub metadata as recorded 2026-11-02, REPORTED) |
| networkx/networkx | library | S1_LISTED | LOW | BSD-3-Clause per its LICENSE.txt (REPORTED); GitHub metadata NOASSERTION |
| NicoBeCodin/solana_mixer | repo | S1_LISTED | NONE | not recorded |
| nirholas/crosschain-proof-page | repo | S1_LISTED | NONE | not recorded |
| orcalayer/polymarket-insider-score-backtest | repo | S1_LISTED | HIGH | not recorded in our documents |
| osslabz/evm-abi-decoder | repo | S1_LISTED | LOW | GPL-3.0 (GitHub metadata as recorded 2026-11-02, REPORTED) |
| outcometick/polymarket-backtest | repo | S2_CODE_EXAMINED | HIGH | MIT (GitHub metadata) |
| pareto-xyz/tutela-app | repo | S2_CODE_EXAMINED | LOW | none (no LICENSE file, REPORTED) |
| PaulieB14/graph-polymarket-mcp | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| PaulieB14/polymarket-v2-subgraphs | repo | S1_LISTED | MEDIUM | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Pendulum Flow Polymarket Orderbook Archive (archive.pendulumflow.com, V3.1 preview hours) | dataset | S3_METHOD_ADAPTED | MEDIUM | CC BY-NC 4.0 (PMXT mirror eras CC BY 4.0; AG6 none), stated in pendulum.py header, README, results.json |
| PerlanLabs/polymarket-paper-trader | repo | S2_CODE_EXAMINED | MEDIUM | MIT |
| pola-rs/polars | library | S1_LISTED | LOW | MIT (GitHub metadata, REPORTED) |
| polyflux-io/polymarket-onchain-trades | repo | S1_LISTED | MEDIUM | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Polygon public JSON-RPC nodes (eth_getTransactionReceipt, eth_getLogs) | service | S4_INTEGRATED_VALIDATED | HIGH | public endpoints |
| Polymarket CLOB WebSocket market channel (wss://ws-subscriptions-clob.polymarket.com/ws/market) | service | S4_INTEGRATED_VALIDATED | MEDIUM | terms of the venue |
| Polymarket Data API v2 (docs and OpenAPI) | service | S4_INTEGRATED_VALIDATED | HIGH | public API |
| Polymarket fee schedule (help article 13364478, July 2026) | paper | S1_LISTED | HIGH | not recorded in our documents |
| Polymarket Gamma API (public-search, profiles, markets) | service | S4_INTEGRATED_VALIDATED | MEDIUM | public API |
| Polymarket official documentation: exchange contracts and Protocol V2 rollout pages | service | S3_METHOD_ADAPTED | MEDIUM | public documentation |
| Polymarket transparency page (governance, supervision) (EXT-021) | service | S1_LISTED | LOW | not recorded in our documents |
| Polymarket/agent-skills | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Polymarket/ctf-exchange-v2 | repo | S1_LISTED | HIGH | BSL 1.1, change date 2030-03-27 (REPORTED): ABI reference only |
| Polymarket/polymarket-subgraph | indexer | S1_LISTED | MEDIUM | LGPL-3.0 (GitHub metadata, REPORTED) |
| Polymarket/polymarket-v2-external | repo | S1_LISTED | HIGH | BSL 1.1, change date 2030 (REPORTED) |
| Polymarket/py-clob-client | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Polymarket/py-clob-client-v2 | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Polymarket/py-sdk | library | S2_CODE_EXAMINED | MEDIUM | MIT (LICENSE and pyproject agree, REPORTED; GitHub API MIT VERIFIED 2026-11-20) |
| Polymarket/real-time-data-client | library | S2_CODE_EXAMINED | LOW | MIT (REPORTED) |
| PostgreSQL 15 | library | S4_INTEGRATED_VALIDATED | MEDIUM | PostgreSQL licence (permissive); not vendored |
| Press coverage cited by the corpus (Reuters, Guardian, CBS, Bloomberg, WIRED, AP, WSJ, CoinDesk, Protos, Fortune, Decrypt, The Block, Le Monde, Morningstar; 16+ URLs) | dataset | S1_LISTED | LOW | not recorded in our documents |
| prettydeath/TornadoCash-demixer | repo | S3_METHOD_ADAPTED | HIGH | MIT (REPORTED; GitHub API MIT VERIFIED 2026-11-20) |
| prettydeath/wallet-attribution | dataset | S1_LISTED | LOW | NOASSERTION (GitHub metadata, REPORTED) |
| Price Dislocations, News Citations and Epistemic Leverage (arXiv 2609.06005) | paper | S1_LISTED | MEDIUM | not recorded in our documents |
| Privacy Cash relayer (api3.privacycash.org /merkle/root, /merkle/proofv2) | service | S4_INTEGRATED_VALIDATED | LOW | off-chain service, no terms recorded |
| Privacy-Cash/privacy-cash | repo | S4_INTEGRATED_VALIDATED | MEDIUM | BSL 1.1, GPL-2.0+ from 2027-12-27 (REPORTED); GitHub metadata NOASSERTION (VERIFIED 2026-11-20). Layout as reference, no code copied |
| Privacy-Cash/privacy-cash-sdk | library | S1_LISTED | NONE | no LICENSE file (REPORTED) |
| pselamy/polymarket-insider-tracker | repo | S1_LISTED | MEDIUM | MIT (GitHub metadata, REPORTED) |
| psyberck/polymarket-subgraph-v2 | repo | S1_LISTED | MEDIUM | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Public JSON-RPC endpoints (dRPC, Tenderly, Base, Arbitrum, Solana mainnet-beta) | service | S4_INTEGRATED_VALIDATED | HIGH | public endpoints |
| pyundev/solana-mixer | repo | S1_LISTED | NONE | not recorded |
| rayperatta/Cluster-Analyzer | repo | S1_LISTED | NONE | not recorded |
| rchen8/hop-airdrop | repo | S2_CODE_EXAMINED | NONE | none (REPORTED) |
| Rebadged/polymarket-alpha | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Relay API (api.relay.link requests/v2) | service | S4_INTEGRATED_VALIDATED | HIGH | public API |
| relayprotocol/relay-kit | library | S1_LISTED | NONE | MIT (GitHub metadata, REPORTED) |
| relayprotocol/relay-protocol-oracle | repo | S1_LISTED | LOW | MIT in package.json (REPORTED) |
| relayprotocol/relay-settlement | repo | S4_INTEGRATED_VALIDATED | HIGH | none (no licence at root, REPORTED; GitHub API licence null VERIFIED 2026-11-20). Interface facts only, no code copied |
| ritugupta8898-cloud/temporal-fraud-gnn | repo | S1_LISTED | NONE | not recorded |
| rled7/sybil-detection-engine | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| rohteemie/Open-Source-Blockchain-Forensics | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| safe-global/safe-core-sdk | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| safe-global/safe-eth-py | repo | S1_LISTED | MEDIUM | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| saisanthosh245/Real-Time-Crypto-Fraud-Attribution-System | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Samy-z/PolyClusters | repo | S2_CODE_EXAMINED | LOW | MIT (REPORTED) |
| Schmidters/collectmarkets | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| scottonchain/layerzero_xgboost | repo | S2_CODE_EXAMINED | LOW | none (REPORTED) |
| ScrapingBee/polymarket-api | repo | S2_CODE_EXAMINED | HIGH | MIT |
| SEC EDGAR full-text search | service | S4_INTEGRATED_VALIDATED | LOW | public records |
| sfrbuilds/polymarket-wallet-analyzer | repo | S2_CODE_EXAMINED | NONE | none (README says MIT, no LICENSE file, REPORTED) |
| shottah/tracer | repo | S2_CODE_EXAMINED | HIGH | MIT OR Apache-2.0 (both files, REPORTED); GitHub API Apache-2.0 (VERIFIED 2026-11-20) |
| SII-WANGZJ/Polymarket_data | repo | S1_LISTED | MEDIUM | not recorded in our documents |
| SoweluAvanzo/intelliFi_anomaly_detection | repo | S3_METHOD_ADAPTED | HIGH | none in upstream (all rights reserved); methods re-specified, no code copied (METHODS_REUSE.md) |
| streamingfast/firehose-ethereum | repo | S1_LISTED | LOW | Apache-2.0 (GitHub metadata as recorded 2026-11-02, REPORTED) |
| streamingfast/substreams | repo | S1_LISTED | LOW | Apache-2.0 (GitHub metadata as recorded 2026-11-02, REPORTED) |
| sturzael/polymarket-edge-research | repo | S2_CODE_EXAMINED | HIGH | no licence (GitHub metadata) |
| subsquid-labs/squid-evm-template | repo | S1_LISTED | LOW | MIT (GitHub metadata as recorded 2026-11-02, REPORTED) |
| subsquid/squid-cli | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| subsquid/squid-sdk | repo | S1_LISTED | LOW | Apache-2.0 (GitHub metadata as recorded 2026-11-02, REPORTED) |
| suislanchez/polymarket-insider-detector | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| Supabase (hosted project, CLI, Data API) | service | S3_METHOD_ADAPTED | LOW | SaaS terms; not applicable |
| tenderly/ethers | repo | S1_LISTED | LOW | , (GitHub metadata as recorded 2026-11-02, REPORTED) |
| tetratensor/polymarket-wallet-analyzer | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| The Ghosts of Polymarket: Off-chain Matches and On-chain Reverts (arXiv 2606.16852) | paper | S1_LISTED | HIGH | not recorded in our documents |
| TheophilusChinomona/polymarket-intel | repo | S2_CODE_EXAMINED | LOW | none in upstream |
| Time-weighted settlement-price manipulation test (ScienceDirect S0165176526004933) | paper | S1_LISTED | MEDIUM | not recorded in our documents |
| tlafargue/polymarket-research | repo | S1_LISTED | MEDIUM | NOASSERTION (custom) |
| troyfol/Blockchain_Investigation_Hub | repo | S1_LISTED | LOW | GPL-3.0 (GitHub metadata as recorded 2026-11-02, REPORTED) |
| TrueBlocks/trueblocks-core | repo | S1_LISTED | MEDIUM | GPL-3.0 (GitHub metadata as recorded 2026-11-02, REPORTED) |
| TrustaLabs/Airdrop-Sybil-Identification | repo | S2_CODE_EXAMINED | LOW | GPL-3.0 (REPORTED) |
| US DOJ press release of 23 April 2026 (Van Dyke indictment) | paper | S2_CODE_EXAMINED | LOW | public document |
| US House Oversight prediction-market inquiry (releases and 13 Nov 2026 memorandum) | paper | S2_CODE_EXAMINED | LOW | public record |
| usepancake/polymarket-history | repo | S1_LISTED | LOW | not recorded in our documents |
| Vedant-29/polymarket-insider-detection | repo | S1_LISTED | LOW | not recorded in our documents |
| veeradittya/polymarket-insider-detection | repo | S2_CODE_EXAMINED | MEDIUM | none (no LICENSE, REPORTED; GitHub API licence null VERIFIED 2026-11-20) |
| Victor, 'Address clustering heuristics for Ethereum' (FC 2020) and Tutela | paper | S1_LISTED | LOW | not recorded |
| vsbtc/polymarket-insider-detection | repo | S2_CODE_EXAMINED | HIGH | MIT (index.json, root EDGE_VERDICT) |
| Walker, Price is (Almost) Right (Princeton thesis 2026) | paper | S1_LISTED | MEDIUM | not recorded in our documents |
| warproxxx/poly_data | repo | S3_METHOD_ADAPTED | HIGH | LICENSE file GPL-3.0 vs pyproject MIT; nothing copied (stated in quantitative_engine README) |
| websockets 15.0.1 (Python library) | library | S3_METHOD_ADAPTED | LOW | BSD-3 (not recorded in our tree) |
| What contract metadata predicts about dispute risk (arXiv 2610.29578) | paper | S1_LISTED | MEDIUM | not recorded in our documents |
| Who Wins and Who Loses in Prediction Markets (SSRN 6443103) | paper | S1_LISTED | MEDIUM | not recorded in our documents |
| wietrade/poly_data | repo | S1_LISTED | LOW | not recorded in our documents |
| Wisdom of the Crowd or Wisdom of the Insider (SSRN 6678718) | paper | S1_LISTED | LOW | not recorded in our documents |
| X public mirrors (cdn.syndication.twimg.com, fxtwitter, vxtwitter) | service | S4_INTEGRATED_VALIDATED | LOW | public mirrors of X |
| x-pertknight/polymarket-insider-detection | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| X-sourced leads (Railgun-funded Maduro accounts, Iran 14 January whale, Snoorrason post) | paper | S4_INTEGRATED_VALIDATED | LOW | public posts |
| XChainDataGen paper (arXiv 2503.13637) and dataset (Zenodo 15341722) | dataset | S1_LISTED | LOW | not recorded |
| XChainDataGen/XChainDataGen | repo | S2_CODE_EXAMINED | MEDIUM | none (no LICENSE file, README badge says MIT, REPORTED; GitHub API licence null VERIFIED 2026-11-20) |
| Xda1Dan/wallet-forensics | repo | S2_CODE_EXAMINED | LOW | MIT (REPORTED) |
| YoppaV/polymarket-mcp | repo | S2_CODE_EXAMINED | LOW | MIT (GitHub metadata, REPORTED) |
| yungcortex/onchain-intel | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
| zhangmatt/connections | repo | S1_LISTED | LOW | UNDECLARED (GitHub metadata as recorded 2026-11-02, REPORTED) |
