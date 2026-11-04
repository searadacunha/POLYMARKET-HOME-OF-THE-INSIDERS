# Verifiable evidence

Each hop, with chain, asset, decimals, raw amount, source, target, transaction, block, time, service and second source: `sources/data/funding_paths.csv`, `sources/data/cashout_paths.csv`, `sources/data/followups.csv`.

## Main files

| File | SHA-256 | Role |
|---|---|---|
| `sources/reports/FUNDING_FORENSICS_FINAL.md` | 9a1aca0b94ca7623b85a21c656bbe947fed47dc4181fa85d4ff4915a75b1de04 | The 11 case files, summary and matrix |
| `sources/reports/COMMON_FUNDERS.md` | ba59446f608c12767c2e8f0f8fca9e4e841d2bea98b7c2603f3f4ff64c0538cf | Common funders, pairs, control accounts, second wallet |
| `sources/reports/EXCHANGE_AND_PRIVACY_EXPOSURE.md` | 633cb2e7dcbcf81ffcd4e2bcaa839cd50f2394120ad9b6dad28c0e9363cf5bde | Services and XMR |
| `sources/reports/CASHOUT_PATHS.md` | 162eae03dee561d5f9a54fab5d44eb05257ff066cfba142c8d27f0fdf0317142 | Withdrawal destinations |
| `sources/reports/UNKNOWN_PATHS.md` | 61f36b75703046401fbeba6c00a4bb87e4f7b905faf3060f400872c8bb2120d6 | Traceability breaks |
| `sources/data/funding_paths.csv` | 000ba1d6d012415df7c15203124531ede4bf5b300b4bced2106b127d421add0f | Inbound paths, hop by hop |
| `sources/data/cashout_paths.csv` | e2ac8046fbcebbb0dd1827a674c5cd0fc88332225643cbb05a978f675d97fe18 | Outbound paths, hop by hop |
| `sources/data/service_attributions.csv` | df714d4d5c40a909679a334a7d8db36f37691ff982c40a7e78d441a34d1c8ddb | Services touched and attribution level |
| `sources/data/followups.csv` | 3b62b4a4b01c8c29633b3b4262027f8a70810f0d8475db318164e6ce6cc9a745 | Follow-ups after the walk stops, key `0x48ec…` |
| `sources/graphs/funding_network.graphml` | 458ba1db0a276b2ee3cccc120615fdaa91cd43eed3b279b4855e867fc3715db7 | Inflow graph |
| `sources/graphs/cashout_network.graphml` | 51f77559bc2e445e72c3e386d9889771262bf6449a4e5439a614f52f7fc36b51 | Outflow graph |
| `sources/state/pairs.json` | 864c0e0695c5475f02f09647ac6c41cb10b6071ae226696c975e8e615033d609 | The 55 pairs |
| `sources/state/reconcile.json` | 70bc067b04197a688d636abc15058a4c4c0fcc32c8439ce8ea3e2f19fceb9cb0 | Reconciliation of pUSD and positions |
| `sources/state/compare_rates.json` | 95d1d77aefa06762988b35695a911d4ea7a53a6e72b4d580b4e74cd8ca31ce87 | Base rates |
| `sources/state/personal_wallets.json` | c7196d3becb4b27f2e4b7be1a2b496e723313b4d704f8c3a621fa2ebed483637 | Search for other wallets |
| `sources/state/wallet_0xa8e6_activity.json` | 78c95622bc2e2e773b6cf74ea18be7bd6bb6f0a96acb3b5d13104c9a9dda0b4b | Activity of the unnamed wallet, market fields only |
| `sources/state/bsc_0xc852b0938f5ad79b640d105ed11c14499454af26.json` | a205bdc425eea154a172a0560336e54e3b2f588e013bf4abf4df7b11abaa0057 | BSC outflows of the brace227 key |
| `sources/evidence/blockscout_tags.json` | 5b47825b2a3bb5fd501fc043ede047783c7ad6a99094ea93f45449c7958902bd | Service tags |

## The second wallet

| Fact | Chain | Reference |
|---|---|---|
| 2,210.00 USDC, brace227 key to `0x48ec…` | Ethereum, block 26157246 | `0x7e3aecb9b41e6d3f92f25b8760228f15e9b55e798cd27977eb7170445cf64349` |
| 2,960.00 USDC, brace227 key to `0x48ec…` | Ethereum, block 26158556 | `0xb07c3c53a713d98aea1d1bd5d6facf849b6edc675c0fe2cfd3df5b791db20add` |
| Wallet creation by the Polymarket factory | Polygon | `0xa6e229972cef372f1efd5dbb24fe2459c4d279b49d1789a1093f7c1dad215d7b` |
| Owner | Polygon | `eth_call owner()` on `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5` |
| Wallet activity | Data API v2 | `sources/state/wallet_0xa8e6_activity.json`, reduced to market fields |

## The direct transfer

`0xd07bea20a22d9381e0ab364e7a7421776318c6f4aa7258799638472ad7092b98`, Ethereum, block 26119420. Preceding Relay payment: `0xb17e1c4627ad8914f98f48a4fa7f5916953d3286e60cf3d80c6508257f46ce3c`, with the same identifier in the calldata and in the Solana instruction.

## Primary sources

| Source | Use | Access |
|---|---|---|
| Etherscan v2 | Native, internal, ERC-20 on Ethereum, Polygon, Arbitrum | Free key, never written here |
| `explorer.optimism.io` | Optimism history | No key |
| `api.mainnet-beta.solana.com` | Solana history | No key |
| Public EVM nodes | Receipts, `owner()`, balances, nonces | No key |
| `solana-mainnet.gateway.tatum.io` | Second Solana source | No key |
| `bsc-mainnet.gateway.tatum.io`, `56.rpc.thirdweb.com` | Historical nonce on BSC | No key |
| `data-api.polymarket.com/v2/activity` | Activity | No key |
| `api.relay.link/requests/v2` | Cross-chain links. Deprecated, with retirement scheduled for November 24, 2026; recorded responses are in `sources/evidence/relay/`. See [Relay's official documentation](https://docs.relay.link/references/api/get-requests-v2), checked November 4, 2026. | Optional key for v2; its v3 successor requires authentication |
| `dln.debridge.finance`, `iris-api.circle.com`, `api.hyperliquid.xyz/info` | deBridge, CCTP, Hyperliquid | No key |
| `eth.blockscout.com` | Service tags, `metadata.tags`: `sources/evidence/blockscout_tags.json` | No key |
| `brianleect/etherscan-labels`, `dawsbot/eth-labels` | Labels. Not copied: hashes in `sources/evidence/labels/SHA256SUMS` | Public |
| Polymarket, Relay, SWFT, ChangeNOW documents | Mechanisms and coin lists: `sources/evidence/docs/` | Public |

## Second source

`second_source` column of the CSVs, taken from `sources/state/verify.json`: public node for EVM, second RPC for Solana. `node_receipt_log` and `node_tx_value` confirm the transfer itself. `node_receipt_tx_exists` confirms only that the transaction exists and succeeded. This is the case for most protocol hops and mints.

## Checks

- `sources/tests/test_forensics.py`: OuldLm3alem burn, direct transfer, shared funders, double counting, attribution, reconciliation, second wallet, mixers.
- `sources/tests/test_claims.py`: every figure and prefix in the narrative must exist in the data. This check verifies the presence of a value, not that it relates to the right fact.
- `data_manifest.json`: every imported file, with its size and SHA-256.

## Not published here

- `state/http_cache`: raw responses, some of which carry profile fields.
- The copies of third-party label lists: hashes and sources only.
- `evidence/docs/polymarket_trading_wallets-auth.md`: its authentication examples trigger the secrets check. Official page: https://docs.polymarket.com/trading/wallets-auth.md, read on 2026-11-02.
- The displayed name of the second wallet: it is not proof, and an address is enough to verify it.
