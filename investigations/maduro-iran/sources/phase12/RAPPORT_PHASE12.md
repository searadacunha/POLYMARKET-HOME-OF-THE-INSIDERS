# Phase 12 : détection avant le wallet

Rapport du 01/10/2026, 10:05 UTC. Documents de référence :
- `PROTOCOLE_P12.md` : écrit avant tout calcul sur VALID, TEST ou le direct ;
- `frozen_p12.json` : seuils et modèles gelés sur TRAIN le 01/10 à 09:55 UTC ;
- `CLOB_LATENCY.md` : latences mesurées.

**Ce qui n'a pas bougé :**
- **La phase 11 est intacte.** SIG_HIST V1, l'achat de 500 $ à T_obs, la sortie à 300 s et l'objectif de 100 alertes sont inchangés. La phase 12 lit ses données sans les écrire.
- **Une seule intervention technique sur la phase 11, documentée :** le flux RTDS du listener s'était tari sans fermeture vers 09:31 UTC. J'ai ajouté un chien de garde (30 s) au listener et au collecteur, puis relancé les deux. Le chien de garde a resservi à 09:58. **Les alertes de 09:31 à 09:58 ont pu être manquées en direct** ; elles restent récupérables a posteriori par le data-api.
- **Aucun ordre, aucune conclusion « insider ».**

## Réponse

**On ne peut pas détecter la même fenêtre que SIG_HIST sans le wallet.**

Les détecteurs sans wallet, appris sur TRAIN et gelés, prédisent bien un repricing à 60 s : 40 à 58 % de précision, contre 14 à 16 % de base, en VALID comme en TEST. Mais **ce sont d'autres événements que SIG_HIST** :
- ils retrouvent **2 à 3 %** seulement des trades SIG_HIST ;
- avant un trade SIG_HIST, le carnet ressemble à celui d'un achat ordinaire (AUC 0,54 à 0,58) ;
- ce qu'ils détectent, c'est surtout un flux déjà en marche (PRE_REPRICING_FLOW / AGGRESSIVE_FLOW), y compris les acheteurs qui suivent un trade SIG_HIST.

Sur Maduro et l'Iran, ils ne voient rien **avant** les gros achats inhabituels. Ils réagissent après, et sonnent aussi souvent dans le mauvais sens.

**La capturabilité n'est pas encore mesurable.**
- Sur la première heure de carnet réel : 36 gros achats anonymes, 0 signal B2, 13 signaux B1.
- Le journal paper (`p12_live.py`) tourne maintenant en parallèle pour accumuler des cas.

**Verdict : NO ACTIONABLE PRE-WALLET SIGNAL.**
- Avec SIG_HIST, l'échec est démontré : son information n'est pas dans le carnet avant le trade.
- Pour un flux court sans wallet, rien n'est démontré : le signal prédit, mais son exécution n'est pas encore mesurée.

| Mesure demandée (§28) | Valeur |
|---|---|
| PRE_WALLET_LEAD | gain théorique 1,73 s (T0 + 0,02 s contre T0 + 1,75 s), mais sur 2 à 3 % des alertes SIG_HIST seulement |
| EXECUTION_PRICE, SLIPPAGE, CAPACITY, NET_RETURN | **INCONNUS** : 0 signal B2 dans le carnet réel enregistré à ce jour |
| FALSE_POSITIVE_RATE | 1,6 à 1,7 % des candidats non suivis d'un repricing (B2). 0,35 à 0,46 % des instants ordinaires déclenchent B1 ; 70 % de ces alertes ne sont pas suivies d'un repricing |

---

## 1. Latences : la vraie fenêtre avant le wallet (§4, §5)

Détail : `CLOB_LATENCY.md`.

**MESURÉ**
- Avant le wallet, seul le carnet est observable : niveaux, mises à jour, trades anonymes avec prix, taille, côté et hash. La chaîne et RTDS apportent le wallet dans le même message que le trade.
- Délai entre l'apparition du trade dans le carnet et l'identité du wallet (575 transactions) :
  - par la voie la plus rapide : **médiane 1,75 s** (P10 0,84, P25 1,24, P75 2,19, P90 2,56, max 3,26) ;
  - RTDS seul : médiane 1,80 s ;
  - nœud Polygon public : médiane 1,62 s, mais P90 14 s (irrégulier).

**INFÉRÉ**
- Supprimer la dépendance au wallet fait gagner au plus 0,8 à 2,6 s.
- Pour gagner plus, il faudrait voir quelque chose **avant** le trade du wallet.

**INCONNU**
- Un nœud privé ou le mempool.

**PROCHAINE ÉTAPE**
- Remesurer sur 2 semaines de fills SIG_HIST (flux `chain` de la phase 11).

## 2. Le signal vient-il du carnet ? (§6, §7, §8, §16 à §19)

**Données.** Flux complets de la phase 10 : 43 333 achats anonymes de 250 $ ou plus, dont 1 628 trades SIG_HIST et 1 553 FAE de contrôle, plus 314 663 instants ordinaires.
- Résolution : la seconde, avec l'ordre exact à l'intérieur de la seconde.
- **Pas de carnet complet dans l'historique.** Le déséquilibre bid/ask et les fenêtres sous la seconde (100 à 500 ms) ne sont mesurables qu'en direct.

**Ce qui précède un trade SIG_HIST, comparé à un FAE de contrôle** (`signature_clob.csv`, IC par bootstrap groupé par marché) :

| Feature AVANT | VALID : SIG_HIST / contrôle | TEST : SIG_HIST / contrôle | Verdict |
|---|---|---|---|
| Variation du prix sur 1 s | +0,18 / +0,04 point | +0,23 / +0,05 | plus élevée, IC excluant 0 |
| Variation du prix sur 60 s | +0,55 / +0,08 point | +0,37 / +0,06 | plus élevée, IC excluant 0 |
| Achats de même sens sur 5 s (nombre) | 0,53 / 0,32 | 0,39 / 0,21 | plus élevé, IC excluant 0 |
| Volume de même sens (1, 5, 60 s) | | | **non significatif** |
| Accélération du flux (5 s contre 60 s) | non significatif | 1,62 / 0,94, IC excluant 0 | instable |
| Niveaux consommés (10 s) | 1,33 / 0,80, IC excluant 0 | non significatif | instable |
| **AUC d'un classifieur TRAIN, features AVANT seules** | **0,58** | **0,54** | quasi aléatoire |

**MESURÉ**
- Une légère dérive de prix dans le bon sens précède les trades SIG_HIST. Elle ne suffit pas à les distinguer d'achats comparables.
- Le volume et le déséquilibre du flux ne les distinguent pas.

**INFÉRÉ**
- L'avantage de SIG_HIST **n'est pas lisible dans le carnet avant le trade**. Il tient à l'identité du wallet.

**INCONNU**
- Le déséquilibre du carnet et les fenêtres sous la seconde : à mesurer sur les données live.

**PROCHAINE ÉTAPE**
- Même comparaison sur les alertes SIG_HIST live de la phase 11, avec le carnet complet.

## 3. A (wallet) contre B (sans wallet) (§9 à §13)

**Seuils gelés sur TRAIN :**
- REPRICING_60_PRE = au moins +2 points dans les 60 s, mesurés depuis le prix d'avant le trade ;
- REPRICING_60_POST = au moins +1 point dans les 60 s, mesurés depuis le dernier niveau consommé ;
- taux de base en TRAIN : 12 %.

**Détecteurs :**
- **B1** : features AVANT seules ;
- **B2** : AVANT + empreinte anonyme du trade (taille, niveaux, impact).
- Les deux sont des HistGradientBoosting, avec un seuil au 95e percentile de TRAIN.

| | Split | Signalés | Précision | Base | Écart [IC] | Rappel | Faux positifs | Délai médian jusqu'au repricing | Trades SIG_HIST retrouvés |
|---|---|---|---|---|---|---|---|---|---|
| **A SIG_HIST** (signal à T0 + 1,75 s) | VALID | 481 | 31,8 % | 14,4 % | +18,1 [13,3 ; 24,1] | 8,0 % | 2,9 % | 4,25 s (18 % déjà faits) | (100 %) |
| | TEST | 569 | 30,2 % | 16,5 % | +14,8 [9,0 ; 20,6] | 12,5 % | 5,7 % | **1,25 s (26 % déjà faits)** | (100 %) |
| **B1 AVANT** (signal juste avant le trade) | VALID | 367 | 58,0 % | 14,1 % | +45,2 [33,2 ; 53,0] | 11,4 % | 1,4 % | 4,0 s | 1,9 % |
| | TEST | 183 | 39,9 % | 15,8 % | +24,6 [16,4 ; 32,3] | 5,5 % | 1,6 % | 4,0 s | **0,7 %** |
| **B2 AVANT + trade** (T0 + 0,02 s) | VALID | 379 | 49,3 % | 14,4 % | +36,0 [23,4 ; 47,5] | 9,8 % | 1,7 % | 4,0 s | 2,7 % |
| | TEST | 206 | 46,6 % | 16,5 % | +30,9 [21,4 ; 39,5] | 7,0 % | 1,6 % | 8,0 s | **2,3 %** |

- AUC des scores B entre trades SIG_HIST et FAE de contrôle : B1 0,57 (VALID) et 0,52 (TEST) ; B2 0,65 et 0,60.
- Sur les alertes SIG_HIST elles-mêmes, le repricing (POST) arrive en médiane 7,0 s (VALID) et 3,5 s (TEST) après le trade. **18 à 26 % des repricings sont faits avant que le wallet soit connu** (1,75 s).

**MESURÉ**
- Sans wallet, on prédit mieux un repricing de court terme que SIG_HIST.
- **Mais on ne retrouve que 2 à 3 % des alertes SIG_HIST** (13 sur 481 en VALID, 13 sur 569 en TEST).
- **Part récupérable de la puissance de SIG_HIST sans wallet : très faible.** Les deux familles de signaux se recouvrent à peine.

**INFÉRÉ**
- B détecte une autre chose : des rafales de flux déjà commencées (« PRE_REPRICING_FLOW »).
- B1 est concentré : en VALID, le premier marché fait 29 % de ses signaux, au-dessus de la limite de 20 %.

**INCONNU**
- Si ces rafales se capturent après coûts.

## 4. Les acheteurs inconnus ont-ils une signature ? (§20)

Fenêtres SIG_HIST contre fenêtres de contrôle (`acheteurs_suivants.csv`) :

| Achats anonymes de 250 $ ou plus | Signalés B2 (VALID / TEST) | Repricing POST (VALID / TEST) |
|---|---|---|
| Suiveurs, 0 à 600 s après un trade SIG_HIST | 6,5 % / 6,5 % | 24 % / 21 % |
| Suiveurs, 0 à 600 s après un FAE de contrôle | 1,3 % / 0,7 % | 8 % / 9 % |
| Le trade SIG_HIST lui-même | 2,7 % / 2,3 % | 32 % / 30 % |

**INFÉRÉ**
- La signature anonyme apparaît **chez les suiveurs**, après le trade SIG_HIST : c'est un flux précoce mais **réactif** (EARLY FLOW au sens de la mission), pas une anticipation du trade SIG_HIST.
- Un détecteur sans wallet arrive donc dans la même vague que les acheteurs inconnus, pas avant le wallet.

## 5. Exécution sur le carnet réel (§14, §15, §19)

**Méthode.** Les données brutes de la phase 11 (01/10, 08:52 → 09:58 UTC) sont rejouées en lecture seule. Chaque entrée et chaque sortie est exécutée sur le carnet connu à l'instant exact, par un ordonnanceur qui ne lit pas le futur.
- latences supplémentaires : 0, 100, 250, 500 ms, 1, 2 et 5 s ;
- tailles : 50 à 1 000 $ ;
- sorties : +60 et +300 s ;
- frais du marché.

**MESURÉ**
- 36 achats anonymes de 250 $ ou plus sur 20 marchés, **0 signal B2**, 13 signaux B1.
- Contrôles (score sous la médiane, 250 $, 60 s) : net −0,8 % (n = 18).
- Après les 13 signaux B1, le mid ne monte pas dans le sens prédit (`live_alerts.csv`).

**INCONNU**
- Prix d'exécution, glissement, capacité et rendement net des signaux B2.

**PROCHAINE ÉTAPE**
- `p12_live.py` journalise en direct (PAPER ONLY) chaque signal et chaque candidat, avec l'entrée attendue et le prix réel de +1 à +300 s.
- À réévaluer avec `p12_execution.py` sur au moins 2 semaines de carnet.

## 6. Maduro (§21)

Détail : `maduro_pre_wallet.csv`. Rangs comparés aux 317 instants ordinaires de la nuit.

| Achat | Flux sur 60 s avant (rang) | Dérive sur 60 s (rang) | Accélération (rang) | Score B1 / B2 |
|---|---|---|---|---|
| `0x31a56e9e` 01:38:35, 6 000 $ | **0,00** | 0,16 | 0,00 | 0,06 / 0,04 |
| `0x31a56e9e` 02:15:05, 7 000 $ | 0,00 | 0,16 | 0,00 | 0,06 / 0,08 |
| `0x31a56e9e` 02:58:25, 7 215 $ | 0,00 | 0,06 | 0,00 | 0,06 / 0,02 |
| `0x6baf05d1` 03:42:01, 10 000 $ | 0,88 | 0,92 | 0,00 | 0,07 / 0,06 |
| Chiwawas 05:35:41, 5 188 $ | 0,93 | 0,98 | 0,99 | 0,08 / 0,08 |

- Seuils gelés : B1 0,50 ; B2 0,47.
- Aucun signal B1 ni B2 de toute la nuit (maximum 0,29 et 0,41).

**MESURÉ**
- Les trois achats de `0x31a56e9e` arrivent dans un **carnet immobile** : aucun flux dans la minute précédente.

**INFÉRÉ**
- Rien dans le flux public ne permettait de les anticiper. Ils ne sont repérables que par le wallet, ou après coup.
- Cause : **UNKNOWN_CAUSE**.

## 7. Iran (§22)

Détail : `iran_pre_wallet.csv`. **Les deux définitions du début de l'anomalie restent publiées :**
- **05:15**, avec une référence glissante sur 12 h ;
- **06:10**, avec la veille comme référence.

**MESURÉ**
- **Avant le premier gros achat de `0x4dfd481c` (05:15:53, 32 337 $) :** pas de signature. Flux sur 60 s au rang 0,80, dérive 0,30, accélération 0. Scores B1 0,06, B2 0,06.
- **Pendant la nuit,** B1 et B2 sonnent **38 fois** (13 B1 et 25 B2), du 27/02 13:25 au 28/02 06:13, dans les deux sens, presque toujours sans suite (±1 point).
- **Première alerte dans le sens YES le jour J :** 05:16:01, **8 s après** l'achat de `0x4dfd481c` (réaction, pas anticipation).
- **De 05:27 à 05:59 :** alertes B2 dans le sens **NO**, c'est-à-dire le mauvais.
- **Alertes YES pendant le vrai repricing :** à 06:12:25, soit 57 s avant le repricing CLOB (06:13:22), mais une fois le prix déjà à 0,26 et en train de monter (+14,5 points dans la minute).
- Planktonbets à 04:48:23 (12 417 $) : B2 0,29 (rang 0,90), sous le seuil.

**INFÉRÉ**
- Selon l'une ou l'autre définition, aucun signal sans wallet ne précède le premier gros achat inhabituel.
- Le détecteur suit le mouvement, avec un bruit important.

## 8. Critères de réussite (§24)

| # | Critère | B1 | B2 |
|---|---|---|---|
| 1 | pas de wallet | oui | oui |
| 2 | avant le repricing | oui (délai médian 4 s) | partiel (19 à 21 % dans la même seconde) |
| 3 | bat le contrôle (taux de repricing) | oui | oui |
| 4 | VALID | oui | oui |
| 5 | TEST | oui | oui |
| 6 | délai ≥ 250 ms | oui (résolution 1 s) | oui |
| 7 | positif après spread | **inconnu** (0 signal dans le carnet réel) | **inconnu** |
| 8 | positif après glissement | inconnu | inconnu |
| 9 | capacité | inconnue | inconnue |
| 10 | dispersion (marché ≤ 20 %) | **non** (29 % en VALID) | oui (19 % et 10 %) |

**Verdict : NO ACTIONABLE PRE-WALLET SIGNAL.**
- Contre SIG_HIST, c'est **établi** : la fenêtre de SIG_HIST n'est pas récupérable sans le wallet.
- Pour un flux court sans wallet (B2), c'est **non démontré** : prédictif hors échantillon, mais rendement non mesuré.

## 9. Écarts et limites

1. **Résolution de l'historique : la seconde.** Les fenêtres de 100, 250 et 500 ms et le déséquilibre bid/ask ne sont pas testables avant d'avoir des données live.
2. **Empreinte du trade.** Dans H, les niveaux sont lus sur les fills makers. En direct, ils le sont en parcourant le carnet d'avant le trade. Les deux mesures sont équivalentes en principe, mais pas identiques.
3. **Échantillon des fenêtres de la phase 10.** Il est centré sur des événements, donc la précision et le rappel sont mesurés sur une population enrichie, et non sur tout Polymarket.
4. **SIG_HIST manqués en direct.** Pendant la panne RTDS du listener (09:31 → 09:58), ils sont à récupérer a posteriori pour la phase 11.

## 10. Fichiers

**`phase12/`**
- Protocole et latences : `PROTOCOLE_P12.md`, `CLOB_LATENCY.md`, `latence_stats.csv`, `latence_detail.csv`
- Événements et scores : `pre_wallet_events.csv`, `pre_wallet_features.csv.gz`, `pre_wallet_scores.csv`, `control_events.csv`
- Comparaisons : `comparaison_A_B.csv`, `signature_clob.csv`, `acheteurs_suivants.csv`
- Exécution et direct : `pre_wallet_execution.csv`, `live_candidats.csv`, `live_signaux_B1.csv`, `live_alerts.csv`
- Cas : `maduro_pre_wallet.csv`, `iran_pre_wallet.csv`
- Gel : `frozen_p12.json`, `modeles/`

**Scripts**
- `p12_features.py`, `p12_backtest.py` (`--freeze`, `--evaluate`, `--cases`)
- `p12_pre_wallet_detector.py`, `p12_execution.py`, `p12_live.py`, `p12_run.sh`

**Journal paper en direct :** `donnees/brut_p12/` (`live_signals.jsonl`, `live_suivi.jsonl`).
