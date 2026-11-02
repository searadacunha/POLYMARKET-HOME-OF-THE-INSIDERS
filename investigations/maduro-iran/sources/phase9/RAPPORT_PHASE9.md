# Phase 9 : détection de wallets en avance (WALLET LEAD DETECTION)

Rapport du 30/09/2026. Il s'appuie sur :
- l'audit des données : `AUDIT_DONNEES.md` ;
- le protocole pré-enregistré, avec son addendum A : `PROTOCOLE_P9.md` ;
- les modèles et seuils figés en TRAIN : `frozen_spec.json` et `modeles/`.

## Verdict

**OBSERVABLE → EARLY → REPRODUCTIBLE : oui, pour un seul signal (SIG_HIST). CAPTURABLE : non.**

**Ce qui marche.** Il existe une petite population de wallets dont les entrées précèdent plus souvent que les autres un mouvement de 3 points, et cette propriété se lit sans regarder le futur :
- signal SIG_HIST : historique de lead résolu avant T, seuil figé en TRAIN ;
- LEAD60 de 30 % contre 10 à 13 % pour des achats appariés sur le contexte ;
- écart de +20,7 points en VALID et +17,6 points en TEST ;
- l'écart survit au contrôle du momentum, aux marchés nouveaux et à trois catégories de marchés.

**Pourquoi ce n'est pas exploitable.** L'avance est courte :
- lead-time médian de 78 à 110 s hors échantillon ;
- près de la moitié des mouvements démarrent en moins d'une minute ;
- le mouvement qui reste après l'exécution du wallet est de 1,5 à 2 points.

Un observateur qui copie ce signal perd de l'argent en TEST, même à 1 seconde de latence :
- à 1 s : −2,3 % ;
- à 60 s : −3,7 %, IC [−6,7 ; −1,2] ;
- même sans frais, −1,2 % à 60 s.

Les autres signaux s'éliminent pour trois raisons différentes :
- **FIRST AGGRESSIVE ENTRY (SIG_WALLET)** : c'est surtout l'impact propre du wallet ;
- **ACCUMULATION et CONVERGENCE** : aucun écart face au contrôle ;
- **nouveaux wallets** : impossibles à distinguer du contexte.

**Mécanisme inféré : du copy-trading, pas une information.** Derrière les wallets SIG_HIST, 20,9 % des suiveurs ont déjà été vus derrière le même wallet, contre 2,1 % pour le contrôle. Le mouvement qui suit ressemble donc à de l'imitation.

**Maduro et Iran.** Aucun signal de la phase 9 n'aurait détecté ces deux événements :
- les 8 comptes de l'enquête sont invisibles pour le détecteur, faute d'historique ;
- sur Maduro, le seul wallet SIG_HIST actif avant le repricing a d'abord acheté **NO**, puis YES seulement après les premières explosions publiques.

### Critères de succès du §23 (VALID **et** TEST, jamais TRAIN)

Source : `criteres_23.csv`.

| Critère | SIG_HIST | SIG_WALLET | SIG_CTX | SIG_CONV | SIG_ACC | SIG_NEW |
|---|---|---|---|---|---|---|
| 1 observable avant le mouvement | oui | oui | oui | oui | oui | oui |
| 2 supérieur au contrôle | oui | oui (faible) | oui | non | non | non |
| 3 reproductible | oui | oui | oui | non | non | non |
| 4 hors échantillon | oui | oui | oui | non | non | non |
| 5 plusieurs marchés | oui | oui | oui | non | non | non |
| **6 capturable après frais** | **non** | **non** | **non** | **non** | **non** | **non** |
| 7 robuste (seuils 2 et 5 points) | oui | oui | oui | non | non | non |
| 8 sans utilisation du futur | oui | oui | oui | oui | oui | oui |
| **9 lead-time suffisant pour agir** | **non** | **non** | **non** | **non** | **non** | **non** |

**Aucun signal ne satisfait les 9 critères.**

SIG_CTX n'est pas un signal de wallet. C'est le contexte de marché, à savoir :
- le niveau de prix ;
- les mouvements récents ;
- l'activité ;
- le temps restant.

Il prédit bien LEAD60 (AUC 0,87 à 0,95), mais sa capture est négative.

---

## 1. Données, unité, cible

**Trades.** 2 515 167 trades preneurs ≥ 100 $ sur 2 097 marchés d'événements, fin entre le 01/10/2025 et le 15/09/2026. Mêmes exclusions qu'en phase 8 : sport, crypto, météo et tweets.

**Unité : WALLET × MARKET × EVENT.** 511 071 événements :

| Type | Définition | Nombre |
|---|---|---|
| FAE | achat ≥ 250 $ sans trade du wallet dans le marché depuis 24 h | 450 644 |
| ACC | 3e achat du même jeton en 30 min, cumul ≥ 750 $ | 45 273 |
| CONV | 3e wallet distinct ≥ 250 $ en 10 min | 47 131 |

**Découpage sur l'heure de l'événement :**
- TRAIN avant le 01/03/2026 ;
- VALID du 01/03 au 31/05 ;
- TEST à partir du 01/06.

Population de base, les FAE non-FOLLOW : 246 408 (TRAIN), 155 008 (VALID), 33 641 (TEST).

**Cible LEAD60.**
- Définition : pas de FOLLOW (Δ 10 min avant < 1,5 point dans la direction), puis une hausse ≥ 3 points à 60 min.
- La hausse est mesurée **sur les trades des autres wallets uniquement**.
- Taux de base LEAD60 : 3,3 % (TRAIN), 2,65 % (VALID), 7,4 % (TEST).
- Même mesure sur des horodatages aléatoires (contrôle E) : 0,8 %, 0,6 % et 1,3 %.

**Résolution réelle.**
- Horodatage à la seconde, mais un trade ≥ 100 $ toutes les 602 s en médiane par marché.
- Les horizons de 5 s à 30 s ne sont observés que dans 9 à 16 % des signaux.
- Sans trade, le mouvement est compté comme nul.

## 2. Résultats par signal (hors échantillon)

Uplift = écart de LEAD60 contre les FAE non-FOLLOW **de la même strate de contexte** : décile de prix × tranche de temps restant × tranche d'activité. IC 95 % par bootstrap groupé par marché.

| Signal | Split | n | Wallets | LEAD60 | Contrôle A apparié | Uplift [IC] | Mouvement après l'exécution du wallet, vs A | Net 1 s / 500 $ | Net 60 s / 500 $ [IC] | Net 60 s sans frais |
|---|---|---|---|---|---|---|---|---|---|---|
| SIG_HIST | VALID | 561 | 64 | 30,7 % | 9,9 % | **+20,7** [16,6 ; 24,8] | **+2,0 pt** [1,4 ; 2,6] | +2,8 % | +1,2 % [−3,5 ; +6,3] | +3,5 % |
| SIG_HIST | TEST | 736 | 76 | 30,4 % | 13,2 % | **+17,6** [12,7 ; 22,3] | **+1,5 pt** [1,1 ; 2,0] | −2,3 % | **−3,7 %** [−6,7 ; −1,2] | −1,2 % |
| SIG_WALLET | VALID | 7 652 | 2 047 | 15,4 % | 7,8 % | +7,6 [6,2 ; 8,8] | +0,4 pt [0,2 ; 0,6] | −2,0 % | −2,8 % [−4,5 ; −0,8] | −0,8 % |
| SIG_WALLET | TEST | 6 471 | 1 329 | 17,5 % | 9,4 % | +7,8 [6,3 ; 9,3] | +0,6 pt [0,4 ; 0,7] | −1,7 % | −2,0 % [−3,7 ; −0,4] | −0,1 % |
| SIG_CTX | VALID | 7 352 | 4 004 | 29,3 % | 9,0 % | +18,6 [16,5 ; 20,6] | +0,3 pt [0,1 ; 0,6] | −0,5 % | −1,0 % [−2,9 ; +1,0] | +1,3 % |
| SIG_CTX | TEST | 4 427 | 1 876 | 30,1 % | 10,6 % | +18,9 [16,7 ; 21,3] | +0,7 pt [0,5 ; 0,9] | −3,1 % | −3,7 % [−5,4 ; −2,0] | −1,4 % |
| SIG_CONV | VALID | 15 572 | 11 128 | 3,6 % | 3,2 % | +0,2 [−0,5 ; 0,9] | 0,0 | −2,4 % | −2,5 % | −1,8 % |
| SIG_CONV | TEST | 2 787 | 1 698 | 11,3 % | 10,5 % | +0,5 [−1,7 ; 3,7] | 0,0 | −1,8 % | −2,2 % | −1,1 % |
| SIG_ACC | VALID | 10 024 | 1 767 | 5,6 % | 4,7 % | +0,7 [−0,2 ; 1,5] | 0,0 | −2,4 % | −2,7 % | −1,8 % |
| SIG_ACC | TEST | 4 586 | 1 653 | 7,4 % | 7,6 % | −0,7 [−2,3 ; 0,9] | 0,0 | −1,9 % | −2,0 % | −1,3 % |
| SIG_NEW | VALID | 209 | 203 | 9,6 % | 10,2 % | −0,5 [−4,5 ; 4,2] | −0,2 pt | +4,8 % | +5,3 % [−2,6 ; +14,4] | +7,1 % |
| SIG_NEW | TEST | 75 | 70 | 13,3 % | 13,1 % | +0,4 [−7,7 ; 9,7] | +0,4 pt | −3,0 % | −1,6 % [−12,1 ; +6,5] | 0,0 % |

Table complète : `backtest_results.csv`. Elle contient aussi TRAIN, les contrôles B, C, D et E, la sensibilité aux seuils, les tailles et l'AUC.

**Décomposition du mouvement.** Pour chaque événement, on sépare :
- **l'impact propre** : prix payé − dernier prix avant T ;
- **le mouvement après l'exécution du wallet** : prix à 60 min − prix payé.

Pour SIG_WALLET, l'impact propre (+1,0 à +1,2 point) fait l'essentiel de LEAD60, et le mouvement après l'exécution reste faible (+0,4 à +0,6 point contre le contrôle). Pour SIG_HIST, le mouvement continue après le trade du wallet : +1,5 à +2,0 points contre le contrôle apparié.

**Contrôles supplémentaires pour SIG_HIST (VALID / TEST).** Ils ont été ajoutés après lecture de TEST, sans rien changer aux signaux figés.

| Contrôle | VALID | TEST |
|---|---|---|
| **B** : wallets ordinaires (score ≤ médiane), même strate | +22,6 points | +20,3 points |
| **C** : mêmes wallets, événements sans le signal (score encore sous le seuil ou < 5 événements) | LEAD60 35 %, uplift +24,2 | LEAD60 38 %, uplift +24,4 |
| **D** : mouvement de l'heure précédente (avance vérifiée, pas de momentum) | −0,45 point | −0,11 point |
| **E** : horodatage aléatoire | LEAD60 2,3 % | LEAD60 2,0 % |

Le contrôle C montre que **la propriété appartient au wallet, pas au trade**. Pour D, la moyenne est même légèrement négative : ces wallets achètent plutôt après une petite baisse.

**Sensibilité (SIG_HIST).**
- Seuil de 2 points : +20,9 (VALID) et +20,6 (TEST).
- Seuil de 5 points : +15,7 et +11,8.

**Profil « just after » (SIG_HIST, uplift de Δpost en points contre la strate, `profil_just_after.csv`).**

| Horizon | 5 s | 10 s | 30 s | 1 min | 5 min | 10 min | 60 min |
|---|---|---|---|---|---|---|---|
| VALID | 0,19 | 0,37 | 0,60 | 1,11 | 1,86 | 2,23 | 2,51 |
| TEST | 0,30 | 0,38 | 0,65 | 0,82 | 1,33 | 1,56 | 1,87 |

Environ 44 % de l'écart à 60 min est déjà là après une minute, en VALID comme en TEST.

---

## 3. Réponses Q1 à Q12

### Q1. Existe-t-il des wallets qui entrent systématiquement avant les mouvements ?

**MESURÉ**
- **Signal SIG_HIST.** 103 wallets distincts le déclenchent en VALID + TEST, soit 0,7 % des FAE. Leur LEAD60 est de 30 %, contre 10 à 13 % en contexte apparié.
- **Test wallet par wallet.** 7 955 wallets ont au moins 5 FAE en TRAIN.
  - 81 sont candidats en TRAIN (FDR 10 %, attendu calculé par le modèle de contexte).
  - 16 restent significatifs hors échantillon (p < 0,05) : 41 % des candidats testables, contre 8,6 % des non-candidats.
- **Classement** (`wallet_lead_scores.csv`) :

  | Classe | Wallets |
  |---|---|
  | PERSISTENT_LEAD (UNKNOWN_CAUSE) | 13 |
  | ACTIONABLE_LEAD (UNKNOWN_CAUSE) | 3 |
  | EARLY_FLOW | 65 |
  | FOLLOWER | 2 |
  | NO_LEAD | 7 872 |

**INFÉRÉ**
- Oui, une avance statistique existe et persiste d'une période à l'autre.
- Mais elle n'est pas « systématique » : 70 % des alertes SIG_HIST ne sont pas suivies d'un mouvement de 3 points.
- Le taux de 8,6 % chez les non-candidats (contre 5 % nominal) montre que le test binomial est un peu trop permissif. L'écart candidats / non-candidats (41 % contre 8,6 %) reste net.

**INCONNU**
- La cause, d'où l'étiquette UNKNOWN_CAUSE.
- Rien ici ne distingue une information privée d'une lecture plus rapide de l'information publique.

**PROCHAINE ÉTAPE**
- Aligner les FAE des 16 wallets persistants sur un flux d'actualité horodaté (dépêches, X) pour mesurer T − heure de publication.

### Q2. Combien de secondes ou de minutes d'avance ?

**MESURÉ** : délai entre le trade et le premier trade d'un autre wallet à ≥ 1,5 point (`lead_time.csv`), sur les événements LEAD60 de SIG_HIST.

| Split | P25 | Médiane | P75 | P90 | Part démarrant en moins de 60 s |
|---|---|---|---|---|---|
| TRAIN | 32 s | 156 s | 977 s | 1 952 s | 34 % |
| VALID | 22 s | 110 s | 420 s | 1 315 s | 45 % |
| TEST | 11 s | 78 s | 550 s | 1 837 s | 47 % |

Délai jusqu'au mouvement complet (≥ 3 points), en médiane : 354 s (TRAIN), 182 s (VALID), 168 s (TEST).

**INFÉRÉ**
- L'avance est de l'ordre d'une à deux minutes, et elle raccourcit avec le temps.
- Les trades ≥ 100 $ sont espacés : le vrai début du mouvement peut être antérieur au premier trade observé. Ces lead-times sont donc un **plafond**.

**INCONNU**
- Le lead-time au bloc sur tout l'univers : le data-api ne donne pas l'ordre à l'intérieur d'une seconde.

**PROCHAINE ÉTAPE**
- Récupérer les `OrderFilled` on-chain (bloc et logIndex) pour les 1 297 événements SIG_HIST de VALID et TEST, puis recalculer le lead-time sans le filtre de 100 $.

### Q3. L'avance existe-t-elle après contrôle du momentum ?

**MESURÉ**
- Les FOLLOW sont exclus par construction.
- Le mouvement moyen de l'heure précédente est de −0,1 à −0,7 point.
- Dans la strate « sans mouvement préalable » (|Δ 10 min| < 0,5 point) :
  - VALID +18,3 [13,0 ; 22,9] ;
  - TEST +16,0 [11,0 ; 20,9].
- Dans la strate « activité calme » : +20,4 et +17,9.

**INFÉRÉ**
- Oui, l'avance de SIG_HIST n'est pas du momentum.

**INCONNU**
- Le momentum sur des trades < 100 $, non collectés.

**PROCHAINE ÉTAPE**
- Aucune prioritaire. Ce point est tranché pour les trades ≥ 100 $.

### Q4. Peut-on identifier cette propriété avant de connaître le résultat du trade ?

**MESURÉ**
- historical_lead_score_at_T n'utilise que les événements du wallet résolus avant T (T_e + 3 600 s ≤ T), avec un seuil figé en TRAIN.
- AUC chez les wallets connus (≥ 10 événements résolus) : 0,815 (VALID) et 0,729 (TEST).
- Le détecteur en flux recalcule lui-même ces étiquettes au fil du temps. Il retrouve **100 %** des alertes SIG_HIST du calcul en lot : 561 sur 561 en VALID, 736 sur 736 en TEST (`detector_concordance.csv`).

**INFÉRÉ**
- Oui, sans fuite, dès que le wallet a au moins 5 événements résolus.

**INCONNU**
- Rien de notable sur ce point.

**PROCHAINE ÉTAPE**
- Faire tourner `p9_detector.py` en observation passive sur les marchés ouverts pendant quatre semaines, puis vérifier que les taux se maintiennent sur des données jamais vues.

### Q5. Le phénomène fonctionne-t-il sur de nouveaux marchés ?

**MESURÉ**
- Marchés dont le premier trade est postérieur au 01/03/2026 :
  - VALID +19,1 [14,5 ; 24,2] ;
  - TEST +17,0 [13,1 ; 22,2].
- Uplift positif, IC excluant 0, en VALID et en TEST dans trois catégories :
  - élections / politique : +18,8 et +19,2 ;
  - géopolitique / guerre : +19,8 et +18,9 ;
  - autres : +19,5 et +18,4.
- Macro / Fed : +51,7 (n = 16) puis −11,9 (n = 37), instable.
- Aucun wallet ne dépasse 13 % des événements, aucun marché 6 %.

**INFÉRÉ**
- Oui : la propriété suit le wallet d'un marché à l'autre.

**INCONNU**
- Culture et économie hors macro : effectifs trop faibles.

**PROCHAINE ÉTAPE**
- Aucune prioritaire.

### Q6. Fonctionne-t-il sur de nouveaux wallets ?

**MESURÉ**
- Wallets avec au plus 2 trades antérieurs dans l'univers.
- SIG_NEW : TRAIN +9,9, mais VALID −0,5 [−4,5 ; 4,2] et TEST +0,4 [−7,7 ; 9,7].
- Par quintile du score wallet, pour le 1er, 2e et 3e trade : le LEAD60 observé ne dépasse jamais ce que prédit le contexte seul (`new_wallet_test.csv`, colonne `lead60_moins_attendu` ≤ 0 dans les 15 cases de VALID).
- AUC : 0,662 (VALID) et 0,634 (TEST), portée par la taille et le rang de taille, pas par le wallet.

**INFÉRÉ**
- **Non.** On ne sait pas reconnaître un wallet en avance avant qu'il ait un historique.
- Les comptes du type de notre enquête (premiers gros achats, historique vide) sont précisément ceux que ces méthodes ne peuvent pas voir.

**INCONNU**
- Si des variables hors marché permettraient de les séparer :
  - financement (phase 8 : S_MOONPAY et S_FASTFUND sans effet) ;
  - âge du wallet ;
  - route de dépôt.

**PROCHAINE ÉTAPE**
- Rejouer SIG_NEW en ajoutant les variables de financement de la phase 8, sur l'échantillon déjà financé. Seuil à figer en TRAIN.

### Q7. Peut-on entrer après le wallet avec un rendement net positif ?

**MESURÉ (SIG_HIST, 500 $, sortie à 60 min, frais 2026)**
- Entrée : prix des achats réellement exécutés par d'autres wallets après la latence.
- Sortie : prix des ventes réellement exécutées.

| Split | 1 s | 5 s | 10 s | 30 s | 60 s | 300 s |
|---|---|---|---|---|---|---|
| VALID net | +2,8 % | +3,0 % | +2,6 % | +2,4 % | +1,2 % | −2,9 % |
| TEST net | −2,3 % | −2,6 % | −2,6 % | −3,1 % | −3,7 % | −4,1 % |
| TEST brut, sans frais | +0,3 % | +0,1 % | 0,0 % | −0,6 % | −1,2 % | −1,5 % |

- En VALID, aucun IC n'exclut 0.
- En TEST, à 60 s : IC [−6,7 ; −1,2].
- Le contrôle apparié fait −2,0 % (VALID) et −4,6 % (TEST) : le signal fait mieux que le hasard, mais reste négatif.

**INFÉRÉ**
- **Non.** Le peu qui reste après l'exécution du wallet (1,5 à 2 points, dont environ 44 % dès la première minute) est absorbé par trois coûts :
  - l'écart entre achat et vente ;
  - les frais ;
  - la concurrence d'autres suiveurs.
- La dégradation régulière avec la latence confirme une avance réelle mais consommée très vite.

**INCONNU**
- Le carnet historique n'existe pas (pas de bid / ask / profondeur passés). Le glissement est donc **inféré** depuis les trades.
- L'entrée n'est simulable que dans 26 à 44 % des cas. Ce sont les cas où d'autres achètent derrière, donc plutôt les plus favorables, ce qui rend l'estimation optimiste.

**PROCHAINE ÉTAPE**
- Enregistrer le carnet en direct (`/book` toutes les secondes) sur les marchés où un wallet SIG_HIST est actif, pour mesurer le vrai ask disponible 1 s et 5 s après l'alerte.

### Q8. Quelle taille peut réellement être exécutée ?

**MESURÉ** : part des alertes SIG_HIST où la taille est remplissable dans les 10 min après une latence de 60 s, au prix des trades des autres.

| Taille | TRAIN | VALID | TEST | Net TEST |
|---|---|---|---|---|
| 100 $ | 45 % | 53 % | 40 % | −5,0 % |
| 500 $ | 31 % | 37 % | 26 % | −3,7 % |
| 1 000 $ | 26 % | 32 % | 20 % | −2,7 % |
| 5 000 $ | 16 % | 16 % | 6,7 % | −2,5 % |
| 10 000 $ | 9,9 % | 11 % | 2,9 % | −6,2 % |

**INFÉRÉ**
- Quelques centaines de dollars par alerte, et le résultat est négatif à toutes les tailles en TEST.
- Les tailles utilisées par ces wallets (médiane des 16 persistants : 580 à 8 500 $) ne sont pas reproductibles par un suiveur.

**INCONNU**
- La profondeur réelle du carnet au moment de l'alerte.

**PROCHAINE ÉTAPE**
- Même enregistrement en direct du carnet qu'en Q7.

### Q9. Le signal vient-il du wallet, de la microstructure, ou des deux ?

**MESURÉ (TRAIN, AUC en validation croisée)**

| Modèle | AUC TRAIN (CV) | Hors échantillon |
|---|---|---|
| Contexte seul (prix, mouvements avant, activité, temps restant, catégorie) | 0,920 | 0,94 / 0,86 |
| Variables wallet / trade seules | 0,755 | 0,77 / 0,71 |
| Historique (SIG_HIST) | | contexte apparié : +17,6 à +20,7 points ; contrôle C : +24 |

- Pour les variables wallet / trade, le mouvement après exécution n'est que de +0,4 à +0,6 point contre le contrôle.

**INFÉRÉ**
- La plus grande partie de ce qui « prédit » un mouvement est la **microstructure et le contexte**. Un prix de 0,99 ne peut pas monter de 3 points, et un marché déjà actif bouge plus.
- La seule composante propre au wallet qui résiste est **historique** : certains wallets, pas certains types de trades.

**INCONNU**
- Rien de plus à ce stade.

**PROCHAINE ÉTAPE**
- Aucune prioritaire.

### Q10. Quelle est la fréquence de faux positifs ?

**MESURÉ**
- Part des alertes non suivies d'un mouvement ≥ 3 points à 60 min :

  | Signal | VALID | TEST |
  |---|---|---|
  | SIG_HIST | 69 % | 70 % |
  | SIG_WALLET | 85 % | 83 % |
  | SIG_CTX | 71 % | 70 % |
  | SIG_CONV | 96 % | 89 % |
  | SIG_ACC | 94 % | 93 % |

- Contrôle apparié : 87 à 90 % pour SIG_HIST.
- En copie simulée (500 $, 60 s), la part de trades nets positifs de SIG_HIST est de 35 % en VALID et 29 % en TEST, contre 20 % et 19 % pour le contrôle (`execution_simulation.csv`, colonne `part_net_positif`).

**INFÉRÉ**
- Environ 7 alertes SIG_HIST sur 10 sont fausses. Le signal est une inclinaison, pas une détection.

**INCONNU**
- Rien de notable sur ce point.

**PROCHAINE ÉTAPE**
- Aucune prioritaire.

### Q11. Quel est le lead-time médian réellement disponible ?

**MESURÉ**
- 78 s (TEST) et 110 s (VALID) entre le trade du wallet et le début observé du mouvement.
- 45 à 47 % des mouvements démarrent en moins de 60 s.
- L'uplift de prix à 5 s est déjà de +0,2 à +0,3 point.

**INFÉRÉ**
- Pour un humain, rien : il faudrait réagir en quelques secondes.
- Pour un robot, l'avance brute existe à 1 s en VALID, mais elle ne survit pas en TEST après coûts.
- Ces lead-times sont un plafond (voir Q2).

**INCONNU**
- La latence d'un robot concurrent au bloc.

**PROCHAINE ÉTAPE**
- Même enregistrement en direct du carnet qu'en Q7.

### Q12. Les 8 comptes de notre enquête présentent-ils une signature particulière ?

**MESURÉ** (`population_A_signature.csv`, `etude_cas_acheteurs_avant_repricing.csv`)
- 5 des 8 comptes apparaissent dans l'univers de la phase 9 (≥ 250 $) : 12 événements FAE au total.
- Aucun n'a jamais eu 5 événements résolus : score historique maximal 0,033, c'est-à-dire le taux a priori.
- Aucun signal de la phase 9 ne se déclenche sur eux.
- LEAD60 :

  | Compte | LEAD60 |
  |---|---|
  | Chiwawas | 1 sur 4 (03/01 05:35:41, +21 points après, dont +19,6 après son propre prix) |
  | Mrs.Joker | 1 sur 2 |
  | chileno777, 154x838hjd6, Planktonbets | 0 |

- Aucun n'est dans le classement des wallets : moins de 5 FAE en TRAIN.

**INFÉRÉ**
- Leur signature de marché est celle d'un **wallet neuf qui fait une grosse première entrée**, exactement la zone où le détecteur est aveugle (Q6).
- Ce qui les distinguait dans les phases 2 à 7 était hors marché : financement et graphe de transferts, pas le flux d'ordres.

**INCONNU**
- Si des comptes similaires existent ailleurs : ils sont par construction indétectables par le flux seul.

**PROCHAINE ÉTAPE**
- Aucune par le flux. La seule piste est la variable de financement de Q6.

---

## 4. Causalité approximative

**H2, mouvement → wallet : écarté pour SIG_HIST.**
- Les FOLLOW sont exclus par construction.
- Le mouvement de l'heure précédente est nul ou négatif (contrôle D).
- L'effet persiste dans la strate sans mouvement préalable.

**H1, wallet → mouvement : partiellement vrai, par deux canaux mesurés.**
- **L'impact propre** : +1,0 à +1,5 point selon le signal, soit un tiers à la moitié des 3 points exigés. C'est l'essentiel de SIG_WALLET.
- **Le copy-trading** :
  - en moyenne par alerte, 20,9 % des acheteurs dans les 10 min après un wallet SIG_HIST ont déjà suivi ce même wallet, contre 2,1 % pour les FAE de wallets établis non signalés ;
  - cela explique qu'une avance « persistante » existe sans information : le wallet est suivi, donc le prix monte après lui.

**H3, facteur externe → wallet ET mouvement : central, non éliminé.**
- Le contexte seul prédit LEAD60 avec une AUC de 0,92.
- Pour SIG_HIST, l'écart survit à l'appariement sur le contexte. Mais sans flux d'actualité horodaté, on ne peut pas exclure que ces wallets réagissent simplement **plus vite à une information publique**.
- Le cas Maduro (section 5) va dans ce sens : le wallet SIG_HIST présent a acheté YES 11 minutes après les premières explosions signalées, et NO avant.

## 5. Fuite d'information ex post : Maduro et Iran

Les heures d'événement ne servent qu'à l'analyse, jamais au signal.

Règle d'« activité inhabituelle », fixée avant lecture des fenêtres : première tranche de 5 minutes dont le volume d'achats agressifs YES-équivalents dépasse le P99 des tranches de la fenêtre de référence (autres jours, même marché).

Sources :
- fills `OrderFilled` on-chain (bloc et logIndex) ;
- série CLOB à la minute de la phase 2 ;
- flux data-api ;
- état du détecteur rejoué causalement.

### Maduro (03/01/2026)

`etude_cas_maduro_iran.csv`, `etude_cas_tranches_5min.csv`.

| Heure UTC | Étape | Niveau |
|---|---|---|
| 03:46 | Ordre de lancement donné (non public à l'époque ; Wikipedia, « 22:46 EST ») | source secondaire |
| 05:35 | Tranche à 5 482 $ d'achats YES, juste sous le P99 (6 261 $). Chiwawas achète 5 188 $ à 0,117 | MESURÉ |
| **05:45** | **Première tranche au-dessus du P99** : 7 310 $, 2 acheteurs, p_yes 0,125. Chiwawas rachète 4 710 $ | MESURÉ |
| 05:51:25 | Seule alerte SIG_HIST du détecteur : wallet `0x090a0d3f` (classé EARLY_FLOW), **achat NO** de 1 252 $ à 0,88 | MESURÉ |
| ~06:00 | Premières explosions signalées à Caracas (« around 02:00 VET », heure approximative) | source secondaire |
| 06:11:07 | `0x090a0d3f` achète YES 4 825 $ à 0,12, puis 2 569 $ à 06:11:41 | MESURÉ |
| 06:15:41 | Un wallet balaie le carnet : 22 985 $ de YES, de 0,12 à 0,51 (alerte SIG_CTX) | MESURÉ |
| **06:16:11** | **Repricing** (p_yes ≥ 1,5 × 0,10) | MESURÉ |
| 06:45:12 | p_yes ≥ 0,5 | MESURÉ |
| 09:21 | Annonce de la capture par Trump (« 04:21 ET ») | source secondaire |

**Intervalles :**
- activité inhabituelle → explosions signalées : environ 15 à 25 min ;
- activité inhabituelle → repricing : 31 à 41 min ;
- explosions → repricing : environ 16 min ;
- repricing → annonce officielle : 3 h 05.

**Absorption.** Entre 05:00 et 06:11 (fin de la fenêtre on-chain), 22 wallets ont acheté 32 184 $ de YES agressifs. Le prix n'est passé que de 0,10 à 0,12-0,125 : le flux a été absorbé sans repricing.

**Détecteur.**
- 10 alertes dans les 6 h précédant le repricing, dans les deux directions.
- Aucune alerte de wallet sur Chiwawas : 3 événements résolus seulement, score 0,025.
- Le seul wallet SIG_HIST pariait NO avant les explosions.
- Le wallet ACTIONABLE_LEAD `0xbaa2bcb5` n'entre qu'à 06:28 et 06:31, après le repricing.

### Iran (28/02/2026)

| Heure UTC | Étape | Niveau |
|---|---|---|
| 27/02 20:38 | Autorisation des frappes (non publique ; Wikipedia, « 3:38 p.m. EST ») | source secondaire |
| **05:28 → 05:30** | **Dès le début de la fenêtre on-chain**, la tranche de 05:30 dépasse le P99 : 33 975 $, 14 acheteurs, p_yes 0,21. Premier achat > P99 des tailles : 8 500 $ à 0,225 à 05:29:31 | MESURÉ, **censuré à gauche** |
| 05:59 et 06:07 | 154x838hjd6 achète deux fois 4 706 $ à 0,23 et 0,26 | MESURÉ |
| **06:13:22** | **Repricing** (p_yes ≥ 1,5 × 0,195) ; p_yes ≥ 0,5 à 06:14:20 | MESURÉ |
| ~06:15 | Début des frappes (« around 9:45 a.m. IRST », heure approximative) | source secondaire |
| 06:23 | Annonce israélienne (Katz, « preemptive strike ») et sirènes ; entrée du Times of Israel datée 8:23 heure d'Israël | source secondaire |

**Mesures :**
- avant le repricing : 141 wallets, 305 105 $ d'achats YES agressifs ;
- **0 wallet éligible SIG_HIST** ; 17 seulement ont au moins 5 événements résolus ;
- le marché n'est pas dans l'univers de la phase 8, donc le détecteur complet n'a pas pu être rejoué dessus.

**INFÉRÉ**
- Le repricing (06:13) précède l'annonce officielle (06:23) d'environ 10 minutes et le début approximatif des frappes de 2 minutes.
- L'activité élevée dès 05:28 est **confondue avec le dernier jour du marché** (échéance le 28/02). Les fenêtres de référence (26/02 soir, 27/02 après-midi) ne sont pas un jour d'échéance.

**INCONNU**
- Le début réel de l'activité inhabituelle : aucun fill collecté entre le 27/02 17:45 et le 28/02 05:28.
- L'heure des premiers signaux publics à la minute : OSINT, suivi des vols, médias iraniens.

**PROCHAINE ÉTAPE**
- Récupérer les fills Iran du 27/02 17:45 au 28/02 05:28 (Etherscan `getLogs`, même script `fills.py`).
- Pour les deux cas, reconstruire une chronologie publique à la minute à partir de sources horodatées (posts X archivés, dépêches).

## 6. Classement des wallets (§24)

- Pas de liste « smart money » fondée sur le PnL. Le classement repose sur la **précision avant mouvement** : LEAD60 observé contre attendu par le modèle de contexte figé en TRAIN.
- Les 16 wallets persistants sont étiquetés **UNKNOWN_CAUSE**. Aucune identité n'a été recherchée.
- Les 3 ACTIONABLE_LEAD le sont au sens de la règle figée : rendement net moyen > 0 sur au moins 3 trades simulés hors échantillon. Mais cela repose sur 5, 7 et 11 trades (+7,4 %, +5,6 %, +2,3 %), sans IC : **non établi**.
- Les 13 autres persistants ont un rendement de copie négatif.
- Rien ne justifie de passer de PERSISTENT_LEAD à INSIDER.

## 7. Le détecteur (§25)

**Script** : `scripts/p9_detector.py`, un outil de recherche qui ne passe aucun ordre.

**Entrée** : un flux de trades au format data-api `/trades`.

**Sortie** : une alerte par événement signalé, avec :

| Champ | Contenu |
|---|---|
| timestamp, market, wallet, direction | identification de l'événement |
| lead_score | modèle S3 figé, plus son rang ajusté au marché |
| wallet_score | modèle S5, variables du wallet seul |
| wallet_history_score, wallet_history_n | score historique et nombre d'événements résolus |
| market_context_score | probabilité selon le contexte seul |
| convergence_score | nombre de wallets distincts en 10 min / 3 |
| signal_strength | ratio au seuil figé du signal le plus fort |
| estimated_lead_time | médiane de TRAIN, avec P25 et P75 |

**État causal.** Les étiquettes d'historique sont recalculées par le détecteur lui-même, une heure après chaque événement, à partir du flux.

**Concordance avec le calcul en lot** sur les 2,5 millions de trades rejoués en 18 s (`detector_concordance.csv`) :
- événements : 511 070 sur 511 071 ;
- SIG_HIST, SIG_ACC, SIG_CONV, FOLLOW, prix de référence, mouvements avant, historique : **100 %** ;
- SIG_WALLET, SIG_CTX, SIG_NEW : ≥ 99,98 %.

Les petits écarts viennent de l'ordre des trades d'un même wallet dans une même seconde (fills multiples d'un ordre), non défini dans la source.

**Alertes rejouées** sur VALID + TEST : `alertes_detecteur_valid_test.csv.gz`, 52 450 alertes. `alerts.csv` est la table historique du §26 (prix à 5 s, 10 s, 30 s, 1 min, 5 min et 60 min, MFE, MAE, lead-time, rendement net simulé).

**Usages :**

```
python3 scripts/p9_detector.py --verify --prints p9/prints.pkl --events p9/events_final.pkl
python3 scripts/p9_detector.py --replay --prints p9/prints.pkl --since 2026-03-01 --out alertes.csv
python3 scripts/p9_detector.py --jsonl trades.jsonl --markets p8/universe.json --warmup p9/prints.pkl
```

## 8. Écarts au protocole et limites

1. **Addendum A** (en TRAIN, avant VALID et TEST).
   - La cible était dominée par le contexte : S3 est requalifié « score de contexte » et S5 (wallet seul) est ajouté.
   - Le critère principal devient l'uplift contre un contrôle apparié sur le contexte.
   - Le contrôle A du protocole initial (même décile de taille) est remplacé par cet appariement. L'appariement par taille n'a pas été fait.
2. **Contrôles B, C, D et sensibilité aux seuils de 2 et 5 points.** Calculés après lecture de TEST (`p9_consolide.py`). Ce sont des contrôles ajoutés : aucun signal, seuil ou paramètre n'a été modifié.
3. **Sortie partielle de l'exécution simulée.** Le protocole prévoyait « dernier prix moins un demi-spread estimé ex ante ». Le code applique un point fixe (la valeur par défaut du protocole) dans tous les cas. Cela concerne environ la moitié des sorties.
4. **Échantillon d'exécution.** Il est plafonné à 3 000 événements par signal et par split. SIG_HIST et SIG_NEW sont complets.
5. **TEST est plus mince et sa composition diffère de VALID.**
   - 33 641 FAE, contre 155 008 en VALID, car l'univers s'arrête aux marchés fermés avant le 15/09.
   - Le taux de base est différent (7,4 % contre 2,65 %).
6. **Filtre à 100 $.**
   - Les trades plus petits sont invisibles : le prix est plus grossier et la part exécutable est sous-estimée.
   - Les horizons sous la minute sont rarement observés.
7. **Carnet d'ordres historique absent.**
   - Bid, ask, spread et glissement sont inférés depuis les trades, jamais mesurés.
   - Pose et annulation d'ordres : INCONNU.
8. **Heures publiques.** Elles viennent de sources secondaires (Wikipedia, Times of Israel), et deux d'entre elles sont approximatives (« around »).
9. **Champ `p0` de `frozen_spec.json`.** Il est vide (NaN). La valeur utilisée, identique partout, est `train_lead_rate` = 0,03298.
10. **Marché Iran hors univers.** Le marché « US strikes Iran by February 28 » n'est pas dans l'univers de la phase 8 : seul l'état des wallets a pu y être évalué.

## 9. Fichiers

**Rapports et protocole**
- `RAPPORT_PHASE9.md`, `AUDIT_DONNEES.md`, `PROTOCOLE_P9.md`, `frozen_spec.json`
- `modeles/` : modèles figés S3, S5 et contexte, plus la spécification

**Tables demandées (§27)**
- `wallet_lead_scores.csv`, `wallet_market_events.csv`, `lead_time.csv`, `alerts.csv`
- `backtest_results.csv`, `out_of_sample_results.csv`, `execution_simulation.csv`
- `new_wallet_test.csv`, `convergence_events.csv`, `microstructure_features.csv`

**Tables complémentaires**
- `criteres_23.csv`, `auc_hors_echantillon.csv`, `strates_h3_categories.csv`, `profil_just_after.csv`
- `population_A_signature.csv`, `detector_concordance.csv`, `alertes_detecteur_valid_test.csv.gz`
- `etude_cas_maduro_iran.csv`, `etude_cas_acheteurs_avant_repricing.csv`, `etude_cas_tranches_5min.csv`

**Scripts** (dans `scripts/`)
- Pipeline : `p9_features.py`, `p9_outcomes.py`, `p9_history.py`, `p9_train.py`, `p9_backtest.py`, `p9_exec.py`, `p9_extra.py`, `p9_freeze_ctx.py`
- Détecteur : `p9_detector.py`
- Consolidation : `p9_consolide.py`
- Étude de cas : `p9_cas_maduro_iran.py`

**Données brutes.** Elles sont copiées dans `donnees/brut_p8_p9/` : trades data-api par marché, univers et fills on-chain de la phase 2. Les dérivés (pickles, environ 2,5 Go) se régénèrent avec les scripts.

**Sources publiques citées :**
- [Wikipedia, 2026 United States intervention in Venezuela](https://en.wikipedia.org/wiki/2026_United_States_intervention_in_Venezuela)
- [Wikipedia, 2026 Iran war](https://en.wikipedia.org/wiki/2026_Iran_war)
- [Times of Israel, liveblog du 28/02/2026](https://www.timesofisrael.com/liveblog_entry/israel-has-launched-a-preemptive-attack-on-iran-defense-minister-katz-says-sirens-sound-across-israel/)
