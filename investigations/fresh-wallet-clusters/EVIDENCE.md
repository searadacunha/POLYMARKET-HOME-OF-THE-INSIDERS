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
