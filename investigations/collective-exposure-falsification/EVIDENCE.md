# Evidence: collective-exposure-falsification

Wallet addresses and market ids are in the files below. `scripts/validate_evidence.py` checks these hashes. The hash of any other file is in `data_manifest.json`.

| File | SHA-256 | Role |
|---|---|---|
| `sources/PROTOCOL.lock` | fb2d486a7ac7dd3c9035a2ccc0c928c3a8318f66414a3899ca980567d477d7ee | Freeze of the plan, code and inputs |
| `sources/analysis_plan.md` | e564204a51642bc9ed54ef5df008d784d25f966ea323a78112c3cde6355e462d | Plan written before the hold-out was read |
| `sources/FALSIFICATION_REPORT.md` | 2349a7e17296eaf105ddb9076c9e74bf82f05734b89365d4747f21cc5b6d0b56 | Full report |
| `sources/STATISTICAL_RESULTS.json` | 620cfe8e9f741e73b0751a644c4d7c5672d9277539ebe59ddd34e21aed162df9 | Assembled results with source hashes |
| `sources/out/models/results_test.json` | 17bb1c7e8d478d9b8755d437606ddc7be3f94579b962fec3caf336a37f2f8a86 | TEST tests, read once |
| `sources/out/models/verdict.json` | 94f1c8382629e0ead06bab2969b2e823f9ba835f135ee6cc902dea93c01dbb7a | Verdict applied by code |
| `sources/controles/positive_controls.md` | a527b7bb874323038732371c0965a56982a5d5830fb1ebb2f609dae5f231d4c9 | Controls and power gate |
| `sources/audit/post_result_audits.md` | 15515efb1cb0add9d62144af18c23a8a494b024e57647c7d6c30a4fe088d1f11 | Independent statistics and leakage audits |
