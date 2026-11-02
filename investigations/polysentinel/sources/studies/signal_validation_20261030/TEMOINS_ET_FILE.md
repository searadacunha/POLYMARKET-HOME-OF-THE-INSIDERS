# Témoins et file de revue : projections des sorties gelées

Scénario0. Pas de statut de faux positif ou d’initié pour ces wallets. La file déduplique les premières priorités ; elle ne compte pas les réobservations. Les maxima ne servent pas à trier la file.

| Ordre wallet | Première priorité UTC | Wallet | Score maximal ultérieur (rétrospectif) |
|---:|---|---|---:|
| 1 | 2026-10-01 17:29:49 | `0xd5a817163ea5acd551ee9201efbcf8b709bf9793` | 2 |
| 2 | 2026-10-01 23:19:49 | `0xeed7c2e6c4e998fd50098b66144ee8dff01d16b2` | 2 |
| 3 | 2026-10-08 15:30:49 | `0xb10047d6a254b2ebb306d7a7d13bf59171ab6461` | 2 |
| 4 | 2026-10-10 12:39:49 | `0xd218e474776403a330142299f7796e8ba32eb5c9` | 2 |
| 5 | 2026-10-11 10:13:49 | `0x6a678ca367432d28cb6aa55bb6bc57d8f53bdf6f` | 2 |
| 6 | 2026-10-13 11:03:49 | `0xf797d4d1c038d1eb0593edae0e66bf8e4b2e0bf2` | 2 |
| 7 | 2026-10-13 18:50:49 | `0x8d3319c51520518ad01f6744486ceea29f376f5b` | 2 |
| 8 | 2026-10-16 23:36:49 | `0x5061b324b41e1493c540b13ca78e915a579e1b03` | 2 |
| 9 | 2026-10-17 23:52:49 | `0x1ee9a5fc09665909c0cce297c581703bfbb9197f` | 3 |
| 10 | 2026-10-18 01:10:49 | `0xb1ca909e848cc24ec4e220ce1c453bc290c51705` | 2 |
| 11 | 2026-10-18 02:02:49 | `0x43372356634781eea88d61bbdd7824cdce958882` | 2 |
| 12 | 2026-10-18 02:34:49 | `0x1ca36d811f2928cd021992916f1a791df50fd80f` | 2 |
| 13 | 2026-10-20 16:03:49 | `0xb0c85813a7a4428f1139ff91d3118a92c391fe7f` | 2 |
| 14 | 2026-10-20 16:06:49 | `0x5cd5c8d7a17c78d7389d8b87b611aed83322ac33` | 2 |
| 15 | 2026-10-20 16:36:49 | `0x1387d145aaf01f6e33b66525dda6e1f51f6955f8` | 2 |
| 16 | 2026-10-20 21:30:49 | `0x7cbefea2f57bf129ea3446d53397b9520747c4b7` | 2 |
| 17 | 2026-10-21 10:48:49 | `0xde44891c8d31b14701892ad932c36429b05f751f` | 2 |
| 18 | 2026-10-21 12:30:49 | `0x818cc53babe10f79c21e21d73eac20a6a447a500` | 2 |
| 19 | 2026-10-21 14:06:49 | `0x5a218c7ad04135830a45c41aaed7294df7809318` | 2 |
| 20 | 2026-10-21 14:48:49 | `0xa278b41b5afda5d18da683eb7f851a7b2dc13369` | 2 |
| 21 | 2026-10-21 15:03:49 | `0x36901eb0f21519cc9055662a6d2483e96da1e16f` | 2 |
| 22 | 2026-10-23 02:58:49 | `0x7789957157a13aa3610e26d61ef8f99317b7a280` | 2 |
| 23 | 2026-10-23 05:34:49 | `0xd6b6f6924341b00626e603240f799644d4b6342b` | 2 |

La file par paire comporte28 dossiers ; sa liste complète, les quatre délais et leurs horodatages sont dans `derived/validation.json.gz`, `scenarios[].queues.wallet_events.queue`. Thin y est8e, après7 dossiers de6 autres wallets.

C1 : tous les témoins de même événement capables de baseline20, hors cible. C2 : aucun témoin dans les classes fixées. Âge = durée depuis première activité du corpus, quantité = achats bruts du corpus ; pas âge de création ni position nette.

| Wallet C1 | Âge observé h | Groupes BUY historiques | Achat24h | Prix moyen24h | Score | Conjonction |
|---|---:|---:|---:|---:|---:|---|
| `0x0b4cd82afbda072e8139a1d6b4bc83d2e8ef4277` | 87.877778 | 21 | 39.206100 | 0.40456196 | 0 | False |
| `0x9c185724747d33a19e7ac12962d9b0a0213ff3a2` | 419.920278 | 24 | 147.690000 | 0.50535500 | 0 | False |
| `0xd0698a02ded7b86284ebf25e9db0bb0d787ad078` | 86.470000 | 28 | 136.540000 | 0.41894954 | 0 | False |
| `0xd5a817163ea5acd551ee9201efbcf8b709bf9793` | 313.363056 | 36 | 4257.512200 | 0.48960753 | 2 | True |

Les43 témoins C0 et toutes leurs covariables sont exportés dans la sortie, `scenarios[0].cohorts.C0.wallets` et `features`. Leurs dépendances et financeurs communs ne sont pas établis.
