---
id: collective-exposure-falsification
title: Falsification of collective exposure shifts (mission 5)
state: DONE
updated_utc: 2026-11-17T15:30:00Z
origin: ~/Projects/Polymarket-collective-falsification-20261117
version: no git; protocol frozen 2026-11-17 14:01:31 UTC, PROTOCOL.lock fb2d486a
---

## Objective

Test out of sample whether collective shifts of real exposure predict outcomes beyond price, public market
information and individual shifts.

## Actual state

Done. Frozen protocol, VALID read once, TEST read once, null gate, verdict applied by code. Two independent
post-result audits (statistics, temporal leakage) passed on every computation; report wording corrected after
them.

## Conclusions

`UNDERPOWERED`: no advantage demonstrated, absence not proven. No tradeable edge is supported.

## Limits

The power gate G1 failed: only an effect of the STRONG injected size is excluded. M4 (funding links) could not
be tested (8 linked units, 30 needed). Fills only, closed markets under 1 M USD volume, no order book. See
`sources/FALSIFICATION_REPORT.md` sections 10 and 12.

## Links

Detector and ledger from `investigation/collective-exposure-shifts` (PR #82, missions 3 and 4); execution
replay in mission 6 (same PR).
