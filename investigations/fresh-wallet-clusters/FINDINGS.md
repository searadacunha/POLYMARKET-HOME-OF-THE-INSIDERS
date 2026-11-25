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

## Amendment 002: fills under 100 USD, fingerprints, longer flows

The parent tape ignored buys and sells under 100 USD. Amendment 002, frozen in `amendment-002.json` before the new tapes were requested, reread the same sample at a 1 USD floor. Rules for commitment, freshness, and H1 to H3 did not change.

| | Parent, 100 USD floor | Amendment, 1 USD floor |
|---|---:|---:|
| Markets with a complete tape | 367 | 355 |
| Markets over the page cap | 4 | 16 |
| Fills under 100 USD kept | 0 | 513,256 |
| Eligible wallet-outcomes | 6,908 | 4,152 |
| Newly eligible |  | 592, on 188 markets |
| No longer eligible because the market became too deep to read |  | 3,301 |
| No longer eligible because small sells pulled committed capital under 1,000 USD |  | 47 |
| H1 test, observed / p | 0 / 1.0 | 0 / 1.0 |
| H1 validation | 0 | 0 |
| H3 | 0 | 0 |
| H2 difference / p | +0.10 / 0.252 | +0.053 / 0.336 |

The headline drop from 6,908 to 4,152 eligible rows is mostly markets that no longer fit in 15 pages once small fills are included. Those markets are out of the rate, not evidence against the wallets. On the markets that stayed complete, 592 wallet-outcomes cross 1,000 USD only after the small buys are counted, and 47 fall back under 1,000 USD once small sells are netted. The verdict does not move. It is still `NOT_OBSERVED`, and the central answer is still `NO`.

The Nobel pipeline check still passes on the new tape: 8 of the 8 known wallets are eligible on YES, and 6 carry the published key as primary funder.

### Fingerprints

Four shapes were taken from the mechanisms already written in this repository and scored as frequencies, not as proof of information. The corrected threshold for four tests is 0.0125. None clears it.

| Fingerprint | What was counted on the test information markets | Result |
|---|---|---|
| FP1, cofunded fresh, 24 hours, plain funder of at least 1,000 USD | 0 groups | Same shape as the Nobel night. Not seen again in the test window |
| FP4, shared plain cash-out | 0 groups | |
| FP3, lonely F1 wallet, entry at 0.20 or below, at least half the eligible capital in the next 15 minutes | information minus control +0.0125, p = 0.86 | The shape is not rarer on the control markets |
| FP2, handoff screen | 17 candidate pairs | Not promoted. The screen matches similar amounts close in time. Each pair was not read from its receipt in this pass, so none receives an evidence class |

### Longer flows and re-entry

The longer lookback, 150,000 blocks, was run for 28 wallets: the Nobel set, and service-only test wallets. It still shows the published key paying 6 of the Nobel wallets. A second address, `0x2c2795ea295d5eb51f9121b728ed2ea4e936a709`, pays two wallets in that longer window. Its nonce at the chain tip is 1,061, so the frozen rule calls it a busy key. Its recent outgoing payments reach active traders on unrelated markets. That is `SHARED SERVICE ONLY`, not a new cluster.

Around the Nobel funding night the same key also sent 330,191.06 USD to the EOA `0xb282b48ae713fa2201282e298f3393130c4f851d` and 70,000 USD to the contract `0x9295ee1d8c5b022be115a2ad3c30c72e34e7f096`. Neither address has a Polymarket activity row. The EOA payment is a verified transfer with no re-entry. The contract is where the trace stops. The following 160,000 blocks show no further outgoing transfer of at least 100 USD from the key. Dossier: [evidence/dossiers/amendment002-nobel-downstream.md](evidence/dossiers/amendment002-nobel-downstream.md).

Maduro, Iran, Ballon d'Or and KPMG headline markets were not added to this tape. At a 1 USD floor their volume exceeds the page cap, so a partial tape would have been discarded. Their published fingerprints are the templates above. They were not re-measured here.

## Amendment 003: coverage, receipts, and the Nobel payments

Amendment 003 was written before this pass was scored. The parent verdict stands for the complete tapes it named. It is not a statement about markets that were not read. A high nonce is recorded and is not, by itself, a shared service.

### Coverage

The volume-filtered catalogue contains 25,789 information markets. Complete tapes at a 1 USD floor, after raising the page cap from 15 to 80 for the markets that had been dropped:

| Set | Markets with a complete tape |
|---|---:|
| Information markets in the catalogue | 25,789 |
| Information markets with a complete 1 USD tape | 260 |
| Coverage of that catalogue | 1.0 percent |
| All families, complete 1 USD tapes, including the sample and the two headline markets below | 368 |
| Still over 80 pages, prefix discarded | 6, including the Harry Kane Ballon d'Or market |

The two headline information markets that completed are "Maduro out by January 31, 2026?" (445 eligible wallet-outcomes, 24 pages) and "Will US or Israel strike Iran by February 28, 2026?" (288 eligible, 32 pages). Nine previously dropped information markets also completed. Three information markets and three public-process markets, including the largest sports tapes, still exceed 80 pages. KPMG is not a new market census: the 14 Relay handoffs already marked CONFIRMED in `research_notes/financial-links-replay-2026-11-07/data/kpmg_handoffs_verified.csv` are not re-derived here.

On the phase-3 complete tapes, 3,729 wallet-outcomes commit at least 1,000 USD, across 2,827 wallets. The sum of those committed amounts is 31,543,664.92 USD. That sum is capital committed, not profit, and it overlaps wallets already counted in the earlier sample.

### The 17 pairs

Each of the 17 transactions named by the handoff screen was read. None of them contains a stablecoin transfer from the named source to the named destination. The screen is **REFUTED** as a direct handoff. In 16 of the 17, the source sends about 6,300 USD to a different EOA. The seventeenth, a Nobel transaction, sends 29,635.65 USD from `0xa430506774f9efaf39903ee7e0db1351f66891ca` to the contract `0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222`, not to `0x1973177faa69b94b4afab818e612a7c05b3c01a9`. Rows are in `data/handoff_receipt_review.csv`.

Two of those EOAs were then read forward. Both have nonce 2.

- `0x8ecd0938300411e8d84b5778b331decee8989705` pays 6,384.88 USD to `0x55332ec9e58aef97bb8e8e7ab3a276fc974efe75` and 6,374.86 USD to `0x6fd67100b7bd9b2c249c84f8c714023addc34331`.
- `0xd8aefc93708f89daa1417faab1a2d26c3cb4e7c9` pays 6,364.84 USD to `0xf5266745d2277887084d86a501fdcd2b99e219df` and 6,354.82 USD to `0xc7106cf0ad32dc0db983d67f4d164920e2c8568b`.

Those four payments are **VERIFIED FINANCIAL LINK**s. They sit on the public-process market `0x4e2f44031d8f6d4c7e8cfbb727fdda42878c3a1d1d56ec502d86c0f89d559920`. The transfers do not establish one owner.

### Nobel, 400,191.06 USD

The 330,191.06 USD payment to `0xb282b48ae713fa2201282e298f3393130c4f851d` (`0xa3b2afdee9ce0c39b9dce54f327760fb1c7c43822f94a8901a6262d94ad77463`) is an EOA with nonce 9. No outgoing stablecoin transfer of at least 50 USD was found in the following 17,000 blocks, and the Polymarket activity listing is empty. The transfer is verified. No re-entry was observed. Class for the transfer: **VERIFIED FINANCIAL LINK**. Class for re-entry: not observed.

The 70,000 USD payment to `0x9295ee1d8c5b022be115a2ad3c30c72e34e7f096` (`0x708b58858b25ea4cad8987054c11981046071b7758d92244dd5a7c1898755b43`) lands on a contract. That contract later sends 70,000 USD to `0xeff7337b37c8d217d01cb8223fe497abd75190d5` and other amounts to `0x07ae8551be970cb1cca11dd7a11f47ae82e70e67` (nonce 516,457) and `0xef1ec136931ab5728b0783fd87d109c9d15d31f1` (nonce 226,285). None of those three has a Polymarket activity row. The path is verified as far as those transfers. It does not identify a person and it does not show a new bet. Class: **UNRESOLVED**.

### H4 on the two headline markets

The 25 largest eligible wallets on each of the Maduro and Iran markets above were read. Twenty-nine were qualifying fresh. Each was traced for 10,000 blocks before its threshold. No collateral inflow was stored for any of them, so no shared funder was read. H4 on this set is **NOT_OBSERVED** for a receipt-read private funder. Funding outside that window, and the other eligible wallets on those markets, were not traced.

## What a class would have meant

`VERIFIED FINANCIAL LINK` is two qualifying wallets, one outcome, seven days, and the same plain EOA as the largest inbound transfer of at least $100 before each threshold. `CORROBORATED COORDINATION` adds a second observation. Neither names a person. Neither is a statement about information.

Public announcement times were not collected. A purchase before resolution is not, by itself, a purchase before the public knew.
