# followup-20261113: the Nobel 2025 distributor (C7) and the Ballon d'Or accounts on Base, Arbitrum and Optimism

Historical on-chain follow-up, data read on 12 November 2026 from public, keyless sources. An address is not a person. These accounts are subjects of investigation, not demonstrated insiders.

## Objective

Answer two open questions of this repository: who funded the Nobel Peace Prize 2025 accounts of case C7, and whether the eleven Ballon d'Or 2026 case files are linked on Base, Arbitrum or Optimism, which were recorded as unread.

## Summary

- **Common funder:** the owner key of the 6741 Safe sends 372,521.54 USDC to eight accounts between 22:40 and 03:30 UTC, before the announcement: the six handles of the C7 roster and two others. All 16 withdrawals of these accounts go back to it or to 6741.
- **aenews0:** the profile is the proxy `0x4bac00c61a02275d681f3857cdc5ae315f1f7075`.
- **Timing:** seven accounts bought after the public repricing; only 6741 bought before it.
- **Ballon d'Or:** no direct transfer and no shared counterparty on Base, Arbitrum or Optimism; one ChangeNOW "funding" is a self round trip.
- **Not demonstrated:** a single operator, coordination, inside information.

## Where to read

| File | Content |
|---|---|
| `FINDINGS.md` | Graded conclusions, negatives included |
| `EVIDENCE.md` | Files and hashes to check yourself |
| `STATUS.md` | Actual state and limits |
| `sources/reports/FOLLOWUP_REPORT.md` | Full report with every transaction |

## Method

Blockscout API v2 for address histories (Polygon, Ethereum, Base, Arbitrum, Optimism), official token contracts only to exclude address poisoning; Polymarket gamma public profiles and data-api v2; Relay requests API v2; Across deposit status; Polymarket CLOB price history. Safe owners read with `getOwners()`. An independent review replayed every transaction of the findings through public JSON-RPC nodes, without Blockscout.

## Reproduce

The collectors in `sources/tools/` ran from the original workspace with Python 3.12 and the standard library. `onchain.py` archives every response and refuses to write when the disk is nearly full. The Relay API allows about one call per minute.
