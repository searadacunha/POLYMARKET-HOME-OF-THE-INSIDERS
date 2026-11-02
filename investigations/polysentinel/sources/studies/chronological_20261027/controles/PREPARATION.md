# Historique des contrôles avant gel

Trois exécutions préalables ont produit 30 lignes synthétiques, aucune réelle.
Les deux premières comportaient neuf scénarios et sept contrôles adverses. Après
la revue du code, la troisième comporte les mêmes neuf scénarios et onze contrôles
adverses. Les neuf sorties scénario sont inchangées.

Le contenu exact de l'ancienne sortie `controles/adversarial.json` des deux premières
exécutions est conservé dans `controles/adversarial_pre_review.json` : SHA-256
`74a376ed4be6c9d8756226a0d512fe05cb3ffa2ddbc605965f89fb17be8bd940`.
Il correspond aux empreintes `sortie_sha` de ces deux lignes de registre. La sortie
active `adversarial.json` est celle des onze contrôles de la troisième exécution.
Le registre n'a été ni réécrit ni tronqué.

Les extractions `data/extraction.json.gz` (v1) et `data/extraction_v2.json.gz` sont
toutes deux conservées. Seule v2 est utilisée par l'analyse finale. Les corrections
ont été faites avant gel et avant tout calcul réel, en réponse à la revue aveugle.
