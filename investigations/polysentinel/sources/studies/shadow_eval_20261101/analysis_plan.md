# Évaluation exploratoire du moteur shadow : plan du 1er novembre 2026

Écrit et gelé avant tout calcul de `shadow/moteur.py` sur de vraies données. Configuration : `shadow/config.json`, gelée ici. Ce moteur a été conçu en connaissant l'affaire du Ballon d'Or et les défauts mesurés du détecteur gelé : **cette évaluation ne peut pas le valider**. Elle dit s'il tient la charge, s'il reste muet là où il devrait, et s'il retrouve un motif injecté. Seule la période prospective comptera comme évaluation.

## Question

E1. Combien de dossiers par jour, par niveau, sur les mêmes lignes que le scénario de référence du rejeu (S_A) ?
E2. Le niveau de priorité reste-t-il rare sur le strate placebo, les marchés continus (prix, sport), où une information privée sur une annonce discrète est peu plausible ?
E3. Un motif synthétique injecté dans le vrai fond est-il retrouvé, et à partir de quel montant ?
E4. Les familles déclenchent-elles près de leur taux nominal (1 % par construction, moins les conditions ajoutées) ?
E5. Où se placent les événements de la famille Ballon dans la file ? Lecture exploratoire, faite après scellement du rejeu.

## Données et exécution

Lignes de `scenario_lignes(u, 'S_A', F)` du rejeu gelé, visibilité identique, de T_debut à T_fin. Grille de 300 s, cadence prévue du service. Aucun dossier n'est émis avant T_alertes. État SQLite isolé dans le dossier de session, hors production. Métadonnées : celles du rejeu (M1 pour le recensement seul, échéance et fermeture actuelles pour la famille et les témoins), sans liquidité.

Limite propre à cette période : historiques de wallets réduits à T_debut, donc baseline courte, et comparateurs vides les premières heures. Les familles sans comparateur ne comptent pas : elles sont comptées à part.

## Passes

- `propre` : les lignes telles quelles.
- `injection` : mêmes lignes plus 54 motifs synthétiques sur événements fictifs, répartis régulièrement de T_alertes à T_fin, marchés discrets ouverts, prix 0,20.
  - 36 motifs à trois wallets neufs, en 20 minutes, montants de 2 500, 5 000, 10 000, 25 000, 50 000 et 100 000 par wallet, 6 fois chacun.
  - 18 motifs à un seul wallet neuf, mêmes montants, 3 fois chacun.

Le motif à trois wallets est celui que la mission décrit. Il prouve la mécanique sur ce motif-là, pas une sensibilité à de vrais initiés.

## Mesures

Dossiers par jour et par niveau, événements distincts, réobservations, part M1, part continue, taux de chaque famille parmi les paires évaluées, part de paires sans comparateur, ressources. Pour E3 : niveau maximal et délai du premier dossier par motif. Aucune p-value, aucune précision, aucun rappel d'initiés.

## Lectures fixées d'avance

- Charge : au-dessus de 10 dossiers de niveau ≥ 2 par jour sur la période, le moteur reste trop bavard pour un humain, à corriger dans une version suivante. Au niveau 3, le plafond de 3 par jour est appliqué ; le nombre d'événements retrogradés par ce plafond est rapporté.
- Placebo : un niveau 3 est impossible par construction sur les marchés continus. La mesure utile est le taux de niveau 2 continu rapporté au discret, à niveau d'activité différent : descriptif seulement.
- Si ces lectures conduisent à changer la configuration : nouvelle version datée, et le résultat de cette passe reste attaché à la version `shadow-0.1`.

## Plafonds

Les mêmes que le rejeu : `code/guard.py` du rejeu, 400 Mo, +100 Mo de swap, 250 Mo d'écritures, 15 Go libres avant, arrêt sous 14 Go.
