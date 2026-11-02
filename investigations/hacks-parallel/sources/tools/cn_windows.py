"""Investigation 2: every outflow of the studied ChangeNOW-tagged wallets, in the target window after each incident and in control windows at the same hour of the week. Raw edges are kept per window; nothing here looks at the stolen funds."""
import gzip
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import chainlib as c

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'state/cn_windows'
H48 = 48 * 3600
WEEK = 7 * 86400
SOURCES = {
    'f2020': ('0xf2020cbfc13fd5d4cb2da0ff8ae2d2c093c1c423', 137),
    '6976': ('0x6976d8025229db5f54bc899dd3dbc9285423896b', 137),
    'HW3': ('0xdd3d72c53ff982ff59853da71158bf1538b3ceee', 1),
    'HW4': ('0xeba88149813bec1cccccfdb0dacefaaa5de94cb1', 1),
    'DEP3F3': ('0x3f3ee0a9cac2d01db44001eca3e8382fbe40207b', 1),
}
# T0 is the first stolen-funds touch of each incident, read on chain
INCIDENTS = {
    'A_0522': dict(t0='2026-05-22 07:29:09', sources=['f2020', '6976', 'HW3', 'HW4'], controls=(-14, -7, 7, 14)),
    'C_0625': dict(t0='2026-06-25 05:51:13', sources=['f2020', '6976', 'HW3', 'HW4'], controls=(-14, -7, 7, 14)),
    'D_1029': dict(t0='2026-10-29 17:10:23', sources=['f2020', '6976', 'DEP3F3'], controls=(-28, -21, -14, -7)),
}


def windows(t0, controls):
    yield 'pre48', t0 - H48, t0
    yield 'target48', t0, t0 + H48
    for d in controls:
        yield f'ctrl{d:+d}d', t0 + d * 86400, t0 + d * 86400 + H48


def collect(source, incident, name, a, b):
    path = OUT / f'{incident}__{source}__{name}.jsonl.gz'
    if path.exists():
        return path
    addr, chain = SOURCES[source]
    ba, bb = c.block_at(a, chain), c.block_at(b, chain, 'after')
    edges, cut = c.all_edges(addr, chain, ba, bb)
    assert not cut
    rows = [e for e in edges if a <= e['ts'] < b]
    OUT.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix('.tmp')
    with gzip.open(tmp, 'wt') as f:
        for e in rows:
            f.write(json.dumps(e) + '\n')
    tmp.replace(path)
    out_rows = sum(e['src'] == addr for e in rows)
    print(incident, source, name, c.utc(a), 'rows', len(rows), 'out', out_rows, 'recipients', len({e['dst'] for e in rows if e['src'] == addr}), flush=True)
    return path


def main():
    for incident, cfg in INCIDENTS.items():
        t0 = c.ts_of(cfg['t0'])
        for source in cfg['sources']:
            for name, a, b in windows(t0, cfg['controls']):
                collect(source, incident, name, a, b)


if __name__ == '__main__':
    main()
