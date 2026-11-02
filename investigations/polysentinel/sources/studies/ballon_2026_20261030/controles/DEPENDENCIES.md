# Contrôles du complément technique — 30 octobre 2026

VÉRIFIÉ : run_collector_frozen.py self-check PASS (horloges distinctes, dates, nominal, malformed rows, pagination). Le module normalize_trade provient obligatoirement de code/vendor/polysentinel/collect.py, restauré octet pour octet depuis source archivée. Les copies collect/net ont les mêmes empreintes que collection_validation.json.

VÉRIFIÉ : ctl_medium_presence.py PASS, une fixture synthétique : un candidat, score 1, priority=false. Assertion manquante du contrôle moyen désormais explicite, sans changer le détecteur.

VÉRIFIÉ : ctl_synthetic.py réexécuté, neuf fixtures PASS avec les mêmes conditions et assertions de futur, doublons, verdict et comparaison. Le registre conserve les exécutions antérieures. Aucun nouveau score de performance réel ; puissance empirique toujours inconnue.

Renormalisation intégrale des bruts en copie fraîche prévue via repro.py après ajout au gel, jamais sur les tables d'entrée originales. Toute comparaison de reproduction conserve les mêmes fenêtres et identités.
