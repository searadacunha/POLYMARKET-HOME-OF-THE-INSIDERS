# Benchmark

La grille est dans `data/scorecard.json`. Le barème est fixe : 100 points, les mêmes items pour chaque dépôt. `yes` donne le poids, `no` donne zéro, `na` signifie que le fichier n'a pas été lu. Un `na` sort du dénominateur normalisé et ne donne rien au score brut. Un dépôt n'est classé que si au moins 75 % du poids a été lu. La grille ne donne pas de point à un détecteur parce qu'il annonce un profit.

Les items et les preuves sont en anglais dans le JSON, parce que les tests les comparent caractère par caractère. Ce texte est la lecture.

## Scores dont toute la grille a été lue

| Dépôt | Brut | Normalisé | Couverture | Classé |
|---|---:|---:|---:|---|
| Ce dépôt après cette note | 82 | 82 | 1,00 | 1 |
| Ce dépôt à `9c27933`, avant la note | 80 | 80 | 1,00 | 2 |
| `pselamy/polymarket-insider-tracker` | 30 | 40 | 0,75 | 3 |

Le seul item qui change entre avant et après est C4 : la semaine close 2026-W47 est maintenant archivée avec ses journaux. Deux points. Aucun autre item n'a été retourné pour améliorer le rang.

## Lus en partie, non classés

| Dépôt | Brut | Normalisé sur la partie lue | Couverture |
|---|---:|---:|---:|
| `orcalayer/polymarket-insider-score-backtest` | 30 | 47,6 | 0,63 |
| `rwondo/polymarket-insider` | 25 | 37,3 | 0,67 |
| `vsbtc/polymarket-insider-detection` | 20 | 32,8 | 0,61 |
| `suislanchez/polymarket-insider-detector` | 10 | 14,5 | 0,69 |

Le 47,6 d'orcalayer n'est pas comparable au 82. Trente-sept pour cent de son poids n'a pas été lu, surtout parce que la base est privée. Sur l'item S4, le contrôle même marché, même jour et même côté, orcalayer est en avance et ce dépôt est à zéro. Sur S2, les lignes qui permettent de recalculer le test sont publiques ici et ne le sont pas là-bas.

## Où d'autres dépôts sont devant, sur des fichiers réellement ouverts

- Livraison d'alertes : pselamy (Discord et Telegram, lus le 20 novembre) et rwondo (webhook, README et module de score ouverts le 25 novembre). Ce dépôt écrit des fichiers locaux. Item L2 : non.
- Contrôle de cellule : orcalayer. Item S4 : non pour nous.
- Échelle : vsbtc publie un classement de 7 784 portefeuilles. orcalayer annonce 356 594 portefeuilles scorés. Ces nombres viennent du benchmark du 20 novembre et n'ont pas été recomptés. Nous n'avons pas de classement de population.
- Ledger split, merge, rachat : les README de bradca0, DGHW et 1816x décrivent cette clôture. Leur code n'a pas été exécuté. L'item R3 reste non, y compris après l'identité de rachat synthétique, parce que les ledgers de cas du dépôt ne l'appliquent pas.
- Vitesse annoncée : vikramT75 affiche 3,4 millions d'événements par seconde. C'est un banc d'auteur, non rejoué, et le dépôt n'entre pas dans la grille faute de code ouvert.

## Où ce dépôt est devant, sur la même grille

- Journaux `OrderFilled` décodés localement, sorties inter-chaînes testées, protocole figé et résultat négatif recalculable sur des lignes publiques.
- Séparation explicite entre transfert, financement vérifié et identité. W47 en est un exemple chiffré.
- Paquets de preuves hachés et commande hors ligne.

Ces avances ne sont pas une première place sur la détection. Le test figé est négatif. Un dépôt qui alerte en direct sans mesurer le résultat peut avoir une meilleure exploitation et un pire énoncé scientifique. La grille compte les deux, et elle laisse pselamy à 30 points bruts surtout parce que l'issue des alertes n'est pas testée.

## Dépôts ouverts sans entrer dans la grille

README seulement, le 25 novembre : `1816x/Polymarket-PnL-AuditLog`, `NeomarketExplorer/neomarket-clickhouse-indexer`, `zh0006xu/PolyLens`, `warproxxx/poly_data`, `TheOneWhoBurns/polymarket-nonce-guard`, `DGHW/polymarket-trader-miner`, `COEFR/polymarket-insider`, `vikramT75/poly-pnl`, `bradca0/polymarket-pnl`. Les classer sur un README serait reprendre leurs titres. PolyLens annonce un calcul d'identifiant de jeton. Le nôtre est testé sur deux marchés archivés. Le leur n'a pas été exécuté. Les deux peuvent être justes. Seul le nôtre est contrôlé dans ce dépôt.

Code au-delà du README, cette session : `rwondo` (`src/models/anomaly_detector.py`) et `suislanchez` (`lib/detection.js`, `lib/demoData.js`).

Huit dépôts avaient déjà été lus fichier par fichier le 20 novembre. Sept n'ont pas été rouverts. pselamy l'a été au niveau du README. Aucun code concurrent n'a été exécuté, ni le 20 novembre ni ici.

## Catalogue

`data/catalog.json` nomme 56 dépôts : 42 revenus des trois recherches GitHub du 25 novembre (`polymarket insider`, `polymarket wash trading`, `polymarket pnl`) et les noms déjà cités le 20 novembre qui n'étaient pas dans ces pages. Un nom catalogue n'est pas une lecture. Les étoiles n'ont pas servi de critère.
