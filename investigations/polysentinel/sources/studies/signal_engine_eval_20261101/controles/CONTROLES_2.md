# Contrôles de l'amendement 001

`tests/test_signal_engine.py`, 51 tests, sortie `tests_signal_engine_2.txt` : les 50 précédents, plus la conservation des seules paires ayant une trouvaille. Les règles de détection n'ont pas changé.

Écart d'ordre à signaler : une exécution de la passe `clean` a démarré quelques secondes avant cet ajout au gel, à cause d'une commande refusée par le verrou alors que la suivante était déjà partie. Elle a été arrêtée, sans sortie ni ligne de registre ; je n'ai lu que le fait qu'elle tournait.
