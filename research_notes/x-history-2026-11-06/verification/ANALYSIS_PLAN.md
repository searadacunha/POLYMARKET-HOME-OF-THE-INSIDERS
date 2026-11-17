# Verification plan for the X leads (written before any result is computed)

Written 2026-11-06, after the raw X objects were archived and while the Ballon d'Or event tapes were downloading, before any of the measures below was computed. It makes `../REPLAY_PROTOCOL.md` concrete; it does not replace it. Any change after the first result is an amendment, dated, appended at the end, with its reason.

## Status labels

- **CONFIRMED**: read from a primary object (archived X embed, Polygon receipt read on two nodes, Polymarket API row matched to an on-chain log) and needing no inference.
- **SUPPORTED**: one primary source plus an inference that has a stated failure mode (for example a self-declared profile field).
- **UNRESOLVED**: the test could not be run, or ran and does not separate the hypotheses.
- **REFUTED**: a primary source contradicts the claim.

A shared exchange, Relay, solver, gas payer, batch redemption or similar amount is typed `SAME_SERVICE` and never counts as a link between owners.

## Ballon d'Or 2026

Events (UTC, from archived X objects unless stated): E1 Cypya post 2026-10-16 17:38:26; E2 Jydyjyd post 2026-10-21 14:25:48; E3 Upside post 2026-10-23 15:17:49 (repository timeline). "Other publications of 22 October" are tested only if a primary object is found; otherwise listed as not tested.

Final ranking (UEFA, 26 Oct): Kane, Mbappé, Yamal, Rodri, Messi.

**Ranking facts (fixed list).** A purchase "supports" a fact when it buys the outcome token that pays only if the fact is true:

| Fact | Markets (event id) | First available |
|---|---|---|
| F_W Kane wins | winner Kane Yes (48361) | before October |
| F_MY Mbappé above Yamal | 1105364 Mbappé | 29 Sep |
| F_RM Rodri above Messi | 1105369 Rodri | 29 Sep |
| F_KY Kane above Yamal | 1105379 Kane | 29 Sep |
| F_T2M Mbappé in top 2 | 1189431 Mbappé Yes | 14 Oct |
| F_T3Y / F_T3M Yamal / Mbappé in top 3 | 811117 Yes | Aug |
| F_T5R / F_T5M Rodri / Messi in top 5 | 811116 Yes | Aug |
| F_P2 Mbappé 2nd, F_P3 Yamal 3rd | 1218178, 1218179 Yes | 19 Oct 14:47 |
| F_P4 Rodri 4th, F_P5 Messi 5th | 1225367, 1225368 Yes | 20 Oct 19:32 |
| F_MM Mbappé above Messi, F_YM Yamal above Messi | 1226675, 1226676 | 20 Oct 23:10 |

A fact is **informative** for a purchase only if the fill price is at most 0.60 (the market did not already treat it as near certain).

**Q1 holdings before E1.** For the 11 audited accounts, Cypya `0x970998da…`, Cypyo `0xa9f4dc80…`, Jydyjyd `0x1c4cd350…` and the unnamed `0xa8e64a3c…`: net shares per token at E1 from the event tapes (both sides of every fill), checked against each wallet's own `/v2/activity`.

**Q2 anticipation.** Per wallet, number of distinct ranking facts supported by informative purchases of at least 100 USDC notional before E1, before 19 Oct 14:47 and before E3. Control population: every other wallet with at least 100 USDC of purchases in the listed men's markets before the same cutoff. Report the focus wallets' counts against the control distribution (rank, share of controls at or above). Exploratory: no p-value is read as evidence of private information.

**Q3 who buys after each event.** For each event and each ranking-fact token already listed, buy notional and number of distinct buying wallets in [E, E+6 h). Placebo windows: the same 6-hour clock window on every other day from 12 to 25 October on which the token was listed. Report the event window's rank among placebo windows. Also report first-time family buyers in each window.

**Q4 cascade.** For the focus wallets, share of each wallet's ranking-fact notional bought before E1, E1 to E3, after E3; and whether exact-place purchases precede or follow the event in which the same order was already public. A purchase of an exact-place token cannot precede its market listing; the analysis checks it.

**Q5 transfers.** Polygon ERC-20 and native transfers (Etherscan v2, chain 137) of the Cypya, Cypyo and Jydyjyd proxies and their owners, matched against the proxies and owners of the 11 accounts and `0xa8e64a3c…`. Only DIRECT_VALUE edges between these sets count. Decisive transactions are re-read on two RPC nodes.

**Q6 eleven or twelve.** Reconcile the press count (Upside, 23 and 27 Oct) with the repository list by name and address; a numerical difference alone is not an omitted account.

**X-to-wallet attribution.** Test: the `xUsername` field of the Polymarket public profile at the address, and the X embed of the post. Self-declared, therefore at most SUPPORTED.

## Maduro / Iran candidates

PURE698 `0x2a1a80e7…`, JamWil23 `0xfddfd657…` (and SBET365 `0x6baf05d1…`, listed in the same post): full `/v2/activity` from first row; window 2025-03-01 to 2026-02-28 reported separately. Markets are classed by fixed title keywords: Iran, Israel, Khamenei, Tehran, Hormuz (Iran/Israel); Venezuela, Maduro, Caracas (Venezuela); "US strike", "US military", "invade" (US engagement). Per condition: buys, sells, redemptions, merges, splits, then payout at resolution; losing expiries kept. Funding and withdrawals: DEPOSIT and WITHDRAWAL rows, Relay requests, Polygon transfers; counterparties compared with the eight-account group, groups E, F, G, H and the PR 27 network list.

## Group G and the 38 accounts

Names are transcribed from the image of the archived post (`2034030676589351244`). Each name is resolved by an exact, case-insensitive match in Gamma public search; ambiguous or missing names stay unresolved. For each resolved proxy: profile creation time, activity, withdrawals and their recipients (activity rows, Relay requests). Test of a pooled deposit address: senders to `0xc5bb1be0…` on Polygon (and, where the read is available, Base and Arbitrum), counted as within or outside the 38. Common ownership is not claimed from a shared recipient; it would need a direct transfer or a common signer.

## cashy, flydartball, thesecondhighlander (Car's correction)

cashy `0x8f42ae0a…`: fill times of its Iran trades from activity and the tape, compared with the alert (06:32:48) and the repository's public-news times. flydartball and thesecondhighlander: address resolved by exact public-search match, full activity, cash-flow result per market including losses. thesecondhighlander is a negative control: an account publicly called an insider whose bet lost.

## Integrity

Raw responses are archived outside git with sha256; the derived tables, scripts and an index of hashes go in this directory. Money is computed from API decimal strings with `Decimal`. Every count states its denominator.
