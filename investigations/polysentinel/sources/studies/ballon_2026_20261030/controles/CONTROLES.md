# Contrôles synthétiques avant gel — 30 octobre 2026

VÉRIFIÉ : trois exécutions successives de code/ctl_synthetic.py, toutes PASS, neuf fixtures par exécution (27 évaluations consignées, plusieurs assertions par fixture). Les reprises ont ajouté la validation de cohérence des entrées puis le rapprochement exact des labels, avant tout calcul réel.

| Scénario | Graines | Wallets par fixture | Priorités attendues / obtenues |
|---|---|---|---|
| Petits achats (nul) | 11,29,47 | 3 | 0 / 0 |
| Un gros achat (moyen) | 11,29,47 | 1 | 0 / 0 |
| Trois gros achats synchronisés (fort) | 11,29,47 | 3 | 3 / 3 |

Les observations acquises après la décision sont exclues. Doubler des lignes à ID inchangé ne double pas le nominal ; un prix contradictoire sous le même ID lève une erreur. L'audit final rend les performances non estimables quand les historiques contemporains sont vides. Le rapprochement synthétique ignore un candidat de mapping ambigu, accepte le mapping exact et ne le transforme pas en détection.

Source de la dernière exécution : controles/synthetic.json ; historique de toutes les exécutions : registre/tests.jsonl. La table montre la sensibilité des seules fixtures, pas une puissance empirique ni une performance sur les comptes de presse. Aucun seuil réglé sur données réelles.
