# Contrôle du lanceur de reproduction v2 — 30 octobre 2026

Premier essai du lanceur v1 : échec avant toute réécriture de donnée. Le script repro.py installé utilise ETUDE_REPRO_DIR, contrairement au descriptif ancien du skill qui évoque ETUDE_REPRO=1. Aucun fichier gelé modifié et aucune erreur masquée.

Nouveau fichier run_collector_frozen_v2.py : même chargement de dépendances et mêmes calculs ; accepte la renormalisation uniquement si le répertoire du code est réellement sous ETUDE_REPRO_DIR. Self-check PASS. Exécution validate-export sur le dossier original explicitement refusée (code1) comme attendu, sans écriture. À relancer par repro.py en copies fraîches.
