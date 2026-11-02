# Phase 8 : extraction d'un signal tradable

30/09/2026. Étude prédictive, hors échantillon, avec protocole pré-enregistré (`PROTOCOLE_PREENREGISTRE.md`, écrit avant tout calcul de résultat).

## Conclusion

**Aucun signal exploitable détecté.**

- Aucun des 8 signaux pré-enregistrés n'est à la fois positif hors échantillon (VALID et TEST), significatif, capturable après coûts, indépendant du momentum et non dépendant d'un seul wallet.
- Les grosses entrées déplacent bien le prix, mais le mouvement est absorbé avant qu'un observateur puisse entrer.
- La convergence de plusieurs wallets suit le momentum au lieu de le précéder.
- Le financement récent annonce une activité plus grosse et plus risquée, mais pas de meilleurs résultats.
- Le financement par la famille MoonPay est trop rare pour être testé.

---

## 1. Données et protocole

| Élément | Valeur |
|---|---|
| **Univers** | 2 097 marchés fermés entre le 01/10/2025 et le 15/09/2026, volume ≥ 250 000 $. Sont exclus : sport, e-sport, prix crypto, up/down, compteurs de tweets, météo. Règles fixées avant toute mesure. |
| **Trades** | 2 515 167 trades preneurs ≥ 100 $ (data-api), 270 477 wallets, **1 662 140 achats** (événements). 42 marchés ont peut-être un historique tronqué au-delà d'environ 10 500 trades. |
| **Découpage** | TRAIN : fin avant 03/2026 (968 marchés). VALID : 03 à 05/2026 (552). TEST : 06 à 09/2026 (577). |
| **Échantillon mesuré** | 30 108 événements (graine 8) : 2 000 aléatoires par split en baseline, jusqu'à 1 500 par signal et par split, les 29 achats de la population A, et 4 294 événements de 1 506 wallets tirés au hasard pour le financement. |
| **Prix** | Séries CLOB à la minute, de T − 65 min à T + 6 h (2 594 jetons, toutes non vides). |
| **Financement** | Afflux USDC.e et USDC hors contrats de trading sur le proxy Polygon (Etherscan). Origine des afflux Relay remontée via l'API Relay, puis contrôle d'un paiement de la famille MoonPay sur l'adresse d'origine (Ethereum). Vérifié sur les comptes connus : Chiwawas et 154x838hjd6 sont bien détectés. |
| **Capturabilité** | Entrée de l'observateur au premier prix CLOB après T + 60 s (p_obs). Coût de 1 point (écart acheteur-vendeur, glissement, frais), sensibilité à 2 points. Les frais preneurs 2026 vont jusqu'à 1 à 1,75 centime par action selon la catégorie. |
| **Tests** | 8 signaux × 6 horizons × 3 splits × 2 coûts = **288 comparaisons**, dont 48 principales (60 min et résolution, coût 1 point). |

**Écarts par rapport au protocole**, signalés :
1. Les terciles de momentum de TRAIN sont dégénérés (bornes à 0, le tercile « moyen » est vide). Le contrôle se fait donc en réalité sur 2 strates : pas de hausse préalable contre hausse préalable.
2. L'échantillon de financement prend les 4 premiers événements de chaque wallet, ce qui le décale vers TRAIN. TEST n'a que 30 à 50 événements pour S_FRESH et S_FASTFUND.
3. Le classement automatique du script a été relu et corrigé pour 4 signaux ; les deux versions sont dans `signals.csv`.

---

## 2. Résultats par signal (critères principaux, coût 1 point)

Les écarts sont exprimés en points de probabilité, par rapport à la baseline stratifiée (tranche de prix × momentum). Les IC sont à 95 %, par bootstrap groupé par marché.

| Signal | Règle (T) | VALID 60 min | TEST 60 min | VALID résolution | TEST résolution | Classement final |
|---|---|---|---|---|---|---|
| S_LARGE | top 1 % des tailles du marché et ≥ 5 000 $ | −0,09 [−0,41 ; +0,21] | +0,05 [−0,32 ; +0,39] | −1,9 [−4,9 ; +1,0] | −0,7 [−3,5 ; +1,8] | **NON CAPTURABLE** |
| S_LONGSHOT_LARGE | prix ≤ 0,20 et top 5 % | −0,39 [−0,92 ; +0,09] | −0,05 [−0,44 ; +0,29] | +4,4 [−4,8 ; +15,6] | −2,4 [−10,3 ; +7,1] | **AUCUN SIGNAL** |
| S_CONV | ≥ 2 autres gros acheteurs du même jeton en 30 min | +0,23 [−0,09 ; +0,50] | +0,10 [−0,57 ; +0,77] | −0,5 [−3,0 ; +1,9] | +0,7 [−2,3 ; +3,5] | **EXPLIQUÉ PAR MOMENTUM** |
| S_ACCUM | ≥ 3 achats du même jeton en 24 h, sans vente | +0,06 | −0,15 | −0,7 | **−2,8 [−5,6 ; −0,6]** | **AUCUN SIGNAL** |
| S_FIRST_LARGE | 1er trade dans le marché, wallet ≤ 2 trades, top 5 % | **−0,23 [−0,46 ; −0,03]** | −0,05 | −0,3 | −1,5 | **AUCUN SIGNAL** |
| S_FRESH | wallet financé < 48 h, ≤ 2 trades | −0,02 [−0,40 ; +0,30] | +0,29 [−0,42 ; +1,09] (n=33) | +1,2 [−1,7 ; +4,5] | +8,1 [−4,7 ; +21,9] (n=30) | **PROMETTEUR (faible)** |
| S_FASTFUND | financé < 60 min avant le trade | −0,10 | +0,83 [−0,10 ; +2,3] | −2,4 [−7,3 ; +1,8] | **+11,1 [+0,3 ; +23,9]** (n=43) | **NON REPRODUCTIBLE** |
| S_MOONPAY | proxy financé par la famille MoonPay (direct ou via Relay) | −1,0 (n=18, 4 wallets) | n=2 | −7,0 | n=0 | **AUCUN SIGNAL (trop rare)** |

**Tests multiples.** 3 IC sur 48 excluent 0 : un positif (S_FASTFUND, TEST, résolution) et deux négatifs. Environ 2,4 sont attendus par hasard. Aucun n'est reproduit dans deux splits.

**Rendement absolu d'un observateur.** À 60 min, il vaut en moyenne −0,5 à −1,1 point net pour **tous** les signaux (−2,2 pour S_MOONPAY en VALID, n = 18), soit à peu près le coût : rien ne compense l'entrée.

---

## 3. Impact de prix et capturabilité (`price_impact.csv`)

| Groupe (TEST) | Hausse préalable 60 min | Mouvement p(T+5 min) − p(T) | Rendement observateur +5 min | +60 min | +6 h |
|---|---|---|---|---|---|
| S_LARGE | +2,2 | **+1,04** | +0,05 | +0,23 | +0,52 |
| S_CONV | **+5,1** | +1,14 | +0,14 | +0,34 | +0,82 |
| S_LONGSHOT_LARGE | −0,1 | +0,97 | +0,10 | −0,08 | +0,18 |
| Baseline aléatoire | +0,45 | +0,36 | +0,05 | +0,11 | +0,37 |

Les rendements sont bruts, en points, avant le coût de 1 point.

**Lecture.**
- Les grosses entrées déplacent le prix d'environ 1 point dans les 5 minutes : c'est l'impact mécanique du trade lui-même.
- À T + 60 s, ce mouvement est déjà dans le prix. L'observateur récupère ensuite 0,05 à 0,3 point à 60 min, moins que le coût.
- **Effet réel, non capturable.**

---

## 4. Momentum ou information (`momentum_control.csv`)

- **S_CONV arrive après une hausse moyenne de +1,8 (VALID) à +5,1 points (TEST)** dans l'heure précédente, contre +0,2 à +0,45 pour la baseline.
- Dans la strate sans hausse préalable, l'écart de S_CONV à 60 min est **négatif** (VALID −0,25 ; TEST −0,14).
- La convergence de plusieurs wallets **suit** le mouvement ; elle ne le précède pas.
- Aucun signal ne conserve un écart positif et significatif une fois le momentum pris en compte.

---

## 5. Pression puis retournement (H2, `pressure_reversal.csv`)

Sur l'ensemble des splits :

| Groupe | n | Impact ≥ 2 points en 5 min | Retournement moyen 5 min → 6 h | Sortie du wallet sous 6 h | Motif complet (impact, sortie, retournement ≥ moitié) |
|---|--:|--:|--:|--:|--:|
| S_LARGE, wallet neuf | 1 286 | 8,8 % | +0,42 | 27 % | 0,47 % |
| S_LARGE, wallet établi | 3 122 | 12,3 % | +0,19 | 14 % | 0,64 % |
| S_CONV | 6 485 | 10,7 % | +0,27 | 31 % | 0,89 % |
| Baseline | 5 982 | 4,8 % | +0,30 | 26 % | 0,28 % |

- Pas de retournement moyen : le prix continue légèrement dans le même sens.
- Le motif « pression → sortie → retournement » est 2 à 3 fois plus fréquent que dans la baseline, mais reste **sous 1 %** des cas, sans mécanisme démontré.
- **Aucune manipulation démontrée.**
- Ordres et annulations : **INCONNU**. Les données publiques utilisées ne les reconstruisent pas, donc aucune conclusion sur le spoofing.

---

## 6. Populations A, B, C (`populations_ABC.csv`, `wallet_features.csv`)

Échantillon de financement : 1 506 wallets.

| Population | Wallets | Événements | Montant médian | Part top 5 % | Prix ≤ 0,20 | Rendement observateur 60 min | Résolution |
|---|--:|--:|--:|--:|--:|--:|--:|
| A (réseau) | 6 | 27 | 999 $ | 22 % | 100 % | +2,0 | +14,2 |
| B (financés par la famille MoonPay) | 28 | 75 | 197 $ | 5 % | 16 % | +0,05 | −1,9 |
| C (contrôle) | 1 472 | 4 192 | 254 $ | 5 % | 8 % | −0,04 | +1,3 |

- **B ne se distingue pas de C** en performance. Ses trades sont plus petits et un peu plus orientés vers les outsiders.
- B ne représente que 1,9 % des wallets tirés : le financement MoonPay n'a **aucune valeur prédictive mesurable** et il est trop rare pour servir de signal.
- A n'est pas un signal : il a été sélectionné sur son résultat (voir §7).

---

## 7. Les comptes du réseau (`population_A_events.csv`)

29 achats de 100 $ ou plus dans l'univers. X34 et Neodbs n'y figurent pas : leurs trades sont hors univers ou sous 100 $.

- **Chiwawas** : 8 paris sur des outsiders (« Maduro out in 2025 ») entre le 23/12 et le 31/12/2025 ; **tous perdus**. Puis 2 entrées le 03/01/2026 à 05:35 et 05:46 UTC, à 0,12 environ, signalées par S_LONGSHOT_LARGE, FASTFUND et MOONPAY. Un observateur entré à T + 60 s aurait eu **+25,5 et +36 points à 60 min**, et +87 à +89 points à la résolution.
- **154x838hjd6** : 6 entrées fin décembre (signaux FRESH, FASTFUND, MOONPAY) ; 3 perdues, 3 gagnées à la résolution.
- **chileno777** : 3 paris perdus en décembre, 1 gagné le 03/01 à 05:35.
- **Mrs.Joker, Planktonbets, TacticalInsiderNews** : paris Iran et Fed, tous perdus dans l'univers.

**Constat.** Les caractéristiques du réseau (financement récent, financement familial, gros pari sur un outsider) sont bien présentes au moment T. Mais ces mêmes caractéristiques, dans la population générale, n'ont aucun rendement positif reproductible. Même dans le réseau, les paris gagnants du 03/01 sont précédés de nombreux paris perdants de même profil. Ce qui distingue les deux entrées gagnantes n'est pas observable avant T avec ces features.

---

## 8. Réponses

**Q1. Un financement récent prédit-il une activité anormale ?**
Oui, mais seulement l'activité, pas le résultat.

| Délai depuis le financement | Part top 5 % | Montant médian | Part d'outsiders |
|---|--:|--:|--:|
| < 60 min | 7,8 % | 453 $ | 14 % |
| > 24 h | 3,1 % | 200 $ | 6 % |

**Q2. Une grosse entrée précède-t-elle un mouvement ?**
Oui mécaniquement : environ +1 point en 5 min. Mais rien au-delà de ce qu'un observateur peut capter.

**Q3. La convergence améliore-t-elle le signal ?**
Non. Elle est expliquée par le momentum préalable.

**Q4. Reste-t-il quelque chose après le momentum ?**
Non.

**Q5. Y a-t-il un signal positif hors échantillon ?**
Non de manière reproductible. Le seul positif significatif (S_FASTFUND, TEST, résolution) est négatif en TRAIN et en VALID.

**Q6. Est-ce capturable ?**
Non. Le rendement net de l'observateur est d'environ −1 point à 60 min pour tous les signaux.

**Q7. Les wallets financés par l'infrastructure MoonPay se comportent-ils différemment ?**
Pas en performance. Leur échantillon est trop petit (28 wallets, 75 événements), et le signal n'est pas testable en TEST (2 événements).

**Q8. Les 8 comptes présentent-ils les mêmes caractéristiques ?**
Oui : financement récent, financement familial pour Chiwawas et 154x838hjd6, et gros paris sur des outsiders. Mais ces caractéristiques ne sont pas prédictives dans la population, et les comptes accumulent aussi de nombreux paris perdants du même profil.

**Q9. Y a-t-il une signature de pression puis retournement ?**
Motif présent dans moins de 1 % des grosses entrées, 2 à 3 fois la baseline, sans retournement moyen. Non démontré. Ordres et annulations : INCONNU.

**Q10. Quelle information en temps réel aurait le plus de valeur ?**
- Aucune n'a de valeur prédictive validée.
- La seule piste à re-tester est **S_FRESH à l'horizon de la résolution** : signe positif dans les 3 splits, jamais significatif. Il faudrait un échantillon de financement beaucoup plus large en VALID et en TEST, avec la règle et le seuil gelés tels quels.
- Côté exécution, seul le **momentum préalable** aide à interpréter la convergence, et il n'est pas exploitable.

---

## 9. Verdict par critère (§21)

| Critère | Résultat |
|---|---|
| 1. Observable avant le mouvement | Oui pour toutes les features |
| 2. Défini sans le résultat | Oui (protocole pré-enregistré) |
| 3. Supérieur à la baseline | Non (aucun écart significatif reproduit) |
| 4. Présent hors échantillon | Non |
| 5. Capturable après glissement | Non |
| 6. Suffisamment fréquent | Oui pour les signaux de taille ; non pour MoonPay |
| 7. Non expliqué par le momentum | Non pour S_CONV |
| 8. Non dépendant d'un seul wallet ou marché | S_ACCUM est concentré (10 à 21 %) |

**Résultat : aucun signal exploitable détecté.** C'est un résultat valide. La meilleure piste (S_FRESH) reste à re-tester, sans changer ses règles, sur un échantillon plus grand et futur.
