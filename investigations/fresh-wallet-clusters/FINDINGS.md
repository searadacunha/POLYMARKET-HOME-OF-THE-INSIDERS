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

Public announcement times were not collected in amendments 002 and 003. Amendment 004 adds two cited clocks, below. A purchase before resolution is not, by itself, a purchase before the public knew.

## Amendment 004: a $100 screen of the information catalogue, and the 29 wallets

Amendment 004 was written before H6 was scored. Parent H1, H2, H3 and H4 are not recomputed. Their verdicts stay `NOT_OBSERVED` and `NO` on the tapes they named.

### Sources

Fills came from the public Polymarket data API, `v2/trades`, cash filter 100 USD, no API key. Two passes were used. A newest-first global cursor covered 18 November 2026 02:53 UTC through 25 November 2026 22:38 UTC (1,350,000 fills, 7.82 days) and was stopped: at that pace a walk back to January 2025 does not finish in this run, because the cursor cannot be sharded. The coverage pass then requested each of the 25,789 information markets, at most three pages (3,000 fills of at least 100 USD). A market whose cursor ended is complete at this floor. A market that still had pages is partial: only its newest 3,000 fills of at least 100 USD are in the aggregate. Raw pages were not stored. The aggregate is `/tmp/fwc-sweep/agg.sqlite`, outside the repository.

The public Goldsky orderbook subgraph returned HTTP 429 and was not used. No Dune or Allium query was run. A full scan of `OrderFilled` logs was not run: the free Polygon endpoints used here accept about 100 blocks (dRPC) or about 9,000 blocks (Tenderly) per `eth_getLogs` call, and the exchange history is tens of millions of blocks. Receipts and short log windows were read for the named addresses only. Legacy FPMM trades were not scanned.

A paid Goldsky or Dune key would unlock `OrderFilled`, split, merge and redeem history without the 100 USD floor and without a three-page cap, and a transfer graph for every candidate wallet rather than the 29 named below. No account was created and no key was bought.

### Coverage

Every one of the 25,789 information markets was requested. None returned an error.

| | Markets | Share of 25,789 |
|---|---:|---:|
| Complete at the 100 USD floor (the cursor ended within three pages) | 24,822 | 96.25 percent |
| Partial (more than 3,000 fills of at least 100 USD remain unread) | 967 | 3.75 percent |
| Complete, and no fill of at least 100 USD was returned | 57 |  |

25,732 markets contributed at least one kept fill. The oldest kept fill is 2024-04-30 05:04 UTC and the newest is 2026-11-25 23:00 UTC. On a partial market the older fills are the ones missing, so that timestamp range is not a full history for those 967 markets. Counts are in `data/phase4_coverage_summary.json`.

On the 24,822 complete tapes, 189,324 wallet-outcomes still have buy notional minus sell notional of at least 1,000 USD, across 23,438 wallets, on 21,627 markets. The sum of those ending nets is 1,524,973,389.26 USD. That sum adds the same collateral once per market, it is not profit, and fills under 100 USD are missing, so some of these wallet-outcomes would fall under 1,000 USD once small sells are counted. Amendment 002 already measured that effect on the sample. A further 169,075 complete wallet-outcomes have gross buys of at least 1,000 USD and an ending net under 1,000 USD: recycling is visible there, and the high-water was not rebuilt trade by trade. On the partial tapes, 155,884 wallet-outcomes have gross buys of at least 1,000 USD in the newest 3,000 fills. They are not treated as eligible.

21,389 complete market-outcomes have two or more wallets in that ending-net screen. That is the ordinary shape of a liquid market. Those cells were not traced, freshness was not recomputed, and they are not clusters. Parent H1 was not rerun on them.

### H6, the 29 wallets

H6 asked whether at least two of the 29 qualifying wallets, the largest fresh wallets on "Maduro out by January 31, 2026?" and "Will US or Israel strike Iran by February 28, 2026?", received their first collateral deposit from the same address that is not Polymarket infrastructure and not a contract. The activity listing was read from the oldest row, up to 3,000 rows. Where that listing had no deposit, a stablecoin log window was read around the first trade.

| Payer | Wallets | What was read | Class |
|---|---:|---|---|
| `0xf70da97812cb96acdf810712aa562db8dfa3dbef` | 5 | Relay solver already documented in this repository. Nonce at the payments is above one million. Includes `0xb5ebce29a273fa6f79ada747a37a00b3f6cf24de`, whose 9.97 and 4,994.49 USDC.e arrived in `0xf40e810c801871e6826c57c46a2ea5e47ed22afdf12dd2d8dbcedbb0c4424061` and `0x8b9f6bb9847ef38074e2736530c29276c3be329afa968dd6decbf505091b72a6` | SHARED SERVICE ONLY |
| `0xd36ec33c8bed5a9f7b6630855f1533455b98a418` | 9 | Contract, 22,142 bytes, nonce 1. The Uniswap pool already identified here as the contract that pays withdrawal-shaped USDC.e credits | SHARED SERVICE ONLY |
| `0x1929347e025d4f5f8d6b2bd2261e2f4efcacd215` | 4 | Contract, 16,414 bytes, nonce 1. A comparison already in this repository records 3,077 recipients for it in a third-party CSV | Contract payer. Not a private EOA |
| `0x09bff7ee7e321ff2b96f2ec92ced36febf30ba5f` and `0x90040fea028119b4fc6373abd3f6c94e75ab37b6` | 1 each | Both are EIP-7702 accounts delegated to `0xe6cae83bde06e4c305530e199d7217f42808555b`, the Relay deposit implementation already checked in the Relay note. The second paid 3.00 and 949.87 USDC.e to `0x4773906be5973bc5cf2b77436da04ead4d152289` | SHARED SERVICE ONLY |
| `0x843a6da3886cf889435cf0920659a00a68db8070` | 1 | EIP-1167 proxy to the ProxyWallet implementation `0x44e999d5c2f66ef0861317f9a4805ac2e90aeb4f` | One Polymarket proxy. The hop stops there |
| `0xf5042e6ffac5a625d4e7848e0b01373d8eb9e222` | 1 | Contract, 8,925 bytes, nonce 2, 5.00 USD | Contract payer |
| `0xec64c4d0a6cd0dd240b62b080d2b512836f71866` | 1 | EOA. Nonce 1 at the payment, nonce 19 at the chain tip. See the single-wallet path below | Verified transfer to one wallet |
| Five other EOAs | 1 each | Nonces 3, 6, 7, 55 and 92 at the payment, for 10.00, 10.00, 1,250.00, 1,510.79 and 1,000.00 USD respectively | Single-wallet credits |
| None read | 1 | `0x9d84ce0306f8551e02efef1680475fc0f1dc1344`. Oldest activity row is a MERGE at 2022-01-19 20:47:36 UTC. No deposit in the first 3,000 rows | Old account. Earlier funding was not read |

H6 verdict: **NOT_OBSERVED**. No two of the 29 share a first depositor that is a private EOA. The addresses that do pay more than one of them are the Relay solver, the Uniswap pool, and the contract `0x1929347e...`.

Distance from each wallet's first read activity to its earliest $1,000 threshold: 6 wallets within 7 days, 2 within 30 to 90 days, 2 within 90 to 180 days, 19 older than 180 days. None fell in the 7-to-30-day bin. Rows are in `data/phase4_windows.csv`.

### One single-wallet path

`0x62764005c3f58450d21da9984f6eab56cf3c2dd9` received 757,793.99 USDC.e at block 81097973 (2026-01-02 00:53:25 UTC, `0x4d6fe34feb631361fbc89933466164b33da51f53264de99c22e98e36aa72b2fd`) and 42,360.29 USDC.e at block 81105988 (`0x158d15630b4c664e05295668b7fc3bae22695b528a57259f301e4f25424eb958`). In the 400 blocks before the first payment the EOA had received 47,005.76, 8,475.36, 252,199.68 and 450,000.00 USDC.e from four contracts. The four contracts share one 124-byte runtime, SHA-256 prefix `f5c625376518f07a`. The same runtime is on `0x886a0940cdcffcbe628835a4401865dba40be38d` and on `0x16e7e8a89d91e80fb5f51060cd59029882d29249`. Those two are not the four payers. The transfer into the Polymarket proxy is a **VERIFIED FINANCIAL LINK** for that one wallet. No second wallet in the set of 29 received a payment from this EOA inside the 42,000 blocks after the first payment. The EOA's nonce at the tip is 19, so later transactions exist and were not all read.

### The two distributors are one chain

`0x8ecd0938300411e8d84b5778b331decee8989705` and `0xd8aefc93708f89daa1417faab1a2d26c3cb4e7c9` are EOAs with nonce 2 and no code. Their four published payments sit inside one USDC.e chain on 25 January 2025, 04:33 UTC, on the public-process market `0x4e2f44031d8f6d4c7e8cfbb727fdda42878c3a1d1d56ec502d86c0f89d559920` (NBA scoring leader). Each hop is about 10 USD smaller than the one before. `0x6fd67100b7bd9b2c249c84f8c714023addc34331` is the hop that joins the two EOAs. The chain enters at contract `0x886a0940cdcffcbe628835a4401865dba40be38d` (6,384.88 USD, `0x24b982d6646b3a69fdf672b134bee52860f85ffd5044abcee84490d8d6ab1f1d`) and was read through `0x0cc9536ea6ea234cf28d3757f1438e65d3fac1e7`. The payment transactions are sent by the EOAs themselves, to the USDC.e contract. Every hop in `data/phase4_chain_hops.csv` is a **VERIFIED FINANCIAL LINK** for the transfer. The two EOAs are not two owners, and the chain is not an information-market result. `0x886a0940...` and `0x16e7e8a8...` are already members of the published cluster on that market, and they share the 124-byte runtime above. Shared bytecode is a common template. It does not identify one signer.

### Recurrent funders

Inside the 29, the only addresses that pay more than one wallet are the Relay solver, the Uniswap pool, and contract `0x1929347e...`. In the parent edge table the only plain EOAs that pay two or more traced wallets remain the published Nobel hub `0x36626bd83accd8c1e0b9268a9db98a2233fc8c55` and `0x2c2795ea295d5eb51f9121b728ed2ea4e936a709` (four wallets, 26.75 USD together). The second was already classed from its recipients on unrelated markets. No new private recurrent funder was confirmed. The $100 screen was not traced wallet by wallet: a recurrent-funder search across every candidate would need the transfer index named above.

### Withdrawals and profit

The newest 200 activity rows were read for each of the 29. Eighteen contain a withdrawal. The largest stablecoin out in that withdrawal's receipt goes to:

- the pUSD contract `0xc011a7e12a19f7b1f670d46f03b03f3342e82dfb`, 10 wallets
- the Relay solver, 3 wallets
- the Relay depository `0x4cd00e387622c35bddb9b4c962c136462338bc31`, 2 wallets
- the EIP-1967 proxy `0xdca4af75705dbb50f62437045aff9921947917d2` (implementation `0xf92018eecaf1585de6b6d4989f51482c3e90cce5`), 2 wallets
- the EOA `0xa48fda0e6e22ed65682d70fb8738d9ed84560d81`, nonce 42, one wallet, 95,000 USD

No two of the 29 share a private EOA as that destination. Eleven wallets had no withdrawal in the newest 200 rows. Lifetime profit was not reconstructed. The public user-PnL and closed-position URLs returned HTTP 410. Sums of buys, sells and redeems inside a 3,000-row activity window are not a profit.

### Two public clocks

The Maduro clock is the Truth Social post cited by Axios at 4:21 a.m. Eastern Time on 3 January 2026, 09:21 UTC. The Department of War notice of the same day confirms the announcement. The Iran clock is the video Axios and NPR place at 2:30 a.m. Eastern Time on 28 February 2026, 07:30 UTC. CSIS places the same video at about 2:00 a.m. Eastern, so the minute is not exact. The date is. No price path was rebuilt.

Eighteen of the 29 are eligible on the Maduro market and eighteen on the Iran market. Seven are on both. Most of the $1,000 crosses are days or months before these posts, on wallets whose first read activity is older than 180 days. The crosses closest to the posts:

| Wallet | Market | Threshold (UTC) | Hours before the post | Funding read for this phase |
|---|---|---|---:|---|
| `0x62764005c3f58450d21da9984f6eab56cf3c2dd9` | Maduro | 2026-01-02 16:49 | 16.53 | The 757,793.99 path at 2026-01-02 00:53 UTC, 32.5 hours before the post |
| `0x858d551d073e9c647c17079ad9021de830201047` | Maduro | 2026-01-02 23:31 | 9.82 | Contract `0xf5042e6f...`, 5.00 USD. First activity 53 days earlier |
| `0x090a0d3fc9d68d3e16db70e3460e3e4b510801b4` | Maduro | 2026-01-03 05:51 | 3.49 | Uniswap pool. First activity 290 days earlier |
| `0x53e55bc7cb3d67ad177c023ce891ad076a9d6177` | Maduro | 2026-01-03 09:10 | 0.18 | Uniswap pool. First activity 549 days earlier |
| `0x4773906be5973bc5cf2b77436da04ead4d152289` | Iran | 2026-02-27 23:23 | 8.10 | Relay deposit account, 949.87 USD at 2026-02-27 23:05 UTC |
| `0x9ef582748baf671ee716075658b870ae747c5d4f` | Iran | 2026-02-27 17:33 | 13.93 | EOA nonce 6, 10.00 USD. First activity 183 days earlier |
| `0x71ed0bc95433cdf1be29f43219725fce9addd9eb` | Iran | 2026-02-28 07:00 | 0.49 | Uniswap pool. First activity 779 days earlier |
| `0x95074f700f93bdf6e62fc965e0832064c0877b04` | Iran | 2026-02-28 07:01 | 0.47 | Relay deposit account, 10,000 USD. First activity 4.71 days earlier |
| `0xb03b826a4fc9893b35d3ddf4f11be824525b6ca1` | Iran | 2026-02-28 07:08 | 0.36 | Contract `0x1929347e...`. First activity 234 days earlier |

Four Maduro thresholds fall after 09:21 UTC (2 minutes, 7 minutes, 17 minutes, and 2.9 hours). They are in `data/phase4_windows.csv`. None of the wallets in this table share a private EOA with another wallet in the set of 29. A $1,000 cross before a public post is a time comparison. It is not evidence that the wallet held non-public information.

### Other chains

No new path was verified off Polygon. The Relay deliveries above are the Polygon leg. The origin chain of those orders was not re-fetched. The KPMG Relay path already marked CONFIRMED, including its Solana signatures, was not re-derived.

## Amendment 005: the Maduro path, and the partial tapes

Amendment 005 was written before H7 was scored. Parent H1 through H6 are not recomputed.

### The two addresses

| Role | Address |
|---|---|
| Polymarket proxy | `0x62764005c3f58450d21da9984f6eab56cf3c2dd9` |
| Pass-through EOA | `0xec64c4d0a6cd0dd240b62b080d2b512836f71866` |

The proxy is a Gnosis Safe. Slot 0 holds the master copy `0xe51abdf814f8854941b9fe8e3a4f65cab4e7a4a8`, the Safe master already identified in this repository. Its runtime is the 124-byte proxy used across Polymarket wallets. The EOA has no code. Its nonce at the chain tip is 19, and all 19 transactions were located by binary search on `eth_getTransactionCount`. Sixteen of them are USDC.e transfers. Nonces 0 through 15 are those sixteen transfers, all to the proxy above, and they sum to 1,105,289.55 USD. Nonce 18, on 3 October 2026, pays 870.24 USD to `0xc7103fb36696a694d1c3a58ad0640ac2c9629d45`, an EOA with nonce 71 and no Polymarket activity. Nonces 16 and 17 call `0x0010a0ffe4cc25e0030f0bc5f41a8e83403a3d76` and `0xc7103fb3...` and move no stablecoin from the EOA. Rows are in `data/phase5_eoa_transfers.csv`.

### Where the 757,793.99 came from

That amount is nonce 0, block 81097973, 2026-01-02 00:53:25 UTC, transaction `0x4d6fe34feb631361fbc89933466164b33da51f53264de99c22e98e36aa72b2fd`. The EOA called `transfer` on USDC.e. In the preceding 400 blocks it had received:

| USD | From | What that address is |
|---:|---|---|
| 47,005.76 | `0xc2a37f1eb84fcc156c8aece9105dc1a73a36c3a6` | Safe, same master copy. Relayer `0x4fac062e...`, nonce 2,416,023, called `execTransaction` |
| 8,475.36 | `0x4638d71d7b2d36eb590b5e1824955712dc8ad587` | Same Safe template. Relayer `0xddafac1c...`, nonce 2,322,097 |
| 252,199.68 | `0x6ce22b6a995836c09871cdc9242b094d9e15e868` | Same Safe template. Relayer `0x6efdade3...`, nonce 1,802,082 |
| 450,000.00 | `0xc62a4388d2b88dd76dc372818b799087f40bc2c7` | Same Safe template. Relayer `0x02a86f51...`, nonce 2,362,177 |

In the day before those withdrawals, stablecoin credits of at least 1,000 USD into the four Safes came from the conditional-token contract `0x4d97dcd97ec945f40cf65f87097ace5ea0476045` and from Wrapped Collateral `0x3a3bd7bb9528e159577f7c2e685cc81a765002e2`. Those are Polymarket contracts. One non-contract credit in that window is 15,020.16 USD from EOA `0xa9c0a496b087c409c7326e3203aada31313d1972` (nonce 29) into `0xc62a4388...` only. The 8,475.36 Safe showed no credit of at least 1,000 USD in that day, so that balance was already there. The Safe signing key was not recovered.

The four Safes have earlier Polymarket activity. None of them has a trade on the 31 January 2026 Maduro market. `0x6ce22b6a...` does have an earlier trade titled "Maduro out in 2025?", a different condition. The transfers are a **VERIFIED FINANCIAL LINK**. A shared Safe template and a shared relayer are not a common owner.

### Stake, prices, and PnL on the Maduro market

Condition `0x580adc1327de9bf7c179ef5aaffa3377bb5cb252b7d6390b027172d43fd6f993`, "Maduro out by January 31, 2026?". Gamma records it resolved: Yes 1, No 0.

The proxy's tape on that condition is 51 fills, all NO, and the cursor ended. Collateral received is not this stake.

| | |
|---|---|
| NO shares bought | 75,640.2547 |
| USDC paid for those buys | 59,952.93 |
| High-water of buy notional minus sells | 59,952.92 at 2026-01-03 08:22:11 UTC |
| First buy | 2026-01-02 16:49:29 UTC, price 0.93, 47,247.06 shares, 43,939.77 USD |
| Last buy | 2026-01-03 08:22:11 UTC, price 0.52 |
| Price range of the buys | 0.51 to 0.93 |
| Shares sold | 75,640.25 |
| USDC received for the sales | 917.00 |
| Sale prices | 0.02 from 09:27 UTC, then 0.006 and 0.002 |
| Redeemed on this condition | 0 |
| Shares left | 0.0047, payout 0 |
| Cash PnL | 917.00 minus 59,952.93 = **-59,035.93 USD** |
| Unrealized | 0 |

The method is the cash identity in `investigations/data-completion-20261123/scripts/ledger_build.py`: collateral in minus collateral out on this market. The position is closed, so there is no open inventory to mark. Fills are in `data/phase5_maduro_fills.csv`.

Across every market, the same proxy's complete trade listing is 14,620 fills: 4,066,459.81 USD of buys and 1,181,219.54 USD of sells, plus 2,682,267.13 USD of redemptions on other conditions. Sells plus redemptions minus buys is -202,973.14 USD. That figure still leaves any open inventory unmarked, so it is not a lifetime profit. The largest other books include "Will André Ventura win the 2026 Portugal presidential election?" (445,588 USD of NO buys), "U.S. anti-cartel ground operation in Mexico by January 31?" (352,795 USD of YES buys), and "Will Eleven die in Stranger Things: Season 5?" (229,260 USD of NO buys).

### H7

H7 asked whether the EOA, or a non-contract address that paid the EOA before block 81097973, also paid at least 1,000 USD to a second wallet that committed at least 1,000 USD to NO on this Maduro market. The only non-proxy recipient of the EOA is the October payment of 870.24 USD, which is under 1,000 USD, and that address has no trade on the market. The addresses that paid the EOA before block 81097973 are the four Safes. H7 is **NOT_OBSERVED**. There is no permutation p-value: H7 is an existence test on one path, not a rate. Parent p-values are unchanged.

### Public clock

The buys are before the Truth Social post that Axios and Reuters place at 4:21 a.m. Eastern on 3 January 2026, 09:21 UTC. The sales at 0.02 begin at 09:27 UTC, six minutes after that post.

Reports that were already public, weeks earlier:

- Reuters, 9 December 2025: Trump declined to rule out troops and hinted at land operations in Venezuela.
- Reuters, 12 December 2025: a Caribbean buildup while Trump campaigned to oust Maduro, and more than 20 strikes on suspected drug boats.
- Reuters, 16 December 2025: the same buildup and the same strikes, after three and a half months.

Those articles do not announce a capture on 3 January. The wallet's first NO buy, at 0.93, was the price the book printed at 16:49 UTC on 2 January. By 08:22 UTC on 3 January the book printed NO at about 0.52. A full price series was not rebuilt. A purchase before the post, on the side that then went to zero, is not evidence of non-public information.

### Coverage

The 967 markets that were partial at three pages were read again, up to 15 pages, at the same 100 USD floor. 806 of them completed. 161 still have more fills.

| | Markets | Share of 25,789 |
|---|---:|---:|
| Complete within 15 pages | 25,628 | 99.38 percent |
| Still partial | 161 | 0.62 percent |

On the 806 markets that became complete only after page 3, 88,695 wallet-outcomes have buy notional minus sell notional of at least 1,000 USD, across 23,098 wallets. The sum of those ending nets is 1,894,407,874.01 USD. Same caveats as amendment 004: the sum counts collateral once per market, fills under 100 USD are missing, and it is not profit. It is not added to the amendment-004 sum.

The pre-registered band of gross buys from 900 USD up to, and not including, 1,000 USD on the three-page complete tapes contains 44,752 wallet-outcomes. Those activity listings were not re-read. No wallet is newly called eligible from a sub-100 USD fill.

The public Goldsky orderbook subgraph returned HTTP 429 again. Dune's free tier is view-only; the API sits on a paid plan or a trial that places a card hold, and neither was opened. Allium's per-call prices are a payment. No account was created and no key was bought.

### What a paid source would add

Listed prices, retrieved 26 November 2026, not a recommendation to buy:

| Source | Listed price | What it would add here |
|---|---|---|
| Dune Analyst | 75 USD per month, 4,000 credits. API export is 10 credits per MB. Free access after a trial is view-only. | One query could score the 44,752 near-threshold wallets with fills under 100 USD, and could read the 161 markets that still exceed 15,000 fills of at least 100 USD. Credit use depends on the scan, so the dollar total is not fixed from the price card alone. |
| Goldsky | 100 USD of one-time starter credit, then worker-hours at about 0.05 USD, queries not billed inside the rate limit. The public Polymarket subgraph used here is a different endpoint and returned 429. | A hosted orderbook subgraph would replace the page cap. The starter credit requires an account this run did not create. |
| Allium | 0.02 to 0.03 USD per wallet or price call on the machine-payment API. Explorer queries need a key. | A per-wallet PnL call is 0.03 USD. Scoring 44,752 wallets that way would be about 1,300 USD and still would not be the market-wide fill history. |

The concrete gap those sources would close is the 44,752 near-threshold wallets and the 161 partial markets. They would not, by themselves, turn a shared relayer or a shared Safe template into a common owner.
