# Contribuer : procédure pour chaque session

Dépôt PRIVÉ : https://github.com/searadacunha/Polymarket-Home-of-the-Insiders

Une session possède un seul dossier `investigations/<id>/` et une seule branche `investigation/<id>`. Elle ne touche à rien d'autre.

## Les 7 étapes

Remplacer `<id>` partout. Les identifiants déjà pris sont dans `INVENTORY.md`. Pour une nouvelle enquête, choisir un identifiant court en minuscules avec des tirets.

```bash
# 1. Clone de travail propre à la session. Jamais le clone central, jamais ~.
git clone https://github.com/searadacunha/Polymarket-Home-of-the-Insiders.git ~/Projects/PHI-<id>
cd ~/Projects/PHI-<id>

# 2. Branche de l'enquête. Si elle existe déjà sur le dépôt : git switch investigation/<id>
git switch -c investigation/<id>

# 3. Se recaler sur main avant de travailler (merge, jamais rebase d'une branche poussée)
git fetch origin && git merge origin/main

# 4. Mettre à jour investigations/<id>/ : voir « Fichiers » ci-dessous.
#    Pour copier des fichiers avec empreintes et contrôle des secrets :
python3 scripts/import_snapshot.py --id <id> --origin <dossier_d_origine>

# 5. Valider. Tant que la commande échoue, on ne pousse pas.
python3 scripts/validate_evidence.py investigations/<id> --fill

# 6. Commit et push de la branche
git add investigations/<id> && git commit -m "<id>: ce qui change" && git push -u origin investigation/<id>

# 7. Pull request vers main. Tout le détail va dans la description.
gh pr create --base main --head investigation/<id> --title "<id>: <résumé>" --body-file <fichier>
```

La session centrale fusionne les PR une par une, puis régénère `MASTER_REPORT.md` et `INVENTORY.md`.

## Interdits

- `git push --force`, réécriture d'historique, push direct sur `main` par une session d'enquête.
- Modifier, déplacer ou supprimer un fichier du dossier d'origine, ou y lancer `git init`, `git add`, `git commit`.
- Modifier `MASTER_REPORT.md`, `INVENTORY.md` ou le dossier d'une autre enquête. Pour signaler une erreur chez une autre enquête : commentaire sur sa PR ou section `Contradictions` de son propre `FINDINGS.md`.
- Publier un secret, un `.env`, une clé, un cookie, ou une donnée personnelle sans rapport avec l'enquête.
- Présenter un travail incomplet comme une conclusion : `state: IN_PROGRESS` tant que ce n'est pas fini.
- Inventer un résultat, une enquête ou une preuve. Ce qui n'a pas été vérifié s'écrit `UNRESOLVED`.

## Fichiers de `investigations/<id>/`

| Fichier | Rôle |
|---|---|
| `README.md` | Objectif, méthode, comment reproduire |
| `STATUS.md` | État réel, lu par le rapport central (format strict) |
| `FINDINGS.md` | Conclusions classées, lues par le rapport central (format strict) |
| `EVIDENCE.md` | Preuves : tx, blocs, adresses, fichiers, SHA-256 |
| `sources/` | Copie de l'arborescence d'origine, chemins relatifs conservés pour que les scripts tournent. Rien d'écrit à la main ici |
| `data_manifest.json` | Généré : chaque fichier d'origine, importé ou non, et pourquoi |
| `local_only_hashes.sha256.gz` | Généré : empreintes des gros ensembles non publiés |
| `results/`, `scripts/`, `tests/` | Optionnels : ce que la session ajoute après l'import |

`import_snapshot.py` remplace `sources/` et le manifeste à chaque lancement, et ne touche jamais aux quatre fichiers `.md`. Il refuse seul les secrets, les caches HTTP bruts et les champs de profil (`bio`, `pseudonym`). Il garde les règles propres à l'enquête dans `scripts/import_rules.json`.

Option pour le contrôle des secrets : `PHI_ENV_FILES=<fichier.env>:<autre>` fait aussi refuser toute occurrence exacte des valeurs de ces fichiers, sans jamais les afficher.

### Format de `EVIDENCE.md`

Les lignes de ce tableau sont vérifiées : écrire `auto`, puis `python3 scripts/validate_evidence.py investigations/<id> --fill` remplit l'empreinte. Pour un fichier non publié, le chemin reste `sources/...` et l'empreinte vient du manifeste.

```
| Fichier | SHA-256 | Rôle |
|---|---|---|
| `sources/reports/RAPPORT.md` | auto | Rapport final |
```

### Format de `STATUS.md`

Le bloc entre `---` est lu par la machine. Les valeurs de `state` sont `IN_PROGRESS`, `DONE`, `PAUSED`, `ABANDONED`.

```
---
id: <id>
title: Titre court
state: IN_PROGRESS
updated_utc: 2026-11-02T15:00:00Z
origin: ~/Projects/<dossier>
version: dernier commit, ou "pas de git" avec la date du dernier fichier
---

Texte libre : ce qui est fait, ce qui reste, ce qui manque pour conclure.
```

### Format de `FINDINGS.md`

Une section par conclusion. La ligne de titre et les 4 puces sont obligatoires.

```
## F-001 | SUPPORTED | Une phrase qui dit ce qui est affirmé
- Sources: sources/reports/RAPPORT.md ; sources/data/fichier.csv ; tx 0xabc... (Polygon, bloc 123, 2026-10-30 12:00 UTC)
- Method: sources/tools/calcul.py, comparaison à N comptes témoins
- Limits: ce que cela ne prouve pas, contre-hypothèses
- Links: autre-enquete:F-003 (vérifié), ou "aucun"
```

Sections optionnelles reprises dans le rapport central : `## Contradictions`, `## Manque pour conclure`, `## Surveillance prospective`. Leur contenu est une liste à puces.

La validation refuse un `FINDINGS.md` dont le titre cite un nombre, une adresse ou un hash absent des fichiers listés dans `Sources` : citer le fichier qui contient réellement le chiffre, écrit de la même façon aux séparateurs près.

Dans `STATUS.md`, les sections `## Objectif`, `## Conclusions`, `## Limites` et `## Liens` sont reprises dans `INVENTORY.md`.

## Niveaux de preuve

| Niveau | Sens |
|---|---|
| `CONFIRMED` | Démontré directement par des éléments reproductibles |
| `SUPPORTED` | Indices convergents, preuve incomplète |
| `HYPOTHESIS` | Interprétation non démontrée |
| `REFUTED` | Hypothèse contredite par les données : à garder, un négatif est un résultat |
| `UNRESOLVED` | Données insuffisantes |

Trois règles de lecture, à ne jamais franchir :

- Un wallet étiqueté ChangeNOW ne prouve pas que son propriétaire est identifié.
- Une entrée dans ChangeNOW et une sortie ultérieure ne prouvent pas un transfert entre les mêmes personnes.
- Des paris suspects ne prouvent pas à eux seuls un délit d'initié. Séparer toujours comportement suspect, coordination démontrée et délit d'initié démontré.

## Données volumineuses

Un fichier de plus de 25 Mo n'entre pas dans git : il est listé dans `data_manifest.json` avec sa taille et son SHA-256, et marqué `local_only`. Un fichier `local_only` n'est PAS archivé : il n'existe que sur ce Mac, et il ne faut pas écrire le contraire.

Ces fichiers ne passent pas par Git LFS : `git-lfs` n'est pas installé sur ce Mac, et les données restent reconstructibles ou référencées par empreinte. Si Benjamin veut une vraie sauvegarde hors du Mac, ce sera une décision à part.
