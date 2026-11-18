#!/usr/bin/env python3
"""Offline replay of the figures in REPORT.md from results/bench.json (no repository, no database, no network).

  python3 -I research_notes/registry-pilot-2026-11-18/verify.py

It recomputes every summary figure from the raw per-address rows and the raw counters, checks that the stored summaries
match, and prints the figures the report quotes. A mismatch exits with 1.
"""
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
bench = json.loads((HERE / "results" / "bench.json").read_text())
problems = []


def check(ok, text):
    if not ok:
        problems.append(text)


# B1: one commit, two builds, one digest
b1 = bench["b1_build"]
check(b1["same_digest_two_builds"], "two builds of one commit gave different digests")
check(b1["build1"]["rows"] == b1["build2"]["rows"], "two builds gave different row counts")
check(b1["build1"]["source"] == "git:" + bench["commit"], "build source is not the benchmarked commit")

# B2: every figure of the summary recomputed from the rows
b2 = bench["b2_address_lookup"]
rows, s = b2["rows"], b2["summary"]
check(s["addresses"] == len(rows), "address count")
check(s["agree"] == sum(r["agree"] for r in rows), "agreement count")
check(s["registry_in_process_median_s"] == round(statistics.median(r["registry_s"] for r in rows), 6), "registry median")
check(s["git_grep_median_s"] == round(statistics.median(r["git_grep_s"] for r in rows), 6), "git grep median")
check(s["registry_bytes_median"] == int(statistics.median(r["registry_bytes"] for r in rows)), "registry bytes median")
check(s["git_grep_bytes_median"] == int(statistics.median(r["git_grep_bytes"] for r in rows)), "git grep bytes median")
for r in rows:
    check(r["agree"] or (r.get("registry_only") or r.get("git_only") or r.get("count_differs")), f"disagreement without a reason: {r['address']}")
by_stratum = {}
for r in rows:
    by_stratum.setdefault(r["stratum"], []).append(r)

# B4: the guard's invariants
g = bench["b4_duplicate_work"]["claim_guard_sqlite"]
check(g["tasks_completed_more_than_once"] == 0, "a task completed twice")
check(g["tasks_lost"] == 0 and g["tasks_done"] == g["tasks"], "a task was lost")
check(g["completions"] == g["tasks"], "completions differ from tasks")

# integrity of the real registry: every check passed, on the same commit
integrity = json.loads((HERE / "results" / "integrity.json").read_text())
check(integrity["passed"] and all(c["ok"] for c in integrity["checks"]), "an integrity check failed")
check(len(integrity["checks"]) == 5, "the integrity check list changed")
check(any(c["check"].startswith("300 sampled") for c in integrity["checks"]), "the sample of the integrity check changed")
check(any(c["check"] == "rebuilding that commit gives the stored digest" and b1["digest"][:16] in c["detail"] for c in integrity["checks"]),
      "the integrity check names another digest than the benchmark")

if problems:
    print("MISMATCH:", *problems, sep="\n- ")
    sys.exit(1)

print(f"commit {bench['commit'][:12]}  digest {b1['digest'][:16]}  same digest on two builds: {b1['same_digest_two_builds']}")
print(f"build: {b1['build1']['wall_s']} s, {b1['build1']['files_scanned']} files, {b1['build1']['bytes_scanned']:,} bytes read, "
      f"peak RSS {b1['peak_rss_bytes_after_first_build'] / 1e6:,.0f} MB, database file {b1['db_file_bytes'] / 1e6:,.0f} MB")
print("rows:", b1["build1"]["rows"])
print(f"address lookups: {s['agree']}/{s['addresses']} identical to git grep (scopes and file counts)")
for name, group in by_stratum.items():
    print(f"  {name:11s} n={len(group):2d}  registry {statistics.median(r['registry_s'] for r in group) * 1000:7.2f} ms   "
          f"git grep {statistics.median(r['git_grep_s'] for r in group):5.2f} s   agree {sum(r['agree'] for r in group)}/{len(group)}")
print(f"  all: registry in process {s['registry_in_process_median_s'] * 1000:.2f} ms, command line {s['registry_cli_wall_median_s'] * 1000:.0f} ms, "
      f"git grep {s['git_grep_median_s']:.2f} s; answer {s['registry_bytes_median']} B vs {s['git_grep_bytes_median']} B")
print(f"claim guard: {g['agents']} agents, {g['tasks']} tasks, {g['claims']} claims, {g['leases_taken_over']} leases taken over, "
      f"0 tasks done twice, 0 lost, {g['wall_s']} s")
print("check-then-act model (no atomic claim):", json.dumps(bench["b4_duplicate_work"]["journal_check_then_act_model"]))
print(f"integrity: {len(integrity['checks'])} checks passed, rebuild digest {b1['digest'][:16]}")
print("OK")
