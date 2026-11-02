# Phase 14 : protocole pré-enregistré (exécution du 2e achat)

Rédigé le 01/10/2026 vers 10:45 UTC, **avant tout calcul de résultat de la phase 14**.
Seuls des faits de structure ont été lus : définitions, scripts, format des données.
Toute déviation sera signalée dans le rapport.

**Question :** le 2e achat du même wallet fournit-il une fenêtre d'exécution réellement exploitable ?

**Interdits :**
- modifier SIG_HIST V1 (sha256 bbb016d2…) ou créer une variante ;
- changer un seuil ;
- passer un ordre réel ;
- utiliser une information non publique ;
- exclure un cas après coup, ou décider de l'éligibilité avec un prix ou une résolution futurs.

## 1. Définitions reprises telles quelles

| Élément | Source | Définition |
|---|---|---|
| Alertes SIG_HIST V1 | `p9/events_final.pkl`, colonne `SIG_HIST` (phase 9, inchangée) | 1 985 alertes : TRAIN 688, VALID 561, TEST 736 |
| Contrôles appariés | `p10/windows.pkl`, groupe `CONTROLE` (phase 10 : même strate, FAE non-FOLLOW, non SIG_HIST) | 1 964 événements |
| Découpage | `endDate` du marché (phase 8) | TRAIN < 01/03/2026 ≤ VALID < 01/06/2026 ≤ TEST |
| **2e achat** | `p13_second_trade.py`, fonction `seq`, avec W = 3 600 s gelé sur TRAIN (`phase13/frozen_p13.json`) | **premier** trade preneur BUY d'au moins 100 $ (`p9/prints.pkl`) du **même wallet** sur le **même jeton**, avec T1 < T2 ≤ T1 + 3 600 s (horodatage à la seconde, donc strictement après la seconde de T1) |
| LEAD60 du 2e achat | phase 13, fonction `outc` | p_before_2 = dernier print (tous wallets) avant T2 ; p60 = dernier print d'un autre wallet dans ]T2, T2 + 3 600 s] ; LEAD60_2 = (p60 − p_before_2 ≥ 0,03) ; sans print, 0 |

**Contrôle de reconstruction, obligatoire avant toute simulation :**
- la reconstruction doit redonner exactement les comptes de `phase13/second_trade.csv` : 118 2e achats SIG_HIST en VALID et 133 en TEST, plus les autres cases ;
- elle doit aussi redonner les T2 de `phase13/second_trade_detail.csv`.

Si l'un ou l'autre diffère, l'analyse s'arrête.

**Population de référence (premier achat) :** les mêmes alertes, à T1, passées dans le même code d'exécution, pour répondre au §9 de la mission. Ce n'est pas un nouveau signal.

## 2. Les temps

| Temps | Historique (janvier à septembre 2026) | Direct (données de la phase 11, depuis le 01/10 08:51 UTC) |
|---|---|---|
| T_trade (T2) | horodatage de bloc du data-api (1 s) | heure d'échange du `last_trade_price` (ms) |
| T_wallet | **non observé.** T2 + L, avec L tiré des mesures de la phase 13 | réception locale du premier message qui nomme le wallet (RTDS ou chaîne) |
| T_book | heure du premier repère de carnet observable après T_OBS : achat-équivalent d'un autre wallet dont les niveaux makers sont consommés (phase 10) | premier état du carnet reconstruit après T_wallet (`p11_replay.Timeline`) |

**Scénarios de connaissance du wallet (§13) :**
- **ORACLE :** L = 0. Premier repère après le 2e achat dans l'ordre d'exécution, même bloc compris (OBSERVER_0 de la phase 10). Personne ne peut l'atteindre.
- **RÉALISTE (principal) :** L = 2 s. Les sources mesurées en phase 13 ont une médiane de 1,19 à 2,08 s, et le P90 de la meilleure voie est de 1,6 à 2,2 s. Le bloc Polygon dure environ 2 s.
- **RÉALISTE prudent :** L = 5 s, au-delà du P99 de RTDS (3,94 s).
- **Courbe :** L = 0, 1, 2, 5, 10, 20, 30, 60, 120 et 300 s (liste de la phase 10).

T_OBS = T2 + L. Aucune décision n'utilise de trade postérieur à T_OBS. Seule la mesure de l'exécution lit les fills qui suivent, comme en phase 10.

## 3. Carnet autour de T_OBS (§6)

**Historique.** Le carnet complet n'existe pas : `/book` répond 404 sur un marché fermé (`phase10/CLOB_DATA_AUDIT.md`). On mesure seulement :
- **best ask :** premier niveau du repère ;
- **profondeur consommée observée** dans les 10 s du repère, jusqu'à +0,5, +1 et +2 points au-dessus du best ask, et au total. C'est une **borne basse**, jamais la profondeur disponible ;
- **best bid, mid et spread :** seulement si une vente-équivalente d'un autre wallet a lieu dans [T_OBS − 2 s, T_OBS + 2 s]. Sinon : **UNKNOWN / NO BOOK DATA** ;
- **consommation du 2e achat lui-même :**
  - nombre de niveaux ;
  - premier niveau (ask juste avant) et dernier niveau ;
  - VWAP ;
  - glissement = VWAP − premier niveau ;
- **distance** = best ask à T_OBS − prix payé par le wallet au 2e achat.

Fenêtre sans flux, ou 2e achat introuvable dans le flux : **UNKNOWN / NO BOOK DATA**. Aucun carnet estimé.

**Direct.** Carnet complet reconstruit (`p11_replay.Timeline.book_at`) : best bid, best ask, mid, spread, profondeur à ±0,5, ±1 et ±2 points, profondeur totale.

## 4. Entrée simulée (§7)

**Tailles :** 50, 100, 250, 500 et 1 000 $.

**Estimateurs historiques**, repris de la phase 10 et gelés :

| Estimateur | Statut | Règle |
|---|---|---|
| **FLUX** | **principal** | L'observateur paie les niveaux réellement consommés par les achats-équivalents des autres wallets dans les 60 s après T_OBS. |
| STRICT | sensibilité | repère dans [T_OBS, T_OBS + 2 s] ; niveaux du repère et des achats-équivalents dans les 10 s |
| SUIVANT | sensibilité | comme STRICT, mais repère accepté jusqu'à T_OBS + 60 s |

**Pourquoi FLUX en principal :**
- la phase 10 a montré que STRICT n'est observable que dans 0,7 à 1,5 % des alertes ;
- ce choix est fait avant tout résultat de la phase 14 ;
- **approximation connue :** des niveaux pris plus tard peuvent avoir été posés après T_OBS.

**Capacité :**
- si les niveaux observés ne suffisent pas, on prend la partie réellement exécutable et on la marque **CAPACITY_LIMIT** ;
- aucun niveau n'est inventé ;
- trois statuts : entièrement exécutable, partiel (CAPACITY_LIMIT), impossible (aucun niveau).

**Direct :** parcours des asks du carnet connu à T_OBS.

## 5. Sortie (§8)

**Horizons :** 1, 5, 10, 30, 60, 120, 300 et 600 s, comptés depuis T_OBS, plus la résolution.

**Sortie historique** (règle de la phase 10) :
- on vend sur les niveaux de bid consommés par la première vente-équivalente d'un autre wallet d'heure ≥ max(T_OBS + H, heure d'entrée + 1 s) ;
- la profondeur est complétée par les ventes-équivalentes des 10 s suivantes (STRICT, SUIVANT) ou des 1 800 s (FLUX) ;
- le repère doit se trouver dans les 900 s ; sinon, la sortie est **non observée** ;
- le délai réel de sortie est publié pour chaque horizon. Une sortie « à 1 s » peut avoir lieu bien plus tard, et ce délai est montré.

**Sortie en direct :** parcours des bids du carnet connu à T_OBS + H.

**Résolution :** 1 ou 0 par action, sans frais de sortie.

## 6. Frais

- **Coefficient c** mesuré sur le reçu de la transaction du 1er achat du même wallet, dans le même marché et moins d'une heure avant (`p10/fees.pkl`, règle de la phase 10).
- **Frais preneur** = c × actions × min(p, 1 − p), à l'entrée et à la sortie.
- Reçu absent : c = 0,02 (phase 10), signalé.
- **En direct :** `feeSchedule` du marché (phase 11).

## 7. Rendements

| Mesure | Définition |
|---|---|
| raw_return | produit / coût − 1 |
| slippage_entry | VWAP − best ask |
| fees | frais d'entrée + frais de sortie |
| net_return | (produit − coût − frais) / coût |
| net_PnL | net_return × coût exécuté |

Le calcul porte sur la partie exécutée. Cette partie est publiée.

## 8. Chemin des prix (§9, §11, §12)

Prix exprimés dans le sens du jeton acheté, sur le flux complet de la fenêtre (toutes tailles).

| Mesure | Définition |
|---|---|
| **p_ref** | dernier trade (tous wallets) avant le 2e achat dans l'ordre d'exécution |
| **Avant :** pre(k) = p_ref − p_tous(T2 − k) | k = 1, 5, 10, 30, 60 et 120 s ; p_tous(t) = dernier trade (tous wallets) d'heure ≤ t ; NaN s'il n'y en a aucun dans le flux |
| **Après :** post(h) = p_autres(T2 + h) − p_ref | h = 1, 5, 10, 30, 60, 120 et 300 s ; p_autres(t) = dernier trade d'un **autre** wallet après le 2e achat d'heure ≤ t ; s'il n'y en a pas encore, le prix est réputé inchangé (p_ref), comme en phase 13 |
| **Prix comparés** | prix du 2e achat contre p_autres(T2 + h) |
| **Segments descriptifs (§12)** | stable si \|pre(60)\| < 0,01 ; hausse préalable si pre(60) ≥ 0,01 ; baisse préalable si pre(60) ≤ −0,01 |

Les segments sont **descriptifs**. Ils ne servent à aucune règle de trading.

**MAE / drawdown :** minimum de p_autres − prix d'entrée sur [entrée, entrée + 600 s].

## 9. Statistiques (§16)

**Pour VALID et TEST séparément** (TRAIN est montré à titre indicatif ; TEST est prioritaire) :
- N, nombre de marchés, nombre de wallets ;
- part positive, moyenne, médiane, P25, P75 ;
- IC 95 % par bootstrap groupé par marché (1 000 tirages, graine 14) :
  - de la moyenne SECOND_BUY ;
  - de la différence SECOND_BUY − MATCHED_CONTROL, rééchantillonnées indépendamment ;
- taille d'effet : différence de moyennes et différence de médianes.

**ALL SECOND BUYS** et **EXECUTION-MEASURABLE SECOND BUYS** sont toujours présentés côte à côte, avec leurs taux de conservation. Moins de 30 cas mesurables : **INSUFFICIENT SAMPLE**.

## 10. Cas principal et règles de conclusion (§19)

**Cas principal :**
- FLUX, RÉALISTE L = 2 s, 500 $, sortie à 300 s, frais mesurés ;
- critère prédictif : LEAD60_2 (définition de la phase 13) sur **tous** les 2e achats.

**Statuts intermédiaires :**
- **PRÉDICTIF** si la différence LEAD60_2 SECOND_BUY − CONTROLE est > 0, avec un IC excluant 0, en VALID **et** en TEST.
- **MOMENTUM** si, dans le segment stable, cette différence est ≤ 0 en VALID **ou** en TEST.
- **EXÉCUTABLE (A)** si toutes ces conditions sont réunies, en VALID et en TEST :
  - net moyen > 0 avec un IC excluant 0, et net médian > 0 ;
  - net SECOND_BUY − CONTROLE > 0 avec un IC excluant 0 ;
  - 500 $ entièrement exécutables dans au moins 50 % des cas mesurables ;
  - net moyen > 0 dans le segment stable ;
  - au moins 30 cas, 10 marchés et 10 wallets ;
  - aucun wallet au-delà de 20 % des cas.

**Arbre de décision, appliqué dans cet ordre :**
1. Non PRÉDICTIF :
   - **E. ABSENCE D'EDGE** si chaque split compte au moins 30 2e achats ;
   - **D. NON CONFIRMÉ** sinon, ou si VALID et TEST se contredisent.
2. PRÉDICTIF et MOMENTUM : **C. EXPLIQUÉ PAR LE MOMENTUM**.
3. PRÉDICTIF, mais moins de 30 cas mesurables (cas principal) en VALID ou en TEST : **D. NON CONFIRMÉ (exécution INSUFFICIENT SAMPLE)**.
4. EXÉCUTABLE : **A. SIGNAL D'EXÉCUTION CONFIRMÉ**.
5. Net ≤ 0, ou IC du net incluant 0 : **B. PRÉDICTIF MAIS NON EXÉCUTABLE**.
6. Net > 0, mais pas au-dessus du contrôle : **E. ABSENCE D'EDGE**.

**Lectures secondaires**, sans effet sur la conclusion :
- ORACLE contre RÉALISTE ;
- STRICT et SUIVANT ;
- autres tailles et horizons.

**Comptabilité des tests :**
- 3 estimateurs × 10 latences × 5 tailles × 9 sorties × 3 splits × 2 groupes ;
- un seul cas principal par split.

## 11. Cas particuliers (§14, §15)

**Les 8 comptes :**
- même règle du 2e achat appliquée à leurs FAE (base phase 9), descriptif ;
- jamais intégrés à l'échantillon SIG_HIST ;
- flux disponible seulement si l'un de leurs trades tombe dans une fenêtre déjà collectée ; sinon NO BOOK DATA.

**Maduro et Iran :**
- 2e achat des wallets déjà documentés (0x31a56e9e et 0x6baf05d1 ; 0x4dfd481c) ;
- même code d'exécution sur les flux `EVT_MADURO` et `EVT_IRAN` de la phase 10 ;
- ces wallets ne sont pas SIG_HIST au moment des achats (phase 13) : les résultats sont des **illustrations**, pas des preuves du signal ;
- les deux définitions de l'anomalie Iran sont conservées.

**Nouveaux wallets :**
- par construction, un 2e achat SIG_HIST exige un 1er achat SIG_HIST, donc un wallet déjà qualifié ;
- on mesure seulement la part des 2e achats venant de wallets récemment qualifiés (hist_n de 5 à 9 à T1, ou qualification de moins de 30 jours) ;
- et le nombre de wallets dont la première alerte SIG_HIST est suivie d'un 2e achat.

## 12. Journal papier en direct (§18)

- `p14_paper.py` est un processus séparé, **PAPER ONLY**, lancé par `p14_run.sh`.
- Il ne touche à aucun processus des phases 11 à 13. Il lit seulement :
  - `donnees/brut_p11/live/alerts.jsonl` ;
  - `donnees/brut_p13/paper_alerts.jsonl` (type SIG_HIST_V1).
- **Pour chaque alerte (T1)**, il surveille pendant 3 600 s le même wallet sur le même jeton :
  - par RTDS ;
  - par les logs Polygon filtrés sur ce wallet.
- **Au premier achat d'au moins 100 $ (T2) :**
  - carnet REST à la détection, entrées papier de 50 à 1 000 $ ;
  - sorties papier à +1, +5, +10, +30, +60, +120 et +300 s.
- **Sortie :** `phase14/paper_second_buy.csv`, plus le brut dans `donnees/brut_p14/`.
