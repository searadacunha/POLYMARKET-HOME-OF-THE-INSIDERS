# Preregistration

The rules in [preregistration.json](preregistration.json) were written before any trade tape for this study was requested. SHA-256 of that file:

`a1e312d04a02cc4106ce26302696d6702d493dc8cd7299133431e5a47d541f4c`

The collector stores the same hash on its first run and stops if the file changes afterwards. Discovery, validation and the test stratum are fixed calendar cuts. The test stratum is not a replacement for an underpowered validation, and validation is not a replacement for the test.

## What is confirmatory

Three tests, Bonferroni threshold 0.05 / 3.

1. **H1.** On information markets in the test window, the number of same-outcome groups of at least two qualifying fresh wallets, each with at least $1,000 of capital committed and threshold times at most seven days apart, that share a primary private funder. The null shuffles those funder identities inside calendar months.
2. **H2.** On the same window, the difference between information markets and public-process markets in the share of markets where two qualifying fresh wallets cross $1,000 on one outcome inside 24 hours. Families are permuted inside log-volume quintiles.
3. **H3.** The same construction as H1, using the primary private cash-out destination instead of the funder.

H1 is additionally labelled not specific to information markets if the public-process copy of H1 is also under the corrected threshold. Fewer than 20 complete test information markets, or a funding trace of under half of the seven-day fresh groups, is `INCONCLUSIVE_COVERAGE`.

## What is not confirmatory

Window counts other than the seven-day funding window and the 24-hour co-timing window are descriptive. The validation numbers are a replication. The Nobel 2025 market is a pipeline check against a link this repository already published. Open markets are described and are outside the three tests. No threshold above is to be edited after the tapes are read.

## Commitment and freshness

Capital committed is the high-water mark of buy notional minus sell proceeds on one outcome. Gross buys that only recycle the same cash do not qualify. Yes and No are not added. A qualifying wallet is F1 (no other Polymarket market before this one), F2 with first activity inside seven days, or F3 with a gap of at least 30 days. A failed history is not fresh. A contract proxy is not F0. A contract, a busy key, an infrastructure address, or a key that pays more than ten traced wallets is a service and is not a private funder.
