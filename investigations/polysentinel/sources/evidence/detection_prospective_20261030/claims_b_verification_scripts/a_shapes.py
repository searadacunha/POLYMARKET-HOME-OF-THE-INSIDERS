from pathlib import Path
import json,gzip,hashlib
p=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/detection_20261030')
for file in ['derived/replay.json.gz','derived/features.json.gz','derived/label_comparison.json','data/labels_after.json','data/runtime_size_profile.json']:
 b=(p/file).read_bytes();d=json.loads(gzip.decompress(b) if file.endswith('.gz') else b)
 print('\nFILE',file,'sha',hashlib.sha256(b).hexdigest())
 print('KEYS',list(d));print('SCALARS',{k:v for k,v in d.items() if not isinstance(v,(list,dict))})
 for k,v in d.items():
  if isinstance(v,list):
   print('LIST',k,'len',len(v),'sample',str(v[0])[:7000] if v else None)
  elif isinstance(v,dict):print('DICT',k,str(v)[:2500])
