# Évaluation du moteur `signal-engine-0.1` : plan du 1er novembre 2026

Écrit et gelé avant tout calcul de ce moteur sur de vraies données, et avant de voir les résultats du rejeu du détecteur gelé. Le code évalué est une copie exacte dans `code/vendor_engine/`.

**Ce que cette évaluation ne peut pas faire.** Le moteur a été conçu en connaissant l'affaire du Ballon d'Or, et après lecture d'un rapport public citant d'autres cas. Il ne peut donc pas être validé sur ces cas. Aucune vérité terrain d'initiés n'existe : ni précision, ni rappel, ni taux de faux positifs. Seule la période prospective, à venir, comptera.

## Questions

E1. Combien de dossiers par jour, par catégorie, sur les mêmes lignes que le scénario de référence du rejeu (S_A) ? Comparaison avec le détecteur gelé après scellement de celui-ci.
E2. Le moteur reste-t-il peu bavard sur les marchés continus (prix), où une annonce discrète n'existe pas ? C'est un placebo imparfait.
E3. Un motif synthétique injecté dans le vrai fond est-il retrouvé, à partir de quel montant, et dans quelle catégorie ?
E4. Le classement tient-il quand 10 % des lignes manquent ?
E5. Où tombent les événements de la famille Ballon et les comptes publics ? Lecture exploratoire, après scellement du rejeu.

## Données

Lignes de `scenario_lignes(u, 'S_A', F)` du rejeu gelé : recensement à 2 500 $, famille Ballon et témoins selon la rotation neutre, de T_debut à T_fin. Grille de 300 s, cadence prévue du service. Aucun dossier avant T_alertes. État SQLite isolé, hors production.

Métadonnées : titres, règles de résolution, tags, échéance et fermeture actuels pour la famille et les témoins ; titre seul pour le recensement seul, donc risque souvent `UNKNOWN`. Pas de liquidité datée : `large_against_liquidity` ne peut pas se déclencher ici.

Limites propres à cette période : historiques courts, comparateurs vides au début, filtre 2 500 $ hors échantillon. Les règles et tags sont des valeurs actuelles, pouvant avoir été modifiées après le trade.

## Passes

- `clean` : les lignes telles quelles.
- `injected` : mêmes lignes plus 54 motifs sur événements fictifs, répartis régulièrement, marché discret ouvert, prix 0,20. 36 motifs à trois wallets neufs en 20 minutes, montants 2 500, 5 000, 10 000, 25 000, 50 000 et 100 000 $ par wallet, 6 fois chacun ; 18 motifs à un wallet neuf, mêmes montants, 3 fois chacun.
- `thinned` : retrait aléatoire de 10 % des lignes, graine fixe 20261101. Mesure : part des événements `CORROBORATED_BEHAVIOR` et `ANOMALOUS` de `clean` encore présents, et catégorie conservée.

## Lectures fixées d'avance

- Charge : au-dessus de 10 nouveaux dossiers `ANOMALOUS` ou plus par jour sur marchés discrets, le moteur reste trop bavard pour un humain ; c'est écrit tel quel et la version suivante devra répondre.
- Placebo : aucune revue n'est possible sur marché continu, par construction. On rapporte seulement le taux de dossiers continus face aux discrets, descriptif.
- Injection : ce motif est celui que la mission décrit, il prouve la mécanique sur ce motif, pas une sensibilité à de vrais initiés.
- Stabilité : moins de 70 % des dossiers `clean` retrouvés dans `thinned` signifierait une dépendance forte aux données manquantes.
- Comparaison au détecteur gelé : nombre de dossiers et d'événements, chevauchement des wallets, rang du wallet de l'affaire dans chaque file. Moins de dossiers n'est pas « meilleur » en soi : sans vérité terrain, on ne peut mesurer que la charge et la stabilité.
- Si ces lectures conduisent à changer le moteur : amendement daté dans le journal scellé, et le résultat reste attaché à la version `signal-engine-0.1`.

## Plafonds

`code/guard.py` du rejeu : 400 Mo, +100 Mo de swap, 250 Mo d'écritures, 15 Go libres avant, arrêt sous 14 Go, arrêt si le battement du collecteur dépasse 180 s.
