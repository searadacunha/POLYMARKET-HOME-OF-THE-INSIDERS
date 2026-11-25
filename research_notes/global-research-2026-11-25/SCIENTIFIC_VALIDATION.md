# Validation scientifique

## Trois objectifs, tenus séparés

La reconstruction rétrospective, la détection d'un comportement inhabituel et la prévision exploitable avant résolution ne sont pas le même résultat.

Cette session refait la reconstruction d'une semaine de financement et l'arithmétique d'un test déjà négatif. Elle ne produit pas un détecteur nouveau, et elle ne montre pas qu'une alerte bat le prix après coûts. Le verdict du dépôt reste `NO_EDGE_VALIDATED`.

## Le test qui était déjà le bon

T1 compare le taux de gain au prix payé, sous l'hypothèse que chaque ligne gagne avec la probabilité `p_alert`. C'est le bon null pour un contrat qui paie 0 ou 1. Un null à 0,5, comme celui par défaut dans `binomialPValue` de `suislanchez/polymarket-insider-detector` (`lib/detection.js`, ouvert le 25 novembre), répond à une autre question. Une série de contrats à 10 cents qui gagne une fois sur dix est compatible avec le prix et extrême sous un null à 0,5. Ce dépôt ne reprend pas ce null.

L'excès recalculé est d'environ 3,5 points. L'intervalle publié, déjà dans `verdict.json`, traverse zéro. Le p de 0,335 ne passe pas un seuil de 0,05, encore moins le seuil de Bonferroni à 18 comparaisons. Aucune nouvelle comparaison n'a été ajoutée au registre figé. Le contrôle de cellule manquant est déclaré non testable, il n'est pas remplacé par un seuillage choisi après avoir vu les gains.

## Biais que cette note refuse d'introduire

- Regarder les trois alertes de découverte, toutes gagnantes, et les fusionner avec la validation.
- Lire le brut Tornado comme un montant misé.
- Traiter un achat postérieur à un crédit mélangé comme la preuve que le crédit a financé l'achat.
- Appeler « informé » un portefeuille parce qu'il a gagné, ou parce qu'un article lui prête un taux de gain.
- Comparer la note 82 de ce dépôt, dont toute la grille a été lue, à la note normalisée d'un dépôt dont une partie du poids n'a pas été ouverte.

Le papier de Chen Wang et coauteurs, sur le seul contrat Trump-YES, définit des portefeuilles informés à partir d'au moins 20 ordres au marché et du mouvement de prix qui suit. Cette définition voit le futur. Elle ne peut pas servir de détecteur au moment de l'achat. Le dépôt ne l'adopte pas.

## Ce que les grands échantillons disent, et ce qu'ils ne disent pas

Cardozo et Rivero-Wildemauwe (arXiv 2609.12878) annoncent 588 millions de transactions et 2,48 millions de portefeuilles, de novembre 2022 à mars 2026, sur le jeu d'Akey et coauteurs version 1.3. Ce volume n'a pas été recompté ici. Leurs propres tableaux changent de signe selon que l'on pondère les contrats, les dollars ou les événements parents. La queue basse perd de l'argent dans deux agrégations et en gagne dans la troisième. Le sport ne porte pas le biais classique des queues. Un résultat qui change avec l'unité d'agrégation n'est pas une règle à copier.

L'article d'anatomie (arXiv 2603.03136) montre, sur les marchés présidentiels de 2024 seulement, qu'un volume brut d'octobre de 958 millions USD sur Trump devient 391 millions USD de rotation de type échange après séparation des émissions et des rachats. Le dépôt le cite comme un avertissement de mesure, pas comme un chiffre revérifié.

Sirolly, Ma, Kanoria et Sethi annoncent qu'environ 25 % du volume historique et 14 % de 1,26 million de portefeuilles sont compatibles avec du wash trading, avec un pic hebdomadaire proche de 60 % en décembre 2024. Ils écrivent eux-mêmes qu'il n'y a pas de vérité de terrain. Cette session ne réimplémente pas l'algorithme et ne reprend pas ces pourcentages comme des faits locaux.

Aucun de ces textes n'est une étude de plus d'un milliard de transactions recomptées ici. L'annonce « 1,1 milliard » associée ailleurs au dépôt `SII-WANGZJ/Polymarket_data` reste une affirmation d'auteur, non vérifiée, déjà notée dans les écarts du 17 novembre.

## Baselines

Le test T1 est déjà une baseline contre le prix. Il ne bat pas ce prix. Les familles d'exécution du 16 novembre (carnet, taker, déséquilibre) restent négatives ou vides dans `EDGE_VERDICT.md`. Rien dans W47 ne fournit les 20 paires exigées par le protocole de financement pour un test de rendement. Il n'y a donc pas de nouveau backtest, pas de nouveau seuil, et pas de profit théorique à rapporter.

## Contrôle de cellule, après collecte

Les 45 bandes sont complètes. 44 ont un autre acheteur du même résultat ce jour-là. L'écart moyen, prix des autres moins prix de l'alerte, vaut environ −0,038. L'intervalle à 95 %, graine 11, 5 000 tirages, est environ [−0,102, +0,026]. La pondération par la taille donne un intervalle qui contient aussi zéro. On ne retient donc pas l'hypothèse que l'alerte a acheté moins cher que les autres achats du jour.

La version causale, achats déjà passés à l'heure de l'alerte, est négative et son intervalle ne contient pas zéro, environ [−0,191, −0,090]. Le prix de l'alerte est plus haut que la moyenne des achats antérieurs. C'est ce qu'on attend si le prix a monté avant l'alerte, et l'alerte est précisément définie sur un mouvement de prix. Ce chiffre ne dit pas qu'un initié a payé trop cher. Il dit que le prix de l'alerte n'est pas une amélioration par rapport aux achats déjà visibles ce jour-là.

Aucune de ces comparaisons n'était dans le protocole figé. Elles ne créent pas un nouveau test primaire. `NO_EDGE_VALIDATED` reste.

Le rang sur 468 portefeuilles d'ignition, corrigé par Benjamini-Hochberg, ne rejette rien. Le plus petit p, 0,001, vient d'un seul pari. Le publier comme une découverte serait un faux positif de sélection.

## Les 588 millions

Le papier de Cardozo et Rivero-Wildemauwe dit « environ 588 millions » de transactions et 2,48 millions de portefeuilles. La carte du jeu `vgregoire/polymarket-users` confirme la période du 11 novembre 2022 au 29 mars 2026 et décrit des transactions d'utilisateur final reconstruites depuis `OrderFilled`. Elle n'imprime pas le nombre de lignes. Deux parquets ont été comptés ici : 729 133 marchés et 316 429 événements. Le nombre de transactions n'a pas été compté. Le fichier des utilisateurs fait plusieurs centaines de mégaoctets et n'a pas été téléchargé. Un article secondaire donne 588 287 492 et 2 480 104. Ces deux entiers restent les siens.

## Niveau de la semaine W47

La semaine est une observation, pas un test d'hypothèse réussi. Zéro compte vérifié est une absence dans les chemins cherchés. Ce n'est pas la preuve qu'aucun financement de service n'existe hors de ces chemins. Les ponts non enregistrés, les dépôts clients chez un intermédiaire, et l'archive native Ethereum manquante restent ouverts. Le rapport du collecteur le dit déjà. Cette note le répète pour que le zéro ne soit pas lu trop largement.
