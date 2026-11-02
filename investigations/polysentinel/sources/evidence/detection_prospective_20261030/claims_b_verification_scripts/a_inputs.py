from pathlib import Path
import json,gzip,hashlib,datetime
p=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/detection_20261030')
m=json.loads((p/'data/input_manifest.json').read_bytes())
b=Path(m['source']).read_bytes();assert hashlib.sha256(b).hexdigest()==m['source_sha256']
src=[json.loads(x) for x in gzip.decompress(b).splitlines()];rows=[json.loads(x) for x in gzip.decompress((p/'data/replay_input.jsonl.gz').read_bytes()).splitlines()]
lo=m['lower'];hi=m['upper_exclusive'];oldlo=datetime.datetime(2026,9,26,20,tzinfo=datetime.timezone.utc).timestamp()
counts={'read':len(src),'before_window':sum(r['timestamp']<lo for r in src),'after_cutoff':sum(r['timestamp']>=hi for r in src),'kept':sum(lo<=r['timestamp']<hi for r in src),'duplicates':len(rows)-len({r['id'] for r in rows})}
assert counts==m['counts']
assert set().union(*(set(r) for r in rows))<=set(m['fields'])
byid={r['id']:r for r in src}
assert all(r['observed_at']==byid[r['id']]['observed_at'] for r in rows)
print('INPUT_RECALC',counts,'wallets',len({r['wallet'] for r in rows}),'events',len({r['event_id'] for r in rows}),'old_window',sum(oldlo<=r['timestamp']<hi for r in src),'extra_before_old',sum(lo<=r['timestamp']<oldlo for r in src),'all_observed_after_cutoff',all(r['observed_at']>hi for r in rows))
report=(p/'results.md').read_text();print('FORM_EM_DASH',report.count('\u2014'))
for i,l in enumerate(report.splitlines(),1):
 if not l.startswith('|') and l.strip():print(f'{i}:{l}')
