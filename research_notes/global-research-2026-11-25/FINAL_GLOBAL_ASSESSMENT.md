# Bilan

Date : 25 novembre 2026. Deux passes sur la même branche. Commit de départ : `9c279334a5dd77ef5fc30c9c2333c9f43aac5a5a`. Verdict prédictif : `NO_EDGE_VALIDATED`, inchangé. Aucun chiffre déjà accepté n'a été réécrit.

## Comptes

| Objet | Nombre |
|---|---:|
| Dépôts catalogués | 56 |
| Dépôts dont un fichier a été ouvert | 13 |
| Dont le source au-delà du README | 6 |
| Code concurrent exécuté | 1 fonction, `luck_pvalue` de vsbtc, sur les 45 lignes figées |
| Publications lues | 10 |
| Dont lecture substantielle | 7 |
| Dont extrait seulement | 3 |
| Trésorerie de marché externe rejouée | 5 comptes Inca, un marché, au cent près |
| Graphes de financement externes reparcourus | 0 |
| Semaine de financement collectée | 1, 2026-W47 |
| Bandes du contrôle de cellule complètes | 45 sur 45, dont 44 avec un autre acheteur |
| Méthodes codées et testées dans la note | 7 |
| Hypothèses réfutées dans le périmètre testé | 6 |
| Chiffres acceptés corrigés | 0 |
| Points de grille avant / après | 80 / 88 |

Les sept méthodes sont l'identifiant de position, l'identité de rachat synthétique, le contrôle de cellule, le ledger d'activité, le rang de Poisson-binomiale avec Benjamini-Hochberg, le recomptage f2020, et la formule de score vsbtc.

## Ce que la seconde passe a mesuré

Le contrôle même marché, même jour UTC et même résultat porte sur les 45 alertes de validation. Les bandes viennent de `data-api.polymarket.com/v2/trades`, sans champs de profil. L'écart moyen entre le prix des autres achats du jour et le prix de l'alerte est d'environ −3,8 cents. L'intervalle bootstrap à 95 % va de −10,2 à +2,6 cents et contient zéro. La version pondérée par la taille contient aussi zéro. Les achats antérieurs à l'alerte sont en moyenne 14 cents moins chers que le prix de l'alerte, intervalle entièrement négatif. C'est le profil d'un prix qui monte avant l'alerte, pas la preuve d'un achat moins cher que le marché.

Les cinq comptes du rapprochement Inca du 6 novembre ont été retéléchargés. Sur le marché « Israel military action against Iran by Friday? », la trésorerie TRADE plus REDEEM retrouve, au cent près, 36 790,37, 85 120,76, 128 735,29, 34 996,81 et 52 329,44 USDC. Aucun SPLIT ni MERGE dans ces cinq historiques complets. Les REWARD ne sont pas dans la somme. Les liens de financement de ce rapport n'ont pas été reparcourus.

La cohorte f2020 se recompte depuis les fichiers engagés : 3 408 bénéficiaires, 158 enregistrements, 153 adresses, 112 EOA, 46 portefeuilles de dépôt, 16 PnL incomplets. L'empreinte SHA-256 de `f2020_recipients.json` égale celle épinglée dans le rapport hebdomadaire.

Le score publié des 7 784 lignes de vsbtc se retrouve par la formule finale de `onchain.py`, écart maximal nul. 65 des 75 lignes de palier High ont `funder_is_service` vrai. Leur code exclut ces financeurs du regroupement, pas du classement.

Sur les 468 portefeuilles de la table d'ignition, Benjamini-Hochberg à 0,05 ne rejette personne. Le plus petit p est 0,001, pour un seul pari.

Le fichier `markets.parquet` du jeu public vgregoire/polymarket-users contient 729 133 lignes. `events.parquet` en contient 316 429. La carte du jeu confirme la période du 11 novembre 2022 au 29 mars 2026 et ne donne pas le nombre de transactions. Le chiffre d'environ 588 millions reste celui du papier. Il n'a pas été recompté.

La page dePortfolio « Polymarket Potential Insider » contient 100 adresses, pas 39. Une seule des cinq adresses Inca de juin 2025 y figure. Aucune intersection avec les bénéficiaires f2020 ni avec les initiateurs de la table d'ignition. Ce n'est pas la liste Inca de juillet 2026.

La page ACDC du 20 août 2026 définit l'Orca, annonce 152 portefeuilles militaires, plus de 8 millions USD, 78 496 paris longshot et 12 355 portefeuilles jusqu'au 5 mai 2026, et ne publie pas d'adresse.

## Classement

1. Ce dépôt après les deux passes, 88.
2. Le même dépôt avant la note, 80.
3. `pselamy/polymarket-insider-tracker`, 30 bruts et 40 normalisés, couverture 0,75.

Les huit points sont W47, le contrôle de cellule, et le ledger réel. orcalayer reste non classé parce que sa base est privée. Son contrôle de cellule n'a pas été exécuté. pselamy, relu dans `scorer.py`, met le seuil d'alerte à 0,80. Le commentaire dit qu'un backtest de coût trouvait un PnL de suiveur négatif sous 0,85. Ce backtest n'a pas été relancé. rwondo reste devant sur la livraison. Le classement de population à l'échelle de vsbtc ou d'orcalayer n'est pas le nôtre.

## Limites

Le client d'une route mélangée. Les listes Inca de juillet et ACDC. Le carnet au moment de l'alerte. Un split réel, absent des cinq historiques. Le décompte des 588 millions de transactions. Les graphes de financement Inca non reparcourus. Un avantage après frais. `NO_EDGE_VALIDATED` ne bouge pas.

## Tests

La note se vérifie hors ligne, y compris le contrôle de cellule, le ledger, f2020, le rang et la grille. La suite de publication du dépôt est relancée sur le commit de cette passe.
