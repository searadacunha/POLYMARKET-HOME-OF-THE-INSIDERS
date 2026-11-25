# Bilan

Date : 25 novembre 2026. Deux passes sur la même branche. Commit de départ : `9c279334a5dd77ef5fc30c9c2333c9f43aac5a5a`. Verdict prédictif : `NO_EDGE_VALIDATED`, inchangé. Aucun chiffre déjà accepté n'a été réécrit.

## Comptes

| Objet | Nombre |
|---|---:|
| Dépôts catalogués | 56 |
| Dépôts dont un fichier a été ouvert | 13 |
| Dont le source au-delà du README | 6 |
| Code concurrent exécuté | `luck_pvalue` de vsbtc sur les 45 lignes ; 8 tests de score de rwondo |
| OrcaLayer et PnL suiveur de pselamy | non exécutables : clé payante absente ; aucun tableau de résultat publié |
| Publications lues | 10 |
| Dont lecture substantielle | 7 |
| Dont extrait seulement | 3 |
| Trésorerie de marché externe rejouée | 5 comptes Inca, un marché, au cent près |
| Graphe Inca relu depuis `flows.csv` | 118 lignes, 5 contreparties partagées |
| Semaine de financement collectée | 1, 2026-W47 |
| Bandes du contrôle de cellule complètes | 45 sur 45, dont 44 avec un autre acheteur |
| Méthodes codées et testées dans la note | 7 |
| Hypothèses réfutées dans le périmètre testé | 6 |
| Chiffres acceptés corrigés | 0 |
| Points de grille avant / après | 80 / 90 |

Les sept méthodes sont l'identifiant de position, l'identité de rachat synthétique, le contrôle de cellule, le ledger d'activité, le rang de Poisson-binomiale avec Benjamini-Hochberg, le recomptage f2020, et la formule de score vsbtc.

## Ce que la seconde passe a mesuré

Le contrôle même marché, même jour UTC et même résultat porte sur les 45 alertes de validation. Les bandes viennent de `data-api.polymarket.com/v2/trades`, sans champs de profil. L'écart moyen entre le prix des autres achats du jour et le prix de l'alerte est d'environ −3,8 cents. L'intervalle bootstrap à 95 % va de −10,2 à +2,6 cents et contient zéro. La version pondérée par la taille contient aussi zéro. Les achats antérieurs à l'alerte sont en moyenne 14 cents moins chers que le prix de l'alerte, intervalle entièrement négatif. C'est le profil d'un prix qui monte avant l'alerte, pas la preuve d'un achat moins cher que le marché.

Les cinq comptes du rapprochement Inca du 6 novembre ont été retéléchargés. Sur le marché « Israel military action against Iran by Friday? », la trésorerie TRADE plus REDEEM retrouve, au cent près, 36 790,37, 85 120,76, 128 735,29, 34 996,81 et 52 329,44 USDC. Ces cinq historiques n'ont ni SPLIT ni MERGE. Un autre compte public, `0x5bab5e3413de4031639ad81ea951275c01460b20`, en a : trois SPLIT et un MERGE, enregistrés dans `data/split_merge_rows.json`. Le ledger les applique au collatéral de la ligne.

La cohorte f2020 se recompte depuis les fichiers engagés : 3 408 bénéficiaires, 158 enregistrements, 153 adresses, 112 EOA, 46 portefeuilles de dépôt, 16 PnL incomplets. L'empreinte SHA-256 de `f2020_recipients.json` égale celle épinglée dans le rapport hebdomadaire.

Le score publié des 7 784 lignes de vsbtc se retrouve par la formule finale de `onchain.py`, écart maximal nul. 65 des 75 lignes de palier High ont `funder_is_service` vrai. Leur code exclut ces financeurs du regroupement, pas du classement.

Sur les 468 portefeuilles de la table d'ignition, Benjamini-Hochberg à 0,05 ne rejette personne. Le plus petit p est 0,001, pour un seul pari.

Le serveur Hugging Face du jeu `vgregoire/polymarket-users`, réponse `partial: false`, donne 588 287 492 transactions, 2 480 104 portefeuilles, 729 133 marchés et 316 429 événements. Les marchés et les événements ont aussi été comptés dans les parquets téléchargés. Les 23 Go de transactions n'ont pas été copiés. Ce décompte est celui des fichiers parquet, pas un nouveau parcours de Polygon.

La page dePortfolio « Polymarket Potential Insider » contient 100 adresses, pas 39. Une seule des cinq adresses Inca de juin 2025 y figure. Aucune intersection avec les bénéficiaires f2020 ni avec les initiateurs de la table d'ignition. Ce n'est pas la liste Inca de juillet 2026.

La page ACDC du 20 août 2026 définit l'Orca, annonce 152 portefeuilles militaires, plus de 8 millions USD, 78 496 paris longshot et 12 355 portefeuilles jusqu'au 5 mai 2026, et ne publie pas d'adresse.

## Classement

1. Ce dépôt après la troisième passe, 90.
2. Le même dépôt avant la note, 80.
3. `pselamy/polymarket-insider-tracker`, 30 bruts et 40 normalisés, couverture 0,75.

Les dix points sont W47, le contrôle de cellule, le ledger réel (y compris un SPLIT et un MERGE observés), et l'exécution de `luck_pvalue` sur les mêmes 45 lignes. orcalayer reste non classé parce que sa base est privée. Son contrôle de cellule n'a pas été exécuté. pselamy, relu dans `scorer.py`, met le seuil d'alerte à 0,80. Le commentaire dit qu'un backtest de coût trouvait un PnL de suiveur négatif sous 0,85. Ce backtest n'a pas été relancé. rwondo reste devant sur la livraison. Le classement de population à l'échelle de vsbtc ou d'orcalayer n'est pas le nôtre.

## Troisième passe

Le fichier `flows.csv` du 6 novembre contient 118 dépôts et retraits des cinq comptes, contreparties non vides. Deux retraits vont à la même adresse Bybit `0x93b7e169…`, pour 42 216,196194 USDC au total du fichier, pas seulement la fenêtre du 13 juin. Confiance : fortement soutenu pour un crédit au même compte d'échange, indéterminé pour une personne unique. Quatre des cinq reçoivent des dépôts de services déjà nommés (`0xf0fc40a6…`, `0x1929347e…`). Trois reçoivent ou envoient vers `0xf70da978…`, la même adresse que vsbtc marque comme financeur de service de 6 409 destinataires. L'adresse est la même : confirmé. Un client unique : réfuté par ce fan-out. Aucune de ces contreparties n'est un bénéficiaire f2020. Le reçu Polygon d'un hash du fichier n'a pas été relu : publicnode a répondu 403, et un autre point d'accès a renvoyé un reçu vide. Le graphe repose donc sur le fichier archivé.

OrcaLayer s'arrête sans `ORCALAYER_API_KEY`. Les 8 tests de score de rwondo passent. Ils entraînent le modèle sur des tirages du test, pas sur nos alertes. Le PnL de suiveur sous 0,85 n'existe dans pselamy que comme une phrase de `scorer.py`. Il n'y a pas de tableau à recalculer.

L'écart de prix du jour est négatif. Aucun signal exécutable ne reste après cet intervalle, et le carnet au moment de l'alerte n'est pas disponible. `NO_EDGE_VALIDATED` ne change pas.

Les listes de 39 et de 152 adresses n'ont pas été trouvées. Les essais sont dans `data/address_search.json`.

## Limites qui restent impossibles avec les données présentes

Les 39 adresses Inca de juillet 2026 et les 152 adresses ACDC : les pages, l'archive du Web et les dépôts publics lus ne les contiennent pas. Le backtest de coût de pselamy : le chiffre n'est pas publié. Le contrôle d'orcalayer sur sa base privée : la clé et les lignes ne sont pas là. Le client derrière f2020 : la route est mélangée. Le carnet historique à la seconde de l'alerte. Une nouvelle marche complète de Polygon pour chaque hop : le reçu demandé n'a pas été relu dans cette session.

## Tests

La note se vérifie hors ligne, y compris le contrôle de cellule, le ledger, f2020, le rang et la grille. La suite de publication du dépôt est relancée sur le commit de cette passe.
