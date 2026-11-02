# ChangeNOW and the 11 Ballon d'Or accounts: what is proven

Establish, address by address, which accounts really touched ChangeNOW, for what amounts, and how far a single order can be found with public data.

**State:** Final report written on November 2. Nothing was sent to ChangeNOW or any third party, no transaction was issued. An address is not a person: no identity is established or sought here.

## Reproduce

From a fresh clone, standard library, no network:

```bash
python3 investigations/changenow-proof/tests/check_published.py
```

It checks that every hash and address of the six reports exists in the published files, recomputes the sums and the key's balance, compares the node proofs with their hashes, and checks the proof levels.

`sources/tools/selfcheck.py` and the collection scripts need third-party files kept on the original machine, so they do not run from a clone. Their steps are in the section "Reproduire" of `sources/reports/CHANGENOW_PROOF_FINAL.md`. Third-party pages and lists are not published: their hashes are in the manifest.

## Two scales

The reports in `sources/` use the scale asked for by this investigation: level 0 no usable evidence, 1 a label from an identified source, 2 corroborated attribution and a confirmed transfer, 3 a specific order backed by an official record, 4 pay-in and payout of one order linked explicitly. `FINDINGS.md` uses the repository's levels, `CONFIRMED` to `UNRESOLVED`. They do not map one to one: a transfer can be `CONFIRMED` while its link to the service stays at level 0.

## Contents

Snapshot of November 2, 2026. `sources/` is a verbatim copy of the original working tree, mostly in French, with relative paths kept. `data_manifest.json` lists every original file, published or not, and why. `local_only_hashes.sha256.gz`, when present, holds the hashes of large unpublished sets.

- [Status](STATUS.md)
- [Classified findings](FINDINGS.md)
- [Evidence and hashes](EVIDENCE.md)
