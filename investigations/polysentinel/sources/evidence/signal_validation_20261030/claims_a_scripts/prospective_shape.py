from pathlib import Path
import json
P=Path('/Users/benjamindacunha/Projects/PolySentinel/evidence/prospective_eval')
d=json.loads((P/'00000001/data.json').read_text())
c=d['captures'][0]
print('capture keys',c.keys())
for k,v in c.items():
 if k not in ['evidence_references','inputs']:print(k,str(v)[:1800])
print('inputs keys',c.get('inputs',{}).keys())
