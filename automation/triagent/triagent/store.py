"""Durable research memory: SQLite in WAL mode, versioned migrations, daily backups.

The database never replaces the original evidence: it stores references (paths, URLs,
transaction hashes) and SHA-256 digests of every captured source.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

STATUSES = ("queued", "running", "awaiting_external_result", "reviewing", "done", "failed", "blocked", "paused")
AGENTS = ("claude", "grok")
KINDS = ("analysis", "develop", "x_research")
EDGE_KINDS = ("DIRECT_TRANSFER", "SAME_FUNDER", "SAME_DEPOSIT_ADDRESS", "BRIDGE_ORDER",
              "SHARED_SERVICE", "TEMPORAL_CORRELATION", "HYPOTHESIS")
EDGE_LEVELS = ("receipt_verified", "agent_reported", "derived", "hypothesis")
TIERS = ("CONFIRMED", "SUPPORTED", "HYPOTHESIS", "REFUTED", "UNRESOLVED")

MIGRATIONS: list[str] = [
    # 1: initial schema
    f"""
    CREATE TABLE investigations (
        id TEXT PRIMARY KEY, title TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'open'
            CHECK (status IN ('open','exhausted','closed')),
        created INTEGER NOT NULL, updated INTEGER NOT NULL,
        low_novelty_streak INTEGER NOT NULL DEFAULT 0, summary TEXT NOT NULL DEFAULT '');
    CREATE TABLE jobs (
        id TEXT PRIMARY KEY,
        agent TEXT NOT NULL CHECK (agent IN {AGENTS}),
        kind TEXT NOT NULL CHECK (kind IN {KINDS}),
        novelty_key TEXT NOT NULL UNIQUE,
        task TEXT NOT NULL, falsifier TEXT NOT NULL DEFAULT '',
        investigation TEXT NOT NULL REFERENCES investigations(id),
        parent TEXT, depth INTEGER NOT NULL, origin TEXT NOT NULL, priority INTEGER NOT NULL DEFAULT 3,
        status TEXT NOT NULL CHECK (status IN {STATUSES}), status_reason TEXT NOT NULL DEFAULT '',
        created INTEGER NOT NULL, updated INTEGER NOT NULL, started INTEGER, finished INTEGER,
        attempts INTEGER NOT NULL DEFAULT 0, review_attempts INTEGER NOT NULL DEFAULT 0,
        deadline INTEGER, pid INTEGER, session_id TEXT, external_nonce TEXT, mission_dir TEXT,
        context_sha256 TEXT, result_json TEXT, result_sha256 TEXT, review_json TEXT,
        novelty INTEGER, decision TEXT, cost_usd REAL NOT NULL DEFAULT 0);
    CREATE INDEX jobs_status ON jobs(status, agent, priority, created);
    CREATE TABLE events (
        id INTEGER PRIMARY KEY, ts INTEGER NOT NULL, level TEXT NOT NULL, kind TEXT NOT NULL,
        job_id TEXT, message TEXT NOT NULL);
    CREATE INDEX events_ts ON events(ts);
    CREATE TABLE costs (
        id INTEGER PRIMARY KEY, ts INTEGER NOT NULL, provider TEXT NOT NULL, job_id TEXT,
        usd REAL NOT NULL, estimated INTEGER NOT NULL, units_json TEXT NOT NULL DEFAULT '{{}}');
    CREATE INDEX costs_ts ON costs(provider, ts);
    CREATE TABLE evidence (
        sha256 TEXT PRIMARY KEY, source TEXT NOT NULL, ref TEXT NOT NULL, chain TEXT,
        fetched_at INTEGER NOT NULL, path TEXT NOT NULL, bytes INTEGER NOT NULL, job_id TEXT);
    CREATE TABLE findings (
        id INTEGER PRIMARY KEY, investigation TEXT NOT NULL, job_id TEXT NOT NULL,
        type TEXT NOT NULL CHECK (type IN ('claim','question','negative','method','test')),
        text TEXT NOT NULL, tier TEXT, evidence_json TEXT NOT NULL DEFAULT '[]',
        window_start INTEGER, window_end INTEGER, method_version TEXT, created INTEGER NOT NULL,
        UNIQUE (investigation, type, text, job_id));
    CREATE TABLE wallets (
        address TEXT PRIMARY KEY, first_seen INTEGER NOT NULL, profiled_at INTEGER,
        first_activity_ts INTEGER, first_deposit_ts INTEGER, first_trade_ts INTEGER,
        n_events INTEGER, truncated INTEGER, profile_json TEXT, examined_by TEXT);
    CREATE TABLE edges (
        id INTEGER PRIMARY KEY, src TEXT NOT NULL, dst TEXT NOT NULL,
        kind TEXT NOT NULL CHECK (kind IN {EDGE_KINDS}), chain TEXT NOT NULL DEFAULT '',
        tx_hash TEXT NOT NULL DEFAULT '', token TEXT NOT NULL DEFAULT '', amount TEXT NOT NULL DEFAULT '',
        ts INTEGER, method TEXT NOT NULL, level TEXT NOT NULL CHECK (level IN {EDGE_LEVELS}),
        evidence_sha256 TEXT, job_id TEXT, created INTEGER NOT NULL,
        UNIQUE (src, dst, kind, chain, tx_hash));
    CREATE INDEX edges_dst ON edges(dst, kind);
    CREATE INDEX edges_src ON edges(src, kind);
    CREATE TABLE trades (
        tx_hash TEXT NOT NULL, proxy_wallet TEXT NOT NULL, condition_id TEXT NOT NULL,
        token_id TEXT NOT NULL, side TEXT NOT NULL, size REAL NOT NULL, price REAL NOT NULL,
        usdc REAL NOT NULL, ts INTEGER NOT NULL, title TEXT, outcome TEXT, seen_at INTEGER NOT NULL,
        onchain TEXT NOT NULL DEFAULT 'pending' CHECK (onchain IN ('pending','confirmed','missing')),
        PRIMARY KEY (tx_hash, proxy_wallet, token_id, side, size, price));
    CREATE INDEX trades_market ON trades(condition_id, outcome, ts);
    CREATE INDEX trades_wallet ON trades(proxy_wallet, ts);
    CREATE TABLE alerts (
        id INTEGER PRIMARY KEY, created INTEGER NOT NULL, address TEXT NOT NULL, condition_id TEXT NOT NULL,
        trade_ts INTEGER NOT NULL, usdc REAL NOT NULL, score INTEGER NOT NULL, flags_json TEXT NOT NULL,
        features_json TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'new', job_id TEXT,
        UNIQUE (address, condition_id));
    CREATE TABLE known_addresses (address TEXT NOT NULL, source_path TEXT NOT NULL,
        PRIMARY KEY (address, source_path));
    CREATE TABLE inventory (
        id TEXT PRIMARY KEY, path TEXT NOT NULL, title TEXT, state TEXT, objective TEXT,
        conclusions TEXT, limits TEXT, sha256 TEXT NOT NULL, scanned_at INTEGER NOT NULL);
    CREATE TABLE kv (key TEXT PRIMARY KEY, value TEXT NOT NULL);
    """,
    # 2: public service labels (bridges, pools, exchanges): shared infrastructure is not a link between people
    """
    CREATE TABLE labels (address TEXT PRIMARY KEY, tags_json TEXT NOT NULL, source TEXT NOT NULL,
        fetched_at INTEGER NOT NULL);
    """,
    # 3: event bus to n8n, single-use leases, observed run durations, two-phase alerts
    """
    CREATE TABLE bus (event_id TEXT PRIMARY KEY, event_type TEXT NOT NULL, job_id TEXT NOT NULL DEFAULT '',
        alert_id TEXT NOT NULL DEFAULT '', created INTEGER NOT NULL, origin TEXT NOT NULL, sent_at INTEGER,
        send_attempts INTEGER NOT NULL DEFAULT 0, next_try INTEGER NOT NULL DEFAULT 0,
        last_error TEXT NOT NULL DEFAULT '', ingested_at INTEGER);
    CREATE INDEX bus_unsent ON bus(sent_at, next_try);
    CREATE TABLE leases (lease_id TEXT PRIMARY KEY, work_id TEXT NOT NULL, agent TEXT NOT NULL,
        task_type TEXT NOT NULL, created INTEGER NOT NULL, expires INTEGER NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('open','dispatched','finished','expired','rejected','interrupted')),
        ended INTEGER, outcome TEXT NOT NULL DEFAULT '');
    CREATE UNIQUE INDEX leases_active ON leases(work_id) WHERE state IN ('open','dispatched');
    CREATE TABLE runs (id INTEGER PRIMARY KEY, provider TEXT NOT NULL, task_type TEXT NOT NULL,
        work_id TEXT NOT NULL, mode TEXT NOT NULL DEFAULT '', model TEXT NOT NULL DEFAULT '', session_id TEXT,
        queued_at INTEGER, started_at INTEGER NOT NULL, last_progress_at INTEGER, finished_at INTEGER,
        runtime_sec REAL, exit_status TEXT, attempts INTEGER, source TEXT NOT NULL DEFAULT 'measured');
    CREATE INDEX runs_kind ON runs(provider, task_type, finished_at);
    ALTER TABLE alerts ADD COLUMN level TEXT NOT NULL DEFAULT 'WATCH';
    ALTER TABLE alerts ADD COLUMN notified_at INTEGER
    """,
    # 4: shadow record of new accounts (factory events) and the payer of their first deposit
    """
    CREATE TABLE new_accounts (proxy TEXT PRIMARY KEY, factory TEXT NOT NULL, owner TEXT NOT NULL DEFAULT '',
        block INTEGER NOT NULL, tx_hash TEXT NOT NULL, created_ts INTEGER, observed_at INTEGER NOT NULL,
        checked_at INTEGER, checks INTEGER NOT NULL DEFAULT 0, first_trade_ts INTEGER, first_deposit_tx TEXT,
        first_deposit_ts INTEGER, receipt_sha256 TEXT, funder TEXT, funder_via TEXT, deposit_token TEXT,
        deposit_value TEXT);
    CREATE INDEX new_accounts_funder ON new_accounts(funder, first_deposit_ts);
    CREATE INDEX new_accounts_todo ON new_accounts(first_deposit_tx, observed_at)
    """,
    # 5: investigation center. Reports are derived from stored reviews (never from a new model call), one row per
    # (subject, source digest): a restart or a re-run finds the row and adds nothing. Preferences live in kv.
    """
    CREATE TABLE reports (id TEXT PRIMARY KEY, kind TEXT NOT NULL CHECK (kind IN ('mission','daily')),
        subject TEXT NOT NULL, version INTEGER NOT NULL, source_sha256 TEXT NOT NULL, investigation TEXT,
        created INTEGER NOT NULL, period_start INTEGER, period_end INTEGER,
        importance TEXT NOT NULL CHECK (importance IN ('major','normal','none')),
        title TEXT NOT NULL, body_md TEXT NOT NULL, sha256 TEXT NOT NULL, UNIQUE (kind, subject, source_sha256));
    CREATE INDEX reports_created ON reports(created);
    CREATE INDEX reports_inv ON reports(investigation, created);
    CREATE TABLE notifications (key TEXT PRIMARY KEY, kind TEXT NOT NULL, created INTEGER NOT NULL,
        title TEXT NOT NULL, message TEXT NOT NULL, link TEXT NOT NULL, sent INTEGER NOT NULL,
        reason TEXT NOT NULL DEFAULT '');
    CREATE INDEX notifications_kind ON notifications(kind, created);
    CREATE TABLE ideas (id INTEGER PRIMARY KEY, created INTEGER NOT NULL, text TEXT NOT NULL,
        investigation TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending'
            CHECK (status IN ('pending','planned','failed')),
        decided_at INTEGER, decision_json TEXT)
    """,
]
EVENT_TYPES = ("work.ready", "mission.completed", "mission.failed", "alert.early", "provider.blocked",
               "provider.unblocked")


def now() -> int:
    return int(time.time())


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def normalize_key(value: str) -> str:
    return " ".join(str(value).lower().split())[:200]


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.migrate()

    @contextmanager
    def conn(self, immediate: bool = False):
        c = sqlite3.connect(self.path, timeout=30, isolation_level=None)
        c.row_factory = sqlite3.Row
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA busy_timeout=30000")
        c.execute("PRAGMA foreign_keys=ON")
        try:
            c.execute("BEGIN IMMEDIATE" if immediate else "BEGIN")
            yield c
            c.execute("COMMIT")
        except BaseException:
            c.execute("ROLLBACK")
            raise
        finally:
            c.close()

    def migrate(self):
        with self.conn(immediate=True) as c:
            c.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
            row = c.execute("SELECT max(version) FROM schema_version").fetchone()
            current = row[0] or 0
            for version, script in enumerate(MIGRATIONS, start=1):
                if version <= current:
                    continue
                for statement in [s for s in script.split(";") if s.strip()]:
                    c.execute(statement)
                c.execute("INSERT INTO schema_version(version) VALUES (?)", (version,))

    def schema_version(self) -> int:
        with self.conn() as c:
            return c.execute("SELECT max(version) FROM schema_version").fetchone()[0]

    def integrity_ok(self) -> bool:
        with self.conn() as c:
            return c.execute("PRAGMA quick_check").fetchone()[0] == "ok"

    def backup(self, target_dir: Path, keep: int = 7) -> Path:
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / time.strftime("triagent-%Y%m%dT%H%M%SZ.sqlite3", time.gmtime())
        src = sqlite3.connect(self.path)
        dst = sqlite3.connect(target)
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
        for old in sorted(target_dir.glob("triagent-*.sqlite3"))[:-keep]:
            old.unlink()
        return target

    # ---- run log, key/value, costs ----
    def log(self, kind: str, message: str, *, level: str = "info", job_id: str | None = None):
        with self.conn() as c:
            c.execute("INSERT INTO events(ts,level,kind,job_id,message) VALUES (?,?,?,?,?)",
                      (now(), level, kind, job_id, message[:4000]))

    def get_kv(self, key: str, default: str | None = None) -> str | None:
        with self.conn() as c:
            row = c.execute("SELECT value FROM kv WHERE key=?", (key,)).fetchone()
            return row[0] if row else default

    def set_kv(self, key: str, value: Any):
        with self.conn() as c:
            c.execute("INSERT INTO kv(key,value) VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                      (key, str(value)))

    def add_cost(self, provider: str, usd: float, *, job_id: str | None, estimated: bool, units: dict | None = None):
        with self.conn() as c:
            c.execute("INSERT INTO costs(ts,provider,job_id,usd,estimated,units_json) VALUES (?,?,?,?,?,?)",
                      (now(), provider, job_id, float(usd or 0), int(estimated), canonical(units or {})))
            if job_id:
                c.execute("UPDATE jobs SET cost_usd=cost_usd+? WHERE id=?", (float(usd or 0), job_id))

    def spent(self, provider: str, since: int) -> tuple[float, int]:
        with self.conn() as c:
            row = c.execute("SELECT coalesce(sum(usd),0), count(*) FROM costs WHERE provider=? AND ts>=?",
                            (provider, since)).fetchone()
            return float(row[0]), int(row[1])

    # ---- investigations and jobs ----
    def ensure_investigation(self, inv_id: str, title: str) -> str:
        with self.conn() as c:
            c.execute("INSERT OR IGNORE INTO investigations(id,title,created,updated) VALUES (?,?,?,?)",
                      (inv_id, title[:300], now(), now()))
        return inv_id

    def investigation(self, inv_id: str) -> dict | None:
        with self.conn() as c:
            row = c.execute("SELECT * FROM investigations WHERE id=?", (inv_id,)).fetchone()
            return dict(row) if row else None

    def enqueue(self, agent: str, kind: str, key: str, task: str, *, origin: str,
                investigation: str | None = None, parent: str | None = None, depth: int = 0,
                falsifier: str = "", priority: int = 3, max_depth: int = 4) -> str | None:
        """Insert a mission; returns None when it duplicates a previous novelty key or is out of bounds."""
        if agent not in AGENTS or kind not in KINDS:
            raise ValueError(f"invalid agent/kind {agent}/{kind}")
        if (agent == "grok") != (kind == "x_research"):
            raise ValueError("grok does x_research only; claude does analysis or develop")
        key = normalize_key(key)
        if len(key) < 8 or not task or len(task) > 8000:
            raise ValueError("invalid novelty key or task")
        if depth > max_depth:
            return None
        inv = investigation or ("inv-" + hashlib.sha256(key.encode()).hexdigest()[:12])
        if investigation is None:
            self.ensure_investigation(inv, task[:120])
        found = self.investigation(inv)
        if found and found["status"] != "open":
            return None
        ident = uuid.uuid4().hex[:16]
        with self.conn(immediate=True) as c:
            cur = c.execute(
                """INSERT OR IGNORE INTO jobs(id,agent,kind,novelty_key,task,falsifier,investigation,parent,depth,
                   origin,priority,status,created,updated) VALUES (?,?,?,?,?,?,?,?,?,?,?,'queued',?,?)""",
                (ident, agent, kind, key, task, falsifier[:2000], inv, parent, depth, origin,
                 max(1, min(5, int(priority))), now(), now()))
            added = bool(cur.rowcount)
        if added:
            self.emit("work.ready", job_id=ident)
        return ident if added else None

    def job(self, job_id: str) -> dict | None:
        with self.conn() as c:
            row = c.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
            return dict(row) if row else None

    def jobs(self, where: str = "1=1", params: Iterable = (), limit: int = 100) -> list[dict]:
        with self.conn() as c:
            return [dict(r) for r in c.execute(
                f"SELECT * FROM jobs WHERE {where} ORDER BY updated DESC LIMIT ?", (*params, limit))]

    def claim(self, agent: str, job_id: str | None = None) -> dict | None:
        """Atomically move the best (or the given) queued job of an agent to running."""
        with self.conn(immediate=True) as c:
            row = c.execute("""SELECT * FROM jobs WHERE agent=? AND status='queued' AND (? IS NULL OR id=?)
                               ORDER BY priority DESC, created, id LIMIT 1""", (agent, job_id, job_id)).fetchone()
            if not row:
                return None
            c.execute("UPDATE jobs SET status='running',attempts=attempts+1,started=?,updated=? WHERE id=?",
                      (now(), now(), row["id"]))
            return dict(row) | {"status": "running", "attempts": row["attempts"] + 1}

    def set_status(self, job_id: str, status: str, reason: str = "", *, expect: tuple[str, ...] | None = None,
                   **fields) -> bool:
        if status not in STATUSES:
            raise ValueError(status)
        cols = {"status": status, "status_reason": reason[:1000], "updated": now(), **fields}
        if status in ("done", "failed"):
            cols.setdefault("finished", now())
        assign = ",".join(f"{k}=?" for k in cols)
        sql = f"UPDATE jobs SET {assign} WHERE id=?"
        params: list[Any] = [*cols.values(), job_id]
        if expect:
            sql += f" AND status IN ({','.join('?' * len(expect))})"
            params += list(expect)
        with self.conn(immediate=True) as c:
            changed = c.execute(sql, params).rowcount == 1
        if changed and status == "failed":
            self.emit("mission.failed", job_id=job_id)
        return changed

    def save_result(self, job_id: str, result: dict) -> str:
        """Persist the raw result before any review: a provider failure later cannot lose it."""
        text = canonical(result)
        digest = sha256_bytes(text.encode())
        self.set_status(job_id, "reviewing", "result stored, awaiting review",
                        result_json=text, result_sha256=digest)
        self.emit("mission.completed", job_id=job_id)
        return digest

    # ---- event bus and observed durations ----
    def emit(self, event_type: str, *, job_id: str = "", alert_id: str = "", origin: str = "broker") -> str:
        """Queue an event for n8n. A fresh id per occurrence; a redelivery keeps it, so ingest stays idempotent."""
        if event_type not in EVENT_TYPES:
            raise ValueError(event_type)
        event_id = f"{event_type}:{job_id or alert_id or 'none'}:{uuid.uuid4().hex[:12]}"[:120]
        with self.conn() as c:
            c.execute("INSERT INTO bus(event_id,event_type,job_id,alert_id,created,origin) VALUES (?,?,?,?,?,?)",
                      (event_id, event_type, str(job_id)[:100], str(alert_id)[:100], now(), origin))
        return event_id

    def run_start(self, provider: str, task_type: str, work_id: str, **fields) -> None:
        cols = {"provider": provider, "task_type": task_type, "work_id": work_id, "started_at": now(), **fields}
        with self.conn() as c:
            c.execute(f"INSERT INTO runs({','.join(cols)}) VALUES ({','.join('?' * len(cols))})", list(cols.values()))

    def run_end(self, work_id: str, exit_status: str, provider: str | None = None) -> None:
        with self.conn() as c:
            c.execute("""UPDATE runs SET finished_at=?, runtime_sec=?-started_at, exit_status=? WHERE id=(
                         SELECT max(id) FROM runs WHERE work_id=? AND finished_at IS NULL AND (? IS NULL OR provider=?))""",
                      (now(), now(), exit_status, work_id, provider, provider))

    def counts(self) -> dict:
        with self.conn() as c:
            return {r[0]: r[1] for r in c.execute("SELECT status,count(*) FROM jobs GROUP BY status")}

    def recent_keys(self, limit: int = 150) -> list[str]:
        with self.conn() as c:
            return [r[0] for r in c.execute("SELECT novelty_key FROM jobs ORDER BY created DESC LIMIT ?", (limit,))]

    # ---- research memory ----
    def add_finding(self, inv: str, job_id: str, type_: str, text: str, *, tier: str | None = None,
                    evidence: list | None = None, window: tuple | None = None, version: str | None = None):
        if tier is not None and tier not in TIERS:
            tier = "UNRESOLVED"
        with self.conn() as c:
            c.execute("""INSERT INTO findings(investigation,job_id,type,text,tier,evidence_json,window_start,
                         window_end,method_version,created) VALUES (?,?,?,?,?,?,?,?,?,?)
                         ON CONFLICT DO NOTHING""",  # one row per mission: divergent verdicts stay visible
                      (inv, job_id, type_, text[:2000], tier, canonical(evidence or []),
                       (window or (None, None))[0], (window or (None, None))[1], version, now()))

    def findings(self, inv: str | None = None, limit: int = 200) -> list[dict]:
        with self.conn() as c:
            if inv:
                rows = c.execute("SELECT * FROM findings WHERE investigation=? ORDER BY id DESC LIMIT ?", (inv, limit))
            else:
                rows = c.execute("SELECT * FROM findings ORDER BY id DESC LIMIT ?", (limit,))
            return [dict(r) for r in rows]

    def add_edge(self, src: str, dst: str, kind: str, *, method: str, level: str, chain: str = "",
                 tx_hash: str = "", token: str = "", amount: str = "", ts: int | None = None,
                 evidence_sha256: str | None = None, job_id: str | None = None) -> bool:
        if kind not in EDGE_KINDS or level not in EDGE_LEVELS:
            raise ValueError(f"bad edge {kind}/{level}")
        if kind in ("DIRECT_TRANSFER", "BRIDGE_ORDER") and level == "receipt_verified" and not tx_hash:
            raise ValueError("a verified transfer needs its transaction")
        with self.conn() as c:
            cur = c.execute("""INSERT INTO edges(src,dst,kind,chain,tx_hash,token,amount,ts,method,level,
                               evidence_sha256,job_id,created) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                               ON CONFLICT(src,dst,kind,chain,tx_hash) DO UPDATE SET
                               level=CASE WHEN excluded.level='receipt_verified' THEN excluded.level ELSE level END,
                               evidence_sha256=coalesce(excluded.evidence_sha256, evidence_sha256)""",
                            (src.lower(), dst.lower(), kind, chain, tx_hash.lower(), token.lower(), str(amount),
                             ts, method, level, evidence_sha256, job_id, now()))
            return cur.rowcount == 1

    def add_evidence(self, sha: str, source: str, ref: str, path: Path, size: int, *,
                     chain: str | None = None, job_id: str | None = None):
        with self.conn() as c:
            c.execute("INSERT OR IGNORE INTO evidence(sha256,source,ref,chain,fetched_at,path,bytes,job_id) "
                      "VALUES (?,?,?,?,?,?,?,?)", (sha, source, ref[:1000], chain, now(), str(path), size, job_id))

    def query(self, sql: str, params: Iterable = ()) -> list[dict]:
        with self.conn() as c:
            return [dict(r) for r in c.execute(sql, tuple(params))]

    def execute(self, sql: str, params: Iterable = ()) -> int:
        with self.conn(immediate=True) as c:
            return c.execute(sql, tuple(params)).rowcount
