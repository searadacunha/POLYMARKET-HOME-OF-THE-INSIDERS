# Parallel research and publication

Research sessions may continue collecting evidence and working on their own branches. Before publishing, fetch the destination branch and merge it into the session branch. Keep uncommitted work in its own worktree; do not reset or clean a collector's working directory.

## Preserve accepted work

- The current `main` README and archived Relay follow-up are referenced by `scripts/publication_baseline.json`. Keep their existing bytes. Change that baseline only for a specifically authorized, reviewed update; never to make an unexpected failure pass.
- **README editorial policy:** preserve the established English narrative, chapter hierarchy, compact tables and direct evidence links. Lead with the most material **verified financial relationships and reconciled amounts**; clearly distinguish separate cohorts and accounting windows. Only promote findings actually supported by reproducible evidence, with matching report links. Do not turn unverified leads, claims of one wallet owner, alleged inside information, or obsolete third-party profit estimates into headlines. Historical contradictions, negative tests and investigative corrections belong in technical reports, not in a promotional README.
- Preserve the validated code fixes and regression tests. Use Git merges and explicit file changes. Never replace the destination with a whole older checkout, source directory or snapshot.
- A session owns its investigation directory. The central importer may update source snapshots, manifests and the corresponding evidence hashes through the documented import process; it must not replace the repository README or shared tools.
- Keep source evidence, frozen protocols and recorded results intact. Put new evidence and corrections in a subsequent documented snapshot or follow-up. Do not invent conclusions or promote a finding's evidence level without its supporting verification.
- Do not merge an existing draft or research PR merely to synchronize. Preserve its review conditions.

## Before publication

Work from a real clone with the complete history and a separate session branch. Fetch and merge `origin/main`, resolve conflicts explicitly, then commit only the intended paths. Check the committed candidate:

```bash
python3 scripts/check_publication.py --target main --candidate HEAD --base-ref origin/main
python3 scripts/test_phi.py
python3 scripts/test_integrity_regressions.py
python3 scripts/test_publication.py
python3 scripts/validate_evidence.py
python3 scripts/build_master_report.py --check
python3 research_notes/relay-followup-2026-11-04/verify.py
```

The first command reads Git objects and does not fetch, modify files, commit or publish. A missing baseline or a stale candidate is an error. Investigations retain their own additional checks. Regenerate central reports through their generator when accepted metadata changes require it.

Push the session branch normally and open a PR. Never force-push or replace history. Recheck the destination and exact PR head before merging, and wait for relevant checks. For Git Data API publication, build on the current destination tree, submit only explicit changed paths, inspect the resulting diff and use an expected-head lease when updating a ref.

GitHub checks report problems; without server-side required checks they cannot prevent every direct or forced push. Do not describe the branches as protected unless GitHub confirms that protection. Do not claim to have checked unpublished Mac sessions from a GitHub-only review.
