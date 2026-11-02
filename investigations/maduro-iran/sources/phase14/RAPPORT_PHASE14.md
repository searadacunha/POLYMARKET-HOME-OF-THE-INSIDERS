# Phase 14 : exécution au 2e achat

## QUESTION

« Le 2e achat du même wallet fournit-il une fenêtre d'exécution réellement exploitable ? »

## Réponse

**Non.** Conclusion de l'arbre pré-enregistré : **B. SIGNAL PRÉDICTIF MAIS NON EXÉCUTABLE.**

**Le 2e achat reste prédictif hors échantillon.** Après le prix d'avant le 2e achat, on mesure un mouvement de +3 points à 60 min (LEAD60_2) :

| Split | SECOND_BUY | Contrôles | Écart (IC 95 %) |
|---|---|---|---|
| VALID | 39,8 % | 11,6 % | +28 points (+15 à +40) |
| TEST | 27,8 % | 10,0 % | +18 points (+7 à +30) |

**Mais il ne laisse rien à prendre.** Cas principal : entrée 2 s après le 2e achat, 500 $, sortie à 300 s, frais inclus.

| Split | Net moyen (IC 95 %) | Médiane | Part positive |
|---|---|---|---|
| VALID | +1,3 % (−2,4 à +5,1) | 0,0 % | 49 % |
| TEST | **−0,7 %** (−7,7 à +7,1) | −2,4 % | 34 % |

**La latence n'est pas en cause.** Avec la connaissance instantanée du wallet (ORACLE), le résultat est le même : +1,1 % en VALID, −1,5 % en TEST. Le problème, c'est l'information encore disponible, pas la vitesse.

**Le premier achat valait plus que le second.** Sur les mêmes alertes, une entrée au premier achat fait +8,1 % en VALID et +3,7 % en TEST. Cette comparaison n'est pas une stratégie, car savoir qu'un 2e achat viendra utilise le futur. Elle montre que la fenêtre du 2e achat arrive après l'essentiel du mouvement.

**Une partie du pouvoir prédictif suit un mouvement déjà visible :**
- 32 % (VALID) et 23 % (TEST) des 2e achats suivent une hausse d'au moins 1 point dans la minute, contre 13 à 17 % pour les contrôles ;
- leur LEAD60_2 est de 55 à 63 % ;
- sur prix stable, l'avantage sur les contrôles tombe à +16 et +7 points, avec des IC qui touchent ou incluent 0 ;
- la règle pré-enregistrée (signe) ne classe pas le cas en C, mais le momentum explique une part réelle.

Aucun ordre, aucune transaction. SIG_HIST V1 est inchangé (sha256 bbb016d2…, revérifiée le 01/10). Aucun seuil n'a été modifié.

---

## 1. Protocole

`PROTOCOLE_P14.md`, écrit avant tout calcul de résultat.

**Points clés :**
- **définition du 2e achat** reprise de `p13_second_trade.py` (W = 3 600 s gelé sur TRAIN) ;
- **contrôles :** ceux de la phase 10 ;
- **estimateurs d'exécution :** ceux de la phase 10, avec FLUX en principal (STRICT est observable dans moins de 2 % des cas) ;
- **arbre de décision** fixé avant les résultats.

**Contrôle de reconstruction (bloquant) :** les 3 949 événements redonnent exactement les T2, le nombre d'achats suivants et LEAD60_2 de `phase13/second_trade_detail.csv`. Il n'y a donc pas eu de redéfinition.

## 2. Données

| Source | Contenu | Limite |
|---|---|---|
| Flux de la phase 10 (`p10/tapes`) | tous les trades, toutes tailles, ordre exact, niveaux makers consommés, de T1 − 900 s à T1 + 4 500 s | **pas de carnet complet** : seuls les niveaux réellement pris sont visibles (`phase10/CLOB_DATA_AUDIT.md`) |
| Carnet en direct (phase 11) | carnet complet depuis le 01/10 08:51 UTC | 2 alertes, aucun 2e achat pour l'instant |
| Latence | mesurée en phase 13 | historique : T_wallet supposé = T2 + 2 s |

**Couverture du flux : 100 %.** Les 662 2e achats (SIG et contrôles) sont tous retrouvés dans les flux.

## 3. Population

**Tous les 2e achats (`phase14_second_buy_events.csv`) :**

| | TRAIN | VALID | TEST |
|---|---|---|---|
| Alertes SIG_HIST | 688 | 561 | 736 |
| **2e achats SIG_HIST** | 144 | **118** | **133** |
| 2e achats contrôles | 98 | 69 | 100 |
| Marchés / wallets (SIG) | 97 / 38 | 61 / 35 | 75 / 52 |
| Résolution connue (SIG) | 144 | 118 | 133 |

**Conservation (cas principal) :**

| | VALID SIG | TEST SIG | VALID contrôle | TEST contrôle |
|---|---|---|---|---|
| Entrée observable (achats d'autres wallets dans les 60 s) | 86 | 83 | 38 | 45 |
| dont 500 $ entièrement exécutés | 39 | 17 | 10 | 11 |
| **EXECUTION-MEASURABLE** (entrée et sortie observées) | **74 (63 %)** | **62 (47 %)** | 30 | 34 |
| Marchés / wallets mesurables | 36 / 26 | 43 / 35 | | |

**Par catégorie** (SIG, tous / mesurables) :

| Catégorie | VALID | TEST |
|---|---|---|
| géopolitique / guerre | 71 / 53 | 65 / 24 |
| autres | 34 / 15 | 45 / 29 |
| élections | 11 / 5 | 14 / 5 |
| macro / Fed | 2 / 1 | 9 / 4 |

**Les cas mesurables ne représentent pas tous les 2e achats.** Ce sont des marchés plus actifs, où le 2e achat est plus souvent suivi d'un mouvement :

| LEAD60_2 | Mesurables | Non mesurables |
|---|---|---|
| TEST SIG | 35 % | 21 % |
| VALID SIG | 42 % | 36 % |
| TEST contrôles | 18 % | 6 % |

Ce biais est **favorable** à l'exécution. Le résultat négatif n'en est que plus net.

## 4. Timing (§5, §9)

**T2 − T1 (secondes) :**

| | P10 | P25 | Médiane | P75 | P90 |
|---|---|---|---|---|---|
| SIG VALID | 5 | 17 | **66** | 584 | 1 550 |
| SIG TEST | 5 | 16 | **81** | 581 | 1 872 |
| Contrôle VALID | 19 | 48 | 242 | 878 | 1 694 |
| Contrôle TEST | 13 | 30 | 92 | 517 | 1 883 |

**T_OBS − T2.**
- En historique, ce délai est une hypothèse : 2 s (les sources de la phase 13 ont une médiane de 1,19 à 2,08 s). La seule mesure directe, sur le trade de l'alerte live du 01/10 (un 1er achat, pas un 2e), donne 1,59 s par RTDS et 15 s par la chaîne.
- **Premier repère de carnet après T_OBS :**
  - 2e achats SIG : médiane **4 s** (VALID) et **6 s** (TEST), P90 de 33 à 44 s ;
  - contrôles : 10 à 11 s.
- 27 % (VALID) et 38 % (TEST) des 2e achats SIG n'ont **aucun** achat d'un autre wallet dans la minute.

## 5. Carnet à T_OBS (§6)

T_OBS = T2 + 2 s. Historique : seulement ce qui est observé (`phase14_tables.csv`, table `carnet`).

| | VALID SIG | TEST SIG |
|---|---|---|
| Best ask observé | 73 % | 62 % |
| Best bid observé (vente dans ±2 s) | 33 % | 36 % |
| Mid et spread | **UNKNOWN / NO BOOK DATA** hors de ces cas ; spread médian 1 point quand il est mesuré (n = 31 et 36) | |
| Best ask − prix du wallet au 2e achat | +1,1 point (médiane +0,3) | +0,6 point (médiane +0,5) |
| Profondeur consommée dans les 10 s : jusqu'à +0,5 / +1 / +2 points / totale (médianes, borne basse) | 48 / 72 / 87 / 88 $ | 35 / 37 / 43 / 54 $ |
| Niveaux consommés par le 2e achat lui-même (médiane) | 5 | 4 |
| Glissement du 2e achat lui-même | +0,7 point | +0,6 point |

Le 2e achat balaie lui-même 4 à 5 niveaux. L'observateur arrive derrière, sur un carnet où la profondeur visible en 10 s se compte en dizaines de dollars.

## 6. Exécution (§7, §8)

**FLUX, T2 + 2 s, 500 $, SIG_HIST** (`phase14_execution.csv`) :

| Horizon | VALID net moyen | VALID médiane | TEST net moyen | TEST médiane | Délai réel de sortie (médiane, VALID / TEST) |
|---|---|---|---|---|---|
| 1 s | −1,0 % | −0,9 % | −1,0 % | −2,0 % | 170 / 218 s |
| 10 s | −1,0 % | −0,9 % | −1,0 % | −2,0 % | 170 / 218 s |
| 30 s | −1,0 % | −1,0 % | −0,2 % | −2,0 % | 178 / 232 s |
| 60 s | +0,04 % | −1,0 % | −0,04 % | −2,0 % | 184 / 263 s |
| 120 s | −0,1 % | −0,4 % | −0,7 % | −2,3 % | 269 / 331 s |
| **300 s** | **+1,3 %** | **0,0 %** | **−0,7 %** | **−2,4 %** | 400 / 601 s |
| 600 s | +1,7 % | +0,9 % | −1,6 % | −2,0 % | 748 / 909 s |
| résolution | −2,2 % | −100 % | −7,5 % | −100 % | |

**Comment lire ces chiffres :**
- **Les horizons courts ne sont pas observables en historique.** Le premier vendeur après T_OBS + 1 s arrive en médiane 3 minutes plus tard, donc une « sortie à 1 s » se fait en réalité vers 3 minutes. Seul le carnet en direct mesurera ces horizons.
- **Frais moyens** pour l'aller-retour de 500 $ : 0,86 $ en VALID, 2,30 $ en TEST.
- **Glissement d'entrée médian : 0.** Le coût est dans la distance au prix du wallet, pas dans la marche du carnet.

**Prix comparés** (prix d'un autre wallet après T2, moins le prix payé par le wallet au 2e achat ; moyennes, en points) :

| | +1 s | +5 s | +10 s | +30 s | +60 s | +120 s | +300 s |
|---|---|---|---|---|---|---|---|
| SIG VALID | −0,8 | −0,4 | −0,5 | −0,2 | +0,7 | +0,3 | +1,8 |
| SIG TEST | −0,5 | −0,3 | −0,2 | −0,3 | +0,3 | +0,6 | +0,9 |
| Contrôle VALID | −0,9 | −0,7 | −0,6 | −0,5 | −0,3 | 0,0 | −0,4 |
| Contrôle TEST | −0,5 | −0,5 | −0,4 | −0,4 | −0,3 | −0,3 | −0,4 |

Pendant la première minute, le prix des autres reste **sous** le prix payé par le wallet. Il ne le dépasse que de 0,9 à 1,8 point à 5 minutes. C'est moins que le coût d'entrée de l'observateur.

## 7. VALID (§16)

Cas principal : n = 74, 36 marchés, 26 wallets, aucun wallet au-delà de 15 % des cas.

| Mesure | Valeur |
|---|---|
| Net moyen | **+1,28 %**, IC 95 % −2,41 à +5,09 |
| Médiane | 0,0 % |
| P25 / P75 | −3,7 % / +5,3 % |
| Part positive | 49 % |
| Contrôle | −3,10 % (n = 30) |
| Écart avec le contrôle | +4,4 points, IC −0,5 à +9,0 |

**Verdict VALID : non significatif.**

## 8. TEST (prioritaire)

Cas principal : n = 62, 43 marchés, 35 wallets, aucun wallet au-delà de 6,5 % des cas.

| Mesure | Valeur |
|---|---|
| Net moyen | **−0,70 %**, IC 95 % −7,69 à +7,07 |
| Médiane | **−2,39 %** |
| P25 / P75 | −9,6 % / +3,3 % |
| Part positive | 34 % |
| Contrôle | −7,47 % (n = 34) |
| Écart avec le contrôle | +6,8 points, IC −2,2 à +17,2 |

**Verdict TEST : négatif en médiane, non significatif en moyenne.**

**Sensibilités (500 $, 300 s, L = 2 s) :**

| Estimateur | VALID | TEST | Lecture |
|---|---|---|---|
| STRICT | +0,02 % (n = 19) | −7,3 % (n = 4) | INSUFFICIENT SAMPLE |
| SUIVANT | −2,0 % (n = 40) | −11,3 % (n = 20) | |

**ORACLE contre RÉALISTE (§13), FLUX, 500 $, 300 s :**

| Latence | VALID | TEST |
|---|---|---|
| 0 s (ORACLE) | +1,09 % | −1,49 % |
| 2 s (RÉALISTE) | +1,28 % | −0,70 % |
| 5 s (prudent) | +1,09 % | +0,04 % |
| 10 s | +1,15 % | +0,55 % |
| 60 s | −0,40 % | −5,94 % |

La courbe est plate jusqu'à 10 s, puis se dégrade. **Connaître le wallet plus tôt ne change rien.** Il ne s'agit ni d'un problème de latence ni d'un problème de liquidité au sens strict : il ne reste pas assez d'information à prendre.

## 9. Contrôles (§10, §11, §12)

**SECOND_BUY contre MATCHED_CONTROL** (contrôles de la phase 10 ; `phase14_controls.csv`) :

| Mesure | VALID | TEST |
|---|---|---|
| LEAD60_2 | 39,8 % contre 11,6 % ; +28,2 points (IC +15,5 à +40,2) | 27,8 % contre 10,0 % ; +17,8 points (IC +7,0 à +29,8) |
| Mouvement à 60 min après le prix du 2e achat (phase 13) | +1,45 contre −0,21 point ; IC de l'écart −0,6 à +3,9 | +1,92 contre −0,86 point ; IC +0,3 à +5,3 |
| Net 500 $ à 300 s | +1,3 % contre −3,1 % | −0,7 % contre −7,5 % |
| Net à 60 s | +0,04 % contre −3,6 % ; IC de l'écart **+0,8 à +6,9** | −0,04 % contre −8,4 % ; IC **+0,8 à +18,2** |

L'écart avec les contrôles est positif. Mais les contrôles perdent beaucoup avec le même estimateur : FLUX pénalise toute entrée, car il paie les niveaux que d'autres prennent en montant. **Le critère qui décide est le net absolu**, et il vaut environ 0.

**Avant contre après le 2e achat (§11).** Moyennes en points. « Avant » compte tous les wallets, « après » les autres wallets seulement.

| SIG | −120 s | −60 s | −30 s | −10 s | +10 s | +60 s | +300 s |
|---|---|---|---|---|---|---|---|
| VALID | +1,39 | +1,04 | +0,88 | +0,41 | +0,68 | +1,78 | +2,88 |
| TEST | +0,79 | +0,39 | +0,34 | +0,54 | +1,11 | +1,56 | +2,11 |
| Contrôle VALID | +0,75 | +0,62 | +0,43 | +0,11 | +0,36 | +0,60 | +0,57 |
| Contrôle TEST | +0,73 | +0,59 | +0,50 | +0,17 | +0,14 | +0,28 | +0,22 |

Lecture :
- les médianes avant le 2e achat sont nulles jusqu'à −60 s ;
- en VALID, environ un tiers du mouvement moyen de la fenêtre −120 s à +300 s a lieu avant le 2e achat (+1,39 sur +4,27 points) ;
- corrélation entre le mouvement à −60 s et celui à +300 s : +0,08 (VALID) et −0,08 (TEST).

**Segments descriptifs (§12)**, mouvement à −60 s, seuil ±1 point. Aucune règle n'en est tirée.

| SIG | Part VALID / TEST | LEAD60_2 VALID / TEST | Net 500 $ 300 s VALID / TEST |
|---|---|---|---|
| prix stable | 53 % / 58 % | 26 % / 18 % | +0,2 % / 0,0 % |
| hausse préalable | 32 % / 23 % | **63 % / 55 %** | +3,8 % / +6,7 % (n = 26 / 18) |
| baisse préalable | 8 % / 4 % | 22 % / 40 % | −10 % / −18 % (n = 6 / 5) |
| inconnu (pas de trade avant) | 8 % / 15 % | | |

**Contrôles sur prix stable :** LEAD60_2 de 10 % (VALID) et 11 % (TEST). L'écart reste positif (+16 et +7 points), mais **ses IC touchent ou incluent 0** (−0,1 à +31,7 ; −4,1 à +18,6).

**Lecture :**
- le 2e achat ajoute un peu d'information sur prix stable, sans que ce soit établi ;
- une grande partie de son pouvoir prédictif vient des cas qui suivent une hausse déjà visible ;
- la règle pré-enregistrée (le signe de l'écart sur prix stable) ne déclenche pas la conclusion C ; une règle sur l'IC l'aurait rendue ambiguë ;
- **la segmentation « hausse préalable » n'est pas un signal** : elle est lue sur les données de TEST, et ses n sont petits.

## 10. Capacité (§17)

FLUX, T2 + 2 s, sortie 300 s, SIG_HIST (`phase14_capacity.csv`). Parts calculées sur **tous** les 2e achats.

| Taille | Entièrement exécutable (VALID / TEST) | Partiel CAPACITY_LIMIT | Impossible | Glissement P90 | Net moyen avec partiels |
|---|---|---|---|---|---|
| 50 $ | 52 % / 36 % | 21 % / 26 % | 27 % / 38 % | 0,4 / 0,7 point | +1,0 % / +3,0 % |
| 100 $ | 47 % / 26 % | 26 % / 37 % | 27 % / 38 % | 0,7 / 1,0 point | +1,4 % / +2,0 % |
| 250 $ | 35 % / 17 % | 38 % / 45 % | 27 % / 38 % | 0,9 / 1,1 point | +2,0 % / +0,5 % |
| 500 $ | 33 % / 13 % | 40 % / 50 % | 27 % / 38 % | 1,3 / 1,6 point | +1,3 % / −0,7 % |
| 1 000 $ | 25 % / 11 % | 48 % / 51 % | 27 % / 38 % | 1,7 / 1,6 point | +0,9 % / −1,1 % |

**Lecture :**
- **En TEST, 500 $ ne sont entièrement exécutables que dans 13 % des 2e achats.**
- Le sous-ensemble entièrement exécuté paraît gagnant (+14 % en moyenne en TEST, n = 13). Mais pouvoir exécuter 500 $ en entier dépend du volume acheté **après** T_OBS par les autres. C'est une information future : ce sous-ensemble ne peut pas être choisi au moment de la décision.
- **Petites tailles :** les chiffres à 50 et 100 $ sont faiblement positifs en TEST (+2 à +3 %), mais non significatifs et sans IC. Ce ne sont pas des montants qui font une stratégie.

## 11. Nouveaux wallets (§15)

**Par construction,** un 2e achat SIG_HIST exige un 1er achat SIG_HIST, donc un wallet **déjà qualifié**. Le 2e achat ne résout pas le problème des wallets nouveaux (phase 13 : NEW_WALLET_DETECTION = NOT POSSIBLE WITH CURRENT SIGNAL).

**Wallets récemment qualifiés** (hist_n de 5 à 9, ou qualification depuis moins de 30 jours, à T1) :

| | VALID | TEST | Wallets anciens |
|---|---|---|---|
| Alertes suivies d'un 2e achat | 20 % | 24 % | 16 à 22 % |
| LEAD60_2 de ces 2e achats | 48 % | 28 % | 28 à 42 % |

**Première alerte SIG_HIST d'un wallet :** suivie d'un 2e achat dans 25 % (VALID, 9 cas) et 34 % (TEST, 13 cas).

Un wallet tout juste qualifié devient donc observable au 2e achat aussi souvent qu'un ancien. Mais, comme pour les autres, le 2e achat n'est pas exécutable.

## 12. Les 8 comptes (§14)

`phase14_cas.csv`. Même règle appliquée à leurs FAE ; aucun n'est SIG_HIST et aucun n'entre dans l'échantillon.
- **Chiwawas : 2 FAE suivis d'un 2e achat :**
  - 31/12, +424 s, 4 704 $ à 0,037 ;
  - 03/01 05:35, +642 s, 4 710 $ à 0,125, sur le marché Maduro. Dans le flux de la phase 10 : **aucun achat d'un autre wallet dans la minute** après T_OBS, donc entrée **pas de repère / UNKNOWN**.
- **Iran** (flux de la phase 10) :
  - **154x838hjd6 : 1 paire stricte** (FAE puis 2e achat), 05:59:05 puis 06:07:25, à 0,23 puis 0,257, juste avant les frappes (environ 06:15, APPROXIMATE). Entrée FLUX à T2 + 2 s, 500 $, frais supposés nuls : net −7 % à 60 s, +27 % à 300 s, +78 % à 600 s ;
  - **Planktonbets :** une paire à 2 s d'écart (04:48:21 puis 04:48:23), net −9 %.
- **Les autres comptes :** aucun FAE suivi d'un 2e achat dans l'heure.

**Lecture :** des cas isolés. Ils ne prouvent rien sur le signal et ne disent rien de l'intention des comptes.

## 13. Maduro (§14)

Flux `EVT_MADURO` (début : 02/01 12:04 UTC).

**0x31a56e9e :**
- premier achat FAE le 02/01 à 16:49 (6 000 $ à 0,066), **sans 2e achat** dans l'heure ;
- puis trois achats le 03/01 : 01:38, 02:15 et 02:58. Ces paires sont **descriptives** (le premier achat n'est pas un FAE) ;
- aux deux 2e achats (02:15:05 et 02:58:25), **aucun achat d'un autre wallet** dans les 60 s : entrée non observable, carnet **UNKNOWN / NO BOOK DATA** ;
- le prix des autres reste vers 0,08 (+0,0 à +2 points à 300 s).

**0x6baf05d1 :** un seul achat (03:42:01), pas de 2e achat.

Aucun de ces wallets n'était SIG_HIST au moment des achats (phase 13). Aucune attribution à une information privée.

## 14. Iran (§14)

Flux `EVT_IRAN`. Wallet 0x4dfd481c, non qualifié SIG_HIST (score 0,022 < 0,222).

| Paire (descriptive) | T2 | Prix du wallet | Ask à T_OBS | Net 500 $ à 300 s (frais = 0) |
|---|---|---|---|---|
| 05:15:53 puis 05:19:51 | +238 s | 0,18 | 0,17 (bid 0,15) | +8,1 % (+18,8 % à 600 s) |
| 05:19:51 puis 05:21:55 | +124 s | 0,20 | 0,22 | −13,8 % |
| 05:21:55 puis 05:33:47 | +712 s | 0,22 | 0,20 | −0,1 % |
| 06:33:49 puis 06:33:59, et suivants | 10 à 94 s | 0,70 à 0,80 | 0,69 à 0,81 | +11 à +30 % |

**Repères publics :**
- début de l'anomalie : 05:15 (référence glissante de 12 h) ou 06:10 (référence veille), les deux définitions conservées ;
- premier trade ≥ 0,5 : 06:12 ;
- frappes : environ 06:15 (APPROXIMATE) ;
- annonce israélienne : 06:23 (VERIFIED).

Les paires de 06:33 viennent après l'annonce publique : elles suivent la nouvelle, elles ne la précèdent pas. Résultats mitigés, et wallet hors signal : c'est une illustration, pas une preuve.

## 15. Limites

1. **Pas de carnet historique.**
   - L'entrée et la sortie sont lues sur les niveaux réellement consommés par d'autres. FLUX peut compter des niveaux posés après T_OBS.
   - Une entrée et une sortie ne sont mesurables que si d'autres wallets traitent ; c'est ce qui biaise l'échantillon vers les marchés actifs (§3).
2. **Horizons courts (1 à 30 s) non mesurables en historique :** la sortie réelle a lieu 3 à 4 minutes plus tard.
3. **T_wallet historique supposé** (2 s), et non mesuré. Les résultats ne varient pas de 0 à 10 s, donc cette hypothèse ne pèse pas.
4. **Frais :** coefficient du reçu du 1er achat (même wallet, même marché, moins d'une heure avant) ; 0,02 si le reçu est absent. TRAIN est sans frais mesurés.
5. **Direct :** 2 alertes depuis le 01/10 08:51, aucun 2e achat (une fenêtre encore ouverte au moment du rapport).
6. **Écart entre phases** (hors périmètre, non corrigé) :
   - le trade de 0x7c3db723 du 01/10 vers 10:29, sur « Oklahoma data center moratorium », est une alerte SIG_HIST pour le processus papier de la phase 13 (p_before 0,66) ;
   - pour le listener de la phase 11, ce même trade est FOLLOW, avec un marché vide et p_before 0,95 ;
   - le journal de la phase 14 lit les deux sources et note l'origine de chaque alerte.
7. **Tests multiples :** un seul cas principal par split. Les autres cases (latences, tailles, horizons, estimateurs) sont des lectures secondaires.

## 16. Conclusion

**B. SIGNAL PRÉDICTIF MAIS NON EXÉCUTABLE.**

| Condition | État |
|---|---|
| LEAD60_2 supérieur aux contrôles en VALID et en TEST (IC hors 0) | oui |
| Avantage présent sur prix stable (règle pré-enregistrée : signe) | oui, mais IC touchant ou incluant 0 |
| ≥ 30 cas mesurables, 10 marchés, 10 wallets par split | oui (74 et 62) |
| Net > 0 avec IC hors 0 en VALID et en TEST | **non** (+1,3 % IC −2,4 à +5,1 ; −0,7 % IC −7,7 à +7,1) |
| Net médian > 0 | **non** (0,0 % ; −2,4 %) |
| 500 $ entièrement exécutables dans au moins 50 % des cas | **non** (45 % et 20 %) |

**Ce qui détruit le rendement, dans l'ordre :**
1. **Une information déjà consommée.** Le mouvement a lieu entre T1 et T2, et le 2e achat le paie lui-même : il balaie 4 à 5 niveaux, et le prix des autres reste sous son prix pendant la première minute.
2. **La liquidité :** 13 à 33 % des 2e achats seulement absorbent 500 $.
3. **Pas la latence :** l'oracle à 0 s ne fait pas mieux.

**Ce que la phase 14 ne dit pas :**
- elle ne mesure pas les horizons de 1 à 30 s sur un vrai carnet ;
- `p14_paper.py` le fera au fil des 2e achats en direct (`paper_second_buy.csv`).

Le protocole ne sera pas modifié à la lecture de ces cas.

**Prochaine étape :**
- laisser tourner les journaux papier des phases 13 et 14 ;
- relire `paper_second_buy.csv` à 30 2e achats en direct ;
- vérifier séparément l'écart entre phases (limite 6).

## Fichiers

**`phase14/`**
- Protocole et rapport : `PROTOCOLE_P14.md`, `RAPPORT_PHASE14.md`, `README_PHASE14.md`, `phase14_conclusion.json`
- Événements : `phase14_second_buy_events.csv` (662 lignes, SIG et contrôles)
- Exécution : `phase14_execution.csv`, `phase14_controls.csv`, `phase14_capacity.csv`, `phase14_latency.csv`
- Tables descriptives : `phase14_tables.csv` (population, catégories, représentativité, timing, carnet, prix avant et après, segments)
- Cas : `phase14_cas.csv` (8 comptes, Maduro, Iran, nouveaux wallets)
- Direct : `phase14_live_second_buy.csv`, `paper_second_buy.csv`

**Scripts** (liens vers `scripts/`) : `p14_second_buy.py`, `p14_execution.py`, `p14_paper.py`, plus `scripts/p14_run.sh`.
