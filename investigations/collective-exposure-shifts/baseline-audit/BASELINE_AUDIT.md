# Baseline audit, collective exposure shifts (mission 1/7)

Date: 2026-11-17. Agent: Claude Code (Opus 5.5). Scope: read-only audit. No new predictive result is produced here.

## 0. Verdict first

**NO-GO for starting a new detector study under the name `investigation/collective-exposure-shifts`, as briefed.**
The branch already exists on `origin` with a complete, frozen and replicated study whose state is `DONE`, verdict
`NOT_SUPPORTED`. Starting again would duplicate it or reopen a frozen protocol. Any follow-up (missions 2-7) has to
start from that study and its open items (section 7), as a new dated amendment or a new study decided by Benjamin.

**GO on the archived baseline:** the three evidence files are present, their SHA-256 match the 8 November audit,
and the 20/36 vs 16/733 contrast reproduces exactly from an independent streaming recount.

## 1. Pre-checks and constraints met

| Check | Result |
|---|---|
| Free disk | 1.1-1.2 GB free, under the 13.5 GB floor (`diskguard check --need 1G` = refused). No clone, download or full checkout made. Everything was read from local git objects (`git show origin/...`) and from `/Volumes/VERBATIM HD/phi-x` (read only). |
| Main clone | `~/Projects/Polymarket-Home-of-the-Insiders` is on `investigation/followup-verification-20261104` with another session's uncommitted changes. Not touched. |
| Branch creation | `git worktree add` was **refused by `protocol_guard`** ("git worktree in a repository containing a frozen study: to be run by Benjamin"). Not bypassed. This file therefore lives outside the repository. |
| README | Not read for editing, not modified. |
| Frozen files | None modified. |
| Required reading | `AGENTS.md`, `CONTRIBUTING.md`, `METHODOLOGY.md` (origin/main `0d79ba6`) read for the relevant rules: one session per investigation directory, frozen protocols and recorded results kept intact, README protected by `scripts/publication_baseline.json`. |

## 2. What already exists (provenance)

| Item | Where | State |
|---|---|---|
| Full study "Collective exposure shifts" | `origin/investigation/collective-exposure-shifts`, tip `b4b9c8e` (2026-11-16 22:41 UTC), 4 commits ahead of main, not merged | `STATUS.md`: `DONE`. `PROTOCOL.lock` re-frozen 2026-11-16T22:40:18Z, `PROTOCOL.lock.v1` kept, 3 amendments (001 excess metric, 002 replication, 003 within-market placebo). |
| Primary run | same branch, `results/tests.json` | 763 markets, 1,518,240 fills, 129 alerts, 16 in TEST: `INCONCLUSIVE` |
| Pre-declared replication | same branch, `results/replication_tests.json` | 1,579 markets, 3,206,979 fills, 266 alerts, 48 in TEST: `NOT_SUPPORTED` (TEST −4.3 points vs price; net negative at 1 % slippage in VALID and TEST) |
| Feb-28 re-check incl. complete tape | same branch, `results/feb28_recheck.json`, `scripts/reproduce_feb28.py` | archived 20/36 vs 16/733 reproduced; on the complete v2 tape: 35/36 vs 27/733 (band) and 28/733 (full history) |
| External methods crosscheck | `main` `0d79ba6` (from `research/collective-exposure-methods-20261116`), `research_notes/collective-exposure-methods-2026-11-16/` | `INTERVAL_LOGIC.md` (NO(D1)+YES(D2) package vs reversal), `BACKTEST_SPEC.md`, `CASE_CROSSCHECK.md`, `recompute.py` + tests |
| Archived Iran evidence | `main`, `research_notes/independent-forensic-audit-2026-11-08/` (REPORT.md section B1, `evidence/SHA256SUMS`) | descriptive, explicitly no p-value |
| G38 tier audit | `main`, `research_notes/g38-proof-tier-audit-2026-11-08/REPORT.md`, `AUDIT_2026-11-08.md` | point 4: retrospective cohort, no valid enrichment probability; missing baseline listed |
| X leads verification | `main`, `research_notes/x-history-2026-11-06/verification/` | wallet-level Iran/Venezuela evidence (Coinbase deposit address shared by JamWil23, bravonoll, Frogensky; 38/38 of the Andrey list to `0xc5bb1be0…`). Funding links, not exposure shifts. |
| Counterparty network | `main`, `investigations/counterparty-network/` | C7 reconciliation + V2 maker-taker edge summariser; no full-market graph, no predictive claim |
| Live monitor | `main`, `monitoring/phi_monitor/` | decodes `OrderFilled` on CTF Exchange V2 `0xe1111800…` and NegRisk Exchange V2 `0xe2222d27…`; uses data-api `/v2/trades?taker_only=false` |
| Pattern / backtest docs | `main`, `PATTERN_RESEARCH.md`, `BACKTEST_RESULTS.md`, `VERIFIED_FINANCIAL_FINDINGS.md` | "No pattern passed"; frozen 34,413-market population (13-14 Nov) reused by the study above. Nothing specific to collective exposure in VERIFIED_FINANCIAL_FINDINGS. |

## 3. SHA-256 of the archived evidence

Recomputed on 2026-11-17 from the git blobs of `origin/main` and from the local copies on VERBATIM.

| File | Size (bytes) | SHA-256 recomputed | Matches `SHA256SUMS` / audit REPORT |
|---|---:|---|---|
| `evidence/feb28_market_trades.jsonl` | 10,489,820 | `3891c17857715ab5f61d74142faa93a52f58fc2d9719cddd2de60365a6889429` | yes |
| `evidence/feb28_noyes_descriptive.json` | 1,534 | `5cd081c264f902f09d1bfdd1c6e56797518196e9f9e5c798cb595ad1b8e9e649` | yes |
| `evidence/feb22_25_traders_createdAt.csv` | 59,901 | `7e145d5fc427aee8513fc828022c58bf508e5479e0f766ce4237dcb89560b303` | yes |
| `/Volumes/VERBATIM HD/phi-x/feb28.jsonl` | | `3891c178…9429` | identical to the archived tape |
| `/Volumes/VERBATIM HD/phi-x/feb22_25.csv` | | `7e145d5f…b303` | identical to the archived CSV |

## 4. Independent recount of 20/36 vs 16/733

Script: `scripts/recount.py` (sha256 `bc358961…3d82`), standard library only. It streams the tape line by line from
`git show`, reads the CSV for population and cohort flag, and **never reads the counts of
`feb28_noyes_descriptive.json` or of the study's `feb28_recheck.json`**. It ends with asserts on 20/36 and 16/733.

Command:

    git show origin/main:research_notes/independent-forensic-audit-2026-11-08/evidence/feb28_market_trades.jsonl \
      | python3 -I scripts/recount.py createdAt.csv

Result (SELF-CHECK OK):

| | value |
|---|---|
| Tape rows | 42,000 (26,957 BUY, 15,043 SELL; 22,371 Yes, 19,629 No) |
| Band | 2026-02-21T18:48:58Z → 2026-02-28T09:32:33Z |
| Distinct wallets in tape | 13,003 |
| CSV rows | 769, all `createdAt` within 22-25 Feb 2026 (0 outside), 36 with `in_g38=True` |
| Population present in tape | 769 = 36 cohort + 733 other |
| Ties (first NO buy and first YES buy in the same second) | 0 |

| Group | n | NO then YES | YES then NO | YES only | NO only | no BUY |
|---|---:|---:|---:|---:|---:|---:|
| Cohort | 36 | **20** | 0 | 15 | 0 | 1 |
| Other | 733 | **16** | 20 | 309 | 354 | 34 |

Identical to the archive and to the study's reading 1.

## 5. Definitions checked

- **Market:** "US strikes Iran by February 28, 2026?", condition `0x3488f31e…7f20`. One market only.
- **Window:** the archived band above. It is not the market history: it is the newest 84 pages of 500 rows of the
  newest-first stream. The study's complete v2 tape shows 59,163 fills missing inside the same band and 217,997 fills
  in the whole market (`feb28_recheck.json`). The band is therefore **censored**.
- **Population:** gamma `createdAt` on 22-25 Feb 2026 **and** present in the band. Selected after the outcome; the 36
  are not a draw from the 769. The CSV only holds those 769 profiles; the other wallets of the tape are not in the file
  (the audit counts 1,262 band proxies with no profile, HTTP 404).
- **Chronology:** earliest `side=BUY` of outcome `No` strictly before earliest `side=BUY` of outcome `Yes`, this market,
  this band. SELLs are ignored by the classifier.
- **Status:** descriptive, no p-value (audit REPORT section B1; G38 tier audit point 4).

### Indicator vs effective liquidation followed by a reversal

The indicator only orders two first purchases. It does **not** say that the NO position was closed, nor that the net
exposure changed sign. Descriptive split of the NO-then-YES accounts (`scripts/liquidation.py`, sha256 `38cdc8ed…b8f2`),
using sells inside the band before the first YES buy:

| Group | NO-then-YES | NO sold ≥ 95 % of band NO buys before first YES buy | partly sold | no NO sell (both sides held) |
|---|---:|---:|---:|---:|
| Cohort | 20 | 20 | 0 | 0 |
| Other | 16 | 9 | 3 | 4 |

Limits of this split: the band is censored, so inventory bought before the band, splits, merges and conversions are
invisible; "sold ≥ 95 %" is band-relative, not a full position. It is a reading, not a test, and it was computed after
seeing the cohort. It supports the wording "NO bought, then sold, then YES bought in the same market" for the 20 in the
band. A **reversal of exposure** in the payoff sense of `INTERVAL_LOGIC.md` still needs the wallet's positions in the
sibling deadline markets of the same event family; that has not been rebuilt for this cohort.

## 6. Data available and coverage

| Data | Location | Status |
|---|---|---|
| Archived 42k tape, CSV, descriptive JSON | git `main` | archived, SHA verified |
| Complete v2 tape of the Iran market | `/Volumes/VERBATIM HD/phi-x/feb28_v2.sqlite` | local only; SHA `1f636371…1015` **matches** the study manifest |
| Primary sample tapes (763 markets) | `…/phi-x/tapes.sqlite` | local only; SHA `63c85df4…15b3` **matches** |
| Replication tapes (1,579 markets) | `…/phi-x/tapes2.sqlite` | local only; **mismatch**: manifest says 438,779,904 bytes / `45209773…34fc`, disk has 763.6 MB / `b6562706…0768` (see 7) |
| `tapes_all.sqlite` (1.2 GB) | `…/phi-x/` | not in any manifest; role unknown |
| Population and labels | git `main`, `research_notes/early-detection-2026-11-13/study/derived/` | archived (frozen 13-14 Nov) |

Version coverage:

- **Trade source:** data-api `/v2/trades` (`v2` is the API version), executed fills only.
- **Exchanges:** the on-chain decoder in `phi_monitor/chain.py` covers CTF Exchange **V2** and NegRisk Exchange **V2**
  only. No V1 exchange decoder exists in the repository. Whether the data-api serves fills from V1-era contracts for
  every market of the 2025-2026 population was **not verified** here.
- **NegRisk:** fills on NegRisk markets come through the API; **conversions, splits, merges and redemptions are not
  reconstructed anywhere** (declared limit of the study: exposure from fills is an upper bound on inventory).
- **Order book:** no historical book archived; execution can only be read at the last fill price.

## 7. Gaps and contradictions found

1. **Contradiction inside the existing study:** `FINDINGS.md` line 62 says "175,997 [fills] in the market", while
   `README.md`, `data_manifest.json` and `results/feb28_recheck.json` say **217,997**. The JSON is the result file; the
   FINDINGS figure looks like a typo. Not corrected (frozen study, other session's directory).
2. **Stale manifest:** `tapes2.sqlite` on disk no longer matches the manifest written at 21:52 UTC; the replication
   commit (22:41 UTC) did not refresh it. The replication results cannot be re-hashed against their declared input.
3. **Funding-linked collective shifts (S5):** `UNRESOLVED`, never measured at population scale.
4. **Execution:** no book; the "not executable" finding is gross, fees and gas excluded.
5. **Large markets:** the sample excludes volume ≥ 1 M USD, where coordinated positions would sit.
6. **Inventory:** splits, merges, NegRisk conversions and redemptions are invisible; V1-era coverage not verified.
7. **Interval logic:** the payoff-vector reading of `INTERVAL_LOGIC.md` was applied to the sample (60 events, F-007),
   not to the 36-account cohort across sibling deadlines.
8. **Disk:** 1.1 GB free. Any new collection is blocked until space is freed (decision for Benjamin).

## 8. GO / NO-GO

| Question | Answer |
|---|---|
| Archived baseline sound (presence, SHA, 20/36 vs 16/733)? | **GO** |
| Start a new detector study on the same branch name? | **NO-GO**: it already exists, frozen and `DONE` |
| Reuse existing reconstructions? | **GO**: `reproduce_feb28.py`, `build_alerts.py`, the local tapes (2 of 3 hashes match), `counterparty_graph.py`, `phi_monitor` |
| New data collection now? | **NO-GO**: disk below the 13.5 GB floor |
| Create the branch / worktree? | **Blocked** by `protocol_guard`; to be run by Benjamin |

Decisions for Benjamin before mission 2: (a) treat the existing study as the baseline and define missions 2-7 as
follow-ups on its open items (S5 funding graph, book recorder, ≥ 1 M USD markets, splits/merges/conversions), or close
it and open a new study; (b) whether to fix items 1-2 by an amendment; (c) free disk space.
