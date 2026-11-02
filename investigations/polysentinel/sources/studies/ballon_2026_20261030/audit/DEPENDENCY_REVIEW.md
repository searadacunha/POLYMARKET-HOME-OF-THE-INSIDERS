# Contre-vérification indépendante des dépendances — 30 octobre 2026

Agent neuf dependency_refutation, rôle protocol-auditor, fork sans historique, lecture seule sans résultats ni labels ni exécution de l'étude.

Verdict : PASS pour la correction du MAJEUR dans le parcours hors réseau raw→minimal puis T1/T2. Vérifié : v3 précharge vendor/polysentinel et vérifie chemin/identité du normaliseur ; seuls collect/net/storage_budget sont importés dans ce parcours ; copies collect/net exactement égales aux chaînes sources archivées (comparaison indépendante), SHA concordants au manifeste initial et au gel ; sortie distincte en copie fraîche, égalité SHA du ledger imposée. Aucun seuil, cohorte, fenêtre ou définition changé.

Le contrôle supplémentaire du candidat moyen exige un candidat, score1, priority=false. Il complète le contrôle après résultats, pas rétroactivement avant le gel. Cette chronologie reste un point mineur historique, désormais documenté.

L'auditeur a confirmé137fichiers conformes,4ajouts,9lignes de registre cohérentes et témoin externe intact. Les ajouts techniques sont postérieurs à T1 et annoncés comme tels. Il n'a pas exécuté les reproductions : la preuve d'exécution appartient au coordinateur (REPRODUCTION.md).

Limites : aucun nouveau réseau certifié reproductible ; dépendance httpx externe avec version/empreintes conservées, environnement pas entièrement hermétique. Git absent du projet (dépôt parent vide) ; aucun fichier gelé antérieur modifié.
