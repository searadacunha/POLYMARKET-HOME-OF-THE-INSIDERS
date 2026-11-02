# Evidence: changenow-proof

Transactions, addresses and amounts are in the files below. `scripts/validate_evidence.py` checks these hashes. The hash of any other file is in `data_manifest.json`.

| File | SHA-256 | Role |
|---|---|---|
| `sources/reports/CHANGENOW_PROOF_FINAL.md` | ccfc9ad1a6c659f15247fa84cd4915ae2f4e574752afb5b3a768b81f755477a8 | Final report |
| `sources/data/verified_transfers.csv` | d4f211b5f5dc6dfc0be43ede2af6e4670a73fbf823f2e5f336551179690cf73c | Transfers reread on a node |
| `sources/reports/ATTRIBUTION_EVIDENCE.md` | a9ff92cd0cbf17627fea73122e610e68e36ada286cf8b2cfb240bad16defb0b2 | Attribution |
| `sources/reports/FALSE_POSITIVES.md` | 9696165ac7eb2499c8277540fb19f139d0182aad67bda8317236f639bf84b370 | False positives |
| `sources/reports/XMR_VISIBILITY.md` | deb69cea5ec75bcf387dc3a57d7fdf1516647944d220535033f62c67a9006aaf | Monero |
| `sources/reports/PAYOUT_MATCHES.md` | c0c954daee2b31302cecfcd203ee8a31f9e30864b8cee857abab5d4d158e16f4 | Payouts |
| `sources/reports/PAYIN_TRANSACTIONS.md` | 66abe338a439450c0d020462b75490002cc3bc6e149f53ea378fe1eb5858d8c5 | Pay-ins |
| `sources/data/changenow_candidates.csv` | ffd9c432c11a4bae5c0e3348106d2659ba775684fb731f3787affc189e014a47 | Addresses some source calls ChangeNOW, with sources and levels |
| `sources/data/attribution_links.csv` | 88a962a1eda73a858ab77cfa3baafceb1779919a5f08072626358abd019f3a7e | Links between the studied and labeled addresses, funder lineage, controls |
| `sources/data/unresolved_paths.csv` | 2df338ed9da2a340f936619063ef065a9dfa0b2cc20b68600ab64d6308446c3b | Where each path stops and what would resolve it |
| `sources/graphs/changenow_network.graphml` | 53c3c08a330df708d9b8fbbbaa06cf116e01238e9d2bf6f50d4231f5944c9bb8 | Graph of the transfers and links |
| `sources/state/figures.json` | eb4bd927ce4e8a6208915595b5419d863160e344dfeee81113cb2ebd555dceec | Figures quoted by the reports, recomputed |
| `sources/state/p10.json` | 13a8f8ed61e4c0c92a02c842817e53dedb7110a30c36d1feabfefd35ef5db9c4 | Witnesses, recipient properties, amount matches |
| `sources/state/p16.json` | ceb3806988c0636565982347fb9adb104e700c66270ac08e407d4b23fad21ba9 | Base rate on the final comparator file |
| `tests/check_published.py` | ae43c822aecdba5d63ea3ac6fa476a8a2789fced1c1d8250af6b5408e4c9e79c | Check of the published copy, from a fresh clone |
| `sources/tools/selfcheck.py` | 51c5ea52f7ba30d38a955ae5264fafbb1474bc709cb24a79b07d9c6b3541e3c0 | Self-check |
