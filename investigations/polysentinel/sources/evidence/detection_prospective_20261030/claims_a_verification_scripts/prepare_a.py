from pathlib import Path
import json,gzip,hashlib
p=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/detection_20261030')
for name in ['derived/replay.json.gz','derived/features.json.gz','derived/label_comparison.json']:
 f=p/name
 obj=json.loads(gzip.decompress(f.read_bytes()) if name.endswith('.gz') else f.read_bytes())
 print('\nFILE',name,'SHA',hashlib.sha256(f.read_bytes()).hexdigest())
 for k,v in obj.items():
  print(k, ('list length '+str(len(v)) if isinstance(v,list) else 'dict keys '+str(list(v)) if isinstance(v,dict) else v))
 if 'scenarios' in obj:
  for s in obj['scenarios']:
   print('SCENARIO',s['delay_seconds'])
   for k,v in s.items():
    print(' ',k, ('list length '+str(len(v)) if isinstance(v,list) else 'dict keys '+str(list(v)) if isinstance(v,dict) else v))
 if 'rows' in obj:
  print('ROW_KEYS',list(obj['rows'][0]) if obj['rows'] else [])
