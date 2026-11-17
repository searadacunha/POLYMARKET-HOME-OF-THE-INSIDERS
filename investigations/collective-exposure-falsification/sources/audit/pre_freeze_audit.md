# Pre-freeze blind audit (2026-11-17)

Workflow `etude-gelee-audit`, run `wf_2c94ab5c-b5d`, mode `aveugle`: silent-failure-hunter, leakage-auditor,
stats-auditor and protocol-auditor in parallel, each BLOCKING or MAJOR finding re-checked by two fresh agents asked
to refute it, then a completeness critic. 43 agents, 0 errors. No result existed on VALID or TEST; the forbidden
list also covered `out/`, `logs/` and the labels file. Full per-agent output:
`~/.claude/projects/-Users-benjamindacunha/74b0b42c-0a9d-432f-8781-ce2eb03a2f09/subagents/workflows/wf_2c94ab5c-b5d/journal.jsonl`.

Gate result: **CLOSED** (2 blocking: no freeze yet; verdict not computed by code). 50 findings in total.

## Disposition of the BLOCKING and MAJOR findings

| Finding | Disposition |
|---|---|
| No PROTOCOL.lock / controls report / collection still running | Fixed by sequence: collection finished (all `ok`), tapes hashed (`derived/tapes_sha256.txt`, checked by `run_all.sh check`), controls re-run, freeze after the control gate. |
| Verdict rule not in code (`status_of` never called) | Fixed: `ana_50_models.py verdict` / `verdict_from`, tested on synthetic inputs (`tests/test_ana.py::test_verdict_rules`). |
| R units drawn with a probability that depends on the market's future length | Fixed: Bernoulli(1/384) per grid time by hash of (cid, t). |
| Labels other than YES/NO silently coded as losses | Fixed: refused in `load_labels` and `ctl_40`; single-class fits refused. |
| Detector read tapes still being written | Fixed: refuses unless every market has a final status; collection finished before the base run. |
| T4 escaped the two-way bootstrap; control reuse ignored | Fixed: two-way over every event involved and the COL wallets; reused controls counted. |
| Effective n / recurrent wallets | Reported per test (events, wallets, share with a wallet active in ≥ 50 events) and a sensitivity without those wallets; limit declared. |
| Monte-Carlo resolution of the decisive p (two-way B = 2,000) | Fixed: B = 20,000 for both bootstraps; `n_tirages` written to the registry. |
| Controls too weak (2 seeds, event-only p, no M4, young-wallet give-away, no detection rate) | Fixed: 5–10 seeds, two-way p, FUNDLINK (M4) and OLD (real old wallets) scenarios, detection rate, gate in code. |
| Null gate on a different population and scrambled price | Partly fixed: same market subset, seeds without COL counted conservatively; scrambled price declared as a limit. |
| NEGATIVE_PRECISE could come from M3 overfitting | Fixed: the T1 bound is corrected by the mean T1 of the NULL controls before the comparison with the SESOI. |
| Inputs outside the study not hashed | Fixed: hashes recorded and checked before each detector run. |
| Ledger differs from the one mission 4 ran on; the test does not compare to mission 4's outputs | Declared in the plan (final ledger used, outputs can differ). Not fixed: no comparison with mission 4's recorded alerts (different ledger and pool make it uninformative). |
| Controls p event-only | Fixed (two-way in controls). |
| Freeze criteria not computed | Fixed: `ctl_45_summary.py`. |

## MINOR findings

Fixed: VALID/TEST shared events purged from the refit; `vol_ratio`-unknown indicator declared; standardisation
moments declared (fitting set); IMPOSSIBLE tests registered without a p; one registry line per sensitivity
variant and the missing variants (λ grid, leave-one-group-out, without hyperactive wallets) implemented; funding
`truncated` / `error` / unresolved pairs → UNKNOWN; Etherscan non-success with an empty list → error unless "No
transactions found"; permutation control made a bijection per market; T4 matches exactly on `endDate` known /
unknown; phase-A cache keyed by code and inputs; VALID one-shot guard; CV refuses an unusable fold; IRLS reports
convergence; counts of moves excluded by ledger class and of units with a known `endDate` written to `stats.json`.

Declared, not fixed: `endDate` as fetched in November 2026; inclusion on end-of-life quantities; TRAIN labels also
read in `ctl_40_inject.py` (TRAIN only); no request / too_deep accounting for the h < 50 tapes; the registry
witness write failure is swallowed by the skill's `registre.py` (outside this study's code).
