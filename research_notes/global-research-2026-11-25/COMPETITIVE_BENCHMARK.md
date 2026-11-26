# Benchmark

La grille est dans `data/scorecard.json`. Le barème est fixe : 100 points, les mêmes items pour chaque dépôt. `yes` donne le poids, `no` donne zéro, `na` signifie que le fichier n'a pas été lu. Un `na` sort du dénominateur normalisé et ne donne rien au score brut. Un dépôt n'est classé que si au moins 75 % du poids a été lu. La grille ne donne pas de point à un détecteur parce qu'il annonce un profit.

Les items et les preuves sont en anglais dans le JSON, parce que les tests les comparent caractère par caractère. Ce texte est la lecture.

## Scores dont toute la grille a été lue

| Dépôt | Brut | Normalisé | Couverture | Classé |
|---|---:|---:|---:|---|
| Ce dépôt après la troisième passe | 90 | 90 | 1,00 | 1 |
| Ce dépôt à `9c27933`, avant la note | 80 | 80 | 1,00 | 2 |
| `pselamy/polymarket-insider-tracker` | 30 | 40 | 0,75 | 3 |

Trois items changent. C4 est la semaine W47. S4 est le contrôle de cellule calculé sur les 45 alertes. R3 est le ledger TRADE et REDEEM sur cinq historiques publics, avec split et merge comptés à zéro. Huit points en tout. Le détail de la seconde passe est dans `FINAL_GLOBAL_ASSESSMENT.md`.

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

## Seconde passe, code ouvert et une fonction exécutée

Le clone superficiel du 25 novembre a servi à lire, pas à être recopié.

- `vsbtc` : `src/enrich_wallets.py` et `src/onchain.py` lus. `luck_pvalue` a été exécuté sur les 45 lignes figées. Le p obtenu est 0,3345912628416913, contre 0,3345912628416912 pour notre queue. L'écart est une unité d'arrondi. La formule finale du score, réécrite ici et appliquée aux 7 784 lignes publiées, retrouve chaque score avec un écart maximal de 0. Les composantes `s_calib`, `s_conc` et `s_fresh` retrouvent les valeurs des 344 lignes dont les champs d'enrichissement sont remplis. 65 des 75 paliers High ont un financeur marqué service. Le message du code dit que ces financeurs sont exclus du regroupement, pas du rang.
- `pselamy` : `detector/scorer.py` lu. Poids 0,40, 0,35 et 0,25. Seuil par défaut 0,80. Le module importe Redis. Il n'a pas été importé ni lancé. Le commentaire d'auteur sur un PnL de suiveur négatif sous 0,85 n'est pas un résultat que nous avons recalculé.
- `PolyLens` : `src/core/ctf_utils.py` lu. Même courbe que notre identifiant. Leur fonction n'a pas tourné, faute de `eth_abi` dans l'environnement. Nos tests restent ceux des deux marchés Gamma.
- `rwondo` : `anomaly_detector.py` lu jusqu'au score. Les tests pytest n'ont pas été lancés : scikit-learn n'est pas installé ici.
- `polymarket-nonce-guard` : `tests/test_offline_logic.py` lu. Non lancé : le module importe web3.

## Catalogue

`data/catalog.json` nomme 56 dépôts : 42 revenus des trois recherches GitHub du 25 novembre (`polymarket insider`, `polymarket wash trading`, `polymarket pnl`) et les noms déjà cités le 20 novembre qui n'étaient pas dans ces pages. Un nom catalogue n'est pas une lecture. Les étoiles n'ont pas servi de critère.
