# Verification of the historical X leads (6 November 2026)

Follow-up to `../REPORT.md` (PR 36). Plan fixed before any result: `ANALYSIS_PLAN.md`, commit `15a633e`. Every figure below is reproduced by `verify.py` (19 checks, 19 pass, of which 2 recompute from the raw archive) or points to a file in `data/` or `evidence/`. Statuses: CONFIRMED (primary object, no inference), SUPPORTED (primary object plus a stated inference), UNRESOLVED, REFUTED. An address is not a person. No identity is sought or recorded.

## 1. What changed

| Lead | Status | One line |
|---|---|---|
| Cypya posted the exact top five on 16 Oct | **CONFIRMED** | Post `2111149784858042762`, 17:38:26 UTC, never edited, three days before the 2nd/3rd place markets opened |
| Cypya X account controls `0x970998da…` | **SUPPORTED** | The Polymarket profile of that address declares `xUsername: Cypya_Poly` (self-declared field) |
| Cypya announced positions already held | **CONFIRMED** | At the post, the address held all 7 ranking facts that had a market, bought 13-14 Oct |
| Jydyjyd "copied the insiders" (PR 36 wording) | **REFUTED as worded** | The visible text says he profited on Yamal "before the insiders got in"; his ledger shows a switch to Mbappé over Yamal 16 minutes before Cypya's post |
| Direct transfer between Cypya, Jydyjyd or Cypyo and the 11 | **None found** | 1,008 filtered log queries, positive control found; the only token movement is one order-book fill |
| PURE698: Iran exposure before Venezuela | **CONFIRMED**, small | 2025 Iran bets of 75 to 297 USDC, then Venezuela; lost on Iran in February 2026 |
| JamWil23 as a winning insider | **REFUTED** | Net result -5,436.40 USDC, every position closed |
| JamWil23, bravonoll and Frogensky share one Coinbase deposit address | **SUPPORTED (new)** | Three accounts, two themes (Venezuela Dec-Jan, Iran Feb), one customer deposit address `0xd1262395…` |
| "38 accounts" of @Andrey_10gwei | **37 of 38 resolved; all 37 pay one Coinbase deposit address** | `0xc5bb1be0…` has no other paying account on Polygon; pooled-service hypothesis rejected on that read |
| "$2.14M profit" | **Not reproduced** | The post's own image sums to $1,575,776.10; recomputed results of the 37: 1,516,585.57 USDC |
| cashy bought Yes before the news | **REFUTED** | 0 Yes shares at the measured repricing (06:13:22); first Yes fill 33 s after it |
| flydartball lost in June 2025 | **REFUTED** | The position ended at +256,137.07; whole account +841,375.23 with 12 losing Iran markets |
| thesecondhighlander (Car's correction) | **CONFIRMED loss**, negative control | -174,453.49 USDC, no winning bet |

## 2. Ballon d'Or 2026

### 2.1 Sources and attribution

- The X objects were archived from the public embed endpoint (`scripts/x_raw.py`): ID, author, time, `edit_control`, quoted post, media. Their sha256 are in `data/x_posts.csv` and `SHA256SUMS_RAW.txt`; the objects themselves stay outside git (third-party content). All 9 posts have an edit history equal to their own ID: never edited.
- Cypya's post (16 Oct 17:38:26 UTC) lists Kane, Mbappé, Yamal, Rodri, Messi in that order and calls it a prediction; the attached image repeats the order. The 2nd and 3rd place markets opened on 19 Oct 14:47, the 4th and 5th on 20 Oct 19:32 (Gamma `startDate`, `investigations/ballon-dor-census/sources/derived/markets.csv`). No fill on any of the 15 tracked tokens precedes its listing (`data/ballon_results.json`, `fills_before_listing: 0`).
- Attribution test: the Polymarket profile of `0x970998da056e60c707d9b1fc55cfdf3d68c252ab` (name Cypya, created 3 Jun 2026) declares `xUsername: Cypya_Poly`; that of `0x1c4cd350bce3cb791daf88ce2034de9b03318d85` (Jydyjyd, created 16 Aug 2025) declares `xUsername: Jydyjyd`. The field is set by the account owner; whether Polymarket verifies it is not documented here, hence SUPPORTED. The look-alike "Cypyo" `0xa9f4dc80…` (rank 7 of Upside's screenshot) declares no X account.
- Cypya was already in the repository: rank 9 of the 15 holders of Mbappé in Upside's screenshot, used as a non-suspect comparator (`investigations/ballon-dor-wallets/sources/evidence/screenshot_reconstruction.json`).
- Owner of Cypya's deposit wallet, `owner()` read on two nodes: `0x5756bddb45817786ece4b3b6d1d71a291dc02006`. It has 0 transactions, 0 internal transactions and 0 token transfers on Ethereum and Polygon.

### 2.2 Positions before the post (Q1)

From the event tapes (both sides of every fill, 692,519 rows, `data/ballon_focus_positions.csv`), checked against the account's own activity rows (same 7 values):

| Ranking fact | Cypya net shares at 17:38:26 | First buy (UTC) |
|---|---:|---|
| Kane wins | 4,128.66 | 13 Oct 18:38 |
| Mbappé in top 3 | 4,447.44 | 14 Oct 00:47 |
| Messi in top 5 | 1,187.82 | 14 Oct 01:08 |
| Rodri in top 5 | 2,214.81 | 14 Oct 01:09 |
| Mbappé above Yamal | 6,370.20 | 14 Oct 02:35 |
| Rodri above Messi | 584.00 | 14 Oct 22:50 |
| Kane above Yamal | 420.00 | 14 Oct 23:08 |

The post therefore announced a book the account already held. Cypya's account is an old, very active trader (22,400 activity rows). On 25 Oct, the day before the ceremony, it bought No on Mbappé 2nd and Yamal 3rd and Yamal in the head-to-head, then merged them (1,763.22, 889.90 and 4,986.96 shares; 5,062.46 more on 26 Oct 10:25), which closes part of its own ranking. It bought exact places again on 26 Oct from 20:49 UTC, after the ceremony began (20:00) and after the 17:15 site leak reported in the repository timeline. That sequence is not what full certainty would produce; it does not exclude anything either.

### 2.3 Several ranking elements before the first exact public ranking (Q2, exploratory)

Facts, tokens and the 0.60 "informative price" rule are fixed in `ANALYSIS_PLAN.md`; a fact counts for a wallet when its purchases of that token at 0.60 or less reach 100 USDC. Controls: every other wallet with 100 USDC of purchases in the listed markets before the cutoff.

| Cutoff | Controls | Controls with 0 / 1 / 2 / 3 facts | Focus wallets |
|---|---:|---|---|
| Cypya post, 16 Oct 17:38 | 1,239 | 979 / 242 / 18 / 0 | Thin, 0x86544e4dfde, brace227, Zoomman17, kraben006: 2 each (18 controls at or above); **BriardxO: 3 (no control)**; Cypya, Jydyjyd, VidenteRibeira, cookedrice, walletwallet8424, unnamed 0xa8e6: 1 |
| Upside post, 23 Oct 15:17 | 1,831 | 1,554 / 253 / 23 / 1 | kraben006 6, Cypya 5, BriardxO 5 (no control at or above), 0x86544e4dfde and brace227 3 |

Reading: before any exact ranking was public, the most "complete" informative book among all these wallets belonged to BriardxO (`0x226aca3e…`, created 2024, non-highlighted in Upside's image), not to one of the 11. The 11 were selected after the fact for holding Mbappé above Yamal, so their 1-2 facts are partly selection. Exact-place facts all come after 19 Oct by construction.

### 2.4 Who buys after each publication (Q3, exploratory)

Buy notional on each listed ranking token in the 6 hours after the event, against the same clock window on every other day from 12 to 25 October (`data/ballon_event_windows.csv`):

- After Cypya's post: Mbappé above Yamal 22,635.55 USDC from 24 buyers, rank 2 of 14 days (median day 6,388.74, top day 22,790.37). Kane winner rank 12 of 14. Top-3 and top-5 tokens near zero.
- After Jydyjyd's post: Mbappé 2nd 1,935.55 USDC, rank 1 of 6 days; other tokens middle ranks.
- After Upside's post: Kane winner 24,757.42 USDC from 38 buyers (15 first-time family buyers), rank 5 of 14; Rodri top 5 rank 1 (824.16); **exact places last** (Mbappé 2nd 167.39 and Yamal 3rd 154.90, rank 7 of 7).
- The "other publications of 22 October" were not identified from a primary source and were not tested.

The burst after Cypya's post is real but not unique. Receipts read on two nodes (`data/receipts_orderfilled.csv`) show that the fills around the post were resting bids hit by third-party sellers: Cypya at 17:21:48 (two orders, taker `0x5cd5c8d7…`) and 17:41:45 (2,500 shares, same taker), Jydyjyd at 17:21:48 and 17:22:08, walletwallet8424 at 17:22:06 and 18:52:04, BriardxO at 15:45:10, 17:21:48 and 18:52:04. A maker fill dates the match, not the order: the placing time of these bids is not on chain. Co-fills in one transaction are not a link (finding F-018 of `ballon-dor-wallets`).

### 2.5 Copy cascade (Q4)

Share of each wallet's ranking-fact purchases bought before Cypya's post (`data/ballon_results.json`, Q4): Thin-Disclaimer-Life 100 %, 0x86544e4dfde 96 %, walletwallet8424 94 %, unnamed 0xa8e6 100 %, Zoomman17 46 %, kraben006 24 %, brace227 19 %, cookedrice 60 %, VidenteRibeira 21 %; WenZhuanBuPei, OuldLm3alem and 0xdd97e6 0 % (accounts or first buys after the post). The largest early books cannot have copied the post. The later accounts are compatible with following public information, whether the post, the leaderboard or the price; the data do not tell which.

Jydyjyd's own ledger: Yamal winner Yes bought 17-20 Sep at about 0.21, sold 30 Sep at 0.423, the profit his post describes; Mbappé above Yamal from 16 Oct 17:21 (1,000 shares, before Cypya's post) and 20-21 Oct; no exact place ever; sold on 25 Oct. The visible text of his 21 Oct post does not say he copied anyone; the remainder is truncated in the embed.

### 2.6 Transfers between the new candidates and the 11 (Q5)

`scripts/q5_transfers.py`: Transfer logs of USDC.e, USDC and pUSD and TransferSingle/TransferBatch of the Conditional Tokens contract on Polygon, filtered on both ends, for 4 candidates (Cypya proxy and owner, Jydyjyd proxy, Cypyo proxy) against 24 addresses (11 proxies, 11 owner keys, unnamed 0xa8e6 and its owner), both directions; on Ethereum, USDC and USDT between Cypya's owner and the 12 owner keys. 1,008 queries. Positive control: the same query finds the known 2,210 and 2,960 USDC from brace227's key to `0x48ec106c…` (F-003).

Result: 0 direct value transfer. The 2 hits are one order-book fill, `0xedd0f88ff99495ad2c004990d20fe174b1537a14b80b6b84f1da8feb17867ed3` (18 Oct 16:09:11, logIndex 562 and 565): brace227, taker, sold 958.58 Rodri-above-Messi shares into four resting bids, two of them Cypyo's (401.52 and 500 at 0.70). Not read: Base, Arbitrum, BSC, Solana; Jydyjyd's and Cypyo's owner keys (Magic proxies, no `owner()`).

### 2.7 Eleven audited accounts and twelve in the press (Q6)

- Upside's first article (23 Oct) defines its 12 as accounts "created between 1 and 20 October" holding 264,000 USD; neither article publishes addresses. The repository's 11 are the 9 accounts highlighted in Upside's image plus the 2 named in its 27 Oct follow-up (OuldLm3alem, 0xdd97e6). OuldLm3alem was created on 22 Oct, outside Upside's own definition. The two lists are built differently; the gap of one is not an omitted account, and Upside's twelfth address is not identifiable from what it published. UNRESOLVED.
- Upside also cites two older accounts "created in August" staking 41,000 and 23,000 USD from the evening of 19 Oct. enginesinmyfactory `0xb4847aba…` (created 6 Aug 2026, first family buy 19 Oct 23:18) bought 40,858.62 USDC in the family before Upside's post: SUPPORTED for the 41,000. No single account matches 23,000: wpj `0x8a93f77d…` 27,816.75, `0xfd74d450…` 17,909.96. UNRESOLVED. enginesinmyfactory is a non-highlighted comparator in the repository's reconstruction.

## 3. Maduro and Iran candidates (@betint_ai, 3 Jan 2026)

The post lists three wallets: SBET365 `0x6baf05d1…` (already in `investigations/maduro-iran` as a "strong July account"), PURE698 `0x2a1a80e7…` (now named Qwerty09876, created 22 Mar 2025) and JamWil23 `0xfddfd657…` (created 16 Dec 2025). Full ledgers in `data/ledger_maduro_alerts.json`; result = sells + redemptions + merges - buys - splits.

- **PURE698**: May 2025, Israel acts against Iran before June Yes 75.00 (lost) and before July Yes 71.36 (redeemed 297.33); 20 Jun 2025, US military action against Iran by Monday Yes 297.34 (redeemed 1,902.66). Dec 2025, US x Venezuela engagement by 31 Dec Yes (lost, sold for 813.26) and by 15 Jan Yes, sold on 3 Jan 08:20:53 at 0.999 for 54,971.16. Feb 2026, Iran: No positions, then Yes on "by 27 February", sold at 0.0023 on 28 Feb 03:39, before the strikes. Result +36,933.71; by class Venezuela +42,771.75, Iran/Israel -5,838.04 (classes overlap on "US strikes Iran"). Funded through Relay from Ethereum `0x4fe1567f…`, itself funded by Coinbase 10; withdrawn to `0xb53640a8…`, which forwards to Coinbase 10. The claimed earlier Iran exposure is CONFIRMED; it was small and mixed.
- **JamWil23**: deposits 15,398.76, withdrawals 9,962.37, result -5,436.40, no open position. Maduro out in 2025 Yes (6,000.55 spent, sold for 895.39), Venezuela engagement by 31 Dec (lost), by 15 Jan Yes 9,962.36 shares bought 2 Jan at 0.141 and redeemed. A loss overall.
- **SBET365**: deposits 25,089.95, withdrawals 166,709.80; Venezuela +145,619.85; Khamenei out by 31 Jan Yes -4,000.00. Its Polygon exit pays `0x0e9310b9…` (LINKCS), already documented in `investigations/maduro-iran`.
- Shared services only between the three: Coinbase at both ends, Relay. Each uses its own Coinbase deposit address. No address of the eight-account network, of cluster E, F, G or H appears in their funding or exits (one hop read).

### 3.1 New: one Coinbase deposit address for three accounts

JamWil23's withdrawal address `0xd12623958b81d71e8be3fa936aed6d8c2528e992` (Ethereum) receives Polymarket withdrawals from two other accounts:

| Account | Created | Bets | Withdrawals to `0xd1262395…` (Relay orders) |
|---|---|---|---|
| Frogensky `0x51633638…` | 12 Dec 2025 | US x Venezuela engagement by 15 Dec, No, +5.08 | 18 Dec: 5.00, then 96.64 |
| JamWil23 `0xfddfd657…` | 16 Dec 2025 | Venezuela and Maduro, -5,436.40 | 3 Jan: 5.00; 4 Jan: 9,957.37 |
| bravonoll `0xab05ffa4…` | 17 Feb 2026 | US and Israel strike Iran, Yes ladder 19-28 Feb, +31,863.48 | 28 Feb 10:10: 5.00; 10:19: 42,853.47 |

Why a Coinbase deposit address and not a personal wallet: it signs only 4 transactions (nonces 0 to 3), each a transfer of its entire USDC balance to Coinbase Hot Wallet 10 within 4 to 7 minutes of a credit, and each preceded about 2 minutes earlier by an ETH gas transfer from Coinbase Hot Wallet 10 (internal transactions). That is how Coinbase sweeps customer deposit addresses (check A11). It has no label (Blockscout). Deposit addresses are issued per customer account; that practice is the exchange's and is not visible on chain.

Each account is funded by its own fresh Polygon key fed by Coinbase hot wallets (`0x7bc863e1…`, `0xb9841c57…`, `0x3d74567d…`), and each withdraws 5.00 USDC first, then the balance. Typed edges: SAME_DEPOSIT_ADDRESS (customer-specific) for the three, CORRELATED_TIMING for the habits. Status: SUPPORTED that the payouts of the three accounts were credited to one Coinbase account. Not established: who holds it, whether it is one person, any information advantage. bravonoll's February Yes ladder lost on 19-24 Feb and won on 28 Feb.

## 4. Group G and the 38 accounts (@Andrey_10gwei, 17 Mar 2026)

- Names transcribed from the post's image (`data_38_names.txt`). Exact public-search match: 27; froshoo from PR 27; the other 9 found as senders to `0xc5bb1be0…` and confirmed by their own profile names (decoderdude970, gentlequarter, gagadolls, irk77, robpat007, TouchOfGrass, gulligan784, portaj1942, scallopbucket). 37 of 38 resolved. "Anon" stays UNRESOLVED: the only exact match (`0xc07356e1…`) never pays the destination.
- 36 of the 37 were created between 22 Feb 12:02 and 25 Feb 07:23 UTC, in runs minutes apart. All 36 bought No on Iran deadlines first (median 1.1 hours after creation, range 0.3 to 12.9 hours, often at the same minute across accounts), then Yes between 27 Feb 20:49 and 23:35 UTC, the evening before the strikes; 4 to 11 markets each, almost all military. 33 withdraw once, between 2 and 9 March; froshoo twice; DimBull and wannabesedated five times, DimBull from 27 Feb (`data/g38_accounts.csv`). The 37th, flipfloppity (created Nov 2025, 348 markets, 311 non-military), does not fit the pattern but is the destination's first and largest payer (229,926.51 USDC on 5 Jan 2026).
- Recomputed results match each image figure to within about 25 USDC. Sum: 1,516,585.57 USDC for the 37, against 1,575,776.10 in the image for 38. The post's "$2.14M" is not reproduced by its own image.
- Destination `0xc5bb1be0407db7312911ec765d399d02461e411a` on Polygon, official USDC and USDC.e only: 1,984,038.17 USDC in and out, 5 Jan to 9 Mar 2026. Paying addresses: 32 list accounts directly, Relay contracts (the other 5 list accounts' Relay orders, on Polygon, Base and Arbitrum, check A13), and 2 dust senders under 0.01 USDC that imitate Coinbase 16. 9 transfers of look-alike tokens are excluded. Its gas comes from addresses labelled Coinbase Gas Supplier 3, 8, 13 and 15, and everything leaves to Coinbase 16 (1,608,438.29), Coinbase 30 (298,804.82), Coinbase 52 (57,674.00) and Coinbase 54 (19,121.06). This is a Coinbase customer deposit address (labels from one source, behaviour as in 3.1).
- Pooled deposit infrastructure: REJECTED on the Polygon read, since no Polymarket account outside the list pays this address. Arbitrum: one Relay delivery (59,863.53, arsonicscribe), forwarded to `0xa656f7d2…`, not traced. Base: not readable with the free Etherscan plan (suffix-295 58,475.75 and unfiltered009 42,142.98 arrive there by Relay).
- "All accounts belong to the same person": SUPPORTED that all 37 payouts were credited to one Coinbase account; the person behind it is UNRESOLVED.
- Comparison: group G (froshoo, suffix-295, unfiltered009, arsonicscribe) is a subset of the 38: CONFIRMED. No address shared with cluster E, the eight-account network or the three accounts of 3.1 on the reads made. The deposit side was read for 12 of the 37 only: 13 distinct funding keys, none shared.

## 5. cashy, flydartball, Car's correction

- **cashy** `0x8f42ae0a…` (profile declares `xUsername: cashyPoly`): No on "US strikes Iran by 28 Feb" bought 19 Feb and 23 Feb as the bot reported, sold 21 and 24 Feb; Yes bought 25 Feb at 0.11, sold 27 Feb; Yes bought 27 Feb 17:39-18:09 and **sold as taker on 27 Feb 21:19:47** (48,221.98 shares at 0.16, verified receipt). At the repricing measured in `investigations/maduro-iran/sources/phase10/RAPPORT_PHASE10.md` (06:13:22), cashy held 0 Yes shares of "by 28 February". First Yes fill 06:13:55, 33 s after it, a resting bid at 0.56: a bid at that price placed while the market was near 0.16 would have executed at once, so it was most probably placed after the move (inference). From the repricing to the alert, 51,038.84 USDC of Yes; the alert (06:32:48) comes 5 s after the fill at 06:32:43. Bought after the public repricing, not before. Account result +464,159.10, Iran class +426,461.58.
- **flydartball** `0x37d10ffb…`: June 2025, "US military action against Iran before July?" Yes, 807,924.82 shares held before 21 Jun (net cost 551,787.75), final +256,137.07: the 19 Jun post showed an unrealized loss. 2025-2026: 26 Iran markets, 14 winners, 12 losers (largest loss "by 27 February" -37,929.92); 359,679.08 Yes shares of "by 28 February" held before the repricing (net cost 58,567.59), built from 4 Feb. Account result +841,375.23. A large directional record on both events, with its losses; the source of its views is UNRESOLVED.
- **thesecondhighlander** `0xb500375a…` (Car's correction, image of the post): 2 bets, both lost: US strikes Iran by 9 Feb Yes -99,453.71, Trump 2024 No -74,999.78; result -174,453.49. An account publicly suspected of inside information that lost everything: a negative control for alert-driven suspicion.

## 6. Method and limits

- Raw responses outside git, `~/Projects/Polymarket-x-leads-raw-20261106/raw`, each with url, time and sha256; list in `SHA256SUMS_RAW.txt`. Copied into `evidence/` (299 files, `SHA256SUMS.txt`): receipts from both nodes, Relay records, Etherscan reads of the key addresses, labels, `owner()` reads.
- Tapes: `data-api /v2/trades?event_id=`, both sides, to 15 Sep (winner event to 25 Sep). Row counts of the smaller events equal the census of 2 Nov exactly (e.g. 16,387, 9,944, 3,412, 2,373). 14,235 rows repeat an identical key inside one transaction: market makers filling identical orders, kept.
- Receipts: publicnode and drpc, identical for 17 of 17 transactions (block hash, status, every log). Exchange logs decoded for the 2026 exchange `0xe1111800…` and the two older exchanges; the taker of each match comes from `OrdersMatched`.
- Money in Decimal from the API's decimal text; tape sizes are rounded to 0.01 share, so exact amounts come from activity rows and receipts.
- Not read: Base (free plan), BSC, Solana exits; deposit sides of 25 of the 37; activity of two heavy comparators (pup1 over 200 pages, mr.ozi stopped); Polymarket's order placement times.
- Errors caught during the work: an earlier filter on token symbols let look-alike tokens through (fixed: contract addresses); a timestamp typed by hand was wrong by 20 minutes (recomputed from the date). A3 of `verify.py` re-decodes the packaged receipts and compares.
- Order of work: the X objects, the `xUsername` fields of Cypya, Jydyjyd and Cypyo and Cypya's rank in the repository's screenshot reconstruction were read before the plan was committed (`15a633e`, 18:52 UTC); the attribution test is therefore not blind. Every other measure was computed after that commit.
- Dust rule of check A12 (under 0.01 USDC) was set after a first run flagged two such senders; both resemble Coinbase 16, one on 4+4 characters, one on 3+3.

## 7. Still open

1. Who controls the Coinbase account behind `0xc5bb1be0…`, and behind `0xd1262395…`: only Coinbase can say.
2. Whether the 36 batch accounts bought Yes on 27 Feb evening ahead of comparable buyers: needs the full Iran-market tape and a fixed comparison window.
3. Base side of `0xc5bb1be0…`, and `0xa656f7d2…` on Arbitrum.
4. Upside's twelfth account and its 23,000 USD older account.
5. The "other publications of 22 October": no primary object found.
6. flydartball's information source: nothing in the ledger separates conviction from access.
7. Deposit sides of the 25 unread accounts of the 38.
