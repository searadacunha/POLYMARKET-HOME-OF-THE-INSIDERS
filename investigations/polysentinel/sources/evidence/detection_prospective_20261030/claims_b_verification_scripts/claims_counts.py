from pathlib import Path
import json,datetime,hashlib
root=Path('/Users/benjamindacunha/Projects/PolySentinel')
store=root/'evidence/prospective_eval'
proof=json.loads((root/'evidence/detection_prospective_20261030/operational_proof_1300.json').read_bytes())
caps=[]
for row in proof['records']:
 caps += json.loads((store/row['record']/'data.json').read_bytes()).get('captures',[])
a=[c['source_alert']['payload'] for c in caps]
print(json.dumps({'observations':len(a),'unique_cases':len(set(x['id'] for x in a)),'unique_wallets':len(set(x['wallet'] for x in a)),'unique_events':len(set(x['event_id'] for x in a)),'cases_created_before_activation':sum(x['created_at']<1793363597.6447291 for x in a),'event_counts':{e:sum(x['event_id']==e for x in a) for e in sorted(set(x['event_id'] for x in a))}},sort_keys=True))
print('CASE_COUNTS',json.dumps({case:sum(x['id']==case for x in a) for case in sorted(set(x['id'] for x in a))},sort_keys=True))
for f in ['tools/prospective_eval/sidecar.py','Library/LaunchAgents/com.benjamin.polysentinel-prospective.plist']:
 p=root/f if not f.startswith('Library') else Path('/Users/benjamindacunha')/f
 for i,l in enumerate(p.read_text().splitlines(),1):
  if f.startswith('Library') or 'fingerprint' in l or 'CAP_BYTES' in l or 'BATCH_SIZE' in l or 'MAX_RECORD_BYTES' in l:
   print(f'{f}:{i}:{l}')
