# Reproduction vérifiée le 30 octobre 2026

Première reproduction de T1/T2 : deux copies fraîches, HOME isolé, derived/audit.json et derived/public_overlap.json identiques aux originaux.

Complément après audit des dépendances : deux tentatives se sont arrêtées explicitement avant tout remplacement de données (v1 : variable de contrôle différente de l'outil installé ; v2 : ledger existant protégé). Ces versions et leurs traces de contrôle restent gelées. Aucun fichier gelé original réécrit.

Commande finale exécutée avec succès (code0) :

```
python3 ~/.claude/skills/etude-gelee/scripts/repro.py studies/ballon_2026_20261030 --commande '/Users/benjamindacunha/Projects/PolySentinel/.venv/bin/python code/run_collector_frozen_v3.py validate-export > normalization_repro.log && python3 code/ana_audit.py && python3 code/ana_compare.py' --sorties 'derived/audit.json' 'derived/public_overlap.json' --fois 2
```

Sortie officielle : passage1 IDENTIQUE audit.json/public_overlap.json ; passage2 IDENTIQUE audit.json/public_overlap.json ; REPRODUIT.

Dans chaque passage, le lanceur v3 a renormalisé les réponses brutes en sortie distincte et imposé l'égalité SHA-256 avec le ledger minimal gelé avant de lancer T1/T2. Si cette égalité échoue, la commande s'arrête. Aucun réseau requis. Les empreintes originales contrôlées par repro.py n'ont pas changé. Refus de v3 sur le dossier original testé également, code1 comme attendu.

Portée : reproduction informatique des données conservées, de leurs montants API et du constat de faisabilité. Ce n'est pas une reconstitution exhaustive de Polymarket ni une validation de précision/rappel.
