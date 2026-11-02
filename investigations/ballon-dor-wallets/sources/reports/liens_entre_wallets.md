# Liens entre les onze wallets

Extrait de la version 2 du rapport final, corrigée après audit le 02/11/2026. Version 1 : `archive/20261102_avant_amendement_audit/liens_entre_wallets.md`. Un service commun ne relie personne, un transfert direct relie deux adresses, et aucune de ces lignes n'attribue deux wallets à un même propriétaire. Données : `graphs/links_classified.json`, `evidence/contre_verification_20261102/`.


Une règle naïve de « financeur commun » relierait **21 paires sur 55**. Après classement, **0 paire** repose sur une adresse partagée discriminante. **Mais 1 paire sur 55, brace227 et kraben006, a un transfert direct entre clés**, que ce classement par adresses partagées ne pouvait pas voir.

| Adresse partagée | Classe | Dossiers | Aussi chez les témoins | Pourquoi |
|---|---|---|---|---|
| `BmFdpraQhk…ymy6` | SERVICE_ETIQUETE | 0xdd97e6, cookedrice, ouldlm3alem, thin, vidente | token_oppose 1 | KuCoin Hot Wallet 2, selon orbmarkets.io |
| `0xc8a6871d…8d64` | SERVICE_MESURE | 0x86544e4dfde, brace227, kraben006, walletwallet8424, zoomman17 | meme_token 1, token_oppose 3, fraiches_recensement 1 | 215 sorties et 211 entrées en 3,75 h, un seul payeur |
| `0x4cd00e38…bc31` | SERVICE_ETIQUETE | brace227, kraben006, zoomman17 | non | Relay Depository, selon api.relay.link |
| `GxjcMTWWDc…nvBW` | SERVICE_MESURE | cookedrice, vidente | non | Environ 1,2 transaction par minute. Sur 120 transactions lues : 18 entrées, 95 sorties, 67 destinataires. Sur 400 tirées : 73 entrées, médiane 270 $,  |
| `0xee7ae85f…4055` | SERVICE_MESURE | ouldlm3alem, wen | token_oppose 1 | Polygon : 1 173 sorties vers 824 destinataires en 12 h autour du 18 oct. Arbitrum : 890 sorties vers 743 destinataires en 12 h autour du 26 oct. Appel |
| `0x0ce9bdf3…f06d` | SERVICE_MESURE | 0x86544e4dfde, walletwallet8424 | non | 85 sorties vers 57 destinataires en 3,8 h |
| `0xc1d13492…a1b5` | SERVICE_MESURE | brace227, kraben006 | non | Contrat vérifié nommé SwftSwap. 549 sorties vers 454 destinataires en 10 h |
| `0x58f298e3…0214` | SERVICE_MESURE | kraben006, zoomman17 | non | Nonce de 114 468 |

**Transferts directs.** Le scan d'origine (33 adresses, Polygon et Ethereum, stablecoins, pUSD et positions, depuis le 25 sept., `graphs/direct_transfers.json`) rendait 0 transfert. Il ne lisait ni l'ETH natif ni l'historique ancien des clés : ce « 0 » de la version 1 était faux pour une paire. Après audit : **1 transfert natif direct, brace227 vers kraben006**, détaillé ci-dessous. Selon l'audit, aucun autre sur 27 adresses EVM lues sur Ethereum, Arbitrum et Base, ni en POL natif sur 46 adresses, ni sur les 9 adresses Solana lues. Ce scan n'est pas refait ici. Pour les deux clés de la paire, l'historique Ethereum complet ne montre que ce seul transfert, et leurs seules contreparties communes sont des services : USDC, Relay Depository, solveur Relay, SwftSwap.

**Exécutions et transactions communes.** Les onze historiques partagent 14 transactions, toutes décodées (`evidence/contre_verification_20261102/transactions_communes.json`). 8 sont des paiements en lot : 5 rebates ou récompenses, 3 redemptions de 20 comptes chacune. 5 sont des exécutions où deux dossiers sont makers face au même tiers, sans échange entre eux, dont une pour brace227 et kraben006 (24 oct. 16:41:44, ventes de Mbappé à 0,84). **1 seule est une exécution directe :** OuldLm3alem vend 520,97 parts à 0,53 à 0x86544e4dfde, le 26 oct. 13:29:02 UTC, `0x870eaa6cb8298d7a02379b48093d4633af4f77ba58638bfc78ff9b0146f30b48`. C'est ordinaire sur un carnet.

**Montant et heure.** 0 candidat entre une sortie et une entrée à 6 h et 90 à 100,1 %, sur 25 sorties et 46 entrées. Placebo à dates décalées : 0 aussi. `graphs/links.json`.

### Un wallet non nommé financé par la clé de brace227

Signalé par l'enquête flow-trace, relu ici sur la chaîne : `evidence/contre_verification_20261102/wallet_0xa8e6.json`. **La version 1 écrivait qu'aucun wallet supplémentaire n'était relié aux onze : c'est faux.** Ce financement pèse bien plus que les 5,53 $ du circuit décrit plus bas.

**Le lien.** Le wallet `0xa8e64a3c08d1e2a4e9f25a2dd33b8ac3458f74a5` a pour propriétaire, `owner()` lu sur Polygon, `0x48ec106cf690edd58fcd6df1e8b6abfc16dab12d`. La clé de brace227 envoie à cette clé 2 210 USDC le 9 oct. à 20:28:35 UTC, `0x7e3aecb9b41e6d3f92f25b8760228f15e9b55e798cd27977eb7170445cf64349`, et 2 960 USDC le 10 oct. à 00:51:11, `0xb07c3c53a713d98aea1d1bd5d6facf849b6edc675c0fe2cfd3df5b791db20add`. Sur Ethereum, ce sont ses seules entrées de jetons avant le retrait du 27 oct., et sa plus ancienne transaction listée date du 9 oct. à 20:32:11, page complète (nonce de 14 pour 13 envois listés, écart non expliqué). Ses deux envois à Relay Depository, 2 200 et 2 965 USDC, sont reliés à ces deux dépôts par l'enregistrement Relay, `user` et `recipient` compris (`wallet_0xa8e6_preuves.json`), sans recoupement ici par identifiant sur la chaîne. **Selon cette comptabilité, les dépôts de ce wallet viennent de la clé de brace227.** Autres chaînes non lues ici, hormis un nonce de 0 sur Polygon. Selon flow-trace, non relu ici : le wallet est créé le 8 oct. à 10:13:20 UTC, la veille des premiers fonds, `0xa6e22997…5d7b`.

**Le partage.** Les arrivées de SwftSwap des 9 et 10 oct. sur la clé de brace227 sont coupées en deux, celle du 16 oct. va tout entière au wallet de brace227. Au total, 34,2 % des 15 096,29 USDC reçus de SwftSwap vont à `0x48ec…` :

| Arrivée sur la clé de brace227 | Vers `0x48ec…` | Part | Vers le wallet de brace227 |
|---|---:|---:|---:|
| 9 oct. 20:03 et 20:06, 4 421,41 USDC | 2 210,00 | 49,98 % | 2 186,43 |
| 10 oct. 00:26, 5 925,84 USDC | 2 960,00 | 49,95 % | 2 986,82, en trois dépôts |
| **Sous-total, 9 et 10 oct.** | **5 170,00** | | **5 173,25** |
| 16 oct. 19:16, 4 749,03 USDC | 0 | 0 % | 4 749,54, en trois dépôts |

**Les paris.** Le wallet dépose 2 200 $ à 20:36:28 et achète à 20:37:10. brace227 dépose 2 186,43 $ à 20:49:05 et achète à 20:50, dont du Kane dès 21:14. Le wallet fait 16 achats, tous sur Kane Yes, 5 164,99 $ pour 8 061,89 parts, du 9 oct. à 20:37 au 11 oct. à 17:54 UTC. Il ne vend jamais.

**La sortie.** Redemption de 8 061,89 $ à 01:58:20 le 27 oct., dans le lot Kane. Retrait de 8 061,90 $ vers `0x48ec…` 16 h 51 min plus tard, à 18:49:06. Retraits moins dépôts : 2 896,90 $, hors des totaux de la section 2. Aucun retour vers la clé de brace227 sur Ethereum. Le 2 nov., `0x48ec…` détient 5 062,18 USDC. Il envoie aussi 2 501 USDC à `0x6A2522Df…7973` le 28 oct., rendus le 29 oct., adresse non analysée. Le 29 oct., il échange 3 000 USDC contre 2 969,57 mUSD, envoyés à Relay Depository : suite non lue ici.

**Ce que cela établit :** selon cette comptabilité, une même clé a financé deux comptes Polymarket, à parts presque égales les 9 et 10 oct., et les deux ont acheté Kane le 9 oct. à moins d'une heure d'écart, 741,47 $ chez brace227. **Ce que cela n'établit pas :** un propriétaire commun, puisque financer un compte n'est pas le contrôler, ni une information privilégiée. Rien ne dit non plus que c'est le douzième compte allégué par la presse (`reports/inventaire_adresses.md`).

| Hypothèse, aucune n'est une conclusion | Pour | Contre ou limite |
|---|---|---|
| Un même opérateur, deux comptes | Aucune transaction listée avant le 9 oct. sur Ethereum, dépôts venus de l'autre clé, parts presque égales les 9 et 10 oct. | Deux clés. brace227 vend son Kane à 0,999 le 26 oct. à 23:10, ce wallet attend le lot puis 16 h. 9 issues d'un côté, 1 de l'autre. La tranche du 16 oct. va tout entière à brace227. Son Kane des 9 et 10 oct. ne pèse que 954,04 $ sur 4 917,62 $ d'achats |
| Deux personnes qui misent à parts égales | Parts égales les 9 et 10 oct., deux clés, sorties différentes | Aucune trace de cet accord, invérifiable |
| Prêt ou don | Compatible avec deux virements ponctuels | Aucun remboursement visible sur Ethereum à ce jour, invérifiable |

**Autre proximité.** Dans les sorties gelées, ce wallet figure aussi dans une rafale E2 de 60 min sur Kane, le 11 oct. à 13:34:42 UTC, 10 667,19 $, avec 0x86544e4dfde et walletwallet8424 (`collective/derived/A_E2.json`). Ni brace227 ni aucun transfert entre eux n'y figurent. C'est une proximité d'achat sur un marché actif, pas un lien.

**Pourquoi la version 1 ne l'a pas vu, et ce que cela implique.** Le dossier suit les dépôts et les sorties de Polymarket, pas ce que la clé envoie ailleurs. Ce wallet ne détient pas Mbappé, donc il n'est pas dans la capture Upside. Avec un seul token, il est aussi écarté d'E4. **Selon flow-trace, c'est le seul wallet actif** parmi 50 adresses personnelles testées autour des onze, 94 essais, 44 adresses sous 2 formes de wallet et 6 clés de dossiers sous l'ancienne forme seulement (`state/personal_wallets.json`), calcul validé sur 11 wallets connus. Les anciens proxys Safe et Magic ne sont pas testés : d'autres peuvent exister.

### Le circuit 7XUJs, clé de brace227, clé de kraben006

Heures UTC, 4 octobre 2026. Données en wei : `evidence/contre_verification_20261102/circuit_7xujs_brace_kraben.json`.

| # | Heure | De | Vers | Montant | Preuve | Niveau |
|---|---|---|---|---|---|---|
| 1 | 13:52:35 | `7XUJsJBNp7…frZc` (Solana) | Relay | 4,62476 USDT, plus 0,0298 de frais | `3XaPp5kRsL5M…NfEL` | **Démontré** |
| 2 | 13:52:47 | solveur Relay `0xadA5bb90…F7CB` | clé de brace227 `0xc852b093…af26` | 0,001692408 ETH | Même identifiant `0x30484595…7867` à l'octet près dans l'instruction Solana et le calldata de `0xb17e1c46…ce3c`, sans dépendre de l'API | **Démontré** : même ordre, valeur équivalente, pas les mêmes jetons |
| 3 | 13:54:35 | clé de brace227 | clé de kraben006 `0x101b5f4d…fb65` | 0,002048944 ETH, environ 5,53 $ | `0xd07bea20…2b98`, bloc 26119420, 2 nœuds, envoi simple sans données, 21 000 gas, succès | **Démontré.** Au moins 81,4 % du montant vient forcément du maillon 2 |
| 4 | 23:48:47 | clé de kraben006 | `0x7e67dF45…6E23` | 0,00247406 ETH | `0x1a39308b…dd71`, Blockscout | Transaction démontrée. **Continuité limitée** : au moins 22,7 % de ce qui a été reçu, 23,9 % gas compris |
| 5 | 23:56:59 | `0x7e67dF45…6E23` | `0x3f3Ee0a9…207B` | 0,00241406 ETH | `0x22710b5e…9c26`, Blockscout | Continuité à l'adresse : 1 entrée, 1 sortie. **Destination étiquetée « ChangeNOW Dep » par Blockscout**, source unique, non recoupée, environ 321 000 transactions selon un compteur Blockscout qui rend 0 pour `0x7e67…`, donc peu fiable |

**Continuité démontrée, maillons 1 à 3.** Le maillon 2 est prouvé par la chaîne seule. Pour le maillon 3, la clé détenait 0,000380298 ETH et n'a rien reçu d'autre entre les deux transactions : au moins 0,001668646 ETH envoyés proviennent donc du paiement. Soldes des deux clés lus sur Blockscout et recoupés au wei près à ces blocs sur un nœud d'archive.

**Simple succession, maillon 4.** Il arrive 9 h 54 min plus tard, sur une clé qui détenait déjà 0,002007933 ETH. Seuls 0,000466127 ETH envoyés, 0,000489889 gas compris, sont imposés par la comptabilité. Attribuer le reste à ce transfert dépendrait d'une convention de traçage : l'ETH est fongible. Aucune lecture ne relie ces montants au capital d'un dépôt Polymarket, fait en USDC. L'ETH étant fongible, le solde de la clé a pu payer le gas de ses dépôts suivants, 0,00018 ETH consommés après l'envoi. Selon flow-trace, `0x7e67…` a le profil d'une adresse de dépôt ChangeNOW : une partie de cet ETH a pu être revendue, ce qui n'est pas démontré.

**Le payeur Solana.** `7XUJs…` compte 8 signatures en tout, depuis le 6 juin 2026 : il reçoit 304,70 USDT, en envoie 300, et le 4 octobre envoie presque tout le reste. Il garde 0,047 USDT. Une seule requête Relay à son nom. Aucune des 27 adresses qu'il touche n'apparaît dans les dossiers, hormis le jeton USDT lui-même.

**Portée du vidage de la clé de brace227.** Le transfert laisse 0,000000494 ETH : 98,85 % du solde envoyés, 1,12 % de gas, 0,02 % restant. Cela ressemble à un envoi du solde maximal, pas à un montant choisi.

- *Ce qui est vidé :* l'ETH seul, et la clé était déjà presque vide. Ses USDT étaient à 0 depuis le 28 avril 2025.
- *Ce n'est ni un abandon, ni un compte drainé :* la clé reçoit 4 337,52 USDC de SwftSwap le 9 octobre, et 22 024,57 USDC y dorment encore le 2 novembre.
- *Ensuite :* le 9 octobre, ses transactions passent par des relais de gas à fort trafic, étiquetés MetaMask par Blockscout, et le 16 octobre elle reçoit 0,00202 ETH de `0x2CfF890f…`, étiqueté NEAR Intents. Le lien de cause avec le vidage n'est pas établi.
- *En montant, ce n'est pas un financement significatif :* 5,53 $, soit 0,055 % des dépôts de brace227 et 0,097 % de ceux de kraben006.
- *La lecture « don de gas » de l'audit est peu soutenue :* la clé de kraben006 détenait déjà 0,0020 ETH et n'en a consommé que 0,00018 depuis. Un donateur peut toutefois ignorer le solde du destinataire.
- *« Première sortie en 17 mois » ne vaut que pour Ethereum.* La clé a un nonce de 109 sur BSC, visible dans son dossier mais jamais lu. Lu par l'enquête flow-trace, relu ici dans son fichier : 5 sorties de décembre 2024 au 17 mai 2025 à 11:52:55 UTC, aucune vers une adresse de dossier, 104 antérieures à juillet 2022 non énumérées. Sa dernière sortie précède donc le transfert de 16 mois et demi, toutes chaînes lues. Entrées BSC non lues.

**Ce que ce circuit établit :** une transaction signée par la clé de brace227 vise l'adresse de celle de kraben006, sans service entre elles. Qui l'a signée, et s'il connaissait le destinataire, reste inconnu. **Ce qu'il n'établit pas :** un propriétaire commun, un pari concerté, une information privilégiée.

| Hypothèse, aucune n'est une conclusion | Pour | Contre ou limite |
|---|---|---|
| Un même opérateur regroupe ses restes | Résidu d'USDT Solana et résidu d'ETH réunis en 2 min, envoi du solde maximal | Aucun autre transfert direct, aucune contrepartie personnelle commune sur Ethereum |
| Deux personnes qui se connaissent, petit paiement | Un seul envoi de 5,53 $ suffit à l'expliquer | Pas de mémo ni de contrepartie visible, invérifiable |
| Paiement sans rapport avec les paris | 5 jours avant le premier achat de brace227 | kraben006 était déjà actif, invérifiable |
| Clé compromise | Sortie 108 s après la réception | Peu probable : 22 024,57 USDC restent sur la clé, qui continue à financer des comptes ensuite |
| Erreur d'adresse | La clé de kraben006 reçoit des transactions de leurre à 0 valeur | Peu probable, et aucune trace d'une relation antérieure qui l'expliquerait |

Aucune donnée lue ici ne les départage : entrées BSC et sauts de la section 7 non lus. Un exchange ou un fournisseur de portefeuille pourrait le faire sur demande légale.

### Retraits rapprochés : ce que le calendrier explique, et ce qu'il n'explique pas

Tests exploratoires, écrits après avoir vu les données, non inscrits au registre gelé. Liste : `evidence/contre_verification_20261102/tests_exploratoires.jsonl`. Résultats : `stats_retraits_kane.json`.

**brace227 et kraben006, 2,8 min d'écart : aucun signal mesurable.** Kane atteint 0,99 à 22:50:24 UTC le 26 octobre. kraben006 retire 48 s après sa vente à 0,999, brace227 136 s après la sienne. Parmi 20 autres vendeurs comparables (5 000 $ ou plus, dans les 30 min après le premier 0,99), **10 retirent eux aussi en moins de 5 min**, p = 0,29 : la vitesse est ordinaire. Leurs ventes sont à 78 s d'écart, pour un écart médian de 45 s entre deux ventes consécutives de ces 22 vendeurs. Leurs retraits sont à 166 s : 8 paires sur 105 font aussi peu parmi les 15 vendeurs qui retirent sous 24 h, sans correction pour le choix de cette paire. Rien ici ne les distingue nettement.

**0x86544e4dfde et walletwallet8424, 1,6 min d'écart : deux faits distincts.**

- *La redemption simultanée est un faux positif.* Le marché Kane est résolu sur la chaîne à 01:57:41 UTC le 27 octobre, `0xf3684759…2430`. De 01:58:14 à 01:58:24, **2 711 comptes sont remboursés en 136 transactions**, 6 204 783,28 $. Les deux comptes y sont, à 01:58:15. Le déclencheur n'est pas lu, mais cette forme rend une décision individuelle synchrone très improbable.
- *La vitesse de retrait ne s'explique pas par le calendrier.* Ils retirent 96 s et 189 s après leur redemption (91 et 184 s après le repère de 01:58:20), et tout leur solde. L'audit classait ce point en faux positif : c'est trop fort.

Face aux autres comptes du lot à 5 000 $ ou plus. 178 lus, 175 retenus : 2 atteignent le plafond de lecture et ne sont pas comptés comme « sans retrait », 1 est le wallet financé par la clé de brace227, décrit plus haut, qui retire 16 h 51 min après. Le p teste 2 nommés sur 2 sous 5 min (Fisher unilatéral). La colonne x 55 corrige le choix de cette paire parmi 55. Sept strates sur treize, toutes dans `reports/CONTRE_VERIFICATION.md`.

| Comparateurs | n | Retrait en moins de 5 min | p brut | p x 55 |
|---|---:|---:|---:|---:|
| Tous | 175 | 1 | 0,0002 | 0,011 |
| Même taille, 20 000 à 50 000 $ | 40 | 0 | 0,0012 | 0,064 |
| Compte de 30 jours ou moins | 22 | 0 | 0,0036 | 0,20 |
| Aucun trade dans l'heure | 124 | 1 | 0,0004 | 0,021 |
| A retiré sous 24 h | 48 | 1 | 0,0024 | 0,13 |
| A retiré sous 24 h, Kane dernière clôture | 27 | 0 | 0,0025 | 0,14 |
| Compte de 60 jours ou moins, a retiré sous 24 h | 19 | 0 | 0,0048 | 0,26 |

Lecture :

- **Atypique à l'état brut, dans toutes les strates. Non significatif après correction dans les strates les plus comparables.**
- **L'écart de 93 s entre eux n'ajoute rien.** Une fois admis que les deux sont rapides, deux délais tirés au hasard sous 5 min sont aussi proches dans 52 % des cas.
- **C'est plutôt un trait du groupe que de la paire.** Entre la dernière clôture et le retrait principal, 8 nommés sur 11 mettent moins de 10 min, contre 9 sur 48 comparateurs qui retirent sous 24 h, p = 0,0011 non corrigé. Le taux des nommés sous 5 min, 4 sur 11, inclut ces deux comptes : appliqué à eux, 13 %. Sur les 9 autres nommés, 2 sur 9 donne 4,9 %. Sélection par la presse dans les deux cas.
- **Biais non contrôlés.** La presse a choisi les nommés après coup, parmi des comptes récents et concentrés. Les strates sont emboîtées, choisies après coup, sur un seul événement. Non mesurés : notifications, logiciel de portefeuille, fuseau horaire (02:00 UTC), autres positions au-delà de 24 h. Les deux clés ont le même contrat de délégation 7702 sur Polygon : le nombre d'adresses qui le partagent n'est pas mesuré ici, et rien n'en fait un lien.

Classement : indice faible, exploratoire. Compatible avec deux comptes dont Kane est la dernière position et qui guettent ce paiement, avec une consigne commune, ou avec un même opérateur. Le test ne les départage pas.

### Taux de base et faux positifs

**Le tableau publié en version 1 n'est pas valable.** Il comptait 50 comparateurs lus comme s'ils étaient tous mesurés. Prévus : 83 lignes, soit 78 wallets distincts, 5 figurant dans deux groupes. **Seuls 30 étaient utilisables, 48 ne l'étaient pas :**

| Cause | Wallets |
|---|---:|
| Jamais lus, tous des comptes frais | 28 |
| Lus, sans origine : la ligne comptait comme « pas KuCoin, pas Solana » | 16 |
| Origine lue, mais historique coupé avant le premier achat | 4 |
| **Total inutilisable** | **48** |

L'audit et la version 2 de ce rapport écrivaient 53 sur 83, en comptant comme jamais lus 5 wallets déjà lus sous un autre groupe.

**Les 17 historiques coupés.** `tools/baseline.py` s'arrête à 12 pages, 6 000 lignes, sans le signaler. Rejoué depuis le cache : les 17 s'arrêtent avant leur premier achat de la famille, 17 sur 17, dont 13 sans origine lue. Le dépôt retenu précède cet achat de 61 à 736 jours, par exemple 0,04 $ en octobre 2024 pour un achat de 2026. Aucun nommé n'est touché : 11 historiques sur 11 sont complets, donc la comptabilité des dossiers ne bouge pas. Liste complète : `reports/CONTRE_VERIFICATION.md`.

**Relecture complète par l'enquête flow-trace.** 77 témoins lus sur 78, tous les dépôts lus depuis l'API, mêmes groupes : `~/Projects/PolySentinel-flow-trace/state/compare_rates.json`, `reports/COMMON_FUNDERS.md`, section 4. RAPPORTÉ : son lecteur n'est pas refait ici. Recoupé ici : ses p sont égaux à mon recalcul, et sur 30 wallets lus par nos deux lecteurs, l'origine concorde 29 fois (`evidence/contre_verification_20261102/recoupe_flow_trace.json`).

| Trait, un dépôt par wallet | Nommés | Tous témoins | p | Comptes frais | p |
|---|---|---:|---:|---:|---:|
| Financement moins d'1 h avant le premier achat | 9/11 | 41/76 | 0,074 | 32/39 | 0,69 |
| Origine Solana, par Relay | 3/11 | 6/68 | 0,11 | 3/39 | 0,11 |
| KuCoin Hot Wallet 2, parmi les origines Solana | 3/3 | 1/6 | 0,048 | 0/3 | 0,050 |
| Dépôt via `0xc8a6…`, VaultDepositooor | 5/11 | 9/77 | 0,013 | 5/39 | 0,030 |
| Adresse de pont 7702 | 6/11 | 59/77 | 0,97 | 34/39 | 1,00 |
| Clé touche SwftSwap | 2/11 | 0/54 | 0,026 | 0/39 | 0,045 |
| Clé reçoit de MetaMask Gas Station | 3/11 | 2/54 | 0,031 | 1/39 | 0,029 |

Fisher unilatéral, non corrigé. **Aucun trait ne passe le seuil corrigé pour 9 tests, 0,0056.** Traits choisis après coup, groupe choisi par la presse : exploratoire.

- **Financement moins d'une heure : rien de distinctif** face aux comptes frais, 9/11 contre 32/39.
- **Le « KuCoin plus fréquent » de la version 1, 3/11 contre 1/50, est retiré.** Reste un indice faible : Solana 3/11 contre 6/68, et KuCoin 3/3 contre 1/6 sur 9 wallets seulement. Son libellé n'est lu que sur une origine Solana, donc c'est la même observation, et l'étiquette a une source unique.
- **`0xc8a6…` est l'écart le plus net.** C'est un outil de dépôt, contrat vérifié selon flow-trace, pas un lien entre personnes.
- **SwftSwap :** les 2 comptes sont brace227 et kraben006, ce n'est pas un trait indépendant de leur lien. **MetaMask Gas Station :** un logiciel de portefeuille.
- **Liens directs entre clés (Ethereum, Polygon, Arbitrum) :** 1 sur 55 paires nommées, 0 sur 1 431 paires de témoins, dont 0 sur 741 chez les comptes frais. Ce n'est pas un test, les paires n'étant pas indépendantes, et seules 54 clés sont lisibles sur 77 wallets. Mais un tel transfert n'est pas banal dans ces témoins.

### Résultats de l'enquête flow-trace, non revérifiés ici

Rapports finaux : `~/Projects/PolySentinel-flow-trace/reports/`. Même famille de modèle : pas un audit indépendant au sens fort.

- **Origine des fonds :** Relay est le seul service commun aux onze. Plus de la moitié des 304 137,63 $ remonte à des plateformes étiquetées : KuCoin Hot Wallet 2 pour 5 comptes et 102 833,93 $, Binance pour 3 comptes et 65 755,73 $, plus Revolut et BloFin. Le reste vient de services non attribués, de SwftSwap et de Chainflip.
- **Sorties :** **aucune destination finale commune.** Environ 74 % des 493 094,76 $ n'avaient pas quitté leur première adresse ou y étaient revenus le 2 nov. Trois comptes ont déposé 118 371,00 $ chez des services non identifiés. Zoomman17 a envoyé 6 893,00 USDC vers une adresse balayée par `0xf7c8da79…d921`, étiqueté Revolut 5.
- **Mixeurs et Monero :** aucune interaction lue avec Tornado Cash, Railgun ou un contrat de confidentialité étiqueté, sur les adresses connues. Monero absent des données accessibles, ni démontré ni exclu derrière les comptes de plateforme et les services non identifiés.
- **Étiquettes :** `0xee7ae85f…4055`, partagé par OuldLm3alem et WenZhuanBuPei, est étiqueté Binance: Hot Wallet 34, `0x8894e0a0…d4e3`, source de Thin, Binance: Hot Wallet. Une étiquette dit ce qu'une source a écrit, elle n'identifie aucun client.
- **Recoupement :** 46 dépôts et 25 retraits rapprochés de la chaîne par un autre lecteur, soldes pUSD égaux sur 11 wallets. Mêmes totaux qu'ici.

**Faux positifs identifiés et écartés :**

- `0xc8a6…`, `0xee7a…`, `GxjcMTWW…`, `0x0ce9…`, `0xc1d1…`, `0x58f2…` : chacun relie plusieurs dossiers, et chacun se révèle mutualisé à la mesure. Tableau ci-dessus.
- La route `0xf70d… → 0xb92f… → 0xc8a6…`, signalée le 30 octobre comme « nature inconnue » entre brace227 et walletwallet8424 : c'est Relay et un contrat de passage, donc pas un lien.
- `GxjcMTWW…` : VidenteRibeira et cookedrice y déposent à un jour d'écart (51 489,00 USDT, 39 158,00 USDC). Les deux sorties sont cosignées par ce service, qui en paie les frais, 4 et 2 s après réception : le « même comportement » de sortie est donc son automatisme, seul le choix commun du service reste à expliquer. Service à 1 % de frais, payant par morceaux. Sur 400 transactions tirées, 2 entrées à 10 000 $ ou plus sur 73, médiane 270,38 $ : ces gros dépôts sont plutôt rares, sans que cela relie leurs auteurs. Les sorties ne s'apparient pas sans le registre du service.
- Part de 29 353 $ sur 30 398 $ d'achats côté Mbappé le 13 octobre par des comptes nommés : mécanique, puisqu'ils sont nommés parce qu'ils détenaient ce token.
- Le candidat de 59,09 POL de `0xc590175e…c02b` vers `0x408ce42a…c5b3`, repéré par l'audit, n'est pas un transfert entre dossiers : dans `0x4b89cf4f…5ac8`, `0x408c…` paie lui-même 5,62 USDC et reçoit ces POL. `0xc590…` est un contrat d'échange mutualisé qui a seulement servi aussi au dépôt de walletwallet8424.
- Relais `0xb42f…` et `0xb01c…` et adresses `0xc066…`, `0xe347…`, partagés par plusieurs dossiers : 160 000 à 850 000 transactions chacun selon l'audit, écartés.
- Redemptions dans une même transaction entre 0x86544e4dfde et cookedrice, VidenteRibeira et WenZhuanBuPei : lots de 20 comptes, sans lien.
- Pièges de lecture évités : nœud Solana rendant 0 signature pour une adresse payée, hash du pont introuvable sur sa chaîne, sondage récent de `0xee7a…` à 0 trafic. Ces trois faux zéros ont été recoupés.
