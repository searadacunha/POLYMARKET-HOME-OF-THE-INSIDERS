# Passe 4. Détecteurs indépendants du moniteur

Les seuils historiques de `phi_monitor` restent une référence. Ils ne décident plus si un marché est étudié. Une série absente n'est pas comptée comme un marché calme.

## Couverture des 381 marchés

Série : quatorze derniers jours avant la date de fin, API publique, grille réelle souvent à 30 minutes. Le seuil de hausse de 0,15 et la règle fixe de 0,05 ont été écrits avant cette mesure. Le quantile 0,90, soit 0,001, est calculé seulement sur les marchés dont la fin est avant le 1er avril 2026. Les 123 marchés d'août à novembre ne servent pas à le choisir. Une période nouvelle, 100 marchés fermés entre le 1er et le 14 novembre 2026, absents du tirage, sert de validation.

| Ensemble | Marchés | 1 h suffisant | 1 h trop espacé | 1 h manquant | 24 h suffisant | 24 h trop espacé | 24 h manquant | 24 h fenêtre inutilisable |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Découverte | 144 | 0 | 61 | 83 | 60 | 0 | 83 | 1 |
| Calibration | 114 | 0 | 55 | 59 | 46 | 6 | 59 | 3 |
| Validation déjà vue | 123 | 52 | 35 | 36 | 82 | 3 | 36 | 2 |
| Validation nouvelle | 100 | 73 | 23 | 4 | 73 | 23 | 4 | 0 |

À une heure, la découverte et la calibration n'ont aucun marché suffisant. Le quantile y est donc estimé sur des variations qu'on ne peut pas étiqueter à une heure.

## Tableau des détecteurs

Cible : hausse d'au moins 0,15 après le signal, sans prix postérieur dans le signal. Les familles de titres qui recoupent une période antérieure sont retirées de la validation nouvelle.

| Détecteur | Période | Horizon | Alertes | Par marché-jour | Précision (IC 95 %) | Rappel (IC 95 %) | Avance médiane |
|---|---|---|---:|---:|---|---|---:|
| Hausse 1 h ≥ 0,001, quantile de découverte | Nouvelle | 1 h | 4417 | 3,29 | 0,27 % (0,16–0,47) | 55 % (35–73) | 1,0 h |
| Aléatoire au même taux | Nouvelle | 1 h | 4422 |  | 0,02 % | 4,5 % |  |
| Hausse 1 h ≥ 0,05, règle fixe | Nouvelle | 1 h | 37 |  | 0 % (0–9,4) | 0 % |  |
| Hausse 1 h ≥ 0,001 | Nouvelle | 24 h | 4417 | 3,29 | 3,6 % (3,1–4,2) | 27 % (24–31) | 11 h |
| Aléatoire au même taux | Nouvelle | 24 h | 4422 |  | 1,2 % | 9,0 % |  |
| Hausse 1 h ≥ 0,05 | Nouvelle | 24 h | 37 |  | 16 % (7,7–31) | 1,0 % (0,5–2,2) |  |

Le quantile bat l'aléatoire parce qu'un petit mouvement positif continue un peu. Il alerte plus de trois fois par marché et par jour, et l'avance médiane à une heure est d'une heure : le mouvement de 0,15 n'est constaté qu'au bout de la fenêtre. Ce n'est pas une alerte précoce exploitable. La règle fixe de 0,05 est plus rare et plus précise à 24 h, et elle rate presque tous les mouvements. Aucune des deux ne domine l'autre sur les deux critères.

Sur la validation déjà vue, non utilisée pour le seuil, la précision à 24 h vaut 5,3 % en crypto, 7,1 % en géopolitique, 0,5 % en autres titres et 14 % en sport. En découverte, la géopolitique est à 1,3 %. L'écart ne se tient pas d'une période à l'autre.

Les détecteurs de volume, de nouvel acheteur, d'accumulation multi-adresses et de concentration ne sont pas mesurés sur ces 381 marchés : les transactions n'ont pas été téléchargées pour eux. C'est une donnée manquante, pas un marché sans anomalie. Vingt marchés actifs ont été listés le 13 novembre 2026 sous `.local/prospective/`, hors de Git. Ils n'ont pas encore d'issue. Aucun résultat n'en est tiré.

## Cas connus

Maduro au 31 janvier 2026, les frappes du 26 et du 28 février 2026, et Kane en octobre 2025 restent des séries de 17 à 29 points. À une heure elles sont trop espacées. Le moniteur figé ne s'y allume pas, comme déjà écrit. Cette passe n'ajoute aucun lien de portefeuille et ne contredit aucun montant publié.

## Verdict

Pas d'avantage prédictif reproductible. La raison est double. La grille publique est trop espacée pour une heure sur les périodes anciennes, donc le seuil appris y est un dixième de point et se déclenche sans cesse dès que la grille devient fine. Et les règles qui restent rares ne rappellent pas les hausses. Un modèle plus lourd n'a pas été ajusté : il n'y a pas assez d'événements propres pour cela.
