# Transfers between accounts of different notes, read from the Relay archive

**Date:** 20 November 2026. **Scope:** Relay orders of the addresses this repository already studies, read once as a single graph. **Status:** two transfers verified by receipts; the rest is a descriptive census. Exploratory: no hypothesis was fixed in advance and no rarity is claimed.

Nothing here establishes a common owner, an identity or access to non-public information. A transfer between two accounts is a money-movement fact.

## Result

1. **A buyer of the Iran strike market paid 1,000 USDC into the account listed as `MAGAMESSI`.** On 16 June 2026 the Polymarket account `0xfd66d7ed45d7962ad009e669cdaec9319e38fb6d` withdrew 1,000 USDC.e through Relay. Eighty-eight seconds later the same 1,000 was credited as collateral to the Polymarket account `0x1fa1be3eab546e06e4290839bf4c1d7abfbf1fa9`. The five transactions are verified by receipts on two nodes.
   - The payer is in the population of [the cluster E network note](../iran-cluster-e-network-2026-11-05/population.txt) and in the reference population of [the Iran exit-rarity study](../iran-exit-rarity-2026-11-06/results.md). It is in none of that study's known groups.
   - The recipient is one of the seven publicly named candidates of the Iran strike and ceasefire markets recorded in [the C5/C7 recovery note](../c5-c7-recovery-overlaps-2026-11-07/REPORT.md), which lists it as `MAGAMESSI` (later renamed) and states that the seven are not shown to be coordinated.
   - No note of this repository connected these two accounts. The order sat in two raw Relay pages of the Iran notes, where its recipient is an Ethereum address that no document tied to `MAGAMESSI`.
2. **A comparator wallet of the Iran exit-rarity study paid 19 USDC to one of the largest buyers of the Nobel market.** On 29 July 2026 the account `0xecb14ac6e9ca447ce2f2912e6217b43d7b655da3` sent 19 USDC through Relay to the account `0xe25b9180f5687aa85bd94ee309bb72a464320f1b`, which is in [the graph of the largest Machado buyers](../early-detection-2026-11-13/data/nobel_top_buyers_direct_graph.json). Both transactions are verified by receipts on two nodes. The purpose of the payment is unknown.
3. **Read as one graph, the archive holds 204 pairs of archived accounts joined by Relay orders, and the two above are the only pairs whose accounts come from different notes.** The 202 others join addresses that the archive labels attach to one investigation, most often an account and its own funding wallet, exit address or control wallet.

## Method

The public Relay requests API is retired on 24 November 2026. Before that date the request records of 1,005 addresses named in this repository were archived, one page at a time, with the SHA-256 of every page. This note reads the archive as it stood on 20 November 2026: 703 complete histories, 14,352 orders dated from 21 June 2025 to 20 November 2026.

`integrations/forensic-intelligence/relay_graph.py` reads the archive offline:

- an order whose sender and recipient differ is a transfer between two parties (14,194 orders, of which 67 were refunded and pay nobody);
- a **direct pair** is a successful order from one archived account to another (186 pairs);
- a pair **through one address** is a successful order from an archived account to an address outside the set, when that address is itself the sender of archived orders into another archived account (18 pairs through 11 addresses).

The 204 pairs rest on 565 orders. They are listed in [data/pairs.csv](data/pairs.csv) with the labels of both ends; every order, with both transaction hashes, is in [data/transfers.csv](data/transfers.csv).

## Transfer 1: `0xfd66d7ed...` to `MAGAMESSI`, 1,000 USDC, 16 June 2026

Relay order `0xb81385da58b0028e35f7fffe0f0782b2d433a52dc996512006242c802932878b`, then the route of the money after the order ended.

| Step | UTC | Chain | Transaction | What the receipt shows |
|---|---|---|---|---|
| 1 | 21:17:43 | Polygon | `0xc716f77872770540b5adf34aef6a694aa2f8085fd5697cfca6f810f18b58d73e` | the payer unwraps 1,000 of the collateral token and sends 1,000.000000 USDC.e to the Relay depository `0x4cd00e38...` |
| 2 | 21:17:59 | Ethereum | `0xdb13cf16ebea06f3bcc37ec86ab84ea9f770476e026278c0466d2dbdcfb63ad7` | the Relay solver `0xf70da978...` sends 1,000.000000 USDC to `0x29ec3716a63cf27c7873831e9458f0486e819031` |
| 3 | 21:18:23 | Ethereum | `0xa41680707227f6697248fd9ee404d454edb3efe821282f57d160f7c40f856a47` | `0x29ec3716...` sends 1,000.000000 USDC to the Relay depository |
| 4 | 21:18:56 | Polygon | `0xade90fd9b144864fdf66fdcfc18f40de0053c9c7c78986c02c3dd907247d8223` | the solver sends 1,000.000000 USDC.e to `0x29ec3716...` on Polygon |
| 5 | 21:19:11 | Polygon | `0xf99eddffe076296abeeef8bc8236acea0c86c7e183a470c0b633f1647b4e3b14` | `0x29ec3716...` sends the 1,000.000000 USDC.e to the collateral token contract, which mints 1,000.000000 to `0x1fa1be3e...` |

Steps 1 and 2 are the two legs of the archived order. Steps 3 and 4 are a second Relay order, which is not in the archive: its identifier is the last 32 bytes of the solver payment of step 4 and is inside the calldata of step 3, the same rule that ties step 2 to step 1.

**The address in the middle.** `0x29ec3716...` is an EIP-7702 account delegated to the contract `0xe6cae83bde06e4c305530e199d7217f42808555b`, with nonce 1 on Ethereum and on Polygon. It did not sign steps 3 and 5 itself: both are submitted by bundlers through an account-abstraction entry point. In the archive it is the sender of 33 successful orders into `0x1fa1be3e...` (87,559.64 USD as valued by the API, 16 February to 21 April 2026, all from Ethereum), and those 33 are the only archived orders the account ever received. This is the behaviour of the deposit address that the platform assigns to an account: what arrives there is forwarded to the account without a human step. The assignment itself was not queried, so the role is stated as observed, not as a platform record.

**What the transfer shows.** The withdrawal of one account was sent to the deposit route of another and credited to it. The archive holds no other order between these two accounts in either direction.

## Transfer 2: `0xecb14ac6...` to `0xe25b9180...`, 19 USDC, 29 July 2026

Relay order `0xe3ec2937f0144ae3973ada3b29fb48f9f9162deab129bb37f9b7412314827231`, Polygon to Polygon.

| Step | UTC | Transaction | What the receipt shows |
|---|---|---|---|
| 1 | 19:22:35 | `0x473aef761609e901ba8eb51fc93119b445de00a31903068f7a8d46afcdd7320b` | the sender unwraps 19 of the collateral token and sends 19.000000 USDC.e to the Relay depository |
| 2 | 19:22:38 | `0x00704662785e55c0aceff117cd806a968f435163ab0d4568a9a701c61da1b7ea` | the solver sends 19.000000 USDC to `0xe25b9180...` |

The sender is a comparator wallet of the exit-rarity study: it bought in three of its comparison markets and is not a subject of any note. The order is in that study's committed Relay page of the wallet; no document interpreted it. The archive holds no other order between the two accounts.

All four accounts are EIP-1167 minimal proxies on Polygon, the standard form of a Polymarket proxy wallet.

## The 204 pairs by archive label

The labels are those of the archive queue, written on 19 November 2026 from the notes that name each address. A label in brackets is the investigation; `pr92 reference` and `pr92 comparator` are the reference and comparator populations of the Iran exit-rarity study.

| From | To | Pairs |
|---|---|---:|
| KPMG | KPMG | 67 |
| G38 | pr92 reference | 36 |
| Maduro/Iran | Maduro/Iran | 31 |
| x-history | Ballon | 13 |
| Nobel C7 | Nobel C7 funder | 8 |
| journal (XFM accounts and collectors) | journal | 7 |
| G38 | G38 | 5 |
| Ballon | Ballon | 5 |
| pr92 reference | G38 | 4 |
| NB-2 account | NB-2 hub key | 4 |
| pr92 reference | Maduro/Iran | 3 |
| NB-2 account | NB-2 owner key | 3 |
| Maduro/Iran | pr92 reference | 3 |
| pr92 comparator | pr92 comparator | 2 |
| eleven other label pairs inside the Iran, Nobel and pardon notes | | 11 |
| **pr92 reference** | **C5/C7** (transfer 1) | **1** |
| **pr92 comparator** | **NB-3** (transfer 2) | **1** |

The G38 funding wallets, the G38 accounts and the reference population belong to the same market, and the `x-history` wallets that pay `Ballon` addresses are the eleven Ballon d'Or accounts paying their own addresses. Whether each of the 202 pairs is already written in a note was not checked pair by pair.

## Levels of evidence

| # | Statement | Level |
|---|---|---|
| E-1 | Transfer 1: 1,000 USDC left `0xfd66d7ed...` and was credited to `0x1fa1be3e...` in five transactions within 88 seconds | CONFIRMED: receipts identical on two nodes for each transaction |
| E-2 | `0x29ec3716...` is the deposit route of `0x1fa1be3e...` | SUPPORTED: delegation, nonce, bundled execution and 33 of 33 inbound orders; the platform's own assignment was not read |
| E-3 | Transfer 2: 19 USDC left `0xecb14ac6...` and reached `0xe25b9180...` | CONFIRMED: receipts identical on two nodes |
| E-4 | 204 pairs among 703 complete histories, two of them across notes | CONFIRMED for the archive as it stood; the archive is incomplete |
| E-5 | The two accounts of either transfer are controlled by one party | UNRESOLVED: not shown by a transfer |

## What is not shown

- Who controls any of the four accounts, and why either payment was made.
- That the payer and `MAGAMESSI` acted together on the Iran markets. The payment is dated three and a half months after the strike of 28 February 2026.
- That delegation to `0xe6cae83b...` links addresses to each other: it is a shared implementation.
- That such transfers are rare. No base rate was computed: 302 histories were still unread when the snapshot was taken, and transfers that do not go through Relay are outside the archive.
- Anything about the frozen exit-rarity study. Its verdict stands as recorded, and nothing here was computed under its protocol.

## Reproduce

```sh
python3 -I research_notes/cross-investigation-relay-transfers-2026-11-20/verify.py   # offline, 25 checks
cd integrations/forensic-intelligence && python3 -m unittest tests.test_relay_graph
```

`verify.py` rechecks the file hashes, recomputes the pairs from `data/transfers.csv`, decodes the token transfers of the seven transactions from the committed receipts of two nodes, checks the identifier rule between a deposit and its solver payment, the delegation of the deposit address, the 33 orders, and the place of the four accounts in the notes cited above. Two checks confirm that a forged recipient or two disagreeing nodes make it fail.

`build.py` rebuilds `data/` from a local copy of the archive and `collect_receipts.py` fetches the receipts again from public nodes. Neither is needed to verify.

## Limits

- The raw archive is not in this repository: the 863 pages read here (16.6 MB compressed) are on the machine that collected them. `data/archive_manifest.jsonl` gives the SHA-256 of each page read; only the three pages of the two recipient accounts are committed under `evidence/relay/`.
- 703 of 1,005 histories were complete when the snapshot was taken. Pairs involving the 302 others are missing.
- The archive sees an order only when one of its two parties was asked for. The orders of the address in the middle towards accounts that were never archived are invisible.
- USD amounts are the API's own valuation at the time of the order.
- Receipts come from two public nodes, dRPC and the Tenderly gateway, read on 20 November 2026.
