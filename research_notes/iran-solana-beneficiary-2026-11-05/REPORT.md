# Iran cluster E: the common Solana beneficiary, where its money went, and two more Polymarket accounts

Date: 5 November 2026. Follow-up to `investigations/maduro-iran` (phase 2 and 3 reports, cluster E) and to the consolidated audit of the same day (`iran_audit_consolide_20261105.zip`, SHA-256 `4c00fba3ed22e7e9bd654dc54edd72ee30b87a968f8d01f77b84ec6870aedb79`, kept outside git). Older files are unchanged.

Every figure below is recomputed by `verify.py` from the archived responses in `evidence/`, without network access. Run `python3 -I verify.py`. The last run passed 18 checks out of 18 (`verification.json`).

## 1. What was already known

On 28 February 2026, Polymarket accounts BlueElephant666 (`0xcc32a117ac254fe51fd867b928e45492b1f6dc7e`) and SemiconductorIT (`0xd36fa21eb3fa7b1aaf97c8499253f76f82a16d48`) sent 10,704.014969 USDC.e through six Relay orders to the Solana address `4dLZQynk9SZJf6PCAV73828TZHGJaf9kWgpKVUzV4Fwy`. That address deposited 12.4478221 SOL into Privacy Cash before SemiconductorIT's credits. The earlier audit had five Polygon receipts out of six, and read the beneficiary over a seven-day window.

## 2. New results

Only results that were not in the existing reports are listed here. Relation levels follow section 7.

### N1. Two more Polymarket accounts paid the same beneficiary

| Account | Proxy wallet | Relay orders | USDC.e debited on Polygon | SOL credited |
|---|---|---|---|---|
| oveiStheair | `0x97e490d61b530d5078348d76143a25c43a47164d` | 2 | 32,210.572027 | 393.673070082 |
| aaamsaasa | `0x0a142164f48dab6448872f0abac310d03e305316` | 3 | 27,150.675873 | 331.684702550 |
| BlueElephant666 (known) | `0xcc32a117ac254fe51fd867b928e45492b1f6dc7e` | 4 | 5,064.014969 | 62.414365218 |
| SemiconductorIT (known) | `0xd36fa21eb3fa7b1aaf97c8499253f76f82a16d48` | 2 | 5,640.000000 | 69.068560977 |
| **Total** | | **11** | **70,065.262869** | **856.840698827** |

Three independent records establish each of the eleven links:
1. The Relay request lists the account as `user` and the beneficiary as `recipient`.
2. The Polygon receipt shows the USDC.e Transfer from the proxy wallet to the Relay Depository `0x4cd00e387622c35bddb9b4c962c136462338bc31`, for the exact raw amount.
3. The Solana credit carries the Relay order identifier as its memo, and the same signature appears in the request's `outTxs`.

The two new accounts provide **59,361.2479 USDC.e, 84.7 % of everything the beneficiary received**. Neither appears in any report of the repository. Both are present only as rows in the raw phase 11 trade tape.

The beneficiary is not a shared deposit address:
- Its full history holds 66 transactions, with complete pagination and a continuous balance path from 0 to 0.
- It was created by the first Relay credit at 14:37:46 UTC and closed the same day.
- Apart from these eleven orders, it received only dust from address-poisoning and spam senders.

### N2. Where the money went: 98.35 % to one Bybit customer deposit address

| Destination | SOL | Share of credits |
|---|---|---|
| `Agnhk1VsurW1ic3YNDtp3NeLTGYCiaaUwpRSKag9PdpV`, labelled **Bybit Deposit (Agnhk)** | 842.687802663 (11 transfers) | 98.35 % |
| Privacy Cash SOL pool `4AV2Qzp3N4c9RfzyEbNZs2wqWfW4EwKnnxFAZCndvfGh` | 12.447822100 (2 deposits) | 1.45 % |
| Unlabeled wallet `98jocp4jVAkpnD9uuhFYrwPksirqg3dDTnMMSd7bm5PG` | 1.700000000 (14:45:06) | 0.20 % |

The rest went to fees and rent: 0.00145 SOL in fees, and 0.00381408 SOL in rent for four Privacy Cash accounts.

After 16:20:47 UTC there is **exactly one outflow**: 69.068480977 SOL to the Bybit deposit address at 16:21:06, 19 seconds after SemiconductorIT's second credit (signature `ffrxvjWySa6N2o4RW3FkUNfmKynq36pAzXNzfkq8gq7bMAeaCY5szr3WR847LBvGn58isHggmrZ7DBimkVqdFUG` in `transactions.csv`). There is no Privacy Cash deposit after SemiconductorIT's credits.

The deposit address behaves as a Bybit customer deposit address, and it is labelled as one:
- Bybit's gas distributor `BhwuB5KYbEgDLHYwCGdet3TcUipjxExDQK3hDqtd78Qv` tops it up before each token sweep (0.011 and 0.006 SOL). This distributor funds up to 17 different addresses in a single slot.
- On 28 February its SOL is swept to **Bybit Hot Wallet 10** `iGdFcQoyR2MwbXMHQskhmNsqddZ6rinsipHc4TNSdwu`: 842.691342663 SOL in four sweeps. That hot wallet receives from 242 distinct senders in two hours.
- Its USDC and USDT are swept to Bybit Hot Wallets 6 and 2.

This is a **service frontier**. Bybit holds the identity of the customer to whom this deposit address is assigned.

### N3. A Privacy Cash withdrawal landed in the same Bybit deposit address

At 14:55:19 UTC, 29 seconds after the beneficiary's 12.3288002 SOL deposit, a Privacy Cash withdrawal paid **0.9905 SOL to the Bybit deposit address**. The decoded `ext_amount` is −990,500,000 lamports. The pool lost exactly 1.000000000 SOL, and Privacy Cash Auth `AWexibGxNFKTa1b5R5MN4PJr9HWnWRwf8EW9g8cLx3dM` received 0.0095 SOL. The relayer was `AF8VuwCncKd5ZBnLYYnMjqh4vLch8mjqE75sFe5ZjRFW`.

The pool's proof hides which deposit is being spent: this withdrawal **cannot** be matched to the beneficiary's deposits from the chain. What the chain does show is that whoever withdrew chose, as recipient, the Bybit deposit address that receives the beneficiary's sweeps.

At 15:12:11 the deposit address's own key moved exactly 0.9905 SOL to `CN5kywyqAzQD7bN6SPTB5r8r6UL6GKfpDvujYBdqv5j9`, not to the Bybit hot wallet. That address is unlabeled and high-traffic: more than 900 transactions since 2023, funded by Binance Hot Wallet 2, and it forwards incoming SOL minus 0.008. The reason for this move is unknown. Beyond it, the 0.9905 SOL merges into a fungible balance of about 50 SOL.

### N4. The Bybit account predates the case and is fed by other exchanges

The deposit address is active from 15 July 2025, when Bybit's gas distributor first funded it. Before February it received:
- about 7,400 USDC from `GJrHw6wSnrMUN9hqgui6cjy9ZR7gbXjA8md8Bd8rHLrK`, an unlabeled memecoin trading wallet that Bybit Hot Wallet 10 had funded with 36.77 SOL the same day (the first deposit back came 80 minutes later);
- 3.81903117 SOL from Binance Hot Wallet 2 in November 2025;
- 4,940.68219 USDC from `AobVSwdW9BbpMdJvTqeCN4hPAmh4rHm7vwLnQ5ATSyrS` in January 2026.

After the case, on 3 March, it received 7,419 USDT from Kraken Hot Wallet 1.

The labels conflict for `AobVSwdW…`: the Orb explorer gives Crypto.com Hot Wallet 1, while an older local library in this workspace gives Robinhood. In either case it is an exchange.

### N5. aaamsaasa's other exit and both new accounts' funding

- **aaamsaasa**:
  - At 11:41 and 11:46 UTC on 28 February, it sent 50 and 8,952 USDC.e through Relay to the Solana address `CCQQKc4vw527ehZZhQidZZT9LEzKr4Ca7bZNwJv6BmBR`, labelled **Crypto.com Deposit (CCQQK)**. That address received 8,995.497557 USDC and swept exactly that amount to Crypto.com Hot Wallet 6 at 12:32:44.
  - Its 18 February deposits (98.464031 and 5,899.2 USDC) came from **Crypto.com 6** on Polygon (`0xfa0b641678f5115ad8a8de5752016bd1359681b9`, Blockscout metadata). They passed through its Polymarket bridge deposit address `0xf7493b5ad5d1f30d18278dbdda2778d2c4c91cff`.
  - So both the entry and one exit of aaamsaasa go through Crypto.com accounts.
- **oveiStheair**: funded on 15 February by Relay orders from BSC, user `0xfe775af18824f4951f19e264901030f8528bf972`: 49.95 and 4,896.54 USDC.

### N6. All six Polygon receipts of the original audit are now archived

The receipt missing from both earlier collections, `0xc0a30b3c70070cf81c6a48bbf5e0206413523b3113fb41cf557dd81978cd3a6b` at 15:05:45 UTC, has status 1. It records a USDC.e Transfer of 1,000.000000 from BlueElephant666 to the Relay Depository. In total, 11 of 11 receipts match their Relay orders.

### N7. Roles of the two recurring addresses

- `0x519fa16e9897132b7633f634b76306a327839e06`, used by SemiconductorIT, yellowtop1 and carltiosway: an **unlabeled transit wallet**.
  - Each Polygon inflow is forwarded within minutes to Binance: Binance 48 / Binance Hot Wallet `0xe7804c37c13166ff0b37f5ae0bb07a3aebb6e245` in June 2025, then Binance: Hot Wallet 34 `0xee7ae85f2fe2239e27d9c1e23fffe168d63b4055` from September 2025.
  - Its inflows come from Relay, a Uniswap V3 pool and `0x852dc1c875f0117ea0808610010893e4c576b6a9`.
  - It is the target of address poisoning: fake "UЅDС" tokens are sent to a look-alike of the Binance address.
- `0xa6c221448af73af8350291c5cdcd877b39683766`, used by carltiosway and Momentumgod: it receives Relay fills and Binance 48 withdrawals, then forwards to `0x852dc1c875f0117ea0808610010893e4c576b6a9` (99,148.87 USDC in 69 transfers).
- `0x852dc1c8…` sent 5,037.60632 USDC to `0x519fa16e…` on 24 June 2025. The two recurring addresses therefore **share a counterparty**. That counterparty is an unlabeled, very active EOA (more than 10,000 token transfers since 2023), and its role is undetermined. This corroborates the grouping already made through carltiosway; it adds no new account.

## 3. Sequence on 28 February: four accounts processed one after another

| Batch | First order (Polygon) | Last credit (Solana) | Test order | Forwarded to Bybit deposit |
|---|---|---|---|---|
| BlueElephant666 | 14:37:43 | 15:12:39 | 150 USDC.e | 15:06:19, 15:13:59 |
| oveiStheair | 15:51:27 | 15:55:48 | 20 USDC.e | 15:56:40 to 16:04:07 (5 transfers) |
| aaamsaasa | 15:57:37 | 16:16:16 | 20 and 20.68 USDC.e | 16:16:32 to 16:18:21 (3 transfers) |
| SemiconductorIT | 16:19:55 | 16:20:47 | 20 USDC.e | 16:21:06 |

The batches do not overlap: oveiStheair's main order lands at 15:55:48, aaamsaasa's test follows at 15:57:37, and SemiconductorIT's test comes after aaamsaasa's last credit. One signer, the beneficiary key, forwarded every batch to the same exchange deposit address within seconds to minutes. Three of the four accounts open with a 20 USDC.e test.

This is consistent with **one operator handling four accounts in turn**. Other readings also fit: several people cashing out through one shared exchange account, or a paid cash-out service. Section 7 classifies it as a hypothesis of coordination and of common control, not as a demonstration.

## 4. Chronology of the bets

Source: `chronology.csv`, built from the Polymarket Data API v2 activity of each account, which is complete for each account.
- The market: "US strikes Iran by February 28, 2026?" and "Israel strikes Iran by February 28, 2026?".
- Cash PnL = redemptions + sells − buys on these two markets.
- Public timeline (phase 11 of `maduro-iran`):
  - authorisation of the strikes on 27/02 at 20:38, not public at the time;
  - first anomalous flow at 05:15;
  - strikes begin around 06:15 (approximate);
  - Israeli announcement at 06:23 (verified).

| Account | Profile created | First deposit | First Iran buy (UTC, price) | Bought | Redeemed + sold | Cash PnL | First withdrawal |
|---|---|---|---|---|---|---|---|
| oveiStheair (new) | 2026-02-15 | 2026-02-15 14:35 | 05:03:35 at 0.14 | 4,943.97 | 32,210.57 | 27,266.60 | 28/02 15:51 |
| aaamsaasa (new) | 2026-01-26 | 2026-02-18 09:25 | 05:18:43 at 0.16 | 5,995.24 | 36,152.67 | 30,157.43 | 28/02 11:41 |
| SemiconductorIT | 2026-02-04 | 2026-02-28 05:27 | 05:27:45 at 0.20 | 9,995.99 | 48,944.95 | 38,948.95 | 28/02 16:19 |
| carltiosway | 2026-02-04 | 2026-02-28 05:49 | 05:49:55 at 0.22 | 3,997.69 | 18,171.32 | 14,173.63 | 28/02 11:49 |
| yellowtop1 | 2026-02-04 | 2026-02-28 05:54 | 05:56:17 at 0.21 | 10,259.37 | 43,431.56 | 33,172.19 | 28/02 10:18 |
| Momentumgod | 2026-02-15 | 2026-02-28 06:07 | 06:08:05 at 0.24 | 1,758.59 | 7,208.74 | 5,450.15 | 01/03 18:58 |
| BlueElephant666 | not served (404) | 2026-01-19 | 05:44:03 at 0.21 | 1,112.56 | 4,874.11 (sold) | 3,761.55 | 23/01 (earlier market) |

The two new accounts differ from the five known ones:
- they were funded days in advance (15 and 18 February), while four of the five known accounts were first funded minutes before their first buy (BlueElephant666 had deposits since January);
- they bought before the cluster's 05:28 window used in phase 2, which explains why that window missed them;
- oveiStheair started before the first anomalous flow at 05:15.

Accounts created between 26 January and 15 February that bet almost only on this event, and all cashed out the same day, are a pattern. That pattern is not evidence of inside information.

**Descriptive comparator** (`comparator.json`): this is EXPLORATORY. The window and the threshold were chosen after seeing the cluster, and no test was frozen.
- Population: all 39,812 maker and taker rows of the US-strikes market from 00:00 to 06:15 UTC.
- 541 wallets bought the Yes token; 115 bought at least 1,000 USDC of it, 76 of them before 05:15.
- Ordered by first buy among those 115: oveiStheair is 77th, aaamsaasa 83rd, SemiconductorIT 85th, carltiosway 94th, yellowtop1 99th, Momentumgod 103rd.

Neither the size nor the timing of these bets is unusual on the deadline day, when Yes cost 0.11 to 0.21 and many traders bought it. The distinctive fact is the **shared exit**, not the bet timing. Inside information is not demonstrated.

## 5. Privacy Cash: every interaction

Program `9fhQBbumKEFuXtMBDw8AaQyAjCorLGJQiS3skWZdQyQD`, instruction `Transact` (Anchor discriminator `d995828fdd34fc77`). `ext_amount` is the little-endian i64 at offset 488 of the instruction data. All three transactions succeeded (`err` = null).

| UTC | Slot | Signature | Signer / fee payer | ext_amount (lamports) | Balance changes (lamports) | Fee |
|---|---|---|---|---|---|---|
| 14:50:06 | 403303671 | `3E3rDmYbGgUy5mKg3ijjXL2Engay6ZsFSA4GLVSsEwj4mgcBp31PYMEJgDGnzkN5SG66pVNmbqBbgaLr8UKKPbAg` | beneficiary | +119,021,900 | beneficiary −121,133,940; pool +119,021,900; two new accounts +953,520 each | 205,000 |
| 14:54:50 | 403304382 | `5j3r5HzQm794uR9G6yji43XZj4rhP2SuyTkEfNrB4nZ7DHLfyWp6aWxqSQ1RwyuAnajcyzimie2niDPHEPnrDGJ8` | beneficiary | +12,328,800,200 | beneficiary −12,330,912,240; pool +12,328,800,200; two new accounts +953,520 each | 205,000 |
| 14:55:19 | 403304456 | `2kkJqk86KfZ1bmMqxEAMpndtSTAFyBQRp4dNy5vQryHWiKtdXJWoMp8biX2VXmyrtWzHTUQDpSbJouiMWp6y9pdh` | relayer `AF8Vuw…` | −990,500,000 | pool −1,000,000,000; Bybit deposit +990,500,000; Privacy Cash Auth +9,500,000; relayer −2,112,040; two new accounts +953,520 each | 205,000 |

The beneficiary made no other Privacy Cash interaction. The Bybit deposit address made none other than this withdrawal.

**Cryptographic frontier.** A Privacy Cash withdrawal proves knowledge of an unspent note in the pool's Merkle tree without revealing which one. No public data matches the 1 SOL withdrawal to the 0.119 or 12.33 SOL deposits, and none may be matched by amount or timing. Three things would resolve it:
- the depositor's note or secret;
- the relayer's or front end's request logs;
- Bybit's record of who controls the deposit address and whether that customer requested the withdrawal.

## 6. Frontiers and what would resolve them

| Funds | Frontier | Resolving evidence |
|---|---|---|
| 842.69 SOL from the beneficiary, and the 1 SOL Privacy Cash withdrawal | Bybit customer deposit `Agnhk1Vs…` | Bybit KYC for that deposit address |
| 8,995.50 USDC from aaamsaasa | Crypto.com customer deposit `CCQQKc4v…` | Crypto.com KYC |
| 12.45 SOL into Privacy Cash | ZK pool | See section 5 |
| 0.9905 SOL to `CN5kywyq…` | Unlabeled relay, fungible balance | Identification of that relay |
| 1.7 SOL to `98jocp4j…` | Unlabeled wallet, 84 transactions, not traced further | WORK_LEFT |
| Funding of oveiStheair from BSC `0xfe775af1…` | BSC history not readable without a paid indexer | BLOCKED_BY_DATA |

Accounting: the beneficiary is ACCOUNTING_RECONCILED, from 0 to 0 lamports with every transaction read. Its money is TRACE_COMPLETE_TO_PUBLIC_FRONTIERS for 856.84 SOL less 1.7 SOL: 99.80 % reaches a Bybit or Privacy Cash frontier, and the 1.7 SOL is WORK_LEFT.

## 7. Classification of relations

| Relation | Level |
|---|---|
| oveiStheair, aaamsaasa, BlueElephant666 and SemiconductorIT → beneficiary | Passage through a service (Relay), confirmed on both chains by order identifier, receipts and memo. Direct economic link to one recipient |
| Beneficiary → Bybit deposit `Agnhk1Vs…` | Direct transfer confirmed (11 transfers) |
| Bybit deposit → Bybit hot wallets | Service (exchange custody) |
| Privacy Cash withdrawal → Bybit deposit | Passage through a service; supported financial relation with the beneficiary's exit, not a matched deposit |
| `GJrHw6wS…` ↔ Bybit deposit | Supported financial relation: withdrawal from Bybit, then a deposit back into this address within two hours. Plausibly the same customer, not proven |
| aaamsaasa → Crypto.com deposit; Crypto.com → aaamsaasa | Passage through a service |
| Funders of BlueElephant666 and carltiosway (KuCoin, Kraken, Binance hot wallets) that also paid the Bybit deposit | Shared exchange hot wallets. **Not a link** |
| `0x519fa16e…` and `0xa6c22144…` through `0x852dc1c8…` | Supported relation through an unlabeled, very active EOA. Role undetermined |
| Four accounts processed one after another into one beneficiary | Hypothesis of coordination |
| One person controls the four accounts and the Bybit account | Hypothesis of common control. Strongest reading of the chain, not demonstrated |
| Inside information | Not demonstrated. Comparators show the timing is not distinctive |

## 8. Leads checked and rejected

- **8 June, carltiosway and aaamsaasa.** carltiosway sent about 12,126.75 USDC to `0x519fa16e…` at 11:13 to 11:15, and aaamsaasa deposited 5,336.90 USDC.e at 11:37:54. But `0x519fa16e…` forwarded the full 12,126.748094 to Binance: Hot Wallet 34 at 11:20:06, and aaamsaasa's deposit came through a separate Relay fill. No link. The origin of that 8 June deposit is WORK_LEFT.
- **Shared Solana funders.** KuCoin Hot Wallet 2, Kraken Hot Wallet 1 and Binance Hot Wallet 2 fund the Polymarket bridge deposit addresses of BlueElephant666 and carltiosway, and also pay the Bybit deposit address. They are exchange hot wallets with 24 to 174 transactions in ten minutes. Not a link.
- **Pre-Feb 28 history of the beneficiary.** None exists: the first credit created the account.

## 9. Limits

- **Labels.** Solana labels come from a single source, the Orb explorer (orbmarkets.io, built by Helius), read on 5 November 2026. Screenshots of the four decisive labels are kept outside git. EVM labels come from the Blockscout metadata service JSON in `evidence/http/`. A label is an attribution, not proof of control. The behaviour checks in `verify.py` (gas top-ups to many addresses, hundreds of senders) are independent of the labels.
- **Relay.** The Relay `requests/v2?hash=` endpoint is announced as retired on 24 November 2026. The archived responses are the record.
- **Polymarket data.** Polymarket API responses are archived with profile fields removed (`bio`, `pseudonym`, images, internal user ids). Trade rows keep seven fields. The originals and their SHA-256 are listed in `evidence/polymarket_reduced/ORIGINALS.json` and kept outside git.
- **Comparator.** It counts only Yes-token buys on the US market, not No-token sells, and it is exploratory.
- **Untraced.** BSC funders of SemiconductorIT, yellowtop1 and oveiStheair: no free BSC history. `98jocp4j…` and `CN5kywyq…`: not traced beyond one hop. `0x852dc1c8…`: role undetermined.
- **Address poisoning.** Look-alike addresses (`AgnhRrjM…`, `AGnHgaLH…`, `4dLjUzva…`, `0xee7a8a18…`) sent dust and fake tokens. They are excluded as noise, not counted as counterparties.

## 10. Reproduction

- `scripts/collect.py`: the sequential collector used, one network worker. It needs Helius keys from the local research pool and, for Polygon history, an Etherscan v2 key; no key is stored.
- `scripts/flows.py` and `scripts/poly_decode.py`: decoders.
- `scripts/build.py`: produces `transactions.csv`, `chronology.csv`, `graph.json`, `graph.mmd`, `labels.csv` and `comparator.json` from the raw responses.
- `verify.py`: needs only this folder.
