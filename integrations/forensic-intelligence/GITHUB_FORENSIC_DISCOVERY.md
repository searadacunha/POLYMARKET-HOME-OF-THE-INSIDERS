# GitHub forensic discovery — scoped evidence ledger

**Snapshot:** 2026-11-02. **Branch:** `research/forensic-intelligence-20261102`. This is a staged investigation, NOT a claim of exhaustive code audits or installation. GitHub REST metadata is fetched for each candidate individually. `Push` is the repository's last push date, NOT independently verified last commit; a head SHA must be pinned before any adoption. `NOASSERTION` and `UNDECLARED` mean the license must be examined manually. No third-party code is executed by this scan.

**Verification legend:** `EXISTS` means GitHub API replied to a repository lookup; `NOT_FOUND` means the lookup failed (may include access or renaming). All rows are **metadata screened**. Selected code paths are reviewed separately below; code review is not implied by a row's presence.

## Candidate inventory

| Repository | Verified | Push UTC | License metadata | Archived | Language | Repository size KB |
|---|---|---|---|---|---|---:|
| [Polymarket/py-sdk](https://github.com/Polymarket/py-sdk) | EXISTS | 2026-11-02 | MIT | NO | Python | 3137 |
| [Polymarket/agent-skills](https://github.com/Polymarket/agent-skills) | EXISTS | 2026-02-19 | UNDECLARED | NO | ? | 25 |
| [Polymarket/ctf-exchange-v2](https://github.com/Polymarket/ctf-exchange-v2) | EXISTS | 2026-10-28 | NOASSERTION | NO | Solidity | 1889 |
| [Polymarket/polymarket-subgraph](https://github.com/Polymarket/polymarket-subgraph) | EXISTS | 2026-02-13 | LGPL-3.0 | NO | TypeScript | 1613 |
| [warproxxx/poly_data](https://github.com/warproxxx/poly_data) | EXISTS | 2026-09-08 | GPL-3.0 | NO | Python | 4585 |
| [moose-code/polymarket-indexer](https://github.com/moose-code/polymarket-indexer) | EXISTS | 2026-07-14 | UNDECLARED | NO | TypeScript | 452 |
| [YoppaV/polymarket-mcp](https://github.com/YoppaV/polymarket-mcp) | EXISTS | 2026-05-20 | MIT | NO | Python | 86 |
| [vsbtc/polymarket-insider-detection](https://github.com/vsbtc/polymarket-insider-detection) | EXISTS | 2026-07-16 | MIT | NO | Python | 19441 |
| [pselamy/polymarket-insider-tracker](https://github.com/pselamy/polymarket-insider-tracker) | EXISTS | 2026-11-01 | MIT | NO | Python | 4312 |
| [zhangmatt/connections](https://github.com/zhangmatt/connections) | EXISTS | 2026-07-12 | UNDECLARED | NO | Python | 16 |
| [tetratensor/polymarket-wallet-analyzer](https://github.com/tetratensor/polymarket-wallet-analyzer) | EXISTS | 2026-07-09 | UNDECLARED | NO | JavaScript | 46 |
| [enviodev/hypersync-client-python](https://github.com/enviodev/hypersync-client-python) | EXISTS | 2026-10-30 | MPL-2.0 | NO | Rust | 454 |
| [blockchain-etl/ethereum-etl](https://github.com/blockchain-etl/ethereum-etl) | EXISTS | 2026-01-25 | MIT | NO | Python | 1893 |
| [blockscout/blockscout](https://github.com/blockscout/blockscout) | EXISTS | 2026-11-02 | NOASSERTION | NO | Elixir | 209276 |
| [gl0bal01/chainmap](https://github.com/gl0bal01/chainmap) | EXISTS | 2026-07-13 | MIT | NO | JavaScript | 1647 |
| [graphsense/graphsense-lib](https://github.com/graphsense/graphsense-lib) | EXISTS | 2026-11-02 | MIT | NO | Python | 44733 |
| [graphsense/graphsense-tagpacks](https://github.com/graphsense/graphsense-tagpacks) | EXISTS | 2026-11-02 | MIT | NO | Python | 16869 |
| [prettydeath/wallet-attribution](https://github.com/prettydeath/wallet-attribution) | EXISTS | 2026-10-01 | NOASSERTION | NO | Python | 137388 |
| [relayprotocol/relay-kit](https://github.com/relayprotocol/relay-kit) | EXISTS | 2026-10-29 | MIT | NO | TypeScript | 15430 |
| [circlefin/evm-cctp-contracts](https://github.com/circlefin/evm-cctp-contracts) | EXISTS | 2026-06-18 | Apache-2.0 | NO | Solidity | 1911 |
| [across-protocol/skills](https://github.com/across-protocol/skills) | EXISTS | 2026-02-27 | UNDECLARED | NO | ? | 25 |
| [networkx/networkx](https://github.com/networkx/networkx) | EXISTS | 2026-11-01 | NOASSERTION | NO | Python | 98443 |
| [neo4j/graph-data-science](https://github.com/neo4j/graph-data-science) | EXISTS | 2026-10-23 | NOASSERTION | NO | Java | 106693 |
| [duckdb/duckdb](https://github.com/duckdb/duckdb) | EXISTS | 2026-11-02 | MIT | NO | C++ | 570594 |
| [pola-rs/polars](https://github.com/pola-rs/polars) | EXISTS | 2026-11-02 | MIT | NO | Rust | 237082 |
| [deepcharles/ruptures](https://github.com/deepcharles/ruptures) | EXISTS | 2026-10-06 | BSD-2-Clause | NO | Python | 11447 |
| [Polymarket/polymarket-v2-external](https://github.com/Polymarket/polymarket-v2-external) | EXISTS | 2026-10-29 | NOASSERTION | NO | Solidity | 10067 |
| [Polymarket/py-clob-client](https://github.com/Polymarket/py-clob-client) | EXISTS | 2026-05-25 | MIT | YES | Python | 286 |
| [psyberck/polymarket-subgraph-v2](https://github.com/psyberck/polymarket-subgraph-v2) | EXISTS | 2026-11-02 | MIT | NO | TypeScript | 372 |
| [polyflux-io/polymarket-onchain-trades](https://github.com/polyflux-io/polymarket-onchain-trades) | EXISTS | 2026-10-29 | MIT | NO | Python | 65 |
| [x-pertknight/polymarket-insider-detection](https://github.com/x-pertknight/polymarket-insider-detection) | EXISTS | 2026-07-09 | UNDECLARED | NO | Python | 156 |
| [jsinyavsky/polymarket_anomaly_detection](https://github.com/jsinyavsky/polymarket_anomaly_detection) | EXISTS | 2026-05-13 | UNDECLARED | NO | Python | 14827 |
| [muzilicheng/polymarket-historical-market-data](https://github.com/muzilicheng/polymarket-historical-market-data) | EXISTS | 2026-08-09 | NOASSERTION | NO | ? | 807 |
| [PaulieB14/polymarket-v2-subgraphs](https://github.com/PaulieB14/polymarket-v2-subgraphs) | EXISTS | 2026-10-10 | UNDECLARED | NO | TypeScript | 202 |
| [caiovicentino/polymarket-mcp-server](https://github.com/caiovicentino/polymarket-mcp-server) | EXISTS | 2026-09-20 | MIT | NO | Python | 1573 |
| [berlinbra/polymarket-mcp](https://github.com/berlinbra/polymarket-mcp) | EXISTS | 2025-06-06 | MIT | NO | Python | 115 |
| [BrainDAO/mcp-polymarket](https://github.com/BrainDAO/mcp-polymarket) | EXISTS | 2026-08-10 | MIT | NO | TypeScript | 461 |
| [suislanchez/polymarket-insider-detector](https://github.com/suislanchez/polymarket-insider-detector) | EXISTS | 2026-02-09 | UNDECLARED | NO | JavaScript | 85 |
| [Rebadged/polymarket-alpha](https://github.com/Rebadged/polymarket-alpha) | EXISTS | 2026-11-02 | UNDECLARED | NO | Python | 6455 |
| [FuckFiat/polymarket-whale-tracker](https://github.com/FuckFiat/polymarket-whale-tracker) | EXISTS | 2026-06-14 | UNDECLARED | NO | Python | 6784 |
| [Schmidters/collectmarkets](https://github.com/Schmidters/collectmarkets) | EXISTS | 2026-01-06 | MIT | NO | Python | 10923 |
| [bensaru/polymarket-analyzer](https://github.com/bensaru/polymarket-analyzer) | EXISTS | 2026-03-23 | MIT | NO | HTML | 27 |
| [troyfol/Blockchain_Investigation_Hub](https://github.com/troyfol/Blockchain_Investigation_Hub) | EXISTS | 2026-07-06 | GPL-3.0 | NO | Python | 17615 |
| [rohteemie/Open-Source-Blockchain-Forensics](https://github.com/rohteemie/Open-Source-Blockchain-Forensics) | EXISTS | 2026-05-05 | MIT | NO | Python | 77 |
| [metaver5o/Blockchain-Forensic-Toolkit](https://github.com/metaver5o/Blockchain-Forensic-Toolkit) | EXISTS | 2025-05-23 | MIT | NO | ? | 2 |
| [agentic-reserve/solana-forensic-intelligence](https://github.com/agentic-reserve/solana-forensic-intelligence) | EXISTS | 2026-02-16 | MIT | NO | TypeScript | 1068 |
| [rled7/sybil-detection-engine](https://github.com/rled7/sybil-detection-engine) | EXISTS | 2026-06-01 | UNDECLARED | NO | TypeScript | 40 |
| [mikemarshall01/sybil-detect](https://github.com/mikemarshall01/sybil-detect) | EXISTS | 2026-06-17 | MIT | NO | Jupyter Notebook | 11058 |
| [MNEMONIMO/onchain-sybil-detector](https://github.com/MNEMONIMO/onchain-sybil-detector) | EXISTS | 2026-10-28 | UNDECLARED | NO | ? | 0 |
| [yungcortex/onchain-intel](https://github.com/yungcortex/onchain-intel) | EXISTS | 2026-03-26 | UNDECLARED | NO | JavaScript | 696 |
| [saisanthosh245/Real-Time-Crypto-Fraud-Attribution-System](https://github.com/saisanthosh245/Real-Time-Crypto-Fraud-Attribution-System) | EXISTS | 2026-09-18 | UNDECLARED | NO | ? | 0 |
| [NachoCanabal/wallet-attribution](https://github.com/NachoCanabal/wallet-attribution) | EXISTS | 2026-10-01 | NOASSERTION | NO | ? | 137388 |
| [Clifford-Swartz/provenance](https://github.com/Clifford-Swartz/provenance) | EXISTS | 2026-09-30 | UNDECLARED | NO | TypeScript | 3601 |
| [subsquid/squid-sdk](https://github.com/subsquid/squid-sdk) | EXISTS | 2026-11-02 | Apache-2.0 | NO | TypeScript | 22105 |
| [subsquid/squid-cli](https://github.com/subsquid/squid-cli) | EXISTS | 2026-06-16 | UNDECLARED | NO | TypeScript | 1045 |
| [subsquid-labs/squid-evm-template](https://github.com/subsquid-labs/squid-evm-template) | EXISTS | 2026-07-27 | MIT | NO | TypeScript | 1267 |
| [HemeraProtocol/hemera-indexer](https://github.com/HemeraProtocol/hemera-indexer) | EXISTS | 2025-10-22 | Apache-2.0 | NO | Python | 5890 |
| [0xaaiden/smoldata](https://github.com/0xaaiden/smoldata) | EXISTS | 2023-07-01 | UNDECLARED | NO | JavaScript | 2894 |
| [osslabz/evm-abi-decoder](https://github.com/osslabz/evm-abi-decoder) | EXISTS | 2026-11-02 | GPL-3.0 | NO | Java | 647 |
| [ChainPrimitives/eth-event-decoder](https://github.com/ChainPrimitives/eth-event-decoder) | EXISTS | 2026-03-21 | MIT | NO | TypeScript | 47 |
| [ethereum/web3.py](https://github.com/ethereum/web3.py) | EXISTS | — | UNDECLARED | ? | ? | — |
| [ethereum/eth-abi](https://github.com/ethereum/eth-abi) | EXISTS | — | UNDECLARED | ? | ? | — |
| [ethereum/eth-account](https://github.com/ethereum/eth-account) | EXISTS | — | UNDECLARED | ? | ? | — |
| [safe-global/safe-eth-py](https://github.com/safe-global/safe-eth-py) | EXISTS | 2026-11-02 | MIT | NO | Python | 7731 |
| [safe-global/safe-core-sdk](https://github.com/safe-global/safe-core-sdk) | EXISTS | 2026-11-02 | MIT | NO | TypeScript | 9158 |
| [gnosis/conditional-tokens-contracts](https://github.com/gnosis/conditional-tokens-contracts) | EXISTS | 2023-01-24 | LGPL-3.0 | NO | Solidity | 7240 |
| [duneanalytics/spellbook](https://github.com/duneanalytics/spellbook) | EXISTS | 2026-11-02 | NOASSERTION | NO | Python | 455677 |
| [streamingfast/substreams](https://github.com/streamingfast/substreams) | EXISTS | 2026-11-02 | Apache-2.0 | NO | Go | 81201 |
| [streamingfast/firehose-ethereum](https://github.com/streamingfast/firehose-ethereum) | EXISTS | 2026-10-30 | Apache-2.0 | NO | Go | 27123 |
| [TrueBlocks/trueblocks-core](https://github.com/TrueBlocks/trueblocks-core) | EXISTS | 2026-10-13 | GPL-3.0 | NO | Shell | 682508 |
| [blockchain-etl/awesome-blockchain-data](https://github.com/blockchain-etl/awesome-blockchain-data) | NOT_FOUND | — | — | ? | — | — |
| [tenderly/ethers](https://github.com/tenderly/ethers) | NOT_FOUND | — | — | ? | — | — |
| [0xPolygon/polygon-edge](https://github.com/0xPolygon/polygon-edge) | EXISTS | 2024-08-27 | Apache-2.0 | YES | Go | 159762 |
| [PaulieB14/graph-polymarket-mcp](https://github.com/PaulieB14/graph-polymarket-mcp) | EXISTS | 2026-10-15 | MIT | NO | TypeScript | 241 |
| [Polymarket/py-clob-client-v2](https://github.com/Polymarket/py-clob-client-v2) | EXISTS | 2026-10-27 | MIT | NO | Python | 211 |


## Shortlist: code-level inspection and decisions

For the following repositories, README plus implementation/configuration/test files were actually opened. A GitHub tree test-file count means **files**, not executed passing tests. **No external package was installed or executed on the user's Mac.** Commit hashes pin the read version, although no packaged release is assumed.

| Repository / inspected commit | Implemented capability (code, not just marketing) | Tests/compatibility/cost/risk | Decision |
|---|---|---|---|
| [Polymarket/py-sdk](https://github.com/Polymarket/py-sdk) `aa94ec431e3d` | PublicClient / AsyncPublicClient and typed 2026 public market interfaces; optional Arrow/Polars integration; code uses Python package `polymarket-client` 0.16.0 | Python >=3.11, MIT, 208 tree paths matching test patterns (not executions). Library includes authenticated/trading methods: **only PublicClient** may be used. Historical coverage and pagination must be measured per endpoint. | **ADAPT** public read-only adapter after test on local fixture; no authenticated client. |
| [Polymarket/ctf-exchange-v2](https://github.com/Polymarket/ctf-exchange-v2) `ccc0596074f4` | Solidity Exchange V2, explicit side/tokenId and signed fields, collateral on/off ramps, adapter and tests | **BSL 1.1, non-production use only, license changes in March 2030**. Foundry/Solidity, not a Python data collector. | **REFERENCE ONLY** for exact ABI and deployment version; do not vendor code. |
| [Polymarket/polymarket-v2-external](https://github.com/Polymarket/polymarket-v2-external) `741f8bbe88c3` | Further protocol V2 PositionManager, new position-ID encoding, routers and exchange code | **BSL 1.1 non-production**, distinct interfaces and deployed contracts. Do not equate this protocol with the earlier CLOB V2 cutover without block-height evidence. | **REFERENCE ONLY**, build versioned contract registry. |
| [moose-code/polymarket-indexer](https://github.com/moose-code/polymarket-indexer) `c287da43d48d` | Envio handlers for V1 Exchange and V2 `OrderFilled`/`OrdersMatched`, raw integer fills, transaction/log index keys, user positions, metadata retry | No license file found, 26 test-like paths. Needs HyperIndex and network services. V2 handler asserts V1/V2 token IDs are interchangeable: **verify by contract era**, especially against newer protocol V2. | **REFERENCE / BLOCKED LICENSE**, use design for an independent ETL adapter, not source copy. |
| [enviodev/hypersync-client-python](https://github.com/enviodev/hypersync-client-python) `6c3e89f494ea` | Rust/PyO3 `HypersyncClient`, filtered transactions, blocks, logs, traces, streaming and Parquet exports | MPL-2.0, API token and rate limits/paid tier, Python >=3.9. No entitlement or network timing benchmark here. Compare costs before using on Mac; use bounded block ranges. | **PILOT CANDIDATE** for BSC/Base and complete history only if service can actually return the chain/trace data. |
| [pselamy/polymarket-insider-tracker](https://github.com/pselamy/polymarket-insider-tracker) `9d370e6521b0` | Wallet poller, on-chain profiling, ML/heuristic scoring, notifications, migrations and extensive tests | MIT, Python >=3.11,<3.14, Redis/Postgres/Docker stack, 212 test-like tree paths. Depends on `py-clob-client` and needs API compatibility review for 2026; macOS arm64 is described as supported but not tested here. | **REFERENCE**, no deployment or score replacement; evaluate against frozen PolySentinel replay. |
| [YoppaV/polymarket-mcp](https://github.com/YoppaV/polymarket-mcp) `3b4f63242ee9` | Read-only HTTP/SQLite research endpoints including cross-wallet correlation | MIT, Python >=3.10, httpx/MCP/aiosqlite; 24 test-like paths. MCP server is executable code and should never receive Mac secrets by default. | **REFERENCE / ISOLATED PILOT**, lightweight techniques may be useful. |
| [vsbtc/polymarket-insider-detection](https://github.com/vsbtc/polymarket-insider-detection) `b2e0fe46f9b5` | Price reveal-jump detection, retrospective wallet calibration, Etherscan funding ring scripts | MIT, Python, **no automated test files identified**, Etherscan API and Claude classifier required. Selects post-resolution winners/reveals, so it cannot directly measure real prospective detection. Reported validation is not independently reproduced here. | **REFERENCE FOR ADVERSARIAL TESTS**, reject its historical winners as a prospective signal. |
| [warproxxx/poly_data](https://github.com/warproxxx/poly_data) `136e129735c7` | Batch Polymarket ingestion, hypersync and dataframe tooling; code and pyproject indicate pandas/polars/hypersync | GitHub license metadata reports **GPL-3.0** while `pyproject.toml` says **MIT**: material licensing discrepancy. Python >=3.9; no live performance verified. | **BLOCK DIRECT INTEGRATION UNTIL LICENSE CLARIFIED**; study pipeline concepts only. |
| [gl0bal01/chainmap](https://github.com/gl0bal01/chainmap) `4b2e8ab1e1e9` | Client-side EVM graph, native/internal/token transfers, Etherscan V2, edges, cycle and peel-chain visualizations, CSV export | MIT, JavaScript browser runtime, finite API/query caps, sampled graph. No reason to copy/host its whole UI; sample cannot establish full-chain absence. | **OPTIONAL GRAPH VISUALIZATION REFERENCE**; produce GraphML/JSON first. |
| [relayprotocol/relay-kit](https://github.com/relayprotocol/relay-kit) `f66fb04e940e` | Cross-chain quote/route interaction and Relay client library | MIT, TS and network; route estimates alone are not a historical transaction identifier or proof of same owner. | **REFERENCE** for order identifiers, use actual receipts/records only. |
| [graphsense/graphsense-tagpacks](https://github.com/graphsense/graphsense-tagpacks) `4015092528e2` | Reusable label/tag packs; can enrich service attribution with provenance | MIT. Label provenance and independence are not established by the tag alone; untrusted CSVs should be sampled and scanned before import. | **LABEL REFERENCE ONLY**, never identity evidence. |
| [graphsense/graphsense-lib](https://github.com/graphsense/graphsense-lib) | Python APIs, models and bulk blockchain analytics tools | MIT; sizeable backend ecosystem, not required to test the present graph hypothesis. | **DEFER FULL DEPLOYMENT**. |
| [circlefin/evm-cctp-contracts](https://github.com/circlefin/evm-cctp-contracts) | Official CCTP contracts and message schema | Apache-2.0; proof requires actual MessageSent/Received identifiers on both chains, not matching amounts. | **PROTOCOL REFERENCE**. |
| [duckdb/duckdb](https://github.com/duckdb/duckdb), [pola-rs/polars](https://github.com/pola-rs/polars), [networkx/networkx](https://github.com/networkx/networkx), [deepcharles/ruptures](https://github.com/deepcharles/ruptures) | Columnar queries, lazy streaming, graph algorithms, change point tests | Optional local libraries. DuckDB/Polars MIT and ruptures BSD-2 per metadata; networkx metadata requires manual license-file review. Memory and Apple Silicon performance remain unmeasured. | **OPTIONAL AFTER STDLIB BASELINE**, no heavyweight graph DB. |

### Other mandatory candidates

- [Polymarket/agent-skills](https://github.com/Polymarket/agent-skills) and [across-protocol/skills](https://github.com/across-protocol/skills): agent instruction sets, not historical forensic evidence engines. No license declared via API; **do not execute untrusted instructions**.
- [Polymarket/polymarket-subgraph](https://github.com/Polymarket/polymarket-subgraph): legacy The Graph manifests; its README explicitly targets CTF/FPMM and local Graph Node, with M1 Docker image caveat. **Do not assume 2026 V2 completeness**. LGPL-3.0 per API.
- [blockchain-etl/ethereum-etl](https://github.com/blockchain-etl/ethereum-etl): MIT Python ETL, useful reference for ERC-20 and trace exports; bulk index cost and range completeness not verified.
- [blockscout/blockscout](https://github.com/blockscout/blockscout): complete explorer backend in Elixir; substantial infrastructure, metadata license NOASSERTION. **Not an appropriate first pilot**.
- [prettydeath/wallet-attribution](https://github.com/prettydeath/wallet-attribution): large label set; metadata license NOASSERTION. Dataset provenance and conflicting labels must be audited before use.
- [zhangmatt/connections](https://github.com/zhangmatt/connections), [tetratensor/polymarket-wallet-analyzer](https://github.com/tetratensor/polymarket-wallet-analyzer): small/no declared license; no compelling demonstrated improvement over existing funding and behavioural modules.
- [neo4j/graph-data-science](https://github.com/neo4j/graph-data-science): nontrivial Java/server footprint, licensing not assumed; defer unless NetworkX/stdlib demonstrably fails.

### Security and evaluation gates

1. No imported third-party code in this first pass. The selected commits are **inspected**, not executed.
2. API keys, if required later, must be restricted, provided outside the repository, and used only after permission and cost check.
3. Do not infer `code is maintained` from recent pushes alone. Release continuity, issue response and fork review are **not yet exhaustively audited**.
4. A GitHub tag, a source label and a service description do not identify a beneficial owner.
5. Code artifacts above are not used to rewrite any historical PolySentinel decisions or probabilities.
6. Additional candidate rows are **discovery leads**, not validated superior algorithms.

### Source references

- Official contract interface: `Polymarket/ctf-exchange-v2/src/exchange/` and `Polymarket/polymarket-v2-external/src/exchange/Exchange.sol`, at the pinned commits above.
- Existing case baseline and negative controls: `../../METHODOLOGY.md`, `../../MASTER_REPORT.md`, `../../investigations/changenow-proof/FINDINGS.md`, `../../investigations/polysentinel/FINDINGS.md`.
