# Harness

Keeps investigations going across crashes, restarts and days, with results that cannot enter memory on an agent's word. It sits beside the collector and the shadow engine, reads them, and changes neither.

```
              collector database (read-only)
                          |
   PLAN  planner.py   ->  queue of tasks with stable keys, dependencies, priorities
   ACT   pipeline.py  ->  one process per task: the engine's own detection and dossiers, then a bundle of raw rows
   VERIFY verify.py   ->  separate process, run twice, recomputes everything from the bundle
   LEARN memory.py    ->  verdict, memory and alert commit together; next run retrieves only what it needs
   RECOVER recover.py, runner.py -> leases, fencing, retries, circuits, resource stops
```

## Three components, not six

| Component | What it is | Model? |
|---|---|---|
| Orchestrator (`runner`, `planner`, `recover`) | Ordinary code, one bounded passage at a time | No |
| Proposer (`agent`) | One call to Claude Code, only when the queue is empty and the budget allows. No tools, no session, no MCP. It returns JSON, and a schema decides what counts | Yes, off by default |
| Verifier (`verify`) | Ordinary code in its own process. It imports nothing from the detector or proposer | No |

Data work, memory and recovery are deterministic, so splitting them into agents would add cost and failure modes with no measurable gain. A research proposer that could spawn others is excluded by construction: it has no tools, and a nested call is refused. For a human-led audit, the existing agents in `~/.claude/agents/` still apply.

## Investigating a case

Each step is a task, and each commits its output with its checkpoint.

1. `discover` reads new rows from the collector, and runs `run_cycle` from the engine in one transaction with the cursor. Decisions use the time the rows were known. Catalogue facts are the latest known, so rows more than `max_lag_s` behind live only warm the comparators, open no case, and are counted in `status`.
2. `case_dossier` calls the engine's `dossiers.build`.
3. `case_funding` traces flows if configured, and keeps only links between flagged wallets, each at the level its state allows.
4. `case_receipts` reads receipts one per commit.
5. `case_bundle` gathers raw rows, wallet histories, control units, collection gaps and the number of pairs screened in the 24 hours before the decision, a count frozen when the case opens.
6. `case_verify` runs the verifier twice, under different hash seeds. Different bytes mean the result is not reproducible.
7. `case_conclude` sets the verdict, updates memory and writes the alert atomically.

An alert exists only after every check passes. It lists its transactions with links, what was rare and among how many, what could not be tested, and what is not established.

## What the verifier checks

| Check | Fails when |
|---|---|
| `integrity` | Bad identifiers, a row observed before it happened, amount differs from size times price |
| `no_future` | A row was known only after the decision time |
| `chain` | The wallet's own order, on chain, contradicts the row. No receipt, or a block not yet final, leaves it open |
| `relations` | A link claims more than its evidence. Common control can never be claimed from public data. A swap service links deposit to withdrawal only with a verified record |
| `language` | The statement names an insider, an owner or a proof |
| `claim_matches` | A number reported by the engine exceeds what the raw rows show |
| `dossier` | The engine's own file checks found a contradiction |
| `coverage` | A collection gap overlaps the entry window: stays open, since the alternatives cannot see there |
| `controls` | Rarity against units in the same price zone, times pairs screened in 24 hours, expects too many false positives. A corroboration claim rests on its second rarest wallet |
| `placebo_events` | Too many other events hold a unit this extreme |
| `alternatives` | Public news before that wallet's own entry, both sides or selling back, a basket, a habit of this size, or following a visible move explains the wallets. A resolution date after entry says nothing about when the news came out, so it stays untestable |
| `robustness` | The finding does not survive losing rows, a smaller measure, its largest fill, or one wallet |

Four outcomes, as in `signal_engine.case_checks`. `PASS` needs all of them. Too little data is `INCOMPLETE`, not a rejection, so the verifier cannot pass a case by being unable to test it, nor reject one for the same reason. The absence of a public source is `NOT_TESTABLE` and appears on the alert.

Population hypotheses, where a feature predicts returns, are tested on wallets and dates the proposer did not see, with `temporal_group_split` from the existing bench. Events are the statistical unit. The number of tests comes from the registry, not from the proposer, and a positive and a negative control run on each test.

## Guarantees enforced below the code

- `validated` needs the latest verification to be a pass by someone other than the proposer: a SQLite trigger refuses anything else. Verifications are append-only. A rule becomes active only with a gate report.
- A worker that lost its lease cannot write: each write checks owner and attempt in its transaction.
- The sandbox profile `deploy/deny_production.sb` makes the kernel refuse writes to production.

## Memory

SQLite, full-text search, one file, no weights. A fact keeps its source. A changed source makes it `stale`, and two facts that disagree are both `contested`, shown first, and resolved by no one but a person. Rejected ideas are stored by what they test rather than how they are worded, so rephrasing finds the rejection, and only new evidence in the spec reopens one.

`python -m harness context --query "..." --budget 6000` gives a briefing under that budget. Long tool outputs go through Stop-Bullshiting's `sbs compress`, with receipts under the harness root, and its absence falls back to a saved original with head and tail.

## Changing a detection rule

`promotion.gate` compares a candidate with the active rule on a holdout it was not tuned on. It requires a proven gain (exact McNemar) and no loss of recall or rise in false positives, counts each look at the holdout, and refuses after three. There is no ground truth on real data, so labels come from injected cases. The gate moves a pointer in the harness's database. Production's rules are changed only by a dated amendment, as before.

The system proposes parameters and hypotheses. It does not edit its own code.

## Recovery

| Event | What happens |
|---|---|
| Task crashes or is killed | Attempt spent, backoff, resumes from its checkpoint. Quarantine after the limit, dependents follow |
| Supervisor killed | The kernel frees the lock, and the next passage reclaims the task. An orphaned worker cannot write and stops at its next commit, or at its own alarm |
| Source down | Waits without spending attempts, other work continues |
| Source answers nonsense | Never stored. Retried, then quarantined |
| Same failure across tasks | Circuit opens for that kind, for a cooldown |
| Same task or hypothesis planned again | Nothing happens: keys and fingerprints are unique |
| Budget, disk, memory, load, collector not normal | The passage stops or the task waits, and nothing is deleted. A step larger than the whole daily budget is quarantined instead of waiting forever |
| Collector database unreadable | The passage stops and says so; it does not read as an empty queue |
| Two passages at once | The second exits at once |

## Commands

```sh
python -m harness run --root DIR --seconds 240     # one passage
python -m harness status --root DIR                # tasks, hypotheses, quarantine, contested facts, usage
python -m harness context --root DIR --query TEXT  # the briefing
python -m harness propose --root DIR --file F.json # queue a hypothesis by hand
python -m harness demo --root DIR                  # synthetic collector data with five planted cases
```

See [integration](HARNESS_INTEGRATION.md).

## Measured

On a demonstration collector of 3,117 synthetic trades, so these show mechanics, not detection power. Everything ran at nice 19 beside a loaded machine.

| Measure | Result |
|---|---|
| One run | 124 tasks in 27 s, 0.22 s per task, supervisor peak 42 MB, 6 MB of state, 0 tokens |
| Worker killed at 4 points, supervisor killed, SIGTERM, 4 concurrent passages | Same conclusions as an uninterrupted run, byte for byte |
| launchd job, passage killed twice | 3 starts, same conclusions, 124 tasks done, none quarantined, job removed, no process left |
| Source down, source answering nonsense | Waits without spending attempts; quarantine, nothing stored as data |
| Engine cases on noise, 5 seeds of 14 days | 67 opened, 0 false alerts, 47 rejected, 20 left open |
| Decoys (news first, both sides, tampered receipts), 5 seeds | 15 of 15 rejected |
| Strong planted cases, 5 seeds | 8 of 10 validated; 2 rejected, cause not examined |
| Size ladder, background capped at 1,500 $ | Validated from 2,000 $ per wallet to 90,000 $; at 1,000 $ the engine opens no case. Real data has large wallets, so this does not carry over |
| Briefing against the project's notes | 5,835 characters against 105,974 |

## Limits

- No ground truth: on real data nothing measures precision or recall. Synthetic results show mechanics.
- The verifier's controls compare size and concentration, not the engine's full feature set.
- `max_expected_false_positives` is 0.5 per 24 hours of screening. That accepts some false alerts by construction, and the threshold has not been tuned on real data.
- After a pause longer than `max_lag_s`, the missed rows open no case: the harness gives up prospects rather than decide with facts that may come from later.
- Wallet histories go back as far as the engine's retention, 14 days by default, so `habitual_size` sees only that far. The alert says so.
- `late_entry` uses a market's last known end date, which can have moved since the entry.
- Control rows are aggregated before the verifier sees them, so that step is not recomputed from raw rows.
- `rpc` receipts and `trace` funding are tested through their parts, with stand-ins for the nodes, never against live nodes from the harness.
- A real restart of the Mac is untested, and no multi-day run has happened. A passage has never gone through real data end to end: the collector was in reduced mode, so the harness stopped there, as designed.
- It does not run the collector, and a sleeping Mac runs nothing.
- Nothing is pruned: when the 500 MB budget is reached, it pauses until someone decides.
- Funding is read through the tracer's relations. An independent audit found a native transfer between two keys that this path would miss.
- The code is a copy of production's engine, which can drift from it.
- The local clock orders events; it is not an independent timestamp.
