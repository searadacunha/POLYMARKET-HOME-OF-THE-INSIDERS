# Synthèse du coordinateur des audits indépendants

30octobre2026. Agents neufs ou réutilisation d'un conseiller méthodologique sans résultats. Fichiers interdits : derived/, results.md, anciens résultats, labels, data/prior_replay.json.gz, registre/tests.jsonl. Lectures autorisées code/plan/contrôles/manifeste et, après gel, PROTOCOL.lock. L'agent leakage a lu cinq projections timestamp/observed_at de la source, sans identités ni labels. Aucun auditeur n'a exécuté le script réel.

| Agent | Rôle | Verdict et portée |
|---|---|---|
| /root/signal_silent | échecs silencieux pré-gel | PASS statique après corrections âge/registre/troncature/date ; pas vérification numérique |
| /root/signal_protocol | extraction code puis comparaison au plan | conformité statique ; réserves de formulation/compteurs synthétiques corrigées avant gel |
| /root/signal_leakage | fuites | aucun BLOQUANT/MAJEUR démontré pour description conditionnelle, aucune indépendance prédictive |
| /root/design_stats | méthodologie puis statistique | PASS après variantes noyau complet et distinction non-évaluable ; aucune p/permutation/fauxpositif |
| /root/signal_closure | contre-audit neuf des majeurs | quatre PASS ; FAIL global du helper registre, PASS du chemin main normal et des reproductions officielles |

Corrections avant gel : âge via préfixe complet au lieu du suffixe plafonné ; refus de produire des résultats si des lignes sont évincées ; égalité du score/noms de règles/best_score_at avec résumé antérieur ; histogrammes complets des maxima ; définition explicite de compteurs descriptifs ; validation timestamp non fini ; vérification explicite longueur du témoin et erreurs de chaîne ; V4 relancé sur noyau complet, pas wallet isolé, pour préserver le contexte de synchronie ; score/null et éligibilité distincts après retrait.

Contrôles six méthodes PASS,59 appels principaux selon plan. Les premières conventions de registre synthétique60/58 et n78 par niveau restent dans les cinq lignes synthétiques ; dernière passe n234 pour neuf fixtures. Aucun résultat réel avant gel.

Limite MAJEURE maintenue après contre-audit : `registered()` ne fait que la vérification après écriture. L'entrée officielle `main()` en fait une avant calcul, mais un appel direct du helper, notamment dans les contrôles, ou une variable ETUDE_REPRO_DIR non vide mal ciblée, pourrait actualiser un ancien témoin avant de constater son ancienneté. `signal_closure` répond explicitement : « Ce constat n'est pas BLOQUANT pour le résultat scientifique du chemin officiel décrit. C'est une limite hors de ce chemin, qui reste MAJEURE pour la garantie globale du helper. » Il exige un lancement réellement terminé sans erreur, et pas seulement un fichier de sortie (écrit avant enregistrement).

Preuves du chemin utilisé : commande originale `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python studies/signal_validation_20261030/code/ana_signal.py`, retour0 avec quatre comptes V1–V4 ; les quatre lignes réelles sont sous gel/code connu ; variable ETUDE_REPRO_DIR absente dans l'environnement normal vérifié. Le script n'a pas été modifié après gel. Reproductions officielles dans le répertoire de reproduction, retour REPRODUIT deux fois identique ; elles n'attestent pas le registre d'origine, vérifié séparément.

Gel :12fichiers,30octobre14:30:21UTC, sha préfixe0d12d82ee0b613fd. Script ana_signal.py SHA256 a89e17e11a1b77d2ca7a9891ddfc09cbc1b621a795a31283ecf18ac0ce721e93. Contre-auditeur a vérifié les empreintes plan/code directement ; coordinateur a lancé gel.py verifier et registre.py verifier/compter. Quatre lignes réelles,14459unités descriptives, cinq synthétiques, aucune ligne réelle hors gel.

Limites de contrôles : pas de fixture dédiée à chaque frontière C2 ou aux transitions avec attrition ; revue statique, dénominateurs exportés pour recalcul indépendant. Les tests ne prouvent aucune puissance ou performance. La protection du helper n'est pas généralisable hors chemin officiel ; une prochaine version devra corriger ce point avant nouveau calcul hors de ce chemin.

Incident de reproduction : première copie sans dossier vide derived, échec explicite avant écriture. Réexécution avec création explicite de ce dossier vide dans chaque copie, même code gelé et mêmes données. Logs préservés, aucune modification du code ni de l'original pour contourner un gel.
