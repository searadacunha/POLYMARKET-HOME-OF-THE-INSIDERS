# Audit forensique indépendant — 8 novembre 2026

Base revue après `git fetch origin main` : `ab7ca23d7824cdf65962c62a736364da27964ec4` (`fix(security): fail closed on incomplete gzip scans and enforce regression tests (#64)`, 2026-11-08 18:14:03 UTC). Le clone n'est pas superficiel. `origin/main` contient **218** commits, du `5c5e23ef` (2026-11-02 14:32 UTC) à cet HEAD. Les refs locales en contiennent **388**. **170** commits et **31** branches distantes ne sont pas dans `main` ; elles n'ont pas été relues ligne à ligne. L'arbre suivi de `main` compte **7 686** fichiers. Cet audit n'est pas une relecture exhaustive de chacun.

Aucune collecte, aucun TriAgent, aucun achat d'API. Les originaux d'archive ne sont pas réécrits. Les nouveaux fichiers bruts sont ajoutés sous `evidence/`.

Légende des sources, répétée à chaque conclusion matérielle : **RPC** = nœud public lu le 8 novembre 2026 ; **archive** = fichier déjà dans le dépôt ; **doc. externe** = page d'explorateur ou documentation ; **inférence** = jugement qui ne suit pas d'un seul de ces trois.

## A. Fiabilité et ce qui survit

Le dépôt sépare déjà plusieurs populations. Cette relecture confirme la séparation et resserre deux frontières qui étaient trop basses (reçus Base, identifiant d'ordre dans certaines transactions Polygon) et une qui était trop ouverte (le saut Arbitrum suivant n'est plus « non classé », mais ce n'est toujours pas un crédit client).

Ce qui survit comme relation financière observée, sans propriétaire ni information privilégiée :

- **38** proxys de trading distincts dans la cohorte Iran de février 2026 (**archive**, revérifié par `verify.py`).
- **36** créés du 22 au 25 février 2026, NO puis YES, premier YES le 27 février entre **20:49** et **23:35** UTC (**archive**, min/max recalculés sur `g38_accounts.csv`). Une date de création est vide ; un compte est daté du 1er novembre 2025. Ces deux-là ne sont pas dans les 36.
- **32** proxys envoient directement de l'USDC ou de l'USDC.e officiel, en **38** transactions (un portefeuille en envoie 5, un autre 3, les 30 autres une). La première passe n'en avait relu que 8 portefeuilles sur 32. La continuation relit les 38 transactions.
- **12** crédits Polygon Relay. Les montants atomiques sont uniques dans cet ensemble. **7** transactions exécutées contiennent l'identifiant d'ordre Relay (**RPC**). **5** ne le contiennent pas : le lien d'ordre est alors le hash fourni par Relay plus l'unicité du montant, pas une preuve de protocole dans l'input.
- **2** reçus Base confirmés en **RPC** sur deux points d'accès. L'identifiant d'ordre n'est dans aucune des deux transactions.
- **1** reçu Arbitrum confirmé en **RPC**. Le montant entier part ensuite vers `0xa656f7d2a93a6f5878aa768f24eb38ec8c827fe2`.
- Somme des résultats historiques arrondis au cent : **+1 576 522,86 USDC**, avec **8** comptes qui gardent des jetons de parts (**archive**). Ce n'est pas un profit réalisé, ni le seul marché Iran, ni un signal prédictif.
- Volume brut Polygon archivé : **chaque côté** (53 entrées, et séparément 24 sorties) vaut **1 984 038,168550** USDC/USDC.e. Ce n'est pas la somme débit+crédit, qui serait le double. Détail des entrées : 38 transferts directs = 1 509 327,186471 ; 12 crédits Relay = 474 710,981541 ; 3 poussières = 0,000538.
- **86** dépôts Relay d'entrée depuis **39** adresses, aucune réutilisée pour deux proxys de la cohorte (**archive**, contrôle du vérificateur exécuté ici).
- Le réseau Maduro/Iran à **8** comptes et le cluster E à **19** comptes n'ont **aucune** adresse en commun. Leurs résultats ne s'additionnent pas. L'arbre Railgun de **71** comptes (5 gains, 66 pertes) non plus.

Ce qui ne survit pas :

- « Il est démontré qu'un seul client Coinbase possède les 38 proxys ». Cet énoncé de démonstration n'est **pas établi**. L'absence de grand livre Coinbase, et le mélange des fonds après le saut Arbitrum, ne **réfutent** pas une propriété commune : elles la laissent **UNRESOLVED**. Une hypothèse de propriétaire commun reste une **HYPOTHESIS**.
- « Les deux routes Base n'ont pas de reçu de destination ». **REFUTÉ** au 8 novembre 2026 au soir. Les hash étaient déjà dans le snapshot Relay ; les reçus publics existent.
- « Le saut Arbitrum est une adresse non classée ». Trop faible. L'adresse est un EOA comminglé, nametag public Coinbase 26. Le classement ne dit pas quel client a été crédité.
- Toute p-value calculée après avoir choisi les gagnants. **Non estimable** ici. Aucune n'est rapportée comme découverte.
- Un vérificateur qui passe n'est pas une validation indépendante. Celui de G38 lit l'archive. Le rejeu RPC est une couche distincte, et il est partiel.

## B. Affirmations, une par une

### B1. Cohorte des 38

| Fait | Contrôle | Statut |
|---|---|---|
| 38 proxys uniques, même ensemble que `g38_resolved_proxies.txt` | `verify.py` sur l'archive | CONFIRMED, archive |
| 36 comptes du 22–25 février, `no_before_yes` vrai, premier YES `02-27` de 20:49 à 23:35 | recalcul CSV | CONFIRMED, archive |
| Le nom affiché `Anon` n'a pas de profil public servi | colonne `profile_served` | CONFIRMED comme absence de profil, pas comme identité |
| +1 576 522,86 et 8 comptes avec jetons ouverts | somme des `result` ; le vérificateur compare chaque ligne au ledger | CONFIRMED comme somme d'un indicateur historique, pas comme profit final |
| 86 dépôts, 39 financeurs, pas de financeur partagé dans cette table | vérificateur sur `g38_deposit_origins.csv` | CONFIRMED sur cette table. Les chaînes non lues restent ouvertes |

La synchronie NO→YES est réelle dans la cohorte sélectionnée après coup. Sans population de référence choisie sans regarder le profit ultérieur, la rareté n'est **pas estimable**. Statut de l'inférence « information privilégiée » : **HYPOTHESIS**, non testée.

### B2. Destinataire `0xc5bb1be0407db7312911ec765d399d02461e411a`

`eth_getCode` renvoie vide sur Polygon, Arbitrum et Base (**RPC**). Ce n'est pas un contrat de pool. L'archive Polygon montre les nonces signés 0 à 23 et des entrées de gas avant les sweeps. Comportement de dépôt : recevoir, puis envoyer. Ce comportement ne nomme pas l'exploitant.

Contrats officiels utilisés pour le brut : USDC Polygon `0x3c499c542cef5e3811e1192ce70d8cc03d5c3359`, USDC.e `0x2791bca1f2de4661ed88a30c99a7a9449aa84174`, tous deux à 6 décimales. Neuf événements d'autres contrats (jetons homoglyphes, USDT0, leurres) sont hors du brut. Trois poussières USDC.e, **538** unités atomiques au total, viennent de `0x98109e048aff6cc2d010813a26c192be6c4d7630` et `0x9817f7959431f5322d5a98488c04b18eda314630`. Elles imitent le préfixe et le suffixe du destinataire de sweep `0x9810762578accf1f314320cca5b72506ae7d7630`. Ce sont des empoisonnements d'adresse, exclus du groupe économique, **inclus** dans le brut. Statut : CONFIRMED sur l'archive. Ces trois hash n'ont pas été relus en RPC.

Le nombre **1 984 038,168550** est le total **de chaque côté**, pas le cumul des deux. Les 53 entrées officielles et les 24 sorties officielles somment chacun à 1 984 038 168 550 unités atomiques. La requête Etherscan archivée (`offset=1000`, **92** lignes de tous jetons, marqueur `DONE` `termination=END`, 2026-11-06) est sous le plafond de page. La marche `eth_getLogs` de la continuation dit si cette égalité tient encore hors de cette page.

Quatre destinataires de sweep sont des EOA (`eth_getCode` vide, **RPC**). Leurs nametags n'ont pas été rechargés dans cette session. Un financeur de gas, `0x660629fe43b0825acf3402e10a999c563075a32c`, porte sur Polygonscan le nametag public « Coinbase: Deposit Funder 3 », la page attribuant l'étiquette à la compilation hildobby (**doc. externe**). Ce n'est pas une attestation Coinbase. Les autres financeurs de gas de l'archive n'ont pas été re-étiquetés ici.

### B3. Les 12 crédits Polygon Relay, reçu et identifiant d'ordre

Les 12 montants sont uniques. L'unicité autorise un appariement par montant, elle ne prouve pas que l'ordre Relay est cette transaction. Deux classes :

**Identifiant présent dans l'input exécuté (7). RPC.** Quatre étaient déjà dans le calldata archivé. Trois n'avaient pas de calldata de fill dans le snapshot Relay ; le hash a été choisi parce que le montant n'apparaît qu'une fois dans les crédits USDC archivés, puis le reçu public a montré l'identifiant.

| UTC | Montant USDC | logIndex | tx | from du Transfer | order id dans l'input |
|---|---:|---:|---|---|---|
| 2026-01-05T01:13:39Z | 99,800270 | 260 | `0xb41628ce479bf020c588823249d80d5ac1e5e15738fba3dafd0057f450ef632f` | `0x56c26202…` | oui, calldata archivé = input |
| 2026-01-05T01:27:33Z | 9 995,375683 | 743 | `0x7a00c6805dfb5657f81db50870e6c09949b0b6a7a64afa2a3f784d1325c4f148` | `0xf5042e6f…` (contrat) | oui ; pas de calldata dans le snapshot |
| 2026-01-05T02:36:43Z | 229 926,513364 | 578 | `0xe07c2c4329c9194ae7fe66bd0afb20dcc6bd965ef8782f930322ba20d1e6fd25` | `0xf5042e6f…` | oui ; pas de calldata dans le snapshot |
| 2026-01-06T00:23:49Z | 3 004,254940 | 1785 | `0xf987d8c9d9cf0bf1ccf13353c7de2d89607c3bd30b13159243e3006735e9c9b7` | `0xf5042e6f…` | oui ; pas de calldata dans le snapshot |
| 2026-02-22T09:59:08Z | 19 106,086041 | 879 | `0xefb3f7e2a65ba9866bcc7a170674a9b90ea0a98963cd0f43896f2c7b85cf2776` | `0xf70da978…` | oui, et le reçu concorde aussi sur Tenderly |
| 2026-02-24T08:47:52Z | 20,976304 | 281 | `0x7a23be65042cd2c9d4de93eb5d62d47fcae557b80f503dc5633fda4e810057f5` | `0xf70da978…` | oui |
| 2026-02-24T08:53:46Z | 99 090,130751 | 540 | `0x764a686c1d2f26389be2d76dbf5822fbb1781236948fbe55e7277f6448726dab` | `0xf70da978…` | oui |

Contrat : USDC Polygon `0x3c499c…3359`, chaîne 137, statut 1, `to` du Transfer = le destinataire. Statut : **CONFIRMED, RPC**, pour le crédit et pour la présence de l'identifiant.

**Identifiant absent de l'input (5). RPC pour le reçu, archive Relay pour le lien d'ordre.** Le calldata archivé égale l'input, le montant est unique, le hash vient du champ `outTx.hash` du snapshot. Le mot supplémentaire dans certains `transferFrom` n'est pas l'identifiant d'ordre et n'est pas son SHA-256.

| UTC | Montant | logIndex | tx |
|---|---:|---:|---|
| 2026-02-22T09:45:26Z | 4,988487 | 1384 | `0x452aeea2e505defffd643252dc7ea9366031c51578c7c224f8114e28a9ccd25e` |
| 2026-02-22T10:03:44Z | 9,986706 | 374 | `0xd78c0265863bc8044e8255645fdbe349f288f2b41a956b9a26ed7d02c9463421` |
| 2026-02-22T10:18:26Z | 57 673,995459 | 331 | `0x46f18ad88bf752620cd78c7aed0bafd291def17e2075d7e88b83ea9c1031ac62` |
| 2026-03-02T08:25:49Z | 4,991204 | 852 | `0x3af69e444d4c7dab69d54f1dd2327cf127f1366c87749bd57ee2b73588f1dd70` |
| 2026-03-02T08:41:07Z | 55 773,882332 | 498 | `0xcabc1a89e1506b11b2d04917d1c28c90272d44ebb6146d5d449c9265fc68ed0c` |

Statut du **reçu** : CONFIRMED, RPC. Statut du **lien à l'ordre** : SUPPORTED (métadonnée du fournisseur + égalité de calldata + montant unique). Pas CONFIRMED comme provenance protocolaire.

Les expéditeurs du Transfer ne sont pas les proxys. `0xf70da978…` et `0x56c26202…` sont des EOA (inventaire de solver, infrastructure partagée). `0xf5042e6f…` est un contrat de 8 925 octets (règlement Relay). Aucun n'est un paiement de compte à compte entre proxys. Un doublon de **1 000 USDC.e** existe dans les entrées directes (`0x4392a6b4…` et `0x703405ba…`, deux proxys de la cohorte). Il ne touche pas les 12 montants Relay, qui restent uniques. L'appariement global par montant, sans séparer les expéditeurs, serait ambigu. Le vérificateur sépare d'abord la cohorte.

### B4. Base

Les deux hash étaient dans le snapshot Relay, pas dans un archive Basescan. Reçus publics, statut 1, USDC Base `0x833589fcd6edb6e08f4c7c32d4f71b54bda02913`, Transfer depuis `0xf70da978…` vers le destinataire. Deux RPC : `https://mainnet.base.org` et `https://base.drpc.org`.

| UTC | Montant | bloc | logIndex | tx | order id dans l'input |
|---|---:|---:|---:|---|---|
| 2026-03-02T09:27:45Z | 58 475,748639 | 42827159 | 772 | `0xf964594781fef3f963893b49e5d2d74cf425a83b3b956ee3348d128842b4c2bb` | non |
| 2026-03-02T09:36:51Z | 42 142,977084 | 42827432 | 452 | `0x898c9724b990a87632b043331aa2142536868ac6a66d9d7d911eaaa73e28af21` | non |

Statut du reçu : **CONFIRMED, RPC**. Statut du lien d'ordre : **SUPPORTED** par le snapshot Relay. Statut « crédit Coinbase » : **UNRESOLVED**. `https://base.llamarpc.com` a répondu 403 ; ce n'est pas une absence de transaction.

### B5. Arbitrum, puis la suite

Reçu : `0x00e110ffb3fc34c319b7c32b2597b69b9fb7ce6292aba5527b3e670daacb16f9`, bloc 437513468, 2026-03-02T09:51:36Z, logIndex 68, 59 863,534997 USDC (`0xaf88d065e77c8cc2239327c5edb3a432268e5831`), depuis `0xf70da978…`. Concordance `https://arb1.arbitrum.io/rpc` et `https://arbitrum-one.public.blastapi.io`. L'identifiant d'ordre n'est pas dans l'input. Statut du reçu : CONFIRMED, RPC. Lien d'ordre : SUPPORTED.

Sortie suivante : `0x51ba878477e317b5d41643b57b5c5923c36f8d0540e402651dca397533a00fec`, bloc 437514401, 2026-03-02T09:55:28Z, logIndex 4, même montant, vers `0xa656f7d2a93a6f5878aa768f24eb38ec8c827fe2`. Code vide : EOA. Sur les 200 000 blocs suivants, **122** Transfers USDC partent de cette adresse, somme **1 042 735,384784** USDC, vers de nombreuses destinations dont `0xd0d08887e8a5b16049534a7f3fc1de92848f5bea` pour des montants de l'ordre de 60 000 à 110 000. Le solde USDC lu ensuite était encore **68 682,747291**. L'adresse mélange des fonds. On ne peut pas suivre les 59 863,534997 comme une pièce identifiée.

**Doc. externe :** Etherscan et Blockscan affichent le nametag « Coinbase 26 », attribué sur la page à la compilation hildobby. Ce n'est pas un relevé Coinbase. Le comportement (EOA, nombreuses sorties, solde résiduel) **soutient** l'hypothèse d'une adresse d'infrastructure qui mélange des fonds. Il ne démontre pas le crédit d'un client identifié, et il ne démontre pas non plus que les 38 proxys n'appartiennent pas au même client. Propriété commune : **UNRESOLVED**. Crédit d'un client nommé : **UNRESOLVED**.

### B6. Autres dossiers, avec le dénominateur

**Huit comptes Maduro/Iran.** Somme recalculée sur `pnl_table.json` pour les huit adresses de `accounting_audit_2026-11-04.json` : 509 993,244904, soit **509 993,24** après arrondi du total. L'intersection avec les 19 adresses `cluster E network` est vide. L'intersection avec les 71 proxys Railgun est vide. Le PnL est un indicateur de ledger (achats, ventes, rachats, valeur courante), pas le flux externe. Les titres 151 084,40 et 660 708,94 n'ont pas été reconstruits ligne à ligne ici : ils restent au statut d'archive antérieur, non promus.

**Cluster E, 19 comptes.** Le fichier `accounts.csv` a 25 lignes : 19 dans le réseau, 4 et 2 dans des groupes de test de rareté explicitement non liés. Les paiements directs et les dépôts d'échange partagés sont des types d'arêtes différents. Cette session n'a pas redécodé les 1 100 reçus. Statut des arêtes directes déjà tabulées : CONFIRMED comme lignes d'archive. Propriétaire unique : HYPOTHESIS.

**Inca.** `TheOneWhoKnocks1312` (`0x6c2c072a…`) et `DonkeyDonkey999` (`0xcb18ea29…`) sont dans les 19. Le PDF Inca n'est pas dans le dépôt : l'affirmation « 2 des 5 comptes publics d'Inca » n'a pas été relue sur la source externe. Statut : SUPPORTED par le rapport de recoupement du dépôt, **UNRESOLVED** contre le document Inca lui-même. Les sorties `ricosuave666` / `AugsburgFClover` / `metushelah` n'ont pas été redécodées. Un identifiant d'ordre deBridge est un lien de protocole ; un montant égal à la même heure ne l'est pas. Cette distinction est déjà dans la méthode. Elle n'a pas été rejouée transaction par transaction ici.

**Pulser, cashy, Car.** Recalcul indépendant sur les **7 596** lignes de `flows.csv` : un match exige retrait et dépôt, contreparties croisées, écart de temps ≤ 1 s, écart d'USDC < 0,000002, au plus un candidat par hash. Résultat : **27** hash, **0** ambigu, volumes 10 757,999999 et 2 692,00 (cashy ↔ Pulser), 250 (cashy → Car), 1 000 (paire témoin séparée), total **14 699,999999**. Le vérificateur du dossier passe sur les mêmes règles. Ce volume est un transfert, pas un profit. Les cinq portefeuilles sont dans la cohorte témoin de juin 2025. Aucune p-value. Statut : CONFIRMED sur l'extrait gelé, pas sur l'univers Polymarket.

**KPMG.** Les 14 lignes du CSV portent des hash, des logIndex et des montants. Le rejeu RPC est dans la section de continuation : il ne faut pas le confondre avec un audit du plan statistique. La fonction `tail` du vérificateur est une somme de Poisson-binomiale sur les `p_i` déjà stockés. L'exécuter reproduit le chiffre archivé ; ce n'est pas une reconstruction indépendante du plan (sélection du groupe, dépendance des marchés, définition des prix, corrections multiples). L'inférence « ce calcul démontre une information privilégiée » n'est **pas soutenue** par ce que j'ai inspecté. Je ne marque pas le test arithmétique **REFUTED** : je ne l'ai pas contredit par un autre calcul.

**Railgun / Venezuela.** 71 proxys, 5 `won=True`, donc 66 pertes, intersection vide avec les huit. L'équation de clôture 22 044,16 n'a pas été re-sommée sur les logs dans cette session : elle reste un résultat d'archive antérieur, non promu au-delà. L'arbre de financement n'est pas la preuve que 71 personnes connaissaient une date. Les 66 pertes sont le contrôle négatif déjà dans le dossier.

**Ballon d'Or.** La bande des 692 519 lignes et les objets X hors git n'ont pas été réagrégés. Les hypothèses déjà rejetées dans `FINDINGS.md` (lien unique, financement dans l'heure, rachat groupé comme signal, ChangeNOW comme lien privé) restent des négatifs d'archive. Un fill maker date l'appariement, pas la soumission de l'ordre. Statut « délit d'initié » : UNRESOLVED. Je ne recalcule pas de probabilité.

**ChangeNOW et Privacy Cash.** Une étiquette ou un paiement de service n'est pas une relation client. Aucun lien cryptographique entrée/sortie n'a été établi dans cette session, et le dépôt dit déjà qu'il n'y en a pas. Statut du lien ZK : non montré. Je n'ai pas rouvert les racines Merkle.

## C. Preuves nouvelles

Fichiers ajoutés, sans écraser les originaux :

- `evidence/g38_rpc_replay_2026-11-08.json`, SHA-256 `14298e5a6ab297247fc77a995ec74411ebc8c06e3d588144870a780427ac812a`
- `evidence/arbitrum_onward_usdc_outs_200k.json`, SHA-256 `18d337978062ddd0bcee5acf85e3ffc6bf76a6b8049b6522bb8ed1479de733d9`

Nouveauté par rapport à l'archive connue :

- `logIndex`, `blockHash`, statut et horodatage de bloc pour les 15 fills et pour la sortie Arbitrum, lus sur un nœud, pas recopiés depuis Etherscan.
- Preuve que l'identifiant d'ordre est **dans** l'input de 7 transactions Polygon, dont 3 dont le snapshot Relay n'avait pas le calldata.
- Preuve que l'identifiant est **absent** de 5 inputs Polygon, des 2 inputs Base et de l'input Arbitrum, alors que le mot supplémentaire du calldata n'est pas cet identifiant.
- Reçus Base sur deux RPC. Ils n'existaient pas comme archive d'explorateur.
- Fenêtre de 122 sorties USDC de l'adresse suivante, qui montre le mélange.
- Premier échantillon : 8 portefeuilles sur 32, pas 8 transactions sur 38. La continuation couvre les 38 transactions.

Ce qui n'est pas nouveau : les hash de fill Base et Arbitrum étaient déjà dans `outTx.hash`. Le travail nouveau est de les avoir lus sur la chaîne et d'avoir séparé le reçu de l'identifiant d'ordre.

Commande de rejeu, sans clé : `eth_getTransactionByHash`, `eth_getTransactionReceipt`, `eth_getBlockByNumber`, `eth_getCode`, `eth_getLogs`, `eth_call` balanceOf. Points d'accès qui ont répondu : `https://polygon.drpc.org`, `https://gateway.tenderly.co/public/polygon` (un reçu), `https://mainnet.base.org`, `https://base.drpc.org`, `https://arb1.arbitrum.io/rpc`, `https://arbitrum-one.public.blastapi.io` (un reçu). Refus ou vide, sans conclure à l'absence de transaction : `polygon-bor-rpc.publicnode.com` 403, `polygon-rpc.com` 401, `rpc.ankr.com/polygon` clé exigée, Blockscout 403, Routescan 400, `base.llamarpc.com` 403. Aucune API payante.

## D. Finances reconciliées

| Mesure | Valeur | Périmètre | Statut |
|---|---|---|---|
| Somme des `result` au cent | +1 576 522,86 USDC | 38 ledgers historiques, 8 avec jetons ouverts | archive, recalculée |
| Brut entrées = sorties Polygon | 1 984 038,168550 | USDC + USDC.e officiels, fenêtre archivée, poussières incluses | archive, pas RPC intégral |
| 12 crédits Relay Polygon | somme des 12 montants appariés | pas le PnL | RPC reçu par reçu |
| 2 crédits Base | 58 475,748639 et 42 142,977084 | reçus de destination | RPC |
| 1 crédit Arbitrum | 59 863,534997 | puis mélange | RPC |
| Huit comptes | +509 993,24 | autre population, autre fenêtre | recalcul JSON |
| Pulser/cashy/Car | 14 699,999999 de transferts | pas un profit | recalcul des 7 596 lignes |

Les frais de gas des sweeps ne sont pas dans le brut USDC. Les positions ouvertes ne sont pas marquées au marché ici. Aucune déduplication n'ajoute la cohorte 38 au réseau 8, au cluster 19 ou à l'arbre 71 : les intersections calculées sont vides pour 8∩19 et 8∩71. Le cluster 19 n'a pas été intersecté avec les 71 dans cette session.

Le +1 576 522,86 est la somme des champs `result` déjà arrondis au centime dans le CSV. La somme non arrondie des `trading_result` du ledger est 1 576 522,861036. Ce n'est pas une réconciliation portefeuille par portefeuille des fills bruts. Le ledger archivé n'a pas de colonne de frais. Huit comptes ont des quantités de parts ouvertes, non réévaluées ici. Les retraits archivés (2 188 286,456614) moins les dépôts archivés (567 775,221686, clé absente pour 4 comptes et alors comptée 0) font 1 620 511,234928. L'écart avec le résultat de trading n'est pas expliqué par une audit de frais : il est laissé comme écart entre deux sommes d'archive.

## E. Contrôles, sélection, signification

La cohorte 38 est rétrospective. Le trait NO-puis-YES est mesuré sur les comptes déjà retenus. Il n'y a pas de témoins ordinaires tirés sans regarder le profit, pas de holdout chronologique, pas de placebo de fenêtre. **La signification n'est pas estimable.** En calculer une maintenant serait une p-value après sélection. Elle n'est pas dans ce rapport.

Le seul contrôle négatif quantitatif recalculé ici est interne aux données gelées : 27 transferts Pulser dans une cohorte témoin, et 66 comptes perdants dans l'arbre de 71. Ils montrent que des paiements directs et un financement commun existent sans qu'on puisse en faire un classificateur d'initié. Ils ne donnent pas un taux de base pour la cohorte 38.

Les p-values KPMG et Ballon d'Or déjà publiées restent des calculs conditionnels à la sélection. Ce rapport ne les répète pas comme résultats.

## F. Code, défauts, correctifs, surfaces non testées

Défauts reproduits avant correction, puis corrigés :

1. **Commentaire gzip non lu.** Un jeton au format GitHub dans le champ FCOMMENT, corps innocent, donnait `audit_public_repository.check() == 0`. `gzip.open` ignore FNAME, FCOMMENT et FEXTRA. Correctif : `phi_lib.gzip_header_text` n'extrait que ces champs, en clair, et les ajoute au buffer scanné. Le flux déflaté n'est pas scanné comme du texte, pour éviter les faux positifs binaires. 352 fichiers `.gz` du dépôt ont un FNAME ; le scan complet après correctif reste à 0 alerte.
2. **Suffixe `.GZ` et plafond.** `inspect_stream` testait `.gz` sensible à la casse. Un fichier `JSON.GZ` au-dessus du plafond passait. Le test de décompression, lui, utilisait déjà `.lower()`. Correctif : même test insensible à la casse. `read_for_scan` décompresse aussi `.GZ`, ce qui ferme le trou d'import où un secret seulement visible après décompression n'était pas vu.
3. **`zlib.error` non capturé.** Un membre gzip au bloc stocké invalide faisait sortir le processus au lieu d'un refus par fichier. Capturé dans le scan public, l'import et `validate_evidence`.
4. **Citation numérique par sous-chaîne.** `1000` passait si la source contenait `21000` ou `0xabc1000def`. Correctif : frontières de chiffres, et les jetons `0x…` sont retirés avant la recherche. Un `1000` isolé passe encore. `validate_evidence.py` sur le dépôt réel : 0 erreur.
5. **`sources/../` échappait le dossier d'enquête.** Refusé.
6. **`restore_stream` écrivait `dest/root/rel` sans contenir le chemin.** Un `rel` `../escaped-file` sortait de la destination. Refusé, fichier non écrit. Les liens symboliques du même index passent par le même contrôle.
7. **Le vérificateur G38 ignorait les marqueurs `DONE`.** Une page manquante pouvait ressembler à la fin. Il exige maintenant `termination == END`, des pages contiguës et le nombre de lignes annoncé, pour le destinataire (tokentx, txlist, txlistinternal Polygon, tokentx Arbitrum) et pour les six dossiers Relay utilisés. Il fige aussi la partition calldata : 4 ordres dont le calldata contient l'identifiant, 8 dont le calldata ne le contient pas, 3 sans calldata de fill. Un ordre étranger est rejeté par `test_verify.py`.

Le test du commentaire gzip, le test `.JSON.GZ` et le test `zlib.error` échouaient sur le code d'arrivée (deux assertions fausses, une exception). Ils passent après correctif.

**Preuve sur l'ancre de publication, sans correctif.** `verify()` compare les chemins listés dans l'objet politique qu'on lui donne. Appel réel sur cet arbre : politique dont `commit` est `ab7ca23d7824cdf65962c62a736364da27964ec4` et dont `protected_paths` ne contient que `research_notes/relay-followup-2026-11-04/`. Résultat : succès, `protected_files` = 13. Les blobs README diffèrent pourtant (`ab7ca23:README.md` = `29cd673d7cf0dc0ad3d6fe8fac59b40a500d77ed`, `HEAD:README.md` au moment du test = `9e4ee9919af32dc86cdbb40f8ff01a5396eb95b8`). Avec la politique du dépôt, le même appel protège 14 fichiers et réussit aussi, parce que le README de HEAD est celui de l'ancre `0658ab3`. Le trou observé est donc : la liste des chemins et l'ancre viennent du JSON lu par le script du candidat. Aucun contournement n'a été « réparé » ici. Le garde-fou reste celui qui refuse un README modifié tant que l'ancre et la liste ne sont pas elles-mêmes changées.

**Tests avant/après, un par correctif.** `python3 -m unittest scripts.test_correction_before_after -v` charge les modules de `ab7ca23` et ceux du HEAD. Les sept tests passent, et chacun montre l'ancien échec : commentaire gzip accepté (code 0) puis refusé ; `.JSON.GZ` au-dessus du plafond accepté puis refusé ; `zlib.error` qui sortait du processus puis devient un refus par fichier ; `1000` contenu dans `21000` et dans `0xabc1000def` accepté par l'ancien `in`, refusé par `number_in_text` ; `sources/../FINDINGS.md` lu par l'ancien `check_findings` (le nombre 99999 était dans le fichier ainsi atteint) puis rejeté ; `restore_stream` écrivait `dest/../escaped-file` puis renvoie `(0, 1)` sans écrire ; `fetch_rows` de l'ancien G38 rendait une page sans marqueur `DONE`, `require_etherscan_complete` lève `AssertionError`. Ce n'est pas seulement les trois tests gzip du premier passage.

`validate_evidence.py` sur le dépôt après le resserrement numérique : 0 erreur. Un `1000` suivi de `.50` reste encore reconnu, parce que le point n'est pas un chiffre. Cette limite est notée, pas élargie en silence.

Surfaces non retestées de bout en bout : restauration réelle depuis le disque externe, collecteurs, workflows GitHub sur ce PR au moment de l'écriture, décodage Solana, bande Ballon d'Or, scripts de phases 4 à 15 de Maduro. `audit_public_repository.py` sur les 7 686 fichiers : 821 AST Python, 4 422 scans, 0 gzip incomplet, code de sortie 0.

## Continuation du 8 novembre 2026 au soir

Horodatages UTC des lectures, pas une seule horloge pour tout.

### Directs : 38 transactions, 32 portefeuilles

`evidence/g38_direct_receipts_2026-11-08.json`, SHA-256 `a4e15dbcb4848cadb498cc1a969f16d2abfd18c7a63f81d6813acc373ca76450`. RPC `https://polygon.drpc.org` avec repli Tenderly. **38/38** reçus : statut 1, bloc égal à l'archive, un log Transfer dont from, to, contrat et montant atomique égalent la ligne. **32/32** portefeuilles ont au moins une de ces transactions. Le premier texte disait 8/38 : c'était 8 portefeuilles sur 32, et il y a 38 transactions parce que `0xf37af11e…` en envoie 5 et `0xc0292a84…` en envoie 3. Ce n'est pas « chaque portefeuille testé » tant que le compte n'est pas 32.

### Journaux Polygon, fenêtres bornées

Fin de fenêtre lue : bloc **96 974 221**, `eth_blockNumber` le **2026-11-08T19:39:47Z**. Balayage continu de **81 100 000** à ce bloc, pas de 20 000, quatre filtres (USDC et USDC.e, topic1 et topic2 = le destinataire). Les coupures RPC sont redivisées ; le compte `failed_splits` compte ces redivisions, pas des trous laissés ouverts. Des sondes de 2 000 blocs tous les 1 000 000 depuis le bloc 70 000 000 étaient vides : ce n'est **pas** un balayage continu avant 81 100 000.

Résultat, dédupliqué par hash et logIndex, comparé à la page archivée :

| Filtre | Logs positifs | Somme atomique | Écart avec l'archive |
|---|---:|---:|---|
| USDC vers le destinataire | 12 | 474 710 981 541 | aucun |
| USDC depuis le destinataire, valeur > 0 | 6 | 474 710 981 541 | aucun |
| USDC depuis le destinataire, valeur 0 | 6 | 0 | absents de l'archive parce que la somme ne gardait que `value > 0` ; destinataires homographes des vraies adresses de sweep |
| USDC.e vers | 41 | 1 509 327 187 009 | aucun des 41 hash |
| USDC.e depuis | 18 | 1 509 327 187 009 | aucun |

41 + 12 = 53 entrées. 18 + 6 = 24 sorties de valeur positive. Chaque côté positif = **1 984 038 168 550**. Le solde `balanceOf` des deux contrats au bloc courant est **0**. Aucun transfert de valeur positive n'apparaît après le dernier bloc archivé (83 968 639) jusqu'à 96 974 221. Fichiers : `polygon_logs_USDC_from.json` `64168f0b8efe0ebdc7530478cfe44e9b3133da88394b2fd95421b26f8693c554`, `polygon_logs_USDC_to.json` `df60873269a59b98a157794ba6c02fd2475c8107c9aaefa79defa563738f44f4`, `polygon_logs_USDCE_from.json` `969298640e2e6b1b966b69e0280e15a251a099c4ecbc793e48e90ffaba014a0a`, `polygon_logs_USDCE_to.json` `ce9e6e19a55a7eae7462d897b201c163c7886d822498b69fa7fcff7a5b09bc96`.

### Matrice 38 / 8 / 19 / 71

Intersections d'adresses, recalculées : **toutes vides**. Les cinq adresses du PDF Inca : deux sont dans les 19 (`0x6c2c072a…`, `0xcb18ea29…`), aucune dans les 38, les 8 ou les 71.

### Inca, source publique

PDF téléchargé le 8 novembre 2026 depuis `https://drive.google.com/uc?export=download&id=1tesSlK0kHOU9vm6VtMf1QRS8VO2ah-Yz`. SHA-256 **`2b14e2874ff26712db5e85a3fcbb5c1c3c425c91671245bc9b34be892141d38b`**, 30 pages, identique au hash déjà cité. Le texte extrait contient les cinq adresses et les profits 36 790,56 ; 85 120,83 ; 128 736,79 ; 34 996,87 ; 52 329,69. Le PDF n'est pas commité : le dépôt le traite comme contenu tiers. Quatorze transactions Polygon de `EVIDENCE_INDEX.csv` ont un reçu statut 1 (`inca_polygon_receipts_2026-11-08.json`, `e143e5800e33bda7fc1b79655d681497fa0b73e21192425800179ed3418ac6e9`). Les jambes Solana et les ordres cross-chain de cet index n'ont pas été rejoués une par une dans cette continuation : 25 lignes restent au niveau de l'index.

### KPMG

28/28 reçus Polygon : statut 1, bloc égal, un log USDC.e du montant et du logIndex archivés (`kpmg_polygon_receipts_2026-11-08.json`, `a07bbe031a2413307e982d9d987acb51493608511fe3101b1d9ec374a4df9ab1`). 28/28 signatures Solana existent sur `https://api.mainnet-beta.solana.com` et `meta.err` est null (`kpmg_solana_receipts_2026-11-08.json`, `b08c75fb69f1c833a99bd82f7cc710a000353006e5f36a3bde04f60641e69107`). Je n'ai pas recalculé le delta de jeton Solana dans cette passe : l'existence du reçu n'est pas le montant. Le vérificateur du dépôt, exécuté ici, refait sa fonction `tail` sur les `p_i` stockés et sort 0. L'inférence d'information privilégiée n'est pas soutenue. Le test arithmétique n'est pas marqué réfuté.

### Railgun, logs bruts déjà dans le dépôt

Six reçus `polygon_receipt_*.json` : le montant décodé dans le data du log `0xd93cf895…` égale `amount_atomic`, logIndex égal, frais / (montant + frais) = 0,0025. Somme **22 044,160154** USDC. Six distributeurs : entrées = sorties = cette somme, **384** enfants. Vers les solveurs Relay **21 977,513862**, résiduel **66,652297**, poussière extérieure **0,006005**, fuite de valeur ≥ 0,01 vers l'extérieur du graphe : **0**. Équation `to_relay + résiduel − poussière = unshield` vraie sur ces fichiers. Aucun `p2` dans cet archive. Le premier unshield du CSV est **2025-12-16T18:43:51Z** (`0x907336f0…`, 3 782,52), avant 18:54. 71 comptes, 5 `won=True`. Ce n'est pas une preuve que 71 personnes connaissaient une date.

### Ballon d'Or, texte public

Snowflake : `2110285369748963671` → **2026-10-14T08:23:34Z** ; `2111149784858042762` → **2026-10-16T17:38:26Z**. Le même horodatage est dans le JSON public `cdn.syndication.twimg.com` lu le 8 novembre 2026 (`ballon_syndication_2026-11-08.json`, `34e00a45b3fd7c52ff212e4b9c2b038a0fd90bfbbb21a5b73aae617c9106a2b4`). Le texte Cypya contient, dans l'ordre, Kane, Mbappé, Yamal, Rodri, Messi. Le texte Snoorrason visible (304 caractères) ne liste pas ces cinq noms ; il parle d'un achat de 66k shares. Cela confirme le statut déjà écrit : top cinq du 16 octobre lisible, top cinq complet du 14 octobre non présent dans ce texte court. Un fill maker ne date pas la pose de l'ordre. Pas de probabilité d'initié.

### Population sans regard sur le profit

API publique `data-api.polymarket.com/v2/trades?condition=0x3488f31e6449f9803f99a8b5dd232c7ad883637f1c86e6953305a2ef19c77f20`. La v1 répond 410 (« retired »). Le paramètre `market` en v2 est refusé ; `condition` est accepté. `offset` en query est refusé ; le curseur `next_cursor` fonctionne. 84 pages de 500, du **2026-02-28T09:32:33Z** jusqu'avant le **2026-02-22** (plus ancien trade lu **2026-02-21T18:48:58Z**), **13 003** proxys. Les champs nom, pseudonyme et bio n'ont pas été enregistrés. `createdAt` via `gamma-api.polymarket.com/public-profile` : **11 741** réponses, le reste en HTTP 404 sur un échantillon de 8 et sur le second passage. Parmi les profils obtenus, **769** ont un `createdAt` le 22, 23, 24 ou 25 février 2026, dont **36** sont la cohorte (les dates gamma reproduisent 18 / 11 / 4 / 3). Il reste donc **733** autres comptes créés ces quatre jours et présents dans cette bande. Deux proxys de la cohorte de 38 ne sont pas dans la bande. La séquence NO puis YES **n'a pas** été mesurée sur les 733 : les lignes de trades n'ont gardé que le compte et les timestamps extrêmes, pas le côté. La signification de cette séquence reste **non estimable**. Aucune p-value n'est calculée. Fichiers : `control_population_summary.json` `b27586ce3910fe5a67f2815aebddb5022f557c073d4f62ddaf5af3776559c543`, `feb22_25_traders_createdAt.csv` `7e145d5fc427aee8513fc828022c58bf508e5479e0f766ce4237dcb89560b303`.

### Histoire des 218 commits

Stratégie, pas une lecture ligne à ligne de chaque diff : `git log --reverse` des 218 sujets de `5c5e23ef` (2026-11-02) à `ab7ca23` ; historique des chemins `phi_lib.py`, `audit_public_repository.py`, `import_snapshot.py`, `validate_evidence.py`, `check_publication.py`, `publication_baseline.json`, `phi_backup.py`, `phi_repo.py`, le workflow CI ; pickaxe `-S` pour `BEGIN RSA PRIVATE KEY`, `BEGIN OPENSSH PRIVATE KEY`, `AKIA`, `github_pat_`, `ghp_`, `xoxb-`. Aucun bloc de clé privée. Les occurrences de `AKIA`, `github_pat_` et `xoxb-` encore dans `origin/main` sont des motifs de scanner ou un motif du même genre dans `build_publication.py` : le caractère qui suit le marqueur est un métacaractère de regex, pas un jeton. Aucune valeur n'est recopiée ici. Les 170 commits hors `main` ne sont pas lus.

### Vérificateurs du workflow

Tous les pas de `.github/workflows/repository-integrity.yml` ont été lancés le 8 novembre 2026, journal `/tmp/audit-cont/verifiers.log`, et ont fini avec **EXIT 0**, y compris ChangeNOW, C1/C5/C7, Iran/Inca/Pulser, Relay du 4 novembre, X, KPMG/Railgun offline, `validate_evidence` (0 erreur), `build_master_report.py --check`. Rien n'a été sauté dans cette liste. Non lancés, et pourquoi : collecteurs réseau du dépôt (interdits), restauration depuis le disque externe (absent), administration GitHub des branches protégées (pas d'API d'admin utilisée).

`x-history` `verify.py`, lancé sans l'archive brute locale, réécrivait `verification.json` : les contrôles B1 et B2 enregistrés devenaient un seul `B* SKIPPED` tout en sortant 0. Le fichier a été restauré à ses octets d'origine. Le script garde désormais ces contrôles enregistrés quand l'archive brute est absente, au lieu de les remplacer par le saut.

## G. Fichiers, commandes, rôles des commits

Ne pas appeler `0658ab3` le rapport final. Rôles :

| SHA | Rôle |
|---|---|
| `ab7ca23d7824cdf65962c62a736364da27964ec4` | `main` relu, base du PR |
| `0658ab3ad326763f92a83250bacd19e9c39de7e6` | premier correctif, premier rapport, octets README. L'ancre de publication pointe ici |
| `2281a9e745ca3e9c9768086097ecf6dd10c63cb1` | n'ajoute que le JSON d'ancre |
| `34d502692a1a95bed5556c3aafb7523948600607` | tête précédente ; n'ajoutait que l'URL de PR dans le premier rapport |
| `87d3fd395f244f5725f23c1909b3118ec0063c2c` | texte corrigé, preuves, tests avant/après. La tête du PR est le premier descendant de ce commit sur cette branche ; il ne fait qu'enregistrer cette ligne |

PR : https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/65. Pas de merge.

Nouveau test : `scripts/test_correction_before_after.py`, appelé par le workflow. Preuves : `evidence/SHA256SUMS` et les fichiers nommés ci-dessus. Les deux JSON du premier passage sont conservés.

## H. Ce qui reste ouvert

1. Création inconnue pour les proxys sans profil public (HTTP 404). Le 769 est un plancher parmi les profils, pas l'univers.
2. Séquence NO puis YES sur les 733 autres comptes : non mesurée. Signification non estimable.
3. Delta de jeton des 28 transactions Solana KPMG, et les 25 jambes non Polygon de l'index Inca.
4. Balayage continu avant le bloc 81 100 000. Les sondes de 2 000 blocs ne le remplacent pas. Le solde actuel 0 et l'égalité de la fenêtre lue rendent un flux positif manqué avant cette fenêtre moins probable, pas impossible.
5. Quatre adresses de sweep et les financeurs de gas autres que `0x660629fe…` : pas de seconde source d'étiquette.
6. Grand livre Coinbase. La propriété commune reste UNRESOLVED.
7. Texte long du post du 14 octobre, au-delà des 304 caractères publics.
8. 170 commits hors `main`, disques du 4 novembre, protection de branche côté serveur.

## Matrice de couverture

| Zone | Fait dans cette continuation | Limite restante |
|---|---|---|
| 218 commits de `main` | sujets, chemins de sécurité, pickaxe sans impression de secret | pas chaque ligne de diff ; rien hors `main` |
| 38 transactions directes / 32 portefeuilles | 38/38 reçus | pas les dépôts d'entrée des 86 ordres |
| Logs Polygon du destinataire | continu 81 100 000–96 974 221, quatre filtres, dédup | avant 81 100 000, sondes seulement |
| 38/8/19/71 | intersections vides | flux externes 151k/660k non reconstruits |
| Ledger 38 | sommes des champs archivés | pas une réconciliation fill par fill ; pas de colonne de frais |
| Inca | PDF hash égal, cinq adresses, 14 reçus Polygon | 25 jambes non Polygon |
| KPMG | 28 reçus Polygon, 28 signatures Solana | delta SPL non recalculé ; plan statistique non audité en profondeur |
| Railgun | équation sur les JSON bruts | pas un nouveau RPC |
| Ballon | snowflake + texte syndication des deux posts | pas la bande de 692 519 fills |
| Témoins | 769 créés les 22–25 fév. dont 36 de la cohorte, dans la bande lue | séquence NO/YES non mesurée ; 404 sans date |
| Suite du workflow | EXIT 0 sur chaque pas | collecteurs et disque externe non lancés |

## Tableau de décision

| Affirmation | Statut antérieur dans le premier texte de ce PR | Contrôle | Statut corrigé | Preuve | Action |
|---|---|---|---|---|---|
| 38 proxys | CONFIRMED archive | CSV + gamma `createdAt` pour 36 | CONFIRMED | CSV et profils publics | aucune |
| +1 576 522,86 | présenté comme ledger vérifié | somme des champs, pas des fills | somme d'archive, pas un audit comptable complet | `ledger_g38.json` | ne pas dire audit portefeuille par portefeuille |
| 32 directs | 8/38 dans le premier texte | 38 reçus, 32 portefeuilles | CONFIRMED RPC 38/38 et 32/32 | `g38_direct_receipts_2026-11-08.json` | corriger le dénominateur |
| 12 Relay, order id | 7 dans l'input, 5 non | inchangé | inchangé | premier JSON RPC | aucune |
| Base | reçus confirmés | inchangé | CONFIRMED reçu, lien d'ordre SUPPORTED | deux RPC | aucune |
| Arbitrum ensuite | nametag et mélange | inchangé | infrastructure SUPPORTED ; propriété UNRESOLVED | logs 200k | ne pas écrire REFUTED |
| Un seul client Coinbase | le premier texte disait REFUTED | pas de ledger | démonstration non faite ; propriété UNRESOLVED | absence ≠ réfutation | corrigé ici |
| 1 984 038,168550 | « entrées = sorties » ambigu | chaque côté, puis logs RPC | chaque côté, pas le cumul ; confirmé par les logs jusqu'au 8 nov. | quatre fichiers de logs | corrigé ici |
| 8 / 19 / 71 | intersections vides, PnL des 8 | recalcul | CONFIRMED sur ces ensembles | JSON et CSV | ne pas additionner |
| Inca 2 des 5 | soutenu par le dépôt | PDF public, hash égal | CONFIRMED pour les cinq adresses et les deux intersections | PDF non commité | aucune |
| Pulser 27 | CONFIRMED sur l'extrait | inchangé | CONFIRMED sur l'extrait | `flows.csv` | aucune |
| KPMG 14 et p-value | le premier texte disait l'inférence REFUTED | 28 reçus Polygon ; `tail()` du dépôt | reçus CONFIRMED ; inférence non soutenue ; arithmétique non réfutée | JSON RPC | ne pas écrire REFUTED pour le test |
| Railgun 22 044,160154 | non re-sommé au premier passage | reçus et tokentx bruts | CONFIRMED sur ces fichiers | `financial-links-replay` evidence | fenêtre dès 18:43:51Z |
| Cypya 16 oct. / Snoorrason 14 oct. | archive | syndication publique | texte du 16 confirmé ; cinq noms du 14 absents du texte court | `ballon_syndication_2026-11-08.json` | ne pas promouvoir le texte long |
| Témoins NO→YES | non estimable | 769 créés ces jours-là ont tradé ; séquence non lue | toujours non estimable | `control_population_summary.json` | pas de p-value |
| Scanner et chemins | correctifs du premier commit | 7 tests avant/après contre `ab7ca23` | les sept écarts sont reproduits | `test_correction_before_after.py` | CI les lance |
| Ancre de publication | décrit sans essai | `verify()` réussit si README n'est pas dans la liste, blobs différents | limite observée, non « réparée » | appel cité en section F | pas de durcissement spéculatif |


Fichiers de comportement : `scripts/phi_lib.py`, `scripts/audit_public_repository.py`, `scripts/import_snapshot.py`, `scripts/validate_evidence.py`, `scripts/backup/phi_backup.py`, `scripts/test_audit_public_repository.py`, `scripts/test_integrity_regressions.py`, `research_notes/g38-proof-tier-audit-2026-11-08/verify.py`, `research_notes/g38-proof-tier-audit-2026-11-08/test_verify.py`.

Fichiers de conclusion, corrections factuelles courtes : `README.md`, `VERIFIED_FINANCIAL_FINDINGS.md`, addendum dans `research_notes/g38-proof-tier-audit-2026-11-08/REPORT.md`. Le README garde sa hiérarchie anglaise. L'ancre de `scripts/publication_baseline.json` doit suivre le commit qui contient ces octets de README ; elle ne protège pas ce rapport.

Preuves ajoutées : les deux JSON ci-dessus et ce rapport.

Commandes exécutées avec succès après correctif : `python3 -m unittest scripts.test_audit_public_repository`, `python3 scripts/test_integrity_regressions.py`, `python3 scripts/test_phi.py`, `python3 scripts/test_publication.py`, `python3 scripts/validate_evidence.py` (0 erreur), `python3 scripts/audit_public_repository.py`, `python3 scripts/build_master_report.py --check`, `python3 -I research_notes/g38-proof-tier-audit-2026-11-08/verify.py`, `python3 -I research_notes/g38-proof-tier-audit-2026-11-08/test_verify.py`, le vérificateur Pulser sur `flows.csv`. Les vérificateurs d'enquête hors G38 et Pulser n'ont pas tous été relancés.

Commit du rapport et des correctifs : `0658ab3ad326763f92a83250bacd19e9c39de7e6`. L'ancre de publication pointe vers ce commit, qui contient le README corrigé. PR : https://github.com/searadacunha/Polymarket-Home-of-the-Insiders/pull/65. Pas de merge.

## H. Questions restantes, par valeur de preuve

1. Marche `eth_getLogs` complète du destinataire Polygon du premier au dernier bloc, pour savoir si les 92 lignes Etherscan du 6 novembre sont exhaustives. Valeur : haute. Non fait : les RPC publics coupent les grandes fenêtres ; Blockscout a répondu 403.
2. Population témoin de comptes créés les 22–25 février 2026 ayant tradé le même marché, tirée sans filtre de profit, pour un taux de base NO→YES. Valeur : haute. Sans elle, pas de signification.
3. Re-étiquette indépendante des quatre destinataires de sweep et des financeurs de gas autres que `0x660629fe…`, de préférence hors de la seule compilation hildobby. Valeur : moyenne. Le comportement EOA est déjà là.
4. Grand livre Coinbase. Inaccessible. Toute phrase sur « le client » doit s'arrêter avant.
5. Redécodage des reçus KPMG, des sorties Inca/Solana et de la clôture Railgun sur les logs bruts. Valeur : moyenne pour confirmer des tables déjà structurées, faible pour changer le statut de propriété.
6. Réagréger la bande Ballon d'Or et les objets X hors git. Valeur : moyenne pour les horodatages, nulle pour un verdict d'initié sans protocole prospectif.
7. Protection de branche GitHub réellement exigée. Non vérifiée depuis l'API d'administration.
8. Les 170 commits hors `main`, les disques d'archive du 4 novembre, les processus arrêtés. Hors périmètre exécuté.

## Matrice de couverture

| Zone | Lu | Recalculé ici | RPC | Non fait |
|---|---|---|---|---|
| Histoire git de `main` | oui, 218 commits, clone complet | décompte | non | contenu des 31 branches non mergées |
| Cohorte 38, ledger, 86 dépôts | CSV + vérificateur | oui | non sur chaque dépôt d'entrée | contrôle statistique |
| 15 fills Relay | snapshot + reçus | oui, les 15 | oui | histoire postérieure au snapshot |
| 32 proxys, 38 transferts directs | archive, puis reçus RPC de la continuation | 38 transactions, 32 portefeuilles | voir continuation | aucun des 32 laissé de côté après la continuation |
| Base, Arbitrum, suite Arbitrum | oui | oui | oui, fenêtre 200 000 blocs | vie entière de `0xa656…` |
| Nametags | 2 adresses via pages publiques | non | non | les autres étiquettes |
| 8 vs 19 vs 71 | listes d'adresses | intersections et PnL des 8 | non | flux externes 151k/660k |
| Pulser | 7 596 lignes | 27 hash | non | reçus Etherscan un par un |
| KPMG, Railgun clôture, Ballon, ChangeNOW, Privacy Cash | rapports et un CSV | 14 lignes, 71/5 | non | décodage et bandes |
| Scanners Python | oui | tests + scan du dépôt | non | disque externe, CI distant |

## Tableau de décision

| Affirmation | Statut antérieur | Contrôle indépendant | Nouveau statut | Preuve | Action |
|---|---|---|---|---|---|
| 38 proxys distincts | CONFIRMED archive | vérificateur + CSV | CONFIRMED archive | `g38_accounts.csv` | aucune |
| 36 créés 22–25 fév., NO puis YES, YES 20:49–23:35 | CONFIRMED archive | min/max du CSV | CONFIRMED archive | même CSV | aucune |
| Résultat +1 576 522,86, 8 jetons ouverts | CONFIRMED comme ledger | somme des centimes | CONFIRMED, pas un profit réalisé | ledger | aucune |
| 32 proxys paient directement (38 transactions) | CONFIRMED archive, échantillon de 8 portefeuilles sur 32 | reçus RPC de chaque transaction | voir continuation : 38/38 transactions et 32/32 portefeuilles, pas 8/38 | reçus de continuation | le premier chiffre 8/38 mélangeait transactions et portefeuilles |
| 12 crédits = 12 ordres par montant seul | SUPPORTED | RPC input | 7 CONFIRMED avec order id dans l'input ; 5 SUPPORTED par hash fournisseur | reçu + input | vérificateur fige la partition |
| Reçus Base absents | RELAY seulement | 2 RPC × 2 hash | CONFIRMED reçu ; order id absent ; crédit client UNRESOLVED | blocs 42827159 et 42827432 | README et index corrigés |
| Saut Arbitrum non classé | UNRESOLVED | RPC 122 sorties + nametag | infrastructure comminglée, nametag Coinbase 26 ; crédit client UNRESOLVED | `arbitrum_onward_usdc_outs_200k.json` | README corrigé |
| Un client Coinbase possède les 38 | énoncé de démonstration trop fort | pas de ledger ; mélange en aval | la démonstration n'est pas faite. La propriété commune reste UNRESOLVED, pas REFUTED | absence de ledger n'est pas une preuve d'absence | ne pas écrire REFUTED pour la propriété |
| 0x660629fe est un financeur de dépôts Coinbase | étiquette d'archive | page Polygonscan hildobby | SUPPORTED doc. externe, pas une attestation Coinbase | page publique | aucune identité |
| 1 984 038,168550 USDC/USDC.e | présenté comme entrées = sorties | somme de chaque côté | chaque côté vaut ce montant ; ce n'est pas la somme débit+crédit | 53 entrées et 24 sorties | dire « chaque côté », pas le cumul |
| 8 comptes +509 993,24 distincts des 19 et des 71 | séparé | intersection vide, somme JSON | CONFIRMED sur ces ensembles | `pnl_table.json` | ne pas additionner |
| Pulser 27 hash / 14 699,999999 | CONFIRMED archive | rejeu des 7 596 lignes | CONFIRMED sur l'extrait | `flows.csv` | aucune |
| 14 passages KPMG et leurs p-values | table d'archive | reçus RPC ; `tail()` exécuté par le vérificateur du dépôt | reçus confirmés dans la continuation. Inférence d'initié non soutenue. Arithmétique du script non réfutée | CSV + RPC | ne pas écrire REFUTED pour le test |
| Arbre 71, 66 pertes | CONFIRMED archive | 71 et 5 `won` relus | CONFIRMED sur le CSV ; clôture USDC non re-sommée | `railgun_tree_accounts.csv` | ne pas promouvoir 22 044,16 |
| Lien ZK Privacy Cash ou client ChangeNOW | non montré | non rouvert | non montré | — | aucune |
| Scanner gzip incomplet refusé | correctif du matin | 3 tests négatifs en échec puis OK ; scan dépôt 0 | CONFIRMED pour plafond, corruption, commentaire, casse, zlib.error | tests | correctif dans ce PR |
| Politique de publication auto-protégée | garde-fou d'ancre | lecture du script | UNRESOLVED contre un PR qui déplace l'ancre | `check_publication.py` | pas de faux durcissement |
