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
