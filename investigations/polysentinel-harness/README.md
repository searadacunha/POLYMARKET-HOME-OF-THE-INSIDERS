# Recovery harness for PolySentinel

Keep an investigation going across crashes and restarts, and admit a result only after an independent process has recomputed it from raw rows.

**State:** Not installed. Its author's verdict: do not install it before the reduced mode is resolved, a supervised run on real data has happened and a retention policy exists.

## Reproduce

`python3 scripts/restore_duplicates.py --id polysentinel-harness --dest <folder>` rebuilds the tree, then run the tests in `tests/`. History: `git clone results/harness_history.bundle`.

## Contents

Snapshot of November 2, 2026. `sources/` is a verbatim copy of the original working tree, mostly in French, with relative paths kept. `data_manifest.json` lists every original file, published or not, and why. `local_only_hashes.sha256.gz`, when present, holds the hashes of large unpublished sets.

- [Status](STATUS.md)
- [Classified findings](FINDINGS.md)
- [Evidence and hashes](EVIDENCE.md)
