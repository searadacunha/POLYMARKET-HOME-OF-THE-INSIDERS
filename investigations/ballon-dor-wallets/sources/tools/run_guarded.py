"""Runs one command at lowest priority under a watchdog: production and the replay come first.

Usage: run_guarded.py [--rss-mb N] -- command...
Suspends the command while the collector's heartbeat is older than 100 s or the load is above 16, resumes when calm, kills it past a memory ceiling or the shared disk floor.
"""
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

HEARTBEAT = Path.home() / 'Projects/PolySentinel/metrics/heartbeat.json'
STALE_S, CALM_S, LOAD_HIGH, LOAD_CALM = 100, 70, 16, 12
FREE_FLOOR = 14_500_000_000


def beat_age():
    return time.time() - json.loads(HEARTBEAT.read_text())['at']


def rss_mb(pid):
    """Whole process group: a child counts too."""
    out = subprocess.run(['ps', '-o', 'rss=', '-g', str(pid)], capture_output=True, text=True).stdout
    return sum(int(x) for x in out.split()) / 1024


def main():
    args = sys.argv[1:]
    ceiling = 600
    if args[0] == '--rss-mb':
        ceiling, args = int(args[1]), args[2:]
    assert args[0] == '--'
    child = subprocess.Popen(['nice', '-n', '19'] + args[1:], start_new_session=True)
    stopped_since, pauses, peak = None, 0, 0
    while child.poll() is None:
        time.sleep(5)
        age, load = beat_age(), os.getloadavg()[0]
        peak = max(peak, rss_mb(child.pid))
        if peak > ceiling or shutil.disk_usage('/').free < FREE_FLOOR:
            print(f'[guard] kill: rss {peak:.0f} MB, ceiling {ceiling}', flush=True)
            os.killpg(child.pid, signal.SIGTERM)
            child.wait(timeout=30)
            sys.exit(3)
        if stopped_since is None and (age > STALE_S or load > LOAD_HIGH):
            os.killpg(child.pid, signal.SIGSTOP)
            stopped_since = time.time()
            pauses += 1
            print(f'[guard] pause {pauses}: heartbeat {age:.0f} s, load {load:.1f}', flush=True)
        elif stopped_since is not None and age < CALM_S and load < LOAD_CALM:
            os.killpg(child.pid, signal.SIGCONT)
            print(f'[guard] resume after {time.time() - stopped_since:.0f} s', flush=True)
            stopped_since = None
    print(f'[guard] done rc={child.returncode} pauses={pauses} peak_rss_mb={peak:.0f}', flush=True)
    sys.exit(child.returncode)


if __name__ == '__main__':
    main()
