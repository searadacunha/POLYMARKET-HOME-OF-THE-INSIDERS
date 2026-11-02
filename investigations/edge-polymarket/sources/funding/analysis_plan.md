# Plan d'analyse : la structure du financement contient-elle une information prédictive ?

Écrit le 02/10/2026 AVANT tout calcul de performance, de mouvement de prix ou de résultat.
Les tailles de populations (comptes, sans résultat) peuvent être regardées avant le gel.

## Question

L'activité des wallets dont le financement présente un motif donné (service d'échange instantané, rupture compatible XMR,
financement complexe, infrastructure commune) précède-t-elle des mouvements de prix Polymarket plus souvent, plus tôt ou
plus fort qu'une population de contrôle, hors échantillon ? Aucun wallet n'est qualifié d'initié ni de blanchisseur :
ces mots ne désignent que des hypothèses.

## Données

- Trades : univers p8 de l'enquête Maduro/Iran (2 097 marchés non crypto, volume ≥ 250 k$, clos du 01/10/2025 au
  15/09/2026), trades preneurs ≥ 100 $ (data-api), lecture seule. Découpage par date de fin de marché, fixé par la
  phase 8 : TRAIN avant 03/2026, VALID 03 à 05/2026, TEST 06 à 09/2026.
- Échantillon : `code/col_10_echantillon.py`, tirage uniforme (graine 20261002) de 2 500 wallets parmi les 55 436 qui ont
  au moins 3 trades sur des marchés TRAIN. Critère d'activité seulement. Aucun filtre sur l'activité future.
- Financement : `code/col_20_graphe_financement.py`, Polygon, jetons ERC-20, afflux strictement antérieurs au premier
  trade p8 du wallet, 3 sauts (2 financeurs puis 1), arrêt sur hubs très actifs et contrats non-portefeuilles.
- Étiquettes : `data/etiquettes.json`, chaque adresse avec sa source sur le disque et son niveau de preuve ; noms de
  contrats vérifiés (getsourcecode) en seconde source.

## Populations (fonction du graphe seul, figées avant toute mesure de résultat)

Montant attribué = somme des afflux stables du nœud racine, réparti le long des chemins des financeurs remontés.
Une étiquette compte si elle apparaît à un nœud de profondeur ≤ 3 du graphe du wallet.

| Code | Définition |
|---|---|
| `ECH` | un nœud porte une étiquette `echange_instantane` (ChangeNOW observé, f2020 fortement compatible, n.exchange…) |
| `ECH_CN_OBS` | sous-ensemble de `ECH` : une adresse ChangeNOW à étiquette publique |
| `XMR_COMPAT` | `ECH` ET ≥ 80 % du montant de la racine passe par la branche d'échange instantané ET aucune autre source étiquetée (rampe fiat, hub non nommé, bridge) n'apparaît. Rupture compatible avec une entrée XMR, jamais prouvée |
| `COMPLEXE` | le chemin du plus gros financeur passe par ≥ 2 EOA intermédiaires non hubs avant toute étiquette ou hub, OU un intermédiaire EOA né moins de 7 jours avant son envoi |
| `CLASSIQUE` | ≥ 80 % du montant vient d'une rampe fiat étiquetée (MoonPay, CheckoutPool) ou d'un hub très actif atteint avec au plus 1 EOA intermédiaire, sans `ECH` |
| `BRIDGE` | ≥ 50 % du montant arrive par un bridge (Relay, mint depuis 0x0, contrat dont le nom contient Relay, Bridge, Across, Stargate, LiFi, Socket) |
| `INCONNU` | aucun des cas ci-dessus |
| `GRAPPE` | wallets de l'échantillon qui partagent un même financeur EOA non hub (profondeur 1 ou 2) |

Nature d'un nœud, dans cet ordre : étiquette du disque (`data/etiquettes.json`), étiquette publique d'explorateur
(titre de page PolygonScan/Etherscan/Arbiscan, `code/col_40_etiquettes_publiques.py`, familles par la table de motifs
`FAMILLES_PUB` de `code/feat_10_populations.py`), nom de contrat vérifié, hub très actif, EOA. L'origine hors Polygon
du plus gros dépôt Relay (`code/col_30_origine_relay.py`) ajoute : `ECH` si l'expéditeur d'origine a été financé par
un échange instantané étiqueté ; `COMPLEXE` si l'expéditeur d'origine est un EOA non hub actif depuis moins de 7 jours ;
`CLASSIQUE` si l'expéditeur d'origine est un hub ou étiqueté CEX/rampe fiat. `ECH_CN` = sous-ensemble de `ECH` où
l'entité est ChangeNOW. Ethereum et Arbitrum seulement pour l'amont (BSC, Base, Solana : chaîne notée, amont non suivi).

**Échantillon ciblé (si `ECH` < 30 wallets dans le tirage aléatoire)** : destinataires directs des adresses ChangeNOW à
étiquette publique sur Polygon, présents dans le cadre p8 (≥ 3 trades TRAIN), mêmes règles de graphe et de coupure.
Défini par le financement seul ; comparé au contrôle du tirage aléatoire, et décrit séparément.

Contrôles : B = `CLASSIQUE` (financement conventionnel) ; C = tous les wallets de l'échantillon hors population testée ;
D = baseline marché (trades preneurs des autres wallets, même marché, même tranche de prix, ±6 h).

Liens entre wallets d'une grappe, classés sans score chiffré :
- **observé directement** : le même financeur a envoyé des fonds aux deux wallets (transferts on-chain) ;
- **fortement compatible** : en plus, les deux envois ont lieu à moins de 24 h d'écart avec des montants à un facteur 2 près ;
- **compatible mais ambigu** : le financeur commun a ≥ 50 destinataires avant la coupure (service possible) ;
- **aucune preuve suffisante** : le reste.

## Unité et mesures (après le gel seulement)

Unité : achat preneur (≥ 100 $) d'un wallet de l'échantillon, prix d'entrée p0 entre 0,02 et 0,98.
Chemin de prix du jeton acheté : dernier trade des AUTRES wallets (jeton opposé converti en 1 − p), ce qui retire
l'impact propre du wallet. p_post = premier prix d'un autre wallet après t0 + 60 s (prix capturable par un suiveur).

- Δ_h = p(t0 + h) − p0 et Δ'_h = p(t0 + h) − p_post, h ∈ {1 min, 5 min, 30 min, 1 h, 6 h, 24 h}.
- Mouvement favorable : max sur ]t0, t0 + 24 h] de p − p0 ≥ X, X ∈ {1, 2, 5, 10} points ; délai du premier franchissement.
- Résolution : gain = jeton gagnant ; rendement brut (gain − p0)/p0 ; net avec frais preneur actuels de la catégorie
  (0,07/0,05/0,04/0 × p(1 − p)) et 1 point de glissement.

**Critères principaux** (déclarés) : Δ'_1h et rendement net à la résolution, population contre contrôle C, par split.
Les autres horizons, seuils et délais sont secondaires (descriptifs).

## Décision

Une population porte un signal seulement si l'écart avec C est > 0 avec IC 95 % excluant 0 pour DEUX bootstraps
(groupé par wallet ET groupé par marché, 5 000 tirages chacun ; contrôle positif : `controles/controles_positifs.md`)
en VALID ET en TEST pour au moins un critère principal, après correction de Bonferroni sur le
nombre total de tests principaux inscrits au registre, et s'il reste après stratification par tranche de prix et
catégorie de marché. Sinon : pas de signal, piste abandonnée. ChangeNOW/XMR : abandonné s'il n'ajoute rien à `COMPLEXE`
et `BRIDGE` (comparaison `ECH` contre wallets non `ECH` de même classe de complexité).

## Biais traités

- Sélection : population définie par le seul financement antérieur au premier trade, jamais par le résultat.
- Look-ahead : coupure du graphe au premier trade ; prix futurs seulement côté mesure.
- Survie : pas de condition sur l'activité future.
- Impact propre : chemin de prix sans les trades du wallet ; p_post à t0 + 60 s.
- Dépendance : deux bootstraps (wallet, marché) ; un groupé par wallet seul déclarait le nul « significatif » 2 fois
  sur 5 en contrôle positif (corrigé avant le gel).
- Tests multiples : tout test passe par `code/registre.py`, correction sur le total du registre.

## Puissance

Écrite après le comptage des populations et avant le gel : n wallets et n trades par population et par split, et écart
minimal détectable sur les contrôles positifs.
