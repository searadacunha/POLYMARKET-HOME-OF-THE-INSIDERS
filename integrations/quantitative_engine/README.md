# Moteur quantitatif expérimental

Adaptateur et tests hors ligne. Aucune dépendance n'est importée par les tests. DuckDB n'est chargé que par `pendulum.py` au moment de lire un Parquet local.

Ce dossier ne copie pas [warproxxx/poly_data](https://github.com/warproxxx/poly_data). Le fichier `LICENSE` de ce dépôt, au commit `136e129735c73bce3a3d59f20354417b188e47fd`, est la GPL-3.0, alors que `pyproject.toml` déclare MIT. Le code n'est pas exécuté ici et n'est pas vendu dans ce dépôt.

## Ce qui est réellement branché

- `executions.py` refuse un historique antérieur au 28 avril 2026, 11:00 UTC, et un contrat autre que `0xe111180000d2663c0091e4f400237545b87b996b`. Deux journaux `OrderFilled` miroirs d'une même transaction deviennent une seule exécution.
- `microstructure.py` lit un carnet strictement antérieur à l'impression, et une issue seulement entre 60 et 180 secondes après. Un carnet n'a pas de portefeuille.
- `validation.py` applique trois hypothèses figées, un seuil de Bonferroni 0,05/3, un minimum de 8 observations par bras, et une permutation à graine fixe. L'heure de découverte ne décide pas.
- `alerts.py` n'émet une alerte que si l'hypothèse a passé la validation. Une archive horaire n'est pas présentée comme un flux instantané.
- `replay.py` dit, pour chaque dossier historique, si la fenêtre calendaire touche une source. Cela ne crée pas un lien de portefeuille.

## Tests

```sh
cd integrations/quantitative_engine
python3 -m unittest discover -s tests -v
python3 ../../research_notes/forensic-engine-2026-11-13/verify.py
```

## Échantillon Pendulum

Les six fichiers science, économie et earnings du 11 octobre 2026, heures 00 et 01 UTC, se relisent avec :

```sh
python3 run_sample.py /chemin/vers/les/parquet /chemin/vers/sortie
```

Les empreintes SHA-256 des fichiers réellement lus sont dans `research_notes/forensic-engine-2026-11-13/data/results.json`. Aucun de ces fichiers n'est dans Git : l'archive est sous CC BY-NC 4.0, à citer comme pendulumflow.

## Bloqué

Pas de jeton `HYPERSYNC_API`. Le collecteur `poly_data` n'a donc pas été lancé. Les heures V1 de février 2026, les fichiers sports et les heures complètes d'un gibioctet n'ont pas été téléchargés.
