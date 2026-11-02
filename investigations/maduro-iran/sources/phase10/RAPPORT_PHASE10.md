# Phase 10 : capture du lead en temps réel

Rapport du 30/09/2026. Il s'appuie sur trois documents :
- `data_audit.md` et `CLOB_DATA_AUDIT.md` : l'audit des données ;
- `PROTOCOLE_P10.md` : le protocole pré-enregistré ;
- `frozen_p10.json` : les seuils gelés sur TRAIN avant toute lecture des variantes.

SIG_HIST est strictement celui de la phase 9 (1 985 alertes). Chaque alerte est comparée à un contrôle apparié : un achat comparable (même période, même niveau de prix, même activité), fait par un wallet non signalé.

## Verdict

**Aucune stratégie ne satisfait les 10 critères du §22. La capture du lead n'est pas démontrée.** Elle n'est pas non plus réfutée. Avec les données publiques, le rendement réalisable sur l'ensemble des alertes reste **INCONNU**.

Ce qui se passe entre le moment où SIG_HIST devient observable et celui où le mouvement devient trop cher :

1. **La compétition arrive en quelques secondes.**
   - Après un trade SIG_HIST, le premier acheteur suivant arrive en **2 à 4 s** (médiane VALID / TEST), contre 64 à 72 s pour les contrôles.
   - Dans 34 % des cas, le trade suivant d'un autre wallet tombe dans le même bloc que celui du wallet signalé, contre 15 % pour les contrôles.
   - À +2 s, le meilleur ask observé est déjà **+0,8 point au-dessus du prix payé par le wallet**. À +60 s, il est à +2,1 points.
2. **Le mouvement n'est pas un simple effet de taille.**
   - Quand le wallet ne déplace pas le prix (impact nul), SIG_HIST reste prédictif : LEAD60 de 19 à 22 %, contre 4 à 12 % pour les contrôles.
   - La continuation après le trade du wallet est de +0,9 à +1,1 point, contre −0,2 à +0,6 pour les contrôles.
3. **La continuation vient de nombreux acheteurs, pas des copieurs récurrents.**
   - Dans les 10 minutes, 5 à 9 acheteurs distincts en médiane, contre 2 à 3 pour les contrôles.
   - Les suiveurs récurrents du wallet ne font que 13 à 14 % de ce volume et environ 0,2 des 1,7 à 2,3 points de hausse du ask.
   - **Le copy-trading de la phase 9 existe, mais il n'explique pas le mouvement.**
4. **Le −2,3 % à 1 s de la phase 9 est reproduit exactement, et il venait surtout des frais supposés.**
   - Sans frais, ce même calcul donne +0,3 % en TEST. Avec les frais **réellement mesurés** sur la chaîne, il donne −0,6 % en TEST, +4,7 % en VALID et +3,2 % en TRAIN.
   - La phase 9 supposait 2,6 % du notionnel. En réalité : zéro avant le 28/04/2026 (1 reçu payant sur 2 153), et zéro dans 89 % des trades de géopolitique après.
   - Autre biais de la phase 9 : son observateur « à 1 s » entrait en réalité **33 s** après (premier fill, en médiane).
5. **La capture n'est mesurable que sur un sous-ensemble biaisé.**
   - Le carnet n'est visible qu'à travers les ordres consommés par les autres traders. À 500 $ et 2 s de latence, la profondeur n'est observable dans les 2 s que pour **5 à 8 %** des alertes.
   - L'estimateur exploratoire FLUX (écart déclaré) donne +4 à +7 % en moyenne (médiane +0,1 à +1 %) sur les 6 à 13 % d'alertes où l'entrée et la sortie sont observables. Les contrôles y font environ 0.
   - Mais ce sous-ensemble est **sélectionné sur le futur** : il ne contient que les cas où d'autres ont acheté ensuite. Son LEAD60 est de 37 à 47 %, contre 22 à 30 % pour les autres alertes.
6. **Les ordres limites ne se remplissent pas.** Probabilité de remplissage ≤ 19 % (règle conservatrice) : **NON CAPTURABLE**.
7. **Aucune variante ne passe TEST.**
   - SIG_HIST_FOLLOW et SIG_HIST_SOCIAL passent VALID avec FLUX, puis échouent en TEST : IC incluant 0, n = 17 à 18.
   - La combinaison du §23 (LOW_IMPACT + FOLLOW) échoue dès VALID.

**Réponse à la question du §26 : la fenêtre contient surtout de la MICROSTRUCTURE**, c'est-à-dire la course des autres acheteurs et la remise à jour des cotations.
- Il s'y ajoute une part d'**INFORMATION** : la continuation existe même sans impact propre.
- Le **SELF-IMPACT** est modéré (environ 1 point).
- Le **COPY-TRADING** est marginal.

Aucune façon réaliste d'y entrer avec un rendement net positif n'est démontrée hors échantillon.

### Critères du §22

Stratégie principale pré-enregistrée : ordre au marché, estimateur STRICT, L = 2 s, 500 $, sortie au bid à 60 min, frais mesurés.

| Critère | SIG_HIST | LOW_IMPACT | FOLLOW | LOW_IMPACT_FOLLOW | SOCIAL |
|---|---|---|---|---|---|
| 1 information disponible à T | oui | oui | oui | oui | oui |
| 2 contrôle du momentum | non | non | oui | oui | oui |
| 3 positive en VALID | **non** (n = 5) | non (4) | non (3) | non (3) | non (4) |
| 4 positive en TEST | **non** (n = 5) | non (4) | non (1) | non (1) | non (1) |
| 5 à 7 frais, glissement, 500 $ | inclus, mais n insuffisant | | | | |
| 8 liquidité (couverture ≥ 30 %) | **non** (0,7 à 1,5 %) | non | non | non | non |
| 9 dispersion | non | non | non | non | non |
| 10 mécanisme identifiable | partiel | | | | |

En exploratoire (FLUX, mêmes paramètres) :
- SIG_HIST_FOLLOW : VALID +8,5 % [1,8 ; 14,6], puis TEST +9,8 % [−0,7 ; 19,5] sur n = 18 ;
- SIG_HIST_SOCIAL : VALID +5,7 % [1,1 ; 11,4], puis TEST +3,4 % [−7,3 ; 14,6] sur n = 17.

Aucune ne passe TEST ni le critère de liquidité (`signal_variants.csv`, `variants_criteres.csv`).

---

## 1. Le signal et T0 (§1, §2)

**MESURÉ**
- SIG_HIST est inchangé : 1 985 alertes, dont 688 en TRAIN, 561 en VALID et 736 en TEST.
- Le trade du wallet a été retrouvé dans le flux complet dans 100 % des cas.
- T0 = horodatage du bloc (seconde), avec la position exacte dans le bloc. L'ordre du data-api est identique au logIndex on-chain : vérifié sur 102 paires sur 102.
- T0 + 1 s et T0 + 2 s tombent dans le même bloc ou le suivant (un bloc ≈ 2 s). Ils sont **indiscernables**.

**INFÉRÉ**
- Aucun observateur ne peut agir avant le bloc suivant. OBSERVER_0 est théorique.

**INCONNU**
- Le délai réel entre le match et la visibilité du trade avec l'adresse du wallet (nœud Polygon, data-api). T0 est une borne basse.

**PROCHAINE ÉTAPE**
- Mesurer en direct, sur un nœud Polygon, l'écart entre l'heure du bloc et l'heure de réception.

## 2. Les trois prix : A, B, C (§3)

| Latence | 0 s | 2 s | 5 s | 10 s | 30 s | 60 s | 120 s | 300 s |
|---|---|---|---|---|---|---|---|---|
| Part des alertes où B est observé à ± 2 s | 37 % | 36 % | 22 % | 20 % | 13 % | 9 % | 6 % | 4 % |
| B − A (points) | +0,75 | +0,82 | +1,25 | +1,23 | +1,84 | +2,13 | +3,01 | +3,71 |
| B − `P_BEFORE` | +1,48 | +1,59 | +2,07 | +2,00 | +2,47 | +3,17 | +4,34 | +4,68 |
| Contrôles, B − A | +0,23 | +0,36 | +0,37 | +0,39 | +0,22 | −0,09 | +0,59 | −0,21 |

Source : `prix_observable_B.csv` (trois périodes réunies).

**MESURÉ**
- **A** = prix moyen payé par le wallet.
- **B** = best ask lu sur le premier niveau consommé par l'achat suivant d'un autre wallet.
- **C** = prix moyen sur les niveaux réellement consommés. Il est fourni dans `execution_simulation.csv` avec son glissement : +0,2 à +1,6 point de 50 à 5 000 $.
- B et C ne sont jamais déduits de A.

**INFÉRÉ**
- Le prix accessible s'éloigne du prix du wallet dès la première seconde et continue de monter.
- Pour les contrôles, B reste plat.

**INCONNU**
- B aux instants sans trade : 63 % des alertes à 2 s, 91 % à 60 s.
- B n'est observé que là où quelqu'un achète. Il est donc conditionné à une demande qui continue.

**PROCHAINE ÉTAPE**
- Enregistrer `/book` en direct à chaque bloc sur les marchés où des wallets SIG_HIST sont actifs.

## 3. Carnet d'ordres (§4)

Voir `CLOB_DATA_AUDIT.md`.

**MESURÉ : disponible**
- Trades de toutes tailles.
- Ordre exact d'exécution.
- Agressif ou passif.
- Niveaux consommés, via les fills makers.
- Frais payés, via les reçus.

**INCONNU : absent**
- Best bid / best ask entre deux trades.
- Profondeur restante.
- Placements et annulations d'ordres.

**Deux constats nouveaux :**
- **Migration des contrats.** Les contrats v1 sont utilisés jusqu'au 28/04/2026 11:00 UTC ; les v2 démarrent le 03/04. TEST est entièrement en v2 : la microstructure de TEST n'est pas celle de TRAIN.
- **Frais réels.**
  - v1 : 1 reçu payant sur 2 153 ;
  - v2 : 54 % des trades sans frais ;
  - sur les marchés payants, frais ≈ 2,9 % × min(p, 1 − p) par action, soit 1,7 % du notionnel en médiane ;
  - géopolitique : 11 % de trades payants ; politique : 98 % ; macro : 100 % ; autres : 59 %.

## 4. Le wallet déplace-t-il lui-même le prix ? (§5, §6, §12)

Décomposition sur le flux complet : Δ_total = Δ_pre + IMMEDIATE_IMPACT + FOLLOW_THROUGH. L'identité est exacte par construction (`impact_decomposition.csv`, `follow_through.csv`).

**Toutes les alertes (moyennes, en points) :**

| | Split | Δ_pre | IMMEDIATE_IMPACT | FT 60 s | FT 600 s | FT 60 min | Δ_total 60 min |
|---|---|---|---|---|---|---|---|
| SIG_HIST | TRAIN | −0,76 | +1,39 | +0,81 | +1,06 | +1,13 | +1,95 |
| SIG_HIST | VALID | −0,35 | +0,98 | +0,87 | +1,72 | +1,70 | +2,61 |
| SIG_HIST | TEST | +0,10 | +1,09 | +0,65 | +1,17 | +1,29 | +2,15 |
| Contrôles | TEST | −0,10 | +0,93 | −0,33 | −0,30 | −0,06 | +0,78 |

**Gagnants seulement (LEAD60 = 1) :**

| Split | Δ_pre | Impact | FT 60 min | Δ_total |
|---|---|---|---|---|
| TRAIN | −1,0 | +2,4 | +6,6 | +8,6 |
| VALID | −0,8 | +1,5 | +7,9 | +9,7 |
| TEST | +0,2 | +1,7 | +5,5 | +7,5 |

Chez les gagnants, 70 à 80 % du mouvement vient **après** le dernier niveau acheté par le wallet.

**Cas (alertes gagnantes) :**

| Cas | Part |
|---|---|
| C MIXTE (impact + continuation) | 39 à 49 % |
| A INFORMATION (impact faible + continuation) | 21 à 26 % |
| B PRICE IMPACT (impact sans suite) | 4 à 8 % |

Chez les perdantes, B PRICE IMPACT représente 24 à 25 %.

**Ratio de continuation** (médiane de FOLLOW_THROUGH / impact) :
- SIG_HIST : 0,2 à 0,4 sur toutes les alertes, 2,5 à 4,5 sur les gagnantes ;
- contrôles : 0.

**MESURÉ**
- Ce qui était déjà là avant le signal : rien, Δ_pre ≤ 0 en moyenne.
- Ce qu'a fait le wallet : environ 1 point.
- Ce qui vient après : 1,1 à 1,7 point à 60 min, dont environ la moitié dès la première minute.

**INFÉRÉ**
- Le lead n'est pas un artefact d'impact. L'impact du wallet est à peine plus grand que celui des contrôles (1,0-1,4 contre 0,9). C'est la suite qui diffère.

**INCONNU**
- `P_BEFORE` est absent pour 14 à 23 % des alertes : aucun trade dans les 15 min qui précèdent.
- La part du « dernier prix » due au rebond entre achat et vente.

**PROCHAINE ÉTAPE**
- Même décomposition sur le mid mesuré en direct.

## 5. Test contre l'impact du premier trade (§11)

Seuil τ_I = 0,5 point (médiane TRAIN). Source : `self_impact_test.csv`.

| Split | Strate | LEAD60 SIG_HIST | LEAD60 contrôles | Écart | FT 60 min SIG_HIST | FT 60 min contrôles |
|---|---|---|---|---|---|---|
| TRAIN | LOW | 20,0 % | 4,0 % | +16,0 pp | +1,10 | −0,01 |
| VALID | LOW | 19,3 % | 4,0 % | +15,3 pp | +0,89 | −0,21 |
| TEST | LOW | 21,9 % | 11,7 % | +10,2 pp | +1,07 | +0,55 |
| TEST | HIGH | 40,8 % | 19,3 % | +21,5 pp | +1,42 | −0,73 |

**MESURÉ**
- Le signal reste prédictif quand l'impact immédiat est nul (impact moyen de la strate LOW : 0,0 point).

**INFÉRÉ**
- Cela renforce l'hypothèse d'un signal porteur d'une information ou d'un positionnement, plutôt que d'un effet de taille.

**INCONNU**
- La nature de cette information : l'heure des nouvelles publiques n'est pas alignée.

**PROCHAINE ÉTAPE**
- Aligner les alertes LOW_IMPACT gagnantes sur un flux d'actualité horodaté.

## 6. Pourquoi −2,3 % à 1 seconde ? (§7)

Reproduction exacte du code de la phase 9 (`reproduction_p9.csv`, `reproduction_p9_detail.csv`).

**TEST, n = 244 :**

| Statistique | Valeur |
|---|---|
| Moyenne | −2,34 % (identique à la phase 9) |
| Médiane | −2,23 % |
| P10 / P25 / P75 / P90 | −16,3 / −7,2 / +0,9 / +12,6 % |
| Min / max | −102 % / +105 % |
| Part positive | 32 % |

| Poste de la perte (TEST) | Mesure |
|---|---|
| Brut, sans frais | **+0,28 %** |
| Frais supposés par la phase 9 | −2,61 % |
| Frais mesurés on-chain | environ −0,9 % → net **−0,61 %** (médiane −0,89 %) |
| Délai réel d'entrée | premier fill à +33 s en médiane, fill moyen pondéré à +68 s (et non 1 s) |
| Prime d'entrée | +1,7 point au-dessus du prix du wallet, +3,0 au-dessus du prix de référence |
| Sortie | −0,8 point sous le dernier prix (on vend au bid) |

**Gagnants et perdants :** mêmes délais et même prime, l'écart vient de la continuation.
- Gagnants (32 %) : LEAD60 90 %, net moyen +13 % ;
- perdants : LEAD60 25 %, net moyen −9,7 %.

**Avec les frais mesurés, sur les trois périodes :** TRAIN +3,2 %, VALID +4,7 %, TEST −0,6 %.

**INFÉRÉ**
- Le « −2,3 % à 1 s » combinait deux choses : une hypothèse de frais trop lourde, et un observateur qui entrait en réalité une demi-minute plus tard.
- Le signe de TEST reste négatif, mais faible.

## 7. Latence (§8)

Voir `latency_curve.csv` et `execution_simulation.csv`.

**Estimateur STRICT (pré-enregistré).** À 500 $, l'entrée n'est observable que dans 2 à 9 % des alertes selon la latence, et l'entrée + la sortie dans 0,7 à 1,5 % (L = 2 s). Les rendements sont **non évaluables** (n = 4 à 10 par période).

**Estimateur FLUX (exploratoire, écart déclaré).** Net moyen à 500 $, sortie à 60 min, sur le sous-ensemble où l'entrée et la sortie sont observables :

| Latence | TRAIN | VALID | TEST | Couverture TEST |
|---|---|---|---|---|
| 0 s | +6,0 % | +5,9 % | +4,3 % | 6,1 % |
| 2 s | +6,9 % [2,2 ; 12,9] | +5,3 % [−0,1 ; 10,9] | +4,1 % [−1,9 ; 11,6] | 5,6 % |
| 10 s | +7,4 % | +4,1 % | +5,1 % | 5,2 % |
| 60 s | +5,9 % | +6,3 % | +0,9 % | 3,0 % |
| 120 s | +2,8 % | +1,5 % | −3,1 % | 2,7 % |
| 300 s | +3,0 % | −1,8 % | −5,1 % | 1,8 % |

- Médianes : +0,1 à +1 %. Part des trades gagnants : 52 à 64 %.
- MAE moyen : −3 à −7 points ; MFE : +7 à +12 points.
- Contrôles dans les mêmes conditions : +0,0 %, +0,6 % et +0,6 %.

**INFÉRÉ**
- L'avantage apparent s'efface entre 60 et 120 s.
- Mais il est mesuré là où d'autres ont acheté ensuite (voir §5 du verdict) : **il n'est pas réalisable en l'état**.

**INCONNU**
- Le rendement des 87 à 94 % d'alertes sans entrée observable.

## 8. Taille (§9)

Voir `size_curve.csv` (FLUX, L = 2 s, sortie à 60 min).

**Net moyen en TEST :**

| Taille | 50 $ | 100 $ | 250 $ | 500 $ | 1 000 $ | 2 500 $ | 5 000 $ |
|---|---|---|---|---|---|---|---|
| Net | +2,4 % | +1,9 % | +3,9 % | +4,1 % | +1,6 % | +4,5 % | +0,1 % |
| Couverture | 19 % | 14 % | 8 % | 6 % | 3 % | 0,8 % | 0,1 % |

Glissement (C − B) : +0,2 point à 50 $, +0,35 à 500 $, +0,6 à 2 500 $.

**INFÉRÉ**
- La contrainte n'est pas le glissement, c'est **l'observabilité de la profondeur**.
- À partir de 500 $, moins de 15 % des alertes offrent une profondeur visible à l'entrée et à la sortie (6 % en TEST).
- « Taille maximale avant que le signal devienne négatif » : **INCONNUE**. Le signe reste positif jusqu'à 2 500 $ sur le sous-ensemble observé, mais ce sous-ensemble tend vers zéro.

## 9. Ordre au marché contre ordre limite (§10)

Voir `limit_orders.csv`.

**Paramètres testés :**
- pose à T0 + 2 s, 500 $ ;
- K1 = ask avant impact, K2 = prix du wallet, K3 = mi-chemin ;
- durée de vie 60 ou 300 s.

**MESURÉ (règle conservatrice)**
- Probabilité de remplissage : **3,7 à 10 % en TEST**, 3,7 à 19 % sur les trois périodes.
- Rendement conditionnel en TEST à 300 s : −12 à −13 %. C'est de la sélection adverse : l'ordre se remplit surtout quand le prix redescend.

**Classement : NON CAPTURABLE** pour les 36 combinaisons.

## 10. Les autres wallets, le copy-trading, leader et follower (§13, §14, §15)

**Dans les 10 min qui suivent l'alerte** (`follower_attribution.csv`) :

| | SIG_HIST | Contrôles |
|---|---|---|
| Acheteurs distincts (médiane) | 4 à 9 | 2 à 3 |
| Volume acheteur (médiane) | 225 à 590 $ | 55 à 128 $ |
| Hausse du ask | +1,7 à +2,3 points | environ 0 |

**Qui fait monter le ask (SIG_HIST) :**

| Source | Contribution |
|---|---|
| Achats de wallets non récurrents | +1,4 à +3,2 points |
| Re-trades du wallet signalé | +0,2 à +0,3 point |
| Suiveurs liés et récurrents | environ +0,2 point |
| Cotations entre deux trades (réassort des makers) | −0,05 à −1,4 point |

**Graphe leader → suiveur** (`follower_analysis.csv`, `follower_summary.csv`) :
- 20 447 couples : 198 FOLLOWER, 99 LEADER, 20 150 INDEPENDENT ;
- 47 des 139 leaders ont au moins un follower ;
- délai médian 68 s ; répétition médiane 3 marchés ;
- mouvement indépendant avant le suiveur : 16 % des cas ;
- rendement du suiveur à 60 min : +2,7 points, contre +5,7 pour le leader ;
- un suiveur récurrent est présent dans 34 % des FAE SIG_HIST, contre 18 % des autres FAE des mêmes wallets ;
- chaînes A → B → C : 11 % des alertes, contre 4 %.

**INFÉRÉ**
- Le copy-trading est réel (répétition, délai d'environ une minute, asymétrie aval/amont), mais **trop petit pour créer le mouvement**. Les suiveurs récurrents pèsent 13 à 14 % du volume acheteur.
- La continuation est portée par un afflux large d'acheteurs sans lien historique avec le wallet : même information, même attention, ou robots de momentum.

**INCONNU**
- Pourquoi ces acheteurs arrivent-ils ? Il n'y a pas d'horodatage des nouvelles.
- Leurs robots et leurs latences.

**PROCHAINE ÉTAPE**
- Classer ces acheteurs par latence (même bloc, moins de 5 s, plus) et par historique, pour séparer robots et humains.

## 11. Les variantes (§16 à §19)

**Seuils gelés le 30/09 à 17:40 UTC**, avant toute lecture des variantes en VALID et TEST :
- τ_I = 0,5 point ;
- τ_F = 2,06 points ;
- k = 2, W = 300 s.

**Résultat principal (STRICT) :** non évaluable, 1 à 10 trades par période.

**Résultat exploratoire (FLUX, 500 $, sortie à 60 min) :**

| Variante | TRAIN | VALID | TEST |
|---|---|---|---|
| SIG_HIST | +6,9 % [1,9 ; 12,4] n = 90 | +5,3 % [−0,1 ; 11,6] n = 75 | +4,1 % [−1,8 ; 11,7] n = 41 |
| LOW_IMPACT | +6,1 % n = 51 | +0,1 % n = 35 | +3,9 % n = 26 |
| FOLLOW | +12,0 % [2,9 ; 24,9] | **+8,5 % [1,8 ; 14,6]** | +9,8 % [−0,7 ; 19,5] n = 18 |
| LOW_IMPACT_FOLLOW | +8,7 % | −0,2 % | +13,4 % n = 11 |
| SOCIAL | +7,8 % n = 30 | **+5,7 % [1,1 ; 11,4]** | +3,4 % [−7,3 ; 14,6] n = 17 |

- Aucune variante ne passe TEST.
- Aucune ne dépasse 25 % de couverture.
- Le §23 (SIG_HIST + LOW SELF IMPACT + FOLLOW THROUGH, avec entrée de l'observateur et rendement net positif hors échantillon) **n'existe pas dans ces données**.

## 12. Maduro et Iran (§20)

Voir `maduro_iran_timeline.csv`, `maduro_iran_minutes.csv`.

**Données manquantes de l'Iran avant 05:28 : trouvées.**
- Source : data-api avec `start`/`end`.
- Couverture : 21 168 trades preneurs du 27/02 12:00 au 28/02 07:00.
- Complétude : 807 transactions sur 807 contre les logs on-chain de la phase 2.

**Iran, 28/02 (UTC) :**

| Heure | Événement | Niveau |
|---|---|---|
| 27/02 12:52 → 21:38 | 5 alertes SIG_HIST dans les deux sens (2 NO, 3 YES, 296 à 6 480 $) | MESURÉ |
| 27/02 14:57:05 et 14:57:29 | Planktonbets et Mrs.Joker achètent chacun 1 700 $ de YES à 0,24, à 24 s d'écart | MESURÉ |
| 27/02 17:20:35 et 17:21:29 | les mêmes rachètent (3 868 $ et 1 938 $ à 0,19), à 54 s d'écart | MESURÉ |
| 27/02 20:38 | autorisation des frappes (non publique à l'époque) | APPROXIMATE |
| 28/02 04:48:21-23 | Planktonbets achète 14 946 $ de YES à 0,13-0,15 (100 niveaux consommés) ; prix à +10 min : 0,13 | MESURÉ |
| 05:59 et 06:07 | 154x838hjd6 achète deux fois 4 706 $ (financé 1 min avant, phase 2) | MESURÉ |
| 06:10 | **première tranche de 5 min au-dessus du P99 de la veille** : 158 206 $. Entre 00:00 et 06:15 : 1 tranche sur 75 dépasse, contre 0,8 attendue par hasard | MESURÉ |
| 06:12:17 | premier trade à p_yes ≥ 0,5 | MESURÉ |
| 06:13:22 | repricing (série CLOB, 1,5 × 0,195) | MESURÉ |
| ~06:15 | début des frappes | APPROXIMATE |
| 06:16:09 | alerte SIG_HIST : achat de **NO** à 0,069 | MESURÉ |
| 06:23 | annonce israélienne (Katz) et sirènes | VÉRIFIÉ |

**Maduro, 03/01 (UTC) :**

| Heure | Événement | Niveau |
|---|---|---|
| 01:35 → 05:55 | 7 tranches au-dessus du P99 de la veille, contre 0,7 attendue : 01:35, 02:15, 02:55, 03:40, 05:35, 05:45, 05:55. Petits montants (P99 = 3 932 $) | MESURÉ |
| 03:46 | ordre de lancement (non public à l'époque) | APPROXIMATE |
| 05:35:27 et 05:35:41 | chileno777 (215 $), puis Chiwawas (5 188 $ à 0,117) | MESURÉ |
| 05:46:23 | Chiwawas rachète 4 710 $ (financé 2,8 min avant, phase 8) | MESURÉ |
| 05:51:25 | seule alerte SIG_HIST : achat de **NO** | MESURÉ |
| ~06:00 | premières explosions signalées | APPROXIMATE |
| 06:15:41 | premier trade à p_yes ≥ 0,5 (22 985 $) | MESURÉ |
| 06:16:11 | repricing (série CLOB) | MESURÉ |
| 09:21 | annonce de Trump | APPROXIMATE |

**INFÉRÉ**
- **Iran.** Rapporté à la veille, le flux n'est pas anormal avant 06:10, soit 3 minutes avant le repricing. L'« activité dès 05:28 » de la phase 9 venait d'une mauvaise référence. Le marché a repricé environ 10 min avant l'annonce officielle et à peu près au moment des frappes (heure approximative).
- **Maduro.** Le flux anormal commence dès 01:35, avant même l'ordre de lancement (APPROXIMATE), sur de petits montants.
- Dans les deux cas, SIG_HIST n'a rien vu dans le bon sens.

**INCONNU**
- Les premières sources publiques à la minute : OSINT, médias locaux, suivi aérien.

**PROCHAINE ÉTAPE**
- Collecter des posts X archivés et des dépêches horodatées autour de 05:30-06:15.

## 13. Les 8 comptes (§21)

Voir `population_A_mecanismes.csv`.

| Mécanisme | Résultat |
|---|---|
| Self-impact | Chiwawas : 1 et 2 points (HIGH), sans continuation (p_yes 0,11 à +10 min, sous son prix). 154x838hjd6 à 06:07 : 0,1 point (LOW), puis repricing public |
| Suiveurs | **aucun suiveur récurrent** (0 wallet sur 2 marchés ou plus), pour les 8 comptes |
| Convergence / accumulation | aucun drapeau CONV ou ACC en phase 9. Une **synchronisation interne au réseau** est observée : Planktonbets et Mrs.Joker, 24 s puis 54 s d'écart, mêmes montants le 27/02 |
| Financement | S_FASTFUND : Chiwawas (2,8 min avant l'achat de 05:46) et 154x838hjd6 (1 min avant, phase 2). Planktonbets et Mrs.Joker sur l'Iran : INCONNU |

**Verdict :** aucun des nouveaux mécanismes de marché (self-impact suivi de continuation, suiveurs, convergence) n'explique leur activité : **NO SIGNAL**. Deux traits hors signal SIG_HIST :
- le financement juste avant l'achat ;
- des achats synchronisés entre comptes du même réseau.

## 14. Écarts au protocole

1. **Estimateur FLUX ajouté après lecture des résultats STRICT.**
   - Motif : couverture de 3 à 8 % et n de 4 à 10.
   - Il n'est **jamais** utilisé pour conclure à une réussite, et il est biaisé par sélection sur le futur.
2. **Bug d'agrégation corrigé.** Les cas de profondeur insuffisante étaient exclus du dénominateur. Corrigé avant toute conclusion.
3. **Repricing dans la chronologie.** Ma règle « premier trade ≥ 1,5 × référence » se déclenchait sur un seul petit trade (Maduro 03:42). Elle a été remplacée par le repère de la phase 2 (série CLOB) et par le premier trade à 0,5.
4. **Référence de l'activité inhabituelle** : la veille de 12:00 à 24:00, et non les fenêtres de la phase 9. Cela change la conclusion Iran.
5. **Marché Iran dans le détecteur.** Son `endDate` Gamma (31/01) est faux. L'échéance a été lue dans l'intitulé (28/02 23:59 ET).
6. **`P_BEFORE` absent** pour 14 à 23 % des alertes. Elles sont exclues de LOW_IMPACT.
7. **Frais de sortie** : même coefficient c que pour l'entrée (celui du wallet signalé à T0).

## 15. Fichiers

**Rapports et protocole**
- `RAPPORT_PHASE10.md`, `PROTOCOLE_P10.md`, `data_audit.md`, `CLOB_DATA_AUDIT.md`, `frozen_p10.json`

**Tables demandées**
- `execution_simulation.csv`, `impact_decomposition.csv`, `follow_through.csv`, `follower_analysis.csv`
- `latency_curve.csv`, `size_curve.csv`, `signal_variants.csv`, `maduro_iran_timeline.csv`

**Tables complémentaires**
- `variants_criteres.csv`, `limit_orders.csv`, `reproduction_p9.csv`, `reproduction_p9_detail.csv`
- `self_impact_test.csv`, `prix_observable_B.csv`, `follower_summary.csv`, `follower_attribution.csv`
- `maduro_iran_minutes.csv`, `population_A_mecanismes.csv`

**Scripts** (dans `scripts/`)
- `p10_replay.py`, `p10_impact.py`, `p10_execution.py`, `p10_followers.py`, `p10_variants.py`, `p10_maduro_iran.py`

**Données brutes** : `donnees/brut_p10/`, avec les fenêtres data-api, les reçus de frais et les flux Maduro/Iran.

**Sources publiques :**
- [Wikipedia, 2026 United States intervention in Venezuela](https://en.wikipedia.org/wiki/2026_United_States_intervention_in_Venezuela)
- [Wikipedia, 2026 Iran war](https://en.wikipedia.org/wiki/2026_Iran_war)
- [Times of Israel, liveblog du 28/02/2026](https://www.timesofisrael.com/liveblog_entry/israel-has-launched-a-preemptive-attack-on-iran-defense-minister-katz-says-sirens-sound-across-israel/)
