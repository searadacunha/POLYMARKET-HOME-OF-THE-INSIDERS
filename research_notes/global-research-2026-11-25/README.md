# Global research note, 25 November 2026

This note is a follow-up. It does not replace `EDGE_VERDICT.md`, the root README, another investigation, or the frozen weekly series through 2026-W46.

The nine reports named in the session brief are in French. Code, tests, JSON and this page are in English. `CONTRIBUTING.md` asks for English outside `sources/`. The French pages are there because the owner asked for those deliverables in French. They add to the count of French files outside `sources/`, which the 20 November benchmark already records as a documentation defect.

## Reproduce

From the repository root, with Python 3.11 or newer and no extra packages:

```bash
python3 -m unittest research_notes/global-research-2026-11-25/tests/test_note.py
python3 research_notes/global-research-2026-11-25/verify.py
```

Both commands are offline. They recompute the frozen T1 tail from the committed analytic table, check the 2026-W47 snapshot, and score the grid in `data/scorecard.json`.

The week was captured on 25 November 2026 from commit `9c279334a5dd77ef5fc30c9c2333c9f43aac5a5a` with the existing collector:

```bash
cd investigations/weekly-funding-intelligence
python3 -m weekly_funding.refresh --week 2026-W47 --dest /tmp/capture-W47
```

The prior report used for continuation is byte-identical to `investigations/weekly-funding-intelligence/results/weekly_funding.json`, SHA-256 `fed5e9193ffa7d9401f4d42d02fdefef6fc7b3c1752bdc8ed66339f3763a3c73`. That file is not copied again. The capture's `previous_report.json` was removed for that reason. Work-directory HTTP caches and the chain snapshots under `w47/` are kept.

## Standing result

`NO_EDGE_VALIDATED` is unchanged. The recomputed validation test is still NOT_SUPPORTED (n = 45, 13 wins, p = 0.3345912628416912).
