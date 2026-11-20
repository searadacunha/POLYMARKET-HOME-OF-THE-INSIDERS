# Nobel Peace Prize 2025: could the eight accounts have been flagged before the announcement?

A replay that uses, at each moment, only what was observable at that moment. Plan and amendments in
[PLAN.md](PLAN.md), all committed before the results they govern (the times written inside PLAN.md are wrong, see
"Record of this note"). Times are UTC. An address is not a person: nothing here says who controls these accounts or
what they knew. Every table between `table:` markers is rendered from `data/` by [verify.py](verify.py), which checks it.

## Answer

**Verdict fixed in the plan: `DETECTED_BEFORE_PUBLIC_REPRICING`, qualified `NOT_A_VALIDATION`.**

- Among the detectors replayed here (the classes of the frozen study of 14 November 2026, two re-implemented external
  rules and `phi_monitor`'s `LONELY_THIN`), the first alert on one of the eight accounts is the class `C1` (a wallet with
  almost no history, funded in the 24 hours before its first purchase of 1,000 USD or more on one side of a market) on
  the account "6741", at **2025-10-09 22:45:07**, 10.25 hours before the announcement (09:00 UTC, 11:00 in Oslo) and
  15.1 minutes before the price series confirmed the public repricing of "Machado Yes" (**23:00:15**, at 0.3895, rule
  of `phi_monitor`).
- The repository's own pre-registered rule S_FRESH (Maduro and Iran file, phase 8: a taker purchase of 100 USD or more
  by a wallet 48 hours old or less with at most two earlier trades) was not replayed. By its definition it would fire on
  6741's first fill, 921.83 USD of "Machado Yes" at 0.048 at 22:42:57, two minutes earlier.
- That first alert is not a discovery. It is the 4th of **57 alerts** that `C1` raised on INFO markets during the night
  (21:00 to 09:00), on 5 events; `C1` raised 109 in the 24 hours before, 36 over the same 12 hours the night before. Out
  of sample, `C1` is under its price by 3.7 points (95 % interval -8.3 to +0.7, `NOT_SUPPORTED_EFFECT_EXCLUDED`). These
  queues are counted inside the frozen study's universe, which keeps only markets that later resolved and reached its
  volume floors: a live analyst would have received more alerts, so the counts are lower bounds and the ranks best cases.
- From 21:00 to the confirmation point, 6741 bought 94.9 % of all "Machado Yes" bought (16,879.50 of 17,780.96 USD);
  other wallets bought 458.67 USD between its first fill and that point. It was funded at 22:40:19 and its fill of
  22:45:07 that opened the `C1` entry was 1,084.77 USD of "No" on Sudan's Emergency Response Rooms at 0.67.
- The group class `C4_COFUNDED_GROUP` (a second freshly funded wallet paid by the same plain key enters the same event)
  fires at **00:55:11** on 10 October, at 0.494, 8.08 hours before the announcement and 1 hour 55 minutes after the
  repricing was confirmed. Inside the universe, that night `C4` raised exactly 8 alerts, all on the group, and none in the
  seven days before. `C4` reaches the eight only through the step that reads who sent money swapped into a deposit, a
  step the frozen study added after looking at this account; `C7`'s amount rule was chosen because an earlier rule missed
  it. On this case these classes are partly fitted, not only written after it.
- Read with each payer's state at the block of its payment instead of its state today (part A), `C4` over the whole
  frozen population (20,070 traced entries, markets with a scheduled end from January 2025 to October 2026, entries from
  1 July 2024) gives **19 alert entries on four events**, not 8 on one. The uniqueness of the Nobel group in the frozen
  study rested on information from the future: the funding keys of the three other groups were plain keys at the time.

## Timeline of the eight accounts

Recomputed by `verify.py` from `data/accounts_activity.csv`, `data/accounts_inflows.csv` and `data/machado_tape.csv`.
"Last print" is the last trade of "Machado Yes" strictly before the account's first purchase there (the data API gives no
log index: trades of one second are taken in the order of `data/machado_tape.csv`).

<!-- table:accounts -->
| Account | Funded by the key | First trade | First buy of 1,000 USD or more | First "Machado Yes" buy, last print before it | Share of its event buying on Machado |
|---|---|---|---|---|---|
| 6741 | 22:40:19 | 22:42:57, 2.6 min | 22:45:07, Sudan's Emergency Response Rooms "No" at 0.670 | 22:42:57 at 0.048, last print 0.031 | 0.62 |
| fmaduro | 00:43:33 | 00:44:43, 1.2 min | 00:55:11 at 0.494 | 00:44:43 at 0.340, last print 0.340 | 1.00 |
| trumpdeservesit | 01:04:15 | 01:07:25, 3.2 min | 01:07:25 at 0.495 | 01:07:25 at 0.495, last print 0.445 | 1.00 |
| striketheboats | 01:10:37 | 01:12:41, 2.1 min | 01:12:41 at 0.566 | 01:12:41 at 0.566, last print 0.520 | 1.00 |
| aenews0 | 01:32:27 | 01:33:47, 1.3 min | 01:33:49 at 0.652 | 01:33:47 at 0.666, last print 0.617 | 0.81 |
| madurowilllose | 01:46:17 | 01:48:33, 2.3 min | 01:48:33, Sudan's Emergency Response Rooms "No" at 0.920 | 01:54:09 at 0.650, last print 0.650 | 0.56 |
| pinkuniforms | 03:11:55 | 03:21:57, 10.0 min | 03:23:29 at 0.655 | 03:21:57 at 0.580, last print 0.632 | 1.00 |
| dirtycup | 03:26:43 | 03:29:17, 2.6 min | 03:29:19 at 0.677 | 03:29:17 at 0.700, last print 0.660 | 1.00 |
<!-- /table:accounts -->

For every account, the first collateral it received on Polygon in the blocks read (from about 04:34 on 9 October) is
the transfer from the key `0xe206961002feebd9edb152eed9b630a351874043`. On "Machado Yes" the group's net cost reached
178,034.89 USD at its last fill there, 03:41:17 UTC; its gross buying, 212,874.44 USD, was 46 % of all buying of that
outcome since 21:00 (`data/group_exposure.csv`). At its first two fills (22:42:57 and 22:46:49), 6741 alone was 68 % and
85 % of that buying.

## First alert on the eight, by detector

Ranks are by time inside the frozen universe (best cases, see above); under a random order, the expected rank of the
first of k group alerts among N is (N + 1) / (k + 1) (`data/queue.json`).

<!-- table:detectors -->
| Detector | First alert on the eight | Price | Rank in the night's queue of that detector |
|---|---|---|---|
| `C1` fresh funded bet (frozen study) | 22:45:07 | 0.670 | 4 of 57 |
| `R1` S_FRESH replication on entries (frozen) | 22:45:07 | 0.670 | 3 of 55 |
| `EXT_PC`, four-signal flag of an external project, re-implemented (amendment 1) | 22:46:49 | 0.100 | 1 of 11 |
| `C7` heavy newcomer (frozen) | 22:57:43 | 0.300 | 1 of 15 |
| `LONELY_THIN` (`phi_monitor`, `monitoring/tests/test_replay.py`) | 23:00:15 |  |  |
| `C4` cofunded group (frozen) | 00:55:11 | 0.494 | 1 of 8 |
| `C4` cofunded group, payer state at the block (part A) | 00:55:11 | 0.494 | 1 of 8 |
| `B2` buying after a move (baseline) | 01:33:49 | 0.652 | 20 of 30 |
| `B1` size of 10,000 USD or more (baseline) | 03:23:29 | 0.655 | 3 of 7 |
<!-- /table:detectors -->

- `EXT_PC` cannot be scored on 133 of the 215 INFO entries of the night (no wallet view in the frozen table); 12 of them
  are at 0.30 or less and one comes before 22:46:49, so its rank 1 is a best case (it could be 2nd).
- `EXT_NN` was scored only on the entries of the Nobel event (40 of its 140 entries of the night; 100 have no wallet
  view, none of them before 22:46:49): first of 16 flagged inside that event, not comparable with the other ranks.
- `M1` and `M2` use thresholds fitted on discovery data through March 2026: they are not point-in-time and are left out.
- Every detector here was written after this case was known, and the case was chosen because it ended well for these
  accounts: this table reconstructs, it does not validate.

## Payer state at the block (part A)

The frozen study described each payer as read on 14 November 2026. Here the code and the number of transactions sent
are read at the block of each payment (15,962 archive reads and 4,546 reads of today's code, none left in error), and
public tags are not used, as no tag has a history:

<!-- table:partA -->
| | Frozen study | At the block, tags not used | At the block, today's tags kept |
|---|---:|---:|---:|
| Funding links | 2,441 | 3,755 | 2,561 |
| `C4` alert entries | 8 | 19 | 10 |
| `C4` events | 1 | 4 | 3 |
| `C5` alert entries | 1 | 22 | 12 |
<!-- /table:partA -->

No link is removed by the block reading; 1,314 are added: 1,194 through addresses tagged today, 74 through addresses
that have code today and had none at the payment, 46 through keys that were not yet busy. The code is read at the end of
the payment block too (amendment 2), for the 1,615 pairs where it was empty just before the block and present today:
1,519 had been delegated through EIP-7702 in that block, 1 was deployed in it, 95 still had no code after it; the
delegation may come after the payment inside the block. In all, 2,234 payers were delegated accounts at their payment.
With the rule before amendment 2 (code just before the block only), the result is the same: 5,380 links, 19 `C4` entries
on the same four events, 22 `C5`.

Only the payer description is point-in-time. Which transfers were collected one hop back, which wallets count for the
fan-out limit, and the exclusion of senders tagged Polymarket from "fresh" money still come from the frozen collection of
November 2026. The independent audit of 20 November tested two of these (removing the 15 links that depend on today's
contract status; counting fan-out only over wallets that had already entered): no change to `C4` or `C5`.

The `C4` events at the block, tags not used (`data/strict_summary.json`; wallets other than the documented accounts are
not published):

<!-- table:events -->
| Event | Alert entries | Wallets | First alert | Funding keys as read today (context only, never used by the class) |
|---|---:|---:|---|---|
| Will Biden finish his term? | 1 | 1 | 2024-07-23 10:04 | one key, delegated through EIP-7702 today, 4,609 transactions sent |
| Yoon out as president of South Korea before April? | 1 | 1 | 2025-02-26 08:37 | one key, no tag, 179,923 transactions sent |
| Nobel Peace Prize Winner 2025 | 8 | 7 | 2025-10-10 00:55 | the documented funder, 18 transactions sent |
| Fed decision in January? | 9 | 9 | 2026-01-12 14:30 | 4 keys tagged "Relay: Solver", 860,846 to 862,557 transactions sent |
<!-- /table:events -->

The Fed group is most likely not one controller: nine wallets bridged in through four keys tagged today as Relay
solvers, which had sent fewer than 1,000 transactions at the payments that link the wallets (the rule requires it) and
more than 860,000 by today. A
real-time `C4` without a historical tag source would have raised it; the frozen study excluded it only because those
keys are busy and tagged today. The keys of the Biden and Yoon groups would be services under the frozen rule applied to
today's state (busy); for the Biden key that rests only on its 4,609 transactions and an EIP-7702 delegation today, the
shape of a user's smart account rather than of a service. The Nobel funder is the only one of the four keys that is still
a key with a handful of transactions.

818 keys that were pass-through keys at the block (at most 5 transactions) were never read one hop further (2,151
pairs; 2,314 keys and 3,647 pairs under the rule before amendment 2), above the 200 of the plan. The Nobel funder is one
of them: its only collateral sender before its payments, the relayer `0x07ae8551be970cb1cca11dd7a11f47ae82e70e67` that
delivered its 249,652.41 USDC at 22:39:09, had sent 288,688 transactions at block 77,472,491 (read on 20 November), so
it is a busy key and adds no link. Reading the others could add links, and through the fan-out limit could also remove
`C4` alerts: 19 is not a bound in either direction.

## What was public

- The announcement: Friday 10 October 2025 at 11:00 CEST, 09:00 UTC (Norwegian Nobel Institute, livestream page
  <https://www.nobelpeaceprize.org/articles/nobels-fredspris-2025-livestrom-1>; press release
  <https://www.nobelpeaceprize.org/press/press-releases/nobel-peace-prize-for-2025>).
- Before it, no public item pointing to Machado was found besides the market price itself (search of news, Norwegian
  outlets and posts on 20 November 2026; every page opened is dated after the announcement). The pages were not
  archived by this note.
- After it: reports of the overnight move and of a probe from 10 October (The Block, 16:21 UTC); the institute's
  director spoke of likely espionage on 11 to 13 October (AFP, CBS, Bloomberg Government); on 29 to 30 January 2026 the
  institute said the name had leaked illegally, most likely through a digital intrusion (VG via TT and ORF). That
  statement concerns the leak, not any account here.

## Contradiction with the follow-up of 13 November

The column "Nobel buys before 09:00 UTC" of `investigations/followup-20261113/sources/reports/FOLLOWUP_REPORT.md`
(table 1.1) is lower than the buying here (for dirtycup 25,496.43 against 68,373.81 USD). Its tool reads the data API's
`v2/trades?user=` without `taker_only=false`, so it counts taker trades only: on 20 November the same request returns
25,496.43 USD for dirtycup by default and 68,373.81 USD with `taker_only=false`. The figures here include maker fills.
The follow-up is not modified.

## Missing data

- Order-book depth before each fill: not archived for October 2025, `DATA_UNAVAILABLE`. Prices are those printed.
- The data API's delay in October 2025 is unknown; observable time is taken as the block time (optimistic for any
  detector that reads the API). Alert times are those of the fill that meets the class: a live engine raises them later.
  On 14 November 2026 the engine stored a large fill 4 to 8 seconds after its block and the API showed it a median 3
  seconds after (`research_notes/realtime-intelligence-2026-11-14/LIVE_RUN.md`); reading a wallet's history and funding
  adds more. The 15-minute lead of the first alert over the repricing point leaves room for that, not for a delay of
  many minutes.
- The night queues come from the frozen universe: markets that never resolved or stayed under its volume floors are
  missing (lower bounds, best-case ranks).
- Public tags have no history: the strict variant does not use them, and the tables show both readings.
- 818 pass-through keys not read one hop further; 133 night entries not scorable by `EXT_PC`, 100 event entries by
  `EXT_NN`.
- Profile creation times are never used: a profile is not observable before its wallet acts on chain.

## What this does not show

- No precision, recall or edge: every detector was written after this case, two of them partly fitted to it, and `C4`
  has no alert on the validation events of the frozen study, strict variant included (not retested here, as that study
  requires).
- Being first in a night's queue says nothing about the next case: the three other strict `C4` groups are funded by keys
  that are busy or tagged today, and the first of them is, as far as today's data show, a delegated user key.
- Nothing about who controls the eight accounts or what they knew.

## Record of this note

The times written in PLAN.md ("about 22:20", "about 22:50", "about 22:35") are wrong; the commit times are
authoritative: plan `74aa7d4` 22:00:35, amendment 1 `642d4f7` 22:05:34, amendment 2 `a1e8e2d` 22:21:35, first results
`5576159` 22:29:47 UTC on 20 November 2026. The order of work (archive reads from 22:03, the night queue from 22:07, the
reads at the end of the block from 22:21) follows the commits. After the independent audit started, the tape builder was
corrected to keep identical rows of one page, which are distinct fills (the API has no log index): no figure of the
account table changed, market buying since 21:00 moved from 465,579.81 to 465,726.87 USD. The audit's findings and their
fixes are listed in the pull request.

## Reproduce

Offline, from the published files: `python3 -I research_notes/nobel-strict-replay-2026-11-20/verify.py`. From the
sources, see [README.md](README.md).
