from pathlib import Path
import json,gzip
P=Path('/Users/benjamindacunha/Projects/PolySentinel/studies/signal_validation_20261030')
for rel,lo,hi in [('code/signals.py',1,89),('code/signals.py',228,280),('code/signals.py',362,460),('results.md',35,81)]:
 print('\nFILE',rel)
 for i,line in enumerate((P/rel).read_text().splitlines(),1):
  if lo<=i<=hi:print(f'{i}: {line}')
d=json.loads(gzip.decompress((P/'derived/validation.json.gz').read_bytes()))
p=json.loads(gzip.decompress((P/'data/prior_replay.json.gz').read_bytes()))
print('prior keys',p.keys(),p['scenarios'][0].keys())
print('prior target',[r for r in p['scenarios'][0]['wallet_events'] if r['wallet']=='0x8d3319c51520518ad01f6744486ceea29f376f5b' and r['event_id']=='1105364'])
print('last target',{k:v for k,v in d['scenarios'][0]['ticks'][-1]['target'].items() if k not in ['alerts','bookkeeping']})
print('config',json.loads((P/'data/config.json').read_text()))
