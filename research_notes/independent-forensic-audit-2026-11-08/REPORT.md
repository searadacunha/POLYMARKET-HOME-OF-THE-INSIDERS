# Audit forensique indépendant — 8 novembre 2026

Document unique. Les versions antérieures de ce fichier empilaient une continuation sur un premier passage ; cette version les remplace. Les archives gelées du dépôt ne sont pas réécrites.

Base de `main` après `git fetch` : `ab7ca23d7824cdf65962c62a736364da27964ec4` (2026-11-08 18:14:03 UTC). Clone complet, 218 commits du `5c5e23ef` (2026-11-02 14:32 UTC) à cette base. 170 commits et 31 branches distantes ne sont pas dans `main` et n'ont pas été lus. L'arbre suivi compte 7 686 fichiers.

La mission demandée n'est pas achevée sur quatre surfaces : lecture ligne à ligne des 218 diffs, histoire hors `main`, montants SPL des jambes Solana, comptabilité fill par fill. Le détail est en H.

Légende : **RPC** = nœud public lu le 8 novembre 2026 ; **archive** = fichier déjà dans le dépôt ; **doc. externe** = page ou PDF public ; **inférence** = jugement qui ne suit pas d'un seul de ces trois. Niveaux : CONFIRMED, SUPPORTED, HYPOTHESIS, REFUTED, UNRESOLVED. Une absence de document ne réfute pas une hypothèse.

## A. Fiabilité et ce qui tient

Ce qui est montré, sans propriétaire et sans information privilégiée :

- **38** proxys distincts dans la cohorte Iran de février 2026 (**archive**). **36** ont un `createdAt` public les 22, 23, 24 ou 25 février 2026, et ces dates reproduisent le décompte du CSV (18 / 11 / 4 / 3) (**doc. externe**, API gamma).
- **38** transactions directes, de **32** portefeuilles, vers `0xc5bb1be0407db7312911ec765d399d02461e411a` : reçus RPC statut 1, bloc, from, to, contrat et montant atomique concordants. **CONFIRMED, RPC.**
- **12** crédits Polygon Relay. **7** transactions contiennent l'identifiant d'ordre. **5** ont le reçu et le hash du fournisseur, pas l'identifiant dans l'input. **CONFIRMED** pour les reçus ; **SUPPORTED** pour le lien d'ordre des 5.
- **2** reçus Base et **1** reçu Arbitrum. **CONFIRMED, RPC.** L'identifiant d'ordre n'y est pas. Le saut Arbitrum suivant est un EOA qui mélange des fonds, nametag public Coinbase 26. **SUPPORTED** comme infrastructure comminglée. Le crédit d'un client nommé est **UNRESOLVED**.
- Chaque côté du brut Polygon officiel, entrées et sorties séparément, vaut **1 984 038,168550** USDC/USDC.e. Les exports RPC annoncés entre les blocs 81 100 000 et 96 974 221 retrouvent les hash et montants de l'archive. **CONFIRMED pour les opérations positives observées ; EXHAUSTIVITÉ NON ÉTABLIE** pour la fenêtre entière.
- Somme d'archive des résultats au centime : **+1 576 522,86 USDC**, 8 comptes avec des quantités de parts ouvertes. Ce n'est pas un audit comptable complet.
- Intersections d'adresses 38 ∩ 8, 38 ∩ 19, 38 ∩ 71, 8 ∩ 19, 8 ∩ 71, 19 ∩ 71 : **vides**.
- Clôture Railgun sur les JSON bruts : **22 044,160154** USDC, 384 enfants, équation fermée. **CONFIRMED** sur ces fichiers.
- PDF Inca : SHA-256 égal au hash déjà cité ; les cinq adresses et les deux intersections avec les 19 y sont. **CONFIRMED** pour ces adresses.
- Bande publique du marché « US strikes Iran by February 28, 2026? » : 42 000 trades, 84 pages. Parmi 733 autres comptes créés les mêmes quatre jours, **16** ont un achat NO strictement avant un achat YES sur ce seul marché et dans cette bande ; **20** des 36 de la cohorte l'ont. Descriptif. Pas de p-value.

Ce qui n'est pas une réfutation :

- L'hypothèse qu'un même client Coinbase détient les 38 proxys. Elle n'est pas démontrée. Elle n'est pas contredite par l'absence de grand livre ni par le mélange en aval. **UNRESOLVED.**
- L'arithmétique du test KPMG. Le script du dépôt reproduit sa propre queue. Je ne l'ai pas contredite. L'inférence d'initié n'est pas soutenue. Ce n'est pas **REFUTED**.

## B. Affirmations

### B1. Cohorte des 38

| Fait | Contrôle | Niveau |
|---|---|---|
| 38 proxys, même ensemble que la liste gelée | `verify.py` | CONFIRMED, archive |
| 36 créés les 22–25 février | CSV et `createdAt` gamma | CONFIRMED |
| NO puis YES dans le ledger d'activité, premier YES le 27 février 20:49–23:35 | min/max du CSV | CONFIRMED pour ce champ d'archive, pas pour un seul marché |
| Nom `Anon` sans profil servi | colonne du CSV | CONFIRMED comme absence de profil servi |
| +1 576 522,86 et 8 comptes avec parts ouvertes | somme des centimes | CONFIRMED comme somme d'archive |
| 86 dépôts, 39 financeurs, aucun financeur commun dans la table | vérificateur | CONFIRMED sur cette table |

Sur le seul marché du 28 février, dans la bande relue, 20 des 36 ont un achat NO avant un achat YES, 15 n'ont qu'un achat YES, 1 n'a aucun achat. Le 36/36 du CSV n'est donc pas ce marché seul. Les deux lectures portent sur des périmètres différents. Aucune ne prouve une information privilégiée.

### B2. Destinataire `0xc5bb1be0…`

`eth_getCode` vide sur Polygon, Arbitrum et Base (**RPC**). EOA. Nonces archivés 0–23. Ce n'est pas un contrat de pool.

Contrats, 6 décimales : USDC `0x3c499c542cef5e3811e1192ce70d8cc03d5c3359`, USDC.e `0x2791bca1f2de4661ed88a30c99a7a9449aa84174`.

**Chaque côté** de l'archive positive vaut 1 984 038 168 550 unités. Ce n'est pas la somme débit+crédit.

| Composante | Lignes | Unités atomiques | USDC |
|---|---:|---:|---:|
| Entrées directes des 32 proxys | 38 | 1 509 327 186 471 | 1 509 327,186471 |
| Entrées Relay | 12 | 474 710 981 541 | 474 710,981541 |
| Poussières USDC.e | 3 | 538 | 0,000538 |
| Total des entrées | 53 | 1 984 038 168 550 | 1 984 038,168550 |
| Sorties de valeur positive | 24 | 1 984 038 168 550 | 1 984 038,168550 |

Les quatre exports RPC déclarent la plage de blocs 81 100 000 à 96 974 221 ; leurs **53 logs entrants et 30 sortants** concordent avec les montants enregistrés, et ils ne contiennent pas de transfert positif supplémentaire après le dernier bloc de l'archive (83 968 639). **Cela ne démontre pas l'absence d'autres opérations dans les blocs non prouvés comme couverts.** Six transferts USDC de valeur **0** vers des adresses homographes des destinataires de sweep sont enregistrés et exclus des montants. `balanceOf` courant des deux jetons était **0** lors de la consultation. La plage antérieure au bloc 81 100 000 n'a fait l'objet que de sondes discontinues.

Qualité de collecte : les quatre JSON indiquent respectivement **4, 24, 28 et 30 `failed_splits`**, soit 86 événements au total. Sans journal par intervalle réussi, ces compteurs ne permettent pas de savoir si tous les essais ont finalement été récupérés. Les nombres de requêtes `windows` ne démontrent pas une couverture sans trous. `scripts/check_polygon_rpc_coverage.py` vérifie à froid l'identité des logs, les 38 reçus directs, les 12 crédits Relay et l'égalité des deux côtés, mais conclut **NOT_ESTABLISHED** pour l'exhaustivité. Un rejeu RPC exhaustif documentant chaque plage (début, fin, résultat, retries, nœud) est encore requis avant d'affirmer l'absence de transferts supplémentaires. Ne pas utiliser l'égalité des totaux pour prouver la propriété commune des comptes.

`0x660629fe…` porte sur Polygonscan le nametag « Coinbase: Deposit Funder 3 », compilation hildobby (**doc. externe**). Les quatre destinataires de sweep sont des EOA ; leurs nametags n'ont pas été rechargés ici.

### B3. Douze crédits Relay et deux Base

Identifiant dans l'input (**CONFIRMED, RPC**) : 99,800270 ; 9 995,375683 ; 229 926,513364 ; 3 004,254940 ; 19 106,086041 ; 20,976304 ; 99 090,130751 USDC. Les trois du milieu n'avaient pas de calldata dans le snapshot ; le hash a été choisi par montant unique, puis l'input a montré l'identifiant.

Reçu sans identifiant dans l'input (**CONFIRMED** pour le reçu, **SUPPORTED** pour l'ordre) : 4,988487 ; 9,986706 ; 57 673,995459 ; 4,991204 ; 55 773,882332 USDC. Les expéditeurs sont des EOA de solver ou le contrat `0xf5042e6f…` (8 925 octets), pas les proxys.

Base, deux RPC (`mainnet.base.org`, `base.drpc.org`) : 58 475,748639 au bloc 42 827 159, logIndex 772 ; 42 142,977084 au bloc 42 827 432, logIndex 452. Arbitrum, deux RPC : 59 863,534997 au bloc 437 513 468, logIndex 68, puis le même montant au bloc 437 514 401, logIndex 4, vers `0xa656f7d2…`. Sur 200 000 blocs, cette adresse envoie 122 transferts USDC totalisant 1 042 735,384784 et garde un solde. Nametag public Coinbase 26. Propriété du client : **UNRESOLVED**.

### B4. Huit, dix-neuf, soixante-et-onze, Inca

Huit comptes : somme des composants de `pnl_table.json` = 509 993,244904, soit **509 993,24** au centime près sur le total. Autre population que les 38. Intersections vides avec les 19 et les 71. Les titres 151 084,40 et 660 708,94 ne sont pas reconstruits ici.

PDF Inca, téléchargé le 8 novembre 2026, SHA-256 `2b14e2874ff26712db5e85a3fcbb5c1c3c425c91671245bc9b34be892141d38b`, 30 pages. Cinq adresses et profits 36 790,56 ; 85 120,83 ; 128 736,79 ; 34 996,87 ; 52 329,69. Deux sont dans les 19. Quatorze reçus Polygon de l'index de sorties : statut 1. Vingt-cinq autres lignes de cet index, surtout Solana, non rejouées.

Pulser : 7 596 lignes, 27 hash, 0 ambigu, 14 699,999999 USDC de transferts. **CONFIRMED** sur l'extrait. Pas un profit.

### B5. KPMG et Railgun

KPMG : 28/28 reçus Polygon, bloc, logIndex et montant USDC.e concordants. 28/28 signatures Solana existent et `meta.err` est null. Le delta SPL n'est pas recalculé : l'existence n'est pas le montant. **CONFIRMED** pour les reçus Polygon ; **SUPPORTED** pour la présence Solana. La fonction `tail` du dépôt, exécutée avec le reste du workflow, reproduit sa queue sur les `p_i` stockés. Je n'ai pas reconstruit le plan (sélection, dépendance, prix, corrections). L'inférence d'initié n'est pas soutenue. L'arithmétique n'est pas **REFUTED**.

Railgun : six logs bruts, montant et logIndex égaux au CSV, frais 0,25 %. Somme 22 044,160154. Entrées des distributeurs = sorties = cette somme. 384 enfants. Vers les solveurs 21 977,513862, résiduel 66,652297, poussière 0,006005, fuite ≥ 0,01 hors graphe : 0. Premier unshield **2025-12-16T18:43:51Z**. 71 comptes, 5 `won=True`, donc 66 pertes. **CONFIRMED** sur ces fichiers. Pas une connaissance partagée d'une date.

### B6. Ballon d'Or

Snowflake et le JSON public `cdn.syndication.twimg.com`, lu le 2026-11-08T20:18:38Z : `2111149784858042762` à **2026-10-16T17:38:26Z**, texte qui nomme Kane, Mbappé, Yamal, Rodri, Messi ; `2110285369748963671` à **2026-10-14T08:23:34Z**, 304 caractères, sans ces cinq noms, avec la mention d'un achat de 66k shares. **CONFIRMED** pour ces textes courts. Le texte long du 14 octobre reste **UNRESOLVED**. La bande de 692 519 fills n'est pas réagrégée. Pas de probabilité d'initié.

## C. Preuves nouvelles

Registre `evidence/SHA256SUMS`. Champs de trades conservés : proxy, side, outcome, outcome_index, timestamp, size, price, transaction_hash. Nom, pseudonyme, bio et images écartés.

| Fichier | SHA-256 | Heure de lecture |
|---|---|---|
| `g38_rpc_replay_2026-11-08.json` | `14298e5a6ab297247fc77a995ec74411ebc8c06e3d588144870a780427ac812a` | 2026-11-08T19:23:17Z, Base revu juste après |
| `g38_direct_receipts_2026-11-08.json` | `a4e15dbcb4848cadb498cc1a969f16d2abfd18c7a63f81d6813acc373ca76450` | même soir, avant les logs |
| `polygon_logs_USDC_from.json` | `64168f0b8efe0ebdc7530478cfe44e9b3133da88394b2fd95421b26f8693c554` | plage déclarée jusqu'au bloc 96 974 221, exhaustivité non prouvée |
| `polygon_logs_USDC_to.json` | `df60873269a59b98a157794ba6c02fd2475c8107c9aaefa79defa563738f44f4` | idem |
| `polygon_logs_USDCE_from.json` | `969298640e2e6b1b966b69e0280e15a251a099c4ecbc793e48e90ffaba014a0a` | idem |
| `polygon_logs_USDCE_to.json` | `ce9e6e19a55a7eae7462d897b201c163c7886d822498b69fa7fcff7a5b09bc96` | idem |
| `kpmg_polygon_receipts_2026-11-08.json` | `a07bbe031a2413307e982d9d987acb51493608511fe3101b1d9ec374a4df9ab1` | même soir |
| `kpmg_solana_receipts_2026-11-08.json` | `b08c75fb69f1c833a99bd82f7cc710a000353006e5f36a3bde04f60641e69107` | `api.mainnet-beta.solana.com` |
| `inca_polygon_receipts_2026-11-08.json` | `e143e5800e33bda7fc1b79655d681497fa0b73e21192425800179ed3418ac6e9` | 14 reçus |
| `ballon_syndication_2026-11-08.json` | `34e00a45b3fd7c52ff212e4b9c2b038a0fd90bfbbb21a5b73aae617c9106a2b4` | 2026-11-08T20:18:38Z |
| `feb28_market_trades.jsonl` | `3891c17857715ab5f61d74142faa93a52f58fc2d9719cddd2de60365a6889429` | 2026-11-08T20:18:38Z, 84 pages, 42 000 lignes |
| `feb28_noyes_descriptive.json` | `5cd081c264f902f09d1bfdd1c6e56797518196e9f9e5c798cb595ad1b8e9e649` | comptes dérivés de cette bande |
| `feb22_25_traders_createdAt.csv` | `7e145d5fc427aee8513fc828022c58bf508e5479e0f766ce4237dcb89560b303` | profils gamma |
| `control_population_summary.json` | `b27586ce3910fe5a67f2815aebddb5022f557c073d4f62ddaf5af3776559c543` | premier passage sans le côté |
| `arbitrum_onward_usdc_outs_200k.json` | `18d337978062ddd0bcee5acf85e3ffc6bf76a6b8049b6522bb8ed1479de733d9` | fenêtre Arbitrum |

RPC qui ont répondu : `polygon.drpc.org`, `gateway.tenderly.co/public/polygon`, `mainnet.base.org`, `base.drpc.org`, `arb1.arbitrum.io/rpc`, `arbitrum-one.public.blastapi.io`. Refus sans valeur négative : publicnode 403, polygon-rpc.com 401, ankr exige une clé, Blockscout 403, Routescan 400, `base.llamarpc.com` 403. Data API v1 : 410. Paramètre `market` en v2 : 400. `condition` et `next_cursor` : 200.

## D. Finances : champs lus, et ce qui n'est pas une comptabilité complète

Champs présents dans `ledger_g38.json` et sommés ici, 38 comptes : `buys` 5 492 912,540709 ; `sells` 1 133 873,040054 ; `redeems` 5 926 572,397266 ; `merges` 8 196,025925 ; `splits` 0 ; `other_reward` 790,9741 ; `other_yield` 2,9644 (2 comptes) ; `deposits` 567 775,221686 (clé absente pour 4 comptes, comptée 0) ; `withdrawals` 2 188 286,456614. `trading_result` non arrondi : somme **1 576 522,861036**. Somme des centimes du CSV : **1 576 522,86**. `open_share_tokens` : quantités de parts, 8 comptes, pas un prix. Retraits moins dépôts : **1 620 511,234928**. L'écart avec le résultat de trading n'est pas attribué à des frais : il n'y a pas de colonne de frais.

Une comptabilité complète demanderait, et ce dépôt ne l'a pas refaite ici : chaque fill (prix, taille, frais CLOB, côté), évaluation des parts ouvertes, gas, séparation dépôt/retrait/bridge/échange, et le rapprochement de ces lignes avec les transferts on-chain de chaque proxy. Le +1 576 522,86 reste une somme d'archive.

Le brut 1 984 038,168550 est un flux de jetons du destinataire, pas un PnL. Les populations 38, 8, 19 et 71 ne s'additionnent pas.

## E. Contrôles, sur la bande qu'on avait d'abord tronquée

Le premier passage avait gardé le proxy et les timestamps extrêmes, et jeté le côté. Ce n'était pas une donnée inaccessible. La même bande a été relue le **2026-11-08T20:18:38Z** : 84 pages, 42 000 lignes, du **2026-02-21T18:48:58Z** au **2026-02-28T09:32:33Z**, marché `0x3488f31e6449f9803f99a8b5dd232c7ad883637f1c86e6953305a2ef19c77f20`.

Population : `createdAt` gamma le 22, 23, 24 ou 25 février 2026, et présent dans cette bande. **769** profils, dont **36** de la cohorte et **733** autres. 1 262 proxys de la bande n'ont pas de profil (HTTP 404 sur un échantillon de 8 et au second passage) : leur date de création est inconnue, ils sont hors de ce 769. La bande n'est pas la vie du compte, ni les autres marchés Iran.

Règle, fixée avant le décompte de cette relecture : achat NO strictement avant achat YES, `side=BUY`, ce marché, cette bande.

| Groupe | n | NO puis YES | YES puis NO | YES seul | NO seul | aucun achat |
|---|---:|---:|---:|---:|---:|---:|
| Cohorte | 36 | 20 | 0 | 15 | 0 | 1 |
| Autres créés ces jours-là | 733 | 16 | 20 | 309 | 354 | 34 |

Parmi ceux qui achètent les deux côtés : 20/20 dans la cohorte, 16/36 chez les autres. Premier achat YES dans le créneau d'archive 27 février 20:49–23:35 UTC : 6 des 35 acheteurs YES de la cohorte, 9 des 345 autres. Premier achat YES avant le 28 février 06:13 UTC (heure de repricing citée ailleurs dans le dépôt, pas un seuil préenregistré ici) : 16/35 et 308/345. Sur ce marché, 19 des 36 ont leur premier achat YES dans l'heure 06 du 28 février.

C'est une description. Les 36 ne sont pas un tirage dans les 769. Aucun plan d'échantillonnage n'a été figé avant de connaître la cohorte. Les bots, la résolution (ventes à 0,999 le matin du 28) et le fait que la bande s'arrête à 09:32 empêchent de lire ces taux comme une rareté. **Pas de p-value.** Un placebo horaire ne serait pas couvert : on n'a pas une seconde bande indépendante ni la vie hors marché. La question « la séquence est-elle rare ? » reste donc sans test. Elle n'est plus « non estimable parce que le côté manquait ».

## F. Code

Correctifs déjà dans la branche, chacun échouant sur `ab7ca23` et passant maintenant (`scripts/test_correction_before_after.py`, 7 tests) :

1. Commentaire gzip non scanné, puis refusé.
2. `.JSON.GZ` au-dessus du plafond accepté, puis refusé.
3. `zlib.error` sortait du processus, puis refus par fichier.
4. `1000` dans `21000` ou `0xabc1000def` comptait, puis non. Un `1000` dans `1000.50` compte encore : le point n'est pas un chiffre. `validate_evidence.py` sur le dépôt : 0 erreur. Limite laissée.
5. `sources/../FINDINGS.md` était lu, puis rejeté.
6. `restore_stream` écrivait hors de la destination, puis `(0, 1)` sans écrire.
7. Une page Etherscan sans `DONE` passait dans l'ancien `fetch_rows` ; `require_etherscan_complete` échoue.

`x-history` `verify.py`, sans l'archive brute, réécrivait `verification.json` et remplaçait B1/B2 par un saut tout en sortant 0. Le fichier gelé a été restauré. Le script conserve ces contrôles enregistrés quand l'archive brute est absente.

L'ancienne ancre PR `0658ab3a` autorisait les changements du README en se comparant à une référence introduite par la PR elle-même : c'était un contournement involontaire. **Correction :** `scripts/publication_baseline.json` et `README.md` ont été rétablis octet pour octet depuis `main` (`ab7ca23`), avec ancre préexistante `eea86d95`. `scripts/check_publication.py` refuse désormais en contexte PR, avec `--base-ref`, toute altération du fichier de politique relativement au commit de destination. Trois tests dédiés reproduisent les cas de modification, conservation et absence de politique. Une protection indépendante côté serveur reste recommandée : le code de CI est lui-même versionné dans la PR.

Scan du dépôt après les correctifs gzip : 821 AST, 4 422 fichiers, 0 gzip incomplet.

## G. Fichiers, commandes, commits

| SHA | Rôle |
|---|---|
| `ab7ca23d7824cdf65962c62a736364da27964ec4` | `main` de départ |
| `0658ab3ad326763f92a83250bacd19e9c39de7e6` | anciens correctifs et version intermédiaire du README, désormais restauré sur la branche |
| `2281a9e745ca3e9c9768086097ecf6dd10c63cb1` | ancienne modification de l'ancre, annulée par les commits correctifs |
| `34d502692a1a95bed5556c3aafb7523948600607` | URL de PR dans l'ancien rapport |
| `87d3fd395f244f5725f23c1909b3118ec0063c2c` | preuves de continuation et rapport encore double |
| `8e1eddfae1033b846a32fcf4210bee3e0f71e7f4` | une phrase d'identification, tête précédente |

Ce fichier est le rapport consolidé, amendé pour séparer reçus RPC vérifiés et exhaustivité de balayage. PR : https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/65. Pas de merge.

Code touché dans la branche : `scripts/phi_lib.py`, `scripts/audit_public_repository.py`, `scripts/import_snapshot.py`, `scripts/validate_evidence.py`, `scripts/backup/phi_backup.py`, `scripts/test_audit_public_repository.py`, `scripts/test_integrity_regressions.py`, `scripts/test_correction_before_after.py`, `research_notes/g38-proof-tier-audit-2026-11-08/verify.py`, `research_notes/g38-proof-tier-audit-2026-11-08/test_verify.py`, `research_notes/x-history-2026-11-06/verification/verify.py`, `.github/workflows/repository-integrity.yml`. Le README a été restauré sans changement de style ou d'octets par rapport à `main`. `VERIFIED_FINANCIAL_FINDINGS.md` porte les précisions documentaires. Nouveaux garde-fous : `check_publication.py`, `test_publication.py`, `check_polygon_rpc_coverage.py`, `test_polygon_rpc_coverage.py` et workflow.

Commandes de la suite workflow, 8 novembre 2026, toutes **EXIT 0** : ChangeNOW, C1/C5/C7, outils GitHub, adapters, Iran/Inca/Pulser, Relay du 4 novembre, liens, X (puis restauration du JSON et correctif), KPMG/Railgun offline, `test_phi`, `test_parallel_publication`, `test_publication`, `validate_evidence`, `build_master_report.py --check`. Après cette consolidation : `check_research_links`, `check_publication`, `audit_public_repository`, `test_correction_before_after`, `test_integrity_regressions`. Collecteurs non lancés. Disque externe absent. API d'administration GitHub non utilisée.

## H. Périmètre encore ouvert

La mission complète n'est pas atteinte.

1. Histoire : sujets des 218 commits, chemins de sécurité, pickaxe sans impression de secret. Pas chaque diff. Pas les 170 commits hors `main`.
2. Comptabilité : champs de D seulement. Pas les fills, les frais, ni la valeur des parts ouvertes.
3. Solana : signatures KPMG présentes, delta SPL non calculé. 25 lignes non Polygon de l'index Inca non rejouées.
4. Logs Polygon : avant le bloc 81 100 000, sondes seulement ; entre 81 100 000 et 96 974 221, les JSON ne contiennent ni manifeste de plages complètes ni statut de récupération des 86 `failed_splits`. Couverture intégrale non prouvée.
5. 1 262 proxys de la bande sans `createdAt` (404). Séquence NO/YES non calculée pour eux, ni hors de cette bande, ni sur les autres marchés.
6. Nametags des quatre sweeps et des autres financeurs de gas. Grand livre Coinbase : la propriété commune reste UNRESOLVED.
7. Texte long du 14 octobre. Bande Ballon d'Or non réagrégée.
8. Protection de branche côté serveur, non lue.

## Matrice de couverture

| Zone | Fait | Non fait |
|---|---|---|
| 218 commits de `main` | sujets, chemins, pickaxe | chaque ligne ; hors `main` |
| 38 transactions / 32 portefeuilles | 38/38 reçus | 86 dépôts d'entrée |
| Logs du destinataire | 53 entrées, 30 sorties réconciliées avec les reçus observés | couverture intégrale 81 100 000–96 974 221 non prouvée ; plage antérieure non couverte |
| 38 / 8 / 19 / 71 | intersections vides, PnL des 8 | flux 151k et 660k |
| Ledger | sommes des champs listés en D | fills, frais, mark-to-market |
| Inca | PDF et 14 reçus Polygon | 25 autres jambes |
| KPMG | 28 reçus Polygon, 28 signatures | delta SPL ; plan statistique |
| Railgun | équation sur les JSON | nouveau RPC |
| Ballon | deux textes publics et leurs heures | 692 519 fills |
| Témoins | 769 profils, côtés relus, taux descriptifs | p-value ; vie hors bande ; 404 |
| Workflow | pas listés en G, EXIT 0 | collecteurs, disque externe |

## Tableau de décision

| Affirmation | Statut dans le dépôt à `ab7ca23` | Contrôle de cette session | Nouveau statut | Preuve | Action |
|---|---|---|---|---|---|
| 38 proxys distincts | CONFIRMED, archive | vérificateur et CSV | CONFIRMED | `g38_accounts.csv` | aucune |
| 36 créés les 22–25 février, NO puis YES dans le ledger, premier YES 20:49–23:35 | CONFIRMED pour le CSV | dates gamma ; bande d'un seul marché | CONFIRMED pour le CSV et les dates. Sur ce marché seul : 20/36 NO puis YES, 15 YES seul | CSV, gamma, `feb28_noyes_descriptive.json` | ne pas étendre le 36/36 à ce seul marché |
| +1 576 522,86, 8 parts ouvertes | somme d'archive, pas un profit réalisé | re-somme des champs | CONFIRMED comme somme d'archive | `ledger_g38.json` | ne pas dire audit complet |
| 32 portefeuilles, 38 transferts directs | CONFIRMED, archive | 38 reçus RPC | CONFIRMED, RPC | `g38_direct_receipts_2026-11-08.json` | dénominateur 38/38 et 32/32 |
| 12 crédits Relay par montant | SUPPORTED | input RPC | 7 CONFIRMED avec order id ; 5 reçus CONFIRMED, lien SUPPORTED | `g38_rpc_replay_2026-11-08.json` | partition figée |
| Reçus Base absents | Relay seulement | deux RPC | CONFIRMED pour le reçu ; order id absent ; crédit client UNRESOLVED | blocs 42827159 et 42827432 | `VERIFIED_FINANCIAL_FINDINGS.md` précise ; README protégé rétabli |
| Saut Arbitrum non classé | UNRESOLVED | logs et nametag | infrastructure SUPPORTED ; client UNRESOLVED | `arbitrum_onward_usdc_outs_200k.json` | README corrigé |
| Un client Coinbase pour les 38 | UNRESOLVED | pas de ledger ; mélange | UNRESOLVED. L'absence ne réfute pas | — | ne pas écrire REFUTED |
| 1 984 038,168550 | brut entrées et sorties, formulation ambiguë | chaque côté, puis logs | CONFIRMED sur les opérations observées, PAS comme bilan exhaustif du compte | quatre fichiers de logs, vérificateur offline | rejouer les plages sans manifeste |
| Huit comptes, +509 993,24, distincts des 19 et des 71 | séparé | intersection vide, somme JSON | CONFIRMED sur ces ensembles | `pnl_table.json` | ne pas additionner |
| Inca : 2 des 5 dans les 19 | SUPPORTED par le recoupement du dépôt | PDF au hash cité | CONFIRMED pour les adresses et les deux intersections | PDF non commité | aucune |
| Pulser, 27 hash, 14 699,999999 | CONFIRMED sur l'extrait | 7 596 lignes | CONFIRMED sur l'extrait | `flows.csv` | aucune |
| KPMG, 14 passages et p-values | passages présentés comme rejoués ; p-values citées comme descriptives d'un groupe choisi | 28 reçus Polygon ; `tail()` du dépôt | reçus Polygon CONFIRMED ; Solana SUPPORTED pour l'existence ; inférence d'initié non soutenue ; arithmétique non REFUTED | `kpmg_polygon_receipts_2026-11-08.json` | ne pas écrire REFUTED |
| Railgun, 71 comptes, 66 pertes, arbre fermé | CONFIRMED dans l'index, à rejouer | reçus et tokentx bruts | CONFIRMED sur ces fichiers, dès 18:43:51Z | evidence financial-links | aucune promotion de connaissance |
| Cypya 16 oct. et Snoorrason 14 oct. | texte du 16 soutenu ; cinq noms du 14 UNRESOLVED | syndication | CONFIRMED pour les textes courts ; long du 14 UNRESOLVED | `ballon_syndication_2026-11-08.json` | ne pas promouvoir le texte long |
| Rareté NO puis YES | non mesurée, pas de témoin | 733 autres, côtés relus | descriptif seulement ; pas de p-value | `feb28_market_trades.jsonl` | ne pas dire que le côté était inaccessible |
| Scanner gzip et chemins | correctif du matin partiel | 7 tests contre `ab7ca23` | CONFIRMED pour ces sept écarts | `test_correction_before_after.py` | CI |
| Couverture du scan Polygon | plage annoncée comme fermée | 53 logs entrants et 30 sortants concordants, mais 86 `failed_splits` non contextualisés | NON ÉTABLIE pour la couverture totale | `check_polygon_rpc_coverage.py`, 4 JSON originaux | produire un manifeste de balayage sans trous |
| Ancre de publication | garde-fou contourné par nouvelle ancre PR | politique et README restaurés depuis `main` ; test comparant la politique au `base_ref` | CORRIGÉ dans le workflow PR ; protection serveur à vérifier | `check_publication.py`, `test_publication.py` | maintenir l'ancre hors des PR ordinaires |
