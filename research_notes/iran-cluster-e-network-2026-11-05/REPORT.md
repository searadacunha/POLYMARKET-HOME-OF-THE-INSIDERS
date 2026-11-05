# Iran cluster E is a network of at least 18 Polymarket accounts

Date: 5 November 2026. Second follow-up of the same day to `../iran-solana-beneficiary-2026-11-05/` (four accounts paying the Solana beneficiary `4dLZQynk…`). That note and its evidence are unchanged. Only results that are not in it, nor in `investigations/maduro-iran`, are reported here.

Every figure is recomputed offline by `verify.py` from `evidence/` and from the previous note's `evidence/`. Run `python3 -I verify.py`. The test of `PLAN_RARITY.md` (frozen in commit `0e84c65` before its data was collected) is still collecting and is not reported here.

## 1. Method in one paragraph

The Relay API `requests/v2?user=<address>` returns the orders in which an address is the **sender or the recipient** (with one gap on the recipient side, section 8). Its control: for `4dLZQynk…` it returns exactly the 11 orders of the previous note, no more. Querying the shared destinations of cluster E, then each new sender, then each new recipient, gives the other Polymarket accounts. Each link is then checked against the account's own Polymarket activity (same transaction hash, or same exact amount within seconds), the Polygon or BSC receipt, and Blockscout labels. A limit was found on the way: queried as recipient, the index misses same-chain orders whose fill has no hash (section 8).

## 2. Two shared destinations are customer-specific, not transit infrastructure

| Address | Previous reading | What the chain shows | Classification |
|---|---|---|---|
| `0x519fa16e9897132b7633f634b76306a327839e06` | unlabeled transit wallet | its only POL comes from **Binance: Deposit Funder 1** `0x9430801ebaf509ad49202aabc5f5bc6fd8a3daf8` (2 top-ups); every USDC it receives is forwarded in full, within minutes, to Binance 48, Binance Hot Wallet 34 (Polygon) or Binance 51 (BSC) | **Binance customer deposit address**. Every deposit is credited to one Binance account |
| `0xa6c221448af73af8350291c5cdcd877b39683766` | forwards to an unlabeled EOA | EIP-7702 delegated EOA (authorization to `0x0000fb7702036ff9f76044a501ac1aa74cbab16b`, ERC-7579 `execute` relayed by `0x80e54311d48127cb66df9d65bf430796c8cf42be`); its 69 non-zero USDC outflows all go to `0x852dc1c875f0117ea0808610010893e4c576b6a9` | **Customer-specific wallet** (a self-custody wallet or a per-customer deposit address of an unidentified service). Every Relay fill and every Polymarket withdrawal it received comes from the accounts below |
| `0x9063493a4233006be654da772ef4dc38720cac55` | not in the repository | every inflow is forwarded in full to **Crypto.com 39** `0x2d17db18b41c92e64abaefb7e35ed70ed45b6dc8` | **Crypto.com customer deposit address** |

Labels come from the Blockscout metadata service (single source, archived in `evidence/http/`). The behaviour (gas from the exchange's funder, full sweeps to the exchange) is checked by `verify.py` independently of the labels.

## 3. Who pays these destinations

Amounts are in USDC or USDC.e as recorded on each transfer; the differences between the two are fees below 0.1 %. "New" means absent from cluster E in every report of the repository.

### 3.1 Binance customer deposit address `0x519fa16e…`

| Account | Proxy wallet | Transfers | Amount | Period |
|---|---|---|---|---|
| ILOVEYOUBABYZZ (new) | `0x909fa9f89976058b8b3ab87adc502ec7415ea8c3` | 11 | 168,282.31 | Jun 2025 to 28 Feb 2026 |
| SemiconductorIT | `0xd36fa21eb3fa7b1aaf97c8499253f76f82a16d48` | 2 | 43,307.06 | Mar 2026 |
| Domariocarios (new) | `0x72630d496a5c3c86665d029a4e05875c0ea9a031` | 1 | 24,596.58 | 10 Jun 2026 |
| DonkeyDonkey999 (new) | `0xcb18ea2923d957bd9cf049cce60a87638722f867` | 2 | 20,011.85 | 13 Jun 2025 |
| yellowtop1 | `0x3e44cfbf234a9616c5f9edddd6bd6bd068854d4a` | 2 | 16,591.57 | 28 Feb 2026 |
| carltiosway | `0xd109e93d5a86a68982c0b5e94323d01ab728de03` | 2 | 12,126.75 | 8 Jun 2026 |
| rrrrgggbbbclat (new) | `0xe756468f0869e27d6c1c51a10993fd7ce4627866` | 1, through `0x44a2c68087a3e6a9a3eedd9cf9c25fd76241e978` | 4,222.00 | 3 May 2026 |
| ALLOWMETOSHOWU1 (new) | `0xc8a6d6b4f5d66a1211ed678edb828acca25c5d97` | 1 | 318.49 | Sep 2025 |

Eight accounts, about 289,457 in total. ILOVEYOUBABYZZ's eight withdrawals of June 2025 went through Polymarket's Uniswap route (the USDC.e leaves the proxy and the pool pays the deposit address in the same transaction); DonkeyDonkey999's two are identified the same way from the receipts. The others are Relay orders whose Polygon input is a WITHDRAWAL row of the account. `0x44a2c680…` receives 4,222 pUSD from rrrrgggbbbclat in a transaction that is a WITHDRAWAL of that account, unwraps it and sends it through Relay 14 seconds later.

### 3.2 EIP-7702 wallet `0xa6c22144…`

| Account | Transfers | Amount |
|---|---|---|
| ALLOWMETOSHOWU1 (new), 9 of them through `0x200b195893faf4da3f431125afc17d0903fc8ea6` | 60 | 49,311.80 |
| ILOVEYOUBABYZZ (new) | 46 | 23,840.97 |
| Momentumgod | 4 | 7,225.72 |
| carltiosway | 2 | 1,045.00 |
| ParkingLocator (new), `0x4f5e7aca62b7fc31e0611b24085bb38574c88903` | 1 | 743.35 |
| `0x8c33013f39b98b3a784f7718ce8a7947db6b59fa` (new, no username), on BSC | 1 | 19.98 |

`0x200b1958…` is not a separate account: each of its 9 Relay orders follows, within 45 seconds and for the same amount, a WITHDRAWAL of ALLOWMETOSHOWU1. ParkingLocator's withdrawal (1 March, 18:56 UTC) precedes Momentumgod's first one to the same wallet by two minutes.

### 3.3 Crypto.com customer deposit address `0x9063493a…`

- TheOneWhoKnocks1312 (new, `0x6c2c072a0aa8fb8b4faf9aecae5520541f3b2d2a`): six withdrawals of 150 to 10,000 USDC.e on 13 June 2025, 00:53 to 01:17 UTC, 35,121.39 USDC received.
- TBFMM (new, `0xc4fdb47064604dc198a911afae48d9e4236b4b39`): three Relay orders, 1 December 2025 and 30 January 2026, 9,541.80.
- Bybit: Wallet 130 `0x1347378b1d0eb69d3462e09b3dfa2fe28ebe74ec` sent 2,687.14 USDC on 24 December 2025.

## 4. Transfers between accounts

| From | To | Date (UTC) | Sent | Received | Path and proof |
|---|---|---|---|---|---|
| TBFMM | BlueElephant666 | 19 Jan 2026, 20:06 | 1, 122, 1,400 | same | The three transactions are WITHDRAWAL rows of TBFMM and DEPOSIT rows of BlueElephant666 with the same hashes (`0x04e4384b85409f77a41d09e43aa31d61415fdd2f11cbf1f3d4be487ee4b65a47` and two others). They are BlueElephant666's first deposits |
| TBFMM | DonkeyDonkey999 | 13 Jan 2026, 10:49 | 32 | same | Same hash as a WITHDRAWAL of TBFMM and a DEPOSIT of DonkeyDonkey999 |
| ILOVEYOUBABYZZ | DonkeyDonkey999 | 13 Jan 2026, 15:34 | 2,073 | same | Same hash as a WITHDRAWAL of ILOVEYOUBABYZZ and a DEPOSIT of DonkeyDonkey999 |
| TBFMM | oveiStheair | 15 Feb 2026, 14:35 and 14:37 | 50 and 4,900.47 USDC.e | 49.90 and 4,894.07 | Relay Polygon to BSC into `0xfe775af18824f4951f19e264901030f8528bf972`, oveiStheair's deposit address, which bridges the exact amount back 14 to 17 s later. These are oveiStheair's only two deposits, attributed until now to a "BSC funder" |
| ILOVEYOUBABYZZ | ALLOWMETOSHOWU1 | 10 Sep 2025, 11:41 | 5,000 USDC.e | 4,994.66 | Into `0x20bd758daa8d5c2a51e95370079d34f38d91f8b2`, which converts exactly the 4,996.07889 USDC received 39 s later for ALLOWMETOSHOWU1. That is ALLOWMETOSHOWU1's first deposit; its profile was created at 11:37 |
| Domariocarios | ALLOWMETOSHOWU1 | 10 Jun 2026, 17:43 | 9,999.999995 | same | Same deposit address `0x20bd758d…`, converted 15 s later; DEPOSIT row at 17:44:04. One minute earlier Domariocarios had sent 24,596.58 to the Binance deposit address |
| aaamsaasa | `0x82be522b4c2936ee10129239cef501f8ba2bcf36` (no username) | 8 Jun 2026, 11:49 | 5,281.90 | same | Into `0x98d4e9aa9527316598c4ee6783329b529e292bcb`, which converts and mints pUSD to `0x82be522b…` in transaction `0x521924de3ba4175ead5ce4c7a83fa73283d59da38188ca64ea17d86c69bf7dcb`, its DEPOSIT row. That account withdrew the same amount one minute later |
| aaamsaasa | FluentCastle1352 `0xb355589a08b22bd9c5602b345ad8294aa04a1494` | 23 Jul 2026, 16:57 | 10 | same | Same pattern through `0xed412759234979acf5818121bc37c606373262b2`; the account was created at 16:52 |

`0x20bd758d…` is ALLOWMETOSHOWU1's deposit address: all four of its deposits pass through it.

## 5. Two exchange round trips that line up

These are supported relations, not proofs: an exchange pays every customer from the same hot wallets.

**14 January 2026, Bybit.** Crypto.com Hot Wallet 1 (Orb label) pays 8.796175 and 4,931.886015 USDC to the Bybit customer deposit address `Agnhk1Vs…` of the previous note, at 11:59:57 and 12:08:08. Bybit sweeps 4,940.68219 USDC at 12:11:11. At 12:12:39, **Bybit Hot Wallet 6** `Gem2VAypSg7Ai7vjDKPTtqFahpoQWkfgVkyzx3rPoTka` pays **4,939.68219 USDC**, exactly 1 USDC less, to `4H4WacXekz1eGebGTQanvcNytAxiei4uBzJy36h9qj1g`, which bridges it 41 s later to TBFMM (Relay order, DEPOSIT row of TBFMM). So the Bybit account that later receives 842.69 SOL from `4dLZQynk…` is, in all likelihood, the account that funded TBFMM, and TBFMM in turn funded BlueElephant666 and oveiStheair.

**28 February 2026, Binance, before the strikes.**

| Order (UTC) | BSC block | Transfer |
|---|---|---|
| 05:25:11 | 83,800,712 | ILOVEYOUBABYZZ withdraws 26,258.78 USDC.e; Relay pays 26,243.02 USDC on BSC to the Binance deposit address `0x519fa16e…` |
| | 83,800,961 | Binance 51 `0x8894e0a0c962cb723c1976a4421c95949be2d4e3` pays 10,000 USDC to `0x937db5b193b367425919de9c08ed78f9119a883c` |
| 05:27:22 | 83,800,995 | that address, SemiconductorIT's deposit address, bridges the 10,000 to SemiconductorIT, who buys Yes at 05:27:45 |
| | 83,801,728 | the Binance deposit address sweeps the 26,243.02 to Binance 51 (its only outflow in this window) |
| | 83,802,283 | Binance Hot Wallet 7 `0xe2fc31f816a9b94326492132018c3aecc4a93ae1` pays 7,222.21 USDC to `0x9028a9e6545e76e74b26f832ec501d63b80b44e7`, Domariocarios's deposit address (bridged at 05:37:14) |
| | 83,804,592 | Binance 51 pays 10,263.49 USDC to `0x5b1323e6f7ebb4643e6d61da582adac8097c64ab`, yellowtop1's deposit address (bridged at 05:54:33) |

The three accounts later withdrew to the same Binance deposit address (section 3.1). The chain shows a deposit into one Binance account followed, within 30 minutes, by three Binance withdrawals that fund three accounts of the network. It cannot show that the withdrawals came from that same Binance account.

## 6. Behaviour shared by the new accounts

Both observations below were made after the financial links. They are descriptive and exploratory.

- **Profile creation.** Six accounts were created on 4 February 2026 within 43 minutes: SemiconductorIT 17:41, Domariocarios 18:10, rrrrgggbbbclat 18:14, carltiosway 18:19, yellowtop1 18:20, `0x8c33013f…` 18:23. Three on 15 February within 34 minutes: Momentumgod 13:25, ParkingLocator 13:28, oveiStheair 13:59. No base rate of account creation was measured.
- **June 2025.** ILOVEYOUBABYZZ, TheOneWhoKnocks1312 and DonkeyDonkey999 all bought Yes on "Israel military action against Iran by Friday?" on 12 June 2025 at 0.10 to 0.17 (last buy 22:49 UTC; 35,872 USDC together) and sold at 0.995 or more from 00:23 UTC on 13 June. Their withdrawals of that night go to the Binance and Crypto.com deposit addresses above. Many traders bought this market that day; no comparator was computed.
- ALLOWMETOSHOWU1 also bought "Will US or Israel strike Iran on March 4, 2026?" and "… March 5" (62,016 USDC of Yes). DonkeyDonkey999 traded "Israel military response against Iran by Friday?" in October 2024.

## 7. Classification of relations

| Relation | Level |
|---|---|
| TBFMM → BlueElephant666; TBFMM → DonkeyDonkey999; ILOVEYOUBABYZZ → DonkeyDonkey999 | Direct transfer confirmed (same transaction hash in both accounts' activity) |
| TBFMM → oveiStheair; ILOVEYOUBABYZZ → ALLOWMETOSHOWU1; Domariocarios → ALLOWMETOSHOWU1; aaamsaasa → `0x82be522b…`; aaamsaasa → FluentCastle1352 | Transfer through the receiving account's own deposit address, confirmed by exact amounts, Relay orders and the receiver's DEPOSIT row |
| Eight accounts → Binance deposit `0x519fa16e…`; two → Crypto.com deposit `0x9063493a…`; six → wallet `0xa6c22144…`; four → `4dLZQynk…` (previous note) | Shared customer-specific destination: their withdrawals were credited to the same exchange account or wallet. Supported financial relation, not proof of common ownership |
| Bybit 14 Jan; Binance 28 Feb | Supported relation through an exchange: timing and exact amounts, customer not provable |
| Creation times, June 2025 trading | Behavioural, exploratory |
| One operator controls the 18 accounts | Hypothesis. It is the simplest reading of sections 3 to 5; a shared exchange account used by several people, or a cash-out service, would also fit section 3 but less easily section 4 |
| Inside information | Not demonstrated |

With the previous note, the network is: BlueElephant666, SemiconductorIT, oveiStheair, aaamsaasa, carltiosway, yellowtop1, Momentumgod (known), and TBFMM, ILOVEYOUBABYZZ, ALLOWMETOSHOWU1, Domariocarios, rrrrgggbbbclat, ParkingLocator, DonkeyDonkey999, TheOneWhoKnocks1312, FluentCastle1352, `0x8c33013f…` and `0x82be522b…` (new). `accounts.csv` lists them with their profile date and activity counts; `transactions.csv` lists every transfer used; `graph.json` and `graph.mmd` draw them.

## 8. Limits

- **Relay index.** Queried as recipient, `requests/v2?user=` misses same-chain orders whose fill has no hash. Example: ILOVEYOUBABYZZ's order of 10 September 2025 to `0x20bd758d…` appears in ILOVEYOUBABYZZ's own pages, not in those of `0x20bd758d…`. Every link here is therefore read from the sender's pages; a destination's pages alone undercount. The endpoint is announced as retired on 24 November 2026; the archived pages are the record.
- **Labels.** Blockscout metadata for EVM, Orb for Solana (previous note): one source each, attributions not proofs. The behaviour checks do not depend on them.
- **Polymarket data.** Reduced copies without profile fields other than the public username (`evidence/polymarket_reduced/ORIGINALS.json` lists the originals and their hashes, kept outside git). Profile creation times come from `gamma-api` `public-profile`; it returns 404 for five accounts.
- **Not traced.** Where `0x82be522b…` sent the 5,281.90 one minute later; rrrrgggbbbclat's other 21 withdrawals and its deposit of 28 February 05:33; the payers of the deposit addresses of ILOVEYOUBABYZZ (`0x08d495fb86399f37a5bda51a2f85a9e21a019ca5`), TBFMM (`0x80f4af8b526f0b6a8b70a81b192f11a464f69efc`) and `0x8c33013f…` (`0x8284600d3a6c04d29b1539209838073843052201`) on BSC; ALLOWMETOSHOWU1's other recipients; what `0x852dc1c8…` is. All WORK_LEFT.
- **Previous open leads.** `98jocp4j…` (1.7 SOL) and `CN5kywyq…` (0.9905 SOL) have no Relay order at all, and the full 84-transaction history of `98jocp4j…` touches no address of the network other than the beneficiary. No link to another Polymarket account was found through them.

## 9. Reproduction

- `scripts/collect.py`: sequential collector, one network worker (Relay pages with `relay-user`, Polymarket activity, Etherscan v2, Helius, Blockscout). Keys are read from the local pool and never written.
- `scripts/bsc.py`: BSC receipts and USDC logs from public nodes, 100 blocks per call.
- `scripts/build.py` and `scripts/netlib.py`: build `evidence/`, `transactions.csv`, `accounts.csv`, `graph.json`, `graph.mmd`.
- `verify.py`: needs only this folder and the previous note's.
