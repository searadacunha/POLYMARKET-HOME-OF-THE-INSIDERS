"""Moves cold files to an external SSD, a few at a time, without assuming it is plugged in.

A file counts as moved only once a copy on the volume, flushed and read back, has the right hash. The source stays by default: removing it is a separate step that a person asks for. Live SQLite
files are refused. The volume must hold the marker a person created on it, so an unrelated drive is never written to, and the destination is not encrypted by this code: format it as encrypted APFS.

Usage: python -m harness.tiering {plan,copy,check} --source DIR --volume /Volumes/NAME [--max-bytes N] [--older-days D] [--remove-source]
"""
import argparse
import hashlib
import json
import os
import shutil
import time
from pathlib import Path

from .paths import assert_isolated

MARKER = '.polysentinel-archive'
LIVE = ('.sqlite3', '.sqlite3-wal', '.sqlite3-shm', '.lock', '.wal', '.shm')
MARGIN_BYTES = 2_000_000_000


class VolumeUnavailable(RuntimeError):
    pass


def file_sha(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(1 << 20):
            digest.update(chunk)
    return digest.hexdigest()


def volume_ready(volume):
    volume = Path(volume)
    if not volume.is_dir():
        raise VolumeUnavailable(f'{volume} is not connected')
    if not (volume / MARKER).exists():
        raise VolumeUnavailable(f'{volume} has no {MARKER} file: create it by hand on the drive meant for this')
    return volume


def manifest_path(volume):
    return Path(volume) / 'manifest.jsonl'


def done_entries(volume):
    path = manifest_path(volume)
    if not path.exists():
        return {}
    entries = {}
    for line in path.read_text().splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue  # a line cut by a crash; its copy has no entry, so it is simply done again
        entries[entry['relative']] = entry
    return entries


def plan(source, volume, max_bytes, older_days):
    source = Path(source)
    cutoff = time.time() - older_days * 86400
    done = done_entries(volume)
    chosen, used, too_large = [], 0, []
    for path in sorted(p for p in source.rglob('*') if p.is_file() and not p.is_symlink()):
        relative = str(path.relative_to(source))
        status = path.stat()
        if path.suffix in LIVE or status.st_mtime > cutoff or relative in done:
            continue
        if status.st_size > max_bytes:
            too_large.append(relative)  # says so, and does not block the smaller files behind it
            continue
        if used + status.st_size > max_bytes:
            break
        chosen.append(dict(relative=relative, size=status.st_size))
        used += status.st_size
    return dict(files=chosen, bytes=used, already_copied=len(done), too_large=too_large)


def copy(source, volume, max_bytes, older_days, remove_source=False, margin=MARGIN_BYTES, fault=None):
    """Safe to interrupt and rerun: a partial file keeps a temporary name, and only a verified one enters the manifest."""
    if remove_source:
        assert_isolated(source)  # deleting from production is a decision for a person, not an option of this tool
    source, volume = Path(source), volume_ready(volume)
    chosen = plan(source, volume, max_bytes, older_days)
    if shutil.disk_usage(volume).free - chosen['bytes'] < margin:
        raise VolumeUnavailable(f"{volume} would keep under {margin / 1e9:.1f} GB free after {chosen['bytes'] / 1e9:.2f} GB")
    out = dict(copied=[], failed=[], removed=[], too_large=chosen['too_large'])
    for item in chosen['files']:
        origin, target = source / item['relative'], volume / item['relative']
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + '.partial')
        before = file_sha(origin)
        with open(origin, 'rb') as read, open(partial, 'wb') as write:
            shutil.copyfileobj(read, write, 1 << 20)
            write.flush()
            if fault:
                fault(partial)
            os.fsync(write.fileno())
        if file_sha(partial) != before or file_sha(origin) != before:
            partial.unlink()  # a bad copy, or a file that changed while being read
            out['failed'].append(item['relative'])
            continue
        os.replace(partial, target)
        with manifest_path(volume).open('a') as manifest:
            manifest.write(json.dumps(dict(relative=item['relative'], size=item['size'], sha256=before, at=time.time())) + '\n')
            manifest.flush()
            os.fsync(manifest.fileno())
        out['copied'].append(item['relative'])
        if remove_source:
            origin.unlink()
            out['removed'].append(item['relative'])
    return out


def check(volume):
    """Reads every archived file back. A drive that rots says so here."""
    volume = volume_ready(volume)
    bad = [relative for relative, entry in done_entries(volume).items() if not (volume / relative).exists() or file_sha(volume / relative) != entry['sha256']]
    return dict(files=len(done_entries(volume)), bad=bad)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('plan', 'copy', 'check'))
    parser.add_argument('--source')
    parser.add_argument('--volume', required=True)
    parser.add_argument('--max-bytes', type=int, default=1_000_000_000)
    parser.add_argument('--older-days', type=float, default=7)
    parser.add_argument('--remove-source', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'plan':
            print(json.dumps(plan(args.source, volume_ready(args.volume), args.max_bytes, args.older_days)))
        elif args.command == 'copy':
            print(json.dumps(copy(args.source, args.volume, args.max_bytes, args.older_days, args.remove_source)))
        else:
            print(json.dumps(check(args.volume)))
    except VolumeUnavailable as exc:
        print(json.dumps(dict(state='volume_unavailable', reason=str(exc))))
        return 3
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
