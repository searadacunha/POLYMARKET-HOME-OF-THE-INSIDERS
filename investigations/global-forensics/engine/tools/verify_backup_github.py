"""Second copy, proved from bytes: download a pack's encrypted assets from the GitHub release, decrypt, unpack, hash each file, compare with the file on the data volume.

Trusts neither manifests nor the service's own verdict. Usage: verify_backup_github.py <out.json> <work dir> [root prefix]. A file changed since it was packed is reported CHANGED_SINCE, not as a failure of the copy.
"""
import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import time
from pathlib import Path

CFG = json.loads((Path.home() / '.config/phi-backup/config.json').read_text())
ROOTS = {'global-forensics': '/Volumes/PHI-Data/global-forensics', 'global-forensics-checkpoint': '/'}


def sha(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


def main(out, work, prefix='global-forensics'):
    db = sqlite3.connect(f"file:{Path.home()}/.local/state/phi-backup/state.sqlite3?mode=ro", uri=True, timeout=60)
    db.row_factory = sqlite3.Row
    work = Path(work)
    packs = db.execute("SELECT * FROM packs WHERE root LIKE ? AND gh_state='verified'", (prefix + '%',)).fetchall()
    report = dict(at=time.time(), repo=CFG['repo'], source='GitHub release assets, downloaded then decrypted with the age identity', packs=[], files=dict(identical=0, changed_since=0, gone=0, different=0), problems=[])
    for pack in packs:
        volumes = json.loads(pack['enc_volumes'])
        here = work / pack['name']
        here.mkdir(parents=True, exist_ok=True)
        for v in volumes:
            subprocess.run([CFG['gh_bin'], 'release', 'download', pack['gh_tag'], '--repo', CFG['repo'], '--pattern', v['name'], '--dir', str(here), '--clobber'], check=True, capture_output=True, timeout=1200)
        joined = here / 'pack.age'
        with joined.open('wb') as w:
            for v in volumes:
                with (here / v['name']).open('rb') as r:
                    shutil.copyfileobj(r, w, 1 << 20)
        clear = here / 'pack.out'
        with clear.open('wb') as w:
            subprocess.run([CFG['age_bin'], '-d', '-i', os.path.expanduser(CFG['identity']), str(joined)], check=True, stdout=w, timeout=1200)
        members = 0
        wanted = {r['member']: r['sha'] for r in db.execute('SELECT sha, member FROM blobs WHERE pack=?', (pack['name'],))}
        with tarfile.open(clear) as tar:
            for member in tar:
                if not member.isfile():
                    continue
                members += 1
                got = hashlib.sha256()
                handle = tar.extractfile(member)
                for chunk in iter(lambda: handle.read(1 << 20), b''):
                    got.update(chunk)
                got = got.hexdigest()
                if wanted.get(member.name) not in (None, got):
                    report['problems'].append(dict(pack=pack['name'], member=member.name, kind='bytes differ from recorded hash'))
                for row in db.execute("SELECT root, rel, mtime_ns FROM files WHERE sha=? AND root LIKE ? AND klass!='link'", (got, prefix + '%')):
                    original = Path(ROOTS[row['root']]) / row['rel']
                    if not original.exists():
                        report['files']['gone'] += 1
                    elif sha(original) == got:
                        report['files']['identical'] += 1
                    else:
                        report['files']['changed_since'] += 1
        report['packs'].append(dict(name=pack['name'], tag=pack['gh_tag'], kind=pack['kind'], volumes=len(volumes), encrypted_bytes=sum(v['size'] for v in volumes), members_read=members, recorded=pack['n_files']))
        shutil.rmtree(here)
    Path(out).write_text(json.dumps(report, indent=1))
    print(json.dumps(dict(packs=len(report['packs']), files=report['files'], problems=len(report['problems']))))
    return 1 if report['problems'] else 0


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
