from pathlib import Path
import re,json
for base in [Path('/private/tmp'),Path('/private/var/folders/ym/llyxpdnn5b95whw2zh5tl81h0000gn/T')]:
 print('BASE',base)
 scanned=0;hits=[]
 for pattern in ['*.py','*/*.py','*/*/*.py']:
  try:paths=base.glob(pattern)
  except OSError:continue
  for p in paths:
   try:
    if p.stat().st_size>1_000_000:continue
    txt=p.read_text();scanned+=1
   except (OSError,UnicodeError):continue
   if 'replay_input.jsonl.gz' in txt:
    if p.parts[-2]=='code' and 'repro_' in str(p):continue
    if 'claims_b.iRPZCf' in str(p):continue
    hits.append(str(p))
 print('small_python_files_scanned',scanned,'non_repro_hits',hits)
