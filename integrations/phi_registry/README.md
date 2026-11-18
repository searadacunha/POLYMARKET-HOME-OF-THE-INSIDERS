# PHI registry (pilot)

A queryable index of what this repository has already established, and a lock that stops two agents from researching the
same thing at the same time. Standard library only, one SQLite file, no network. The measurements, the Supabase decision
and the limits are in [research_notes/registry-pilot-2026-11-18/REPORT.md](../../research_notes/registry-pilot-2026-11-18/REPORT.md).

It adds nothing to the evidence: every row is derived from files already in git, with its path, and can be rebuilt.

## Use

```bash
cd integrations/phi_registry
export PHI_REGISTRY_DB=~/.local/state/phi-registry/registry.sqlite3     # default if unset

python3 phi_registry.py build --repo ~/Projects/Polymarket-Home-of-the-Insiders --ref origin/main
python3 phi_registry.py check 0x<40 hex>          # where this address already appears, and which findings cite it
python3 phi_registry.py check funding purchase    # findings containing every word (exact words: a synonym is missed)
python3 phi_registry.py check maduro-iran         # an investigation id lists all its findings and open items
python3 phi_registry.py verify --repo . --sample 25   # integrity and provenance against the commit the registry names
python3 phi_registry.py brief                     # levels, refuted findings, "missing to conclude", task queue
python3 phi_registry.py tests                     # archived statistical tests, counted per study
python3 phi_registry.py digest                    # sha256 of the derived content: same commit, same digest
```

`build` reads a git ref from git objects (never the working tree), so a dirty clone or another branch cannot leak into it,
and it replaces every derived table in one transaction. An appearance of an address in a file is a pointer to prior work,
never a link between accounts (see [METHODOLOGY.md](../../METHODOLOGY.md)). Only full `0x` + 40 hex addresses are indexed:
abbreviated forms (`0xa8e6…74a5`), Solana addresses, handles and zero-padded log topics are not.

## Duplicate-work guard

```bash
python3 phi_registry.py task add wallet 0x<40 hex>        # same kind and subject = same task; reports prior work
python3 phi_registry.py task claim my-agent --ttl 900     # one task or null; keep the returned "token"
python3 phi_registry.py task heartbeat <task> my-agent <token>
python3 phi_registry.py task done <task> my-agent <token> F-007
python3 phi_registry.py task fail <task> my-agent <token> "rate limited"
```

A task is held by one agent for `ttl` seconds. If the holder disappears the lease expires and the next `claim` takes it
over; the token (the attempt number) makes every later call from the old holder fail, so a task completes once. A failure
re-queues the task until `max_attempts` is used up, then closes it as `failed`. Every transition is appended to
`task_events`. The guard stores no findings and no results: a result is a finding written the usual way
(`investigations/<id>/FINDINGS.md`), and `result_ref` only points at it. It does not replace `JOURNAL_AGENTS.md`.

## PostgreSQL and Supabase

`supabase/migrations/` holds the SQL, in the layout the Supabase CLI expects. The first two files are portable (SQLite and
PostgreSQL run them unchanged); `*.pg.sql` adds row level security and the task functions and is PostgreSQL only.

```bash
python3 phi_registry.py export-sql > /tmp/registry.sql          # derived tables; add --tables ...,wallet_mentions for the index
for f in supabase/migrations/*.sql; do psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f "$f"; done
psql "$SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f /tmp/registry.sql
```

The tests apply exactly these files to a throw-away PostgreSQL 15 on a local socket, with stand-ins for the `anon`,
`authenticated` and `service_role` roles. That checks the SQL, the grants, the policies and the claim functions. It does
**not** check a hosted project: no Supabase project was used, so `supabase db push`, the Data API settings, network latency,
quotas and the free plan's pausing are untested. No code here reads a Supabase key or opens a connection.

Rules if it is ever deployed: tasks and results of unpublished work go to a private project, never to a public one; the
wallet index stays local; the service key stays out of git, shell history and CI logs.

## Tests

```bash
python3 -m unittest discover -s tests -v          # 24 SQLite tests, offline, a few seconds
PHI_REGISTRY_PG_BIN=/opt/homebrew/opt/postgresql@15/bin python3 -m unittest tests.test_postgres -v   # 10 PostgreSQL tests
python3 bench/bench.py --repo . --ref origin/main --out /tmp/bench.json                              # the measurements of the report
```

The PostgreSQL tests are skipped unless server binaries are on `PATH` (`initdb`, `pg_ctl`, `psql`), in Homebrew's usual
folders, or named by `PHI_REGISTRY_PG_BIN` (on Debian or Ubuntu: `/usr/lib/postgresql/<version>/bin`; `none` skips them). The
continuous integration step therefore runs the SQLite tests only.

## Limits

- The index is a snapshot of one commit: rebuild after a merge. `check` answers "has this been seen", not "is it true".
  Word search needs the exact words of a finding (a search for "signal" does not return one that says SIG_HIST): to conclude
  about an investigation, list it whole with `check <investigation id>`.
- `hypothesis_tests` reads three archived register formats and skips every other file of the same name. It counts what the
  repository archived; whether tests form one family is decided in a frozen plan, so the tool pools nothing.
- A full `build` of the 7,338 text files of `origin/main` reads 0.48 GB, holds the address index in memory (peak about 0.6 GB)
  and produces a 150 MB file. Into a file it goes through SQLite's write-ahead log first, so it can transiently need about
  twice that on disk (not measured); `PHI_REGISTRY_DB=:memory:` has no such cost but keeps nothing.
- Dedup keys fold case with the database locale: ASCII subjects (addresses, ids, English text) behave the same on SQLite
  and PostgreSQL; accented capitals may not.
