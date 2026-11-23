# Evidence register

Every result below is rebuilt by the scripts of this folder. Raw logs, source caches and agent working files stay on the original machine; `data_manifest.json` and `local_only_hashes.sha256.gz` give their sizes and SHA-256.

| File | SHA-256 | Role |
|---|---|---|
| `results/REPORT.md` | 2cc6bb265c00a12b4b6a20df747cb83bd45e191a129f32ab39eb0e40d27646c8 | Human-readable results, generated from the files below |
| `results/ledger_results.json` | 2f24de8e492a6ec79033d0c6918ac6078c464e2bfc861a1a7391a61ce9a25b52 | Cohort ledger totals, denominators, stream coverage and check counts |
| `results/wallet_summary.csv` | c57f9b113b9853f370a816e10e8497751ab0cc68e16a5d543666e3c5613732b4 | One row per cohort trading address: fills, markets, PnL status, reconciliation, Data API control |
| `results/wallet_position_summary.csv.gz` | d01b011e4bd373bb41a82c7d07304ee8fe24622ec024bffd5604dabcd7b9f6ea | One row per account and market: trades, fees, inventory, valuation, PnL, identity check, flags |
| `results/wallet_fills.parquet` | fbdeda038c22a000d4a8f982631a4540c38f5e86f91abf84ac7e8b1a41a6ed07 | Canonical trade ledger: every OrderFilled owned by a cohort account |
| `results/wallet_position_ledger.parquet` | c2ea57d63bbb7754b8f32cebff06eb108c58292d024c77e74e966b3df73fc2c1 | Position ledger: every account, transaction and outcome-token leg with its collateral share |
| `results/coverage_by_contract.csv` | 579b241f48c8b26ad9158aa96a7b1ad957645e19efe997be862a3970116345bd | Logs per emitter, month and event family |
| `results/coverage_by_market.csv.gz` | ed2585c4b30b6ea472f94116a96197a1e2010ab592f1af00b6400d1feaf2c10f | Per market: accounts, fills, on-chain resolution, Gamma outcome prices |
| `results/coverage_by_chain.csv` | 4898da8543cec2e45e1202c192551c0132d2c00a9fd3683eaafa1624e2eb4bbc | Datasets per chain with their coverage status |
| `results/reconciliation_failures.csv` | 05e47698a83de2b87e2255d0e0b383d3e1dd4397566e8224826248f24d997f63 | Every failed reconciliation check with its reason |
| `results/regression_pr111.json` | b3de423264f959fa44d75d5e8d95cfb19b165e555ed79c838b0f7d0ef5063d4f | Market-by-market comparison with PR 111's published results |
| `results/data_gap_matrix.csv` | 0362081021c5b3e2c625310d854e9ace5e238f52359b4fa6be31e2c1e1432f21 | Dataset-level gap matrix |
| `results/data_gap_matrix.json` | 7b883016410b9f5821cccc7827fc336ae053ad730e92795ea7e58a103c5c18a3 | Same matrix, machine-readable |
| `results/file_inventory.csv.gz` | 45229aecbe4546fcfd3e5e9fd5a33793cd56003aa20f007182e499ace73d2865 | File-level audit of every investigation manifest |
| `results/file_inventory_summary.json` | 7e2a5cabaa8038d753c6a8c5d2db190c575ebcabfb67eae9eab31e23e5071f26 | Counts of the file-level audit |
| `results/weekly_service_funding.csv` | 560f5a73400af76a1a29e610f43daf43140f170529838186cca23cce5cbcf0cf | PR 110 weekly sets in the requested columns |
| `results/weekly_service_funding_union.json` | 61724a914f8e93f0df44a30a426908a55d4e6c798076bf4ad42ec1b2c8d64d47 | All-period distinct wallets as set unions |
| `results/eth_weeks_coverage.csv` | 2f2be6eda57c65057ca2e5cdc1360df87dbd0cababc9756027607a724caf7368 | Ethereum source streams recovered for 2026-W16 to W38 |
| `results/eth_downstream_linking.json` | 07f82770ac50d5485655e7e89d4fce4c27e47eee342489e5f76256fb353131f8 | Keyless downstream linking methods tested on a sample |
| `results/relay_v2_screen.csv` | 93c77d9bb748cca4ef3df32d9eadc5561db43fea4b91d088fb4870f6ef577e09 | Relay v2 history status of each of PR 110's Ethereum recipients |
| `results/relay_v2_screen.json` | 14980214b6914cbde976374bec2fedda18989205e59027225811b5df466f5fd5 | Relay v2 screen summary |
| `results/archived_vs_chain.json` | 7a213a12ec9618d39011497edbbba6acbef1c0f0819c63ac2ee9861484066369 | Archived Data API PnL against the on-chain ledger, capped and uncapped records |
| `results/provider_sample.json` | 3d77f761b5a486685f422e89346dd96c0c5fda3911cdb76560296f8a98398a86 | Second-provider comparison of a deterministic sample of receipts |
| `results/relay_v2_orders.csv` | 81c85fe881acf8ea760bdd8bc1a864ac386d12cc7859728a2795397d6e29da37 | Every Relay order found, with its date against PR 110's screened weeks |
| `results/cross_chain_routes.csv` | 712c7d0473af42a9bfef5ee8137097544654f54980782ccbde1aa668e46e5f74 | PR 109 Arbitrum passages, leg by leg, with provider agreement |
| `results/cross_chain_provider_comparison.json` | 57ad9ac8c557b8b04da9fda8861e89047974dc5afa2622692e63ed6660530863 | Field-level provider comparison |
| `results/cross_chain_passages.json` | 2fd8e07342ef9b351c133b2a5faf527355cf91583447e5a5a33dd2c526030e2f | Relay request identifiers and balances of each passage |
| `results/prospective_data_quality.csv` | ac639033b9c43dfd01f7c85a9617554233075de7a57feaafbb98943ee4710690 | Availability of prospective evaluation data |
| `results/leakage_and_comparison.json` | 05abd11d86894988d4f9cfb71ab223b7640f6b8ec39812e5ddeb3a55f64685ab | Residual leakage paths and comparison checklist for the PR 109 evaluator |
| `results/contract_semantics.json` | 73642179f3d40b8dd6c0444f6a44df780a90ccd4e582e5da0f2e0f854ca22535 | Exchange lifetimes, event signatures, fee rules, taker semantics, positions and collateral |
| `results/source_probes.json` | 5041050c70b356b2b97d801b32e4d1b90a1cf23c0286fb7272b078efbead0779 | Measured limits of public data sources |
| `results/recovery_attempts.jsonl` | e32faa55e8865697938013eccb0b28223149df75dd33055ed5e48e8d740aacb0 | Every recovery attempt and its outcome |
| `results/tests_run.json` | b9cdfe4d7ff0aead95ee9f7cb7fb9ebf61568bddaefcec6578429b2670725853 | Test suites executed and their results |
