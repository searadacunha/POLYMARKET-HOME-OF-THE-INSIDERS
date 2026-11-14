> **Précision du 14 novembre 2026.** Le résultat zéro ignition sur 381 marchés reflète surtout l'insuffisance de la grille historique (souvent 30 minutes) face à la règle exigeant 18 points en six heures ; il ne valide pas une absence générale d'ignitions. La [recherche ultérieure](../../PATTERN_RESEARCH.md) de la PR #71 teste cette classe sur des séries de 10 minutes et conclut `NOT_SUPPORTED` (+3,5 points, p = 0,33). Les deux essais ont des périmètres distincts.

# Avantage de détection

13 novembre 2026. Les seuils de `monitoring/phi_monitor` ne sont pas modifiés. Aucune étiquette d'initié n'existe, donc aucun taux de faux positifs d'accusation n'est calculé.

## Cadre

L'API Gamma a fourni 3 600 marchés fermés, volume entre 5 000 et 50 000, entre 50 000 et 500 000, ou au moins 500 000, sur trois périodes : découverte avant le 1er avril 2026, calibration d'avril à août 2026, validation d'août à novembre 2026. Le tirage est stratifié par période, catégorie (mots du titre) et liquidité, graine 20261113, 12 marchés par case quand la case en contient assez. Le cadre est [data/sampling_frame.jsonl](data/sampling_frame.jsonl). Le tirage est [data/sampling_draw.json](data/sampling_draw.json) : 381 marchés, 203 avec au moins un prix, 178 avec au moins 18 points.

La série de prix est celle des 14 derniers jours avant la date de fin, via `data-api /v2/prices-history`, puis ramenée à une grille de 10 minutes. L'API renvoie souvent un point toutes les 30 minutes. La règle figée exige 18 points dans les six heures de base. Une grille à 30 minutes n'en fournit qu'une douzaine. `poly_data` v2 ne couvre pas les marchés d'avant avril 2026. Pendulum n'a pas été retéléchargé.

## Résultat sur l'échantillon

Ignitions du moniteur figé sur la grille publique : **0 sur 381**, dont 0 sur 144 marchés de découverte, 0 sur 114 de calibration et 0 sur 123 de validation.

Parmi 178 séries assez longues, 4 seulement montrent un passage d'un prix d'au plus 0,20 à un prix supérieur d'au moins 0,30 en six heures. Sur la grille reconstruite par les trades :

| Marché | Grille fine | Moniteur |
|---|---|---|
| Bitcoin à 62 500 USD en juillet | ignition, puis prix déjà au-dessus de 0,90 | pas d'alerte |
| Primaire du Minnesota | pas de trades dans la fenêtre | pas de grille |
| Primaire du Rhode Island | 3 points | pas d'ignition |
| Présidentielle brésilienne | 10 points, bande tronquée | pas d'ignition |

La régression logistique et la forêt d'isolation ne sont pas estimées. Il n'y a aucune alerte du moniteur à comparer, et quatre sauts ne font pas un ajustement hors échantillon. Les règles « gros achat sous 0,25 » et « pic de volume » ne sont pas notées sur ces quatre fenêtres, parce que le moniteur s'arrête avant, sur un prix déjà résolu ou sur une grille incomplète.

## Cas connus

Fenêtres centrées sur l'événement, même règle figée :

| Marché | Points | Plage de prix | Ignition |
|---|---:|---|---|
| Maduro out by January 31, 2026 | 17 | 0,055 à 1 | non |
| US next strike Iran, 28 février 2026 | 17 | 0,031 à 1 | non |
| US next strike Iran, 26 février 2026 | 18 | 0 à 0,042 | non |
| Harry Kane, Ballon d'Or 2026, octobre 2025 | 29 | 0,105 à 1 | non |

Le saut est visible dans la série, mais trop peu de points tombent dans les six heures de base. Le moniteur ne part pas. Sur la bande locale de juin 2025, déjà mesurée, il ne part pas non plus : 18,9 % contre un seuil de 50 %.

## Verdict

Aucun avantage de détection précoce n'est démontré. Sur cette population, le moniteur figé n'alerte pas, ni avant les règles simples, ni mieux qu'elles : la comparaison n'a pas d'alerte à départager. La limite vient de la règle elle-même, qui demande une grille fine et un prix encore sous 0,90, et de la grille publique, qui est plus espacée. Abaisser le nombre de points exigé pour faire apparaître des alertes serait changer le seuil après avoir vu les données. Cela n'a pas été fait.
