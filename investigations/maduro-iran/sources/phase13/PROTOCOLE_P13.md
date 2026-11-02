# Phase 13 : protocole pré-enregistré

Rédigé le 01/10/2026 vers 10:10 UTC, **avant toute mesure de la phase 13**.

**Ce qui ne change pas :**
- SIG_HIST V1 est gelé (`phase11/SIG_HIST_VERSION.json`) : seuils, historique minimal, univers, outcome.
- Les phases 11 et 12 continuent sans modification. La phase 13 lit leurs données en lecture seule et ajoute ses propres processus.
- Aucun ordre, aucun classement public de wallets, aucune conclusion « insider ».

## 1. Les trois temps

| Temps | Définition |
|---|---|
| **T_EXEC** | heure d'échange (ms) du `last_trade_price` portant le hash du trade du wallet. Sa réception locale arrive ~20 ms plus tard ; les mises à jour du carnet ~20 ms plus tôt |
| **T_DETECT(source)** | réception locale du premier message de cette source qui identifie le wallet (RTDS, logs Polygon, data-api). T_DETECT réaliste = la plus rapide des sources réellement branchées |
| **T_EXEC_OBSERVER** | T_DETECT + temps de calcul de SIG_HIST (mesuré) + délai d'envoi d'un ordre. Ce dernier n'est pas mesurable sans ordre réel : hypothèses 0, 100 et 250 ms, publiées séparément |

**Mesures dérivées :**
- IDENTIFICATION_LATENCY = T_DETECT − T_EXEC ;
- EXECUTION_LATENCY = T_EXEC_OBSERVER − T_EXEC ;
- REMAINING_EDGE = prix futur (mid à +60 s et +300 s) − VWAP disponible à T_EXEC_OBSERVER.

## 2. Comparaison des sources (§4, §5)

**Sources testées en parallèle**, pendant la même fenêtre, sur les mêmes marchés :
- RTDS ;
- websocket Polygon publicnode (`eth_subscribe logs`) ;
- un second fournisseur RPC public s'il accepte `eth_subscribe` ;
- data-api `/trades` interrogé par marché en boucle.

**Référence :** `last_trade_price` du websocket du carnet.

**Par source :**
- latence P10, P50, P90, P99 ;
- pertes : trade vu dans le carnet et jamais vu par la source dans les 60 s ;
- doublons ;
- inversions d'ordre par rapport au carnet ;
- reconnexions.

**Par catégorie** (`latency_distribution.csv`) : marché, taille (< 100, 100-1 000, ≥ 1 000 $), jeton, direction, minute, nombre de trades dans le même bloc.

## 3. Watchlist (§6)

Elle est calculée avec le détecteur V1 rejoué (historique + rattrapage), donc avec l'état connu au démarrage.

| Classe | Définition |
|---|---|
| **KNOWN_HIGH_LEAD** | qualifié (hist_n ≥ 5 et hist_score ≥ seuil) avec hist_n ≥ 10 |
| **NEWLY_QUALIFIED** | qualifié avec hist_n de 5 à 9 |
| **UNKNOWN** | tous les autres wallets |

`wallet_watchlist.csv` est local, jamais publié.

## 4. Courbe de latence et capacité (§8 à §12), sur le carnet réel enregistré (phase 11)

**Événements :**
- **principal :** les alertes SIG_HIST V1 ;
- **élargi :** tout achat preneur de 250 $ ou plus d'un wallet de la watchlist, sur un marché dont le carnet est enregistré. Il est publié séparément et ne remplace jamais le principal.

**Exécution simulée :**
- **entrées contrefactuelles** à T_EXEC + L, avec L = 0, 100, 250, 500, 750 ms, 1, 1,5, 2, 3, 5 et 10 s ;
- **entrée réaliste** à T_DETECT mesuré pour chaque source ;
- **tailles :** 50, 100, 250, 500, 1 000, 2 500 et 5 000 $ ;
- **calcul :** carnet connu à l'instant de décision (jamais de profondeur future), sortie sur le carnet à +60 et +300 s, frais du marché.

**Lecture de la courbe :**
- **INFORMATION LIMIT** si le net reste > 0 à 1-2 s ;
- **LATENCY LIMIT** s'il devient ≤ 0 dès quelques centaines de ms.

**Taille maximale exécutable :** plus grande taille dont le net moyen reste > 0.

## 5. Second trade et continuation (§13 à §15), historique, découpage TRAIN, VALID, TEST de la phase 9

**SIG_HIST_SECOND :**
- après une alerte SIG_HIST V1, le **deuxième achat** du même wallet sur le même jeton, dans une fenêtre W ;
- W est choisi sur TRAIN parmi 300, 1 800 et 3 600 s (le W qui maximise le nombre de seconds achats suivis d'un mouvement de 3 points à 60 min). Il est gelé avant VALID.
- **outcome :** variation du prix des autres entre le prix du 2e achat et 60 min plus tard ; taux LEAD60 et FT.

**Contrôle :** deuxième achat d'un FAE de contrôle (même règle).

**Continuation :** achats de rang 1, 2, 3 et 4 d'une séquence (même wallet, même jeton, écart < W) ; outcome après chacun.

**Délai disponible :** entre l'identification du 1er achat (T_DETECT ≈ T_EXEC + 1,75 s, latence live médiane) et le 2e achat. On mesure aussi la variation de prix qui a eu lieu entre les deux.

## 6. Wallet déjà actif et positions (§16, §17)

**Features antérieures à T, calculées sur les trades ≥ 100 $ :**
- temps depuis le dernier trade du wallet ;
- direction et marché du dernier trade ;
- nombre de marchés distincts sur 24 h ;
- fréquence sur 24 h ;
- position nette sur le jeton avant le trade.

**Tests :**
- prédire, sur TRAIN, qu'un wallet de la watchlist va déclencher SIG_HIST dans les 10 min, puis vérifier sur VALID et TEST ;
- signal plus fort quand la position passe de faible à forte (ratio après/avant).

## 7. Nouveaux wallets (§21, §22)

Pour les wallets qualifiés un jour :
- nombre de FAE résolus et délai (jours) entre le premier trade et la qualification ;
- part des wallets ayant 1 à 4 FAE résolus qui disparaissent (aucun trade ≥ 100 $ dans les 30 jours suivants) avant de se qualifier.

**Filtres de priorisation** (âge du wallet, financement, choix de marché) : taux de qualification future par classe. Ce sont des filtres de surveillance, jamais une preuve.

## 8. Cas (§18, §19, §20)

**8 comptes :** présence dans la watchlist, qualification, trades après le premier historique, continuation, financement (en feature séparée).

**Maduro** (`0x31a56e9e`, `0x6baf05d1`) **et Iran** (`0x4dfd481c`) :
- statut SIG_HIST V1 à l'instant du trade ;
- T_EXEC ;
- T_DETECT estimé (distribution live : P10, P50, P90) ;
- T_REPRICING ;
- T_PUBLIC (VERIFIED ou APPROXIMATE) ;
- prix observé à chaque étape.

Le prix observé est celui du prochain trade d'un autre wallet après l'instant ; le carnet complet d'époque n'existe pas. Pour l'Iran, les deux définitions du début de l'anomalie sont conservées.

## 9. Paper trading (§23)

`p13_paper.py`, processus séparé, **PAPER ONLY** :
- il identifie les wallets de la watchlist par la voie la plus rapide (logs Polygon filtrés sur ces wallets + RTDS) ;
- il calcule SIG_HIST V1 ;
- il prend une entrée papier sur le carnet REST au moment de la détection, puis des sorties papier à +60 et +300 s.

Chaque alerte est journalisée, y compris les pertes.

## 10. Critères (§24) et diagnostic (§25)

Les 10 critères de la mission doivent tous être remplis, avec :
- VALID et TEST pour les tests historiques ;
- le direct pour l'exécution.

Sinon, la cause est classée parmi : WALLET IDENTIFICATION TOO SLOW, MARKET MOVES TOO FAST, INSUFFICIENT LIQUIDITY, SIGNAL DISAPPEARS AFTER OBSERVATION, NO NET EDGE.
