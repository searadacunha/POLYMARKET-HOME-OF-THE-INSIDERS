from pathlib import Path
import json,hashlib,datetime,stat,plistlib
root=Path('/Users/benjamindacunha/Projects/PolySentinel')
evidence=root/'evidence/detection_prospective_20261030'
store=root/'evidence/prospective_eval'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def dt(x):return datetime.datetime.fromtimestamp(x,datetime.timezone.utc).isoformat(timespec='microseconds')
proof=json.loads((evidence/'operational_proof_1300.json').read_bytes())
print('INTERMEDIATE',dt(proof['observed_at']))
previous='0'*64
total=0
for rp in proof['records']:
    d=store/rp['record']/'data.json'; r=d.with_name('receipt.json')
    data=json.loads(d.read_bytes()); receipt=json.loads(r.read_bytes())
    checks={'data_sha':sha(d)==rp['data_sha256']==receipt['data_sha256'],'chain':data['previous_sha256']==previous,'emitted':rp['emitted_at']==receipt['emitted_at'],'captures':len(data.get('captures',[]))==rp['captures'],'data_0400':stat.S_IMODE(d.stat().st_mode)==0o400,'receipt_0400':stat.S_IMODE(r.stat().st_mode)==0o400,'data_uchg':bool(d.stat().st_flags & stat.UF_IMMUTABLE),'receipt_uchg':bool(r.stat().st_flags & stat.UF_IMMUTABLE)}
    print('RECORD',rp['record'],checks)
    assert all(checks.values())
    total+=len(data.get('captures',[]));previous=sha(r)
print('CAPTURES',total,'equal',total==proof['captures'])
first=json.loads((store/'00000001/data.json').read_bytes())
for c in first['captures']:
    p=c['source_alert']['payload']
    print('ALERT', json.dumps(p,ensure_ascii=False))
    print('CAPTURE_TIME',dt(c['observed_by_sidecar_at']),'MISSING',len(c['missing_inputs']),'PUBLIC',c['public_knowledge'])
    for i in c['inputs']:
        if i['kind']=='event': print('EVENT',json.dumps(i['payload'],ensure_ascii=False))
for name,val in json.loads((store/'00000001/receipt.json').read_bytes()).items():
    print('RECEIPT',name,dt(val) if name.endswith('_at') else val)
activation=json.loads((store/'00000000/data.json').read_bytes())['next_state']
print('ACTIVATION',dt(activation['activated_at']),activation['cursor'],activation['epoch'])
for name,expected in activation['fingerprints'].items():
    file=root/'tools/prospective_eval/sidecar.py' if name=='sidecar.py' else root/name
    actual=sha(file)
    if actual!=expected:print('FINGERPRINT_MISMATCH',name,expected,actual)
print('FINGERPRINTS_COMPARED',len(activation['fingerprints']))
print('SIDECAR_SHA',sha(root/'tools/prospective_eval/sidecar.py'))
launch=Path('/Users/benjamindacunha/Library/LaunchAgents/com.benjamin.polysentinel-prospective.plist')
print('LAUNCHER_SHA',sha(launch),sha(launch)==proof['launcher_sha256'])
calendar=evidence/'fomc_calendar.html'; cr=json.loads(calendar.with_name('fomc_calendar_receipt.json').read_bytes())
print('CALENDAR',calendar.stat().st_size,sha(calendar),cr,'hash_ok',sha(calendar)==cr['sha256'])
lines=calendar.read_text().splitlines()
for k,line in enumerate(lines):
    if 'December' in line and 1390<k<1700:
        print('CALENDAR_LINES','\n'.join(f'{i+1}: {lines[i]}' for i in range(max(k-3,0),min(k+12,len(lines)))))
for rel in ['evidence/detection_prospective_20261030/OPERATIONAL_REPORT.md','tools/prospective_eval/sidecar.py']:
    print('LINES',rel)
    for n,line in enumerate((root/rel).read_text().splitlines(),1):
        if rel.endswith('.md') or any(x in line for x in ['CAP_BYTES','MAX_RECORD_BYTES','BATCH_SIZE','min_free_bytes','floor =','quota_accounted_bytes','mode=ro','query_only','def commit','def load_chain','Refusal(','persisted =','emitted =','sealed_at =','next_state =','save_state','fingerprints(root)']):print(f'{n}: {line}')
