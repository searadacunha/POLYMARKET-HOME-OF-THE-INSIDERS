# Nobel Peace Prize 2025: strict point-in-time replay, plan written before the new analyses

Written on 20 November 2026 at about 22:20 UTC, from `main` at `b6e0aa3`, before any of the computations listed under
"New analyses" was run. Committed alone, before its results.

## Question

Could the eight accounts funded by the key `0xe206961002feebd9edb152eed9b630a351874043` (table of
`investigations/followup-20261113/sources/reports/FOLLOWUP_REPORT.md`, section 1.1) have been flagged in October 2025,
before the winner was announced, by detectors that do not know the result and that use, at each moment, only what was
observable at that moment? When is the first alert, how does the group rank among the other alerts of the same night, and
what load of other alerts comes with it?

## Already established before this plan (not recomputed as new results)

- `BACKTEST_RESULTS.md`: the `phi_monitor` rule `LONELY_THIN` alerts on the account "6741" at 2025-10-09 23:00:15 UTC; the
  funder's cluster is listed from 00:50 to 03:30 UTC on 10 October. The rule was written from this night: a
  reconstruction, not a prediction.
- `research_notes/realtime-intelligence-2026-11-14/RESULTS.md`: in the frozen study of large purchases, the group class
  `C4_COFUNDED_GROUP` fires on one event of discovery, this one, at 2025-10-10 00:55:11 UTC at 0.49, and on no event of
  validation. The classes C1, C7 and R1 fire on the documented accounts, and on the same event from 14 August 2025.
- `NEGATIFS` of the agents' memory and the follow-up report: seven of the eight accounts first bought after the public
  repricing of "Machado Yes" (0.036 at 22:30, 0.39 at 23:00 UTC on 9 October 2025).

## Known gap this plan addresses

The frozen study describes each payer **as read on 14 November 2026** (code, number of transactions sent, public name
tags; `study/analysis_plan.md`, "Features and point-in-time rule"), which it states "can only remove links". A key that
became busy, a key later delegated through EIP-7702 (it then shows code), or an address tagged later, is excluded from
the group classes although it was a plain key when it paid. The pass-through rule (a key with at most 5 transactions is
followed one hop further) uses the same count read today. How many links that removed, and whether the Nobel group
stays the only `C4` event once the payer state is read at the block of each payment, is unknown.

## New analyses

### A. Payer state at the block (strict point-in-time C4 and C5)

Inputs, read-only: the frozen study's `data/funding.sqlite` (deposits, payers, hops, inflows),
`derived/funding_todo.jsonl`, `derived/entries.sqlite`, on the machine that computed them. Code: the published
`research_notes/realtime-intelligence-2026-11-14/study/code/feat_40_groups.py` (`build_links`, `classify`), imported
without modification.

Replacement of the payer description only, everything else unchanged (24-hour deposit window, `FANOUT_MAX` 10,
`BUSY_NONCE` 1,000, `PASS_THROUGH_NONCE` 5, `WINDOW` 10,000 blocks, 7-day pairing):

- `code(a, b)` = `eth_getCode(a, b - 1)` and `nonce(a, b)` = `eth_getTransactionCount(a, b - 1)` on an archive JSON-RPC
  endpoint, where `b` is the block of the payment considered (the deposit for an apparent payer, the transfer for a
  sender of swapped money or behind a pass-through key).
- plain key at `b`: `code(a, b)` empty and `nonce(a, b)` < 1,000. Public name tags are **not used**: no historical tag
  is available, so a tag read today would be information from the future.
- pass-through at `b`: plain key at `b` and `nonce(a, b)` <= 5.
- A code of exactly 23 bytes beginning with `0xef0100` is an EIP-7702 delegation: the address is an account with a key
  that has delegated its execution. It counts as code, as in the frozen rule; the number of such payers is reported.

Calls are reduced only by properties that hold on the chain: a nonce never decreases (a count under 1,000 today was
under 1,000 at every earlier block; a count of 1,000 or more at the earliest block concerned holds at every later one);
the code of a contract that is not an EIP-7702 delegation does not disappear (code found at the earliest block concerned
holds at every later one). Every other (address, block) pair is read. A failed read leaves the link `UNRESOLVED`, never
plain and never service; the number of such links is reported.

Keys that are pass-through at the block but were not read one hop further by the frozen collector (their count today
is above 5): their incoming transfers of the 10,000 blocks before are read from logs if they are 200 keys or fewer;
otherwise they are reported as unread.

Outputs: the number of links added and removed by category (tags ignored, busy today but not then, delegated today,
code at the block, new pass-through hops); strict `C4` and `C5` entries and events over the whole frozen population
(January 2025 to October 2026); whether the Nobel event is still the only `C4` event; for any other `C4` event, its
event id, alert time, entry size and number of wallets. No outcome (`labels.jsonl`, `win`) is read for this part.
Wallet addresses of events other than the documented case stay on the computing machine.

### B. The queue an analyst would have faced that night

From the frozen analytic table (`derived/analytic_table.jsonl`), class flags and alert moments only, the outcome column
never read: every entry alerted by each class (C1 to C7, R1, M1, M2, B1 to B3) with its alert moment in
[2025-10-09 21:00:00, 2025-10-10 09:00:00) UTC, separately for INFO and PUBLIC_PROCESS markets. For each class: number
of alerts, wallets and events; how many are on the eight accounts (the only step that uses their identity); rank of the
earliest alert on the eight by time; rank by entry size; the expected rank of the first of k group alerts among N under a
random order, (N + 1) / (k + 1). The same counts per day for the seven days before, as the load of other alerts.
With the strict `C4` of part A as well.

### C. Timeline of what was observable

For each of the eight accounts: first on-chain observation (first collateral received), first funding by the key and
its block, time from funding to first trade, first fill and first fill of 1,000 USD or more on the event, cumulative
cost bought on the Machado market at each of the group's fills, the last price printed before each of its first fills,
and the share of its event buying on the Machado market. Sources: the Polymarket data API (`v2/trades` of the event's
markets, `v2/activity` with an `end` bound), the CLOB price history, Polygon logs and receipts. Depth of the order book
before each fill: not archived for October 2025, reported `DATA_UNAVAILABLE`.

The first public information about the winner is the official announcement; its time is taken from the Nobel
committee's own publication. Public reporting of the price move, with its publication times, is listed apart.

### D. Verdict wording, fixed now

- `DETECTED_BEFORE_PUBLIC_REPRICING`: a detector fires on one of the eight before the first 10-minute price point of
  "Machado Yes" that meets the `phi_monitor` confirmation rule (6-hour median at 0.15 or less, then three times that
  and at least 0.10 more).
- `DETECTED_AFTER_REPRICING_BEFORE_ANNOUNCEMENT`: the earliest such alert is after that point and before the
  announcement.
- `NOT_DETECTED_BEFORE_ANNOUNCEMENT`: no detector fires on the eight before the announcement.
- In every case `NOT_A_VALIDATION`: every detector here was written after this case was known, and this case was
  selected because it ended well for those accounts. Nothing here measures precision or recall.

## What this note does not do

No outcome test of any class (C4 and C5 have no validation alert and the frozen study forbids retesting C2, C4, C5 and M3
on its data), no threshold chosen or tuned here, no change to any frozen file, no claim about who controls the accounts
or what they knew.

## Amendment 1, 20 November 2026, about 22:50 UTC, before parts B and C were computed

Part A was running; nothing of parts B and C had been computed. Two external scoring rules are added to part B as
baselines. Both are re-implemented from their published code or description, no code is copied, and both are under
permissive licences (read on 20 November 2026):

- `EXT_PC`, the pre-cutoff flag of `andy1245-rgb/PolyCrawler` (Apache-2.0): account age at most 14 days at the entry,
  at most 15 other markets traded before it, entry price at most 0.30, entry of 1,000 USD or more; flagged when the
  four hold. The original has a fifth signal and flags at four of five; the fifth is not in the frozen table, so this
  version needs all four (stated, and stricter). Computed on every entry of the night queue, from the frozen table's
  point-in-time wallet features (`age_h`, `prior_other_markets`) and the entry's price and size.
- `EXT_NN`, the 0-10 score of `NickNaskida/polymarket-insider-bot` (MIT), default thresholds of its `config.py`
  (fresh wallet under 30 days, bet over 1,000 USD, large-bet multiplier 3 over the market's mean trade size, wallet
  concentration 0.6, niche market under 50,000 USD of volume, alert at 7). Computed only on the entries of 1,000 USD or
  more on the markets of the Nobel event during the night, with the market statistics of the 24 hours before each
  entry read from the complete public tape. The wallet's concentration (largest share of its trades in one market) is
  not in the frozen table; it is bounded from below by the share of the wallet's trades on the entry's market
  (stated: this can only lower the score).

Their alerts, ranks and load are reported exactly like the other baselines. Neither rule is changed after its output
is seen.

## Amendment 2, 20 November 2026, about 22:35 UTC, after the first counts of part A, before the strict classes entered part B

No outcome is read in part A; these changes follow from its counts only.

1. A payer without code at `b - 1` may have been deployed, or delegated, in block `b` itself. Reading the code at `b - 1`
   alone would then describe a contract as a key. The description also reads `eth_getCode(a, b)` for every pair where the
   code at `b - 1` is empty and the code today is not: code at `b` makes the address a contract (or a delegated account)
   at the payment. Found because 1,615 added links came from addresses with code today; 1,614 of them are EIP-7702
   delegations today.
2. A decomposition is added, descriptive only: the same classification with code and nonce read at the block but
   today's public tags kept as an exclusion, to separate the effect of not using tags from that of the block state.
3. Keys that are pass-through at the block but whose incoming transfers were never read: 2,314 keys (3,647 pairs), above
   the 200 of the plan. They are reported as unread and not read. Reading them could only add links.
