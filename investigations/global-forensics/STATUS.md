---
id: global-forensics
title: Global Polymarket forensics engine and catalogue
state: IN_PROGRESS
updated_utc: 2026-11-03T09:15:00Z
origin: new work, branch research/global-insider-forensics-20261102
version: stacked on research/forensic-intelligence-20261102 (PR 11)
---

## Objective

Open any Polymarket account from its address, rebuild its public funding and exits as far as proof allows, find other accounts tied by money or by behaviour, test timing patterns under a frozen plan, and run a separate shadow detector. No wallet is called an insider.

## Actual state

In progress. Done: audit, engine with tests, re-reading of references, one external control, catalogue, ChangeNOW join, frozen study with blind audit and reproduction, shadow replay and its analysis, order books for two markets, the Maduro edge re-reading, the neodbs and planktonbets link, a separate claims auditor. Running: traces of the Ballon d'Or and documented lists, discovery in budgeted batches, ChangeNOW files and comparators, the graph. Prepared, not run on any data: a second study with a holdout, in `results/study_sync_v2/` once frozen.

## Conclusions

Provisional until the state is DONE. See FINDINGS.md.

## Limits

Only public data. Windows, not whole chains, on Base and BSC. All reviewers are instances of the same model family. Press and court documents are accusations, not ground truth.

## Links

Re-reads `ballon-dor-wallets`, `ballon-dor-flow-trace`, `changenow-proof`, `maduro-iran`. Audits `polysentinel`. Reuses the universe of `maduro-iran` phase 8.
