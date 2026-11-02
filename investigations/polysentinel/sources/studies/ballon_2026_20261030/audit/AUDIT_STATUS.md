# Audits indépendants — 30 octobre 2026

Pré-gel silent-failure-hunter : PASS code après corrections pagination, compteurs d'erreurs, imports/provenance, validation SHA et entrées historiques vides. Aucune donnée/label lu par cet auditeur.

Premier lancement des auditeurs après calcul : contexte hérité contenant des résultats, aveuglement refusé. Les trois tâches ont été abandonnées et remplacées par trois agents neufs avec fork_turns=none. Aucun rapport issu du premier lancement n'est utilisé pour affirmer un audit aveugle.

Auditeur blind_leakage : PASS dans le périmètre descriptif, respect des interdits. Dates transaction et acquisition distinctes ; métadonnées actuelles exclues ; absence de vérité terrain et limites d'alias explicitement dites.

Auditeur blind_stats : PASS descriptif ; un défaut mineur d'assertion du candidat moyen. Résolu par ctl_medium_presence.py distinct (un candidat score1 sans priorité, PASS), sans modification des anciens fichiers ni seuils. Les contrôles ne mesurent aucune puissance empirique. Effectif externe un cas.

Auditeur blind_protocol : PASS T1/T2 ; défaut majeur pour réexécuter le collecteur via des imports vivants non gelés. Complément additif vendor et run_collector_frozen_v3, sans changement des calculs, puis renormalisation brute et T1/T2 reproduits deuxfois. Une contre-vérification indépendante du complément est demandée à dependency_refutation ; résultat à consigner séparément.

Les labels ajoutés après le résultat suivent la comparaison déjà inscrite au plan ; ils restent séparés. Les analyses forensiques ultérieures T3/T4 sont exploratoires et inscrites au registre, jamais promues en tests du détecteur. Les observations de chaque auditeur sont bornées à son périmètre : aucune certification de collecte exhaustive ni d'initiés.

Complément final : contre-vérification indépendante dependency_refutation PASS pour normalisation hors réseau ; voir DEPENDENCY_REVIEW.md. Le défaut majeur de dépendances est fermé dans ce périmètre. Le caractère post-résultats des ajouts et du contrôle moyen reste explicitement conservé.

Correction de nomenclature : les compléments forensiques sont T3/T3b (et non T3/T4). Les deux audits de conclusions ont retrouvé cinq distributions structurelles calculées pendant l'audit stats hors registre. Script et sortie conservés dans audit/, enregistrement tardif exploratoire explicite à11:21:54UTC ; total actuel29comparaisons réelles,37fixtures synthétiques,10lignes. Ce correctif ne rend pas ces diagnostics prévus au plan.

Correction de provenance du diagnostic structurel : voir PROVENANCE_CORRECTION.md ; invocation réelle10:58:08.462UTC, début de session10:56:17UTC. Registre conservé sans réécriture, total29 inchangé.

Rédaction finale : deux claims-auditor indépendants PASS10/10, aucun autre audit de conclusions lu, SHArapport b44657d03a91bcd3573721fb0755229dcf41db5ee69818d8e05488fde71fa188. Rapports claims_first.md et claims_second.md. Absence de performance contrefactuelle établie conservée. Étude non publiée et non close ; validation finale appartient à Benjamin.
