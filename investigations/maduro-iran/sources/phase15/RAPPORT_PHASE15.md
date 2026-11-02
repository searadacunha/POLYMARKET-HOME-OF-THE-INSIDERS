# Phase 15 : audit de couverture et de détection en direct

Rapport du 01/10/2026, mis à jour à 21:35 UTC avec l'enregistrement complet. Protocole : `PROTOCOLE_P15.md`.

**Cadre :**
- **Audit uniquement :** SIG_HIST V1 inchangé, aucun seuil modifié, aucun processus existant arrêté ni modifié, aucun signal créé, aucun ordre.
- **Données, période P11 :** fichiers bruts des phases 11 à 14 (01/10, de 08:45 à 11:30 UTC, environ 2,6 h).
- **Données, audit live :** enregistreur indépendant `p15_audit.py`, de 11:36:50 à 14:02:40 UTC (**2 h 26**) : 151 313 trades vérité, 5 833 blocs.
- **Écart au protocole :** le protocole visait au moins 3 h. Le Mac s'est mis en **veille, capot fermé, sur batterie (35 %)**, de 14:04:39 à 21:24:33 UTC (journal `pmset`), et l'enregistreur s'est arrêté au réveil. Le volume suffit, et les défauts étaient démontrés avant la coupure. **La veille est elle-même un résultat** (§7).

## Conclusion

**INFRASTRUCTURE NOT VALIDATED.**

Les processus tournent, mais le chemin des alertes du listener P11 a trois défauts démontrés sur des données brutes, et toute l'infrastructure a un quatrième défaut :

1. **Marché.**
   - RTDS envoie **890 marchés sans `conditionId`**, toujours les mêmes, avec un `outcomeIndex` forcé à 0.
   - Le listener range ces trades dans un faux marché commun, ce qui fausse le prix de référence et le filtre FOLLOW.
   - Ce défaut touche 13 % des achats d'au moins 250 $ de l'univers suivi, et 22 % des FAE du listener (62 sur 284 jusqu'à la veille).
2. **Wallet.**
   - Sur les marchés sans frais, aucune ligne RTDS ne marque le preneur.
   - La règle du listener se trompe alors de wallet près de 4 fois sur 5 (78 % d'erreurs sur 437 trades d'au moins 100 $).
   - **83 % des alertes SIG_HIST historiques** étaient sur des trades sans frais.
3. **Trous.**
   - Chaque connexion RTDS se tait environ 30 s **toutes les 20 min environ** (7 fois en 2 h 26 sur la connexion A).
   - Chaque démarrage laisse 300 à 360 s non traitées.
   - Rien n'est jamais rattrapé.
4. **Veille du Mac.** Capot fermé sur batterie, `caffeinate` n'empêche pas la veille : **les 5 processus ont été aveugles 7 h 20**, tout en restant « vivants », et sans aucun rattrapage au réveil.

**Résultat sur les alertes en direct de la journée :**
- **listener P11 : 3 alertes justes sur 6** ;
  - **A2** vient d'un maker pris pour le preneur ;
  - **A3** (CNN) et **A5** (Fed d'octobre) reposent sur le faux marché, avec un p_before faux (A5 : 0,61 au lieu de 0,36) ;
  - A1 est juste, mais avec un p_before STALE de 4 points ;
- **P13 : 3 alertes SIG_HIST justes sur 3** (preneur et p_before exacts), dont Oklahoma.

**Ce qui est fiable :**
- les données historiques du data-api (régression Maduro et Iran identique à 100 %) ;
- la chaîne comme vérité de complétude ;
- le carnet CLOB sur les marchés abonnés ;
- les lignes RTDS dont le preneur est marqué par une ligne `fee`.

Les résultats historiques des phases 8 à 14 ne sont pas remis en cause. Les résultats **en direct** des phases 11 à 14 ne sont **pas interprétables tels quels**.

---

## Inventaire des sources (§3)

Valeurs observées (`phase15_latency.csv`, `phase15_trade_coverage.csv`).

| Source | Fonction | Horodatage | Wallet | Jeton | Marché | Prix | Trades | Latence observée |
|---|---|---|---|---|---|---|---|---|
| Websocket carnet P11 (collecteur) | carnet + `last_trade_price` | heure d'échange (ms) | non | oui | oui (`market`) | oui | 99,8 % des trades des marchés **abonnés** (2 537/2 542) | réception = échange + 0 à 140 ms (P50) ; 2,2 s avant le bloc |
| RTDS (collecteur, listener, P13, P14) | tous les trades de la plateforme | secondes, environ 1 s avant le bloc | oui, une ligne par participant ; preneur = ligne `fee` si frais | oui (`asset`) | **vide pour 7,7 % des lignes** (890 marchés) | oui | **95,8 à 96,4 %** par connexion ; 99,5 % pour deux connexions fusionnées | réception - bloc : P50 -0,21 s, P99 1,3 à 1,7 s |
| Polygon `OrderFilled` v2 (publicnode) | logs | bloc + logIndex | oui (maker du fill preneur) | oui (tokenId) | non (via Gamma) | oui (montants) | complet si rattrapé (2 trous de 1 à 2 blocs rattrapés, 174 logs) | P50 -0,7 s, mais **P90 182 s, P99 255 s** (nœud en retard) |
| data-api `/trades` | historique, vérité de contrôle | bloc (s) | oui | oui | oui | oui | complet (régression 100 %) | minutes (phase 13) |
| Gamma | jeton → marché, outcome | | | | vérité D | | | |
| P12 | carnet seul | heure d'échange | **non** | oui | oui | oui | journal des signaux seulement | |
| P13 | SIG_HIST par RTDS + chaîne (107 wallets) | | oui | oui | depuis la liste Gamma de démarrage | | journal des alertes seulement | |
| P14 | 2e achat par RTDS + chaîne (wallets d'alerte) | | oui | oui | | | journal des fenêtres et des 2e achats | |

**Horloge :** temps Unix UTC partout ; Mac décalé de +0,03 à +0,11 s (SNTP, time.apple.com).

**Identifiants :** le hash de transaction est le même dans RTDS, le carnet, la chaîne et le data-api. Il n'existe pas d'identifiant de fill commun.

---

## 1. L'univers des marchés est-il correctement couvert ?

**MESURÉ** (`phase15_market_coverage.csv`)

**Univers live** (actif, volume ≥ 10 000 $, non exclu) : 3 988 marchés.
- Abonnés au carnet P11 ou P12 à un moment : **1 044 (26 %)**, qui portent **64 à 65 % du volume preneur**.
- Marchés de type phase 8 encore actifs (≥ 250 000 $) : 719, dont 319 abonnés (44 %).

**Règles d'exclusion :**
- même motif EXCL qu'en phase 8 ;
- le direct ajoute GAME (codes d'équipes + date) et abaisse le seuil de volume (10 000 $ au lieu de 250 000 $) ;
- aucune des 1 985 alertes historiques ne serait exclue en direct.

**Identification du marché par RTDS** (période P11, 304 597 lignes) :
- 1 580 jetons, soit **890 marchés**, n'arrivent **jamais** avec `conditionId`, et les 9 868 autres **toujours**. C'est déterministe par marché.
- Ces lignes ont aussi `slug`, `eventSlug` et `outcome` vides, et `outcomeIndex` = 0, ce qui est **faux pour 13 %** d'entre elles (jetons NO).
- Ce ne sont pas seulement des marchés récents :
  - Fed d'octobre (5,5 M$ de volume) ;
  - cessez-le-feu US x Iran (0,94 M$) ;
  - oléoduc saoudien, Houthis, Russie contre UE ;
  - Oklahoma et Louisiane (moratoire data centers).
- Part de ces lignes : **18 %** des lignes preneur de l'univers live, et **13 %** des achats d'au moins 250 $.
- Parmi les 778 marchés de l'univers qui ont tradé, 127 (16 %) n'ont jamais de nom.

| Champ RTDS | CORRECT | MISSING | WRONG |
|---|---|---|---|
| `conditionId` | 92,3 % des lignes | 7,7 % | 0 % |
| `outcomeIndex` si `conditionId` présent | 100 % | | |
| `outcomeIndex` si `conditionId` vide | 87 % | | 13 % |

**Le marché n'est jamais DELAYED dans RTDS :** il ne se résout pas plus tard.

**Que fait chaque processus d'une ligne sans marché :**
- **listener P11 :** il crée un faux marché `''` commun à tous ces trades et y calcule p_before, FOLLOW et l'historique des wallets ;
- **P13 :** il ignore la ligne. Son état de ces marchés vieillit (prix STALE), sauf pour les 107 wallets suivis par la chaîne.

**INFÉRÉ**
- La cause est côté serveur RTDS (métadonnées absentes pour certains marchés), pas une perte réseau.

**PROCHAINE ÉTAPE**
- Résoudre marché et outcome **depuis le jeton** (Gamma), et ne jamais utiliser `conditionId` ni `outcomeIndex` de RTDS.

---

## 2. Les trades sont-ils correctement capturés ?

**MESURÉ, audit live** (vérité : fills preneur de la chaîne, 2 h 26, 151 313 trades ; `phase15_trade_coverage.csv`)

| Source | Rappel | Précision | Remarque |
|---|---|---|---|
| RTDS A (connexion continue) | **96,4 %** | 100 % | 7 silences de 30 s et 1 fermeture ; avant le premier silence, 99,96 % |
| RTDS B (coupée 7 fois 30 s, volontairement) | 95,8 % | 100 % | plus 4 silences |
| **RTDS du collecteur P11** (production) | **95,8 %** | 100 % | silences |
| A ou B | **99,5 %** | | à 12:28:40, A et B se sont tues **ensemble** |
| Carnet P11, marchés abonnés à l'heure du trade | **99,8 %** (2 537/2 542) | | |
| Chaîne du collecteur P11 (wallets filtrés) | **80 %** (36/45) | | nœud bloqué ou en retard ; P99 33 s |

**Une perte vient du serveur RTDS lui-même :** les 17 trades d'un même bloc (11:46:06) n'ont été reçus par **aucune** des 3 connexions RTDS.

**MESURÉ, période P11** (vérité data-api sur 69 marchés, 276 trades) :
- rappel du RTDS du collecteur : 91 % ;
- 71 % sur les marchés sans `conditionId` (l'échantillon contient la minute Oklahoma) ;
- **temps aveugle du RTDS du collecteur : 907 s sur 9 432 (9,6 %)**, en 13 trous de plus de 5 s : 7 silences de 30 s et des redémarrages de 1 à 3 min.

**Redémarrages :**
- le listener ne traite rien entre la fin de son rattrapage et son abonnement RTDS : **296 à 301 s perdues à chacun de ses 3 démarrages** ;
- P13 : 360 s (de 10:18:34 à 10:24:34).

**Doublons (§10, `phase15_duplicates.csv`) :**
- **aucun vrai doublon RTDS** :
  - 40 groupes de lignes identiques sur 40 sont des fills distincts (contrôle data-api) ;
  - audit live : 19 322 groupes de lignes identiques, aucun vrai doublon d'après le nombre de fills de la chaîne ;
- dont 1 808 TIMESTAMP_ALIAS : même transaction, même wallet, deux horodatages RTDS (écart de 1 s) ;
- **88 logs chaîne en double** (reçus en direct puis rattrapés), éliminés par la clé (tx, logIndex) ;
- carnet : 0 doublon ;
- SAME_TRADE_DIFFERENT_ID : 0, puisque toutes les sources partagent le hash de transaction.

**Attention :** une déduplication naïve des lignes RTDS identiques supprimerait 1 851 vrais fills.

**INFÉRÉ**
- La capture est complète quand la connexion est vivante. Les pertes sont des trous de temps, pas un tri.

---

## 3. Les wallets sont-ils correctement identifiés ?

**MESURÉ** (`phase15_wallet_audit.csv`, audit live, trades d'au moins 100 $)

| Statut du preneur dans RTDS | Trades | Wallet de la règle du listener = preneur de la chaîne |
|---|---|---|
| une seule ligne `fee` | 8 114 | **99,99 %** |
| ambigu (aucune ligne `fee`, ou plusieurs) | 437 (5,1 %) | **22 %** |
| ensemble (8 552) | | 96,0 % |

**Les cas ambigus sont les marchés sans frais :**
- RTDS ne publie jamais `fee` = 0 : il omet le champ ;
- dans les marchés suivis, 30 à 48 % des achats d'au moins 250 $ sont ambigus (bout en bout) ;
- seules **17 %** des alertes SIG_HIST historiques ont payé des frais : TRAIN 0 %, VALID 18 %, TEST 32 %.

**Le bon wallet est presque toujours présent :** le wallet du preneur figure parmi les lignes RTDS dans 99,94 % des cas. Le défaut est la **sélection** de la ligne, pas l'absence d'information.

**Proxy, relayer, EOA :** `proxyWallet` RTDS = champ maker du fill preneur de la chaîne = `proxyWallet` du data-api. Aucune confusion observée.

**Règle « ambiguë » du listener :**
- il met en tête toute ligne d'achat d'au moins 250 $ d'un wallet **éligible**, puis la première ligne reçue ;
- un **maker** éligible est donc traité comme preneur : c'est l'alerte A2, non confirmée par le data-api à 60 s et 600 s.

**PROCHAINE ÉTAPE**
- Identifier le preneur par la chaîne (fill dont le taker est le contrat d'échange) ou par la ligne dont la taille égale la somme des autres.
- Ne pas émettre d'alerte avant cette confirmation.

---

## 4. Les timestamps sont-ils fiables ?

**MESURÉ** (`phase15_latency.csv`)

Les horodatages se suivent toujours dans le même ordre :

| Étape | Délai | Horloge |
|---|---|---|
| Heure d'échange (`last_trade_price`, ms) | référence | |
| Réception carnet | + 29 à 140 ms (P50) | locale |
| Horodatage RTDS (secondes) | + 1,3 s (P50) | |
| Bloc Polygon (= horodatage data-api, 30 sur 30) | + 2,2 s (P50) | |

**Écarts entre sources :**
- horodatage RTDS moins horodatage de bloc : **-1 s le plus souvent** (-2 à +1 ; +4 au maximum en direct) ;
- RTDS est reçu **avant** l'horodatage de son bloc (P50 -0,21 s) : il publie au moment de l'appariement.

**Le bug d'une seconde de la phase 14 est expliqué :**
- T1 venait de RTDS (`ts_echange` du listener), T2 du data-api (bloc) ;
- l'écart systématique est de -1 s ;
- il faut toujours comparer des horodatages de même nature.

**Horloge locale :** fiable à 0,1 s près.

**Le nœud publicnode n'est pas une horloge fiable :** ses en-têtes arrivent jusqu'à 280 s en retard (hors veille).

**INFÉRÉ**
- Les horodatages sont **réconciliés**. Le risque est leur mélange, pas leur qualité.

---

## 5. Les prix sont-ils fiables ?

**MESURÉ** (`phase15_price_audit.csv`, audit live)

| Ligne retenue | CORRECT | ROUNDING | WRONG_TOKEN | WRONG |
|---|---|---|---|---|
| ligne `fee` (preneur marqué) | **100 %** | | | |
| ligne du preneur lui-même | 99,94 % | | | |
| règle du listener, cas ambigus d'au moins 100 $ (437) | 35 % | 4 % | **55 %** | 7 % |
| ensemble des trades d'au moins 100 $ (8 552) | 96,8 % (avec ROUNDING) | | | |

**Autres écarts :**
- **WRONG_SIDE :** sur une ligne sans `conditionId`, le prix d'un jeton NO est lu comme un prix YES (13 % de ces lignes) ;
- **STALE :** le listener traite les trades dans l'ordre d'arrivée RTDS, pas dans l'ordre d'exécution.

**Prix de référence (p_before) des alertes live contre la vérité** (dernier trade preneur d'au moins 100 $ avant le trade, dans l'ordre d'exécution du data-api ; `phase15_alertes_live_audit.csv`) :

| Alerte | p_before du processus | Vérité | Classe |
|---|---|---|---|
| A1 Likud (listener) | 0,83 | 0,87 | **STALE** (le trade précédent, dans la même seconde, est traité après) |
| A2 Israël x Iran (listener) | 0,19 | 0,19 | correct, mais **mauvais wallet** |
| A3 CNN (listener) | 0,91 | 0,882 | **faux marché** `''` |
| A4 OpenAI, prix du millénaire (listener) | 0,25 | 0,25 | CORRECT |
| A5 Fed + 25 pb en octobre (listener) | **0,61** | **0,36** | **faux marché** `''` (25 points d'écart) |
| A6 OpenAI, faillite (listener) | 0,93 | 0,93 | CORRECT |
| P3 et P7 (P13, mêmes trades que A4 et A6) | 0,25 ; 0,93 | 0,25 ; 0,93 | CORRECT |
| Oklahoma (listener, sans alerte) | 0,95 | 0,66 | **faux marché** `''` |
| Oklahoma (P13) | 0,66 | 0,66 | CORRECT |

**Risque STALE sur l'historique :** 3,1 % des alertes SIG_HIST historiques ont un trade d'au moins 100 $ dans la même seconde juste avant.

---

## 6. Les reconnexions créent-elles des trous ?

**MESURÉ** (`phase15_reconnect.csv`)

**Coupures volontaires de RTDS B** (7 coupures de 30 s) :
- 300 à 585 trades vérité par trou ; **B en manque 92 à 96 %** (le reste arrive avant la coupure) ;
- **tous** sont vus par A ;
- RTDS ne rejoue rien ;
- aucun doublon après la reconnexion.

**Silences non provoqués pendant l'audit :**
- **A :** 7 silences de 30 s et 1 fermeture ; 566 à 1 035 trades par trou, dont 88 à 95 % perdus ;
- **B :** 4 silences ;
- **silence simultané :** à 12:28:40, A et B se taisent ensemble. A perd 646 trades, dont B n'en voit que 50 : **deux connexions ne suffisent pas toujours**.

**Silences en production** (un par connexion, à des heures différentes) :

| Processus | Silences de 30 s |
|---|---|
| collecteur RTDS | 9 |
| listener | 7 |
| P13 | 4 |
| P14 | 1 |

**Chaîne :**
- 24 blocages « aucun bloc depuis 60 s » au collecteur ;
- 430 blocs sur 5 447 jamais reçus par le collecteur (7,9 %), jamais rattrapés ;
- dans l'audit, les deux trous d'en-têtes ont été **rattrapés par `eth_getLogs`** (174 logs).

**Veille du Mac, de 14:04:39 à 21:24:33 UTC** (`pmset` : « Clamshell Sleep », sur batterie) :
- aucun message reçu par aucun processus pendant **7 h 20** ;
- au réveil, chaque processus se reconnecte, sans rattrapage.

**Réponse : oui.**
- En production, un trou de 30 s fait perdre les trades de ces 30 s au processus, définitivement.
- Les données existent ailleurs (autre connexion, data-api, `eth_getLogs`), mais aucun processus ne va les chercher.

---

## 7. Les processus peuvent-ils être vivants mais aveugles ?

**Oui, mesuré** (`phase15_watchdog.csv`).

| Processus | Vivant | Battement avec compteur | Aveuglement constaté |
|---|---|---|---|
| **Les 5 processus** | oui, toute la journée | | **7 h 20 sans aucune donnée** (veille capot fermé) ; `caffeinate -is` ne l'empêche pas sur batterie |
| Collecteur RTDS | oui | oui | 30 s par silence, 9 fois en 3,6 h |
| Collecteur chaîne | oui | oui | nœud en retard jusqu'à 270 s ; blocs perdus |
| Listener P11 | oui | toutes les 10 min | silences + **aveugle en permanence** aux 890 marchés sans `conditionId` |
| P12 | oui | **non** | indétectable dans ses journaux |
| P13 | oui | **non** | chaîne aveugle jusqu'à 600 s (délai de son chien de garde) |
| P14 | oui | sans compteur de messages | chaîne : aucun chien de garde |

**Les superviseurs relancent bien les processus :** `p1x_run.sh`, reconnexion en 1 à 2 s. C'est le flux qui n'est pas surveillé.

---

## 8. Pourquoi P11 et P13 ont-ils divergé sur Oklahoma ?

Reconstruction : `phase15_oklahoma_timeline.csv`.

| Temps (UTC) | Événement |
|---|---|
| 29/09 15:56 | marché créé (Gamma) ; jeton NO = `1398563…` |
| **01/10 10:29:02,731** | **listener P11** reçoit le trade par RTDS : `conditionId` **vide**, `outcomeIndex` 0 (vrai : 1). Rangé dans le pseudo-marché `''` : p_before 0,95 (vrai : 0,66) et dpre_10m 0,15, venus d'autres marchés, donc FOLLOW, donc pas d'alerte. |
| 10:28:59 à 10:29:30 | **collecteur P11** : connexion RTDS silencieuse, trade non enregistré |
| 10:29:03 | bloc 94 763 602 : achat NO à 0,66, 2 030 $ par `0x7c3db723` (data-api, reçu de transaction) |
| | **carnet P11 et P12** : marché jamais abonné |
| 10:29:31,157 | **P13** reçoit le log de la chaîne (28 s de retard du nœud) ; marché retrouvé par le jeton (sa liste Gamma) ; p_before 0,66 correct ; hist_n 413 → alerte SIG_HIST_V1. La ligne RTDS sans marché avait été **ignorée** par P13. |
| 10:44:38 | **P14** ouvre la fenêtre de 2e achat sur l'alerte P13 |

**Réponse.** Ce n'est pas un bug isolé, mais le cumul de deux défauts systématiques et d'un trou :
1. le marché vide de RTDS ;
2. le faux marché commun du listener ;
3. le silence de la connexion du collecteur.

**P13 avait raison :** il a pris le marché depuis le jeton et le wallet depuis la chaîne.

**Ampleur :**
- jusqu'à la veille, 62 FAE du listener (sur 284) sont dans le pseudo-marché ;
- 36 wallets ont reçu un FAE non-FOLLOW dont le résultat sera calculé sur le faux marché. Leur historique SIG_HIST en direct est donc **contaminé** au fil des heures.

---

## 9. Combien d'alertes SIG_HIST historiques auraient été détectables ?

Table : `phase15_sig_hist_replay.csv`. Taux mesurés appliqués aux 1 985 alertes ; SIG_HIST n'est pas recalculé.

| Étape | Taux | Alertes |
|---|---|---|
| Exclues par les règles du direct | 0 % | 0 |
| Reçues par une connexion RTDS de production | 95,8 % | **≈ 1 902** |
| … avec un `conditionId` présent (87 %) | | **≈ 1 656 (83 %)** |
| … avec un preneur marqué par `fee` | 17 % | ≈ 280 (17 % des 1 656) |
| … sinon, règle « éligible et achat d'au moins 250 $ » | | le vrai preneur est traité, mais tout maker éligible de la même transaction l'est aussi |
| Risque de p_before STALE (même seconde) | 3,1 % | |
| Hors trous de démarrage et hors veille du Mac | | dépend du nombre de redémarrages et de la veille |

**INFÉRÉ**
- Environ **4 alertes historiques sur 5** seraient calculées sur le bon marché et le bon wallet.
- Mais le flux en direct contiendrait aussi des **fausses alertes** (makers éligibles, faux marché). Sur les 6 alertes réelles du listener, 3 sont fausses.

**INCONNU**
- La part exacte de fausses alertes sur un grand nombre de cas. Elle dépend du nombre de makers éligibles par transaction.

---

## 10. L'infrastructure est-elle assez fiable pour interpréter les futures données en direct ?

**Non, en l'état.**

| # | Critère (§23) | État |
|---|---|---|
| 1 | couverture des marchés connue | **oui** (26 % des marchés, 65 % du volume ; 890 marchés sans nom dans RTDS) |
| 2 | couverture des trades connue | **oui** |
| 3 | pertes ≤ 1 % sur le RTDS du listener | **non** (95,8 % par connexion ; 9,6 % de temps aveugle sur la période P11 ; 7 h 20 de veille) |
| 4 | doublons mesurés | **oui** (aucun vrai doublon RTDS) |
| 5 | timestamps réconciliés | **oui** |
| 6 | prix WRONG ≤ 0,1 % (≥ 100 $) | **non** (3,2 % par la règle du listener ; 13 % de mauvais outcome sur les lignes sans marché) |
| 7 | wallets faux ≤ 0,1 % (≥ 100 $) | **non** (4,0 % ; 78 % en cas ambigu) |
| 8 | reconnexions testées | **oui** (perte totale du trou, aucun rattrapage) |
| 9 | chiens de garde testés | **oui** (vivant mais aveugle démontré) |
| 10 | SIG_HIST historique rejouable | **partiel** (≈ 83 % bien calculées, avec des fausses alertes) |
| 11 | cas Oklahoma expliqué | **oui** |
| 12 | aucune divergence critique inexpliquée | **non** : les divergences sont expliquées, mais critiques |

**Ce que cela change aux phases précédentes :**
- **Phases 8 à 14, historique :** data-api et flux de la phase 10, validés par la régression (§11). **Inchangées.**
- **Phase 11 :**
  - l'alerte A1, utilisée dans les rapports des phases 11 et 13, est valide (preneur confirmé) ;
  - A4 et A6 sont valides ;
  - A2 est une **fausse alerte** ; A3 et A5 reposent sur un faux marché ;
  - la cible des « 100 alertes confirmées » n'est pas interprétable sans tri.
- **Phase 14 :** le journal papier a ouvert des fenêtres sur A2, A3 et A5. Il faut les écarter ou les marquer à l'analyse.
- **Phase 11, objectif « 6 semaines » :** chaque fermeture du capot sur batterie coupe toute la collecte.

## 11. Tests de régression et cas particuliers

**Maduro et Iran** (`phase15_regression_maduro_iran.csv`) :
- 4 379 et 21 168 trades preneurs relus aujourd'hui, **identiques** à la phase 10 (transaction, wallet, horodatage, prix, côté, outcome, taille) ;
- outcome conforme à Gamma : 100 % ;
- horodatage data-api = bloc : 15 sur 15 pour chaque fenêtre.

**Les 8 comptes** (`phase15_comptes8.csv`) :
- **aucun trade depuis février 2026** (derniers le 28/02) ;
- l'absence d'alerte en direct vient donc de leur **inactivité**, pas de la couverture ;
- historiquement, aucun ne s'est jamais qualifié (phase 13).

**Watchlist** (`phase15_watchlist_audit.csv`) :

| Processus | Wallets surveillés |
|---|---|
| P11 listener, P13 | 107 éligibles |
| filtre chaîne du collecteur | 164 |
| P12 | aucun (par construction) |
| P14 | 5 wallets d'alerte |

- 17 des 107 wallets ont tradé pendant la période P11 ; tous sont vus par RTDS et par la chaîne au moins une fois.
- **Un wallet surveillé qui trade est-il vu de tous ?**
  - P12 : jamais ;
  - P14 : seulement pendant une fenêtre d'alerte ;
  - P11 et P13 : oui, hors silences ; mais le marché est faux une fois sur 8 (listener) ou le trade est ignoré (P13, sans la chaîne).

**Bout en bout** (`phase15_end_to_end.csv`, **239 trades** : achats d'au moins 250 $ sur les marchés abonnés ; 77 sur la période P11, 162 pendant l'audit) :
- **131 FAE** au sens de la définition (achat preneur d'au moins 250 $, sans trade preneur d'au moins 100 $ du wallet dans le marché depuis 24 h) ;
- le listener en enregistre **90 avec le bon wallet (69 %)**, 3 avec un mauvais wallet ;
- il en manque 38, dont 29 ambigus et 5 sur un marché vide ;
- il enregistre aussi 16 FAE hors définition ;
- délais médians après la réception du carnet : RTDS +2,2 s, chaîne +1,5 s (wallets filtrés), listener +2,1 s.

## 12. Limites

- **Audit live :** 2 h 26 au lieu des 3 h prévues, à cause de la veille du Mac. Le volume (151 313 trades vérité) suffit pour toutes les mesures.
- **Univers suivi par P13 :** sa liste Gamma de démarrage n'est pas journalisée ; elle est déduite des règles (« probable »).
- **P12, P13, P14 :** ils ne journalisent pas les trades reçus. Leur couverture par trade est INCONNU, sauf via les alertes et la chaîne.
- **Rejeu SIG_HIST :** c'est une **application de taux** mesurés, pas un rejeu événement par événement : les marchés historiques sont fermés, et RTDS ne rejoue rien.

## Prochaine étape

Correctifs à décider par l'utilisateur. Aucun n'a été appliqué : c'était un audit.

1. **Marché :** résoudre marché et outcome par le jeton (table Gamma), en ignorant `conditionId` et `outcomeIndex` de RTDS.
2. **Preneur :** le confirmer par la chaîne ou par l'égalité des tailles avant toute alerte ; journaliser le statut.
3. **Ordre :** traiter dans l'ordre (bloc, logIndex) quand deux trades tombent dans la même seconde.
4. **Trous :**
   - garder deux connexions RTDS et fusionner (rappel 99,96 %) ;
   - après chaque reconnexion, rattraper la fenêtre par le data-api ;
   - au démarrage, s'abonner **avant** le rattrapage.
5. **Chaîne :** rattrapage `eth_getLogs` et surveillance du retard des en-têtes.
6. **Battements :** un compteur de messages par minute pour P12, P13 et P14.
7. **Veille :** laisser le Mac sur secteur, capot ouvert, ou déplacer la collecte sur une machine qui ne dort pas. Après chaque réveil, rattraper la période par le data-api.
8. **Après correction :** relancer `p15_audit.py` (même protocole) et revalider. Écarter ou marquer A2, A3 et A5, et l'historique des wallets du listener depuis le 01/10 08:51.
