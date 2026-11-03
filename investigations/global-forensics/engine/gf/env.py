"""Where data lives and when to stop. The volume is found by UUID, never by an assumed mount path.

Disk, RAM and swap are different problems: the data root solves the first, streaming and the guard the
others. A guard that cannot read its measure stops the run instead of passing as healthy.
"""
import os
import plistlib
import resource
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

DATA_VOLUME_UUID = '19C7854C-15DE-4C7B-B578-F3E57DBB6FA7'  # APFS image PHI-Data, on VERBATIM HD
DISK_UUID = 'E29F7361-DA26-3CB6-A0D0-5E39D11AD935'
SSD_FLOOR = 13_500_000_000
BATTERY_FLOOR = 15
RSS_CEILING_BYTES = 1_500_000_000
SWAP_RISE_MB = 600
LIVE_COLLECTOR_HEARTBEAT = Path.home() / 'Projects/PolySentinel/metrics/heartbeat.json'


class Stop(RuntimeError):
    """A guard stayed red. Everything already read is on disk; the run resumes from it."""


def mount_of(uuid):
    try:
        info = plistlib.loads(subprocess.check_output(['diskutil', 'info', '-plist', uuid], stderr=subprocess.DEVNULL, timeout=30))
    except (subprocess.SubprocessError, ValueError) as exc:
        raise Stop(f'volume {uuid} not readable: {exc}') from exc
    mount = info.get('MountPoint')
    if not mount:
        raise Stop(f'volume {uuid} not mounted')
    return Path(mount)


def data_root():
    root = mount_of(DATA_VOLUME_UUID) / 'global-forensics'
    root.mkdir(parents=True, exist_ok=True)
    return root


def redirect_temp():
    """Temporaries and caches of this process go to the external volume, not the SSD shared with the collector."""
    tmp = data_root() / 'tmp'
    tmp.mkdir(exist_ok=True)
    os.environ['TMPDIR'] = str(tmp)
    tempfile.tempdir = str(tmp)
    return tmp


def swap_used_mb():
    text = subprocess.check_output(['sysctl', '-n', 'vm.swapusage'], text=True, timeout=15)
    return float(text.split('used = ')[1].split('M')[0])


def battery_percent():
    """None on mains power, otherwise the charge. Unreadable raises: a blind run is not a safe run."""
    text = subprocess.check_output(['pmset', '-g', 'batt'], text=True, timeout=15)
    if 'discharging' not in text:
        return None
    return int(text.split('%')[0].rsplit(None, 1)[-1])


class Guard:
    """Polled from the network layer, at most every 30 s. Waits while red, then raises Stop."""

    def __init__(self, max_wait_s=1800, interval_s=30, sleep=time.sleep):
        self.max_wait_s, self.interval_s, self.sleep = max_wait_s, interval_s, sleep
        self.checked = 0.0
        self.swap_start = None

    def red(self):
        free = shutil.disk_usage('/').free
        if free < SSD_FLOOR:
            return f'SSD at {free / 1e9:.2f} GB free, floor {SSD_FLOOR / 1e9:.1f}'
        data_free = shutil.disk_usage(data_root()).free
        if data_free < 20_000_000_000:
            return f'data volume at {data_free / 1e9:.1f} GB free'
        used = swap_used_mb()
        if self.swap_start is None:
            self.swap_start = used
        if used > self.swap_start + SWAP_RISE_MB:
            return f'swap rose to {used:.0f} MB from {self.swap_start:.0f} MB'
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss  # bytes on macOS
        if rss > RSS_CEILING_BYTES:
            raise Stop(f'process peak memory {rss / 1e9:.2f} GB above ceiling: fix the code, do not wait')
        charge = battery_percent()
        if charge is not None and charge < BATTERY_FLOOR:
            raise Stop(f'on battery at {charge}%: stopped now')
        if charge is not None:  # long jobs run on mains power only: a cable pulled for a moment costs a wait, and past that the run stops with everything on disk
            return f'on battery at {charge}%'
        return None

    def __call__(self):
        if time.time() - self.checked < self.interval_s:
            return
        self.checked = time.time()
        started = time.time()
        while (why := self.red()):
            if time.time() - started > self.max_wait_s:
                raise Stop(why)
            self.sleep(60)
