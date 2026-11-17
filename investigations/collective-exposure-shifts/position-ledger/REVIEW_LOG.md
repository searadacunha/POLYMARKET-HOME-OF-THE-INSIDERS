# Review log (2026-11-17)

Two independent reviews ran on this folder before delivery. Every finding came with a concrete failing input;
reproductions were run against the code. Agent transcripts are in the session's workflow journals
(`wf_3572b34d-efe` for the engine review, `wf_e0e592e3-85f` for the deliverable audit).

## Review 1: engine (four lenses: payoff algebra, look-ahead, silent failures, class separation)

Each finding was re-run by an independent skeptic before being counted.

| # | Defect (confirmed) | Fix | Test |
|---|---|---|---|
| 1 | Transaction verdicts and `TX_UNBALANCED` used rows first seen after T (look-ahead both ways) | snapshot at T computed on a ledger rebuilt from rows seen by T | `test_tx_check_uses_only_rows_seen_by_T`, `test_late_observed_event_is_not_used_before_it_is_seen` |
| 2 | Same-second fills ordered by tx hash created false "proven unobserved inflow" and false `UNKNOWN` | running minima at second boundaries | `test_same_second_order_cannot_create_negative_inventory` |
| 3 | Partition by market close time is outcome-dependent for "by date" markets; trade periods overlap | partition by observation time t1, purge rule, frozen rule kept for reference | `test_partitions_never_put_iran_in_valid_or_test` |
| 4 | A fill exactly on the hour was never classified (bucket `ts // W` vs window `(t0, t1]`) | `window_index = (ts − 1) // W` | `test_window_index_matches_left_open_windows` |
| 5 | B was tested before A and hid a reversal on the later deadline | B refused when a leg buys against a side already held on the same deadline | `test_ladder_reversal_on_later_deadline_is_A_not_B` |
| 6 | Market-making test marked the change at a quantity-weighted price across tokens | net change marked per token at its own last price | `test_market_making_is_marked_per_token` |
| 7 | A complete set larger than a reversal hid the reversal | complete set only when the shape change itself is immaterial | `test_reversal_hidden_in_a_complete_set_is_A` |
| 8 | A neg-risk complete set (YES on every member) read `NONE` | material trading with unchanged shape over 2+ tokens = `C_COMPLETE_SET` | `test_neg_risk_complete_set_on_every_member` |
| 9 | An interval package built YES-D2-first read A (depended on leg order) | B decided from legs held at t1 | `test_ladder_reverse_order_is_still_B` |
| 10 | Bounds ignored redemption and conversion coverage (`hi < lo` possible; `EXACT` despite invisible redemptions) | coverage of each class enters status and bounds | `test_bounds_respect_redemption_coverage` |
| 11 | Rows without a transaction hash escaped the check silently | counted, reason `TX_UNCHECKED` | `test_rows_without_tx_are_flagged` |
| 12 | Markets without a tape appeared in no output | `missing_tape.jsonl` | none (runner; 0 such markets in this run) |
| 13 | Checkpoint keyed by unit name only: a market added later was skipped | checkpoint stores the market list; mismatch stops the run | none (runner) |
| 14 | A crash between outputs and checkpoint duplicated episodes on resume | uncheckpointed lines dropped at restart; checkpoint written last | none (runner) |
| 15 | Units spanning partitions labelled `MIXED`; a missing close time read as 1970 | partition per observation; `UNKNOWN_CLOSE` | `test_partitions_never_put_iran_in_valid_or_test` |

Rejected after reproduction (3):

- "Buying another candidate in a neg-risk event is not an inversion" (raised by two lenses): the payoff difference
  between the two worlds does reverse; YES on M2 is economically NO on M1 and M3. INTERVAL_LOGIC.md defines the
  reversal on payoff differences, not token names. Kept as A, stated in POSITION_SCHEMA.md.
- "MIN_PAYOUT in shares contradicts the plan's marked USD": a declared choice (payout dollars), stated in the schema.

Found by the data, not the review: fee paid in shares on fee-enabled markets made transactions unbalanced; verdict
`FEE_IN_SHARES` added (`test_fee_in_shares_is_not_a_missing_fill`).

## Review 2: deliverables (claims audit and mission coverage)

Fixed in code, then the whole run was redone:

| Finding | Fix | Test |
|---|---|---|
| B accepted a complete set on D1 plus YES on D2 (raw flows instead of net exposure) | B uses net exposure per deadline | `test_complete_set_on_d1_plus_yes_d2_is_not_B` |
| REDEEM rows from the activity feed (no outcome index) could not be ingested | REDEEM without outcome burns every token of the condition held | `test_redeem_without_outcome_burns_the_whole_position` |
| Cash flow reported as known on fee-enabled markets without fee data | `cash_flow = None` there | `test_fee_enabled_market_without_fee_data_has_unknown_cash` |
| Ledger built with `check_tx=False` (Iran example) carried no warning | reason `TX_UNCHECKED` on every fill | `test_unchecked_transactions_are_flagged` |
| Payoff vector gave no bounds on the payout level | `payout_lo`, `payout_hi` from member inventories | `test_payoff_vector_carries_level_bounds` |
| Iran cohort observations in the TRAIN period stayed in TRAIN | cohort exploratory in every period | `test_partitions_never_put_iran_in_valid_or_test` |
| Ledger rows had flows but no status | each row carries `x_status_end_of_second`, `reasons`, `inventory_lo_end_of_second` | run output |
| Counterparties not recorded | episodes list `co_participants_not_linked` | run output |
| Example 1 used `t // 3600` windows | `window_index` | example rerun |
| Iran example ignored 124 REDEEM rows before the last fill | applied (burn resolved deadline); feb28 fills of each wallet checked against the complete tape | example rerun |
| Outcome fields stored in `data/gamma_meta.jsonl` and the Iran event cache | removed (`outcomePrices`, `umaResolutionStatus`, prices) | none |

Corrected in the text only: duplicate rows by verdict, fee-rate modes per fee type, scope of the activity re-read
(binary episodes only), MERGE counts before and after the last fill, the example 2 reading, the bound condition on
neg-risk markets, the B threshold wording.

Left open, stated in DATA_GAPS.md: exchange contract per fill (not in the tape), fee schedule per fee type (the
0.10 cap is a plausibility band, not a proof), Gamma flags read today rather than as of each fill, the 209 TRAIN A
episodes in exclusive families not re-read with activity, no unit test for the runner's resume logic.
