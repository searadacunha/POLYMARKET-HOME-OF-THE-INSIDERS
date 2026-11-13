# Verifiable evidence

Every transaction cited by the findings is listed with its chain, time and amount in the data files below, and can be checked on a public explorer. Raw API responses are not published: `sources/data/raw_response_index.csv` gives their URL, SHA-256 and fetch time.

## Main files

| File | SHA-256 | Role |
|---|---|---|
| `sources/reports/FOLLOWUP_REPORT.md` | 7997bf31a387bd5060ab1de0a1237761fcfb6cd163f42bdd7d526102f42d3c99 | Full report: tables, method, verification, limits |
| `sources/data/nobel_accounts.csv` | ed5f23b23af05003fa1b7d60d13a5b95d1d63b076cbe24101ec07192d9a1d440 | The eight accounts: proxy, Safe owner, profile creation, first funding, first Machado buy |
| `sources/data/nobel_funding_transfers.csv` | f0ab02ce7ffd7b0ce009171adce843feff4fc401da61c6bab6cfbb518751fea7 | The 14 funding transfers (Polygon USDC) |
| `sources/data/nobel_relay_withdrawals.csv` | 538fc84693334eba750d3cad317b7450292db69678e0531fecc0e3624a05bc5c | The 16 Relay withdrawals and their recipients |
| `sources/data/funder_polygon_flows.csv` | 68b88e824f9abd34096c4ec99f35eba44ed4e50c816bb72d9b48378e920c13e0 | All Polygon USDC and POL flows of the funder |
| `sources/data/funder_and_source_ethereum_flows.csv` | e03a669f358b458922dd61de49e4ffa8721ef7a86163d076dbe6b6d2a85c4629 | Ethereum flows of the funder and of its source |
| `sources/data/funder_upstream_downstream.json` | fb5001c90c47ab58f0e0ec4e0ab98912adf0c3342fff320071efa3a7a8ac55c8 | Across fill of the capital and exits |
| `sources/data/machado_yes_price_history.json` | d67ed1b7258ab80ff6697fbfc1d98d6e616118367e87ec25ba1a219d2e187942 | CLOB price history of the Machado Yes token |
| `sources/data/owner_keys_activity.csv` | bc4dfeef922ba4e283bf0b31505f1717d802ac8dd7672fcef3ba053bfd38e202 | On-chain activity of the seven other Safe owner keys |
| `sources/data/ballon_l2_summary.json` | 58600fd03194cd6e579658ec545d41830f72fa5480d09b1b8f631acf49712dc5 | Ballon d'Or: counts on Base, Arbitrum, Optimism |
| `sources/data/ballon_l2_coverage.csv` | d157c163c0bcb32ccbbf15d814c490146914048288a21017f2c214c18091b5ca | Ballon d'Or: per-address coverage, truncation flags |
| `sources/data/ballon_l2_edges.csv` | 585d0ea6d93954591f5fd479772abdc59aabbbd77b8e88d77f46594cd6aaaa8d | Ballon d'Or: the 24 kept edges |
| `sources/data/ballon_changenow_roundtrip.csv` | 2f91398c8b2e8ab7cd5ff92a41261f4f9bc61f4eec4ccd75698f6cadea76184b | ChangeNOW round trip of 0x3eaef6d5 |
| `sources/data/raw_response_index.csv` | 369f49fd666d0523013529a34cd456339a70b86d672d8bf40ee31662dab9e069 | Provenance of the raw API responses |
| `sources/tools/pm_nobel_c7.py` | 41cb82b9da11ab709595b02c3c2cfad69300c409809c1e40bec24af64fbf8486 | Collector: inbound and outbound transfers of the C7 proxies |
| `sources/tools/pm_nobel_financeur.py` | 45869815444ce62f867704b903fceed1869f096fa742cf6b0e86079635c70ef7 | Collector: full history of the funder |
| `sources/tools/pm_nobel_comptes.py` | 88c7dcc9e9af12c1e8446a815e589446ef8e291b8ba0e8dbe8ff361211bc1195 | Collector: profiles, trades and Relay withdrawals of the funded accounts |
| `sources/tools/pm_nobel_amont_aval.py` | bd4fe69ef568be1bd36b4e6d2b50663ef3a2746cddd38fe562e6a08da5f49cec | Collector: capital source and exits |
| `sources/tools/pm_ballon_l2.py` | 3aa8b0dca05e3b093a6688941096640f72027acd1691037a9e164837a46ef0fe | Collector: Ballon d'Or keys on Base, Arbitrum, Optimism |
| `sources/tools/onchain.py` | f241688ebedf98c6d1d7406999f3c19b4c7bb4501b5b4d7cca8930ee7d3ae2fa | Shared HTTP and RPC helper (archives responses, no key printed) |
