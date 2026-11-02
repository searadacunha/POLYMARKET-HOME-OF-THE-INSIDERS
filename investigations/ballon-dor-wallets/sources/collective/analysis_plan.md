# Détection collective du Ballon d'Or 2026 : plan du 1er novembre 2026

Question : plusieurs comptes pouvaient-ils former un signal collectif visible au niveau de l'événement, sans score individuel, sans nom et sans résultat, et ce signal se distingue-t-il de ce qu'on voit ailleurs sur Polymarket ?

Le plan cherche à détruire cette hypothèse. Il est écrit avant tout calcul de taux. Tout changement ensuite est un amendement.

**Ce que l'auteur sait déjà, donc pas d'aveuglement personnel :** le résultat du 26 octobre, le classement des détenteurs de la capture Upside, les adresses de ces détenteurs, le premier signal de Thin le 13 octobre. Les seuils ci-dessous sont choisis en connaissant l'affaire. Ce travail ne valide donc rien : c'est une analyse conditionnelle d'un seul cas, choisi après sa médiatisation.

## Données

Lecture seule, entrées déjà collectées par `pipeline_replay_20261101` et `ballon_2026_20261030`, aucune sortie de S_C, aucun fichier d'alias :

| Fichier | Contenu | Limite |
|---|---|---|
| `ballon_2026_20261030/data/trades_minimal.jsonl.gz` | 46 533 lignes taker, 31 événements | 3 flux tronqués : écartés ici au profit de la ligne suivante |
| `pipeline_replay_20261101/data/family_extra.jsonl.gz` | 91 428 lignes taker, flux 48361, 811116, 811117 | du 24 sept. à T_FIN |
| `pipeline_replay_20261101/data/controls.jsonl.gz`, `sample.json` | 30 262 lignes taker, 13 unités tirées le 1er nov. | tirage fait avant tout score, strates et poids connus |
| `pipeline_replay_20261101/data/global_window.jsonl.gz` | 47 044 lignes taker ≥ 2 500 $, tout Polymarket, 11 au 23 oct. | seulement les grosses lignes |
| `ballon_2026_20261030/data/catalog_refreshed.json` | token, marché, issue | lu après coup : sert à l'affichage et aux univers, jamais au calcul d'un signal |

Nouvelle collecte, une seule : `code/col_01_ages.py` lit le premier événement de chaque wallet qualifié sur `data-api /activity` (`limit=1`, ordre croissant), plafond 2 500 requêtes. Il compte demandés, reçus, vides, en erreur. Les champs `name`, `pseudonym`, `bio`, `profile*` ne sont jamais écrits. Une erreur n'est jamais un âge.

Le flux est **taker seulement**. Un compte qui n'achète que par ordres limites n'apparaît pas. Les achats par `split` n'apparaissent pas. C'est une limite, pas un zéro.

## Univers

- **M (hommes, testé)** : 48361, 811116, 811117, 1189431, 1105185, 1105364, 1105369, 1105379, 1105380, 1105381, 1218178, 1218179, 1225367, 1225368, 1226675, 1226676.
- **W (femmes, témoin de structure)** : 994444, 1105213, 1105212, 1105210, 1105391, 1105390. Même cérémonie, même mécanique. Très petit : un seul wallet y atteint 1 000 $ en 72 h, compté avant ce plan. W n'a donc presque aucune puissance, et on l'écrit.
- **X (témoins tirés)** : 13 unités de `sample.json`, statut `inclus`. Surtout des matchs : comparaison imparfaite, lue par strate.
- **G (recensement)** : tout token du recensement, hors M et W. Le seul dénominateur non choisi.
- Hors analyse : présence à la cérémonie (1200407), prix annexes (1236…).

## Dates (temps simulé)

D1 = 13 oct. 00:00:00 UTC (1791849600). D2 = 13 oct. 18:51:00 UTC (1791917460). T_FIN = 23 oct. 15:17:49 UTC (1792768669). Début commun T0 = 26 sept. 20:00:00 UTC (1790452800). G commence le 11 oct. vers 04:00 : ses fenêtres de 72 h sont plus courtes avant le 14 oct. et c'est écrit.

## Unité et n effectif

Unité : token × tick horaire pour E1, fenêtre glissante pour E2. Les ticks d'un token se chevauchent et les tokens d'un événement sont liés (Mbappé et Yamal sont opposés, top 3 et top 5 sont emboîtés). **n effectif de M : une affaire.** Pas de précision, de rappel, de taux de faux positifs. Un nombre de wallets est un maximum d'opérateurs : un même opérateur peut tenir plusieurs wallets.

## Décisions

Fills d'un même (wallet, token, côté) dans une même transaction : un groupe. Groupes consécutifs à 120 s ou moins : une décision. Les trois comptes (lignes, groupes, décisions) sont rapportés. Montant = taille × prix, hors frais.

## Partie A, prospective : aucun résultat, aucun nom

`ana_10`, `ana_11`, `ana_12`, `ana_20` ne lisent aucun nom, aucune résolution, aucune liste de comptes. Pour un tick t ils n'utilisent que les lignes de `timestamp ≤ t` et l'âge du wallet. L'âge est fixé par une date passée : un wallet qui a un achat avant t a son premier événement avant t.

**E1, cohorte fraîche (test principal).** Pour un token k et un tick t, un wallet compte si ses achats sur k dans ]t − 72 h, t] atteignent 1 000 $ et si l'écart entre son premier achat de cette fenêtre et son premier événement Polymarket est au plus 14 jours. N = nombre de ces wallets, U = leur somme. **Alerte A0 : N ≥ 3 et U ≥ 10 000 $.** Balayage de sensibilité déclaré : N ∈ {2, 3, 5}, U ∈ {5 000, 10 000, 25 000}, âge ∈ {14, 30} jours, fenêtre ∈ {24, 72} h, soit 36 règles.

**E1G, même règle sur le recensement** : un wallet compte s'il a au moins 2 500 $ en lignes du recensement sur k dans la fenêtre. Même N et U. Les tokens de M et W sont lus par leurs seules lignes ≥ 2 500 $, pour rester comparables. Pré-filtre pour économiser des requêtes : seuls les tokens ayant au moins 3 wallets qualifiés, tous âges confondus, reçoivent une lecture d'âge.

**E2, rafales.** Fenêtres de 5, 15, 60 min. Rafale : au moins 3 wallets distincts à 250 $ ou plus chacun sur un token, le premier wallet portant au plus 80 % du montant. Les fenêtres qui se chevauchent sont fusionnées. Rapporté par token-jour actif et par million de dollars achetés, par univers.

**E3, petits puis gros.** Wallet × token avec au moins 3 décisions d'achat, où une décision atteint 1 000 $ et au moins 5 fois la médiane des précédentes. Rapporté pour 100 wallets × token à 1 000 $ ou plus, par univers.

**E4, combinaisons rares.** M, wallets à 500 $ ou plus avant la date. Matrice wallet × token. Pour chaque paire, somme des log(wallets/wallets du token) sur les tokens communs. Nul : tirages Curveball qui gardent les totaux par wallet et par token (200 tirages, graine 20261101). Rapporté : nombre de paires au-dessus du maximum nul à leur nombre de tokens communs. Le partage d'une opinion suffit à produire du chevauchement : un excédent n'est pas une coordination.

**Placebo de E1.** Dates de premier événement mélangées entre les wallets qualifiés d'un même univers, 1 000 tirages, graine 20261101. Statistique : maximum de N sur tous les tokens et ticks jusqu'à D2, puis jusqu'à T_FIN. Mesure si la fraîcheur se concentre sur un token plus que le hasard. Avec 1 000 tirages, on rapporte au mieux p < 3/1000. **Placebo de date :** E1 sur M décalé : relevé à D2 − 7 j.

Résultats de A écrits dans `derived/A_*.json` et empreintes écrites dans `derived/A_seal.json` **avant** toute exécution de la partie B.

## Verdict A, fixé d'avance

À D2, puis à T_FIN :
- `VISIBLE_ET_SPECIFIQUE_CONDITIONNEL` : au moins un token de M en alerte A0 à cette date ou avant, au moins un token de M dans le top 10 de G à la date par (N, puis U) sous E1G, et au plus 20 tokens hors M et W par jour en alerte E1G (charge de revue, seuil arbitraire fixé ici).
- `VISIBLE_NON_SPECIFIQUE` : alerte dans M, mais rang ou charge au-delà.
- `NON_VISIBLE` : aucune alerte dans M à cette date.

Aucun de ces verdicts ne dit « initié », « coordination » ni « aurait été détecté » : PolySentinel n'existait pas et le recensement est un filtre hypothétique.

## Partie B, rétrospective : après le sceau de A

`ana_30` lit les comptes publics, les résolutions et les historiques ultérieurs. Rien de B ne revient dans A.

- **E5, groupe nommé.** G12 = wallets résolus surlignés ou nommés (`data/labels_retro.json`). Comparateurs : les 6 détenteurs non surlignés de la capture ; 2 000 groupes de même taille tirés parmi les wallets à 1 000 $ ou plus sur le même token ; idem sur le token opposé. Statistiques : paires achetant le même token à moins de 5, 15, 60 min ; tokens communs ; part des achats dans les 24 h les plus actives.
- **E6, financement.** Écart entre dernier dépôt et premier achat, par wallet, mêmes comparateurs sur ce que l'historique rend.
- **E7, prix.** Pour les 20 plus grosses décisions d'achat sur M avant T_FIN : prix juste avant, prix moyen payé, prix à +5 min, part du volume du token sur les 24 h précédentes. Aucun carnet daté n'existe : la profondeur reste inconnue.
- **Biais de sélection de E5 :** le groupe a été surligné par la presse parce qu'il détient beaucoup et que ses comptes sont récents. Âge et taille ne sont donc pas des résultats pour ce groupe. Seuls le calendrier et la combinaison peuvent apporter quelque chose, et le fait de partager le même token est imposé par la sélection.

## Tests et correction

Tous les calculs vont au registre. Sur données réelles, il n'y a pas de seuil de significativité revendiqué sauf le placebo E1 et E4, lus avec la correction du registre. Tout ce qui n'est pas ici est exploratoire.

## Contrôles positifs avant le gel

`code/ctl_synth.py` passe par les mêmes fonctions : table nulle, cohorte moyenne, cohorte forte, trois graines. Le nul doit rester muet, le fort doit alerter, et l'injection d'une cohorte dans une vraie unité de X doit être retrouvée.

## Limites écrites d'avance

Taker seulement. Aucun carnet ni liquidité datée. Âge lu aujourd'hui sur l'API. Disponibilité API en temps réel à ces dates non vérifiée. X surtout sportif, W sans puissance. Une seule affaire. Aucune information publique dans le calcul : la comparaison à l'actualité est faite à part et reste incomplète.
