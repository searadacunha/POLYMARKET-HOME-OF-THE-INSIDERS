import json,gzip,hashlib
from pathlib import Path
P=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/signal_validation_20261030')
d=json.loads(gzip.decompress((P/'derived/validation.json.gz').read_bytes()))
print('PATH',Path(__file__).parent)
print('ROOT',[(k,type(v).__name__,len(v) if hasattr(v,'__len__') else None) for k,v in d.items()])
for k,v in d.items():
 if k!='scenarios':print(k,str(v)[:3000])
s=d['scenarios'][0]
for k,v in s.items():print('SCENARIO',k,type(v).__name__,str(v)[:2400])
for rel in ['analysis_plan.md','results.md','TRANSACTIONS.md','TEMOINS_ET_FILE.md','code/ana_signal.py']:
 print('LINES',rel)
 for i,line in enumerate((P/rel).read_text().splitlines(),1):
  if rel=='code/ana_signal.py' or rel=='results.md' or '\u2014' in line:print(i,line)
lock=json.loads((P/'PROTOCOL.lock').read_text())
print('HASH_CHECK',[(n,hashlib.sha256((P/n).read_bytes()).hexdigest()==h) for n,h in lock['fichiers'].items()])
print('OUTPUT_HASH',hashlib.sha256((P/'derived/validation.json.gz').read_bytes()).hexdigest())
print('AMENDMENTS',list((P/'amendements').iterdir()))
