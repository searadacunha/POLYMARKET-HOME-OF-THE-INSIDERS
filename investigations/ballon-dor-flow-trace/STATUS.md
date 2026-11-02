---
id: ballon-dor-flow-trace
title: Funding and cash-outs of the 11 Ballon d'Or 2026 accounts
state: DONE
updated_utc: 2026-11-02T15:30:00Z
origin: ~/Projects/PolySentinel-flow-trace (export publish/origin)
version: no git, last file dated 2026-11-02
---

## Objective

For each of the 11 accounts: where the money came from, through which intermediaries, where it went afterward, and whether there are common funders or destinations beyond shared services.

## Actual state

State: DONE, last update 2026-11-02T15:30:00Z.

Not published:

- `state/http_cache` (82 MB): raw responses, some of which carry profile fields. It exists only on this Mac, so it is not archived.
- The copies of the label lists (27 MB): hashes and sources are in `sources/evidence/labels/`.

Left for Benjamin to decide:

- Entry of wallet `0xa8e64a3c…74a5` into the frozen R3, by dated amendment.
- Independent review.

## Conclusions

- The brace227 key funds, in almost equal shares, an unnamed Polymarket wallet that buys only Kane Yes. A financial link is demonstrated, a common owner is not.
- 1 direct transfer out of 55 pairs, no other shared personal address.
- More than half of the deposits come from addresses labeled KuCoin and Binance. Relay everywhere. No labeled mixer, no sign of XMR.
- About 74% of the withdrawals were still on their first address, or had returned to it, on November 2.
- Funding less than an hour before the first purchase is not distinctive against accounts of the same age.
- Coordination and inside information remain not demonstrated.

## Limits

- **BSC and Base:** no free history. `base.blockscout.com` answers with an anti-bot check, not bypassed. On BSC: known receipts, nonces, balances, 5 recent outflows of the brace227 key. Its 104 outflows before July 30, 2022 are not enumerated. BSC and Base inflows not read.
- **Labels:** some have a single source, including KuCoin Hot Wallet 2 and Revolut 5. One list dates from 2023. Blockscout tags were read only for the 73 service addresses encountered around the case files; control accounts use the public lists alone, to stay comparable.
- **Services absent from the lists:** "no interaction" means no interaction with a known address.
- **Search for other wallets:** 50 addresses. 5 case-file keys with no flow read are not tested in the old form. The old Safe and Magic proxies are not tested.
- **FIFO allocation:** an accounting convention, not proof that those exact dollars moved.
- **Control accounts:** traits chosen after the fact, a single positive control for a direct link, 54 readable keys out of 77 wallets.
- **Review:** parallel Claude session for the second wallet and the rates. Same model family: no independent audit in the strong sense.
- **Figure check:** it verifies the presence of a value, not that it relates to the right fact. One error corrected: 47 addresses instead of 50, see `sources/JOURNAL_AGENTS.md`.
- **Tests:** `sources/tests/test_forensics.py` gives 77 out of 77 on the workstation, with the HTTP cache. Without it and without the label lists, the network must be read again, and the result is not guaranteed identical.

## Links

- Original investigation and session `polysentinel-investigation-03`: its report cites these results. Identifier in this repository not verified at the time of this publication.
