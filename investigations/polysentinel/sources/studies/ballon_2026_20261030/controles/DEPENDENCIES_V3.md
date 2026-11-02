# Contrôle de la destination distincte — 30 octobre 2026

La v2 a refusé de remplacer le ledger existant, y compris dans la copie fraîche : garde de conservation respectée. V3 conserve toutes les données gelées et crée un nouveau sous-dossier normalization_work dans la seule copie fraîche. Ses entrées sont des liens de lecture vers la copie ; le nouveau ledger et la validation sont distincts. Le SHA-256 du nouveau ledger doit égaler celui du ledger gelé, sinon le processus échoue. Aucun fichier gelé antérieur modifié, aucune règle ni taux changé.

Self-check du normaliseur et refus sur le dossier original contrôlés avant ajout. La comparaison intégrale reste à exécuter par repro.py après gel de ce nouveau lanceur.
