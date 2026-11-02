# Phase 8 : protocole pré-enregistré

Rédigé le 30/09/2026, **avant tout calcul de résultat** (prix après l'entrée, résolution).
Toute déviation sera signalée dans le rapport.

## Univers (`scripts/p8_universe.py`)

- **Marchés :** marchés Polymarket fermés, avec une endDate entre le 01/10/2025 et le 15/09/2026 et un volume d'au moins 250 000 $.
- **Exclusions par motif de slug :**
  - sport et e-sport, dont le format « codes d'équipes + date » ;
  - prix et seuils crypto, marchés up/down ;
  - compteurs de tweets et météo.
- **Résultat :** 2 097 marchés.
- **Découpage temporel sur endDate :**
  - TRAIN : avant le 01/03/2026 ;
  - VALID : du 01/03/2026 au 31/05/2026 ;
  - TEST : du 01/06/2026 au 15/09/2026.

## Événements

- **Définition :** trade preneur (data-api `/trades`, côté BUY) d'au moins 100 $ dans un marché de l'univers.
- **Instant T :** horodatage du trade.
- **Features :** uniquement ce qui est observable avant T :
  - la liste des trades d'au moins 100 $ du marché antérieurs à T ;
  - l'historique Polygon du wallet antérieur à T ;
  - la série de prix CLOB jusqu'à T.

## Features (calculées à T)

| Feature | Définition |
|---|---|
| `size_usd` | taille × prix |
| `size_rank_mkt` | rang percentile de `size_usd` parmi les trades antérieurs du marché (≥ 30 trades antérieurs, sinon NA) |
| `first_in_mkt` | aucun trade antérieur du wallet dans ce marché |
| `prior_trades_univ` | nombre de trades antérieurs du wallet dans l'univers |
| `conv_30m` | nombre d'autres wallets ayant acheté le même jeton dans les 30 min précédentes avec une taille ≥ 90e percentile du marché |
| `accum` | au moins 3 achats antérieurs du wallet sur ce même jeton dans les 24 h, aucune vente |
| `price` | prix payé |
| `hours_to_end` | endDate − T |
| `momo_60` | p(T) − p(T − 60 min) du jeton acheté (série CLOB) |
| `wallet_age_h` | T − premier afflux USDC (USDC.e ou natif) non lié au trading sur le proxy Polygon (sous-échantillon) |
| `last_funding_min` | T − dernier afflux USDC non lié au trading avant T (sous-échantillon) |
| `moonpay_funded` | le proxy a reçu des USDC, avant T, d'une adresse de la famille ou d'un wallet étiqueté MoonPay (sous-échantillon) |

## Signaux (seuils fixés ici, sans optimisation)

| Code | Règle |
|---|---|
| S_LARGE | `size_rank_mkt` ≥ 0,99 et `size_usd` ≥ 5 000 |
| S_LONGSHOT_LARGE | `price` ≤ 0,20 et `size_rank_mkt` ≥ 0,95 |
| S_CONV | `conv_30m` ≥ 2 et `size_rank_mkt` ≥ 0,90 |
| S_ACCUM | `accum` vrai |
| S_FIRST_LARGE | `first_in_mkt` et `prior_trades_univ` ≤ 2 et `size_rank_mkt` ≥ 0,95 |
| S_FRESH | `wallet_age_h` ≤ 48 et `prior_trades_univ` ≤ 2 (sous-échantillon financement) |
| S_FASTFUND | `last_funding_min` ≤ 60 (sous-échantillon financement) |
| S_MOONPAY | `moonpay_funded` (sous-échantillon financement) |

## Résultats mesurés (après T, jamais utilisés pour sélectionner)

- **Entrée d'un observateur (capturabilité) :** p_obs = premier point de la série CLOB (pas de 1 min) postérieur à T + 60 s.
- **Rendement net en points de probabilité :** r_h = p(T + h) − p_obs − coût.
  - Coût de base : 1,0 point (écart acheteur-vendeur et glissement) ; sensibilité à 2,0 points.
  - Horizons : 5, 15, 30 et 60 min, 6 h, et résolution (gain 1 ou 0 − p_obs − coût).
- **Rendement non capturable du wallet,** pour contraste : p(T + h) − prix payé.
- **Excursions :** MFE et MAE sur 6 h par rapport à p_obs.
- **Critères principaux :** r_60min et r_résolution, nets à 1 point.

## Comparaisons

- **Baseline 1 :** tous les événements du même split.
- **Baseline 2 (appariée) :** événements du même marché et de la même tranche de prix (0-0,2 / 0,2-0,5 / 0,5-0,8 / 0,8-1).
- **Contrôle momentum :** stratification par tercile de `momo_60`, avec des bornes calculées sur TRAIN.
- **Intervalle de confiance :** IC 95 % par bootstrap groupé par marché (1 000 tirages).

## Critères de décision (§21 de la mission)

Un signal est **CONFIRMÉ** si toutes les conditions suivantes sont réunies :
- l'écart avec la baseline 2 est > 0, avec un IC excluant 0, sur VALID **et** TEST, pour au moins un critère principal ;
- chaque split compte au moins 30 événements, sur au moins 10 marchés et au moins 10 wallets ;
- l'effet persiste dans chaque tercile de momentum (signe positif) ;
- aucun wallet ne représente plus de 20 % des événements.

Les autres classes (prometteur, non capturable, expliqué par le momentum, non reproductible, aucun signal) suivent le §22.

## Comptabilité des tests multiples

- 8 signaux × 6 horizons × 3 splits × 2 coûts = **288 comparaisons**, dont **16 principales par split** (8 signaux × 2 critères).
- Ordres et annulations : non reconstructibles avec les données publiques utilisées. Tout ce qui s'y rapporte (spoofing, etc.) est **INCONNU**.

## Échantillonnage (pour des raisons de coût d'API)

- **Séries de prix :** tous les événements signalés (plafond aléatoire de 1 500 par signal et par split) plus un échantillon aléatoire de baseline de 2 000 événements par split.
- **Financement :** échantillon aléatoire de wallets tirés parmi les auteurs d'événements, plus les wallets de la population A.
- Graine aléatoire fixée à 8.
