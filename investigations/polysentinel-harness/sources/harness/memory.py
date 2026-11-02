"""Operational memory. It is a recollection, not a source of truth: a fact whose source changed is stale, and two facts that disagree are both shown as contested.

Nothing here touches model weights. Each run receives only what its question retrieves, under a character budget.
"""
import hashlib
import json
import re
import shutil
import subprocess
import os
import time
from pathlib import Path

from .store import dumps, sha

WORD = re.compile(r'\w{2,}', re.UNICODE)
OBJECTIVE = json.loads((Path(__file__).parent / 'objective.json').read_text())
SBS_CANDIDATES = (os.environ.get('HARNESS_SBS', ''), shutil.which('sbs') or '', str(Path.home() / '.local/bin/sbs'))


def _file_sha(path):
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except OSError:
        return None


def remember(h, kind, topic, key, value, *, status='observed', source_path=None, source_sha=None, hypothesis=None):
    """Returns the fact's status. A differing value under one topic and key contests both; neither is chosen here."""
    value = value if isinstance(value, str) else dumps(value)
    if source_path and not source_sha:
        source_sha = _file_sha(source_path)
    with h.tx() as cx:
        same = cx.execute('SELECT id, status FROM facts WHERE topic=? AND key=? AND value=?', (topic, key, value)).fetchone()
        if same:
            cx.execute('UPDATE facts SET seen=seen+1, at=? WHERE id=?', (time.time(), same['id']))
            return same['status']
        rivals = cx.execute("SELECT id FROM facts WHERE topic=? AND key=? AND value<>? AND kind=? AND status IN ('verified','observed','contested')", (topic, key, value, kind)).fetchall()
        if rivals:
            status = 'contested'
            cx.executemany("UPDATE facts SET status='contested' WHERE id=?", [(r['id'],) for r in rivals])
            h.log('warning', 'memory_contradiction', topic=topic, key=key, rivals=[r['id'] for r in rivals])
        cx.execute('INSERT INTO facts(kind, topic, key, value, status, source_path, source_sha, hypothesis, at) VALUES(?,?,?,?,?,?,?,?,?)',
                   (kind, topic, key, value, status, str(source_path) if source_path else None, source_sha, hypothesis, time.time()))
    return status


def _source_holds(h, row):
    if row['source_path']:
        return _file_sha(row['source_path']) == row['source_sha']
    if row['source_sha']:
        return h.cx.execute('SELECT 1 FROM artifacts WHERE sha=?', (row['source_sha'],)).fetchone() is not None
    return True


def recall(h, query, limit=20):
    """Ranked by relevance. Each fact's source is checked on the way out, so a stale one cannot pass as current."""
    words = WORD.findall(query)
    if not words:
        return []
    match = ' OR '.join(f'"{w}"' for w in words)
    rows = h.cx.execute('SELECT f.* FROM facts_fts JOIN facts f ON f.id=facts_fts.rowid WHERE facts_fts MATCH ? ORDER BY bm25(facts_fts) LIMIT ?', (match, limit)).fetchall()
    found = []
    for row in rows:
        fact = dict(row)
        if fact['status'] != 'stale' and not _source_holds(h, row):
            fact['status'] = 'stale'
            with h.tx() as cx:
                cx.execute("UPDATE facts SET status='stale' WHERE id=?", (fact['id'],))
                h.log('warning', 'memory_stale', fact=fact['id'], source=fact['source_path'])
        found.append(fact)
    return found


def propose(h, kind, statement, spec, proposer):
    """Returns (id, status, duplicate). The fingerprint ignores wording: rephrasing a rejected idea finds the rejection. Only new evidence in the spec reopens it."""
    fingerprint = sha(dict(kind=kind, spec=spec))
    now = time.time()
    with h.tx() as cx:
        row = cx.execute('SELECT id, status FROM hypotheses WHERE fingerprint=?', (fingerprint,)).fetchone()
        if row:
            return row['id'], row['status'], True
        new = cx.execute('INSERT INTO hypotheses(fingerprint, kind, statement, spec, proposer, created_at, updated_at) VALUES(?,?,?,?,?,?,?)', (fingerprint, kind, statement, dumps(spec), proposer, now, now)).lastrowid
    return new, 'proposed', False


def context_pack(h, query, budget_chars=6000):
    """The smallest useful briefing: objective, state, then what the question retrieves, rejections first so they are not retried."""
    status = h.status()
    head = [f"OBJECTIVE: {OBJECTIVE['objective']}", 'RULES: ' + ' '.join(OBJECTIVE['rules']),
            f"STATE: tasks {status['tasks']}; hypotheses {status['hypotheses']}; alerts {status['alerts']}"]
    words = WORD.findall(query)
    lines, order = [], dict(contested=0, stale=1, verified=2, observed=3)
    for fact in sorted(recall(h, query, limit=60), key=lambda f: (f['kind'] != 'rejected', order[f['status']])):
        lines.append(f"[{fact['kind']}/{fact['status']}#{fact['id']}] {fact['topic']} {fact['key']}: {fact['value'][:300]}")
    rejected = h.cx.execute("SELECT id, statement, reason FROM hypotheses WHERE status='rejected' ORDER BY id DESC LIMIT 200").fetchall()
    rejected = [r for r in rejected if not words or set(w.lower() for w in WORD.findall(r['statement'])) & set(w.lower() for w in words)]
    lines = [f"[rejected#{r['id']}] {r['statement'][:200]}: {(r['reason'] or '')[:200]}" for r in rejected[:30]] + lines
    used, kept = sum(len(x) + 1 for x in head), []
    for line in lines:
        if used + len(line) + 1 > budget_chars:
            break
        kept.append(line)
        used += len(line) + 1
    return dict(text='\n'.join(head + kept), chars=used, kept=len(kept), omitted=len(lines) - len(kept))


def compress_output(text, root, source='harness'):
    """Stop-Bullshiting's own reversible view, its receipts kept under this root. If it is absent, the original goes to a file and the head and tail stay readable."""
    root = Path(root)
    executable = next((c for c in SBS_CANDIDATES if c and Path(c).exists()), None)
    if executable:
        try:
            done = subprocess.run([executable, 'compress'], input=text, capture_output=True, text=True, timeout=30, env=dict(os.environ, SBS_HOME=str(root / 'sbs')))
            if done.returncode == 0 and done.stdout:
                return dict(view=done.stdout, tool='stop-bullshiting', original_chars=len(text), visible_chars=len(done.stdout))
        except (OSError, subprocess.SubprocessError):
            pass
    if len(text) <= 3500:
        return dict(view=text, tool='none', original_chars=len(text), visible_chars=len(text))
    keep = root / 'originals'
    keep.mkdir(parents=True, exist_ok=True)
    path = keep / f'{sha(text.encode())[:16]}.txt'
    path.write_text(text)
    view = f'{text[:1600]}\n... [{len(text) - 3200} chars omitted, full text: {path}] ...\n{text[-1600:]}'
    return dict(view=view, tool='fallback', original_chars=len(text), visible_chars=len(view), original=str(path))
