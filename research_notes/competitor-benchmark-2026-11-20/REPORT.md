# Competitor benchmark: eight public Polymarket insider-detection repositories (20 Nov 2026)

**Type:** comparison note built from code read at pinned commits; the data is [`benchmark.json`](benchmark.json) and this page is its rendering by [`verify.py`](verify.py), which also checks it offline. This repository was read at `0b0882c`. Every statement about this repository was re-read in a clone at this commit (origin/main on 20 Nov 2026, after the five monitoring changes of that day).

Status words: VERIFIED: read in the file at the pinned commit, or counted in the archived tree listing. REPORTED: stated by the project itself (README, comment, paper) and not recomputed here. NOT ASSESSED: no file of that repository was read for this capability; absence of a cell value is not evidence of absence.

## Result

Across 13 capabilities compared with 8 public repositories, this repository is ahead on 4 (Fill decoding, Cross-chain exit tracing, Point-in-time discipline, Reproducible evidence packages); level on 1 (Collection and indexing); mixed on 2 (Funding tracing depth, Statistical validation and negative results); behind on 5 (Sourced information times, Population-scale scoring, Live alerting and delivery, Tests and CI, Licence and reusability); not compared on 1 (Position and PnL reconstruction).

| Capability | Position | Basis |
|---|---|---|
| Collection and indexing | **level** | Every compared repository collects its own data; ours reads chain logs, others read APIs, archives or a private database. No one collector is clearly ahead on the evidence read. |
| Fill decoding | **ahead** | Ours decodes V1 and V2 OrderFilled logs and cites tx, log index and block for each fill; the four repositories read for this use API rows, bulk archives or private data. |
| Position and PnL reconstruction | **not compared** | No PnL code of the eight was read. Outside the set, the scout read a conversion-aware lot ledger with an on-chain balance check (NeomarketExplorer, below) that goes further than our case-scoped ledger. |
| Funding tracing depth | **mixed** | Case notes trace funding trees far deeper than any competitor read. The live engine stays inside the deposit receipt plus one predecessor, while pselamy's live profiler walks up to 3 hops (with a 44-hour window and no use in its score). |
| Cross-chain exit tracing | **ahead** | Ours decodes and traces bridged exits with tested decoders; none of the funding-focused repositories read (vsbtc, pselamy, Benja-Pauls) traces exits in the files read. Four repositories were not assessed. |
| Point-in-time discipline | **ahead** | Two competitors read funding state at run time or from the chain tip (verified defects). Ours reads history strictly before t and, since 20 Nov, pins payer code and nonce to the deposit block. Residual look-ahead: public tags are still read when the alert is built. |
| Statistical validation and negative results | **mixed** | Ours has a frozen protocol, a corrected alpha and a published negative verdict, all recomputable offline. orcalayer's out-of-time negative result is far larger (author reported) and has a same-market, same-day, same-side control we lack. |
| Sourced information times | **behind** | veeradittya dates first public information systematically from GDELT with a tiered outlet list and Wayback proof; ours has sourced times for 11 of 23 registry cases and no automated news ingestion. |
| Population-scale scoring | **behind** | vsbtc publishes a 7,784-wallet ranking and orcalayer reports 356,594 scored wallets; ours publishes alert sets (45 frozen, 6,645 retrospective) and no wallet-level ranking. |
| Live alerting and delivery | **behind** | pselamy delivers alerts to Discord and Telegram and exports Prometheus metrics; ours writes alerts to local files only and has no delivery channel. |
| Tests and CI | **behind** | pselamy has a Python version matrix, two type checkers and a mutation workflow; ours has one CI job without a matrix or type checker and leaves the edge_research tests out of CI. Ours is ahead of the five repositories with no tests. |
| Licence and reusability | **behind** | Our research content is CC BY-NC-ND 4.0, which forbids derivatives; three competitors are MIT and one is CC-BY-4.0 for the whole repository. Ours is more reusable than the four with no licence. |
| Reproducible evidence packages | **ahead** | Ours runs 19 offline verify.py scripts in CI over committed evidence with SHA-256 lists; orcalayer publishes aggregates only, veeradittya's scan data is not committed, and no competitor verifier was found among the files read. |

The comparison is not audit grade for a ranking. The eight repositories were not chosen by frozen inclusion criteria: they came from a GitHub repository search and an earlier provisional card, so the set is open to a selection-bias challenge. No competitor code was executed; every competitor statement comes from files and metadata read through the public GitHub API at the pinned commits.

No first-place claim is made. The weaknesses listed below are the reasons: the main one is that this repository's own frozen detection study is negative (NOT_SUPPORTED), and an auditor will not rank a detector first on a negative result.

11 weaknesses prevent a first-place claim; they are listed below with their evidence.

## Method

- Selection: the eight repositories are those of an earlier provisional card, built from a GitHub repository search for Polymarket insider-detection projects; they were not chosen by frozen inclusion criteria. The scout then screened 625 repositories from repository search (586 after removing the registry of external work (pull request 97), the eight, our own mentions and archived repositories) and arXiv; it did not use code search.
- Reading: for each of the eight, the head commit, the recursive tree, the licence endpoint and the files cited were fetched through the public GitHub REST API on 20 Nov 2026 and read at the pinned commit. The compact metadata (heads, tree listings with blob sizes, licence results, BRKME workflow runs and compare result) is in raw/github_api_metadata.json; no third-party file content is committed.
- Our side: every statement about this repository was re-read in a clone at 0b0882c, after the five monitoring changes of 20 Nov; the test counts come from running the four suites that day.
- Not executed: no competitor code, test suite or pipeline was run. Their numbers are VERIFIED only when read or counted in their files, otherwise REPORTED.
- Positions: a capability is 'ahead' or 'behind' when files read on both sides show it; 'mixed' when this repository is ahead on one part and behind on another; 'level' when no side is clearly ahead; 'not compared' when no competitor file for it was read. No numeric score was assigned.

## Compared repositories

| Repository | Licence | Commit read | Last commit (UTC) | What it does |
|---|---|---|---|---|
| [veeradittya/polymarket-insider-detection](https://github.com/veeradittya/polymarket-insider-detection) | None. No LICENSE or COPYING file in the recursive tree, the licence endpoint returns 404 and the README names no licence: all rights reserved (`(tree)`, `(api:license)`, `README.md`) | `df957ea65a6974c11d54944776a2a1bbbf70cf4a` | 2026-06-12T16:51:15Z | Thesis-style batch research: GDELT GKG news per case, Wayback snapshots, wallet scoring on known events, an unsupervised Isolation Forest and autoencoder scan, and Leiden co-trading communities. No live component. |
| [vsbtc/polymarket-insider-detection](https://github.com/vsbtc/polymarket-insider-detection) | MIT (LICENSE file; licence endpoint MIT) (`LICENSE`, `(api:license)`) | `b2e0fe46f9b515cdb524c1ef177c3550abf1441e` | 2026-07-16T23:18:51Z | A one-commit batch pipeline: markets and trades from public APIs, a score and ranking of 7,784 wallets, a Poisson-binomial luck p-value, and each wallet's first USDC funder on Polygon through the Etherscan V2 API. One 6-wallet ring is hand coded. |
| [pselamy/polymarket-insider-tracker](https://github.com/pselamy/polymarket-insider-tracker) | MIT (LICENSE file; licence endpoint MIT) (`LICENSE`, `(api:license)`) | `49f8770c87148c41c3161198e178f2e11bf7ad23` | 2026-11-19T03:33:10Z | A production-style live polling detector: fresh-wallet, size-anomaly and niche-market signals, Discord and Telegram alerts, Prometheus metrics. No investigated cases and no forensic output. |
| [orcalayer/polymarket-insider-score-backtest](https://github.com/orcalayer/polymarket-insider-score-backtest) | CC-BY-4.0 (LICENSE file text 'Attribution 4.0 International', covering the whole repository including the script; licence endpoint CC-BY-4.0) (`LICENSE`, `(api:license)`) | `37894d686472371e675b0a7a12d4b99dedfbf61a` | 2026-11-01T08:04:13Z | A negative-result statistical backtest of a wallet 'Early score' built on a private database: scored on period A (Oct 2025 to Mar 2026), tested on period B (Apr to Sep 2026). Publishes aggregates and one script that needs a paid API key. |
| [Benja-Pauls/polymarket-insider-detection](https://github.com/Benja-Pauls/polymarket-insider-detection) | None. No LICENSE or COPYING file in the tree, licence endpoint 404, no licence in the README: all rights reserved (`(tree)`, `(api:license)`, `README.md`) | `6fae8df864d64db26ad8f04f56f2fa54882c27f3` | 2026-11-09T11:27:36Z | A label-building project: news, Reddit and X allegations, an LLM that curates candidate wallets into a 242-row table, and a retired market-level detector whose 74% hit rate is still the headline of the paper draft. |
| [matthewmurden/polymarket-insider-detection](https://github.com/matthewmurden/polymarket-insider-detection) | None. No LICENSE file in the tree and licence endpoint 404: all rights reserved (`(tree)`, `(api:license)`) | `75550647378bad11a38b536c1e17d6b20f29f205` | 2026-11-08T16:53:29Z | A C++ live lag tracker and flagger with a manual review of flagged cases and a negative control on randomly sampled markets. |
| [yasithdsl/polymarket-surveillance](https://github.com/yasithdsl/polymarket-surveillance) | None. No LICENSE file in the tree and licence endpoint 404: all rights reserved (`(tree)`, `(api:license)`) | `a98d6a1d81bb894a063dd9e9797837804d6042ac` | 2026-08-12T02:21:53Z | A dissertation codebase that compares several detectors and baselines in a backtesting harness, replays trades causally and has a small poller. |
| [BRKME/Polymarket_insider](https://github.com/BRKME/Polymarket_insider) | MIT (LICENSE file; licence endpoint MIT) (`LICENSE`, `(api:license)`) | `afe554b154dda1aa72a550699f871264656b0bce` | 2026-11-20T10:54:39Z | A GitHub Actions betting and copy-trading bot with LLM forecasts; its workflows include 'Fill Matcher (auto entry/stake)' and 'copy monitor (sports whales)'. Not a forensic tool; no chain data. |

## Capability matrix

Competitor paths are at the commit listed above; ours are links into this clone.

### Collection and indexing: level

- **This repository:** A live collector of Polygon OrderFilled logs, and a live engine that keeps fills, Gamma markets and deposit receipts in one SQLite file. Evidence: [`monitoring/livecollect/decode.py`](../../monitoring/livecollect/decode.py), [`monitoring/phi_engine/feed.py`](../../monitoring/phi_engine/feed.py), [`monitoring/phi_engine/README.md`](../../monitoring/phi_engine/README.md)
- **veeradittya/polymarket-insider-detection:** Case-filtered, resumable GDELT GKG ingestion that records each file's sha1; trades from bulk archives. Evidence: `scripts/ingest_gdelt_gkg.py`
- **vsbtc/polymarket-insider-detection:** One-shot collection of markets and trades from public APIs. Evidence: `src/collect_markets.py`, `src/collect_trades.py`
- **pselamy/polymarket-insider-tracker:** Live polling ingestor with health metrics. Evidence: `src/polymarket_insider_tracker/ingestor/health.py`
- **orcalayer/polymarket-insider-score-backtest:** Private database; the public script needs a paid API key. Evidence: `scripts/early_score_check.py`
- **Benja-Pauls/polymarket-insider-detection:** Weekly scheduled Gamma metadata snapshot. Evidence: `.github/workflows/proxy_market_metadata.yml`
- **matthewmurden/polymarket-insider-detection:** C++ live lag tracker (52 C++ source and header files). Evidence: `polyLagTracker/README.md`, `(tree)`
- **yasithdsl/polymarket-surveillance:** Data loader for a backtesting harness. Evidence: `backtesting/data_loader.py`
- **BRKME/Polymarket_insider:** Scheduled GitHub Actions collection; a 'Historical Data Collection' run succeeded on 2026-11-20. Evidence: `(api:runs)`

### Fill decoding: ahead

- **This repository:** Decodes V1 and V2 OrderFilled logs (topics at decode.py lines 18-19); each alert lists tx, log_index and block of its fills. Evidence: [`monitoring/livecollect/decode.py`](../../monitoring/livecollect/decode.py), [`monitoring/phi_engine/report.py`](../../monitoring/phi_engine/report.py)
- **veeradittya/polymarket-insider-detection:** Bulk trade archives; no log decoding seen. Evidence: `(tree)`
- **vsbtc/polymarket-insider-detection:** Public API trade rows. Evidence: `src/collect_trades.py`
- **pselamy/polymarket-insider-tracker:** Data API rows. Evidence: `src/polymarket_insider_tracker/endpoints.py`
- **orcalayer/polymarket-insider-score-backtest:** Private per-entry data, not public. Evidence: `scripts/early_score_check.py`
- **Benja-Pauls/polymarket-insider-detection:** Not assessed. Evidence: none read
- **matthewmurden/polymarket-insider-detection:** Not assessed. Evidence: none read
- **yasithdsl/polymarket-surveillance:** Not assessed. Evidence: none read
- **BRKME/Polymarket_insider:** No chain data (REPORTED). Evidence: `(tree)`

### Position and PnL reconstruction: not compared

- **This repository:** Case-scoped ledger: cash identity over Data API activity (TRADE, REDEEM), checked against on-chain pUSD mint and burn logs and the wallet balance; no MERGE, SPLIT or conversion handling found in it. Evidence: [`investigations/ballon-dor-census/sources/code/ana_20_ledger.py`](../../investigations/ballon-dor-census/sources/code/ana_20_ledger.py)
- **veeradittya/polymarket-insider-detection:** Not assessed. Evidence: none read
- **vsbtc/polymarket-insider-detection:** Not assessed. Evidence: none read
- **pselamy/polymarket-insider-tracker:** Not assessed. Evidence: none read
- **orcalayer/polymarket-insider-score-backtest:** Not assessed. Evidence: none read
- **Benja-Pauls/polymarket-insider-detection:** Not assessed. Evidence: none read
- **matthewmurden/polymarket-insider-detection:** Not assessed. Evidence: none read
- **yasithdsl/polymarket-surveillance:** Not assessed. Evidence: none read
- **BRKME/Polymarket_insider:** A 'Mark-to-Market (open positions)' workflow for its own bets, not a forensic reconstruction. Evidence: `(api:runs)`

### Funding tracing depth: mixed

- **This repository:** Live engine: payer read inside the deposit receipt, with a unique same-token earlier-log path through at most 6 pass-through contracts and ambiguous joins left unresolved; one funding predecessor checked at its own block. Case notes: multi-hop trees (links_multihop.py to depth 3, EXPLORATORY; Railgun and Relay trees in the financial-links replay). Evidence: [`monitoring/phi_engine/receipt_link_guard.py`](../../monitoring/phi_engine/receipt_link_guard.py), [`monitoring/phi_engine/enrich.py`](../../monitoring/phi_engine/enrich.py), [`research_notes/realtime-intelligence-2026-11-14/scripts/links_multihop.py`](../../research_notes/realtime-intelligence-2026-11-14/scripts/links_multihop.py), [`research_notes/financial-links-replay-2026-11-07/REPORT.md`](../../research_notes/financial-links-replay-2026-11-07/REPORT.md)
- **veeradittya/polymarket-insider-detection:** Not assessed. Evidence: none read
- **vsbtc/polymarket-insider-detection:** First funder only, one hop; first page of 300 transfers per token. Evidence: `src/onchain.py`
- **pselamy/polymarket-insider-tracker:** max_hops=3 with an 80,000-block lookback (about 44 h); funding is not used in the score. Evidence: `src/polymarket_insider_tracker/profiler/funding.py`, `src/polymarket_insider_tracker/profiler/_funding_rpc.py`, `src/polymarket_insider_tracker/detector/scorer.py`
- **orcalayer/polymarket-insider-score-backtest:** Not attempted (REPORTED from the README). Evidence: `README.md`
- **Benja-Pauls/polymarket-insider-detection:** One case script: 50,000 blocks back from the chain tip in 5,000-block chunks. Evidence: `scripts/analyze_byron_cluster.py`
- **matthewmurden/polymarket-insider-detection:** Deliberately not built. Evidence: `polyLagTracker/README.md`
- **yasithdsl/polymarket-surveillance:** Not assessed. Evidence: none read
- **BRKME/Polymarket_insider:** No chain data (REPORTED). Evidence: `(tree)`

### Cross-chain exit tracing: ahead

- **This repository:** Bridged exits decoded and traced (Mayan, LI.FI, deBridge, Relay), with decoder tests run in CI. Evidence: [`research_notes/inca-bridged-exits-2026-11-06/REPORT.md`](../../research_notes/inca-bridged-exits-2026-11-06/REPORT.md), [`research_notes/inca-bridged-exits-2026-11-06/scripts/test_decoders.py`](../../research_notes/inca-bridged-exits-2026-11-06/scripts/test_decoders.py), [`research_notes/financial-links-replay-2026-11-07/REPORT.md`](../../research_notes/financial-links-replay-2026-11-07/REPORT.md)
- **veeradittya/polymarket-insider-detection:** Not assessed. Evidence: none read
- **vsbtc/polymarket-insider-detection:** An s_exit score component exists in the ranking; its definition was not read. Evidence: `data/processed/wallet_rankings.csv`
- **pselamy/polymarket-insider-tracker:** Inbound funding only in the files read. Evidence: `src/polymarket_insider_tracker/profiler/funding.py`
- **orcalayer/polymarket-insider-score-backtest:** Not assessed. Evidence: none read
- **Benja-Pauls/polymarket-insider-detection:** Inbound funding only in the files read. Evidence: `scripts/analyze_byron_cluster.py`
- **matthewmurden/polymarket-insider-detection:** Not assessed. Evidence: none read
- **yasithdsl/polymarket-surveillance:** Not assessed. Evidence: none read
- **BRKME/Polymarket_insider:** No chain data (REPORTED). Evidence: `(tree)`

### Point-in-time discipline: ahead

- **This repository:** asof.view reads rows dated strictly before t. Since 20 Nov: payer code and nonce read at the deposit block with no latest fallback, links used only with receipt_guard_v1 provenance, C4/C5 fan-out counted from links dated before the entry. Public tags are still read when the alert is built (data_quality.payer_tags). Evidence: [`monitoring/phi_engine/asof.py`](../../monitoring/phi_engine/asof.py), [`monitoring/phi_engine/enrich.py`](../../monitoring/phi_engine/enrich.py), [`monitoring/phi_engine/report.py`](../../monitoring/phi_engine/report.py), [`research_notes/phi-engine-historical-funding-20261120/README.md`](../../research_notes/phi-engine-historical-funding-20261120/README.md), [`research_notes/phi-engine-link-provenance-20261120/README.md`](../../research_notes/phi-engine-link-provenance-20261120/README.md)
- **veeradittya/polymarket-insider-detection:** Not assessed. Evidence: none read
- **vsbtc/polymarket-insider-detection:** Funder fan-out read at run time, not as of the bet. Evidence: `src/onchain.py`
- **pselamy/polymarket-insider-tracker:** Scoring weights are fixed and stored with each assessment, so records replay. Evidence: `src/polymarket_insider_tracker/detector/scorer.py`
- **orcalayer/polymarket-insider-score-backtest:** Out-of-time split (score on Oct 2025 to Mar 2026, test on Apr to Sep 2026); the 8 Oct rule file has no public timestamp before the first commit (REPORTED). Evidence: `METHOD.md`, `README.md`
- **Benja-Pauls/polymarket-insider-detection:** Funding read back from the chain tip, not from before the bet. Evidence: `scripts/analyze_byron_cluster.py`
- **matthewmurden/polymarket-insider-detection:** Not assessed. Evidence: none read
- **yasithdsl/polymarket-surveillance:** A causal replay test exists; its body was not read. Evidence: `tests/test_causal_boost_replay.py`, `backtesting/causal_boost_replay.py`
- **BRKME/Polymarket_insider:** Not assessed. Evidence: none read

### Statistical validation and negative results: mixed

- **This repository:** Frozen protocol, alpha corrected for 18 comparisons, published NOT_SUPPORTED (T1 n=45, 13 wins, mean price 0.254, p=0.335); overall NO_EDGE_VALIDATED. Evidence: [`research_notes/early-detection-2026-11-13/study/derived/verdict.json`](../../research_notes/early-detection-2026-11-13/study/derived/verdict.json), [`EDGE_VERDICT.md`](../../EDGE_VERDICT.md)
- **veeradittya/polymarket-insider-detection:** Not assessed. Evidence: none read
- **vsbtc/polymarket-insider-detection:** Exact Poisson-binomial luck p-value per wallet over entry prices. Evidence: `src/enrich_wallets.py`
- **pselamy/polymarket-insider-tracker:** No outcome validation (no investigated cases, REPORTED). Evidence: `(tree)`
- **orcalayer/polymarket-insider-score-backtest:** Out-of-time negative result on 356,594 wallets (author reported) with a same-market, same-day, same-side control. Evidence: `README.md`, `data/check_b_same_market_day_side.csv`, `data/groups_24h_prereg.csv`
- **Benja-Pauls/polymarket-insider-detection:** The paper draft still headlines a 74% hit rate (n=113) of a detector moved to legacy/. Evidence: `paper/paper.tex`, `legacy/README.md`
- **matthewmurden/polymarket-insider-detection:** Wilson intervals and 18 randomly sampled negative-control markets. Evidence: `polyLagTracker/analysis/generalization_review.py`, `polyLagTracker/analysis/negative_control_results.json`
- **yasithdsl/polymarket-surveillance:** Detector-versus-baseline harness; tests present, not run. Evidence: `backtesting/evaluation.py`, `tests/test_sota_baselines.py`
- **BRKME/Polymarket_insider:** Not assessed. Evidence: none read

### Sourced information times: behind

- **This repository:** 11 of 23 registry cases carry a sourced first_public_information_utc (ballon-c1c7 11 of 14, maduro-iran 0 of 9); no automated news ingestion. Evidence: [`research_notes/early-detection-2026-11-13/audit/ballon-c1c7/case_registry.json`](../../research_notes/early-detection-2026-11-13/audit/ballon-c1c7/case_registry.json), [`research_notes/early-detection-2026-11-13/audit/maduro-iran/case_registry.json`](../../research_notes/early-detection-2026-11-13/audit/maduro-iran/case_registry.json)
- **veeradittya/polymarket-insider-detection:** GDELT GKG per case, tiered outlet allowlist (tier 1 anchor grade), Wayback Save Page Now and CDX. Evidence: `scripts/ingest_gdelt_gkg.py`, `configs/phase5/outlet_allowlist.yaml`, `scripts/wayback_snapshotter.py`
- **vsbtc/polymarket-insider-detection:** Not assessed. Evidence: none read
- **pselamy/polymarket-insider-tracker:** Not assessed. Evidence: none read
- **orcalayer/polymarket-insider-score-backtest:** Not assessed. Evidence: none read
- **Benja-Pauls/polymarket-insider-detection:** 44 allegation incidents with source URLs and confidence tiers (allegation sources, not information times). Evidence: `data/labels/incidents/incidents_review.csv`
- **matthewmurden/polymarket-insider-detection:** Not assessed. Evidence: none read
- **yasithdsl/polymarket-surveillance:** Not assessed. Evidence: none read
- **BRKME/Polymarket_insider:** Not assessed. Evidence: none read

### Population-scale scoring: behind

- **This repository:** The frozen study screened 34,413 markets and kept 45 alerts; a retrospective export holds 6,645 alert rows; no published wallet-level ranking. Evidence: [`research_notes/early-detection-2026-11-13/study/derived/stage1_counts.json`](../../research_notes/early-detection-2026-11-13/study/derived/stage1_counts.json), [`research_notes/early-detection-2026-11-13/study/derived/verdict.json`](../../research_notes/early-detection-2026-11-13/study/derived/verdict.json), [`research_notes/realtime-intelligence-2026-11-14/data/study_export/alerts.jsonl`](../../research_notes/realtime-intelligence-2026-11-14/data/study_export/alerts.jsonl)
- **veeradittya/polymarket-insider-detection:** A 676,642-wallet unsupervised scan claimed in the README; its data is not committed. Evidence: `README.md`, `scripts/anomaly_scan/score_anomalies.py`
- **vsbtc/polymarket-insider-detection:** 7,784 wallets ranked with components s_calib, s_conc, s_fresh, s_chain, s_exit. Evidence: `data/processed/wallet_rankings.csv`
- **pselamy/polymarket-insider-tracker:** Per-trade live score (fresh wallet 0.40, size anomaly 0.35, niche market 0.25); no population dataset. Evidence: `src/polymarket_insider_tracker/detector/scorer.py`
- **orcalayer/polymarket-insider-score-backtest:** 356,594 wallets scored (author reported, aggregates only). Evidence: `README.md`, `data/groups_24h_prereg.csv`
- **Benja-Pauls/polymarket-insider-detection:** 242 LLM-curated candidate wallets. Evidence: `data/labels/curated_final.csv`
- **matthewmurden/polymarket-insider-detection:** Not assessed. Evidence: none read
- **yasithdsl/polymarket-surveillance:** Not assessed. Evidence: none read
- **BRKME/Polymarket_insider:** Not assessed. Evidence: none read

### Live alerting and delivery: behind

- **This repository:** The live engine writes alerts to SQLite and to a hash-chained alerts.jsonl; no delivery channel; collector health is a file-reading status command. Evidence: [`monitoring/phi_engine/README.md`](../../monitoring/phi_engine/README.md), [`monitoring/phi_engine/store.py`](../../monitoring/phi_engine/store.py), [`monitoring/livecollect/HEALTHCHECK.md`](../../monitoring/livecollect/HEALTHCHECK.md)
- **veeradittya/polymarket-insider-detection:** Batch only, no live component. Evidence: `(tree)`
- **vsbtc/polymarket-insider-detection:** Batch only (one-commit pipeline). Evidence: `(tree)`
- **pselamy/polymarket-insider-tracker:** Discord and Telegram channels, Prometheus Counter, Gauge and Histogram. Evidence: `src/polymarket_insider_tracker/alerter/channels/discord.py`, `src/polymarket_insider_tracker/alerter/channels/telegram.py`, `src/polymarket_insider_tracker/ingestor/health.py`
- **orcalayer/polymarket-insider-score-backtest:** Batch only. Evidence: `(tree)`
- **Benja-Pauls/polymarket-insider-detection:** Weekly metadata job only. Evidence: `.github/workflows/proxy_market_metadata.yml`
- **matthewmurden/polymarket-insider-detection:** C++ live lag tracker and flagger. Evidence: `polyLagTracker/README.md`
- **yasithdsl/polymarket-surveillance:** A small poller (REPORTED). Evidence: `README.md`
- **BRKME/Polymarket_insider:** 19 scheduled workflows of a betting and copy-trading bot; latest runs succeeded on 2026-11-20. Evidence: `.github/workflows/copy_monitor.yml`, `(api:runs)`

### Tests and CI: behind

- **This repository:** Tests passing locally on 20 Nov: monitoring 88, forensic-intelligence 44, quantitative_engine 35, edge_research 6. CI: one ubuntu-24.04 job, no version matrix, no type checker; edge_research is not in CI. Evidence: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml), [`monitoring/tests/test_link_provenance.py`](../../monitoring/tests/test_link_provenance.py), [`edge_research/tests/test_cost_gate.py`](../../edge_research/tests/test_cost_gate.py)
- **veeradittya/polymarket-insider-detection:** No tests, no CI. Evidence: `(tree)`
- **vsbtc/polymarket-insider-detection:** No tests, no CI. Evidence: `(tree)`
- **pselamy/polymarket-insider-tracker:** 216 Python files under tests/; CI matrix 3.11, 3.12, 3.13 with mypy, Pyright, Vulture and Complexipy; mutation workflow. Evidence: `.github/workflows/ci.yml`, `.github/workflows/mutation.yml`, `tests/detector/test_scorer.py`
- **orcalayer/polymarket-insider-score-backtest:** No tests, no CI. Evidence: `(tree)`
- **Benja-Pauls/polymarket-insider-detection:** No tests; one scheduled data workflow. Evidence: `(tree)`, `.github/workflows/proxy_market_metadata.yml`
- **matthewmurden/polymarket-insider-detection:** No tests, no CI. Evidence: `(tree)`
- **yasithdsl/polymarket-surveillance:** 12 files under tests/, no CI. Evidence: `tests/test_causal_boost_replay.py`, `(tree)`
- **BRKME/Polymarket_insider:** 66 files under tests/ and 19 workflows; whether the workflows run the tests was not read. Evidence: `tests/test_journal_resolver.py`, `(tree)`

### Licence and reusability: behind

- **This repository:** Code MIT; research content CC BY-NC-ND 4.0 (no derivatives, non-commercial). Evidence: [`LICENSE`](../../LICENSE), [`LICENSE-CONTENT.md`](../../LICENSE-CONTENT.md)
- **veeradittya/polymarket-insider-detection:** None: all rights reserved. Evidence: `(tree)`, `(api:license)`
- **vsbtc/polymarket-insider-detection:** MIT. Evidence: `LICENSE`, `(api:license)`
- **pselamy/polymarket-insider-tracker:** MIT. Evidence: `LICENSE`, `(api:license)`
- **orcalayer/polymarket-insider-score-backtest:** CC-BY-4.0 for the whole repository, script included. Evidence: `LICENSE`, `(api:license)`
- **Benja-Pauls/polymarket-insider-detection:** None: all rights reserved. Evidence: `(tree)`, `(api:license)`
- **matthewmurden/polymarket-insider-detection:** None: all rights reserved. Evidence: `(tree)`, `(api:license)`
- **yasithdsl/polymarket-surveillance:** None: all rights reserved. Evidence: `(tree)`, `(api:license)`
- **BRKME/Polymarket_insider:** MIT. Evidence: `LICENSE`, `(api:license)`

### Reproducible evidence packages: ahead

- **This repository:** 19 research_notes/*/verify.py scripts run offline in CI, over committed evidence and SHA-256 lists. Evidence: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml), [`research_notes/inca-bridged-exits-2026-11-06/SHA256SUMS.txt`](../../research_notes/inca-bridged-exits-2026-11-06/SHA256SUMS.txt), [`research_notes/financial-links-replay-2026-11-07/verify.py`](../../research_notes/financial-links-replay-2026-11-07/verify.py)
- **veeradittya/polymarket-insider-detection:** The 676,642-wallet scan data is not committed. Evidence: `README.md`
- **vsbtc/polymarket-insider-detection:** Processed CSVs committed (the 7,784-row ranking among them); no verifier read. Evidence: `data/processed/wallet_rankings.csv`
- **pselamy/polymarket-insider-tracker:** No investigated case or archived alert history (REPORTED, consistent with the tree). Evidence: `(tree)`
- **orcalayer/polymarket-insider-score-backtest:** Aggregates only; per-entry data private and the script needs a paid key. Evidence: `scripts/early_score_check.py`, `data/meta.json`
- **Benja-Pauls/polymarket-insider-detection:** Label tables committed; the labels are LLM verdicts. Evidence: `data/labels/curated_final.csv`
- **matthewmurden/polymarket-insider-detection:** Decision log and negative-control results committed. Evidence: `polyLagTracker/DECISION_LOG.md`, `polyLagTracker/analysis/negative_control_results.json`
- **yasithdsl/polymarket-surveillance:** Not assessed. Evidence: none read
- **BRKME/Polymarket_insider:** Committed journals and a journal verifier; their content was not read. Evidence: `calibration_journal.jsonl`, `event_journal.jsonl`, `verify_journal.py`

## Repository by repository

### veeradittya/polymarket-insider-detection

**Strengths**

- Co-trading graph: wallets on the same side of the same market within 5 minutes, pre-filtered to the top 1% by composite rank, communities by Leiden (lines 2-34, 59, 277) (VERIFIED). Theirs: `scripts/anomaly_scan/build_cotrading_graph.py`. Ours: [`research_notes/realtime-intelligence-2026-11-14/scripts/links_multihop.py`](../../research_notes/realtime-intelligence-2026-11-14/scripts/links_multihop.py)
- IsolationForest with 200 trees plus a PyTorch autoencoder D-32-8-32-D (lines 14-16, 141) (VERIFIED). Theirs: `scripts/anomaly_scan/score_anomalies.py`. Ours: [`monitoring/phi_engine/asof.py`](../../monitoring/phi_engine/asof.py)
- Resumable, case-filtered GDELT V2 GKG ingestion that records each file's sha1 (lines 2-26) (VERIFIED). Theirs: `scripts/ingest_gdelt_gkg.py`. Ours: [`research_notes/early-detection-2026-11-13/audit/ballon-c1c7/case_registry.json`](../../research_notes/early-detection-2026-11-13/audit/ballon-c1c7/case_registry.json)
- Tiered outlet allowlist, tier 1 anchor grade (line 12) (VERIFIED). Theirs: `configs/phase5/outlet_allowlist.yaml`. Ours: [`research_notes/early-detection-2026-11-13/audit/maduro-iran/case_registry.json`](../../research_notes/early-detection-2026-11-13/audit/maduro-iran/case_registry.json)
- Wayback Save Page Now plus CDX lookup (lines 86-87) (VERIFIED). Theirs: `scripts/wayback_snapshotter.py`. Ours: [`research_notes/early-detection-2026-11-13/audit/ballon-c1c7/case_registry.json`](../../research_notes/early-detection-2026-11-13/audit/ballon-c1c7/case_registry.json)

**Defects**

- No licence, so no file can be copied (VERIFIED). Theirs: `(tree)`, `(api:license)`. Ours: [`LICENSE`](../../LICENSE)
- Scoring script in 4 stacked versions (scoring_run.py and _v6_1, _v6_2, _v6_3); no tests and no CI (VERIFIED). Theirs: `scripts/scoring_run.py`, `scripts/scoring_run_v6_3.py`, `(tree)`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)
- The 676,642-wallet scan is a README claim; its data is not committed (README line 40) (REPORTED). Theirs: `README.md`. Ours: [`research_notes/early-detection-2026-11-13/study/derived/stage1_counts.json`](../../research_notes/early-detection-2026-11-13/study/derived/stage1_counts.json)

**What it does better than this repository**

- Systematic dating of first public information from GDELT with a tiered outlet allowlist and Wayback proof. Ours: 11 of 23 registry cases are dated and nothing ingests news automatically (VERIFIED). Theirs: `scripts/ingest_gdelt_gkg.py`, `configs/phase5/outlet_allowlist.yaml`. Ours: [`research_notes/early-detection-2026-11-13/audit/ballon-c1c7/case_registry.json`](../../research_notes/early-detection-2026-11-13/audit/ballon-c1c7/case_registry.json), [`research_notes/early-detection-2026-11-13/audit/maduro-iran/case_registry.json`](../../research_notes/early-detection-2026-11-13/audit/maduro-iran/case_registry.json)
- An all-wallet unsupervised scan. Ours scores flagged entries only; the only IsolationForest or networkx code in our tree is vendored PolySentinel code (VERIFIED). Theirs: `scripts/anomaly_scan/score_anomalies.py`. Ours: [`monitoring/phi_engine/asof.py`](../../monitoring/phi_engine/asof.py), [`investigations/polysentinel/sources/polysentinel/investigation.py`](../../investigations/polysentinel/sources/polysentinel/investigation.py)

**What this repository does better**

- Exact on-chain fill decoding for V1 and V2 OrderFilled; theirs reads bulk trade archives only (VERIFIED). Theirs: `(tree)`. Ours: [`monitoring/livecollect/decode.py`](../../monitoring/livecollect/decode.py)
- A frozen protocol with an alpha corrected for 18 comparisons and a published negative verdict (VERIFIED). Theirs: `(tree)`. Ours: [`research_notes/early-detection-2026-11-13/study/derived/verdict.json`](../../research_notes/early-detection-2026-11-13/study/derived/verdict.json)
- Tests that run in CI; theirs has none (VERIFIED). Theirs: `(tree)`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)

**Errors of the earlier provisional card**

- The earlier card said our cases have no sourced first-public-information time. Wrong: 11 of the 14 ballon-c1c7 registry cases carry first_public_information_utc.

### vsbtc/polymarket-insider-detection

**Strengths**

- wallet_rankings.csv has 7,784 rows with components s_calib, s_conc, s_fresh, s_chain and s_exit (VERIFIED). Theirs: `data/processed/wallet_rankings.csv`. Ours: [`research_notes/early-detection-2026-11-13/study/derived/verdict.json`](../../research_notes/early-detection-2026-11-13/study/derived/verdict.json)
- Inflows of USDC.e and native USDC; a funder counts as a service when it pays 50 or more distinct recipients (SERVICE_RECIPIENTS=50, line 29; funder_fanout, lines 48-60) (VERIFIED). Theirs: `src/onchain.py`. Ours: [`monitoring/phi_engine/enrich.py`](../../monitoring/phi_engine/enrich.py)
- luck_pvalue: an exact O(n^2) Poisson-binomial dynamic programme over entry prices (lines 26-47) (VERIFIED). Theirs: `src/enrich_wallets.py`. Ours: [`research_notes/early-detection-2026-11-13/study/derived/verdict.json`](../../research_notes/early-detection-2026-11-13/study/derived/verdict.json)
- ring_funding_edges.csv: 8 edges with a test_then_send flag (VERIFIED). Theirs: `data/processed/ring_funding_edges.csv`. Ours: [`research_notes/financial-links-replay-2026-11-07/REPORT.md`](../../research_notes/financial-links-replay-2026-11-07/REPORT.md)

**Defects**

- Funding is first funder only, one hop: usdc_inflows reads the first page of 300 transfers per token and funder_fanout stops at 10,000 transfers (lines 36-60) (VERIFIED). Theirs: `src/onchain.py`. Ours: [`monitoring/phi_engine/receipt_link_guard.py`](../../monitoring/phi_engine/receipt_link_guard.py)
- The fan-out count is read at run time, not as of the bet (no timestamp filter in funder_fanout) (VERIFIED). Theirs: `src/onchain.py`. Ours: [`monitoring/phi_engine/enrich.py`](../../monitoring/phi_engine/enrich.py)
- Needs an Etherscan API key (line 18); whether the free tier still covers Polygon is unknown (VERIFIED). Theirs: `src/onchain.py`. Ours: [`monitoring/phi_engine/README.md`](../../monitoring/phi_engine/README.md)
- ring_trace.py hard codes 2 funders and 4 fresh wallets (lines 19-30) (VERIFIED). Theirs: `src/ring_trace.py`. Ours: [`research_notes/realtime-intelligence-2026-11-14/scripts/links_multihop.py`](../../research_notes/realtime-intelligence-2026-11-14/scripts/links_multihop.py)
- One commit, no tests, no CI (VERIFIED). Theirs: `(tree)`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)

**What it does better than this repository**

- Publishes a population ranking of 7,784 scored wallets. Ours: the frozen study publishes 45 alerts over 34,413 markets and no wallet ranking (VERIFIED). Theirs: `data/processed/wallet_rankings.csv`. Ours: [`research_notes/early-detection-2026-11-13/study/derived/stage1_counts.json`](../../research_notes/early-detection-2026-11-13/study/derived/stage1_counts.json), [`research_notes/early-detection-2026-11-13/study/derived/verdict.json`](../../research_notes/early-detection-2026-11-13/study/derived/verdict.json)
- Counts a funder's fan-out over its on-chain transfers (up to 10,000). Ours counts fan-out only over the wallets the live engine itself has linked (FANOUT_MAX 10, enrich.py), so a busy funder that the engine has seen pay few wallets is not excluded by that rule (the block-pinned nonce rule BUSY_NONCE 1,000 still applies) (VERIFIED). Theirs: `src/onchain.py`. Ours: [`monitoring/phi_engine/enrich.py`](../../monitoring/phi_engine/enrich.py)

**What this repository does better**

- Point-in-time: asof.view reads only rows dated before t, and since 20 Nov payer code and nonce are read at the deposit block; vsbtc reads fan-out at run time (VERIFIED). Theirs: `src/onchain.py`. Ours: [`monitoring/phi_engine/asof.py`](../../monitoring/phi_engine/asof.py), [`research_notes/phi-engine-historical-funding-20261120/README.md`](../../research_notes/phi-engine-historical-funding-20261120/README.md)
- The payer is read inside the deposit transaction across USDC, USDC.e and pUSD, wrapping and pass-through included, and equal-amount ties are refused rather than resolved to the first sender; vsbtc takes the first inbound transfer (VERIFIED). Theirs: `src/onchain.py`. Ours: [`monitoring/phi_engine/chainfund.py`](../../monitoring/phi_engine/chainfund.py), [`monitoring/phi_engine/receipt_link_guard.py`](../../monitoring/phi_engine/receipt_link_guard.py), [`research_notes/receipt-link-ambiguity-20261120/README.md`](../../research_notes/receipt-link-ambiguity-20261120/README.md)
- Multi-hop tracing to depth 3 with a stated service rule (WINDOW 10,000 blocks, service = code, tag or 1,000 or more transactions, FANOUT_MAX 10), labelled EXPLORATORY (VERIFIED). Theirs: `src/onchain.py`. Ours: [`research_notes/realtime-intelligence-2026-11-14/scripts/links_multihop.py`](../../research_notes/realtime-intelligence-2026-11-14/scripts/links_multihop.py)
- Tests and CI (VERIFIED). Theirs: `(tree)`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)

**Errors of the earlier provisional card**

- The earlier card said our deep tracer is tied to case folders. Partly wrong: the deposit-payer reader is a generic function of the live engine; only the multi-hop tracer is study scoped.

### pselamy/polymarket-insider-tracker

**Strengths**

- DEFAULT_WEIGHTS fresh_wallet 0.40, size_anomaly 0.35, niche_market 0.25, immutable so that stored records replay (lines 41-53) (VERIFIED). Theirs: `src/polymarket_insider_tracker/detector/scorer.py`. Ours: [`monitoring/phi_engine/report.py`](../../monitoring/phi_engine/report.py)
- Health module uses prometheus_client Counter, Gauge and Histogram (line 18 onward) (VERIFIED). Theirs: `src/polymarket_insider_tracker/ingestor/health.py`. Ours: [`monitoring/livecollect/HEALTHCHECK.md`](../../monitoring/livecollect/HEALTHCHECK.md)
- Discord and Telegram alert channels (VERIFIED). Theirs: `src/polymarket_insider_tracker/alerter/channels/discord.py`, `src/polymarket_insider_tracker/alerter/channels/telegram.py`. Ours: [`monitoring/phi_engine/README.md`](../../monitoring/phi_engine/README.md)
- CI matrix 3.11, 3.12, 3.13 plus mypy, Pyright, Vulture and Complexipy (lines 38-48); mutation and relentless-ci workflows (VERIFIED). Theirs: `.github/workflows/ci.yml`, `.github/workflows/mutation.yml`, `.github/workflows/relentless-ci.yml`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)
- 216 Python files under tests/ (VERIFIED). Theirs: `(tree)`. Ours: [`monitoring/tests/test_engine.py`](../../monitoring/tests/test_engine.py)
- Funding profiler with max_hops=3 and DEFAULT_MAX_LOOKBACK_BLOCKS=80_000 (about 44 h at 2 s per block) (VERIFIED). Theirs: `src/polymarket_insider_tracker/profiler/funding.py`, `src/polymarket_insider_tracker/profiler/_funding_rpc.py`. Ours: [`monitoring/phi_engine/enrich.py`](../../monitoring/phi_engine/enrich.py)

**Defects**

- Funding is never used in the score: scorer.py contains 0 occurrences of 'funding' (VERIFIED). Theirs: `src/polymarket_insider_tracker/detector/scorer.py`. Ours: [`monitoring/phi_engine/enrich.py`](../../monitoring/phi_engine/enrich.py)
- The 80,000-block funding lookback (about 44 h) misses older funding (VERIFIED). Theirs: `src/polymarket_insider_tracker/profiler/_funding_rpc.py`. Ours: [`monitoring/phi_engine/asof.py`](../../monitoring/phi_engine/asof.py)
- No investigated wallet, market or archived alert history (REPORTED). Theirs: `(tree)`. Ours: [`research_notes/financial-links-replay-2026-11-07/REPORT.md`](../../research_notes/financial-links-replay-2026-11-07/REPORT.md)

**What it does better than this repository**

- Each assessment is stored with its scoring configuration and replays exactly. Ours: the alert body has an id hash but no detector or configuration version field (VERIFIED). Theirs: `src/polymarket_insider_tracker/detector/scorer.py`. Ours: [`monitoring/phi_engine/report.py`](../../monitoring/phi_engine/report.py), [`monitoring/tests/test_replay.py`](../../monitoring/tests/test_replay.py)
- Alert delivery to Discord and Telegram plus Prometheus metrics. Ours: no delivery channel in monitoring/ (the only 'telegram' hit is a secret-scanner pattern, scripts/phi_lib.py line 26) and health is a file-reading status command (VERIFIED). Theirs: `src/polymarket_insider_tracker/alerter/channels/telegram.py`, `src/polymarket_insider_tracker/ingestor/health.py`. Ours: [`scripts/phi_lib.py`](../../scripts/phi_lib.py), [`monitoring/livecollect/HEALTHCHECK.md`](../../monitoring/livecollect/HEALTHCHECK.md)
- CI with a version matrix and type checkers. Ours: one ubuntu-24.04 job, no matrix, no type checker, and the edge_research tests are not in CI (VERIFIED). Theirs: `.github/workflows/ci.yml`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml), [`edge_research/tests/test_cost_gate.py`](../../edge_research/tests/test_cost_gate.py)

**What this repository does better**

- Fills come from on-chain OrderFilled V1 and V2 logs, with tx, log_index and block in each alert; theirs come from Data API rows (VERIFIED). Theirs: `src/polymarket_insider_tracker/endpoints.py`. Ours: [`monitoring/livecollect/decode.py`](../../monitoring/livecollect/decode.py), [`monitoring/phi_engine/report.py`](../../monitoring/phi_engine/report.py)
- The deposit payer is read in the deposit transaction and listed in the alert (deposits and plain_keys_behind_deposits), and since 20 Nov only links with receipt_guard_v1 provenance are listed (VERIFIED). Theirs: `src/polymarket_insider_tracker/profiler/funding.py`. Ours: [`monitoring/phi_engine/report.py`](../../monitoring/phi_engine/report.py), [`research_notes/phi-engine-link-provenance-20261120/README.md`](../../research_notes/phi-engine-link-provenance-20261120/README.md)
- Forensic case files and frozen studies with published negative verdicts (VERIFIED). Theirs: `(tree)`. Ours: [`research_notes/early-detection-2026-11-13/study/derived/verdict.json`](../../research_notes/early-detection-2026-11-13/study/derived/verdict.json), [`EDGE_VERDICT.md`](../../EDGE_VERDICT.md)

### orcalayer/polymarket-insider-score-backtest

**Strengths**

- 356,594 wallets scored (README line 9; the number is author reported) (REPORTED). Theirs: `README.md`. Ours: [`research_notes/early-detection-2026-11-13/study/derived/verdict.json`](../../research_notes/early-detection-2026-11-13/study/derived/verdict.json)
- groups_24h_prereg.csv top10: move24_cents 0.864, t 6.99, entries 429,032, events 18,826 (VERIFIED). Theirs: `data/groups_24h_prereg.csv`. Ours: [`research_notes/early-detection-2026-11-13/study/derived/verdict.json`](../../research_notes/early-detection-2026-11-13/study/derived/verdict.json)
- A same-market, same-day, same-side control (README line 26) (VERIFIED). Theirs: `README.md`, `data/check_b_same_market_day_side.csv`. Ours: [`research_notes/early-detection-2026-11-13/verify.py`](../../research_notes/early-detection-2026-11-13/verify.py)
- A dated rule-change table starting 8 October (lines 3, 51-54) (VERIFIED). Theirs: `METHOD.md`. Ours: [`edge_research/PROTOCOL.lock`](../../edge_research/PROTOCOL.lock)
- A 519-line script with 429 handling that needs a Premium key (lines 25, 89, 99) (VERIFIED). Theirs: `scripts/early_score_check.py`. Ours: [`research_notes/early-detection-2026-11-13/verify.py`](../../research_notes/early-detection-2026-11-13/verify.py)

**Defects**

- The headline cannot be recomputed: per-entry data is private and the API key is paid (script line 25) (VERIFIED). Theirs: `scripts/early_score_check.py`. Ours: [`research_notes/early-detection-2026-11-13/verify.py`](../../research_notes/early-detection-2026-11-13/verify.py)
- The 8 October pre-registration has no public timestamp before the first commit (REPORTED). Theirs: `METHOD.md`. Ours: [`edge_research/PROTOCOL.lock`](../../edge_research/PROTOCOL.lock)
- No tests and no CI (VERIFIED). Theirs: `(tree)`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)

**What it does better than this repository**

- Sample size of the out-of-time test: 356,594 wallets and 25,903 events (author reported). Ours: 45 alerts on 44 events (REPORTED). Theirs: `README.md`. Ours: [`research_notes/early-detection-2026-11-13/study/derived/verdict.json`](../../research_notes/early-detection-2026-11-13/study/derived/verdict.json)
- An explicit entry-price control against other wallets in the same market, day and side. Ours: no such control in the early-detection note (plain-text search found none) (VERIFIED). Theirs: `data/check_b_same_market_day_side.csv`. Ours: [`research_notes/early-detection-2026-11-13/verify.py`](../../research_notes/early-detection-2026-11-13/verify.py)

**What this repository does better**

- Full public reproducibility: CI runs 19 offline verify.py scripts from public data; orcalayer publishes aggregates only (VERIFIED). Theirs: `scripts/early_score_check.py`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)
- On-chain funding and payer evidence, which they do not attempt (VERIFIED). Theirs: `README.md`. Ours: [`monitoring/phi_engine/receipt_link_guard.py`](../../monitoring/phi_engine/receipt_link_guard.py)

### Benja-Pauls/polymarket-insider-detection

**Strengths**

- incidents_review.csv: 44 incidents with confidence_tier, n_sources and top_source_url (VERIFIED). Theirs: `data/labels/incidents/incidents_review.csv`. Ours: [`research_notes/external-polymarket-cases-2026-11-07/CASES.csv`](../../research_notes/external-polymarket-cases-2026-11-07/CASES.csv)
- curated_final.csv: 242 rows with evidence_urls and model_used (VERIFIED). Theirs: `data/labels/curated_final.csv`. Ours: [`research_notes/external-polymarket-cases-2026-11-07/EXTERNAL_WALLETS.csv`](../../research_notes/external-polymarket-cases-2026-11-07/EXTERNAL_WALLETS.csv)
- A weekly cron '17 3 * * 1' refreshes market metadata (VERIFIED). Theirs: `.github/workflows/proxy_market_metadata.yml`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)

**Defects**

- resolve_funding uses max_back_blocks=50_000 from the chain tip in 5,000-block chunks: it sees about 28 h before now, not before the bet (lines 29-64) (VERIFIED). Theirs: `scripts/analyze_byron_cluster.py`. Ours: [`monitoring/phi_engine/enrich.py`](../../monitoring/phi_engine/enrich.py)
- paper.tex still headlines a 74% hit rate, n=113 (lines 52 and 300), although the market-level detector moved to legacy/ (VERIFIED). Theirs: `paper/paper.tex`, `legacy/README.md`. Ours: [`EDGE_VERDICT.md`](../../EDGE_VERDICT.md)
- No tests (VERIFIED). Theirs: `(tree)`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)
- Labels are LLM verdicts (model_used column), which makes them circular as ground truth (VERIFIED). Theirs: `data/labels/curated_final.csv`. Ours: [`research_notes/external-polymarket-cases-2026-11-07/CASES.csv`](../../research_notes/external-polymarket-cases-2026-11-07/CASES.csv)

**What it does better than this repository**

- A labelled external allegation table of 44 incidents with source URLs and tiers. Ours: 13 cases and 12 external wallets (VERIFIED). Theirs: `data/labels/incidents/incidents_review.csv`. Ours: [`research_notes/external-polymarket-cases-2026-11-07/CASES.csv`](../../research_notes/external-polymarket-cases-2026-11-07/CASES.csv), [`research_notes/external-polymarket-cases-2026-11-07/EXTERNAL_WALLETS.csv`](../../research_notes/external-polymarket-cases-2026-11-07/EXTERNAL_WALLETS.csv)

**What this repository does better**

- Funding is read inside the deposit transaction with state pinned to the deposit block, not from the chain tip (VERIFIED). Theirs: `scripts/analyze_byron_cluster.py`. Ours: [`monitoring/phi_engine/enrich.py`](../../monitoring/phi_engine/enrich.py), [`research_notes/phi-engine-historical-funding-20261120/README.md`](../../research_notes/phi-engine-historical-funding-20261120/README.md)
- Tests and CI; no LLM-generated labels used as ground truth (VERIFIED). Theirs: `(tree)`, `data/labels/curated_final.csv`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)

### matthewmurden/polymarket-insider-detection

**Strengths**

- 52 C++ source and header files (VERIFIED). Theirs: `(tree)`. Ours: [`monitoring/livecollect/decode.py`](../../monitoring/livecollect/decode.py)
- generalization_review.py: Wilson intervals (6 hits) and 18 negative-control markets (VERIFIED). Theirs: `polyLagTracker/analysis/generalization_review.py`. Ours: [`research_notes/financial-cycle-negative-control-20261118/REPORT.md`](../../research_notes/financial-cycle-negative-control-20261118/REPORT.md)
- A decision log and negative-control results are committed (VERIFIED). Theirs: `polyLagTracker/DECISION_LOG.md`, `polyLagTracker/analysis/negative_control_results.json`. Ours: [`research_notes/early-detection-2026-11-13/study/derived/verdict.json`](../../research_notes/early-detection-2026-11-13/study/derived/verdict.json)

**Defects**

- Funding tracing deliberately not built (README lines 70, 653, 745) (VERIFIED). Theirs: `polyLagTracker/README.md`. Ours: [`monitoring/phi_engine/receipt_link_guard.py`](../../monitoring/phi_engine/receipt_link_guard.py)
- No tests, no CI, no licence (VERIFIED). Theirs: `(tree)`, `(api:license)`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)

**What it does better than this repository**

- A randomly sampled negative-control market set with Wilson intervals inside the flagger's own review. Ours: comparable controls exist only inside frozen studies and archival replays, not in the live engine (not rechecked exhaustively) (REPORTED). Theirs: `polyLagTracker/analysis/generalization_review.py`. Ours: [`research_notes/financial-cycle-negative-control-20261118/REPORT.md`](../../research_notes/financial-cycle-negative-control-20261118/REPORT.md), [`monitoring/phi_engine/README.md`](../../monitoring/phi_engine/README.md)

**What this repository does better**

- Funding evidence, V2 decoding, tests and CI (VERIFIED). Theirs: `polyLagTracker/README.md`, `(tree)`. Ours: [`monitoring/livecollect/decode.py`](../../monitoring/livecollect/decode.py), [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)

**Errors of the earlier provisional card**

- The earlier card said '108 KB README'. The root README.md is 5,965 bytes; the 108,707-byte file is polyLagTracker/README.md.

### yasithdsl/polymarket-surveillance

**Strengths**

- 12 files in tests/, including test_causal_boost_replay.py (VERIFIED). Theirs: `tests/test_causal_boost_replay.py`, `(tree)`. Ours: [`monitoring/tests/test_replay.py`](../../monitoring/tests/test_replay.py)

**Defects**

- No CI and no licence (VERIFIED). Theirs: `(tree)`, `(api:license)`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)

**What it does better than this repository**

- A regression test that second-layer boosts never use later trades (file present, body not read), inside a detector-versus-baseline harness. Ours: asof self-tests exist, but no detector-versus-baseline harness at a matched flag budget was found (REPORTED). Theirs: `tests/test_causal_boost_replay.py`, `tests/test_sota_baselines.py`. Ours: [`monitoring/tests/test_engine.py`](../../monitoring/tests/test_engine.py), [`monitoring/phi_engine/asof.py`](../../monitoring/phi_engine/asof.py)

**What this repository does better**

- On-chain evidence, funding and case files (VERIFIED). Theirs: `(tree)`. Ours: [`monitoring/phi_engine/receipt_link_guard.py`](../../monitoring/phi_engine/receipt_link_guard.py), [`research_notes/financial-links-replay-2026-11-07/REPORT.md`](../../research_notes/financial-links-replay-2026-11-07/REPORT.md)

### BRKME/Polymarket_insider

**Strengths**

- 19 workflows and 66 files in tests/ at the pinned head (VERIFIED). Theirs: `(tree)`, `tests/test_journal_resolver.py`. Ours: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)
- A long unattended run: the latest workflow runs succeeded on 2026-11-20 (VERIFIED). Theirs: `(api:runs)`. Ours: [`monitoring/phi_engine/README.md`](../../monitoring/phi_engine/README.md)

**Defects**

- The head moved from 9583b15 to afe554b by 2 automated commits that touch only copy_seen.json, so the earlier reading is unaffected (VERIFIED). Theirs: `(api:compare)`, `copy_seen.json`. Ours: [`research_notes/competitor-benchmark-2026-11-20/raw/github_api_metadata.json`](../../research_notes/competitor-benchmark-2026-11-20/raw/github_api_metadata.json)
- No chain data (REPORTED). Theirs: `(tree)`. Ours: [`monitoring/livecollect/decode.py`](../../monitoring/livecollect/decode.py)

**What it does better than this repository**

- Committed, time-stamped forward journals over months (content not read). Ours: the committed live alert records found are 1 and 13 rows (maduro-iran phase11 and phase12 live_alerts.csv); the 6,645-row alert export is retrospective (VERIFIED). Theirs: `calibration_journal.jsonl`, `event_journal.jsonl`. Ours: [`investigations/maduro-iran/sources/phase11/live_alerts.csv`](../../investigations/maduro-iran/sources/phase11/live_alerts.csv), [`investigations/maduro-iran/sources/phase12/live_alerts.csv`](../../investigations/maduro-iran/sources/phase12/live_alerts.csv), [`research_notes/realtime-intelligence-2026-11-14/data/study_export/alerts.jsonl`](../../research_notes/realtime-intelligence-2026-11-14/data/study_export/alerts.jsonl)

**What this repository does better**

- Every forensic dimension: funding, fills from logs, case evidence (VERIFIED). Theirs: `(tree)`. Ours: [`monitoring/livecollect/decode.py`](../../monitoring/livecollect/decode.py), [`monitoring/phi_engine/receipt_link_guard.py`](../../monitoring/phi_engine/receipt_link_guard.py)

**Errors of the earlier provisional card**

- The earlier reader counted 20 workflows; the count is 19 at afe554b.
- The earlier summary abbreviated the head as afe554b154; the full commit is afe554b154dda1aa72a550699f871264656b0bce.

## Corrections to earlier statements about this repository

- The earlier card said the live engine has no fan-out rule and that the fan-out rule exists only in the EXPLORATORY links_multihop.py. Wrong: the live engine has FANOUT_MAX = 10 (enrich.py line 21, present since the engine was added on 14 Nov), counted over the engine's own stored links dated before the entry, and a block-pinned nonce rule (BUSY_NONCE 1,000). What is true: it does not count a funder's on-chain fan-out. Evidence: [`monitoring/phi_engine/enrich.py`](../../monitoring/phi_engine/enrich.py)
- The earlier card listed a self-disclosed look-ahead in which payer tags and transaction counts are read when the alert is built. Since 20 Nov transaction counts and contract code are read at the deposit block, and unavailable historical state stays unresolved; public tags are still read when the alert is built and are used only to exclude services. Evidence: [`monitoring/phi_engine/report.py`](../../monitoring/phi_engine/report.py), [`research_notes/phi-engine-historical-funding-20261120/README.md`](../../research_notes/phi-engine-historical-funding-20261120/README.md)
- Since 20 Nov the live engine refuses ambiguous equal-amount receipt joins (unique same-token earlier-log path required) and excludes funding links cached before these guards from new C4/C5 alerts. This can lower C4/C5 coverage; no prospective comparison has measured precision. Evidence: [`monitoring/phi_engine/receipt_link_guard.py`](../../monitoring/phi_engine/receipt_link_guard.py), [`research_notes/receipt-link-ambiguity-20261120/README.md`](../../research_notes/receipt-link-ambiguity-20261120/README.md), [`research_notes/phi-engine-link-provenance-20261120/README.md`](../../research_notes/phi-engine-link-provenance-20261120/README.md)
- The earlier card counted 51 monitoring tests. On 20 Nov at 0b0882c the count is 88, all passing. Evidence: [`monitoring/tests/test_link_provenance.py`](../../monitoring/tests/test_link_provenance.py), [`monitoring/tests/test_chainfund_unique_receipt_path.py`](../../monitoring/tests/test_chainfund_unique_receipt_path.py)
- The earlier list of French-language files outside sources/ named 16 paths; the heuristic list has 17 (research_notes/independent-forensic-audit-2026-11-08/REPORT.md was omitted). Evidence: [`research_notes/independent-forensic-audit-2026-11-08/REPORT.md`](../../research_notes/independent-forensic-audit-2026-11-08/REPORT.md)

## Capabilities worth integrating

Ranked by the readers' priority (the compared set first, then the scout's projects); not a measured ranking.

| Rank | Capability | Source | What the licence allows | Today | Measurable gain | Effort | Ours |
|---|---|---|---|---|---|---|---|
| 1 | Stamp each alert with a detector version (sha256 of asof.py, receipt_link_guard.py, enrich.py and report.py plus the threshold constants) and add a test that rebuilds a stored alert byte for byte | Idea from pselamy src/polymarket_insider_tracker/detector/scorer.py lines 41-47 | MIT: copying allowed with the notice, but only the idea is needed (about 15 lines of our own code) | The alert body has an id hash and no detector or configuration version; test_replay.py has no version check | Share of published alerts tied to the exact code and thresholds that produced them, from 0% to 100% | S | [`monitoring/phi_engine/report.py`](../../monitoring/phi_engine/report.py), [`monitoring/tests/test_replay.py`](../../monitoring/tests/test_replay.py) |
| 2 | Run the edge_research tests in CI and add a Python version matrix to the existing job | Pattern from pselamy .github/workflows/ci.yml lines 42-62 | MIT; a workflow matrix is a generic pattern, re-implement | 6 edge_research tests pass locally and are not in CI; one ubuntu-24.04 job, no matrix | Test files and Python versions proven in the CI log | S | [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml), [`edge_research/tests/test_cost_gate.py`](../../edge_research/tests/test_cost_gate.py) |
| 3 | A point-in-time on-chain fan-out for deposit payers in the live engine: transfers of the payer counted only before the entry, EXPLORATORY, without changing frozen alert classes | Our own links_multihop.py rules; compare vsbtc src/onchain.py lines 29 and 48-60 (fan-out of 50 or more, but read at run time: do not copy) | Our own code; vsbtc is MIT but its run-time design is the weaker one | FANOUT_MAX 10 counts only links the engine stored; nonce and code are block-pinned since 20 Nov; public tags are read at alert time | Alerts whose payer class changes when on-chain fan-out is computed as of the trade, counted | M | [`monitoring/phi_engine/enrich.py`](../../monitoring/phi_engine/enrich.py), [`research_notes/realtime-intelligence-2026-11-14/scripts/links_multihop.py`](../../research_notes/realtime-intelligence-2026-11-14/scripts/links_multihop.py) |
| 4 | Sourced first-public-information times dated from GDELT GKG and Wayback with a tiered outlet allowlist | Method of veeradittya scripts/ingest_gdelt_gkg.py, scripts/wayback_snapshotter.py, configs/phase5/outlet_allowlist.yaml | None: all rights reserved. Re-implement from the public GDELT and Wayback APIs only; copy no code or list | 11 of 23 registry cases dated; no automated news ingestion | Number of cases with a sourced information time (11 now) | M | [`research_notes/early-detection-2026-11-13/audit/ballon-c1c7/case_registry.json`](../../research_notes/early-detection-2026-11-13/audit/ballon-c1c7/case_registry.json) |
| 5 | A same-market, same-day, same-side entry-price control for flagged entries, EXPLORATORY and post hoc on the 45 frozen rows | orcalayer README.md line 26 and data/check_b_same_market_day_side.csv | CC-BY-4.0: copying with attribution allowed; a short re-implementation with a citation is simpler | The frozen study compares outcomes with the price paid (T1); no same-cell control | Separates entry-price edge from information in the negative result | M | [`research_notes/early-detection-2026-11-13/study/derived/verdict.json`](../../research_notes/early-detection-2026-11-13/study/derived/verdict.json) |
| 6 | A larger labelled external allegation table with source URLs and tiers, as a recall check | Benja-Pauls data/labels/incidents/incidents_review.csv, as a finding aid only | None: all rights reserved. Re-source every fact and URL independently; do not copy the file | 13 cases and 12 external wallets | Case count for a recall test (13 now) | M | [`research_notes/external-polymarket-cases-2026-11-07/CASES.csv`](../../research_notes/external-polymarket-cases-2026-11-07/CASES.csv) |
| 7 | Optional alert delivery (standard-library Telegram call) and a metrics file for the live collector | pselamy alerter/channels/telegram.py and ingestor/health.py | MIT; a standard-library re-implementation is smaller than their stack | No delivery; status reads files | Seconds from trade to delivered alert (report.py already records seconds_from_trade_to_alert) | S | [`monitoring/phi_engine/report.py`](../../monitoring/phi_engine/report.py), [`monitoring/livecollect/HEALTHCHECK.md`](../../monitoring/livecollect/HEALTHCHECK.md) |
| 8 | Conversion-aware position ledger (NegRisk conversions carry cost basis) closed by an on-chain ERC1155 balance check | NeomarketExplorer/neomarket-clickhouse-indexer src/ledger-engine.ts and src/reconcile-balances.ts (scout reading) | None: all rights reserved. Specify and re-implement independently | Case-scoped cash ledger without MERGE, SPLIT or conversion handling | Positions reconcilable to on-chain balances | M | [`investigations/ballon-dor-census/sources/code/ana_20_ledger.py`](../../investigations/ballon-dor-census/sources/code/ana_20_ledger.py) |
| 9 | Mint-type bucket and occurrence-counter dedupe that keeps true duplicate fills | 1816x/Polymarket-PnL-AuditLog src/analysis/fees.ts and src/ingest/rebuild-fills.ts (scout reading) | None: all rights reserved. Re-implement the rules independently | Not checked in our decoder (the scout's search was plain text only) | Fills lost or mis-bucketed, counted | S | [`monitoring/livecollect/decode.py`](../../monitoring/livecollect/decode.py), [`research_notes/financial-links-replay-2026-11-07/tools/xfm_decode.py`](../../research_notes/financial-links-replay-2026-11-07/tools/xfm_decode.py) |
| 10 | Nonce-invalidation and reverted-settlement behaviour per wallet as a new anomaly family | TheOneWhoBurns/polymarket-nonce-guard and arXiv 2609.17902 (selector 0x627cdcb9 recomputed by the scout) | MIT; the idea needs a frozen plan before any use | No hit for incrementNonce or 627cdcb9 in our documents and code | A new, testable family; EXPLORATORY | M | [`monitoring/livecollect/decode.py`](../../monitoring/livecollect/decode.py) |
| 11 | Offline derivation of position ids from a conditionId (USDC.e for ordinary markets, wrapped collateral for NegRisk) to check token-to-market mapping | zh0006xu/PolyLens src/core/ctf_utils.py; the scout re-derived it and matched Gamma on 3 of 3 markets | MIT; small enough to re-derive independently | No alt_bn128 or getCollectionId code found | Mis-bucketed asset ids, counted | S | [`monitoring/phi_engine/feed.py`](../../monitoring/phi_engine/feed.py) |

## Newer projects and papers found by the scout

| Project | Licence | Last commit (UTC) | What it offers | Caveats |
|---|---|---|---|---|
| [NeomarketExplorer/neomarket-clickhouse-indexer](https://github.com/NeomarketExplorer/neomarket-clickhouse-indexer) | none (all rights reserved) | 2026-02-21T16:39:33Z | Indexes CTF Exchange, ConditionalTokens and NegRiskAdapter events; per-wallet lots with cost basis; conversion carries burned cost basis; ledger checked against balanceOfBatch | No tests in tree; pre-V2 snapshot; a fallback injects last prices into zero cost basis; not run |
| [1816x/Polymarket-PnL-AuditLog](https://github.com/1816x/Polymarket-PnL-AuditLog) | none (all rights reserved) | 2026-07-27T17:35:36Z | Cash-identity PnL per market; replay-safe dedupe that keeps true duplicate fills; mint-type bucket; maker and taker role validated on chain | Specialised to short crypto Up/Down markets and 4 wallets; reconciliation figures reported, not rerun; tests not run |
| [TheOneWhoBurns/polymarket-nonce-guard](https://github.com/TheOneWhoBurns/polymarket-nonce-guard) | MIT | 2026-11-09T22:52:44Z | Filters V1 exchange calls with selector 0x627cdcb9 (incrementNonce); paired with arXiv 2609.17902 | Treats every incrementNonce caller as an exploiter (README admits false positives); V1 address only; tests cover helpers only |
| [DGHW/polymarket-trader-miner](https://github.com/DGHW/polymarket-trader-miner) | MIT | 2026-08-11T11:35:03Z | Settlement-closed ledger; flags and excludes positions touched by MERGE, SPLIT or conversion and publishes analyzable_share | The exclusion is a Data API limit, not a chain limit; reconciliation claims reported, not rerun |
| [zh0006xu/PolyLens](https://github.com/zh0006xu/PolyLens) | MIT | 2026-02-06T04:52:00Z | Offline position-id derivation from a conditionId; re-derived and matched on 3 of 3 live markets by the scout | No tests; its indexer decodes only the V1 OrderFilled and treats each OrderFilled as a trade: not for trade reconstruction |
| [Sentinel-Nexus/sentinel-nexus-ai-builder-cup](https://github.com/Sentinel-Nexus/sentinel-nexus-ai-builder-cup) | MIT | 2026-10-18T11:55:04Z | Explainable fixed-weight score over 9 features; synthetic decoy groups (household, exchange cluster, busy honest) as a false-positive harness for common-funder rules | Results come from its own generator (circular); hackathon code |
| [alphalab-research/wash-replication-2026](https://github.com/alphalab-research/wash-replication-2026) | CC-BY-NC-4.0 (non-commercial) | 2026-05-27T15:21:57Z | Notebook and docs for a wash-trading paper (SSRN 6835860) | Its NegRisk family rule zeroes the wrong field: the scout refuted it on 9 markets (questionID, not conditionId, gives negRiskMarketID); a printed collateral address is wrong |
| [tabookhandawn/interchange-osint-cross-chain-tracing](https://github.com/tabookhandawn/interchange-osint-cross-chain-tracing) | MIT file, no tracing code | 2026-11-04T04:53:30Z | Nothing usable: marketing for a closed Windows app | Rejected; star count is not evidence |

| Paper | Method we could use |
|---|---|
| [Ghost-Filled Orders: Detecting and Testing Atomicity Violations in Non-Custodial Prediction Markets](https://arxiv.org/abs/2609.17902) | Count reverted settlement transactions and separate attacker profit from counterparty loss (abstract level, REPORTED) |
| [Measuring Trade Direction in a Prediction Market: Settlement Ground Truth and Trading-Cost Measurement on Polymarket](https://arxiv.org/abs/2610.06412) | Sign each print against the taker leg of its settlement; never pool maker and taker legs under mint-and-merge (REPORTED) |
| [The Anatomy of a Blockchain Prediction Market: Polymarket in the 2024 U.S. Presidential Election](https://arxiv.org/abs/2603.03136) | Separate turnover from net inflow, since mint and burn inflate naive volume (REPORTED) |
| [Settlement Manipulation in Prediction Markets](https://arxiv.org/abs/2606.31675) | Event study of spot order flow around settlement of short crypto contracts (REPORTED) |
| [Beyond Profit Rankings: Identifying, Understanding, and Evaluating Smart Money in Prediction Markets](https://arxiv.org/abs/2610.34754) | Profitability persistence tests and behavioural clustering of wallet trades (REPORTED) |
| [Resolution Is Not Settlement, Part II: Protocol Finality and Observed Redemption on Polymarket](https://arxiv.org/abs/2609.15373) | Event-sourced condition and redemption framework at a fixed snapshot block (REPORTED) |
| [Per-Market Information Leakage and Order-Flow Skill: Two Methodological Lenses on Informed Trading in Decentralized Prediction Markets](https://arxiv.org/abs/2605.02287) | Layered detection: sign-randomisation test, composite wallet-market screen, per-market leakage score (REPORTED) |
| [Wash Trading in Polymarket V1 NegRisk, January to December 2024](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=6835860) | Deterministic wash detector, trade-count wash rate 0.22% (REPORTED, unreplicated, SSRN under moderation) |

## Weaknesses that prevent a first-place claim

1. No validated detection result: the frozen early-detection verdict is NOT_SUPPORTED (T1 n=45, 13 wins, mean price 0.254, p=0.335) and the overall verdict is NO_EDGE_VALIDATED. Evidence: [`research_notes/early-detection-2026-11-13/study/derived/verdict.json`](../../research_notes/early-detection-2026-11-13/study/derived/verdict.json), [`EDGE_VERDICT.md`](../../EDGE_VERDICT.md)
2. Scale: 45 alerts over 34,413 markets, against a published 7,784-wallet ranking (vsbtc) and 356,594 scored wallets (orcalayer, author reported); no population-level wallet dataset is published. Evidence: [`research_notes/early-detection-2026-11-13/study/derived/stage1_counts.json`](../../research_notes/early-detection-2026-11-13/study/derived/stage1_counts.json)
3. The live engine's funding attribution stays inside the deposit receipt plus one predecessor; multi-hop tracing exists only as an EXPLORATORY study script. Evidence: [`monitoring/phi_engine/receipt_link_guard.py`](../../monitoring/phi_engine/receipt_link_guard.py), [`research_notes/realtime-intelligence-2026-11-14/scripts/links_multihop.py`](../../research_notes/realtime-intelligence-2026-11-14/scripts/links_multihop.py)
4. Residual look-ahead: public payer tags are read when the alert is built, not as of the trade (data_quality.payer_tags), although code and nonce are block-pinned since 20 Nov. Evidence: [`monitoring/phi_engine/report.py`](../../monitoring/phi_engine/report.py)
5. Alerts carry no detector or configuration version. Evidence: [`monitoring/phi_engine/report.py`](../../monitoring/phi_engine/report.py)
6. CI is weaker than pselamy's: one job, no version matrix, no type checker, edge_research tests not run in CI. Evidence: [`.github/workflows/repository-integrity.yml`](../../.github/workflows/repository-integrity.yml)
7. Language: by an EXPLORATORY word-frequency heuristic, 164 of 441 tracked .md files contained French on 20 Nov, 17 of them outside sources/ folders (13 in the forensic-engine note, the two livecollect documents, the quantitative_engine README and one audit report). Evidence: [`research_notes/forensic-engine-2026-11-13/RAPPORT_FINAL.md`](../../research_notes/forensic-engine-2026-11-13/RAPPORT_FINAL.md), [`monitoring/livecollect/HEALTHCHECK.md`](../../monitoring/livecollect/HEALTHCHECK.md), [`monitoring/livecollect/README.md`](../../monitoring/livecollect/README.md), [`integrations/quantitative_engine/README.md`](../../integrations/quantitative_engine/README.md), [`research_notes/independent-forensic-audit-2026-11-08/REPORT.md`](../../research_notes/independent-forensic-audit-2026-11-08/REPORT.md)
8. Only 11 of 23 registry cases have a sourced first-public-information time; the maduro-iran registry has none. Evidence: [`research_notes/early-detection-2026-11-13/audit/maduro-iran/case_registry.json`](../../research_notes/early-detection-2026-11-13/audit/maduro-iran/case_registry.json)
9. Research content is CC BY-NC-ND 4.0, which forbids derivatives, against MIT or CC-BY competitors. Evidence: [`LICENSE-CONTENT.md`](../../LICENSE-CONTENT.md)
10. No long committed forward-dated live alert history: the committed live alert files found have 1 and 13 rows. Evidence: [`investigations/maduro-iran/sources/phase11/live_alerts.csv`](../../investigations/maduro-iran/sources/phase11/live_alerts.csv), [`investigations/maduro-iran/sources/phase12/live_alerts.csv`](../../investigations/maduro-iran/sources/phase12/live_alerts.csv)
11. This benchmark is not audit grade: the repository set was not fixed by frozen inclusion criteria and no competitor code was executed. Evidence: [`research_notes/competitor-benchmark-2026-11-20/benchmark.json`](../../research_notes/competitor-benchmark-2026-11-20/benchmark.json)

## What is not shown

- No competitor score, rank or weighted total: the earlier numeric card scores were neither re-scored nor endorsed.
- No third-party code, data file or licence text is reproduced; licences marked none mean all rights reserved.
- Files not opened: veeradittya's scan output and Leiden results, yasithdsl's test bodies, matthewmurden's C++ sources, BRKME's journals, pselamy's mutation workflow body and recall test.
- The scout's eight projects and eight papers were read by the scout only; their tree listings are not archived here, so their paths are not checked by verify.py.

## Reproduce

```bash
python3 -B research_notes/competitor-benchmark-2026-11-20/verify.py            # offline checks
python3 -B research_notes/competitor-benchmark-2026-11-20/verify.py --online   # also re-reads the eight head commits
python3 -B research_notes/competitor-benchmark-2026-11-20/verify.py --write    # re-renders REPORT.md from benchmark.json
python3 -B research_notes/competitor-benchmark-2026-11-20/test_verify.py       # tests of the checks
A competitor file at the pinned commit: https://github.com/<repo>/blob/<commit>/<path>
```

## Limits

- The set of repositories is not exhaustive and was not fixed in advance, so no ranking follows from it.
- Cells marked Not assessed say nothing about the competitor; several 'ahead' positions rest on the competitors that were read for that capability.
- Whether the Etherscan V2 free tier still covers Polygon (vsbtc's dependency) is unknown.
- The French-language count is a word-frequency heuristic (more than 5 hits of common French words), not a language classifier.
- Paper findings are abstract level and were not rechecked.
- This note's own verify.py is not yet called by the CI workflow.
