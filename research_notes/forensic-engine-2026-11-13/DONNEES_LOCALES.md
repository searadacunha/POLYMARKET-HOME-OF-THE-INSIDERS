# Données locales du 13 novembre 2026

## Ce qui a été lu

Le correctif non commité de `investigation/followup-verification-20261104` a été appliqué dans un worktree détaché au commit `17acd3409382201dfb6fc0d43a30d4208952eb02`. Cette branche n'a pas été poussée ni modifiée. Le correctif réécrit le README et reprend des montants déjà publiés sur `main` : les 2 210 et 2 960 USDC de la clé de brace227 vers le propriétaire de `0xa8e64a3c…74a5`, le pari exclusif sur Kane, et le PnL agrégé de 509 993,24 $. Aucun montant nouveau n'y apparaît. Le README du correctif n'est pas repris : le README accepté reste figé.

`research/early-detection-20261113` n'est toujours pas une référence distante. La liste complète des branches, une page, ne la contient pas. Il n'y a donc pas d'analyse de cette branche à réutiliser.

Les deux archives `inca-raw` ont été extraites sous `.local/inca-raw`, ignoré par Git. 38 232 fichiers, non commités. Leurs empreintes sont dans [data/inca_raw_manifest.json](data/inca_raw_manifest.json).

## Bande du marché de juin 2025

La bande `raw/trades` du condition `0x7f398088…abaac`, « Israel military action against Iran by Friday? », donne 7 271 impressions dédupliquées. Le rapport [Inca](../inca-crosscheck-2026-11-06/REPORT.md) a déjà établi les liens d'argent R1 et R2 et l'égalité des profits. Cette passe ne relit pas les 34 160 reçus Polygon. Elle ne revendique donc ni un lien nouveau ni l'absence d'un lien hors de ce rapport.

Le calcul nouveau est la place des cinq comptes dans la population, avant le premier achat Yes au prix d'au moins 0,50. Ce seuil et la ligne de 5 000 USDC sont fixés sans utiliser les noms. Le saut tombe le 2025-06-12 à 23:59:01 UTC, au prix 0,5345. Les cinq premiers achats restent ceux du rapport : 06:15:43, 07:00:01, 08:28:17, 12:19:21 et 18:45:29 UTC. Les notionnels Yes recomptés sont 6 332,74, 33 928,65, 6 125,08, 25 002,03 et 13 045,09 USDC.

| Population avant le saut | Nombre |
|---|---:|
| Achats Yes | 1 661 |
| Portefeuilles | 328 |
| Portefeuilles à 5 000 USDC ou plus | 17 |
| Dont les cinq comptes nommés | 5 |
| Autres portefeuilles au-dessus de la ligne | 12 |
| Taux de base de la ligne | 17/328 = 5,2 % |

Rangs des cinq par notionnel : 1, 2, 6, 12 et 14. Une permutation de 2 000 tirages de cinq portefeuilles ne retrouve pas leur somme de 84 433,59 USDC (queue 0,00050). Cette queue décrit un groupe choisi après la résolution parce qu'il a gagné. Elle n'est pas un taux de faux positifs. Douze autres portefeuilles franchissent la même ligne. La décision est `NOT_DISCRIMINANT`.

## poly_data et Pendulum

Le marché est de juin 2025. `poly_data` v2 commence au contrat d'avril 2026. Pendulum V1 commence le 2026-02-21 à 18:00 UTC. Aucune des deux sources ne couvre ces impressions. Les joindre serait une couverture fausse.

## Séparation

- Démontré ici : les cinq notionnels recoupent le rapport déjà publié, et 328 portefeuilles achètent Yes avant le saut à 0,50.
- Hypothèse : aucune nouvelle. Le contrôle commun et l'information privilégiée restent non démontrés, comme dans le rapport Inca.
- Négatif : la ligne des 5 000 USDC ne distingue pas les cinq comptes. Douze autres la franchissent. Aucune alerte prospective n'en sort.
