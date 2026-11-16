# Evidence, collective exposure shifts

`auto` is replaced by the file hash by `python3 scripts/validate_evidence.py investigations/collective-exposure-shifts --fill`.

| File | SHA-256 | Role |
|---|---|---|
| `analysis_plan.md` | 833eaa17d562bbb967c42a8fc3dddf72de1670ac3f5f0f46f7812c82c0f0de82 | Frozen plan: population, signals, tests, verdict rule |
| `PROTOCOL.lock` | f6bbf9ee2b8719361427faeca5d1793384f6a2b059a1849613093c36e480b625 | Hashes of the plan, code and tests actually shipped |
| `PROTOCOL.lock.v1` | 80ed2803eeda83476833b8c1a5f5b8c02b227ce07973fb87096663a8a6edaf5d | The initial freeze of 20:12:35Z, preserved unchanged |
| `scripts/collect_tapes.py` | ee7f6d75d4e5cede7b07091ab25dcd5981b8bc816d9f03e418c2c3956b8af1d1 | Resumable v2 tape collector (cursor pagination, newest-first assertion) |
| `scripts/split.py` | 433980eac9aecea3f6b9245adf2ff07c41c8a48f940a4c9315f8f8aa77dbb64f | Outcome-free chronological split |
| `scripts/build_alerts.py` | 4f00ab97142bd100eb8324edf643d9846222c9b3f4014dff8b0418a7641d3d82 | Position accounting and S2/S3/S4/S4b signals |
| `scripts/score.py` | 8ac602a0915e47876ecc9743d9b73a186a7a25e668d0487c2128e909a634df5d | Label join (only reader of labels), placebo draw, slippage grid |
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
| `results/scored.jsonl.placebo.jsonl` | 6f0af45b44aa975fb87e71d7697746ea93d31e94507e423133b5551df90e965f | S1 matched placebo points |
| `results/sweep_1_scored.jsonl` | dcaf8b3fa7263f24918af8de026236ea71511ca938895a8430162d3ab89ff455 | Declared sweep cell 1 (250 USD / 1,500 USD / 3 wallets) |
| `results/sweep_2_scored.jsonl` | 6289c1064b827a764934a045590cd68a574d853722d2a724674b16a36c905e7b | Declared sweep cell 2 (4 wallets) |
| `results/sweep_3_scored.jsonl` | 96cc893b14e71d606f87dba3abb45bcf1a1df8e9111b93b2e2216c908e523902 | Declared sweep cell 3 (180-minute window) |
| `results/tests.json` | 50a0679c00c4c38d832628debaeb4d860cb9953ddf49643c601280f0d2058e88 | T1–T8, intervals, corrections, verdict |
| `results/tables.json` | 49c67af8fa5918b1296e983bcf4929996ee820b9f101216dfefda2d45188963b | Slippage table, break-even, best alerts and false positives with tx |
| `results/feb28_recheck.json` | de96223d7ed4ccca46379090b19916850d8cc27dd7d6cf1ea9ad5c0d9833d832 | Archived 42,000-row tape vs complete tape |
| `results/interval_reading.json` | 589651452cb35ff1a6e37e148c146abe59fa31b66ee384218c00d6e818cd02cd | Event-level side sequences across deadlines |
| `results/replication_alerts.jsonl` | 390d8158d9e990aaaa2ef0c430fe39a9734ff166e4f4778b0a91263e1eb7292b | Alerts of the pre-declared replication (1,579 markets) |
| `results/replication_status.json` | 125df9202a7a9b343405c565d86653a7257c0b6940fd308ac6d9e7124be8f9a1 | Per-market status of the replication |
| `results/replication_scored.jsonl` | 215fcc6517361bc5fa49b6550c02220446c5a3a86cbe907a7aaae7b42f567200 | Replication alerts joined to the outcome |
| `results/replication_scored.jsonl.placebo.jsonl` | d862fbf7862a1e1c020cb6f487dbb2f2767bb73e70ccab00f5e06951f1455db0 | Within-market placebo points of the replication |
| `results/replication_tests.json` | 4fcffe96c4a73c037a2ca5d64c29eddc9d6d10d78606d2fc2009087e1ab0c4c3 | T1–T8 on the replication, with the `NOT_SUPPORTED` verdict |
| `results/replication_tables.json` | b39c009f603208c4896b6e5b59e00ed2d0f8c00c6b15e6f454f4db270c253882 | Slippage table and verifiable alert lists of the replication |
| `results/replication_state.json` | b728cfa98fd9a77f2f000c727318dd2146be4fca56ead7f1c37469d92724021a | Collection state of the replication |
| `results/splits_expanded.json` | 39fb8bd95db0d8b5a029790701838c3452758640b7b3348ba723bbcb0c3a9233 | Chronological split of the replication sample |
| `data_manifest.json` | fc3e67cd1fbc0659c3b6178c2f59c800740a4b87ddf6e0d56fbcc090a7e83e1e | Inputs and local-only tapes, with size and hash |
| `amendements/001-2026-11-16-excess-metric.md` | f7c825f06d0e7913b504240dd6b9b11ddae6af86e050b5628c3ca9967793a6f4 | Dated amendment: excess metric and bootstrap p-values |
| `amendements/002-2026-11-16-replication.md` | c9b98c8f25f518a3c76ee22c9dee7a27582f60fe647a0031ba186e030e9c0e86 | Dated amendment: pre-declared replication |
| `amendements/003-2026-11-16-within-market-placebo.md` | 0ab4ae5de1be7dacf293ad22daa00f61ad0f5ea072a0750e3e1b9ab5f7722836 | Dated amendment: placebo drawn inside the alert's market |
