"""One SQLite file for the engine's work state and the harness's memory, so one transaction covers both.

Two files would lose work: trades committed in one and a crash before the other leaves pairs that are never
evaluated again, because add_trades reports only rows it just inserted.
"""
import hashlib
import json
import sys
import time
import zlib
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from signal_engine.store import SignalStore  # noqa: E402

from .paths import assert_isolated  # noqa: E402

SCHEMA = '''
CREATE TABLE IF NOT EXISTS tasks(
    id INTEGER PRIMARY KEY, dedupe_key TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, params TEXT NOT NULL DEFAULT '{}', priority REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','running','done','quarantined')),
    attempts INT NOT NULL DEFAULT 0, max_attempts INT NOT NULL DEFAULT 4, next_at REAL NOT NULL DEFAULT 0, owner TEXT, lease_until REAL,
    checkpoint TEXT, result TEXT, last_error TEXT, signature TEXT, why TEXT, created_at REAL, updated_at REAL);
CREATE INDEX IF NOT EXISTS tasks_ready ON tasks(status, next_at, priority);
CREATE TABLE IF NOT EXISTS task_deps(task INT NOT NULL, needs INT NOT NULL, PRIMARY KEY(task, needs)) WITHOUT ROWID;
CREATE INDEX IF NOT EXISTS task_deps_needs ON task_deps(needs);
CREATE TABLE IF NOT EXISTS log(id INTEGER PRIMARY KEY, at REAL, level TEXT, event TEXT, task INT, data TEXT);
CREATE TABLE IF NOT EXISTS errors(signature TEXT PRIMARY KEY, kind TEXT, cls TEXT, message TEXT, first_at REAL, last_at REAL, total INT, window_start REAL, window_count INT);
CREATE TABLE IF NOT EXISTS usage(day INT, resource TEXT, amount REAL, PRIMARY KEY(day, resource)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS artifacts(sha TEXT PRIMARY KEY, body BLOB NOT NULL, raw_bytes INT NOT NULL);

CREATE TABLE IF NOT EXISTS hypotheses(
    id INTEGER PRIMARY KEY, fingerprint TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, statement TEXT NOT NULL, spec TEXT NOT NULL, proposer TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'proposed' CHECK(status IN ('proposed','validated','rejected','needs_data')), reason TEXT, created_at REAL, updated_at REAL);
CREATE TABLE IF NOT EXISTS verifications(
    id INTEGER PRIMARY KEY, hypothesis INT NOT NULL REFERENCES hypotheses(id), verifier TEXT NOT NULL, verdict TEXT NOT NULL CHECK(verdict IN ('PASS','FAIL','INCOMPLETE')),
    report_sha TEXT NOT NULL, input_sha TEXT NOT NULL, code_sha TEXT NOT NULL, at REAL);
-- An agent's word cannot validate anything: only the latest verification, by someone else, can.
CREATE TRIGGER IF NOT EXISTS validated_needs_proof BEFORE UPDATE OF status ON hypotheses WHEN NEW.status='validated' AND NOT EXISTS(
    SELECT 1 FROM verifications v WHERE v.hypothesis=NEW.id AND v.verdict='PASS' AND v.verifier<>NEW.proposer AND v.id=(SELECT MAX(id) FROM verifications WHERE hypothesis=NEW.id))
    BEGIN SELECT RAISE(ABORT, 'validated requires a passing verification by someone other than the proposer'); END;
CREATE TRIGGER IF NOT EXISTS validated_not_at_birth BEFORE INSERT ON hypotheses WHEN NEW.status='validated'
    BEGIN SELECT RAISE(ABORT, 'a hypothesis cannot be born validated'); END;
CREATE TRIGGER IF NOT EXISTS verifications_no_update BEFORE UPDATE ON verifications BEGIN SELECT RAISE(ABORT, 'verifications are append-only'); END;
CREATE TRIGGER IF NOT EXISTS verifications_no_delete BEFORE DELETE ON verifications BEGIN SELECT RAISE(ABORT, 'verifications are append-only'); END;

CREATE TABLE IF NOT EXISTS facts(
    id INTEGER PRIMARY KEY, kind TEXT NOT NULL CHECK(kind IN ('result','rejected','method_ok','method_bad','error','decision','limit','proposal')),
    topic TEXT NOT NULL, key TEXT NOT NULL, value TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'observed' CHECK(status IN ('verified','observed','contested','stale')),
    source_path TEXT, source_sha TEXT, hypothesis INT, at REAL, seen INT NOT NULL DEFAULT 1, UNIQUE(topic, key, value));
CREATE VIRTUAL TABLE IF NOT EXISTS facts_fts USING fts5(topic, key, value, content='facts', content_rowid='id', tokenize='unicode61');
CREATE TRIGGER IF NOT EXISTS facts_ai AFTER INSERT ON facts BEGIN INSERT INTO facts_fts(rowid, topic, key, value) VALUES(new.id, new.topic, new.key, new.value); END;
CREATE TABLE IF NOT EXISTS experiments(id INTEGER PRIMARY KEY, name TEXT, params TEXT, seed TEXT, code_sha TEXT, input_sha TEXT, metrics TEXT, outcome TEXT, at REAL);

CREATE TABLE IF NOT EXISTS rules(id INTEGER PRIMARY KEY, name TEXT NOT NULL, params TEXT NOT NULL, status TEXT NOT NULL CHECK(status IN ('candidate','active','rejected','retired')), report_sha TEXT, reason TEXT, at REAL);
CREATE UNIQUE INDEX IF NOT EXISTS one_active_rule ON rules(name) WHERE status='active';
CREATE TRIGGER IF NOT EXISTS active_needs_report BEFORE UPDATE OF status ON rules WHEN NEW.status='active' AND NEW.report_sha IS NULL AND OLD.status<>'active'
    BEGIN SELECT RAISE(ABORT, 'a rule becomes active only through the gate'); END;
CREATE TABLE IF NOT EXISTS holdout_uses(holdout_sha TEXT, rule INT, at REAL);
CREATE TABLE IF NOT EXISTS alerts(id INTEGER PRIMARY KEY, dedupe_key TEXT NOT NULL UNIQUE, hypothesis INT NOT NULL, event_key TEXT, body TEXT NOT NULL, sha TEXT NOT NULL, at REAL);
'''


def dumps(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False, default=str)


def sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else dumps(value).encode()).hexdigest()


class BudgetExceeded(RuntimeError):
    pass


class Harness:
    def __init__(self, root):
        self.root = assert_isolated(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.signal = SignalStore(self.root / 'harness.sqlite3')
        self.cx = self.signal.cx
        self.cx.isolation_level = None  # explicit transactions only, so a checkpoint and its output commit together
        self.cx.execute('PRAGMA synchronous=FULL')
        self.cx.execute('PRAGMA foreign_keys=ON')
        self.cx.executescript(SCHEMA)

    def close(self):
        self.signal.close()

    @contextmanager
    def tx(self):
        if self.cx.in_transaction:  # nested write joins the transaction already open
            yield self.cx
            return
        self.cx.execute('BEGIN IMMEDIATE')
        try:
            yield self.cx
            self.cx.execute('COMMIT')
        except BaseException:
            self.cx.execute('ROLLBACK')
            raise

    def log(self, level, event, task=None, **data):
        self.cx.execute('INSERT INTO log(at, level, event, task, data) VALUES(?,?,?,?,?)', (time.time(), level, event, task, dumps(data)))

    def put_artifact(self, value):
        raw = dumps(value).encode()
        digest = sha(raw)
        self.cx.execute('INSERT OR IGNORE INTO artifacts VALUES(?,?,?)', (digest, zlib.compress(raw), len(raw)))
        return digest

    def get_artifact(self, digest):
        row = self.cx.execute('SELECT body FROM artifacts WHERE sha=?', (digest,)).fetchone()
        if row is None:
            raise KeyError(f'artifact {digest} absent')
        raw = zlib.decompress(row[0])
        if sha(raw) != digest:
            raise ValueError(f'artifact {digest} altered')
        return json.loads(raw)

    def spend(self, resource, amount, limit=None):
        """Counts in the caller's transaction, so work that rolls back costs nothing on the books."""
        day = int(time.time() // 86400)
        used = self.used(resource)
        if limit is not None and used + amount > limit:
            raise BudgetExceeded(f'{resource}: {used + amount:g} over the daily limit of {limit:g}')
        self.cx.execute('INSERT INTO usage VALUES(?,?,?) ON CONFLICT(day, resource) DO UPDATE SET amount=amount+excluded.amount', (day, resource, amount))
        return used + amount

    def used(self, resource):
        row = self.cx.execute('SELECT amount FROM usage WHERE day=? AND resource=?', (int(time.time() // 86400), resource)).fetchone()
        return row[0] if row else 0.0

    def status(self):
        count = lambda table, column='status': {r[0]: r[1] for r in self.cx.execute(f'SELECT {column}, COUNT(*) FROM {table} GROUP BY 1')}
        return dict(last_passage=self.signal.get('harness:last_passage'), rows_too_late_for_cases=self.signal.get('harness:rows_too_late_for_cases') or 0, tasks=count('tasks'), hypotheses=count('hypotheses'), facts=count('facts'), alerts=self.cx.execute('SELECT COUNT(*) FROM alerts').fetchone()[0],
                    quarantined=[dict(r) for r in self.cx.execute("SELECT id, kind, dedupe_key, last_error FROM tasks WHERE status='quarantined' ORDER BY id DESC LIMIT 10")],
                    contested=[dict(r) for r in self.cx.execute("SELECT topic, key, value FROM facts WHERE status='contested' ORDER BY id DESC LIMIT 10")],
                    usage={r[0]: r[1] for r in self.cx.execute('SELECT resource, amount FROM usage WHERE day=?', (int(time.time() // 86400),))})

    def digest(self):
        """What the run concluded, without clocks or attempts: an interrupted run must reach the same value."""
        hypotheses = [tuple(r) for r in self.cx.execute('SELECT fingerprint, status, reason FROM hypotheses ORDER BY fingerprint')]
        alerts = [tuple(r) for r in self.cx.execute('SELECT dedupe_key, sha FROM alerts ORDER BY dedupe_key')]
        trades = self.cx.execute('SELECT COUNT(*) FROM trades').fetchone()[0]
        cases = [tuple(r) for r in self.cx.execute('SELECT event_key, version, category, fingerprint FROM cases ORDER BY event_key')]
        return sha(dict(hypotheses=hypotheses, alerts=alerts, trades=trades, cases=cases))
