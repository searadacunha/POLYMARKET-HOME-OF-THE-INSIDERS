# Example portfolios, checkable transaction by transaction

Two worked examples built by the scripts of this folder. Every row carries the Polygon transaction hash and the block time (UTC), so it can be checked on any block explorer (`https://polygonscan.com/tx/<hash>`). No outcome label was read to build them.

## 1. One wallet, one market: what the tape shows and what it cannot show

- Wallet (proxy): `0x7789806c754eb0af4c3abeb026c218b4ba78f823`
- Market: `0xad1b0c00056e2f29ac47f2b410a91f2dda57181d5c01257f6efa395089805558`, "Andrew Tate guilty of human trafficking in 2024?" (Gamma version `v1`, neg-risk False, fees enabled False)
- Tape: `tapes2.sqlite`, status `ok` (complete from the market's first fill), last fill 2025-01-01 07:09:26 UTC. Every one of the market's 3107 transactions passes the conservation check (`BALANCED`).
- Activity feed (`/v2/activity`, fetched 2026-11-17T09:49:44Z, sha256 `3b34c89925333810b33f2e6238c41ea0b32293b6bc41d8ed8320b950dbbbe940`): 34 TRADE rows and 8 MERGE rows, nothing unmapped. The wallet's TRADE rows match its tape fills on all 31 (transaction, side, outcome) keys, 0 mismatches.

Reproduce: `python3 -I scripts/example_portfolio.py --tapes ../../../tapes2.sqlite --cid 0xad1b0c00056e2f29ac47f2b410a91f2dda57181d5c01257f6efa395089805558 --wallet 0x7789806c754eb0af4c3abeb026c218b4ba78f823 --meta data/gamma_meta.jsonl --out out/example --activity out/example/activity_0x7789806c_0xad1b0c00.json`

Partition: every observation is in 2024, so `EXCLUDED_PERIOD`; the example is outside TRAIN, VALID and TEST.

Columns: **flows** = YES / NO from fills only (tape); **X** = YES minus NO, identical in both readings (asserted at every row); **lo (tape)** = proven lower bound on inventory from the tape, assuming no transfer; **inventory (tape + activity)** = flows once the MERGE rows are applied (still assuming no ERC-1155 transfer, status BOUNDED for that reason).

| as of (UTC) | event | tx | flows YES / NO (tape) | X | x status | lo (tape) | inventory YES / NO (tape + activity) |
|---|---|---|---|---|---|---|---|
| 2024-01-18 23:16:10 | BUY YES 300 @ 0.1200 | `0x5dbf1ce0e36c4f3e099a3249dbd160675d6e54e3e42c168c2da729a292b259ed` | 300.00 / 0.00 | 300.00 | OBSERVABLE | 300.00 / 0.00 | 300.00 / 0.00 |
| 2024-01-20 05:37:32 | BUY NO 800 @ 0.8900 | `0xdc6a599505b4b7ebdf8b64f9c8445db50c341f12327ce2f57a7d9a334e8d8d9f` | 300.00 / 800.00 | -500.00 | OBSERVABLE | 0.00 / 500.00 | 300.00 / 800.00 |
| 2024-01-21 13:05:25 | BUY NO 778 @ 0.8400 | `0x1dbdd62183b7bbf524cb02d0137fb95a81615f4541542e45a0c8d44a6c473689` | 300.00 / 1578.00 | -1278.00 | OBSERVABLE | 0.00 / 1278.00 | 300.00 / 1578.00 |
| 2024-01-21 19:18:36 | MERGE set 300 | `0x9b881d5e0bc184ce29fd542e14603c9041c48363faff3bbddf8a173e1122ffcd` | 300.00 / 1578.00 | -1278.00 | OBSERVABLE | 0.00 / 1278.00 | 0.00 / 1278.00 |
| 2024-01-24 11:11:45 | BUY NO 500 @ 0.8400 | `0x8555ab03b8a872e88f10f73d32d388f5917f5e95d6d1c38413bead084f913cfa` | | | | | |
|  | BUY NO 1500 @ 0.8400 | `0x8555ab03b8a872e88f10f73d32d388f5917f5e95d6d1c38413bead084f913cfa` | 300.00 / 3578.00 | -3278.00 | OBSERVABLE | 0.00 / 3278.00 | 0.00 / 3278.00 |
| 2024-01-26 22:33:03 | BUY YES 2000 @ 0.1600 | `0x972fffbbce936b0671aa315e2e33f663a70ed7c77575eb736a8071aa6da2937c` | | | | | |
|  | BUY YES 2000 @ 0.1600 | `0x972fffbbce936b0671aa315e2e33f663a70ed7c77575eb736a8071aa6da2937c` | 4300.00 / 3578.00 | 722.00 | OBSERVABLE | 722.00 / 0.00 | 4000.00 / 3278.00 |
| 2024-01-26 23:50:47 | MERGE set 3278 | `0x1c5ca06fa1067ba4530d74a3e0d2d0809d84a330d7a20951c41503979798b9a0` | 4300.00 / 3578.00 | 722.00 | OBSERVABLE | 722.00 / 0.00 | 722.00 / 0.00 |
| 2024-02-09 23:59:19 | BUY NO 5000 @ 0.8300 | `0x103a85d3ded461fb5ddc976759953bbcec1fbb50cd4c7b4cb964b6612573c1de` | 4300.00 / 8578.00 | -4278.00 | OBSERVABLE | 0.00 / 4278.00 | 722.00 / 5000.00 |
| 2024-02-10 04:18:09 | MERGE set 722 | `0xb238882587d426caf6b73a9ea6f43033c449882df963d2bb4b5e71ff69cc3816` | 4300.00 / 8578.00 | -4278.00 | OBSERVABLE | 0.00 / 4278.00 | 0.00 / 4278.00 |
| 2024-02-11 04:27:11 | BUY YES 1.5 @ 0.1700 | `0x2170fbb81ed9f0283692e21258fed8145938dc3ea493ad55e9fb1fc614d46944` | 4301.50 / 8578.00 | -4276.50 | OBSERVABLE | 0.00 / 4276.50 | 1.50 / 4278.00 |
| 2024-02-12 10:26:32 | BUY YES 181.81 @ 0.1700 | `0x5b57b35bcd0fc99f622b7f9b0a583572b3edfbe4ff1684b2cbf06876e287bf2b` | 4483.31 / 8578.00 | -4094.69 | OBSERVABLE | 0.00 / 4094.69 | 183.31 / 4278.00 |
| 2024-02-12 14:28:36 | MERGE set 183.31 | `0xe4c7ea7ad60d169ddae3d1b6d59ff5a9ca87396ba9b87383728c076b12cab98c` | 4483.31 / 8578.00 | -4094.69 | OBSERVABLE | 0.00 / 4094.69 | 0.00 / 4094.69 |
| 2024-02-15 01:23:35 | BUY YES 2500 @ 0.1700 | `0x74fcb73d4d8309dcd24a95475a010031beeb209a8fa3e95ea0061a8ff97d0919` | 6983.31 / 8578.00 | -1594.69 | OBSERVABLE | 0.00 / 1594.69 | 2500.00 / 4094.69 |
| 2024-02-15 01:33:15 | MERGE set 2500 | `0xdaf437dbd755627f374d6fcc63375076bae60ea663f37301295a87705b939ba5` | 6983.31 / 8578.00 | -1594.69 | OBSERVABLE | 0.00 / 1594.69 | 0.00 / 1594.69 |
| 2024-02-15 01:54:20 | SELL NO 1594.69 @ 0.8300 | `0x9ea258ffbb74d0dd8cf5f51f895a4a366b031f49f90d080ea8bf67d7b03f7e79` | 6983.31 / 6983.31 | 0.00 | OBSERVABLE | 0.00 / 0.00 | 0.00 / 0.00 |
| 2024-03-02 22:44:35 | BUY YES 2500 @ 0.1600 | `0xb3ee7d3b933e055a762080578bf3250170ae243734329ae083d05bafe373461e` | 9483.31 / 6983.31 | 2500.00 | OBSERVABLE | 2500.00 / 0.00 | 2500.00 / 0.00 |
| 2024-03-02 22:55:23 | BUY YES 1274 @ 0.1500 | `0xda9fc6858076acee090c221bf55e02bc53ded35d3396c29416f5e92921d11b10` | 10757.31 / 6983.31 | 3774.00 | OBSERVABLE | 3774.00 / 0.00 | 3774.00 / 0.00 |
| 2024-03-02 22:58:18 | BUY YES 500 @ 0.1500 | `0x560ef2181c2283e758a5be7479590922deb7ae8e06516b821121e309ab9597a9` | 11257.31 / 6983.31 | 4274.00 | OBSERVABLE | 4274.00 / 0.00 | 4274.00 / 0.00 |
| 2024-03-02 22:58:42 | BUY YES 1226 @ 0.1500 | `0x8e22ae324a2e1010a7e52d71aecb0e1d8a19d863f94bdf7f9c58386bc2590ea3` | 12483.31 / 6983.31 | 5500.00 | OBSERVABLE | 5500.00 / 0.00 | 5500.00 / 0.00 |
| 2024-03-03 14:33:50 | BUY YES 2500 @ 0.1500 | `0x99740924556a78ce2b991a2b79df25fc90a07709fa91aae76f4a1e479286f764` | 14983.31 / 6983.31 | 8000.00 | OBSERVABLE | 8000.00 / 0.00 | 8000.00 / 0.00 |
| 2024-03-12 01:05:35 | SELL YES 6000 @ 0.1400 | `0x1aa04e781fcfdb849a6832aa300e143d965f646d743894a202ced1fd8ec88237` | 8983.31 / 6983.31 | 2000.00 | OBSERVABLE | 2000.00 / 0.00 | 2000.00 / 0.00 |
| 2024-03-12 08:30:00 | SELL YES 11.33 @ 0.1500 | `0x1e68a2b8ad84341b7210e153bf33b9093055cdb137fabb2f877cb218b0a7ae15` | 8971.98 / 6983.31 | 1988.67 | OBSERVABLE | 1988.67 / 0.00 | 1988.67 / 0.00 |
| 2024-03-23 04:41:22 | BUY YES 1500 @ 0.1600 | `0x882bb46a4bce38299313eb56ae530bdfde248342f9c0668e558e588ff35a23cd` | 10471.98 / 6983.31 | 3488.67 | OBSERVABLE | 3488.67 / 0.00 | 3488.67 / 0.00 |
| 2024-04-16 09:13:24 | BUY YES 22.7273 @ 0.1200 | `0x1c2119fc099e775245a9d5d5ed7d5d0676f743f6977f19bd87e8fac852d227a8` | 10494.71 / 6983.31 | 3511.40 | OBSERVABLE | 3511.40 / 0.00 | 3511.40 / 0.00 |
| 2024-04-28 19:04:27 | BUY NO 5000 @ 0.8600 | `0xbbeecfcf7ad7343da40dbe1adc7f1cc1dcf2a5eb3495321b685b27053c3a7798` | 10494.71 / 11983.31 | -1488.60 | OBSERVABLE | 0.00 / 1488.60 | 3511.40 / 5000.00 |
| 2024-04-28 21:46:46 | MERGE set 3511.4 | `0x0534a76a658b0e9948e65590d8d87a0b229626872f08a1cf3779947e4518fba2` | 10494.71 / 11983.31 | -1488.60 | OBSERVABLE | 0.00 / 1488.60 | 0.00 / 1488.60 |
| 2024-05-01 18:02:19 | SELL NO 1488.6 @ 0.7729 | `0xf0f0d02dc7bc6116f33af73049bae04a2423d0305f08f3a216c99a0d3ad077ef` | 10494.71 / 10494.71 | -0.00 | OBSERVABLE | 0.00 / 0.00 | 0.00 / 0.00 |
| 2024-05-11 18:16:56 | BUY YES 10.52 @ 0.1800 | `0x8195a9b3c35c373089276c46dabb4e1ccea39383568d138dcf95ec097abca4f4` | 10505.23 / 10494.71 | 10.52 | OBSERVABLE | 10.52 / 0.00 | 10.52 / 0.00 |
| 2024-05-15 12:53:39 | BUY NO 38.74 @ 0.8000 | `0x490100f14aa81eef280bc2ffc0444b0c316d05314e8ad6ab3ba36b58eaa5866f` | 10505.23 / 10533.45 | -28.22 | OBSERVABLE | 0.00 / 28.22 | 10.52 / 38.74 |
| 2024-05-15 20:38:29 | MERGE set 10.52 | `0x0056e1623d9f0196cccb23ee4b672c8c042bf74b942ba54f544baab34ce5618e` | 10505.23 / 10533.45 | -28.22 | OBSERVABLE | 0.00 / 28.22 | 0.00 / 28.22 |
| 2024-05-17 21:33:11 | BUY NO 1 @ 0.8000 | `0x6969fa5bf4491a9b3fb1a687d3f73b8a1777bbdef973314b531cddb41f58beef` | 10505.23 / 10534.45 | -29.22 | OBSERVABLE | 0.00 / 29.22 | 0.00 / 29.22 |
| 2024-05-18 17:47:46 | BUY NO 12.5 @ 0.8000 | `0x6539fa0ea13a6280a3bbd04bb94a442e57f09443b18945c95b39257bb794f3ee` | 10505.23 / 10546.95 | -41.72 | OBSERVABLE | 0.00 / 41.72 | 0.00 / 41.72 |
| 2024-05-22 07:54:46 | BUY NO 5 @ 0.8000 | `0xbb2d8b412e7ebfa89828bbfb6fd116cbb807c45d594edefd70fe930d3998e56b` | 10505.23 / 10551.95 | -46.72 | OBSERVABLE | 0.00 / 46.72 | 0.00 / 46.72 |
| 2024-05-24 22:30:28 | BUY YES 500 @ 0.1700 | `0xa40eaf53122ad43f4ea9bc1ea3a360a6f009be4b76665005d12795b61c40072c` | 11005.23 / 10551.95 | 453.28 | OBSERVABLE | 453.28 / 0.00 | 500.00 / 46.72 |
| 2024-05-25 02:42:38 | MERGE set 46.7227 | `0x0a60878934615baabf108cee465ef746432ca30b546a169276bcaec6d78e5ac7` | 11005.23 / 10551.95 | 453.28 | OBSERVABLE | 453.28 / 0.00 | 453.28 / 0.00 |
| 2024-06-03 11:44:50 | BUY YES 900 @ 0.1400 | `0xe6e6b67af08f608f1b8d39a5dfefe12bd4abce6269d052b114bc3b982cc65701` | 11905.23 / 10551.95 | 1353.28 | OBSERVABLE | 1353.28 / 0.00 | 1353.28 / 0.00 |
| 2024-06-20 02:37:39 | SELL YES 1352.78 @ 0.1400 | `0x3f6adfe8e522baff64331663d36be4e32994c9a0faf2f6ef3228d095392459b1` | 10552.45 / 10551.95 | 0.50 | OBSERVABLE | 0.50 / 0.00 | 0.50 / 0.00 |
| 2024-07-16 06:46:06 | BUY YES 900 @ 0.1100 | `0x38f09901a373e5fb7731bfa6349c031b0140502046b3d73ced5876a3de8b01eb` | | | | | |
|  | BUY YES 500 @ 0.1200 | `0x38f09901a373e5fb7731bfa6349c031b0140502046b3d73ced5876a3de8b01eb` | 11952.45 / 10551.95 | 1400.50 | OBSERVABLE | 1400.50 / 0.00 | 1400.50 / 0.00 |
| 2024-09-28 00:52:17 | SELL YES 1400.49 @ 0.0400 | `0xb602410e7630d1931285afc8f166eed1d2770bf7128a31aa89c350082904f1ca` | 10551.96 / 10551.95 | 0.01 | OBSERVABLE | 0.01 / 0.00 | 0.01 / 0.00 |

Hourly windows (only those with a class other than NONE), class from the tape alone and with the activity feed:

| window start (UTC) | tape only | tape + activity |
|---|---|---|
| 2024-01-20 05:00:00 | DIRECTIONAL_ADD | DIRECTIONAL_ADD |
| 2024-01-21 13:00:00 | DIRECTIONAL_ADD | DIRECTIONAL_ADD |
| 2024-01-21 19:00:00 | NONE | C_TECHNICAL |
| 2024-01-24 11:00:00 | DIRECTIONAL_ADD | DIRECTIONAL_ADD |
| 2024-01-26 22:00:00 | A_TRUE_INVERSION | A_TRUE_INVERSION |
| 2024-01-26 23:00:00 | NONE | C_TECHNICAL |
| 2024-02-09 23:00:00 | A_TRUE_INVERSION | A_TRUE_INVERSION |
| 2024-02-10 04:00:00 | NONE | C_TECHNICAL |
| 2024-02-12 14:00:00 | NONE | C_TECHNICAL |
| 2024-02-15 01:00:00 | C_HEDGE_REBALANCE | C_HEDGE_REBALANCE |
| 2024-03-02 22:00:00 | D_UNVERIFIED_NO_RETENTION | DIRECTIONAL_ADD |
| 2024-03-03 14:00:00 | D_UNVERIFIED_NO_RETENTION | DIRECTIONAL_ADD |
| 2024-03-12 01:00:00 | C_HEDGE_REBALANCE | C_HEDGE_REBALANCE |
| 2024-03-23 04:00:00 | D_UNVERIFIED_NO_RETENTION | DIRECTIONAL_ADD |
| 2024-04-28 19:00:00 | A_TRUE_INVERSION | A_TRUE_INVERSION |
| 2024-04-28 21:00:00 | NONE | C_TECHNICAL |
| 2024-05-01 18:00:00 | C_HEDGE_REBALANCE | C_HEDGE_REBALANCE |
| 2024-05-15 20:00:00 | NONE | C_TECHNICAL |
| 2024-05-25 02:00:00 | NONE | C_TECHNICAL |
| 2024-06-03 11:00:00 | D_UNVERIFIED_NO_RETENTION | DIRECTIONAL_ADD |
| 2024-06-20 02:00:00 | C_HEDGE_REBALANCE | C_HEDGE_REBALANCE |
| 2024-07-16 06:00:00 | D_UNVERIFIED_NO_RETENTION | DIRECTIONAL_ADD |
| 2024-09-28 00:00:00 | C_HEDGE_REBALANCE | C_HEDGE_REBALANCE |

What the example shows:

- **X is the same in both readings at every instant.** Eight MERGE events (invisible in the tape) change the
  inventory but never X.
- **The tape overstates inventory.** On 2 March 2024 the tape still shows 6,983 NO held while the wallet buys YES, so
  the tape alone reads `D_UNVERIFIED_NO_RETENTION` (YES accumulation with NO apparently kept). The activity feed shows
  that the NO had been merged away: the wallet held 0 NO, and the window is an ordinary `DIRECTIONAL_ADD`. Five such windows change class once merges are visible. This is why D is never reported as verified from fills alone.
- **Merges show up as `C_TECHNICAL`** windows (protocol events, no directional trade).
- **`A_TRUE_INVERSION` is the same in both readings** (26 January, 9 February, 28 April 2024): X changes sign by more
  than 500 payout dollars, which merges cannot cause.

## 2. Nested deadlines (EXPLORATORY, Iran cohort): reading NO-then-YES across deadlines

Exploratory only: the Iran cohort never enters a rate, a test, TRAIN, VALID or TEST. Built by `scripts/example_ladder_iran.py` from each wallet's own fills (`/v2/trades?user=`, `taker_only=false`) and activity feed (`/v2/activity?user=`, fetched 2026-11-17), and the Gamma event `us-strikes-iran-by` (65 markets). The family is limited to the deadlines the wallet traded and is proven by `prove_ladder` (same rules text and question once dates are masked, cumulative 'by' wording). REDEEM rows are applied (a deadline that resolved while the wallet still traded burns that position). Limits: counterparty rows were not fetched, so no conservation check (every reading carries `TX_UNCHECKED`); transfers are not covered. Completeness check: for each wallet, its 28 February fills from the per-wallet fetch match the complete 28 February tape transaction by transaction (35 of 35 wallets, 0 mismatches).

On the complete 28 February tape, 35 of the 36 cohort wallets bought NO before YES on that market (20 in the archived band; the frozen study corrected it to 35/36). Read across every deadline they traded, their hourly windows classify as:

| class | windows |
|---|---|
| DIRECTIONAL_ADD | 506 |
| B_INTERVAL_PACKAGE | 102 |
| C_HEDGE_REBALANCE | 77 |
| C_TECHNICAL | 64 |
| NONE | 59 |

No window of these 35 wallets reads `A_TRUE_INVERSION` once each deadline's redemption is applied.

One of them, `0x4ec2f11d2893eb1bc3bab7449910540c93adf7ec` (8 deadlines traded, 5 redemptions before its last fill). Windows other than NONE, with the payoff shape at the end of the window (payout dollars per world minus the minimum; worlds of deadlines already resolved are impossible by then, their entries are kept for the algebra only):

| window start (UTC) | class | shape over: `<= 2026-02-22`, `(2026-02-22, 2026-02-23]`, `(2026-02-23, 2026-02-24]`, `(2026-02-24, 2026-02-25]`, `(2026-02-25, 2026-02-26]`, `(2026-02-26, 2026-02-27]`, `(2026-02-27, 2026-02-28]`, `(2026-02-28, 2026-03-01]`, `> 2026-03-01` | first tx |
|---|---|---|---|
| 2026-02-22 14:00 | DIRECTIONAL_ADD | 0 / 1,203 / 1,203 / 1,203 / 1,203 / 1,203 / 1,203 / 1,203 / 1,203 | `0x10b87c0f4a18aeda0aa50545d9e9b793e59dead36bfaa45a93e4a6c3e61345b4` |
| 2026-02-22 15:00 | DIRECTIONAL_ADD | 0 / 7,676 / 13,606 / 13,606 / 13,606 / 13,606 / 13,606 / 13,606 / 13,606 | `0x096ffa3b0ed2db0c8bc33aa8d9ed5d3c256df5704b40903d0ce2c21c882623e3` |
| 2026-02-22 18:00 | DIRECTIONAL_ADD | 0 / 8,492 / 14,422 / 14,422 / 14,422 / 14,422 / 14,422 / 14,422 / 14,422 | `0x81b0f9a9cdbca3db9b8582812de05e438365be7ad79f9091f32c515bde0bb9fa` |
| 2026-02-22 20:00 | DIRECTIONAL_ADD | 0 / 8,492 / 15,524 / 15,524 / 15,524 / 15,524 / 15,524 / 15,524 / 15,524 | `0x59d65674ec066ff2adbf341d852df23c96fb18973edde4ca4587cd21ff193f65` |
| 2026-02-23 08:00 | C_TECHNICAL | 0 / 0 / 7,032 / 7,032 / 7,032 / 7,032 / 7,032 / 7,032 / 7,032 | `0x9c2c5771f48f6fd04ae4f3e74062a27f851a186c027e5582c6d99b0a64048988` |
| 2026-02-23 11:00 | DIRECTIONAL_ADD | 0 / 0 / 10,265 / 10,265 / 10,265 / 10,265 / 10,265 / 10,265 / 10,265 | `0xe8718782ca2e20658d9c6dc05cdba54daeb8d6a181a338a28918b076c978d2e4` |
| 2026-02-23 20:00 | DIRECTIONAL_ADD | 0 / 0 / 10,265 / 11,955 / 11,955 / 11,955 / 11,955 / 11,955 / 11,955 | `0x0beb353c5f3a93f01e1bc08f719d10b6725328f508a2fac6bd39fc1ffabf5d45` |
| 2026-02-23 21:00 | DIRECTIONAL_ADD | 0 / 0 / 10,265 / 11,955 / 13,203 / 14,402 / 14,402 / 14,402 / 14,402 | `0x1dc6aa8272d75fa676fa1f6b9da1bf1a6fe65c7741018dfd025f62e1ba377ccb` |
| 2026-02-23 22:00 | DIRECTIONAL_ADD | 0 / 0 / 10,265 / 13,441 / 14,689 / 15,888 / 15,888 / 15,888 / 15,888 | `0xd7adb48599e03d8e9c255ecf863d3fef172c27a0c49946e8a325796fafd70b42` |
| 2026-02-24 10:00 | C_HEDGE_REBALANCE | 0 / 0 / 0 / 3,176 / 4,424 / 5,623 / 6,300 / 6,300 / 6,300 | `0x74c42da022ad309eb7346609e2e5ef23684cba513f2cc3930c15c12f40ef1e19` |
| 2026-02-24 15:00 | DIRECTIONAL_ADD | 0 / 0 / 0 / 3,176 / 6,979 / 8,178 / 8,855 / 8,855 / 8,855 | `0x38497c279a0fe1420a16f170f9678a68bdc7d27a2593212594a3f7ae7107e141` |
| 2026-02-24 17:00 | DIRECTIONAL_ADD | 0 / 0 / 0 / 3,176 / 6,979 / 8,178 / 8,855 / 10,267 / 10,267 | `0x1f174de15dcab124604fab5122f749a864c761e3b2058040f0c8296a03b7fd61` |
| 2026-02-24 20:00 | DIRECTIONAL_ADD | 0 / 0 / 0 / 4,895 / 8,698 / 9,897 / 11,807 / 13,219 / 13,219 | `0x2e32b8d388e7c746e0f23ae1fdaad1388c70a31098b11ba25ad1e19aee4b482d` |
| 2026-02-24 21:00 | DIRECTIONAL_ADD | 0 / 0 / 0 / 8,147 / 11,950 / 13,149 / 15,059 / 16,471 / 16,471 | `0x39c659d46727e48ce4e3398e6c992cb1d470549048b8b436a6d1e0b36629cee1` |
| 2026-02-25 08:00 | C_TECHNICAL | 0 / 0 / 0 / 0 / 3,803 / 5,002 / 6,912 / 8,324 / 8,324 | `0x6d57510812891ebd6cda971ae0c06c3efc3d6f6f6aad754e0ba7e2dbf2719f1a` |
| 2026-02-25 10:00 | DIRECTIONAL_ADD | 0 / 0 / 0 / 0 / 5,045 / 6,392 / 8,418 / 9,830 / 9,830 | `0xbfe89498785bd1a76be8f43a5c9ed2ee33255eeb5f606ca01801d21e00e21895` |
| 2026-02-25 19:00 | DIRECTIONAL_ADD | 0 / 0 / 0 / 0 / 6,410 / 8,413 / 10,439 / 11,851 / 11,851 | `0x1447ea6611fb6779548ee83d636396c3510439b1a2f918a0d8edb1875c13544a` |
| 2026-02-25 20:00 | DIRECTIONAL_ADD | 0 / 0 / 0 / 0 / 6,410 / 9,548 / 11,574 / 14,379 / 14,379 | `0xad9aa5e9f441b9470bc947a7e25ff88706c57e9810abf34f93c5ef4cbeb1d4f0` |
| 2026-02-25 21:00 | DIRECTIONAL_ADD | 0 / 0 / 0 / 0 / 6,410 / 9,548 / 12,266 / 15,071 / 15,071 | `0x90a92e247bee369997fb285ee69f738f27be12cc6e416271d5fdfcc05ada0876` |
| 2026-02-25 22:00 | DIRECTIONAL_ADD | 0 / 0 / 0 / 0 / 6,410 / 10,823 / 13,541 / 16,346 / 16,346 | `0x7246a9202eca00cc0db649769c3464f2344d3b808a4ef80df0cff3561201085d` |
| 2026-02-26 09:00 | C_TECHNICAL | 0 / 0 / 0 / 0 / 0 / 4,849 / 7,567 / 10,372 / 10,372 | `0x195c74e3f45769e26e6224533d8778ae20cf9ee4d6870b54a6839ede1fdca1a4` |
| 2026-02-26 23:00 | DIRECTIONAL_ADD | 0 / 0 / 0 / 0 / 0 / 8,765 / 11,483 / 14,288 / 14,288 | `0x4b3d93f497cd8fc524ff97a2a1e70980e16bac75ecd6ad764c009c272553288a` |
| 2026-02-27 00:00 | DIRECTIONAL_ADD | 0 / 0 / 0 / 0 / 0 / 13,865 / 15,888 / 15,888 / 15,888 | `0x34ee7268625b13caaf0f1aa3764813468e5a01c066d69ee8b0a5ad2eeafadf23` |
| 2026-02-27 09:00 | C_TECHNICAL | 0 / 0 / 0 / 0 / 0 / 0 / 2,023 / 2,023 / 2,023 | `0x455c8f30c9860626fd054b1fbefe992a9d2942ad0547dfcaf42d1f6b92116510` |
| 2026-02-27 21:00 | B_INTERVAL_PACKAGE | 8,699 / 8,699 / 8,699 / 8,699 / 8,699 / 8,699 / 10,722 / 1,298 / 0 | `0x8fb97a1189f6ab89d2c402072e789d56b090f9640d77b53d82dbe735660a4104` |
| 2026-02-27 23:00 | B_INTERVAL_PACKAGE | 9,320 / 9,320 / 9,320 / 9,320 / 9,320 / 9,320 / 11,343 / 1,298 / 0 | `0xcb81af07c5dde48830d611d2d2986c8000feb230f741dc720f4ca848cbfea405` |
| 2026-02-28 02:00 | DIRECTIONAL_ADD | 13,656 / 13,656 / 13,656 / 13,656 / 13,656 / 13,656 / 15,103 / 2,405 / 0 | `0x196eb42a22368dfbb40f2be00ad8705383a5c011dacde8d8f4ea384cdc5d9f66` |
| 2026-02-28 03:00 | DIRECTIONAL_ADD | 31,936 / 31,936 / 31,936 / 31,936 / 31,936 / 31,936 / 32,691 / 2,405 / 0 | `0x1a0a61060c74d2b3f3a10749fade4752fd9354e03b6d79e1407412017cdc3bc3` |
| 2026-02-28 04:00 | DIRECTIONAL_ADD | 32,691 / 32,691 / 32,691 / 32,691 / 32,691 / 32,691 / 32,691 / 2,405 / 0 | `0x01c9a51f0542bc807e3e240091d23d1c4fa3121c4ff530c6daee2cec5d073ec7` |
| 2026-02-28 05:00 | DIRECTIONAL_ADD | 45,750 / 45,750 / 45,750 / 45,750 / 45,750 / 45,750 / 45,750 / 2,405 / 0 | `0x08f412d0cadd189d91b6f8c6191d0b8af2a15ddcb9070196c73f7ee81aa5f48c` |
| 2026-02-28 06:00 | DIRECTIONAL_ADD | 55,630 / 55,630 / 55,630 / 55,630 / 55,630 / 55,630 / 55,630 / 4,642 / 0 | `0x228a8fc0b5c0af6087766e05f8a561aa597c84afeeb7b14d7c65ecdad0cc2208` |

Redemptions in its activity feed:

| time (UTC) | market | shares | tx |
|---|---|---|---|
| 2026-02-23 08:12 | US strikes Iran by February 22, 2026? | 8,492 | `0x9c2c5771f48f6fd04ae4f3e74062a27f851a186c027e5582c6d99b0a64048988` |
| 2026-02-24 10:49 | US strikes Iran by February 23, 2026? | 10,265 | `0x74c42da022ad309eb7346609e2e5ef23684cba513f2cc3930c15c12f40ef1e19` |
| 2026-02-25 08:00 | US strikes Iran by February 24, 2026? | 8,147 | `0x6d57510812891ebd6cda971ae0c06c3efc3d6f6f6aad754e0ba7e2dbf2719f1a` |
| 2026-02-26 09:09 | US strikes Iran by February 25, 2026? | 6,410 | `0x195c74e3f45769e26e6224533d8778ae20cf9ee4d6870b54a6839ede1fdca1a4` |
| 2026-02-27 09:15 | US strikes Iran by February 26, 2026? | 13,865 | `0x455c8f30c9860626fd054b1fbefe992a9d2942ad0547dfcaf42d1f6b92116510` |
| 2026-03-02 09:50 | 0xdc4b9ecbfa | 4,265 | `0x80099724f1d3669215a53b4fb541b1161dbd7ee0c48eef907cb8aee62cea4599` |
| 2026-03-02 09:50 | US strikes Iran by March 1, 2026? | 4,642 | `0x80099724f1d3669215a53b4fb541b1161dbd7ee0c48eef907cb8aee62cea4599` |
| 2026-03-02 09:50 | US strikes Iran by February 28, 2026? | 50,988 | `0x80099724f1d3669215a53b4fb541b1161dbd7ee0c48eef907cb8aee62cea4599` |

Reading:

- From 22 to 27 February the wallet holds NO on the upcoming deadlines (the largest on the next day's), and redeems
  each one the morning after its deadline passes without a strike (`C_TECHNICAL` windows). The position is "no strike
  before the coming deadlines", rolled forward day by day. These are directional NO bets, not reversals.
- On the evening of 27 February it holds NO on "by 27 February" (2,023 shares) and buys YES on "by 28 February": the
  window reads `B_INTERVAL_PACKAGE`, the payoff peaks on the interval (27 Feb, 28 Feb].
- On 28 February between 02:00 and 06:00 UTC it buys about 50,000 YES on "by 28 February" (the shape on worlds up to
  28 February rises from about 9,300 to 55,630), plus 4,642 YES on "by 1 March". These windows read `DIRECTIONAL_ADD`.
- Nothing in this history is a NO position on the same deadline turned into a YES position on that deadline: the
  NO-then-YES order seen on the 28 February market alone is read here, deadline by deadline, as rolled NO bets on
  earlier days followed by YES on 28 February. Descriptive only, on a pre-selected cohort: no p-value, no comparison
  group, and the sample's own ladders (2 proven) are too few to say how common this is elsewhere.

