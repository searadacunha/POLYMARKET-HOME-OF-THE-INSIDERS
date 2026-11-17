# Final audit, collective exposure shifts (2026-11-17)

Independent audit of the study as published on branch `investigation/collective-exposure-shifts` at commit
`b4b9c8e85454b0493c92d6a261f77c273437f270`. Every number below comes from `results/audit/final_audit.json`, written by
`scripts/audit/final_audit.py`. That script recomputes the study from the raw inputs with code written for the audit. It does
not import `score.py`, `stats.py` or `report_tables.py`. Only the two sensitivity re-runs call
`build_alerts.evaluate_market`, because their purpose is to change exactly one rule of that engine.

Nothing frozen was edited. `analysis_plan.md`, both locks, the amendments, the scripts and `results/` are byte-for-byte
the audited commit.

## Inputs and hashes

| Input | Where | SHA-256 |
|---|---|---|
| Primary tapes (763 markets, 1,518,268 fills) | local only, `tapes.sqlite` | `63c85df4d3bce9f9afe77b713d10036f4fff426b021172fc763cbfe50eb915b3` (matches the manifest) |
| Replication tapes (816 more markets, 1,688,711 fills) | local only, `tapes2.sqlite` | `b65627060569f53a466ebfa5fa9e9731347fe66f79cd3c09cabb3823184f0768` (**the manifest records a mid-collection snapshot**, see A-05) |
| Complete Iran 28 February tape | local only, `feb28_v2.sqlite` | `1f636371b6573416770ada4cdbfc5f5e8f29b21819791a9c0ca315290c6f1015` (matches) |
| Population | git `research_notes/early-detection-2026-11-13/study/derived/universe_markets.jsonl.gz` | `8549fa71eeec96df97b21bc859d908704fe7131bfa24af8eae9acf5c1334a038` |
| Labels | git, same folder, `labels.jsonl.gz` | `97d4ea90d7b6698e2d6fb03c4be4a433856577aab2313b9e7947006db04c26b2` |

## What each result is

| Class | Result |
|---|---|
| **EXISTING** | The 34,413-market population and its labels (early-detection study, 13 November 2026). The archived Iran contrast, 20 of 36 versus 16 of 733 (independent forensic audit, 8 November 2026). The external-methods crosscheck (`research_notes/collective-exposure-methods-2026-11-16`, merged in PR 81). Those notes are cited as prior work; none of it is presented as new here. |
| **REPRODUCED** (by this audit) | The sample rule, with 763 and 1,579 identical sets. The chronological splits, with 0 mismatches over 6,329 scored rows. The label join, with 0 mismatches. All 395 S4 alert prices against the tape. All 1,963 wallet shifts, to the cent. T1, T5 and T7 and both verdicts (`INCONCLUSIVE` primary, `NOT_SUPPORTED` replication). The Iran recheck, byte-identical output (20/36, 16/733, then 35/36 and 27/733 on the complete tape). The study's 10 unit tests, including the planted-shift positive control. |
| **NEW** | The study itself (16 November 2026): an outcome-blind sample, positions rebuilt from fills, and a null result. The censoring of the archived Iran tape. The audit measurements in this file: time-honest alert re-run, T2 matched to S4 only, price staleness, coexistence count, executed-liquidity proxy, chronology of files. |
| **UNTESTABLE** | A fillable net result and capacity: no historical order book exists in the repository. Financially linked collective shifts (S5): no funding graph at this scale. Splits, merges and redemptions: absent from fill tapes. Markets of 1 M USD and above: excluded by the sample rule. The content of the plan at first freeze: the text behind hash `0433bb0f…` is not recoverable on this machine (A-03). Public byte-level reproduction of the tapes: they are local only, and a new collection can differ. |
| **REFUTED** | Statements of the published text that the audit contradicts: A-02, A-04, A-05, A-06 and A-07 below. The hypothesis of a **large** edge: across all 266 replication alerts, an excess above +1.8 points over the price is excluded at 95 % (event-clustered interval −5.0 … +1.8). An excess above +4.0 points is excluded in the time-honest re-run (−2.7 … +4.0). A small edge is neither supported nor refuted. |

## Priority checks

| Check | Outcome |
|---|---|
| Lookahead or post-selection | **Found (A-01).** The 6-hour non-maximum suppression keeps the *largest* candidate of a block, so the entry time can depend on candidates that occur after it. Every feature of the kept alert uses fills at or before its own time: 0 of 395 alerts has a contributing fill after `t`. |
| NO / YES classification | Clean. The tapes contain only `Yes` and `No` outcomes. The NO side is priced from NO fills and scored as `winner == side`; 0 mismatches. |
| Inventory versus trade | Clean as declared. Exposure is net of fills, not inventory: splits, merges and redemptions are invisible. Coexistence is **not** flagged in code (A-02). |
| TEST contamination | No threshold or signal changed after TEST was read: `build_alerts.py` and `split.py` are hash-identical between the two locks. But the plan, `score.py` and `stats.py` did change after the first results (A-03). The verdict rule lives in `stats.py`. 4 of 48 TEST alerts fired before 2026-07-01, because the split is by market close date. Keeping only the 44 that fired on or after that date: excess −4.55 points, unchanged verdict. |
| Group built with later transactions | No. Every wallet's change is computed on fills in `(t − 1 h, t]`, and the last contributing fill is never after `t`. |
| Unfair comparison with price alone | **Found (A-04).** The published T2 placebo is drawn for every alert of every variant, not for the S4 primary alerts it is compared with. Matched to S4 only: −2.24 points primary (CI −5.1 … +0.5), −0.53 points replication (CI −2.4 … +1.3). Still null. The entry price is the last executed fill: median age 121 s, none older than 1 h, and 14 of 266 entries more than 5 points away from `1 − other side`. |
| Unrealistic fees or depth | Fees and gas are excluded and no depth is modelled. The slippage grid is applied uniformly whatever the size. See capacity below. |
| Missing data turned into zeros | No. Markets that are too short are excluded and counted: 1 primary, 2 replication. No `too_deep` or error market exists. 0 alerts lost between building and scoring. 9,746 fully identical fill rows (0.64 %) exist in the tape. Removing them leaves the result unchanged (A-08). |
| False positives excluded without justification | No. All 14 TEST false positives are listed below. The plan says documented cases are "listed and removed", but there is no such list in the code (A-06). The Iran 28 February market is not in either sample. |
| External results presented as own work | No. The population, labels, Iran figures and methods note are cited to their repository sources. |

## Audit findings

- **A-01, lookahead in alert timing, and it moves the headline.** Re-running the replication with the first candidate
  in time as the alert, so that a later candidate cannot displace it, gives the same wins at earlier and cheaper
  entries:

  | Replication S4 primary | Published rule (largest in 6 h) | First firing in time | Identical rows removed |
  |---|---:|---:|---:|
  | All, n = 266, wins | 191 | 191 | 191 |
  | All, mean price | 0.734 | 0.711 | 0.734 |
  | All, excess (95 % CI, events) | −1.58 pt (−5.0 … +1.8) | **+0.74 pt** (−2.7 … +4.0) | −1.54 pt (−5.0 … +1.7) |
  | TEST, n = 48, excess | −4.34 pt (−12.4 … +3.9) | **+1.18 pt** (−6.8 … +9.3) | −4.13 pt (−12.2 … +3.9) |
  | TEST, one-sided p vs price | 0.808 | 0.500 | 0.799 |
  | TEST, result per share at 1 % slippage | −0.053 | **+0.002** | −0.051 |
  | Verdict rule | NOT_SUPPORTED | NOT_SUPPORTED | NOT_SUPPORTED |

  The published sentence "in TEST the alerted side won less often than its own price implied (−4.3 points)" is true of
  the published rule. It is mostly produced by that rule's choice of a later, higher-priced moment. The robust
  statement is that no rule variant shows a significant edge in either direction.
- **A-02, coexistence not implemented.** The plan and README say coexistence (holding YES and NO at once) is
  "detected and counted explicitly". No code does it. Counted here: 62 of 129 primary alerts, and 115 of 266
  replication alerts, include at least one wallet with positive YES and NO holdings at the alert. This does not change
  the direction of `X = q(YES) − q(NO)`, which is still the right directional quantity.
- **A-03, frozen plan edited after the first results.** `PROTOCOL.lock.v1` pins `analysis_plan.md` at `0433bb0f…`.
  The shipped plan is `833eaa17…`, last modified 2026-11-16 22:00:52 UTC; the first `tests.json` was written at
  20:23:54. The text at first freeze cannot be recovered, so what changed is untestable. `score.py` and `stats.py`
  also changed (declared in amendments 001 and 003). The lock's stated reason ("units fix in build_alerts.py") does not
  match the hashes, because `build_alerts.py` is identical in both locks. `PROTOCOL.lock.v1` says `frozen_utc
  20:13:23Z`; the README and `PROTOCOL.lock` say 20:12:35Z.
- **A-04, T2 comparator not matched to S4.** See the table above. The published values stay in `results/`.
- **A-05, data manifest snapshot of `tapes2.sqlite` taken mid-collection.** The manifest records 438,779,904 bytes,
  `45209773…`, at 21:52:23Z. The final file, last written at 21:57:42, is 800,653,312 bytes, `b6562706…`. The
  replication results were computed on the final file: its row and market counts match `replication_state.json`.
- **A-06, documented-case exclusion not implemented.** The plan states that documented cases' condition ids "are
  listed and removed". No list exists in the code. The Iran 28 February market (`0x3488f31e…`) is not sampled, so
  that cohort does not enter any rate.
- **A-07, ordering claims contradicted by file times.** Amendments 001 and 002 say they were written before the
  replication sample was collected. On the working disk, both files were created at 21:44:36; `sample_expanded.jsonl`
  at 21:43:22 and `tapes2.sqlite` at 21:43:24. Collection started 72 seconds earlier. The replication rule is the same
  outcome-blind hash with a wider threshold, and it was run once. But the decision to extend the sample was taken after
  the primary result was known. Stale text: the README's primary T2 (−2.69 pt) is the pre-amendment-003 value, while
  `results/tests.json` holds −0.68 pt. FINDINGS still lists the replication as "the only open item".
- **A-08, duplicate fill rows.** There are 9,746 rows identical in (market, tx, wallet, side, outcome, size, price,
  time), across 609 markets. The largest is 59 identical 10-share fills at 0.001 in one transaction, which looks like a
  ladder of identical resting orders rather than a pagination overlap. Re-running without them changes nothing that
  matters (table above).

## Steps 1 to 6 of 17 November 2026, checked

Each step worked outside this folder: the repository's protocol guard refused `git worktree add` while a frozen study
exists in the repository. Their deliverables are copied here without their scratch files, superseded outputs or large
derived files. The large files stay on the working disk and are listed in each step's README.

| Step | Folder | What was checked here | Result |
|---|---|---|---|
| 1, baseline audit | `baseline-audit/` | Hashes of the archived Iran files, and the claim that FINDINGS and results disagree | Hashes confirmed (also by `scripts/reproduce_feb28.py`, byte-identical output). The claimed disagreement does **not** hold. "175,997" in FINDINGS is 217,997 minus the 42,000 archived rows, so the text is ambiguous, not wrong. The `tapes2.sqlite` manifest mismatch is confirmed (A-05). |
| 2, external methods | `METHODS_REUSE.md` | Attribution, licences, nothing copied or executed | External repositories are cited at pinned commits and none of their code is copied. Their code defects are read, not run, so they are UNTESTABLE here. Classified EXISTING (external) plus proposals. |
| 3, position ledger | `position-ledger/` | Test suite; fill count; partition rule | 37 of 37 tests pass on re-run. The 3,206,979 fills applied equal the two tapes' row count. TEST uses the frozen split rule. Inventory is bounded, never claimed exact. |
| 4, exposure signals | `exposure-signals/` | Test suite; outcome isolation; headline numbers | 11 of 11 tests pass on re-run. The label file holds exactly the 623 TRAIN markets, and no VALID or TEST label was read. The ANY-family excess against the price at `t` is −0.35 points (CI −2.1 … +1.3): exploratory, TRAIN only, uncorrected. |
| 5, falsification | not included | Progress at 12:21 UTC | **Not audited, not published.** The step was still preparing a collection of trade histories for 9,395 new markets (3,806 holdout, 3,609 extended TRAIN, 1,980 history), so no statistical result existed to check. Nothing here depends on it. The verdict below rests on the frozen study, its replication and this audit. |
| 6, execution | `execution/` | Pre-registration time; headline cell; causal timing | `prereg/GRID.json` was created at 09:25:58 UTC, before the first results at 09:29:15. Its hash (`6a99a1a1…`) is in `EXECUTION_LIMITS.md`; the hash file itself is withheld because it holds a local path. The headline cell recomputed from `out/TRADE_REPLAY.csv`: −17.50 USD on 2,160.15 USD, 26 of 48 executed. The non-causal frozen times are 117 of 266, which agrees independently with A-01. Its input `tapes_all.sqlite` (SHA-256 `49a995942d8259194784342421dd445204c2f2c23d688fdb6afd5137d9cc3ee2`) holds 3,206,979 fills in 1,579 markets, exactly the two study tapes combined. |

## Final verdict

1. **Is an incremental statistical edge demonstrated?** No. No declared test passes Bonferroni (0.05/10) under any
   variant. Against the price: −1.6 points (published rule) or +0.7 points (time-honest rule) on 266 alerts in 197
   events. Against a placebo at the same market and price: −0.5 points. Against naive buy consensus and a single
   wallet's shift: null. An edge larger than about +4 points over the price is excluded at 95 %. Smaller edges are not
   excluded.
2. **Is a net executable edge demonstrated?** No. At the last executed price plus 1 % slippage, the TEST result is
   −0.053 per share (published rule) or +0.002 (time-honest rule); neither is distinguishable from zero. Fees, gas,
   spread and depth are not modelled, because the historical order book does not exist in the repository.
3. **Frequency, capacity, uncertainty.** About one S4 alert per six markets (0.169 per market). Extrapolated to the
   5,843 markets under 1 M USD that closed in the TEST window: roughly 240 alerts a month. That is an extrapolation
   from a 5 % sample, not a measurement. Capacity proxy: the notional that **executed** on the alert side within one
   point of the entry price, in the hour after the alert, had a median of 377 USD (quartiles 11 and 2,259 USD; zero
   for 57 of 266 alerts). That is an upper bound on what a follower could have taken without moving the price, not a
   book depth. Uncertainty: the TEST excess interval is about 16 points wide (−6.8 … +9.3 time-honest; −12.4 … +3.9
   published rule).
4. **Can the result be reproduced?** Yes from the recorded tapes: every published figure is recomputed exactly
   (`results/audit/final_audit.json`, `tests/audit/test_final_audit.py`). From public data only in part: the three tapes are
   local only, and a fresh collection from data-api v2 can differ from the snapshot. The population, labels, code and
   all derived results are in git.
5. **What evidence is still missing?** A prospective book recorder at alert time (ask, depth, spread), to turn the
   gross reading into a fillable one and to measure capacity. A funding graph for the sampled wallets, for S5. A
   coexistence and documented-case implementation that matches the plan. The plan text at first freeze, or an explicit
   amendment saying what changed in it. A larger TEST window, about 4× the alerts, to resolve edges of ±4 points.

## Best alerts and false positives (replication, TEST split)

Ranking is outcome-blind: size of the collective shift. The outcome is shown after ranking. "Last fill" is the entry
price used by the study. The tx links are fills of the largest contributing wallet inside the alert window. The `v2`
link opens the public tape of the market. Full rows, with every wallet: `results/audit/publication_tables.json`, plus
`best_alerts.csv` and `false_positives.csv`.

See [`results/audit/tables.md`](results/audit/tables.md) for both tables, rendered from the JSON by `scripts/audit/render_tables.py`.

## Reproduce

```bash
python3 scripts/audit/final_audit.py --inv . --tapes tapes.sqlite --tapes2 tapes2.sqlite \
    --labels labels.jsonl.gz --universe universe_markets.jsonl.gz --out results/audit
python3 scripts/audit/render_tables.py results/audit/publication_tables.json > results/audit/tables.md
python3 tests/audit/test_final_audit.py
```

`labels.jsonl.gz` and `universe_markets.jsonl.gz` come from `git show
origin/main:research_notes/early-detection-2026-11-13/study/derived/<file>`. The full run, with the two engine
re-runs, took 18 minutes on a USB disk; `--skip-reruns` took 1 min 25 s.
