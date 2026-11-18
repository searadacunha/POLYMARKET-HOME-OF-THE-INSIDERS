#!/usr/bin/env python3
"""PHI registry: what this repository already established, queryable, plus a duplicate-work guard for agents.

Two kinds of state, kept apart on purpose:
  * DERIVED tables (investigations, findings, open_items, evidence, finding_addresses, wallet_mentions,
    hypothesis_tests): a pure function of one git commit. `build` throws them away and rebuilds them, so they are
    reproducible (same commit, same `digest`) and never need a backup.
  * OPERATIONAL tables (agent_tasks, task_events): leases that stop two agents from researching the same unit.

Local first: stdlib only, one SQLite file ($PHI_REGISTRY_DB). The same SQL (supabase/migrations/) also applies to
PostgreSQL; nothing here opens a network connection. Examples:

  python3 phi_registry.py build --repo ~/Projects/Polymarket-Home-of-the-Insiders --ref origin/main
  python3 phi_registry.py check 0xa8e64a3c...        # prior work on an address, or on words
  python3 phi_registry.py brief                      # levels, refuted tracks, open items, task queue
  python3 phi_registry.py task add wallet 0x...      # then: task claim <agent>, task done|fail <id> <agent> <token>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import re
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "scripts"))
import phi_lib  # noqa: E402  the repository's own STATUS / FINDINGS parsers, reused as they are
from build_master_report import status_section  # noqa: E402  (importing it runs nothing: main() is guarded)

SCHEMA_VERSION = "1"
MIGRATIONS = HERE / "supabase" / "migrations"
# Parents before children: build() inserts in this order and deletes in the reverse order.
DERIVED = ("investigations", "findings", "open_items", "evidence", "finding_addresses", "wallet_mentions", "hypothesis_tests")
DEFAULT_EXPORT = tuple(t for t in DERIVED if t != "wallet_mentions")  # the big index stays local unless asked for
TEXT_EXT = frozenset(".md .json .jsonl .csv .txt .py .tsv .log .yml .yaml .html .graphml .sh .mmd".split())
ADDR = re.compile(rb"0x[0-9a-fA-F]{40}(?![0-9a-fA-F])")  # a 64-hex transaction hash does not match
ADDR_FULL = re.compile(r"0x[0-9a-fA-F]{40}")
EVIDENCE_ROW = re.compile(r"^\| `([^`]+)` \| (auto|[0-9a-f]{64}|local_only) \|(.*)$", re.M)
TEST_FILES = {"tests.json", "verdict.json", "test_register.jsonl"}
OPEN_KINDS = {"Contradictions": "contradiction", "Missing to conclude": "missing", "Prospective monitoring": "monitoring"}


def default_db():
    base = os.environ.get("XDG_STATE_HOME") or str(Path.home() / ".local" / "state")
    return os.environ.get("PHI_REGISTRY_DB") or str(Path(base) / "phi-registry" / "registry.sqlite3")


def connect(path):
    """Open (and create) the registry. Portable migrations are applied; `*.pg.sql` files are PostgreSQL only."""
    path = str(path)
    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=30, isolation_level=None)  # explicit BEGIN / COMMIT everywhere
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA foreign_keys=ON")
    for sql in sorted(MIGRATIONS.glob("*.sql")):
        if not sql.name.endswith(".pg.sql"):
            con.executescript(sql.read_text())
    con.execute("INSERT OR IGNORE INTO registry_meta VALUES ('schema_version', ?)", (SCHEMA_VERSION,))
    return con


# ---------------------------------------------------------------- sources: a git commit, or a plain directory

def scope_of(path):
    """Where a file lives for 'has this been looked at': an investigation, a research note, or a top-level folder."""
    p = path.split("/")
    if p[0] == "investigations" and len(p) > 2:
        return p[1]
    if p[0] == "research_notes" and len(p) > 2:
        return "rn:" + p[1]
    return p[0]


def wanted(path, size):
    name = path.rsplit("/", 1)[-1]
    return "." in name and "." + name.rsplit(".", 1)[1].lower() in TEXT_EXT and size <= phi_lib.MAX_FILE_BYTES


class GitSource:
    """Text blobs of one commit, streamed from git objects: the working tree (dirty, other branch) is never read."""

    def __init__(self, repo, ref):
        self.repo = str(repo)
        done = subprocess.run(["git", "-C", self.repo, "rev-parse", "--verify", ref + "^{commit}"], capture_output=True, text=True)
        if done.returncode:
            raise SystemExit(f"cannot resolve {ref!r} in {self.repo}: {done.stderr.strip()}")
        self.commit = done.stdout.strip()
        self.label = "git:" + self.commit

    def files(self):
        listing = subprocess.run(["git", "-C", self.repo, "ls-tree", "-r", "-l", "-z", self.commit], capture_output=True, check=True).stdout
        todo = []
        for rec in listing.split(b"\0"):
            if rec:
                meta, raw = rec.split(b"\t", 1)
                _mode, typ, sha, size = meta.split()
                path = raw.decode("utf-8", "surrogateescape")
                if typ == b"blob" and wanted(path, int(size)):
                    todo.append((path, sha))
        with subprocess.Popen(["git", "-C", self.repo, "cat-file", "--batch"], stdin=subprocess.PIPE, stdout=subprocess.PIPE) as proc:
            for path, sha in todo:
                proc.stdin.write(sha + b"\n")
                proc.stdin.flush()
                head = proc.stdout.readline().split()
                if len(head) != 3:
                    raise RuntimeError(f"git cat-file could not read {path}: {head}")
                data = proc.stdout.read(int(head[2]))
                proc.stdout.read(1)
                yield path, data
            proc.stdin.close()


class DirSource:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.label = "dir:" + str(self.root)

    def files(self):
        for base, dirs, names in os.walk(self.root):
            dirs[:] = sorted(d for d in dirs if d != ".git")
            for name in sorted(names):
                full = Path(base) / name
                rel = full.relative_to(self.root).as_posix()
                if full.is_file() and wanted(rel, full.stat().st_size):
                    yield rel, full.read_bytes()


# ---------------------------------------------------------------- parsing

def addresses_in(*texts):
    return sorted({m.decode().lower() for t in texts for m in ADDR.findall(t.encode())})


def num(x):
    """A number or None: registers sometimes hold a list or a string where a figure is expected."""
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def parse_tests(path, data):
    """Rows for the three archived test-register formats. Another file with the same name is skipped, never guessed."""
    study, name = scope_of(path), path.rsplit("/", 1)[-1]
    text = data.decode("utf-8", "replace")
    rows = []
    if name == "test_register.jsonl":
        for i, line in enumerate(text.splitlines(), 1):
            r = json.loads(line)
            if isinstance(r, dict) and "test" in r and isinstance(r.get("p"), (int, float)):
                status = "exploratory" if str(r.get("status", "")).startswith("explor") else "confirmatory"
                rows.append((study, f"L{i}:{r['test']}", f"{r.get('variant', '')} / {r.get('script', '')}".strip(" /"),
                             status, None, num(r.get("effect")), r["p"], None, None, path))
        return rows
    d = json.loads(text)
    if not isinstance(d, dict):
        return rows
    if name == "tests.json" and isinstance(d.get("tests"), dict):
        for tid, t in d["tests"].items():
            if isinstance(t, dict) and isinstance(t.get("p_value"), (int, float)):
                n = next((t[k] for k in ("n", "n_s4", "n_s4b") if k in t), None)
                effect = next((t[k] for k in ("excess", "diff") if k in t), None)
                rows.append((study, tid, str(t.get("description", "")), "confirmatory", num(n), num(effect), t["p_value"],
                             num(t.get("bonferroni_alpha")), num(d.get("n_comparisons")), path))
    elif name == "verdict.json" and any(k.startswith("primary_T") for k in d):
        for key, t in d.items():
            if key.startswith("primary_T") and isinstance(t, dict) and isinstance(t.get("p"), (int, float)):
                n = next((t[k] for k in ("n", "n_flag") if k in t), None)
                effect = next((t[k] for k in ("excess", "diff") if k in t), None)
                rows.append((study, key[len("primary_"):], key, "confirmatory", num(n), num(effect), t["p"],
                             num(d.get("alpha_corrected")), num(d.get("comparisons_on_real_data")), path))
    return rows


def build(con, source):
    """Rebuild every derived table from `source` in one transaction. Operational tables are not touched."""
    t0 = time.time()
    structured, tests, mentions, scanned, nbytes = {}, {}, {}, 0, 0
    for path, data in source.files():
        scanned, nbytes = scanned + 1, nbytes + len(data)
        parts = path.split("/")
        if len(parts) == 3 and parts[0] == "investigations" and parts[2] in ("STATUS.md", "FINDINGS.md", "EVIDENCE.md"):
            structured[path] = data.decode("utf-8", "replace")
        if parts[-1] in TEST_FILES:
            tests[path] = data
        found = {m.decode().lower() for m in ADDR.findall(data)}
        if found:
            scope = scope_of(path)
            for a in found:
                row = mentions.setdefault((a, scope), [0, path])
                row[0] += 1

    inv_rows, find_rows, open_rows, evid_rows, faddr_rows, skipped = [], [], [], [], [], []
    for inv in sorted({p.split("/")[1] for p in structured}):
        status, findings = structured.get(f"investigations/{inv}/STATUS.md"), structured.get(f"investigations/{inv}/FINDINGS.md")
        fields, body = phi_lib.parse_status(status) if status else (None, "")
        if not fields or findings is None:
            skipped.append(inv)
            continue
        if fields.get("state") not in phi_lib.STATES:
            raise ValueError(f"investigations/{inv}/STATUS.md: state {fields.get('state')!r} is not one of {phi_lib.STATES}")
        inv_rows.append((inv, fields.get("title", ""), fields["state"], fields.get("updated_utc", ""), fields.get("origin", ""),
                         fields.get("version", ""), status_section(body, "Objective"), status_section(body, "Conclusions"),
                         status_section(body, "Limits")))
        items, sections = phi_lib.parse_findings(findings)
        for f in items:
            cells = [f.get(k, "") for k in ("Sources", "Method", "Limits", "Links")]
            find_rows.append((inv, f["id"], f["level"], f["claim"], *cells))
            faddr_rows += [(inv, f["id"], a) for a in addresses_in(f["claim"], *cells)]
        for title, kind in OPEN_KINDS.items():
            open_rows += [(inv, kind, i, text) for i, text in enumerate(sections.get(title, []), 1)]
        evid_rows += [(inv, m.group(1), m.group(2), m.group(3).strip().strip("|").strip())
                      for m in EVIDENCE_ROW.finditer(structured.get(f"investigations/{inv}/EVIDENCE.md", ""))]
    test_rows, test_skipped = [], []
    for path in sorted(tests):
        try:
            got = parse_tests(path, tests[path])
        except ValueError:  # includes json.JSONDecodeError
            got = []
        (test_rows.extend(got) if got else test_skipped.append(path))
    mention_rows = [(a, s, v[0], v[1]) for (a, s), v in sorted(mentions.items())]

    con.execute("BEGIN IMMEDIATE")
    try:
        for t in reversed(DERIVED):
            con.execute(f"DELETE FROM {t}")
        for table, rows in (("investigations", inv_rows), ("findings", find_rows), ("open_items", open_rows),
                            ("evidence", evid_rows), ("finding_addresses", faddr_rows), ("wallet_mentions", mention_rows),
                            ("hypothesis_tests", test_rows)):
            if rows:
                con.executemany(f"INSERT INTO {table} VALUES ({','.join('?' * len(rows[0]))})", rows)
        meta = {"source": source.label, "built_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "files_scanned": scanned,
                "bytes_scanned": nbytes, "investigations_skipped": ",".join(skipped), "test_files_skipped": ",".join(test_skipped)}
        con.executemany("INSERT INTO registry_meta VALUES (?, ?) ON CONFLICT (key) DO UPDATE SET value = excluded.value",
                        [(k, str(v)) for k, v in meta.items()])
        con.execute("COMMIT")
    except BaseException:
        con.execute("ROLLBACK")
        raise
    meta["content_sha256"] = digest(con)
    con.execute("INSERT INTO registry_meta VALUES ('content_sha256', ?) ON CONFLICT (key) DO UPDATE SET value = excluded.value", (meta["content_sha256"],))
    counts = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in DERIVED}
    return {**meta, "counts": counts, "seconds": round(time.time() - t0, 2)}


def digest(con):
    """sha256 over the derived tables, in a canonical order: equal digests mean equal content."""
    h = hashlib.sha256()
    for t in DERIVED:
        cols = [r[1] for r in con.execute(f"PRAGMA table_info({t})")]
        h.update(f"#{t}\n".encode())
        for row in con.execute(f"SELECT * FROM {t} ORDER BY {', '.join(cols)}"):
            h.update((json.dumps(list(row), ensure_ascii=False) + "\n").encode())
    return h.hexdigest()


# ---------------------------------------------------------------- questions an agent asks before starting

def check(con, query, limit=15):
    """Prior work on a full 0x address, or on words (every word must appear in a finding)."""
    q = query.strip()
    inv = con.execute("SELECT id, title, state, objective, conclusions, limits FROM investigations WHERE id = ?", (q,)).fetchone()
    if inv:
        return {"query": q, "kind": "investigation", **dict(inv),
                "findings": [dict(r) for r in con.execute(
                    "SELECT finding_id AS finding, level, substr(claim, 1, 160) AS claim FROM findings WHERE investigation_id = ? "
                    "ORDER BY finding_id", (q,))],
                "open_items": [dict(r) for r in con.execute(
                    "SELECT kind, text FROM open_items WHERE investigation_id = ? ORDER BY kind, seq", (q,))]}
    if ADDR_FULL.fullmatch(q):
        a = q.lower()
        return {"query": q, "kind": "address",
                "scopes": [dict(r) for r in con.execute(
                    "SELECT scope, files, first_ref FROM wallet_mentions WHERE address = ? ORDER BY files DESC, scope", (a,))],
                "findings": [dict(r) for r in con.execute(
                    "SELECT f.investigation_id AS investigation, f.finding_id AS finding, f.level, substr(f.claim, 1, 160) AS claim "
                    "FROM finding_addresses x JOIN findings f USING (investigation_id, finding_id) WHERE x.address = ? "
                    "ORDER BY f.investigation_id, f.finding_id", (a,))],
                "tasks": [dict(r) for r in con.execute("SELECT id, status, claimed_by FROM agent_tasks WHERE dedup_key LIKE ?", ("%:" + a,))]}
    words = q.lower().split()
    haystack = "lower(claim || ' ' || sources || ' ' || method || ' ' || limits || ' ' || links)"
    where = " AND ".join([f"instr({haystack}, ?) > 0"] * len(words)) or "1"
    rows = con.execute(f"SELECT investigation_id AS investigation, finding_id AS finding, level, substr(claim, 1, 160) AS claim "
                       f"FROM findings WHERE {where} ORDER BY investigation_id, finding_id", words).fetchall()
    return {"query": q, "kind": "words", "total": len(rows), "findings": [dict(r) for r in rows[:limit]]}


def brief(con):
    meta = dict(con.execute("SELECT key, value FROM registry_meta").fetchall())
    levels = dict(con.execute("SELECT level, count(*) FROM findings GROUP BY level").fetchall())
    states = dict(con.execute("SELECT state, count(*) FROM investigations GROUP BY state").fetchall())
    return {"source": meta.get("source"), "content_sha256": meta.get("content_sha256"), "levels": levels, "states": states,
            "refuted": [dict(r) for r in con.execute(
                "SELECT investigation_id AS investigation, finding_id AS finding, substr(claim, 1, 140) AS claim FROM findings "
                "WHERE level = 'REFUTED' ORDER BY investigation_id, finding_id")],
            "missing_to_conclude": [dict(r) for r in con.execute(
                "SELECT investigation_id AS investigation, substr(text, 1, 140) AS text FROM open_items WHERE kind = 'missing' "
                "ORDER BY investigation_id, seq")],
            "tasks": task_stats(con)}


def tests_report(con, alpha=0.05):
    """What the repository archived of each study's tests, as a count per study. Deliberately no pooled correction and no
    'expected by chance': rows of one study are often variants of the same test, and whether tests form one family is
    decided in a frozen plan, not here. `declared` above `registered` means the rest is archived elsewhere or not at all."""
    return {"studies": [dict(r) for r in con.execute(
        "SELECT study, count(*) AS registered, max(declared_comparisons) AS declared, "
        "coalesce(sum(status = 'exploratory'), 0) AS exploratory, coalesce(sum(p_value < ?), 0) AS nominal_p_below_alpha_unadjusted "
        "FROM hypothesis_tests GROUP BY study ORDER BY study", (alpha,))], "alpha": alpha}


def scope_pathspecs(scope, investigation_ids):
    """git pathspecs of the text files of one scope; None for top-level files and folders (the rebuild check covers them)."""
    base = "research_notes/" + scope[3:] if scope.startswith("rn:") else "investigations/" + scope if scope in investigation_ids else None
    return [f":(glob){base}/**/*.{e.lstrip('.')}" for e in sorted(TEXT_EXT)] if base else None


def verify(con, repo, sample=25, seed=20261118):
    """Integrity and provenance of the derived tables: against themselves, against a fresh rebuild of the commit they name,
    and against `git grep`, an independent implementation of the address search. Returns a list of checks."""
    checks = []

    def add(name, passed, detail=""):
        checks.append({"check": name, "ok": bool(passed), "detail": detail})
    meta = dict(con.execute("SELECT key, value FROM registry_meta").fetchall())
    stored = meta.get("content_sha256", "")
    add("the stored digest equals the tables as they are now (no manual edit)", stored == digest(con))
    add("foreign keys hold", not con.execute("PRAGMA foreign_key_check").fetchall())
    add("every address linked to a finding appears in that finding's text", not con.execute(
        "SELECT 1 FROM finding_addresses a JOIN findings f USING (investigation_id, finding_id) WHERE instr(lower(f.claim || ' ' || "
        "f.sources || ' ' || f.method || ' ' || f.limits || ' ' || f.links), a.address) = 0 LIMIT 1").fetchall())
    src = meta.get("source", "")
    if not src.startswith("git:"):
        add("the registry was built from a git commit", False, src or "no source recorded")
        return checks
    try:
        source = GitSource(repo, src[4:])
    except SystemExit as exc:
        add("the commit named by the registry is in the repository", False, str(exc))
        return checks
    mem = connect(":memory:")
    rebuilt = build(mem, source)["content_sha256"]
    mem.close()
    add("rebuilding that commit gives the stored digest", rebuilt == stored, f"rebuilt {rebuilt[:16]}, stored {stored[:16]}")
    ids = {r[0] for r in con.execute("SELECT id FROM investigations")}
    rows = [r for r in con.execute("SELECT address, scope, files, first_ref FROM wallet_mentions ORDER BY address, scope")
            if scope_pathspecs(r["scope"], ids)]
    bad = []
    picks = random.Random(seed).sample(rows, min(sample, len(rows)))
    for r in picks:
        pattern = f"{r['address']}(?![0-9a-fA-F])"
        base = ["git", "-C", str(repo), "grep", "-I", "-i", "-P"]
        files = subprocess.run([*base, "-c", pattern, source.commit, "--", *scope_pathspecs(r["scope"], ids)], capture_output=True).stdout.splitlines()
        first = subprocess.run([*base, "-q", pattern, source.commit, "--", ":(literal)" + r["first_ref"]], capture_output=True).returncode == 0
        if len(files) != r["files"] or not first or scope_of(r["first_ref"]) != r["scope"]:
            bad.append({"address": r["address"], "scope": r["scope"], "registry_files": r["files"], "git_grep_files": len(files), "first_ref_ok": first})
    add(f"{len(picks)} sampled address rows agree with an independent git grep (file count, first reference, scope)", not bad, json.dumps(bad[:3]))
    return checks


# ---------------------------------------------------------------- duplicate-work guard

def collapse(text):
    return re.sub(r"\s+", " ", text).strip()


def norm(text):
    """The dedup form of a subject: lower-case, whitespace collapsed. ASCII-safe: non-ASCII case folding follows the database locale."""
    return collapse(text).lower()


def _event(con, task_id, now, agent, event, detail=None):
    con.execute("INSERT INTO task_events VALUES (?, ?, ?, ?, ?, ?)", (os.urandom(16).hex(), task_id, now, agent, event, detail))


def _txn(con, fn):
    con.execute("BEGIN IMMEDIATE")
    try:
        out = fn()
        con.execute("COMMIT")
        return out
    except BaseException:
        con.execute("ROLLBACK")
        raise


def add_task(con, kind, subject, priority=3, max_attempts=3, now=None):
    """Create the task unless an identical one exists (same kind, same normalised subject). Also reports prior work."""
    now = int(time.time() if now is None else now)
    key = f"{kind.lower()}:{norm(subject)}"
    tid = hashlib.sha256(key.encode()).hexdigest()[:16]

    def go():
        cur = con.execute("INSERT INTO agent_tasks (id, dedup_key, kind, subject, priority, max_attempts, created_at, updated_at) "
                          "VALUES (?, ?, ?, ?, ?, ?, ?, ?) ON CONFLICT (dedup_key) DO NOTHING",
                          (tid, key, kind.lower(), collapse(subject), priority, max_attempts, now, now))
        if cur.rowcount == 1:
            _event(con, tid, now, None, "added")
        return cur.rowcount == 1
    created = _txn(con, go)
    prior = check(con, subject) if ADDR_FULL.fullmatch(subject.strip()) else None
    return {"task": tid, "created": created, "prior_scopes": len(prior["scopes"]) if prior else None,
            "prior_findings": len(prior["findings"]) if prior else None}


def claim(con, agent, ttl=900, now=None):
    """One task, or None. A lease that expired is taken over; the returned `token` fences every later call."""
    now = int(time.time() if now is None else now)

    def go():
        for (tid, holder) in con.execute("SELECT id, claimed_by FROM agent_tasks WHERE status = 'running' AND lease_until < ? "
                                         "AND attempts >= max_attempts", (now,)).fetchall():
            con.execute("UPDATE agent_tasks SET status = 'failed', last_error = 'lease expired after max attempts', lease_until = NULL, "
                        "updated_at = ? WHERE id = ?", (now, tid))
            _event(con, tid, now, holder, "failed", "lease expired after max attempts")
        row = con.execute("SELECT id, status, claimed_by FROM agent_tasks WHERE status = 'queued' OR (status = 'running' AND lease_until < ?) "
                          "ORDER BY priority, created_at, id LIMIT 1", (now,)).fetchone()
        if row is None:
            return None
        got = con.execute("UPDATE agent_tasks SET status = 'running', claimed_by = ?, lease_until = ?, attempts = attempts + 1, "
                          "updated_at = ? WHERE id = ? RETURNING id, kind, subject, dedup_key, attempts",
                          (agent, now + ttl, now, row["id"])).fetchone()
        _event(con, got["id"], now, agent, "claimed", f"taken over from {row['claimed_by'] or '?'}" if row["status"] == "running" else None)
        return {"task": got["id"], "kind": got["kind"], "subject": got["subject"], "key": got["dedup_key"], "token": got["attempts"]}
    return _txn(con, go)


def _held(con, task_id, agent, token):
    return con.execute("SELECT 1 FROM agent_tasks WHERE id = ? AND status = 'running' AND claimed_by = ? AND attempts = ?",
                       (task_id, agent, token)).fetchone() is not None


def heartbeat(con, task_id, agent, token, ttl=900, now=None):
    now = int(time.time() if now is None else now)

    def go():
        if not _held(con, task_id, agent, token):
            return False
        con.execute("UPDATE agent_tasks SET lease_until = ?, updated_at = ? WHERE id = ?", (now + ttl, now, task_id))
        _event(con, task_id, now, agent, "heartbeat")
        return True
    return _txn(con, go)


def complete(con, task_id, agent, token, result_ref=None, now=None):
    """True once; a holder whose lease was taken over (or who already completed) gets False."""
    now = int(time.time() if now is None else now)

    def go():
        if not _held(con, task_id, agent, token):
            return False
        con.execute("UPDATE agent_tasks SET status = 'done', result_ref = ?, lease_until = NULL, updated_at = ? WHERE id = ?",
                    (result_ref, now, task_id))
        _event(con, task_id, now, agent, "done", result_ref)
        return True
    return _txn(con, go)


def fail(con, task_id, agent, token, error, now=None):
    """Re-queues until attempts are used up, then closes as failed. Returns the new status, or None if not the holder."""
    now = int(time.time() if now is None else now)

    def go():
        if not _held(con, task_id, agent, token):
            return None
        status = con.execute("UPDATE agent_tasks SET status = CASE WHEN attempts < max_attempts THEN 'queued' ELSE 'failed' END, "
                             "last_error = ?, lease_until = NULL, claimed_by = NULL, updated_at = ? WHERE id = ? RETURNING status",
                             (error, now, task_id)).fetchone()[0]
        _event(con, task_id, now, agent, "requeued" if status == "queued" else "failed", error)
        return status
    return _txn(con, go)


def task_stats(con):
    return dict(con.execute("SELECT status, count(*) FROM agent_tasks GROUP BY status").fetchall())


# ---------------------------------------------------------------- export to PostgreSQL / Supabase, backup

def sql_literal(v):
    if v is None:
        return "NULL"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        return "NULL" if v != v or v in (float("inf"), float("-inf")) else repr(v)
    return "'" + str(v).replace("\x00", "").replace("'", "''") + "'"


def export_sql(con, tables=DEFAULT_EXPORT, batch=200):
    """One transaction that replaces the derived tables on a PostgreSQL database: psql "$SUPABASE_DB_URL" -f export.sql."""
    unknown = [t for t in tables if t not in DERIVED]
    if unknown:
        raise SystemExit(f"not a derived table: {unknown}")
    chosen = [t for t in DERIVED if t in tables]
    out = ["-- phi_registry export; rebuilds derived tables only, never the task tables.",
           "-- Needs standard_conforming_strings = on (the PostgreSQL default): backslashes are literal in the strings below.", "BEGIN;"]
    out += [f"DELETE FROM {t};" for t in reversed(chosen)]
    for t in chosen:
        cols = [r[1] for r in con.execute(f"PRAGMA table_info({t})")]
        rows = [tuple(r) for r in con.execute(f"SELECT * FROM {t} ORDER BY {', '.join(cols)}")]
        for i in range(0, len(rows), batch):
            body = ",\n".join("(" + ", ".join(sql_literal(v) for v in r) + ")" for r in rows[i:i + batch])
            out.append(f"INSERT INTO {t} ({', '.join(cols)}) VALUES\n{body};")
    for k, v in con.execute("SELECT key, value FROM registry_meta WHERE key IN ('source', 'content_sha256', 'schema_version')"):
        out.append(f"INSERT INTO registry_meta VALUES ({sql_literal(k)}, {sql_literal(v)}) ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value;")
    out.append("COMMIT;")
    return "\n".join(out) + "\n"


def backup(con, dest):
    """Online, consistent copy of the whole registry (tasks included), safe while agents are claiming."""
    target = sqlite3.connect(str(dest))
    with target:
        con.backup(target)
    target.close()


# ---------------------------------------------------------------- command line

def render(obj):
    return json.dumps(obj, ensure_ascii=False, indent=1)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--db", default=default_db())
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--repo", default=".")
    b.add_argument("--ref", default="origin/main")
    b.add_argument("--dir", help="read a plain directory instead of a git ref")
    sub.add_parser("brief")
    vf = sub.add_parser("verify", help="integrity and provenance against the commit the registry names")
    vf.add_argument("--repo", default=".")
    vf.add_argument("--sample", type=int, default=25)
    sub.add_parser("tests")
    sub.add_parser("digest")
    c = sub.add_parser("check")
    c.add_argument("words", nargs="+")
    e = sub.add_parser("export-sql")
    e.add_argument("--tables", default=",".join(DEFAULT_EXPORT), help="comma list; add wallet_mentions for the full index")
    bk = sub.add_parser("backup")
    bk.add_argument("dest")
    t = sub.add_parser("task").add_subparsers(dest="action", required=True)
    a = t.add_parser("add")
    a.add_argument("kind")
    a.add_argument("subject")
    a.add_argument("--priority", type=int, default=3)
    cl = t.add_parser("claim")
    cl.add_argument("agent")
    cl.add_argument("--ttl", type=int, default=900)
    for name in ("done", "fail", "heartbeat"):
        p = t.add_parser(name)
        p.add_argument("task")
        p.add_argument("agent")
        p.add_argument("token", type=int)
        p.add_argument("detail", nargs="?", default="")
    t.add_parser("stats")
    args = ap.parse_args(argv)

    con = connect(args.db)
    if args.cmd == "build":
        source = DirSource(args.dir) if args.dir else GitSource(args.repo, args.ref)
        print(render(build(con, source)))
    elif args.cmd == "check":
        print(render(check(con, " ".join(args.words))))
    elif args.cmd == "brief":
        print(render(brief(con)))
    elif args.cmd == "tests":
        print(render(tests_report(con)))
    elif args.cmd == "verify":
        checks = verify(con, args.repo, args.sample)
        print(render({"passed": all(c["ok"] for c in checks), "checks": checks}))
        sys.exit(0 if all(c["ok"] for c in checks) else 1)
    elif args.cmd == "digest":
        print(digest(con))
    elif args.cmd == "export-sql":
        sys.stdout.write(export_sql(con, tuple(x for x in args.tables.split(",") if x)))
    elif args.cmd == "backup":
        backup(con, args.dest)
    elif args.action == "add":
        print(render(add_task(con, args.kind, args.subject, args.priority)))
    elif args.action == "claim":
        print(render(claim(con, args.agent, args.ttl)))
    elif args.action == "stats":
        print(render(task_stats(con)))
    else:
        fn = {"done": lambda: complete(con, args.task, args.agent, args.token, args.detail or None),
              "fail": lambda: fail(con, args.task, args.agent, args.token, args.detail or "unspecified"),
              "heartbeat": lambda: heartbeat(con, args.task, args.agent, args.token)}[args.action]
        print(render(fn()))


if __name__ == "__main__":
    main()
