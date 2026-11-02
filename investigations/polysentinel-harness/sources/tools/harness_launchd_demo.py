"""launchd test with demonstration data only: a throwaway job under its own label, removed at the end, never written to ~/Library/LaunchAgents.

Loads the job from this folder (so a login would not bring it back), kills its passage and its worker while they run, and checks that launchd's next start finishes the work with the
same conclusions as an uninterrupted run. Does not cover a real restart of the Mac.

Usage: python tools/harness_launchd_demo.py STATE_DIR OUT.json
"""
import json
import os
import plistlib
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.environ.setdefault('SIGNAL_ENGINE_STATE', str(ROOT / 'state/engine_state'))

from harness import demo  # noqa: E402
from harness.store import Harness  # noqa: E402

LABEL = 'com.benjamin.polysentinel-harness-demo'
SMALL = dict(wallets=700, events=40, batch_rows=200)


def digest(root):
    h = Harness(root)
    try:
        return h.digest(), h.status()
    finally:
        h.close()


def pids(root):
    done = subprocess.run(['pgrep', '-f', str(root)], capture_output=True, text=True)
    return [int(p) for p in done.stdout.split() if int(p) != os.getpid()]


def main(state, out):
    state = Path(state).resolve()
    reference, root = state / 'reference', state / 'launchd'
    domain = f'gui/{os.getuid()}'
    target = f'{domain}/{LABEL}'
    result = dict(label=LABEL, starts=[], kills=[])
    demo.build(reference, **SMALL)
    subprocess.run([sys.executable, '-m', 'harness', 'run', '--root', str(reference), '--seconds', '300'], cwd=ROOT, check=True, capture_output=True)
    result['reference_digest'] = digest(reference)[0]
    demo.build(root, **SMALL)
    plist = state / f'{LABEL}.plist'
    plist.write_bytes(plistlib.dumps(dict(Label=LABEL, Nice=15, ProcessType='Standard', RunAtLoad=True, StartInterval=10, WorkingDirectory=str(ROOT), StandardOutPath=str(root / 'launchd.out'), StandardErrorPath=str(root / 'launchd.err'),
                                          EnvironmentVariables=dict(PYTHONDONTWRITEBYTECODE='1'),
                                          ProgramArguments=['/usr/bin/sandbox-exec', '-D', f'HOME={Path.home()}', '-f', str(ROOT / 'deploy/deny_production.sb'), str(ROOT / '.venv/bin/python'), '-m', 'harness', 'run', '--root', str(root), '--seconds', '40'])))
    subprocess.run(['plutil', '-lint', str(plist)], check=True, capture_output=True)
    result['production_plist_lint'] = subprocess.run(['plutil', '-lint', str(ROOT / 'deploy/com.benjamin.polysentinel-harness.plist')], capture_output=True, text=True).stdout.strip()
    subprocess.run(['launchctl', 'bootstrap', domain, str(plist)], check=True, capture_output=True, text=True)
    try:
        database = root / 'harness.sqlite3'
        deadline = time.monotonic() + 300
        kills = 0
        while time.monotonic() < deadline:
            time.sleep(1)
            running = pids(root)
            if not database.exists():
                continue
            h = Harness(root)
            done = h.cx.execute("SELECT COUNT(*) FROM tasks WHERE status='done'").fetchone()[0]
            pending = h.cx.execute("SELECT COUNT(*) FROM tasks WHERE status IN ('pending','running')").fetchone()[0]
            h.close()
            if kills < 2 and done >= 3 + kills * 25 and running:
                for pid in running:
                    try:
                        os.kill(pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                kills += 1
                result['kills'].append(dict(at_done=done, killed=len(running)))
            if done and not pending and not running and kills >= 2:
                break
        info = subprocess.run(['launchctl', 'print', target], capture_output=True, text=True).stdout
        result['launchd_runs'] = next((line.strip() for line in info.splitlines() if line.strip().startswith('runs =')), None)
        result['launchd_last_exit'] = next((line.strip() for line in info.splitlines() if 'last exit' in line), None)
    finally:
        subprocess.run(['launchctl', 'bootout', target], capture_output=True, text=True)
    for _ in range(20):
        if not pids(root):
            break
        time.sleep(.5)
    found, status = digest(root)
    result.update(digest=found, same_as_reference=found == result['reference_digest'], tasks=status['tasks'], quarantined=status['quarantined'], job_removed=subprocess.run(['launchctl', 'print', target], capture_output=True).returncode != 0, leftover_processes=pids(root))
    Path(out).write_text(json.dumps(result, indent=1))
    print(json.dumps(result, indent=1))
    return 0 if result['same_as_reference'] and result['job_removed'] and len(result['kills']) == 2 else 1


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
