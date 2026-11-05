# New findings, 5 November 2026: the cluster E network

Full detail, tables, limits and levels are in [REPORT.md](REPORT.md). Each figure is recomputed offline by `verify.py`.

## 1. Eleven more Polymarket accounts are financially linked to cluster E

- **Established:** TBFMM, ILOVEYOUBABYZZ, ALLOWMETOSHOWU1, Domariocarios, rrrrgggbbbclat, ParkingLocator, DonkeyDonkey999, TheOneWhoKnocks1312, FluentCastle1352 and two accounts without username (`0x8c33013f39b98b3a784f7718ce8a7947db6b59fa`, `0x82be522b4c2936ee10129239cef501f8ba2bcf36`) either exchanged funds with cluster E accounts or withdrew to the same customer-specific destinations.
- **Decisive evidence:** Relay orders read from each sender's own pages, matched to the account's Polymarket WITHDRAWAL or DEPOSIT rows by hash or by exact amount within seconds, plus Polygon and BSC receipts.
- **Consequence:** cluster E is a network of at least 18 accounts; some of them have traded since October 2024.

## 2. Direct transfers between accounts

- **Established:**
  - TBFMM paid BlueElephant666 1,523 USDC.e on 19 January 2026: the three transactions are both WITHDRAWAL rows of TBFMM and DEPOSIT rows of BlueElephant666.
  - On 13 January 2026, TBFMM (32) and ILOVEYOUBABYZZ (2,073) each paid DonkeyDonkey999 directly, again with matching hashes.
  - TBFMM paid oveiStheair 4,950.47 USDC.e on 15 February 2026 through oveiStheair's own BSC deposit address; these are oveiStheair's only deposits.
  - ILOVEYOUBABYZZ funded ALLOWMETOSHOWU1's first deposit on 10 September 2025, five minutes after the profile was created; Domariocarios paid ALLOWMETOSHOWU1 9,999.999995 on 10 June 2026.
  - aaamsaasa paid two other accounts in June and July 2026.
- **Consequence:** two of the four payers of the Solana beneficiary were funded by the same account, TBFMM.

## 3. The shared exits are customer accounts

- **Established:**
  - `0x519fa16e9897132b7633f634b76306a327839e06`, called a transit wallet until now, is a **Binance customer deposit address**: gas from Binance: Deposit Funder 1, every inflow swept to Binance. Eight accounts withdrew about 289,457 to it.
  - `0x9063493a4233006be654da772ef4dc38720cac55` is a **Crypto.com customer deposit address** used by TBFMM and TheOneWhoKnocks1312.
  - `0xa6c221448af73af8350291c5cdcd877b39683766` is an EIP-7702 wallet that receives only from six accounts of the network and Binance, and sends everything to one address.
- **Consequence:** the network's money ends in at least three exchange accounts (Binance, Bybit, Crypto.com) whose holders the exchanges know.

## 4. Two exchange round trips

- **Established:**
  - 14 January 2026: 4,940.68219 USDC deposited into the Bybit account of the previous note; 88 seconds after Bybit's sweep, Bybit Hot Wallet 6 pays exactly 1 USDC less to TBFMM's Solana deposit address.
  - 28 February 2026, 05:25 UTC: ILOVEYOUBABYZZ pays 26,243 USDC into the Binance deposit address; within 30 minutes Binance hot wallets fund the deposit addresses of SemiconductorIT, Domariocarios and yellowtop1, which then buy Yes.
- **Limit:** an exchange pays all its customers from the same hot wallets. Timing and exact amounts support, but do not prove, the same customer.

## 5. Behaviour

- Six accounts created within 43 minutes on 4 February 2026, three within 34 minutes on 15 February.
- In June 2025, three of the new accounts bought Yes on "Israel military action against Iran by Friday?" at 0.10 to 0.17 during the day before the strikes and sold at 0.995 or more after midnight UTC.
- These are exploratory observations, noticed after the links.

## What this does not establish

- **Common control.** One operator is the simplest reading, not a demonstration. The holders of the Binance, Bybit and Crypto.com accounts are not known.
- **Inside information.** Not demonstrated. The rarity test frozen in `PLAN_RARITY.md` is still collecting.
