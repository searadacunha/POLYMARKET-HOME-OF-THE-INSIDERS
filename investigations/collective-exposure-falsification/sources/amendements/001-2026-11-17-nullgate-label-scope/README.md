# Amendment 001, 2026-11-17 ~15:05 UTC: label lookup of the null gate

**What failed.** `sh code/run_all.sh nullgate` (frozen `ana_50_models.py`, sha256 `dc65a450…`) stopped with
"9 units without a label … refused". `stage_nullgate` loads labels only for the condition ids that have an
observed TEST unit, but the day-shifted null panels create COL units in other TEST markets of the hold-out.

**Change.** `nullgate_label_scope.py` imports the frozen module unchanged and widens only the label lookup to
the 1,234 hold-out TEST markets (`derived/holdout_markets.jsonl`, split TEST). The statistic, the null panels
(19 seeds, produced by the frozen `feat_30_detect.py`, sha256 `076ff73c…`, recorded in each `stats.json`), the
same-market restriction, the conservative counting of seeds without COL and the p formula are unchanged.

**Decision.** Taken under Benjamin's instruction of 2026-11-17 ("Termine NULLGATE"), after the TEST results were
read. It cannot change the H1 verdict: `SUPPORTED` requires T1 to pass Holm and the control gate to pass; T1 did
not pass (p = 0.98) and the control gate failed (G1). Because the code is outside the freeze, the registry marks
the line `TEST_nullgate_T1` as not declared (exploratory); the gate is reported as such.
