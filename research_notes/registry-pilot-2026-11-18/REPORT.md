# Registry pilot: does a shared database, Supabase in particular, help these investigations?

Audit of commit `874292b` (`origin/main`, 18 November 2026), then the smallest pilot that could measure a gain. Nothing was
deployed, pushed or merged. Every figure below is in [results/bench.json](results/bench.json) or
[results/integrity.json](results/integrity.json) and is replayed offline by [verify.py](verify.py); figures read from other files
name their source.

## Verdict

- **Supabase is not adopted.** The audit found no function of this repository that a hosted database would improve today. The
  raw histories are far over the free plan's 500 MB per project (one local cache alone is 7.9 GB), the three structured Markdown
  files of each investigation total 130 KB, and every agent this audit found runs on one machine. A hosted copy would add a second source of truth, a key to guard
  and a free plan that pauses when idle, for no capability the files and local databases lack.
- **Structure did give a measured gain, and it runs locally.** An address index built from git objects (415,288 addresses,
  rebuilt in 10 s, same commit, same digest) answers "has this address been seen, and where" in 0.02 ms in process against
  1.17 s for `git grep`, with identical answers on 45 of 45 sampled addresses. A claim guard for agents (8 agents, 400
  tasks, 10 % crashes) completed every task once and lost none, where a check-then-act model started 141 to 216 tasks twice.
- **The SQL is Supabase-ready and tested on PostgreSQL 15** (10 tests: same columns as SQLite, grants, row level security,
  claim functions under concurrency). No Supabase project exists, so the hosted behavior is untested, not assumed.
- **No signal is claimed.** Section 6 maps the six families of the brief to what the repository already tested: two
  negative, one partly tested, one that anticipates price but whose capture was tested and not demonstrated, two untested.

## 1. What was read

The whole tree of `origin/main` from git objects (8,102 tracked files; the 7,338 text files, 479 MB, were scanned), `AGENTS.md`, `CONTRIBUTING.md`,
`METHODOLOGY.md`, `README.md` (not touched), the generators and validators in `scripts/`, the monitor and engines under
`monitoring/` and `integrations/`, and, read only, the local SQLite stores of the services running on the machine. The
working tree of the central clone was not used: it sits on another branch with staged work from another session.

## 2. What the audit found

| Question | Finding | Source |
|---|---|---|
| Where is data stored? | In git: 8,102 files, about 650 MB of text (5,422 JSON, 275 CSV, 77 JSONL, 715 gzip). Outside git: raw data reported at 19.3 GB (not re-measured, the disk was not mounted). Local SQLite: PolySentinel, 7.9 GB, a content-addressed cache of API responses (about 2.57 M contents, 2.54 M history references, 1.63 M object references, 618 k indexed trades); TriAgent, 115 MB, 26 tables; the monitor's store. | `git ls-tree`, `sqlite3 -readonly` on the stores |
| How are wallets tied to markets? | There is no single table. Three SQLite schemas overlap: the monitor (`fills`, `tokens`, `funding`, `owners`), TriAgent (`trades`, `wallets`, `edges`, `known_addresses`) and PolySentinel (`trade_index` plus the cache). Investigation folders keep CSV and JSON with study-specific columns. | `monitoring/phi_monitor/store.py`, store schemas |
| How are signals produced? | `monitoring/phi_monitor` (ignition and tape features), `integrations/quantitative_engine`, PolySentinel's engine, TriAgent's alert score (labelled a selection signal, not evidence), and per-study code (collective exposure S1 to S4). | code under those folders |
| How are investigations archived? | `investigations/<id>/` with four Markdown files in a strict format and a manifest; a validator refuses a finding whose numbers, addresses or hashes are absent from the files it cites; `MASTER_REPORT.md` and `INVENTORY.md` are generated. Today: 17 investigations, 115 findings (33 CONFIRMED, 18 SUPPORTED, 6 HYPOTHESIS, 25 REFUTED, 33 UNRESOLVED), 173 evidence rows, 130,523 bytes of text. | `CONTRIBUTING.md`, `scripts/validate_evidence.py`, `scripts/build_master_report.py` |
| How are results evaluated? | Frozen plans with a lock (12 `PROTOCOL.lock`, 14 `analysis_plan.md`), 13 copies of a `registre.py` test register, positive controls, blind audits. The test registers of the studies come in four JSON shapes; the pilot reads three. | `METHODOLOGY.md`, file census |
| How do agents exchange information? | Through git (`AGENTS.md`: fetch, merge, own investigation folder, pull requests), a local per-project journal that stays out of git, a shared notes folder outside the repository, and, for the autonomous system, TriAgent's SQLite store (jobs, leases with a unique active lease per work item, leads with a dedup key, findings with an evidence level, an event bus towards n8n). In its first 11 days TriAgent closed 55 of its 139 leads as duplicates and finished all 175 of its leases. | `AGENTS.md`, TriAgent store |
| Which components would benefit from Supabase? | None measurably, see section 3. | |

Two redundancies stand out and are not caused by any missing database: the three overlapping wallet and trade schemas, and
the four register shapes. Both are better fixed by a shared local schema (DuckDB or Parquet over the existing files if joins
across millions of rows are ever needed) than by a hosted one.

## 3. Supabase against what exists

Free plan figures come from Supabase's documentation as found by search on 18 November 2026 and were not fetched page by
page: [pricing](https://supabase.com/pricing), [pausing](https://supabase.com/kb/faqs/platform/free-project-pausing),
[row level security](https://supabase.com/docs/guides/database/postgres/row-level-security),
[API keys](https://supabase.com/docs/guides/getting-started/api-keys). The pricing page was reported as old: check it before
deciding. Reported: 500 MB database and 2 projects on the free plan, a project paused after a week of low activity, no automatic
backups or point-in-time recovery on free (daily backups on Pro, listed at 25 USD a month), a restriction when the database
exceeds its quota, tables of an exposed schema readable and writable without row level security, `service_role` bypassing
it, and the `anon` and `service_role` keys being replaced by publishable and secret keys by the end of 2026.

| Function | Today | What Supabase would add | Cost or risk | Decision |
|---|---|---|---|---|
| Raw histories and caches (GB) | SQLite, JSONL, gzip, git | nothing; does not fit 500 MB | a paid plan to host data that stays local anyway | keep |
| Wallet and market analytics | SQLite, scripts | nothing; joins are faster beside the data | network round trips | keep (DuckDB over files if needed) |
| Findings, evidence, negative results | generated Markdown, validated | remote queries | second source of truth next to `FINDINGS.md` | local registry, derived, rebuildable |
| Address lookup across the repository | `git grep`, 1.17 s | nothing a local index lacks | the index (150 MB) would use about a third of the free quota for no gain | local index |
| Agent task claims | TriAgent leases (one host), journal reading for other sessions | claims across hosts | key handling, pausing when idle | local guard now; Supabase only if agents run on a second host |
| Dashboard and alerts | TriAgent page, n8n, notifications | Studio and realtime | another surface to secure | none needed |
| Off-machine copy | phi-backup, GitHub (degraded at the time of writing) | a small copy of derived tables | free plan has no backups and pauses | not a backup; derived tables rebuild from git anyway |

### Overlap with TriAgent's SQLite store

TriAgent (draft pull requests, not on `main`) keeps its own SQLite file. Compared by schema and by content on 18 November:

| Registry piece | TriAgent counterpart | Measured overlap | Decision |
|---|---|---|---|
| `investigations` | `inventory`, 68 rows, built by parsing the generated `INVENTORY.md` | 15 of the registry's 17 investigation ids are in it | keep: the registry reads `STATUS.md` with the repository's own parsers; TriAgent could read it instead of parsing a second time |
| `wallet_mentions` | `known_addresses`, 26,053 rows, 7,884 distinct addresses (`.md`, `.csv`, `.json` up to 5 MB under `investigations/` and `research_notes/`) | all 7,884 are in the registry; the registry holds 415,288, so 98.1 % are unknown to TriAgent | keep: TriAgent's index is a strict subset of the registry's. Replacing its scan by the registry is a later simplification, not made here |
| `agent_tasks`, `task_events` | `jobs`, `leases`, `events`, `runs` | same concept (one active lease per work item, a dedup key), but TriAgent's cover only its own missions on one host | keep: it serves sessions that are not TriAgent missions. Nothing is written into TriAgent's tables |
| `findings`, `evidence`, `open_items`, `hypothesis_tests` | none: TriAgent's `findings` and `evidence` hold what its agents produced and fetched, under the same names but another meaning | none | keep |

Duplicated code was removed where it existed: the `STATUS.md` section reader now comes from `scripts/build_master_report.py`, and
the finding and status parsers are `scripts/phi_lib.py`'s. What stays duplicated is deliberate: a public index pinned to a commit
beside a private working store.

Adopting it later would be justified by one of: agents running on a second machine or in the cloud; a reader other than the
owner who needs live access; a measured need for remote queries. None holds now. What would then be measured, which this pilot
could not: latency from the agents' machine, behavior after a pause, the real limits of the plan in force, key rotation.

## 4. The pilot

One module, [phi_registry.py](../../integrations/phi_registry/phi_registry.py), standard library only, one SQLite file.

- **Derived tables**, rebuilt from one commit read from git objects: `investigations`, `findings` (with the five levels),
  `open_items` (contradictions, missing to conclude, monitoring), `evidence`, `finding_addresses`, `wallet_mentions` (an
  address and the scopes where it already appears), `hypothesis_tests` (archived tests, counted per study, pooled by nobody).
  Facts and hypotheses stay distinct through the repository's own `level`; refuted tracks stay as rows. The parsers are
  `scripts/phi_lib.py`'s, not new ones.
- **Operational tables**: `agent_tasks` and `task_events`. A task is a unit of research with a dedup key; a holder has a lease
  and a token that fences later calls; a failure re-queues until the attempts are used; a crashed last attempt is closed, not
  retried forever. It stores no result: a result is a finding written the usual way, `result_ref` points at it.
- **Commands**: `build`, `check` (an address, words, or an investigation id), `brief`, `tests`, `verify` (integrity and provenance),
  `digest`, `export-sql`, `backup` and `task add|claim|heartbeat|done|fail|stats`.
- **SQL** in `supabase/migrations/`: two portable files (SQLite and PostgreSQL) and one PostgreSQL file with row level
  security and the claim functions. Export to PostgreSQL is a generated SQL script run through `psql`; the Python never
  opens a network connection and reads no key.
- **Not built, on purpose**: wallet clusters, funding relationships, wallet activity, markets and signal performance tables
  (the data lives in files and TriAgent, and no question asked here needed them), a vector index (one recall miss of the exact
  word search was observed, section 7; the cheaper fix was applied), a dashboard.

## 5. Measured results

Machine: macOS 14.6, 8 cores, Python 3.14, SQLite 3.54, PostgreSQL 15.17 (local, unix socket only).

| Measure | Before | After | What it shows |
|---|---|---|---|
| Prior work on an address, 45 sampled in three strata (1, 2 to 3, 4 or more scopes) | `git grep` of the commit: median 1.17 s | 0.02 ms in process, 73 ms by command line (Python start-up) | same information, about a second saved per lookup |
| Agreement of the two answers | n/a | 45 of 45 identical (scopes and file counts) | the index is complete and the importer correct, on these 45 |
| Size of an answer | 329 bytes (paths and counts) | 402 bytes (scopes, counts, citing findings) | no saving; the registry adds which findings cite the address |
| Build | none needed | 10.4 s, reads 7,338 files and 479,238,986 bytes, peak memory 590 MB, file 150 MB | the cost of the index |
| Reproducibility | n/a | two builds of one commit, one digest (`f3dc49fd…`) | the derived tables are a pure function of the commit |
| Tasks started twice, 400 tasks, 8 agents | check then act on a shared journal (a model, not real agents): 141, 183, 216 with 1, 5, 20 ms between reading and writing | 0, with 42 expired leases taken over and 10 % of claims abandoned; 0 lost; 5.9 s | an atomic claim removes the race window; real agents think longer than 20 ms |
| PostgreSQL | n/a | 10 of 10 tests: same columns, constraints, `anon` refused, `authenticated` read only, task functions closed to both, a grant alone shows no row without a policy, 80 tasks over 8 clients with crashes, none twice | the SQL and access model work on PostgreSQL 15 |
| Integrity and provenance (`verify`) | none | 5 checks pass on the real registry: stored digest equals the tables, foreign keys hold, finding addresses appear in their findings, a rebuild of the commit gives the stored digest, and 300 sampled address rows equal an independent `git grep` in file count, first reference and scope ([results/integrity.json](results/integrity.json)) | the index is exactly what its commit says, and it detects a manual edit or a forged digest (tested) |
| Footprint against the free plan's 500 MB | n/a | derived tables 0.58 MB in PostgreSQL; address index about 161 MB (loaded on every 32nd row, scaled, not a full load) | fits, but the index has no reason to be remote |

What these numbers do not show. No real agent session was timed, so no saving in tokens or minutes is claimed. The one
second saved per lookup matters little unless lookups are frequent. Only 18 of the 415,288 addresses are cited by a finding
(findings mostly cite abbreviated addresses, which the index does not read), so for almost every address the answer is
"seen in these folders", not "established". 174,124 addresses appear in two or more scopes and the widest in 26: that is
what shared infrastructure addresses look like, and an appearance is never a link between accounts. Nothing was measured on
a hosted project: no latency, no quota, no pause.

## 6. Signals: what the repository already tested

Built from the registry's findings and from [EDGE_VERDICT.md](../../EDGE_VERDICT.md). No new
test was run: a new one needs a frozen plan, and the tracks below carry negative or unresolved results.

| Family of the brief | Already tested | Result | Open |
|---|---|---|---|
| Coordinated accumulation of positions | `collective-exposure-shifts` (naive buy consensus S2, 392 alerts in the primary sample); alert-following in `EDGE_VERDICT.md` (45 alerts, +3.5 points, p = 0.33; a recount of 2,885 alerts, excess -2.65 points) | no excess over price: `collective-exposure-shifts:F-003`, `F-004` REFUTED | an edge below about 4 points is not excluded |
| Collective exposure shifts | same study, rule S4 (3 wallets each +500 USD within an hour), replication on 1,579 markets and 266 alerts | `F-005` not executable (negative before cost), `F-009` alerted side wins less than its price implies in TEST, `F-011` that sign comes from the de-duplication rule (time-honest +1.2 points, interval -6.8 to +9.3) | `F-013` capacity and fillable execution UNRESOLVED; no archived order book |
| Funding flows between wallets | funding less than an hour before the first buy: `ballon-dor-wallets:F-006`, `ballon-dor-flow-trace:F-010` REFUTED (9/11 against 32/39 fresh accounts, p = 0.69); `changenow-polymarket:F-002` link real but tiny | no predictive use found | financially linked collective shifts: UNRESOLVED, no funding graph was built at that scale |
| Activity before price moves | `maduro-iran:F-006` none of 8 preregistered signals exploitable out of sample (288 comparisons) REFUTED; `F-007` SIG_HIST precedes moves (LEAD60 30 % against 10 to 13 % for matched buys, held in VALID and TEST) SUPPORTED | the lead exists, the capture does not: `F-009` the second buy offers no executable window (-0.7 % net in TEST) REFUTED; `F-008` the return over all alerts is UNKNOWN with public data (phase 10: no strategy meets the 10 preregistered criteria, the next buyer arrives in 2 to 4 s, limit orders fill at most 19 % of the time); `EDGE_VERDICT.md`: a round trip costs 0.1 to 1.9 cents a share before any edge | depth is visible for 5 to 8 % of alerts; `F-010` the live infrastructure was not validated |
| Reappearance of historical behaviours | `counterparty-network:F-003`, `polysentinel:F-003` | UNRESOLVED, not measured | untested |
| Divergence between price and participants | only "alerted side against its own price" (T1 of the study above, null); order-book imbalance in `EDGE_VERDICT.md` NON_EXPLOITABLE | partly | untested as a price against cohort positioning question |

Three studies could follow. [NEXT_STUDY.md](NEXT_STUDY.md) compares them on interpretability, cost, power to refute,
out-of-sample testing and comparison with the price alone, and ranks them: (1) replication of the external sports
calibration claim at T-7d, free public data and the best chance of an interpretable answer; (2) financially linked collective
shifts, which needs a funding graph and is probably underpowered; (3) capture of the SIG_HIST lead with archived books, the
costliest and the least likely to yield an answer. None was started, and a rank is not a claim about any of them.

## 7. Not done, and why

- The word search is exact. The first coverage table of section 6 missed `maduro-iran:F-009` because a search for "signal" does
  not return a finding that says SIG_HIST; it was corrected after reading that investigation's findings. `check <investigation>`
  now lists all findings of an investigation, and the cheaper fix is to read an investigation whole before concluding about it.
  This is one observed recall miss, not a demonstrated need for a vector index, which stays out.
- No dashboard: nothing in the audit asks for one, and TriAgent already serves a local page.
- No project on Supabase, no `supabase db push` (the CLI is not installed), no Data API settings: untested.
- No wallet cluster, funding relationship or signal performance tables: designed in section 4, not populated.
- `hypothesis_tests` is a count of what is archived: the census study's register holds 28 rows and some studies declare more
  comparisons than they archived. No pooled correction is computed, because rows of one study are often variants of one test.
- The benchmark was sized to leave the machine's free-space margin alone (builds in memory, the index loaded into PostgreSQL
  on every 32nd row), which is why the size of the index in PostgreSQL is an extrapolation.

## 8. Decisions that belong to the owner

1. Whether to publish this branch: it adds `integrations/phi_registry/`, this folder, and one step in
   `.github/workflows/repository-integrity.yml`. Nothing else changes, `README.md` and the publication baseline included.
2. Whether sessions should use the local registry as a shared lookup and claim point (default file
   `~/.local/state/phi-registry/registry.sqlite3`, rebuilt after each merge).
3. Whether to open a Supabase project at all, and if so a private one for tasks, never the public one.
4. Whether to freeze the first-ranked study of `NEXT_STUDY.md` (stage 1 only, free data), or another.

## Reproduce

```bash
python3 -I research_notes/registry-pilot-2026-11-18/verify.py                     # replay of the figures from results/bench.json
cd integrations/phi_registry && python3 -m unittest discover -s tests -v          # 24 SQLite tests, plus 10 PostgreSQL tests when server binaries exist
python3 bench/bench.py --repo . --ref 874292b4c841811585c5a255ecf431da4c020305 --out /tmp/bench.json
python3 integrations/phi_registry/phi_registry.py --db /tmp/r.sqlite3 build --repo . --ref 874292b4c841811585c5a255ecf431da4c020305
python3 integrations/phi_registry/phi_registry.py --db /tmp/r.sqlite3 verify --repo . --sample 300      # results/integrity.json
```
