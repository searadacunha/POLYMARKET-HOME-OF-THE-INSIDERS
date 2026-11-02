# Phase 9 : protocole pré-enregistré

Rédigé le 30/09/2026 après l'audit (`AUDIT_DONNEES.md`) et **avant tout calcul de mouvement postérieur à T**. Toute déviation sera signalée.

## Données et découpage

- **Trades :** preneurs de 100 $ ou plus de la phase 8, sur 2 097 marchés d'événements. Sport et crypto sont exclus, comme en phase 8.
- **Découpage sur l'heure de l'événement T** (et non sur la fin du marché), pour que les historiques de wallets restent causaux :
  - TRAIN : T avant le 01/03/2026 ;
  - VALID : T du 01/03/2026 au 31/05/2026 ;
  - TEST : T à partir du 01/06/2026.
- **Test « nouveaux marchés » :** marchés dont le premier trade est postérieur au 01/03/2026.

## Prix de référence (direction d = jeton acheté)

- **Série « YES-équivalent » par marché**, construite à partir de tous les trades des deux jetons : p_yes = prix si le jeton est YES, 1 − prix si c'est NO. Dans la direction d, p_d = p_yes ou 1 − p_yes.
- **Achat-équivalent de d** (proxy de l'ask de d) : achat du jeton d au prix x, ou vente du jeton opposé au prix y, soit un prix 1 − y.
- **Vente-équivalente de d** (proxy du bid de d) : vente du jeton d, ou achat du jeton opposé.

## Événements (définis uniquement sur le passé)

| Code | Définition | Instant de détection T |
|---|---|---|
| FAE | achat ≥ 250 $ d'un wallet sans aucun trade dans ce marché dans les 24 h précédentes | le trade |
| ACC | 3e achat du même jeton par le même wallet en 30 min, cumul ≥ 750 $ | le 3e achat (T1 = 1er achat) |
| CONV | 3e wallet distinct achetant le même jeton en 10 min, chacun ≥ 250 $ | le 3e wallet (T1 = 1er wallet) |

## Mouvements et étiquettes

- **Mouvement avant :** Δpre_w = p_d(dernier trade < T) − p_d(dernier trade ≤ T − w), pour w = 10 s, 30 s, 1, 5, 10, 30 et 60 min. Les trades de la même seconde que T sont exclus (ordre inconnu).
- **Mouvement après :** Δpost_h = p_d(dernier trade **d'autres wallets** dans ]T, T + h]) − p_d(dernier trade < T), pour h = 5 s, 10 s, 30 s, 1, 5, 10, 30 et 60 min. S'il n'y a aucun trade, pas de mouvement : l'événement est marqué « sans observation ».
- **Seuil de mouvement significatif :** θ = 3 points. 2 et 5 points servent seulement de sensibilité, en TRAIN.
- **FOLLOW :** Δpre_10m ≥ θ / 2 dans la direction.
- **LEAD60 :** pas FOLLOW, et Δpost_60m ≥ θ.
- **lead_time (événements LEAD60) :** secondes entre T et le premier trade d'un autre wallet où Δ ≥ θ / 2 (début du mouvement).

## Features au temps T

- Taille : log(usd), rang de taille dans le marché, taille relative à la médiane du wallet.
- Achats du wallet sur ce jeton en 30 min ; concentration directionnelle du wallet dans le marché.
- Mouvements avant (Δpre à 1, 10 et 60 min) et activité récente du marché (nombre de trades en 10 min, rapporté au rythme des 7 jours).
- Contexte : prix, heures avant la fin, premier trade dans le marché, nombre de trades antérieurs dans l'univers, catégorie.
- Score historique du wallet.

## Lead score (choisi en TRAIN uniquement, puis figé)

- **Population d'apprentissage :** événements FAE non-FOLLOW de TRAIN, cible LEAD60.
- **4 spécifications comparées** par validation croisée en 5 plis groupés par marché (AUC) :
  - S1 : z-scores à poids égaux de 5 composantes ;
  - S2 : régression logistique ;
  - S3 : gradient boosting (HistGradientBoosting, paramètres par défaut) ;
  - S4 : rang de taille seul.
- La meilleure AUC moyenne est figée dans `frozen_spec.json`.
- **lead_score_raw** = sortie du modèle figé.
- **lead_score_market_adjusted** = rang percentile de lead_score_raw parmi les événements **antérieurs** du même marché (au moins 20, sinon NA).
- **Seuil d'alerte :** 95e percentile de lead_score_raw en TRAIN, figé.

## Score historique du wallet (sans fuite)

- historical_lead_score_at_T = (LEAD + α × p0) / (n + α), avec α = 10 et p0 = taux de base LEAD60 de TRAIN.
- Calculé uniquement sur les événements FAE non-FOLLOW du wallet résolus avant T (T_e + 3 600 s ≤ T).
- **Signal HIST :** score ≥ 99e percentile de TRAIN parmi les wallets ayant au moins 5 événements résolus. Seuil figé.

## Exécution simulée (observateur)

- **Latences :** 1, 5, 10, 30, 60 et 300 s.
- **Tailles :** 100, 500, 1 000, 5 000 et 10 000 $.
- **Entrée :** prix moyen pondéré (VWAP) des achats-équivalents d'**autres** wallets dans [T + L, T + L + 600 s], sur les S premiers dollars. Si ce volume observé n'atteint pas S, l'entrée est « non exécutable ».
- **Sortie à T + 60 min** (10 min en secondaire) :
  - VWAP des ventes-équivalentes dans [T + H, T + H + 600 s] sur la même quantité ;
  - à défaut, dernier prix moins un demi-spread estimé ex ante (paires achat-vente d'autres wallets à moins de 60 s dans les 7 jours précédents ; 1 point par défaut).
- **Frais :** 0,02 × min(p, 1 − p) par action et par côté, avec un scénario sans frais.
- **Rendement net** = (produit − coût − frais) / coût.

## Contrôles

| Code | Contrôle |
|---|---|
| A | achats aléatoires du même split et du même décile de taille |
| B | événements FAE de wallets ordinaires (score historique ≤ médiane) |
| C | même wallet, trades sans le signal |
| D | même marché avant intervention (Δpre_60m) |
| E | horodatages aléatoires dans le même marché, 1 par événement, à au moins 1 h de tout événement |

**Facteur externe (H3) :** effet mesuré séparément dans la strate « activité calme » (activité récente ≤ médiane de TRAIN) et dans la strate « sans mouvement préalable ».

## Classement des wallets (au moins 5 événements FAE non-FOLLOW en TRAIN)

- Test binomial du taux LEAD60 contre p0, puis correction de Benjamini-Hochberg (FDR 10 %) sur TRAIN : on obtient les **candidats**.
- Candidat au taux LEAD60 supérieur à p0 hors échantillon (au moins 3 événements VALID + TEST, binomial unilatéral p < 0,05) : **PERSISTENT_LEAD**. De plus, rendement net de l'observateur (latence 60 s, 500 $) > 0 hors échantillon : **ACTIONABLE_LEAD**. Cause toujours **UNKNOWN_CAUSE**.
- Candidat non persistant : **EARLY_FLOW**.
- Au moins 50 % d'événements FOLLOW : **FOLLOWER**.
- Sinon : **NO_LEAD**.

**Test « nouveaux wallets » :** au plus 2 trades antérieurs dans l'univers, en VALID et TEST. **Test « wallets connus » :** au moins 10 événements résolus.

**Critères de succès :** ceux du §23 de la mission, tous requis.

## Addendum A (30/09/2026, en TRAIN, avant tout accès à VALID et TEST)

**Constat en TRAIN (CV 5 plis groupés par marché) :**
- AUC : S3 0,926, S2 0,855, S4 0,549, S1 0,439.
- Importance par permutation dominée par le prix avant l'entrée (0,28). Un modèle de contexte seul (prix, mouvements avant, activité, temps restant, catégorie) atteint 0,920 ; un modèle wallet/trade seul, 0,755.
- La cible LEAD60 est donc largement prévisible par le **contexte de marché**, pas par le wallet.

**Décisions figées avant VALID et TEST :**
1. S3 reste le `lead_score_raw` figé, conformément au protocole. Il est désormais qualifié de **score de contexte**.
2. Ajout de **S5 = `lead_score_wallet`** : HistGradientBoosting entraîné sur TRAIN avec les seules variables wallet/trade (taille log, rang de taille, taille relative au wallet, achats en 30 min, concentration directionnelle, premier trade dans le marché, trades antérieurs, score et taille d'historique). Seuil d'alerte : 95e percentile de TRAIN.
3. **Critère principal d'évaluation : l'uplift contre le contrôle A apparié sur le contexte**, c'est-à-dire FAE non-FOLLOW du même split, même décile de prix (p_before), même tranche de temps restant (< 1 h, 1-6 h, 6-24 h, 1-7 j, > 7 j) et même tranche d'activité (act_10m : 0, 1, 2-4, ≥ 5). Deux mesures : taux LEAD60 et Δpost_60m moyen. IC par bootstrap groupé par marché.
4. **Capturabilité :** rendement net de l'observateur (latence 60 s, 500 $, sortie à 60 min, avec frais), signal contre contrôle apparié.
