# Patterns testés

Trois hypothèses ont été figées avant de calculer les issues de l'échantillon. Elles ne sont pas devenues des règles parce qu'un score était élevé. Aucune n'a passé la validation.

## Règle de décision

L'heure `2026-10-11T00` est la découverte. L'heure `2026-10-11T01` est la validation. Seule la validation décide. Les seuils ne sont pas estimés sur ces heures.

Une impression entre dans un bras seulement si la taille est d'au moins 50 parts, ou le notionnel prix × taille d'au moins 20, et si une issue existe. L'issue est le milieu du premier carnet ou du premier meilleur achat/vente situé entre 60 et 180 secondes après l'impression, dans le sens du côté envoyé par le venue, d'au moins 0,02. Le carnet utilisé pour le signal est le dernier `book` strictement antérieur. Un carnet postérieur ne change pas le spread. Un milieu situé avant 60 secondes n'est pas l'issue. Les tests unitaires couvrent ces deux interdictions.

| Hypothèse | Signal | Contrôle |
|---|---|---|
| H1, consommation du premier niveau | taille / profondeur ≥ 0,5 et spread ≥ 0,02 | consommation < 0,25 |
| H2, spread large | spread ≥ 0,04 | spread < 0,02 |
| H3, rafale d'impressions | impression précédente du même token à ≤ 2 s | aucun antécédent, ou écart > 30 s |

Le milieu des distributions est exclu des deux bras, pour ne pas classer la frontière après avoir vu les données. Le test est un Fisher unilatéral et une permutation de 2 000 tirages, graine 20261113. Le seuil est 0,05 / 3. Chaque bras doit avoir au moins 8 impressions, sinon la décision est `UNDERPOWERED` et l'hypothèse ne passe pas. Il n'existe pas d'étiquette « initié » dans ces fichiers. Le taux de faux positifs d'une accusation n'est donc pas calculé. Le champ `insider_probability` reste nul.

## Entonnoir, catégories science, économie et earnings

Catégories choisies parce que les fichiers faisaient moins de 5 Mo, pas parce qu'elles ressemblent à Maduro, à l'Iran ou au Ballon d'Or. Ce n'est pas un échantillon aléatoire du venue.

| | Découverte T00 | Validation T01 |
|---|---:|---:|
| Impressions | 163 | 190 |
| Carnet antérieur | 119 | 136 |
| Issue dans la fenêtre | 77 | 74 |
| Taille éligible | 36 | 50 |
| Éligible et étiquetée | 18 | 10 |

La médiane des tailles de l'heure de validation est 17,64 parts. Le seuil de 50 parts, fixé avant, laisse la plupart des impressions dehors. C'est la raison de la faible puissance. Le seuil n'a pas été abaissé après ce constat.

## Résultats de validation

Aucun pattern ne passe. Neuf impressions de validation auraient allumé au moins une hypothèse ; elles sont retenues et aucune alerte n'est émise. Le rejeu est une archive horaire, pas un flux en direct.

| Hypothèse | Signal | Mouvements signal | Contrôle | Mouvements contrôle | Fisher | Permutation | Décision |
|---|---:|---:|---:|---:|---:|---:|---|
| H1 | 7 | 3 | 1 | 0 | 0,625 | 0,624 | UNDERPOWERED |
| H2 | 4 | 1 | 3 | 1 | 0,857 | 0,860 | UNDERPOWERED |
| H3 | 3 | 2 | 7 | 2 | 0,333 | 0,326 | UNDERPOWERED |

Le seuil de Bonferroni est 0,0167. Même si l'on ignorait le minimum de 8, aucune de ces probabilités ne le franchirait. H2 va dans l'autre sens sur ce point (1/4 contre 1/3) mais le bras est trop petit pour en faire un rejet estimé. La décision reste le manque de puissance.

La découverte, non utilisée pour décider, est du même ordre : H1 a 11 signaux dont 4 mouvements contre 2 contrôles sans mouvement ; H3 n'a aucun signal. Elle ne sauve pas l'hypothèse.

## Ce qui n'a pas été trouvé

Pas de groupe de portefeuilles : les impressions n'ont pas d'adresse. Pas de lien entre un changement de carnet et un wallet. Pas de reçu on-chain pour les 353 hashs. Pas de taux de base d'un délit. Les explications ordinaires restent ouvertes : teneur de marché, carnet mince, information déjà publique, impression du venue non confirmée sur la chaîne, hasard.

Les 353 lignes scorées sont dans [data/scored_prints.jsonl](data/scored_prints.jsonl). `verify.py` les recalcule.
