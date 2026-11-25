# Bilan

Date : 25 novembre 2026. Commit de départ : `9c279334a5dd77ef5fc30c9c2333c9f43aac5a5a`. Verdict prédictif : `NO_EDGE_VALIDATED`, inchangé.

## Comptes

| Objet | Nombre |
|---|---:|
| Dépôts catalogués | 56 |
| Dépôts dont un fichier a été ouvert dans cette session | 12 |
| Dont le source au-delà du README | 2 |
| Dépôts déjà lus fichier par fichier le 20 novembre | 8 |
| Union des lectures fichier, sans double compte | 19 |
| Code concurrent exécuté | 0 |
| Publications lues | 8 |
| Dont lecture substantielle | 5 |
| Dont extrait seulement | 3 |
| Investigations externes rejouées de bout en bout dans cette session | 0 |
| Test interne reproduit au chiffre près | 1 (T1, n = 45) |
| Semaine de financement manquante collectée | 1 (2026-W47) |
| Méthodes nouvelles codées et testées | 2 (identifiant de position, identité de rachat synthétique) |
| Constats nouveaux à niveau explicite | voir `ORIGINAL_FINDINGS.md` |
| Hypothèses réfutées dans le périmètre testé | 4 |
| Chiffres acceptés corrigés | 0 |
| Points de grille avant | 80 |
| Points de grille après | 82 |

Les quatre réfutations sont l'erreur d'arithmétique supposée sur 48 contre 45 lignes, la présence supposée d'un pair de cellule dans la table, un groupe vérifié de comptes financés pendant W47, et la lecture des 63 873 531,26 USD bruts Tornado comme un financement de marché.

## Classement

Sur les dépôts dont au moins 75 % de la grille a été lue :

1. Ce dépôt après la note, 82.
2. Le même dépôt avant la note, 80.
3. `pselamy/polymarket-insider-tracker`, 30 bruts, 40 normalisés, couverture 0,75.

Le gain de deux points est l'archivage de W47. Il ne récompense pas un détecteur. orcalayer reste devant sur le contrôle de cellule et hors classement parce que sa base privée laisse 37 % de la grille non lue. vsbtc reste devant sur le classement de population. pselamy et rwondo restent devant sur la livraison des alertes. bradca0, DGHW et 1816x décrivent un ledger plus complet. Leurs pourcentages de rapprochement n'ont pas été refaits.

## Où ce dépôt est objectivement plus solide

Reconstruction de cas avec transactions, blocs et séparation entre résultat de trading et flux externes. Résultat négatif figé, recalculé ici sans écart. Sorties inter-chaînes et preuves hachées. Refus de promouvoir un transfert mélangé en identité. Ces points s'appuient sur des fichiers du dépôt, pas sur une comparaison d'étoiles.

## Où il reste moins avancé

Pas de contrôle même cellule. Pas de classement de plusieurs centaines de milliers de portefeuilles. Pas de canal de livraison. Pas de split, merge et conversion dans les ledgers de cas. Pas de rejeu des détecteurs concurrents. Pas d'accès aux graphes privés des analystes de chaîne. La semaine W47 ne ferme aucun de ces écarts, sauf l'absence de cette semaine-là dans la série publique.

## Limites que les données présentes ne lèvent pas

L'identité du client d'une route mélangée. Les listes de portefeuilles qu'Inca et l'ACDC n'ont pas publiées dans les pages obtenues. Le carnet au moment exact d'une alerte ancienne. La part de wash trading sans vérité de terrain. Un avantage exécutable après frais. Un milliard de transactions : aucun papier lu ici n'en a été recompté, et le plus grand chiffre substantiel (588 millions) est une annonce d'auteurs sur un jeu tiers.

## Tests

`python3 -m unittest research_notes/global-research-2026-11-25/tests/test_note.py` couvre Keccak, les deux marchés Gamma, le T1, le rachat synthétique, le snapshot W47 et la grille. `verify.py` refait les contrôles hors ligne. La suite de publication du dépôt est lancée sur le commit de cette note et son résultat est celui du journal de la session, pas une affirmation séparée.

## Décision

Aucun niveau de preuve d'un dossier existant n'est relevé. Aucun portefeuille n'est appelé initié. La seule donnée primaire ajoutée est une semaine close, et elle est surtout vide aux niveaux vérifiés. C'est un résultat utilisable : la série hebdomadaire a maintenant cette semaine, et elle ne montre pas, dans les chemins enregistrés, le schéma que l'on serait tenté d'y chercher.
