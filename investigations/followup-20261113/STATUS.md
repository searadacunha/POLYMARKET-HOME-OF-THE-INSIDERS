---
id: followup-20261113
title: Nobel 2025 distributor (C7) and Ballon d'Or accounts on Base, Arbitrum and Optimism
state: DONE
updated_utc: 2026-11-13T08:00:44Z
origin: ~/Projects/OpenPlanter-Investigations/publication/followup-20261113
version: no git in the origin folder, last file dated 2026-11-13
---

## Objective

Resolve open questions of this repository with public, keyless data: the alleged common distributor of the Nobel Peace Prize 2025 accounts (case C7), and the Base, Arbitrum and Optimism histories of the eleven Ballon d'Or 2026 accounts, recorded as unread.

## Actual state

State: DONE, last update 2026-11-13T08:00:44Z. Data read on 12 November 2026; every transaction of the findings replayed through public JSON-RPC by an independent review. Follow-ups on the Iran leads (L13, L14, L16) are not part of this folder: they were not completed.

Not published:

- Raw API responses (HTTP caches). Their URLs, SHA-256 and fetch times are in `sources/data/raw_response_index.csv`.

## Conclusions

- The owner key of the 6741 Safe funded eight accounts, the six handles of the C7 roster and two others, with 372,521.54 USDC between 22:40 and 03:30 UTC before the announcement, and all their withdrawals went back to it or to 6741.
- aenews0 is the proxy `0x4bac00c61a02275d681f3857cdc5ae315f1f7075` (public profile name).
- Seven of the eight accounts bought after the public repricing; only 6741 bought before it. Inside information and a single operator are not demonstrated.
- No direct transfer and no shared counterparty between the eleven Ballon d'Or case files on Base, Arbitrum or Optimism.
- A ChangeNOW payout recorded as funding of a former funder of the brace227 key is a round trip of that address through ChangeNOW.

## Limits

- **BSC:** still unread, no free history.
- **Labels:** FixedFloat, ChangeNOW hot wallet and Relay depository tags come from Blockscout alone.
- **Profiles:** creation times come from the public profile API, not from the Safe deployment; aenews0 rests on the profile name.
- **Base rate:** the other large Machado buyers of the night are not enumerated completely.
- **Identity:** an address is not a person; no owner, coordination or inside information is shown.

## Links

- `research_notes/c5-c7-recovery-overlaps-2026-11-07/REPORT.md`, `research_notes/c1-c7-primary-anchors-2026-11-07/REPORT.md` (case C7).
- `investigations/ballon-dor-flow-trace/` (F-003, F-004, F-012) and `investigations/changenow-proof/` (F-013).
- Branch `research/global-insider-forensics-20261102` (commit `34ff284`), which already holds the funder in machine-generated tables.
