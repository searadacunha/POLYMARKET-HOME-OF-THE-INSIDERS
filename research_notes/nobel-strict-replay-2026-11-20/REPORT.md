# Nobel Peace Prize 2025: could the eight accounts have been flagged before the announcement?

A replay that uses, at each moment, only what was observable at that moment. Plan and amendments in
[PLAN.md](PLAN.md), all committed before the results they govern. Times are UTC. An address is not a person: nothing
here says who controls these accounts or what they knew.

## Answer

**Verdict fixed in the plan: `DETECTED_BEFORE_PUBLIC_REPRICING`, qualified `NOT_A_VALIDATION`.**

- The first alert that any detector of this repository raises on one of the eight accounts is the class `C1` (a wallet
  with almost no history, funded in the 24 hours before a first purchase of 1,000 USD or more) on the account "6741",
  at **2025-10-09 22:45:07**, 10.25 hours before the announcement (09:00 UTC, 11:00 in Oslo) and 15.1 minutes before the
  price series confirmed the public repricing of "Machado Yes" (**23:00:15**, at 0.3895, rule of `phi_monitor`).
- That alert is not a discovery. It is the 4th of **57 alerts** that `C1` raised on INFO markets during the night
  (21:00 to 09:00), on 5 events; `C1` had raised 109 the day before. Out of sample, `C1` is under its price by 3.7 points
  (frozen study of 14 November 2026, `NOT_SUPPORTED_EFFECT_EXCLUDED`).
- The account's own buying is what moved the price: it was funded at 22:40:19, bought "Machado Yes" at 0.048 at
  22:42:57 (921.83 USD, under the 1,000 USD entry size), then 1,084.77 USD of "No" on Sudan's Emergency Response Rooms at
  0.67 at 22:45:07, the fill that opens the `C1` entry.
- The group alert `C4_COFUNDED_GROUP` (a second freshly funded wallet paid by the same plain key enters the same event)
  fires at **00:55:11** on 10 October, at 0.494, 8.08 hours before the announcement and 1 hour 55 minutes after the
  repricing was confirmed. That night `C4` raised exactly 8 alerts, all on the group; in the seven days before, none.
- Read with each payer's state at the block of its payment instead of its state today (part A), `C4` over the whole
  frozen population (January 2025 to October 2026, 20,070 traced entries) gives **19 alert entries on four events**, not
  8 on one: the Nobel group, and three groups whose funding keys look like services from what is known today. The
  uniqueness of the Nobel group in the frozen study rested on information from the future.

## Timeline of the eight accounts

Recomputed by `verify.py` from `data/accounts_activity.csv`, `data/accounts_inflows.csv` and `data/machado_tape.csv`.
"Last print" is the last trade of "Machado Yes" strictly before the account's first purchase there (the data API gives no
log index: trades of one second are taken in the order of `data/machado_tape.csv`).

| Account | Funded by the key | First trade | First buy of 1,000 USD or more | First "Machado Yes" buy, last print before it | Share of its event buying on Machado |
|---|---|---|---|---|---|
| 6741 | 22:40:19 | 22:42:57, 2.6 min later | 22:45:07, Sudan ERR "No" at 0.67 | 22:42:57 at 0.048, last print 0.031 | 0.62 |
| fmaduro | 00:43:33 | 00:44:43, 1.2 min | 00:55:11 at 0.494 | 00:44:43 at 0.34, last print 0.340 | 1.00 |
| trumpdeservesit | 01:04:15 | 01:07:25, 3.2 min | 01:07:25 at 0.495 | 01:07:25 at 0.495, last print 0.445 | 1.00 |
| striketheboats | 01:10:37 | 01:12:41, 2.1 min | 01:12:41 at 0.566 | 01:12:41 at 0.566, last print 0.520 | 1.00 |
| aenews0 | 01:32:27 | 01:33:47, 1.3 min | 01:33:49 at 0.652 | 01:33:47 at 0.666, last print 0.617 | 0.81 |
| madurowilllose | 01:46:17 | 01:48:33, 2.3 min | 01:48:33, Sudan ERR "No" at 0.92 | 01:54:09 at 0.65, last print 0.650 | 0.56 |
| pinkuniforms | 03:11:55 | 03:21:57, 10.0 min | 03:23:29 at 0.655 | 03:21:57 at 0.58, last print 0.632 | 1.00 |
| dirtycup | 03:26:43 | 03:29:17, 2.6 min | 03:29:19 at 0.677 | 03:29:17 at 0.70, last print 0.660 | 1.00 |

For every account, the first collateral it received on Polygon in the blocks read (from about 05:00 on 9 October) is
the transfer from the key `0xe206961002feebd9edb152eed9b630a351874043`. The group's cumulative cost on "Machado Yes" reached 178,034.89 USD at
its last fill there, 03:41:17 UTC, 38 % of all buying of that outcome since 21:00 (`data/group_exposure.csv`); at its
first two fills (22:42:57 and 22:46:49), 6741 alone accounted for 68 % and 85 % of that buying.

## First alert on the eight, by detector

| Detector | First alert on the eight | Price | Rank in the night's queue of that detector |
|---|---|---|---|
| `C1` fresh funded bet (frozen study) | 22:45:07 | 0.67 | 4 of 57 |
| `R1` S_FRESH replication (frozen) | 22:45:07 | 0.67 | 3 of 55 |
| `EXT_PC`, re-implemented four-signal flag of an external project (amendment 1) | 22:46:49 | 0.10 | 1 of 11 |
| `EXT_NN`, re-implemented 0-10 score of an external bot (amendment 1, event markets only) | 22:46:49 | 0.10 | 1 of 16 flagged |
| `C7` heavy newcomer (frozen) | 22:57:43 | 0.30 | 1 of 15 |
| `LONELY_THIN` (`phi_monitor`, `monitoring/tests/test_replay.py`) | 23:00:15 | | |
| `C4` cofunded group, frozen and strict | 00:55:11 | 0.494 | 1 of 8 |
| `B2` buying after a move (baseline) | 01:33:49 | 0.652 | 20 of 30 |
| `B1` size of 10,000 USD or more (baseline) | 03:23:29 | 0.655 | 3 of 7 |

`EXT_NN` could be scored on 40 of the 140 entries of the event that night (100 have no wallet view in the frozen table).
Ranks are by time; under a random order, the expected rank of the first of k group alerts among N is (N + 1) / (k + 1)
(`data/queue.json`). Every detector here was written after this case was known, and the case was chosen because it ended
well for these accounts: this table reconstructs, it does not validate.

## Payer state at the block (part A)

The frozen study described each payer as read on 14 November 2026. Reading the code and the number of transactions sent
at the block of each payment (15,962 archive reads and 4,546 reads of today's code, none left in error), and not using public tags, which have no
history:

| | Frozen study | At the block, tags not used | At the block, today's tags kept |
|---|---:|---:|---:|
| Funding links | 2,441 | 3,755 | 2,561 |
| `C4` alert entries | 8 | 19 | 10 |
| `C4` events | 1 | 4 | 3 |
| `C5` alert entries | 1 | 22 | 12 |

No link is removed by the block reading; 1,314 are added: 1,194 through addresses tagged today, 74 through addresses
that have code today and had none at the payment, 46 through keys that were not yet busy. The 1,615 pairs where the code
was empty just before the payment but present today were read again at the end of the payment block (amendment 2): 1,519
had been delegated through EIP-7702 in that very block, 1 was deployed in it, 95 still had no code after it.

The `C4` events at the block, tags not used (`data/strict_summary.json`; wallets other than the documented accounts are
not published):

| Event | Alert entries | First alert | What the funding keys are, as read today (context only, never used by the class) |
|---|---:|---|---|
| Will Biden finish his term? | 1 | 2024-07-23 10:04 | one key, code today, 4,609 transactions sent |
| Yoon out as president of South Korea before April? | 1 | 2025-02-26 08:37 | one key, 179,923 transactions sent, no tag |
| Nobel Peace Prize Winner 2025 | 8 | 2025-10-10 00:55 | the documented funder, 18 transactions sent |
| Fed decision in January? | 9 | 2026-01-12 14:30 | four keys tagged "Relay: Solver", 860,846 to 862,557 transactions sent |

The Fed group is the clearest false group: nine wallets bridged in through Relay solvers that had just been put into
service and had sent fewer than 1,000 transactions at the time. A real-time `C4` without a historical tag source would
have raised it; the frozen study excluded it only because those keys are busy and tagged today. The Nobel funder is
the only one of the four that is still a key with a handful of transactions. 818 keys that were pass-through keys at the
block (at most 5 transactions) were never read one hop further (2,151 pairs, above the 200 of the plan): reading them
could only add links.

## What was public

- The announcement: Friday 10 October 2025 at 11:00 CEST, 09:00 UTC (Norwegian Nobel Institute, livestream page
  <https://www.nobelpeaceprize.org/articles/nobels-fredspris-2025-livestrom-1>; press release
  <https://www.nobelpeaceprize.org/press/press-releases/nobel-peace-prize-for-2025>).
- Before it, no public item pointing to Machado was found besides the market price itself (search of news, Norwegian
  outlets and posts on 20 November 2026; pages opened are dated after the announcement).
- After it: reports of the overnight move and of a probe from 10 October (The Block, 16:21 UTC); the institute's
  director spoke of likely espionage on 11 to 13 October (AFP, CBS, Bloomberg Government); on 29 to 30 January 2026 the
  institute said the name had leaked illegally, most likely through a digital intrusion (VG via TT and ORF). That
  statement concerns the leak, not any account here.

## Missing data

- Order-book depth before each fill: not archived for October 2025, `DATA_UNAVAILABLE`. Prices are those printed.
- The data API's delay in October 2025 is unknown; observable time is taken as the block time (optimistic for any
  detector that reads the API).
- Public tags have no history: the strict variant does not use them, and the table above shows both readings.
- 818 pass-through keys not read one hop further; 100 event entries without a wallet view for `EXT_NN`.
- Profile creation times are never used: a profile is not observable before its wallet acts on chain.

## What this does not show

- No precision, recall or edge: every detector was written after this case, and `C4` has no alert on the validation
  events of the frozen study (not retested here, as that study requires).
- Being first in a night's queue says nothing about the next case: three of the four strict `C4` events are, as far as
  today's data show, services.
- Nothing about who controls the eight accounts or what they knew.

## Reproduce

Offline, from the published files: `python3 -I research_notes/nobel-strict-replay-2026-11-20/verify.py`. From the
sources, see [README.md](README.md).
