from pathlib import Path
import hashlib,json,datetime,stat
root=Path('/Users/benjamindacunha/Projects/PolySentinel')
p=root/'evidence/detection_prospective_20261030'
store=root/'evidence/prospective_eval'
def read(path):return json.loads(path.read_bytes())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def utc(t):return datetime.datetime.fromtimestamp(t,datetime.timezone.utc).isoformat()
data=read(store/'00000001/data.json'); activation=read(store/'00000000/data.json'); proof=read(p/'operational_proof_1300.json')
print('ACTIVATION',activation['next_state']['epoch'],utc(activation['next_state']['activated_at']),activation['next_state']['cursor'])
for c in data['captures']:
 a=c['source_alert']['payload']
 print('CAPTURE',json.dumps({k:v for k,v in a.items() if k not in ['alerts','trade_ids','evidence','features']},ensure_ascii=False))
 print('TIMES',utc(a['calculated_at']),utc(a['created_at']),utc(c['source_alert']['observed_at']),utc(c['observed_by_sidecar_at']))
 print('ALERT_KEYS', [list(x) for x in a['alerts'][:1]],'ALERT_COUNT',len(a['alerts']))
 print('MISSING',len(c['missing_inputs']), 'PUBLIC',c['public_knowledge']['first_public_at'],c['public_knowledge']['verdict'])
 print('EVENT', [x['payload'] for x in c['inputs'] if x['kind']=='event'])
 print('COUNTS_IDENTITY',all(x['requested']==x['received']+x['empty']+x['errors'] for x in c['lookup_counts'].values()))
for name,t in read(store/'00000001/receipt.json').items():
 print('RECEIPT',name,utc(t) if name.endswith('_at') else t)
checks=[];prev='0'*64;total=0
for declared in proof['records']:
 f=store/declared['record']; d=read(f/'data.json'); r=read(f/'receipt.json')
 n=len(d.get('captures',[]));total+=n
 checks.append(dict(record=f.name,captures=n,declared_n=declared['captures'],hash_ok=sha(f/'data.json')==r['data_sha256']==declared['data_sha256'],chain_ok=d['previous_sha256']==prev,immutable=all(bool((f/k).stat().st_flags&stat.UF_IMMUTABLE) for k in ['data.json','receipt.json']),modes=[oct((f/k).stat().st_mode&0o777) for k in ['data.json','receipt.json']]))
 prev=sha(f/'receipt.json')
print('PROOF_RECORDS',json.dumps(checks));print('CAPTURE_TOTAL',total,proof['captures'])
for file in ['tools/prospective_eval/sidecar.py','config.json','polysentinel/engine.py']:
 print('HASH',file,sha(root/file))
print('LAUNCHER_HASH',sha(Path('/Users/benjamindacunha/Library/LaunchAgents/com.benjamin.polysentinel-prospective.plist')))
print('CALENDAR_HASH',sha(p/'fomc_calendar.html'),read(p/'fomc_calendar_receipt.json')['sha256'])
print('ONDISK_MANIFEST_MATCH',all(sha(root/k if k!='sidecar.py' else root/'tools/prospective_eval/sidecar.py')==v for k,v in activation['next_state']['fingerprints'].items()))
for filename in ['OPERATIONAL_REPORT.md']:
 for i,line in enumerate((p/filename).read_text().splitlines(),1):
  print(f'{filename}:{i}:{line}')
