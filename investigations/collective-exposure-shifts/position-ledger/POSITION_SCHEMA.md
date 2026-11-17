# Position schema: point-in-time exposure ledger

Mission 3 of 7 for `collective-exposure-shifts`. This folder adds a ledger; it does not change the frozen study
(`../PROTOCOL.lock`, `../analysis_plan.md`, `../scripts/`, `../results/` are untouched), the original tapes or the
main README. No outcome field is used or stored in this folder.

Code: `scripts/ledger.py` (engine), `scripts/run_ledger.py` (partitioned, resumable run over the tapes),
`scripts/fetch_meta.py` (Gamma metadata), `scripts/example_portfolio.py` (worked example).
Tests: `tests/test_ledger.py` (synthetic cases and edge cases, `python3 -I tests/test_ledger.py`).

## 1. Event (one row of the ledger)

| Field | Meaning |
|---|---|
| `ts` | block time of the event, Unix seconds (from the source; the tape gives `timestamp`) |
| `seen_ts` | first time the record was observable to us; defaults to `ts`. A snapshot at T uses an event only if `ts <= T` **and** `seen_ts <= T` |
| `wallet` | the address the source attributes the event to: the Polymarket **proxy wallet** for tape and activity rows. Never merged with any other address (section 6) |
| `cid` | condition id |
| `kind` | `BUY`, `SELL` (directional fills); `SPLIT`, `MERGE`, `REDEEM`, `CONVERT_OUT`, `CONVERT_IN`, `TRANSFER_IN`, `TRANSFER_OUT`, `REWARD`, `FEE` (protocol or technical events, not directional trades) |
| `oi` | outcome index: 0 = YES (first token), 1 = NO. Required for fills, redemptions and transfers |
| `qty` | shares (tokens), always >= 0; the sign comes from `kind` |
| `price` | USDC per share for fills, in [0, 1] |
| `usdc`, `fee` | cash leg when the source gives it; `None` means unknown, never zero |
| `tx`, `seq`, `src` | transaction hash, source order, provenance (`tapes.sqlite#rowid=123`, `activity#7`) |

Refused at entry (`ChronologyError` / `ValueError`, never applied): missing, negative or NaN timestamp,
`seen_ts < ts`, negative or NaN quantity, fill price outside [0, 1], unknown kind, fill without an outcome index.
Rows for a market absent from the market table are quarantined as `UNKNOWN_MARKET`.

Order: `(ts, tx, seq, wallet, kind, oi, qty)`. Same input in any order gives the same ledger (tested). The order
inside one second is not observable (the tape has no log index); nothing depends on it, because running minima are
taken at second boundaries (tested).

Token effect on the event's own condition (`token_delta`):

| kind | YES | NO | cash |
|---|---|---|---|
| BUY YES / BUY NO | +q / 0 | 0 / +q | −q·price |
| SELL YES / SELL NO | −q / 0 | 0 / −q | +q·price |
| SPLIT | +q | +q | −q |
| MERGE | −q | −q | +q |
| REDEEM (oi) | −q on oi | | +usdc |
| REDEEM (no outcome, as in the activity feed) | burns all YES held | burns all NO held | +usdc |
| CONVERT_OUT (neg-risk) | | −q | +usdc |
| CONVERT_IN (neg-risk) | +q | | |
| TRANSFER_IN / OUT (oi) | ±q on oi | | |
| REWARD, FEE | | | usdc |

## 2. Transaction conservation check

For every `(tx, condition)` group of fills, the change in YES supply must equal the change in NO supply:
a regular match moves tokens between wallets (0, 0), a mint match creates a set (+m, +m), a merge match destroys one
(−m, −m). Verdicts (`reconcile_tx`):

- `BALANCED`: kept as is (two identical rows that balance are kept: identical fills inside one tx are possible);
- `DUPLICATES_DROPPED`: balanced only after collapsing exact duplicate rows; the extra rows go to quarantine
  (`DUPLICATE_ROW`), counted;
- `FEE_IN_SHARES`: fee-enabled market (Gamma `feesEnabled`), gap explained by a buyer fee paid in shares, implied
  rate `gap / Σ min(p, 1 − p)·shares` over the short side's BUY rows in (0, `MAX_FEE_RATE` = 0.10]; the tape already
  shows the shares the payer received, so positions stand; every implied rate is reported;
- `MULTI_TIMESTAMP`: rows of one tx with different timestamps (one block cannot): flagged like `UNBALANCED`;
- `UNBALANCED`: a fill is missing or doubled; rows kept, every wallet in the tx gets `TX_UNBALANCED` from that time,
  which makes its readings `UNKNOWN`;
- `NO_TX`: no hash, cannot be checked; counted, and the wallets get the soft reason `TX_UNCHECKED`.

As-of rule: a transaction lies in one block, so with `seen_ts = ts` it is either wholly visible at T or not at all.
When some event is seen after it happened, the snapshot at T is computed on a ledger rebuilt from the events seen by
T, so a counterparty row that arrives later can neither vouch for nor taint an earlier reading (tested).

## 3. Snapshot as of T (`Ledger.snapshot(wallet, cid, T)`)

Three readings, never mixed:

**Observable** (exact, from what the source shows): `flow_yes`, `flow_no` (signed sums of covered events),
`x_yes_equiv = flow_yes − flow_no`, `cash_flow` (`None` if any cash leg is unknown), and
`proven_unobserved_inflow = max(0, −min_t flow)` per outcome: shares sold before they were ever bought in the source,
which proves an inflow the source cannot see (a split, a transfer, a conversion or pre-tape history).

**Directional status `x_status`**. `X = q_YES − q_NO` is unchanged by `SPLIT` and `MERGE` (both legs move together),
so it is readable from fills alone. It is moved by transfers and, on neg-risk markets, by conversions.

- `EXACT`: every class that moves X is covered.
- `OBSERVABLE`: exact unless an event of a class the source cannot see happened; the class is named in `reasons`
  (`TRANSFERS_NOT_COVERED`, `CONVERSIONS_NOT_COVERED`, `UNOBSERVED_INFLOW_PROVEN`, `NEG_RISK_FLAG_UNKNOWN`).
- `UNKNOWN`: a hard reason applies: `INITIAL_POSITION_UNKNOWN` (tape does not reach the market's first fill),
  `TX_UNBALANCED`, `NEGATIVE_INVENTORY_WITH_FULL_COVERAGE` (every inflow class covered and the inventory still goes
  negative: an event is missing).

Soft reasons (status stays `OBSERVABLE`): `TRANSFERS_NOT_COVERED`, `CONVERSIONS_NOT_COVERED` (neg-risk only),
`NEG_RISK_FLAG_UNKNOWN`, `REDEMPTIONS_NOT_COVERED` (burns tokens, only after resolution), `UNOBSERVED_INFLOW_PROVEN`,
`TX_UNCHECKED`. Coverage can be set per market and, for a wallet whose activity feed was read, per wallet
(`wallet_coverage`).

**Inventory bounds** `inventory = {status, lo, hi, lo_assumes}`:

- `EXACT` (`lo = hi = flows`) only when trades, splits/merges, transfers, redemptions and (on neg-risk markets)
  conversions are all covered, history is complete and no hard reason applies.
- `BOUNDED`, every inflow class covered but not redemptions: `lo = 0`, `hi = flows` (redemption only burns).
- `BOUNDED` with fills only: true `q_i = flow_i + s + u_i`, `s` = net split minus merge (common to both legs),
  `u_i` = unobserved transfers or conversions. With `u = 0`, `q >= 0` forces `s >= −min(flow_yes, flow_no)`, so
  `lo = (max(X, 0), max(−X, 0))` (the directional part) and `lo_assumes` says so. Unconditionally only `q >= 0` is
  proven. `hi = None` (no upper bound: any number of splits is possible) unless splits, transfers and, on neg-risk
  markets, conversions are covered.
- `UNKNOWN`: `lo = hi = None`.

Nothing is imputed: a missing class leaves the matching component unknown or bounded, with its reason.

`fees`: `UNKNOWN` when the market has fees enabled (Gamma `feesEnabled`) or the flag is unknown and the source
has no fee field (the tape has none), else `NONE_OR_COVERED`.

## 4. Families and payoff vectors

A family is a set of conditions whose tokens pay in a common set of mutually exclusive worlds.

| Type | Worlds | YES of member i pays in | NO of member i pays in | Proof required |
|---|---|---|---|---|
| `binary` | YES, NO | YES | NO | none |
| `exclusive` (neg-risk event) | each sampled member, plus `OTHER` unless the family is proven complete | world i | every world except i | Gamma `negRisk` true for every member |
| `ladder` (nested deadlines D1 < … < Dk) | `<= D1`, `(D1, D2]`, …, `> Dk` | every interval up to Di | every interval after Di | `prove_ladder`, below |

`payoff_vector(wallet, family, T)` returns `q_flow` (payout per world implied by the wallet's flows, in payout
dollars: one share pays one dollar; not holdings), `shape = q_flow − min(q_flow)`, and `payout_lo` / `payout_hi`,
the payout per world bounded by the member inventories (`None` when unbounded). Because YES + NO of one condition pays 1 in every
world, splits and merges only add a constant vector: **the shape is observable from fills, the level is not**.
Inside a complete neg-risk event a conversion also leaves the shape unchanged (tested); when the family holds only
the sampled members (world `OTHER`), a conversion can move value to members outside it, so the reason
`CONVERSIONS_NOT_COVERED` stays on the vector. `vector_change(v0, v1)` gives `d_shape` and `d_q_flow` between two
instants.

Worked algebra (tested): one NO on D1 plus one YES on D2 gives `q_flow = (1, 2, 1)` over
(`<= D1`, `(D1, D2]`, `> D2`), shape `(0, 1, 0)`: a bet on the interval, not a reversal.

**Ladder proof (`prove_ladder`)**, all required, otherwise the family is `unproven` and only per-market readings are
made: not neg-risk; every question uses cumulative wording (`by`, `before`, `no later than`) and none uses `on`/`in`
`<month>`; questions identical once dates are masked; Gamma rules text (`description`) identical once dates are
masked; exactly one explicit full date per question, all distinct. Titles or `endDate` alone never prove nesting
(the Iran market's Gamma `endDate` is 2026-01-31 while its question says 28 February).

## 5. Classes of a change over (t0, t1]

`classify(ledger, wallet, family, t0, t1)`. Rules are tried in this order; the first match wins. The order is part of
the definition.

| # | Class | Rule |
|---|---|---|
| 1 | `UNRESOLVED_FAMILY` | the family is `unproven` |
| 2 | `UNKNOWN` | the payoff vector is `UNKNOWN` at t0 or t1 |
| 3 | `NONE` | no event of the wallet in the family during the window |
| 4 | `C_TECHNICAL` | only protocol events (split, merge, redeem, conversion, transfer, reward, fee), no fill |
| 5 | `C_MARKET_MAKING` | bought and sold the same token in the window, and traded notional >= `MM_RATIO` (5) × the net change marked per token (`|bought − sold|` of each token × its last price at t1) |
| 6 | `C_COMPLETE_SET` | largest shape change < `MIN_PAYOUT`, but at least 2 tokens traded for at least `MIN_PAYOUT` shares: a trade that leaves the payoff shape unchanged (YES + NO of one member, YES or NO on every member of an exclusive event): arbitrage or a synthetic split/merge. A reversal hidden next to a larger set is not absorbed: the set adds a constant, so the residue is the shape change itself |
| 7 | `NONE` | largest shape change < `MIN_PAYOUT` (500 payout dollars), and not rule 6 |
| 8 | `B_INTERVAL_PACKAGE` | ladder only, no sale in the window: NO on an earlier deadline and YES on a later one both held at t1 (>= `MIN_PAYOUT` each), at least one of the two legs bought in the window for >= `MIN_PAYOUT` shares, held legs read on net exposure per deadline (a complete set on D1 is not a NO leg), and no buy against a side already held on the same deadline (that would be a disposal). Either order of the legs counts (INTERVAL_LOGIC.md, falsification test 2) |
| 9 | `A_TRUE_INVERSION` | for some pair of worlds, the payoff difference changes sign, `|difference| >= MIN_PAYOUT` at both t0 and t1 (binary: X changes sign). In an exclusive family this includes buying another candidate past the first one: the payoff difference between the two worlds really reverses, whatever the token names |
| 10 | `D_YES_ACCUM_KEEP_NO` | binary: YES bought >= `MIN_PAYOUT` in the window, NO flow >= `MIN_PAYOUT` at t0 and t1, no NO sold, **and the wallet's merges are visible** (activity feed read) |
| 10b | `D_UNVERIFIED_NO_RETENTION` | the same from fills only: a merge, invisible in the tape, can remove NO without a sale. On TRAIN, 414 of 849 such episodes were confirmed once merges were read (DATA_GAPS.md) |
| 11 | `C_HEDGE_REBALANCE` | largest payoff advantage reduced by at least `MIN_PAYOUT`, no sign change |
| 12 | `DIRECTIONAL_ADD` | material directional change that is none of the above |

`MIN_PAYOUT = 500` and `MM_RATIO = 5` come from the frozen plan (500 USD per wallet, 5× two-sided rule). The frozen
plan's 500 is in marked USD; here it is in payout dollars (shares), a declared choice: what changes hands at
resolution. None of these values was tuned.

The run (`run_ledger.py`) classifies each wallet over the hourly windows `(k·3600, (k+1)·3600]` in which it acted in
the family (the frozen plan's `W = 3600`; an event at exactly `k·3600` belongs to window `k − 1`, `window_index`).
Episodes A, B and D are written with their transactions; other classes are counted per unit and partition.

Version 1 of these rules was reviewed adversarially (2026-11-17) and changed where a counterexample showed a wrong
class: B hid a reversal on the later deadline, depended on the order of the legs; the market-making test marked at a
quantity-weighted price across tokens; a complete set hid a reversal; a neg-risk complete set read `NONE`.

## 6. Identities and roles

The tape gives one address per fill: the proxy wallet that holds the tokens. Signers (the EOA behind a proxy),
funders and relayers are **not** in the tape; the schema has no field for them rather than an invented value. The
other wallets of each transaction are recorded on episodes as `co_participants_not_linked`. The exchange contract
of a fill is not in the tape either (DATA_GAPS.md, section 4). Wallets that share a
transaction are co-participants of one match, not linked accounts. No two addresses are ever merged into one
identity by this code. Any identity link must come from an independent, documented proof (see DATA_GAPS.md).

## 7. Partitions

An **observation** (wallet, family, window ending at t1) belongs to the partition containing t1, UTC, with the frozen
plan's calendar bounds:

| Partition | t1 |
|---|---|
| `TRAIN` | 2025-01-01 to 2025-12-31 |
| `VALID` | 2026-01-01 to 2026-06-30 |
| `TEST` | 2026-07-01 to 2026-10-31 |
| `EXCLUDED_PERIOD` | anything else |
| `EXPLORATORY_IRAN` | any observation of the Iran 28 February market or of an event whose slug starts with `us-strikes-iran`; and any observation of the 36 Iran cohort wallets that would fall in VALID or TEST |

Why not the frozen rule (whole market by close time): for "by date" markets the close time depends on the outcome
(an early YES closes early), so membership would carry label information. The frozen rule is still computed per
market for reference (`frozen_close_partition`, 0 disagreements with `splits.json` and `splits_expanded.json`).
Purge rule for any training on this ledger: `usable_for_training(market_close, partition)`, an observation is usable
only if its market closed by the end of its own partition. See `PARTITIONS.json`; the TEST window has already been
read by the S4 study and by parallel missions.

## 8. Output files of a run

| File | Content |
|---|---|
| `out/full/ledger/<unit-hash>.jsonl.gz` | every applied event: `ts, cid, wallet, kind, oi, qty, price, tx, src, flow_yes, flow_no, tx_check`, and as of the end of that second `x_status_end_of_second`, `reasons`, `inventory_lo_end_of_second`. A wallet's flows at T are its last row with `ts <= T`; they are flows, not holdings, and come with their status |
| `out/full/units.jsonl` | per event (unit): tape status per market, Gamma version, fee and neg-risk flags, family type or why it is unproven, conservation verdicts, quarantine counts, status counts at the last fill, class counts, ledger file sha256 |
| `out/full/episodes.jsonl` | A, B and D episodes (observation partition, market close times for the purge rule, shapes at t0 and t1, statuses, transaction hashes, `co_participants_not_linked`) |
| `out/full/missing_tape.jsonl` | sampled markets with no tape (none in this run) |
| `out/full/SUMMARY.json` | totals, verdicts, statuses, classes per partition (`scripts/summarize.py`) |
| `out/full/verify_TRAIN.json` | TRAIN A and D episodes re-read with each wallet's activity feed |
| `out/full/checkpoint.jsonl` | units done, with their markets, tapes and ledger sha256; a restart skips them, drops lines of unfinished units, and stops if a unit's market list changed |
