# Competitor benchmark, extension: 24 more public repositories (20 Nov 2026)

Extends [the published benchmark](../competitor-benchmark-2026-11-20/REPORT.md) (8 repositories, 13 capabilities),
which is not modified. The data is [`scout.json`](scout.json); the repository table below is its rendering by
[`verify.py`](verify.py), which checks it offline. No competitor code was executed or copied.

## Result

**`COMPETITIVE_NOT_FIRST_PROVEN`. No first place is claimed.**

- In the files read, none of the 24 added repositories combines a frozen out-of-sample test with a corrected threshold,
  funding state read at the block of each payment, and evidence recomputed offline in CI. Two have parts of it:
  `tlafargue/polymarket-research` recomputes its headline numbers offline from committed data, and
  `andy1245-rgb/PolyCrawler` flags wallets from data strictly before a cut-off date. The published positions "ahead"
  on point-in-time discipline and reproducible evidence stand.
- Several of them are ahead of this repository on things it does not do: a position and PnL ledger checked against an
  independent source (`bradca0/polymarket-pnl`, reported 829 of 901 token balances matching the positions endpoint on
  51 wallets), a V1 and V2 decoded trade dataset cross-checked against other indexers (`polyflux-io/polymarket-onchain-trades`),
  links between wallets that bet alike without any funding link (`Samy-z/PolyClusters`), and a persistence test of
  wallet skill (`tlafargue/polymarket-research`, split-half rank correlation of zero over 6,119 wallets, reported).
- On one common replay, two external rules re-implemented in the Nobel note (an Apache-2.0 four-signal flag and an MIT
  0-10 score) put the Nobel group first: 1st of 11 and 1st of 16 flagged, both at 22:46:49 UTC. This repository's
  class `C1` reaches it 102 seconds earlier but as the 4th of 57 alerts of the night. One case chosen because it ended
  well cannot rank detectors: every rule here was written after it, or after cases like it.

## Positions of the published benchmark that move

Only the capabilities whose evidence changed on 20 November are listed; the ten others are as published.

| Capability | Published | Now | Basis |
|---|---|---|---|
| Live alerting and delivery | behind | **mixed** | The radar layer (`monitoring/radar`, its own pull request) seals every engine alert with its inputs, controls and code hashes into a hash-chained file, evaluates it later in a second chain, renders a local page, and can notify a webhook or Telegram; tested offline. It is not in production, and `pselamy/polymarket-insider-tracker` still delivers to Discord and Telegram with metrics. |
| Point-in-time discipline | ahead | **ahead, with a measured residual** | The frozen study of 14 November described payers as read that day. Read at the block of each payment, its group class `C4` gives 19 alert entries on four events instead of 8 on one ([Nobel note](../nobel-strict-replay-2026-11-20/REPORT.md)); the extra groups are funded by keys that are busy or tagged as Relay solvers today. |
| Sourced information times | behind | behind | One more case has a sourced announcement time (Nobel 2025, 09:00 UTC, from the Norwegian Nobel Institute); there is still no automated news ingestion, as `veeradittya/polymarket-insider-detection` has. |

## What the 24 show that the comparison did not have

| Capability | Seen in | This repository |
|---|---|---|
| Position and PnL ledger checked against an independent source | `bradca0/polymarket-pnl` (no licence) | none beyond case notes: behind |
| Decoded V1 and V2 trade dataset, cross-checked against independent indexers | `polyflux-io/polymarket-onchain-trades` (MIT code) | decoders inside the engines and case notes, no published dataset: behind |
| Links between wallets that bet alike, without funding | `Samy-z/PolyClusters` (MIT) | none: behind |
| Persistence of wallet skill across time | `tlafargue/polymarket-research` (MIT code) | none: behind |
| Several detectors compared on one point-in-time replay | this repository (Nobel note) | not seen in the files read of the 24 |
| A third exchange address of protocol V2 in an indexer's configuration | `enviodev/polymarket-v2-indexer` lists `0xe2222d002000ba0053cef3375333610f64600036` | not in the engine's registry; the engine's sentinel found no unregistered emitter of `OrderFilled` on 20 November (`python3 -m phi_engine doctor`); not checked further |

## Method

- Selection: about 60 GitHub repository and code searches (Polymarket with insider, detection, cluster, wallet, graph,
  sybil, wash, pnl, forensic, anomaly, alerts, indexer, smart money, coalition, vpin, manipulation, and the topic hash of
  the V2 `OrderFilled` event). Kept: Polymarket-specific, public, code or reproducible data present, pushed on or after
  1 January 2026, not among the eight nor the scout list of the published note, and showing at least one of wallet
  clustering or funding, PnL or fill reconstruction, V2 decoding, point-in-time or negative-result research, or live
  surveillance. Stars only break ties. Two repositories found by search returned 404. The rules were written by the
  reader before reading the code but were not frozen: the set is open to a selection challenge.
- Reading: through the GitHub contents API, on 20 November 2026. The "What its code or README shows" column says which:
  for about a third of the repositories only the README and the file tree were read. Licences come from the LICENSE file
  and the licence endpoint; a repository without a licence is all rights reserved, and its code may not be reused.
- Re-implementation: only methods of permissively licensed repositories were re-implemented, from their published
  rules, in original code (Nobel note, amendment 1).

## The 24 repositories

<!-- table:repos -->
| Repository | Licence | Last push | Category | What its code or README shows | Point-in-time risk | Tests |
|---|---|---|---|---|---|---|
| [andy1245-rgb/PolyCrawler](https://github.com/andy1245-rgb/PolyCrawler) | Apache-2.0 | 2026-11-16 | Wallet clustering by funding, backtest-first insider discov… | Read src/polycrawler/discovery/{flagging,links,funding,engine}.py and research/*.md. Step 1 flags wallets from data strictly before a splitDate: isNew (age <= 14 d), isFocused (markets traded <= 15), isLongshot (avg buy… | Low for discovery (buys filtered ts < cutoff, markets resolved < cutoff, activity cut at cutoff). Own audit finds whole-burst entry selection uses future legs… | 196 tests in 26 files (README: 195 pass, 1 fails); fixtures present (tests/fixtures/*.jso… |
| [anthonylin99/polymarket-insider-detection](https://github.com/anthonylin99/polymarket-insider-detection) | none (all rights reserved) | 2026-05-29 | Take-home investigation with ranked lead queue | Read report/heuristics.md and the head of src/identify_candidate_leads.py. Lead screen: buy on the side that resolved as winner, entry 20-85 cents, >= 24 h before resolution, >= $3,000 same wallet/market/side; ranking t… | High by design: selection on the realised winner; a lead queue, not a detector. | No tests directory; verify_submission.py. |
| [Antoinechss/Polymarket-coalition-detection](https://github.com/Antoinechss/Polymarket-coalition-detection) | none (all rights reserved) | 2026-11-16 | V2 OrderFilled decoding plus streaming anomaly score | Read ingest/decoders/orders_filled.py, common/params.py and anomaly_detection/anomaly_scorer.py. Decoder reads topic 0xd543adfd..., maker and taker from topics, data words side, tokenId, makerAmountFilled, takerAmountFi… | Low in the scorer (streaming). Wallet identity is the maker topic, not the proxy owner: not verified. | None. |
| [Arturas-Salivonas/Pollysider](https://github.com/Arturas-Salivonas/Pollysider) | MIT | 2026-02-03 | Live surveillance UI (WebSocket) | README only: wallet age, size, velocity, timing signals over WebSocket feeds. | Not verified. | None. |
| [ashwin-bar/polymarket-insider-trading-vpin](https://github.com/ashwin-bar/polymarket-insider-trading-vpin) | MIT | 2026-08-26 | Prediction-market microstructure research (VPIN) | README only. Volume-time buckets, VPIN = /buy volume - sell volume/ / total volume, period Brier contribution; market fixed-effects panel regression (coefficient 0.0053, n = 147,780 periods, 3,748 markets); independence… | Calibration uses resolved outcomes (ex post, intended). | 1 test file listed. |
| [bradca0/polymarket-pnl (PolyEdge, package pmsr)](https://github.com/bradca0/polymarket-pnl) | none (all rights reserved) | 2026-08-03 | Position and PnL reconstruction plus skill scoring | Read README.md, src/pmsr/pnl.py and src/pmsr/skill.py. Folds six Data API activity types into cash and token balances (TRADE, SPLIT, MERGE, REDEEM, REWARD excluded by default, CONVERSION counted and skipped); recovers t… | Designed to avoid it (skill estimated only on markets resolved before the cut). Fill price used as the market price (admitted in market_brier docstring). | 4 test files (test_pnl, test_skill, test_forecast, test_data_api); offline status not run. |
| [Diego-2510/PolyAugur](https://github.com/Diego-2510/PolyAugur) | MIT | 2026-11-04 | Market anomaly screening with LLM review and evaluation | README and docs/EVALUATION.md read; code not read. Gamma ingestion, rule-based market anomaly scoring (volume, price, liquidity, topic), optional Mistral review with strict JSON schema, CLOB trade concentration, whale t… | tests/test_time_semantics.py exists; contents not read. | 15 test files plus CI; fixtures present, offline status not verified. |
| [enviodev/poly-whale-tracker](https://github.com/enviodev/poly-whale-tracker) | none (all rights reserved) | 2026-10-28 | Live OrderFilled streaming (HyperSync TUI) | README and tree only: streams OrderFilled via HyperSync and shows BUY trades above a USD threshold, optional address filter; src/config.ts mentions the V2 topic. | None in scope. | None. |
| [enviodev/polymarket-v2-indexer](https://github.com/enviodev/polymarket-v2-indexer) | none (all rights reserved) | 2026-08-11 | V2 contracts indexer (OrderFilled with builder codes, pUSD,… | Read README.md and config.yaml. Event signature OrderFilled(bytes32 orderHash, address maker, address taker, uint8 side, uint256 tokenId, uint256 makerAmountFilled, uint256 takerAmountFilled, uint256 fee, bytes32 builde… | None in the scope (chain events). | 15 tests (test/*.test.ts, CI workflow) using real on-chain data via HyperSync: not offlin… |
| [EricChong02/cs6290-polymarket-signal-analysis-group13](https://github.com/EricChong02/cs6290-polymarket-signal-analysis-group13) | none (all rights reserved) | 2026-04-19 | Market manipulation anomaly detection (student project) | README only (Chinese). Hourly data for 35+ markets; ZScoreDetector, VolumeDetector, ThresholdDetector fused by a ConflictResolver; liquidity-tier validation and significance tests. | Not verified. | 18 test files; not run. |
| [escalonalabs/polymarket-alert-bot](https://github.com/escalonalabs/polymarket-alert-bot) | none (all rights reserved) | 2026-04-11 | Live alerting pipeline | README and tree only. Collect, normalise, score, dedupe with cooldown, Telegram dispatch, file artifacts; circuit breaker and healthcheck modules; backtest and feedback analytics. | Not verified. | 16 test files; not run. |
| [hugompt/polymarket-microstructure-lab](https://github.com/hugompt/polymarket-microstructure-lab) | MIT | 2026-06-27 | Wallet PnL reconstruction and latency paper trading | README only (code not read). Reconstructs one wallet's PnL from public data, computes break-even win rate, forward paper trades across a latency grid; reports fees eat 34% of gross, 52.4% win vs 49.8% break-even. | Not verified. | 22 test files in tree, offline status not verified. |
| [irregularchat/poly-sniff (fork of agile-enigma/poly-sniff)](https://github.com/irregularchat/poly-sniff) | unclear, treated as all rights reserved | 2026-11-17 | Per-market behavioural flagger plus claim-to-market search | Read poly_sniff/metrics/{conviction,dominance,timing,directional}.py and config.py. Per user per market: directional consistency >= 0.85, dominant-side volume ratio >= 0.90, USDC-weighted price conviction <= 0 (contrari… | hoursBeforeResolution uses the realised resolution time, which is not known at trade time for open-ended markets. | 1 test file (test_signal.py), offline not verified. |
| [jonathanhawkins/polymarket-graphrag](https://github.com/jonathanhawkins/polymarket-graphrag) | none (all rights reserved) | 2026-05-22 | Funding-graph investigation (Neo4j) and PnL reproduction | Read README.md and docs/STORY.md (grep), pipeline file list. Ingests trades into Neo4j, traces USDC funding to depth 2 via Etherscan v2, reproduces the Theo whale cluster and a realised PnL of about $78.4M (92% of Bloom… | Retrospective by design (known cluster re-found); funding edges not cut at trade time. Not verified in code. | None in tree. |
| [kobeythacker32/Vigil](https://github.com/kobeythacker32/Vigil) | none (all rights reserved) | 2026-05-17 | Suspicious-trade detection plus paper trading (Polymarket a… | README and tree only: detection engine, related-market repricing map, isolated paper-trading simulation, React dashboard. | Not verified. | 21 test files; not run. |
| [mzkworks/polymarket-insider-detector](https://github.com/mzkworks/polymarket-insider-detector) | none (all rights reserved) | 2026-02-16 | Wallet scoring and temporal-graph clustering | README only. Composite insider score 0-100 from binomial win-rate test, timing before resolution, size-win correlation, PnL; temporal correlation graph (same market within 5 min) with Louvain. | Outcome-based components: ex post (from README). | None. |
| [NickNaskida/polymarket-insider-bot](https://github.com/NickNaskida/polymarket-insider-bot) | MIT | 2026-01-04 | Live surveillance bot | Read src/anomaly_detector.py. Additive 0-10 score: age < 1 d +2 or < N days +1; size > market mean x multiplier +3; wallet concentration >= threshold +2; niche market volume +1/+2; repeated entries +1; coordinated activ… | Wallet age and concentration from API at run time, not as-of the trade (not verified). | None. |
| [Ong-pogs/polymarket-insider-detector-bot](https://github.com/Ong-pogs/polymarket-insider-detector-bot) | MIT | 2026-11-02 | Live surveillance bot (paid API) | README read. Bets >= $2,000 grouped per wallet and outcome, scored out of 100 from wallet age at bet time (30), thin history (20), concentration (20), long-shot price (15), holder rank (15); flag at >= 60; RECORDED vs L… | Self-declared: wallet history is a snapshot. | bot/engine.test.mjs with node --test and CI; offline not verified. |
| [polyflux-io/polymarket-onchain-trades](https://github.com/polyflux-io/polymarket-onchain-trades) | MIT (code) | 2026-10-29 | V1 and V2 OrderFilled decoding, full on-chain dataset | Read README.md and docs/DATASET_CARD.md (grep). Era-agnostic extractor with V1 and V2 parsers, splits, merges, redeems, settlements; one parquet per day; cross-checks of daily fill counts against moose-code/polymarket-o… | Raw chain data is as-of by block; derived markets table comes from Gamma at build time (not verified). | No tests directory; cross-check scripts only. |
| [rwondo/polymarket-insider](https://github.com/rwondo/polymarket-insider) | MIT | 2026-09-28 | Live surveillance bot | README read (scoring table); code files listed, not read. Polls Data API trades >= $500 every 60 s; score = 40 if the first trade seen from a wallet > $10,000, +30 if size > 3 sd above the wallet's running mean (Welford… | Streaming, but model retrained hourly on stored trades (leakage inside the training window not verified). | 6 test files, README says offline; not run. |
| [Samy-z/PolyClusters](https://github.com/Samy-z/PolyClusters) | MIT | 2026-08-06 | Co-betting wallet clustering | Read README.md and polyclusters/analysis/cluster.py (header). Net positions per (wallet, market, outcome) bet key; IDF-weighted, size-weighted (log USD) sparse user x bet matrix, cosine similarity threshold 0.35, min 2… | Clustering uses whole-history positions and resolution-based win rates: retrospective. No as-of cut. Not verified whether suspicion score uses outcomes (README… | 1 test file; offline status not verified. |
| [suislanchez/polymarket-insider-detector](https://github.com/suislanchez/polymarket-insider-detector) | none (all rights reserved) | 2026-02-09 | Wallet scoring (statistical) and funding clustering | Read lib/detection.js and the head of lib/demoData.js and app/api/analyze/route.js. Binomial p-value of wins against p = 0.5 (ignores entry price), win-rate bands, average minutes before resolution, last-minute ratio, v… | High: win rate and resolution timing are ex post by construction. | None. |
| [tlafargue/polymarket-research](https://github.com/tlafargue/polymarket-research) | MIT (code) | 2026-07-24 | Prediction-market manipulation and edge research, published… | Read README.md, LICENSE-CODE and the file list. Sixteen falsification studies over a tick archive; wallet skill split-half (past edge versus future edge, 6,119 wallets) shows zero rank correlation and only uncopyable ma… | Look-ahead and stale quotes are named as failure causes of apparent edges; method details not verified. | No tests directory; verify_stats.py is the check (offline status stated by README, not ru… |
| [whongach/polymarket-insider-trading](https://github.com/whongach/polymarket-insider-trading) | MIT | 2026-06-11 | Event-study research (bachelor thesis) | Read the notebook cells (event_study_clean.ipynb) and README. Contract-level event study on daily Dune volume: estimation window days -60 to -8, event window -7 to -1 before t0, cumulative abnormal volume (CAV) and a pr… | t0 is a realised event date by design (event study); estimation window avoids the event window. | None; data missing. |
<!-- /table:repos -->

## Research published since 1 October 2026

No new peer-reviewed or arXiv paper on Polymarket insider detection was found (arXiv and web search on 20 November 2026,
not exhaustive). Related: "Whether Is Not When: Separating Occurrence from Timing in Polymarket Prices" (arXiv
2610.36639, 27 October 2026), "What Prediction-Market Contracts Reveal at Launch" (2610.29578), "Beyond Profit Rankings:
Identifying, Understanding, and Evaluating Smart Money in Prediction Markets" (2610.34754), "Reading the Count" (2611.00338).

## Limits

- No competitor code or test was run; a number of theirs is reported, not recomputed.
- Positions are qualitative and come from the files read; absence in a file read is not absence in the project.
- The selection was not frozen and stars are low across the field (49 at most): this is a scan, not a census.
