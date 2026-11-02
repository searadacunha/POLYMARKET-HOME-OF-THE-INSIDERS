# Recovery

Everything needed to rebuild the research without the original Mac.

## What you need

- The age identity file, kept apart from the archives. Without it, the GitHub copy and the secrets cannot be read. The clear packs on the disk do not need it.
- For GitHub: `gh auth login` with access to the private repository.
- Python 3 (`xcode-select --install`). `age` comes with this folder for Apple Silicon, otherwise `brew install age`.

## From the external disk

```bash
cd "/Volumes/VERBATIM HD/Polymarket-Home-of-the-Insiders/recovery"
./restore_all.sh --dest ~/Restored                                   # everything but the secrets
./restore_all.sh --dest ~/Restored --identity ~/age-identity.txt     # secrets too
./restore_all.sh --dest ~/Restored --root PolySentinel-flow-trace    # one project
```

## From GitHub

```bash
git clone https://github.com/searadacunha/Polymarket-Home-of-the-Insiders.git
cd Polymarket-Home-of-the-Insiders/scripts/backup
./restore_all.sh --source github --dest ~/Restored --identity ~/age-identity.txt
```

## Git histories

The disk holds a bare mirror of this repository in `git-backups/`, and bundles of local history that exists nowhere else: `git clone <name>.bundle`.

## How the data is stored

Packs under `projects/` and `raw-data/` are plain `.tar`, `.tar.gz` or `.sqlite3.gz` volumes: concatenate the numbered files of one pack, then read them with standard tools. `archives/` holds the same packs encrypted with age, plus the packs of secrets, which exist in no other form. `manifests/index-latest.jsonl.gz` gives each file's path, size, SHA-256, pack and member.

Live databases are stored as `.sqlite3.gz`: a consistent page image that opens directly once decompressed.

Older versions of a file stay in their packs: `manifests/versions-latest.jsonl.gz`, also inside the encrypted index on GitHub, gives the pack and member of each version.
