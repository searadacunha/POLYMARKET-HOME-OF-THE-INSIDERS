# Complément technique après audit — 30 octobre 2026

Résultats déjà vus : oui. Aucun seuil, population, label, fenêtre, critère ni calcul T1/T2 modifié. Aucun fichier gelé antérieur réécrit.

L'audit de protocole a identifié un import vers le code vivant dans col_historical.py, conservé tel quel comme trace de l'acquisition initiale. Deux chaînes distinctes : la reproduction de T1/T2 sur tables gelées était déjà autonome ; la renormalisation des réponses brutes demandait un chargement indépendant du projet vivant.

Ajouts techniques : copies exactes des collect.py/net.py archivés dans data/trade_normalizer_sources.json, copies de storage_budget.py et __init__.py, exigences de dépendances conservées. run_collector_frozen.py précharge ces copies, vérifie l'origine du normaliseur, charge le collecteur gelé puis pointe ses lectures de provenance sur le vendor. Il ne permet que self-check et validate-export hors réseau, ce dernier uniquement sous repro.py dans une copie fraîche. Il ne modifie pas l'acquisition originale ni les tables gelées.

Un contrôle synthétique supplémentaire asserte explicitement la présence du candidat moyen, en plus de son absence de priorité. Il ne règle aucun seuil et n'ajoute aucun test réel. Les anciens contrôles et leur registre restent inchangés. Ces ajouts répondent aux constats d'audit et ne constituent pas une nouvelle méthode de détection.
