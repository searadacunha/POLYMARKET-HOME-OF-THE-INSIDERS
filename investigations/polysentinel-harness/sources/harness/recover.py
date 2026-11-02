"""Durable queue and everything that keeps it honest after a crash: leases, fencing, retries, circuits, resources.

A task can run twice, so its effects commit with its checkpoint and carry unique keys. A worker that lost its
lease cannot write, because every write checks the owner and attempt in the same transaction.
"""
import fcntl
import hashlib
import json
import os
import random
import re
import shutil
import time

from polysentinel.storage_budget import storage_usage

from .store import dumps


class Transient(Exception):
    """Worth another try, after a delay."""
    def __init__(self, message, retry_after=None):
        super().__init__(message)
        self.retry_after = retry_after


class InvalidResponse(Transient):
    """A response that fails validation is never stored as data. It may be a truncated read, so it gets retried."""


class Permanent(Exception):
    """Another try would give the same answer."""


class Pause(Exception):
    """Not the task's fault (budget, resources, outage): waits without spending an attempt."""
    def __init__(self, message, delay=300):
        super().__init__(message)
        self.delay = delay


class LeaseLost(Exception):
    pass


def backoff(task_id, attempt, base=2.0, cap=600.0):
    return min(cap, base * 2 ** max(0, attempt - 1)) * (0.5 + random.Random(f'{task_id}:{attempt}').random() / 2)


def signature(kind, exc):
    """Same failure despite different ids, amounts or addresses."""
    text = re.sub(r'0x[0-9a-fA-F]+|\d+', '#', str(exc))[:200]
    return hashlib.sha1(f'{kind}|{type(exc).__name__}|{text}'.encode()).hexdigest()[:16]


def enqueue(h, dedupe_key, kind, params=None, priority=0.0, needs=(), why='', max_attempts=4):
    """Returns (id, created). The same key never makes a second task: redundant plans cost nothing."""
    now = time.time()
    with h.tx() as cx:
        row = cx.execute('SELECT id FROM tasks WHERE dedupe_key=?', (dedupe_key,)).fetchone()
        if row:
            return row[0], False
        task = cx.execute('INSERT INTO tasks(dedupe_key, kind, params, priority, max_attempts, why, created_at, updated_at) VALUES(?,?,?,?,?,?,?,?)',
                          (dedupe_key, kind, dumps(params or {}), priority, max_attempts, why, now, now)).lastrowid
        cx.executemany('INSERT OR IGNORE INTO task_deps VALUES(?,?)', [(task, n) for n in needs])
        h.log('info', 'task_added', task, key=dedupe_key, why=why)
    return task, True


def open_circuits(h, now=None):
    now = now or time.time()
    return [r[0].split(':', 2)[2] for r in h.cx.execute("SELECT key, value FROM kv WHERE key LIKE 'harness:circuit:%'") if float(r[1]) > now]


def claim(h, owner, lease_s=120, now=None):
    now = now or time.time()
    closed = open_circuits(h, now)
    marks = ','.join('?' * len(closed))
    with h.tx() as cx:
        row = cx.execute(f"""SELECT * FROM tasks t WHERE status='pending' AND next_at<=? AND kind NOT IN ({marks})
                             AND NOT EXISTS(SELECT 1 FROM task_deps d JOIN tasks n ON n.id=d.needs WHERE d.task=t.id AND n.status<>'done')
                             ORDER BY priority DESC, id LIMIT 1""", (now, *closed)).fetchone()
        if row is None:
            return None
        cx.execute("UPDATE tasks SET status='running', owner=?, lease_until=?, attempts=attempts+1, updated_at=? WHERE id=?", (owner, now + lease_s, now, row['id']))
        h.log('info', 'task_claimed', row['id'], owner=owner, attempt=row['attempts'] + 1)
        return dict(cx.execute('SELECT * FROM tasks WHERE id=?', (row['id'],)).fetchone())


def _fenced(cx, task_id, owner, attempt):
    row = cx.execute('SELECT status, owner, attempts FROM tasks WHERE id=?', (task_id,)).fetchone()
    if row is None or row['status'] != 'running' or row['owner'] != owner or row['attempts'] != attempt:
        raise LeaseLost(f'task {task_id}: lease no longer held by {owner} attempt {attempt}')


def renew(h, task_id, owner, attempt, lease_s=120):
    with h.tx() as cx:
        _fenced(cx, task_id, owner, attempt)
        cx.execute('UPDATE tasks SET lease_until=? WHERE id=?', (time.time() + lease_s, task_id))


def commit(h, task_id, owner, attempt, checkpoint, write=None):
    """Output and checkpoint land together, or neither does."""
    with h.tx() as cx:
        _fenced(cx, task_id, owner, attempt)
        if write:
            write(cx)
        cx.execute('UPDATE tasks SET checkpoint=?, updated_at=? WHERE id=?', (dumps(checkpoint), time.time(), task_id))


def finish(h, task_id, owner, attempt, result=None, write=None):
    with h.tx() as cx:
        _fenced(cx, task_id, owner, attempt)
        if write:
            write(cx)
        cx.execute("UPDATE tasks SET status='done', result=?, owner=NULL, lease_until=NULL, updated_at=? WHERE id=?", (dumps(result), time.time(), task_id))
        h.log('info', 'task_done', task_id)


def _quarantine(cx, h, task_id, reason):
    cx.execute("UPDATE tasks SET status='quarantined', owner=NULL, lease_until=NULL, last_error=?, updated_at=? WHERE id=?", (reason[:500], time.time(), task_id))
    h.log('error', 'task_quarantined', task_id, reason=reason[:500])
    # Nothing can ever satisfy these dependents, and silently waiting would look like an empty queue.
    for row in cx.execute("""WITH RECURSIVE blocked(id) AS (SELECT task FROM task_deps WHERE needs=? UNION SELECT d.task FROM task_deps d JOIN blocked b ON d.needs=b.id)
                             SELECT id FROM blocked""", (task_id,)).fetchall():
        cx.execute("UPDATE tasks SET status='quarantined', last_error=?, updated_at=? WHERE id=? AND status='pending'", (f'dependency {task_id} quarantined', time.time(), row[0]))


def fail(h, task, exc, config, now=None):
    """Records one failed attempt and decides what comes next. Returns the outcome, or 'stale' if the lease moved on."""
    now = now or time.time()
    recovery = config.get('recovery', {})
    task_id, kind = task['id'], task['kind']
    mark = signature(kind, exc)
    message = f'{type(exc).__name__}: {exc}'[:500]
    with h.tx() as cx:
        row = cx.execute('SELECT status, owner, attempts, max_attempts FROM tasks WHERE id=?', (task_id,)).fetchone()
        if row is None or row['status'] != 'running' or row['owner'] != task['owner'] or row['attempts'] != task['attempts']:
            return 'stale'
        if isinstance(exc, Pause):
            cx.execute("UPDATE tasks SET status='pending', owner=NULL, lease_until=NULL, attempts=attempts-1, next_at=?, last_error=?, updated_at=? WHERE id=?", (now + exc.delay, message, now, task_id))
            h.log('warning', 'task_paused', task_id, reason=message)
            return 'paused'
        window = recovery.get('circuit_window_s', 600)
        cx.execute('''INSERT INTO errors VALUES(?,?,?,?,?,?,1,?,1) ON CONFLICT(signature) DO UPDATE SET last_at=excluded.last_at, total=total+1,
                      window_count=CASE WHEN ?-window_start>? THEN 1 ELSE window_count+1 END, window_start=CASE WHEN ?-window_start>? THEN excluded.window_start ELSE window_start END''',
                   (mark, kind, type(exc).__name__, message, now, now, now, now, window, now, window))
        repeats = cx.execute('SELECT window_count FROM errors WHERE signature=?', (mark,)).fetchone()[0]
        cx.execute('UPDATE tasks SET signature=? WHERE id=?', (mark, task_id))
        cx.execute("""INSERT INTO facts(kind, topic, key, value, at) VALUES('error', ?, ?, ?, ?) ON CONFLICT(topic, key, value) DO UPDATE SET seen=seen+1, at=excluded.at""", (kind, mark, message, now))
        if repeats >= recovery.get('circuit_failures', 5) and not isinstance(exc, Permanent):
            # Many tasks failing the same way is one outage: stop spending their attempts on it.
            h.signal.put(f'harness:circuit:{kind}', now + recovery.get('circuit_cooldown_s', 300))
            h.log('warning', 'circuit_open', task_id, kind=kind, signature=mark, repeats=repeats)
        if isinstance(exc, Permanent) or row['attempts'] >= row['max_attempts']:
            _quarantine(cx, h, task_id, message)
            return 'quarantined'
        delay = getattr(exc, 'retry_after', None)
        if delay is None:
            delay = backoff(task_id, row['attempts'], recovery.get('backoff_base_s', 2.0), recovery.get('backoff_cap_s', 600.0))
        cx.execute("UPDATE tasks SET status='pending', owner=NULL, lease_until=NULL, next_at=?, last_error=?, updated_at=? WHERE id=?", (now + delay, message, now, task_id))
        h.log('warning', 'task_retry', task_id, delay=round(delay, 3), error=message)
        return 'retry'


def reclaim_dead(h, owner, now=None):
    """Called holding the instance lock, so any other owner's running task is dead. A crash counts as an attempt, so a poison task ends in quarantine."""
    now = now or time.time()
    out = dict(requeued=0, quarantined=0)
    with h.tx() as cx:
        for row in cx.execute("SELECT id, attempts, max_attempts, owner FROM tasks WHERE status='running' AND owner<>?", (owner,)).fetchall():
            if row['attempts'] >= row['max_attempts']:
                _quarantine(cx, h, row['id'], f'crashed {row["attempts"]} times, last owner {row["owner"]}')
                out['quarantined'] += 1
            else:
                cx.execute("UPDATE tasks SET status='pending', owner=NULL, lease_until=NULL, next_at=0, updated_at=? WHERE id=?", (now, row['id']))
                h.log('warning', 'task_reclaimed', row['id'], previous_owner=row['owner'])
                out['requeued'] += 1
    return out


class InstanceLock:
    """Released by the kernel when the process dies, however it dies, so a crash never leaves a stale lock."""

    def __init__(self, path):
        self.path, self.file, self.acquired = path, None, False

    def __enter__(self):
        self.file = open(self.path, 'w')
        try:
            fcntl.flock(self.file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.acquired = True
            self.file.write(str(os.getpid()))
            self.file.flush()
        except BlockingIOError:
            self.acquired = False
        return self

    def __exit__(self, *args):
        self.file.close()


def retry_call(fn, attempts=4, base=0.5, cap=30.0, sleep=time.sleep, on_retry=None, seed='retry'):
    """Bounded retry for one read inside a task. Raises the last error when attempts run out."""
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Transient as exc:
            if attempt == attempts:
                raise
            delay = exc.retry_after if exc.retry_after is not None else min(cap, base * 2 ** (attempt - 1)) * (0.5 + random.Random(f'{seed}:{attempt}').random() / 2)
            if on_retry:
                on_retry(attempt, exc, delay)
            sleep(delay)


def resource_block(root, config, now=None):
    """The collector comes first: a reason here stops the passage before it adds any load."""
    limits = config['resources']
    free = shutil.disk_usage(root).free
    if free < limits['disk_floor_bytes']:
        return f"disk: {free / 1e9:.2f} GB free, floor {limits['disk_floor_bytes'] / 1e9:.2f} GB"
    used = storage_usage(root)['quota_accounted_bytes']
    if used >= limits['root_quota_bytes']:
        return f"storage: {used / 1e6:.1f} MB used, budget {limits['root_quota_bytes'] / 1e6:.1f} MB"
    load = os.getloadavg()[0]
    if load > limits['max_load']:
        return f"load: {load:.1f}, ceiling {limits['max_load']}"
    heartbeat = config.get('source', {}).get('heartbeat')
    if heartbeat:
        from signal_engine.service import collector_refusal
        return collector_refusal(now or time.time(), os.path.expanduser(heartbeat))
    return None


def load_json(text, default=None):
    return json.loads(text) if text else default
