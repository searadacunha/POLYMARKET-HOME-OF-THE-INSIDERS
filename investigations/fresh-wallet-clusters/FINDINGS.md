# Findings

Generated from `data/stats.json` at 2026-11-25T14:54:40Z, then rewritten once after the funding queue was completed and `analyze` was run again. The verdict strings are `NO` and `NOT_OBSERVED`. The spec hash is `a1e312d04a02cc4106ce26302696d6702d493dc8cd7299133431e5a47d541f4c`.

## Answer

Beyond chance and shared financial infrastructure, this sample does not show groups of fresh wallets each committing at least $1,000 to the same outcome of an information-sensitive market, with a private funding link or a converging private withdrawal.

What was read:

- Catalogue: closed events of at least $50,000 from 1 January 2025 through 25 November 2026, plus open events of that size. Information markets in the frame: 13,390 discovery, 7,032 validation, 1,196 test, 4,060 open. Public-process markets are the control. Match-level and price-ladder tags are excluded and were not sampled.
- Systematic sample, spanning each stratum by end date: 80 test information markets, 80 validation information markets, 61 discovery information markets, 40 open information markets, and 30 / 40 / 40 public-process markets in discovery, validation and test. Four tapes hit the page cap and are out of every rate (`too_deep`): one validation information market, one validation control, one discovery control, one open market. The other 367 sampled tapes are complete. Every test information market and every test control market has a complete tape.
- Eligible wallet-outcome rows, capital committed at least $1,000 after sells are netted off: 6,908. Qualifying fresh rows: 993.
- Funding traces completed: 966, errors 0. Every member of the 15 seven-day fresh groups on test information markets was traced (`test_groups_7d` 15, `test_groups_traced` 15).

## The three tests

Corrected threshold: 0.05 / 3 = 0.0166666667. One-sided. Two thousand permutations, seed 20261125.

| Test | Stratum | Observed | Null mean | p | Role |
|---|---|---:|---:|---:|---|
| H1 private funder | TEST × INFO | 0 | 0.0 | 1.0 | confirmatory |
| H1 specificity | TEST × PUBLIC_PROCESS | 0 | 0.0 | 1.0 | qualifier |
| H2 24-hour co-timing | TEST, INFO minus control | 0.1 | 0.06139375 | 0.251874 | confirmatory |
| H3 private cash-out | TEST × INFO | 0 | 0.0 | 1.0 | confirmatory |
| H1 replication | VALIDATION × INFO | 0 | 0.0 | 1.0 | replication |
| H3 replication | VALIDATION × INFO | 0 | 0.0 | 1.0 | replication |

H1 verdict: **NOT_OBSERVED**. Central answer: **NO**.

H2 is the share of markets with two qualifying fresh wallets on one outcome inside 24 hours. The 10-point gap is not under the corrected threshold. In the matched table it sits entirely in the highest volume fifth: 8 of 21 information markets, and 0 of 3 control markets. That control cell is too small for the gap to mean much, and the permutation already treats it as one bin. It is not a finding of coordination.

## What the fresh groups were, once traced

Fifty-nine groups of at least two qualifying fresh wallets on one outcome, threshold times at most seven days apart:

| Stratum | Family | In the rate denominator | Class | Groups |
|---|---|---|---|---:|
| Test | Information | yes | SHARED SERVICE ONLY | 10 |
| Test | Information | yes | BEHAVIORAL SIMILARITY | 5 |
| Validation | Information | yes | SHARED SERVICE ONLY | 8 |
| Validation | Information | yes | BEHAVIORAL SIMILARITY | 3 |
| Validation | Public process | yes | SHARED SERVICE ONLY | 7 |
| Validation | Public process | yes | BEHAVIORAL SIMILARITY | 1 |
| Discovery | Information | yes | SHARED SERVICE ONLY | 11 |
| Discovery | Information | yes | BEHAVIORAL SIMILARITY | 2 |
| Discovery | Information | no (pipeline check) | VERIFIED FINANCIAL LINK | 1 |
| Discovery | Public process | yes | BEHAVIORAL SIMILARITY | 3 |
| Discovery | Public process | yes | SHARED SERVICE ONLY | 1 |
| Open | Information | no | SHARED SERVICE ONLY | 5 |
| Open | Information | no | BEHAVIORAL SIMILARITY | 1 |
| Discovery | Information | no | BEHAVIORAL SIMILARITY | 1 |

No test or validation group is `VERIFIED FINANCIAL LINK`, `CORROBORATED COORDINATION` or `REFUTED`. No plain cash-out destination of at least $100 is shared by two traced wallets.

`SHARED SERVICE ONLY` means the wallets' inbound collateral, inside the 10,000-block window, came from contracts, infrastructure, or busy keys. `BEHAVIORAL SIMILARITY` means they crossed $1,000 on the same outcome inside the window and the trace did not find a shared counterparty. Neither class is a common owner.

## The one verified link

Condition `0x14a3dfeba8b22a32feb0f10763db68bc4d2abeb5bff90e9ae20de53793b35a1d`, Nobel Peace Prize 2025, discovery, not in the confirmatory denominator. Fourteen qualifying fresh wallets on YES sit inside seven days. Two plain keys account for the link:

- `0xe206961002feebd9edb152eed9b630a351874043`, the key already published with the eight-wallet set. Six of those eight are labelled with it as primary funder. The other two received the same key while its nonce was still 5 or below, so the pre-registered rule calls those payments passthrough rather than primary. The transfers are in `funding_edges.csv`. The largest single transfer kept per sender is $40,000; a second $30,000 transfer to one of the wallets is not added on top. The published total is higher. The identity of the key is not affected.
- `0x36626bd83accd8c1e0b9268a9db98a2233fc8c55`, the hub already published for the second Nobel network, $59,978.70 and $31,259.44 to the two wallets named in that note.

They fall in one time window because both networks bought YES on the same night. They are not one key. The dossier is [evidence/dossiers/](evidence/dossiers/INDEX.md). This is a pipeline check. It was in the repository before this run. It does not estimate how often such a group occurs.

## Keys that are not hits

Two other plain addresses pay more than one traced wallet, both below the $100 link floor: `0x2c2795ea295d5eb51f9121b728ed2ea4e936a709` (four wallets, $2 to $19) and `0xfdb1b8dc7f5789a0c9a398026585b8b10fba5507` ($71.51 to one wallet and $5.75 to another). They are not primary funders.

Seventeen low-nonce addresses each forward roughly $6,300 to two or three wallets, mostly into `nba-scoring-leader`, a public-process discovery market. The walk reaches a contract within three hops and stops. A passthrough is not a private funder under the frozen rule. The chain is unresolved, and it is not in the information family.

## What a class would have meant

`VERIFIED FINANCIAL LINK` is two qualifying wallets, one outcome, seven days, and the same plain EOA as the largest inbound transfer of at least $100 before each threshold. `CORROBORATED COORDINATION` adds a second observation. Neither names a person. Neither is a statement about information.

Public announcement times were not collected. A purchase before resolution is not, by itself, a purchase before the public knew.
