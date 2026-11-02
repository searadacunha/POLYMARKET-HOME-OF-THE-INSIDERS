# Independent audit of the Ballon d'Or investigation

Check version 1 of the Ballon d'Or report independently of its code: accounts, chain, relations, conclusions.

**State:** Finished on November 2. Its corrections are part of version 3 of `ballon-dor-wallets`.

## Reproduce

Scripts in `sources/code/`, outputs in `sources/out/` (see the head of `sources/RAPPORT_AUDIT.md`). They read the files of the original investigation and public nodes.

## Contents

Snapshot of November 2, 2026. `sources/` is a verbatim copy of the original working tree, mostly in French, with relative paths kept. `data_manifest.json` lists every original file, published or not, and why. `local_only_hashes.sha256.gz`, when present, holds the hashes of large unpublished sets.

- [Status](STATUS.md)
- [Classified findings](FINDINGS.md)
- [Evidence and hashes](EVIDENCE.md)
