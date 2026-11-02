"""Bound new study artifacts; never reclaim existing evidence."""
from pathlib import Path
import shutil

STUDY=Path(__file__).resolve().parents[1]
CAP=20_000_000

def capacity(extra=0):
    used=0
    for p in STUDY.rglob('*'):
        if p.is_symlink():raise ValueError('Study symlink not allowed')
        if p.is_file():
            s=p.stat();used+=max(s.st_size,s.st_blocks*512)
    if used+extra>CAP:raise RuntimeError('Study 20 MB cap; no evidence deleted')
    if shutil.disk_usage(STUDY).free-extra<10_500_000_000:
        raise RuntimeError('Study preserves 10.5 GB normal-mode margin')
    return used

def write_bytes(path,body):
    capacity(len(body)+8192)
    with Path(path).open('xb') as stream:stream.write(body)
