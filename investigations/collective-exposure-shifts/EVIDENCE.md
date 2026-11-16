# Evidence, collective exposure shifts

`auto` is replaced by the file hash by `python3 scripts/validate_evidence.py investigations/collective-exposure-shifts --fill`.

| File | SHA-256 | Role |
|---|---|---|
| `analysis_plan.md` | 833eaa17d562bbb967c42a8fc3dddf72de1670ac3f5f0f46f7812c82c0f0de82 | Frozen plan: population, signals, tests, verdict rule |
| `PROTOCOL.lock` | 80ed2803eeda83476833b8c1a5f5b8c02b227ce07973fb87096663a8a6edaf5d | Hashes of plan, code and tests at freeze time |
| `scripts/collect_tapes.py` | ee7f6d75d4e5cede7b07091ab25dcd5981b8bc816d9f03e418c2c3956b8af1d1 | Resumable v2 tape collector (cursor pagination, newest-first assertion) |
| `scripts/split.py` | 433980eac9aecea3f6b9245adf2ff07c41c8a48f940a4c9315f8f8aa77dbb64f | Outcome-free chronological split |
| `scripts/build_alerts.py` | 4f00ab97142bd100eb8324edf643d9846222c9b3f4014dff8b0418a7641d3d82 | Position accounting and S2/S3/S4/S4b signals |
| `scripts/score.py` | 20c9ea2e3f430a98e34e668c1b70e7662636f8ea07f69b0904d855a05a43a397 | Label join (only reader of labels), placebo draw, slippage grid |
| `scripts/stats.py` | b833bc16a5bd5fec4bd2611309dfb9058e0f29cbbf42719389a234d6d3784d87 | Declared tests T1–T8, event-clustered bootstrap, corrections |
| `scripts/report_tables.py` | 095e2f2a62b9911fc036beb2551904d31f80a47bba8f97e4a554aa12a60c4741 | Executable reading and verifiable alert lists |
| `scripts/reproduce_feb28.py` | bbc7786d73d056872b194e8633e49e8f85c2c7d66c24e295f60d5d37393ce53e | Reproduction and censoring check of the archived Iran tape |
| `scripts/interval_reading.py` | dca8e158f51e38c8110788f5160d1e5e26d8300a1729ec4671d904b881ec3300 | Case B: NO(D1)/YES(D2) interval positions at event level |
| `scripts/freeze.py` | 6dce9bb84a83586caccc95c9d75a885574b6bfeb2276410dce004ddb84f288aa | Writes PROTOCOL.lock |
| `scripts/make_manifest.py` | a7b9ec6b9e8f5dd176fcd5bcad1b65ff98ded0cfe9b832370a630fa9e891b714 | Writes data_manifest.json |
| `tests/test_exposure.py` | 0999186c0f2bb2cbc877603dc316c68827374990e7a7da54d1975c904fbb5954 | Accounting tests and the positive control (planted shift vs null tapes) |
| `tests/test_freeze.py` | 781329654bd114863fc5e423e8dfbaa51a412c31a6548a42a00dc639790a621c | Refuses a frozen file edited after the freeze |
| `results/alerts.jsonl` | f7772fb5ed863058e6ea2c20952739178bea9f33f273f28708b017d732792810 | Every alert with its variant, wallets and size (no outcome) |
| `results/alerts_status.json` | 5bdb1f2ab36c53eb9db388d5fd50a552ea0e4a76579b04604806c04f8f97c819 | Per-market collection and scoring status |
| `results/scored.jsonl` | 040d6e8e092270e5bf5eb1b3dca5633b689e5e5b1f2260681afd68d2f846d18b | Alerts joined to the outcome, with the slippage grid |
| `results/scored.jsonl.placebo.jsonl` | 50dc1f405cac2d504d333305225c887cef7bf5663447411189dac0096b3ccaf6 | S1 matched placebo points |
| `results/sweep_1_scored.jsonl` | dcaf8b3fa7263f24918af8de026236ea71511ca938895a8430162d3ab89ff455 | Declared sweep cell 1 (250 USD / 1,500 USD / 3 wallets) |
| `results/sweep_2_scored.jsonl` | 6289c1064b827a764934a045590cd68a574d853722d2a724674b16a36c905e7b | Declared sweep cell 2 (4 wallets) |
| `results/sweep_3_scored.jsonl` | 96cc893b14e71d606f87dba3abb45bcf1a1df8e9111b93b2e2216c908e523902 | Declared sweep cell 3 (180-minute window) |
| `results/tests.json` | 0a0abac106fe04abc0e6ba62b29b190c9c638d0b7144d385dab5173715df657c | T1–T8, intervals, corrections, verdict |
| `results/tables.json` | 49c67af8fa5918b1296e983bcf4929996ee820b9f101216dfefda2d45188963b | Slippage table, break-even, best alerts and false positives with tx |
| `results/feb28_recheck.json` | de96223d7ed4ccca46379090b19916850d8cc27dd7d6cf1ea9ad5c0d9833d832 | Archived 42,000-row tape vs complete tape |
| `results/interval_reading.json` | 589651452cb35ff1a6e37e148c146abe59fa31b66ee384218c00d6e818cd02cd | Event-level side sequences across deadlines |
| `data_manifest.json` | fc3e67cd1fbc0659c3b6178c2f59c800740a4b87ddf6e0d56fbcc090a7e83e1e | Inputs and local-only tapes, with size and hash |
| `amendements/001-2026-11-16-excess-metric.md` | 89bc57e2fc847bd2aab17f2a4db086c9c690d4e3f1bfd09826cedefd58aba631 | Dated amendment: excess metric and bootstrap p-values |
| `amendements/002-2026-11-16-replication.md` | caea22f4b0180acb1698f9b36371d47593847ae74087795b10b145709ca78bd3 | Dated amendment: pre-declared replication |
