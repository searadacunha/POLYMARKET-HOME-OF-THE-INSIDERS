#!/usr/bin/env python3
"""Before / after measurements of the registry on a real git ref. Writes one JSON file, prints a short summary.

  python3 bench.py --repo ~/Projects/Polymarket-Home-of-the-Insiders --ref origin/main --out ../../../research_notes/registry-pilot-2026-11-18/results/bench.json

Nothing here touches the network or the working tree of the repository: the ref is read from git objects. Every
comparison names what it compares and what it does NOT show (see the report). Local PostgreSQL stands in for
Supabase only to test SQL and access rules; no remote project was used, so no latency, quota or pause is measured.
"""
import argparse
import json
import multiprocessing
import os
import platform
import random
import resource
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "tests"))
import phi_registry as reg  # noqa: E402

PATHSPEC = ["*." + e.lstrip(".") for e in sorted(reg.TEXT_EXT)]


def median(xs):
    return round(statistics.median(xs), 6)


# ---------------------------------------------------------------- B1 build, reproducibility, footprint
def rss_self():
    ru = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return ru if sys.platform == "darwin" else ru * 1024


def b1_build(repo, ref, workdir):
    """Two builds of the same commit, in memory (a file build writes its WAL, about twice the database, before checkpointing);
    one copy is then written without a WAL to serve the lookups."""
    out, digests, dest = {}, [], workdir / "registry.sqlite3"
    for i in (1, 2):
        con = reg.connect(":memory:")
        t0 = time.perf_counter()
        info = reg.build(con, reg.GitSource(repo, ref))
        wall = time.perf_counter() - t0
        digests.append(info["content_sha256"])
        out[f"build{i}"] = {"wall_s": round(wall, 2), "rows": info["counts"], "files_scanned": info["files_scanned"],
                            "bytes_scanned": info["bytes_scanned"], "source": info["source"]}
        if i == 1:
            out["peak_rss_bytes_after_first_build"] = rss_self()
            reg.backup(con, dest)
        con.close()
    out["db_file_bytes"] = dest.stat().st_size
    out["same_digest_two_builds"] = digests[0] == digests[1]
    out["digest"] = digests[0]
    return out, dest


# ---------------------------------------------------------------- B2 prior work on an address: registry vs git grep
def baseline_scopes(repo, commit, address):
    """`git grep` with the registry's own definition of an address, over the same file types."""
    pattern = f"{address}(?![0-9a-fA-F])"
    t0 = time.perf_counter()
    done = subprocess.run(["git", "-C", repo, "grep", "-I", "-i", "-P", "-c", pattern, commit, "--", *PATHSPEC], capture_output=True)
    wall = time.perf_counter() - t0
    files = {}
    for line in done.stdout.decode("utf-8", "replace").splitlines():
        path = line[len(commit) + 1:].rsplit(":", 1)[0]
        files.setdefault(reg.scope_of(path), []).append(path)
    return files, wall, len(done.stdout)


def b2_lookup(con, repo, commit, per_stratum, seed):
    rng = random.Random(seed)
    counts = con.execute("SELECT address, count(*) FROM wallet_mentions GROUP BY address ORDER BY address").fetchall()
    strata = {"1 scope": [a for a, c in counts if c == 1], "2-3 scopes": [a for a, c in counts if 2 <= c <= 3],
              "4+ scopes": [a for a, c in counts if c >= 4]}
    rows = []
    for name, pool in strata.items():
        for addr in rng.sample(pool, per_stratum):
            reg_times = []
            for _ in range(5):
                t0 = time.perf_counter()
                got = reg.check(con, addr)
                reg_times.append(time.perf_counter() - t0)
            reg_bytes = len(reg.render(got).encode())
            files, git_wall, git_bytes = baseline_scopes(repo, commit, addr)
            mine = {s["scope"]: s["files"] for s in got["scopes"]}
            theirs = {s: len(p) for s, p in files.items()}
            row = {"stratum": name, "address": addr, "registry_s": round(min(reg_times), 6), "registry_bytes": reg_bytes,
                   "git_grep_s": round(git_wall, 3), "git_grep_bytes": git_bytes, "scopes": len(mine), "agree": mine == theirs}
            if not row["agree"]:
                row["registry_only"] = sorted(set(mine) - set(theirs))
                row["git_only"] = sorted(set(theirs) - set(mine))
                row["count_differs"] = sorted(s for s in set(mine) & set(theirs) if mine[s] != theirs[s])
            rows.append(row)
    cli = []
    for row in rows[:5]:
        t0 = time.perf_counter()
        subprocess.run([sys.executable, str(HERE.parent / "phi_registry.py"), "--db", str(con.execute("PRAGMA database_list").fetchone()[2]),
                        "check", row["address"]], capture_output=True, check=True)
        cli.append(time.perf_counter() - t0)
    summary = {"addresses": len(rows), "agree": sum(r["agree"] for r in rows),
               "registry_in_process_median_s": median([r["registry_s"] for r in rows]),
               "registry_cli_wall_median_s": median(cli),
               "git_grep_median_s": median([r["git_grep_s"] for r in rows]),
               "registry_bytes_median": int(statistics.median(r["registry_bytes"] for r in rows)),
               "git_grep_bytes_median": int(statistics.median(r["git_grep_bytes"] for r in rows))}
    return {"summary": summary, "rows": rows}


# ---------------------------------------------------------------- B3 sizes of what an agent would otherwise read
def b3_sizes(repo, commit, con):
    def blob(path):
        return int(subprocess.run(["git", "-C", repo, "cat-file", "-s", f"{commit}:{path}"], capture_output=True, text=True, check=True).stdout)
    return {"MASTER_REPORT.md_bytes": blob("MASTER_REPORT.md"), "INVENTORY.md_bytes": blob("INVENTORY.md"),
            "brief_bytes": len(reg.render(reg.brief(con)).encode()),
            "refuted_rows": con.execute("SELECT count(*) FROM findings WHERE level = 'REFUTED'").fetchone()[0],
            "structured_text_bytes_status_findings_evidence": sum(
                blob(f"investigations/{i}/{f}") for (i,) in con.execute("SELECT id FROM investigations") for f in ("STATUS.md", "FINDINGS.md", "EVIDENCE.md"))}


# ---------------------------------------------------------------- B4 duplicate-work guard under concurrency
def claim_worker(args):
    db, n, ttl = args
    con = reg.connect(db)
    claims = completes = 0
    for step in range(100_000):
        got = reg.claim(con, f"agent-{n}", ttl=ttl)
        if got is None:
            if con.execute("SELECT count(*) FROM agent_tasks WHERE status IN ('queued', 'running')").fetchone()[0] == 0:
                break
            time.sleep(0.05)
            continue
        claims += 1
        if hash((n, step)) % 10 == 0:  # a crash: the lease is left to expire
            continue
        completes += reg.complete(con, got["task"], f"agent-{n}", got["token"])
    con.close()
    return claims, completes


def journal_worker(args):
    journal, tasks, n, think = args
    started = 0
    while True:
        seen = set()
        if os.path.exists(journal):
            with open(journal) as f:
                seen = {json.loads(line)["task"] for line in f if line.strip()}
        todo = [t for t in tasks if t not in seen]
        if not todo:
            return started
        pick = todo[n % len(todo)] if len(todo) > 1 else todo[0]
        time.sleep(think)  # the time an agent spends between reading the journal and recording its intention
        with open(journal, "a") as f:
            f.write(json.dumps({"agent": n, "task": pick}) + "\n")
        started += 1


def b4_concurrency(workdir, tasks, workers):
    ctx = multiprocessing.get_context("spawn")
    db = str(workdir / "tasks.sqlite3")
    con = reg.connect(db)
    for i in range(tasks):
        reg.add_task(con, "wallet", f"subject {i}", max_attempts=20)
    t0 = time.perf_counter()
    with ctx.Pool(workers) as pool:
        res = pool.map(claim_worker, [(db, n, 1) for n in range(workers)])
    wall = time.perf_counter() - t0
    done_events = dict(con.execute("SELECT task_id, count(*) FROM task_events WHERE event = 'done' GROUP BY task_id").fetchall())
    guard = {"agents": workers, "tasks": tasks, "wall_s": round(wall, 2), "claims": sum(c for c, _ in res), "completions": sum(d for _, d in res),
             "tasks_done": reg.task_stats(con).get("done", 0), "tasks_completed_more_than_once": sum(1 for v in done_events.values() if v > 1),
             "tasks_lost": tasks - len(done_events), "leases_taken_over": con.execute(
                 "SELECT count(*) FROM task_events WHERE event = 'claimed' AND detail LIKE 'taken over%'").fetchone()[0]}
    con.close()
    names = [f"subject {i}" for i in range(tasks)]
    model = {}
    for think in (0.001, 0.005, 0.02):
        journal = str(workdir / f"journal-{think}.jsonl")
        with ctx.Pool(workers) as pool:
            pool.map(journal_worker, [(journal, names, n, think) for n in range(workers)])
        starts = {}
        with open(journal) as f:
            for line in f:
                starts[json.loads(line)["task"]] = starts.get(json.loads(line)["task"], 0) + 1
        model[f"think_{int(think * 1000)}ms"] = {"tasks": tasks, "starts_recorded": sum(starts.values()),
                                                 "tasks_started_more_than_once": sum(1 for v in starts.values() if v > 1)}
    return {"claim_guard_sqlite": guard, "journal_check_then_act_model": model}


# ---------------------------------------------------------------- B5 PostgreSQL: SQL, access rules, concurrency, footprint
def b5_postgres(con):
    import test_postgres as tp
    if not tp.find_bin():
        return {"skipped": "no PostgreSQL server binaries"}
    out = {}
    t0 = time.perf_counter()
    suite = subprocess.run([sys.executable, "-m", "unittest", "test_postgres", "-v"], cwd=str(HERE.parent / "tests"), capture_output=True, text=True)
    out["postgres_test_suite"] = {"passed": suite.returncode == 0, "wall_s": round(time.perf_counter() - t0, 1),
                                  "tests": suite.stderr.count(" ... ok"), "output_tail": suite.stderr.strip().splitlines()[-3:]}
    pg = tp.Postgres
    pg.setUpClass()
    try:
        size_sql = ("SELECT coalesce(sum(pg_total_relation_size(c.oid)), 0) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
                    "WHERE n.nspname = 'public' AND c.relkind = 'r'")
        # shortcut: the wallet index is loaded on every 32nd row and its size scaled x32 (a full load would need ~0.5 GB of disk,
        # more than the disk guard leaves free); load it fully when the exact figure matters.
        step = 32
        pg.sql("DELETE FROM finding_addresses; DELETE FROM open_items; DELETE FROM evidence; DELETE FROM findings; DELETE FROM wallet_mentions; "
               "DELETE FROM hypothesis_tests; DELETE FROM investigations;")
        t0 = time.perf_counter()
        script = reg.export_sql(con, reg.DEFAULT_EXPORT)
        gen = time.perf_counter() - t0
        t0 = time.perf_counter()
        pg.sql(script)
        out["default_tables"] = {"sql_bytes": len(script.encode()), "generate_s": round(gen, 2), "load_s": round(time.perf_counter() - t0, 2),
                                 "rows": {t: int(pg.sql(f"SELECT count(*) FROM {t}")) for t in reg.DEFAULT_EXPORT},
                                 "relation_bytes_in_postgres": int(pg.sql(size_sql))}
        sample = con.execute(f"SELECT * FROM wallet_mentions WHERE rowid % {step} = 0 ORDER BY address, scope").fetchall()
        t0 = time.perf_counter()
        parts = ["BEGIN;"] + [
            "INSERT INTO wallet_mentions (address, scope, files, first_ref) VALUES " + ",".join(
                "(" + ",".join(reg.sql_literal(v) for v in tuple(r)) + ")" for r in sample[i:i + 500]) + ";" for i in range(0, len(sample), 500)] + ["COMMIT;"]
        pg.sql("\n".join(parts))
        load = time.perf_counter() - t0
        sample_bytes = int(pg.sql("SELECT pg_total_relation_size('wallet_mentions')"))
        out["wallet_index"] = {"rows_total": con.execute("SELECT count(*) FROM wallet_mentions").fetchone()[0], "rows_loaded": len(sample),
                               "relation_bytes_loaded_sample": sample_bytes, "relation_bytes_scaled_x%d" % step: sample_bytes * step,
                               "load_s_sample": round(load, 2), "method": f"every {step}th row, size scaled x{step} (extrapolation, not a full load)"}
    finally:
        pg.doClassCleanups()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=".")
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--out", required=True)
    ap.add_argument("--addresses", type=int, default=15, help="per stratum (three strata)")
    ap.add_argument("--tasks", type=int, default=400)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=20261118)
    ap.add_argument("--skip-postgres", action="store_true")
    args = ap.parse_args()
    repo = str(Path(args.repo).expanduser().resolve())
    commit = subprocess.run(["git", "-C", repo, "rev-parse", "--verify", args.ref + "^{commit}"], capture_output=True, text=True, check=True).stdout.strip()
    result = {"commit": commit, "ref": args.ref, "seed": args.seed,
              "machine": {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version, "platform": platform.platform(),
                          "cpus": os.cpu_count()}}
    with tempfile.TemporaryDirectory(prefix="phi-bench-") as tmp:
        work = Path(tmp)
        print("B1 build ...", flush=True)
        result["b1_build"], db = b1_build(repo, commit, work)
        con = reg.connect(db)
        print("B2 address lookups ...", flush=True)
        result["b2_address_lookup"] = b2_lookup(con, repo, commit, args.addresses, args.seed)
        print("B3 sizes ...", flush=True)
        result["b3_sizes"] = b3_sizes(repo, commit, con)
        print("B4 concurrency ...", flush=True)
        result["b4_duplicate_work"] = b4_concurrency(work, args.tasks, args.workers)
        result["b6_tests_ledger"] = reg.tests_report(con)
        if not args.skip_postgres:
            print("B5 postgres ...", flush=True)
            result["b5_postgres"] = b5_postgres(con)
        con.close()
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=1, ensure_ascii=False) + "\n")
    s = result["b2_address_lookup"]["summary"]
    print(json.dumps({"digest": result["b1_build"]["digest"], "same_digest": result["b1_build"]["same_digest_two_builds"],
                      "b2": s, "b4": result["b4_duplicate_work"]["claim_guard_sqlite"]}, indent=1))


if __name__ == "__main__":
    main()
