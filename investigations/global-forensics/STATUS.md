---
id: global-forensics
title: Global Polymarket forensics engine and catalogue
state: IN_PROGRESS
updated_utc: 2026-11-03T02:30:00Z
origin: new work, branch research/global-insider-forensics-20261102
version: stacked on research/forensic-intelligence-20261102 (PR 11)
---

## Objective

Open any Polymarket account from its address, rebuild its public funding and exits as far as proof allows, find other accounts tied by money or by behaviour, test timing patterns under a frozen plan, and run a separate shadow detector. No wallet is called an insider.

## Actual state

In progress. Done: audit, engine with tests, re-reading of references, one external control, catalogue, ChangeNOW join, frozen study with blind audit and reproduction, shadow replay, order books for two markets. Not done: most traces of the catalogue and discovery lists, the Maduro edge re-reading (64 of 571 rows), the full graph. Collection is paused: the SSD sits under the guard's floor, because of other work, and lowering the floor is Benjamin's decision.

## Conclusions

Provisional until the state is DONE. See FINDINGS.md.

## Limits

Only public data. Windows, not whole chains, on Base and BSC. All reviewers are instances of the same model family. Press and court documents are accusations, not ground truth.

## Links

Re-reads `ballon-dor-wallets`, `ballon-dor-flow-trace`, `changenow-proof`, `maduro-iran`. Audits `polysentinel`. Reuses the universe of `maduro-iran` phase 8.
