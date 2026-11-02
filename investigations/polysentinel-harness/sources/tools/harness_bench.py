"""Measures what the harness changes, on synthetic data with known answers. It measures the mechanics and the filter, not the ability to detect private information.

`noise`: receipts for every trade, so the on-chain check hides nothing; how many cases does the engine open, and how many false alerts survive? `ladder`: how small can a planted case be and still pass?
`cost`: duration and peak memory of a run, context size against reading the project's notes.

Usage: python tools/harness_bench.py {noise,ladder,cost} STATE_DIR
"""
import json
import os
import resource
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('SIGNAL_ENGINE_STATE', str(ROOT / 'state/engine_state'))

from harness import demo, memory  # noqa: E402
from harness.store import Harness  # noqa: E402

SMALL = dict(wallets=700, events=40, batch_rows=200)


def run(root, seconds=600):
    started = time.monotonic()
    done = subprocess.run(['/usr/bin/time', '-l', sys.executable, '-m', 'harness', 'run', '--root', str(root), '--seconds', str(seconds)], cwd=ROOT, capture_output=True, text=True, check=True)
    peak = next((int(line.split()[0]) for line in done.stderr.splitlines() if 'maximum resident set size' in line), 0)
    return dict(out=json.loads(done.stdout.strip().splitlines()[-1]), seconds=time.monotonic() - started, supervisor_peak_mb=peak / 1e6)


def receipts_for_all(root):
    """Every trade gets a matching receipt, so a false alert cannot hide behind a missing one."""
    import sqlite3
    import zlib
    cx = sqlite3.connect(root / 'demo_collector/data/polysentinel.sqlite3')
    existing = json.loads((root / 'demo_receipts.json').read_text())
    for body, in cx.execute("SELECT c.body FROM object_refs r JOIN contents c ON c.id=r.content_id WHERE r.kind='trade'"):
        trade = json.loads(zlib.decompress(body))
        existing.setdefault(trade['transaction_hash'], demo.receipt_for(trade))
    cx.close()
    (root / 'demo_receipts.json').write_text(json.dumps(existing))


def verdicts(root):
    h = Harness(root)
    try:
        rows = [(json.loads(r['spec'])['event_key'], r['status'], r['reason'] or '') for r in h.cx.execute('SELECT spec, status, reason FROM hypotheses')]
        return rows, h.cx.execute('SELECT COUNT(*) FROM alerts').fetchone()[0]
    finally:
        h.close()


def noise(state, seeds=(1, 2, 3, 4, 5)):
    out = []
    for seed in seeds:
        root = Path(state) / f'noise{seed}'
        shutil.rmtree(root, ignore_errors=True)
        demo.build(root, seed=seed, **SMALL)
        receipts_for_all(root)
        run(root)
        rows, alerts = verdicts(root)
        background = [r for r in rows if not r[0].startswith('case_')]
        planted = {r[0]: r[1] for r in rows if r[0].startswith('case_')}
        out.append(dict(seed=seed, engine_cases_on_background=len(background), background_validated=sum(r[1] == 'validated' for r in background), background_rejected=sum(r[1] == 'rejected' for r in background), background_open=sum(r[1] == 'needs_data' for r in background), alerts=alerts, planted=planted))
        print(json.dumps(out[-1]), flush=True)
        shutil.rmtree(root, ignore_errors=True)
    return out


def ladder(state, sizes=(90000, 30000, 10000, 5000, 3000, 2000, 1000)):
    """One case, three wallets, at each size, on ordinary trading only: other planted cases would count among its controls. Where it stops passing is the cost of the filter."""
    out = []
    for nominal in sizes:
        root = Path(state) / f'ladder{nominal}'
        shutil.rmtree(root, ignore_errors=True)
        demo.build(root, plant_cases=False, **SMALL)
        from polysentinel.db import Store
        store = Store(root / 'demo_collector')
        receipts = json.loads((root / 'demo_receipts.json').read_text())
        with store.transaction() as cx:
            event = 'ladder_case'
            start = demo.case_start(4) + 7200
            tokens = demo.put_event(store, event, demo.HIGH_RISK_TITLE, demo.T0 + 40 * 86400, cx=cx)
            for i in range(3):
                payload = demo.put_trade(store, f'ladder:{i}', demo.address(f'ladder{i}'), event, tokens[0], start + i, float(nominal), .3, demo.HIGH_RISK_TITLE, cx=cx)
                receipts[payload['transaction_hash']] = demo.receipt_for(payload)
        store.conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        store.conn.close()
        (root / 'demo_receipts.json').write_text(json.dumps(receipts))
        run(root)
        rows, _ = verdicts(root)
        found = [r for r in rows if r[0] == 'ladder_case']
        out.append(dict(nominal_per_wallet=nominal, engine_opened=bool(found), verdict=found[0][1] if found else None, reason=found[0][2][:200] if found else None))
        print(json.dumps(out[-1]), flush=True)
        shutil.rmtree(root, ignore_errors=True)
    return out


def cost(state):
    root = Path(state) / 'cost'
    shutil.rmtree(root, ignore_errors=True)
    demo.build(root, **SMALL)
    result = run(root)
    h = Harness(root)
    tasks = h.cx.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0]
    pack = memory.context_pack(h, 'case_true_case rejected funding', 6000)
    usage = h.status()['usage']
    h.close()
    production = Path.home() / 'Projects/PolySentinel'
    notes = sum((production / f).stat().st_size for f in ('JOURNAL_AGENTS.md', 'REPRISE.md'))
    size = sum(f.stat().st_size for f in root.rglob('*') if f.is_file() and 'demo_collector' not in f.parts)
    worker = subprocess.run(['/usr/bin/time', '-l', sys.executable, '-c', 'import sys;sys.path.insert(0,".");import os;os.environ["SIGNAL_ENGINE_STATE"]="/nonexistent";import harness.pipeline'], cwd=ROOT, capture_output=True, text=True)
    worker_peak = next((int(line.split()[0]) for line in worker.stderr.splitlines() if 'maximum resident set size' in line), 0)
    return dict(tasks=tasks, seconds=round(result['seconds'], 1), seconds_per_task=round(result['seconds'] / tasks, 3), supervisor_peak_mb=round(result['supervisor_peak_mb'], 1), worker_import_peak_mb=round(worker_peak / 1e6, 1), harness_state_mb=round(size / 1e6, 1), tokens=usage.get('llm_tokens', 0),
                context_chars=pack['chars'], project_notes_chars=notes, context_share_of_notes=round(pack['chars'] / notes, 4))


if __name__ == '__main__':
    fn = dict(noise=noise, ladder=ladder, cost=cost)[sys.argv[1]]
    state = Path(sys.argv[2])
    state.mkdir(parents=True, exist_ok=True)
    result = fn(state)
    (state / f'{sys.argv[1]}.json').write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
