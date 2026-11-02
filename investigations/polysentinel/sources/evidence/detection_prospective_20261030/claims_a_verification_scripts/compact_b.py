from pathlib import Path
import json,datetime
root=Path('/Users/benjamindacunha/Projects/PolySentinel')
data=json.loads((root/'evidence/prospective_eval/00000001/data.json').read_bytes())
for c in data['captures']:
 p=c['source_alert']['payload']
 for k in ['id','event_id','score','calculated_at','created_at']:print(k,p[k])
 print('families',sorted({s['family'] for s in p['signals'] if s['weight']}))
 print('rules',sorted({s['rule'] for s in p['signals']}))
 print('missing',len(c['missing_inputs']))
 print('public',c['public_knowledge'])
 counts=c['lookup_counts']
 print('counts', {k:sum(v[k] for v in counts.values()) for k in ['requested','received','empty','errors']})
print('script lines:')
s=(root/'tools/prospective_eval/sidecar.py').read_text().splitlines()
for a,b in [(330,375),(410,444)]:
 for n in range(a,b):print(f'{n+1}: {s[n]}')
print('memory evidence lines')
m=Path('/Users/benjamindacunha/.codex/memories/MEMORY.md').read_text().splitlines()
for a,b in [(55,81)]:
 for n in range(a-1,b):print(f'{n+1}: {m[n]}')
