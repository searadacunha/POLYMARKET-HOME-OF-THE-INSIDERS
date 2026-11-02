"""Offline integrity of state/out_full: blocks never go back inside a file (a re-appended page would), row count equals its checkpoint, every checkpoint is done and reached the end of the window. Writes state/check_out.json. Exit 1 on any defect."""
import csv, glob, gzip, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
win = json.loads((ROOT / 'state/window.json').read_text())
res, bad = {}, []
for p in sorted(glob.glob(str(ROOT / 'state/out_full/*.csv.gz'))):
    name = Path(p).name[:-7]
    chain, addr, action = name.split('_', 2)
    ck = json.loads((ROOT / f'state/out_full/{name}.ck.json').read_text())
    n, back, last, first_b, last_b, first_t, last_t = 0, 0, 0, None, None, None, None
    seen = set()
    dup = 0
    with gzip.open(p, 'rt', newline='') as f:
        for r in csv.reader(f):
            n += 1
            b = int(r[0])
            if b < last:
                back += 1
            last = b
            first_b = first_b or b
            first_t = first_t or int(r[1])
            last_t = int(r[1])
            if action == 'txlist':
                if r[2] in seen:
                    dup += 1
                seen.add(r[2])
    ok = n == ck['rows'] and back == 0 and dup == 0 and ck['done'] and ck['end'] == win['chains'][chain][1]
    res[name] = dict(rows=n, ck_rows=ck['rows'], back=back, dup_hash=dup, done=ck['done'], first_block=first_b, last_block=last, first_ts=first_t, last_ts=last_t, ok=ok)
    if not ok:
        bad.append(name)
(ROOT / 'state/check_out.json').write_text(json.dumps(res, indent=0))
print('files', len(res), 'rows', sum(v['rows'] for v in res.values()), 'bad', bad)
for k in bad:
    print(k, res[k])
sys.exit(1 if bad else 0)
