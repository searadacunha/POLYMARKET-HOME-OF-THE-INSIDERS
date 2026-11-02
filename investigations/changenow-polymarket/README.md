# ChangeNOW payees who bet on Polymarket

Measure whether the payees of ChangeNOW payment wallet `f2020` bet on Polymarket, and whether they show signs of insiders.

**State:** Closed. The PnL was recomputed on November 2, 2026 from `sources/state/pm_pnl2.csv` by `scripts/recompute_pm_pnl2.py`.

## Reproduce

`python3 investigations/changenow-polymarket/scripts/recompute_pm_pnl2.py`. 8 scripts are not published because they hold the Polymarket address of the repository owner, including `proxy_resolver.py`, which 8 other published scripts import: those will not run without it. See the manifest.

## Contents

Snapshot of November 2, 2026. `sources/` is a verbatim copy of the original working tree, mostly in French, with relative paths kept. `data_manifest.json` lists every original file, published or not, and why. `local_only_hashes.sha256.gz`, when present, holds the hashes of large unpublished sets.

- [Status](STATUS.md)
- [Classified findings](FINDINGS.md)
- [Evidence and hashes](EVIDENCE.md)
