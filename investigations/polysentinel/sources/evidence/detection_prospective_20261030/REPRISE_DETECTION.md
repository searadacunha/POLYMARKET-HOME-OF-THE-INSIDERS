# Reprise : détection PolySentinel

État : R1/R2/R3 terminés, sorties scellées ; phase de reproduction bloquée par le stockage. Ne pas présenter l'étude comme validée ni publier le rapport prévu avant deux reproductions complètes et deux audits de conclusions.

- Étude : studies/detection_20261030 ;47fichiers gelés,1ajout, vérification intacte. Ancienne étude inchangée.
- Plan et seuils figés à12:58:02UTC ; sceau R1/R2 à13:09:48UTC, avant import des labels.
- Entrées officielles : code/ana_replay.py, ana_features.py, ana_labels.py. Ne jamais modifier le code gelé. Les sorties refusent tout écrasement.
- R1/R2/R3 sont dans derived/. Le sceau contient SHA R1/R2. Tous les classements, heures, raisons, inconnus et dénominateurs y sont conservés.
- Registre14lignes :10synthétiques,4réelles,36459769comparaisons comptables ; aucune p-value, une affaire indépendante. Les reproductions identiques ne créent pas de nouvelles hypothèses.
- Audits aveugles terminés : audit/PHASE5.md. Réserve de portée : pas de puissance/FPR mesurée ; nuance du plan sur les graines documentée.
- Deux reproductions officielles lancées en copies fraîches distinctes avec HOME isolé : arrêt lors du callback capacity() quand le disque est tombé sous10,5Go. Logs intacts dans evidence/detection_prospective_20261030/repro_1.log et repro_2.log. Ce ne sont pas des divergences numériques observées : le calcul n'a pas atteint la comparaison finale.
- Aucune suppression supplémentaire ni abaissement de seuil. Le manifeste temporaire de13fixtures n'est plus une proposition valable à0,697Go :12fichiers sont devenus absents sans action de ce coordinateur, un seul reste. Ne pas supprimer d'autres chemins à sa place.
- Surveillance prospective activée, LaunchAgent com.benjamin.polysentinel-prospective, toutes les60s. À consulter : latest_status.json et sidecar.py verify. Refus explicite au plancher disque, reprise automatique quand la ressource revient ; plafond20Mo, aucune purge. OPERATIONAL_REPORT.md expose la première preuve live et ses limites.

## Suite après marge disque stable

1. Recontrôler disque, processus, service live, gel et registre. Viser12Go libres stables ; ne pas contourner le plancher10,5Go de cette étude. Les causes exactes des dernières variations de près de1Go n'ont pas été établies.
2. Relancer deux invocations du reproducteur officiel, chacune avec --fois1 (ou une --fois2), en gardant les deux anciens journaux d'échec. Commande analytique inchangée : python code/ana_replay.py && python code/ana_features.py && python code/ana_labels.py. Sorties : derived/replay.json.gz derived/features.json.gz derived/label_comparison.json. Timeout1800par passe. Employer le Python absolu .venv/bin/python de PolySentinel pour les trois scripts.
3. Les deux passages doivent terminer REPRODUIT, les trois sorties IDENTIQUE, aucune clé ignorée ni modification de l'original. Ne pas écrire dans l'étude pendant la photographie du reproducteur.
4. Le formatter evidence/detection_prospective_20261030/render_report.py est PRÉPARATOIRE, syntaxe analysée seulement. Il refuse de produire results.md tant que les deux logs désignés ne terminent pas REPRODUIT ; remplacer ses chemins de logs par ceux des réussites, sans réécrire les échecs. Il reformate les sorties scellées sans recalculer le détecteur. Son texte n'est pas encore approuvé par des claims-auditor.
5. Après reproduction : produire le rapport, faire deux audits indépendants des conclusions, corriger toute formulation, vérifier gel/registre/état live, ajouter le journal. Aucun travail de dégel ou clôture : réservé à Benjamin.
