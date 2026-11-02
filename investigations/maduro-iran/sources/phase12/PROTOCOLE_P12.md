# Phase 12 : protocole pré-enregistré

Rédigé le 01/10/2026 vers 10:00 UTC :
- après la mesure des latences (`CLOB_LATENCY.md`) ;
- **avant tout calcul de feature ou d'outcome sur VALID, TEST ou le direct**.

La phase 12 est une expérience séparée. **Elle ne modifie pas la phase 11** : ni SIG_HIST V1, ni l'achat de 500 $ à T_obs, ni la sortie à 300 s, ni la collecte. Elle lit les données de la phase 11 sans les écrire.

Catégories autorisées : PRE_WALLET_ANOMALY, PRE_REPRICING_FLOW, AGGRESSIVE_FLOW, ORDERBOOK_IMBALANCE, UNKNOWN_CAUSE. Jamais « insider » ni « informed trader ».

## 1. Données

| Code | Contenu | Résolution | Usage |
|---|---|---|---|
| **H** | flux complets de la phase 10 : 1 985 fenêtres SIG_HIST et 1 964 fenêtres de contrôle, [T0 − 900 s, T0 + 4 500 s], tous les trades preneurs, ordre exact, niveaux makers consommés | seconde, plus l'ordre à l'intérieur de la seconde. **Pas de carnet complet** | apprentissage (TRAIN), validation (VALID), test (TEST), découpage de la phase 9 |
| **L** | données brutes de la phase 11 depuis le 01/10/2026 08:51 UTC : carnet complet en ms, `last_trade_price`, RTDS, chaîne | milliseconde | hors échantillon, **seule source pour l'exécution** (§14) |

## 2. Événements candidats et direction

- **Candidat :** trade preneur **anonyme** d'achat (de l'un ou l'autre jeton) d'au moins 250 $.
  - Dans H, ce sont tous ceux des fenêtres.
  - Dans L, ceux des marchés enregistrés.
- **Direction :** le jeton acheté. Tous les prix sont exprimés dans cette direction.
- **Interdit :** le wallet, son historique, son statut FAE (« pas de trade depuis 24 h » dépend du wallet) ne servent jamais de feature.
- **Usage permis du wallet :**
  - repérer a posteriori les trades SIG_HIST (`was_SIG_HIST_wallet`) ;
  - exclure le wallet lui-même des « autres wallets » dans l'outcome ;
  - évaluer.

## 3. Features

Chaque bloc s'arrête strictement à un instant. Les feuilles sont dans `pre_wallet_features.csv`.

### AVANT (strictement antérieur au trade, dans l'ordre d'exécution)

| Famille | Features |
|---|---|
| Prix | variation du dernier prix sur 1, 2, 5, 10, 30 et 60 s ; dans L aussi 100, 250 et 500 ms |
| Flux | volume et nombre de trades dans le même sens et en sens opposé sur 1, 2, 5, 10 et 60 s ; volume net ; accélération (5 s contre moyenne sur 60 s) ; taille maximale et taille moyenne sur 10 s ; temps depuis le dernier trade |
| Consommation de niveaux | niveaux et capital consommés par les achats de même sens sur 5 et 10 s ; maximum de niveaux en un trade |
| Carnet | dans H, écart entre le dernier ask et le dernier bid observés (≤ 60 s). Dans L, best bid, best ask, spread, profondeur à 1, 2 et 5 points, déséquilibre bid/ask, variation de profondeur et de spread sur 1 s et 5 s, niveaux apparus ou disparus |
| Niveau | prix avant le trade |

### PENDANT, anonyme (le trade lui-même, sans le wallet)

- taille en dollars (log) ;
- nombre de niveaux consommés ;
- marche dans le carnet (dernier niveau − premier) ;
- impact (dernier niveau − prix avant) ;
- prime (premier niveau − prix avant).

Dans L, il est visible environ 20 ms après le match, avant l'identité du wallet. **Il n'est jamais mélangé aux features « AVANT »** (§8 de la mission). Il définit un détecteur séparé.

## 4. Outcome REPRICING_60 (défini et gelé sur TRAIN)

Prix de référence : dernier trade d'un **autre** wallet.

| Outcome | Définition |
|---|---|
| **REPRICING_60_PRE** | variation du prix des autres entre l'instant juste avant le trade et 60 s après ≥ θ_pre |
| **REPRICING_60_POST** | variation entre le dernier niveau consommé par le trade et 60 s après ≥ θ_post |

- **Seuils :** θ_pre et θ_post = 90e percentile de la variation correspondante sur les candidats de TRAIN, arrondi à 0,005 près, au minimum 0,01. Ils sont écrits dans `frozen_p12.json` avant toute lecture de VALID.
- **T_REPRICING :** premier trade d'un autre wallet où la variation atteint le seuil.

## 5. Détecteurs (TRAIN seulement, puis gel)

| Code | Contenu |
|---|---|
| **A, WALLET-AWARE** | SIG_HIST V1, inchangé. Heure du signal = T0 + latence d'identification du wallet (médiane live 1,75 s ; P10 0,84 ; P90 2,56) |
| **B1, PRE-TRADE** | HistGradientBoosting (graine 12) sur les seules features AVANT, cible REPRICING_60_PRE. Heure du signal = juste avant le trade |
| **B2, TRADE-ANONYME** | HistGradientBoosting (graine 12) sur AVANT + PENDANT anonyme, cible REPRICING_60_POST. Heure du signal = T0 + 20 ms (visibilité dans le carnet) |

- **Seuil d'alerte** de B1 et B2 = 95e percentile de leur score sur les candidats de TRAIN. Il est gelé.
- **Aucun réglage** après VALID. TEST est lu une seule fois.

## 6. Tests

1. **Le signal vient-il du carnet ? (§16, §17, §18)** Les features AVANT avant les trades SIG_HIST sont comparées à celles avant les FAE de contrôle et à des instants tirés au hasard dans les mêmes fenêtres (un toutes les 60 s, hors ± 120 s autour des événements) :
   - écart de moyenne par feature, IC par bootstrap groupé par marché ;
   - AUC d'un classifieur appris sur TRAIN (SIG_HIST contre contrôle) avec les seules features AVANT, évaluée sur VALID et TEST.
2. **A contre B (§11).** Sur la même population de candidats :
   - taux de REPRICING_60 parmi les signalés (précision) ;
   - rappel ;
   - taux de faux positifs ;
   - délai jusqu'au repricing (T_REPRICING − T_SIGNAL) ;
   - **part des alertes SIG_HIST retrouvées par B** (rappel de B sur les trades SIG_HIST) ;
   - AUC du score B entre trades SIG_HIST et FAE de contrôle.
3. **Gain de temps (§13)** = T_WALLET − T_SIGNAL. Mesuré dans L ; dans H, borné par les latences de L.
4. **Exécution (§14), dans L seulement**, carnet connu à l'instant de décision :
   - latence supplémentaire : 0, 100, 250, 500 ms, 1, 2 et 5 s ;
   - tailles : 50, 100, 250, 500 et 1 000 $ ;
   - sorties : sur le carnet à +60 s et +300 s ;
   - frais du marché ;
   - **contrôle** : candidats non signalés (score sous la médiane) du même marché, l'heure la plus proche.
   - **Stratégie principale : B2, latence 250 ms, 250 $, sortie à 60 s.**
5. **Maduro et Iran (§21, §22).** Features AVANT et scores B1/B2 juste avant chaque gros achat, comparés à leur distribution sur tous les autres instants de la nuit (rang percentile). Les deux références de l'Iran sont publiées.
6. **Direct (§23).** `p12_live.py` est un processus séparé, en lecture seule du marché, **PAPER ONLY**. Il journalise les alertes de B2 gelé (heure, marché, direction, score, entrée attendue) et le prix futur à +60 et +300 s.

## 7. Critères de réussite (§24)

| # | Critère | Condition |
|---|---|---|
| 1 | aucun wallet | vérifié dans le code |
| 2 | avant le repricing | délai > 0 |
| 3 | bat le contrôle | taux de repricing et rendement net supérieurs au contrôle, IC excluant 0 |
| 4 | VALID | même chose |
| 5 | TEST | même chose |
| 6 | délai mesurable | médiane ≥ 250 ms |
| 7, 8 | après spread et glissement | net > 0 dans L |
| 9 | capacité | ≥ 250 $ remplis à ≥ 80 % |
| 10 | dispersion | sans les 5 % meilleurs trades > 0 ; aucun marché au-dessus de 20 % |

Sinon : **NO ACTIONABLE PRE-WALLET SIGNAL**.

**Limite connue à l'avance.** Les critères 7 à 9 ne peuvent être évalués que sur L, aujourd'hui court (début le 01/10 08:51). Une évaluation finale sera refaite quand L couvrira au moins 2 semaines.
