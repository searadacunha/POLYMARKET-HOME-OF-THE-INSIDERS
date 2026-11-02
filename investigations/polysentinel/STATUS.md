---
id: polysentinel
title: PolySentinel, prospective monitoring of Polymarket
state: IN_PROGRESS
updated_utc: 2026-11-02T15:10:21Z
origin: ~/Projects/PolySentinel
version: no git; working files up to 2026-11-02, collector running
---

## Objective

Watch public Polymarket activity locally and read-only, flag unusual behaviour, seal each decision in a hash chain, and produce files an analyst can verify on chain. An alert is a reason to look, never a finding of wrongdoing.

## Actual state

Collector and prospective registry running at snapshot time. The pipeline replay is unfinished: only scenario S_A is sealed. The signal engine runs in shadow mode. No ground truth exists.

## Conclusions

The system was not deployed before the Ballon d'Or affair. Its conditional replay is a case study, and its real historical detection capacity cannot be estimated.

## Limits

Publicly named accounts are allegations, so no precision, recall or false positive rate. Coverage is partial: taker rows, a size filter, a rotating sample. A sleeping Mac collects nothing.

## Links

The Ballon d'Or case is investigated wallet by wallet in `ballon-dor-wallets`. `signal_engine/fund_flow` is the reusable tracing engine.
