# Contributing

One investigation is one folder `investigations/<id>/` and one branch `investigation/<id>`. A session touches nothing else.

## Steps

Replace `<id>` everywhere. Ids already taken are in `INVENTORY.md`. For a new investigation, pick a short lowercase id with hyphens.

```bash
# 1. A working clone of your own, never the central one
git clone https://github.com/searadacunha/Polymarket-Home-of-the-Insiders.git ~/Projects/PHI-<id>
cd ~/Projects/PHI-<id>

# 2. The investigation branch. If it already exists: git switch investigation/<id>
git switch -c investigation/<id>

# 3. Get up to date with main before working (merge, never rebase a pushed branch)
git fetch origin && git merge origin/main

# 4. Update investigations/<id>/, see "Files" below. To copy files with hashes and the scan:
python3 scripts/import_snapshot.py --id <id> --origin <original_folder>

# 5. Validate. Do not push while this fails.
python3 scripts/validate_evidence.py investigations/<id> --fill

# 6. Commit and push the branch
git add investigations/<id> && git commit -m "<id>: what changes" && git push -u origin investigation/<id>

# 7. Open a pull request to main. Put the full detail in the description.
gh pr create --base main --head investigation/<id> --title "<id>: summary" --body-file <file>
```

The central session merges pull requests one at a time, then regenerates `MASTER_REPORT.md` and `INVENTORY.md`.

## Never

- `git push --force`, history rewrites, or a direct push to `main` from an investigation session.
- Change, move or delete a file in the original folder, or run `git init`, `git add` or `git commit` there.
- Edit `MASTER_REPORT.md`, `INVENTORY.md` or another investigation's folder. To flag an error elsewhere, comment on its pull request or use the `Contradictions` section of your own `FINDINGS.md`.
- Publish a secret, a `.env` file, a key, a cookie, third-party content, or personal data unrelated to the investigation.
- Present incomplete work as a conclusion: keep `state: IN_PROGRESS` until it is finished.
- Invent a result, an investigation or a piece of evidence. What was not checked is `UNRESOLVED`.

All written files, commit messages and pull requests are in English. Only `sources/` keeps the original language.

## Files in `investigations/<id>/`

| File | Role |
|---|---|
| `README.md` | Objective, method, how to reproduce |
| `STATUS.md` | Actual state, read by the master report (strict format) |
| `FINDINGS.md` | Classified findings, read by the master report (strict format) |
| `EVIDENCE.md` | Evidence files with their SHA-256 |
| `sources/` | Copy of the original tree, relative paths kept so that scripts still run. Nothing written by hand here |
| `data_manifest.json` | Generated: each original file, imported or not, and why |
| `local_only_hashes.sha256.gz` | Generated: hashes of large unpublished sets |
| `results/`, `scripts/`, `tests/` | Optional: what a session adds after the import |

`import_snapshot.py` replaces `sources/` and the manifest on each run, and never touches the four `.md` files. It refuses secrets, raw HTTP caches, images, agent working files and profile fields (`bio`, `pseudonym`) on its own. Rules specific to an investigation live in `scripts/import_rules.json`.

Optional for the secret scan: `PHI_ENV_FILES=<file.env>:<other>` also refuses any exact occurrence of the sensitive values of those files, without ever printing them.

### `STATUS.md`

Machines read the block between `---`. `state` is one of `IN_PROGRESS`, `DONE`, `PAUSED`, `ABANDONED`. The sections `## Objective`, `## Conclusions`, `## Limits` and `## Links` are copied into `INVENTORY.md`.

```
---
id: <id>
title: Short title
state: IN_PROGRESS
updated_utc: 2026-11-02T15:00:00Z
origin: ~/Projects/<folder>
version: last commit, or "no git" with the date of the last file
---

## Objective

## Actual state

## Conclusions

## Limits

## Links
```

### `FINDINGS.md`

One section per finding. The title line and the four bullets are required.

```
## F-001 | SUPPORTED | One sentence stating what is claimed
- Sources: sources/reports/REPORT.md ; sources/data/file.csv ; tx 0xabc... (Polygon, block 123, 2026-10-30 12:00 UTC)
- Method: sources/tools/compute.py, comparison with N control accounts
- Limits: what this does not prove, competing explanations
- Links: other-investigation:F-003, or none
```

Optional sections copied into the master report, each a bullet list: `## Contradictions`, `## Missing to conclude`, `## Prospective monitoring`.

Validation refuses a title that cites a number, an address or a hash absent from the files listed in `Sources`. Cite the file that really holds the figure. Separators do not matter: `304,137.63` matches `304 137,63`.

### `EVIDENCE.md`

Rows of this table are checked. Write `auto`, and `validate_evidence.py --fill` writes the hash. For an unpublished file, the path stays `sources/...` and the hash comes from the manifest.

```
| File | SHA-256 | Role |
|---|---|---|
| `sources/reports/REPORT.md` | auto | Final report |
```

## Levels of evidence

| Level | Meaning |
|---|---|
| `CONFIRMED` | Shown directly by reproducible elements |
| `SUPPORTED` | Converging signs, proof incomplete |
| `HYPOTHESIS` | Interpretation not demonstrated |
| `REFUTED` | Contradicted by the data. Keep it: a negative result is a result |
| `UNRESOLVED` | Not enough data |

See [METHODOLOGY.md](METHODOLOGY.md) for the readings that are never allowed.

## Large data

A file over 25 MB does not enter git: `data_manifest.json` lists it with its size and SHA-256, marked `local_only`. A `local_only` file is NOT archived: it exists only on the original machine, and nothing may say otherwise.
