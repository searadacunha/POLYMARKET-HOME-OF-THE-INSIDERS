"""One bounded passage: reclaim, check resources, plan, run tasks one at a time, exit. launchd starts the next one, so a stuck run cannot accumulate.

Each task runs in its own process: a hang, a memory blow-up or a crash costs one attempt, and the supervisor can see and stop all three.
"""
import argparse
import ctypes
import json
import os
import signal
import sqlite3
import subprocess
import sys
import time
import traceback
import uuid
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from .paths import assert_isolated  # noqa: E402
from .recover import InstanceLock, LeaseLost, Pause, Permanent, Transient, claim, fail, finish, open_circuits, reclaim_dead, renew, resource_block  # noqa: E402

DEFAULTS = Path(__file__).parent / 'default_config.json'


def merge(base, extra):
    out = dict(base)
    for key, value in extra.items():
        out[key] = merge(out[key], value) if isinstance(value, dict) and isinstance(out.get(key), dict) else value
    return out


def load_config(root):
    config = json.loads(DEFAULTS.read_text())
    own = Path(root) / 'config.json'
    return merge(config, json.loads(own.read_text())) if own.exists() else config


def isolate_environment(root):
    """The engine reads its state folder from here at import: without this it would point at production's."""
    os.environ['SIGNAL_ENGINE_STATE'] = str(Path(root) / 'engine_state')


class WorkerKilled(Transient):
    pass


LIBPROC = ctypes.CDLL('/usr/lib/libproc.dylib')
PROC_PGRP_ONLY = 2
FOOTPRINT_OFFSET = 72  # rusage_info_v0.ri_phys_footprint, which also counts compressed pages


def footprint_mb(pid):
    buffer = ctypes.create_string_buffer(512)
    if LIBPROC.proc_pid_rusage(pid, 0, buffer) != 0:
        return None
    return int.from_bytes(buffer.raw[FOOTPRINT_OFFSET:FOOTPRINT_OFFSET + 8], 'little') / 1e6


def group_memory_mb(group):
    """The worker and what it started, such as the verifier. Asked of the kernel because the sandbox forbids `ps`: a ceiling read through it would silently read zero."""
    buffer = (ctypes.c_int * 256)()
    size = LIBPROC.proc_listpids(PROC_PGRP_ONLY, group, buffer, ctypes.sizeof(buffer))
    return sum(footprint_mb(pid) or 0.0 for pid in buffer[:size // ctypes.sizeof(ctypes.c_int)] if pid > 0)


def kill_group(group, sig=signal.SIGKILL):
    try:
        os.killpg(group, sig)
    except (ProcessLookupError, PermissionError):  # already gone; macOS answers EPERM for a group of zombies
        pass


def supervise(h, task, config, stop):
    """Returns an outcome. The worker records its own success and failure; anything it could not record, like a kill, is recorded here."""
    limits = config['resources']
    logs = h.root / 'logs'
    logs.mkdir(exist_ok=True)
    log_path = logs / f"task-{task['id']}-{task['attempts']}.log"
    with log_path.open('w') as log:
        worker = subprocess.Popen([sys.executable, '-m', 'harness.runner', 'worker', '--root', str(h.root), '--task', str(task['id'])], stdout=log, stderr=log, cwd=ROOT_DIR, env=dict(os.environ), start_new_session=True)
    started = last_renew = last_memory = time.monotonic()
    outcome = None
    while worker.poll() is None:
        time.sleep(.1)
        now = time.monotonic()
        if now - last_renew > limits['lease_s'] / 3:
            try:
                renew(h, task['id'], task['owner'], task['attempts'], limits['lease_s'])
            except LeaseLost:
                outcome = 'lease_lost'
                kill_group(worker.pid)
            except sqlite3.OperationalError:
                pass  # the worker holds a long transaction; it is working, and the next renewal will get through
            last_renew = now
        if now - last_memory > 2:
            used = group_memory_mb(worker.pid)
            last_memory = now
            if used > limits['worker_memory_mb']:
                outcome = WorkerKilled(f"Worker at {used:.0f} MB, ceiling {limits['worker_memory_mb']} MB")
                kill_group(worker.pid)
        if now - started > limits['task_timeout_s']:
            outcome = WorkerKilled(f"Task over {limits['task_timeout_s']} s")
            kill_group(worker.pid)
        if stop['requested'] and outcome is None:
            outcome = Pause('Passage stopped by a signal', delay=0)
            kill_group(worker.pid, signal.SIGTERM)
            try:
                worker.wait(timeout=10)
            except subprocess.TimeoutExpired:
                kill_group(worker.pid)
    worker.wait()
    row = h.cx.execute('SELECT status, owner, attempts FROM tasks WHERE id=?', (task['id'],)).fetchone()
    still_mine = row['status'] == 'running' and row['owner'] == task['owner'] and row['attempts'] == task['attempts']
    if still_mine:
        if outcome is None or outcome == 'lease_lost':
            outcome = WorkerKilled(f'Worker ended with code {worker.returncode} without a result: {log_path.read_text()[-300:]}')
        result = fail(h, task, outcome, config)
    elif row['status'] == 'pending' and row['attempts'] < task['attempts']:
        result = 'paused'  # the worker recorded a wait, which gives its attempt back
    else:
        result = row['status']
    if row['status'] == 'done' or result in ('done',):
        log_path.unlink(missing_ok=True)
    return result


def passage(root, seconds=240, max_tasks=None, wait_s=5):
    """Returns what happened, for the log and the tests. Any state here is safe to be killed in."""
    root = assert_isolated(root)
    root.mkdir(parents=True, exist_ok=True)
    isolate_environment(root)
    from . import planner
    from .store import Harness
    config = load_config(root)
    out = dict(state=None, done=0, retried=0, quarantined=0, paused=0, reclaimed=None)
    with InstanceLock(root / 'harness.lock') as lock:
        if not lock.acquired:
            return dict(out, state='already_running')
        h = Harness(root)
        owner = f'{os.getpid()}:{uuid.uuid4().hex[:8]}'
        stop = dict(requested=False)
        handlers = {s: signal.signal(s, lambda *_: stop.update(requested=True)) for s in (signal.SIGTERM, signal.SIGINT)}
        try:
            if footprint_mb(os.getpid()) is None:
                return dict(out, state='paused', reason='memory cannot be measured, so its ceiling would not hold')
            out['reclaimed'] = reclaim_dead(h, owner)
            deadline = time.monotonic() + seconds
            while True:
                if stop['requested']:
                    out['state'] = 'stopped'
                    break
                if time.monotonic() > deadline or (max_tasks is not None and out['done'] + out['retried'] + out['quarantined'] >= max_tasks):
                    out['state'] = 'deadline'
                    break
                reason = resource_block(root, config)
                if reason:
                    with h.tx():
                        h.log('warning', 'passage_paused', reason=reason)
                    out.update(state='paused', reason=reason)
                    break
                try:
                    planner.plan(h, config)
                except planner.SourceUnavailable as exc:
                    out.update(state='paused', reason=str(exc))
                    break
                task = claim(h, owner, config['resources']['lease_s'])
                if task is None:
                    pending = h.cx.execute("SELECT COUNT(*) FROM tasks WHERE status='pending'").fetchone()[0]
                    if not pending:
                        out['state'] = 'drained'
                        break
                    closed = open_circuits(h)
                    ahead = h.cx.execute(f"SELECT MIN(next_at) FROM tasks WHERE status='pending' AND kind NOT IN ({','.join('?' * len(closed))})", closed).fetchone()[0]
                    wait = (ahead or 0) - time.time()
                    if 0 < wait <= wait_s:
                        time.sleep(wait)
                        continue
                    # Nothing ready soon: a circuit is open or a dependency waits. The next passage looks again, no spinning.
                    out.update(state='waiting', next_at=ahead, open_circuits=closed)
                    break
                result = supervise(h, task, config, stop)
                key = dict(done='done', retry='retried', pending='retried', quarantined='quarantined', paused='paused').get(result)
                if key:
                    out[key] += 1
            with h.tx():
                h.log('info', 'passage_end', **{k: v for k, v in out.items() if k != 'reclaimed'})
                h.signal.put('harness:last_passage', {k: v for k, v in out.items() if k != 'reclaimed'} | dict(at=time.time()))
        finally:
            for sig, handler in handlers.items():
                signal.signal(sig, handler)
            h.close()
    return out


def worker(root, task_id):
    """Records its own outcome. Exit 0 means the outcome is in the database, whatever it was."""
    isolate_environment(root)
    from .pipeline import ACTIONS, Context
    from .store import Harness
    config = load_config(root)
    h = Harness(root)
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(Pause('Asked to stop', delay=0)))
    signal.alarm(int(config['resources']['task_timeout_s'] * 2))  # if the supervisor dies, nothing else would stop a hung worker
    task = dict(h.cx.execute('SELECT * FROM tasks WHERE id=?', (task_id,)).fetchone())
    try:
        result = ACTIONS[task['kind']](Context(h, task, config), **json.loads(task['params']))
        finish(h, task['id'], task['owner'], task['attempts'], result)
    except LeaseLost as exc:
        print(f'Lease lost, nothing written: {exc}', file=sys.stderr)
    except (Transient, Permanent, Pause) as exc:
        fail(h, task, exc, config)
    except Exception as exc:
        # An unforeseen error is retried, then quarantined with its trace: never swallowed, never endless.
        traceback.print_exc()
        fail(h, task, Transient(f'{type(exc).__name__}: {exc}'), config)
    finally:
        h.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command', choices=('worker',))
    parser.add_argument('--root', required=True)
    parser.add_argument('--task', type=int, required=True)
    args = parser.parse_args()
    worker(assert_isolated(args.root), args.task)
