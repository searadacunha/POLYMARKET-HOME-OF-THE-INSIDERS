# ChangeNOW collection correction — 2026-11-05

## Scope and evidence preservation

The reviewed baseline is commit `17acd3409382201dfb6fc0d43a30d4208952eb02`.
The imported `sources/` tree, its manifest, historical results, protocols and all
README files remain unchanged. This follow-up supplies an executable preparation
step rather than editing an imported snapshot or silently changing its hashes.

`../scripts/prepare_changenow_fix.py` copies Python collector code into a NEW
workspace and applies two narrowly matched corrections. It refuses an existing
output, a nested output, ambiguous edits and changed code anchors. The original
project is read-only throughout. No network requests or collectors are launched.

## Corrections

1. `net.es_all` requests 1,000 rows and uses the same page size for termination.
   Etherscan's official changelog specifies the Free-tier reduction from 10,000
   to 1,000 records effective July 1, 2026:
   https://docs.etherscan.io/changelog
   Cut boundary blocks are re-read, legitimate identical events are retained,
   and a single block reaching the page cap raises an explicit completeness
   error rather than returning an apparently complete result.
2. ChangeNOW internal membership is limited to level-A address/chain pairs.
   An explored level-B neighbor is not automatically treated as internal.
   Other-service labels can therefore retain their service classification.
   Unlabeled neighbors become candidates for the existing checks, not proven
   clients. Existing explicit ChangeNOW labels retain their original behavior.

The 2,505-row pagination regression uses synthetic data. It is not evidence of
newly collected transactions. The attribution tests verify code behavior, not
independent on-chain attribution of the example address.

## Reproduce offline checks

From the repository root:

```bash
python3 investigations/ballon-dor-census/tests/test_changenow_fix.py
python3 investigations/ballon-dor-census/scripts/prepare_changenow_fix.py \
  investigations/ballon-dor-census/sources --check
```

The regression suite extracts the actual `es_all` function and classification
statements from the archived code without importing or running its networking
modules. It also tests workspace isolation, drift rejection and preservation of
unrelated changes. The repository integrity workflow runs this suite against the
complete published source files.

## Prepare a fresh local collection

Use an idle local project with its existing runtime prerequisites. From the
central repository root, choose an output directory that does not exist:

```bash
python3 investigations/ballon-dor-census/scripts/prepare_changenow_fix.py \
  "$HOME/Projects/PolySentinel-ballon-dor-2026" \
  --output "$HOME/Projects/PolySentinel-changenow-corrected-20261105"
```

Preparation copies only Python files under `code/` and these inputs, when
present: `derived/cn_universe.csv` (required),
`derived/census_trades.jsonl.gz`, `CLUSTERS.json` and `PROTOCOL.md`.
It does not copy `.env` files, HTTP caches, previously computed `cn_*` outputs,
label caches or test registers. `CHANGENOW_FIX.json` records hashes and missing
optional inputs. An incomplete preparation is marked `PREPARATION_FAILED.txt`;
do not run that directory.

The original Mac runtime requirements remain in place, including the Etherscan
key lookup, resource guards, PolySentinel heartbeat and external label lists.
Preparation does not install dependencies or alter those requirements. A missing
census must be recovered from the original project before interpreting a
Ballon d'Or comparison; it must not be replaced with an empty population.

After reviewing the prepared workspace, a separate, explicit collection can
run `code/col_76_cn_extend.py`, then `code/ana_75_cn_recipients.py collect`.
Do not import old `cn_functions*`, `cn_sends*`, `cn_links*`, `cn_inactivity*` or
`cn_result*` into the new workspace. These could preserve the original omission
or classification. Keep new results separate until validated and imported by
the documented snapshot procedure.

## What is not established

No live recollection, new funding link or revised verdict is produced by this
change. Historical result files retain their original meaning and limitations.
The exact amount of missing history is unresolved until a corrected collection
is compared with the recorded responses. This bounded fix does not certify
contract coverage, proxy resolution, complete thirty-day follow-up windows,
low-value payout candidates or the separate inactivity estimator. A zero in the
old result is not promoted to a newly validated absence of links.
