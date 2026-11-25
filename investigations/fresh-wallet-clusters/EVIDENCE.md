# Evidence register

Hashes of the files this run published. The cache of raw API pages is local only and is not in git.

| File | SHA-256 | Role |
|---|---|---|
| `preregistration.json` | a1e312d04a02cc4106ce26302696d6702d493dc8cd7299133431e5a47d541f4c | Frozen rules, hashed before the tapes were requested |
| `data/stats.json` | bd32761084da2c3d47637750995f0bd1c853db5e5d3253a1fc77de591acb1290 | Test statistics, coverage and the pipeline check |
| `data/cluster_statistics.csv` | 5964f1e84b43c1047c1f6fccbd03d63d70d3ed8f265c1777e63efbcb466661e2 | The same statistics in a table |
| `data/eligible_wallets.csv` | 4cad4ea364fdbb19e9db34bb0814639c84d89d0f3de460e4ceaa5a296812f6f2 | Wallets that committed at least 1000 USD on one outcome |
| `data/funding_edges.csv` | b1198c398f4196c00ecb4fbc44a536dd54a31152c7f5ae61ae296b3808a86ad2 | Inbound collateral edges and the class of each sender |
| `data/cashout_edges.csv` | e497e52abd485b1c908139bc28cbf63877094593b766ca01f39904529f24f3fc | Withdrawal destinations |
| `data/wallet_clusters.csv` | ba5303ccd3f53b27086d9c0afce8be52fec7c58c0e4023cac1eeafb2a836ca01 | Same-outcome fresh groups and their evidence class |
| `data/matched_controls.csv` | 65382ff9a727fef868115dedc1ee9bef29d6096bf90e96061f86203d2ea7efdb | 24-hour co-timing by volume quintile |
| `data/market_exposures.csv` | 8b95bfb70608f5fe1802e23e7f6aefa97b03608247c0f42dbead2cb44c392112 | Buy, sell and committed capital by wallet and outcome |
| `data/data_coverage.csv` | 27f1d624075586377d5096dfddbbae0269540417fea787c9dd58c248adf45d7e | Catalogue frame and which sampled markets were fetched |
| `figures/test_stratum_rates.svg` | f0083ce0c596005f2280c6356ef2e960c72d00009c816d902ff2090fd4187f6e | Observed clusters against the null means |
| `amendment-002.json` | 53a002ed1f14df48300ea092ec90e686bd15bf724c7a9845564f5159e83c38aa | Rules for the 1 USD tape, fingerprints, longer flows and re-entry, written before those tapes |
| `data/amendment002_stats.json` | 3f81bb2788d5ab04e1f88e0505dda217ebb73fccf1403c9cc4ccb10cd756e40c | Sensitivity counts, fingerprint tests, longer-flow summary |
| `data/amendment002_comparison.csv` | 068deae02657db2bcea1b9a395d3076ff9acdda849e7c1e7656e041a3a0e877b | Parent counts beside the 1 USD-floor counts |
| `data/fingerprints.csv` | 3ee384362da895152ab3dc342a7427d3e109ae6697fd5f72a2017a75a7d797b4 | Four fingerprint frequencies and the Nobel check |
| `data/deep_flows.csv` | 15d2f63abecef13c370002260216c0dbae131c4a2970a8ad23fe40228b0dd9c5 | Plain keys paying two wallets inside the longer lookback |
| `data/reentry.csv` | 90d81b2aff22c20b99dea0fcf1a3ecd29516789a8cc86c047f90b6f55a8d61e7 | Reviewed downstream destinations of the plain keys |
| `evidence/dossiers/amendment002-nobel-downstream.md` | c43a59f8626fdf9900c5a1b405eabf55b6d2c784c8879f3cefc7b262705c4efd | Same-night destinations of the published Nobel key |
| `amendment-003.json` | c3acf36e5df56b69e86417a4ecc065d7601d917f56532a646b9635270bae1f13 | Coverage and receipt rules, written before H4 was scored |
| `data/handoff_receipt_review.csv` | a906410598ccb9963fd981455525fdc705d19aa26b647b4c0f94c0b529b5dc92 | Receipt result for each of the 17 handoff-screen transactions |
| `data/phase3_coverage.csv` | 0cdb6832e56d45c91f4f8df691579925deae017c70753be5d78861ea31342f84 | Page-cap recovery and headline market fetch status |
| `data/phase3_eligible.csv` | 2932504d9bc2354100d4c562a98661fe5a3e9136bd5109d78932970877abf53e | Wallet-outcomes of at least 1000 USD on the phase-3 complete tapes |
| `scripts/fwc/phase3.py` | ee7ca8d5c4ddb7ff2ab87a36ad136cbff65551b391e46f05d58ffe0e2e785ed8 | Recovery collector |
| `scripts/fwc/phase3_fund.py` | 5c3e3583ae59a30130d6b6de4a83023b50e23cb27334ef3a93854e8b93e0611e | Bounded funding trace on the two headline markets |
| `amendment-004.json` | ecc075b0acdbee1a4ffbf5f3cd10226a47c31ec98848e8c5cdd507c00c19be40 | H6 and the 100 USD screen, written before H6 was scored |
| `data/phase4_coverage_summary.json` | e59b1c72938ca5a1770a62fa7672426f3c72cf22989b2961615eed6a591b3077 | Counts for the 25,789-market screen |
| `data/phase4_wallets.csv` | 4f89e122d3ea82c5321c74b022601366b2cf6836f790552cb764dad80e604903 | First activity and first deposit of the 29 wallets |
| `data/phase4_first_payers.csv` | aed8f5c7426dcfe12ff9995a0c4d374beed264a8293f001911f9852be68b2bc0 | First payers grouped across those wallets |
| `data/phase4_windows.csv` | 19a0e1ba08929bdec62a5f81eb5458bf487c13072e24d272ad3ee9cd33f6a5ae | Gap from first activity to the 1,000 USD threshold, and hours before the two posts |
| `data/phase4_chain_hops.csv` | fd87c9b69ff1380ea1842ca1b34b8806e0c04ebaaa8761708c5bc4bc6b17d39a | Distributor chain and the single-wallet funding hops |
| `data/phase4_distributor_flows.csv` | cdf0cec3883664f755aad3c90d87c27f56a8d070248475b7b41b3bbc0d683894 | Stablecoin logs around the two nonce-2 EOAs |
| `data/phase4_distributor_state.csv` | dd4a7fc621ce46dca305a8ee20444567669cffb6bfb69d44f721e69246d06920 | Code length and nonce of the two EOAs |
| `data/phase4_distributor_txfrom.csv` | ffa33f66adda5396ac5afd48b591feb29005329f7fc4fde2d89830af6ff7be58 | Sender of the four published distributor transactions |
| `data/phase4_withdrawals_latest.csv` | 15d395fa7dbc17f8a3dd7e816c8c3149a4e162ee7cf27ecd050fedbed1e7b4a0 | Withdrawals in the newest 200 activity rows |
| `data/phase4_withdrawal_destinations.csv` | 56ebe3b52b1bd37682af9a1cc482ba273d304bd6650dab09cac2ee1a2d547275 | Largest stablecoin destination in those withdrawal receipts |
| `data/phase4_wallet_missing.txt` | 01ba4719c80b6fe911b091a7c05124b64eeece964e09c058ef8f9805daca546b | Prefixes with no activity-wallet match. None were missing |
| `scripts/fwc/census.py` | becadc271cac6c9fe6efb4f566c57af87143e31b50f17f3131a5b6fda799a94e | Newest-first global cursor, stopped after 7.82 days |
| `scripts/fwc/sweep.py` | 6034c38c9a9046d66e31e33c405c3941a98383f3bd31f7b886e251f7896984c3 | Per-market 100 USD screen |
| `scripts/fwc/phase4_wallets.py` | 27679e33f34f259ec61199558c70d12d2ca180e54f2e42798f4881f49a0f3c54 | First-deposit reader for the 29 wallets |
| `scripts/fwc/phase4_hops.py` | a8a5acc076b121da65e92ae786505af4fa0673eac1f3492f33a7aa0850a49622 | Log window behind the two distributors |
