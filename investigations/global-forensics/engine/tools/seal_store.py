"""A dated, finished copy of the HTTP store, so a batch's answers reach the encrypted backup at the next pack. The service sends an image of a live base to GitHub only every 7 days. Usage: seal_store.py. Keeps the 2 newest: a sealed file already packed stays in the backup."""
import gzip
import shutil
import sqlite3
import sys
import time
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gf import env

env.redirect_temp()


def main():
    root = env.data_root()
    source = root / 'raw' / 'http_store.sqlite3'
    out = root / 'raw' / 'sealed'
    out.mkdir(exist_ok=True)
    tmp = root / 'tmp' / 'store_seal.sqlite3'
    tmp.unlink(missing_ok=True)
    with sqlite3.connect(f'file:{source}?mode=ro', uri=True, timeout=120) as live, sqlite3.connect(tmp) as copy:
        live.backup(copy, pages=2000, sleep=.05)
    with sqlite3.connect(tmp) as copy:
        check = copy.execute('PRAGMA integrity_check').fetchone()[0]
        answers = copy.execute('SELECT count(*) FROM answers').fetchone()[0]
    if check != 'ok':
        raise RuntimeError(f'sealed copy fails integrity_check: {check}')
    target = out / f"http_store-{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}.sqlite3.gz"
    part = target.with_suffix('.part')
    with tmp.open('rb') as f, gzip.open(part, 'wb', compresslevel=3) as g:
        shutil.copyfileobj(f, g, 1 << 20)
    part.replace(target)
    tmp.unlink()
    for old in sorted(out.glob('http_store-*.sqlite3.gz'))[:-2]:
        old.unlink()
    print(target.name, target.stat().st_size, 'answers', answers)


if __name__ == '__main__':
    main()
