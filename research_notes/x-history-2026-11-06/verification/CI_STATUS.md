# Why the PR 36 checks fail (diagnosis, nothing bypassed)

Checked on 6 November 2026 against `origin/main` at `17acd34`, in a clean detached worktree, and on this branch.

| Check | `origin/main` | This branch | Cause |
|---|---|---|---|
| `scripts/check_publication.py --target main` | refused: README.md changed | same | `scripts/publication_baseline.json` anchors `main` at `870b434`; commit `0d31b08` (4 Nov, directly on `main`) rewrote `README.md` without moving the anchor, so every candidate built on `main` differs from the protected bytes |
| `scripts/validate_evidence.py` | 2 errors | the same 2 | an em dash in `README.md`; `MASTER_REPORT.md` links `investigations/followup-verification-20261104/README.md`, which is not on `main` |
| `scripts/build_master_report.py --check` | stale | stale | `MASTER_REPORT.md` and `INVENTORY.md` not regenerated |
| `test_phi.py`, `test_integrity_regressions.py` (18), `test_publication.py` (8) | pass | pass | |

This branch changes no protected path, no README, no MASTER_REPORT and no investigation folder: only `research_notes/x-history-2026-11-06/`.

The repair already proposed is PR 33: move `branches.main.commit` to the reviewed README of PR 31, then merge PR 33 into PR 31 and PR 31 into `main` as merge commits, after the owner approves the README text. The two other failures belong to the session that owns `followup-verification-20261104` and to the central report generator. None of this is changed here, and PR 36 is not merged while these checks fail.
