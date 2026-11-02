# Evidence: ballon-dor-wallets

Transactions, addresses and amounts are in the files below. `scripts/validate_evidence.py` checks these hashes. The hash of any other file is in `data_manifest.json`.

| File | SHA-256 | Role |
|---|---|---|
| `sources/reports/rapport_final.md` | 07216e205caaab0d94c38d0337e663b7e7e4b68cd024ecc1c49237cf73f62f8d | Report v3 |
| `sources/reports/liens_entre_wallets.md` | 4ae4db6aea58486754300ab315a9cf120d7400e36c1fa5f231925892a20796ed | Links between wallets |
| `sources/reports/AMENDEMENT_AUDIT_2026-11-02.md` | 1f482df109885acf7f8d7dbf3002ade0bd1bc8d7403bb8d954a2a8b5981eda08 | Amendment |
| `sources/reports/CONTRE_VERIFICATION.md` | efb1bd655a703a6d06f3835ab8b97ea64b08e06342d1231c45c3fe0bb221c40c | Counter-verification |
| `sources/collective/results.md` | d4ba90a65d1ebcd7fd49b05cec09597ff0bff590ed9e80370b59026ab0866e71 | Frozen results |
| `sources/collective/PROTOCOL.lock` | d533668f3fa011fabb8e71c988a46348d39b75af872f52d2be4d7cfec7baba23 | Freeze |
| `sources/collective/analysis_plan.md` | c54d0ad38638654a084e5b533632544fb3e0f0e1d28d590b276acd623d10d6f3 | Plan |
| `sources/archive/20261102_avant_amendement_audit/rapport_final.md` | de683ab687b293fca7d2ed9d09cda0aefe4341e0ee956510238022f76021c8c0 | Version 1, kept unchanged |
| `sources/reports/JOURNAL_MODIFICATIONS_2026-11-02.md` | e94e0adca33a588796eb4eda959e3d2764c9b07006fde041064ceea375cc49b8 | Hashes before and after each change |
| `sources/tools/appliquer_amendement_20261102.py` | c50f96a014074b9d16602e0b1b92f094a14de18d749aa2ba22b15638cbdfdb40 | Rebuilds report v3 from version 1 |
| `sources/archive/20261102_v2_avant_flow_trace/rapport_final.md` | 883683ab1bdb6cd8c9aa39d9f840398e8821852d1d1458b7c3eebc7b214c8bd3 | Version 2, kept unchanged |
| `sources/evidence/contre_verification_20261102/circuit_7xujs_brace_kraben.json` | 498745fc864e35b3964f7c665321e5c79719db3dab067d10b0fe25639874cf18 | Circuit in wei, continuity against succession |
| `sources/evidence/contre_verification_20261102/identifiant_relay_7xujs.json` | 0c7bff31639a99618598e386f20a83cb2d34fc425874b869df30b9f66a24e964 | Same Relay identifier on both chains |
| `sources/evidence/contre_verification_20261102/wallet_0xa8e6.json` | bfa1922305daae75710182bb422c0727de31b92b2988003733db1260a41728e7 | Unnamed wallet funded by the key of brace227 |
| `sources/evidence/contre_verification_20261102/wallet_0xa8e6_preuves.json` | c3e4576c444088b94ad338e3bb89266deb5d98e48dc5ff432f711e56cffb1daf | Relay records of its two deposits, burst E2 |
| `sources/evidence/contre_verification_20261102/etiquettes_blockscout.json` | ecddc8cb80fc679e6dfc77533ed5bcd995bea729e105cdd26a09152c681ef35a | ChangeNOW and other labels on two keys |
| `sources/evidence/contre_verification_20261102/calendrier_kane.json` | 2a4b4284d8f26131d67ac98a89a736390b84c6e1aa2f0d794a201c8f0c864e48 | Kane resolution and batch of 2,711 accounts |
| `sources/evidence/contre_verification_20261102/transactions_communes.json` | 41b2b91219b2504f3023d8daae3fab103318e29756efaf4cc5dff8614310f731 | The 14 shared transactions, decoded |
| `sources/evidence/contre_verification_20261102/stats_retraits_kane.json` | be75636f26a83ed84001d675ebb8f9e1506a40f88e71f6629ff8621d544f8e31 | Withdrawal speed, 13 strata, sellers |
| `sources/evidence/contre_verification_20261102/tests_exploratoires.jsonl` | a4d72f99ab66aed6c7533071f252b9d533b5b5136ed0a69a8db7520d4ea4580c | Exploratory tests, outside the frozen register |
| `sources/evidence/contre_verification_20261102/coupure_par_comparateur.json` | a9d4ac4b6b13bfe5d1ccde960045352af2c62966680205117b5e543d3a601998 | The cut histories, replayed from cache |
| `sources/evidence/contre_verification_20261102/taux_de_base.json` | e93b9c492a46ad7e6e2bd4c73ff8f8c185c9f5ea4a7087032215bc2a0172b233 | Base rate, recount |
| `sources/evidence/contre_verification_20261102/complements.json` | 4411ecb2b2faaa9cf44818646a1c1c7c019a3c37fb7d92925da241ac35b304a8 | Base rate bounds, E6 ranks, close buys |
| `sources/evidence/contre_verification_20261102/recoupe_flow_trace.json` | 7dee30415ff5bc968f6feed4d02efd322d07c113eb4142fe8b1710cebe86f857 | Cross-check of flow-trace, corrected comparator count |
| `sources/evidence/contre_verification_20261102/reconciliation_montants.json` | 1cd1fed963265ca88f9e565172412a63df84bbc579f4893c5474b852a4e00b0d | 25 burns, 46 mints, perimeters of the amounts |
| `sources/evidence/contre_verification_20261102/e4_reproduction.json` | 65aef3e259f3d122f7e32950ac5207c666c3c14b69c68d970d39b36670d46d35 | E4 v2 rerun, coverage of named pairs |
