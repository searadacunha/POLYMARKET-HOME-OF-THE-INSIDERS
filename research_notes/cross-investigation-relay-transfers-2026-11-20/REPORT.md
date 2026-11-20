# Transfers between accounts of different notes, read from the Relay archive

**Date:** 20 November 2026. **Scope:** Relay orders of the addresses this repository already studies, read once as a single graph. **Status:** two transfers whose transactions are verified by receipts; the rest is a descriptive census. Exploratory: no hypothesis was fixed in advance and no rarity is claimed.

Nothing here establishes a common owner, an identity or access to non-public information. A transfer between two accounts is a money-movement fact.

## Result

1. **A buyer of the Iran strike market paid 1,000 USDC that reached the account listed as `MAGAMESSI`.** On 16 June 2026 the Polymarket account `0xfd66d7ed45d7962ad009e669cdaec9319e38fb6d` withdrew 1,000 USDC.e through Relay. Eighty-eight seconds later 1,000 was credited as collateral to the Polymarket account `0x1fa1be3eab546e06e4290839bf4c1d7abfbf1fa9`. Each of the five transactions is verified by receipts on two nodes; that they carry the same funds from one account to the other is supported, not shown (E-1b below).
   - The payer is in the population of [the cluster E network note](../iran-cluster-e-network-2026-11-05/population.txt) and in the reference population of [the Iran exit-rarity study](../iran-exit-rarity-2026-11-06/results.md). It is in none of that study's known groups.
   - The recipient is one of the seven public proxy candidates of the Iran strike and ceasefire markets recorded in [the C5/C7 recovery note](../c5-c7-recovery-overlaps-2026-11-07/REPORT.md), which lists it as `MAGAMESSI` (later renamed) and states that the seven are not shown to be coordinated.
   - No file of this repository records a transfer between these two accounts; files of the Maduro/Iran investigation and of the exit-rarity study list both only as traders of the Iran markets. The order sat in two raw Relay pages of the Iran notes, where its recipient is an Ethereum address that no document tied to `MAGAMESSI`.
2. **A comparator wallet of the Iran exit-rarity study paid 19 USDC to one of the 45 largest buyers of the Nobel market.** On 29 July 2026 the account `0xecb14ac6e9ca447ce2f2912e6217b43d7b655da3` sent 19 USDC through Relay to the account `0xe25b9180f5687aa85bd94ee309bb72a464320f1b`, which is in [the graph of the 45 largest Machado buyers](../early-detection-2026-11-13/data/nobel_top_buyers_direct_graph.json). Both transactions are verified by receipts on two nodes. The purpose of the payment is unknown, and both accounts trade many markets (see Transfer 2).
3. **Read as one graph, the archive holds 204 pairs of archived accounts joined by Relay orders.** The two above were picked by hand from the archive labels: one joins a `pr92 reference` account to a `C5/C7` candidate, the other a `pr92 comparator` account to an `NB-3` account, and no document of the repository had discussed either order. They are not the only pairs whose labels come from different notes: the table below also has `G38` to `pr92 reference` (36, and 4 the other way), `x-history` to `Ballon` (13), `pr92 reference` to and from `Maduro/Iran` (6) and single pairs to `control`, `lead` and `Inca` addresses. Most of the others join an account and a wallet that the labels call its funding wallet, its owner key, an exit address, or a deposit address shared by its cohort. Whether each pair is already discussed in a note was not checked pair by pair.

## Method

The public Relay requests API is scheduled to be retired on 24 November 2026 ([AUDIT_2026-11-04.md](../../AUDIT_2026-11-04.md)). Before that date the request records of 1,005 addresses named in this repository were archived, one page at a time, with the SHA-256 of every page. This note reads the archive as it stood on 20 November 2026 at 12:54 UTC: 703 complete histories in 863 pages, holding 14,352 distinct orders. Of these, 14,194 have a sender and a recipient that differ, dated from 21 June 2025 to 20 November 2026, and are in [data/transfers.csv](data/transfers.csv); the other 158 have the same party at both ends or a missing one. The census of what was read, merged or left out is in [data/census.json](data/census.json), written by `build.py` from the local archive.

`integrations/forensic-intelligence/relay_graph.py` reads the archive offline:

- a history counts as complete only when its pages run from 0 to n without a gap, and a page is used only if its hash and its number of orders match the manifest;
- an order read in two histories counts once; the 419 such orders differ between the two reads only in the USD valuations of amounts and fees that the API recomputes at each read, and an order whose recorded facts change between reads keeps its later state (none did);
- an order whose sender and recipient differ is a transfer between two parties (14,194 orders, of which 67 were refunded and pay nobody);
- a **direct pair** is a successful order from one archived account to another (186 pairs);
- a pair **through one address** is a successful order from an archived account to an address outside the set, when that address is itself the sender of archived orders into another archived account (18 pairs through 11 addresses). No time order is required: in 4 of the 18, every archived order of the address in the middle precedes the first payment into it (column `n_orders_via_after` of the pairs file).

The 204 pairs rest on 565 orders. They are listed in [data/pairs.csv](data/pairs.csv) with the labels of both ends; every order, with both transaction hashes, is in [data/transfers.csv](data/transfers.csv).

## Transfer 1: `0xfd66d7ed...` to `0x1fa1be3e...` (listed as `MAGAMESSI`), 1,000 USDC, 16 June 2026

Relay order `0xb81385da58b0028e35f7fffe0f0782b2d433a52dc996512006242c802932878b`, then the route of the money after the order ended.

| Step | UTC | Chain | Transaction | What the receipt shows |
|---|---|---|---|---|
| 1 | 21:17:43 | Polygon | `0xc716f77872770540b5adf34aef6a694aa2f8085fd5697cfca6f810f18b58d73e` | the payer unwraps 1,000 of the collateral token and sends 1,000.000000 USDC.e to the Relay depository `0x4cd00e38...` |
| 2 | 21:17:59 | Ethereum | `0xdb13cf16ebea06f3bcc37ec86ab84ea9f770476e026278c0466d2dbdcfb63ad7` | the Relay solver `0xf70da978...` sends 1,000.000000 USDC to `0x29ec3716a63cf27c7873831e9458f0486e819031` |
| 3 | 21:18:23 | Ethereum | `0xa41680707227f6697248fd9ee404d454edb3efe821282f57d160f7c40f856a47` | `0x29ec3716...` sends 1,000.000000 USDC to the Relay depository |
| 4 | 21:18:56 | Polygon | `0xade90fd9b144864fdf66fdcfc18f40de0053c9c7c78986c02c3dd907247d8223` | the solver sends 1,000.000000 USDC.e to `0x29ec3716...` on Polygon |
| 5 | 21:19:11 | Polygon | `0xf99eddffe076296abeeef8bc8236acea0c86c7e183a470c0b633f1647b4e3b14` | `0x29ec3716...` sends the 1,000.000000 USDC.e to the collateral token contract, which mints 1,000.000000 to `0x1fa1be3e...` |

Steps 1 and 2 are the two legs of the archived order. Steps 3 and 4 are a second Relay order, which is not in the archive: a 32-byte value at the end of the solver payment of step 4 also appears in the calldata of step 3, the same rule that ties step 2 to step 1 (for the archived orders that value is not the order id the API returns). Steps 2 to 3 and 4 to 5 are joined only by the same address, the same amount and gaps of 24 and 15 seconds; the balance of `0x29ec3716...` before step 3 was not read.

**The address in the middle.** `0x29ec3716...` is an EIP-7702 account delegated to the contract `0xe6cae83bde06e4c305530e199d7217f42808555b`, with nonce 1 on Ethereum and on Polygon. It did not send steps 3 and 5: both are transactions of other addresses to the account-abstraction entry point `0x4337084d...`, each executing an operation of `0x29ec3716...`. The entry point runs such an operation only after the account has validated it, so these steps do not show that no key holder acted; who holds the signing key was not read. In the archive the address is the sender of 33 successful orders into `0x1fa1be3e...` (87,559.64 USD as valued by the API, 16 February to 21 April 2026, all from Ethereum), and those 33 are the only archived orders the account ever received. This matches the behaviour of a deposit address that a platform assigns to an account: what arrives there is forwarded to the account within seconds. The assignment itself was not queried, so the role is stated as observed, not as a platform record.

**What the transfer shows.** One account's withdrawal went to the address that forwards deposits into another account, and 1,000 was credited to that account 88 seconds later. The archive holds no other order between these two accounts in either direction.

## Transfer 2: `0xecb14ac6...` to `0xe25b9180...`, 19 USDC, 29 July 2026

Relay order `0xe3ec2937f0144ae3973ada3b29fb48f9f9162deab129bb37f9b7412314827231`, Polygon to Polygon.

| Step | UTC | Transaction | What the receipt shows |
|---|---|---|---|
| 1 | 19:22:35 | `0x473aef761609e901ba8eb51fc93119b445de00a31903068f7a8d46afcdd7320b` | the sender unwraps 19 of the collateral token and sends 19.000000 USDC.e to the Relay depository |
| 2 | 19:22:38 | `0x00704662785e55c0aceff117cd806a968f435163ab0d4568a9a701c61da1b7ea` | the solver sends 19.000000 USDC to `0xe25b9180...` |

The sender is a comparator wallet of the exit-rarity study: it bought Yes in three of its comparison markets and is a population wallet in two. No report discusses it. It appears in data files of other investigations: the Maduro/Iran phase-13 detector watchlist (class `KNOWN_HIGH_LEAD`, a detector rule), the Ballon d'Or counter-verification lists, and the Nobel Machado trade tape of the early-detection note, where it bought No. The recipient is in several of the same files, among them the Ballon d'Or census population and counter-verification lists: both accounts trade many markets. The order is in the study's committed Relay page of the sender; no document interpreted it. The archive holds no other order between the two accounts.

All four accounts are EIP-1167 minimal proxies on Polygon, the standard form of a Polymarket proxy wallet.

## The 204 pairs by archive label

The labels are those of the archive queue, written on 19 November 2026 from the notes that name each address. The tag of a label is the investigation written in brackets, or its first two words when it has none; `pr92 reference` and `pr92 comparator` are the reference and comparator populations of the Iran exit-rarity study, `G38` the archived network of the collective-exposure investigation.

| From | To | Pairs |
|---|---|---:|
| KPMG | KPMG | 67 |
| G38 | pr92 reference | 36 |
| Maduro/Iran | Maduro/Iran | 31 |
| x-history | Ballon | 13 |
| Nobel C7 | nobel-c7 funder | 8 |
| journal | journal | 7 |
| Ballon | Ballon | 5 |
| G38 | G38 | 5 |
| NB-2 account | NB-2 hub | 4 |
| pr92 reference | G38 | 4 |
| Maduro/Iran | pr92 reference | 3 |
| NB-2 account | NB-2 owner | 3 |
| pr92 reference | Maduro/Iran | 3 |
| pr92 comparator | pr92 comparator | 2 |
| NB-2 hub | NB-2 account | 1 |
| Nobel C7 | Nobel C7 | 1 |
| control | pr92 reference | 1 |
| lead | lead | 1 |
| lead | pr92 reference | 1 |
| pardon | pardon | 1 |
| pr92 comparator | Inca | 1 |
| pr92 comparator | control | 1 |
| pr92 comparator | lead | 1 |
| pr92 comparator | pr92 reference | 1 |
| pr92 reference | pr92 reference | 1 |
| **pr92 reference** | **C5/C7** (transfer 1) | **1** |
| **pr92 comparator** | **NB-3** (transfer 2) | **1** |

The two rows in bold were selected by reading the labels; no rule computes them. By tag, 121 pairs stay inside one tag and 83 join two different tags, but a tag is not a note: `Nobel C7` and `nobel-c7 funder`, or `NB-2 account` and `NB-2 hub`, belong to one investigation. The `G38` rows join wallets of the G38 network to accounts of the reference population, which bought in the same Iran markets. The `x-history` rows join the Ballon d'Or accounts of the X-history note to addresses that the Ballon d'Or notes record as their owner keys or as their wallets on another chain. In the cross-tag rows, the `control` address is a Pulser control partner wallet, and the `lead` addresses are a withdrawal recipient shared by Pulser and cashy and an Iran cluster E deposit address; the `lead` to `lead` row joins a funding key and a buyer account of the 14 January Iran episode.

## Levels of evidence

| # | Statement | Level |
|---|---|---|
| E-1 | Transfer 1: five transactions each moved 1,000.000000 within 88 seconds: payer to Relay, Relay to `0x29ec3716...`, `0x29ec3716...` to Relay, Relay to `0x29ec3716...`, `0x29ec3716...` to the collateral contract with a mint to `0x1fa1be3e...` | CONFIRMED: same block, status, logs, calldata and block time on two nodes for each transaction |
| E-1b | The five transfers are one movement of the payer's 1,000 to `0x1fa1be3e...` | SUPPORTED: steps 1-2 and 3-4 are tied by the Relay identifier; steps 2-3 and 4-5 rest on the same address, the same amount and gaps of 24 and 15 seconds; the balance of `0x29ec3716...` was not read |
| E-2 | `0x29ec3716...` is the deposit route of `0x1fa1be3e...` | SUPPORTED: delegation, nonce, bundled execution and 33 of 33 inbound orders; the platform's own assignment was not read |
| E-3 | Transfer 2: 19 USDC left `0xecb14ac6...` and reached `0xe25b9180...` | CONFIRMED: same block, status, logs, calldata and block time on two nodes |
| E-4 | 204 pairs among 703 complete histories | CONFIRMED for the archive as it stood; the archive is incomplete |
| E-5 | The two accounts of either transfer are controlled by one party | UNRESOLVED: not shown by a transfer |
| E-6 | 496 orders name two different recipients; none is among the 565 pair orders | CONFIRMED for the archive as it stood; which field names the final recipient is UNRESOLVED |

## What is not shown

- Who controls any of the four accounts, and why either payment was made.
- That the payer and `MAGAMESSI` acted together on the Iran markets. The payment is dated three and a half months after the strike of 28 February 2026.
- That delegation to `0xe6cae83b...` links addresses to each other: it is a shared implementation.
- That such transfers are rare. No base rate was computed: 302 of the 1,005 histories had not been asked for yet when the snapshot was taken, and transfers that do not go through Relay are outside the archive.
- Anything about the frozen exit-rarity study. Its verdict stands as recorded, and nothing here was computed under its protocol.

## Reproduce

```sh
python3 -I research_notes/cross-investigation-relay-transfers-2026-11-20/verify.py   # offline, 32 checks
cd integrations/forensic-intelligence && python3 -m unittest tests.test_relay_graph
```

`verify.py` rechecks the file hashes and the contiguity of every archived history, recomputes the pairs, the label table above and the census from the committed files, decodes the token transfers of the seven transactions from the committed receipts of two nodes, checks the identifier rule between a deposit and its solver payment, the delegation of the deposit address, the 33 orders, the place of the four accounts in the notes cited above, and that the three committed Relay pages give the same rows as `data/transfers.csv`. Three checks confirm that a forged recipient, two disagreeing nodes, or a receipt filed under another transaction make it fail.

`build.py --snapshot` rebuilds `data/` from a local copy of the archive, reading only the pages listed in `data/archive_manifest.jsonl`, and `collect_receipts.py` fetches the receipts again from public nodes. Neither is needed to verify.

## Limits

- The raw archive is not in this repository: the 863 pages read here (16.6 MB compressed, 190.3 MB of page bodies, both in `data/census.json`) are on the machine that collected them. `data/archive_manifest.jsonl` gives the SHA-256 of each page read; only the three pages of the two recipient accounts are committed under `evidence/relay/`. The 14,352 orders and the 158 without two distinct parties can therefore not be recounted offline.
- 703 of 1,005 histories were complete when the snapshot was taken; the other 302 had not been asked for yet. Pairs involving them are missing. 80 of the 703 complete histories hold no order.
- The archive sees an order only when one of its two parties was asked for. The orders of the address in the middle towards accounts that were never archived are invisible.
- USD amounts are the API's own valuation at the time of the order.
- 496 of the 14,352 orders name two different recipients, the order's own field and its metadata, and `relay_graph.py` follows the metadata. In the state changes that the API recorded, the order's own recipient gains in the deposit transaction in 109 of them and in the fill in 80; in 307 neither field gains. None of the 565 pair orders is among them, but 27 would join two complete histories if the order's own field were followed. They are listed in [data/field_conflicts.csv](data/field_conflicts.csv) and were not read further.
- The API record of 71 of the 565 pair orders has no fill transaction hash; their status `success` is the API's own.
- Receipts come from two public nodes, dRPC and the Tenderly gateway, read on 20 November 2026. Block, status, logs, calldata and block time are compared; provider extras such as `blobGasUsed` differ and are not.
