"""PLAN: turns the state into tasks, by rule and without a model. Running it twice adds nothing, because every task has a stable key."""
import json
import sqlite3
import time

from . import pipeline
from .recover import enqueue
from .sources import CollectorSource


class SourceUnavailable(RuntimeError):
    pass


def plan(h, config, now=None):
    """Returns the keys it added. Order of the queue comes from each task's priority, not from here."""
    now = now or time.time()
    pending = h.cx.execute("SELECT COUNT(*) FROM tasks WHERE status='pending'").fetchone()[0]
    if pending >= config['recovery']['max_pending']:
        with h.tx():
            h.log('warning', 'plan_skipped', pending=pending)
        return []
    added = []

    def add(key, kind, params, priority, why, **kwargs):
        _, created = enqueue(h, key, kind, params, priority, why=why, **kwargs)
        if created:
            added.append(key)

    # 1. New rows at the collector. The key names the data, so a finished read does not repeat and new rows make a new task.
    cursor = h.signal.get('harness:cursor') or 0
    latest = None
    try:
        source = CollectorSource(config['source'])
        try:
            latest = source.cx.execute("SELECT MAX(observed_at) FROM object_refs WHERE kind='trade'").fetchone()[0]
        finally:
            source.close()
    except sqlite3.Error as exc:
        raise SourceUnavailable(f"Collector database unreadable at {config['source'].get('database')}: {exc}") from exc  # an empty queue must not read as nothing to do
    # One reader at a time: a retry waiting beside a fresh task would read the same rows twice and move the cursor back.
    reading = h.cx.execute("SELECT 1 FROM tasks WHERE kind='discover' AND status IN ('pending','running') LIMIT 1").fetchone()
    if latest and latest > cursor and not reading:
        add(f'discover:{cursor}:{latest}', 'discover', {}, .5, f'rows up to {latest} after cursor {cursor}')

    # 2. Unresolved cases: looked at again later, and only a few times, since new data may or may not come.
    recheck = config.get('recheck', dict(after_s=86400, rounds=3))
    for row in h.cx.execute("SELECT id, kind, updated_at FROM hypotheses WHERE status='needs_data' AND kind='case' AND updated_at<?", (now - recheck['after_s'],)).fetchall():
        rounds = h.cx.execute('SELECT COUNT(*) FROM verifications WHERE hypothesis=?', (row['id'],)).fetchone()[0]
        if rounds <= recheck['rounds']:
            first = h.cx.execute('SELECT params FROM tasks WHERE dedupe_key=?', (f"case:{row['id']}:case_dossier",)).fetchone()
            pipeline.add_case_tasks(h, row['id'], {k: v for k, v in json.loads(first['params']).items() if k not in ('hypothesis', 'suffix')}, .3, suffix=f':r{rounds}')
            added.append(f"recheck:{row['id']}:r{rounds}")

    # 3. A model only when nothing deterministic is left, within budget, and not too often.
    llm = config['llm']
    idle = not added and h.cx.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('pending','running')").fetchone()[0] == 0
    if llm.get('enabled') and idle and h.used('llm_calls') < config['budgets']['llm_calls_per_day']:
        add(f"propose:{int(now // llm['cooldown_s'])}", 'propose_hypotheses', {}, .1, 'queue empty, model allowed', max_attempts=2)
    return added
