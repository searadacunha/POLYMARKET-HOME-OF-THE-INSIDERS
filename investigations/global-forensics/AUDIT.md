# Technical audit before integration

Read on 2026-11-02 from `origin/main` and from the PR 11 branch. Every line here marked "shown by test" has a named test in `tests/test_adversarial_existing.py`, which runs on synthetic input, without network, and changes nothing. A `test_defect_*` passes while the defect exists. No active engine, sealed decision or historical result was changed.

## The three risks named at the start

| Risk | Verdict | Proof |
|---|---|---|
| `funding_graph.py` can call a shared funder without a real split between private wallets and central infrastructure | **Confirmed.** The `infrastructure` flag is set only from `config/contracts.json`, which holds 8 Polymarket contracts and no exchange. A hot wallet paying two customers gives `SHARED_FUNDER`, and `corroborating_funding` returns it. A label alone does not stop it. `close_in_time` is computed and never gates | `test_defect_exchange_hot_wallet_without_flag_becomes_shared_funder`, `test_defect_label_alone_does_not_stop_a_shared_funder`, `test_defect_shared_funder_has_no_time_limit` |
| `collective_behavior.py` can read convergence without a tight window | **Confirmed, and it is the top category.** Three flagged wallets buying inside 24 hours are `convergence`, and `evidence_scoring.classify` returns `CORROBORATED_BEHAVIOR` from that alone. `convergence_spread_s` gates nothing | `test_defect_convergence_over_almost_a_full_day`, `test_defect_that_convergence_alone_sets_the_top_category` |
| Central validation checks references without reproducing calculations or chain reads | **Confirmed.** A finding saying a wallet won 5,170 passes when its source says it lost 5,170. An invented transaction hash passes once it is written in a cited file | `test_defect_a_number_elsewhere_in_the_file_validates_any_claim`, `test_defect_an_invented_hash_passes_once_written_in_a_source` |

## Other defects found

| Defect | Effect | Proof |
|---|---|---|
| `collective_signals` and `repeated_pairs` have no upper time bound on `pairs.evaluated_at` | On an already filled database, a replay at time T reads anomalies evaluated after T. Inert in a forward-only run. Whether a past replay was affected was not checked | `test_defect_replay_sees_flags_set_after_its_clock`, `test_defect_repeated_pairs_read_the_future_too` |
| `unique_edges` keys on (tx, log_index) with no chain | Unindexed rows of one transaction collide and both vanish as a "conflict" | `test_defect_unindexed_rows_of_one_transaction_cancel_each_other` |
| `fund_flow/trace.py`: receipts are capped by sorting hashes, and `capped` is computed before the scan adds rows | Receipts dropped by hash order while `capped` says false | `test_defect_scan_can_exceed_the_receipt_cap_while_capped_stays_false` |
| `flow-trace/tools/walk.py`: past depth 0, only the 8 largest flows and the first are followed, with no stop written | A branch disappears silently from a path presented as walked | `test_defect_deep_nodes_keep_eight_flows_and_record_nothing_else` |
| `walk.py` follows a Relay hop whatever `relay_proof` returned | The on-chain check is stored and not used. Measured impact: 63 proven, 1 not read, 0 false in the 11 dossiers, a same-chain swap, so no conclusion changes | `test_defect_relay_hop_is_followed_whatever_its_chain_proof_says`, count from `state/walk_*.json` |
| PR 11 `ledger.id_of`: unindexed rows are identified by route | Two equal internal moves of a transaction count once; two unequal ones refuse the whole import | `test_defect_two_equal_internal_moves_of_a_transaction_merge_into_one`, `test_defect_two_different_internal_moves_of_a_transaction_are_refused` |
| PR 11 `temporal.WINDOWS` has 60 s, not the 90 s asked for | The requested window is untestable with that module | `test_defect_requested_90_second_window_is_absent` |
| Polymarket's data API v1 answers HTTP 410 since its retirement | Any tool calling `/trades` or `/activity` without `/v2` now fails. `maduro-iran` phases 8 to 15 and parts of `ballon-dor-wallets` used them: their archives remain the only copy of those reads | Read 2026-11-02: `{"error":"Data API v1 has been retired"}` |
| `cases` and `fund_flow` read `owner()` at the latest block only | A wallet's owner today is not proof of its owner then | New `account.control` reads both; equal on every wallet read so far |

## What holds

`build_funding_links` never states a common owner, flagged infrastructure is not a funder, and trades not yet observed are invisible to `collective_signals`. `validate_evidence.py` refuses a number absent from its source. PR 11's `canonical_edges` refuses contradictory logs, and `coverage.py` separates a provider's claim from proof. `position_anomalies.reconstruct_from_fills` already reads `maker` correctly: every order emits a fill with its owner as `maker`, and `taker` is often the exchange, so a fill's `taker` field says nothing about who decided.

## Corrections in this branch

None of the audited files is edited. `investigations/global-forensics/engine/gf/` answers these points in its own code and its tests (`tests/test_engine.py`, `tests/test_shadow.py`):

| Point | Answer |
|---|---|
| Levels of proof | `events.py`: a level rises only through `proof.py`, from receipts of two independent nodes, never from a report |
| Silent truncation | `tracer.py` writes a stop for every unfollowed branch, and `explorer.py` reads by block cursor to the end, or states the range read |
| Bridges | `bridges.py`: no hop without the same identifier on both chains, or a message the destination contract verified |
| Shared services | `graph.py`: services, hubs and contracts sit in their own layer and cannot join two files |
| Fungibility | `alloc.py`: bounds that hold without a convention, FIFO and LIFO written as conventions, unexplained amounts shown |
| Accounting | `ledger_pnl.py`: cash by market, unknown types counted apart, residual shown |
| Future leaks | `shadow.py` refuses a row not yet observed, and its source holds no outcome field, enforced by a test |

The active engine still has these defects. Fixing them is a production change, and it is yours to decide.
