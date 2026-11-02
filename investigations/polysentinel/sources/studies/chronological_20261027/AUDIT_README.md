# Périmètre des relectures

Étude isolée : `studies/chronological_20261027/`. Aucun fichier de production,
aucun ancien plan ou rapport n'est dans le gel demandé. Le parent organise les
auditeurs ; le constructeur n'a lancé aucun sous-agent.

Avant gel : lire le plan, `code/col_extract.py`, `code/ana_evaluate.py`,
`code/ctl_synthetic.py`, `code/validate_data.py`, le module v1.2 copié,
`data/collection_validation_v2.json` et le rapport synthétique. L'extraction raw v2 peut
être lue pour contrôler provenance et sélection, mais ne pas exécuter l'analyse.
`code/write_report.py` ne fait que mettre en forme la sortie enregistrée.

Après gel, interdits aux auditeurs aveugles :

- `derived/evaluation.json` ;
- `results.md` ;
- `audit/` (rapports d'autres auditeurs) ;
- `registre/tests.jsonl`.

Le registre complet est réservé à l'audit des conclusions ; pour les autres,
utiliser `registre.py exporter-aveugle` vers un dossier temporaire, et `compter`.
Les fichiers listés dans `PROTOCOL.lock` restent lisibles conformément au skill.
`data/pre_freeze_manifest.json` est une photographie intermédiaire de préparation,
pas le manifeste final : l'intégrité finale est exclusivement celle de `PROTOCOL.lock`.

Le gel puis `sh code/run_analysis.sh` exigent le retour favorable de la revue avant gel.
Les reproductions doivent appeler le même script dans les copies fraîches ;
aucune base de production ou requête réseau n'est nécessaire pour reproduire.
Les sorties à comparer sont `derived/evaluation.json` et `results.md`.

Corrections de revue avant gel : première observation terminale dans toute l'histoire
qualifiante, inventaire et réconciliation des clés dossiers exclues, couverture
manquante non imputée, cible observée après décision, cycles `ok`/`degraded` seuls.
`controles/PREPARATION.md` conserve les correspondances des preuves avant correction.

Les gates du skill (audits aveugles, contradictions, deux audits de conclusions)
sont documentées séparément par le parent. Un calcul reproductible ne vaut pas clôture de
ces portes ; seul Benjamin peut clôturer formellement une étude gelée.
