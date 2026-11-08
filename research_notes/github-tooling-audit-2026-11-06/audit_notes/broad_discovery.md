# Broad GitHub discovery (blockchain forensics gaps), 2026-11-06

Method: `gh search repos` (about 70 two-to-three word queries, raw results in raw/bd/all.txt and all2.txt), `gh search code` (about 20 queries), `gh api` for issues, releases and licenses, and shallow clones into clones/<owner>__<repo> (l2beat via sparse checkout of packages/backend/src/modules/interop only, 13 MB). Nothing was run, installed or imported. No keys were used. The 75 screened repos and the other agents' repos were excluded. Pinned SHA = HEAD of the default branch at clone time. "Date" = commit date of that SHA.

## Ranked candidates

### 1. l2beat/l2beat, interop plugins. ADOPT-CANDIDATE (method and test vectors, not code)
- SHA 3197d43b00f71695e1cd7bbcfbbaaf94c9aa9085, 2026-11-05. MIT (LICENSE file, 1 KB). Path: packages/backend/src/modules/interop/plugins/.
- Capability, matching source and destination legs by protocol identifier, never by amount or time:
  - Relay: `db.find(TokenSent, {id})` at relay/relay.plugin.ts:35. The id comes from the Relay requests API (relay/relay.indexer.ts:261,278), so it dies with requests/v2 on 24 Nov.
  - Mayan Swift: `OrderCreated(bytes32 key)` joined to `OrderFulfilled(key, sequence)` (mayan-swift.ts:55-57, 437). The Wormhole `LogMessagePublished.sequence` is checked at :235 to bind the unlock message.
  - deBridge DLN: `orderId` bytes32 across CreatedOrder, FulfilledOrder, ClaimedUnlock (debridge-dln.ts:15-31, lookups at :188, :232).
  - Also CCTP v1 and v2 (cctp/cctp-v2.plugin.ts:302,365), Across by deposit id (across/across.plugin.ts:179,235), and LI.FI intents, GasZip, Wormhole token bridge and NTT, Hyperlane, Axelar, Stargate.
- Collector hygiene to copy:
  - Pagination integrity: relay.indexer.ts:180 aborts on a repeated continuation cursor, and :185-187 aborts on a cursor with zero rows.
  - Dedup by event id, within the chunk and against the database: relay.indexer.ts:299-312.
- Adds: tested, cross-protocol identifier schemas (event signatures, which field is the key) that we can port to Python as an offline cross-check of our Relay calldata and memo matching. It also gives a second implementation for the post-retirement period, since the EVM-side keys for Mayan, DLN and CCTP are independent of Relay.
- Limit, important: Solana is declared "one-sided". The plugins never decode the Solana leg. Mayan Swift on a one-sided chain is counted only when the EVM source unlocks (mayan-swift.ts:429-440), and `grep -i solana` in relay/ finds only script.ts:28. So it gives the EVM keys to search for on Solana, not a Solana decoder.
- Cost and risk: pure TypeScript, needs only RPC and logs we already pull. The repo is 1 GB, so use a sparse clone. Activity is very high, so pin a commit. Relay part tied to a retiring API.

### 2. XChainDataGen/XChainDataGen (mirror: AndreAugusto11/XChainDataGen). ADOPT-CANDIDATE for the Solana-leg method; code license unclear
- SHA 5ab92992f6bcc83b6fa7f15d7b69b653e6e819f1, 2026-09-24. No LICENSE file in the tree. README header badge says MIT, pyproject has no license field. Written confirmation is needed before copying code. Paper: arXiv 2503.13637. Dataset: Zenodo 15341722 (not downloaded).
- Capability, EVM and Solana legs joined by protocol key:
  - Mayan order-hash reconstruction: extractor/mayan/utils/OrderHash.py:6-60 rebuilds the 239-byte keccak preimage (trader, chains, tokens, amounts, deadline, referrer, random). This lets the Solana-side order be tied to the EVM `key`.
  - Mayan joins: generator/mayan/generator.py:254 (`MayanInitOrder.order_hash == MayanOrderFulfilled.key`), :449, :652.
  - Solana instruction decoding: extractor/mayan/handler.py:416 and extractor/debridge/handler.py:257 (`handle_solana_events`). Signature enumeration with `before` cursor: rpcs/solana_rpc_client.py:23-67.
  - deBridge: generator/debridge/generator.py:280 joins on `order_id`. But :400 joins Solana-created orders on `maker_order_nonce`, which is weaker.
  - CCTP: generator/cctp/generator.py:162 joins on `nonce` plus chain pair plus token. Across: generator/across/generator.py:154 joins on `deposit_id` plus `output_amount`.
- Dedup lesson from its own history: PR #8 and #9 fixed lost events because nonce is not unique. It now uses tx_hash and log index (evm_extractor.py:85 stores `log_index`).
- Adds: the only code-backed Solana-to-EVM key derivation found (Mayan), plus deBridge Solana order decoding.
- Risks:
  - Decoding is fragile. handler.py:296-320 finds transfer instructions by hard-coded offsets (`idx + 6`).
  - It uses a node RPC and database stack (Docker, Postgres).
  - The Solana decoder depends on a custom `parseTransactionByHash`.
  - Issue #30 is an open NoneType error on tx input_data.
  - No LICENSE file, so use as a reference to re-derive from the public Mayan SDK (mayan-finance/swap-sdk) rather than copy.

### 3. prettydeath/TornadoCash-demixer. ADOPT-CANDIDATE (design and tests; code is MIT)
- SHA cc30ba7c19f990d7a055614a9f80500adac9c307, 2026-10-29. MIT. PyPI `tornado-demix`, Zenodo DOI, 20 releases, v2.20.0. 0 open issues. Not the already-screened prettydeath/wallet-attribution.
- Capability, exchange deposit-address detection and attribution (problem 2) with a chance baseline:
  - tornado_demix/deposit_addresses.py:104 `classify_deposit_address`. Rules at :9-36: quiet account (under 1000 txs, at most 50 senders), at least 80% of outflow goes to hot wallets, the sweep follows the incoming amount within 3200 blocks and is short by at most 0.01 ETH or 1% (`forwards_to`, :70, the Victor FC 2020 forwarding test). Sweep targets are either labelled exchanges or "busy" addresses (at least 10000 txs).
  - Linking two wallets that sent to the same deposit address: `shared_deposit` evidence in heuristics.py:26,185-201.
  - Placebo/decoy method: placebo.py:1-70 shifts the search window to before the first real deposit, so every lead found there is chance by construction. The tools/placebo_*.py scripts measure per-family chance rates, and tools/tutela_baseline.py compares against Tutela. The README states that amount/time and gas-price matches occur as often by chance as for real exits, so they never raise a band.
  - Evidence bands (strong needs two independent sources).
- Adds:
  - A tested forwarding-sweep classifier that can replace label-only detection of deposit addresses.
  - The decoy-window idea, which transfers directly to our "empirical comparators" (shift the window, count chance links).
- Requirements and risk: written for Etherscan-style `account` API calls (txlist/tokentx, paged at offset 1000, `_rows` truncation = not a deposit address). We would adapt it to Blockscout or our archived Polygon data. EVM only. Tornado-specific parts are not needed. It is a single maintainer and new, so its false-positive rate on real exchanges is self-reported (docs/EVALUATION.md, not independently verified).

### 4. Ikey168/Noesis, src/kb/onchain_clustering.py. ADOPT-CANDIDATE (re-implement about 60 lines)
- SHA e4ae1319b357d063cb02909fadc9c5ab07b804b9, 2026-11-05. MIT. The repo is a large, unrelated knowledge-base project, so take only this module.
- Capability, rarity of a shared hub under a null (problem 3):
  - Edge score `1/(hub size - 1)` (:255, :306, :353).
  - `_null_model` (:361-410): degree-preserving hub shuffle. Hub sizes and each address's number of memberships are kept, memberships are permuted 200 times, and the expected number of neighbours of the queried address is compared with the observed count (`excess_over_null`).
  - The edge types are common-input, deposit-address reuse, and deployer funding (first inbound value).
  - onchain_calibration.py sweeps the threshold on a labelled fixture.
- Adds: a ready recipe for "how many linked wallets would chance give with this hub structure", which is the baseline that is missing from a shared-funder or shared-exit count.
- Limits:
  - The shuffle treats memberships as exchangeable across addresses, so it does not model one operator running many wallets (the dependence we worry about).
  - The calibration fixture is synthetic and fictional.
  - It works on the repo's internal record store (needs an adapter), stdlib only.
  - 200 permutations with a fixed seed derived from the input is reproducible but coarse.

### 5. pareto-xyz/tutela-app. REFERENCE
- SHA 5a33bfbf4827aec117282eb5cd10a61fe1a8745d, 2022-02-14 (last push 2024-01-22). No LICENSE file.
- src/cluster/deposit.py:183-253 implements Victor Algorithm 1 (merge_asof on block with `t_max` 3200 blocks and `a_max` 0.01 ETH, exchange set, miner and blacklist exclusion). :255-305 gives a linear confidence score. src/tcash/heuristic.py has the unique-gas-price and same-count Tornado heuristics.
- Superseded for our purposes by #3, which re-implements this with a forwarding test and a placebo. Hard-coded amount/time rule, ETH only, no license, pandas `append` (old API). Do not copy.

### 6. debridge-finance/solana-tx-parser-public. REFERENCE
- SHA d30e1f76f1a79230482cb8c28b0e0fdb1fa8075d, 2026-09-10 (release v3.5.0). LGPL-2.1. Halborn pentest PDF is included.
- src/helpers.ts:118-150 `flattenTransactionResponse` orders top-level and inner (CPI) instructions into one call sequence, preserving instruction index. src/decoders/token22.ts plus src/programs/token-extensions/ decode Token-2022 extensions, including transfer-fee instructions that change received amounts.
- Known bug to learn from: issue #37 (open), `parseLogs` ids do not match `flattenTransactionResponse` ids because some programs (for example secp verify) emit no invoke log. This applies to our memo-from-logs decoding.
- TypeScript, LGPL, and an IDL-driven approach. Value is the ordering logic and the Token-2022 fee decoding as a checklist for our decoder.

### 7. andy1245-rgb/PolyCrawler. REFERENCE
- SHA 27ef519bde22fc33f3ba9eee4e58a5339209ee35, 2026-11-04. Apache-2.0.
- discovery/funding.py:216-290: hub (router/sprayer) rejection for funders, counting distinct stablecoin counterparties and treating a full page plus real bytecode as a router. :18 sets `etherscanMaxPages = 10` (the 10000-row window) and :319 loops to it. engine.py:218-243 dedups Polymarket activity by (transactionHash, conditionId, side, timestamp, size, outcome, type).
- Overlaps our funding graph. Needs Etherscan and Alchemy keys. The useful idea is the degree-based hub guard and an explicit 10k-window cap. Copy-trading orientation.

### 8. scottonchain/layerzero_xgboost. REFERENCE
- SHA 0f62a1c012fd86f8021a88ce0515e8fd1d698ddd, 2026-10-10. No license. Reproduces Imig et al. 2025 on 434,786 LayerZero addresses.
- sybil_pipeline.py:11,45 uses a group split by gas-provision tree, so no tree spans train and test (README documents the leakage that a random split causes). Metrics use a corrected resampled t-test with Holm adjustment (README table).
- Lesson only: non-independence handled by grouping on the funding tree. Needs the labelled airdrop data. Not usable as code.

### 9. TrustaLabs/Airdrop-Sybil-Identification, rchen8/hop-airdrop, ArbitrumFoundation/sybil-detection. REFERENCE (Trusta, Hop), REJECT (Arbitrum)
- Trusta SHA fd14ec02cc334ae66ecf6a4a1bc1e0b010c7cd0d, 2023-09-22, GPL-3.0: src/scripts/network_community.py and components_scripts.py implement connected components, Louvain and K-core on a transfer graph and on a "first gas provision" graph. The README describes star, convergence, tree and chain patterns. No null model.
- Hop SHA f88d627a392c69fc903672cee9e8cf576efaece4, 2022-05-23, no license: union_find.py:1-50 is plain union-find over transfers, with blacklist files.
- Arbitrum SHA ceda238929057c2ff40484aaed3eee096e7ed120, 2023-03-22, no license: README only. No code, so it does not count.
- All are threshold heuristics. None estimates how rare a shared funder is. Not new beyond what we have.

### 10. Samy-z/PolyClusters. REFERENCE
- SHA 800cf3dd6732cceca9cddebff10243f256db83c2, 2026-08-06. MIT.
- polyclusters/analysis/cluster.py:68 drops "stopword" bets held by over 25% of users, and :92 applies an IDF weight `log((n+1)/(holders+1))+1`, so a shared obscure position counts more. It is a rarity weight, not a null model. Louvain on top.
- Adds only the idea of IDF-weighting shared markets in a co-betting graph. Qt desktop app.

### 11. ForesightFlow/datasets, ffic-inventory. REFERENCE
- SHA 5ba4127473648a7a278eaa11bd24b82a024181c2, 2026-08-26. CC-BY-4.0 (LICENSE.md).
- ffic-v1.csv: 8 publicly documented Polymarket insider cases mapped to 24 market id prefixes. No wallets. Most rows say `trade_history_available=False`. At most a list of cases for positive-control selection.

### 12. alphalab-research/wash-detector-v3. REJECT
- SHA d2268bd9c97e35ff39708d0439216fc99f90f8f7, 2026-05-27. MIT.
- verifier.py:1-30: pair score with hand-set weights and an ad hoc closed-form threshold `0.70/log10(volume/1000)`. No validation in the repo. Not usable as a detector.

Other rejects after reading: nirholas/crosschain-proof-page (a signing-size UI, no forensics), jayrabol/solana-holder-clusters (shared-funder grouping like ours, MIT, SHA a75a729...; only notable detail is resolving token accounts to owners and reporting a coverage denominator in docs/METHODOLOGY.md), Lightprotocol/instruction-decoder (SHA f325fc2..., no license file, a litesvm test-logging decoder, not a forensic parser), rayperatta/Cluster-Analyzer (single-seed heuristic scores), 0xinsider/research (CC-BY, market-clustered bootstrap and an honest look-ahead correction note, relevant as statistics reference only).

## Empty or weak categories
- Problem 4, privacy pools: nothing code-backed beyond the excluded Privacy-Cash repos. Elusiv has no decoder (code search found nothing). Several hackathon "Solana mixer" repos (catmcgee/solana-mixer-circom, NicoBeCodin/solana_mixer, pyundev/solana-mixer) are new mixers, not analysis tools. No anonymity-set measurement tool for Solana found.
- Problem 5, temporal graph anomaly: only generic ML repos (JakubReha/ProvCTDG on provenance graphs, ritugupta8898-cloud/temporal-fraud-gnn on Elliptic Bitcoin). Nothing applicable to EVM or Solana forensics. Prediction-market insider repos (more than 25 beyond the excluded) are score-and-alert bots with fresh-wallet and size rules.
- Problem 6, evidence reproducibility: no content-addressed raw-archive collector for chain APIs found. Only lessons embedded in #1 (cursor integrity), #2 (log-index dedup) and #7 (10k window cap). Problem 2's label datasets with provenance: brianleect/etherscan-labels (scraped dump, MIT, 2023) and forta-network/labelled-datasets (2023) exist but are scraped or stale; not examined further.

## Search queries used (examples)
Repo searches: sybil airdrop; sybil detection; bridge forensics; cross-chain tracing; deposit address clustering; exchange attribution; address labels dataset; solana parser; solana transaction graph; tornado cash deanonymization; privacy pool solana; anonymity set; temporal graph anomaly; polymarket insider/cluster/suspicious/sybil; wash trading; common funder; etherscan labels; cross-chain bridge dataset; solana mixer; zk privacy solana. Code searches: "deposit address reuse"; orderId fulfillOrder dln; mayan swift; sybil common funder; inner_instructions token_balances owner; light protocol nullifier decode; hot wallet sweep exchange; same funder null model; permutation test funding wallet sybil; first funder gas sybil; transactionIndex dedup signatures.

## Not checked
LI.FI and Across indexers beyond what l2beat/XChainDataGen contain; ton-labels and other non-EVM label sets; the HuggingFace wash-trading dataset; Zenodo XChainDataGen dataset; docs/EVALUATION.md claims of the demixer were read only as headers, not recomputed; no code was executed, so no claim here has been run.
